# Extensão 2026: contratos, faturas e leads (dados fictícios)

Criada em 05/11/2026. A base original cobre 2024-2025 (janela de histórico do projeto). Esta extensão acrescenta **2026** sem alterar nenhum dos 6 CSVs originais, para os números do site, o Power BI e a regra da janela continuarem valendo.

## O que existe
Pasta `data/processed/extensao_2026/` (só versão limpa, sem `raw`):

| Arquivo | Conteúdo |
|---|---|
| `contratos_locacao_2026.csv` | 35 contratos, ids `CT-01211` a `CT-01245`. Mesmas colunas de `contratos_locacao.csv`. |
| `faturamento_2026.csv` | 76 faturas, ids a partir de `FT-002488`. Mesmas colunas de `faturamento.csv`. |
| `leads_2026.csv` | 66 leads (formato do dataset, datas aaaa-mm-dd, com `inicio_pretendido` para auditoria). |
| `leads_2026_planilha.csv` | Os mesmos 66 leads prontos para importar na aba `Leads` da planilha (sem cabeçalho, datas dd/mm/aaaa, colunas A a L). |

Gerar: `python src/gerador_dados/gerar_extensao_2026.py` (semente 42; rodar de novo dá arquivos idênticos).
Conferir: `python tests/conferir_extensao_2026.py` (independente do gerador; sai com erro se algo divergir).

## Regras
- **"Hoje" da extensão: 05/11/2026.** Contrato cujo fim previsto está a menos de 5 dias de "hoje" ou depois fica **Ativo**; os demais, **Encerrado**.
- **5 contratos fechados por categoria** (7 categorias = 35), com início entre 12/01 e 16/10/2026.
- **Disponibilidade da máquina.** Um contrato novo só entra se a máquina: está com `status_cadastro = Ativo` e já foi adquirida; não tem outro contrato por cima (folga de 3 dias, como no gerador original); não estava em OS Aberta ou Em andamento no fim de 2025 (assume-se oficina até 20/01/2026). Contratos "Ativo" no fim de 2025 tinham o fim previsto cortado em 31/12/2025 pelo gerador, então assume-se que seguem com a máquina até 31/01/2026.
- **Leads perdidos por indisponibilidade (14, 2 por categoria).** Em cada categoria, o modelo com **menos unidades ativas** tem **todas** as unidades alugadas ao mesmo tempo numa janela de 2026 (Grove RT540E, JLG E600JP, Komatsu PC210, New Holland B95B, Caterpillar XQ125, Case 821F e Clark C25L). Dois leads pedem esse modelo dentro da janela. A observação cita o período e os contratos que ocupavam as máquinas, e o teste confere de novo, por conta própria, que todas as unidades do modelo estavam alugadas na data do lead e nos 7 dias seguintes à data pretendida.
- **Leads perdidos por outros motivos (7, 1 por categoria)** e **leads em aberto (10: 4 Novo, 3 Em Contato, 3 Orçado).** Não vêm de contrato nenhum.
- **Faturas.** Mesma regra do gerador original (Mensal: 1 por mês; Semanal e Diária: 1 no fim do contrato), mas só existem as já emitidas até "hoje"; contrato Ativo ainda não devolvido não tem fatura final. O status de pagamento é decidido contra "hoje".

## O que é da base e o que é inventado nos leads
- **Da base (leads Fechado):** nome (razão social do cliente), cidade, equipamento, prazo (modalidade e dias), obra, valor e id do contrato.
- **Inventado:** contato (e-mail terminado em `.example`, que não existe, ou telefone começando com 0, que é inválido), origem (site 50%, whatsapp 20%, telegram 10%, telefone 10%, indicação 10%), as datas do lead e do desfecho, os leads perdidos e em aberto, e os motivos de perda.
- Toda observação começa com `[histórico fictício]`, para separar essas linhas das que chegam de verdade pelo formulário do site.
- As 3 colunas novas da aba (`data_desfecho`, `id_contrato`, `motivo_perda`) ligam o lead ao contrato e alimentam os indicadores.

## Indicadores de leads (definidos em `docs/kpis.csv`)
Taxa de conversão de leads, tempo médio de fechamento, leads por origem, perdas por motivo e perda por indisponibilidade (esta cruza com a utilização física do segmento). Na planilha, a aba `Indicadores` calcula tudo (fórmulas de matriz nas células A4, A15, A23 e A32); pedido do site sem `status` conta como `Novo`.

**Cuidado ao ler os números:** o histórico é uma amostra montada para demonstrar o indicador (35 fechados contra 21 perdidos dão 62,5% de conversão). Não é uma taxa real de uma operação.

## Não gerado em 2026
Telemetria de horímetro, ordens de manutenção e a inspeção automática em cada devolução. Por isso a disponibilidade em 2026 considera apenas os contratos e as OS que estavam abertas no fim de 2025. Se esses dados forem gerados depois, a disponibilidade precisa ser recalculada.

## Como usar no Power BI
Acrescente as tabelas com "Anexar consultas" (Power Query): `contratos_locacao` + `contratos_locacao_2026` e `faturamento` + `faturamento_2026`. Os 6 CSVs originais não mudaram. `dim_calendario` vai até 30/06/2026; para os meses seguintes de 2026 ela precisa ser regenerada (não feito).
