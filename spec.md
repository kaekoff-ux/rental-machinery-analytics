# spec.md — LocaMaq: sistema integrado de atendimento, gestão e IA

> Case de portfólio com dados 100% fictícios (empresa "LocaMaq"). PRD no formato da aula
> "Planejamento Estratégico com PRD" (Hashtag No Code e IA), adaptado ao projeto. Consulte
> também `docs/roadmap.md` (fases originais de BI) e `docs/quem_somos.md` (história, missão,
> visão, valores, paleta visual).

## 1. Dor do usuário

Hoje a gestão de uma locadora de máquinas pesadas fica fragmentada em pontos que não
conversam entre si: não existe um site que capte pedidos de orçamento diretamente dos
clientes; não há um canal de atendimento ágil (como Telegram) ligado ao fluxo comercial; e o
controle de equipamentos, manutenção, contratos e faturamento vive espalhado em fontes
manuais (planilhas/CSVs, com o dashboard de BI ainda pendente). Resultado: a jornada do
cliente — do primeiro contato até a locação assinada — e a operação interna — venda,
atendimento, oficina — não têm um sistema único que as integre.

## 2. Proposta de valor

Um sistema integrado, construído em camadas sobre a base de dados fictícia já existente da
LocaMaq, que cobre o ciclo completo: **captação do cliente** (site + Telegram) →
**orquestração do atendimento** (N8N, a definir módulo por módulo) → **fluxo comercial
interno** (recebido → vendedor → atendimento → oficina → contratação) → **gestão de
dados/frota** (modelo estrela, Power BI) → **inteligência aplicada** (RAG + MCP + agentes de
IA para perguntas em linguagem natural e alertas proativos). Cada camada entrega valor por si
só, permitindo mostrar progresso de portfólio ao longo do caminho.

## 3. Funcionalidades principais

| Camada | Funcionalidade |
|---|---|
| 1 | Site institucional + formulário de orçamento/contato |
| 2 | Fluxo interno: recebido → vendedor → atendimento → oficina → contratação |
| 3 | Orquestração via N8N e canal Telegram (ferramenta exata a decidir módulo por módulo) |
| 4 | Dashboard Power BI com os 18 KPIs de `docs/kpis.csv` |
| 5 | Camada de inteligência: DuckDB + RAG (dicionário/KPIs) + servidor MCP + agente de texto-para-SQL + app Streamlit (gráficos + chat) + agentes de regra (preventiva, qualidade de dados, resumo semanal) |

## 4. Recursos essenciais (MVP)

Primeiro incremento (Camada 1, em construção): página institucional da LocaMaq (história,
missão, visão, valores, frota em destaque) + formulário de orçamento, publicados no GitHub
Pages, com captura real de leads via Google Apps Script → Google Sheet. Sem backend de
orquestração ainda — esse é o ponto exato onde a Camada 3 vai plugar depois.

## 5. Público-alvo e perfis

- **Cliente final** — empresas/obras que precisam alugar equipamento; pede orçamento pelo
  site ou Telegram; pouco interesse em detalhes técnicos, quer resposta rápida.
- **Vendedor** — recebe o lead, negocia condições, fecha o contrato.
- **Atendimento** — faz a triagem e o acompanhamento do pedido entre as etapas.
- **Oficina** — inspeciona/prepara o equipamento antes e depois da locação (já existe como
  módulo de controle via `status_os` em `ordens_manutencao.csv`).
- **Gestor (dono da locadora)** — acompanha KPIs no dashboard Power BI e conversa com os
  dados pelo chat de IA (Camada 5).

## 6. Arquitetura técnica

| Camada | Stack |
|---|---|
| 1 | HTML + CSS + JavaScript puro, hospedagem GitHub Pages |
| 1 (backend do form) | Google Apps Script (Web App) → Google Sheet |
| 3 | N8N (Community Edition self-hosted, gratuito) + API do Telegram — decisão de escopo exato em aberto |
| 4 | Power BI Desktop, modelo estrela (3 dimensões + 5 fatos) sobre `data/processed/*.csv` |
| 5 | DuckDB (camada de consulta) + servidor MCP em Python + RAG por contexto fixo (sem embeddings) sobre `docs/dicionario_dados.csv`/`docs/kpis.csv`/`docs/modelo_dados.md` + Streamlit + modelo Claude Haiku (custo-benefício) |

## 7. Direção visual

Paleta definida em `docs/quem_somos.md`: verde-musgo `#4A5D3A` (principal), laranja queimado
`#C8651B` (destaque), marrom terra `#6B4A32` (apoio), areia `#E8DCC4` (fundo), azul-petróleo
`#2F5D62` (complementar). Tom documental e caloroso, ancorado na história fictícia da
LocaMaq (Seu José, 1992 → unidade atual). Usar a skill de design de páginas ao construir
qualquer página pública, para evitar visual genérico.

## 8. Processo

- Construir em camadas independentes (1 a 5), cada uma terminando em algo visível e
  testável — ver `docs/roadmap.md` para as fases originais de BI (0-7) e o plano de
  implementação detalhado (mantido fora do repositório, nas notas de planejamento da sessão).
- Ordem combinada: Camada 1 (site) primeiro; Camada 4 (Power BI) em paralelo, sem bloquear
  nem ser bloqueada; Camada 5 só depois da Camada 4; Camadas 2-3 (fluxo interno/orquestração)
  com decisões técnicas em aberto, a fechar quando chegar a vez delas.
- Passos pequenos, cada um verificável (abrir no navegador, ver linha nova na planilha, ver
  alerta correto no terminal) — ritmo adequado a quem está aprendendo HTML/JSON/Python aos
  poucos.
- Honestidade de portfólio: todo texto público deve identificar a LocaMaq como case
  fictício, sem insinuar experiência profissional ou operação real.

---
> Consolidado a partir das decisões tomadas em sessão de planejamento com Claude Code.
