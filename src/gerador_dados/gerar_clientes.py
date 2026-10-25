"""Gera a tabela clientes da LocaMaq (dados 100% ficticios).

Saidas:
    data/raw/clientes.csv        com sujeira proposital (entrada do Power Query)
    data/processed/clientes.csv  versao limpa (gabarito para validar o Power Query)

Como rodar, a partir da raiz do repositorio:
    python src/gerador_dados/gerar_clientes.py

Reprodutibilidade: a seed e fixa (42). Rodar de novo gera exatamente os mesmos arquivos.
Colunas e sujeira prevista: docs/dicionario_dados.csv.
"""
import csv
import random
from datetime import date, timedelta
from pathlib import Path

SEED = 42

# Mesma janela de historico das outras tabelas (24 meses).
INICIO_HISTORICO = date(2024, 1, 1)
FIM_HISTORICO = date(2025, 12, 31)

RAIZ = Path(__file__).resolve().parents[2]
ARQ_RAW = RAIZ / "data" / "raw" / "clientes.csv"
ARQ_PROCESSED = RAIZ / "data" / "processed" / "clientes.csv"

COLUNAS = [
    "id_cliente", "razao_social", "cnpj", "segmento_cliente", "cidade", "uf",
    "limite_credito", "data_cadastro",
]

# --- Catalogo de clientes ------------------------------------------------------------------
# segmento_cliente: (quantidade de clientes, faixa de limite de credito em R$)
# Total: 70 clientes (o roadmap sugere 60 a 80).
CATALOGO = {
    "Construção civil": (24, (80000, 900000)),
    "Infraestrutura": (12, (150000, 1500000)),
    "Mineração": (6, (300000, 2000000)),
    "Indústria": (10, (100000, 800000)),
    "Eventos": (8, (30000, 250000)),
    "Logística": (6, (60000, 500000)),
    "Agronegócio": (4, (100000, 700000)),
}

PREFIXOS_RAZAO_SOCIAL = [
    "Construtora", "Engenharia", "Terraplenagem", "Incorporadora", "Locações",
    "Infraestrutura", "Mineração", "Logística", "Eventos", "Montagens",
]
NOMES_FANTASIA = [
    "Alfa", "Beta", "Horizonte", "Vale Verde", "Pedra Forte", "Nova Era", "Bandeirantes",
    "Rio Claro", "Serra Azul", "Planalto", "Atlântica", "Sul Mineira", "Vale do Sol",
    "Pioneira", "Central", "Progresso", "União", "Guarani", "Ipê Dourado", "Cruzeiro",
    "Estrela", "Rota Norte", "Litoral", "Capital", "Vértice", "Matriz", "Paulista",
    "Vanguarda", "Eixo Sul", "Nova Aurora", "Brisa", "Marcos", "Norte Forte", "Zênite",
    "Delta", "Omega", "Trevo", "Portal", "Aliança", "Base Firme", "Gênesis", "Átrio",
]
SUFIXOS_SOCIETARIOS = ["Ltda", "S.A.", "Eireli", "ME"]

# (cidade, uf, peso) - maioria em SP (onde ficam as filiais), com alguma presença em estados vizinhos
CIDADES = [
    ("São Paulo", "SP", 22), ("Campinas", "SP", 16), ("Ribeirão Preto", "SP", 12),
    ("Sorocaba", "SP", 10), ("São José dos Campos", "SP", 9), ("Santos", "SP", 6),
    ("Jundiaí", "SP", 5), ("Piracicaba", "SP", 5), ("Belo Horizonte", "MG", 6),
    ("Rio de Janeiro", "RJ", 5), ("Curitiba", "PR", 4),
]

# --- Sujeira (so vai para o raw) -----------------------------------------------------------
P_RAZAO_ABREVIADA = 0.25      # "Construtora Alfa Ltda" -> "CONSTR. ALFA"
P_CNPJ_SEM_MASCARA = 0.45     # "12.345.678/0001-90" -> "12345678000190"
P_SEGMENTO_SUJO = 0.25        # categoria fora do padrão do dicionário
P_CIDADE_SUJA = 0.30          # grafia diferente
P_UF_MINUSCULA = 0.15
P_UF_NULA = 0.05
P_DATA_ISO = 0.35             # data como aaaa-mm-dd (o resto vem como dd/mm/aaaa)
N_CLIENTES_DUPLICADOS = 3     # mesmo cliente (mesmo CNPJ), razao social escrita diferente

VARIANTES_SEGMENTO = {
    "Construção civil": ["CONSTRUÇÃO CIVIL", "Constr. Civil", "construção civil", "Obras"],
    "Infraestrutura": ["INFRAESTRUTURA", "Infra", "infraestrutura"],
    "Mineração": ["MINERAÇÃO", "Mineracao", "mineração"],
    "Indústria": ["INDÚSTRIA", "Industria", "indústria"],
    "Eventos": ["EVENTOS", "eventos", "Prod. Eventos"],
    "Logística": ["LOGÍSTICA", "Logistica", "logística"],
    "Agronegócio": ["AGRONEGÓCIO", "Agronegocio", "Agro"],
}


def sortear_ponderado(rng, opcoes):
    """Sorteia um item de uma lista [(item, peso), ...]."""
    itens = [item for item, _ in opcoes]
    pesos = [peso for _, peso in opcoes]
    return rng.choices(itens, weights=pesos)[0]


def gerar_cnpj(rng):
    """Gera um CNPJ no formato padrao (sem validar digito verificador - dado ficticio)."""
    bloco1 = rng.randint(10, 99)
    bloco2 = rng.randint(100, 999)
    bloco3 = rng.randint(100, 999)
    filial = "0001"
    dv = rng.randint(10, 99)
    return f"{bloco1}.{bloco2}.{bloco3}/{filial}-{dv}"


def sortear_data_cadastro(rng):
    """80% dos clientes já estavam na base antes do histórico; 20% entraram durante."""
    if rng.random() < 0.20:
        inicio, fim = INICIO_HISTORICO, FIM_HISTORICO
    else:
        inicio, fim = date(2015, 1, 1), INICIO_HISTORICO - timedelta(days=1)
    return inicio + timedelta(days=rng.randrange((fim - inicio).days + 1))


# --- Passo 1: gerar a base limpa -----------------------------------------------------------
def gerar_clientes_limpo(rng):
    linhas = []
    nomes_usados = set()
    for segmento, (quantidade, (limite_min, limite_max)) in CATALOGO.items():
        for _ in range(quantidade):
            while True:
                prefixo = rng.choice(PREFIXOS_RAZAO_SOCIAL)
                nome = rng.choice(NOMES_FANTASIA)
                sufixo = rng.choice(SUFIXOS_SOCIETARIOS)
                razao_social = f"{prefixo} {nome} {sufixo}"
                if razao_social not in nomes_usados:
                    nomes_usados.add(razao_social)
                    break

            cidade, uf = sortear_ponderado(
                rng, [((c, u), p) for c, u, p in CIDADES]
            )

            linhas.append({
                "razao_social": razao_social,
                "cnpj": gerar_cnpj(rng),
                "segmento_cliente": segmento,
                "cidade": cidade,
                "uf": uf,
                "limite_credito": round(rng.uniform(limite_min, limite_max) / 1000) * 1000,
                "data_cadastro": sortear_data_cadastro(rng),
            })

    rng.shuffle(linhas)  # mistura os segmentos para os IDs não ficarem agrupados
    for numero, linha in enumerate(linhas, start=1):
        linha["id_cliente"] = f"CL-{numero:04d}"
    return linhas


# --- Passo 2: versao processed (limpa, tudo como texto para gravar no CSV) ----------------
def formatar_processed(linha):
    return {
        "id_cliente": linha["id_cliente"],
        "razao_social": linha["razao_social"],
        "cnpj": linha["cnpj"],
        "segmento_cliente": linha["segmento_cliente"],
        "cidade": linha["cidade"],
        "uf": linha["uf"],
        "limite_credito": f"{linha['limite_credito']:.2f}",
        "data_cadastro": linha["data_cadastro"].isoformat(),  # aaaa-mm-dd
    }


# --- Passo 3: versao raw (aplica a sujeira prevista no dicionario) ------------------------
def sujar_linha(rng, linha):
    razao_social = linha["razao_social"]
    if rng.random() < P_RAZAO_ABREVIADA:
        palavras = razao_social.split()
        razao_social = " ".join(
            (p[:6].upper() + "." if len(p) > 6 else p.upper()) for p in palavras
        )

    cnpj = linha["cnpj"]
    if rng.random() < P_CNPJ_SEM_MASCARA:
        cnpj = cnpj.replace(".", "").replace("/", "").replace("-", "")

    segmento = linha["segmento_cliente"]
    if rng.random() < P_SEGMENTO_SUJO:
        segmento = rng.choice(VARIANTES_SEGMENTO[segmento])

    cidade = linha["cidade"]
    if rng.random() < P_CIDADE_SUJA:
        cidade = rng.choice([cidade.upper(), cidade.lower()])

    uf = linha["uf"]
    if rng.random() < P_UF_NULA:
        uf = ""
    elif rng.random() < P_UF_MINUSCULA:
        uf = uf.lower()

    if rng.random() < P_DATA_ISO:
        data_cadastro = linha["data_cadastro"].isoformat()
    else:
        data_cadastro = linha["data_cadastro"].strftime("%d/%m/%Y")

    return {
        "id_cliente": linha["id_cliente"],
        "razao_social": razao_social,
        "cnpj": cnpj,
        "segmento_cliente": segmento,
        "cidade": cidade,
        "uf": uf,
        "limite_credito": f"{linha['limite_credito']:.2f}",
        "data_cadastro": data_cadastro,
    }


def gerar_raw(rng, clientes):
    raw = [sujar_linha(rng, linha) for linha in clientes]
    # Duplicados: o mesmo cliente (mesmo CNPJ) cadastrado de novo com outra grafia da razao social.
    for linha in rng.sample(clientes, N_CLIENTES_DUPLICADOS):
        duplicata = sujar_linha(rng, linha)
        raw.insert(rng.randrange(len(raw) + 1), duplicata)
    return raw


def gravar_csv(caminho, linhas):
    # utf-8-sig: o Excel e o Power Query reconhecem os acentos. Separador ';' como no dicionário.
    with open(caminho, "w", encoding="utf-8-sig", newline="") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=COLUNAS, delimiter=";", lineterminator="\n")
        escritor.writeheader()
        escritor.writerows(linhas)


def main():
    rng = random.Random(SEED)  # gerador de numeros aleatorios proprio, sempre iniciado com 42
    clientes = gerar_clientes_limpo(rng)
    processed = [formatar_processed(linha) for linha in clientes]
    raw = gerar_raw(rng, clientes)

    ARQ_RAW.parent.mkdir(parents=True, exist_ok=True)
    ARQ_PROCESSED.parent.mkdir(parents=True, exist_ok=True)
    gravar_csv(ARQ_RAW, raw)
    gravar_csv(ARQ_PROCESSED, processed)

    print(f"raw:       {len(raw)} linhas ({N_CLIENTES_DUPLICADOS} duplicadas) -> {ARQ_RAW.relative_to(RAIZ)}")
    print(f"processed: {len(processed)} linhas -> {ARQ_PROCESSED.relative_to(RAIZ)}")
    print("\nAmostra do raw:")
    for linha in raw[:6]:
        print("  " + " | ".join(linha[coluna] for coluna in COLUNAS))


if __name__ == "__main__":
    main()
