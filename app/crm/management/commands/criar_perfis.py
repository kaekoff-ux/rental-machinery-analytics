"""Cria os perfis de acesso (grupos) do sistema: Gestor, Vendedor, Atendimento e Oficina.

Uso: python manage.py criar_perfis   (pode rodar de novo; só ajusta as permissões)
Depois, no /admin/, coloque cada usuário no grupo certo. O superusuário vê e faz tudo.
"""
from django.contrib.auth.models import Group, Permission
from django.core.management.base import BaseCommand

OBJETOS = ["lead", "cliente", "equipamento", "contrato", "fatura", "ordemservico", "leiturahorimetro", "atividade"]


def perms(acoes, objetos):
    return [f"{a}_{o}" for o in objetos for a in acoes]


PERFIS = {
    # Gestor: tudo, menos apagar (apagar fica só no admin, com superusuário).
    "Gestor": perms(["view", "add", "change"], OBJETOS),
    # Vendedor: funil de leads, clientes e contratos; vê frota, faturas e oficina.
    "Vendedor": perms(["view", "add", "change"], ["lead", "cliente", "contrato", "atividade"])
    + perms(["view"], ["equipamento", "fatura", "ordemservico", "leiturahorimetro"]),
    # Atendimento: triagem dos leads e acompanhamento; vê o resto.
    "Atendimento": perms(["view", "add", "change"], ["lead", "atividade"])
    + perms(["view"], ["cliente", "equipamento", "contrato", "fatura", "ordemservico"]),
    # Oficina: ordens de serviço, horímetro e cadastro da frota; vê contratos.
    "Oficina": perms(["view", "add", "change"], ["ordemservico", "leiturahorimetro", "atividade"])
    + perms(["view", "change"], ["equipamento"])
    + perms(["view"], ["contrato"]),
}


class Command(BaseCommand):
    help = "Cria ou atualiza os grupos Gestor, Vendedor, Atendimento e Oficina."

    def handle(self, *args, **opts):
        for nome, codenames in PERFIS.items():
            grupo, _ = Group.objects.get_or_create(name=nome)
            permissoes = list(Permission.objects.filter(content_type__app_label="crm", codename__in=codenames))
            faltando = set(codenames) - {p.codename for p in permissoes}
            if faltando:
                self.stderr.write(f"Permissões não encontradas para {nome}: {sorted(faltando)} (rode migrate antes)")
            grupo.permissions.set(permissoes)
            self.stdout.write(f"{nome}: {len(permissoes)} permissões")
