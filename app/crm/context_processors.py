from django.urls import NoReverseMatch, reverse

# Abas do topo, como a barra de navegação do Salesforce: (nome da url, rótulo, permissão).
ABAS = [
    ("crm:inicio", "Início", None),
    ("crm:leads", "Leads", "crm.view_lead"),
    ("crm:clientes", "Clientes", "crm.view_cliente"),
    ("crm:equipamentos", "Frota", "crm.view_equipamento"),
    ("crm:contratos", "Contratos", "crm.view_contrato"),
    ("crm:oficina", "Oficina", "crm.view_ordemservico"),
    ("crm:faturas", "Faturas", "crm.view_fatura"),
    ("crm:painel", "Painel", None),
]


def navegacao(request):
    if not getattr(request, "user", None) or not request.user.is_authenticated:
        return {}
    caminho = request.path
    abas = []
    for nome, rotulo, perm in ABAS:
        if perm and not request.user.has_perm(perm):
            continue
        try:
            url = reverse(nome)
        except NoReverseMatch:
            continue
        raiz = url.rstrip("/")
        ativa = caminho == url if nome == "crm:inicio" else bool(raiz) and caminho.startswith(raiz)
        abas.append({"url": url, "rotulo": rotulo, "ativa": ativa})
    u = request.user
    nome = u.get_full_name() or u.username
    iniciais = "".join(p[0] for p in nome.split()[:2]).upper() or "?"
    perfis = ", ".join(u.groups.values_list("name", flat=True)) or ("Administrador" if u.is_superuser else "Sem perfil")
    return {"abas": abas, "usuario_nome": nome, "usuario_iniciais": iniciais, "usuario_perfis": perfis}
