"""Gera a tabela horimetro_telemetria da LocaMaq (dados 100% ficticios).

Depende de:
    data/processed/cadastro_equipamentos.csv
    data/processed/contratos_locacao.csv
Rode gerar_cadastro_equipamentos.py e gerar_contratos_locacao.py primeiro.

Saidas:
    data/raw/horimetro_telemetria.csv        com sujeira proposital (entrada do Power Query)
    data/processed/horimetro_telemetria.csv  versao limpa (gabarito para validar o Power Query)

Como rodar, a partir da raiz do repositorio:
    python src/gerador_dados/gerar_horimetro_telemetria.py

Reprodutibilidade: a seed e fixa (42). Rodar de novo gera exatamente os mesmos arquivos,
desde que cadastro_equipamentos.csv e contratos_locacao.csv (processed) nao mudem.
Colunas e sujeira prevista: docs/dicionario_dados.csv.

Logica: simula, dia a dia, o horimetro acumulado de cada equipamento - mais horas por dia
quando ha um contrato vigente naquele dia, poucas horas quando esta parado no patio (testes,
manutencao, aquecimento). Sorteia leituras periodicas desse historico simulado: mais
frequentes para equipamentos com fonte_leitura=Telemetria, mais esparsas para Manual (cada
equipamento tem uma fonte fixa, sorteada uma vez - simplificacao: nenhuma maquina troca de
fonte no meio do periodo). "Lacunas" entre leituras são naturais da amostragem periódica,
não é algo só do raw. id_contrato na leitura é o contrato vigente naquele dia, ou vazio se a
maquina estava no patio - contratos "Cancelado" não contam como uso (igual ao gerador de
contratos_locacao: a maquina nunca saiu do patio nesse caso).
"""
import csv
import random
from datetime import date, timedelta
from pathlib import Path

from utils import construir_intervalos_contrato, contrato_vigente, gravar_csv

SEED = 42

# Mesma janela de historico das outras tabelas (24 meses).
INICIO_HISTORICO = date(2024, 1, 1)
FIM_HISTORICO = date(2025, 12, 31)

RAIZ = Path(__file__).resolve().parents[2]
ARQ_EQUIPAMENTOS = RAIZ / "data" / "processed" / "cadastro_equipamentos.csv"
ARQ_CONTRATOS = RAIZ / "data" / "processed" / "contratos_locacao.csv"
ARQ_RAW = RAIZ / "data" / "raw" / "horimetro_telemetria.csv"
ARQ_PROCESSED = RAIZ / "data" / "processed" / "horimetro_telemetria.csv"

COLUNAS = [
    "id_leitura", "id_equipamento", "data_leitura", "horimetro_horas", "fonte_leitura",
    "id_contrato",
]

P_TELEMETRIA = 0.35               # fração da frota com telemetria (resto é leitura manual)
INTERVALO_LEITURA_TELEMETRIA = (2, 5)   # dias entre leituras automáticas
INTERVALO_LEITURA_MANUAL = (20, 40)     # dias entre leituras manuais (menos frequente)

HORAS_DIA_ATIVO = (5.0, 10.0)      # uso diário quando há contrato vigente
HORAS_DIA_PATIO = (0.0, 1.0)       # uso diário quando a máquina está parada no pátio
MEDIA_HORAS_ANO_ANTES_HISTORICO = 1300  # para estimar o horímetro inicial de máquinas antigas

# --- Sujeira (só vai para o raw) -----------------------------------------------------------
P_ID_EQUIPAMENTO_SUJO = 0.20   # minúsculo
P_FONTE_SUJA = 0.20            # caixa mista
P_DATA_ISO = 0.35              # data como aaaa-mm-dd (o resto vem como dd/mm/aaaa)
P_HORIMETRO_DIMINUI = 0.04     # erro de digitação: leitura menor que a anterior da mesma máquina


def carregar_csv(caminho):
    with open(caminho, encoding="utf-8-sig", newline="") as arquivo:
        return list(csv.DictReader(arquivo, delimiter=";"))


def horas_iniciais(equipamento, rng):
    """Estima quantas horas a máquina já tinha acumulado antes do início do histórico."""
    data_aquisicao = date.fromisoformat(equipamento["data_aquisicao"])
    if data_aquisicao >= INICIO_HISTORICO:
        return rng.uniform(0, 40)  # máquina nova: só horas de teste/entrega
    anos_antes = (INICIO_HISTORICO - data_aquisicao).days / 365
    return max(0.0, anos_antes * MEDIA_HORAS_ANO_ANTES_HISTORICO * rng.uniform(0.7, 1.3))


# --- Passo 2: simular dia a dia e sortear as leituras de UM equipamento -------------------
def simular_leituras_equipamento(rng, equipamento, intervalos_equipamento):
    data_aquisicao = date.fromisoformat(equipamento["data_aquisicao"])
    dia = max(INICIO_HISTORICO, data_aquisicao)
    horimetro = horas_iniciais(equipamento, rng)

    telemetria = rng.random() < P_TELEMETRIA
    fonte_leitura = "Telemetria" if telemetria else "Manual"
    intervalo = INTERVALO_LEITURA_TELEMETRIA if telemetria else INTERVALO_LEITURA_MANUAL

    leituras = []
    proxima_leitura = dia + timedelta(days=rng.randint(*intervalo))
    while dia <= FIM_HISTORICO:
        id_contrato = contrato_vigente(intervalos_equipamento, dia)
        incremento = rng.uniform(*HORAS_DIA_ATIVO) if id_contrato else rng.uniform(*HORAS_DIA_PATIO)
        horimetro += incremento

        if dia >= proxima_leitura:
            leituras.append({
                "id_equipamento": equipamento["id_equipamento"],
                "data_leitura": dia,
                "horimetro_horas": round(horimetro, 1),
                "fonte_leitura": fonte_leitura,
                "id_contrato": id_contrato,
            })
            proxima_leitura = dia + timedelta(days=rng.randint(*intervalo))
        dia += timedelta(days=1)
    return leituras


def gerar_leituras_limpo(rng, equipamentos, intervalos):
    """Retorna {id_equipamento: [leituras cronológicas]} e já atribui id_leitura sequencial."""
    leituras_por_equipamento = {}
    numero = 1
    for equipamento in equipamentos:
        leituras = simular_leituras_equipamento(
            rng, equipamento, intervalos.get(equipamento["id_equipamento"], [])
        )
        for leitura in leituras:
            leitura["id_leitura"] = f"HR-{numero:06d}"
            numero += 1
        leituras_por_equipamento[equipamento["id_equipamento"]] = leituras
    return leituras_por_equipamento


# --- Passo 3: versão processed (limpa) ----------------------------------------------------
def formatar_processed(leitura):
    return {
        "id_leitura": leitura["id_leitura"],
        "id_equipamento": leitura["id_equipamento"],
        "data_leitura": leitura["data_leitura"].isoformat(),
        "horimetro_horas": f"{leitura['horimetro_horas']:.1f}",
        "fonte_leitura": leitura["fonte_leitura"],
        "id_contrato": leitura["id_contrato"] or "",
    }


# --- Passo 4: versão raw (aplica a sujeira prevista no dicionário) -----------------------
def sujar_linha(rng, leitura):
    id_equipamento = leitura["id_equipamento"]
    if rng.random() < P_ID_EQUIPAMENTO_SUJO:
        id_equipamento = id_equipamento.lower()

    fonte_leitura = leitura["fonte_leitura"]
    if rng.random() < P_FONTE_SUJA:
        fonte_leitura = rng.choice([fonte_leitura.upper(), fonte_leitura.lower()])

    data_leitura = leitura["data_leitura"]
    data_formatada = data_leitura.isoformat() if rng.random() < P_DATA_ISO else data_leitura.strftime("%d/%m/%Y")

    return {
        "id_leitura": leitura["id_leitura"],
        "id_equipamento": id_equipamento,
        "data_leitura": data_formatada,
        "horimetro_horas": f"{leitura['horimetro_horas']:.1f}",
        "fonte_leitura": fonte_leitura,
        "id_contrato": leitura["id_contrato"] or "",
    }


def gerar_raw_equipamento(rng, leituras_cronologicas):
    """Aplica a sujeira em sequência - precisa saber a leitura anterior para simular o erro
    de digitação (horímetro que diminui)."""
    linhas = []
    valor_raw_anterior = None
    for leitura in leituras_cronologicas:
        linha = sujar_linha(rng, leitura)
        if valor_raw_anterior is not None and rng.random() < P_HORIMETRO_DIMINUI:
            valor_errado = max(valor_raw_anterior - rng.uniform(20, 200), 0)
            linha["horimetro_horas"] = f"{valor_errado:.1f}"
        valor_raw_anterior = float(linha["horimetro_horas"])
        linhas.append(linha)
    return linhas


def gerar_raw(rng, leituras_por_equipamento):
    raw = []
    for leituras in leituras_por_equipamento.values():
        raw.extend(gerar_raw_equipamento(rng, leituras))
    return raw


def main():
    rng = random.Random(SEED)  # gerador de números aleatórios próprio, sempre iniciado com 42
    equipamentos = carregar_csv(ARQ_EQUIPAMENTOS)
    contratos = carregar_csv(ARQ_CONTRATOS)
    intervalos = construir_intervalos_contrato(contratos)

    leituras_por_equipamento = gerar_leituras_limpo(rng, equipamentos, intervalos)
    processed = [
        formatar_processed(leitura)
        for leituras in leituras_por_equipamento.values()
        for leitura in leituras
    ]
    raw = gerar_raw(rng, leituras_por_equipamento)

    ARQ_RAW.parent.mkdir(parents=True, exist_ok=True)
    ARQ_PROCESSED.parent.mkdir(parents=True, exist_ok=True)
    gravar_csv(ARQ_RAW, COLUNAS, raw)
    gravar_csv(ARQ_PROCESSED, COLUNAS, processed)

    print(f"raw:       {len(raw)} linhas -> {ARQ_RAW.relative_to(RAIZ)}")
    print(f"processed: {len(processed)} linhas -> {ARQ_PROCESSED.relative_to(RAIZ)}")
    n_telemetria = sum(1 for ls in leituras_por_equipamento.values() if ls and ls[0]["fonte_leitura"] == "Telemetria")
    print(f"equipamentos com telemetria: {n_telemetria} de {len(equipamentos)}")
    print("\nAmostra do raw:")
    for linha in raw[:6]:
        print("  " + " | ".join(linha[coluna] for coluna in COLUNAS))


if __name__ == "__main__":
    main()
