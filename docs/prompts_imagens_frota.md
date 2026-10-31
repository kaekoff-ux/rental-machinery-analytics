# Imagens da frota: lista de equipamentos e prompts

> A LocaMaq é uma empresa fictícia (case de portfólio). Estas imagens serão geradas por IA, e o
> site informa isso. Não citar marcas nem modelos reais no prompt: os geradores erram letras e
> logotipos, e uma marca real na imagem sugeriria parceria que não existe.

## A lista (7 segmentos, 117 equipamentos ativos)

Números e modelos tirados de `data/processed/cadastro_equipamentos.csv` (seed 42), só os ativos.
A coluna "referência" serve apenas para você pesquisar como a máquina é; **não vai no prompt**.

| # | Segmento | Ativos | O que existe no cadastro | Referência (só para pesquisa) | Nome do arquivo |
|---|---|---|---|---|---|
| 1 | Escavadeira | 26 | Escavadeira hidráulica sobre esteiras, porte médio (~20 a 22 t) | Caterpillar 320GC e 320D, Volvo EC210B, Hyundai HX220L, Komatsu PC210 | `escavadeira.jpg` |
| 2 | Gerador | 23 | Gerador a diesel em cabine silenciada, 125 a 250 kVA | Atlas Copco QAS150, Cummins C150D5 e C250D5, Caterpillar XQ125 | `gerador.jpg` |
| 3 | Retroescavadeira | 17 | Trator com pá carregadeira na frente e braço escavador atrás | JCB 3CX, Caterpillar 416F, Case 580N, New Holland B95B | `retroescavadeira.jpg` |
| 4 | Pá-carregadeira | 15 | Carregadeira de rodas articulada, porte médio | Volvo L60H, XCMG LW500, Case 821F, Caterpillar 950H | `pa-carregadeira.jpg` |
| 5 | Empilhadeira | 14 | Empilhadeira a combustão contrabalançada, 2,5 a 8 t | Yale GDP50VX, Hyster H80FT, Toyota 8FGU25, Clark C25 | `empilhadeira.jpg` |
| 6 | Plataforma elevatória | 12 | Plataforma articulada de lança (não há tesoura no cadastro), 16 a 21 m | Skyjack SJ63AJ, Genie Z45, Haulotte HA16, JLG 600AJ | `plataforma-elevatoria.jpg` |
| 7 | Guindaste | 10 | Guindaste móvel sobre rodas com lança telescópica, 25 a 50 t | Liebherr LTM1050, XCMG QY25K, Grove RT540E | `guindaste.jpg` |

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
| Empilhadeira | uma empilhadeira a combustão contrabalançada, com garfos e torre de elevação | levando um palete de sacos de cimento no pátio de um depósito de materiais |
| Plataforma elevatória | uma plataforma elevatória articulada sobre rodas, com lança dobrada e cesto com guarda-corpo | com o cesto erguido junto à fachada de um galpão em construção |
| Guindaste | um guindaste móvel sobre rodas, com lança telescópica estendida e patolas abertas e apoiadas no chão | içando uma viga metálica na obra de um galpão industrial |

## Onde salvar

1. Salve cada imagem em `docs/imagens/frota/` com o nome exato da tabela (minúsculas, sem
   acento, com hífen).
2. Rode `python src/site/otimizar_imagens.py` na raiz do repositório. Ele grava versões leves em
   `site/img/frota/`, que é a pasta que o site usa.
3. Abra `site/index.html` no navegador e clique em Frota no menu: a foto aparece no topo do
   slide daquele segmento. Enquanto uma imagem não existir, o slide mostra só o nome e os
   números do segmento, sem quebrar.

## Imagens da história que ainda pedem ajuste

- `docs/imagens/02_barracao_1992.jpg` (gerada em 30/10/2026): o letreiro agora está legível, mas
  diz "Equipamontos" em vez de "Equipamentos". O site corta o letreiro por enquanto. Se gerar de
  novo, peça o texto exato "LOCAÇÃO DE FERRAMENTAS" ou "sinal pintado à mão, sem texto legível".
- `docs/imagens/03_unidade_atual.jpg`: as máquinas continuam amarelas. Para alinhar com a frota,
  gerar de novo com "máquinas pintadas de laranja queimado com detalhes verde-escuros".
