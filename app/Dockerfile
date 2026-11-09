# Imagem do sistema de gestão LocaMaq (Django + gunicorn + WhiteNoise).
# Construir a partir da RAIZ do repositório, porque a base fictícia está em data/processed:
#   docker build -f app/Dockerfile -t locamaq-gestao .
# Variáveis obrigatórias ao rodar: LOCAMAQ_SECRET_KEY e LOCAMAQ_HOSTS. Ver app/README.md.
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    LOCAMAQ_PRODUCAO=1 \
    LOCAMAQ_DADOS=/srv/dados_base \
    LOCAMAQ_DB=/dados/db.sqlite3

WORKDIR /srv/app
COPY app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ /srv/app/
COPY data/processed/ /srv/dados_base/

# Arquivos estáticos com nome versionado (o navegador nunca usa CSS/JS velho).
RUN LOCAMAQ_SECRET_KEY=so-para-o-build LOCAMAQ_HOSTS=localhost python manage.py collectstatic --noinput

RUN useradd --create-home --uid 1000 locamaq && mkdir -p /dados && chown locamaq /dados
USER locamaq
VOLUME ["/dados"]
EXPOSE 8000
CMD ["sh", "/srv/app/entrypoint.sh"]
