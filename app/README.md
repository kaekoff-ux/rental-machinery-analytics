# LocaMaq Gestão — sistema de gestão da locadora (case fictício)

Sistema web no estilo do Salesforce para a LocaMaq, empresa **fictícia** do case de portfólio:
leads com funil e Kanban, clientes, frota, contratos, oficina (ordens de serviço e horímetro),
faturas, atividades e tarefas, busca global e o **Painel** com os indicadores que antes estavam no
dashboard do Cowork. Abre no navegador, fora do Claude, com login.

Todos os dados são fictícios (gerados por script em `data/processed/`).

## O que tem

| Área | O que faz |
|---|---|
| Início | Resumo do dia: leads em aberto, contratos ativos, frota disponível, máquinas em manutenção, faturas vencidas, minhas tarefas, leads recentes, contratos que terminam em 30 dias, OS mais antigas |
| Leads | Lista com busca, filtros e visões (em aberto, meus, sem responsável); Kanban por etapa (arrastar e soltar; perdido pede o motivo); página do lead com etapas, atividades e **Converter em contrato** |
| Clientes | Lista e página com contratos, faturas e leads relacionados |
| Frota | Situação de cada máquina (disponível, locada, em manutenção, fora da frota), horímetro, OS e contratos |
| Contratos | Regra do projeto: não deixa usar a máquina já contratada no mesmo período |
| Oficina | Quadro Kanban das OS (Aberta, Em andamento, Concluída) e lista de OS |
| Faturas | Lista por status e ano, registro de pagamento |
| Painel | O dashboard do Cowork, calculado do banco (mesmas fórmulas; números conferidos por teste) |
| API | `POST /api/leads/` para o n8n gravar os leads do site direto no sistema |

Toda lista exporta CSV (com BOM, abre certo no Excel).

## Rodar no computador (Windows)

Jeito mais fácil: **duplo clique em `app\abrir_sistema.bat`**. Na primeira vez ele prepara o
ambiente Python, cria o banco com a base fictícia e pede para você criar o usuário
administrador (a senha não aparece enquanto você digita). Depois abre
<http://127.0.0.1:8000> no navegador. Fechar a janela preta desliga o sistema.

Passo a passo manual (PowerShell, dentro de `app\`):

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py criar_perfis
.\.venv\Scripts\python.exe manage.py importar_base
.\.venv\Scripts\python.exe manage.py createsuperuser
.\.venv\Scripts\python.exe manage.py runserver
```

Abra <http://127.0.0.1:8000>. O `createsuperuser` pede usuário e senha: quem digita é você.

- `criar_perfis` cria os grupos **Gestor**, **Vendedor**, **Atendimento** e **Oficina**. No
  `/admin/`, crie os usuários da equipe e coloque cada um no grupo certo.
- `importar_base` lê os CSVs de `data/processed/` (e da extensão 2026). Rodar de novo só cria o
  que falta; `--sobrescrever` também atualiza o que já existe com os valores dos CSVs.
- Banco: `app/db.sqlite3` (fora do Git).

## Testes

```powershell
.\.venv\Scripts\python.exe manage.py test crm
```

29 testes: importação, indicadores contra os CSVs do dashboard do Cowork
(`crm/tests/referencia_cowork/`), telas, permissões por perfil, regras de contrato, horímetro,
conversão de lead e API.

## De onde vem o Painel

O painel é o dashboard do Cowork de 07/11/2026 (artefato "Dashboard LocaMaq - Locação de
Máquinas"), portado sem mudar as fórmulas:

- `crm/kpis.py` monta no servidor as tabelas que o dashboard lia ("máquina × mês" e leads);
- `crm/static/crm/painel_cowork.js` é o código de cálculo e gráficos do Cowork;
- `crm/static/crm/painel_dash.js` faz esse código rodar fora do Cowork.

Operação (receita, utilização, margem, MTBF/MTTR) cobre 2024–2025, porque a base não tem
horímetro nem OS de 2026. Leads, faturas e contratos a vencer refletem o que está no sistema.

## API para o n8n

`POST /api/leads/` com um JSON com os campos que o fluxo já grava na planilha (`data_envio`,
`nome`, `contato`, `cidade`, `equipamento`, `prazo`, `observacao`, `origem`, `status` e,
opcionalmente, `id_lead`). Sem `id_lead`, o sistema gera o número e devolve na resposta.

Acesso: com `LOCAMAQ_API_REDE_INTERNA=1`, só chamadas diretas da rede interna do Docker (o n8n
no mesmo servidor; o proxy bloqueia `/crm/api/` para quem vem de fora). Ou, com
`LOCAMAQ_API_TOKEN`, o cabeçalho `Authorization: Bearer <chave>`. Sem nenhuma das duas, a API fica
desligada (503). Reenviar o mesmo pedido não duplica.

## Produção (servidor)

Imagem Docker em `app/Dockerfile` (construir da raiz do repositório:
`docker build -f app/Dockerfile -t locamaq-gestao .`). Variáveis:

| Variável | Para quê |
|---|---|
| `LOCAMAQ_SECRET_KEY` | Chave do Django (obrigatória; gerar com `openssl rand -hex 32`) |
| `LOCAMAQ_HOSTS` | Endereços aceitos, separados por vírgula (obrigatória) |
| `LOCAMAQ_PREFIXO` | Caminho sob o qual o sistema roda, ex.: `/crm` |
| `LOCAMAQ_API_REDE_INTERNA` | `1` para o n8n do mesmo servidor gravar leads sem chave |
| `LOCAMAQ_API_TOKEN` | Chave da API de leads (alternativa à rede interna) |
| `LOCAMAQ_LEAD_PISO` | Último número de lead já usado na planilha; o sistema continua dali |
| `LOCAMAQ_DB` | Caminho do banco (padrão `/dados/db.sqlite3`, volume do contêiner) |

Na primeira subida o contêiner aplica as migrações, cria os perfis e importa a base fictícia.
Testado em 09/11/2026 só no computador (Docker + proxy com o prefixo `/crm`); não testado no
servidor da AWS.
