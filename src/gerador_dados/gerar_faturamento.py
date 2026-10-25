"""Gera a tabela faturamento da LocaMaq (dados 100% ficticios).

Depende de:
    data/processed/contratos_locacao.csv
Rode gerar_contratos_locacao.py primeiro.

Saidas:
    data/raw/faturamento.csv        com sujeira proposital (entrada do Power Query)
    data/processed/faturamento.csv  versao limpa (gabarito para validar o Power Query)

Como rodar, a partir da raiz do repositorio:
    python src/gerador_dados/gerar_faturamento.py

Reprodutibilidade: a seed e fixa (42). Rodar de novo gera exatamente os mesmos arquivos,
desde que contratos_locacao.csv (processed) nao mude.
Colunas e sujeira prevista: docs/dicionario_dados.csv.

Logica: contratos Cancelado nunca saíram do pátio, não faturam. Contratos Mensal geram
UMA fatura por mês de duração (simplificação: cada mês fatura o valor_mensal cheio, sem
pró-rata no mês parcial). Contratos Semanal/Diária geram UMA fatura única (valor_diaria x
dias de contrato). O status_pagamento é decidido simulando o comportamento de pagamento
do cliente e comparando com o "hoje" do histórico (FIM_HISTORICO) - mesma lógica de
"Ativo"/"Aberta" usada nos outros geradores para dados ainda em aberto na data do corte.
"""
import calendar
import csv
import random
from datetime import date, timedelta
from pathlib import Path

from utils import formatar_real, gravar_csv

SEED = 42

INICIO_HISTORICO = date(2024, 1, 1)
FIM_HISTORICO = date(2025, 12, 31)

RAIZ = Path(__file__).resolve().parents[2]
ARQ_CONTRATOS = RAIZ / "data" / "processed" / "contratos_locacao.csv"
ARQ_RAW = RAIZ / "data" / "raw" / "faturamento.csv"
ARQ_PROCESSED = RAIZ / "data" / "processed" / "faturamento.csv"

COLUNAS = [
    "id_fatura", "id_contrato", "competencia", "valor_faturado", "data_emissao",
    "data_vencimento", "data_pagamento", "status_pagamento",
]

PRAZO_VENCIMENTO_MENSAL = (10, 20)   # dias entre emissão e vencimento (contratos Mensal)
PRAZO_VENCIMENTO_CURTO = (5, 15)     # idem para Semanal/Diária (contrato mais curto)

# Comportamento de pagamento do cliente: (probabilidade, faixa de atraso em dias vs. vencimento)
# "paga em dia" pode até pagar um pouco antes (atraso negativo).
COMPORTAMENTO_PAGAMENTO = [
    (0.80, (-5, 3)),    # paga no prazo
    (0.10, (10, 45)),   # paga atrasado
    (0.10, None),       # não paga dentro da janela do histórico
]

# --- Sujeira (só vai para o raw) -----------------------------------------------------------
P_COMPETENCIA_SUJA = 0.40        # "2025-03" -> "03/2025"
P_DATA_ISO = 0.35                # data como aaaa-mm-dd (o resto vem como dd/mm/aaaa)
P_VALOR_COM_REAL = 0.55          # "R$ 28.000,00" em vez de "28000.00"
P_STATUS_SUJO = 0.20             # caixa mista


def carregar_csv(caminho):
    with open(caminho, encoding="utf-8-sig", newline="") as arquivo:
        return list(csv.DictReader(arquivo, delimiter=";"))


def adicionar_meses(data_base, meses):
    mes_total = data_base.month - 1 + meses
    ano = data_base.year + mes_total // 12
    mes = mes_total % 12 + 1
    ultimo_dia_mes = calendar.monthrange(ano, mes)[1]
    dia = min(data_base.day, ultimo_dia_mes)
    return date(ano, mes, dia)


def sortear_pagamento(rng, data_vencimento):
    """Decide se/quando o cliente paga. Retorna (status, data_pagamento)."""
    sorteio = rng.random()
    acumulado = 0.0
    atraso_intervalo = None
    for probabilidade, intervalo in COMPORTAMENTO_PAGAMENTO:
        acumulado += probabilidade
        if sorteio < acumulado:
            atraso_intervalo = intervalo
            break

    data_pagamento_real = None
    if atraso_intervalo is not None:
        atraso = rng.randint(*atraso_intervalo)
        data_pagamento_real = data_vencimento + timedelta(days=atraso)

    if data_pagamento_real is not None and data_pagamento_real <= FIM_HISTORICO:
        return "Pago", data_pagamento_real
    if data_vencimento < FIM_HISTORICO:
        return "Vencido", None
    return "Em aberto", None


# --- Gerar as faturas de UM contrato -------------------------------------------------------
def gerar_faturas_contrato(rng, contrato):
    if contrato["status"] == "Cancelado":
        return []  # nunca saiu do pátio - não há o que faturar

    data_inicio = date.fromisoformat(contrato["data_inicio"])
    data_fim = date.fromisoformat(contrato["data_devolucao"] or contrato["data_fim_prevista"])
    faturas = []

    if contrato["modalidade"] == "Mensal":
        duracao_dias = max((data_fim - data_inicio).days, 1)
        num_meses = max(round(duracao_dias / 30), 1)
        valor_mensal = float(contrato["valor_mensal"])
        for indice in range(num_meses):
            periodo_inicio = adicionar_meses(data_inicio, indice)
            competencia = date(periodo_inicio.year, periodo_inicio.month, 1)
            data_emissao = adicionar_meses(data_inicio, indice + 1) + timedelta(days=rng.randint(0, 5))
            data_vencimento = data_emissao + timedelta(days=rng.randint(*PRAZO_VENCIMENTO_MENSAL))
            status, data_pagamento = sortear_pagamento(rng, data_vencimento)
            faturas.append({
                "id_contrato": contrato["id_contrato"],
                "competencia": competencia,
                "valor_faturado": round(valor_mensal, 2),
                "data_emissao": data_emissao,
                "data_vencimento": data_vencimento,
                "data_pagamento": data_pagamento,
                "status_pagamento": status,
            })
    else:
        duracao_dias = max((data_fim - data_inicio).days, 1)
        valor_total = float(contrato["valor_diaria"]) * duracao_dias
        competencia = date(data_inicio.year, data_inicio.month, 1)
        data_emissao = data_fim + timedelta(days=rng.randint(0, 5))
        data_vencimento = data_emissao + timedelta(days=rng.randint(*PRAZO_VENCIMENTO_CURTO))
        status, data_pagamento = sortear_pagamento(rng, data_vencimento)
        faturas.append({
            "id_contrato": contrato["id_contrato"],
            "competencia": competencia,
            "valor_faturado": round(valor_total, 2),
            "data_emissao": data_emissao,
            "data_vencimento": data_vencimento,
            "data_pagamento": data_pagamento,
            "status_pagamento": status,
        })
    return faturas


def gerar_faturas_limpo(rng, contratos):
    faturas = []
    for contrato in contratos:
        faturas.extend(gerar_faturas_contrato(rng, contrato))
    rng.shuffle(faturas)
    for numero, fatura in enumerate(faturas, start=1):
        fatura["id_fatura"] = f"FT-{numero:06d}"
    return faturas


# --- Versão processed (limpa) -------------------------------------------------------------
def formatar_processed(fatura):
    return {
        "id_fatura": fatura["id_fatura"],
        "id_contrato": fatura["id_contrato"],
        "competencia": fatura["competencia"].strftime("%Y-%m"),
        "valor_faturado": f"{fatura['valor_faturado']:.2f}",
        "data_emissao": fatura["data_emissao"].isoformat(),
        "data_vencimento": fatura["data_vencimento"].isoformat(),
        "data_pagamento": "" if fatura["data_pagamento"] is None else fatura["data_pagamento"].isoformat(),
        "status_pagamento": fatura["status_pagamento"],
    }


# --- Versão raw (aplica a sujeira prevista no dicionário) --------------------------------
def sujar_linha(rng, fatura):
    competencia = fatura["competencia"].strftime("%Y-%m")
    if rng.random() < P_COMPETENCIA_SUJA:
        competencia = fatura["competencia"].strftime("%m/%Y")

    def formatar_data(data_valor):
        if data_valor is None:
            return ""
        return data_valor.isoformat() if rng.random() < P_DATA_ISO else data_valor.strftime("%d/%m/%Y")

    valor_faturado = fatura["valor_faturado"]
    valor_texto = formatar_real(valor_faturado) if rng.random() < P_VALOR_COM_REAL else f"{valor_faturado:.2f}"

    status = fatura["status_pagamento"]
    if rng.random() < P_STATUS_SUJO:
        status = rng.choice([status.upper(), status.lower()])

    return {
        "id_fatura": fatura["id_fatura"],
        "id_contrato": fatura["id_contrato"],
        "competencia": competencia,
        "valor_faturado": valor_texto,
        "data_emissao": formatar_data(fatura["data_emissao"]),
        "data_vencimento": formatar_data(fatura["data_vencimento"]),
        "data_pagamento": formatar_data(fatura["data_pagamento"]),
        "status_pagamento": status,
    }


def main():
    rng = random.Random(SEED)  # gerador de números aleatórios próprio, sempre iniciado com 42
    contratos = carregar_csv(ARQ_CONTRATOS)

    faturas = gerar_faturas_limpo(rng, contratos)
    processed = [formatar_processed(f) for f in faturas]
    raw = [sujar_linha(rng, f) for f in faturas]

    ARQ_RAW.parent.mkdir(parents=True, exist_ok=True)
    ARQ_PROCESSED.parent.mkdir(parents=True, exist_ok=True)
    gravar_csv(ARQ_RAW, COLUNAS, raw)
    gravar_csv(ARQ_PROCESSED, COLUNAS, processed)

    contagem_status = {}
    for linha in processed:
        contagem_status[linha["status_pagamento"]] = contagem_status.get(linha["status_pagamento"], 0) + 1

    print(f"raw:       {len(raw)} linhas -> {ARQ_RAW.relative_to(RAIZ)}")
    print(f"processed: {len(processed)} linhas -> {ARQ_PROCESSED.relative_to(RAIZ)}")
    print(f"status_pagamento: {contagem_status}")
    print("\nAmostra do raw:")
    for linha in raw[:6]:
        print("  " + " | ".join(linha[coluna] for coluna in COLUNAS))


if __name__ == "__main__":
    main()
