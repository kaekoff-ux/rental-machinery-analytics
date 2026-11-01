"""Confere se os numeros do site (site/index.html) batem com data/processed/.

Verifica: frota por segmento, modelos de cada card, unidades (total e por segmento), 117 ativas,
site/dados_frota.js (modelos, unidades, fichas e fotos), prazo do pedido (30 a 360 dias),
revisoes preventivas, inspecoes de devolucao e telemetria.
Nao altera nenhum arquivo.

Como rodar, a partir da raiz do repositorio:
    python tests/conferir_site.py

Sai com codigo 0 se tudo bate e 1 se algum numero diverge.
"""
import csv
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
ARQ_SITE = RAIZ / "site" / "index.html"
PROCESSED = RAIZ / "data" / "processed"

sys.stdout.reconfigure(encoding="utf-8")

falhas = []


def conferir(descricao, obtido, esperado):
    if obtido == esperado:
        print(f"OK     {descricao}: {obtido}")
    else:
        print(f"FALHA  {descricao}: site={obtido}, dados={esperado}")
        falhas.append(descricao)


def ler_csv(nome):
    with open(PROCESSED / nome, encoding="utf-8-sig", newline="") as arq:
        return list(csv.DictReader(arq, delimiter=";"))


def para_int(texto):
    # No site o milhar tem ponto: "2.039" vira 2039.
    return int(texto.replace(".", ""))


# --- Dados (data/processed/) ---------------------------------------------------------------
equipamentos = ler_csv("cadastro_equipamentos.csv")
ativos = [e for e in equipamentos if e["status_cadastro"] == "Ativo"]
ordens = ler_csv("ordens_manutencao.csv")
leituras = ler_csv("horimetro_telemetria.csv")

html = ARQ_SITE.read_text(encoding="utf-8")

# --- Frota por segmento (cards do pop-up "A frota") ----------------------------------------
# Ex.: <h3>Escavadeira <span class="pilula">26 na frota</span></h3>
cards = re.findall(r'<h3>([^<]+?)\s*<span class="pilula">([\d.]+) na frota</span>', html)
por_segmento = Counter(e["segmento"] for e in ativos)
conferir("cards de segmento", len(cards), len(por_segmento))
for nome, qtd in cards:
    conferir(f"frota: {nome}", para_int(qtd), por_segmento[nome])

# --- Modelos na frota (dentro de cada card, depois de "Onde está") ---------------------------
slides = re.findall(r'<article class="slide slide-maquina[^"]*"[^>]*data-nome="([^"]+)"(.*?)</article>', html, re.S)
for nome, bloco in slides:
    lista = bloco.split("Modelos na frota", 1)[1] if "Modelos na frota" in bloco else ""
    itens = re.findall(r'<span>([^<]+)</span><span class="barra"></span><span class="qtd">(\d+)</span>', lista)
    conferir(
        f"modelos: {nome}",
        {modelo: int(qtd) for modelo, qtd in itens},
        dict(Counter(f'{e["fabricante"]} {e["modelo"]}' for e in ativos if e["segmento"] == nome)),
    )

# --- Unidades (pop-up "Cinco unidades") ----------------------------------------------------
unidades = re.findall(
    r'<article class="slide slide-unidade" data-rotulo="([^"]+)">(.*?)</article>', html, re.S
)
conferir("quantidade de unidades", len(unidades), len({e["filial"] for e in ativos}))
for nome, bloco in unidades:
    total = re.search(r"<strong>([\d.]+)</strong> máquinas ativas", bloco)
    itens = re.findall(
        r'<span>([^<]+)</span><span class="barra"></span><span class="qtd">(\d+)</span>', bloco
    )
    da_unidade = [e for e in ativos if e["filial"] == nome]
    conferir(f"unidade {nome}: máquinas ativas", para_int(total.group(1)), len(da_unidade))
    conferir(
        f"unidade {nome}: por segmento",
        {segmento: int(qtd) for segmento, qtd in itens},
        dict(Counter(e["segmento"] for e in da_unidade)),
    )

# --- 117 ativas --------------------------------------------------------------------------
# Aparece no texto do pop-up de unidades ("117 equipamentos ativos, de escavadeiras...").
for valor in re.findall(r"([\d.]+) equipamentos ativos", html):
    conferir("texto 'equipamentos ativos'", para_int(valor), len(ativos))
soma_unidades = sum(
    para_int(re.search(r"<strong>([\d.]+)</strong> máquinas ativas", bloco).group(1))
    for _, bloco in unidades
)
conferir("soma das unidades = ativos", soma_unidades, len(ativos))

# --- Modelos da frota (site/dados_frota.js, usado no filtro dos cards e no pedido) -----------
# Tem de bater com o cadastro (quantidade e unidades de cada modelo ativo), com as fichas técnicas
# de docs/fichas_tecnicas_modelos.csv e com as fotos que existem em site/img/frota/modelos/.
texto_js = (RAIZ / "site" / "dados_frota.js").read_text(encoding="utf-8")
frota_js = json.loads(texto_js.split("window.FROTA = ", 1)[1].rstrip().rstrip(";"))
fichas = defaultdict(list)
with open(RAIZ / "docs" / "fichas_tecnicas_modelos.csv", encoding="utf-8-sig", newline="") as arq:
    for linha in csv.DictReader(arq, delimiter=";"):
        fichas[f'{linha["fabricante"]} {linha["modelo"]}'].append([linha["campo"], linha["valor"]])

modelos_js = {m["nome"]: m for lista in frota_js.values() for m in lista}
conferir(
    "dados_frota.js: modelos e quantidades",
    {nome: m["quantidade"] for nome, m in modelos_js.items()},
    dict(Counter(f'{e["fabricante"]} {e["modelo"]}' for e in ativos)),
)
conferir(
    "dados_frota.js: unidades de cada modelo",
    {nome: m["unidades"] for nome, m in modelos_js.items()},
    {nome: dict(Counter(e["filial"] for e in ativos if f'{e["fabricante"]} {e["modelo"]}' == nome))
     for nome in modelos_js},
)
conferir("dados_frota.js: fichas iguais ao CSV", {n: m["ficha"] for n, m in modelos_js.items()},
         {n: fichas.get(n, []) for n in modelos_js})
conferir("dados_frota.js: todo modelo ativo tem ficha", [n for n, m in modelos_js.items() if not m["ficha"]], [])
conferir("dados_frota.js: fotos citadas existem",
         [m["foto"] for m in modelos_js.values() if m["foto"] and not (RAIZ / "site" / m["foto"]).exists()], [])

# --- Prazo do pedido de orçamento: 30 a 360 dias ---------------------------------------------
dias = re.search(r'<input type="range" id="sim-dias" name="dias" min="(\d+)" max="(\d+)"', html)
conferir("pedido: prazo mínimo e máximo (dias)", (int(dias.group(1)), int(dias.group(2))), (30, 360))

# --- Revisoes preventivas (pop-up "Revisão programada") -------------------------------------
preventivas = Counter(o["tipo_manutencao"] for o in ordens)["Preventiva"]
conferir(
    "revisões preventivas",
    para_int(re.search(r"([\d.]+) revisões preventivas", html).group(1)),
    preventivas,
)

# --- Inspecoes de devolucao (pop-up "Inspeção em toda devolução") ----------------------------
preditivas = Counter(o["tipo_manutencao"] for o in ordens)["Preditiva"]
conferir(
    "inspeções de devolução",
    para_int(re.search(r'slide-destaque">([\d.]+)</p>\s*<h3>Inspeção em toda devolução', html).group(1)),
    preditivas,
)

# --- Telemetria (pop-up "Horas acompanhadas de perto") ---------------------------------------
# Ex.: <p class="slide-destaque">40 de 117</p>
com_telemetria = {l["id_equipamento"] for l in leituras if l["fonte_leitura"] == "Telemetria"}
ids_ativos = {e["id_equipamento"] for e in ativos}
telemetria = re.search(r'slide-destaque">(\d+) de (\d+)</p>', html)
conferir("telemetria: ativas com telemetria", int(telemetria.group(1)), len(com_telemetria & ids_ativos))
conferir("telemetria: total de ativas", int(telemetria.group(2)), len(ativos))

print()
if falhas:
    print(f"{len(falhas)} verificação(ões) falharam.")
    sys.exit(1)
print("Todas as verificações passaram.")
