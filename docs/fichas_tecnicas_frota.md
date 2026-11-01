# Fichas técnicas da frota (fontes dos dados do site)

Consulta feita em **01/11/2026** pelo Claude Code, por busca na web. Os dados abaixo alimentam os
cards da Frota em `site/index.html` (tanque, consumo e tipo de energia) e a escolha de modelos em
`src/gerador_dados/gerar_cadastro_equipamentos.py`.

**Cuidado:** parte das fontes é de revendas, locadoras ou bases de especificações, não do
fabricante. A coluna "Tipo de fonte" diz qual é qual. Antes de usar num material de venda,
conferir na ficha oficial do fabricante. Especificações mudam por ano, versão e mercado.

Regra do projeto (decisão do usuário, 01/11/2026): consumo e tanque vêm de ficha ou manual do
fabricante, não da base fictícia. Quando o fabricante não publica o consumo, o site não mostra
consumo.

## Usados no site

| Card | Modelo de referência (o mais comum na frota) | Dado no site | Fonte | Tipo de fonte |
|---|---|---|---|---|
| Escavadeira | Caterpillar 320 GC | 345 L de tanque | [cat.com, 320 GC](https://www.cat.com/en_IN/products/new/equipment/excavators/medium-excavators/126515.html) | Fabricante |
| Retroescavadeira | JCB 3CX | cerca de 160 L de tanque | [Plant & Equipment, anúncio 3CX 2018](https://www.plantandequipment.com/equipment-items/2018-jcb-3cx-1218498) | Revenda (as fontes variam de 150 a 173 L conforme a versão; por isso "cerca de") |
| Pá-carregadeira | Volvo L60H | 222 L de tanque | [Power Equipment Company, L60H](https://power-equip.com/p/volvo-l60h-wheel-loader/) | Revenda |
| Guindaste | Liebherr LTM 1050-3.1 | 350 L de tanque do chassi; 50 t de capacidade máxima | [codeready.org, LTM 1050-3.1](https://www.codeready.org/cranes/liebherr-cranes/liebherr-ltm-1050-3-1-crane) (tanque); [liebherr.com, LTM 1050-3.1](https://www.liebherr.com/zh-cn/%E7%A7%BB%E5%8A%A8%E5%BC%8F%E5%92%8C%E5%B1%A5%E5%B8%A6%E5%BC%8F%E8%B5%B7%E9%87%8D%E6%9C%BA/%E7%A7%BB%E5%8A%A8%E5%BC%8F%E8%B5%B7%E9%87%8D%E6%9C%BA/ltm%E7%A7%BB%E5%8A%A8%E5%BC%8F%E8%B5%B7%E9%87%8D%E6%9C%BA/ltm-1050-3-1-4043648) (50 t) | Base de especificações (tanque); fabricante (capacidade) |
| Gerador | Atlas Copco QAS 150 | 26,1 L/h a 75% de carga, 60 Hz (21,9 L/h em 50 Hz) | [Datasheet QAS 150-200 JD](https://cdn.shopify.com/s/files/1/0403/8898/4990/files/QAS_150_200_Datasheet.pdf); [manual QAS 150 JD](https://manuals.plus/atlas-copco/qas-150-jd-mobile-generator-manual) | Ficha e manual do fabricante, hospedados por terceiros |

Não usado: tanque do gerador (as fontes divergem: 1.268 L no manual e 223 gal numa matéria).

## Energia das empilhadeiras e plataformas

Empilhadeiras a GLP e plataformas elétricas são decisão do usuário (01/11/2026). Os modelos do
cadastro que eram a diesel foram trocados pela versão GLP ou elétrica da mesma marca.

| Tipo | Antes | Depois | O que a fonte diz | Fonte | Tipo de fonte |
|---|---|---|---|---|---|
| Empilhadeira | Yale GDP50VX | Yale **GLP50VX** | GDP50VX é diesel; a versão GLP é a GLP50VX (5 t) | [LECTURA Specs, GDP 50 VX](https://www.lectura-specs.com/en/model/forklifts/diesel-forklifts-yale/gdp-50-vx-1036480); [LECTURA Specs, GLP50VX6](https://www.lectura-specs.com/en/model/forklifts/lpg-forklifts-yale/glp50vx6-productivity-11762228) | Base de especificações |
| Empilhadeira | Hyster H80FT | (mantido) | Versão a GLP com cerca de 3,6 t (8.000 lb) | [Hyster H80-120FT Tech Guide](https://www.scribd.com/document/493225423/H80-120FT-TechGuide-1) | Ficha do fabricante, hospedada por terceiros |
| Empilhadeira | Toyota 8FGU25 | (mantido) | GLP/gasolina, cerca de 2,5 t (5.000 lb) | [eLiftruck, 8FGU25 2022](https://www.eliftruck.com/details/1016325-33/year-2022-fuel-lp-gas-make-toyota-model-8fgu25/HTTP:/WWW.ATLASD2D.COM) | Revenda |
| Empilhadeira | Clark C25 | Clark **C25L** | C25L é a versão a GLP (2,5 t) | [LiftsToday, C25L 2015](https://www.liftstoday.com/listing/for-sale/228643835/2015-clark-c25l-pneumatic-tire-forklifts?print=1) | Revenda |
| Plataforma | JLG 600AJ | JLG **E600JP** | 600AJ é diesel ou bicombustível; E600JP é articulada elétrica, 48 V, plataforma de 18,4 m | [jlg.com, E600JP](https://www.jlg.com/en-au/equipment/boom-lifts/articulating/electric-hybrid/e600-and-m600-series/e600jp) | Fabricante |
| Plataforma | Genie Z45 | Genie **Z45DC** (Z-45 DC) | Elétrica, bateria de 48 V e 390 Ah, 15,92 m de altura de trabalho | [Ficha Genie Z-45 DC/FE](https://access-lift.com/wp-content/uploads/2023/11/ZBOOMSPEC_Z45_DC_Z45_FE_EN-US_NA_LR.pdf) | Ficha do fabricante, hospedada por revenda |
| Plataforma | Skyjack SJ63AJ | Skyjack **SJ45AJE+** | SJ63AJ é diesel ou bicombustível; SJ45 AJE+ é articulada elétrica, 15,7 m de altura de trabalho | [Skyjack SJ63 AJ, ficha](https://www.lectura-specs.es/datasheet-downloads/sj_63_aj_en(e19).pdf); [lançamento do AJE+](https://www.forconstructionpros.com/equipment/fleet-maintenance/hybrid-engines/article/22909865/skyjack-skyjack-releases-electric-rough-terrain-articulating-boom-lift-series) | Ficha do fabricante (via base); imprensa especializada |
| Plataforma | Haulotte HA16 (RTJ) | Haulotte **HA16E** | HA16 RTJ é diesel; HA16 E é elétrica, 16 m de altura de trabalho | [United Equipment, HA16 E PRO](https://www.unitedequipment.com.au/product/haulotte-electric-articulating-boom-lift-ha16-e-pro); [Haulotte HA16 RTJ PRO](https://unitedequipment.com.au/haulotte-diesel-articulating-boom-lift-ha16-rtj-pro) | Revenda |

Faixa de altura de trabalho das plataformas no site: "cerca de 16 a 20 metros" (Z-45 DC 15,9 m;
SJ45 AJE+ 15,7 m; HA16 E 16 m; E600JP com plataforma de 18,4 m, cerca de 20 m de trabalho).

## Não conferido

- Consumo de GLP das empilhadeiras e autonomia de bateria das plataformas: não encontrei nas
  fontes consultadas; o site não mostra.
- Consumo por hora de escavadeira, retroescavadeira, pá-carregadeira e guindaste: os fabricantes
  não publicam esse número nas fichas encontradas; o site mostra só o tanque.
