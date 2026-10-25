"""Funcoes compartilhadas pelos geradores de dados da LocaMaq.

Usado por todos os scripts em src/gerador_dados/. Mantem a logica de sorteio ponderado
e a gravacao de CSV iguais entre as 7 fontes (cadastro_equipamentos, clientes, etc.).
"""
import csv


def sortear_ponderado(rng, opcoes):
    """Sorteia um item de uma lista [(item, peso), ...]."""
    itens = [item for item, _ in opcoes]
    pesos = [peso for _, peso in opcoes]
    return rng.choices(itens, weights=pesos)[0]


def gravar_csv(caminho, colunas, linhas):
    """Grava um CSV no padrao dos geradores: separador ';', utf-8-sig (Excel e Power Query
    reconhecem os acentos), uma linha por dicionario em `linhas`.
    """
    with open(caminho, "w", encoding="utf-8-sig", newline="") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=colunas, delimiter=";", lineterminator="\n")
        escritor.writeheader()
        escritor.writerows(linhas)
