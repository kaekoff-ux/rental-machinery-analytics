"""Telas, permissões por perfil e regras de negócio (sem senhas: os testes usam force_login)."""
import io
import json
from datetime import date, timedelta

from django.contrib.auth.models import Group, User
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.urls import reverse

from crm.models import Atividade, Cliente, Contrato, Equipamento, Fatura, Lead, OrdemServico


class Base(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("importar_base", stdout=io.StringIO())
        call_command("criar_perfis", stdout=io.StringIO())
        cls.gestor = User.objects.create_user("gestor", first_name="Gina", last_name="Gestora")
        cls.gestor.groups.add(Group.objects.get(name="Gestor"))
        cls.atendimento = User.objects.create_user("atendimento", first_name="Ana")
        cls.atendimento.groups.add(Group.objects.get(name="Atendimento"))
        cls.oficina = User.objects.create_user("oficina", first_name="Otto")
        cls.oficina.groups.add(Group.objects.get(name="Oficina"))


class Acesso(Base):
    def test_sem_login_vai_para_entrar(self):
        r = self.client.get(reverse("crm:leads"))
        self.assertEqual(r.status_code, 302)
        self.assertIn(reverse("login"), r["Location"])

    def test_pagina_de_login_abre(self):
        self.assertEqual(self.client.get(reverse("login")).status_code, 200)

    def test_todas_as_telas_abrem_para_o_gestor(self):
        self.client.force_login(self.gestor)
        lead = Lead.objects.first()
        urls = [
            reverse("crm:inicio"), reverse("crm:painel"), reverse("crm:busca") + "?q=CL-00",
            reverse("crm:leads"), reverse("crm:leads") + "?visao=abertos&status=Novo&o=-nome",
            reverse("crm:leads_kanban"), reverse("crm:lead_novo"), reverse("crm:lead", args=[lead.pk]),
            reverse("crm:lead_editar", args=[lead.pk]), reverse("crm:clientes"),
            reverse("crm:cliente", args=[Cliente.objects.first().pk]), reverse("crm:equipamentos") + "?situacao=Disponível",
            reverse("crm:equipamento", args=[Equipamento.objects.first().pk]), reverse("crm:contratos") + "?visao=atrasados",
            reverse("crm:contrato", args=[Contrato.objects.first().pk]), reverse("crm:oficina"), reverse("crm:ordens"),
            reverse("crm:os", args=[OrdemServico.objects.first().pk]), reverse("crm:faturas") + "?status=Vencido",
            reverse("crm:fatura", args=[Fatura.objects.first().pk]), reverse("crm:os_nova"), reverse("crm:contrato_novo"),
            reverse("crm:leitura_nova"), reverse("trocar_senha"),
        ]
        for url in urls:
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 200)

    def test_painel_entrega_os_dados(self):
        self.client.force_login(self.gestor)
        r = self.client.get(reverse("crm:painel"))
        self.assertContains(r, 'id="dados-painel"')
        self.assertContains(r, "painel_cowork.js")

    def test_atendimento_nao_cria_contrato(self):
        self.client.force_login(self.atendimento)
        self.assertEqual(self.client.get(reverse("crm:contrato_novo")).status_code, 403)
        self.assertEqual(self.client.get(reverse("crm:leads")).status_code, 200)

    def test_oficina_nao_ve_leads(self):
        self.client.force_login(self.oficina)
        self.assertEqual(self.client.get(reverse("crm:leads")).status_code, 403)
        self.assertEqual(self.client.get(reverse("crm:oficina")).status_code, 200)
        r = self.client.get(reverse("crm:inicio"))
        self.assertNotContains(r, f'href="{reverse("crm:leads")}"')

    def test_exportar_csv(self):
        self.client.force_login(self.gestor)
        r = self.client.get(reverse("crm:faturas") + "?status=Vencido&formato=csv")
        self.assertEqual(r["Content-Type"], "text/csv; charset=utf-8")
        texto = r.content.decode("utf-8-sig")
        self.assertEqual(texto.count("\n"), 1 + Fatura.objects.filter(status_pagamento="Vencido").count())


class Regras(Base):
    def setUp(self):
        self.client.force_login(self.gestor)

    def test_mudar_etapa_registra_atividade(self):
        lead = Lead.objects.filter(status="Novo").first()
        r = self.client.post(reverse("crm:lead_etapa", args=[lead.pk]), {"status": "Em Contato"})
        self.assertEqual(r.status_code, 302)
        lead.refresh_from_db()
        self.assertEqual(lead.status, "Em Contato")
        self.assertEqual(lead.responsavel, self.gestor)
        self.assertTrue(Atividade.objects.filter(lead=lead, tipo="Mudança de etapa", assunto="Novo → Em Contato").exists())

    def test_perdido_exige_motivo(self):
        lead = Lead.objects.filter(status="Orçado").first()
        r = self.client.post(reverse("crm:lead_etapa", args=[lead.pk]), {"status": "Perdidos"},
                             HTTP_ACCEPT="application/json")
        self.assertEqual(r.status_code, 400)
        r = self.client.post(reverse("crm:lead_etapa", args=[lead.pk]),
                             {"status": "Perdidos", "motivo_perda": "Indisponibilidade de máquina"},
                             HTTP_ACCEPT="application/json")
        self.assertEqual(json.loads(r.content)["status"], "Perdidos")
        lead.refresh_from_db()
        self.assertEqual(lead.motivo_perda, "Indisponibilidade de máquina")
        self.assertIsNotNone(lead.data_desfecho)

    def test_contrato_com_maquina_ocupada_e_recusado(self):
        ocupado = Contrato.objects.filter(status="Encerrado").first()
        dados = {
            "cliente": Cliente.objects.first().pk, "equipamento": ocupado.equipamento_id, "modalidade": "Diária",
            "data_inicio": ocupado.data_inicio.isoformat(), "data_fim_prevista": (ocupado.data_inicio + timedelta(days=3)).isoformat(),
            "valor_diaria": "500", "status": "Ativo",
        }
        if ocupado.equipamento.status_cadastro != "Ativo":
            self.skipTest("máquina fora da frota")
        r = self.client.post(reverse("crm:contrato_novo"), dados)
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "já está em contrato")

    def test_converter_lead_cria_cliente_e_contrato(self):
        lead = Lead.objects.create(nome="Construtora Teste Ltda", cidade="Campinas",
                                   equipamento_pedido="Gerador – Cummins C150D6", status="Orçado")
        livre = None
        inicio = date(2027, 3, 1)
        for eq in Equipamento.objects.filter(status_cadastro="Ativo", segmento="Gerador"):
            if not eq.contratos.exclude(status="Cancelado").filter(data_inicio__lte=inicio + timedelta(days=60)).exclude(
                    data_fim_prevista__lt=inicio).exists():
                livre = eq
                break
        self.assertIsNotNone(livre)
        r = self.client.post(reverse("crm:lead_converter", args=[lead.pk]), {
            "razao_social": "Construtora Teste Ltda", "equipamento": livre.pk, "modalidade": "Mensal",
            "data_inicio": inicio.isoformat(), "data_fim_prevista": (inicio + timedelta(days=60)).isoformat(),
            "valor_mensal": "42000", "obra_local": "Obra teste",
        })
        self.assertEqual(r.status_code, 302)
        lead.refresh_from_db()
        self.assertEqual(lead.status, "Fechado")
        self.assertEqual(lead.contrato.equipamento, livre)
        self.assertEqual(lead.cliente.razao_social, "Construtora Teste Ltda")
        self.assertTrue(lead.cliente.codigo.startswith("CL-"))
        self.assertEqual(lead.contrato.codigo, "CT-01246")

    def test_novo_lead_continua_a_numeracao(self):
        lead = Lead.objects.create(nome="Teste")
        self.assertEqual(lead.codigo.split("/")[0], "LEAD_0067")

    def test_pagar_fatura(self):
        f = Fatura.objects.filter(status_pagamento="Vencido").first()
        self.client.post(reverse("crm:fatura_pagar", args=[f.pk]))
        f.refresh_from_db()
        self.assertEqual(f.status_pagamento, "Pago")
        self.assertIsNotNone(f.data_pagamento)

    def test_mover_os_no_quadro(self):
        os_ = OrdemServico.objects.filter(status="Aberta").first()
        r = self.client.post(reverse("crm:os_status", args=[os_.pk]), {"status": "Em andamento"}, HTTP_ACCEPT="application/json")
        self.assertEqual(json.loads(r.content), {"ok": True, "status": "Em andamento"})

    def test_horimetro_nao_volta(self):
        eq = Equipamento.objects.filter(status_cadastro="Ativo").first()
        ultima = eq.leituras.order_by("-data_leitura").first()
        r = self.client.post(reverse("crm:leitura_nova"), {
            "equipamento": eq.pk, "data_leitura": (ultima.data_leitura + timedelta(days=1)).isoformat(),
            "horimetro_horas": str(ultima.horimetro_horas - 10), "fonte": "Manual",
        })
        self.assertContains(r, "Horímetro não volta")

    def test_atividade_e_tarefa(self):
        cliente = Cliente.objects.first()
        self.client.post(reverse("crm:atividade_nova"), {"alvo": f"cliente:{cliente.pk}", "tipo": "Tarefa",
                                                         "assunto": "Ligar para renovar", "vencimento": "2026-12-01"})
        t = Atividade.objects.get(assunto="Ligar para renovar")
        self.assertEqual(t.cliente, cliente)
        self.assertContains(self.client.get(reverse("crm:inicio")), "Ligar para renovar")


@override_settings(LOCAMAQ_API_TOKEN="chave-de-teste")
class ApiLeads(Base):
    url = "/api/leads/"

    def post(self, dados, chave="chave-de-teste"):
        return self.client.post(self.url, json.dumps(dados), content_type="application/json",
                                HTTP_AUTHORIZATION=f"Bearer {chave}")

    def test_chave_errada(self):
        self.assertEqual(self.post({"nome": "X"}, chave="errada").status_code, 401)

    @override_settings(LOCAMAQ_API_TOKEN="")
    def test_api_desligada_sem_chave(self):
        self.assertEqual(self.post({"nome": "X"}).status_code, 503)

    def test_cria_e_nao_duplica(self):
        dados = {"id_lead": "LEAD_0067/26", "data_envio": "07/11/2026 08:30:00", "nome": "Obra Real SA",
                 "contato": "compras@exemplo.example", "cidade": "Sorocaba",
                 "equipamento": "Escavadeira – Caterpillar 320GC", "prazo": "Mensal, 60 dias", "origem": "site",
                 "status": "Novo"}
        r = self.post(dados)
        self.assertEqual(r.status_code, 201)
        lead = Lead.objects.get(codigo="LEAD_0067/26")
        self.assertEqual((lead.segmento, lead.modelo), ("Escavadeira", "Caterpillar 320GC"))
        self.assertEqual(lead.data_envio.hour, 11)  # 08:30 em Brasília = 11:30 UTC
        r2 = self.post(dados)
        self.assertEqual(r2.status_code, 200)
        self.assertFalse(json.loads(r2.content)["criado"])
        self.assertEqual(Lead.objects.filter(codigo="LEAD_0067/26").count(), 1)

    def test_numero_repetido_de_outro_pedido_nao_some(self):
        manual = Lead.objects.create(nome="Lead criado à mão", contato="11 0000-0000")
        r = self.post({"id_lead": manual.codigo, "nome": "Pedido do site", "contato": "obra@exemplo.example"})
        self.assertEqual(r.status_code, 201)
        corpo = json.loads(r.content)
        self.assertNotEqual(corpo["id_lead"], manual.codigo)
        self.assertIn("aviso", corpo)
        self.assertTrue(Lead.objects.filter(nome="Pedido do site").exists())

    @override_settings(LOCAMAQ_API_TOKEN="", LOCAMAQ_API_REDE_INTERNA=True, LOCAMAQ_LEAD_PISO=80)
    def test_rede_interna_e_numero_gerado_pelo_sistema(self):
        dados = json.dumps({"nome": "Pedido pelo n8n", "data_envio": "09/11/2026 10:00:00"})
        r = self.client.post(self.url, dados, content_type="application/json")  # direto, sem chave
        self.assertEqual(r.status_code, 201)
        self.assertEqual(json.loads(r.content)["id_lead"], "LEAD_0081/26")
        # Pelo proxy (com X-Forwarded-For) é recusado, mesmo vindo de endereço privado.
        r = self.client.post(self.url, dados, content_type="application/json", HTTP_X_FORWARDED_FOR="203.0.113.9")
        self.assertEqual(r.status_code, 401)

    def test_json_invalido_e_sem_nome(self):
        r = self.client.post(self.url, "isso não é json", content_type="application/json",
                             HTTP_AUTHORIZATION="Bearer chave-de-teste")
        self.assertEqual(r.status_code, 400)
        self.assertEqual(self.post({"cidade": "X"}).status_code, 400)
