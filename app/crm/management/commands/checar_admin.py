"""Sai com código 1 se ainda não existe administrador (usado por abrir_sistema.bat)."""
import sys

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Confere se já existe um superusuário."

    def handle(self, *args, **opts):
        if get_user_model().objects.filter(is_superuser=True, is_active=True).exists():
            self.stdout.write("Administrador encontrado.")
            return
        self.stdout.write("Ainda não há administrador.")
        sys.exit(1)
