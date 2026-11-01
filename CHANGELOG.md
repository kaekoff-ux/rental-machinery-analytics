# Changelog — LocaMaq

Formato baseado em [Keep a Changelog](https://keepachangelog.com/). Datas conferidas no
histórico do Git (`git log`) e nas notas de sessão; nada aqui é inventado.

## [Não lançado]

### Added (01/11/2026, frota por modelo)
- Cards da Frota com filtro de modelo: ao escolher o modelo aparecem a foto, a ficha técnica e
  "Onde estão" as máquinas daquele modelo; "Todos os modelos" volta à visão do tipo de máquina. O
  card começa no modelo mais comum que tem foto.
- `docs/fichas_tecnicas_modelos.csv`: 83 valores de ficha técnica dos 28 modelos ativos, tirados
  de manual/ficha do fabricante ou de fonte de referência (concessionária, revenda, base de
  especificações), com fonte e tipo de fonte em cada linha. Valor em que as fontes não batem
  ficou de fora (ex.: consumo do Cat XQ125, lança do XCMG QY25K). A fonte não aparece no site.
- `src/site/recortar_modelos_frota.py`: recorta do painel enviado pelo usuário
  (`docs/imagens/frota/painel_modelos.jpeg`) uma foto por modelo, apagando o nome escrito no
  canto. Não usa os quadros errados ("Volvo EC210B" mostra um gerador, "Hyundai HX220L" uma
  escavadeira Volvo, "Atlas Copco QAS150" um guindaste) nem os dois que não existem no cadastro;
  o Komatsu PC210 não tem quadro. Esses 4 modelos ficam sem foto. Logotipos e textos pintados nas
  máquinas são borrados (as imagens são de IA; o site mostra só o equipamento). Uma imagem avulsa
  em `docs/imagens/frota/modelos/<fabricante-modelo>.jpg` (ex.: feita no Gemini) substitui o quadro.
- `docs/prompts_imagens_frota.md`: regra nova das fotos (por modelo, sem logotipo), passo a passo
  para refazer no Gemini e prompts dos 5 modelos a refazer.
- `src/site/gerar_dados_frota.py`: junta cadastro ativo, fichas e fotos em `site/dados_frota.js`.
- `tests/conferir_site.py`: confere `dados_frota.js` contra o cadastro, o CSV de fichas e as fotos,
  e o prazo do pedido (30 a 360 dias). Saiu a conferência dos contratos por modalidade, que o site
  não mostra mais.

### Changed (01/11/2026, contrato mínimo de 30 dias)
- Decisão do usuário: locação a partir de 30 dias (abaixo disso, frete e mobilização custam mais
  que o aluguel). Pedido de orçamento de 30 a 360 dias, com o prazo em meses ("1 mês e 15 dias");
  topo da página e slide de serviços passaram a dizer "Contratos de 30 a 360 dias".
- Pedido de orçamento: escolhe também o modelo (lista do tipo de máquina, ou "Qualquer modelo") e
  mostra a ficha técnica e a miniatura do modelo (a miniatura não aparece no celular nem em tela
  baixa). O modelo vai junto no campo `equipamento` ("Escavadeira – Caterpillar 320GC"), porque a
  planilha do Apps Script não tem coluna de modelo.
- Decisão do usuário: o mínimo de 30 dias vale só para o site; os dados não mudam
  (`contratos_locacao.csv` segue com contratos diários e semanais). Outros prazos são atendimento
  conforme a demanda, pelo Telegram.

### Removed (01/11/2026, fotos por tipo de máquina)
- `site/img/frota/disponiveis.js`, a lista `FROTA` de `src/site/otimizar_imagens.py` e o trecho do
  `script.js` que a lia: o site nunca teve essas fotos (a lista estava vazia) e agora usa as fotos
  por modelo.

### Removed (01/11/2026, abastecimento)
- Fonte `abastecimento` retirada do projeto por decisão do usuário: não faz parte do controle de
  frota do case, e "diesel por hora" não vale para toda a frota (empilhadeiras são a GLP,
  plataformas são elétricas). Apagados `src/gerador_dados/gerar_abastecimento.py`,
  `data/raw/abastecimento.csv` e `data/processed/abastecimento.csv` (recuperáveis pelo histórico
  do Git). O projeto passa a ter 6 fontes e o modelo estrela, 4 fatos.
- KPI "Consumo de combustível por hora" removido de `docs/kpis.csv`; "Margem por máquina" perdeu
  o termo de custo de combustível. Ajustados também `docs/dicionario_dados.csv`,
  `docs/modelo_dados.md`, `docs/roadmap.md`, `powerbi/checklist_power_query.md`, `README.md`,
  `spec.md`, `CLAUDE.md` e o docstring de `src/gerador_dados/utils.py`.
- Pendente fora do Claude Code: o `.pbix` do dashboard ainda tem a tabela `f_abastecimento`;
  excluir a consulta no Power BI Desktop antes de atualizar, senão a atualização falha.

### Changed (01/11/2026, cadastro)
- Empilhadeiras a GLP e plataformas elétricas: os modelos que eram a diesel viraram a versão
  GLP/elétrica da mesma marca (Yale GDP50VX → GLP50VX, Clark C25 → C25L, JLG 600AJ → E600JP,
  Genie Z45 → Z45DC, Skyjack SJ63AJ → SJ45AJE+, Haulotte HA16 → HA16E) e o guindaste Liebherr
  passou a ter o nome oficial `LTM 1050-3.1`. Só mudaram as colunas `modelo` e `numero_serie` do
  cadastro (26 linhas no processed); os outros CSVs saíram idênticos ao regenerar (seed 42).

### Changed (01/11/2026, site)
- Cards da frota: saíram consumo (L/h) e tanque, que vinham do gerador de abastecimento. Entraram
  o tipo de energia (Diesel, GLP na empilhadeira, elétrica a bateria na plataforma), o tanque do
  modelo mais comum (escavadeira, retro, pá-carregadeira, guindaste) e o consumo do gerador a 75%
  de carga, todos de ficha de fabricante, e a lista "Modelos na frota" (do cadastro, só ativos).
  Empilhadeira sem a faixa "2,5 a 8 toneladas"; guindaste cita o Liebherr LTM 1050-3.1.
- Simulador do pedido de orçamento: saíram "Diesel estimado" e "Tanques cheios"; entraram a
  energia e a ficha técnica da máquina escolhida (descrição e dados do card dela na Frota).

### Added (01/11/2026, documentação e testes)
- `docs/fichas_tecnicas_frota.md`: fontes (consultadas em 01/11/2026) de cada dado técnico do
  site e da troca de modelos, com o tipo de fonte (fabricante, revenda ou base de dados).
- `tests/conferir_site.py`: confere os números do site contra `data/processed/` (frota por
  segmento, modelos de cada card, unidades, 117 ativas, contratos, preventivas, inspeções e
  telemetria).
- Fora do repositório: os 4 arquivos de `00_Fase_0_Fundacao` que citavam abastecimento foram
  ajustados, com cópia em `00_Fase_0_Fundacao/_backup_2026-11-01_antes_de_tirar_abastecimento/`.

### Changed (31/10/2026, Apps Script)
- `src/apps_script/receber_orcamento.gs` passou a usar `LockService`: dois pedidos ao mesmo
  tempo não gravam o cabeçalho duas vezes nem se sobrepõem. Testado só em simulação (Node, com
  planilha, trava e resposta falsas); o Google de verdade não foi testado.
- `docs/plano_camada1_site.md`: passo 5 com os rótulos do Apps Script conferidos na documentação
  oficial em 31/10/2026 e com a lista do que ainda não foi testado.
- Planilha `LocaMaq - Leads` e projeto `LocaMaq - Receber orçamento` criados na conta Google do
  usuário (passos 1 a 3 do plano). A implantação foi preparada e parou na autorização do Google;
  nenhuma implantação existe ainda, e o formulário do site segue em modo de teste.

### Added (31/10/2026, publicação)
- Site publicado no GitHub Pages (branch `main`, pasta raiz):
  <https://kaekoff-ux.github.io/rental-machinery-analytics/site/>. Link no `README.md` e no
  `CLAUDE.md` (passos 7 e 8 do plano da Camada 1).

### Changed (31/10/2026, publicação)
- `README.md`: status atualizado (dizia "Fase 0 em andamento"; agora Fase 1 completa e Fase 2
  em andamento), site na lista de entregas e HTML/CSS/JavaScript na stack.

### Changed (31/10/2026, site, tablets)
- Limite entre celular e tablet de 768 px (48rem) para 736 px (46rem), no CSS e nas imagens do
  Quem somos: o iPad mini em pé (744 px) caía no layout de celular e o pop-up Unidades rolava.
- "Como funciona": 2 etapas por vez de 736 a 959 px e 3 a partir de 960 px.
- Simulação em 12 telas de tablet (iPad mini, 10/Air, Pro 11, Pro 12,9, 9,7 e Galaxy Tab S9,
  em pé e deitado): todas sem rolagem lateral e com os pop-ups cabendo sem rolar.

### Added (31/10/2026, site, terceira revisão)
- Animação no topo: vídeo do Gemini (`docs/videos/01_hero_animacao.mp4`, 10 s, 1280×720,
  4 MB), copiado pelo `otimizar_imagens.py` para `site/video/hero.mp4`. Toca só a partir de
  960 px, sem economia de dados e sem "reduzir movimento"; some sobre a foto no fim de cada volta
  e pausa fora da tela. Botão "Pausar animação" para vídeo, foto e letreiro.
- Área do cliente (planejada): botão no cabeçalho e no rodapé com aviso de "em planejamento";
  escopo, login e dados a discutir (`spec.md`, seção 9).
- `site/img/frota/disponiveis.js`, gerado pelo script: o site só pede as fotos da frota que
  existem (antes eram 7 erros 404 no console).
- Prévia de link (`og:*`) para compartilhar no LinkedIn e no WhatsApp.
- `spec.md`: Área do cliente nas funcionalidades e na arquitetura, padrão visual do usuário na
  direção visual e nova seção 9, "Decisões em aberto".

### Changed (31/10/2026, site, terceira revisão)
- Slide 2016: mural em faixa larga em cima e texto embaixo, como o slide de 1992.
- Quem somos no celular só com texto; as fotos ficam em `<picture>` e nem são baixadas.
- Revisão de design: contraste do link dos números, folga do rodapé para o botão
  "Atendimento", página sem salto ao abrir pop-up, foco no pop-up ao abrir, cabeçalho em uma
  linha em 320 px, pop-ups cabendo em notebook 1366×768, véu mais escuro atrás do título, botão
  de pausa fora do caminho do "Atendimento", fonte reduzida às larguras e pesos usados.

### Added (31/10/2026, site)
- `docs/imagens/07_2016.jpeg` (mural de recordações, do usuário, gerado por IA) virou
  `site/img/mural-2016.jpg` e ilustra o slide 2016 do pop-up Quem somos, com botão "Ver o mural
  inteiro" que amplia a imagem dentro do próprio pop-up.
- Imagens `docs/imagens/04_Missão.jpeg`, `05_Visão.jpeg` e `06_Valores.jpeg` (do usuário,
  geradas por IA) entraram no `otimizar_imagens.py` (viram `site/img/missao.jpg`, `visao.jpg`
  e `valores.jpg`) e são o fundo translúcido dos slides de Missão, Visão e Valores, que agora
  são três slides separados no pop-up Quem somos.

### Changed (31/10/2026, site, segunda revisão)
- Página inicial enxuta, conforme prints do usuário: topo, letreiro, números (cada um abre um
  pop-up), chamada de orçamento e rodapé condensado, sem botão de orçamento repetido.
- Serviços, Frota, Como funciona, Quem somos e Unidades viraram pop-ups com slides laterais
  (setas, pontinhos ou etiquetas, arraste no celular e teclado).
- Orçamento em pop-up de dois passos (máquina e simulação; dados) com tela de confirmação.
- Botão "Atendimento" do Telegram no canto inferior, configurável em `CONTATO.telegram`.
- `src/site/otimizar_imagens.py` passou a recortar a moldura preta do retrato e o letreiro do
  barracão (que tinha o erro "Equipamontos").

### Changed (31/10/2026, site)
- Visual mais moderno e contido, a pedido do usuário: escala de texto e espaçamentos menores,
  largura máxima de 1200 px, botões em pílula translúcidos, cartões de vidro, brilhos suaves,
  cabeçalho translúcido sobre a foto e letreiro de LED fino no lugar da faixa laranja grande.
- Chamadas de ação abrem pop-ups (`<dialog>`): orçamento (o formulário passou para o pop-up, com
  tela de sucesso), simulador (saiu da página), unidade (máquinas por tipo, lidas das fichas da
  frota) e "sobre o case". No celular os pop-ups sobem de baixo, como gaveta.
- Botão flutuante "Pedir orçamento" que aparece só no meio da página.

### Added (30/10/2026, Camada 1)
- `site/` — landing page da LocaMaq em HTML, CSS e JavaScript puro (passos 1 a 4 e 6 do
  `docs/plano_camada1_site.md`), com estrutura inspirada em scarpantiempilhadeiras.com.br:
  topo com foto e faixa rolante, serviços, números, frota com simulador, como funciona,
  história/missão/visão/valores, unidades com esquema de rodovias, formulário de orçamento e
  rodapé. Números do site conferidos contra `data/processed/` (117 ativos, 7 segmentos,
  ativos por filial e por segmento, 2.039 preventivas, 1.033 inspeções de devolução, 40
  máquinas com telemetria, contratos por modalidade).
- Simulador da frota com regras dos geradores: consumo e tanque por segmento
  (`gerar_abastecimento.py`), preventiva a cada 250 h (`gerar_ordens_manutencao.py`) e
  modalidade por duração (`gerar_contratos_locacao.py`); preenche o formulário de orçamento.
- Contatos genéricos centralizados no objeto `CONTATO` de `site/script.js`.
- `src/site/otimizar_imagens.py` — gera as imagens leves de `site/img/` (de 274/916/928 KB para
  104/220/238 KB).
- `src/apps_script/receber_orcamento.gs` — backend do formulário (passo 5), ainda não publicado.
- `docs/prompts_imagens_frota.md` — lista dos 7 equipamentos e prompts para as fotos da frota.

### Changed (30/10/2026)
- `docs/imagens/02_barracao_1992.jpg` substituída pela imagem nova do usuário (renomeada de
  "Generated Image October 30, 2026 - 5_25AM.jpg"); o letreiro saiu com o erro "Equipamontos".

### Fixed (30/10/2026)
- `.gitignore` ignorava `/site` (resto do modelo padrão de Python para mkdocs), o que impediria
  o site de ir para o GitHub.

### Added
- `spec.md` — PRD consolidado do projeto (dor do usuário, proposta de valor,
  funcionalidades, MVP, personas, arquitetura técnica, direção visual).
- `CHANGELOG.md` — este arquivo.
- Escopo expandido de portfólio: site institucional + Telegram + N8N + fluxo interno
  (vendedor/atendimento/oficina/contratação) + camada de inteligência (RAG + MCP + agentes),
  organizado em 5 camadas sobre a base LocaMaq já existente.
- Identificação de pendências nas imagens de `docs/quem_somos.md` (placa ilegível em
  `02_barracao_1992.jpg`, cor das máquinas em `03_unidade_atual.jpg`) e início da correção
  via Kling AI (image-to-image) — gerações ainda não concluídas por falta de créditos na
  conta Kling.

### Pendências (do usuário)
- `docs/quem_somos.md` + `docs/imagens/` (história, missão, visão, valores da LocaMaq) —
  commitados em 31/10/2026 (226fdac) e já usados no site publicado. Resta corrigir duas
  imagens: `03_unidade_atual.jpg` (máquinas ainda amarelas; via Kling AI, aguardando recarga de
  créditos) e `02_barracao_1992.jpg` (o letreiro saiu com o erro "Equipamontos", que o script
  de imagens corta fora).
- `data/raw/Dashboard_Rental_Machinery.pbix` — ainda não commitado. Power BI (Fases 2-4 do
  roadmap: ETL/modelo estrela, DAX, dashboard) não construído; arquivo é só o placeholder
  vazio criado pelo Power BI Desktop.

### Verified
- Números de `docs/quem_somos.md` (135 equipamentos, 117 ativos, distribuição por filial,
  aquisição mais antiga em fevereiro/2016) conferidos contra
  `data/processed/cadastro_equipamentos.csv` — todos batem.

## [2026-10-25] Fase 2 (início)

### Added
- `dim_calendario.csv` (gerador determinístico, sem seed).
- Rascunho do modelo estrela em `docs/modelo_dados.md` (3 dimensões + 5 fatos).

## [2026-10-25] Fase 1 — Base fictícia completa

### Added
- Geradores Python das 7 fontes de dados (cadastro de equipamentos, clientes, contratos de
  locação, horímetro/telemetria, ordens de manutenção, abastecimento, faturamento), com
  seed fixa 42 e sujeira proposital só em `data/raw/`.
- `src/gerador_dados/utils.py` com funções compartilhadas entre os geradores.

### Fixed
- Duplicados no gerador de clientes.

## [2026-10-16] Fase 0 — Fundação

### Added
- Documentação inicial do projeto (roadmap, dicionário de dados, KPIs, `CLAUDE.md`,
  `README.md`).

### Fixed
- Codificação UTF-8 de `docs/roadmap.md`.
