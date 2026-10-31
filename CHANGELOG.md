# Changelog — LocaMaq

Formato baseado em [Keep a Changelog](https://keepachangelog.com/). Datas conferidas no
histórico do Git (`git log`) e nas notas de sessão; nada aqui é inventado.

## [Não lançado]

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
  ainda não commitado no repositório. Falta concluir a correção das duas imagens (placa de
  `02_barracao_1992.jpg` e cor das máquinas de `03_unidade_atual.jpg` via Kling AI, aguardando
  recarga de créditos) antes de publicar.
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
