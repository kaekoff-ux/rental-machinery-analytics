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

## Status em 31/10/2026

| Passo | Situação | Como foi verificado |
| --- | --- | --- |
| 1. Página mínima | Feito (já com a estrutura completa) | Abre direto pelo arquivo e por servidor local |
| 2. Estrutura completa | Feito (capítulos em pop-ups com slides) | Pop-ups abertos e conferidos no Chrome |
| 3. Formulário | Feito (pop-up em dois passos) | Validação testada: campos obrigatórios e "telefone ou e-mail" |
| 4. Captura local | Feito | Envio mostra confirmação com resumo e imprime os dados no console (F12) |
| 5. Apps Script | **Código pronto, falta publicar** (precisa da sua conta Google) | Não testado |
| 6. Visual | Feito, revisado três vezes | 320, 390, 768, 1024, 1120, 1200, 1366×657, 1440 e 1920 px: sem rolagem lateral e cabeçalho em uma linha; também sem JavaScript. Pop-ups cabem sem rolar em tablet e notebook; no celular (folha que sobe de baixo) alguns rolam por dentro, de propósito. Mais 12 telas de tablet, em pé e deitado (ver abaixo) |
| 7. GitHub Pages | Feito em 31/10/2026 (opção A: branch `main`, pasta raiz) | Build sem erro; página, CSS, JS, 7 imagens e vídeo respondendo 200; no Chrome do computador, vídeo tocando, 9 pop-ups abrindo e console sem erros. Não testado em celular ou tablet de verdade |
| 8. Link no CLAUDE/README | Feito em 31/10/2026 | Link em `README.md` e `CLAUDE.md` |

Referência visual escolhida pelo usuário: a estrutura de
[scarpantiempilhadeiras.com.br](https://www.scarpantiempilhadeiras.com.br/) (cabeçalho fixo com
telefone, topo escuro com foto e faixa rolante de serviços, serviços, faixa de números,
categorias de equipamento, bloco escuro de chamada, rodapé em colunas e botão flutuante de
WhatsApp). A estrutura foi seguida. Depoimentos e logos de marcas não entraram: numa empresa
fictícia seriam inventados.

Revisão de 31/10/2026, a pedido do usuário: visual mais moderno e contido (escala de texto e
espaços menores, conteúdo limitado a 1200 px), botões em pílula com transparência, cartões de
vidro, brilhos suaves, faixa rolante virou letreiro de LED fino, e as chamadas de ação passaram a
abrir pop-ups: orçamento (com o formulário), simulador, unidade (máquinas por tipo naquela
unidade) e "sobre o case". Nesse ponto o pedido do usuário vale mais que as regras da skill de
design (que proíbem vidro, sombra e brilho).

Segunda revisão de 31/10/2026, seguindo prints do usuário: a página inicial ficou só com topo,
letreiro, números, chamada de orçamento e rodapé enxuto. Serviços, Frota, Como funciona, Quem
somos e Unidades viraram pop-ups com slides laterais (abertos pelo menu e pelos números). O
orçamento virou um pop-up em dois passos com o simulador no primeiro. Só três botões "Pedir
orçamento" ficam na página (cabeçalho, topo e bloco final). No canto inferior entrou o botão
"Atendimento" do Telegram, que abre um aviso enquanto o chat bot (Camada 3) não existe. As
fotos da história deixaram de ter moldura: o script de imagens recorta a borda preta do retrato
e o letreiro do barracão.

Terceira revisão de 31/10/2026:

- **Animação no topo:** vídeo do Gemini (voo de drone sobre a unidade, 10 s, 1280×720) em
  `docs/videos/01_hero_animacao.mp4`, copiado para `site/video/hero.mp4`. Só toca a partir de
  960 px de largura, sem "economia de dados" e sem "reduzir movimento"; nos outros casos fica a
  foto, que é igual ao primeiro quadro. Perto do fim de cada volta o vídeo some sobre a foto,
  para a repetição não ter corte seco, e ele pausa quando o topo sai da tela. O botão "Pausar
  animação" para vídeo, foto e letreiro (exigência de acessibilidade para movimento automático
  com mais de 5 s).
- **Slide 2016:** mural em faixa larga em cima e texto embaixo, como o slide de 1992; "Ver o
  mural inteiro" amplia dentro do pop-up.
- **Quem somos no celular:** só texto. Cada foto está num `<picture>` que, no celular, entrega
  um ponto transparente, então as fotos nem são baixadas.
- **Área do cliente:** botão no cabeçalho (ícone de pessoa) e no rodapé, abrindo um aviso de
  "em planejamento". O escopo será discutido (ver `spec.md`, seção 9).
- **Revisão de design e técnica:** contraste do link âmbar dos números (passava de 3,9:1 para
  acima de 4,5:1), rodapé com folga para o botão "Atendimento", página que não "pula" ao abrir
  pop-up (`scrollbar-gutter`), foco no próprio pop-up ao abrir (sem anel solto no botão de
  fechar), cabeçalho cabendo em 320 px, pop-ups cabendo em notebook 1366×768, véu mais escuro
  atrás do título (o letreiro da fachada competia com ele), botão de pausa fora do caminho do
  "Atendimento", fonte só com as larguras e pesos usados, fotos da frota pedidas só se existirem
  (sem erros 404), prévia de link para LinkedIn/WhatsApp (`og:image`) e links "Entenda o projeto"
  e "Sobre o case" levando ao GitHub quando não há JavaScript.

Simulação em tablets antes de publicar (31/10/2026), com a área visível do navegador de cada
aparelho: iPad mini (744×1063 em pé, 1133×674 deitado), iPad 10/Air (820×1110, 1180×750),
iPad Pro 11 (834×1120, 1194×764), iPad Pro 12,9 (1024×1290, 1366×950), Galaxy Tab S9
(800×1200, 1280×720) e iPad 9,7 (768×950, 1024×690). Só o iPad mini em pé falhou: com 744 px
ele caía no layout de celular e o pop-up Unidades rolava 28 px. O limite entre celular e tablet
passou de 768 px (48rem) para 736 px (46rem), no CSS e nas imagens do Quem somos, e o "Como
funciona" mostra 2 etapas por vez de 736 a 959 px e 3 a partir de 960 px. Depois do ajuste, as
12 telas passaram: sem rolagem lateral, cabeçalho de 64 px, títulos em até 2 linhas e os 6
pop-ups cabendo sem rolar. Em 320 px o texto do topo ocupa 4 linhas, o que é aceitável nessa
largura. Não testado em aparelho de verdade.

## Arquivos

```text
rental-machinery-analytics/
├── site/                         o que vai para o GitHub Pages
│   ├── index.html                conteúdo e estrutura
│   ├── estilo.css                visual (cores e tamanhos no topo, em variáveis)
│   ├── script.js                 contatos, pop-ups, carrossel, pedido, animação do topo
│   ├── img/                      imagens leves geradas pelo script abaixo
│   │   └── frota/disponiveis.js  lista das fotos da frota que existem (gerada pelo script)
│   └── video/hero.mp4            animação do topo (cópia de docs/videos/01_hero_animacao.mp4)
├── src/site/otimizar_imagens.py  docs/imagens -> site/img (máx. 1400 px, JPEG 80): história,
│                                 mural de 2016, Missão/Visão/Valores, fotos da frota quando
│                                 existirem, a lista disponiveis.js e a cópia do vídeo
├── docs/videos/                  vídeos originais (o do topo veio do Gemini em 31/10/2026)
├── src/apps_script/receber_orcamento.gs   backend do formulário (passo 5)
└── docs/prompts_imagens_frota.md lista dos 7 equipamentos e prompts das fotos da frota
```

### Onde mudar cada coisa

- **Telefones, WhatsApp, e-mail, endereços e horário:** só no objeto `CONTATO`, no topo de
  `site/script.js`. Hoje estão genéricos (`(15) 0000-0000`, `Av. Exemplo, 1000`,
  `contato@locamaq.example`). O botão flutuante de WhatsApp aparece sozinho quando o campo
  `whatsapp` deixa de estar vazio.
- **Destino do formulário:** `URL_APPS_SCRIPT`, logo abaixo de `CONTATO`.
- **Pop-ups:** são os elementos `<dialog>` de `site/index.html`. Qualquer botão com
  `data-abrir="id-do-pop-up"` abre um deles. Os slides de cada pop-up ficam dentro de
  `<div class="slides">`; setas e pontinhos são criados pelo `script.js`. Sem JavaScript, os
  pop-ups aparecem como seções comuns da página.
- **Telegram:** campo `telegram` do `CONTATO` (nome do bot, sem @). Vazio, o botão
  "Atendimento" abre o aviso de "em breve"; preenchido, abre o chat em `t.me`.
- **Cores e tamanhos:** variáveis no topo de `site/estilo.css`.
- **Fotos da frota:** salvar em `docs/imagens/frota/` com os nomes de
  `docs/prompts_imagens_frota.md` e rodar `python src/site/otimizar_imagens.py`. O script
  atualiza a lista `site/img/frota/disponiveis.js`, e o site passa a mostrar as fotos novas.
- **Animação do topo:** trocar `docs/videos/01_hero_animacao.mp4` e rodar o mesmo script. O
  vídeo deve começar no mesmo enquadramento de `docs/imagens/03_unidade_atual.jpg`, que fica
  por baixo dele.
- **Área do cliente:** o aviso é o pop-up `modal-cliente` em `site/index.html`.
- O site tem `noindex` (não aparece no Google) para não se misturar a empresas reais de nome
  parecido. Para um portfólio, o acesso é pelo link direto.

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

## Passo 5 em detalhe: ligar o formulário à planilha

Feito por você, porque usa a sua conta Google. Os nomes de menu abaixo foram escritos de
memória, sem conferir a documentação do Google nesta data; se algum mudou, procure a função
equivalente.

1. No Google Drive, crie uma planilha nova chamada `LocaMaq - Leads`.
2. Em Arquivo > Configurações, deixe o fuso horário em "(GMT-03:00) São Paulo": a coluna
   `data_envio` usa o fuso da planilha.
3. Em Extensões > Apps Script, apague o conteúdo de `Código.gs`, cole
   `src/apps_script/receber_orcamento.gs` e salve.
4. Implantar > Nova implantação > tipo "App da Web". Executar como: "Eu". Quem pode acessar:
   "Qualquer pessoa". Autorize o acesso à planilha (o aviso de "app não verificado" aparece
   porque o script é seu; siga por "Avançado").
5. Copie a URL que termina em `/exec` e abra no navegador: deve aparecer `{"ok":true,...}`.
6. Cole a URL em `URL_APPS_SCRIPT`, no topo de `site/script.js`.
7. Envie um pedido pelo site com dados fictícios e confira a linha nova na aba `Leads`.

Cuidados: depois de mudar o código do Apps Script, publique uma nova versão em "Gerenciar
implantações" (a URL continua a mesma). A URL fica visível no `script.js`, então qualquer pessoa
pode mandar linhas para essa planilha; o campo-isca e o limite de tamanho reduzem o lixo, mas
não guarde nada sensível nela.

## Passo 7 em detalhe: publicar no GitHub Pages

Feito em 31/10/2026 com a opção A. Endereço do site:
<https://kaekoff-ux.github.io/rental-machinery-analytics/site/> (a raiz,
<https://kaekoff-ux.github.io/rental-machinery-analytics/>, mostra o README). O endereço não muda
nas atualizações: cada push na `main` dispara um novo build e o site atualiza em 1 a 2 minutos
(Ctrl+F5 mostra a versão nova sem cache). O andamento do build aparece na aba Actions do
repositório. Como o site tem `noindex`, ele não aparece em buscas: divulgue o link direto.

O GitHub Pages publica a raiz do repositório ou a pasta `docs/`, não uma pasta `site/`
escolhida livremente. Duas saídas:

- **A (mais simples, recomendada agora):** em Settings > Pages, "Deploy from a branch", branch
  `main`, pasta `/ (root)`. O site fica em
  `https://kaekoff-ux.github.io/rental-machinery-analytics/site/`. Não exige automação.
- **B:** um workflow do GitHub Actions publica só a pasta `site/`, e o endereço perde o `/site/`.
  Fica para depois, se o endereço mais curto fizer diferença.

Antes de publicar: commit e push dos arquivos novos (o `.gitignore` já foi corrigido para não
ignorar `site/`). Depois, abrir o link no computador e no celular. A prévia de link
(`og:image` no `<head>` do `index.html`) aponta para o endereço da opção A; se a opção for B,
trocar `/site/img/` por `/img/` nessa linha.

Para ver no celular antes de publicar (mesmo Wi-Fi): rodar `python -m http.server 8765 --bind
0.0.0.0` dentro de `site/` e abrir `http://IP-DO-COMPUTADOR:8765` no celular (o IP aparece em
`ipconfig`). Com o Wi-Fi marcado como rede "Pública" no Windows, o firewall bloqueia: permita o
Python ou marque a rede de casa como "Privada". Feche com Ctrl+C ao terminar.

## Pendências e decisões em aberto

- Publicar o Apps Script (passo 5). O GitHub Pages (passo 7) foi publicado em 31/10/2026.
- Abrir o site publicado num celular e num tablet de verdade (até agora só simulado).
- Área do cliente: discutir escopo, login e onde ficam os pedidos (`spec.md`, seção 9).
- Fotos da frota: gerar as 7 imagens (`docs/prompts_imagens_frota.md`).
- Vídeo do topo: recomprimir quando houver ffmpeg (hoje 4 MB, sem recompressão).
- `03_unidade_atual.jpg`: máquinas ainda amarelas (a animação também).

## O que vem depois (não é desta camada)

Camada 2 (fluxo interno: vendedor/atendimento/oficina/contratação), Camada 3 (N8N +
Telegram), Camada 4 (Power BI, pendência do usuário, roda em paralelo sem depender desta
camada) e Camada 5 (DuckDB + RAG + MCP + agentes + Streamlit, só depois da Camada 4). Ver
`spec.md`, seções 3 e 8, para o mapa completo.
