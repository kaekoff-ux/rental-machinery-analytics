"""Gera a tabela contratos_locacao da LocaMaq (dados 100% ficticios).

Depende dos CSVs limpos gerados por gerar_cadastro_equipamentos.py e gerar_clientes.py
(le data/processed/cadastro_equipamentos.csv e data/processed/clientes.csv) - rode esses
dois geradores primeiro.

Saidas:
    data/raw/contratos_locacao.csv        com sujeira proposital (entrada do Power Query)
    data/processed/contratos_locacao.csv  versao limpa (gabarito para validar o Power Query)

Como rodar, a partir da raiz do repositorio:
    python src/gerador_dados/gerar_contratos_locacao.py

Reprodutibilidade: a seed e fixa (42). Rodar de novo gera exatamente os mesmos arquivos,
desde que cadastro_equipamentos.csv e clientes.csv (processed) nao mudem.
Colunas e sujeira prevista: docs/dicionario_dados.csv.

Logica: para cada equipamento, simula um historico de locacoes SEQUENCIAIS (sem
sobreposicao de datas) entre a data de aquisicao (ou o inicio do historico, o que for
maior) e o fim do historico, com periodos ociosos no patio entre um contrato e outro -
como aconteceria de verdade numa locadora. Equipamentos "Vendido"/"Baixado" ainda geram
contratos dentro da janela (assume-se que a venda/baixa aconteceu depois do historico;
simplificacao aceitavel para este case).
"""
import csv
import random
from datetime import date, timedelta
from pathlib import Path

from utils import gravar_csv, sortear_ponderado

SEED = 42

# Mesma janela de historico das outras tabelas (24 meses).
INICIO_HISTORICO = date(2024, 1, 1)
FIM_HISTORICO = date(2025, 12, 31)

RAIZ = Path(__file__).resolve().parents[2]
ARQ_EQUIPAMENTOS = RAIZ / "data" / "processed" / "cadastro_equipamentos.csv"
ARQ_CLIENTES = RAIZ / "data" / "processed" / "clientes.csv"
ARQ_RAW = RAIZ / "data" / "raw" / "contratos_locacao.csv"
ARQ_PROCESSED = RAIZ / "data" / "processed" / "contratos_locacao.csv"

COLUNAS = [
    "id_contrato", "id_cliente", "id_equipamento", "data_inicio", "data_fim_prevista",
    "data_devolucao", "modalidade", "valor_diaria", "valor_mensal", "obra_local", "status",
]

MODALIDADES = [("Mensal", 55), ("Semanal", 25), ("Diária", 20)]

# Duração do contrato em dias, por modalidade (mínimo, máximo).
DURACAO_DIAS = {
    "Mensal": (30, 180),
    "Semanal": (7, 28),
    "Diária": (1, 6),
}

P_CONTRATO_CANCELADO = 0.06   # cancelado antes de a máquina sair do pátio (não conta como uso)
P_GAP_LONGO = 0.25            # chance de um intervalo ocioso mais longo entre contratos
GAP_CURTO = (3, 20)           # dias ociosos "normais" entre locações, no pátio
GAP_LONGO = (21, 75)          # dias ociosos mais raros (máquina parada por mais tempo)
N_CONTRATOS_DUPLICADOS = 6    # linhas de contrato duplicadas (mesmo id_contrato, conforme dicionário)

OBRA_PREFIXOS = [
    "Obra", "Canteiro", "Condomínio", "Loteamento", "Ampliação", "Reforma", "Pátio industrial",
]
OBRA_NOMES = [
    "Jardim das Acácias", "Vila Nova", "Parque Industrial Sul", "Rodovia dos Bandeirantes km 80",
    "Rodovia Anhanguera km 112", "Residencial Alto da Serra", "Distrito Industrial Norte",
    "Avenida Dom Pedro I", "Rodovia Washington Luís km 230", "Complexo Logístico Oeste",
    "Setor B da mina", "Terminal de cargas", "Marginal do rio", "Trevo de acesso leste",
]

# --- Sujeira (só vai para o raw) -----------------------------------------------------------
P_ID_EQUIPAMENTO_SUJO = 0.25  # minúsculo ou com espaço
P_MODALIDADE_SUJA = 0.25      # caixa mista
P_STATUS_SUJO = 0.20          # caixa mista
P_DATA_ISO = 0.35             # data como aaaa-mm-dd (o resto vem como dd/mm/aaaa) - mesmo
                               # tratamento nos 3 campos de data da tabela, por consistência.


def carregar_csv(caminho):
    with open(caminho, encoding="utf-8-sig", newline="") as arquivo:
        return list(csv.DictReader(arquivo, delimiter=";"))


def sortear_data_devolucao(rng, data_fim_prevista):
    """Devolução perto do fim previsto: a maioria pontual, uma parte adianta ou atrasa."""
    desvio = rng.choices(
        [rng.randint(-5, -1), 0, rng.randint(1, 10)],
        weights=[20, 45, 35],
    )[0]
    return data_fim_prevista + timedelta(days=desvio)


def calcular_valores(rng, modalidade, valor_aquisicao):
    """Taxa mensal como fração do valor de aquisição (referência comum no mercado de locação)."""
    valor_mensal_base = valor_aquisicao * rng.uniform(0.025, 0.045)
    valor_diaria_base = (valor_mensal_base / 22) * rng.uniform(1.3, 1.6)  # diária tem ágio
    valor_diaria = round(valor_diaria_base / 10) * 10
    valor_mensal = round(valor_mensal_base / 100) * 100
    if modalidade == "Mensal":
        return None, valor_mensal
    return valor_diaria, None  # Semanal e Diária cobram pela diária (não há valor_semanal na tabela)


# --- Passo 1: simular o histórico de locações de um equipamento, sem sobreposição --------
def gerar_contratos_equipamento(rng, equipamento, clientes):
    data_aquisicao = date.fromisoformat(equipamento["data_aquisicao"])
    cursor = max(INICIO_HISTORICO, data_aquisicao)
    contratos = []

    while cursor < FIM_HISTORICO:
        gap_min, gap_max = GAP_LONGO if rng.random() < P_GAP_LONGO else GAP_CURTO
        cursor += timedelta(days=rng.randint(gap_min, gap_max))
        if cursor >= FIM_HISTORICO:
            break

        modalidade = sortear_ponderado(rng, MODALIDADES)
        duracao = rng.randint(*DURACAO_DIAS[modalidade])
        data_inicio = cursor
        data_fim_prevista = min(data_inicio + timedelta(days=duracao), FIM_HISTORICO)

        cliente = rng.choice(clientes)
        valor_diaria, valor_mensal = calcular_valores(rng, modalidade, float(equipamento["valor_aquisicao"]))
        obra_local = f"{rng.choice(OBRA_PREFIXOS)} {rng.choice(OBRA_NOMES)}"

        if rng.random() < P_CONTRATO_CANCELADO:
            status, data_devolucao = "Cancelado", None
            cursor = data_fim_prevista  # máquina não saiu do pátio - não "usa" o período
        elif data_fim_prevista >= FIM_HISTORICO - timedelta(days=5):
            status, data_devolucao = "Ativo", None
            cursor = FIM_HISTORICO  # ainda em andamento no fim do histórico - encerra o laço
        else:
            status = "Encerrado"
            data_devolucao = sortear_data_devolucao(rng, data_fim_prevista)
            cursor = max(data_fim_prevista, data_devolucao)

        contratos.append({
            "id_cliente": cliente["id_cliente"],
            "id_equipamento": equipamento["id_equipamento"],
            "data_inicio": data_inicio,
            "data_fim_prevista": data_fim_prevista,
            "data_devolucao": data_devolucao,
            "modalidade": modalidade,
            "valor_diaria": valor_diaria,
            "valor_mensal": valor_mensal,
            "obra_local": obra_local,
            "status": status,
        })
    return contratos


def gerar_contratos_limpo(rng, equipamentos, clientes):
    contratos = []
    for equipamento in equipamentos:
        contratos.extend(gerar_contratos_equipamento(rng, equipamento, clientes))
    rng.shuffle(contratos)  # mistura os equipamentos para os IDs não ficarem agrupados
    for numero, contrato in enumerate(contratos, start=1):
        contrato["id_contrato"] = f"CT-{numero:05d}"
    return contratos


# --- Passo 2: versão processed (limpa, tudo como texto para gravar no CSV) ---------------
def formatar_processed(contrato):
    return {
        "id_contrato": contrato["id_contrato"],
        "id_cliente": contrato["id_cliente"],
        "id_equipamento": contrato["id_equipamento"],
        "data_inicio": contrato["data_inicio"].isoformat(),
        "data_fim_prevista": contrato["data_fim_prevista"].isoformat(),
        "data_devolucao": "" if contrato["data_devolucao"] is None else contrato["data_devolucao"].isoformat(),
        "modalidade": contrato["modalidade"],
        "valor_diaria": "" if contrato["valor_diaria"] is None else f"{contrato['valor_diaria']:.2f}",
        "valor_mensal": "" if contrato["valor_mensal"] is None else f"{contrato['valor_mensal']:.2f}",
        "obra_local": contrato["obra_local"],
        "status": contrato["status"],
    }


# --- Passo 3: versão raw (aplica a sujeira prevista no dicionário) -----------------------
def sujar_linha(rng, contrato):
    id_equipamento = contrato["id_equipamento"]
    if rng.random() < P_ID_EQUIPAMENTO_SUJO:
        id_equipamento = rng.choice([id_equipamento.lower(), f" {id_equipamento}", f"{id_equipamento} "])

    modalidade = contrato["modalidade"]
    if rng.random() < P_MODALIDADE_SUJA:
        modalidade = rng.choice([modalidade.upper(), modalidade.lower()])

    status = contrato["status"]
    if rng.random() < P_STATUS_SUJO:
        status = rng.choice([status.upper(), status.lower()])

    def formatar_data(data_valor):
        if data_valor is None:
            return ""
        return data_valor.isoformat() if rng.random() < P_DATA_ISO else data_valor.strftime("%d/%m/%Y")

    return {
        "id_contrato": contrato["id_contrato"],
        "id_cliente": contrato["id_cliente"],
        "id_equipamento": id_equipamento,
        "data_inicio": formatar_data(contrato["data_inicio"]),
        "data_fim_prevista": formatar_data(contrato["data_fim_prevista"]),
        "data_devolucao": formatar_data(contrato["data_devolucao"]),
        "modalidade": modalidade,
        "valor_diaria": "" if contrato["valor_diaria"] is None else f"{contrato['valor_diaria']:.2f}",
        "valor_mensal": "" if contrato["valor_mensal"] is None else f"{contrato['valor_mensal']:.2f}",
        "obra_local": contrato["obra_local"],
        "status": status,
    }


def gerar_raw(rng, contratos):
    raw = [sujar_linha(rng, contrato) for contrato in contratos]
    # Duplicados: a mesma linha de contrato exportada/importada duas vezes (mesmo id_contrato),
    # como o dicionário de dados prevê para esta tabela.
    for contrato in rng.sample(contratos, N_CONTRATOS_DUPLICADOS):
        raw.insert(rng.randrange(len(raw) + 1), sujar_linha(rng, contrato))
    return raw


def main():
    rng = random.Random(SEED)  # gerador de números aleatórios próprio, sempre iniciado com 42
    equipamentos = carregar_csv(ARQ_EQUIPAMENTOS)
    clientes = carregar_csv(ARQ_CLIENTES)

    contratos = gerar_contratos_limpo(rng, equipamentos, clientes)
    processed = [formatar_processed(c) for c in contratos]
    raw = gerar_raw(rng, contratos)

    ARQ_RAW.parent.mkdir(parents=True, exist_ok=True)
    ARQ_PROCESSED.parent.mkdir(parents=True, exist_ok=True)
    gravar_csv(ARQ_RAW, COLUNAS, raw)
    gravar_csv(ARQ_PROCESSED, COLUNAS, processed)

    print(f"raw:       {len(raw)} linhas ({N_CONTRATOS_DUPLICADOS} duplicadas) -> {ARQ_RAW.relative_to(RAIZ)}")
    print(f"processed: {len(processed)} linhas -> {ARQ_PROCESSED.relative_to(RAIZ)}")
    contagem_status = {}
    for linha in processed:
        contagem_status[linha["status"]] = contagem_status.get(linha["status"], 0) + 1
    print(f"status: {contagem_status}")
    print("\nAmostra do raw:")
    for linha in raw[:6]:
        print("  " + " | ".join(linha[coluna] for coluna in COLUNAS))


if __name__ == "__main__":
    main()
