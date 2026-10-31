"""Gera as versões leves das imagens e o vídeo usados pelo site (pastas site/img/ e site/video/).

Lê as originais em docs/imagens/ (história), docs/imagens/frota/ (equipamentos) e docs/videos/,
reduz as imagens para no máximo 1400 px de largura e salva em JPEG de qualidade 80, sem
metadados. O vídeo é só copiado: não há ffmpeg nesta máquina para recomprimir.
Foto da frota que ainda não existe é só avisada; o site funciona sem ela. A lista das fotos
que existem vai para site/img/frota/disponiveis.js, para o site não pedir arquivos inexistentes.

Rodar a partir da raiz do repositório:
    python src/site/otimizar_imagens.py
Depende do Pillow (pip install pillow).
"""

import json
import shutil
from pathlib import Path

from PIL import Image

RAIZ = Path(__file__).resolve().parents[2]
ORIGEM = RAIZ / "docs" / "imagens"
DESTINO = RAIZ / "site" / "img"
LARGURA_MAXIMA = 1400
QUALIDADE = 80

# original: (nome no site, recorte (esquerda, topo, direita, base) em pixels, ou None).
# Os recortes valem para as imagens atuais; se trocar a imagem, revise ou apague o recorte.
HISTORIA = {
    # tira a moldura preta que veio embutida no retrato
    "01_seu_jose.jpg": ("seu-jose.jpg", (24, 16, 1000, 992)),
    # tira o letreiro com o erro "Equipamontos" (topo) e o fio claro da borda esquerda
    "02_barracao_1992.jpg": ("barracao-1992.jpg", (2, 180, 1376, 768)),
    "03_unidade_atual.jpg": ("unidade-atual.jpg", None),
    # mural de recordações do slide 2016 (pop-up Quem somos)
    "07_2016.jpeg": ("mural-2016.jpg", None),
    # fundos dos slides de Missão, Visão e Valores (pop-up Quem somos)
    "04_Missão.jpeg": ("missao.jpg", None),
    "05_Visão.jpeg": ("visao.jpg", None),
    "06_Valores.jpeg": ("valores.jpg", None),
}

# Animação do topo da página (gerada no Gemini a partir de 03_unidade_atual.jpg).
VIDEOS = {
    RAIZ / "docs" / "videos" / "01_hero_animacao.mp4": RAIZ / "site" / "video" / "hero.mp4",
}

# Mesmos nomes de docs/prompts_imagens_frota.md e de site/index.html.
FROTA = [
    "escavadeira",
    "retroescavadeira",
    "pa-carregadeira",
    "guindaste",
    "empilhadeira",
    "plataforma-elevatoria",
    "gerador",
]
EXTENSOES = (".jpg", ".jpeg", ".png", ".webp")


def otimizar(origem, destino, recorte=None):
    with Image.open(origem) as imagem:
        imagem = imagem.convert("RGB")
        if recorte:
            imagem = imagem.crop(recorte)
        if imagem.width > LARGURA_MAXIMA:
            altura = round(imagem.height * LARGURA_MAXIMA / imagem.width)
            imagem = imagem.resize((LARGURA_MAXIMA, altura), Image.LANCZOS)
        destino.parent.mkdir(parents=True, exist_ok=True)
        imagem.save(destino, "JPEG", quality=QUALIDADE, optimize=True, progressive=True)
        largura, altura = imagem.size
    kb = destino.stat().st_size // 1024
    print(f"ok  {origem.relative_to(RAIZ)} -> {destino.relative_to(RAIZ)} ({largura}x{altura}, {kb} KB)")


def achar_original_frota(nome):
    for extensao in EXTENSOES:
        caminho = ORIGEM / "frota" / f"{nome}{extensao}"
        if caminho.exists():
            return caminho
    return None


def gravar_lista_frota(disponiveis):
    destino = DESTINO / "frota" / "disponiveis.js"
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(
        "// Gerado por src/site/otimizar_imagens.py: fotos da frota que existem em site/img/frota/.\n"
        f"window.FOTOS_FROTA = {json.dumps(disponiveis)};\n",
        encoding="utf-8",
    )
    print(f"ok  lista da frota -> {destino.relative_to(RAIZ)} ({len(disponiveis)} de {len(FROTA)} fotos)")


def main():
    for nome_origem, (nome_destino, recorte) in HISTORIA.items():
        otimizar(ORIGEM / nome_origem, DESTINO / nome_destino, recorte)

    disponiveis = []
    for nome in FROTA:
        original = achar_original_frota(nome)
        if original:
            otimizar(original, DESTINO / "frota" / f"{nome}.jpg")
            disponiveis.append(nome)
        else:
            print(f"--  ainda sem foto: docs/imagens/frota/{nome}.jpg")
    gravar_lista_frota(disponiveis)

    for origem, destino in VIDEOS.items():
        if not origem.exists():
            print(f"--  ainda sem vídeo: {origem.relative_to(RAIZ)}")
            continue
        destino.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(origem, destino)
        print(f"ok  {origem.relative_to(RAIZ)} -> {destino.relative_to(RAIZ)} ({destino.stat().st_size // 1024} KB, sem recompressão)")


if __name__ == "__main__":
    main()
