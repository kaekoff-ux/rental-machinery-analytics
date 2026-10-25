# Checklist de limpeza — Power Query

Rascunho **[P]**, não testado no Power BI. Um checklist por fonte, derivado de
`docs/dicionario_dados.csv` (fonte da verdade da sujeira) e dos geradores em
`src/gerador_dados/` (que sei exatamente o que sujaram). Carregue sempre de
`data/raw/*.csv` — `data/processed/` é só o gabarito pra você conferir o resultado.

Separador dos CSVs: `;`. Codificação: UTF-8 (com BOM — o Power Query detecta sozinho).

## Técnicas gerais (reaproveita nas 7 fontes)

| Problema | Onde aparece | Ação sugerida no Power Query |
|---|---|---|
| Texto categórico em caixa mista (`ATIVO`/`ativo`/`Ativo`) | status, modalidade, tipo_manutencao, fonte_leitura... | `Transformar > Formato > Cada Palavra em Maiúscula`, ou melhor: coluna condicional / `Table.ReplaceValue` por valor — valores possíveis estão no dicionário de dados |
| Abreviação (`Prev.`/`PREV` → `Preventiva`) | tipo_manutencao, segmento, fabricante | **Merge** com uma tabela pequena "de-para" (mais fácil de manter que vários `Replace Values` soltos) |
| ID com minúsculo/espaço/sem hífen | id_equipamento, id_cliente (quando sujo) | `Texto.Trim` + `Texto.Maiúscula`, depois confirme contra `dim_equipamento`/`dim_cliente` |
| Datas em formato misto (ISO vs `dd/mm/aaaa`) | toda coluna de data | `Transformar coluna > Data > Usando Localidade`, com `try` em `pt-BR` `otherwise` tentar ISO — ou duas colunas de tentativa + `Table.CombineColumns` |
| Decimal com vírgula | litros, valor_litro (abastecimento) | Ao definir tipo **Usando Localidade**, escolha `Portuguese (Brazil)` |
| Valor com `R$` e ponto de milhar | valor_aquisicao, custo_pecas, custo_mao_obra, valor_faturado | Remover `"R$ "` (Texto.Substituir), depois **Usando Localidade** `Portuguese (Brazil)` para o ponto/vírgula |
| Nulo legítimo (não é sujeira, é ausência real) | ano_fabricacao, horimetro_na_os, horas_parada | **Não** preencher com 0 nem com média — deixe `null`. Documentado em `CLAUDE.md` do projeto |

## cadastro_equipamentos

- `id_equipamento`: minúsculo/sem hífen → padronizar para `EQ-0000`
- `segmento`, `fabricante`: grafias variadas → merge de-para
- `modelo`: espaços extras → Trim
- `ano_fabricacao`: nulo legítimo — manter
- `data_aquisicao`: formato misto
- `valor_aquisicao`: `R$`/milhar
- `filial`: acento ausente/caixa mista
- `status_cadastro`: caixa mista
- **Linhas duplicadas** (4 propositais, mesmo `numero_serie`): decidir critério de dedupe — ver nota abaixo

## clientes

- `razao_social`: abreviação → é a pista visual, não a chave de dedupe
- `cnpj`: com/sem máscara → **normalize removendo pontuação antes de comparar**
- `segmento_cliente`, `cidade`: grafias variadas
- `uf`: minúsculo ou vazio
- `data_cadastro`: formato misto
- **Importante:** os 3 clientes duplicados têm `id_cliente` **diferente** e o **mesmo
  CNPJ** (de propósito — ver `gerar_clientes.py`). Remover Duplicados por `id_cliente` não
  resolve. Agrupe por CNPJ normalizado e decida qual registro é o "mestre" (ex.: o de
  `data_cadastro` mais antiga).

## contratos_locacao

- `id_equipamento`: minúsculo/espaço
- `modalidade`, `status`: caixa mista
- `data_inicio`, `data_fim_prevista`, `data_devolucao`: formato misto; `data_devolucao`
  vazia é legítimo (contrato Ativo ou Cancelado)
- `valor_diaria`/`valor_mensal`: um dos dois sempre vazio, dependendo da `modalidade` —
  não é erro
- **Linhas duplicadas** (6, mesmo `id_contrato`): aqui sim é seguro **Remover Duplicados**
  por `id_contrato`

## horimetro_telemetria

- `id_equipamento`: minúsculo
- `data_leitura`: formato misto
- `horimetro_horas`: **cuidado** — além do formato, uma fração das leituras tem valor
  *menor* que a leitura anterior da mesma máquina (erro de digitação simulado). Ordene por
  `id_equipamento` + `data_leitura` e sinalize onde o valor atual é menor que o anterior
  antes de decidir corrigir ou descartar a linha
- `fonte_leitura`: caixa mista
- `id_contrato`: vazio é legítimo (máquina no pátio)

## ordens_manutencao

- `id_equipamento`: minúsculo
- `tipo_manutencao`: abreviação/caixa mista (`Prev.`/`PREV`/`preventiva`)
- `data_abertura`, `data_conclusao`: formato misto; `data_conclusao` vazia é legítimo (OS
  Aberta/Em andamento)
- `horimetro_na_os`, `horas_parada`: nulo legítimo em parte dos casos
- `custo_pecas`, `custo_mao_obra`: `R$`/milhar
- `status_os`: caixa mista — **são as 3 colunas do seu board de oficina**

## abastecimento

- `id_equipamento`: minúsculo
- `data_abastecimento`: formato misto
- `litros`, `valor_litro`: vírgula decimal
- `valor_total`: numa fração dos casos **não bate** com `litros × valor_litro` (erro de
  digitação simulado) — vale criar uma coluna de verificação (`valor_total` calculado vs.
  informado) para decidir qual usar
- `horimetro_horas`: nulo legítimo em parte dos casos
- `responsavel`: nome abreviado (`M. Silva` vs `Marcos Silva`)

## faturamento

- `competencia`: formato misto (`2025-03` vs `03/2025`)
- `valor_faturado`: `R$`/milhar
- `data_emissao`, `data_vencimento`, `data_pagamento`: formato misto; `data_pagamento`
  vazia é legítimo (status Vencido/Em aberto)
- `status_pagamento`: caixa mista

## Depois de limpar as 7 fontes

Ver `docs/modelo_dados.md` para como relacioná-las (dimensões, fatos, chaves) e o ponto de
atenção sobre trazer `id_equipamento` para dentro de `fato_faturamento` via merge.
