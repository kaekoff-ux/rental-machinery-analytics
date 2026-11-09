"""Importa a base fictícia (data/processed) para o banco do sistema.

Uso:
    python manage.py importar_base                 # cria só o que ainda não existe
    python manage.py importar_base --sobrescrever  # também atualiza os registros existentes

Lê os 6 CSVs de 2024-2025 e a extensão 2026 (contratos, faturas e leads). A chave de cada
registro é o código (CL-0001, EQ-0001, ...), então rodar de novo não duplica nada. Os 66 leads
históricos recebem LEAD_0001/26 a LEAD_0066/26 pela ordem da data de envio, e o primeiro lead
real do site continua sendo LEAD_0067/26.
"""
import csv
from datetime import date, datetime
from decimal import Decimal
from zoneinfo import ZoneInfo

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from crm.models import Cliente, Contrato, Equipamento, Fatura, Lead, LeituraHorimetro, OrdemServico, separar_equipamento

BRASILIA = ZoneInfo("America/Sao_Paulo")


def ler(caminho):
    with open(caminho, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f, delimiter=";"))


def dec(v):
    return Decimal(v) if v not in ("", None) else None


def dia(v):
    return date.fromisoformat(v) if v else None


class Command(BaseCommand):
    help = "Importa a base fictícia da LocaMaq (CSVs de data/processed) sem duplicar registros."

    def add_arguments(self, parser):
        parser.add_argument("--pasta", default=str(settings.LOCAMAQ_DADOS), help="Pasta data/processed.")
        parser.add_argument(
            "--sobrescrever", action="store_true", help="Atualiza registros existentes com os valores dos CSVs."
        )
        parser.add_argument(
            "--se-vazio", action="store_true", help="Só importa se o banco ainda não tem equipamentos (1ª subida)."
        )

    def handle(self, *args, **opts):
        from pathlib import Path

        if opts["se_vazio"] and Equipamento.objects.exists():
            self.stdout.write("Banco já tem dados: importação pulada.")
            return
        pasta = Path(opts["pasta"])
        ext = pasta / "extensao_2026"
        if not (pasta / "cadastro_equipamentos.csv").exists():
            raise CommandError(f"Não encontrei os CSVs em {pasta}")
        self.sobrescrever = opts["sobrescrever"]

        with transaction.atomic():
            self.clientes(ler(pasta / "clientes.csv"))
            self.equipamentos(ler(pasta / "cadastro_equipamentos.csv"))
            self.contratos(ler(pasta / "contratos_locacao.csv") + ler(ext / "contratos_locacao_2026.csv"))
            self.faturas(ler(pasta / "faturamento.csv") + ler(ext / "faturamento_2026.csv"))
            self.ordens(ler(pasta / "ordens_manutencao.csv"))
            self.leituras(ler(pasta / "horimetro_telemetria.csv"))
            self.leads(ler(ext / "leads_2026.csv"))

        for model in (Cliente, Equipamento, Contrato, Fatura, OrdemServico, LeituraHorimetro, Lead):
            self.stdout.write(f"{model._meta.verbose_name_plural}: {model.objects.count()}")

    # Grava em lote. Sem --sobrescrever, códigos já existentes ficam como estão.
    def gravar(self, model, objetos, campos):
        if self.sobrescrever:
            model.objects.bulk_create(
                objetos, batch_size=500, update_conflicts=True, unique_fields=["codigo"], update_fields=campos
            )
        else:
            model.objects.bulk_create(objetos, batch_size=500, ignore_conflicts=True)

    def mapa(self, model):
        return dict(model.objects.values_list("codigo", "pk"))

    def clientes(self, linhas):
        objs = [
            Cliente(
                codigo=r["id_cliente"],
                razao_social=r["razao_social"],
                cnpj=r["cnpj"],
                segmento=r["segmento_cliente"],
                cidade=r["cidade"],
                uf=r["uf"],
                limite_credito=dec(r["limite_credito"]),
                data_cadastro=dia(r["data_cadastro"]),
            )
            for r in linhas
        ]
        self.gravar(Cliente, objs, ["razao_social", "cnpj", "segmento", "cidade", "uf", "limite_credito", "data_cadastro"])

    def equipamentos(self, linhas):
        objs = [
            Equipamento(
                codigo=r["id_equipamento"],
                segmento=r["segmento"],
                fabricante=r["fabricante"],
                modelo=r["modelo"],
                ano_fabricacao=int(r["ano_fabricacao"]) if r["ano_fabricacao"] else None,
                numero_serie=r["numero_serie"],
                data_aquisicao=dia(r["data_aquisicao"]),
                valor_aquisicao=dec(r["valor_aquisicao"]),
                vida_util_horas=int(r["vida_util_horas"]),
                filial=r["filial"],
                status_cadastro=r["status_cadastro"],
            )
            for r in linhas
        ]
        self.gravar(
            Equipamento,
            objs,
            ["segmento", "fabricante", "modelo", "ano_fabricacao", "numero_serie", "data_aquisicao",
             "valor_aquisicao", "vida_util_horas", "filial", "status_cadastro"],
        )

    def contratos(self, linhas):
        cli, eq = self.mapa(Cliente), self.mapa(Equipamento)
        objs = [
            Contrato(
                codigo=r["id_contrato"],
                cliente_id=cli[r["id_cliente"]],
                equipamento_id=eq[r["id_equipamento"]],
                data_inicio=dia(r["data_inicio"]),
                data_fim_prevista=dia(r["data_fim_prevista"]),
                data_devolucao=dia(r["data_devolucao"]),
                modalidade=r["modalidade"],
                valor_diaria=dec(r["valor_diaria"]),
                valor_mensal=dec(r["valor_mensal"]),
                obra_local=r["obra_local"],
                status=r["status"],
            )
            for r in linhas
        ]
        self.gravar(
            Contrato,
            objs,
            ["cliente", "equipamento", "data_inicio", "data_fim_prevista", "data_devolucao", "modalidade",
             "valor_diaria", "valor_mensal", "obra_local", "status"],
        )

    def faturas(self, linhas):
        ct = self.mapa(Contrato)
        objs = [
            Fatura(
                codigo=r["id_fatura"],
                contrato_id=ct[r["id_contrato"]],
                competencia=r["competencia"],
                valor_faturado=dec(r["valor_faturado"]),
                data_emissao=dia(r["data_emissao"]),
                data_vencimento=dia(r["data_vencimento"]),
                data_pagamento=dia(r["data_pagamento"]),
                status_pagamento=r["status_pagamento"],
            )
            for r in linhas
        ]
        self.gravar(
            Fatura,
            objs,
            ["contrato", "competencia", "valor_faturado", "data_emissao", "data_vencimento", "data_pagamento",
             "status_pagamento"],
        )

    def ordens(self, linhas):
        eq = self.mapa(Equipamento)
        objs = [
            OrdemServico(
                codigo=r["id_os"],
                equipamento_id=eq[r["id_equipamento"]],
                tipo=r["tipo_manutencao"],
                data_abertura=dia(r["data_abertura"]),
                data_conclusao=dia(r["data_conclusao"]),
                horimetro_na_os=dec(r["horimetro_na_os"]),
                descricao=r["descricao_falha"],
                horas_parada=dec(r["horas_parada"]),
                custo_pecas=dec(r["custo_pecas"]) or 0,
                custo_mao_obra=dec(r["custo_mao_obra"]) or 0,
                status=r["status_os"],
            )
            for r in linhas
        ]
        self.gravar(
            OrdemServico,
            objs,
            ["equipamento", "tipo", "data_abertura", "data_conclusao", "horimetro_na_os", "descricao",
             "horas_parada", "custo_pecas", "custo_mao_obra", "status"],
        )

    def leituras(self, linhas):
        eq, ct = self.mapa(Equipamento), self.mapa(Contrato)
        objs = [
            LeituraHorimetro(
                codigo=r["id_leitura"],
                equipamento_id=eq[r["id_equipamento"]],
                data_leitura=dia(r["data_leitura"]),
                horimetro_horas=dec(r["horimetro_horas"]),
                fonte=r["fonte_leitura"],
                contrato_id=ct.get(r["id_contrato"]) if r["id_contrato"] else None,
            )
            for r in linhas
        ]
        self.gravar(LeituraHorimetro, objs, ["equipamento", "data_leitura", "horimetro_horas", "fonte", "contrato"])

    def leads(self, linhas):
        ct = dict(Contrato.objects.values_list("codigo", "pk"))
        cliente_do_contrato = dict(Contrato.objects.values_list("codigo", "cliente_id"))
        linhas = sorted(linhas, key=lambda r: r["data_envio"])
        objs = []
        for n, r in enumerate(linhas, start=1):
            envio = datetime.fromisoformat(r["data_envio"]).replace(tzinfo=BRASILIA)
            seg, mod = separar_equipamento(r["equipamento"])
            objs.append(
                Lead(
                    codigo=f"LEAD_{n:04d}/{envio.year % 100:02d}",
                    data_envio=envio,
                    nome=r["nome"],
                    contato=r["contato"],
                    cidade=r["cidade"],
                    equipamento_pedido=r["equipamento"],
                    segmento=seg,
                    modelo=mod,
                    prazo=r["prazo"],
                    inicio_pretendido=dia(r["inicio_pretendido"]),
                    observacao=r["observacao"],
                    origem=r["origem"],
                    status=r["status"],
                    data_desfecho=dia(r["data_desfecho"]),
                    motivo_perda=r["motivo_perda"],
                    contrato_id=ct.get(r["id_contrato"]),
                    cliente_id=cliente_do_contrato.get(r["id_contrato"]),
                )
            )
        self.gravar(
            Lead,
            objs,
            ["data_envio", "nome", "contato", "cidade", "equipamento_pedido", "segmento", "modelo", "prazo",
             "inicio_pretendido", "observacao", "origem", "status", "data_desfecho", "motivo_perda", "contrato",
             "cliente"],
        )
