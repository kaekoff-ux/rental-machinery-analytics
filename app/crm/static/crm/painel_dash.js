// Adaptador: faz o código do dashboard do Cowork rodar fora do Cowork.
// Oferece o mesmo objeto `dash` (data, calc, draw, params, onData) usando os dados que o
// servidor calculou do banco (bloco JSON #dados-painel). Nada aqui muda as fórmulas.
(() => {
  const fontes = JSON.parse(document.getElementById("dados-painel").textContent);
  const desenhos = {};
  const ouvintes = [];
  let params = {};

  const rodar = (nome, el) => {
    try { desenhos[nome](el); } catch (e) { console.error("Painel:", nome, e); }
  };
  const redesenhar = () => {
    Object.keys(desenhos).forEach((nome) => document.querySelectorAll(`[data-draw="${nome}"]`).forEach((el) => rodar(nome, el)));
    ouvintes.forEach((fn) => { try { fn(); } catch (e) { console.error("Painel:", e); } });
  };
  let pedido = 0;
  const agendar = () => {
    cancelAnimationFrame(pedido);
    pedido = requestAnimationFrame(redesenhar);
  };

  window.dash = {
    data(id) {
      const rows = fontes[id];
      if (rows === undefined) return { status: "missing", data: [], columns: [], refreshing: false, meta: [] };
      return { status: "ok", data: rows, columns: rows.length ? Object.keys(rows[0]) : [], refreshing: false, meta: [] };
    },
    calc(id, { inputs, fn }) { fontes[id] = fn(...inputs.map((i) => fontes[i] || [])); },
    loader() {},
    draw(nome, fn) {
      if (fn) { desenhos[nome] = fn; return; }
      if (desenhos[nome]) document.querySelectorAll(`[data-draw="${nome}"]`).forEach((el) => rodar(nome, el));
    },
    params() { return { ...params }; },
    // Como no Cowork, o redesenho vem depois: o código do painel primeiro mostra o bloco de
    // detalhamento e só então os gráficos medem a largura disponível.
    setParams(p) {
      Object.entries(p).forEach(([k, v]) => { if (v == null) delete params[k]; else params[k] = v; });
      agendar();
    },
    resetParams() { params = {}; agendar(); },
    onData(fn) { ouvintes.push(fn); },
    setLink() {},
    refresh() {},
  };
  window.lmRedesenhar = redesenhar;

  let espera;
  let largura = window.innerWidth;
  window.addEventListener("resize", () => {
    if (window.innerWidth === largura) return;
    largura = window.innerWidth;
    clearTimeout(espera);
    espera = setTimeout(redesenhar, 150);
  });
})();
