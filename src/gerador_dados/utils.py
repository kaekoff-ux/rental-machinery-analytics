"""Funcoes compartilhadas pelos geradores de dados da LocaMaq.

Usado por todos os scripts em src/gerador_dados/. Mantem a logica de sorteio ponderado,
intervalos de contrato e gravacao de CSV iguais entre as 7 fontes (cadastro_equipamentos,
clientes, etc.) - evita copiar a mesma funcao em cada gerador novo.
"""
import csv
from datetime import date


def sortear_ponderado(rng, opcoes):
    """Sorteia um item de uma lista [(item, peso), ...]."""
    itens = [item for item, _ in opcoes]
    pesos = [peso for _, peso in opcoes]
    return rng.choices(itens, weights=pesos)[0]


def formatar_real(valor):
    """845000.0 -> 'R$ 845.000,00' (padrao brasileiro de planilha)."""
    texto = f"{valor:,.2f}"  # '845,000.00'
    texto = texto.replace(",", "#").replace(".", ",").replace("#", ".")
    return f"R$ {texto}"


def construir_intervalos_contrato(contratos, incluir_cancelados=False):
    """A partir dos contratos (processed), retorna {id_equipamento: [(inicio, fim, id_contrato)]},
    cada lista ordenada por data. Por padrao ignora contratos Cancelado - a maquina nunca saiu
    do patio nesse caso, nao conta como periodo de uso.
    """
    intervalos = {}
    for contrato in contratos:
        if not incluir_cancelados and contrato["status"] == "Cancelado":
            continue
        inicio = date.fromisoformat(contrato["data_inicio"])
        fim = date.fromisoformat(contrato["data_devolucao"] or contrato["data_fim_prevista"])
        intervalos.setdefault(contrato["id_equipamento"], []).append((inicio, fim, contrato["id_contrato"]))
    for lista in intervalos.values():
        lista.sort()
    return intervalos


def contrato_vigente(intervalos_equipamento, dia):
    """Retorna o id_contrato vigente em `dia` para esse equipamento, ou None se estava no patio."""
    for inicio, fim, id_contrato in intervalos_equipamento:
        if inicio <= dia <= fim:
            return id_contrato
    return None


def gravar_csv(caminho, colunas, linhas):
    """Grava um CSV no padrao dos geradores: separador ';', utf-8-sig (Excel e Power Query
    reconhecem os acentos), uma linha por dicionario em `linhas`.
    """
    with open(caminho, "w", encoding="utf-8-sig", newline="") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=colunas, delimiter=";", lineterminator="\n")
        escritor.writeheader()
        escritor.writerows(linhas)
