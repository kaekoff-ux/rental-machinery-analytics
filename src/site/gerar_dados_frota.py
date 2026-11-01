"""Gera site/dados_frota.js: os modelos da frota (quantidade, unidades, ficha, foto) e a manutenção.

Junta quatro fontes:
    data/processed/cadastro_equipamentos.csv  modelos e quantidades (só máquinas com status Ativo)
    docs/fichas_tecnicas_modelos.csv          ficha técnica de cada modelo (valores de manual/ficha
                                              do fabricante; a fonte fica no CSV, não vai para o site)
    docs/manutencao_fabricante.csv            plano de manutenção recomendado pelo fabricante, por
                                              tipo de máquina, e notas de modelo (fonte só no CSV)
    site/img/frota/modelos/                   foto de cada modelo (src/site/recortar_modelos_frota.py)

O site lê window.FROTA no filtro de modelo dos cards da Frota e no pedido de orçamento, e
window.MANUTENCAO no bloco de manutenção dos cards e na contagem de revisões do pedido.
Rodar a partir da raiz do repositório, sempre que o cadastro, as fichas ou as fotos mudarem:
    python src/site/gerar_dados_frota.py
Só usa a biblioteca padrão do Python.
"""
import csv
import json
import re
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
ARQ_CADASTRO = RAIZ / "data" / "processed" / "cadastro_equipamentos.csv"
ARQ_FICHAS = RAIZ / "docs" / "fichas_tecnicas_modelos.csv"
ARQ_MANUTENCAO = RAIZ / "docs" / "manutencao_fabricante.csv"
PASTA_FOTOS = RAIZ / "site" / "img" / "frota" / "modelos"
ARQ_SAIDA = RAIZ / "site" / "dados_frota.js"


def ler_csv(caminho):
    with open(caminho, encoding="utf-8-sig", newline="") as arq:
        return list(csv.DictReader(arq, delimiter=";"))


def nome_arquivo(fabricante, modelo):
    """'Liebherr', 'LTM 1050-3.1' -> 'liebherr-ltm-1050-3-1' (mesmo nome usado no recorte das fotos)."""
    texto = unicodedata.normalize("NFD", f"{fabricante} {modelo}").encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", texto.lower()).strip("-")


def main():
    ativos = [l for l in ler_csv(ARQ_CADASTRO) if l["status_cadastro"] == "Ativo"]
    fichas = defaultdict(list)
    for linha in ler_csv(ARQ_FICHAS):
        fichas[(linha["fabricante"], linha["modelo"])].append([linha["campo"], linha["valor"]])

    # Manutenção: linhas sem modelo formam o plano do tipo de máquina; linhas com modelo viram notas
    # daquele modelo. A coluna conta_no_simulador marca o intervalo usado para contar revisões no pedido.
    manutencao = {}
    notas_manutencao = defaultdict(list)
    for linha in ler_csv(ARQ_MANUTENCAO):
        item = [linha["intervalo"], linha["servico"]]
        if linha["modelo"]:
            notas_manutencao[linha["modelo"]].append(item)
            continue
        tipo = manutencao.setdefault(linha["segmento"], {"plano": [], "revisao_horas": None})
        tipo["plano"].append(item)
        if linha["conta_no_simulador"] == "sim":
            tipo["revisao_horas"] = int(linha["horas"])

    por_modelo = defaultdict(list)
    for maquina in ativos:
        por_modelo[(maquina["segmento"], maquina["fabricante"], maquina["modelo"])].append(maquina)

    frota = defaultdict(list)
    for (segmento, fabricante, modelo), maquinas in por_modelo.items():
        arquivo = nome_arquivo(fabricante, modelo)
        foto = PASTA_FOTOS / f"{arquivo}.jpg"
        unidades = Counter(m["filial"] for m in maquinas)
        frota[segmento].append({
            "fabricante": fabricante,
            "modelo": modelo,
            "nome": f"{fabricante} {modelo}",
            "quantidade": len(maquinas),
            "unidades": dict(sorted(unidades.items(), key=lambda kv: (-kv[1], kv[0]))),
            "ficha": fichas.get((fabricante, modelo), []),
            "manutencao": notas_manutencao.get(f"{fabricante} {modelo}", []),
            "foto": f"img/frota/modelos/{arquivo}.jpg" if foto.exists() else None,
        })
    for modelos in frota.values():
        modelos.sort(key=lambda m: (-m["quantidade"], m["nome"]))

    # Avisos (não param o script): modelo ativo sem ficha ou sem foto, e ficha de modelo que saiu da frota.
    for segmento, modelos in frota.items():
        for m in modelos:
            if not m["ficha"]:
                print(f"AVISO: sem ficha técnica: {m['nome']} ({segmento})")
            if not m["foto"]:
                print(f"aviso: sem foto: {m['nome']} ({segmento})")
    nomes_ativos = {(f, m) for (_, f, m) in por_modelo}
    for fabricante, modelo in fichas:
        if (fabricante, modelo) not in nomes_ativos:
            print(f"AVISO: ficha de modelo sem máquina ativa: {fabricante} {modelo}")
    for segmento in frota:
        if not manutencao.get(segmento, {}).get("revisao_horas"):
            print(f"AVISO: sem plano de manutenção (ou sem intervalo para o simulador): {segmento}")
    nomes_completos = {f"{f} {m}" for (_, f, m) in por_modelo}
    for nome in notas_manutencao:
        if nome not in nomes_completos:
            print(f"AVISO: nota de manutenção de modelo sem máquina ativa: {nome}")

    corpo = json.dumps(frota, ensure_ascii=False, indent=1)
    corpo_manutencao = json.dumps(manutencao, ensure_ascii=False, indent=1)
    ARQ_SAIDA.write_text(
        "// Gerado por src/site/gerar_dados_frota.py a partir do cadastro (só Ativo), de\n"
        "// docs/fichas_tecnicas_modelos.csv, docs/manutencao_fabricante.csv e das fotos em\n"
        "// site/img/frota/modelos/. Não edite à mão.\n"
        f"window.FROTA = {corpo};\n"
        f"window.MANUTENCAO = {corpo_manutencao};\n",
        encoding="utf-8",
    )
    total = sum(len(m) for m in frota.values())
    print(f"site/dados_frota.js: {total} modelos em {len(frota)} tipos de máquina")


if __name__ == "__main__":
    main()
