# Imagens da frota: lista de equipamentos e prompts

> A LocaMaq é uma empresa fictícia (case de portfólio). As imagens são geradas por IA, e o site
> informa isso.

## Fotos por modelo (regra atual, decidida pelo usuário em 01/11/2026)

O site mostra **uma foto por modelo** no card da Frota e no pedido de orçamento. Como são imagens
de IA, a máquina pode ter as cores e o formato do modelo real, mas **sem logotipo nem texto**: o
site mostra só o equipamento. Nas fotos que vêm do painel (`docs/imagens/frota/painel_modelos.jpeg`)
os logotipos são borrados pelo script de recorte; imagens novas já devem vir sem logotipo.

### Como refazer uma foto no Gemini

1. No Gemini (gemini.google.com), peça a imagem com o prompt do modelo (lista abaixo).
2. Baixe a imagem e salve em `docs/imagens/frota/modelos/` com o nome exato da lista (pode ser
   `.jpg` ou `.png`). A imagem dessa pasta substitui o quadro do painel.
3. Na raiz do repositório, rode:
   `python src/site/recortar_modelos_frota.py`, depois `python src/site/gerar_dados_frota.py` e
   `python tests/conferir_site.py`.
4. Se a imagem vier com letras ou logotipo na máquina, peça de novo no Gemini ("sem nenhum texto,
   letra ou logotipo na máquina"), ou avise para borrar a área no script.

Situação em 01/11/2026: os 28 modelos têm imagem do Gemini nessa pasta. O painel ficou só como
reserva, caso uma imagem avulsa seja apagada.

Modelo de prompt (troque só o trecho entre colchetes):

```text
Fotografia de estúdio realista de [MÁQUINA], inteira no quadro, vista em três quartos pela
frente, sobre fundo cinza-claro liso e uniforme, com sombra suave no chão. Sem nenhum texto,
letra, número, logotipo ou adesivo na máquina. Iluminação difusa de estúdio, cores fiéis ao
fabricante. Formato horizontal 16:9.
```

| Arquivo (em `docs/imagens/frota/modelos/`) | [MÁQUINA] | Por quê |
|---|---|---|
| `volvo-ec210b.jpg` | uma escavadeira hidráulica sobre esteiras de cerca de 21 toneladas, como a Volvo EC210B, pintura amarela com cabine e contrapeso cinza-escuros | o quadro do painel mostra um gerador |
| `hyundai-hx220l.jpg` | uma escavadeira hidráulica sobre esteiras de cerca de 22 toneladas, como a Hyundai HX220L, pintura amarela com detalhes cinza-escuros | o quadro do painel mostra uma escavadeira Volvo |
| `komatsu-pc210.jpg` | uma escavadeira hidráulica sobre esteiras de cerca de 22 toneladas, como a Komatsu PC210, pintura amarela com detalhes pretos | não tem quadro no painel |
| `atlas-copco-qas150.jpg` | um gerador a diesel móvel de 150 kVA em cabine metálica silenciada, montado sobre carreta de dois eixos com engate, como o Atlas Copco QAS 150 | o quadro do painel mostra um guindaste |
| `grove-rt540e.jpg` | um guindaste para terreno acidentado de cerca de 35 toneladas, dois eixos, uma cabine só e lança telescópica de quatro seções, como o Grove RT540E, pintura vermelha e cinza | o quadro do painel saiu com "GFOVE" na lança (hoje borrado) |

Opcional: as plataformas (JLG E600JP, Genie Z-45 DC, Skyjack SJ45 AJE+, Haulotte HA16 E) e duas
empilhadeiras (Yale GLP50VX, Clark C25L) usam a foto da versão antiga da mesma marca. Para refazer,
use o nome de arquivo da foto atual em `site/img/frota/modelos/` (ex.: `jlg-e600jp.jpg`) e
descreva a versão elétrica ou a GLP.

## Primeira versão: uma foto por tipo de máquina (substituída em 01/11/2026)

O que segue é o plano original, com uma foto por tipo de máquina e sem marcas no prompt. Ficou como
referência das cenas.

## A lista (7 segmentos, 117 equipamentos ativos)

Números e modelos tirados de `data/processed/cadastro_equipamentos.csv` (seed 42), só os ativos.
A coluna "referência" serve apenas para você pesquisar como a máquina é; **não vai no prompt**.

| # | Segmento | Ativos | O que existe no cadastro | Referência (só para pesquisa) | Nome do arquivo |
|---|---|---|---|---|---|
| 1 | Escavadeira | 26 | Escavadeira hidráulica sobre esteiras, porte médio (~20 a 22 t) | Caterpillar 320GC e 320D, Volvo EC210B, Hyundai HX220L, Komatsu PC210 | `escavadeira.jpg` |
| 2 | Gerador | 23 | Gerador a diesel em cabine silenciada, 125 a 250 kVA | Atlas Copco QAS150, Cummins C150D5 e C250D5, Caterpillar XQ125 | `gerador.jpg` |
| 3 | Retroescavadeira | 17 | Trator com pá carregadeira na frente e braço escavador atrás | JCB 3CX, Caterpillar 416F, Case 580N, New Holland B95B | `retroescavadeira.jpg` |
| 4 | Pá-carregadeira | 15 | Carregadeira de rodas articulada, porte médio | Volvo L60H, XCMG LW500, Case 821F, Caterpillar 950H | `pa-carregadeira.jpg` |
| 5 | Empilhadeira | 14 | Empilhadeira contrabalançada a combustão, movida a GLP | Yale GLP50VX, Hyster H80FT, Toyota 8FGU25, Clark C25L | `empilhadeira.jpg` |
| 6 | Plataforma elevatória | 12 | Plataforma articulada de lança, elétrica a bateria (não há tesoura no cadastro), cerca de 16 a 20 m | Skyjack SJ45 AJE+, Genie Z-45 DC, Haulotte HA16 E, JLG E600JP | `plataforma-elevatoria.jpg` |
| 7 | Guindaste | 10 | Guindaste móvel sobre rodas com lança telescópica, 25 a 50 t | Liebherr LTM 1050-3.1, XCMG QY25K, Grove RT540E | `guindaste.jpg` |

## Regras para as 7 imagens parecerem um conjunto

- **Mesma pintura:** máquina laranja queimado (`#C8651B`) com detalhes verde-musgo escuro
  (`#4A5D3A`), as cores da paleta da LocaMaq.
- **Nenhum texto:** sem marca, logotipo, número de modelo, placa ou adesivo com letras.
- **Mesmo enquadramento:** máquina inteira, centralizada, vista em três quartos pela frente,
  câmera na altura dos olhos, com espaço em volta (o site pode cortar as bordas).
- **Mesma luz:** fim de tarde, sol baixo e tons quentes; aparência de foto documental, com leve
  granulação, igual ao tom das fotos da história.
- **Mesmo lugar:** interior de São Paulo, terra vermelha, céu limpo, vegetação ao fundo.
- **Formato:** horizontal 4:3 (16:9 também serve), pelo menos 1200 px de largura.
- **Pessoas:** de preferência nenhuma. Se aparecer alguém, pequeno, de costas, com capacete e colete.

## Modelo de prompt

Troque só os dois trechos entre colchetes:

```text
Fotografia documental realista de [EQUIPAMENTO], [CENA]. A máquina é pintada de laranja
queimado (#C8651B) com detalhes em verde-musgo escuro (#4A5D3A), sem nenhuma marca, logotipo,
número ou texto legível. Máquina inteira no quadro, centralizada, vista em três quartos pela
frente, câmera na altura dos olhos, com espaço em volta. Interior de São Paulo, terra vermelha,
céu limpo, vegetação ao fundo. Luz natural de fim de tarde, tons quentes, leve granulação de
filme. Formato horizontal 4:3.
```

## O que colocar nos colchetes

Cada cena usa um setor que existe em `clientes.csv` (construção civil, infraestrutura, indústria,
eventos, mineração, logística), para a imagem combinar com os dados do case.

| Segmento | [EQUIPAMENTO] | [CENA] |
|---|---|---|
| Escavadeira | uma escavadeira hidráulica sobre esteiras, de porte médio, com braço e caçamba | abrindo a fundação de um prédio em um canteiro de obras |
| Gerador | um gerador a diesel dentro de uma cabine metálica fechada e silenciada, montado sobre uma carreta de dois eixos | ao lado da tenda branca de um evento ao ar livre, com cabos grossos no chão |
| Retroescavadeira | uma retroescavadeira, trator com pá carregadeira na frente e braço escavador atrás, com as sapatas estabilizadoras apoiadas no chão | abrindo uma vala para rede de esgoto em uma rua de bairro |
| Pá-carregadeira | uma pá-carregadeira de rodas articulada, de porte médio, com a caçamba erguida | carregando pedra britada em uma pedreira |
| Empilhadeira | uma empilhadeira a combustão contrabalançada, movida a GLP, com o cilindro de gás preso atrás do banco, garfos e torre de elevação | levando um palete de sacos de cimento no pátio de um depósito de materiais |
| Plataforma elevatória | uma plataforma elevatória articulada elétrica sobre rodas, sem escapamento, com lança dobrada e cesto com guarda-corpo | com o cesto erguido junto à fachada de um galpão em construção |
| Guindaste | um guindaste móvel sobre rodas, com lança telescópica estendida e patolas abertas e apoiadas no chão | içando uma viga metálica na obra de um galpão industrial |

## Onde salvar

Ver "Fotos por modelo", no início deste documento: as fotos do site agora são por modelo e ficam
em `docs/imagens/frota/modelos/` (imagens avulsas) ou no painel `docs/imagens/frota/painel_modelos.jpeg`.

## Imagens da história que ainda pedem ajuste

- `docs/imagens/02_barracao_1992.jpg` (gerada em 30/10/2026): o letreiro agora está legível, mas
  diz "Equipamontos" em vez de "Equipamentos". O site corta o letreiro por enquanto. Se gerar de
  novo, peça o texto exato "LOCAÇÃO DE FERRAMENTAS" ou "sinal pintado à mão, sem texto legível".
- `docs/imagens/03_unidade_atual.jpg`: as máquinas continuam amarelas. Para alinhar com a frota,
  gerar de novo com "máquinas pintadas de laranja queimado com detalhes verde-escuros".
