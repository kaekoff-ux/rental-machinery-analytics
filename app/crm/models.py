"""Objetos do sistema de gestão LocaMaq.

Os nomes seguem o dicionário de dados do projeto (docs/dicionario_dados.csv). Cada objeto tem
um `codigo` legível (CL-0001, EQ-0001, CT-00001, FT-000001, OS-00001, HR-000001,
LEAD_0001/26), que é a chave usada na importação: reimportar atualiza, não duplica.
"""
import re
from datetime import date

from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils import timezone

SEGMENTOS = [
    "Escavadeira",
    "Retroescavadeira",
    "Pá-carregadeira",
    "Guindaste",
    "Empilhadeira",
    "Plataforma elevatória",
    "Gerador",
]
FILIAIS = ["Sorocaba", "São Paulo", "Campinas", "Ribeirão Preto", "São José dos Campos"]


def _opcoes(lista):
    return [(x, x) for x in lista]


def proximo_codigo(model, prefixo, digitos):
    """Próximo código sequencial (ex.: CL-0071) a partir do maior já gravado."""
    maior = 0
    for codigo in model.objects.filter(codigo__startswith=prefixo).values_list("codigo", flat=True):
        m = re.search(r"(\d+)", codigo[len(prefixo):])
        if m:
            maior = max(maior, int(m.group(1)))
    return f"{prefixo}{maior + 1:0{digitos}d}"


class Registro(models.Model):
    """Campos comuns: data de criação e de alteração."""

    criado_em = models.DateTimeField("criado em", auto_now_add=True)
    atualizado_em = models.DateTimeField("atualizado em", auto_now=True)

    class Meta:
        abstract = True


class Cliente(Registro):
    SEGMENTOS_CLIENTE = [
        "Construção civil",
        "Infraestrutura",
        "Indústria",
        "Eventos",
        "Mineração",
        "Logística",
        "Agronegócio",
    ]
    codigo = models.CharField("código", max_length=12, unique=True)
    razao_social = models.CharField("razão social", max_length=120)
    cnpj = models.CharField("CNPJ", max_length=18, blank=True)
    segmento = models.CharField("segmento", max_length=30, choices=_opcoes(SEGMENTOS_CLIENTE), blank=True)
    cidade = models.CharField("cidade", max_length=60, blank=True)
    uf = models.CharField("UF", max_length=2, blank=True)
    limite_credito = models.DecimalField("limite de crédito", max_digits=14, decimal_places=2, null=True, blank=True)
    data_cadastro = models.DateField("data de cadastro", default=date.today)

    class Meta:
        ordering = ["razao_social"]
        verbose_name = "cliente"
        verbose_name_plural = "clientes"

    def __str__(self):
        return self.razao_social

    def get_absolute_url(self):
        return reverse("crm:cliente", args=[self.pk])

    def save(self, *args, **kwargs):
        if not self.codigo:
            self.codigo = proximo_codigo(Cliente, "CL-", 4)
        super().save(*args, **kwargs)


class Equipamento(Registro):
    STATUS = ["Ativo", "Vendido", "Baixado"]
    codigo = models.CharField("código", max_length=12, unique=True)
    segmento = models.CharField("segmento", max_length=30, choices=_opcoes(SEGMENTOS))
    fabricante = models.CharField("fabricante", max_length=40)
    modelo = models.CharField("modelo", max_length=40)
    ano_fabricacao = models.PositiveIntegerField("ano de fabricação", null=True, blank=True)
    numero_serie = models.CharField("número de série", max_length=40, blank=True)
    data_aquisicao = models.DateField("data de aquisição")
    valor_aquisicao = models.DecimalField("valor de aquisição", max_digits=14, decimal_places=2)
    vida_util_horas = models.PositiveIntegerField("vida útil (horas)")
    filial = models.CharField("filial", max_length=30, choices=_opcoes(FILIAIS))
    status_cadastro = models.CharField("status do cadastro", max_length=10, choices=_opcoes(STATUS), default="Ativo")

    class Meta:
        ordering = ["codigo"]
        verbose_name = "equipamento"
        verbose_name_plural = "equipamentos"

    def __str__(self):
        return f"{self.codigo} · {self.fabricante} {self.modelo}"

    def get_absolute_url(self):
        return reverse("crm:equipamento", args=[self.pk])

    def save(self, *args, **kwargs):
        if not self.codigo:
            self.codigo = proximo_codigo(Equipamento, "EQ-", 4)
        super().save(*args, **kwargs)

    @property
    def nome_modelo(self):
        return f"{self.fabricante} {self.modelo}"

    def situacao(self, hoje=None):
        """Situação operacional: Fora da frota, Em manutenção, Locado ou Disponível."""
        if self.status_cadastro != "Ativo":
            return "Fora da frota"
        if self.ordens.exclude(status="Concluída").exists():
            return "Em manutenção"
        if self.contratos.filter(status="Ativo").exists():
            return "Locado"
        return "Disponível"

    def horimetro_atual(self):
        ultima = self.leituras.order_by("-data_leitura", "-horimetro_horas").first()
        return ultima.horimetro_horas if ultima else None


class Contrato(Registro):
    MODALIDADES = ["Diária", "Semanal", "Mensal"]
    STATUS = ["Ativo", "Encerrado", "Cancelado"]
    codigo = models.CharField("código", max_length=12, unique=True)
    cliente = models.ForeignKey(Cliente, on_delete=models.PROTECT, related_name="contratos", verbose_name="cliente")
    equipamento = models.ForeignKey(
        Equipamento, on_delete=models.PROTECT, related_name="contratos", verbose_name="equipamento"
    )
    data_inicio = models.DateField("início")
    data_fim_prevista = models.DateField("fim previsto")
    data_devolucao = models.DateField("devolução", null=True, blank=True)
    modalidade = models.CharField("modalidade", max_length=10, choices=_opcoes(MODALIDADES))
    valor_diaria = models.DecimalField("valor da diária", max_digits=12, decimal_places=2, null=True, blank=True)
    valor_mensal = models.DecimalField("valor mensal", max_digits=12, decimal_places=2, null=True, blank=True)
    obra_local = models.CharField("obra / local", max_length=120, blank=True)
    status = models.CharField("status", max_length=10, choices=_opcoes(STATUS), default="Ativo")

    class Meta:
        ordering = ["-data_inicio", "-codigo"]
        verbose_name = "contrato"
        verbose_name_plural = "contratos"

    def __str__(self):
        return self.codigo

    def get_absolute_url(self):
        return reverse("crm:contrato", args=[self.pk])

    def save(self, *args, **kwargs):
        if not self.codigo:
            self.codigo = proximo_codigo(Contrato, "CT-", 5)
        super().save(*args, **kwargs)

    @property
    def devolucao_atrasada(self):
        return self.status == "Ativo" and self.data_fim_prevista < timezone.localdate()

    @property
    def valor_referencia(self):
        if self.modalidade == "Mensal" and self.valor_mensal:
            return self.valor_mensal
        return self.valor_diaria


class Fatura(Registro):
    STATUS = ["Pago", "Em aberto", "Vencido"]
    codigo = models.CharField("código", max_length=12, unique=True)
    contrato = models.ForeignKey(Contrato, on_delete=models.PROTECT, related_name="faturas", verbose_name="contrato")
    competencia = models.CharField("competência (aaaa-mm)", max_length=7)
    valor_faturado = models.DecimalField("valor faturado", max_digits=14, decimal_places=2)
    data_emissao = models.DateField("emissão")
    data_vencimento = models.DateField("vencimento")
    data_pagamento = models.DateField("pagamento", null=True, blank=True)
    status_pagamento = models.CharField("status", max_length=10, choices=_opcoes(STATUS), default="Em aberto")

    class Meta:
        ordering = ["-data_emissao", "-codigo"]
        verbose_name = "fatura"
        verbose_name_plural = "faturas"

    def __str__(self):
        return self.codigo

    def get_absolute_url(self):
        return reverse("crm:fatura", args=[self.pk])

    def save(self, *args, **kwargs):
        if not self.codigo:
            self.codigo = proximo_codigo(Fatura, "FT-", 6)
        super().save(*args, **kwargs)

    @property
    def dias_atraso(self):
        if self.data_pagamento and self.data_pagamento > self.data_vencimento:
            return (self.data_pagamento - self.data_vencimento).days
        if not self.data_pagamento and self.data_vencimento < timezone.localdate():
            return (timezone.localdate() - self.data_vencimento).days
        return 0


class OrdemServico(Registro):
    TIPOS = ["Preventiva", "Corretiva", "Preditiva"]
    STATUS = ["Aberta", "Em andamento", "Concluída"]
    codigo = models.CharField("código", max_length=12, unique=True)
    equipamento = models.ForeignKey(
        Equipamento, on_delete=models.PROTECT, related_name="ordens", verbose_name="equipamento"
    )
    tipo = models.CharField("tipo", max_length=12, choices=_opcoes(TIPOS))
    data_abertura = models.DateField("abertura", default=date.today)
    data_conclusao = models.DateField("conclusão", null=True, blank=True)
    horimetro_na_os = models.DecimalField("horímetro na OS", max_digits=10, decimal_places=1, null=True, blank=True)
    descricao = models.CharField("descrição", max_length=200)
    horas_parada = models.DecimalField("horas parada", max_digits=8, decimal_places=1, null=True, blank=True)
    custo_pecas = models.DecimalField("custo de peças", max_digits=12, decimal_places=2, default=0)
    custo_mao_obra = models.DecimalField("custo de mão de obra", max_digits=12, decimal_places=2, default=0)
    status = models.CharField("status", max_length=14, choices=_opcoes(STATUS), default="Aberta")
    responsavel = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="responsável"
    )

    class Meta:
        ordering = ["-data_abertura", "-codigo"]
        verbose_name = "ordem de serviço"
        verbose_name_plural = "ordens de serviço"

    def __str__(self):
        return self.codigo

    def get_absolute_url(self):
        return reverse("crm:os", args=[self.pk])

    def save(self, *args, **kwargs):
        if not self.codigo:
            self.codigo = proximo_codigo(OrdemServico, "OS-", 5)
        if self.status == "Concluída" and not self.data_conclusao:
            self.data_conclusao = timezone.localdate()
        super().save(*args, **kwargs)

    @property
    def custo_total(self):
        return (self.custo_pecas or 0) + (self.custo_mao_obra or 0)


class LeituraHorimetro(models.Model):
    FONTES = ["Telemetria", "Manual"]
    codigo = models.CharField("código", max_length=12, unique=True)
    equipamento = models.ForeignKey(
        Equipamento, on_delete=models.CASCADE, related_name="leituras", verbose_name="equipamento"
    )
    data_leitura = models.DateField("data da leitura")
    horimetro_horas = models.DecimalField("horímetro (h)", max_digits=10, decimal_places=1)
    fonte = models.CharField("fonte", max_length=12, choices=_opcoes(FONTES), default="Manual")
    contrato = models.ForeignKey(
        Contrato, on_delete=models.SET_NULL, null=True, blank=True, related_name="leituras", verbose_name="contrato"
    )

    class Meta:
        ordering = ["-data_leitura"]
        verbose_name = "leitura de horímetro"
        verbose_name_plural = "leituras de horímetro"
        indexes = [models.Index(fields=["equipamento", "data_leitura"])]

    def __str__(self):
        return f"{self.equipamento.codigo} · {self.data_leitura:%d/%m/%Y} · {self.horimetro_horas} h"

    def save(self, *args, **kwargs):
        if not self.codigo:
            self.codigo = proximo_codigo(LeituraHorimetro, "HR-", 6)
        super().save(*args, **kwargs)


class Lead(Registro):
    ETAPAS = ["Novo", "Em Contato", "Orçado", "Fechado", "Perdidos"]
    ETAPAS_ABERTAS = ["Novo", "Em Contato", "Orçado"]
    ORIGENS = ["site", "whatsapp", "telegram", "telefone", "indicação", "e-mail", "outro"]
    MOTIVOS_PERDA = [
        "Indisponibilidade de máquina",
        "Preço acima do concorrente",
        "Crédito não aprovado",
        "Obra adiada pelo cliente",
        "Sem retorno do cliente",
        "Outro",
    ]
    codigo = models.CharField("número do lead", max_length=16, unique=True)
    data_envio = models.DateTimeField("data de envio", default=timezone.now)
    nome = models.CharField("nome / empresa", max_length=120)
    contato = models.CharField("contato (e-mail ou telefone)", max_length=120, blank=True)
    cidade = models.CharField("cidade", max_length=60, blank=True)
    equipamento_pedido = models.CharField(
        "equipamento pedido", max_length=80, blank=True, help_text='Como chega do site: "Segmento – Modelo".'
    )
    segmento = models.CharField("segmento", max_length=30, blank=True)
    modelo = models.CharField("modelo", max_length=60, blank=True)
    prazo = models.CharField("prazo", max_length=40, blank=True)
    inicio_pretendido = models.DateField("início pretendido", null=True, blank=True)
    observacao = models.TextField("observação", blank=True)
    origem = models.CharField("origem", max_length=12, choices=_opcoes(ORIGENS), default="site")
    status = models.CharField("etapa", max_length=12, choices=_opcoes(ETAPAS), default="Novo")
    data_desfecho = models.DateField("data do desfecho", null=True, blank=True)
    motivo_perda = models.CharField("motivo da perda", max_length=40, choices=_opcoes(MOTIVOS_PERDA), blank=True)
    cliente = models.ForeignKey(
        Cliente, on_delete=models.SET_NULL, null=True, blank=True, related_name="leads", verbose_name="cliente"
    )
    contrato = models.ForeignKey(
        Contrato, on_delete=models.SET_NULL, null=True, blank=True, related_name="leads", verbose_name="contrato"
    )
    responsavel = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="responsável"
    )

    class Meta:
        ordering = ["-data_envio"]
        verbose_name = "lead"
        verbose_name_plural = "leads"

    def __str__(self):
        return f"{self.codigo} · {self.nome}"

    def get_absolute_url(self):
        return reverse("crm:lead", args=[self.pk])

    def save(self, *args, **kwargs):
        if not self.codigo:
            self.codigo = proximo_codigo_lead(timezone.localtime(self.data_envio).year)
        seg, mod = separar_equipamento(self.equipamento_pedido)
        self.segmento, self.modelo = seg, mod
        if self.status in ("Fechado", "Perdidos") and not self.data_desfecho:
            self.data_desfecho = timezone.localdate()
        if self.status not in ("Fechado", "Perdidos"):
            self.data_desfecho = None
        if self.status != "Perdidos":
            self.motivo_perda = ""
        super().save(*args, **kwargs)

    @property
    def aberto(self):
        return self.status in self.ETAPAS_ABERTAS

    @property
    def dias_fechamento(self):
        if self.status == "Fechado" and self.data_desfecho:
            return (self.data_desfecho - timezone.localtime(self.data_envio).date()).days
        return None


def separar_equipamento(texto):
    """'Escavadeira – Caterpillar 320GC' -> ('Escavadeira', 'Caterpillar 320GC')."""
    texto = (texto or "").strip()
    if not texto:
        return "", ""
    partes = re.split(r"\s+[–-]\s+", texto, maxsplit=1)
    segmento = partes[0].strip()
    modelo = partes[1].strip() if len(partes) > 1 else ""
    if segmento not in SEGMENTOS:
        return "", modelo or segmento
    return segmento, modelo


def proximo_codigo_lead(ano):
    """LEAD_NNNN/aa com numeração contínua entre anos (regra do fluxo do n8n).

    Nunca volta abaixo de LOCAMAQ_LEAD_PISO, o último número já usado na planilha.
    """
    maior = settings.LOCAMAQ_LEAD_PISO
    for codigo in Lead.objects.values_list("codigo", flat=True):
        m = re.match(r"LEAD_(\d+)/", codigo)
        if m:
            maior = max(maior, int(m.group(1)))
    return f"LEAD_{maior + 1:04d}/{ano % 100:02d}"


class Atividade(models.Model):
    TIPOS = ["Nota", "Ligação", "E-mail", "Reunião", "Tarefa", "Mudança de etapa"]
    tipo = models.CharField("tipo", max_length=20, choices=_opcoes(TIPOS), default="Nota")
    assunto = models.CharField("assunto", max_length=160)
    descricao = models.TextField("descrição", blank=True)
    data = models.DateTimeField("registrada em", default=timezone.now)
    vencimento = models.DateField("vencimento (tarefas)", null=True, blank=True)
    concluida = models.BooleanField("concluída", default=False)
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="usuário"
    )
    lead = models.ForeignKey(Lead, on_delete=models.CASCADE, null=True, blank=True, related_name="atividades")
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, null=True, blank=True, related_name="atividades")
    contrato = models.ForeignKey(Contrato, on_delete=models.CASCADE, null=True, blank=True, related_name="atividades")
    equipamento = models.ForeignKey(
        Equipamento, on_delete=models.CASCADE, null=True, blank=True, related_name="atividades"
    )
    ordem_servico = models.ForeignKey(
        OrdemServico, on_delete=models.CASCADE, null=True, blank=True, related_name="atividades"
    )

    class Meta:
        ordering = ["-data"]
        verbose_name = "atividade"
        verbose_name_plural = "atividades"

    def __str__(self):
        return f"{self.tipo}: {self.assunto}"

    @property
    def registro(self):
        return self.lead or self.cliente or self.contrato or self.equipamento or self.ordem_servico
