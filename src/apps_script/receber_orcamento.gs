/**
 * LocaMaq · recebe os pedidos de orçamento do site e grava uma linha por pedido na planilha
 * "LocaMaq - Leads". Passo 5 de docs/plano_camada1_site.md, que traz o passo a passo de publicação.
 *
 * Onde colar: na planilha, Extensões > Apps Script, substituindo o conteúdo de Código.gs.
 * Publicar: Implantar > Nova implantação > App da Web, executar como "Eu" e acesso "Qualquer pessoa".
 * A URL gerada (termina em /exec) vai em URL_APPS_SCRIPT, no topo de site/script.js.
 */

const NOME_DA_ABA = "Leads";
const COLUNAS = ["data_envio", "nome", "contato", "cidade", "equipamento", "prazo", "observacao", "origem"];
const TAMANHO_MAXIMO = 1000;

function doPost(e) {
  const pedido = (e && e.parameter) || {};
  if (pedido.site) return responder({ ok: true }); // campo-isca do formulário preenchido: robô

  const planilha = SpreadsheetApp.getActiveSpreadsheet();
  const aba = planilha.getSheetByName(NOME_DA_ABA) || planilha.insertSheet(NOME_DA_ABA);
  if (aba.getLastRow() === 0) aba.appendRow(COLUNAS);

  const valores = COLUNAS.slice(1).map((coluna) => limpar(pedido[coluna]));
  aba.appendRow([new Date(), ...valores]);
  return responder({ ok: true });
}

// Abrir a URL do Web App no navegador cai aqui: serve para conferir se a publicação deu certo.
function doGet() {
  return responder({ ok: true, mensagem: "Web App da LocaMaq no ar. Os pedidos chegam por POST." });
}

// Texto que começa com = + - @ vira fórmula no Google Sheets; o apóstrofo força a ser só texto.
function limpar(valor) {
  const texto = String(valor || "").slice(0, TAMANHO_MAXIMO).trim();
  return /^[=+\-@]/.test(texto) ? "'" + texto : texto;
}

function responder(objeto) {
  return ContentService.createTextOutput(JSON.stringify(objeto)).setMimeType(ContentService.MimeType.JSON);
}
