"""Gera site/dados_frota.js: os modelos da frota, com quantidade, unidades, ficha técnica e foto.

Junta três fontes:
    data/processed/cadastro_equipamentos.csv  modelos e quantidades (só máquinas com status Ativo)
    docs/fichas_tecnicas_modelos.csv          ficha técnica de cada modelo (valores de manual/ficha
                                              do fabricante; a fonte fica no CSV, não vai para o site)
    site/img/frota/modelos/                   foto de cada modelo (src/site/recortar_modelos_frota.py)

O site lê window.FROTA no filtro de modelo dos cards da Frota e no pedido de orçamento.
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

    corpo = json.dumps(frota, ensure_ascii=False, indent=1)
    ARQ_SAIDA.write_text(
        "// Gerado por src/site/gerar_dados_frota.py a partir do cadastro (só Ativo), de\n"
        "// docs/fichas_tecnicas_modelos.csv e das fotos em site/img/frota/modelos/. Não edite à mão.\n"
        f"window.FROTA = {corpo};\n",
        encoding="utf-8",
    )
    total = sum(len(m) for m in frota.values())
    print(f"site/dados_frota.js: {total} modelos em {len(frota)} tipos de máquina")


if __name__ == "__main__":
    main()
