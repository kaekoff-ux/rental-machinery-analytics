# CLAUDE.md - Rental Machinery Analytics (LocaMaq)

Este arquivo orienta o Claude Code neste repositório. Leia antes de qualquer tarefa.

PRD do projeto (dor do usuário, proposta de valor, funcionalidades, MVP, personas,
arquitetura, direção visual) em `spec.md`, na raiz do repositório. Histórico de mudanças em
`CHANGELOG.md`.

**Camada 1 (site do cliente) publicada em 31/10/2026:**
<https://kaekoff-ux.github.io/rental-machinery-analytics/site/> (GitHub Pages, branch `main`,
pasta raiz). Cada push na `main` republica no mesmo endereço em 1 a 2 minutos. Passo a passo e
status em `docs/plano_camada1_site.md`. **Formulário ligado desde 05/11/2026:** o site envia o pedido
para um Webhook do n8n (Docker em uma instância EC2 da AWS, endereço fixo pelo ngrok), que grava na
planilha Google `LocaMaq - Leads`. O Apps Script foi descartado (commit `7370dbd`, 02/11/2026). Como o
servidor foi montado e como operá-lo: `docs/servidor_n8n_aws/` (só no computador do usuário, fora do
GitHub por decisão dele: não versionar nem dar push). Cópia do fluxo, sem IDs:
`src/n8n/leads_locamaq.json`. Política de privacidade do site:
`site/privacidade.html`. Fotos da frota: `docs/prompts_imagens_frota.md`. Power BI segue em
paralelo, sem depender disso.

**Área do cliente (logada):** pedida pelo usuário em 31/10/2026 para os clientes acompanharem
pedidos e requisições. Ainda não construída e com escopo a discutir: ver `spec.md`, seção 9. No
site há só um botão que abre um aviso de "em planejamento".

**Padrão visual das páginas públicas:** o do usuário (moderno, pop-ups com slides, vidro e brilho
suaves, página inicial enxuta, celular sem imagens no Quem somos) vale mais que as regras da
skill de design; ver `spec.md`, seção 7.

## O que é este projeto
Case de portfólio sobre gestão de locação de máquinas pesadas, inspirado em um anúncio público do Workana. **Todos os dados são fictícios** e gerados por script. A empresa fictícia se chama **LocaMaq**.

Objetivo: demonstrar o ciclo entender o problema > consolidar dados > analisar > automatizar > aplicar IA > medir resultado.

## Quem está desenvolvendo
Carlos, engenheiro mecânico com experiência em manutenção, gestão de ativos, peças e compras. Power Query bom, DAX básico (dificuldade com funções temporais), Python iniciante, GitHub iniciante. Estuda cerca de 1 hora por dia.

## Como trabalhar com ele
- Passos pequenos, um de cada vez, cada um terminando em algo que ele consegue rodar e ver.
- Explique o "porquê" de cada comando de Git ou Python na primeira vez que aparecer.
- Relacione as soluções a problemas reais de manutenção, ativos e operações.
- Não faça grandes refatorações sem pedir. Mostre o plano antes de mudar muitos arquivos.

## Regras do projeto
1. Dados fictícios: nunca incluir dados reais de empresas, clientes ou pessoas.
2. Reprodutibilidade: o gerador de dados usa **seed fixa = 42**. A mesma execução deve gerar os mesmos arquivos.
3. Sujeira só nos dados brutos (`data/raw/`). Os dados tratados (`data/processed/`) saem limpos, com datas em formato ISO (aaaa-mm-dd). Exceção: um valor realmente ausente na vida real (ex.: `ano_fabricacao` que nunca foi registrado) pode ficar vazio também no `processed` — isso não é "sujeira" (inconsistência de formatação/grafia), é ausência legítima do dado. Se usar essa exceção num gerador, comentar no código qual campo e por quê.
4. Nomes de colunas em português, `snake_case`, sem acento. Seguir o dicionário em `docs/dicionario_dados.csv`.
5. KPIs seguem as definições em `docs/kpis.csv`. Se uma fórmula mudar, atualizar o arquivo.
6. Textos públicos (README, case, posts) devem dizer que é um case com dados fictícios e não declarar experiência profissional inexistente.
7. Leads e indicadores seguem a seção "Leads e indicadores" abaixo (diretriz de 05/11/2026).

## Leads e indicadores (diretriz de 05/11/2026)
Decisão do usuário: o funil de leads e os indicadores dele fazem parte do projeto, e os dados de 2026
precisam fazer sentido com a disponibilidade das máquinas.
- **Onde ficam os leads:** planilha Google `LocaMaq - Leads`, aba `Leads` (recurso Tabela, `A1:L1000`).
  Colunas: as 9 que o n8n grava (`data_envio` a `status`) mais `data_desfecho`, `id_contrato` e
  `motivo_perda`, que a equipe preenche (e, depois, a automação do Slack). Etapas do `status`: `Novo`,
  `Em Contato`, `Orçado`, `Fechado`, `Perdidos` (lista suspensa da aba; usar exatamente esses nomes).
- **Entrada:** formulário do site → Webhook do n8n → Google Sheets (fluxo em
  `src/n8n/leads_locamaq.json`; instalação em `docs/servidor_n8n_aws/`, só local). O n8n
  não aumenta a Tabela: ao passar de 1000 linhas, ajustar o intervalo (menu da tabela).
- **Indicadores de leads** (5, em `docs/kpis.csv`): taxa de conversão, tempo médio de fechamento,
  leads por origem, perdas por motivo e perda por indisponibilidade. Tabela `leads` em
  `docs/dicionario_dados.csv`. Se uma fórmula mudar, atualizar o CSV (regra 5). A aba `Indicadores` da
  planilha calcula tudo com 4 fórmulas de matriz (células A4, A15, A23 e A32, sobre `Leads!2:1000`);
  pedido do site sem `status` conta como `Novo`. Ainda não há versão no Power BI.
- **Disponibilidade primeiro:** contrato novo só entra com a máquina ativa e livre (sem sobreposição e
  fora de OS aberta). Lead perdido por "Indisponibilidade de máquina" precisa ser provável nos dados:
  todas as unidades do modelo alugadas na data do lead. `tests/conferir_extensao_2026.py` confere isso
  e deve passar antes de qualquer commit que toque a extensão.
- **Dados de 2026 (extensão):** `data/processed/extensao_2026/`, em arquivos separados (os 6 CSVs de
  2024-2025 não mudam): 35 contratos, 76 faturas e 66 leads (35 Fechado, 21 Perdidos, 10 em aberto).
  "Hoje" da extensão: 05/11/2026. Gerar com `python src/gerador_dados/gerar_extensao_2026.py`;
  premissas em `docs/extensao_2026_leads.md`. Não há telemetria, OS nem inspeção de devolução em 2026.
- **Marca do histórico fictício:** toda observação de lead gerada por script começa com
  `[histórico fictício]`; lead real, vindo do site, não leva a marca. Contatos fictícios usam `.example`
  ou telefone inexistente: nunca pôr e-mail ou telefone reais.
- **A taxa de conversão do histórico (62,5%) é amostra**, não resultado real: não usar como número de
  portfólio sem dizer isso.

## Estrutura do repositório
```
rental-machinery-analytics/
├── README.md
├── CLAUDE.md
├── .gitignore
├── docs/                  documentação (roadmap, dicionário, KPIs, case)
├── data/
│   ├── raw/               CSVs brutos com sujeira (saída do gerador)
│   └── processed/         dados tratados (referência para validar o Power Query)
├── src/
│   ├── gerador_dados/     scripts que geram a base fictícia
│   ├── ml/                modelo de risco de parada e previsão de demanda
│   └── agentes/           agentes de IA (preventiva, qualidade de dados, resumo)
├── powerbi/               arquivos .pbix e anotações
├── excel/                 versão Excel (Power Query e Power Pivot)
├── app/                   app de ordens de serviço de manutenção
└── notebooks/             exploração e estudos
```

## Fases (resumo)
0 Fundação | 1 Base fictícia | 2 ETL e modelo | 3 DAX e dashboard | 4 Versão Excel | 5 IA preditiva | 6 App e agentes | 7 Portfólio.
Detalhes em `docs/roadmap.md`. Fase atual: **1 - Base fictícia (completa, as 6 fontes geradas) → prestes a iniciar Fase 2**.

## Tabelas de origem (6)
cadastro_equipamentos, clientes, contratos_locacao, horimetro_telemetria, ordens_manutencao, faturamento.

Abastecimento foi retirado do projeto em 01/11/2026 (decisão do usuário: não faz parte do
controle de frota do case; empilhadeiras são a GLP e plataformas são elétricas, então "diesel por
hora" não se aplica a toda a frota). Não recriar o gerador nem o CSV. Consumo, se aparecer no
site, vem de médias de manual do fabricante, com a fonte citada, e não da base fictícia. Fontes
dos dados técnicos do site e da escolha dos modelos GLP/elétricos: `docs/fichas_tecnicas_frota.md`.
Conferir os números do site contra a base: `python tests/conferir_site.py` (sai com erro se algo
divergir; rodar depois de mudar geradores ou `site/index.html`).

## Comandos úteis
Rodar a partir da raiz do repositório. Novos comandos entram aqui conforme as fases avançarem.
- `python src/gerador_dados/gerar_cadastro_equipamentos.py` gera `cadastro_equipamentos.csv` em `data/raw/` (com sujeira, 139 linhas) e em `data/processed/` (limpo, 135 linhas). Só usa a biblioteca padrão do Python.
- `python src/gerador_dados/gerar_clientes.py` gera `clientes.csv` em `data/raw/` (com sujeira, 73 linhas) e em `data/processed/` (limpo, 70 linhas). Só usa a biblioteca padrão do Python.
- `python src/gerador_dados/gerar_contratos_locacao.py` gera `contratos_locacao.csv` em `data/raw/` (com sujeira, 1216 linhas) e em `data/processed/` (limpo, 1210 linhas). Depende de `cadastro_equipamentos.csv` e `clientes.csv` (processed) já existirem — rode os geradores anteriores primeiro. Simula locações sequenciais sem sobreposição de datas por máquina.
- `python src/gerador_dados/gerar_horimetro_telemetria.py` gera `horimetro_telemetria.csv` em `data/raw/` e em `data/processed/` (11792 linhas nas duas — "lacunas" entre leituras são naturais da amostragem periódica, não é sujeira só do raw). Depende de `cadastro_equipamentos.csv` e `contratos_locacao.csv` (processed). Simula o horímetro dia a dia (mais uso quando há contrato vigente) e sorteia leituras periódicas; ~35% da frota tem fonte_leitura=Telemetria (leituras frequentes), o resto é Manual (esparsas).
- `python src/gerador_dados/gerar_ordens_manutencao.py` gera `ordens_manutencao.csv` (3922 linhas). **Módulo de controle de oficina** — `status_os` (Aberta/Em andamento/Concluída) é o board Kanban. Depende de `cadastro_equipamentos.csv`, `contratos_locacao.csv` e `horimetro_telemetria.csv` (processed). Três origens de OS: Preventiva (limiar de horímetro, a cada 250h), Corretiva (falha aleatória, mais provável em uso), Preditiva (regra comercial→oficina: toda devolução de contrato abre uma inspeção automática — validado: 1033 de 1034 devoluções geraram OS).
- `python src/gerador_dados/gerar_faturamento.py` gera `faturamento.csv` (2487 linhas). Depende de `contratos_locacao.csv` (processed). Contratos Mensal geram 1 fatura por mês de duração; Semanal/Diária geram 1 fatura única. Contratos Cancelado não faturam. `status_pagamento` (Pago/Vencido/Em aberto) é decidido comparando a data de vencimento com o fim da janela de histórico (o "hoje" fictício do case).
- **As 6 fontes de dados do roadmap estão geradas.** Fase 1 (Base fictícia) completa.
- `python src/gerador_dados/gerar_dim_calendario.py` gera `dim_calendario.csv` (1277 dias, 2023-01-01 a 2026-06-30 — mais largo que a janela de histórico de propósito, ver docstring do script). Sem sujeira, sem seed (determinístico). Marcar como tabela de datas no Power BI.
- **Fase 2 (ETL e modelo) em andamento.** Modelo estrela rascunhado em `docs/modelo_dados.md` (3 dimensões + 4 fatos). Checklist de limpeza por fonte em `powerbi/checklist_power_query.md`. Nenhum dos dois foi testado no Power BI ainda — são planos, não resultado. O trabalho de Power Query em si acontece na interface do Power BI Desktop, fora do que o Claude Code executa diretamente.
- Funções repetidas entre os geradores (sorteio ponderado, gravação de CSV) ficam em `src/gerador_dados/utils.py`.
- Janela de histórico: 2024-01-01 a 2025-12-31 (24 meses). Todas as tabelas devem usar a mesma janela. **Exceção documentada:** a extensão 2026 (contratos, faturas e leads, de jan a 05/11/2026) fica em arquivos separados em `data/processed/extensao_2026/`, sem tocar nos 6 CSVs. Gerar: `python src/gerador_dados/gerar_extensao_2026.py` (não usar `-I`, ele importa dos geradores vizinhos). Conferir: `python tests/conferir_extensao_2026.py`. Detalhes e premissas: `docs/extensao_2026_leads.md`.
- **Site (Camada 1):** abrir `site/index.html` direto no navegador, ou rodar
  `python -m http.server 8765` dentro de `site/` e abrir `http://127.0.0.1:8765` (igual ao GitHub
  Pages). Telefones/endereços genéricos ficam no objeto `CONTATO` e a URL do formulário em
  `URL_WEBHOOK` (webhook do n8n), ambos no topo de `site/script.js`. Os números do site (frota, unidades,
  preventivas, telemetria) foram tirados de `data/processed/`; se os geradores mudarem,
  atualizar `site/index.html` também.
- `python src/site/otimizar_imagens.py` gera as imagens leves de `site/img/` a partir de
  `docs/imagens/` (história) e copia o vídeo `docs/videos/01_hero_animacao.mp4` para
  `site/video/hero.mp4` (sem recompressão: não há ffmpeg). Precisa do Pillow. Rodar sempre que
  uma imagem ou o vídeo mudar.
- **Frota por modelo (01/11/2026):** cada card da Frota tem filtro de modelo, foto e ficha
  técnica; o pedido de orçamento também escolhe o modelo. Fluxo:
  `python src/site/recortar_modelos_frota.py` (fotos de `docs/imagens/frota/painel_modelos.jpeg`
  para `site/img/frota/modelos/`; precisa do Pillow) e `python src/site/gerar_dados_frota.py`
  (junta cadastro ativo + `docs/fichas_tecnicas_modelos.csv` + fotos em `site/dados_frota.js`).
  Regra do usuário: ficha só com dado de manual/ficha do fabricante (ou fonte de referência
  quando não houver), nunca inventado; a fonte fica no CSV e não aparece no site. Valor em que as
  fontes não batem fica de fora. As fotos são de IA: logotipos e textos das máquinas são borrados
  no recorte (lista `LOGOS` do script); o site mostra só o equipamento. Imagem nova (o usuário usa
  o Gemini) vai em `docs/imagens/frota/modelos/<fabricante-modelo>.jpg` e substitui o quadro do
  painel; prompts e nomes em `docs/prompts_imagens_frota.md`. Desde 01/11/2026, os 28 modelos usam
  imagem avulsa do Gemini (enquadrada automaticamente em volta da máquina); o painel ficou só como
  reserva. Versões que sobraram ficam em `docs/imagens/frota/modelos/alternativas/`.
- **Manutenção recomendada pelo fabricante (01/11/2026):** cada card da Frota tem o bloco
  "Manutenção recomendada pelo fabricante" (abre ao toque), e o pedido conta as revisões pelo
  intervalo do tipo de máquina. Dados em `docs/manutencao_fabricante.csv`: plano por tipo de máquina
  (linhas sem modelo) e notas de modelo (com modelo), cada um com fonte; a coluna
  `conta_no_simulador` marca o intervalo do pedido. Os manuais completos quase nunca são públicos,
  então o plano usa fichas e manuais de modelos da mesma classe; o que só aparecia em blogs ficou de
  fora. O site deixou de dizer "revisão a cada 250 h"; **a base de dados não muda** (o gerador de
  ordens continua com preventiva a cada 250 h, regra do case).
- **Contrato mínimo de 30 dias só no site** (decisão do usuário, 01/11/2026: abaixo disso a
  logística custa mais que a locação). O pedido do site vai de 30 a 360 dias. **Não mexer nos
  dados por causa disso:** `contratos_locacao.csv` continua com contratos diários e semanais;
  outros prazos são atendimento conforme a demanda, pelo Telegram (Camada 3).
