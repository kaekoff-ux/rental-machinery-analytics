"""Gera as fotos de cada modelo da frota em site/img/frota/modelos/<fabricante-modelo>.jpg.

Duas origens, nesta ordem:
1. O painel docs/imagens/frota/painel_modelos.jpeg (imagem gerada por IA, enviada pelo usuário em
   01/11/2026), com 30 quadros e o nome do modelo escrito no canto. O nome do canto é apagado e os
   logotipos/textos das máquinas são borrados (lista LOGOS): as imagens são de IA e o site mostra
   só o equipamento.
2. Imagens avulsas em docs/imagens/frota/modelos/<fabricante-modelo>.(jpg|jpeg|png|webp), por
   exemplo uma imagem nova feita no Gemini. Quando existe, ela substitui o quadro do painel. Gere
   a imagem já sem logotipo (ver docs/prompts_imagens_frota.md); o script só reduz o tamanho.

Quadros que NÃO são usados, porque a imagem não confere com o nome:
    - "Volvo EC210B": mostra um gerador rebocável;
    - "Hyundai HX220L": mostra uma escavadeira com a marca Volvo;
    - "Atlas Copco QAS150": mostra um guindaste XCMG;
    - "Caterpilall 32220" e "Caterpillar 320UC": empilhadeiras que não existem no cadastro.
O Komatsu PC210 não tem quadro. Esses modelos aparecem no site sem foto.
As plataformas e duas empilhadeiras estão com o nome antigo (a diesel) no painel; a foto é usada
para a versão GLP/elétrica da mesma marca, que tem o mesmo formato (ver docs/fichas_tecnicas_frota.md).

Rodar a partir da raiz do repositório (depois, rode src/site/gerar_dados_frota.py):
    python src/site/recortar_modelos_frota.py
Depende do Pillow (pip install pillow).
"""
from pathlib import Path

from PIL import Image, ImageFilter

RAIZ = Path(__file__).resolve().parents[2]
PAINEL = RAIZ / "docs" / "imagens" / "frota" / "painel_modelos.jpeg"
AVULSAS = RAIZ / "docs" / "imagens" / "frota" / "modelos"
DESTINO = RAIZ / "site" / "img" / "frota" / "modelos"
QUALIDADE = 82
TAMANHO_MAXIMO = (680, 252)  # mesmo porte dos quadros do painel
EXTENSOES = (".jpg", ".jpeg", ".png", ".webp")

# Grade do painel (pixels da imagem original, 2816 x 1536), medida pelos vãos brancos entre os quadros.
FAIXAS = [(8, 274), (287, 535), (548, 762), (775, 1007), (1020, 1255), (1268, 1524)]
QUADROS = [
    [(11, 489), (502, 944), (957, 1401), (1414, 1864), (1877, 2326), (2339, 2805)],
    [(10, 505), (518, 967), (980, 1401), (1414, 1864), (1877, 2326), (2339, 2805)],
    [(10, 692), (707, 1401), (1414, 1864), (1878, 2326), (2339, 2805)],
    [(10, 692), (707, 1401), (1415, 2110), (2125, 2805)],
    [(10, 691), (707, 1401), (1415, 2110), (2125, 2805)],
    [(10, 692), (707, 1401), (1415, 2110), (2125, 2805)],
]

# (faixa, quadro) -> nome do arquivo. Mesmo nome que src/site/gerar_dados_frota.py monta a partir de
# fabricante + modelo do cadastro. Quadro fora desta lista não é usado (ver docstring).
USADOS = {
    (0, 0): "yale-glp50vx", (0, 1): "toyota-8fgu25", (0, 2): "hyster-h80ft", (0, 3): "clark-c25l",
    (1, 0): "caterpillar-320d", (1, 1): "caterpillar-320gc",
    (1, 4): "cummins-c150d5", (1, 5): "cummins-c250d5",
    (2, 0): "caterpillar-xq125", (2, 1): "liebherr-ltm-1050-3-1", (2, 3): "xcmg-qy25k", (2, 4): "grove-rt540e",
    (3, 0): "skyjack-sj45aje", (3, 1): "genie-z45dc", (3, 2): "haulotte-ha16e", (3, 3): "jlg-e600jp",
    (4, 0): "caterpillar-950h", (4, 1): "volvo-l60h", (4, 2): "case-821f", (4, 3): "xcmg-lw500",
    (5, 0): "jcb-3cx", (5, 1): "case-580n", (5, 2): "caterpillar-416f", (5, 3): "new-holland-b95b",
}

# Logotipos e textos pintados nas máquinas do painel: (esquerda, topo, direita, base) em pixels do
# recorte já pronto (mesmas coordenadas da foto em site/img/frota/modelos/). Medidos em 01/11/2026.
LOGOS = {
    "case-580n": [(308, 92, 368, 122), (495, 15, 535, 80)],
    "case-821f": [(465, 50, 525, 78)],
    "caterpillar-320d": [(198, 60, 240, 86), (366, 130, 392, 168)],
    "caterpillar-320gc": [(215, 53, 246, 73), (368, 128, 392, 150)],
    "caterpillar-416f": [(468, 30, 500, 62), (335, 85, 366, 112), (280, 85, 312, 105)],
    "caterpillar-950h": [(432, 50, 480, 76)],
    "caterpillar-xq125": [(258, 52, 300, 92), (376, 68, 424, 108), (448, 58, 478, 70)],
    "clark-c25l": [(186, 35, 214, 110), (262, 155, 325, 176)],
    "cummins-c150d5": [(200, 108, 250, 155)],
    "cummins-c250d5": [(252, 104, 290, 155)],
    "genie-z45dc": [(432, 85, 490, 116), (452, 113, 472, 124), (178, 104, 196, 114)],
    "grove-rt540e": [(132, 48, 195, 72)],
    "haulotte-ha16e": [(330, 46, 398, 68), (392, 114, 420, 128), (225, 108, 252, 124)],
    "hyster-h80ft": [(198, 38, 225, 102), (280, 174, 326, 194), (296, 152, 324, 166)],
    "jcb-3cx": [(302, 84, 338, 104), (444, 46, 472, 92)],
    "jlg-e600jp": [(522, 80, 552, 102), (156, 80, 182, 92), (228, 80, 262, 92)],
    "liebherr-ltm-1050-3-1": [(244, 50, 335, 74), (306, 114, 370, 128)],
    "new-holland-b95b": [(508, 25, 540, 95), (355, 106, 394, 124)],
    "skyjack-sj45aje": [(240, 72, 345, 96), (116, 154, 148, 170), (390, 134, 475, 148)],
    "toyota-8fgu25": [(160, 60, 194, 102), (250, 134, 316, 154)],
    "volvo-l60h": [(466, 54, 494, 72)],
    "xcmg-lw500": [(340, 45, 398, 108), (496, 46, 534, 62), (450, 58, 480, 74)],
    "xcmg-qy25k": [(160, 52, 218, 74), (262, 116, 294, 130)],
    "yale-glp50vx": [(213, 34, 240, 82), (324, 156, 350, 172)],
}

MARGEM = 7          # tira a borda arredondada do quadro
FAIXA_ROTULO = 62   # altura (px) da faixa do topo onde fica o nome do modelo
ESCURO = 150        # pixel cinza mais escuro que isso, na faixa do rótulo, é letra


def letra(rgb):
    """Letra do rótulo: cinza neutro e escuro. Peça colorida da máquina (cesto laranja) não conta."""
    r, g, b = rgb
    return max(r, g, b) - min(r, g, b) < 30 and (r + g + b) / 3 < ESCURO


def cobrir_rotulo(quadro):
    """Apaga o nome do modelo (canto superior esquerdo): só os pixels das letras viram cor de fundo."""
    px = quadro.load()
    largura = quadro.width
    # O nome começa na esquerda; termina quando aparecem 16 colunas seguidas sem letra (o espaço
    # entre palavras é menor; a torre de uma empilhadeira ou o cesto de uma plataforma ficam além).
    fim, vazias = 0, 0
    for x in range(int(largura * 0.75)):
        if any(letra(px[x, y]) for y in range(4, FAIXA_ROTULO)):
            fim, vazias = x, 0
        elif fim:
            vazias += 1
            if vazias >= 16:
                break
    if not fim:
        return quadro
    linhas = [y for y in range(4, FAIXA_ROTULO) if any(letra(px[x, y]) for x in range(fim + 1))]
    topo, base = max(0, linhas[0] - 4), min(FAIXA_ROTULO, linhas[-1] + 4)
    cor_fundo = quadro.getpixel((largura - 12, 6))  # canto de cima à direita: só fundo

    # Dentro da área do nome, todo pixel cinza vira fundo (letra e o contorno claro em volta dela);
    # pixel colorido fica, porque é peça da máquina.
    mascara = Image.new("L", quadro.size, 0)
    m = mascara.load()
    for x in range(fim + 5):
        for y in range(topo, base):
            r, g, b = px[x, y]
            if max(r, g, b) - min(r, g, b) < 30:
                m[x, y] = 255
    mascara = mascara.filter(ImageFilter.GaussianBlur(1))
    quadro.paste(Image.new("RGB", quadro.size, cor_fundo), (0, 0), mascara)
    return quadro


def borrar_logos(quadro, areas):
    """Desfoque forte em cada área: a marca fica ilegível e a forma da máquina continua."""
    for area in areas:
        trecho = quadro.crop(area)
        for _ in range(3):
            trecho = trecho.filter(ImageFilter.GaussianBlur(6))
        quadro.paste(trecho, area[:2])
    return quadro


def salvar(imagem, nome, origem):
    imagem.save(DESTINO / f"{nome}.jpg", "JPEG", quality=QUALIDADE, optimize=True, progressive=True)
    print(f"site/img/frota/modelos/{nome}.jpg  {imagem.width}x{imagem.height}  ({origem})")


def main():
    DESTINO.mkdir(parents=True, exist_ok=True)
    painel = Image.open(PAINEL).convert("RGB")
    for (faixa, coluna), nome in USADOS.items():
        y0, y1 = FAIXAS[faixa]
        x0, x1 = QUADROS[faixa][coluna]
        quadro = painel.crop((x0 + MARGEM, y0 + MARGEM, x1 - MARGEM, y1 - MARGEM))
        quadro = borrar_logos(cobrir_rotulo(quadro), LOGOS.get(nome, []))
        salvar(quadro, nome, "painel")

    # Imagem avulsa (ex.: feita no Gemini) substitui o quadro do painel, ou cobre um modelo sem quadro.
    for arquivo in sorted(AVULSAS.glob("*")) if AVULSAS.exists() else []:
        if arquivo.suffix.lower() not in EXTENSOES:
            continue
        with Image.open(arquivo) as imagem:
            imagem = imagem.convert("RGB")
            imagem.thumbnail(TAMANHO_MAXIMO, Image.LANCZOS)
            salvar(imagem, arquivo.stem.lower(), f"avulsa: {arquivo.name}")


if __name__ == "__main__":
    main()
