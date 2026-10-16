PROJETO RENTAL MACHINERY - ROADMAP E ESCOPO
Case de portfÃ³lio: gestÃ£o de locaÃ§Ã£o de mÃ¡quinas pesadas (dados 100% fictÃ­cios)

1. CONTEXTO
Projeto de estudo aplicado, inspirado em um anÃºncio pÃºblico do Workana ("Especialista em Excel, IA e Power Query para modernizaÃ§Ã£o da gestÃ£o de locaÃ§Ã£o de mÃ¡quinas pesadas"). NÃ£o hÃ¡ dados nem dores reais de cliente. Toda a base Ã© fictÃ­cia e gerada por script. Em qualquer publicaÃ§Ã£o, deixar claro: "case com dados fictÃ­cios".

Objetivo: demonstrar o ciclo completo
entender o problema > consolidar os dados > analisar > automatizar > aplicar IA > medir o resultado.

2. EMPRESA FICTÃCIA: LOCAMAQ
Locadora de mÃ¡quinas pesadas com filiais em SP.
Segmentos: escavadeiras, retroescavadeiras, pÃ¡s-carregadeiras, guindastes, geradores, empilhadeiras e plataformas elevatÃ³rias.
Frota sugerida: 120 a 150 equipamentos, 24 meses de histÃ³rico, 60 a 80 clientes.

3. FONTES DE DADOS (7)
1) Cadastro de equipamentos
2) Clientes
3) Contratos de locaÃ§Ã£o
4) HorÃ­metro / telemetria
5) Ordens de manutenÃ§Ã£o
6) Abastecimento
7) Faturamento e inadimplÃªncia
Os arquivos "brutos" terÃ£o sujeira realista de propÃ³sito: datas em formatos diferentes, duplicidades, nomes de cliente divergentes, tipos de manutenÃ§Ã£o escritos de vÃ¡rias formas, leituras de horÃ­metro que diminuem. Isso dÃ¡ sentido ao Power Query.

4. INDICADORES (KPIs)
UtilizaÃ§Ã£o fÃ­sica, disponibilidade fÃ­sica, utilizaÃ§Ã£o financeira, receita por mÃ¡quina, margem por mÃ¡quina, custo de manutenÃ§Ã£o por hora, mix preventiva x corretiva, MTBF, MTTR, contratos a vencer, inadimplÃªncia, consumo de combustÃ­vel por hora e comparaÃ§Ãµes temporais (mÃªs anterior, acumulado no ano, mesmo mÃªs do ano anterior). DefiniÃ§Ãµes e fÃ³rmulas na pasta 03_KPIs.

5. STACK
- Power BI Desktop (gratuito): entregÃ¡vel principal
- Excel com Power Query e Power Pivot: versÃ£o espelho do que o anÃºncio pede
- Google Sheets: cadastro e apontamentos (nÃ£o tem Power Query, nÃ£o Ã© o centro da anÃ¡lise)
- Python + Claude Code: geraÃ§Ã£o da base fictÃ­cia, modelo preditivo, app e agentes
- GitHub: repositÃ³rio pÃºblico do projeto
DecisÃ£o de arquitetura: os dados ficam em pasta local/repositÃ³rio (CSV). Isso evita o problema de atualizaÃ§Ã£o do Power Query via SharePoint. Documentar isso no case.

6. ROADMAP (aprox. 12 semanas, 1 hora por dia)
FASE 0 - FundaÃ§Ã£o (semana 1)
Entregas: repositÃ³rio no GitHub, dicionÃ¡rio de dados, lista de KPIs, CLAUDE.md.
Aprende: Git/GitHub bÃ¡sico, documentaÃ§Ã£o.

FASE 1 - Base fictÃ­cia (semanas 2-3)
Entrega: script Python (feito com Claude Code) que gera as 7 fontes com sujeira realista, com seed fixa para ser reprodutÃ­vel.
Aprende: Claude Code na prÃ¡tica, Python bÃ¡sico.

FASE 2 - ETL e modelo (semanas 4-5)
Entrega: Power Query consolidando as fontes e modelo estrela (fato locaÃ§Ã£o, fato manutenÃ§Ã£o, fato faturamento; dimensÃµes equipamento, cliente, calendÃ¡rio).
Aprende: Power Query avanÃ§ado, modelagem de dados.

FASE 3 - DAX e dashboard (semanas 6-7)
Entrega: dashboard Power BI com os KPIs e comparaÃ§Ãµes temporais.
Aprende: tabela calendÃ¡rio, CALCULATE, TOTALYTD, SAMEPERIODLASTYEAR, DATEADD (nessa ordem).

FASE 4 - VersÃ£o Excel (semana 8)
Entrega: dashboard em Excel com Power Pivot.
Aprende: Power Pivot e tabelas dinÃ¢micas.

FASE 5 - IA preditiva (semanas 9-10)
Entrega: risco de parada por mÃ¡quina e previsÃ£o de demanda por segmento, integrados ao dashboard.
Aprende: ML bÃ¡sico aplicado e interpretaÃ§Ã£o de resultados.

FASE 6 - App e agentes (semanas 11-12)
Entrega: app de ordens de serviÃ§o de manutenÃ§Ã£o (Claude Code) com 2 a 3 agentes: alerta de preventiva vencendo, qualidade de dados, resumo semanal. Assistente em linguagem natural sobre os dados.
Aprende: agentes de IA, integraÃ§Ã£o de sistemas.

FASE 7 - PortfÃ³lio (contÃ­nuo)
Entrega: case documentado, um post no LinkedIn por fase, README no GitHub, amostra para propostas no Workana.

7. FASE 0 - PLANO DA SEMANA 1 (1 hora por dia)
Dia 1: criar conta no GitHub e instalar o Git. Criar o repositÃ³rio "rental-machinery-analytics".
Dia 2: clonar o repositÃ³rio no computador e copiar os arquivos da pasta 04_GitHub_Setup (README.md e CLAUDE.md).
Dia 3: revisar o dicionÃ¡rio de dados e ajustar campos que faÃ§am sentido para vocÃª (sua experiÃªncia com ativos e peÃ§as vale aqui).
Dia 4: revisar os KPIs e as fÃ³rmulas. Marcar quais vocÃª jÃ¡ sabe calcular e quais vai aprender.
Dia 5: primeiro commit e push com toda a documentaÃ§Ã£o. Testar o Claude Code lendo o CLAUDE.md.
Dia 6: rascunhar o texto do case (problema e objetivo) na pasta 05.
Dia 7: folga ou ajustes. Publicar post curto no LinkedIn anunciando o projeto de estudo (opcional).

CritÃ©rio de pronto da Fase 0: repositÃ³rio no GitHub com documentaÃ§Ã£o, e o Claude Code consegue descrever o projeto ao abrir a pasta.

8. REGRAS DE HONESTIDADE DO PORTFÃ“LIO
- Sempre identificar como case com dados fictÃ­cios.
- NÃ£o declarar experiÃªncia profissional em locaÃ§Ã£o ou em Power BI que nÃ£o existe. Descrever como "projeto de estudo aplicado".
- No Workana, usar como amostra de trabalho na proposta, sem dizer que foi feito para cliente real.

