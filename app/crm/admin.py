from django.contrib import admin

from .models import Atividade, Cliente, Contrato, Equipamento, Fatura, Lead, LeituraHorimetro, OrdemServico


@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ["codigo", "razao_social", "segmento", "cidade", "uf"]
    search_fields = ["codigo", "razao_social", "cnpj"]
    list_filter = ["segmento", "uf"]


@admin.register(Equipamento)
class EquipamentoAdmin(admin.ModelAdmin):
    list_display = ["codigo", "segmento", "fabricante", "modelo", "filial", "status_cadastro"]
    search_fields = ["codigo", "modelo", "fabricante", "numero_serie"]
    list_filter = ["segmento", "filial", "status_cadastro"]


@admin.register(Contrato)
class ContratoAdmin(admin.ModelAdmin):
    list_display = ["codigo", "cliente", "equipamento", "data_inicio", "data_fim_prevista", "status"]
    search_fields = ["codigo", "cliente__razao_social", "equipamento__codigo"]
    list_filter = ["status", "modalidade"]
    raw_id_fields = ["cliente", "equipamento"]


@admin.register(Fatura)
class FaturaAdmin(admin.ModelAdmin):
    list_display = ["codigo", "contrato", "competencia", "valor_faturado", "data_vencimento", "status_pagamento"]
    search_fields = ["codigo", "contrato__codigo"]
    list_filter = ["status_pagamento"]
    raw_id_fields = ["contrato"]


@admin.register(OrdemServico)
class OrdemServicoAdmin(admin.ModelAdmin):
    list_display = ["codigo", "equipamento", "tipo", "data_abertura", "status"]
    search_fields = ["codigo", "equipamento__codigo", "descricao"]
    list_filter = ["tipo", "status"]
    raw_id_fields = ["equipamento"]


@admin.register(LeituraHorimetro)
class LeituraAdmin(admin.ModelAdmin):
    list_display = ["codigo", "equipamento", "data_leitura", "horimetro_horas", "fonte"]
    search_fields = ["codigo", "equipamento__codigo"]
    raw_id_fields = ["equipamento", "contrato"]


@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    list_display = ["codigo", "nome", "segmento", "origem", "status", "data_envio"]
    search_fields = ["codigo", "nome", "contato"]
    list_filter = ["status", "origem", "segmento"]
    raw_id_fields = ["cliente", "contrato"]


@admin.register(Atividade)
class AtividadeAdmin(admin.ModelAdmin):
    list_display = ["tipo", "assunto", "data", "usuario", "concluida"]
    list_filter = ["tipo", "concluida"]
    raw_id_fields = ["lead", "cliente", "contrato", "equipamento", "ordem_servico"]
