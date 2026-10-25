# Modelo de dados — modelo estrela LocaMaq

Rascunho **[P]** para a Fase 2 (ETL e modelo). Baseado nos KPIs em `docs/kpis.csv` e nas 7
fontes + calendário geradas na Fase 1. Ainda não construído no Power BI — isto é o plano,
não o resultado.

## Dimensões (3)

| Dimensão | Fonte | Chave |
|---|---|---|
| `dim_equipamento` | `cadastro_equipamentos.csv` | `id_equipamento` |
| `dim_cliente` | `clientes.csv` | `id_cliente` |
| `dim_calendario` | gerada (`gerar_dim_calendario.py`) | `data` |

`dim_calendario` cobre 2023-01-01 a 2026-06-30 — mais larga que a janela de histórico
(2024-2025) de propósito: cobre o ano anterior (para SAMEPERIODLASTYEAR) e a cauda de
faturas com vencimento depois do fim do histórico. **Marcar como tabela de datas no Power
BI** (coluna `data`) antes de usar TOTALYTD, SAMEPERIODLASTYEAR, DATEADD, PREVIOUSMONTH.

## Fatos (5)

O roadmap cita 3 fatos (locação, manutenção, faturamento); na prática os KPIs também
precisam de horímetro e abastecimento como fatos próprios — ambos têm data + métricas
numéricas + `id_equipamento`, então modelá-los como dimensão não se aplica.

| Fato | Fonte | Grão | Data que liga ao calendário |
|---|---|---|---|
| `fato_locacao` | `contratos_locacao.csv` | 1 linha por contrato | `data_inicio` |
| `fato_manutencao` | `ordens_manutencao.csv` | 1 linha por OS | `data_abertura` |
| `fato_faturamento` | `faturamento.csv` | 1 linha por fatura | `data_emissao` |
| `fato_horimetro` | `horimetro_telemetria.csv` | 1 linha por leitura | `data_leitura` |
| `fato_abastecimento` | `abastecimento.csv` | 1 linha por abastecimento | `data_abastecimento` |

## Relacionamentos

```
dim_equipamento ──1───N── fato_locacao
dim_equipamento ──1───N── fato_manutencao
dim_equipamento ──1───N── fato_horimetro
dim_equipamento ──1───N── fato_abastecimento
dim_cliente     ──1───N── fato_locacao
dim_calendario  ──1───N── (todas as 5 tabelas de fato, pela coluna de data acima)
```

## Atenção — `fato_faturamento` não tem `id_equipamento`

`faturamento.csv` só referencia `id_contrato`. Sem `id_equipamento` direto, "receita por
máquina" dependeria de relacionamento indireto por `fato_locacao`, que o Power BI não
resolve bem entre duas tabelas de fato.

**Recomendação [P]:** no Power Query, fazer um *merge* de `faturamento` com
`contratos_locacao` para trazer `id_equipamento` (e `id_cliente`) direto para dentro de
`fato_faturamento` antes de carregar. Assim cada fato carrega suas próprias chaves, sem
depender de relacionamento fato-a-fato.

## Atenção — `fato_locacao` tem 3 datas, só 1 relacionamento ativo

`contratos_locacao` tem `data_inicio`, `data_fim_prevista` e `data_devolucao`. O Power BI
só permite um relacionamento *ativo* por par de tabelas. `data_inicio` fica ativo (grão
"quando o contrato começou"); para usar `data_devolucao` ou `data_fim_prevista` numa
medida, use `USERELATIONSHIP` dentro do `CALCULATE`, ou recrie `dim_calendario` como
tabela de papéis (*role-playing dimension*) se precisar das três ativas ao mesmo tempo.

## Ponto mais avançado do modelo: "dias locados" por mês

KPIs como *Taxa de utilização física* (`dias locados / dias do período`) pedem contar,
por equipamento e por mês, quantos dias caem **dentro** do intervalo `[data_inicio,
data_devolucao]` de algum contrato — isso não é um SUM direto de uma coluna, é uma medida
DAX com `FILTER`/`CALCULATE` cruzando `fato_locacao` com `dim_calendario` por intervalo de
datas, não por igualdade. Deixar para depois de dominar `CALCULATE` básico (fórmulas mais
simples dos KPIs primeiro, na ordem sugerida em `docs/kpis.csv` — coluna
`nivel_dax_para_estudo`).

## Próximo passo

Ver `powerbi/checklist_power_query.md` para o que limpar em cada fonte antes de carregar.
