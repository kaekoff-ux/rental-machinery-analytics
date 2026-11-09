# Sistema de gestão LocaMaq (estilo Salesforce): plano e situação

Pedido do usuário em 09/11/2026: transformar os dashboards feitos no Cowork em um sistema
operacional de verdade, aberto fora do Claude, parecido com o Salesforce, com as cores do
dashboard, e rodando também na AWS. Case de portfólio: **todos os dados são fictícios**.

Código: `app/` (é a pasta que o roadmap reservava para o app da Fase 6). Como rodar:
`app/README.md`.

## Decisões tomadas (recomendação minha, o usuário pode mudar)

| Tema | Escolha | Por quê |
|---|---|---|
| Tecnologia | Django 5.2 + SQLite, páginas geradas no servidor | Login, permissões, formulários, proteção CSRF e admin prontos; Python, que já é a linguagem do projeto; leve para a EC2 de 1 GB |
| Visual | Tokens de cor, fonte, vidro e pílulas do dashboard do Cowork (claro e escuro) | Pedido do usuário |
| Painel | Código do Cowork portado sem mudar fórmulas; o servidor monta as tabelas a partir do banco | Os números conferem com o Cowork (teste automático) |
| Leads | Mesmo funil da planilha: Novo, Em Contato, Orçado, Fechado, Perdidos | O fluxo do n8n e os indicadores já usam esses nomes |
| Numeração | `LEAD_NNNN/aa` contínua; os 66 históricos recebem LEAD_0001/26 a LEAD_0066/26 | Igual ao fluxo do n8n (primeiro lead real: LEAD_0067/26) |
| Perfis | Gestor, Vendedor, Atendimento, Oficina | Personas do `spec.md`, seção 5 |

## Incremento 1 (feito em 09/11/2026)

- Objetos: lead, cliente, equipamento, contrato, fatura, ordem de serviço, leitura de
  horímetro e atividade (nota, ligação, e-mail, reunião, tarefa, mudança de etapa).
- Telas: início, listas com busca, filtros, visões, ordenação e exportação CSV, página de
  registro com destaques, etapas, detalhes, relacionados e histórico; Kanban de leads e da
  oficina; busca global; conversão de lead em cliente e contrato; painel.
- Regras: contrato não aceita máquina já contratada no período; horímetro não volta; lead
  perdido exige motivo; mudança de etapa fica registrada no histórico.
- API `POST /api/leads/` para o n8n: no servidor, só pela rede interna do Docker (o proxy
  bloqueia `/crm/api/` de fora); sem `id_lead`, o sistema gera o número (decisão do usuário em
  09/11/2026: o sistema passa a ser o dono da numeração).
- Imagem Docker pronta para servidor (gunicorn + WhiteNoise, roda sob o prefixo `/crm`).
- Verificado: 29 testes passando; números do painel iguais aos do Cowork (3.107 linhas
  máquina × mês, 15 medidas, zero divergência); telas abertas no navegador em tema claro,
  escuro e largura de celular (390 px, sem rolagem lateral); imagem Docker rodando no PC atrás de
  um proxy com `/crm`, com a API respondendo pela rede interna (como o n8n vai chamar).
- **Não testado:** nada disso no servidor da AWS; uso com vários usuários ao mesmo tempo.

## Rodar na AWS: dá, com cuidados

A EC2 atual (`t3.micro`, 1 GB de RAM, com 2 GB de swap) já roda o n8n e o ngrok. No teste no
PC, o contêiner do sistema usou cerca de 93 MB e o proxy (Caddy) cerca de 15 MB. Cabe, mas
apertado; se ficar lento, a saída é subir para `t3.small` (2 GB), com custo maior (preço não
consultado: confirmar no console da AWS antes de decidir). O plano gratuito vence em
28/01/2027.

O domínio gratuito do ngrok é um só. Proposta: colocar um proxy pequeno (Caddy) na frente,
mandando `/crm/` para o sistema e todo o resto para o n8n, como está hoje. Assim o webhook do
site continua no mesmo endereço. O passo a passo do servidor fica na pasta local
`docs/servidor_n8n_aws/` (fora do GitHub, regra do usuário).

Autorizado pelo usuário em 09/11/2026 ("sim, para todos"): subir o sistema na EC2, trocar o
destino do ngrok para o proxy, ligar o fluxo do n8n à API e passar a numeração para o sistema.

## Próximos incrementos (propostos)

1. **Servidor:** publicar na EC2, criar os usuários reais, backup diário do banco
   (`sqlite3 .backup` + snapshot do volume).
2. **Integração:** n8n grava cada lead do site no sistema, além da planilha. Depois, decidir se
   o sistema passa a ser o dono da numeração (hoje quem gera é a Data table do n8n).
3. **Operação:** fatura em aberto vira "Vencido" sozinha pela data; aviso de preventiva pelo
   horímetro (agente da Fase 6); painel com ano selecionável quando houver OS e horímetro de 2026.
4. **Área do cliente:** em espera por decisão do usuário (09/11/2026).
