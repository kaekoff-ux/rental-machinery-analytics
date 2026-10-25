"""Gera a tabela ordens_manutencao da LocaMaq (dados 100% ficticios).

Depende de:
    data/processed/cadastro_equipamentos.csv
    data/processed/contratos_locacao.csv
    data/processed/horimetro_telemetria.csv
Rode os geradores anteriores primeiro (nessa ordem).

Saidas:
    data/raw/ordens_manutencao.csv        com sujeira proposital (entrada do Power Query)
    data/processed/ordens_manutencao.csv  versao limpa (gabarito para validar o Power Query)

Como rodar, a partir da raiz do repositorio:
    python src/gerador_dados/gerar_ordens_manutencao.py

Reprodutibilidade: a seed e fixa (42). Rodar de novo gera exatamente os mesmos arquivos,
desde que os CSVs de que depende (processed) nao mudem.
Colunas e sujeira prevista: docs/dicionario_dados.csv.

Este e o modulo de CONTROLE DE OFICINA: status_os (Aberta/Em andamento/Concluida) e,
na pratica, um board Kanban de 3 colunas. Tres origens de ordem de servico:

1. Preventiva: disparada quando o horimetro simulado cruza um multiplo de
   INTERVALO_PREVENTIVA_HORAS desde a ultima revisao (igual a uma locadora real agenda
   manutencao programada por horas de uso).
2. Corretiva: falhas aleatorias, mais prováveis enquanto o equipamento esta em uso
   (contrato vigente) do que parado no patio.
3. Preditiva: a REGRA DE INTEGRACAO comercial -> oficina documentada no FINAL_REPORT.md do
   Cartographer - toda devolucao de contrato (data_devolucao preenchida) abre
   automaticamente uma ordem de inspecao pos-locacao.
"""
import csv
import random
from datetime import date, timedelta
from pathlib import Path

from utils import construir_intervalos_contrato, contrato_vigente, formatar_real, gravar_csv

SEED = 42

# Mesma janela de historico das outras tabelas (24 meses).
INICIO_HISTORICO = date(2024, 1, 1)
FIM_HISTORICO = date(2025, 12, 31)

RAIZ = Path(__file__).resolve().parents[2]
ARQ_EQUIPAMENTOS = RAIZ / "data" / "processed" / "cadastro_equipamentos.csv"
ARQ_CONTRATOS = RAIZ / "data" / "processed" / "contratos_locacao.csv"
ARQ_HORIMETRO = RAIZ / "data" / "processed" / "horimetro_telemetria.csv"
ARQ_RAW = RAIZ / "data" / "raw" / "ordens_manutencao.csv"
ARQ_PROCESSED = RAIZ / "data" / "processed" / "ordens_manutencao.csv"

COLUNAS = [
    "id_os", "id_equipamento", "tipo_manutencao", "data_abertura", "data_conclusao",
    "horimetro_na_os", "descricao_falha", "horas_parada", "custo_pecas", "custo_mao_obra",
    "status_os",
]

# (descricao, severidade 1-3). A severidade decide custo, horas_parada e duracao da OS.
CATALOGO_DESCRICAO = {
    "Preventiva": [
        ("Troca de óleo hidráulico", 1),
        ("Troca de filtros e óleo do motor", 1),
        ("Lubrificação geral e inspeção de desgaste", 1),
        ("Calibração e ajuste do sistema hidráulico", 1),
        ("Revisão geral programada", 2),
    ],
    "Corretiva": [
        ("Troca de pneus/esteiras danificadas", 2),
        ("Reparo no sistema elétrico", 2),
        ("Reparo em vazamento de óleo", 1),
        ("Substituição de motor de partida", 2),
        ("Falha no sistema de freios", 2),
        ("Substituição de bomba hidráulica", 3),
        ("Quebra de componente estrutural (lança/caçamba)", 3),
    ],
    "Preditiva": [
        ("Inspeção pós-locação", 1),
    ],
}

SEVERIDADE_CUSTO_PECAS = {1: (150, 900), 2: (600, 3200), 3: (3000, 12000)}
SEVERIDADE_CUSTO_MAO_OBRA = {1: (100, 500), 2: (400, 1800), 3: (1200, 4000)}
SEVERIDADE_HORAS_PARADA = {1: (1, 8), 2: (8, 30), 3: (24, 96)}
SEVERIDADE_DURACAO_DIAS = {1: (0, 2), 2: (1, 5), 3: (3, 10)}

INTERVALO_PREVENTIVA_HORAS = 250  # revisão programada a cada 250h de uso
TAXA_CORRETIVA_POR_DIA_ATIVO = 1 / 90  # ~1 falha a cada 90 dias de uso efetivo (por máquina)
JANELA_OS_ABERTA = 10  # OS abertas nos últimos N dias do histórico podem não estar concluídas

# --- Sujeira (só vai para o raw, exceto nulos legítimos - ver comentário em main) ---------
P_ID_EQUIPAMENTO_SUJO = 0.20   # minúsculo
P_TIPO_SUJO = 0.30             # "Prev." / "preventiva" / "PREV"
P_STATUS_SUJO = 0.20           # caixa mista
P_DATA_ISO = 0.35              # data como aaaa-mm-dd (o resto vem como dd/mm/aaaa)
P_HORIMETRO_NULO = 0.08        # oficina às vezes não registra o horímetro no momento da OS
P_HORAS_PARADA_NULO = 0.05     # idem para horas de máquina parada
P_CUSTO_COM_REAL = 0.55        # "R$ 3.200,00" em vez de "3200.00"

VARIANTES_TIPO = {
    "Preventiva": ["Prev.", "preventiva", "PREV", "PREVENTIVA"],
    "Corretiva": ["Corr.", "corretiva", "CORR", "CORRETIVA"],
    "Preditiva": ["Pred.", "preditiva", "PRED", "PREDITIVA"],
}


def carregar_csv(caminho):
    with open(caminho, encoding="utf-8-sig", newline="") as arquivo:
        return list(csv.DictReader(arquivo, delimiter=";"))


def construir_historico_horimetro(leituras):
    """{id_equipamento: [(data, horas), ...]} ordenado - para achar o horímetro na data de uma OS."""
    historico = {}
    for leitura in leituras:
        historico.setdefault(leitura["id_equipamento"], []).append(
            (date.fromisoformat(leitura["data_leitura"]), float(leitura["horimetro_horas"]))
        )
    for lista in historico.values():
        lista.sort()
    return historico


def horimetro_na_data(historico_equipamento, dia):
    """Última leitura conhecida em ou antes de `dia`. None se não há leitura anterior."""
    valor = None
    for data_leitura, horas in historico_equipamento:
        if data_leitura > dia:
            break
        valor = horas
    return valor


def montar_os(rng, id_equipamento, tipo, data_abertura, historico_equipamento, descricao_extra=""):
    descricao, severidade = rng.choice(CATALOGO_DESCRICAO[tipo])
    if descricao_extra:
        descricao = f"{descricao} - {descricao_extra}"

    duracao = rng.randint(*SEVERIDADE_DURACAO_DIAS[severidade])
    dias_restantes = (FIM_HISTORICO - data_abertura).days

    if dias_restantes > duracao + JANELA_OS_ABERTA:
        status = "Concluída"
        data_conclusao = data_abertura + timedelta(days=duracao)
    else:
        status = "Aberta" if dias_restantes <= 2 else "Em andamento"
        data_conclusao = None

    horimetro = horimetro_na_data(historico_equipamento, data_abertura)
    if horimetro is not None and rng.random() < P_HORIMETRO_NULO:
        horimetro = None

    horas_parada = rng.uniform(*SEVERIDADE_HORAS_PARADA[severidade])
    if rng.random() < P_HORAS_PARADA_NULO:
        horas_parada = None

    return {
        "id_equipamento": id_equipamento,
        "tipo_manutencao": tipo,
        "data_abertura": data_abertura,
        "data_conclusao": data_conclusao,
        "horimetro_na_os": horimetro,
        "descricao_falha": descricao,
        "horas_parada": horas_parada,
        "custo_pecas": round(rng.uniform(*SEVERIDADE_CUSTO_PECAS[severidade]) / 10) * 10,
        "custo_mao_obra": round(rng.uniform(*SEVERIDADE_CUSTO_MAO_OBRA[severidade]) / 10) * 10,
        "status_os": status,
    }


# --- Origem 1: preventiva, disparada por limiar de horímetro -----------------------------
def gerar_preventivas(rng, historico_horimetro):
    ordens = []
    for id_equipamento, leituras in historico_horimetro.items():
        proximo_limiar = INTERVALO_PREVENTIVA_HORAS
        for data_leitura, horas in leituras:
            if horas >= proximo_limiar:
                data_abertura = data_leitura + timedelta(days=rng.randint(0, 2))
                if data_abertura <= FIM_HISTORICO:
                    ordens.append(montar_os(rng, id_equipamento, "Preventiva", data_abertura, leituras))
                # pula para o próximo múltiplo acima do valor atual - evita disparar várias
                # OS de uma vez só quando o intervalo entre leituras é grande.
                proximo_limiar = (int(horas // INTERVALO_PREVENTIVA_HORAS) + 1) * INTERVALO_PREVENTIVA_HORAS
    return ordens


# --- Origem 2: corretiva, falha aleatória mais provável em uso ---------------------------
def gerar_corretivas(rng, equipamentos, intervalos_contrato, historico_horimetro):
    ordens = []
    for equipamento in equipamentos:
        id_equipamento = equipamento["id_equipamento"]
        data_aquisicao = date.fromisoformat(equipamento["data_aquisicao"])
        dia = max(INICIO_HISTORICO, data_aquisicao)
        leituras = historico_horimetro.get(id_equipamento, [])
        while dia <= FIM_HISTORICO:
            em_uso = contrato_vigente(intervalos_contrato.get(id_equipamento, []), dia) is not None
            taxa = TAXA_CORRETIVA_POR_DIA_ATIVO if em_uso else TAXA_CORRETIVA_POR_DIA_ATIVO / 4
            if rng.random() < taxa:
                ordens.append(montar_os(rng, id_equipamento, "Corretiva", dia, leituras))
            dia += timedelta(days=1)
    return ordens


# --- Origem 3: preditiva, regra comercial -> oficina (devolução abre inspeção) -----------
def gerar_preditivas(rng, contratos, historico_horimetro):
    ordens = []
    for contrato in contratos:
        if not contrato["data_devolucao"]:
            continue
        id_equipamento = contrato["id_equipamento"]
        data_devolucao = date.fromisoformat(contrato["data_devolucao"])
        data_abertura = data_devolucao + timedelta(days=rng.randint(0, 2))
        if data_abertura > FIM_HISTORICO:
            continue
        leituras = historico_horimetro.get(id_equipamento, [])
        ordem = montar_os(
            rng, id_equipamento, "Preditiva", data_abertura, leituras,
            descricao_extra=f"contrato {contrato['id_contrato']}",
        )
        ordens.append(ordem)
    return ordens


# --- Versão processed (limpa) -------------------------------------------------------------
def formatar_processed(ordem):
    return {
        "id_os": ordem["id_os"],
        "id_equipamento": ordem["id_equipamento"],
        "tipo_manutencao": ordem["tipo_manutencao"],
        "data_abertura": ordem["data_abertura"].isoformat(),
        "data_conclusao": "" if ordem["data_conclusao"] is None else ordem["data_conclusao"].isoformat(),
        "horimetro_na_os": "" if ordem["horimetro_na_os"] is None else f"{ordem['horimetro_na_os']:.1f}",
        "descricao_falha": ordem["descricao_falha"],
        "horas_parada": "" if ordem["horas_parada"] is None else f"{ordem['horas_parada']:.1f}",
        "custo_pecas": f"{ordem['custo_pecas']:.2f}",
        "custo_mao_obra": f"{ordem['custo_mao_obra']:.2f}",
        "status_os": ordem["status_os"],
    }


# --- Versão raw (aplica a sujeira prevista no dicionário) --------------------------------
def sujar_linha(rng, ordem):
    id_equipamento = ordem["id_equipamento"]
    if rng.random() < P_ID_EQUIPAMENTO_SUJO:
        id_equipamento = id_equipamento.lower()

    tipo = ordem["tipo_manutencao"]
    if rng.random() < P_TIPO_SUJO:
        tipo = rng.choice(VARIANTES_TIPO[tipo])

    status = ordem["status_os"]
    if rng.random() < P_STATUS_SUJO:
        status = rng.choice([status.upper(), status.lower()])

    def formatar_data(data_valor):
        if data_valor is None:
            return ""
        return data_valor.isoformat() if rng.random() < P_DATA_ISO else data_valor.strftime("%d/%m/%Y")

    def formatar_valor(valor):
        if rng.random() < P_CUSTO_COM_REAL:
            return formatar_real(valor)
        return f"{valor:.2f}"

    return {
        "id_os": ordem["id_os"],
        "id_equipamento": id_equipamento,
        "tipo_manutencao": tipo,
        "data_abertura": formatar_data(ordem["data_abertura"]),
        "data_conclusao": formatar_data(ordem["data_conclusao"]),
        "horimetro_na_os": "" if ordem["horimetro_na_os"] is None else f"{ordem['horimetro_na_os']:.1f}",
        "descricao_falha": ordem["descricao_falha"],
        "horas_parada": "" if ordem["horas_parada"] is None else f"{ordem['horas_parada']:.1f}",
        "custo_pecas": formatar_valor(ordem["custo_pecas"]),
        "custo_mao_obra": formatar_valor(ordem["custo_mao_obra"]),
        "status_os": status,
    }


def main():
    rng = random.Random(SEED)  # gerador de números aleatórios próprio, sempre iniciado com 42
    equipamentos = carregar_csv(ARQ_EQUIPAMENTOS)
    contratos = carregar_csv(ARQ_CONTRATOS)
    leituras = carregar_csv(ARQ_HORIMETRO)

    intervalos_contrato = construir_intervalos_contrato(contratos)
    historico_horimetro = construir_historico_horimetro(leituras)

    ordens = []
    ordens.extend(gerar_preventivas(rng, historico_horimetro))
    ordens.extend(gerar_corretivas(rng, equipamentos, intervalos_contrato, historico_horimetro))
    ordens.extend(gerar_preditivas(rng, contratos, historico_horimetro))

    rng.shuffle(ordens)  # mistura as origens para os IDs não ficarem agrupados
    for numero, ordem in enumerate(ordens, start=1):
        ordem["id_os"] = f"OS-{numero:05d}"

    processed = [formatar_processed(o) for o in ordens]
    raw = [sujar_linha(rng, o) for o in ordens]

    ARQ_RAW.parent.mkdir(parents=True, exist_ok=True)
    ARQ_PROCESSED.parent.mkdir(parents=True, exist_ok=True)
    gravar_csv(ARQ_RAW, COLUNAS, raw)
    gravar_csv(ARQ_PROCESSED, COLUNAS, processed)

    contagem_tipo = {}
    contagem_status = {}
    for linha in processed:
        contagem_tipo[linha["tipo_manutencao"]] = contagem_tipo.get(linha["tipo_manutencao"], 0) + 1
        contagem_status[linha["status_os"]] = contagem_status.get(linha["status_os"], 0) + 1

    print(f"raw:       {len(raw)} linhas -> {ARQ_RAW.relative_to(RAIZ)}")
    print(f"processed: {len(processed)} linhas -> {ARQ_PROCESSED.relative_to(RAIZ)}")
    print(f"tipo_manutencao: {contagem_tipo}")
    print(f"status_os (board Kanban): {contagem_status}")
    print("\nAmostra do raw:")
    for linha in raw[:6]:
        print("  " + " | ".join(linha[coluna] for coluna in COLUNAS))


if __name__ == "__main__":
    main()
