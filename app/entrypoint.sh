#!/bin/sh
# Sobe o sistema no contêiner: aplica migrações, garante os perfis, importa a base fictícia
# só na primeira vez (banco vazio) e inicia o gunicorn.
set -e
python manage.py migrate --noinput
python manage.py criar_perfis
python manage.py importar_base --se-vazio
exec gunicorn locamaq.wsgi:application \
  --bind 0.0.0.0:8000 \
  --workers "${LOCAMAQ_WORKERS:-2}" \
  --timeout 60 \
  --access-logfile -
