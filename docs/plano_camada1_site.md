# Plano — Camada 1: site do cliente (próximo passo prioritário)

> Se você é uma sessão nova do Claude Code abrindo este repositório: este é o **próximo
> passo a executar**. Leia `spec.md` primeiro para o contexto completo do projeto; este
> arquivo é só o passo a passo detalhado desta camada específica.

## Objetivo

Uma landing page pública da LocaMaq com formulário de orçamento/contato, publicada no
GitHub Pages, ensinando HTML/CSS/JS básico no processo (o usuário é iniciante nessas
tecnologias — passos pequenos, cada um terminando em algo visível no navegador).

## Decisões já travadas para esta camada (não alterar sem o usuário pedir)

- Stack: **HTML + CSS + JavaScript puro**, sem framework (nada de React/Vue/Next).
- Hospedagem: **GitHub Pages**, dentro deste mesmo repositório.
- Backend do formulário: **formulário HTML próprio** (não Google Forms embutido, para manter
  o visual integrado ao site) enviando para um **Google Apps Script publicado como Web App**,
  que grava numa Google Sheet. Motivo: Formspree e Web3Forms só liberam webhook no plano
  pago; Google Apps Script é gratuito e sem limite relevante.
- Todo texto público deve deixar claro que é case com dados fictícios.

## Arquivos a criar

```
rental-machinery-analytics/
└── site/
    ├── index.html
    ├── estilo.css
    └── script.js
```

## Passo a passo (cada um visível no navegador)

1. **Página mínima** — `site/index.html` com texto simples (nome da LocaMaq, frase curta).
   Verificação: abrir o arquivo local no navegador.
2. **Estrutura completa** — seções hero, "sobre a LocaMaq" (usar a história/missão/visão já
   escritas em `docs/quem_somos.md`, deixando claro que é case fictício), equipamentos em
   destaque (os 7 segmentos reais de `data/processed/cadastro_equipamentos.csv`: escavadeira,
   retroescavadeira, pá-carregadeira, guindaste, empilhadeira, plataforma elevatória,
   gerador), formulário de orçamento e rodapé. Ainda sem estilo.
3. **Formulário de orçamento** — campos: nome, telefone/e-mail, cidade, tipo de equipamento
   (lista dos 7 segmentos reais), prazo desejado, observação.
4. **Captura do envio, versão local** — `script.js` intercepta o envio e mostra confirmação
   na tela + imprime no console (F12). JavaScript puro no navegador não grava arquivo no
   servidor sem backend — por isso o próximo passo é necessário.
5. **Backend real via Google Apps Script** — publicar um Apps Script como "Web App",
   vinculado a uma Google Sheet nova (`LocaMaq - Leads`), que recebe o POST do `script.js` e
   grava uma linha por envio (nome, contato, cidade, equipamento, prazo, data). Trocar o
   passo 4 para enviar de fato pra essa URL. Verificação: preencher o formulário no site e
   ver a linha nova na Sheet.
6. **Visual** — aplicar CSS (ou Tailwind via CDN) usando a skill de design de landing pages
   (`design-taste-frontend`) para não ficar com "cara de formulário cru". Testar também em
   largura de celular.
7. **Publicar no GitHub Pages** — configurar o repositório para publicar a pasta `site/` (ou
   branch dedicado). Testar o link público, inclusive no celular.
8. **Atualizar `CLAUDE.md`/`README.md`** — nova seção com o link do site publicado.

## O que vem depois (não é desta camada)

Camada 2 (fluxo interno: vendedor/atendimento/oficina/contratação), Camada 3 (N8N +
Telegram), Camada 4 (Power BI, pendência do usuário, roda em paralelo sem depender desta
camada) e Camada 5 (DuckDB + RAG + MCP + agentes + Streamlit, só depois da Camada 4). Ver
`spec.md`, seções 3 e 8, para o mapa completo.
