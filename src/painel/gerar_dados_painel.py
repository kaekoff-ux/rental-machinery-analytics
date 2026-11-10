"""Gera painel/dados.js, os dados do painel de consulta da LocaMaq (GitHub Pages).

Uso, na raiz do repositório:  python src/painel/gerar_dados_painel.py
Só usa a biblioteca padrão. Lê data/processed/ (e a extensão 2026) e grava três tabelas,
as mesmas do dashboard do Cowork de 09/11/2026:

- equip_mes: uma linha por máquina e mês (2024-2025) com receita, dias locados, horas,
  paradas, OS por tipo, custos e faturas vencidas;
- os_det: uma linha por ordem de serviço;
- leads_det: um lead de 2026 por linha, sem nome nem contato.

Regras (conferidas contra os CSVs do Cowork por tests/conferir_painel.py):
- receita, vencido e atraso: faturas pela competência, na máquina do contrato;
- dias_locados: do início à devolução (ou ao fim previsto, se ativo), último dia incluído,
  sem contratos cancelados; dias_frota: dias desde a aquisição; horas_periodo = dias × 24;
- OS (quantidade, horas paradas, custo): pelo mês de abertura; os_corretiva_h conta só as
  corretivas com horas paradas registradas (base do MTTR);
- horas_trab: cada intervalo do horímetro conta no mês da leitura seguinte; o trecho antes da
  primeira leitura é estimado pela taxa do primeiro intervalo; depreciação = horas × valor ÷
  vida útil.
Todos os dados são fictícios; o arquivo gerado é público no GitHub Pages.
"""
import csv
import json
import re
from collections import defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
DADOS = RAIZ / "data" / "processed"
SAIDA = RAIZ / "painel" / "dados.js"
INICIO, FIM = date(2024, 1, 1), date(2025, 12, 31)

METRICAS = [
    "receita", "dias_locados", "dias_frota", "horas_periodo", "horas_parada", "horas_trab", "custo_manut",
    "depreciacao", "os_preventiva", "os_preditiva", "os_corretiva", "os_corretiva_h", "horas_parada_corretiva",
    "vencido", "atraso_soma", "atraso_n",
]


def ler(nome):
    with open(DADOS / nome, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f, delimiter=";"))


def num(v):
    return float(v) if v not in ("", None) else 0.0


def dia(v):
    return date.fromisoformat(v) if v else None


def mes(d):
    return f"{d.year:04d}-{d.month:02d}"


def somar_dias(inicio, fim, acum, chave, campo):
    """Soma os dias de [inicio, fim] (fim incluído) dentro da janela, mês a mês."""
    d, b = max(inicio, INICIO), min(fim, FIM)
    while d <= b:
        prox = date(d.year + (d.month == 12), d.month % 12 + 1, 1)
        ate = min(b, prox - timedelta(days=1))
        acum[(chave, mes(d))][campo] += (ate - d).days + 1
        d = prox


def equip_mes(eqs, contratos, faturas, ordens, leituras):
    por_eq = {e["id_equipamento"]: e for e in eqs}
    linhas = defaultdict(lambda: defaultdict(float))
    for e in eqs:
        somar_dias(dia(e["data_aquisicao"]), FIM, linhas, e["id_equipamento"], "dias_frota")
    for c in contratos:
        if c["status"] == "Cancelado":
            continue
        fim = dia(c["data_devolucao"]) or min(dia(c["data_fim_prevista"]), FIM)
        somar_dias(dia(c["data_inicio"]), fim, linhas, c["id_equipamento"], "dias_locados")
    eq_do_contrato = {c["id_contrato"]: c["id_equipamento"] for c in contratos}
    for f in faturas:
        if not ("2024-01" <= f["competencia"] <= "2025-12"):
            continue
        lin = linhas[(eq_do_contrato[f["id_contrato"]], f["competencia"])]
        valor = num(f["valor_faturado"])
        lin["receita"] += valor
        if f["status_pagamento"] == "Vencido":
            lin["vencido"] += valor
        pago, venc = dia(f["data_pagamento"]), dia(f["data_vencimento"])
        if pago and pago > venc:
            lin["atraso_soma"] += (pago - venc).days
            lin["atraso_n"] += 1
    tipo = {"Preventiva": "os_preventiva", "Preditiva": "os_preditiva", "Corretiva": "os_corretiva"}
    for o in ordens:
        aberta = dia(o["data_abertura"])
        if not (INICIO <= aberta <= FIM):
            continue
        lin = linhas[(o["id_equipamento"], mes(aberta))]
        lin["horas_parada"] += num(o["horas_parada"])
        lin["custo_manut"] += num(o["custo_pecas"]) + num(o["custo_mao_obra"])
        lin[tipo[o["tipo_manutencao"]]] += 1
        if o["tipo_manutencao"] == "Corretiva":
            lin["horas_parada_corretiva"] += num(o["horas_parada"])
            if o["horas_parada"] != "":
                lin["os_corretiva_h"] += 1
    por_maquina = defaultdict(list)
    for r in leituras:
        d = dia(r["data_leitura"])
        if INICIO <= d <= FIM:
            por_maquina[r["id_equipamento"]].append((d, num(r["horimetro_horas"])))
    for eq, lst in por_maquina.items():
        lst.sort()
        if len(lst) >= 2:
            (d1, h1), (d2, h2) = lst[0], lst[1]
            comeco = max(INICIO, dia(por_eq[eq]["data_aquisicao"]))
            if (d2 - d1).days > 0 and d1 > comeco:
                linhas[(eq, mes(d1))]["horas_trab"] += (h2 - h1) / (d2 - d1).days * (d1 - comeco).days
        for (_, h0), (d1, h1) in zip(lst, lst[1:]):
            linhas[(eq, mes(d1))]["horas_trab"] += max(0.0, h1 - h0)
    saida = []
    for (eq, m), lin in sorted(linhas.items()):
        e = por_eq[eq]
        lin["horas_periodo"] = lin["dias_frota"] * 24
        lin["depreciacao"] = lin["horas_trab"] * num(e["valor_aquisicao"]) / num(e["vida_util_horas"])
        saida.append([eq, m, e["segmento"], e["filial"], f'{e["fabricante"]} {e["modelo"]}']
                     + [round(lin[k], 2) for k in METRICAS])
    return ["id_equipamento", "mes", "segmento", "filial", "modelo"] + METRICAS, saida


def os_det(eqs, ordens):
    por_eq = {e["id_equipamento"]: e for e in eqs}
    colunas = ["id_os", "id_equipamento", "modelo", "segmento", "filial", "tipo", "status", "data_abertura",
               "data_conclusao", "horas_parada", "custo", "descricao_falha"]
    linhas = []
    for o in ordens:
        e = por_eq[o["id_equipamento"]]
        linhas.append([
            o["id_os"], o["id_equipamento"], f'{e["fabricante"]} {e["modelo"]}', e["segmento"], e["filial"],
            o["tipo_manutencao"], o["status_os"], o["data_abertura"], o["data_conclusao"] or None,
            num(o["horas_parada"]) if o["horas_parada"] != "" else None,
            round(num(o["custo_pecas"]) + num(o["custo_mao_obra"]), 2), o["descricao_falha"],
        ])
    return colunas, linhas


def leads_det(leads):
    colunas = ["mes_envio", "segmento", "modelo", "cidade", "origem", "status", "motivo_perda", "dias_fechamento"]
    linhas = []
    for r in sorted(leads, key=lambda r: r["data_envio"]):
        partes = re.split(r"\s+[–-]\s+", r["equipamento"].strip(), maxsplit=1)
        envio = datetime.fromisoformat(r["data_envio"]).date()
        desfecho = dia(r["data_desfecho"])
        dias = (desfecho - envio).days if r["status"] == "Fechado" and desfecho else None
        linhas.append([r["data_envio"][:7], partes[0], partes[1] if len(partes) > 1 else "Qualquer modelo",
                       r["cidade"], r["origem"], r["status"], r["motivo_perda"] or None, dias])
    return colunas, linhas


def main():
    eqs = ler("cadastro_equipamentos.csv")
    contratos = ler("contratos_locacao.csv") + ler("extensao_2026/contratos_locacao_2026.csv")
    faturas = ler("faturamento.csv") + ler("extensao_2026/faturamento_2026.csv")
    ordens = ler("ordens_manutencao.csv")
    leituras = ler("horimetro_telemetria.csv")
    tabelas = {
        "equip_mes": equip_mes(eqs, contratos, faturas, ordens, leituras),
        "os_det": os_det(eqs, ordens),
        "leads_det": leads_det(ler("extensao_2026/leads_2026.csv")),
    }
    dados = {"gerado_em": date.today().isoformat(),
             **{k: {"colunas": c, "linhas": l} for k, (c, l) in tabelas.items()}}
    texto = json.dumps(dados, ensure_ascii=False, separators=(",", ":"))
    SAIDA.parent.mkdir(parents=True, exist_ok=True)
    SAIDA.write_text(
        "// Gerado por src/painel/gerar_dados_painel.py a partir de data/processed (dados fictícios).\n"
        f"window.LOCAMAQ_DADOS = {texto};\n",
        encoding="utf-8",
    )
    for k, (_, l) in tabelas.items():
        print(f"{k}: {len(l)} linhas")
    print(f"gravado: {SAIDA.relative_to(RAIZ)} ({SAIDA.stat().st_size / 1024:.0f} KB)")


if __name__ == "__main__":
    main()
