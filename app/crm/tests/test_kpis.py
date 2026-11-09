"""Os números do Painel precisam bater com o dashboard do Cowork (CSVs em referencia_cowork/)."""
import csv
import io
from pathlib import Path

from django.core.management import call_command
from django.test import TestCase

from crm import kpis
from crm.models import Cliente, Contrato, Equipamento, Fatura, Lead, LeituraHorimetro, OrdemServico

REF = Path(__file__).parent / "referencia_cowork"


def ler(nome):
    with open(REF / nome, encoding="utf-8") as f:
        return list(csv.DictReader(f))


class ImportacaoEIndicadores(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("importar_base", stdout=io.StringIO())
        cls.em = kpis.equip_mes()

    def test_contagens_da_importacao(self):
        self.assertEqual(Cliente.objects.count(), 70)
        self.assertEqual(Equipamento.objects.count(), 135)
        self.assertEqual(Contrato.objects.count(), 1210 + 35)
        self.assertEqual(Fatura.objects.count(), 2487 + 76)
        self.assertEqual(OrdemServico.objects.count(), 3922)
        self.assertEqual(LeituraHorimetro.objects.count(), 11792)
        self.assertEqual(Lead.objects.count(), 66)
        self.assertEqual(Lead.objects.order_by("data_envio").first().codigo, "LEAD_0001/26")
        self.assertEqual(Lead.objects.order_by("data_envio").last().codigo, "LEAD_0066/26")

    def test_reimportar_nao_duplica(self):
        call_command("importar_base", stdout=io.StringIO())
        self.assertEqual(Contrato.objects.count(), 1245)
        self.assertEqual(Lead.objects.count(), 66)

    def _comparar(self, nossos, ref, chave, colunas):
        por = {r[chave]: r for r in ref}
        self.assertEqual(len(nossos), len(por))
        for linha in nossos:
            esperado = por[str(linha[chave])]
            for c in colunas:
                if esperado[c] == "":
                    continue
                self.assertAlmostEqual(float(linha[c] or 0), float(esperado[c]), delta=0.02 + 1e-6 * abs(float(esperado[c])),
                                       msg=f"{chave}={linha[chave]} coluna {c}")

    def test_mensal_igual_ao_cowork(self):
        colunas = [c for c in kpis.METRICAS if c not in ("vencido", "atraso_soma", "atraso_n")]
        self._comparar(kpis.mensal(self.em), ler("mensal.csv"), "mes", colunas)

    def test_segmentos_igual_ao_cowork(self):
        colunas = ["equipamentos"] + [c for c in kpis.METRICAS if c not in ("vencido", "atraso_soma", "atraso_n")]
        self._comparar(kpis.segmentos(self.em), ler("segmentos_2025.csv"), "segmento", colunas)

    def test_faturas_igual_ao_cowork(self):
        self._comparar(kpis.faturas_ano(), ler("faturas_ano.csv"), "ano",
                       ["faturado", "vencido_aberto", "a_vencer", "faturas", "faturas_pagas", "atraso_medio_dias"])

    def test_leads_igual_ao_cowork(self):
        status, motivo, origem = kpis.leads_resumo(kpis.leads_det(2026))
        self._comparar(status, ler("leads_status.csv"), "status", ["leads", "tempo_medio_fechamento_dias"])
        self._comparar(motivo, ler("leads_motivo.csv"), "motivo", ["leads"])
        self._comparar(origem, ler("leads_origem.csv"), "origem", ["leads", "fechados", "perdidos"])

    def test_receita_2025(self):
        receita = sum(r["receita"] for r in self.em if r["mes"].startswith("2025"))
        self.assertAlmostEqual(receita, 24_019_030.0, places=2)
