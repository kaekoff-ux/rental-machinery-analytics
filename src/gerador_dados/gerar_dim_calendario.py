"""Gera a dimensão calendário (dim_calendario) para o modelo estrela da LocaMaq.

Diferente dos outros geradores, esta tabela não tem sujeira - é uma dimensão de datas,
gerada de forma determinística (sem seed, não há sorteio aqui).

Saída:
    data/processed/dim_calendario.csv

Como rodar, a partir da raiz do repositorio:
    python src/gerador_dados/gerar_dim_calendario.py

Por que o intervalo é maior que a janela de histórico (2024-01-01 a 2025-12-31):
- KPIs como "receita vs mesmo mês do ano anterior" (SAMEPERIODLASTYEAR) para um dado de
  janeiro/2024 precisam encontrar janeiro/2023 na tabela calendário, senão o resultado
  fica em branco.
- Faturas podem ter data_vencimento/data_pagamento um pouco depois do fim do histórico
  (ver gerar_faturamento.py) - a tabela precisa cobrir essa cauda também.
Por isso o intervalo vai de 2023-01-01 a 2026-06-30.

No Power BI, marque esta tabela como "tabela de datas" (Marcar como tabela de datas,
usando a coluna `data`) antes de usar funções de inteligência de tempo (TOTALYTD,
SAMEPERIODLASTYEAR, DATEADD, PREVIOUSMONTH) - sem isso essas funções não funcionam.
"""
from datetime import date, timedelta
from pathlib import Path

from utils import gravar_csv

INICIO = date(2023, 1, 1)
FIM = date(2026, 6, 30)

RAIZ = Path(__file__).resolve().parents[2]
ARQ_PROCESSED = RAIZ / "data" / "processed" / "dim_calendario.csv"

COLUNAS = [
    "data", "ano", "trimestre", "ano_trimestre", "mes", "nome_mes", "mes_abrev",
    "ano_mes", "chave_ano_mes", "semana_ano", "dia_mes", "dia_semana_numero",
    "nome_dia_semana", "fim_de_semana",
]

NOMES_MES = [
    "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto",
    "Setembro", "Outubro", "Novembro", "Dezembro",
]
ABREV_MES = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"]
NOMES_DIA_SEMANA = [
    "Segunda-feira", "Terça-feira", "Quarta-feira", "Quinta-feira", "Sexta-feira",
    "Sábado", "Domingo",
]


def gerar_linha(dia):
    trimestre = (dia.month - 1) // 3 + 1
    dia_semana_numero = dia.isoweekday()  # 1 = segunda, 7 = domingo
    return {
        "data": dia.isoformat(),
        "ano": dia.year,
        "trimestre": trimestre,
        "ano_trimestre": f"{dia.year}-T{trimestre}",
        "mes": dia.month,
        "nome_mes": NOMES_MES[dia.month - 1],
        "mes_abrev": ABREV_MES[dia.month - 1],
        "ano_mes": f"{dia.year}-{dia.month:02d}",
        "chave_ano_mes": dia.year * 100 + dia.month,
        "semana_ano": dia.isocalendar()[1],
        "dia_mes": dia.day,
        "dia_semana_numero": dia_semana_numero,
        "nome_dia_semana": NOMES_DIA_SEMANA[dia_semana_numero - 1],
        "fim_de_semana": "Sim" if dia_semana_numero in (6, 7) else "Não",
    }


def gerar_calendario():
    linhas = []
    dia = INICIO
    while dia <= FIM:
        linhas.append(gerar_linha(dia))
        dia += timedelta(days=1)
    return linhas


def main():
    linhas = gerar_calendario()
    ARQ_PROCESSED.parent.mkdir(parents=True, exist_ok=True)
    gravar_csv(ARQ_PROCESSED, COLUNAS, linhas)
    print(f"processed: {len(linhas)} linhas ({INICIO.isoformat()} a {FIM.isoformat()}) -> {ARQ_PROCESSED.relative_to(RAIZ)}")
    print("\nAmostra:")
    for linha in linhas[:3]:
        print("  " + " | ".join(str(linha[coluna]) for coluna in COLUNAS))


if __name__ == "__main__":
    main()
