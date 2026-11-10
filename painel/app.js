// Painel LocaMaq: telas, filtros, comparação mês a mês e gráficos (d3 v7).
// Os números vêm de calcs.js; aqui só se escolhe o que mostrar e como.
(() => {
  const C = window.lmCalc;

  // ---------- Formatos (pt-BR) ----------
  const nf = (o) => new Intl.NumberFormat('pt-BR', o);
  const um = {minimumFractionDigits: 1, maximumFractionDigits: 1};
  const MESES = ['jan', 'fev', 'mar', 'abr', 'mai', 'jun', 'jul', 'ago', 'set', 'out', 'nov', 'dez'];
  const F = {
    brl: (v) => 'R$ ' + nf({notation: 'compact', maximumFractionDigits: 1}).format(v),
    brlc: (v) => nf({style: 'currency', currency: 'BRL', maximumFractionDigits: 0}).format(v),
    brl2: (v) => nf({style: 'currency', currency: 'BRL', minimumFractionDigits: 2, maximumFractionDigits: 2}).format(v),
    pct: (v) => nf({style: 'percent', ...um}).format(v),
    pct0: (v) => Math.round(v * 100) + '%',
    int: (v) => nf({maximumFractionDigits: 0}).format(v),
    h: (v) => nf({maximumFractionDigits: 0}).format(v) + ' h',
    h1: (v) => nf(um).format(v) + ' h',
    dias: (v) => nf(um).format(v) + ' dias',
    d0: (v) => nf({maximumFractionDigits: 0}).format(v) + ' dias',
    txt: (v) => String(v),
  };
  const fmt = (tipo, v) => (v == null || (typeof v === 'number' && !isFinite(v)) ? '—' : F[tipo](v));
  const nomePer = (p) => (p.length === 4 ? p : `${MESES[+p.slice(5, 7) - 1]}/${p.slice(0, 4)}`);
  const mesCurto = (m) => `${MESES[+m.slice(5, 7) - 1]}/${m.slice(2, 4)}`;
  // Variação entre o período e o de comparação: relativa (%), em pontos percentuais ou absoluta.
  const variacao = (tipo, a, b) => {
    if (a == null || b == null || !isFinite(a) || !isFinite(b)) return null;
    if (tipo === 'rel') return b ? a / b - 1 : null;
    return a - b;
  };
  // Variação que arredonda para zero na tela (0,0% ou 0,0 p.p.) conta como "sem mudança".
  const zero = (tipo, d) => (tipo === 'abs' ? Math.abs(d) < 0.05 : Math.abs(d) < 0.0005);
  const textoDelta = (tipo, d) => {
    if (d == null) return '—';
    if (zero(tipo, d)) return '= 0';
    const s = d > 0 ? '▲ ' : '▼ ';
    if (tipo === 'rel') return s + nf(um).format(Math.abs(d) * 100) + '%';
    if (tipo === 'pp') return s + nf(um).format(Math.abs(d) * 100) + ' p.p.';
    return s + nf({maximumFractionDigits: 1}).format(Math.abs(d));
  };
  const classeDelta = (d, bom, tipo) => (d == null || !bom || zero(tipo, d) ? '' : (d > 0) === (bom > 0) ? 'bom' : 'ruim');
  const AVISO_FIM_BASE = 'Dez/2025 é o fim da base fictícia: as OS abertas nos últimos dias ainda não têm conclusão registrada, por isso o número na oficina salta nesse mês. Não é piora real.';

  // ---------- Pequenos construtores de DOM ----------
  const h = (tag, attrs = {}, ...filhos) => {
    const el = document.createElement(tag);
    for (const [k, v] of Object.entries(attrs)) {
      if (v == null || v === false) continue;
      if (k === 'class') el.className = v;
      else if (k.startsWith('on')) el.addEventListener(k.slice(2), v);
      else el.setAttribute(k, v === true ? '' : v);
    }
    for (const f of filhos.flat()) if (f != null && f !== false) el.append(f instanceof Node ? f : String(f));
    return el;
  };
  const ICONES = {
    resumo: '<path d="M4 4h7v7H4zM13 4h7v7h-7zM4 13h7v7H4zM13 13h7v7h-7z"/>',
    receita: '<path d="M3 17l6-6 4 4 8-8M15 7h6v6"/>',
    frota: '<path d="M2 7h12v9H2zM14 10h4l3 3v3h-7"/><circle cx="6" cy="18" r="2"/><circle cx="17" cy="18" r="2"/>',
    oficina: '<path d="M14.7 6.3a4 4 0 0 0-5.4 5.4L3 18l3 3 6.3-6.3a4 4 0 0 0 5.4-5.4l-2.6 2.6-2.4-.6-.6-2.4z"/>',
    manutencao: '<circle cx="12" cy="12" r="3"/><path d="M12 2v3M12 19v3M2 12h3M19 12h3M4.9 4.9l2.1 2.1M17 17l2.1 2.1M4.9 19.1L7 17M17 7l2.1-2.1"/>',
    financeiro: '<rect x="3" y="6" width="18" height="13" rx="2"/><path d="M3 10h18M16 15h2"/>',
    comercial: '<circle cx="9" cy="8" r="3.5"/><path d="M2.5 20a6.5 6.5 0 0 1 13 0M16 4.5a3.5 3.5 0 0 1 0 7M18 14a6 6 0 0 1 3.5 6"/>',
    filtro: '<path d="M3 5h18l-7 8v6l-4 2v-8z"/>',
    baixar: '<path d="M12 4v11M7 10l5 5 5-5M5 20h14"/>',
  };
  const icone = (nome) => { const s = document.createElementNS('http://www.w3.org/2000/svg', 'svg'); s.setAttribute('class', 'ic'); s.setAttribute('viewBox', '0 0 24 24'); s.setAttribute('aria-hidden', 'true'); s.innerHTML = ICONES[nome]; return s; };

  // ---------- Setores ----------
  // kpis: [campo, rótulo, formato, tipo de variação, 1 = subir é bom / -1 = descer é bom, dica]
  const OP = {
    receita: {
      kpis: [['receita', 'Receita', 'brl', 'rel', 1], ['margem', 'Margem', 'pct', 'pp', 1, '(Receita − manutenção − depreciação) ÷ receita'],
        ['receita_maquina', 'Receita por máquina', 'brl', 'rel', 1], ['maquinas', 'Máquinas', 'int', null, 0]],
      meta: true, barra: ['receita', 'brl', 'margem', (v) => 'margem ' + F.pct0(v)],
      serie: [['receita', 'Receita', 'var(--sf-marca)', 'brlc']], y: 'brl', tabela: ['receita', 'Receita', 'brlc', 'rel', 1],
    },
    frota: {
      kpis: [['util_fisica', 'Utilização', 'pct', 'pp', 1, 'Dias locados ÷ dias de frota'],
        ['disponibilidade', 'Disponibilidade', 'pct', 'pp', 1, 'Horas sem parada de oficina ÷ horas do período'],
        ['ociosidade', 'Ociosa', 'pct', 'pp', -1, 'Disponibilidade − utilização: máquina pronta sem contrato'], ['maquinas', 'Máquinas', 'int', null, 0]],
      barra: ['util_fisica', 'pct', 'disponibilidade', (v) => 'disp. ' + F.pct0(v), 1],
      serie: [['disponibilidade', 'Disponibilidade', 'var(--sf-marca)', 'pct'], ['util_fisica', 'Utilização', 'var(--sf-acento)', 'pct']],
      y: 'pct0', dom: [0, 1], tabela: ['util_fisica', 'Utilização', 'pct', 'pp', 1],
    },
    manutencao: {
      kpis: [['pct_corretiva', 'OS corretivas', 'pct', 'pp', -1, 'OS corretivas ÷ total de OS'], ['mtbf', 'MTBF', 'h', 'rel', 1, 'Horas trabalhadas ÷ OS corretivas'],
        ['mttr', 'MTTR', 'h1', 'rel', -1, 'Horas paradas em corretivas ÷ corretivas com horas registradas'],
        ['custo_hora', 'Custo de manutenção por hora', 'brl2', 'rel', -1, 'Peças e mão de obra ÷ horas trabalhadas']],
      barra: ['pct_corretiva', 'pct', 'mtbf', (v) => 'MTBF ' + F.h(v)],
      serie: [['pct_corretiva', 'Corretivas', 'var(--sf-acento)', 'pct']], y: 'pct0', tabela: ['pct_corretiva', 'OS corretivas', 'pct', 'pp', -1],
    },
    financeiro: {
      kpis: [['inadimplencia', 'Inadimplência', 'pct', 'pp', -1, 'Faturas vencidas ÷ faturado (posição de 05/11/2026)'],
        ['vencido', 'Vencido em aberto', 'brl', 'rel', -1], ['receita', 'Faturado', 'brl', 'rel', 1],
        ['atraso_medio', 'Atraso médio', 'dias', 'rel', -1, 'Dias de atraso das faturas pagas depois do vencimento']],
      barra: ['inadimplencia', 'pct', 'vencido', (v) => 'vencido ' + F.brl(v)],
      serie: [['inadimplencia', 'Inadimplência', 'var(--sf-acento)', 'pct']], y: 'pct0', tabela: ['inadimplencia', 'Inadimplência', 'pct', 'pp', -1],
    },
  };
  // Ordem de leitura de um CEO: visão geral, depois o que mexe no caixa (receita, vendas, cobrança),
  // depois a operação que sustenta isso (frota, manutenção, oficina).
  const SETORES = [
    ['resumo', 'Resumo'], ['receita', 'Receita'], ['comercial', 'Comercial'], ['financeiro', 'Financeiro'],
    ['frota', 'Frota'], ['manutencao', 'Manutenção'], ['oficina', 'Oficina'],
  ];

  // ---------- Estado (fica no endereço: #frota?filial=Sorocaba&periodo=2025-03&comparar=ano) ----------
  const PADRAO = {filial: '', segmento: '', cidade: '', periodo: '2025', periodoLeads: '2026', comparar: 'anterior'};
  const est = {setor: 'resumo', ...PADRAO};
  const lerEndereco = () => {
    const [setor, q] = location.hash.slice(1).split('?');
    est.setor = SETORES.some(([id]) => id === setor) ? setor : 'resumo';
    const p = new URLSearchParams(q || '');
    for (const k of Object.keys(PADRAO)) est[k] = p.get(k) ?? PADRAO[k];
    if (!C.filiais.includes(est.filial)) est.filial = '';
    if (!C.segmentos.includes(est.segmento)) est.segmento = '';
    if (!C.cidades.includes(est.cidade)) est.cidade = '';
    if (est.periodo !== '2024' && est.periodo !== '2025' && !C.MESES_OP.includes(est.periodo)) est.periodo = PADRAO.periodo;
    if (est.periodoLeads !== '2026' && !C.MESES_LEADS.includes(est.periodoLeads)) est.periodoLeads = PADRAO.periodoLeads;
    if (!['anterior', 'ano'].includes(est.comparar)) est.comparar = 'anterior';
  };
  const gravarEndereco = () => {
    const p = new URLSearchParams();
    for (const k of Object.keys(PADRAO)) if (est[k] !== PADRAO[k]) p.set(k, est[k]);
    const q = p.toString();
    history.replaceState(null, '', `#${est.setor}${q ? '?' + q : ''}`);
  };
  const mudar = (novo) => { Object.assign(est, novo); gravarEndereco(); desenhar(); };
  const filtrosOp = () => ({filial: est.filial, segmento: est.segmento});
  const filtrosLead = () => ({cidade: est.cidade, segmento: est.segmento});
  const ehLeads = () => est.setor === 'comercial';
  const perAtual = () => (ehLeads() ? est.periodoLeads : est.periodo);
  const perComp = () => C.comparado(perAtual(), est.comparar);
  const nomeComp = () => {
    const p = perAtual(), c = perComp();
    if (ehLeads() && c.startsWith('2025')) return 'sem leads de 2025 na base';
    if (p.length === 4) return `vs ${c}`;
    return est.comparar === 'ano' ? `vs ${nomePer(c)} (mesmo mês)` : `vs ${nomePer(c)} (mês anterior)`;
  };

  // ---------- Componentes ----------
  const comp = (titulo, sub, corpo, acoes = [], rodape = null, id = null) => h('section', {class: 'sf-comp', id},
    h('div', {class: 'sf-comp-cab'}, h('h2', {}, titulo, sub ? h('span', {class: 'sub'}, sub) : null), h('div', {class: 'sf-leg'}, acoes)),
    h('div', {class: 'sf-comp-corpo'}, corpo), rodape ? h('div', {class: 'sf-comp-rodape'}, rodape) : null);

  // Minigráfico mês a mês dentro do card, com o período escolhido destacado.
  const spark = (valores, marcar = []) => {
    const el = h('div', {class: 'sf-spark', 'aria-hidden': 'true'});
    requestAnimationFrame(() => {
      const ok = valores.filter((v) => v != null && isFinite(v));
      if (ok.length < 2) return;
      const W = Math.max(60, el.clientWidth), H = el.clientHeight - 8 || 34;
      const x = d3.scaleLinear([0, valores.length - 1], [3, W - 3]);
      const [lo, hi] = d3.extent(ok);
      const y = d3.scaleLinear(lo === hi ? [lo - 1, hi + 1] : [lo, hi], [H - 3, 3]);
      const passo = (W - 6) / Math.max(1, valores.length - 1);
      const svg = d3.create('svg').attr('width', '100%').attr('height', H).attr('viewBox', `0 0 ${W} ${H}`);
      marcar.forEach((i) => svg.append('rect').attr('x', x(i) - passo / 2).attr('width', passo).attr('height', H).style('fill', 'var(--sf-acento-tinta)'));
      svg.append('path').attr('d', d3.line().defined((v) => v != null && isFinite(v)).x((_, i) => x(i)).y((v) => y(v))(valores))
        .attr('fill', 'none').style('stroke', 'var(--sf-marca)').attr('stroke-width', 1.6).attr('stroke-linejoin', 'round');
      const ult = marcar.length ? marcar[marcar.length - 1] : valores.length - 1;
      if (valores[ult] != null && isFinite(valores[ult])) svg.append('circle').attr('cx', x(ult)).attr('cy', y(valores[ult])).attr('r', 3).style('fill', 'var(--sf-acento)');
      el.append(svg.node());
    });
    return el;
  };

  const kpi = ({rot, valor, formato, delta, tipo, bom, dica, extra, ir, serie, marcar}) => {
    const d = h('span', {class: 'sf-delta ' + classeDelta(delta, bom, tipo)}, textoDelta(tipo, delta));
    const comparar = tipo && !nomeComp().startsWith('sem');
    const filhos = [h('span', {class: 'rot'}, rot), h('span', {class: 'val'}, fmt(formato, valor)),
      h('span', {class: 'det'}, comparar ? [d, h('span', {}, nomeComp())] : null, extra || null),
      serie ? spark(serie, marcar) : null];
    return ir ? h('button', {type: 'button', class: 'sf-kpi', title: dica, onclick: () => mudar({setor: ir})}, filhos)
      : h('div', {class: 'sf-kpi', title: dica}, filhos);
  };

  const legenda = (series) => series.map(([, nome, cor]) => h('span', {}, h('i', {style: `background:${cor}`}), nome));

  const baixarCSV = (nome, colunas, linhas) => {
    const cel = (v) => (v == null ? '' : typeof v === 'number' ? String(Math.round(v * 1e4) / 1e4).replace('.', ',')
      : /[;"\n]/.test(String(v)) ? '"' + String(v).replace(/"/g, '""') + '"' : String(v));
    const texto = '﻿' + [colunas.join(';'), ...linhas.map((r) => colunas.map((c) => cel(r[c])).join(';'))].join('\r\n');
    const a = h('a', {href: URL.createObjectURL(new Blob([texto], {type: 'text/csv;charset=utf-8'})), download: `locamaq_${nome}.csv`});
    document.body.append(a); a.click(); a.remove();
  };
  const botaoCSV = (nome, colunas, linhas) => h('button', {type: 'button', class: 'sf-icone', title: 'Exportar CSV', 'aria-label': 'Exportar CSV',
    onclick: () => baixarCSV(nome, colunas, linhas())}, icone('baixar'));

  // Barras clicáveis: o clique aplica o filtro do nível seguinte.
  const barras = (linhas, {valor, formato, nota, notaFmt, max, nBaixo, clicar, vazio = 'Sem dados para este filtro.'}) => {
    if (!linhas.length) return h('p', {class: 'sf-vazio'}, vazio);
    const topo = Math.max(max || 0, d3.max(linhas, (r) => Math.abs(r[valor] || 0)) || 1);
    return h('div', {class: 'sf-barras'}, linhas.map((r) => {
      const baixo = nBaixo && nBaixo(r);
      const filhos = [h('span', {class: 'n'}, r.rotulo), h('span', {class: 't'}, h('i', {style: `width:${Math.abs(r[valor] || 0) / topo * 100}%`})),
        h('span', {class: 'v'}, h('b', {}, fmt(formato, r[valor])), h('small', {}, r[nota] != null && r[nota] !== '' ? notaFmt(r[nota]) : ''))];
      const titulo = baixo ? 'Poucos casos: leia como indício, não como tendência' : null;
      return clicar ? h('button', {type: 'button', class: 'sf-barra' + (baixo ? ' n-baixo' : ''), title: titulo, onclick: () => clicar(r)}, filhos)
        : h('div', {class: 'sf-barra' + (baixo ? ' n-baixo' : ''), title: titulo}, filhos);
    }));
  };

  // Gráfico de linhas com régua, dica e faixa no período escolhido.
  const linhasGraf = (series, rotulos, {yFmt, yDom, marcar = []}) => {
    const el = h('div', {class: 'sf-graf'});
    requestAnimationFrame(() => {
      const W = Math.max(260, el.clientWidth), H = Math.max(160, el.clientHeight || 240), mt = 8, mb = 22, mr = 8;
      const svg = d3.create('svg').attr('width', '100%').attr('viewBox', `0 0 ${W} ${H}`).attr('role', 'img');
      el.replaceChildren(svg.node());
      const todos = series.flatMap((s) => s.values).filter((v) => v != null && isFinite(v));
      const y = d3.scaleLinear(yDom || [Math.min(0, d3.min(todos) ?? 0), (d3.max(todos) || 1) * 1.08], [H - mb, mt]).nice();
      const ticks = y.ticks(4);
      const g = svg.append('g');
      const ml = Math.ceil(d3.max(ticks, (d) => g.append('text').text(yFmt(d)).node().getComputedTextLength()) || 0) + 10;
      g.selectAll('*').remove();
      const x = d3.scalePoint(rotulos.map((_, i) => i), [ml, W - mr]).padding(0.3);
      const passoX = x.step();
      marcar.forEach((i) => g.append('rect').attr('x', x(i) - passoX / 2).attr('width', passoX).attr('y', mt).attr('height', H - mt - mb)
        .style('fill', 'var(--sf-acento-tinta)'));
      g.selectAll('line.g').data(ticks).join('line').attr('x1', ml).attr('x2', W - mr).attr('y1', y).attr('y2', y).style('stroke', 'var(--sf-grade)');
      g.selectAll('text.y').data(ticks).join('text').attr('x', ml - 8).attr('y', y).attr('dy', '0.32em').attr('text-anchor', 'end').text(yFmt);
      const passo = Math.max(1, Math.ceil(rotulos.length / Math.max(1, Math.floor((W - ml) / 46))));
      g.selectAll('text.x').data(rotulos.map((r, i) => [r, i]).filter(([, i]) => i % passo === 0)).join('text')
        .attr('x', ([, i]) => x(i)).attr('y', H - 5).attr('text-anchor', 'middle').text(([r]) => r);
      const linha = d3.line().defined((v) => v != null && isFinite(v)).x((_, i) => x(i)).y((v) => y(v));
      series.forEach((s) => svg.append('path').attr('d', linha(s.values)).attr('fill', 'none').style('stroke', s.cor)
        .attr('stroke-width', 2.2).attr('stroke-dasharray', s.tracejada ? '4 4' : null).attr('stroke-linejoin', 'round').attr('stroke-linecap', 'round'));
      const regua = svg.append('line').attr('y1', mt).attr('y2', H - mb).style('stroke', 'var(--sf-eixo)').attr('stroke-dasharray', '3 3').attr('opacity', 0);
      const pts = svg.append('g');
      const tip = h('div', {class: 'sf-tip', hidden: true});
      el.append(tip);
      svg.append('rect').attr('x', ml).attr('width', W - ml - mr).attr('height', H).attr('fill', 'transparent')
        .on('mousemove', (ev) => {
          const i = Math.max(0, Math.min(rotulos.length - 1, Math.round((d3.pointer(ev)[0] - x(0)) / passoX)));
          const vis = series.filter((s) => s.values[i] != null && isFinite(s.values[i]));
          regua.attr('x1', x(i)).attr('x2', x(i)).attr('opacity', 1);
          pts.selectAll('circle').data(vis).join('circle').attr('cx', x(i)).attr('cy', (s) => y(s.values[i])).attr('r', 4)
            .style('fill', (s) => s.cor).style('stroke', 'var(--sf-card)').attr('stroke-width', 2);
          tip.replaceChildren(h('div', {class: 't'}, rotulos[i]), ...vis.map((s) => h('div', {class: 'l'}, h('i', {style: `background:${s.cor}`}), `${s.nome}: ${s.tipFmt(s.values[i])}`)));
          tip.hidden = false;
          const k = svg.node().getBoundingClientRect().width / W;
          tip.style.left = Math.max(0, Math.min(el.clientWidth - tip.offsetWidth, x(i) * k + 12)) + 'px';
          tip.style.top = Math.max(0, y(d3.max(vis, (s) => s.values[i]) ?? 0) * k - tip.offsetHeight - 8) + 'px';
        })
        .on('mouseleave', () => { regua.attr('opacity', 0); pts.selectAll('circle').remove(); tip.hidden = true; });
    });
    return el;
  };

  // Velocímetro: receita do período contra a meta (mesmo período do ano anterior + 5%).
  const velocimetro = (m) => {
    const el = h('div', {class: 'sf-gauge'});
    if (!m) { el.append(h('p', {class: 'sf-vazio'}, 'Sem meta: não há o mesmo período do ano anterior na base.')); return el; }
    const {receita: v, meta, atingimento: at} = m, max = Math.max(meta * 1.2, v * 1.05);
    const W = 220, H = 150, r = 86, sw = 13, ang = (x) => -Math.PI / 2 + Math.min(1, x / max) * Math.PI;
    const svg = d3.create('svg').attr('width', '100%').attr('viewBox', `0 0 ${W} ${H}`).attr('role', 'img')
      .attr('aria-label', `${F.brl(v)}, ${F.pct0(at)} da meta de ${F.brl(meta)}`);
    const g = svg.append('g').attr('transform', `translate(${W / 2},${r + 10})`);
    const arco = d3.arc().innerRadius(r - sw).outerRadius(r).cornerRadius(sw / 2);
    g.append('path').attr('d', arco({startAngle: -Math.PI / 2, endAngle: Math.PI / 2})).style('fill', 'var(--sf-trilho)');
    g.append('path').attr('d', d3.arc().innerRadius(r + 4).outerRadius(r + 7)({startAngle: ang(meta), endAngle: Math.PI / 2})).style('fill', 'var(--sf-bom)').attr('opacity', 0.55);
    g.append('path').attr('d', arco({startAngle: -Math.PI / 2, endAngle: ang(v)})).style('fill', at >= 1 ? 'var(--sf-marca)' : 'var(--sf-acento)');
    const am = ang(meta), a = ang(v);
    g.append('line').attr('x1', Math.sin(am) * (r - sw - 3)).attr('y1', -Math.cos(am) * (r - sw - 3)).attr('x2', Math.sin(am) * (r + 9)).attr('y2', -Math.cos(am) * (r + 9))
      .style('stroke', 'var(--sf-texto)').attr('stroke-width', 2);
    g.append('path').attr('d', `M-3,0 L0,${-(r - sw - 10)} L3,0 Z`).attr('transform', `rotate(${a * 180 / Math.PI})`).style('fill', 'var(--sf-texto)');
    g.append('circle').attr('r', 6).style('fill', 'var(--sf-texto)');
    g.append('text').attr('y', 32).attr('text-anchor', 'middle').attr('class', 'sf-g-valor').text(F.pct0(at));
    g.append('text').attr('y', 48).attr('text-anchor', 'middle').attr('class', 'sf-g-meta').text(`${F.brl(v)} de ${F.brl(meta)}`);
    el.append(svg.node());
    return el;
  };

  // Tabela de comparação mês a mês do ano do período escolhido.
  // col: [campo, rótulo, formato, tipo de variação, bom]; extras: colunas de apoio [campo, rótulo, formato ou função da linha].
  const tabelaMensal = ({mensal, col: [campo, rotulo, formato, tipo, bom], extras = [], anoTotal, semAnoAnterior}) => {
    const per = perAtual(), ano = per.slice(0, 4);
    const por = new Map(mensal.map((r) => [r.mes, r]));
    const linhas = mensal.filter((r) => r.mes.startsWith(ano));
    const cel = (d, b) => h('td', {class: classeDelta(d, b, tipo) || (d == null ? 'fraco' : null)}, textoDelta(tipo, d));
    const apoio = (r) => extras.map(([c, , f]) => h('td', {}, r ? (typeof f === 'function' ? f(r) : fmt(f, r[c])) : '—'));
    const corpo = linhas.map((r) => {
      const ant = por.get(C.comparado(r.mes, 'anterior')), aa = por.get(C.comparado(r.mes, 'ano'));
      return h('tr', {class: r.mes === per ? 'sel' : null, title: 'Ver ' + nomePer(r.mes), onclick: () => mudar(ehLeads() ? {periodoLeads: r.mes} : {periodo: r.mes})},
        h('td', {}, nomePer(r.mes)), h('td', {}, fmt(formato, r[campo])),
        cel(variacao(tipo, r[campo], ant ? ant[campo] : null), bom),
        semAnoAnterior ? null : cel(variacao(tipo, r[campo], aa ? aa[campo] : null), bom), ...apoio(r));
    });
    const tot = anoTotal(ano), totAnt = anoTotal(String(+ano - 1));
    const pe = h('tr', {}, h('td', {}, `Ano ${ano}`), h('td', {}, fmt(formato, tot ? tot[campo] : null)), h('td', {class: 'fraco'}, '—'),
      semAnoAnterior ? null : cel(variacao(tipo, tot ? tot[campo] : null, totAnt ? totAnt[campo] : null), bom), ...apoio(tot));
    return h('div', {class: 'sf-tabela-caixa'}, h('table', {class: 'sf-tabela'},
      h('thead', {}, h('tr', {}, h('th', {}, 'Mês'), h('th', {}, rotulo), h('th', {}, 'vs mês anterior'),
        semAnoAnterior ? null : h('th', {}, `vs ${+ano - 1}`), ...extras.map(([, r]) => h('th', {}, r)))),
      h('tbody', {}, corpo), h('tfoot', {}, pe)));
  };

  // ---------- Cabeçalho e filtros ----------
  const cabecalho = (titulo) => {
    const partes = [ehLeads() ? est.cidade : est.filial, est.segmento].filter(Boolean);
    return h('header', {class: 'sf-cab'}, h('span', {class: 'sf-cab-icone'}, icone(est.setor)),
      h('div', {class: 'sf-cab-txt'}, h('p', {}, 'Painel · ' + (partes.length ? partes.join(' · ') : ehLeads() ? 'Todas as cidades' : 'Toda a frota')),
        h('h1', {}, `${titulo} · ${nomePer(perAtual())}`)),
      h('div', {class: 'sf-cab-meta'}, ehLeads() ? 'Leads de 2026 (base fictícia)' : 'Operação 2024–2025 (base fictícia)', h('br'), `Dados gerados em ${dataBR(C.gerado_em)}`));
  };
  const dataBR = (iso) => (iso ? iso.split('-').reverse().join('/') : '—');
  const select = (id, rotulo, valor, opcoes, aoMudar, padrao = '') => h('div', {class: 'sf-campo'},
    h('label', {for: id}, rotulo),
    h('select', {id, class: valor !== padrao ? 'ativo' : null, onchange: (e) => aoMudar(e.target.value)},
      opcoes.map((o) => (o.grupo ? h('optgroup', {label: o.grupo}, o.itens.map(([v, t]) => h('option', {value: v, selected: v === valor}, t)))
        : h('option', {value: o[0], selected: o[0] === valor}, o[1])))));
  const filtros = () => {
    const leads = ehLeads();
    const anos = leads ? ['2026'] : ['2025', '2024'];
    const universo = leads ? C.MESES_LEADS : C.MESES_OP;
    const opcoesPer = [{grupo: 'Ano inteiro', itens: anos.map((a) => [a, `Ano ${a}`])},
      ...anos.map((a) => ({grupo: `Meses de ${a}`, itens: universo.filter((m) => m.startsWith(a)).reverse().map((m) => [m, nomePer(m)])}))];
    const local = leads
      ? select('f-cidade', 'Cidade', est.cidade, [['', 'Todas'], ...C.cidades.map((c) => [c, c])], (v) => mudar({cidade: v}))
      : select('f-filial', 'Filial', est.filial, [['', 'Todas'], ...C.filiais.map((c) => [c, c])], (v) => mudar({filial: v}));
    const ativos = (leads ? est.cidade : est.filial) || est.segmento;
    return h('div', {class: 'sf-filtros', role: 'group', 'aria-label': 'Filtros'},
      h('span', {class: 'sf-filtros-tit'}, icone('filtro'), 'Filtros'),
      local,
      select('f-segmento', 'Segmento', est.segmento, [['', 'Todos'], ...C.segmentos.map((c) => [c, c])], (v) => mudar({segmento: v})),
      select('f-periodo', 'Período', perAtual(), opcoesPer, (v) => mudar(leads ? {periodoLeads: v} : {periodo: v}), leads ? '2026' : '2025'),
      select('f-comparar', 'Comparar com', est.comparar,
        [['anterior', perAtual().length === 4 ? 'Ano anterior' : 'Mês anterior'], ['ano', perAtual().length === 4 ? 'Ano anterior' : 'Mesmo mês do ano anterior']],
        (v) => mudar({comparar: v}), 'anterior'),
      h('button', {type: 'button', class: 'sf-limpar', disabled: !ativos && perAtual() === (leads ? '2026' : '2025') && est.comparar === 'anterior',
        onclick: () => mudar(leads ? {cidade: '', segmento: '', periodoLeads: '2026', comparar: 'anterior'} : {filial: '', segmento: '', periodo: '2025', comparar: 'anterior'})}, 'Limpar filtros'),
      h('span', {class: 'sf-comparando'}, nomeComp().startsWith('sem') ? `${nomePer(perAtual())}: ${nomeComp()}` : `Comparando ${nomePer(perAtual())} ${nomeComp()}`));
  };

  // Nível do detalhamento: filial → segmento → máquina (cidade → segmento → modelo nos leads).
  const nivel = () => {
    const local = ehLeads() ? est.cidade : est.filial;
    if (!local) return ehLeads() ? ['cidade', 'Por cidade'] : ['filial', 'Por filial'];
    if (!est.segmento) return ['segmento', 'Por segmento'];
    return ehLeads() ? ['modelo', 'Por modelo'] : ['id_equipamento', 'Por máquina'];
  };
  const aoClicarBarra = (campo) => (campo === 'filial' ? (r) => mudar({filial: r.chave}) : campo === 'cidade' ? (r) => mudar({cidade: r.chave})
    : campo === 'segmento' ? (r) => mudar({segmento: r.chave}) : null);

  // ---------- Telas ----------
  const telaOp = (id, titulo) => {
    const cfg = OP[id], f = filtrosOp(), per = perAtual(), comp_ = perComp();
    const atual = C.op(f, per) || {}, antes = C.op(f, comp_) || {};
    const mensal = C.opMensal(f);
    const idx = C.meses(per, C.MESES_OP).map((m) => C.MESES_OP.indexOf(m));
    const cartoes = cfg.kpis.map(([c, rot, formato, tipo, bom, dica]) => kpi({rot, valor: atual[c], formato, tipo, bom, dica,
      delta: variacao(tipo, atual[c], antes[c]), serie: mensal.map((r) => r[c]), marcar: idx}));
    const [campo, tituloNivel] = nivel();
    const grupos = C.opPor(f, per, campo).sort((a, b) => (b[cfg.barra[0]] ?? -1) - (a[cfg.barra[0]] ?? -1));
    const [bc, bf, bn, bnf, bmax] = cfg.barra;
    const csvCols = ['mes', 'maquinas', 'receita', 'margem', 'util_fisica', 'disponibilidade', 'ociosidade', 'pct_corretiva', 'mtbf', 'mttr', 'custo_hora', 'inadimplencia', 'vencido', 'atraso_medio'];
    return [
      cfg.meta ? h('div', {class: 'sf-meta'}, comp('Meta de vendas', null, velocimetro(C.meta(f, per)), [], 'Meta = receita do mesmo período do ano anterior + 5%'),
        h('div', {class: 'sf-kpis'}, cartoes)) : h('div', {class: 'sf-kpis'}, cartoes),
      h('div', {class: 'sf-grade'},
        comp(tituloNivel, nomePer(per), barras(grupos, {valor: bc, formato: bf, nota: bn, notaFmt: bnf, max: bmax, nBaixo: campo !== 'id_equipamento' ? (r) => r.maquinas < 3 : null, clicar: aoClicarBarra(campo)}),
          [botaoCSV(`${id}_${campo}`, ['rotulo', ...csvCols.slice(1)], () => grupos)],
          campo === 'id_equipamento' ? 'Uma máquina por linha' : 'Clique para detalhar · linhas claras têm menos de 3 máquinas'),
        comp('Mês a mês', 'jan/24 a dez/25', linhasGraf(cfg.serie.map(([c, nome, cor, tf]) => ({nome, cor, values: mensal.map((r) => r[c]), tipFmt: F[tf]})),
          C.MESES_OP.map(mesCurto), {yFmt: F[cfg.y], yDom: cfg.dom, marcar: idx}), legenda(cfg.serie), 'A faixa destacada é o período escolhido')),
      comp('Comparação mês a mês', `${per.slice(0, 4)} · ${cfg.tabela[1]}`,
        tabelaMensal({mensal, col: cfg.tabela, anoTotal: (a) => C.op(f, a)}),
        [botaoCSV(`${id}_mes_a_mes`, csvCols, () => mensal)], 'Clique num mês para ver os números dele'),
    ];
  };

  // Uma faixa do Resumo: título do tema e quatro cards.
  const secao = (titulo, sub, cards) => h('section', {class: 'sf-secao'},
    h('h2', {class: 'sf-secao-tit'}, titulo, h('span', {}, sub)), h('div', {class: 'sf-linha'}, cards));

  // Resumo na ordem de leitura de um CEO: resultado, vendas, caixa, operação.
  const telaResumo = () => {
    const f = filtrosOp(), per = est.periodo, comp_ = perComp();
    const a = C.op(f, per) || {}, b = C.op(f, comp_) || {};
    const mensal = C.opMensal(f), por = new Map(mensal.map((r) => [r.mes, r]));
    const idx = C.meses(per, C.MESES_OP).map((m) => C.MESES_OP.indexOf(m));
    const t = (c, rot, formato, tipo, bom, ir, dica, extra) => kpi({rot, valor: a[c], formato, tipo, bom, ir, dica, extra,
      delta: variacao(tipo, a[c], b[c]), serie: mensal.map((r) => r[c]), marcar: idx});
    const of = C.oficina(f, per), ofb = C.oficina(f, comp_), ofm = C.oficinaMensal(f);
    const fl = {segmento: est.segmento}, ld = C.leads(fl, '2026') || {}, ldm = C.leadsMensal(fl);
    const tl = (c, rot, formato, dica, extra) => kpi({rot, valor: ld[c], formato, ir: 'comercial', dica, extra, serie: ldm.map((r) => r[c])});
    const ano = (y) => Array.from({length: 12}, (_, i) => (por.get(`${y}-${String(i + 1).padStart(2, '0')}`) || {}).receita ?? null);
    const marcar = per.length === 4 ? [] : [+per.slice(5, 7) - 1];
    const filiais = C.opPor({segmento: est.segmento}, per, 'filial').sort((x, y) => y.receita - x.receita);
    return [
      secao('Receita e resultado', nomePer(per), [
        h('section', {class: 'sf-comp', title: 'Meta = receita do mesmo período do ano anterior + 5%'},
          h('div', {class: 'sf-comp-cab'}, h('h2', {}, 'Meta de vendas', h('span', {class: 'sub'}, 'ano anterior + 5%'))),
          h('div', {class: 'sf-comp-corpo'}, velocimetro(C.meta(f, per)))),
        t('receita', 'Receita', 'brl', 'rel', 1, 'receita'),
        t('margem', 'Margem', 'pct', 'pp', 1, 'receita', '(Receita − manutenção − depreciação) ÷ receita'),
        t('receita_maquina', 'Receita por máquina', 'brl', 'rel', 1, 'receita', null, h('span', {}, `${F.int(a.maquinas || 0)} máquinas`)),
      ]),
      secao('Comercial', 'leads de 2026, ano todo', [
        tl('leads', 'Leads recebidos', 'int', null, h('span', {}, `${F.int(ld.em_andamento || 0)} em andamento`)),
        tl('conversao', 'Conversão', 'pct', 'Fechados ÷ (fechados + perdidos)', h('span', {}, `n = ${ld.desfecho || 0} com desfecho`)),
        tl('perda_indisp', 'Perdidos por falta de máquina', 'pct', 'Perdidos por indisponibilidade ÷ leads com desfecho'),
        tl('tempo_medio', 'Tempo até fechar', 'dias', 'Dias do envio do lead ao contrato', h('span', {}, `n = ${ld.fechados || 0} fechados`)),
      ]),
      secao('Financeiro', nomePer(per), [
        t('inadimplencia', 'Inadimplência', 'pct', 'pp', -1, 'financeiro', 'Faturas vencidas ÷ faturado'),
        t('vencido', 'Vencido em aberto', 'brl', 'rel', -1, 'financeiro'),
        t('atraso_medio', 'Atraso médio', 'dias', 'rel', -1, 'financeiro', 'Dias de atraso das faturas pagas depois do vencimento'),
        t('custo_manut', 'Custo de manutenção', 'brl', 'rel', -1, 'manutencao', 'Peças e mão de obra das OS abertas no período'),
      ]),
      secao('Operação', nomePer(per), [
        t('util_fisica', 'Utilização da frota', 'pct', 'pp', 1, 'frota', 'Dias locados ÷ dias de frota'),
        t('disponibilidade', 'Disponibilidade', 'pct', 'pp', 1, 'frota', 'Horas sem parada de oficina ÷ horas do período'),
        t('pct_corretiva', 'OS corretivas', 'pct', 'pp', -1, 'manutencao', 'OS corretivas ÷ total de OS', h('span', {}, `MTBF ${fmt('h', a.mtbf)}`)),
        kpi({rot: 'Na oficina (fim do período)', valor: of.na_oficina, formato: 'int', tipo: 'abs', bom: -1, ir: 'oficina',
          dica: per === '2025' || per === '2025-12' ? AVISO_FIM_BASE : 'OS abertas até o fim do período e ainda não concluídas',
          delta: variacao('abs', of.na_oficina, ofb.na_oficina), extra: h('span', {}, `${F.int(of.maquinas)} máquinas`),
          serie: ofm.map((r) => r.na_oficina), marcar: idx}),
      ]),
      h('div', {class: 'sf-grade'},
        comp('Receita mês a mês', '2024 × 2025', linhasGraf([
          {nome: '2024', cor: 'var(--sf-terra)', values: ano('2024'), tipFmt: F.brlc, tracejada: true},
          {nome: '2025', cor: 'var(--sf-marca)', values: ano('2025'), tipFmt: F.brlc}], MESES, {yFmt: F.brl, marcar}),
        legenda([[0, '2024', 'var(--sf-terra)'], [0, '2025', 'var(--sf-marca)']])),
        comp('Receita por filial', nomePer(per), barras(filiais, {valor: 'receita', formato: 'brl', nota: 'margem', notaFmt: (v) => 'margem ' + F.pct0(v),
          clicar: (r) => mudar({setor: 'receita', filial: r.chave})}), [], 'Clique numa filial para abrir a Receita dela')),
    ];
  };

  const telaOficina = () => {
    const f = filtrosOp(), per = perAtual(), comp_ = perComp();
    const a = C.oficina(f, per), b = C.oficina(f, comp_);
    const mensal = C.oficinaMensal(f);
    const idx = C.meses(per, C.MESES_OP).map((m) => C.MESES_OP.indexOf(m));
    const k = (c, rot, formato, tipo, bom, dica, extra) => kpi({rot, valor: a[c], formato, tipo, bom, dica, extra,
      delta: tipo ? variacao(tipo, a[c], b[c]) : null, serie: mensal.map((r) => r[c]), marcar: idx});
    const [campo, tituloNivel] = nivel();
    const grupos = C.oficinaPor(f, per, campo).filter((r) => r.na_oficina > 0)
      .sort((x, y) => (campo === 'id_equipamento' ? y.dias_aberta - x.dias_aberta : y.na_oficina - x.na_oficina));
    const serie = [['abertas', 'Abertas', 'var(--sf-terra)', 'int'], ['concluidas', 'Concluídas', 'var(--sf-marca)', 'int']];
    return [
      h('div', {class: 'sf-kpis'},
        k('na_oficina', 'Na oficina no fim do período', 'int', 'abs', -1, 'OS abertas até o fim do período e ainda não concluídas', h('span', {}, `${F.int(a.maquinas)} máquinas`)),
        k('abertas', 'OS abertas no período', 'int', 'rel', -1),
        k('concluidas', 'OS concluídas no período', 'int', 'rel', 1),
        k('acima_prazo', 'Acima do prazo', 'int', 'abs', -1, 'Na oficina há mais dias que 90% das OS do mesmo tipo levam para fechar'),
        k('prazo_corretiva', 'Prazo das corretivas', 'dias', 'rel', -1, 'Dias da abertura à conclusão das corretivas concluídas no período', h('span', {}, `n = ${a.n_corretivas}`))),
      per === '2025' || per === '2025-12' ? h('p', {class: 'sf-nota'}, AVISO_FIM_BASE) : null,
      h('div', {class: 'sf-grade'},
        comp(campo === 'id_equipamento' ? 'Máquinas na oficina · dias aberta' : `${tituloNivel} · na oficina`, `fim de ${nomePer(per)}`,
          campo === 'id_equipamento'
            ? barras(grupos, {valor: 'dias_aberta', formato: 'd0', nota: 'servico', notaFmt: F.txt, vazio: 'Nenhuma máquina na oficina no fim do período.'})
            : barras(grupos, {valor: 'na_oficina', formato: 'int', nota: 'acima_prazo', notaFmt: (v) => (v ? `${F.int(v)} acima do prazo` : ''), clicar: aoClicarBarra(campo),
              vazio: 'Nenhuma máquina na oficina no fim do período.'}),
          [botaoCSV('oficina_os_abertas', ['id_os', 'id_equipamento', 'modelo', 'filial', 'segmento', 'tipo', 'status', 'descricao_falha', 'data_abertura', 'dias_aberta', 'prazo_p90'],
            () => C.linhasOS(f, per))], 'Exporta a lista de OS na oficina no fim do período'),
        comp('Entrada e saída de OS', 'jan/24 a dez/25', linhasGraf(serie.map(([c, nome, cor, tf]) => ({nome, cor, values: mensal.map((r) => r[c]), tipFmt: F[tf]})),
          C.MESES_OP.map(mesCurto), {yFmt: F.int, marcar: idx}), legenda(serie), 'A faixa destacada é o período escolhido')),
      comp('Comparação mês a mês', `${per.slice(0, 4)} · OS na oficina no fim do mês`,
        tabelaMensal({mensal, col: ['na_oficina', 'Na oficina (fim do mês)', 'int', 'abs', -1],
          extras: [['abertas', 'Abertas', 'int'], ['concluidas', 'Concluídas', 'int']], anoTotal: (y) => C.oficina(f, y)}),
        [botaoCSV('oficina_mes_a_mes', ['mes', 'abertas', 'concluidas', 'na_oficina', 'maquinas', 'acima_prazo', 'prazo_corretiva'], () => mensal)],
        'Na linha do ano, "na oficina" é a posição em 31/12. ' + (per.startsWith('2025') ? AVISO_FIM_BASE : '')),
    ];
  };

  const telaComercial = () => {
    const f = filtrosLead(), per = perAtual(), comp_ = perComp();
    const a = C.leads(f, per) || {}, b = C.leads(f, comp_) || {};
    const mensal = C.leadsMensal(f);
    const idx = C.meses(per, C.MESES_LEADS).map((m) => C.MESES_LEADS.indexOf(m));
    const k = (c, rot, formato, tipo, bom, dica, extra) => kpi({rot, valor: a[c], formato, tipo, bom, dica, extra,
      delta: variacao(tipo, a[c], b[c]), serie: mensal.map((r) => r[c]), marcar: idx});
    const [campo, tituloNivel] = nivel();
    const grupos = C.leadsPor(f, per, campo).sort((x, y) => y.leads - x.leads);
    const serie = [['leads', 'Leads', 'var(--sf-marca)', 'int'], ['fechados', 'Fechados', 'var(--sf-acento)', 'int']];
    return [
      h('div', {class: 'sf-kpis'},
        k('leads', 'Leads recebidos', 'int', 'abs', 1, null, h('span', {}, `${F.int(a.em_andamento || 0)} em andamento`)),
        k('conversao', 'Conversão', 'pct', 'pp', 1, 'Fechados ÷ (fechados + perdidos)', h('span', {}, `n = ${a.desfecho || 0}`)),
        k('perda_indisp', 'Perdidos por falta de máquina', 'pct', 'pp', -1, 'Perdidos por indisponibilidade ÷ leads com desfecho'),
        k('tempo_medio', 'Tempo até fechar', 'dias', 'rel', -1, 'Dias do envio do lead ao contrato', h('span', {}, `n = ${a.fechados || 0} fechados`))),
      h('div', {class: 'sf-grade'},
        comp(tituloNivel, nomePer(per), barras(grupos, {valor: 'leads', formato: 'int', nota: 'conversao', notaFmt: (v) => `${F.pct0(v)} convertem`,
          nBaixo: (r) => r.desfecho < 5, clicar: aoClicarBarra(campo)}),
        [botaoCSV(`comercial_${campo}`, ['rotulo', 'leads', 'fechados', 'perdidos', 'em_andamento', 'conversao', 'perda_indisp', 'tempo_medio'], () => grupos)],
        'Linhas claras têm menos de 5 leads com desfecho'),
        comp('Mês a mês', 'jan a nov/2026', linhasGraf(serie.map(([c, nome, cor, tf]) => ({nome, cor, values: mensal.map((r) => r[c]), tipFmt: F[tf]})),
          C.MESES_LEADS.map(mesCurto), {yFmt: F.int, marcar: idx}), legenda(serie), 'A faixa destacada é o período escolhido')),
      comp('Comparação mês a mês', '2026 · leads recebidos',
        tabelaMensal({mensal, col: ['leads', 'Leads', 'int', 'abs', 1], extras: [['fechados', 'Fechados', 'int'], ['perdidos', 'Perdidos', 'int'],
          ['conversao', 'Conversão', (r) => (r.conversao == null ? '—' : `${F.pct0(r.conversao)} · n=${r.desfecho}`)]],
          anoTotal: (y) => C.leads(f, y), semAnoAnterior: true}),
        [botaoCSV('comercial_mes_a_mes', ['mes', 'leads', 'fechados', 'perdidos', 'em_andamento', 'conversao', 'perda_indisp', 'tempo_medio'], () => mensal)],
        'A base não tem leads de 2025: não há comparação com o ano anterior. Com poucos leads por mês, uma venda muda muito a conversão.'),
    ];
  };

  // ---------- Desenho ----------
  const nav = document.getElementById('nav');
  SETORES.forEach(([id, rot]) => nav.append(h('button', {type: 'button', 'data-ir': id, onclick: () => mudar({setor: id})}, icone(id), rot)));
  const desenhar = () => {
    const [, titulo] = SETORES.find(([id]) => id === est.setor);
    nav.querySelectorAll('button').forEach((b) => (b.dataset.ir === est.setor ? b.setAttribute('aria-current', 'page') : b.removeAttribute('aria-current')));
    const corpo = est.setor === 'resumo' ? telaResumo() : est.setor === 'oficina' ? telaOficina() : est.setor === 'comercial' ? telaComercial() : telaOp(est.setor, titulo);
    document.getElementById('conteudo').replaceChildren(cabecalho(titulo), filtros(), ...corpo);
    document.title = `${titulo} · Painel LocaMaq`;
  };

  // Tema claro/escuro (guardado só neste navegador).
  const raiz = document.documentElement;
  const temaAtual = () => raiz.dataset.tema || (matchMedia('(prefers-color-scheme: dark)').matches ? 'escuro' : 'claro');
  const pintarTema = () => document.querySelectorAll('[data-tema]').forEach((b) => b.setAttribute('aria-pressed', String(b.dataset.tema === temaAtual())));
  document.querySelectorAll('[data-tema]').forEach((b) => b.addEventListener('click', () => {
    raiz.dataset.tema = b.dataset.tema;
    try { localStorage.setItem('lm-painel-tema', b.dataset.tema); } catch (e) { /* sem armazenamento */ }
    pintarTema();
  }));
  pintarTema();

  let largura = innerWidth, espera;
  addEventListener('resize', () => { if (innerWidth !== largura) { largura = innerWidth; clearTimeout(espera); espera = setTimeout(desenhar, 150); } });
  addEventListener('hashchange', () => { lerEndereco(); desenhar(); });
  document.getElementById('gerado').textContent = dataBR(C.gerado_em);
  lerEndereco();
  desenhar();
})();
