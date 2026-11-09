// Interface do sistema de gestão LocaMaq: tema, filtros, guias, avisos e Kanban.
(() => {
  const raiz = document.documentElement;

  // Tema claro/escuro: a escolha fica só neste navegador.
  const temaAtual = () => raiz.dataset.tema || (matchMedia("(prefers-color-scheme: dark)").matches ? "escuro" : "claro");
  const pintarBotao = () => {
    const t = temaAtual();
    document.querySelectorAll("[data-icone-tema]").forEach((el) => { el.hidden = el.dataset.iconeTema !== t; });
  };
  document.querySelectorAll("[data-alternar-tema]").forEach((b) => b.addEventListener("click", () => {
    const novo = temaAtual() === "escuro" ? "claro" : "escuro";
    raiz.dataset.tema = novo;
    try { localStorage.setItem("lm-tema", novo); } catch (e) { /* navegador sem armazenamento */ }
    pintarBotao();
    window.dispatchEvent(new Event("lm-tema"));
  }));
  pintarBotao();

  // Filtros: mudar a opção já aplica.
  document.querySelectorAll("[data-enviar]").forEach((el) => el.addEventListener("change", () => el.form && el.form.requestSubmit()));

  // Menu do usuário fecha ao clicar fora.
  document.addEventListener("click", (ev) => {
    document.querySelectorAll("details.usuario[open]").forEach((d) => { if (!d.contains(ev.target)) d.open = false; });
  });

  // Avisos somem depois de alguns segundos.
  document.querySelectorAll(".aviso").forEach((a, i) => setTimeout(() => a.remove(), 6000 + i * 800));

  // Guias Detalhes / Relacionados na página de registro.
  document.querySelectorAll("[data-guias]").forEach((box) => {
    const guias = [...box.querySelectorAll('[role="tab"]')];
    const mostrar = (alvo) => guias.forEach((g) => {
      const ativa = g === alvo;
      g.setAttribute("aria-selected", String(ativa));
      const painel = document.getElementById(g.getAttribute("aria-controls"));
      if (painel) painel.hidden = !ativa;
    });
    guias.forEach((g) => g.addEventListener("click", () => mostrar(g)));
    if (guias.length) mostrar(guias[0]);
  });

  // ----- Kanban -----
  const csrf = () => {
    const el = document.querySelector("input[name=csrfmiddlewaretoken]");
    return el ? el.value : "";
  };
  const aviso = (texto, tipo = "success") => {
    let box = document.querySelector(".avisos");
    if (!box) { box = document.createElement("div"); box.className = "avisos"; box.setAttribute("role", "status"); document.body.appendChild(box); }
    const a = document.createElement("div"); a.className = "aviso " + tipo; a.textContent = texto; box.appendChild(a);
    setTimeout(() => a.remove(), 5000);
  };
  const dialogoPerda = document.getElementById("dialogo-perda");
  const pedirMotivo = () => new Promise((resolve) => {
    if (!dialogoPerda) { resolve(null); return; }
    const sel = dialogoPerda.querySelector("select");
    sel.value = "";
    const fechar = () => {
      dialogoPerda.removeEventListener("close", fechar);
      resolve(dialogoPerda.returnValue === "ok" && sel.value ? sel.value : null);
    };
    dialogoPerda.addEventListener("close", fechar);
    dialogoPerda.showModal();
  });
  const mover = async (cartao, destino, tipo) => {
    const dados = new FormData();
    dados.append("status", destino);
    if (tipo === "lead" && destino === "Perdidos") {
      const motivo = await pedirMotivo();
      if (!motivo) return false;
      dados.append("motivo_perda", motivo);
    }
    try {
      const r = await fetch(cartao.dataset.url, {
        method: "POST", body: dados, credentials: "same-origin",
        headers: { "X-CSRFToken": csrf(), Accept: "application/json" },
      });
      const j = await r.json().catch(() => ({}));
      if (!r.ok || !j.ok) { aviso(j.erro || "Não foi possível mover. Recarregue a página.", "error"); return false; }
      aviso(`${cartao.querySelector(".cod").textContent.split(" ·")[0]} → ${destino}`);
      return true;
    } catch (e) {
      aviso("Sem conexão com o servidor.", "error");
      return false;
    }
  };
  const recontar = (kanban) => kanban.querySelectorAll("[data-coluna]").forEach((col) => {
    const n = col.querySelectorAll("[data-cartao]").length;
    const span = col.querySelector(".coluna-topo span");
    if (span) span.textContent = n;
    const vazio = col.querySelector(".vazio");
    if (vazio) vazio.hidden = n > 0;
  });

  document.querySelectorAll("[data-kanban]").forEach((kanban) => {
    const tipo = kanban.dataset.tipo;
    let arrastado = null;
    kanban.addEventListener("dragstart", (ev) => {
      const c = ev.target.closest("[data-cartao]");
      if (!c || c.getAttribute("draggable") !== "true") return;
      arrastado = c; c.classList.add("arrastando");
      ev.dataTransfer.effectAllowed = "move";
      ev.dataTransfer.setData("text/plain", c.dataset.url);
    });
    kanban.addEventListener("dragend", () => {
      if (arrastado) arrastado.classList.remove("arrastando");
      arrastado = null;
      kanban.querySelectorAll(".alvo").forEach((c) => c.classList.remove("alvo"));
    });
    kanban.querySelectorAll("[data-coluna]").forEach((col) => {
      col.addEventListener("dragover", (ev) => { if (arrastado) { ev.preventDefault(); col.classList.add("alvo"); } });
      col.addEventListener("dragleave", (ev) => { if (!col.contains(ev.relatedTarget)) col.classList.remove("alvo"); });
      col.addEventListener("drop", async (ev) => {
        ev.preventDefault(); col.classList.remove("alvo");
        const c = arrastado;
        if (!c || c.closest("[data-coluna]") === col) return;
        const origem = c.closest("[data-coluna]");
        col.insertBefore(c, col.querySelector("[data-cartao]") || col.querySelector(".vazio"));
        recontar(kanban);
        const ok = await mover(c, col.dataset.coluna, tipo);
        if (!ok) { origem.appendChild(c); recontar(kanban); }
        else { const sel = c.querySelector("[data-enviar-mover]"); if (sel) sel.value = col.dataset.coluna; }
      });
    });
    // Celular e teclado: a lista "mover para" faz o mesmo que arrastar.
    kanban.querySelectorAll("[data-enviar-mover]").forEach((sel) => sel.addEventListener("change", async () => {
      const c = sel.closest("[data-cartao]");
      const origem = c.closest("[data-coluna]");
      const destino = kanban.querySelector(`[data-coluna="${CSS.escape(sel.value)}"]`);
      const ok = await mover(c, sel.value, tipo);
      if (ok && destino) { destino.insertBefore(c, destino.querySelector("[data-cartao]") || destino.querySelector(".vazio")); recontar(kanban); }
      else sel.value = origem.dataset.coluna;
    }));
  });
})();
