"""Confere os dados do painel de consulta (painel/dados.js) contra a base e o dashboard do Cowork.

Uso, na raiz do repositório:  python tests/conferir_painel.py
Só usa a biblioteca padrão. Sai com erro se algo divergir. Rodar depois de mudar os geradores ou
src/painel/gerar_dados_painel.py (e depois de gerar o painel de novo).

Confere:
1. painel/dados.js está em dia com data/processed (gera de novo em memória e compara);
2. as somas mensais e por segmento batem com os CSVs do dashboard do Cowork (tests/referencia_cowork/);
3. os leads de 2026 batem por status, motivo e origem;
4. contagens básicas: 135 máquinas, 3.922 OS, 66 leads, 76 OS abertas em 31/12/2025.
"""
import csv
import importlib.util
import json
import sys
from collections import defaultdict
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
REF = Path(__file__).resolve().parent / "referencia_cowork"
falhas = []


def confere(cond, msg):
    print(("ok    " if cond else "FALHA ") + msg)
    if not cond:
        falhas.append(msg)


def ler_ref(nome):
    with open(REF / nome, encoding="utf-8") as f:
        return list(csv.DictReader(f))


texto = (RAIZ / "painel" / "dados.js").read_text(encoding="utf-8")
dados = json.loads(texto[texto.index("{"):texto.rstrip().rindex("}") + 1])
tab = {k: [dict(zip(v["colunas"], linha)) for linha in v["linhas"]] for k, v in dados.items() if isinstance(v, dict)}

# 1. Em dia com a base: o gerador produz as mesmas linhas.
spec = importlib.util.spec_from_file_location("gerador", RAIZ / "src" / "painel" / "gerar_dados_painel.py")
ger = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ger)
eqs, ordens = ger.ler("cadastro_equipamentos.csv"), ger.ler("ordens_manutencao.csv")
contratos = ger.ler("contratos_locacao.csv") + ger.ler("extensao_2026/contratos_locacao_2026.csv")
faturas = ger.ler("faturamento.csv") + ger.ler("extensao_2026/faturamento_2026.csv")
_, linhas_em = ger.equip_mes(eqs, contratos, faturas, ordens, ger.ler("horimetro_telemetria.csv"))
confere(linhas_em == dados["equip_mes"]["linhas"], "painel/dados.js (máquina × mês) está em dia com data/processed")
confere(ger.os_det(eqs, ordens)[1] == dados["os_det"]["linhas"], "painel/dados.js (OS) está em dia com data/processed")
confere(ger.leads_det(ger.ler("extensao_2026/leads_2026.csv"))[1] == dados["leads_det"]["linhas"], "painel/dados.js (leads) está em dia")

# 2. Somas contra o dashboard do Cowork.
METRICAS = [m for m in ger.METRICAS if m not in ("os_corretiva_h", "vencido", "atraso_soma", "atraso_n")]
mensal, seg = defaultdict(lambda: defaultdict(float)), defaultdict(lambda: defaultdict(float))
maquinas_seg = defaultdict(set)
for r in tab["equip_mes"]:
    for m in METRICAS:
        mensal[r["mes"]][m] += r[m]
        if r["mes"].startswith("2025"):
            seg[r["segmento"]][m] += r[m]
    if r["mes"].startswith("2025") and r["dias_frota"] > 0:
        maquinas_seg[r["segmento"]].add(r["id_equipamento"])
erros = [(ref["mes"], m) for ref in ler_ref("mensal.csv") for m in METRICAS
         if abs(mensal[ref["mes"]][m] - float(ref[m])) > 0.05 + 1e-6 * abs(float(ref[m]))]
confere(not erros, f"24 meses × {len(METRICAS)} medidas iguais ao Cowork" + (f" (divergem: {erros[:3]})" if erros else ""))
erros = [(ref["segmento"], m) for ref in ler_ref("segmentos_2025.csv") for m in METRICAS
         if abs(seg[ref["segmento"]][m] - float(ref[m])) > 0.05 + 1e-6 * abs(float(ref[m]))]
erros += [(ref["segmento"], "equipamentos") for ref in ler_ref("segmentos_2025.csv") if len(maquinas_seg[ref["segmento"]]) != int(ref["equipamentos"])]
confere(not erros, "7 segmentos de 2025 iguais ao Cowork" + (f" (divergem: {erros[:3]})" if erros else ""))

# 3. Leads.
por_status, por_motivo, por_origem = defaultdict(int), defaultdict(int), defaultdict(lambda: [0, 0, 0])
for r in tab["leads_det"]:
    por_status[r["status"]] += 1
    if r["status"] == "Perdidos":
        por_motivo[r["motivo_perda"]] += 1
    o = por_origem[r["origem"]]
    o[0] += 1
    o[1] += r["status"] == "Fechado"
    o[2] += r["status"] == "Perdidos"
confere(all(por_status[x["status"]] == int(x["leads"]) for x in ler_ref("leads_status.csv")), "leads por status iguais ao Cowork")
confere(all(por_motivo[x["motivo"]] == int(x["leads"]) for x in ler_ref("leads_motivo.csv")), "leads perdidos por motivo iguais ao Cowork")
confere(all(por_origem[x["origem"]] == [int(x["leads"]), int(x["fechados"]), int(x["perdidos"])] for x in ler_ref("leads_origem.csv")),
        "leads por origem iguais ao Cowork")

# 4. Contagens.
confere(len({r["id_equipamento"] for r in tab["equip_mes"]}) == 135, "135 máquinas")
confere(len(tab["os_det"]) == 3922, "3.922 ordens de serviço")
confere(len(tab["leads_det"]) == 66, "66 leads de 2026")
abertas = [o for o in tab["os_det"] if o["data_abertura"] <= "2025-12-31" and (not o["data_conclusao"] or o["data_conclusao"] > "2025-12-31")]
confere(len(abertas) == 76, f"76 OS na oficina em 31/12/2025 (achou {len(abertas)})")

print()
print("Tudo certo." if not falhas else f"{len(falhas)} conferência(s) falharam.")
sys.exit(1 if falhas else 0)
