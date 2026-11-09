#!/usr/bin/env python
"""Ponto de entrada do Django para o sistema de gestão LocaMaq."""
import os
import sys


def main():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "locamaq.settings")
    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
