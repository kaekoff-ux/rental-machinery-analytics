from django.urls import path

from . import api, views

app_name = "crm"

urlpatterns = [
    path("", views.inicio, name="inicio"),
    path("busca/", views.busca, name="busca"),
    path("painel/", views.painel, name="painel"),
    # Leads
    path("leads/", views.LeadLista.as_view(), name="leads"),
    path("leads/kanban/", views.leads_kanban, name="leads_kanban"),
    path("leads/novo/", views.LeadCriar.as_view(), name="lead_novo"),
    path("leads/<int:pk>/", views.LeadDetalhe.as_view(), name="lead"),
    path("leads/<int:pk>/editar/", views.LeadEditar.as_view(), name="lead_editar"),
    path("leads/<int:pk>/etapa/", views.lead_etapa, name="lead_etapa"),
    path("leads/<int:pk>/converter/", views.lead_converter, name="lead_converter"),
    # Clientes
    path("clientes/", views.ClienteLista.as_view(), name="clientes"),
    path("clientes/novo/", views.ClienteCriar.as_view(), name="cliente_novo"),
    path("clientes/<int:pk>/", views.ClienteDetalhe.as_view(), name="cliente"),
    path("clientes/<int:pk>/editar/", views.ClienteEditar.as_view(), name="cliente_editar"),
    # Frota
    path("frota/", views.EquipamentoLista.as_view(), name="equipamentos"),
    path("frota/novo/", views.EquipamentoCriar.as_view(), name="equipamento_novo"),
    path("frota/<int:pk>/", views.EquipamentoDetalhe.as_view(), name="equipamento"),
    path("frota/<int:pk>/editar/", views.EquipamentoEditar.as_view(), name="equipamento_editar"),
    path("frota/horimetro/novo/", views.LeituraCriar.as_view(), name="leitura_nova"),
    # Contratos
    path("contratos/", views.ContratoLista.as_view(), name="contratos"),
    path("contratos/novo/", views.ContratoCriar.as_view(), name="contrato_novo"),
    path("contratos/<int:pk>/", views.ContratoDetalhe.as_view(), name="contrato"),
    path("contratos/<int:pk>/editar/", views.ContratoEditar.as_view(), name="contrato_editar"),
    # Oficina (ordens de serviço)
    path("oficina/", views.oficina, name="oficina"),
    path("oficina/ordens/", views.OSLista.as_view(), name="ordens"),
    path("oficina/ordens/nova/", views.OSCriar.as_view(), name="os_nova"),
    path("oficina/ordens/<int:pk>/", views.OSDetalhe.as_view(), name="os"),
    path("oficina/ordens/<int:pk>/editar/", views.OSEditar.as_view(), name="os_editar"),
    path("oficina/ordens/<int:pk>/status/", views.os_status, name="os_status"),
    # Faturas
    path("faturas/", views.FaturaLista.as_view(), name="faturas"),
    path("faturas/nova/", views.FaturaCriar.as_view(), name="fatura_nova"),
    path("faturas/<int:pk>/", views.FaturaDetalhe.as_view(), name="fatura"),
    path("faturas/<int:pk>/editar/", views.FaturaEditar.as_view(), name="fatura_editar"),
    path("faturas/<int:pk>/pagar/", views.fatura_pagar, name="fatura_pagar"),
    # Atividades
    path("atividades/nova/", views.atividade_nova, name="atividade_nova"),
    path("atividades/<int:pk>/concluir/", views.atividade_concluir, name="atividade_concluir"),
    # API para o n8n
    path("api/leads/", api.receber_lead, name="api_leads"),
]
