"""Gera a tabela abastecimento da LocaMaq (dados 100% ficticios).

Depende de:
    data/processed/cadastro_equipamentos.csv
    data/processed/contratos_locacao.csv
    data/processed/horimetro_telemetria.csv
Rode os geradores anteriores primeiro (nessa ordem).

Saidas:
    data/raw/abastecimento.csv        com sujeira proposital (entrada do Power Query)
    data/processed/abastecimento.csv  versao limpa (gabarito para validar o Power Query)

Como rodar, a partir da raiz do repositorio:
    python src/gerador_dados/gerar_abastecimento.py

Reprodutibilidade: a seed e fixa (42). Rodar de novo gera exatamente os mesmos arquivos,
desde que os CSVs de que depende (processed) nao mudem.
Colunas e sujeira prevista: docs/dicionario_dados.csv.

Logica: cada segmento de equipamento tem um consumo medio (litros/hora) e uma capacidade
de tanque. Simulando o uso diario (igual ao gerador de horimetro: mais consumo com
contrato vigente, quase nada no patio), acumula litros consumidos e dispara um
abastecimento quando o tanque chegaria perto do fim.
"""
import csv
import random
from datetime import date, timedelta
from pathlib import Path

from utils import (
    construir_historico_horimetro,
    construir_intervalos_contrato,
    contrato_vigente,
    gravar_csv,
    horimetro_na_data,
)

SEED = 42

INICIO_HISTORICO = date(2024, 1, 1)
FIM_HISTORICO = date(2025, 12, 31)

RAIZ = Path(__file__).resolve().parents[2]
ARQ_EQUIPAMENTOS = RAIZ / "data" / "processed" / "cadastro_equipamentos.csv"
ARQ_CONTRATOS = RAIZ / "data" / "processed" / "contratos_locacao.csv"
ARQ_HORIMETRO = RAIZ / "data" / "processed" / "horimetro_telemetria.csv"
ARQ_RAW = RAIZ / "data" / "raw" / "abastecimento.csv"
ARQ_PROCESSED = RAIZ / "data" / "processed" / "abastecimento.csv"

COLUNAS = [
    "id_abastecimento", "id_equipamento", "data_abastecimento", "litros", "valor_litro",
    "valor_total", "horimetro_horas", "responsavel",
]

# segmento: (consumo em litros/hora ativo, capacidade do tanque em litros)
PERFIL_CONSUMO = {
    "Escavadeira": (18, 400),
    "Retroescavadeira": (14, 300),
    "Pá-carregadeira": (16, 350),
    "Guindaste": (22, 450),
    "Gerador": (8, 200),
    "Empilhadeira": (6, 100),
    "Plataforma elevatória": (4, 80),
}
CONSUMO_PATIO_FRACAO = 0.05  # no pátio, consumo residual (testes/aquecimento) é bem menor

PRECO_DIESEL_BASE = 6.00       # R$/litro no início do histórico
PRECO_DIESEL_VARIACAO_ANUAL = 0.06  # ~6% de inflação ao ano no período

RESPONSAVEIS = [
    "Marcos Silva", "Ana Souza", "Carlos Pereira", "Juliana Lima", "Roberto Santos",
    "Fernanda Costa", "Paulo Oliveira", "Camila Rocha", "Diego Alves", "Patrícia Gomes",
]

# --- Sujeira (só vai para o raw) -----------------------------------------------------------
P_ID_EQUIPAMENTO_SUJO = 0.20     # minúsculo
P_DATA_ISO = 0.35                # data como aaaa-mm-dd (o resto vem como dd/mm/aaaa)
P_DECIMAL_VIRGULA = 0.50         # litros/valor_litro com vírgula em vez de ponto
P_TOTAL_INCONSISTENTE = 0.04     # valor_total não bate com litros × valor_litro (erro de digitação)
P_HORIMETRO_NULO = 0.08          # nem todo abastecimento registra o horímetro
P_NOME_ABREVIADO = 0.35          # "Marcos Silva" -> "M. Silva"


def carregar_csv(caminho):
    with open(caminho, encoding="utf-8-sig", newline="") as arquivo:
        return list(csv.DictReader(arquivo, delimiter=";"))


def preco_diesel_na_data(rng, dia):
    """Preço base sobe com inflação simples ao longo da janela, mais um ruído diário pequeno."""
    anos_desde_inicio = (dia - INICIO_HISTORICO).days / 365
    preco_tendencia = PRECO_DIESEL_BASE * (1 + PRECO_DIESEL_VARIACAO_ANUAL) ** anos_desde_inicio
    return round(preco_tendencia * rng.uniform(0.96, 1.04), 2)


# --- Simular os abastecimentos de UM equipamento ------------------------------------------
def gerar_abastecimentos_equipamento(rng, equipamento, intervalos_contrato, historico_horimetro):
    consumo_hora, capacidade_tanque = PERFIL_CONSUMO[equipamento["segmento"]]
    data_aquisicao = date.fromisoformat(equipamento["data_aquisicao"])
    dia = max(INICIO_HISTORICO, data_aquisicao)

    litros_acumulados = rng.uniform(0, capacidade_tanque * 0.3)  # nível inicial do tanque
    limiar = capacidade_tanque * rng.uniform(0.8, 1.0)
    abastecimentos = []

    while dia <= FIM_HISTORICO:
        em_uso = contrato_vigente(intervalos_contrato.get(equipamento["id_equipamento"], []), dia) is not None
        horas_dia = rng.uniform(5.0, 10.0) if em_uso else rng.uniform(0.0, 1.0)
        fracao_patio = 1.0 if em_uso else CONSUMO_PATIO_FRACAO
        litros_acumulados += horas_dia * consumo_hora * fracao_patio

        if litros_acumulados >= limiar:
            horimetro = horimetro_na_data(historico_horimetro.get(equipamento["id_equipamento"], []), dia)
            abastecimentos.append({
                "id_equipamento": equipamento["id_equipamento"],
                "data_abastecimento": dia,
                "litros": round(litros_acumulados, 1),
                "valor_litro": preco_diesel_na_data(rng, dia),
                "horimetro_horas": horimetro,
                "responsavel": rng.choice(RESPONSAVEIS),
            })
            litros_acumulados = rng.uniform(0, capacidade_tanque * 0.1)  # sobra pequena no tanque
            limiar = capacidade_tanque * rng.uniform(0.8, 1.0)
        dia += timedelta(days=1)
    return abastecimentos


def gerar_abastecimentos_limpo(rng, equipamentos, intervalos_contrato, historico_horimetro):
    abastecimentos = []
    for equipamento in equipamentos:
        abastecimentos.extend(
            gerar_abastecimentos_equipamento(rng, equipamento, intervalos_contrato, historico_horimetro)
        )
    rng.shuffle(abastecimentos)
    for numero, abastecimento in enumerate(abastecimentos, start=1):
        abastecimento["id_abastecimento"] = f"AB-{numero:06d}"
        abastecimento["valor_total"] = round(abastecimento["litros"] * abastecimento["valor_litro"], 2)
    return abastecimentos


# --- Versão processed (limpa) -------------------------------------------------------------
def formatar_processed(abastecimento):
    return {
        "id_abastecimento": abastecimento["id_abastecimento"],
        "id_equipamento": abastecimento["id_equipamento"],
        "data_abastecimento": abastecimento["data_abastecimento"].isoformat(),
        "litros": f"{abastecimento['litros']:.1f}",
        "valor_litro": f"{abastecimento['valor_litro']:.2f}",
        "valor_total": f"{abastecimento['valor_total']:.2f}",
        "horimetro_horas": "" if abastecimento["horimetro_horas"] is None else f"{abastecimento['horimetro_horas']:.1f}",
        "responsavel": abastecimento["responsavel"],
    }


# --- Versão raw (aplica a sujeira prevista no dicionário) --------------------------------
def sujar_linha(rng, abastecimento):
    id_equipamento = abastecimento["id_equipamento"]
    if rng.random() < P_ID_EQUIPAMENTO_SUJO:
        id_equipamento = id_equipamento.lower()

    data_abastecimento = abastecimento["data_abastecimento"]
    data_formatada = (
        data_abastecimento.isoformat() if rng.random() < P_DATA_ISO
        else data_abastecimento.strftime("%d/%m/%Y")
    )

    def formatar_decimal(valor, casas):
        texto = f"{valor:.{casas}f}"
        return texto.replace(".", ",") if rng.random() < P_DECIMAL_VIRGULA else texto

    litros_texto = formatar_decimal(abastecimento["litros"], 1)
    valor_litro_texto = formatar_decimal(abastecimento["valor_litro"], 2)

    valor_total = abastecimento["valor_total"]
    if rng.random() < P_TOTAL_INCONSISTENTE:
        valor_total = round(valor_total * rng.uniform(0.85, 1.15), 2)  # não bate com litros x valor_litro
    valor_total_texto = formatar_decimal(valor_total, 2)

    horimetro_horas = abastecimento["horimetro_horas"]
    if horimetro_horas is not None and rng.random() < P_HORIMETRO_NULO:
        horimetro_horas = None
    horimetro_texto = "" if horimetro_horas is None else f"{horimetro_horas:.1f}"

    responsavel = abastecimento["responsavel"]
    if rng.random() < P_NOME_ABREVIADO:
        partes = responsavel.split()
        responsavel = f"{partes[0][0]}. {partes[-1]}"

    return {
        "id_abastecimento": abastecimento["id_abastecimento"],
        "id_equipamento": id_equipamento,
        "data_abastecimento": data_formatada,
        "litros": litros_texto,
        "valor_litro": valor_litro_texto,
        "valor_total": valor_total_texto,
        "horimetro_horas": horimetro_texto,
        "responsavel": responsavel,
    }


def main():
    rng = random.Random(SEED)  # gerador de números aleatórios próprio, sempre iniciado com 42
    equipamentos = carregar_csv(ARQ_EQUIPAMENTOS)
    contratos = carregar_csv(ARQ_CONTRATOS)
    leituras = carregar_csv(ARQ_HORIMETRO)

    intervalos_contrato = construir_intervalos_contrato(contratos)
    historico_horimetro = construir_historico_horimetro(leituras)

    abastecimentos = gerar_abastecimentos_limpo(rng, equipamentos, intervalos_contrato, historico_horimetro)
    processed = [formatar_processed(a) for a in abastecimentos]
    raw = [sujar_linha(rng, a) for a in abastecimentos]

    ARQ_RAW.parent.mkdir(parents=True, exist_ok=True)
    ARQ_PROCESSED.parent.mkdir(parents=True, exist_ok=True)
    gravar_csv(ARQ_RAW, COLUNAS, raw)
    gravar_csv(ARQ_PROCESSED, COLUNAS, processed)

    print(f"raw:       {len(raw)} linhas -> {ARQ_RAW.relative_to(RAIZ)}")
    print(f"processed: {len(processed)} linhas -> {ARQ_PROCESSED.relative_to(RAIZ)}")
    print("\nAmostra do raw:")
    for linha in raw[:6]:
        print("  " + " | ".join(linha[coluna] for coluna in COLUNAS))


if __name__ == "__main__":
    main()
