"""Confere a extensao 2026 (data/processed/extensao_2026/) de forma independente do gerador.

Le os CSVs de novo, sem importar nada de src/gerador_dados/, e verifica:
  - base 2024-2025 intacta (contagem de linhas dos CSVs originais);
  - ids novos sem colisao e continuando a numeracao da base;
  - cada contrato novo: cliente e maquina existem, maquina Ativa e ja adquirida, datas e status coerentes;
  - nenhuma maquina com dois contratos sobrepostos (folga de 3 dias) nem em OS aberta no fim de 2025;
  - 5 ou mais contratos fechados por categoria;
  - leads: status validos (os da lista da planilha), 1 lead Fechado por contrato, datas em ordem,
    3 ou mais perdidos por categoria, 2 ou mais por indisponibilidade em cada uma;
  - a PROVA de cada perda por indisponibilidade: todas as unidades ativas do modelo estavam
    alugadas na data em que o lead chegou e nos 7 dias seguintes a data pretendida;
  - faturas: so de contratos novos nao cancelados, sem emissao depois de "hoje".
Nao altera nenhum arquivo.

Como rodar, a partir da raiz do repositorio (depois de gerar_extensao_2026.py):
    python tests/conferir_extensao_2026.py

Sai com codigo 0 se tudo bate e 1 se algo diverge.
"""
import csv
import re
import sys
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
PROCESSED = RAIZ / "data" / "processed"
EXTENSAO = PROCESSED / "extensao_2026"

sys.stdout.reconfigure(encoding="utf-8")

HOJE = date(2026, 11, 5)
FIM_ATIVOS_2025 = date(2026, 1, 31)
FIM_OS_ABERTAS = date(2026, 1, 20)
FOLGA = 3
STATUS_LEAD = {"Novo", "Em Contato", "Orçado", "Fechado", "Perdidos"}
ABERTOS = {"Novo", "Em Contato", "Orçado"}
MOTIVO_INDISPONIVEL = "Indisponibilidade de máquina"
LINHAS_BASE = {"contratos_locacao.csv": 1210, "faturamento.csv": 2487}

falhas = []


def conferir(descricao, condicao, detalhe=""):
    if condicao:
        print(f"OK     {descricao}" + (f": {detalhe}" if detalhe != "" else ""))
    else:
        print(f"FALHA  {descricao}" + (f": {detalhe}" if detalhe != "" else ""))
        falhas.append(descricao)


def ler(pasta, nome):
    with open(pasta / nome, encoding="utf-8-sig", newline="") as arq:
        return list(csv.DictReader(arq, delimiter=";"))


def dia(texto):
    return date.fromisoformat(texto) if texto else None


def numero(id_texto):
    return int(re.search(r"(\d+)$", id_texto).group(1))


# --- Dados ----------------------------------------------------------------------------------
equipamentos = {e["id_equipamento"]: e for e in ler(PROCESSED, "cadastro_equipamentos.csv")}
clientes = {c["id_cliente"] for c in ler(PROCESSED, "clientes.csv")}
base_contratos = ler(PROCESSED, "contratos_locacao.csv")
base_faturas = ler(PROCESSED, "faturamento.csv")
ordens = ler(PROCESSED, "ordens_manutencao.csv")
contratos = ler(EXTENSAO, "contratos_locacao_2026.csv")
faturas = ler(EXTENSAO, "faturamento_2026.csv")
leads = ler(EXTENSAO, "leads_2026.csv")

# --- Base 2024-2025 intacta -------------------------------------------------------------------
conferir("contratos_locacao.csv da base sem mudança", len(base_contratos) == LINHAS_BASE["contratos_locacao.csv"],
         f"{len(base_contratos)} linhas")
conferir("faturamento.csv da base sem mudança", len(base_faturas) == LINHAS_BASE["faturamento.csv"],
         f"{len(base_faturas)} linhas")
conferir("base não tem contrato iniciado em 2026",
         all(not c["data_inicio"].startswith("2026") for c in base_contratos))

# --- Ids ------------------------------------------------------------------------------------
ids_contrato = [c["id_contrato"] for c in contratos]
conferir("ids de contrato únicos", len(set(ids_contrato)) == len(ids_contrato))
maior_base = max(numero(c["id_contrato"]) for c in base_contratos)
conferir("ids de contrato continuam a base", sorted(map(numero, ids_contrato)) == list(range(maior_base + 1, maior_base + 1 + len(contratos))),
         f"CT-{maior_base + 1:05d} a CT-{maior_base + len(contratos):05d}")
ids_fatura = [f["id_fatura"] for f in faturas]
conferir("ids de fatura únicos e sem colisão com a base",
         len(set(ids_fatura)) == len(ids_fatura) and not set(ids_fatura) & {f["id_fatura"] for f in base_faturas})

# --- Contratos ------------------------------------------------------------------------------
problemas = []
for c in contratos:
    eq = equipamentos.get(c["id_equipamento"])
    inicio, fim = dia(c["data_inicio"]), dia(c["data_fim_prevista"])
    devolucao = dia(c["data_devolucao"])
    if c["id_cliente"] not in clientes:
        problemas.append((c["id_contrato"], "cliente inexistente"))
    if eq is None:
        problemas.append((c["id_contrato"], "máquina inexistente"))
        continue
    if eq["status_cadastro"] != "Ativo":
        problemas.append((c["id_contrato"], f"máquina {eq['status_cadastro']}"))
    if dia(eq["data_aquisicao"]) > inicio:
        problemas.append((c["id_contrato"], "máquina adquirida depois do início"))
    if not (date(2026, 1, 1) <= inicio <= HOJE - timedelta(days=15)):
        problemas.append((c["id_contrato"], f"início fora do esperado: {inicio}"))
    if fim <= inicio:
        problemas.append((c["id_contrato"], "fim previsto não é depois do início"))
    if c["status"] == "Encerrado":
        if devolucao is None or not (inicio < devolucao < HOJE):
            problemas.append((c["id_contrato"], f"Encerrado com devolução inválida: {devolucao}"))
    elif c["status"] == "Ativo":
        if devolucao is not None or fim < HOJE - timedelta(days=5):
            problemas.append((c["id_contrato"], "Ativo incoerente (devolução ou fim previsto)"))
    else:
        problemas.append((c["id_contrato"], f"status inesperado: {c['status']}"))
    if c["modalidade"] == "Mensal":
        if not c["valor_mensal"] or c["valor_diaria"]:
            problemas.append((c["id_contrato"], "Mensal deve ter só valor_mensal"))
    elif not c["valor_diaria"] or c["valor_mensal"]:
        problemas.append((c["id_contrato"], f"{c['modalidade']} deve ter só valor_diaria"))
conferir("contratos novos coerentes (cliente, máquina ativa, datas, status, valores)", not problemas,
         f"{len(contratos)} contratos" if not problemas else str(problemas[:3]))

# --- Sem sobreposição de máquina (contratos da base + novos + OS abertas) ------------------------
ocupacao = defaultdict(list)
for c in base_contratos:
    if c["status"] == "Cancelado":
        continue
    fim = FIM_ATIVOS_2025 if c["status"] == "Ativo" else dia(c["data_devolucao"] or c["data_fim_prevista"])
    ocupacao[c["id_equipamento"]].append((dia(c["data_inicio"]), fim, c["id_contrato"]))
for o in ordens:
    if o["status_os"] in ("Aberta", "Em andamento"):
        ocupacao[o["id_equipamento"]].append((dia(o["data_abertura"]), FIM_OS_ABERTAS, o["id_os"]))
novos_por_maquina = defaultdict(list)
for c in contratos:
    fim_efetivo = dia(c["data_devolucao"]) or dia(c["data_fim_prevista"])
    ocupacao[c["id_equipamento"]].append((dia(c["data_inicio"]), fim_efetivo, c["id_contrato"]))
    novos_por_maquina[c["id_equipamento"]].append(c["id_contrato"])
sobrepostos = []
for id_maquina, ids_novos in novos_por_maquina.items():
    # Cada contrato novo contra TUDO o que ocupa a máquina (contratos da base, OS abertas e outros novos).
    # Pares só da base (ex.: um contrato antigo com uma OS aberta) não são problema da extensão.
    for i1, f1, r1 in ocupacao[id_maquina]:
        if r1 not in ids_novos:
            continue
        for i2, f2, r2 in ocupacao[id_maquina]:
            if r2 == r1:
                continue
            if i1 <= f2 + timedelta(days=FOLGA) and f1 + timedelta(days=FOLGA) >= i2:
                sobrepostos.append((id_maquina, r1, r2))
conferir("nenhum contrato novo sobreposto a outro contrato ou a OS aberta", not sobrepostos,
         f"{len(novos_por_maquina)} máquinas conferidas" if not sobrepostos else str(sobrepostos[:3]))

# --- Contratos por categoria ------------------------------------------------------------------
fechados_por_categoria = Counter(equipamentos[c["id_equipamento"]]["segmento"] for c in contratos)
todas_categorias = {e["segmento"] for e in equipamentos.values() if e["status_cadastro"] == "Ativo"}
conferir("5 ou mais contratos fechados em cada categoria",
         set(fechados_por_categoria) == todas_categorias and min(fechados_por_categoria.values()) >= 5,
         str(dict(fechados_por_categoria)))

# --- Faturas ------------------------------------------------------------------------------------
contratos_por_id = {c["id_contrato"]: c for c in contratos}
conferir("faturas só de contratos novos", all(f["id_contrato"] in contratos_por_id for f in faturas))
conferir("nenhuma fatura emitida depois de hoje", all(dia(f["data_emissao"]) <= HOJE for f in faturas))
conferir("status de pagamento coerente com hoje",
         all((f["status_pagamento"] == "Pago") == bool(f["data_pagamento"]) for f in faturas)
         and all(dia(f["data_pagamento"]) <= HOJE for f in faturas if f["data_pagamento"])
         and all(dia(f["data_vencimento"]) < HOJE for f in faturas if f["status_pagamento"] == "Vencido")
         and all(dia(f["data_vencimento"]) >= HOJE for f in faturas if f["status_pagamento"] == "Em aberto"),
         str(dict(Counter(f["status_pagamento"] for f in faturas))))
conferir("todo contrato Encerrado tem fatura",
         all(any(f["id_contrato"] == c["id_contrato"] for f in faturas) for c in contratos if c["status"] == "Encerrado"))

# --- Leads ------------------------------------------------------------------------------------------
conferir("status dos leads são os da lista da planilha", {l["status"] for l in leads} <= STATUS_LEAD,
         str(dict(Counter(l["status"] for l in leads))))
conferir("toda observação traz a marca de histórico fictício", all(l["observacao"].startswith("[histórico fictício]") for l in leads))
conferir("contatos fictícios (e-mail .example ou telefone inexistente)",
         all(re.fullmatch(r"[a-z0-9-]+@[a-z0-9-]+\.example|\(\d\d\) 00000-\d{4}", l["contato"]) for l in leads))

fechados = [l for l in leads if l["status"] == "Fechado"]
conferir("um lead Fechado para cada contrato novo, sem repetir",
         sorted(l["id_contrato"] for l in fechados) == sorted(ids_contrato))
erros_datas = []
for l in leads:
    envio = datetime.fromisoformat(l["data_envio"])
    desfecho = dia(l["data_desfecho"])
    if envio > datetime(2026, 11, 5, 23, 59, 59) or envio.year != 2026:
        erros_datas.append((l["nome"], "envio fora de 2026 ou no futuro"))
    if l["status"] in ABERTOS:
        if desfecho or l["motivo_perda"] or l["id_contrato"]:
            erros_datas.append((l["nome"], "lead em aberto com desfecho"))
    else:
        if desfecho is None or desfecho < envio.date() or desfecho > HOJE:
            erros_datas.append((l["nome"], "desfecho antes do envio ou no futuro"))
    if l["status"] == "Fechado":
        c = contratos_por_id[l["id_contrato"]]
        if not (envio.date() < dia(c["data_inicio"]) and desfecho <= dia(c["data_inicio"])):
            erros_datas.append((l["id_contrato"], "envio/desfecho depois do início do contrato"))
        if l["motivo_perda"]:
            erros_datas.append((l["id_contrato"], "Fechado com motivo de perda"))
    if l["status"] == "Perdidos" and (not l["motivo_perda"] or l["id_contrato"]):
        erros_datas.append((l["nome"], "Perdido sem motivo ou com contrato"))
conferir("datas e campos dos leads coerentes com o status", not erros_datas, str(erros_datas[:3]) if erros_datas else "")
conferir("10 ou mais leads em aberto", sum(1 for l in leads if l["status"] in ABERTOS) >= 10,
         str(sum(1 for l in leads if l["status"] in ABERTOS)))

categoria_do_lead = lambda l: l["equipamento"].split(" – ")[0]
perdidos = Counter(categoria_do_lead(l) for l in leads if l["status"] == "Perdidos")
indisponiveis = Counter(categoria_do_lead(l) for l in leads if l["motivo_perda"] == MOTIVO_INDISPONIVEL)
conferir("3 ou mais leads perdidos em cada categoria",
         set(perdidos) == todas_categorias and min(perdidos.values()) >= 3, str(dict(perdidos)))
conferir("2 ou mais perdas por indisponibilidade em cada categoria",
         set(indisponiveis) == todas_categorias and min(indisponiveis.values()) >= 2, str(dict(indisponiveis)))

# --- Prova da indisponibilidade ------------------------------------------------------------------------
falhas_prova = []
for l in leads:
    if l["motivo_perda"] != MOTIVO_INDISPONIVEL:
        continue
    segmento, resto = l["equipamento"].split(" – ", 1)
    unidades = [e["id_equipamento"] for e in equipamentos.values()
                if e["status_cadastro"] == "Ativo" and e["segmento"] == segmento
                and f"{e['fabricante']} {e['modelo']}" == resto]
    envio = datetime.fromisoformat(l["data_envio"]).date()
    pretendido = dia(l["inicio_pretendido"])
    if not unidades or pretendido is None:
        falhas_prova.append((l["nome"], "modelo ou data pretendida não encontrados"))
        continue
    for unidade in unidades:
        cobertura = [
            r for (i, f, r) in ocupacao[unidade]
            if i <= envio and f >= pretendido + timedelta(days=7) and r in contratos_por_id
        ]
        if not cobertura:
            falhas_prova.append((l["nome"], f"{unidade} estava livre em {envio}..{pretendido + timedelta(days=7)}"))
            break
n_prova = sum(1 for l in leads if l["motivo_perda"] == MOTIVO_INDISPONIVEL)
conferir("perdas por indisponibilidade provadas (todas as unidades do modelo alugadas)", not falhas_prova and n_prova >= 14,
         f"{n_prova} leads" if not falhas_prova else str(falhas_prova[:3]))

print()
if falhas:
    print(f"{len(falhas)} verificação(ões) falharam: {falhas}")
    sys.exit(1)
print("Todas as verificações passaram.")
