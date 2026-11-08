# Rental Machinery Analytics

Projeto de estudo aplicado em dados, automação e IA para **gestão de locação de máquinas pesadas**.

> **Aviso:** todos os dados deste repositório são **fictícios**, gerados por script. O projeto foi inspirado em um anúncio público de vaga e não representa um cliente real.

## Problema
Locadoras de máquinas pesadas costumam ter dados espalhados em várias planilhas e sistemas (contratos, manutenção, horímetro, faturamento). Isso dificulta enxergar utilização, custo por máquina, risco de parada e inadimplência.

## O que o projeto entrega
- Base fictícia realista, com sujeira proposital, de uma locadora (LocaMaq)
- Consolidação e tratamento dos dados com Power Query
- Modelo de dados em estrela e dashboards em Power BI e Excel
- Indicadores de utilização, disponibilidade, margem, manutenção e inadimplência
- Modelo preditivo de risco de parada e previsão de demanda
- App de ordens de serviço de manutenção com agentes de IA
- Site de apresentação da locadora fictícia, com pedido de orçamento
- Captura de leads do site com n8n, Google Sheets, confirmação por e-mail e alertas por categoria no Slack, funil de vendas e indicadores de leads (conversão, tempo de fechamento, perdas por motivo e por falta de máquina)

## Site da LocaMaq
Página da locadora fictícia, com frota, unidades, história e pedido de orçamento:
[kaekoff-ux.github.io/rental-machinery-analytics/site](https://kaekoff-ux.github.io/rental-machinery-analytics/site/)

Textos, números, contatos e imagens são ilustrativos; as imagens e a animação foram geradas por IA. O código está em `site/`.

O pedido de orçamento chega a um fluxo do n8n (em um servidor na AWS) que gera o número do lead, grava na planilha Google, envia e-mail de confirmação ao cliente e avisa a equipe comercial no Slack no canal específico da categoria do equipamento (cópia do fluxo em `src/n8n/leads_locamaq.json`; a instalação do servidor não é versionada). A política de privacidade do site: [site/privacidade.html](https://kaekoff-ux.github.io/rental-machinery-analytics/site/privacidade.html).

## Stack
Power BI Desktop, Excel (Power Query e Power Pivot), Python, HTML, CSS e JavaScript (GitHub Pages), n8n, Docker, AWS (EC2), ngrok, Slack, Google Sheets, Gmail, Claude Code, Google Antigravity, GitHub.

## Status
Fase 1 (base fictícia) completa e Fase 2 (tratamento e modelo de dados) em andamento. O site da LocaMaq está publicado e o formulário de orçamento grava os leads numa planilha Google pelo n8n (desde 05/11/2026), com envio automático de confirmação por e-mail e distribuição por categoria de máquina no Slack (desde 08/11/2026). Os dados de 2026 (contratos, faturas e leads) estão em `data/processed/extensao_2026/`, separados da base de 2024-2025. Veja o roadmap em `docs/roadmap.md`.

## Autor
Carlos - engenheiro mecânico em transição para dados, automação e IA aplicada a operações industriais.
