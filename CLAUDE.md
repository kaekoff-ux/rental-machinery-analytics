# CLAUDE.md - Rental Machinery Analytics (LocaMaq)

Este arquivo orienta o Claude Code neste repositório. Leia antes de qualquer tarefa.

PRD do projeto (dor do usuário, proposta de valor, funcionalidades, MVP, personas,
arquitetura, direção visual) em `spec.md`, na raiz do repositório. Histórico de mudanças em
`CHANGELOG.md`.

**Próximo passo prioritário: Camada 1 (site do cliente).** Passo a passo detalhado em
`docs/plano_camada1_site.md` — comece por lá antes de qualquer outra camada (Power BI segue
em paralelo, sem depender disso).

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
Detalhes em `docs/roadmap.md`. Fase atual: **1 - Base fictícia (completa, as 7 fontes geradas) → prestes a iniciar Fase 2**.

## Tabelas de origem (7)
cadastro_equipamentos, clientes, contratos_locacao, horimetro_telemetria, ordens_manutencao, abastecimento, faturamento.

## Comandos úteis
Rodar a partir da raiz do repositório. Novos comandos entram aqui conforme as fases avançarem.
- `python src/gerador_dados/gerar_cadastro_equipamentos.py` gera `cadastro_equipamentos.csv` em `data/raw/` (com sujeira, 139 linhas) e em `data/processed/` (limpo, 135 linhas). Só usa a biblioteca padrão do Python.
- `python src/gerador_dados/gerar_clientes.py` gera `clientes.csv` em `data/raw/` (com sujeira, 73 linhas) e em `data/processed/` (limpo, 70 linhas). Só usa a biblioteca padrão do Python.
- `python src/gerador_dados/gerar_contratos_locacao.py` gera `contratos_locacao.csv` em `data/raw/` (com sujeira, 1216 linhas) e em `data/processed/` (limpo, 1210 linhas). Depende de `cadastro_equipamentos.csv` e `clientes.csv` (processed) já existirem — rode os geradores anteriores primeiro. Simula locações sequenciais sem sobreposição de datas por máquina.
- `python src/gerador_dados/gerar_horimetro_telemetria.py` gera `horimetro_telemetria.csv` em `data/raw/` e em `data/processed/` (11792 linhas nas duas — "lacunas" entre leituras são naturais da amostragem periódica, não é sujeira só do raw). Depende de `cadastro_equipamentos.csv` e `contratos_locacao.csv` (processed). Simula o horímetro dia a dia (mais uso quando há contrato vigente) e sorteia leituras periódicas; ~35% da frota tem fonte_leitura=Telemetria (leituras frequentes), o resto é Manual (esparsas).
- `python src/gerador_dados/gerar_ordens_manutencao.py` gera `ordens_manutencao.csv` (3922 linhas). **Módulo de controle de oficina** — `status_os` (Aberta/Em andamento/Concluída) é o board Kanban. Depende de `cadastro_equipamentos.csv`, `contratos_locacao.csv` e `horimetro_telemetria.csv` (processed). Três origens de OS: Preventiva (limiar de horímetro, a cada 250h), Corretiva (falha aleatória, mais provável em uso), Preditiva (regra comercial→oficina: toda devolução de contrato abre uma inspeção automática — validado: 1033 de 1034 devoluções geraram OS).
- `python src/gerador_dados/gerar_abastecimento.py` gera `abastecimento.csv` (22263 linhas). Depende de `cadastro_equipamentos.csv`, `contratos_locacao.csv` e `horimetro_telemetria.csv` (processed). Consumo por segmento (litros/hora) e capacidade de tanque disparam o abastecimento; preço do diesel sobe com inflação simples ao longo da janela.
- `python src/gerador_dados/gerar_faturamento.py` gera `faturamento.csv` (2487 linhas). Depende de `contratos_locacao.csv` (processed). Contratos Mensal geram 1 fatura por mês de duração; Semanal/Diária geram 1 fatura única. Contratos Cancelado não faturam. `status_pagamento` (Pago/Vencido/Em aberto) é decidido comparando a data de vencimento com o fim da janela de histórico (o "hoje" fictício do case).
- **As 7 fontes de dados do roadmap estão geradas.** Fase 1 (Base fictícia) completa.
- `python src/gerador_dados/gerar_dim_calendario.py` gera `dim_calendario.csv` (1277 dias, 2023-01-01 a 2026-06-30 — mais largo que a janela de histórico de propósito, ver docstring do script). Sem sujeira, sem seed (determinístico). Marcar como tabela de datas no Power BI.
- **Fase 2 (ETL e modelo) em andamento.** Modelo estrela rascunhado em `docs/modelo_dados.md` (3 dimensões + 5 fatos). Checklist de limpeza por fonte em `powerbi/checklist_power_query.md`. Nenhum dos dois foi testado no Power BI ainda — são planos, não resultado. O trabalho de Power Query em si acontece na interface do Power BI Desktop, fora do que o Claude Code executa diretamente.
- Funções repetidas entre os geradores (sorteio ponderado, gravação de CSV) ficam em `src/gerador_dados/utils.py`.
- Janela de histórico: 2024-01-01 a 2025-12-31 (24 meses). Todas as tabelas devem usar a mesma janela.
