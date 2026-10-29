# Changelog — LocaMaq

Formato baseado em [Keep a Changelog](https://keepachangelog.com/). Datas conferidas no
histórico do Git (`git log`) e nas notas de sessão; nada aqui é inventado.

## [Não lançado]

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
