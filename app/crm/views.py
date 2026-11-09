"""Telas do sistema de gestão LocaMaq.

Organização parecida com a do Salesforce: abas por objeto, listas com busca, filtros e
visões; página de registro com destaques, etapas (path), detalhes, listas relacionadas e
histórico de atividades; Kanban de leads e da oficina; busca global; painel.
"""
import csv
from collections import namedtuple
from datetime import timedelta

from django.contrib import messages
from django.contrib.auth.decorators import permission_required
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.core.cache import cache
from django.db import transaction
from django.db.models import Count, Exists, OuterRef, Q, Sum
from django.http import Http404, HttpResponse, HttpResponseBadRequest, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST
from django.views.generic import CreateView, DetailView, ListView, UpdateView

from . import formatos as fmt
from . import kpis
from .forms import (
    FormAtividade, FormCliente, FormContrato, FormConverterLead, FormEquipamento, FormFatura, FormLead,
    FormLeitura, FormOS,
)
from .models import (
    FILIAIS, SEGMENTOS, Atividade, Cliente, Contrato, Equipamento, Fatura, Lead, LeituraHorimetro, OrdemServico,
)

Coluna = namedtuple("Coluna", "rotulo valor ordem num", defaults=(None, False))


def link(texto, url):
    return {"texto": fmt.texto(texto), "url": url}


def selo(texto):
    return {"texto": texto or "—", "selo": fmt.SELOS.get(texto, "neutro")}


def texto_celula(c):
    return c["texto"] if isinstance(c, dict) else fmt.texto(c)


def nome_usuario(u):
    return (u.get_full_name() or u.username) if u else "—"


def anotar_situacao(qs):
    """Situação da máquina calculada no banco (para listar e filtrar sem uma consulta por linha)."""
    os_aberta = OrdemServico.objects.filter(equipamento=OuterRef("pk")).exclude(status="Concluída")
    ct_ativo = Contrato.objects.filter(equipamento=OuterRef("pk"), status="Ativo")
    return qs.annotate(em_manut=Exists(os_aberta), locado=Exists(ct_ativo))


def situacao_anotada(e):
    if e.status_cadastro != "Ativo":
        return "Fora da frota"
    if e.em_manut:
        return "Em manutenção"
    if e.locado:
        return "Locado"
    return "Disponível"


# ---------------------------------------------------------------- colunas por objeto
COLUNAS = {
    "lead": [
        Coluna("Número", lambda o: link(o.codigo, o.get_absolute_url()), "codigo"),
        Coluna("Nome / empresa", lambda o: o.nome, "nome"),
        Coluna("Segmento", lambda o: o.segmento or "—", "segmento"),
        Coluna("Modelo", lambda o: o.modelo or "—", "modelo"),
        Coluna("Cidade", lambda o: o.cidade, "cidade"),
        Coluna("Origem", lambda o: o.origem, "origem"),
        Coluna("Etapa", lambda o: selo(o.status), "status"),
        Coluna("Enviado em", lambda o: fmt.data(o.data_envio), "data_envio"),
        Coluna("Responsável", lambda o: nome_usuario(o.responsavel), "responsavel__first_name"),
    ],
    "cliente": [
        Coluna("Código", lambda o: link(o.codigo, o.get_absolute_url()), "codigo"),
        Coluna("Razão social", lambda o: link(o.razao_social, o.get_absolute_url()), "razao_social"),
        Coluna("Segmento", lambda o: o.segmento, "segmento"),
        Coluna("Cidade", lambda o: f"{o.cidade}/{o.uf}" if o.uf else o.cidade, "cidade"),
        Coluna("Contratos ativos", lambda o: getattr(o, "n_ativos", None), "n_ativos", True),
        Coluna("Limite de crédito", lambda o: fmt.brl(o.limite_credito, 0), "limite_credito", True),
    ],
    "equipamento": [
        Coluna("Código", lambda o: link(o.codigo, o.get_absolute_url()), "codigo"),
        Coluna("Segmento", lambda o: o.segmento, "segmento"),
        Coluna("Modelo", lambda o: o.nome_modelo, "modelo"),
        Coluna("Filial", lambda o: o.filial, "filial"),
        Coluna("Situação", lambda o: selo(situacao_anotada(o)) if hasattr(o, "em_manut") else selo(o.situacao())),
        Coluna("Ano", lambda o: o.ano_fabricacao, "ano_fabricacao", True),
        Coluna("Aquisição", lambda o: fmt.data(o.data_aquisicao), "data_aquisicao", True),
    ],
    "contrato": [
        Coluna("Contrato", lambda o: link(o.codigo, o.get_absolute_url()), "codigo"),
        Coluna("Cliente", lambda o: link(o.cliente, o.cliente.get_absolute_url()), "cliente__razao_social"),
        Coluna("Equipamento", lambda o: link(o.equipamento, o.equipamento.get_absolute_url()), "equipamento__codigo"),
        Coluna("Modalidade", lambda o: o.modalidade, "modalidade"),
        Coluna("Início", lambda o: fmt.data(o.data_inicio), "data_inicio", True),
        Coluna("Fim previsto", lambda o: fmt.data(o.data_fim_prevista), "data_fim_prevista", True),
        Coluna("Status", lambda o: selo("Devolução atrasada") if o.devolucao_atrasada else selo(o.status), "status"),
    ],
    "fatura": [
        Coluna("Fatura", lambda o: link(o.codigo, o.get_absolute_url()), "codigo"),
        Coluna("Contrato", lambda o: link(o.contrato.codigo, o.contrato.get_absolute_url()), "contrato__codigo"),
        Coluna("Cliente", lambda o: o.contrato.cliente.razao_social, "contrato__cliente__razao_social"),
        Coluna("Competência", lambda o: o.competencia, "competencia"),
        Coluna("Valor", lambda o: fmt.brl(o.valor_faturado), "valor_faturado", True),
        Coluna("Vencimento", lambda o: fmt.data(o.data_vencimento), "data_vencimento", True),
        Coluna("Status", lambda o: selo(o.status_pagamento), "status_pagamento"),
    ],
    "os": [
        Coluna("OS", lambda o: link(o.codigo, o.get_absolute_url()), "codigo"),
        Coluna("Equipamento", lambda o: link(o.equipamento, o.equipamento.get_absolute_url()), "equipamento__codigo"),
        Coluna("Tipo", lambda o: selo(o.tipo), "tipo"),
        Coluna("Descrição", lambda o: o.descricao, "descricao"),
        Coluna("Abertura", lambda o: fmt.data(o.data_abertura), "data_abertura", True),
        Coluna("Status", lambda o: selo(o.status), "status"),
        Coluna("Custo", lambda o: fmt.brl(o.custo_total, 0), None, True),
    ],
    "leitura": [
        Coluna("Data", lambda o: fmt.data(o.data_leitura), "data_leitura"),
        Coluna("Horímetro", lambda o: fmt.numero(o.horimetro_horas, 1) + " h", "horimetro_horas", True),
        Coluna("Fonte", lambda o: o.fonte, "fonte"),
        Coluna("Contrato", lambda o: link(o.contrato.codigo, o.contrato.get_absolute_url()) if o.contrato else "—"),
    ],
}


def montar_path(etapas, atual):
    """Estado de cada etapa: feita (antes da atual), atual, perdida ou futura ('')."""
    if atual == "Perdidos":
        return [{"nome": e, "estado": "perdida" if e == atual else ""} for e in etapas]
    sequencia = [e for e in etapas if e != "Perdidos"]
    pos = sequencia.index(atual) if atual in sequencia else -1
    itens = []
    for e in etapas:
        if e == atual:
            estado = "atual"
        elif e in sequencia and sequencia.index(e) < pos:
            estado = "feita"
        else:
            estado = ""
        itens.append({"nome": e, "estado": estado})
    return itens


def montar_linhas(objetos, colunas):
    return [{"celulas": [{"v": c.valor(o), "num": c.num} for c in colunas]} for o in objetos]


# ---------------------------------------------------------------- listas
class Lista(PermissionRequiredMixin, ListView):
    """Lista com busca (q), filtros (?campo=valor), visões, ordenação (?o=) e exportação CSV."""

    template_name = "crm/lista.html"
    paginate_by = 25
    objeto = ""
    titulo = ""
    busca = []
    filtros = []  # (parâmetro, rótulo, opções, campo do ORM)
    fks = []  # filtros ocultos vindos de links (?cliente=3)
    visoes = []  # (chave, rótulo, função(request) -> Q)
    ordem_padrao = "-pk"
    url_novo = None
    perm_novo = None
    botoes = []  # [(rótulo, nome da url)]

    def get_queryset(self):
        qs = self.base()
        r = self.request.GET
        q = r.get("q", "").strip()
        if q:
            cond = Q()
            for campo in self.busca:
                cond |= Q(**{f"{campo}__icontains": q})
            qs = qs.filter(cond)
        for param, _, _, campo in self.filtros:
            v = r.get(param)
            if v:
                qs = self.filtrar(qs, param, campo, v)
        for param in self.fks:
            v = r.get(param)
            if v and v.isdigit():
                qs = qs.filter(**{f"{param}_id": int(v)})
        visao = r.get("visao")
        for chave, _, func in self.visoes:
            if chave == visao:
                qs = qs.filter(func(self.request))
        ordem = r.get("o", "")
        validas = {c.ordem for c in COLUNAS[self.objeto] if c.ordem}
        if ordem.lstrip("-") in validas:
            qs = qs.order_by(ordem, "pk")
        else:
            qs = qs.order_by(self.ordem_padrao, "pk")
        return qs

    def base(self):
        return self.model.objects.all()

    def filtrar(self, qs, param, campo, valor):
        return qs.filter(**{campo: valor})

    def get(self, request, *args, **kwargs):
        if request.GET.get("formato") == "csv":
            return self.exportar_csv()
        return super().get(request, *args, **kwargs)

    def exportar_csv(self):
        colunas = COLUNAS[self.objeto]
        resp = HttpResponse(content_type="text/csv; charset=utf-8")
        resp["Content-Disposition"] = f'attachment; filename="locamaq_{self.objeto}s.csv"'
        resp.write("﻿")  # BOM: o Excel abre os acentos certos
        w = csv.writer(resp, delimiter=";")
        w.writerow([c.rotulo for c in colunas])
        for o in self.get_queryset()[:5000]:
            w.writerow([texto_celula(c.valor(o)) for c in colunas])
        return resp

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        r = self.request.GET
        colunas = COLUNAS[self.objeto]
        ordem = r.get("o", "")
        cab = []
        for c in colunas:
            if c.ordem:
                nova = c.ordem if ordem != c.ordem else "-" + c.ordem
                params = r.copy()
                params["o"] = nova
                params.pop("page", None)
                estado = "asc" if ordem == c.ordem else "desc" if ordem == "-" + c.ordem else ""
                cab.append({"rotulo": c.rotulo, "url": "?" + params.urlencode(), "estado": estado, "num": c.num})
            else:
                cab.append({"rotulo": c.rotulo, "url": None, "estado": "", "num": c.num})
        filtros = []
        for param, rotulo, opcoes, _ in self.filtros:
            opcoes = opcoes() if callable(opcoes) else opcoes
            filtros.append({"param": param, "rotulo": rotulo, "opcoes": opcoes, "valor": r.get(param, "")})
        sem_pagina = r.copy()
        sem_pagina.pop("page", None)
        csv_params = sem_pagina.copy()
        csv_params["formato"] = "csv"
        visoes = []
        for chave, rotulo, _ in [("", "Todos", None)] + list(self.visoes):
            p = sem_pagina.copy()
            p.pop("visao", None)
            if chave:
                p["visao"] = chave
            visoes.append({"rotulo": rotulo, "url": "?" + p.urlencode(), "ativa": r.get("visao", "") == chave})
        ctx.update({
            "titulo": self.titulo,
            "objeto": self.objeto,
            "cabecalho": cab,
            "linhas": montar_linhas(ctx["object_list"], colunas),
            "filtros": filtros,
            "visoes": visoes if self.visoes else [],
            "q": r.get("q", ""),
            "ocultos": [(p, r.get(p)) for p in self.fks + ["visao", "o"] if r.get(p)],
            "querystring": sem_pagina.urlencode(),
            "url_csv": "?" + csv_params.urlencode(),
            "url_novo": reverse(self.url_novo) if self.url_novo and self.request.user.has_perm(self.perm_novo) else None,
            "botoes": [{"rotulo": b[0], "url": reverse(b[1])} for b in self.botoes],
            "total": ctx["paginator"].count if ctx.get("paginator") else len(ctx["object_list"]),
        })
        return ctx


def _opcoes(lista):
    return [(x, x) for x in lista]


class LeadLista(Lista):
    model = Lead
    permission_required = "crm.view_lead"
    objeto, titulo = "lead", "Leads"
    busca = ["codigo", "nome", "contato", "cidade", "modelo", "equipamento_pedido"]
    filtros = [
        ("status", "Etapa", _opcoes(Lead.ETAPAS), "status"),
        ("origem", "Origem", _opcoes(Lead.ORIGENS), "origem"),
        ("segmento", "Segmento", _opcoes(SEGMENTOS), "segmento"),
    ]
    fks = ["cliente", "contrato"]
    visoes = [
        ("abertos", "Em aberto", lambda r: Q(status__in=Lead.ETAPAS_ABERTAS)),
        ("meus", "Meus leads", lambda r: Q(responsavel=r.user)),
        ("sem_dono", "Sem responsável", lambda r: Q(responsavel__isnull=True, status__in=Lead.ETAPAS_ABERTAS)),
    ]
    ordem_padrao = "-data_envio"
    url_novo, perm_novo = "crm:lead_novo", "crm.add_lead"
    botoes = [("Kanban", "crm:leads_kanban")]

    def base(self):
        return Lead.objects.select_related("responsavel")


class ClienteLista(Lista):
    model = Cliente
    permission_required = "crm.view_cliente"
    objeto, titulo = "cliente", "Clientes"
    busca = ["codigo", "razao_social", "cnpj", "cidade"]
    filtros = [
        ("segmento", "Segmento", _opcoes(Cliente.SEGMENTOS_CLIENTE), "segmento"),
        ("uf", "UF", lambda: _opcoes(Cliente.objects.order_by("uf").values_list("uf", flat=True).distinct()), "uf"),
    ]
    ordem_padrao = "razao_social"
    url_novo, perm_novo = "crm:cliente_novo", "crm.add_cliente"

    def base(self):
        return Cliente.objects.annotate(n_ativos=Count("contratos", filter=Q(contratos__status="Ativo")))


class EquipamentoLista(Lista):
    model = Equipamento
    permission_required = "crm.view_equipamento"
    objeto, titulo = "equipamento", "Frota"
    busca = ["codigo", "modelo", "fabricante", "numero_serie"]
    filtros = [
        ("segmento", "Segmento", _opcoes(SEGMENTOS), "segmento"),
        ("filial", "Filial", _opcoes(FILIAIS), "filial"),
        ("situacao", "Situação", _opcoes(["Disponível", "Locado", "Em manutenção", "Fora da frota"]), None),
        ("status_cadastro", "Cadastro", _opcoes(Equipamento.STATUS), "status_cadastro"),
    ]
    ordem_padrao = "codigo"
    url_novo, perm_novo = "crm:equipamento_novo", "crm.add_equipamento"

    def base(self):
        return anotar_situacao(Equipamento.objects.all())

    def filtrar(self, qs, param, campo, valor):
        if param != "situacao":
            return super().filtrar(qs, param, campo, valor)
        if valor == "Fora da frota":
            return qs.exclude(status_cadastro="Ativo")
        qs = qs.filter(status_cadastro="Ativo")
        if valor == "Em manutenção":
            return qs.filter(em_manut=True)
        if valor == "Locado":
            return qs.filter(em_manut=False, locado=True)
        return qs.filter(em_manut=False, locado=False)


class ContratoLista(Lista):
    model = Contrato
    permission_required = "crm.view_contrato"
    objeto, titulo = "contrato", "Contratos"
    busca = ["codigo", "cliente__razao_social", "equipamento__codigo", "equipamento__modelo", "obra_local"]
    filtros = [
        ("status", "Status", _opcoes(Contrato.STATUS), "status"),
        ("modalidade", "Modalidade", _opcoes(Contrato.MODALIDADES), "modalidade"),
    ]
    fks = ["cliente", "equipamento"]
    visoes = [
        ("vencer", "Terminam em 30 dias", lambda r: Q(
            status="Ativo", data_fim_prevista__gte=timezone.localdate(),
            data_fim_prevista__lte=timezone.localdate() + timedelta(days=30))),
        ("atrasados", "Devolução atrasada", lambda r: Q(status="Ativo", data_fim_prevista__lt=timezone.localdate())),
    ]
    ordem_padrao = "-data_inicio"
    url_novo, perm_novo = "crm:contrato_novo", "crm.add_contrato"

    def base(self):
        return Contrato.objects.select_related("cliente", "equipamento")


class FaturaLista(Lista):
    model = Fatura
    permission_required = "crm.view_fatura"
    objeto, titulo = "fatura", "Faturas"
    busca = ["codigo", "contrato__codigo", "contrato__cliente__razao_social", "competencia"]
    filtros = [
        ("status", "Status", _opcoes(Fatura.STATUS), "status_pagamento"),
        ("ano", "Ano", _opcoes(["2024", "2025", "2026"]), "competencia__startswith"),
    ]
    fks = ["contrato"]
    ordem_padrao = "-data_emissao"
    url_novo, perm_novo = "crm:fatura_nova", "crm.add_fatura"

    def base(self):
        return Fatura.objects.select_related("contrato__cliente")

    def get_queryset(self):
        qs = super().get_queryset()
        cliente = self.request.GET.get("cliente")
        if cliente and cliente.isdigit():
            qs = qs.filter(contrato__cliente_id=int(cliente))
        return qs


class OSLista(Lista):
    model = OrdemServico
    permission_required = "crm.view_ordemservico"
    objeto, titulo = "os", "Ordens de serviço"
    busca = ["codigo", "equipamento__codigo", "equipamento__modelo", "descricao"]
    filtros = [
        ("status", "Status", _opcoes(OrdemServico.STATUS), "status"),
        ("tipo", "Tipo", _opcoes(OrdemServico.TIPOS), "tipo"),
        ("segmento", "Segmento", _opcoes(SEGMENTOS), "equipamento__segmento"),
    ]
    fks = ["equipamento"]
    visoes = [("abertas", "Não concluídas", lambda r: ~Q(status="Concluída"))]
    ordem_padrao = "-data_abertura"
    url_novo, perm_novo = "crm:os_nova", "crm.add_ordemservico"
    botoes = [("Quadro da oficina", "crm:oficina")]

    def base(self):
        return OrdemServico.objects.select_related("equipamento")


# ---------------------------------------------------------------- página de registro
class Detalhe(PermissionRequiredMixin, DetailView):
    template_name = "crm/detalhe.html"
    objeto = ""
    rotulo = ""
    campos_ocultos = {"id", "criado_em", "atualizado_em"}

    def campos(self, obj):
        saida = []
        for f in obj._meta.fields:
            if f.name in self.campos_ocultos:
                continue
            valor = getattr(obj, f.name)
            if f.choices:
                valor = getattr(obj, f"get_{f.name}_display")()
            if f.is_relation and valor is not None:
                url = valor.get_absolute_url() if hasattr(valor, "get_absolute_url") else None
                valor = link(nome_usuario(valor) if f.name == "responsavel" else valor, url) if url else nome_usuario(valor)
            elif f.get_internal_type() == "DecimalField" and valor is not None and (
                "valor" in f.name or "custo" in f.name or "limite" in f.name
            ):
                valor = fmt.brl(valor)
            saida.append({"rotulo": f.verbose_name[:1].upper() + f.verbose_name[1:], "valor": valor if isinstance(valor, dict) else fmt.texto(valor)})
        saida.append({"rotulo": "Criado em", "valor": fmt.data(getattr(obj, "criado_em", None))})
        saida.append({"rotulo": "Atualizado em", "valor": fmt.data(getattr(obj, "atualizado_em", None))})
        return saida

    def relacionado(self, titulo, objeto, qs, url_lista=None, url_novo=None, limite=8):
        total = qs.count()
        return {
            "titulo": titulo,
            "total": total,
            "cabecalho": [{"rotulo": c.rotulo, "num": c.num} for c in COLUNAS[objeto]],
            "linhas": montar_linhas(qs[:limite], COLUNAS[objeto]),
            "url_lista": url_lista if total > limite else None,
            "url_novo": url_novo,
        }

    def extras(self, obj):
        return {}

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        obj = self.object
        ctx.update({
            "objeto": self.objeto,
            "rotulo_objeto": self.rotulo,
            "campos": self.campos(obj),
            "com_atividades": self.objeto in ALVOS,
            "atividades": obj.atividades.select_related("usuario")[:30] if self.objeto in ALVOS else [],
            "form_atividade": FormAtividade(),
            "alvo": f"{self.objeto}:{obj.pk}",
            "url_editar": reverse(f"crm:{self.objeto}_editar", args=[obj.pk])
            if self.request.user.has_perm(f"crm.change_{obj._meta.model_name}") else None,
        })
        ctx.update(self.extras(obj))
        return ctx


class LeadDetalhe(Detalhe):
    model = Lead
    permission_required = "crm.view_lead"
    objeto, rotulo = "lead", "Lead"

    def extras(self, o):
        relac = []
        if o.cliente:
            relac.append(self.relacionado("Contratos do cliente", "contrato",
                                          Contrato.objects.filter(cliente=o.cliente).select_related("cliente", "equipamento"),
                                          reverse("crm:contratos") + f"?cliente={o.cliente_id}"))
        return {
            "titulo": o.nome,
            "subtitulo": o.codigo,
            "destaques": [
                ("Etapa", selo(o.status)), ("Origem", o.origem), ("Segmento", o.segmento or "—"),
                ("Modelo", o.modelo or "Qualquer modelo"), ("Cidade", o.cidade or "—"),
                ("Responsável", nome_usuario(o.responsavel)), ("Enviado em", fmt.data(o.data_envio)),
            ],
            "path": {
                "itens": montar_path(Lead.ETAPAS, o.status), "url": reverse("crm:lead_etapa", args=[o.pk]),
                "motivos": Lead.MOTIVOS_PERDA, "pode": self.request.user.has_perm("crm.change_lead"),
            },
            "acoes": [a for a in [
                {"rotulo": "Converter em contrato", "url": reverse("crm:lead_converter", args=[o.pk]), "destaque": True}
                if not o.contrato and o.status != "Perdidos" and self.request.user.has_perm("crm.add_contrato") else None,
                {"rotulo": "Ver no Kanban", "url": reverse("crm:leads_kanban")},
            ] if a],
            "relacionados": relac,
        }


class ClienteDetalhe(Detalhe):
    model = Cliente
    permission_required = "crm.view_cliente"
    objeto, rotulo = "cliente", "Cliente"

    def extras(self, o):
        faturas = Fatura.objects.filter(contrato__cliente=o)
        tot = faturas.aggregate(fat=Sum("valor_faturado"), venc=Sum("valor_faturado", filter=Q(status_pagamento="Vencido")))
        contratos = Contrato.objects.filter(cliente=o).select_related("cliente", "equipamento")
        return {
            "titulo": o.razao_social,
            "subtitulo": o.codigo,
            "destaques": [
                ("Segmento", o.segmento or "—"), ("Cidade", f"{o.cidade}/{o.uf}"), ("CNPJ", o.cnpj or "—"),
                ("Contratos ativos", contratos.filter(status="Ativo").count()),
                ("Faturado", fmt.brl_compacto(tot["fat"])), ("Vencido", fmt.brl_compacto(tot["venc"] or 0)),
                ("Limite de crédito", fmt.brl_compacto(o.limite_credito)),
            ],
            "acoes": [{"rotulo": "Novo contrato", "url": reverse("crm:contrato_novo") + f"?cliente={o.pk}", "destaque": True}]
            if self.request.user.has_perm("crm.add_contrato") else [],
            "relacionados": [
                self.relacionado("Contratos", "contrato", contratos, reverse("crm:contratos") + f"?cliente={o.pk}"),
                self.relacionado("Faturas", "fatura", faturas.select_related("contrato__cliente"),
                                 reverse("crm:faturas") + f"?cliente={o.pk}"),
                self.relacionado("Leads", "lead", o.leads.select_related("responsavel"), reverse("crm:leads") + f"?cliente={o.pk}"),
            ],
        }


class EquipamentoDetalhe(Detalhe):
    model = Equipamento
    permission_required = "crm.view_equipamento"
    objeto, rotulo = "equipamento", "Equipamento"

    def extras(self, o):
        h = o.horimetro_atual()
        receita = Fatura.objects.filter(contrato__equipamento=o).aggregate(s=Sum("valor_faturado"))["s"]
        user = self.request.user
        acoes = []
        if user.has_perm("crm.add_ordemservico"):
            acoes.append({"rotulo": "Abrir OS", "url": reverse("crm:os_nova") + f"?equipamento={o.pk}", "destaque": True})
        if user.has_perm("crm.add_leiturahorimetro"):
            acoes.append({"rotulo": "Registrar horímetro", "url": reverse("crm:leitura_nova") + f"?equipamento={o.pk}"})
        if user.has_perm("crm.add_contrato") and o.status_cadastro == "Ativo":
            acoes.append({"rotulo": "Novo contrato", "url": reverse("crm:contrato_novo") + f"?equipamento={o.pk}"})
        return {
            "titulo": o.nome_modelo,
            "subtitulo": f"{o.codigo} · {o.segmento}",
            "destaques": [
                ("Situação", selo(o.situacao())), ("Filial", o.filial),
                ("Horímetro", fmt.numero(h, 1) + " h" if h is not None else "—"),
                ("Vida útil", fmt.numero(o.vida_util_horas) + " h"),
                ("Aquisição", fmt.data(o.data_aquisicao)), ("Valor", fmt.brl_compacto(o.valor_aquisicao)),
                ("Receita total", fmt.brl_compacto(receita or 0)),
            ],
            "acoes": acoes,
            "relacionados": [
                self.relacionado("Ordens de serviço", "os", o.ordens.select_related("equipamento"),
                                 reverse("crm:ordens") + f"?equipamento={o.pk}"),
                self.relacionado("Contratos", "contrato", o.contratos.select_related("cliente", "equipamento"),
                                 reverse("crm:contratos") + f"?equipamento={o.pk}"),
                self.relacionado("Leituras do horímetro", "leitura", o.leituras.select_related("contrato"), limite=6),
            ],
        }


class ContratoDetalhe(Detalhe):
    model = Contrato
    permission_required = "crm.view_contrato"
    objeto, rotulo = "contrato", "Contrato"

    def extras(self, o):
        fat = o.faturas.aggregate(s=Sum("valor_faturado"))["s"]
        acoes = []
        if self.request.user.has_perm("crm.add_fatura"):
            acoes.append({"rotulo": "Nova fatura", "url": reverse("crm:fatura_nova") + f"?contrato={o.pk}", "destaque": True})
        return {
            "titulo": f"{o.codigo} · {o.cliente.razao_social}",
            "subtitulo": o.obra_local or o.equipamento.nome_modelo,
            "destaques": [
                ("Status", selo("Devolução atrasada") if o.devolucao_atrasada else selo(o.status)),
                ("Cliente", link(o.cliente, o.cliente.get_absolute_url())),
                ("Equipamento", link(o.equipamento, o.equipamento.get_absolute_url())),
                ("Modalidade", o.modalidade),
                ("Valor", fmt.brl(o.valor_referencia) + ("/mês" if o.modalidade == "Mensal" else "/dia")),
                ("Período", f"{fmt.data(o.data_inicio)} a {fmt.data(o.data_devolucao or o.data_fim_prevista)}"),
                ("Faturado", fmt.brl_compacto(fat or 0)),
            ],
            "acoes": acoes,
            "relacionados": [
                self.relacionado("Faturas", "fatura", o.faturas.select_related("contrato__cliente"),
                                 reverse("crm:faturas") + f"?contrato={o.pk}"),
                self.relacionado("Leads de origem", "lead", o.leads.select_related("responsavel")),
            ],
        }


class FaturaDetalhe(Detalhe):
    model = Fatura
    permission_required = "crm.view_fatura"
    objeto, rotulo = "fatura", "Fatura"

    def extras(self, o):
        acoes = []
        if o.status_pagamento != "Pago" and self.request.user.has_perm("crm.change_fatura"):
            acoes.append({"rotulo": "Registrar pagamento hoje", "post": reverse("crm:fatura_pagar", args=[o.pk]), "destaque": True})
        return {
            "titulo": f"{o.codigo} · {fmt.brl(o.valor_faturado)}",
            "subtitulo": f"Competência {o.competencia} · {o.contrato.cliente.razao_social}",
            "destaques": [
                ("Status", selo(o.status_pagamento)), ("Contrato", link(o.contrato.codigo, o.contrato.get_absolute_url())),
                ("Emissão", fmt.data(o.data_emissao)), ("Vencimento", fmt.data(o.data_vencimento)),
                ("Pagamento", fmt.data(o.data_pagamento)), ("Dias de atraso", o.dias_atraso or "—"),
            ],
            "acoes": acoes,
        }


class OSDetalhe(Detalhe):
    model = OrdemServico
    permission_required = "crm.view_ordemservico"
    objeto, rotulo = "os", "Ordem de serviço"

    def extras(self, o):
        return {
            "titulo": f"{o.codigo} · {o.descricao}",
            "subtitulo": str(o.equipamento),
            "destaques": [
                ("Status", selo(o.status)), ("Tipo", selo(o.tipo)),
                ("Equipamento", link(o.equipamento, o.equipamento.get_absolute_url())),
                ("Abertura", fmt.data(o.data_abertura)), ("Conclusão", fmt.data(o.data_conclusao)),
                ("Horas parada", fmt.numero(o.horas_parada, 1) if o.horas_parada is not None else "—"),
                ("Custo total", fmt.brl(o.custo_total)), ("Responsável", nome_usuario(o.responsavel)),
            ],
            "path": {
                "itens": montar_path(OrdemServico.STATUS, o.status), "url": reverse("crm:os_status", args=[o.pk]),
                "pode": self.request.user.has_perm("crm.change_ordemservico"),
            },
            "acoes": [{"rotulo": "Quadro da oficina", "url": reverse("crm:oficina")}],
        }


# ---------------------------------------------------------------- criar e editar
class FormularioMixin(PermissionRequiredMixin, SuccessMessageMixin):
    template_name = "crm/form.html"
    rotulo = ""
    voltar = ""
    prefill = []  # campos que aceitam valor inicial pela URL (?cliente=3)

    def get_initial(self):
        inicial = super().get_initial()
        for campo in self.prefill:
            v = self.request.GET.get(campo)
            if v:
                inicial[campo] = v
        return inicial

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["rotulo_objeto"] = self.rotulo
        ctx["url_voltar"] = self.object.get_absolute_url() if getattr(self, "object", None) else reverse(self.voltar)
        return ctx


def _criar(model, form, perm, rotulo, voltar, prefill=(), msg=None):
    return type(f"Criar{model.__name__}", (FormularioMixin, CreateView), {
        "model": model, "form_class": form, "permission_required": perm, "rotulo": rotulo, "voltar": voltar,
        "prefill": list(prefill), "success_message": msg or f"{rotulo} criado.",
    })


def _editar(model, form, perm, rotulo, voltar):
    return type(f"Editar{model.__name__}", (FormularioMixin, UpdateView), {
        "model": model, "form_class": form, "permission_required": perm, "rotulo": rotulo, "voltar": voltar,
        "success_message": "Alterações salvas.",
    })


class LeadCriar(_criar(Lead, FormLead, "crm.add_lead", "Lead", "crm:leads")):
    def form_valid(self, form):
        if not form.instance.responsavel:
            form.instance.responsavel = self.request.user
        resp = super().form_valid(form)
        Atividade.objects.create(tipo="Nota", assunto=f"Lead cadastrado por {nome_usuario(self.request.user)}",
                                 usuario=self.request.user, lead=self.object)
        return resp


LeadEditar = _editar(Lead, FormLead, "crm.change_lead", "Lead", "crm:leads")
ClienteCriar = _criar(Cliente, FormCliente, "crm.add_cliente", "Cliente", "crm:clientes")
ClienteEditar = _editar(Cliente, FormCliente, "crm.change_cliente", "Cliente", "crm:clientes")
EquipamentoCriar = _criar(Equipamento, FormEquipamento, "crm.add_equipamento", "Equipamento", "crm:equipamentos")
EquipamentoEditar = _editar(Equipamento, FormEquipamento, "crm.change_equipamento", "Equipamento", "crm:equipamentos")
ContratoCriar = _criar(Contrato, FormContrato, "crm.add_contrato", "Contrato", "crm:contratos", ["cliente", "equipamento"])
ContratoEditar = _editar(Contrato, FormContrato, "crm.change_contrato", "Contrato", "crm:contratos")
FaturaCriar = _criar(Fatura, FormFatura, "crm.add_fatura", "Fatura", "crm:faturas", ["contrato"], "Fatura criada.")
FaturaEditar = _editar(Fatura, FormFatura, "crm.change_fatura", "Fatura", "crm:faturas")
OSCriar = _criar(OrdemServico, FormOS, "crm.add_ordemservico", "Ordem de serviço", "crm:ordens", ["equipamento"],
                 "Ordem de serviço aberta.")
OSEditar = _editar(OrdemServico, FormOS, "crm.change_ordemservico", "Ordem de serviço", "crm:ordens")


class LeituraCriar(_criar(LeituraHorimetro, FormLeitura, "crm.add_leiturahorimetro", "Leitura do horímetro",
                          "crm:equipamentos", ["equipamento"], "Leitura registrada.")):
    def get_success_url(self):
        return self.object.equipamento.get_absolute_url()


# ---------------------------------------------------------------- ações
def _voltar(request, padrao):
    destino = request.POST.get("voltar") or request.META.get("HTTP_REFERER")
    if destino and url_has_allowed_host_and_scheme(destino, {request.get_host()}, request.is_secure()):
        return redirect(destino)
    return redirect(padrao)


def _quer_json(request):
    return request.headers.get("Accept", "").startswith("application/json")


@require_POST
@permission_required("crm.change_lead", raise_exception=True)
def lead_etapa(request, pk):
    lead = get_object_or_404(Lead, pk=pk)
    nova = request.POST.get("status")
    if nova not in Lead.ETAPAS:
        return HttpResponseBadRequest("Etapa inválida.")
    motivo = request.POST.get("motivo_perda", "")
    if nova == "Perdidos" and motivo not in Lead.MOTIVOS_PERDA:
        erro = "Para marcar como perdido, escolha o motivo."
        if _quer_json(request):
            return JsonResponse({"ok": False, "erro": erro}, status=400)
        messages.error(request, erro)
        return redirect(lead)
    antiga = lead.status
    if nova != antiga:
        lead.status = nova
        lead.motivo_perda = motivo if nova == "Perdidos" else ""
        if not lead.responsavel:
            lead.responsavel = request.user
        lead.save()
        detalhe = f" ({motivo})" if nova == "Perdidos" else ""
        Atividade.objects.create(tipo="Mudança de etapa", assunto=f"{antiga} → {nova}{detalhe}", usuario=request.user, lead=lead)
    if _quer_json(request):
        return JsonResponse({"ok": True, "status": lead.status})
    messages.success(request, f"{lead.codigo} agora está em {lead.status}.")
    return _voltar(request, lead.get_absolute_url())


@require_POST
@permission_required("crm.change_ordemservico", raise_exception=True)
def os_status(request, pk):
    ordem = get_object_or_404(OrdemServico, pk=pk)
    novo = request.POST.get("status")
    if novo not in OrdemServico.STATUS:
        return HttpResponseBadRequest("Status inválido.")
    antigo = ordem.status
    if novo != antigo:
        ordem.status = novo
        if novo != "Concluída":
            ordem.data_conclusao = None
        ordem.save()
        Atividade.objects.create(tipo="Mudança de etapa", assunto=f"{antigo} → {novo}", usuario=request.user,
                                 ordem_servico=ordem)
    if _quer_json(request):
        return JsonResponse({"ok": True, "status": ordem.status})
    messages.success(request, f"{ordem.codigo} agora está {ordem.status.lower()}.")
    return _voltar(request, ordem.get_absolute_url())


@require_POST
@permission_required("crm.change_fatura", raise_exception=True)
def fatura_pagar(request, pk):
    fatura = get_object_or_404(Fatura, pk=pk)
    if fatura.status_pagamento != "Pago":
        fatura.status_pagamento = "Pago"
        fatura.data_pagamento = timezone.localdate()
        fatura.save()
        messages.success(request, f"Pagamento de {fatura.codigo} registrado em {fmt.data(fatura.data_pagamento)}.")
    return redirect(fatura)


ALVOS = {
    "lead": (Lead, "lead"), "cliente": (Cliente, "cliente"), "contrato": (Contrato, "contrato"),
    "equipamento": (Equipamento, "equipamento"), "os": (OrdemServico, "ordem_servico"),
}


@require_POST
@permission_required("crm.add_atividade", raise_exception=True)
def atividade_nova(request):
    tipo, _, pk = request.POST.get("alvo", "").partition(":")
    if tipo not in ALVOS or not pk.isdigit():
        raise Http404
    model, campo = ALVOS[tipo]
    alvo = get_object_or_404(model, pk=int(pk))
    form = FormAtividade(request.POST)
    if form.is_valid():
        atv = form.save(commit=False)
        atv.usuario = request.user
        setattr(atv, campo, alvo)
        atv.save()
        messages.success(request, "Atividade registrada.")
    else:
        messages.error(request, "Atividade não registrada: preencha o assunto.")
    return redirect(alvo)


@require_POST
@permission_required("crm.change_atividade", raise_exception=True)
def atividade_concluir(request, pk):
    atv = get_object_or_404(Atividade, pk=pk)
    atv.concluida = not atv.concluida
    atv.save(update_fields=["concluida"])
    return _voltar(request, reverse("crm:inicio"))


@permission_required(["crm.add_contrato", "crm.change_lead"], raise_exception=True)
def lead_converter(request, pk):
    """Lead vira contrato: escolhe ou cria o cliente, escolhe a máquina livre e fecha o lead."""
    lead = get_object_or_404(Lead, pk=pk)
    if lead.contrato:
        messages.info(request, f"Este lead já tem o contrato {lead.contrato.codigo}.")
        return redirect(lead)
    inicial = {
        "razao_social": lead.nome, "obra_local": "", "data_inicio": lead.inicio_pretendido or timezone.localdate(),
        "cliente": lead.cliente_id or Cliente.objects.filter(razao_social__iexact=lead.nome).values_list("pk", flat=True).first(),
    }
    form = FormConverterLead(request.POST or None, initial=inicial)
    livres = anotar_situacao(Equipamento.objects.filter(status_cadastro="Ativo"))
    if lead.segmento:
        livres = livres.filter(segmento=lead.segmento)
    form.fields["equipamento"].queryset = livres.order_by("em_manut", "locado", "codigo")
    form.fields["equipamento"].label_from_instance = lambda e: f"{e} · {e.filial} · {situacao_anotada(e)}"
    if request.method == "POST" and form.is_valid():
        d = form.cleaned_data
        with transaction.atomic():
            cliente = d["cliente"]
            if not cliente:
                cliente = Cliente.objects.create(razao_social=d["razao_social"], cnpj=d["cnpj"], cidade=lead.cidade)
            contrato = Contrato.objects.create(
                cliente=cliente, equipamento=d["equipamento"], modalidade=d["modalidade"], data_inicio=d["data_inicio"],
                data_fim_prevista=d["data_fim_prevista"], valor_diaria=d["valor_diaria"], valor_mensal=d["valor_mensal"],
                obra_local=d["obra_local"], status="Ativo",
            )
            antiga = lead.status
            lead.cliente, lead.contrato, lead.status = cliente, contrato, "Fechado"
            lead.data_desfecho = timezone.localdate()
            lead.save()
            Atividade.objects.create(tipo="Mudança de etapa", assunto=f"{antiga} → Fechado (contrato {contrato.codigo})",
                                     usuario=request.user, lead=lead, contrato=contrato)
        messages.success(request, f"Contrato {contrato.codigo} criado e lead {lead.codigo} fechado.")
        return redirect(contrato)
    return render(request, "crm/converter.html", {"form": form, "lead": lead, "rotulo_objeto": "Lead"})


# ---------------------------------------------------------------- Kanban
@permission_required("crm.view_lead", raise_exception=True)
def leads_kanban(request):
    limite_fechados = timezone.now() - timedelta(days=60)
    qs = Lead.objects.select_related("responsavel")
    seg = request.GET.get("segmento", "")
    if seg:
        qs = qs.filter(segmento=seg)
    if request.GET.get("meus"):
        qs = qs.filter(responsavel=request.user)
    colunas = []
    for etapa in Lead.ETAPAS:
        itens = qs.filter(status=etapa)
        if etapa in ("Fechado", "Perdidos"):
            itens = itens.filter(Q(data_desfecho__gte=limite_fechados.date()) | Q(data_desfecho__isnull=True))
        itens = list(itens.order_by("-data_envio")[:60])
        colunas.append({"etapa": etapa, "cor": fmt.SELOS[etapa], "itens": itens, "total": len(itens)})
    return render(request, "crm/kanban_leads.html", {
        "colunas": colunas, "motivos": Lead.MOTIVOS_PERDA, "segmentos": SEGMENTOS, "segmento": seg,
        "meus": bool(request.GET.get("meus")), "pode": request.user.has_perm("crm.change_lead"),
    })


@permission_required("crm.view_ordemservico", raise_exception=True)
def oficina(request):
    qs = OrdemServico.objects.select_related("equipamento", "responsavel")
    filial = request.GET.get("filial", "")
    if filial:
        qs = qs.filter(equipamento__filial=filial)
    colunas = []
    for st in OrdemServico.STATUS:
        itens = qs.filter(status=st)
        itens = list(itens.order_by("-data_conclusao", "-data_abertura")[:20]) if st == "Concluída" else list(
            itens.order_by("data_abertura"))
        colunas.append({"etapa": st, "cor": fmt.SELOS[st], "itens": itens, "total": len(itens)})
    hoje = timezone.localdate()
    for col in colunas[:2]:
        for o in col["itens"]:
            o.dias_aberta = (hoje - o.data_abertura).days
    return render(request, "crm/kanban_os.html", {
        "colunas": colunas, "filiais": FILIAIS, "filial": filial,
        "pode": request.user.has_perm("crm.change_ordemservico"),
    })


# ---------------------------------------------------------------- Início, busca e painel
def inicio(request):
    hoje = timezone.localdate()
    u = request.user
    frota = anotar_situacao(Equipamento.objects.filter(status_cadastro="Ativo"))
    em_manut = frota.filter(em_manut=True).count()
    locados = frota.filter(em_manut=False, locado=True).count()
    ativos = frota.count()
    vencidas = Fatura.objects.filter(status_pagamento="Vencido").aggregate(s=Sum("valor_faturado"), n=Count("pk"))
    tiles = [
        {"rotulo": "Leads em aberto", "valor": Lead.objects.filter(status__in=Lead.ETAPAS_ABERTAS).count(),
         "nota": f'{Lead.objects.filter(status="Novo").count()} novos sem contato', "url": reverse("crm:leads") + "?visao=abertos"},
        {"rotulo": "Contratos ativos", "valor": Contrato.objects.filter(status="Ativo").count(),
         "nota": f'{Contrato.objects.filter(status="Ativo", data_fim_prevista__lt=hoje).count()} com devolução atrasada',
         "url": reverse("crm:contratos") + "?status=Ativo"},
        {"rotulo": "Frota disponível", "valor": ativos - em_manut - locados,
         "nota": f"de {ativos} ativas · {locados} locadas", "url": reverse("crm:equipamentos") + "?situacao=Disponível"},
        {"rotulo": "Em manutenção", "valor": em_manut, "nota": "máquinas com OS aberta", "url": reverse("crm:oficina")},
        {"rotulo": "Faturas vencidas", "valor": fmt.brl_compacto(vencidas["s"] or 0),
         "nota": f'{vencidas["n"]} faturas', "url": reverse("crm:faturas") + "?status=Vencido", "alerta": True},
    ]
    tarefas = Atividade.objects.filter(tipo="Tarefa", concluida=False, usuario=u).order_by("vencimento", "data")[:8]
    return render(request, "crm/inicio.html", {
        "tiles": tiles,
        "tarefas": tarefas,
        "hoje": hoje,
        "leads_recentes": Lead.objects.select_related("responsavel").order_by("-data_envio")[:6],
        "a_vencer": Contrato.objects.select_related("cliente", "equipamento").filter(
            status="Ativo", data_fim_prevista__gte=hoje, data_fim_prevista__lte=hoje + timedelta(days=30)
        ).order_by("data_fim_prevista")[:6],
        "os_antigas": OrdemServico.objects.select_related("equipamento").exclude(status="Concluída").order_by("data_abertura")[:6],
    })


def busca(request):
    q = request.GET.get("q", "").strip()
    grupos = []
    if len(q) >= 2:
        u = request.user
        defs = [
            ("Leads", "lead", "crm.view_lead", Lead.objects.select_related("responsavel"),
             ["codigo", "nome", "contato", "cidade", "modelo"]),
            ("Clientes", "cliente", "crm.view_cliente",
             Cliente.objects.annotate(n_ativos=Count("contratos", filter=Q(contratos__status="Ativo"))),
             ["codigo", "razao_social", "cnpj"]),
            ("Frota", "equipamento", "crm.view_equipamento", anotar_situacao(Equipamento.objects.all()),
             ["codigo", "modelo", "fabricante", "numero_serie"]),
            ("Contratos", "contrato", "crm.view_contrato", Contrato.objects.select_related("cliente", "equipamento"),
             ["codigo", "cliente__razao_social", "obra_local"]),
            ("Ordens de serviço", "os", "crm.view_ordemservico", OrdemServico.objects.select_related("equipamento"),
             ["codigo", "descricao", "equipamento__codigo"]),
            ("Faturas", "fatura", "crm.view_fatura", Fatura.objects.select_related("contrato__cliente"), ["codigo"]),
        ]
        for titulo, objeto, perm, qs, campos in defs:
            if not u.has_perm(perm):
                continue
            cond = Q()
            for c in campos:
                cond |= Q(**{f"{c}__icontains": q})
            achados = qs.filter(cond)
            total = achados.count()
            if total:
                grupos.append({
                    "titulo": titulo, "total": total,
                    "cabecalho": [{"rotulo": c.rotulo, "num": c.num} for c in COLUNAS[objeto]],
                    "linhas": montar_linhas(achados[:8], COLUNAS[objeto]),
                })
    return render(request, "crm/busca.html", {"q": q, "grupos": grupos})


def painel(request):
    dados = cache.get("painel_dados")
    if dados is None:
        dados = kpis.dados_painel()
        cache.set("painel_dados", dados, 300)
    return render(request, "crm/painel.html", {"dados": dados, "hoje": timezone.localdate()})
