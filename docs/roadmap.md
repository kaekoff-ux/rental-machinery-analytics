PROJETO RENTAL MACHINERY - ROADMAP E ESCOPO
Case de portfólio: gestão de locação de máquinas pesadas (dados 100% fictícios)

1. CONTEXTO
Projeto de estudo aplicado, inspirado em um anúncio público do Workana ("Especialista em Excel, IA e Power Query para modernização da gestão de locação de máquinas pesadas"). Não há dados nem dores reais de cliente. Toda a base é fictícia e gerada por script. Em qualquer publicação, deixar claro: "case com dados fictícios".

Objetivo: demonstrar o ciclo completo
entender o problema > consolidar os dados > analisar > automatizar > aplicar IA > medir o resultado.

2. EMPRESA FICTÍCIA: LOCAMAQ
Locadora de máquinas pesadas com filiais em SP.
Segmentos: escavadeiras, retroescavadeiras, pás-carregadeiras, guindastes, geradores, empilhadeiras e plataformas elevatórias.
Frota sugerida: 120 a 150 equipamentos, 24 meses de histórico, 60 a 80 clientes.

3. FONTES DE DADOS (7)
1) Cadastro de equipamentos
2) Clientes
3) Contratos de locação
4) Horímetro / telemetria
5) Ordens de manutenção
6) Abastecimento
7) Faturamento e inadimplência
Os arquivos "brutos" terão sujeira realista de propósito: datas em formatos diferentes, duplicidades, nomes de cliente divergentes, tipos de manutenção escritos de várias formas, leituras de horímetro que diminuem. Isso dá sentido ao Power Query.

4. INDICADORES (KPIs)
Utilização física, disponibilidade física, utilização financeira, receita por máquina, margem por máquina, custo de manutenção por hora, mix preventiva x corretiva, MTBF, MTTR, contratos a vencer, inadimplência, consumo de combustível por hora e comparações temporais (mês anterior, acumulado no ano, mesmo mês do ano anterior). Definições e fórmulas na pasta 03_KPIs.

5. STACK
- Power BI Desktop (gratuito): entregável principal
- Excel com Power Query e Power Pivot: versão espelho do que o anúncio pede
- Google Sheets: cadastro e apontamentos (não tem Power Query, não é o centro da análise)
- Python + Claude Code: geração da base fictícia, modelo preditivo, app e agentes
- GitHub: repositório público do projeto
Decisão de arquitetura: os dados ficam em pasta local/repositório (CSV). Isso evita o problema de atualização do Power Query via SharePoint. Documentar isso no case.

6. ROADMAP (aprox. 12 semanas, 1 hora por dia)
FASE 0 - Fundação (semana 1)
Entregas: repositório no GitHub, dicionário de dados, lista de KPIs, CLAUDE.md.
Aprende: Git/GitHub básico, documentação.

FASE 1 - Base fictícia (semanas 2-3)
Entrega: script Python (feito com Claude Code) que gera as 7 fontes com sujeira realista, com seed fixa para ser reprodutível.
Aprende: Claude Code na prática, Python básico.

FASE 2 - ETL e modelo (semanas 4-5)
Entrega: Power Query consolidando as fontes e modelo estrela (fato locação, fato manutenção, fato faturamento; dimensões equipamento, cliente, calendário).
Aprende: Power Query avançado, modelagem de dados.

FASE 3 - DAX e dashboard (semanas 6-7)
Entrega: dashboard Power BI com os KPIs e comparações temporais.
Aprende: tabela calendário, CALCULATE, TOTALYTD, SAMEPERIODLASTYEAR, DATEADD (nessa ordem).

FASE 4 - Versão Excel (semana 8)
Entrega: dashboard em Excel com Power Pivot.
Aprende: Power Pivot e tabelas dinâmicas.

FASE 5 - IA preditiva (semanas 9-10)
Entrega: risco de parada por máquina e previsão de demanda por segmento, integrados ao dashboard.
Aprende: ML básico aplicado e interpretação de resultados.

FASE 6 - App e agentes (semanas 11-12)
Entrega: app de ordens de serviço de manutenção (Claude Code) com 2 a 3 agentes: alerta de preventiva vencendo, qualidade de dados, resumo semanal. Assistente em linguagem natural sobre os dados.
Aprende: agentes de IA, integração de sistemas.

FASE 7 - Portfólio (contínuo)
Entrega: case documentado, um post no LinkedIn por fase, README no GitHub, amostra para propostas no Workana.

7. FASE 0 - PLANO DA SEMANA 1 (1 hora por dia)
Dia 1: criar conta no GitHub e instalar o Git. Criar o repositório "rental-machinery-analytics".
Dia 2: clonar o repositório no computador e copiar os arquivos da pasta 04_GitHub_Setup (README.md e CLAUDE.md).
Dia 3: revisar o dicionário de dados e ajustar campos que façam sentido para você (sua experiência com ativos e peças vale aqui).
Dia 4: revisar os KPIs e as fórmulas. Marcar quais você já sabe calcular e quais vai aprender.
Dia 5: primeiro commit e push com toda a documentação. Testar o Claude Code lendo o CLAUDE.md.
Dia 6: rascunhar o texto do case (problema e objetivo) na pasta 05.
Dia 7: folga ou ajustes. Publicar post curto no LinkedIn anunciando o projeto de estudo (opcional).

Critério de pronto da Fase 0: repositório no GitHub com documentação, e o Claude Code consegue descrever o projeto ao abrir a pasta.

8. REGRAS DE HONESTIDADE DO PORTFÓLIO
- Sempre identificar como case com dados fictícios.
- Não declarar experiência profissional em locação ou em Power BI que não existe. Descrever como "projeto de estudo aplicado".
- No Workana, usar como amostra de trabalho na proposta, sem dizer que foi feito para cliente real.

