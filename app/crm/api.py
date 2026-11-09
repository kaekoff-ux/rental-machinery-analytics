"""Entrada de leads vinda do n8n: POST /api/leads/.

Acesso: cabeçalho Authorization: Bearer <LOCAMAQ_API_TOKEN>, ou, com LOCAMAQ_API_REDE_INTERNA=1,
chamada direta da rede interna do Docker (o n8n no mesmo servidor). Sem nenhuma das duas, a API
responde 503 (desligada). Sem id_lead, o sistema gera o número e devolve no campo id_lead.
Corpo JSON com os campos que o fluxo grava na planilha:
id_lead, data_envio, nome, contato, cidade, equipamento, prazo, observacao, origem, status.

Reprocessar o mesmo pedido (mesmo id_lead, nome e contato) não duplica: a resposta é 200 com o
lead que já existe, sem sobrescrever o que a equipe mudou no sistema. Lead novo: 201. Se o
id_lead já pertence a outro pedido (número repetido entre o n8n e um lead criado à mão), o
pedido não é descartado: entra com o próximo número livre e a resposta traz "aviso".
"""
import hmac
import ipaddress
import json
import re
from datetime import datetime
from zoneinfo import ZoneInfo

from django.conf import settings
from django.contrib.auth.decorators import login_not_required
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .models import Atividade, Lead

BRASILIA = ZoneInfo("America/Sao_Paulo")
LIMITE_BYTES = 20_000
FORMATOS_DATA = ["%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S", "%d/%m/%Y %H:%M:%S", "%d/%m/%Y %H:%M", "%Y-%m-%dT%H:%M"]


def _data_envio(texto):
    texto = (texto or "").strip()
    if not texto:
        return timezone.now()
    try:
        d = datetime.fromisoformat(texto.replace("Z", "+00:00"))
    except ValueError:
        d = None
        for f in FORMATOS_DATA:
            try:
                d = datetime.strptime(texto, f)
                break
            except ValueError:
                continue
        if d is None:
            raise ValueError("data_envio em formato desconhecido")
    return d if timezone.is_aware(d) else d.replace(tzinfo=BRASILIA)


def _texto(dados, campo, limite):
    return str(dados.get(campo) or "").strip()[:limite]


def _autorizado(request):
    """True/False conforme a chave ou a rede interna; None se a API estiver desligada."""
    chave = settings.LOCAMAQ_API_TOKEN
    if chave:
        enviado = request.headers.get("Authorization", "")
        return hmac.compare_digest(enviado.encode(), f"Bearer {chave}".encode())
    if settings.LOCAMAQ_API_REDE_INTERNA:
        try:
            ip = ipaddress.ip_address(request.META.get("REMOTE_ADDR", ""))
        except ValueError:
            return False
        # Chamada direta (sem X-Forwarded-For) vinda de endereço privado: o n8n no mesmo servidor.
        return ip.is_private and "HTTP_X_FORWARDED_FOR" not in request.META
    return None


@csrf_exempt
@login_not_required
@require_POST
def receber_lead(request):
    autorizado = _autorizado(request)
    if autorizado is None:
        return JsonResponse({"ok": False, "erro": "API desligada."}, status=503)
    if not autorizado:
        return JsonResponse({"ok": False, "erro": "Não autorizado."}, status=401)
    if len(request.body) > LIMITE_BYTES:
        return JsonResponse({"ok": False, "erro": "Corpo grande demais."}, status=413)
    try:
        dados = json.loads(request.body.decode("utf-8"))
        if not isinstance(dados, dict):
            raise ValueError
    except (ValueError, UnicodeDecodeError):
        return JsonResponse({"ok": False, "erro": "JSON inválido."}, status=400)

    nome = _texto(dados, "nome", 120)
    if not nome:
        return JsonResponse({"ok": False, "erro": "O campo nome é obrigatório."}, status=400)
    codigo = _texto(dados, "id_lead", 16)
    if codigo and not re.fullmatch(r"LEAD_\d{4,}/\d{2}", codigo):
        return JsonResponse({"ok": False, "erro": "id_lead fora do padrão LEAD_NNNN/aa."}, status=400)
    aviso = ""
    if codigo:
        existente = Lead.objects.filter(codigo=codigo).first()
        if existente and existente.nome == nome and existente.contato == _texto(dados, "contato", 120):
            # Reprocessamento do mesmo pedido: não duplica nem sobrescreve.
            return JsonResponse({"ok": True, "criado": False, "id_lead": existente.codigo,
                                 "url": request.build_absolute_uri(existente.get_absolute_url())})
        if existente:
            # Mesmo número, outro pedido (ex.: lead criado à mão no sistema): não descarta,
            # grava com o próximo número livre e avisa.
            aviso = f"{codigo} já era de outro lead; gravado com número novo."
            codigo = ""
    try:
        envio = _data_envio(dados.get("data_envio"))
    except ValueError as e:
        return JsonResponse({"ok": False, "erro": str(e)}, status=400)

    origem = _texto(dados, "origem", 12).lower() or "site"
    status = _texto(dados, "status", 12) or "Novo"
    lead = Lead(
        codigo=codigo,
        data_envio=envio,
        nome=nome,
        contato=_texto(dados, "contato", 120),
        cidade=_texto(dados, "cidade", 60),
        equipamento_pedido=_texto(dados, "equipamento", 80),
        prazo=_texto(dados, "prazo", 40),
        observacao=_texto(dados, "observacao", 2000),
        origem=origem if origem in Lead.ORIGENS else "outro",
        status=status if status in Lead.ETAPAS else "Novo",
    )
    lead.save()
    Atividade.objects.create(tipo="Nota", assunto="Lead recebido pelo formulário do site (n8n)",
                             descricao=aviso, lead=lead)
    resposta = {"ok": True, "criado": True, "id_lead": lead.codigo,
                "url": request.build_absolute_uri(lead.get_absolute_url())}
    if aviso:
        resposta["aviso"] = aviso
    return JsonResponse(resposta, status=201)
