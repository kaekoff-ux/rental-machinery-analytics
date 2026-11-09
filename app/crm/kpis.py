"""Dados do Painel: as mesmas tabelas que alimentavam o dashboard do Cowork, agora lidas do banco.

O dashboard do Cowork (artefato de 07/11/2026) calculava tudo a partir de uma tabela
"máquina × mês" (equip_mes) e de uma lista de leads (leads_det). Aqui o servidor monta essas
tabelas a partir do banco e a página aplica as mesmas fórmulas. As regras abaixo foram
conferidas contra os CSVs do Cowork em 09/11/2026 (testes em crm/tests/test_kpis.py):

- receita: faturas pela competência, na máquina do contrato;
- dias_locados: dias em contrato, do início à devolução (ou ao fim previsto, se ativo), com o
  último dia incluído e sem contratos cancelados;
- dias_frota: dias em que a máquina já tinha sido adquirida; horas_periodo = dias_frota × 24;
- horas_parada, custo_manut e contagem de OS: pelo mês de abertura da OS;
- horas_trab: cada intervalo entre leituras do horímetro conta no mês da leitura seguinte; o
  trecho antes da primeira leitura é estimado pela taxa do primeiro intervalo, desde o início
  da janela ou a aquisição;
- depreciacao: horas_trab × valor de aquisição ÷ vida útil em horas;
- vencido: faturas Vencido; atraso: só faturas pagas depois do vencimento.
"""
from collections import defaultdict
from datetime import date, timedelta

from django.utils import timezone

from .models import Contrato, Equipamento, Fatura, Lead, LeituraHorimetro, OrdemServico

INICIO = date(2024, 1, 1)
FIM = date(2025, 12, 31)

METRICAS = [
    "receita", "dias_locados", "dias_frota", "horas_periodo", "horas_parada", "horas_trab", "custo_manut",
    "depreciacao", "os_preventiva", "os_preditiva", "os_corretiva", "horas_parada_corretiva", "vencido",
    "atraso_soma", "atraso_n",
]


def _mes(d):
    return f"{d.year:04d}-{d.month:02d}"


def _f(v):
    return float(v) if v is not None else 0.0


def _dias_por_mes(inicio, fim, acum, chave):
    """Soma 1 por dia de [inicio, fim] (fim incluído) dentro da janela, agrupado por mês."""
    a, b = max(inicio, INICIO), min(fim, FIM)
    d = a
    while d <= b:
        # avança mês a mês para não iterar dia a dia
        prox = date(d.year + (d.month == 12), d.month % 12 + 1, 1)
        ate = min(b, prox - timedelta(days=1))
        acum[(chave, _mes(d))]["dias"] += (ate - d).days + 1
        d = prox


def equip_mes():
    """Uma linha por máquina e mês (2024-2025), com as medidas do dashboard."""
    eqs = list(Equipamento.objects.values("id", "codigo", "segmento", "filial", "fabricante", "modelo",
                                          "data_aquisicao", "valor_aquisicao", "vida_util_horas"))
    por_id = {e["id"]: e for e in eqs}
    linhas = defaultdict(lambda: defaultdict(float))

    # Frota: dias desde a aquisição.
    tmp = defaultdict(lambda: defaultdict(float))
    for e in eqs:
        _dias_por_mes(e["data_aquisicao"], FIM, tmp, e["id"])
    for (eq, m), v in tmp.items():
        linhas[(eq, m)]["dias_frota"] = v["dias"]
        linhas[(eq, m)]["horas_periodo"] = v["dias"] * 24

    # Locação: início até devolução (ou fim previsto), sem cancelados.
    tmp = defaultdict(lambda: defaultdict(float))
    for c in Contrato.objects.exclude(status="Cancelado").values(
        "equipamento_id", "data_inicio", "data_devolucao", "data_fim_prevista"
    ):
        fim = c["data_devolucao"] or min(c["data_fim_prevista"], FIM)
        _dias_por_mes(c["data_inicio"], fim, tmp, c["equipamento_id"])
    for (eq, m), v in tmp.items():
        linhas[(eq, m)]["dias_locados"] = v["dias"]

    # Faturas: receita, vencido e atraso pela competência.
    for f in Fatura.objects.filter(competencia__gte=_mes(INICIO), competencia__lte=_mes(FIM)).values(
        "contrato__equipamento_id", "competencia", "valor_faturado", "status_pagamento", "data_pagamento",
        "data_vencimento",
    ):
        lin = linhas[(f["contrato__equipamento_id"], f["competencia"])]
        lin["receita"] += _f(f["valor_faturado"])
        if f["status_pagamento"] == "Vencido":
            lin["vencido"] += _f(f["valor_faturado"])
        if f["data_pagamento"] and f["data_pagamento"] > f["data_vencimento"]:
            lin["atraso_soma"] += (f["data_pagamento"] - f["data_vencimento"]).days
            lin["atraso_n"] += 1

    # Ordens de serviço pelo mês de abertura.
    chave_tipo = {"Preventiva": "os_preventiva", "Preditiva": "os_preditiva", "Corretiva": "os_corretiva"}
    for o in OrdemServico.objects.filter(data_abertura__range=(INICIO, FIM)).values(
        "equipamento_id", "data_abertura", "tipo", "horas_parada", "custo_pecas", "custo_mao_obra"
    ):
        lin = linhas[(o["equipamento_id"], _mes(o["data_abertura"]))]
        lin["horas_parada"] += _f(o["horas_parada"])
        lin["custo_manut"] += _f(o["custo_pecas"]) + _f(o["custo_mao_obra"])
        lin[chave_tipo[o["tipo"]]] += 1
        if o["tipo"] == "Corretiva":
            lin["horas_parada_corretiva"] += _f(o["horas_parada"])

    # Horímetro: horas trabalhadas e depreciação por horas.
    leituras = defaultdict(list)
    for r in LeituraHorimetro.objects.filter(data_leitura__range=(INICIO, FIM)).values_list(
        "equipamento_id", "data_leitura", "horimetro_horas"
    ):
        leituras[r[0]].append((r[1], _f(r[2])))
    for eq, lst in leituras.items():
        lst.sort()
        e = por_id[eq]
        taxa_dep = _f(e["valor_aquisicao"]) / e["vida_util_horas"] if e["vida_util_horas"] else 0.0
        if len(lst) >= 2:
            (d1, h1), (d2, h2) = lst[0], lst[1]
            inicio = max(INICIO, e["data_aquisicao"])
            if (d2 - d1).days > 0 and d1 > inicio:
                estimado = (h2 - h1) / (d2 - d1).days * (d1 - inicio).days
                linhas[(eq, _mes(d1))]["horas_trab"] += estimado
        for (_, h0), (d1, h1) in zip(lst, lst[1:]):
            linhas[(eq, _mes(d1))]["horas_trab"] += max(0.0, h1 - h0)
    for (eq, m), lin in linhas.items():
        e = por_id[eq]
        if e["vida_util_horas"]:
            lin["depreciacao"] = lin["horas_trab"] * _f(e["valor_aquisicao"]) / e["vida_util_horas"]

    saida = []
    for (eq, m), lin in sorted(linhas.items(), key=lambda kv: (por_id[kv[0][0]]["codigo"], kv[0][1])):
        e = por_id[eq]
        saida.append({
            "id_equipamento": e["codigo"], "mes": m, "segmento": e["segmento"], "filial": e["filial"],
            "modelo": f'{e["fabricante"]} {e["modelo"]}',
            **{k: round(lin.get(k, 0.0), 4) for k in METRICAS},
        })
    return saida


def mensal(linhas_equip_mes):
    acc = defaultdict(lambda: defaultdict(float))
    for r in linhas_equip_mes:
        for k in METRICAS:
            acc[r["mes"]][k] += r[k]
    return [{"mes": m, **{k: round(v[k], 2) for k in METRICAS}} for m, v in sorted(acc.items())]


def segmentos(linhas_equip_mes, ano="2025"):
    acc = defaultdict(lambda: defaultdict(float))
    maquinas = defaultdict(set)
    for r in linhas_equip_mes:
        if r["mes"].startswith(ano):
            for k in METRICAS:
                acc[r["segmento"]][k] += r[k]
            if r["dias_frota"] > 0:
                maquinas[r["segmento"]].add(r["id_equipamento"])
    return [
        {"segmento": s, "equipamentos": len(maquinas[s]), **{k: round(v[k], 2) for k in METRICAS}}
        for s, v in sorted(acc.items())
    ]


def faturas_ano():
    """Faturado, vencido em aberto, a vencer e atraso médio por ano de competência."""
    acc = defaultdict(lambda: {"faturado": 0.0, "vencido_aberto": 0.0, "a_vencer": 0.0, "faturas": 0,
                               "faturas_pagas": 0, "atraso_soma": 0, "atraso_n": 0})
    for f in Fatura.objects.values("competencia", "valor_faturado", "status_pagamento", "data_pagamento",
                                   "data_vencimento"):
        a = acc[f["competencia"][:4]]
        v = _f(f["valor_faturado"])
        a["faturado"] += v
        a["faturas"] += 1
        if f["status_pagamento"] == "Vencido":
            a["vencido_aberto"] += v
        elif f["status_pagamento"] == "Em aberto":
            a["a_vencer"] += v
        elif f["status_pagamento"] == "Pago":
            a["faturas_pagas"] += 1
        if f["data_pagamento"] and f["data_pagamento"] > f["data_vencimento"]:
            a["atraso_soma"] += (f["data_pagamento"] - f["data_vencimento"]).days
            a["atraso_n"] += 1
    saida = []
    for ano, a in sorted(acc.items()):
        saida.append({
            "ano": ano, "faturado": round(a["faturado"], 2), "vencido_aberto": round(a["vencido_aberto"], 2),
            "a_vencer": round(a["a_vencer"], 2), "faturas": a["faturas"], "faturas_pagas": a["faturas_pagas"],
            "atraso_medio_dias": round(a["atraso_soma"] / a["atraso_n"], 2) if a["atraso_n"] else 0,
        })
    return saida


def contratos_vencer(hoje=None):
    """Contratos ativos pelo fim previsto, a partir de hoje."""
    hoje = hoje or timezone.localdate()
    janelas = [("Até 30 dias", 0, 30), ("31 a 60 dias", 31, 60), ("61 a 90 dias", 61, 90), ("Mais de 90 dias", 91, None)]
    cont = {j[0]: 0 for j in janelas}
    for fim in Contrato.objects.filter(status="Ativo", data_fim_prevista__gte=hoje).values_list(
        "data_fim_prevista", flat=True
    ):
        d = (fim - hoje).days
        for nome, a, b in janelas:
            if d >= a and (b is None or d <= b):
                cont[nome] += 1
                break
    return [{"janela": n, "contratos": cont[n], "ordem": i} for i, (n, _, _) in enumerate(janelas, start=1)]


def leads_det(ano=None):
    """Um lead por linha, sem nome nem contato (o que o painel precisa)."""
    qs = Lead.objects.all()
    if ano:
        qs = qs.filter(data_envio__year=ano)
    saida = []
    for lead in qs.order_by("data_envio"):
        envio = timezone.localtime(lead.data_envio)
        saida.append({
            "mes_envio": _mes(envio.date()),
            "segmento": lead.segmento or "Não informado",
            "modelo": lead.modelo or "Qualquer modelo",
            "cidade": lead.cidade or "Não informada",
            "origem": lead.origem,
            "status": lead.status,
            "motivo_perda": lead.motivo_perda,
            "dias_fechamento": lead.dias_fechamento,
        })
    return saida


def leads_resumo(det):
    por_status = defaultdict(lambda: {"leads": 0, "dias": 0, "n": 0})
    motivos = defaultdict(int)
    origens = defaultdict(lambda: {"leads": 0, "fechados": 0, "perdidos": 0})
    for r in det:
        s = por_status[r["status"]]
        s["leads"] += 1
        if r["status"] == "Fechado" and r["dias_fechamento"] is not None:
            s["dias"] += r["dias_fechamento"]
            s["n"] += 1
        if r["status"] == "Perdidos" and r["motivo_perda"]:
            motivos[r["motivo_perda"]] += 1
        o = origens[r["origem"]]
        o["leads"] += 1
        o["fechados"] += r["status"] == "Fechado"
        o["perdidos"] += r["status"] == "Perdidos"
    status = [
        {"status": st, "leads": v["leads"], "tempo_medio_fechamento_dias": round(v["dias"] / v["n"], 1) if v["n"] else None}
        for st, v in sorted(por_status.items(), key=lambda kv: -kv[1]["leads"])
    ]
    motivo = [{"motivo": m, "leads": n} for m, n in sorted(motivos.items(), key=lambda kv: -kv[1])]
    origem = [{"origem": o, **v} for o, v in sorted(origens.items(), key=lambda kv: -kv[1]["leads"])]
    return status, motivo, origem


def dados_painel(ano_leads=2026):
    em = equip_mes()
    det = leads_det(ano_leads)
    status, motivo, origem = leads_resumo(det)
    return {
        "equip_mes": em,
        "mensal": mensal(em),
        "segmentos_2025": segmentos(em, "2025"),
        "faturas_ano": faturas_ano(),
        "contratos_vencer": contratos_vencer(),
        "leads_det": det,
        "leads_status": status,
        "leads_motivo": motivo,
        "leads_origem": origem,
    }
