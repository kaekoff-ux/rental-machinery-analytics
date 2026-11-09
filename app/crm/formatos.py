"""Formatação brasileira (R$ 1.234,56; 12,5%; 09/11/2026) usada nas telas e no CSV."""
from datetime import date, datetime
from decimal import Decimal

from django.utils import timezone

# Cor do selo de cada status (nomes de tokens do CSS).
SELOS = {
    "Novo": "petroleo", "Em Contato": "terra", "Orçado": "laranja", "Fechado": "verde", "Perdidos": "ruim",
    "Ativo": "verde", "Encerrado": "neutro", "Cancelado": "ruim", "Devolução atrasada": "ruim",
    "Pago": "verde", "Em aberto": "laranja", "Vencido": "ruim",
    "Aberta": "laranja", "Em andamento": "petroleo", "Concluída": "verde",
    "Disponível": "verde", "Locado": "petroleo", "Em manutenção": "laranja", "Fora da frota": "neutro",
    "Vendido": "neutro", "Baixado": "neutro",
    "Preventiva": "verde", "Preditiva": "petroleo", "Corretiva": "laranja",
}


def numero(v, casas=0):
    if v is None or v == "":
        return "—"
    v = float(v)
    txt = f"{abs(v):,.{casas}f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return ("−" if v < 0 else "") + txt


def brl(v, casas=2):
    if v is None or v == "":
        return "—"
    return "R$ " + numero(v, casas)


def brl_compacto(v):
    if v is None:
        return "—"
    v = float(v)
    if abs(v) >= 1_000_000:
        return "R$ " + numero(v / 1_000_000, 1) + " mi"
    if abs(v) >= 1_000:
        return "R$ " + numero(v / 1_000, 0) + " mil"
    return brl(v, 0)


def pct(v, casas=1):
    if v is None:
        return "—"
    return numero(float(v) * 100, casas) + "%"


def data(d):
    if not d:
        return "—"
    if isinstance(d, datetime):
        d = timezone.localtime(d) if timezone.is_aware(d) else d
        return d.strftime("%d/%m/%Y %H:%M")
    return d.strftime("%d/%m/%Y")


def texto(v):
    if v is None or v == "":
        return "—"
    if isinstance(v, bool):
        return "Sim" if v else "Não"
    if isinstance(v, (datetime, date)):
        return data(v)
    if isinstance(v, Decimal):
        return numero(v, 2 if v != v.to_integral_value() else 0)
    return str(v)
