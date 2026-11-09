from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm

from .models import Atividade, Cliente, Contrato, Equipamento, Fatura, Lead, LeituraHorimetro, OrdemServico

DATA = forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d")
DATAHORA = forms.DateTimeInput(attrs={"type": "datetime-local"}, format="%Y-%m-%dT%H:%M")


class FormLogin(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].label = "Usuário"
        self.fields["username"].widget.attrs.update({"autocomplete": "username", "autofocus": True})
        self.fields["password"].label = "Senha"


class FormBase(forms.ModelForm):
    """Datas como campo de data do navegador e usuários pelo nome."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for nome, campo in self.fields.items():
            if isinstance(campo, forms.DateField):
                campo.widget = DATA
            elif isinstance(campo, forms.DateTimeField):
                campo.widget = DATAHORA
            if nome == "responsavel":
                campo.queryset = get_user_model().objects.filter(is_active=True).order_by("first_name", "username")
                campo.label_from_instance = lambda u: u.get_full_name() or u.username


class FormLead(FormBase):
    class Meta:
        model = Lead
        fields = [
            "nome", "contato", "cidade", "equipamento_pedido", "prazo", "inicio_pretendido", "origem", "status",
            "motivo_perda", "responsavel", "cliente", "contrato", "observacao", "data_envio",
        ]
        widgets = {"observacao": forms.Textarea(attrs={"rows": 4})}

    def clean(self):
        dados = super().clean()
        if dados.get("status") == "Perdidos" and not dados.get("motivo_perda"):
            self.add_error("motivo_perda", "Informe o motivo da perda.")
        return dados


class FormCliente(FormBase):
    class Meta:
        model = Cliente
        fields = ["razao_social", "cnpj", "segmento", "cidade", "uf", "limite_credito", "data_cadastro"]


class FormEquipamento(FormBase):
    class Meta:
        model = Equipamento
        fields = [
            "segmento", "fabricante", "modelo", "ano_fabricacao", "numero_serie", "filial", "data_aquisicao",
            "valor_aquisicao", "vida_util_horas", "status_cadastro",
        ]


class FormContrato(FormBase):
    class Meta:
        model = Contrato
        fields = [
            "cliente", "equipamento", "modalidade", "data_inicio", "data_fim_prevista", "data_devolucao",
            "valor_diaria", "valor_mensal", "obra_local", "status",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["equipamento"].queryset = Equipamento.objects.filter(status_cadastro="Ativo")

    def clean(self):
        dados = super().clean()
        for campo, msg in erros_contrato(dados, self.instance.pk):
            self.add_error(campo, msg)
        return dados


def erros_contrato(dados, pk_atual=None):
    """Regras do contrato: datas coerentes, valores da modalidade e máquina livre no período."""
    erros = []
    ini, fim, dev = dados.get("data_inicio"), dados.get("data_fim_prevista"), dados.get("data_devolucao")
    if ini and fim and fim < ini:
        erros.append(("data_fim_prevista", "O fim previsto não pode ser antes do início."))
    if ini and dev and dev < ini:
        erros.append(("data_devolucao", "A devolução não pode ser antes do início."))
    eq = dados.get("equipamento")
    if eq and ini and fim and dados.get("status", "Ativo") != "Cancelado":
        # Regra do projeto: contrato novo só com a máquina livre no período.
        candidatos = (
            Contrato.objects.filter(equipamento=eq, data_inicio__lte=dev or fim)
            .exclude(status="Cancelado")
            .exclude(pk=pk_atual)
        )
        choque = [c for c in candidatos if (c.data_devolucao or c.data_fim_prevista) >= ini]
        if choque:
            codigos = ", ".join(c.codigo for c in choque[:3])
            erros.append(("equipamento", f"A máquina já está em contrato nesse período ({codigos})."))
    if dados.get("modalidade") == "Mensal" and not dados.get("valor_mensal"):
        erros.append(("valor_mensal", "Contrato mensal precisa do valor mensal."))
    if dados.get("modalidade") in ("Diária", "Semanal") and not dados.get("valor_diaria"):
        erros.append(("valor_diaria", "Informe o valor da diária."))
    return erros


class FormFatura(FormBase):
    class Meta:
        model = Fatura
        fields = [
            "contrato", "competencia", "valor_faturado", "data_emissao", "data_vencimento", "data_pagamento",
            "status_pagamento",
        ]
        widgets = {"competencia": forms.TextInput(attrs={"placeholder": "2026-11", "pattern": r"\d{4}-\d{2}"})}

    def clean(self):
        dados = super().clean()
        if dados.get("status_pagamento") == "Pago" and not dados.get("data_pagamento"):
            self.add_error("data_pagamento", "Fatura paga precisa da data de pagamento.")
        return dados


class FormOS(FormBase):
    class Meta:
        model = OrdemServico
        fields = [
            "equipamento", "tipo", "descricao", "status", "responsavel", "data_abertura", "data_conclusao",
            "horimetro_na_os", "horas_parada", "custo_pecas", "custo_mao_obra",
        ]


class FormLeitura(FormBase):
    class Meta:
        model = LeituraHorimetro
        fields = ["equipamento", "data_leitura", "horimetro_horas", "fonte", "contrato"]

    def clean(self):
        dados = super().clean()
        eq, h, d = dados.get("equipamento"), dados.get("horimetro_horas"), dados.get("data_leitura")
        if eq and h is not None and d:
            anterior = eq.leituras.filter(data_leitura__lte=d).exclude(pk=self.instance.pk).order_by("-data_leitura").first()
            if anterior and h < anterior.horimetro_horas:
                self.add_error(
                    "horimetro_horas",
                    f"Menor que a leitura de {anterior.data_leitura:%d/%m/%Y} ({anterior.horimetro_horas} h). "
                    "Horímetro não volta.",
                )
        return dados


class FormAtividade(FormBase):
    class Meta:
        model = Atividade
        fields = ["tipo", "assunto", "descricao", "vencimento"]
        widgets = {"descricao": forms.Textarea(attrs={"rows": 3})}


class FormConverterLead(forms.Form):
    """Lead fechado vira cliente (novo ou existente) e contrato."""

    cliente = forms.ModelChoiceField(
        Cliente.objects.all(), required=False, label="Cliente existente",
        help_text="Deixe em branco para cadastrar um cliente novo com os dados do lead.",
    )
    razao_social = forms.CharField(label="Razão social (cliente novo)", required=False, max_length=120)
    cnpj = forms.CharField(label="CNPJ (cliente novo)", required=False, max_length=18)
    equipamento = forms.ModelChoiceField(Equipamento.objects.filter(status_cadastro="Ativo"), label="Equipamento")
    modalidade = forms.ChoiceField(choices=[(m, m) for m in Contrato.MODALIDADES], label="Modalidade")
    data_inicio = forms.DateField(label="Início", widget=DATA)
    data_fim_prevista = forms.DateField(label="Fim previsto", widget=DATA)
    valor_diaria = forms.DecimalField(label="Valor da diária", required=False, max_digits=12, decimal_places=2)
    valor_mensal = forms.DecimalField(label="Valor mensal", required=False, max_digits=12, decimal_places=2)
    obra_local = forms.CharField(label="Obra / local", required=False, max_length=120)

    def clean(self):
        dados = super().clean()
        if not dados.get("cliente") and not dados.get("razao_social"):
            self.add_error("razao_social", "Escolha um cliente existente ou informe a razão social.")
        for campo, msg in erros_contrato(dados):
            self.add_error(campo, msg)
        return dados
