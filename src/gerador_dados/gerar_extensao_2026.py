"""Gera a EXTENSAO 2026 da base da LocaMaq (dados 100% ficticios): contratos fechados, faturas
e leads (ganhos, perdidos e em aberto) de janeiro a novembro de 2026.

Por que separado: os 6 CSVs da base cobrem 2024-2025 (a janela de historico do projeto) e os
numeros do site e o Power BI ja dependem deles. A extensao NAO altera nenhum deles: grava
arquivos novos em data/processed/extensao_2026/ (somente versao limpa, sem raw). No Power BI,
acrescente com "Anexar consultas".

Depende de (processed): cadastro_equipamentos, clientes, contratos_locacao, ordens_manutencao e
faturamento. Rode os geradores anteriores primeiro. NAO use "python -I": este script importa
funcoes dos geradores vizinhos (mesma pasta).

Saidas (data/processed/extensao_2026/):
    contratos_locacao_2026.csv   mesmas colunas de contratos_locacao.csv; ids a partir de CT-01211
    faturamento_2026.csv         mesmas colunas de faturamento.csv; ids a partir de FT-002488
    leads_2026.csv               leads para a planilha "LocaMaq - Leads" (colunas na docstring abaixo)
    leads_2026_planilha.csv      o mesmo, pronto para importar na planilha (sem cabeçalho, datas dd/mm/aaaa)

Como rodar, a partir da raiz do repositorio:
    python src/gerador_dados/gerar_extensao_2026.py

Reprodutibilidade: seed fixa (42); a mesma execucao gera os mesmos arquivos.

Logica
------
"Hoje" da extensao = 2026-11-05. Contratos novos so entram se a maquina estiver livre:
  - cadastro com status_cadastro = Ativo e ja adquirida;
  - sem sobreposicao (folga de 3 dias, como o gerador original) com nenhum contrato da base nem
    com outro contrato novo;
  - fora das OS que estavam Aberta/Em andamento no fim de 2025 (assume-se oficina ate 20/01/2026);
  - contratos "Ativo" no fim de 2025 tinham fim previsto cortado em 31/12/2025 pelo gerador;
    assume-se que seguem com a maquina ate 31/01/2026.
Em cada categoria (segmento) escolhe-se o modelo com MENOS unidades ativas e ocupam-se TODAS
elas, ao mesmo tempo, em uma janela de 2026: sao os contratos "de ocupacao" (contam entre os 5
fechados da categoria). Dois leads sao PERDIDOS por indisponibilidade dentro dessa janela - cada
um pede o modelo numa data em que todas as unidades estao alugadas (o script confere isso, e
tests/conferir_extensao_2026.py confere de novo, de forma independente).

Faturas: mesma regra do gerador original (Mensal = 1 por mes de duracao; Semanal/Diaria = 1 no
fim do contrato), mas so existem as ja emitidas ate "hoje"; o status de pagamento e decidido
contra "hoje".

NAO gerados em 2026 (fora do pedido): telemetria de horimetro, ordens de manutencao e a
inspecao automatica em cada devolucao. Por isso a disponibilidade em 2026 considera so os
contratos e as OS abertas no fim de 2025.

O que e da base e o que e inventado nos leads
  da base (contrato fechado): nome (razao social), cidade, equipamento, prazo, obra, valor, id.
  inventado: contato (e-mail em .example, que nao existe, ou telefone invalido), origem, datas
  do lead e do desfecho, os leads perdidos e os em aberto, e os motivos de perda.
Toda observacao dos leads comeca com "[historico ficticio]" para separar das linhas reais.

Colunas de leads_2026.csv: data_envio (aaaa-mm-dd hh:mm:ss), nome, contato, cidade, equipamento,
prazo, observacao, origem, status (Novo/Em Contato/Orcado/Fechado/Perdidos, como na lista da
planilha), data_desfecho (aaaa-mm-dd), id_contrato, motivo_perda, inicio_pretendido (aaaa-mm-dd).
As 3 ultimas servem ao indicador e a auditoria; inicio_pretendido nao vai para a planilha.
"""
import csv
import random
import re
import unicodedata
from collections import defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path

from gerar_contratos_locacao import (
    DURACAO_DIAS,
    MODALIDADES,
    OBRA_NOMES,
    OBRA_PREFIXOS,
    calcular_valores,
    carregar_csv,
    sortear_data_devolucao,
)
from gerar_faturamento import (
    COMPORTAMENTO_PAGAMENTO,
    PRAZO_VENCIMENTO_CURTO,
    PRAZO_VENCIMENTO_MENSAL,
    adicionar_meses,
)
from utils import formatar_real, gravar_csv, sortear_ponderado

SEED = 42

HOJE = date(2026, 11, 5)
FIM_ATIVOS_2025 = date(2026, 1, 31)   # contratos "Ativo" no fim de 2025 seguem com a maquina ate aqui
FIM_OS_ABERTAS = date(2026, 1, 20)    # OS abertas no fim de 2025 liberam a maquina ate aqui
FOLGA = 3                             # dias entre contratos da mesma maquina (como no original)
PRIMEIRO_INICIO = date(2026, 1, 12)   # primeiro inicio de contrato novo
ULTIMO_INICIO = HOJE - timedelta(days=20)

RAIZ = Path(__file__).resolve().parents[2]
PROCESSED = RAIZ / "data" / "processed"
PASTA_SAIDA = PROCESSED / "extensao_2026"

COLUNAS_CONTRATOS = [
    "id_contrato", "id_cliente", "id_equipamento", "data_inicio", "data_fim_prevista",
    "data_devolucao", "modalidade", "valor_diaria", "valor_mensal", "obra_local", "status",
]
COLUNAS_FATURAS = [
    "id_fatura", "id_contrato", "competencia", "valor_faturado", "data_emissao",
    "data_vencimento", "data_pagamento", "status_pagamento",
]
COLUNAS_LEADS = [
    "data_envio", "nome", "contato", "cidade", "equipamento", "prazo", "observacao", "origem",
    "status", "data_desfecho", "id_contrato", "motivo_perda", "inicio_pretendido",
]

FECHADOS_POR_CATEGORIA = 5
PERDIDOS_OUTROS_POR_CATEGORIA = 1     # alem dos 2 por indisponibilidade
LEADS_ABERTOS = [("Novo", 4), ("Em Contato", 3), ("Orçado", 3)]

# Mes da janela de "todas as unidades alugadas" de cada categoria (espalha as perdas pelo ano).
MES_JANELA = {
    "Guindaste": 2, "Plataforma elevatória": 3, "Escavadeira": 4, "Retroescavadeira": 5,
    "Gerador": 6, "Pá-carregadeira": 7, "Empilhadeira": 8,
}

ORIGENS = [("site", 50), ("whatsapp", 20), ("telegram", 10), ("telefone", 10), ("indicação", 10)]

MOTIVO_INDISPONIVEL = "Indisponibilidade de máquina"
MOTIVOS_OUTROS = [
    ("Preço acima do concorrente", "Cliente achou o valor acima da proposta de outra locadora."),
    ("Fechou com concorrente", "Cliente fechou com outra locadora."),
    ("Obra adiada pelo cliente", "Cliente adiou o início da obra."),
    ("Cliente sem retorno", "Cliente não respondeu aos contatos."),
    ("Crédito não aprovado", "Análise de crédito não aprovou a locação."),
]
OBS_ABERTOS = {
    "Novo": "Pedido recebido, ainda sem contato.",
    "Em Contato": "Cliente contatado, levantando os dados da obra.",
    "Orçado": "Orçamento enviado, aguardando aprovação do cliente.",
}

DDD = {
    "São Paulo": "11", "Jundiaí": "11", "Campinas": "19", "Sorocaba": "15",
    "Ribeirão Preto": "16", "São José dos Campos": "12", "Belo Horizonte": "31",
    "Rio de Janeiro": "21", "Curitiba": "41",
}
MARCA = "[histórico fictício]"


# --- Utilitários ---------------------------------------------------------------------------
def so_ascii(texto):
    base = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9]+", "-", base.lower()).strip("-")


def numero_do_id(id_texto):
    return int(re.search(r"(\d+)$", id_texto).group(1))


def nome_equipamento(eq):
    return f"{eq['segmento']} – {eq['fabricante']} {eq['modelo']}"


def hora_aleatoria(rng, dia):
    return datetime(dia.year, dia.month, dia.day, rng.randint(7, 18), rng.randint(0, 59), rng.randint(0, 59))


def dmy(dia):
    return dia.strftime("%d/%m/%Y")


# --- Ocupação das máquinas ---------------------------------------------------------------
def montar_ocupacao(contratos, ordens):
    """{id_equipamento: [(inicio, fim, referencia)]} com tudo que ocupa a máquina a partir de 2026."""
    ocupacao = defaultdict(list)
    for contrato in contratos:
        if contrato["status"] == "Cancelado":
            continue
        inicio = date.fromisoformat(contrato["data_inicio"])
        if contrato["status"] == "Ativo":
            fim = FIM_ATIVOS_2025
        else:
            fim = date.fromisoformat(contrato["data_devolucao"] or contrato["data_fim_prevista"])
        ocupacao[contrato["id_equipamento"]].append((inicio, fim, contrato["id_contrato"]))
    for ordem in ordens:
        if ordem["status_os"] in ("Aberta", "Em andamento"):
            ocupacao[ordem["id_equipamento"]].append(
                (date.fromisoformat(ordem["data_abertura"]), FIM_OS_ABERTAS, ordem["id_os"])
            )
    return ocupacao


def maquina_livre(ocupacao, id_equipamento, inicio, fim):
    for inicio_ocupado, fim_ocupado, _ in ocupacao[id_equipamento]:
        if inicio <= fim_ocupado + timedelta(days=FOLGA) and fim + timedelta(days=FOLGA) >= inicio_ocupado:
            return False
    return True


# --- Contratos -----------------------------------------------------------------------------
def criar_contrato(rng, equipamento, clientes, inicio, modalidade, duracao):
    fim_prevista = inicio + timedelta(days=duracao)
    cliente = rng.choice(clientes)
    valor_diaria, valor_mensal = calcular_valores(rng, modalidade, float(equipamento["valor_aquisicao"]))
    obra_local = f"{rng.choice(OBRA_PREFIXOS)} {rng.choice(OBRA_NOMES)}"
    if fim_prevista >= HOJE - timedelta(days=5):
        status, devolucao, fim_efetivo = "Ativo", None, fim_prevista
    else:
        status = "Encerrado"
        devolucao = sortear_data_devolucao(rng, fim_prevista)
        devolucao = max(inicio + timedelta(days=1), min(devolucao, HOJE - timedelta(days=1)))
        fim_efetivo = devolucao
    return {
        "id_cliente": cliente["id_cliente"],
        "id_equipamento": equipamento["id_equipamento"],
        "data_inicio": inicio,
        "data_fim_prevista": fim_prevista,
        "data_devolucao": devolucao,
        "modalidade": modalidade,
        "valor_diaria": valor_diaria,
        "valor_mensal": valor_mensal,
        "obra_local": obra_local,
        "status": status,
        "fim_efetivo": fim_efetivo,
        "categoria": equipamento["segmento"],
    }


def registrar(ocupacao, contrato):
    ocupacao[contrato["id_equipamento"]].append(
        (contrato["data_inicio"], contrato["fim_efetivo"], contrato)
    )


def gerar_contratos_categoria(rng, segmento, unidades_ativas, clientes, ocupacao):
    """Retorna (contratos, janela) da categoria; janela descreve o período 'todas alugadas'."""
    por_modelo = defaultdict(list)
    for eq in unidades_ativas:
        por_modelo[(eq["fabricante"], eq["modelo"])].append(eq)
    # Modelo escasso: o de menos unidades (empate: ordem alfabética, para ser determinístico).
    chave_escasso = sorted(por_modelo, key=lambda chave: (len(por_modelo[chave]), chave))[0]
    unidades_escasso = sorted(por_modelo[chave_escasso], key=lambda eq: eq["id_equipamento"])

    for _ in range(300):
        ancora = date(2026, MES_JANELA[segmento], rng.randint(3, 10))
        planejados = []
        for indice, equipamento in enumerate(unidades_escasso):
            inicio = ancora + timedelta(days=indice * rng.randint(0, 3))
            planejados.append(criar_contrato(rng, equipamento, clientes, inicio, "Mensal", rng.randint(70, 110)))
        comum_inicio = max(c["data_inicio"] for c in planejados)
        comum_fim = min(c["fim_efetivo"] for c in planejados)
        if (comum_fim - comum_inicio).days < 25:
            continue
        if not all(
            maquina_livre(ocupacao, c["id_equipamento"], c["data_inicio"], c["fim_efetivo"]) for c in planejados
        ):
            continue
        break
    else:
        raise RuntimeError(f"Não achei janela livre para {segmento}")

    contratos = list(planejados)
    for contrato in contratos:
        registrar(ocupacao, contrato)

    outras = [eq for eq in unidades_ativas if (eq["fabricante"], eq["modelo"]) != chave_escasso]
    tentativas = 0
    while len(contratos) < FECHADOS_POR_CATEGORIA:
        tentativas += 1
        if tentativas > 2000:
            raise RuntimeError(f"Não consegui contratos livres para {segmento}")
        equipamento = rng.choice(outras)
        modalidade = sortear_ponderado(rng, MODALIDADES)
        duracao = rng.randint(*DURACAO_DIAS[modalidade])
        inicio = PRIMEIRO_INICIO + timedelta(days=rng.randint(0, (ULTIMO_INICIO - PRIMEIRO_INICIO).days))
        if date.fromisoformat(equipamento["data_aquisicao"]) > inicio:
            continue
        candidato = criar_contrato(rng, equipamento, clientes, inicio, modalidade, duracao)
        if not maquina_livre(ocupacao, candidato["id_equipamento"], candidato["data_inicio"], candidato["fim_efetivo"]):
            continue
        contratos.append(candidato)
        registrar(ocupacao, candidato)

    janela = {
        "segmento": segmento,
        "fabricante": chave_escasso[0],
        "modelo": chave_escasso[1],
        "unidades": [eq["id_equipamento"] for eq in unidades_escasso],
        "inicio": comum_inicio,
        "fim": comum_fim,
        "contratos": planejados,
    }
    return contratos, janela


# --- Faturas -------------------------------------------------------------------------------
def sortear_pagamento(rng, data_vencimento):
    """Mesma lógica do gerador original, contra o 'hoje' da extensão."""
    sorteio = rng.random()
    acumulado = 0.0
    atraso_intervalo = None
    for probabilidade, intervalo in COMPORTAMENTO_PAGAMENTO:
        acumulado += probabilidade
        if sorteio < acumulado:
            atraso_intervalo = intervalo
            break
    data_pagamento = None
    if atraso_intervalo is not None:
        data_pagamento = data_vencimento + timedelta(days=rng.randint(*atraso_intervalo))
    if data_pagamento is not None and data_pagamento <= HOJE:
        return "Pago", data_pagamento
    if data_vencimento < HOJE:
        return "Vencido", None
    return "Em aberto", None


def gerar_faturas_contrato(rng, contrato):
    inicio = contrato["data_inicio"]
    fim = contrato["data_devolucao"] or contrato["data_fim_prevista"]
    faturas = []
    if contrato["modalidade"] == "Mensal":
        duracao = max((fim - inicio).days, 1)
        meses = max(round(duracao / 30), 1)
        for indice in range(meses):
            periodo = adicionar_meses(inicio, indice)
            emissao = adicionar_meses(inicio, indice + 1) + timedelta(days=rng.randint(0, 5))
            vencimento = emissao + timedelta(days=rng.randint(*PRAZO_VENCIMENTO_MENSAL))
            status, pagamento = sortear_pagamento(rng, vencimento)
            if emissao > HOJE:
                continue  # fatura ainda não emitida
            faturas.append({
                "id_contrato": contrato["id_contrato"],
                "competencia": date(periodo.year, periodo.month, 1),
                "valor_faturado": round(contrato["valor_mensal"], 2),
                "data_emissao": emissao, "data_vencimento": vencimento,
                "data_pagamento": pagamento, "status_pagamento": status,
            })
    else:
        duracao = max((fim - inicio).days, 1)
        emissao = fim + timedelta(days=rng.randint(0, 5))
        vencimento = emissao + timedelta(days=rng.randint(*PRAZO_VENCIMENTO_CURTO))
        status, pagamento = sortear_pagamento(rng, vencimento)
        if contrato["status"] == "Encerrado" and emissao <= HOJE:  # Ativo ainda não devolveu: sem fatura final
            faturas.append({
                "id_contrato": contrato["id_contrato"],
                "competencia": date(inicio.year, inicio.month, 1),
                "valor_faturado": round(contrato["valor_diaria"] * duracao, 2),
                "data_emissao": emissao, "data_vencimento": vencimento,
                "data_pagamento": pagamento, "status_pagamento": status,
            })
    return faturas


# --- Leads ---------------------------------------------------------------------------------
class Contatos:
    """Um contato fictício por cliente (e-mail em .example ou telefone inválido), sempre o mesmo."""

    def __init__(self, rng):
        self.rng = rng
        self.por_cliente = {}

    def obter(self, cliente):
        if cliente["id_cliente"] not in self.por_cliente:
            if self.rng.random() < 0.7:
                prefixo = self.rng.choice(["compras", "obras", "contato", "engenharia"])
                valor = f"{prefixo}@{so_ascii(cliente['razao_social'])[:28].strip('-')}.example"
            else:
                ddd = DDD.get(cliente["cidade"], "11")
                valor = f"({ddd}) 00000-{self.rng.randint(0, 9999):04d}"  # começa com 0: número inexistente
            self.por_cliente[cliente["id_cliente"]] = valor
        return self.por_cliente[cliente["id_cliente"]]


def sortear_prazo(rng):
    modalidade = sortear_ponderado(rng, MODALIDADES)
    return modalidade, rng.randint(*DURACAO_DIAS[modalidade])


def montar_leads(rng, contratos, janelas, clientes, clientes_por_id, equipamentos_por_id, ativos_por_segmento):
    contatos = Contatos(rng)
    leads = []

    def novo_lead(cliente, equipamento_texto, prazo, observacao, status, envio, desfecho="",
                  id_contrato="", motivo="", inicio_pretendido=""):
        leads.append({
            "data_envio": envio.strftime("%Y-%m-%d %H:%M:%S"),
            "nome": cliente["razao_social"],
            "contato": contatos.obter(cliente),
            "cidade": cliente["cidade"],
            "equipamento": equipamento_texto,
            "prazo": prazo,
            "observacao": f"{MARCA} {observacao}",
            "origem": sortear_ponderado(rng, ORIGENS),
            "status": status,
            "data_desfecho": desfecho.isoformat() if desfecho else "",
            "id_contrato": id_contrato,
            "motivo_perda": motivo,
            "inicio_pretendido": inicio_pretendido.isoformat() if inicio_pretendido else "",
        })

    # Ganhos: um lead para cada contrato novo.
    for contrato in contratos:
        cliente = clientes_por_id[contrato["id_cliente"]]
        equipamento = equipamentos_por_id[contrato["id_equipamento"]]
        dias = (contrato["data_fim_prevista"] - contrato["data_inicio"]).days
        defasagem = min(rng.randint(5, 20), (contrato["data_inicio"] - date(2026, 1, 2)).days)
        envio_dia = contrato["data_inicio"] - timedelta(days=defasagem)
        desfecho = max(contrato["data_inicio"] - timedelta(days=rng.randint(0, 3)), envio_dia + timedelta(days=2))
        valor = (f"{formatar_real(contrato['valor_mensal'])}/mês" if contrato["valor_mensal"] is not None
                 else f"{formatar_real(contrato['valor_diaria'])}/dia")
        novo_lead(
            cliente, nome_equipamento(equipamento), f"{contrato['modalidade']}, {dias} dias",
            f"Contrato {contrato['id_contrato']} fechado. {contrato['obra_local']}. {valor}.",
            "Fechado", hora_aleatoria(rng, envio_dia), desfecho, contrato["id_contrato"],
            inicio_pretendido=contrato["data_inicio"],
        )

    # Perdidos por indisponibilidade: dentro da janela em que TODAS as unidades do modelo estão alugadas.
    for janela in janelas:
        comprimento = (janela["fim"] - janela["inicio"]).days
        primeiro = janela["inicio"] + timedelta(days=max(6, int(comprimento * 0.25)))
        segundo = janela["inicio"] + timedelta(days=max((primeiro - janela["inicio"]).days + 4, int(comprimento * 0.55)))
        referencias = ", ".join(sorted(c["id_contrato"] for c in janela["contratos"]))
        rotulo = f"{janela['fabricante']} {janela['modelo']}"
        for pretendido in (primeiro, segundo):
            assert pretendido + timedelta(days=8) <= janela["fim"], "janela curta demais"
            envio_dia = pretendido - timedelta(days=rng.randint(2, 5))
            assert envio_dia >= janela["inicio"], "lead antes da janela"
            modalidade, dias = sortear_prazo(rng)
            quantas = len(janela["unidades"])
            if quantas == 1:
                sujeito, participio = "a única unidade", "locada"
            else:
                sujeito, participio = f"as {quantas} unidades", "locadas"
            novo_lead(
                rng.choice(clientes), f"{janela['segmento']} – {rotulo}", f"{modalidade}, {dias} dias",
                f"Sem unidade disponível: {sujeito} do {rotulo} {participio} de {dmy(janela['inicio'])} "
                f"a {dmy(janela['fim'])} ({referencias}). Pretendia iniciar em {dmy(pretendido)}.",
                "Perdidos", hora_aleatoria(rng, envio_dia),
                envio_dia + timedelta(days=rng.randint(1, 3)), "", MOTIVO_INDISPONIVEL,
                inicio_pretendido=pretendido,
            )

    # Perdidos por outros motivos: 1 por categoria.
    for segmento in MES_JANELA:
        for _ in range(PERDIDOS_OUTROS_POR_CATEGORIA):
            equipamento = rng.choice(ativos_por_segmento[segmento])
            motivo, detalhe = rng.choice(MOTIVOS_OUTROS)
            modalidade, dias = sortear_prazo(rng)
            envio_dia = date(2026, 1, 5) + timedelta(days=rng.randint(0, (HOJE - timedelta(days=30) - date(2026, 1, 5)).days))
            novo_lead(
                rng.choice(clientes), nome_equipamento(equipamento), f"{modalidade}, {dias} dias", detalhe,
                "Perdidos", hora_aleatoria(rng, envio_dia), envio_dia + timedelta(days=rng.randint(2, 12)),
                "", motivo, inicio_pretendido=envio_dia + timedelta(days=rng.randint(5, 15)),
            )

    # Em aberto (últimas semanas antes de "hoje").
    categorias = list(MES_JANELA)
    posicao = 0
    for status, quantidade in LEADS_ABERTOS:
        for _ in range(quantidade):
            equipamento = rng.choice(ativos_por_segmento[categorias[posicao % len(categorias)]])
            posicao += 1
            modalidade, dias = sortear_prazo(rng)
            recuo = {"Novo": (0, 3), "Em Contato": (3, 10), "Orçado": (6, 20)}[status]
            envio_dia = HOJE - timedelta(days=rng.randint(*recuo))
            novo_lead(
                rng.choice(clientes), nome_equipamento(equipamento), f"{modalidade}, {dias} dias",
                OBS_ABERTOS[status], status, min(hora_aleatoria(rng, envio_dia), datetime(2026, 11, 5, 9, 0, 0)),
            )

    leads.sort(key=lambda lead: lead["data_envio"])
    return leads


def gravar_leads_para_planilha(caminho, leads):
    """Arquivo para Arquivo > Importar > Anexar na planilha 'LocaMaq - Leads': sem cabeçalho, na ordem das
    colunas da aba (A a L), datas como dd/mm/aaaa (o Sheets em português lê como data), vírgula e aspas
    onde precisar, UTF-8 sem BOM. Não leva inicio_pretendido (só serve à auditoria)."""
    colunas = COLUNAS_LEADS[:-1]
    with open(caminho, "w", encoding="utf-8", newline="") as arquivo:
        escritor = csv.writer(arquivo, delimiter=",", lineterminator="\n")
        for lead in leads:
            linha = dict(lead)
            envio = datetime.strptime(lead["data_envio"], "%Y-%m-%d %H:%M:%S")
            linha["data_envio"] = envio.strftime("%d/%m/%Y %H:%M:%S")
            if lead["data_desfecho"]:
                linha["data_desfecho"] = dmy(date.fromisoformat(lead["data_desfecho"]))
            escritor.writerow([linha[coluna] for coluna in colunas])


# --- Principal ------------------------------------------------------------------------------
def main():
    rng = random.Random(SEED)

    equipamentos = carregar_csv(PROCESSED / "cadastro_equipamentos.csv")
    clientes = carregar_csv(PROCESSED / "clientes.csv")
    contratos_base = carregar_csv(PROCESSED / "contratos_locacao.csv")
    ordens = carregar_csv(PROCESSED / "ordens_manutencao.csv")
    faturas_base = carregar_csv(PROCESSED / "faturamento.csv")

    equipamentos_por_id = {eq["id_equipamento"]: eq for eq in equipamentos}
    clientes_por_id = {c["id_cliente"]: c for c in clientes}
    ativos_por_segmento = defaultdict(list)
    for eq in sorted(equipamentos, key=lambda e: e["id_equipamento"]):
        if eq["status_cadastro"] == "Ativo":
            ativos_por_segmento[eq["segmento"]].append(eq)
    assert set(ativos_por_segmento) == set(MES_JANELA), "categorias do cadastro mudaram"

    ocupacao = montar_ocupacao(contratos_base, ordens)

    contratos, janelas = [], []
    for segmento in MES_JANELA:
        novos, janela = gerar_contratos_categoria(rng, segmento, ativos_por_segmento[segmento], clientes, ocupacao)
        contratos.extend(novos)
        janelas.append(janela)

    # Ids em ordem cronológica (a base original embaralha; aqui a ordem ajuda a conferir).
    contratos.sort(key=lambda c: (c["data_inicio"], c["id_equipamento"]))
    proximo = max(numero_do_id(c["id_contrato"]) for c in contratos_base) + 1
    for contrato in contratos:
        contrato["id_contrato"] = f"CT-{proximo:05d}"
        proximo += 1

    faturas = []
    for contrato in contratos:
        faturas.extend(gerar_faturas_contrato(rng, contrato))
    faturas.sort(key=lambda f: (f["data_emissao"], f["id_contrato"]))
    proxima_fatura = max(numero_do_id(f["id_fatura"]) for f in faturas_base) + 1
    for fatura in faturas:
        fatura["id_fatura"] = f"FT-{proxima_fatura:06d}"
        proxima_fatura += 1

    leads = montar_leads(rng, contratos, janelas, clientes, clientes_por_id, equipamentos_por_id, ativos_por_segmento)

    contratos_csv = [{
        "id_contrato": c["id_contrato"], "id_cliente": c["id_cliente"], "id_equipamento": c["id_equipamento"],
        "data_inicio": c["data_inicio"].isoformat(), "data_fim_prevista": c["data_fim_prevista"].isoformat(),
        "data_devolucao": "" if c["data_devolucao"] is None else c["data_devolucao"].isoformat(),
        "modalidade": c["modalidade"],
        "valor_diaria": "" if c["valor_diaria"] is None else f"{c['valor_diaria']:.2f}",
        "valor_mensal": "" if c["valor_mensal"] is None else f"{c['valor_mensal']:.2f}",
        "obra_local": c["obra_local"], "status": c["status"],
    } for c in contratos]
    faturas_csv = [{
        "id_fatura": f["id_fatura"], "id_contrato": f["id_contrato"],
        "competencia": f["competencia"].strftime("%Y-%m"), "valor_faturado": f"{f['valor_faturado']:.2f}",
        "data_emissao": f["data_emissao"].isoformat(), "data_vencimento": f["data_vencimento"].isoformat(),
        "data_pagamento": "" if f["data_pagamento"] is None else f["data_pagamento"].isoformat(),
        "status_pagamento": f["status_pagamento"],
    } for f in faturas]

    PASTA_SAIDA.mkdir(parents=True, exist_ok=True)
    gravar_csv(PASTA_SAIDA / "contratos_locacao_2026.csv", COLUNAS_CONTRATOS, contratos_csv)
    gravar_csv(PASTA_SAIDA / "faturamento_2026.csv", COLUNAS_FATURAS, faturas_csv)
    gravar_csv(PASTA_SAIDA / "leads_2026.csv", COLUNAS_LEADS, leads)
    gravar_leads_para_planilha(PASTA_SAIDA / "leads_2026_planilha.csv", leads)

    contagem = lambda linhas, campo: dict(sorted({v: sum(1 for l in linhas if l[campo] == v) for v in {l[campo] for l in linhas}}.items()))
    print(f"contratos_locacao_2026.csv: {len(contratos_csv)} linhas | status {contagem(contratos_csv, 'status')}")
    print(f"  por categoria: { {s: sum(1 for c in contratos if c['categoria'] == s) for s in MES_JANELA} }")
    print(f"faturamento_2026.csv: {len(faturas_csv)} linhas | status {contagem(faturas_csv, 'status_pagamento')}")
    print(f"leads_2026.csv: {len(leads)} linhas | status {contagem(leads, 'status')}")
    print(f"  motivos de perda: {contagem([l for l in leads if l['motivo_perda']], 'motivo_perda')}")
    print(f"  origens: {contagem(leads, 'origem')}")
    print("Janelas 'todas as unidades alugadas':")
    for janela in janelas:
        print(f"  {janela['segmento']}: {janela['fabricante']} {janela['modelo']} "
              f"({len(janela['unidades'])} un.) de {janela['inicio']} a {janela['fim']}")
    print(f"\nArquivos em {PASTA_SAIDA.relative_to(RAIZ)}")


if __name__ == "__main__":
    main()
