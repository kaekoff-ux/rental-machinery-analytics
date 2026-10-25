"""Gera a tabela cadastro_equipamentos da LocaMaq (dados 100% fictícios).

Saídas:
    data/raw/cadastro_equipamentos.csv        com sujeira proposital (entrada do Power Query)
    data/processed/cadastro_equipamentos.csv  versão limpa (gabarito para validar o Power Query)

Como rodar, a partir da raiz do repositório:
    python src/gerador_dados/gerar_cadastro_equipamentos.py

Reprodutibilidade: a seed é fixa (42). Rodar de novo gera exatamente os mesmos arquivos.
Colunas e sujeira prevista: docs/dicionario_dados.csv.
"""
import random
import unicodedata
from datetime import date, timedelta
from pathlib import Path

from utils import gravar_csv, sortear_ponderado

SEED = 42

# Janela de histórico do projeto (24 meses). As outras tabelas devem usar a mesma janela.
INICIO_HISTORICO = date(2024, 1, 1)
FIM_HISTORICO = date(2025, 12, 31)

RAIZ = Path(__file__).resolve().parents[2]
ARQ_RAW = RAIZ / "data" / "raw" / "cadastro_equipamentos.csv"
ARQ_PROCESSED = RAIZ / "data" / "processed" / "cadastro_equipamentos.csv"

COLUNAS = [
    "id_equipamento", "segmento", "modelo", "fabricante", "ano_fabricacao", "numero_serie",
    "data_aquisicao", "valor_aquisicao", "vida_util_horas", "filial", "status_cadastro",
]

# --- Catálogo da frota -------------------------------------------------------------------
# segmento: (quantidade de máquinas, [(fabricante, modelo, sigla do n. de série, valor base R$, vida útil em horas)])
# Total: 135 máquinas (o roadmap sugere 120 a 150).
CATALOGO = {
    "Escavadeira": (30, [
        ("Caterpillar", "320D", "CAT", 845000, 12000),
        ("Caterpillar", "320GC", "CAT", 920000, 12000),
        ("Komatsu", "PC210", "KOM", 780000, 12000),
        ("Volvo", "EC210B", "VOL", 810000, 12000),
        ("Hyundai", "HX220L", "HYU", 760000, 12000),
    ]),
    "Retroescavadeira": (22, [
        ("Caterpillar", "416F", "CAT", 380000, 10000),
        ("JCB", "3CX", "JCB", 360000, 10000),
        ("Case", "580N", "CAS", 340000, 10000),
        ("New Holland", "B95B", "NHL", 330000, 10000),
    ]),
    "Pá-carregadeira": (18, [
        ("Caterpillar", "950H", "CAT", 780000, 12000),
        ("Volvo", "L60H", "VOL", 690000, 12000),
        ("Case", "821F", "CAS", 640000, 12000),
        ("XCMG", "LW500", "XCM", 480000, 12000),
    ]),
    "Guindaste": (10, [
        ("Grove", "RT540E", "GRO", 1950000, 15000),
        ("Tadano", "GR500EX", "TAD", 1700000, 15000),
        ("Liebherr", "LTM1050", "LIE", 2900000, 15000),
        ("XCMG", "QY25K", "XCM", 1100000, 15000),
    ]),
    "Gerador": (25, [
        ("Cummins", "C150D5", "CUM", 160000, 20000),
        ("Cummins", "C250D5", "CUM", 230000, 20000),
        ("Caterpillar", "XQ125", "CAT", 190000, 20000),
        ("Atlas Copco", "QAS150", "ATL", 140000, 20000),
    ]),
    "Empilhadeira": (18, [
        ("Toyota", "8FGU25", "TOY", 140000, 12000),
        ("Hyster", "H80FT", "HYS", 150000, 12000),
        ("Yale", "GDP50VX", "YAL", 130000, 12000),
        ("Clark", "C25", "CLK", 110000, 12000),
    ]),
    "Plataforma elevatória": (12, [
        ("JLG", "600AJ", "JLG", 380000, 12000),
        ("Genie", "Z45", "GEN", 290000, 12000),
        ("Skyjack", "SJ63AJ", "SKY", 340000, 12000),
        ("Haulotte", "HA16", "HAU", 260000, 12000),
    ]),
}

# (filial, peso no sorteio) - filiais no estado de SP
FILIAIS = [("São Paulo", 30), ("Campinas", 25), ("Ribeirão Preto", 20), ("Sorocaba", 15), ("São José dos Campos", 10)]
STATUS = [("Ativo", 88), ("Vendido", 7), ("Baixado", 5)]

# --- Sujeira (só vai para o raw) ---------------------------------------------------------
# Cada número é a chance (0 a 1) de a sujeira aparecer em uma linha.
P_ANO_NULO = 0.06            # ano_fabricacao vazio (este vazio também fica no processed)
P_ID_SUJO = 0.20             # eq-0001 / EQ0001 / eq0001
P_SEGMENTO_SUJO = 0.30
P_MODELO_ESPACOS = 0.10
P_FABRICANTE_SUJO = 0.35
P_DATA_ISO = 0.35            # data como aaaa-mm-dd (o resto vem como dd/mm/aaaa)
P_VALOR_COM_REAL = 0.55      # valor como "R$ 845.000,00" (o resto vem como 845000.00)
P_FILIAL_SUJA = 0.30
P_STATUS_SUJO = 0.20
N_DUPLICADOS = 4             # máquinas que aparecem 2 vezes (mesmo numero_serie)

VARIANTES_SEGMENTO = {
    "Escavadeira": ["ESCAVADEIRA", "Escav.", "escavadeira"],
    "Retroescavadeira": ["RETROESCAVADEIRA", "Retro", "retro escavadeira"],
    "Pá-carregadeira": ["Pa carregadeira", "PÁ CARREGADEIRA", "pa-carregadeira"],
    "Guindaste": ["GUINDASTE", "guindaste", "Guindaste Móvel"],
    "Gerador": ["GERADOR", "gerador", "Grupo Gerador"],
    "Empilhadeira": ["EMPILHADEIRA", "empilhadeira", "Empilh."],
    "Plataforma elevatória": ["Plataforma Elevatoria", "PLATAFORMA ELEVATÓRIA", "plataforma elevatoria"],
}
ALIASES_FABRICANTE = {
    "Caterpillar": ["CAT", "Cat"],
    "Volvo": ["Volvo CE"],
    "Hyundai": ["Hyundai CE"],
    "Case": ["Case CE"],
    "New Holland": ["NH", "New Holland CE"],
    "Atlas Copco": ["Atlas-Copco"],
}


def sem_acento(texto):
    """'São José' -> 'Sao Jose' (separa a letra do acento e descarta o acento)."""
    return "".join(c for c in unicodedata.normalize("NFD", texto) if unicodedata.category(c) != "Mn")


def formatar_real(valor):
    """845000.0 -> 'R$ 845.000,00' (padrão brasileiro de planilha)."""
    texto = f"{valor:,.2f}"  # '845,000.00'
    texto = texto.replace(",", "#").replace(".", ",").replace("#", ".")
    return f"R$ {texto}"


# --- Passo 1: gerar a frota limpa ---------------------------------------------------------
def sortear_data_aquisicao(rng):
    """85% das máquinas já estavam na frota antes do histórico; 15% foram compradas durante."""
    if rng.random() < 0.15:
        inicio, fim = INICIO_HISTORICO, date(2025, 9, 30)
    else:
        inicio, fim = date(2016, 1, 1), INICIO_HISTORICO - timedelta(days=1)
    return inicio + timedelta(days=rng.randrange((fim - inicio).days + 1))


def gerar_frota_limpa(rng):
    linhas = []
    series_usadas = set()
    for segmento, (quantidade, modelos) in CATALOGO.items():
        for _ in range(quantidade):
            fabricante, modelo, sigla, valor_base, vida_util = rng.choice(modelos)
            data_aquisicao = sortear_data_aquisicao(rng)

            # Máquina nova (0 anos) é o mais comum; usada de 1 a 6 anos de fabricação é menos.
            anos_de_uso = rng.choices(range(7), weights=[50, 20, 12, 8, 5, 3, 2])[0]
            ano = max(2010, data_aquisicao.year - anos_de_uso)
            if rng.random() < P_ANO_NULO:
                ano = None

            while True:  # garante número de série único
                numero_serie = f"{sigla}{modelo}-{rng.randint(100000, 999999)}"
                if numero_serie not in series_usadas:
                    series_usadas.add(numero_serie)
                    break

            linhas.append({
                "segmento": segmento,
                "modelo": modelo,
                "fabricante": fabricante,
                "ano_fabricacao": ano,
                "numero_serie": numero_serie,
                "data_aquisicao": data_aquisicao,
                "valor_aquisicao": round(valor_base * rng.uniform(0.92, 1.08) / 500) * 500,
                "vida_util_horas": vida_util,
                "filial": sortear_ponderado(rng, FILIAIS),
                "status_cadastro": sortear_ponderado(rng, STATUS),
            })

    rng.shuffle(linhas)  # mistura os segmentos para os IDs não ficarem agrupados
    for numero, linha in enumerate(linhas, start=1):
        linha["id_equipamento"] = f"EQ-{numero:04d}"
    return linhas


# --- Passo 2: versão processed (limpa, tudo como texto para gravar no CSV) -----------------
def formatar_processed(linha):
    return {
        "id_equipamento": linha["id_equipamento"],
        "segmento": linha["segmento"],
        "modelo": linha["modelo"],
        "fabricante": linha["fabricante"],
        "ano_fabricacao": "" if linha["ano_fabricacao"] is None else str(linha["ano_fabricacao"]),
        "numero_serie": linha["numero_serie"],
        "data_aquisicao": linha["data_aquisicao"].isoformat(),  # aaaa-mm-dd
        "valor_aquisicao": f"{linha['valor_aquisicao']:.2f}",
        "vida_util_horas": str(linha["vida_util_horas"]),
        "filial": linha["filial"],
        "status_cadastro": linha["status_cadastro"],
    }


# --- Passo 3: versão raw (aplica a sujeira prevista no dicionário) ------------------------
def sujar_linha(rng, linha):
    id_equipamento = linha["id_equipamento"]
    sorteio = rng.random()
    if sorteio < P_ID_SUJO * 0.4:
        id_equipamento = id_equipamento.lower()                      # eq-0001
    elif sorteio < P_ID_SUJO * 0.7:
        id_equipamento = id_equipamento.replace("-", "")             # EQ0001
    elif sorteio < P_ID_SUJO:
        id_equipamento = id_equipamento.replace("-", "").lower()     # eq0001

    segmento = linha["segmento"]
    if rng.random() < P_SEGMENTO_SUJO:
        segmento = rng.choice(VARIANTES_SEGMENTO[segmento])

    modelo = linha["modelo"]
    if rng.random() < P_MODELO_ESPACOS:
        modelo = rng.choice([f" {modelo}", f"{modelo} ", f" {modelo}  "])

    fabricante = linha["fabricante"]
    if rng.random() < P_FABRICANTE_SUJO:
        fabricante = rng.choice([fabricante.upper(), fabricante.lower()] + ALIASES_FABRICANTE.get(fabricante, []))

    if rng.random() < P_DATA_ISO:
        data_aquisicao = linha["data_aquisicao"].isoformat()
    else:
        data_aquisicao = linha["data_aquisicao"].strftime("%d/%m/%Y")

    if rng.random() < P_VALOR_COM_REAL:
        valor_aquisicao = formatar_real(linha["valor_aquisicao"])
    else:
        valor_aquisicao = f"{linha['valor_aquisicao']:.2f}"

    filial = linha["filial"]
    if rng.random() < P_FILIAL_SUJA:
        filial = rng.choice([sem_acento(filial), filial.upper(), filial.lower(), sem_acento(filial).lower()])

    status = linha["status_cadastro"]
    if rng.random() < P_STATUS_SUJO:
        status = rng.choice([status.upper(), status.lower()])

    return {
        "id_equipamento": id_equipamento,
        "segmento": segmento,
        "modelo": modelo,
        "fabricante": fabricante,
        "ano_fabricacao": "" if linha["ano_fabricacao"] is None else str(linha["ano_fabricacao"]),
        "numero_serie": linha["numero_serie"],
        "data_aquisicao": data_aquisicao,
        "valor_aquisicao": valor_aquisicao,
        "vida_util_horas": str(linha["vida_util_horas"]),
        "filial": filial,
        "status_cadastro": status,
    }


def gerar_raw(rng, frota):
    raw = [sujar_linha(rng, linha) for linha in frota]
    # Duplicados: a mesma máquina cadastrada de novo, com outra "grafia" (mesmo numero_serie).
    for linha in rng.sample(frota, N_DUPLICADOS):
        raw.insert(rng.randrange(len(raw) + 1), sujar_linha(rng, linha))
    return raw


def main():
    rng = random.Random(SEED)  # gerador de números aleatórios próprio, sempre iniciado com 42
    frota = gerar_frota_limpa(rng)
    processed = [formatar_processed(linha) for linha in frota]
    raw = gerar_raw(rng, frota)

    ARQ_RAW.parent.mkdir(parents=True, exist_ok=True)
    ARQ_PROCESSED.parent.mkdir(parents=True, exist_ok=True)
    gravar_csv(ARQ_RAW, COLUNAS, raw)
    gravar_csv(ARQ_PROCESSED, COLUNAS, processed)

    print(f"raw:       {len(raw)} linhas ({N_DUPLICADOS} duplicadas) -> {ARQ_RAW.relative_to(RAIZ)}")
    print(f"processed: {len(processed)} linhas -> {ARQ_PROCESSED.relative_to(RAIZ)}")
    print("\nAmostra do raw:")
    for linha in raw[:6]:
        print("  " + " | ".join(linha[coluna] for coluna in COLUNAS))


if __name__ == "__main__":
    main()
