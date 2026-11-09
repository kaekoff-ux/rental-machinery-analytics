// Painel: código do dashboard do Cowork (base.js e drill.js, 07/11/2026), sem alteração de
// fórmulas. Roda sobre o adaptador painel_dash.js, que entrega os dados vindos do banco.

window.lm = (() => {
  d3.formatDefaultLocale({decimal: ',', thousands: '.', grouping: [3], currency: ['R$ ', '']});
  const nf = (o) => new Intl.NumberFormat('pt-BR', o);
  const um = {minimumFractionDigits: 1, maximumFractionDigits: 1};
  const fmts = {
    brl: (v) => 'R$ ' + nf({notation: 'compact', maximumFractionDigits: 1}).format(v),
    brl2: (v) => nf({style: 'currency', currency: 'BRL', minimumFractionDigits: 2, maximumFractionDigits: 2}).format(v),
    brlc: (v) => nf({style: 'currency', currency: 'BRL', maximumFractionDigits: 0}).format(v),
    pct: (v) => nf({style: 'percent', ...um}).format(v),
    pct0: (v) => Math.round(v * 100) + '%',
    spct: (v) => (v >= 0 ? '+' : '−') + nf({style: 'percent', ...um}).format(Math.abs(v)),
    pp: (v) => (v >= 0 ? '+' : '−') + nf(um).format(Math.abs(v * 100)) + ' p.p.',
    int: (v) => nf({maximumFractionDigits: 0}).format(v),
    h: (v) => nf({maximumFractionDigits: 0}).format(v) + ' h',
    h1: (v) => nf(um).format(v) + ' h',
    dias: (v) => nf(um).format(v) + ' dias',
    atraso: (v) => 'atraso médio ' + nf(um).format(v) + ' dias',
    conv: (v) => nf({style: 'percent', maximumFractionDigits: 0}).format(v) + ' convertem',
    txt: (v) => String(v),
  };
  const meses = ['jan', 'fev', 'mar', 'abr', 'mai', 'jun', 'jul', 'ago', 'set', 'out', 'nov', 'dez'];
  const mesCurto = (m) => meses[+m.slice(5, 7) - 1];
  const mesAno = (m) => mesCurto(m) + '/' + m.slice(2, 4);
  const parseWhere = (w) => Object.fromEntries(w.split('&').map((p) => p.split('=').map(decodeURIComponent)));
  const findRow = (rows, el) => {
    if (el.dataset.row != null) return rows[+el.dataset.row];
    if (el.dataset.where) { const w = parseWhere(el.dataset.where); return rows.find((r) => Object.entries(w).every(([k, v]) => String(r[k]) === v)); }
    return rows[0];
  };
  // Escreve um valor formatado e, com data-bom, colore a variação.
  const escrever = (el, v) => {
    el.classList.remove('lm-bom', 'lm-ruim');
    if (v == null || v === '' || (el.dataset.fmt !== 'txt' && !isFinite(Number(v)))) { el.textContent = '—'; return; }
    const x = el.dataset.fmt === 'txt' ? v : Number(v);
    el.textContent = fmts[el.dataset.fmt || 'int'](x);
    if (el.dataset.bom && Math.abs(x) > 1e-9) el.classList.add((el.dataset.bom === 'desce' ? x < 0 : x > 0) ? 'lm-bom' : 'lm-ruim');
  };
  const falha = (el) => { const d = document.createElement('div'); d.className = 'lm-falha'; d.textContent = 'Falha ao carregar'; el.replaceChildren(d); };
  const pronto = (el, id) => {
    const s = dash.data(id).status;
    if (s === 'ok') { el.classList.remove('dash-skeleton'); return true; }
    if (s === 'error') { el.classList.remove('dash-skeleton'); falha(el); return false; }
    el.classList.add('dash-skeleton'); el.replaceChildren(); return false;
  };
  const tip = (box) => {
    let t = box.querySelector('.lm-tip');
    if (!t) { t = document.createElement('div'); t.className = 'lm-tip'; box.appendChild(t); }
    t.hidden = true;
    return {
      show(x, y, titulo, linhas) {
        const head = document.createElement('div'); head.className = 't'; head.textContent = titulo;
        const ls = linhas.map(([cor, nome, val]) => { const l = document.createElement('div'); l.className = 'l'; const i = document.createElement('i'); i.style.background = cor; const s = document.createElement('span'); s.textContent = nome + ': ' + val; l.append(i, s); return l; });
        t.replaceChildren(head, ...ls); t.hidden = false;
        const w = t.offsetWidth, bw = box.clientWidth;
        t.style.left = Math.max(0, Math.min(bw - w, x + 12)) + 'px';
        t.style.top = Math.max(0, y - t.offsetHeight - 8) + 'px';
      },
      hide() { t.hidden = true; },
    };
  };
  const medir = (svg, textos) => {
    const g = svg.append('g');
    const w = d3.max(textos, (s) => g.append('text').text(s).node().getComputedTextLength()) || 0;
    g.remove(); return w;
  };
  // Gráfico de linhas usado no painel principal e no detalhamento.
  const linhas = (el, {rotulos, titulos, series, yFmt, yDom}) => {
    const W = Math.max(280, el.clientWidth), H = 240, mt = 10, mb = 26, mr = 12;
    const svg = d3.create('svg').attr('width', '100%').attr('viewBox', `0 0 ${W} ${H}`).attr('role', 'img');
    el.replaceChildren(svg.node());
    const todos = series.flatMap((s) => s.values).filter((v) => v != null && isFinite(v));
    const y = d3.scaleLinear(yDom || [Math.min(0, d3.min(todos) ?? 0), (d3.max(todos) || 1) * 1.08], [H - mb, mt]).nice();
    const ticks = y.ticks(5);
    const ml = Math.ceil(medir(svg, ticks.map(yFmt))) + 10;
    const x = d3.scalePoint(rotulos.map((_, i) => i), [ml, W - mr]).padding(0.3);
    const g = svg.append('g');
    g.selectAll('line').data(ticks).join('line').attr('x1', ml).attr('x2', W - mr).attr('y1', y).attr('y2', y).style('stroke', (d) => (d === 0 ? 'var(--lm-eixo)' : 'var(--lm-grade)'));
    g.selectAll('text.y').data(ticks).join('text').attr('class', 'y').attr('x', ml - 8).attr('y', (d) => y(d)).attr('dy', '0.32em').attr('text-anchor', 'end').text(yFmt);
    const passo = Math.max(1, Math.ceil(rotulos.length / Math.max(1, Math.floor((W - ml) / 46))));
    g.selectAll('text.x').data(rotulos.map((r, i) => [r, i]).filter(([, i]) => i % passo === 0)).join('text').attr('class', 'x')
      .attr('x', ([, i]) => x(i)).attr('y', H - 8).attr('text-anchor', 'middle').text(([r]) => r);
    const linha = d3.line().defined((v) => v != null && isFinite(v)).x((_, i) => x(i)).y((v) => y(v));
    series.forEach((s) => {
      svg.append('path').attr('d', linha(s.values)).attr('fill', 'none').style('stroke', s.cor).attr('stroke-width', 2.2).attr('stroke-linecap', 'round').attr('stroke-linejoin', 'round');
    });
    const regua = svg.append('line').attr('y1', mt).attr('y2', H - mb).style('stroke', 'var(--lm-eixo)').attr('stroke-dasharray', '3 3').attr('opacity', 0);
    const pts = svg.append('g');
    const tp = tip(el);
    const tem = (s, i) => s.values[i] != null && isFinite(s.values[i]);
    svg.append('rect').attr('x', ml).attr('y', 0).attr('width', W - ml - mr).attr('height', H).attr('fill', 'transparent')
      .on('mousemove', (ev) => {
        const [mx] = d3.pointer(ev);
        const i = Math.max(0, Math.min(rotulos.length - 1, Math.round((mx - x(0)) / x.step())));
        const vis = series.filter((s) => tem(s, i));
        regua.attr('x1', x(i)).attr('x2', x(i)).attr('opacity', 1);
        pts.selectAll('circle').data(vis).join('circle').attr('cx', x(i)).attr('cy', (s) => y(s.values[i])).attr('r', 4)
          .style('fill', (s) => s.cor).style('stroke', 'var(--lm-bg)').attr('stroke-width', 2);
        const k = svg.node().getBoundingClientRect().width / W;
        tp.show(x(i) * k, y(d3.max(vis, (s) => s.values[i]) ?? 0) * k, titulos[i], vis.map((s) => [s.cor, s.nome, s.tipFmt(s.values[i])]));
      })
      .on('mouseleave', () => { regua.attr('opacity', 0); pts.selectAll('circle').remove(); tp.hide(); });
  };
  return {fmts, mesCurto, mesAno, findRow, escrever, falha, pronto, tip, medir, linhas};
})();


dash.calc('kpi_ano', {
  inputs: ['mensal'], title: 'Indicadores por ano',
  description: 'Soma os meses de cada ano e calcula utilização, disponibilidade, margem, custo por hora, MTBF e MTTR.',
  fn: (mensal) => ['2024', '2025'].map((ano) => {
    const ms = mensal.filter((m) => m.mes.slice(0, 4) === ano);
    const s = (k) => ms.reduce((t, m) => t + Number(m[k]), 0);
    const receita = s('receita'), corr = s('os_corretiva');
    return {
      ano, receita,
      util_fisica: s('dias_locados') / s('dias_frota'),
      disponibilidade: 1 - s('horas_parada') / s('horas_periodo'),
      margem: (receita - s('custo_manut') - s('depreciacao')) / receita,
      custo_hora: s('custo_manut') / s('horas_trab'),
      mtbf: s('horas_trab') / corr,
      mttr: s('horas_parada_corretiva') / corr,
      pct_corretiva: corr / (s('os_preventiva') + s('os_preditiva') + corr),
    };
  }),
});

dash.calc('inad', {
  inputs: ['faturas_ano'], title: 'Inadimplência por ano',
  description: 'Valor vencido em aberto sobre o valor faturado de cada ano de competência.',
  fn: (faturas_ano) => faturas_ano.map((f) => ({
    ano: f.ano, faturado: Number(f.faturado),
    inadimplencia: Number(f.vencido_aberto) / Number(f.faturado),
    atraso_medio_dias: Number(f.atraso_medio_dias),
  })),
});

dash.calc('kpi_var', {
  inputs: ['kpi_ano', 'inad'], title: 'Variação 2025 contra 2024',
  description: 'Receita e custo em variação percentual; taxas em pontos percentuais.',
  fn: (kpi_ano, inad) => {
    const a = kpi_ano.find((r) => r.ano === '2024'), b = kpi_ano.find((r) => r.ano === '2025');
    const ia = inad.find((r) => r.ano === '2024'), ib = inad.find((r) => r.ano === '2025');
    return [{
      receita: b.receita / a.receita - 1,
      util_fisica: b.util_fisica - a.util_fisica,
      disponibilidade: b.disponibilidade - a.disponibilidade,
      margem: b.margem - a.margem,
      custo_hora: b.custo_hora / a.custo_hora - 1,
      inadimplencia: ib.inadimplencia - ia.inadimplencia,
    }];
  },
});

dash.calc('mensal_kpi', {
  inputs: ['mensal'], title: 'Utilização e disponibilidade por mês',
  description: 'Dias locados sobre dias de frota, e horas sem parada sobre horas do período, mês a mês.',
  fn: (mensal) => mensal.map((m) => ({
    mes: m.mes,
    util_fisica: Number(m.dias_locados) / Number(m.dias_frota),
    disponibilidade: 1 - Number(m.horas_parada) / Number(m.horas_periodo),
  })),
});

dash.calc('seg_kpi', {
  inputs: ['segmentos_2025'], title: 'Indicadores por segmento',
  description: 'As mesmas fórmulas dos indicadores anuais, aplicadas a cada segmento em 2025.',
  fn: (segmentos_2025) => segmentos_2025.map((s) => {
    const n = (k) => Number(s[k]);
    return {
      segmento: s.segmento, equipamentos: n('equipamentos'), receita: n('receita'),
      util_fisica: n('dias_locados') / n('dias_frota'),
      disponibilidade: 1 - n('horas_parada') / n('horas_periodo'),
      margem: (n('receita') - n('custo_manut') - n('depreciacao')) / n('receita'),
      custo_hora: n('custo_manut') / n('horas_trab'),
      mtbf: n('horas_trab') / n('os_corretiva'),
      mttr: n('horas_parada_corretiva') / n('os_corretiva'),
    };
  }).sort((a, b) => b.receita - a.receita),
});

dash.calc('seg_top', {
  inputs: ['segmentos_2025'], title: 'Segmento que mais fatura',
  description: 'Segmento de maior receita em 2025 e sua participação na receita total.',
  fn: (segmentos_2025) => {
    const total = segmentos_2025.reduce((t, s) => t + Number(s.receita), 0);
    const top = segmentos_2025.reduce((a, b) => (Number(b.receita) > Number(a.receita) ? b : a));
    return [{segmento: top.segmento, participacao: Number(top.receita) / total}];
  },
});

dash.calc('leads_kpi', {
  inputs: ['leads_status', 'leads_motivo'], title: 'Resumo dos leads de 2026',
  description: 'Conversão sobre leads com desfecho e perdas por falta de máquina sobre o mesmo total.',
  fn: (leads_status, leads_motivo) => {
    const q = (st) => Number((leads_status.find((r) => r.status === st) || {}).leads || 0);
    const total = leads_status.reduce((t, r) => t + Number(r.leads), 0);
    const fechados = q('Fechado'), perdidos = q('Perdidos');
    const indisp = Number((leads_motivo.find((r) => r.motivo === 'Indisponibilidade de máquina') || {}).leads || 0);
    return [{
      total, fechados, perdidos, em_andamento: total - fechados - perdidos,
      conversao: fechados / (fechados + perdidos),
      perda_indisponibilidade: indisp / (fechados + perdidos),
    }];
  },
});

dash.calc('origem_kpi', {
  inputs: ['leads_origem'], title: 'Conversão por origem',
  description: 'Leads por canal e fechados sobre leads com desfecho em cada canal.',
  fn: (leads_origem) => leads_origem.map((o) => ({
    origem: o.origem, leads: Number(o.leads),
    conversao: Number(o.fechados) / (Number(o.fechados) + Number(o.perdidos)),
  })),
});

dash.draw('v', (el) => {
  const id = el.dataset.source;
  if (dash.data(id).status !== 'ok') { el.textContent = '—'; return; }
  const row = lm.findRow(dash.data(id).data, el);
  lm.escrever(el, row ? row[el.dataset.field] : null);
});

dash.draw('hbar', (el) => {
  const id = el.dataset.source;
  if (!lm.pronto(el, id)) return;
  const rows = dash.data(id).data;
  const val = (r) => Number(r[el.dataset.value]);
  const max = Math.max(Number(el.dataset.max || 0), d3.max(rows, val) || 1);
  const fmt = lm.fmts[el.dataset.fmt || 'int'];
  el.replaceChildren(...rows.map((r) => {
    const l = document.createElement('div'); l.className = 'lm-hbar-l';
    const n = document.createElement('span'); n.className = 'n'; n.textContent = r[el.dataset.label];
    const t = document.createElement('span'); t.className = 't';
    const b = document.createElement('span'); b.className = 'b'; b.style.width = (val(r) / max * 100) + '%';
    if (el.dataset.destaque && r[el.dataset.label] === el.dataset.destaque) b.classList.add('lm-alerta');
    t.appendChild(b);
    const v = document.createElement('span'); v.className = 'v';
    const vb = document.createElement('b'); vb.textContent = fmt(val(r)); v.appendChild(vb);
    const nota = Number(r[el.dataset.note]);
    if (el.dataset.note && isFinite(nota) && nota > 0) v.appendChild(document.createTextNode(' · ' + lm.fmts[el.dataset.noteFmt](nota)));
    l.append(n, t, v); return l;
  }));
});

dash.draw('receita', (el) => {
  if (!lm.pronto(el, 'mensal')) return;
  const rows = dash.data('mensal').data;
  const mm = (i) => String(i + 1).padStart(2, '0');
  const ano = (a) => Array.from({length: 12}, (_, i) => { const r = rows.find((m) => m.mes === `${a}-${mm(i)}`); return r ? Number(r.receita) : null; });
  const rot = Array.from({length: 12}, (_, i) => lm.mesCurto(`2025-${mm(i)}`));
  lm.linhas(el, {
    rotulos: rot, titulos: rot, yFmt: lm.fmts.brl,
    series: [
      {nome: '2024', cor: 'var(--lm-terra)', values: ano('2024'), tipFmt: lm.fmts.brlc},
      {nome: '2025', cor: 'var(--lm-verde)', values: ano('2025'), tipFmt: lm.fmts.brlc},
    ],
  });
});

dash.draw('uso', (el) => {
  if (!lm.pronto(el, 'mensal_kpi')) return;
  const rows = dash.data('mensal_kpi').data;
  const rot = rows.map((r) => lm.mesAno(r.mes));
  lm.linhas(el, {
    rotulos: rot, titulos: rot, yDom: [0, 1], yFmt: lm.fmts.pct0,
    series: [
      {nome: 'Disponibilidade', cor: 'var(--lm-verde)', values: rows.map((r) => r.disponibilidade), tipFmt: lm.fmts.pct},
      {nome: 'Utilização', cor: 'var(--lm-laranja)', values: rows.map((r) => r.util_fisica), tipFmt: lm.fmts.pct},
    ],
  });
});

dash.draw('mix', (el) => {
  if (!lm.pronto(el, 'mensal')) return;
  const rows = dash.data('mensal').data.map((m) => ({mes: m.mes, os_preventiva: Number(m.os_preventiva), os_preditiva: Number(m.os_preditiva), os_corretiva: Number(m.os_corretiva)}));
  const tipos = [['os_preventiva', 'Preventiva', 'var(--lm-verde)'], ['os_preditiva', 'Preditiva', 'var(--lm-petroleo)'], ['os_corretiva', 'Corretiva', 'var(--lm-laranja)']];
  const W = Math.max(280, el.clientWidth), H = 220, mt = 8, mb = 26, mr = 6;
  const svg = d3.create('svg').attr('width', '100%').attr('viewBox', `0 0 ${W} ${H}`).attr('role', 'img');
  el.replaceChildren(svg.node());
  const total = (r) => r.os_preventiva + r.os_preditiva + r.os_corretiva;
  const y = d3.scaleLinear([0, d3.max(rows, total)], [H - mb, mt]).nice();
  const ticks = y.ticks(4);
  const ml = Math.ceil(lm.medir(svg, ticks.map(String))) + 10;
  const x = d3.scaleBand(rows.map((r) => r.mes), [ml, W - mr]).padding(0.22);
  svg.selectAll('line.g').data(ticks).join('line').attr('x1', ml).attr('x2', W - mr).attr('y1', y).attr('y2', y).style('stroke', 'var(--lm-grade)');
  svg.selectAll('text.y').data(ticks).join('text').attr('x', ml - 8).attr('y', y).attr('dy', '0.32em').attr('text-anchor', 'end').text((d) => lm.fmts.int(d));
  const passo = Math.max(1, Math.ceil(rows.length / Math.floor((W - ml) / 46)));
  svg.selectAll('text.x').data(rows.filter((_, i) => i % passo === 0)).join('text').attr('x', (r) => x(r.mes) + x.bandwidth() / 2).attr('y', H - 8).attr('text-anchor', 'middle').text((r) => lm.mesAno(r.mes));
  const pilha = d3.stack().keys(tipos.map((t) => t[0]))(rows);
  const tp = lm.tip(el);
  const grupos = svg.append('g');
  pilha.forEach((camada, k) => {
    grupos.append('g').selectAll('rect').data(camada).join('rect')
      .attr('x', (d) => x(d.data.mes)).attr('width', Math.min(32, x.bandwidth()))
      .attr('y', (d) => y(d[1])).attr('height', (d) => Math.max(0, y(d[0]) - y(d[1]) - (k < 2 ? 1 : 0)))
      .attr('rx', k === 2 ? 2 : 0).style('fill', tipos[k][2]);
  });
  svg.append('g').selectAll('rect').data(rows).join('rect')
    .attr('x', (r) => x(r.mes) - x.step() * x.paddingInner() / 2).attr('width', x.step()).attr('y', mt).attr('height', H - mt - mb).attr('fill', 'transparent')
    .on('mousemove', (ev, r) => {
      const k = svg.node().getBoundingClientRect().width / W;
      grupos.selectAll('rect').attr('opacity', (d) => (d.data.mes === r.mes ? 1 : 0.45));
      tp.show(x(r.mes) * k, y(total(r)) * k, lm.mesAno(r.mes), [
        ...tipos.map(([key, nome, cor]) => [cor, nome, lm.fmts.int(r[key])]),
        ['transparent', 'Corretivas', lm.fmts.pct(r.os_corretiva / total(r))],
      ]);
    })
    .on('mouseleave', () => { grupos.selectAll('rect').attr('opacity', 1); tp.hide(); });
});

// Tabela por segmento: cada linha abre o detalhamento daquele segmento.
dash.draw('segtab', (el) => {
  if (dash.data('seg_kpi').status !== 'ok') { el.replaceChildren(); return; }
  const rows = dash.data('seg_kpi').data;
  const max = d3.max(rows, (r) => r.receita);
  const f = lm.fmts;
  el.replaceChildren(...rows.map((r) => {
    const tr = document.createElement('tr'); tr.className = 'lm-clicavel'; tr.dataset.key = r.segmento;
    const cel = (txt) => { const td = document.createElement('td'); td.textContent = txt; return td; };
    const rec = document.createElement('td'); const wrap = document.createElement('span'); wrap.className = 'lm-cel-barra';
    const bar = document.createElement('i'); bar.style.width = (r.receita / max * 4) + 'rem';
    const txt = document.createElement('span'); txt.textContent = f.brl(r.receita); wrap.append(bar, txt); rec.appendChild(wrap);
    const marg = cel(f.pct(r.margem)); if (r.margem < 0) marg.className = 'lm-ruim';
    tr.append(cel(r.segmento), cel(f.int(r.equipamentos)), rec, cel(f.pct(r.util_fisica)), cel(f.pct(r.disponibilidade)), marg, cel(f.brl2(r.custo_hora)), cel(f.h(r.mtbf)), cel(f.h1(r.mttr)));
    return tr;
  }));
});
document.querySelectorAll('#segmentos tbody').forEach((tb) => tb.addEventListener('click', (ev) => {
  const tr = ev.target.closest('tr[data-key]');
  if (tr && window.lmAbrir) window.lmAbrir('receita', {seg: tr.dataset.key});
}));


dash.calc('drill', {
  inputs: ['equip_mes'], title: 'Frota por segmento, filial e máquina',
  description: 'Soma cada máquina-mês em toda a frota, segmento, filial, segmento × filial e máquina, por ano e por mês, e aplica as fórmulas dos indicadores.',
  fn: (equip_mes) => {
    const M = ['receita', 'dias_locados', 'dias_frota', 'horas_periodo', 'horas_parada', 'horas_trab', 'custo_manut', 'depreciacao',
      'os_preventiva', 'os_preditiva', 'os_corretiva', 'horas_parada_corretiva', 'vencido', 'atraso_soma', 'atraso_n'];
    const nos = new Map();
    const add = (chave, nivel, periodo, rotulo, seg, fil, r) => {
      const id = chave + '|' + periodo;
      let n = nos.get(id);
      if (!n) { n = {id, chave, nivel, periodo, rotulo, segmento: seg, filial: fil, eqs: new Set()}; M.forEach((k) => { n[k] = 0; }); nos.set(id, n); }
      M.forEach((k) => { n[k] += Number(r[k]); });
      if (Number(r.dias_frota) > 0) n.eqs.add(r.id_equipamento);
    };
    for (const r of equip_mes) {
      const s = r.segmento, f = r.filial;
      const grupos = [['T', 'T', 'Toda a frota', '', ''], ['S|' + s, 'S', s, s, ''], ['F|' + f, 'F', f, '', f], ['SF|' + s + '|' + f, 'SF', s + ' · ' + f, s, f]];
      for (const [c, nv, rot, gs, gf] of grupos) { add(c, nv, r.mes.slice(0, 4), rot, gs, gf, r); add(c, nv, r.mes, rot, gs, gf, r); }
      add('M|' + r.id_equipamento, 'M', r.mes.slice(0, 4), r.id_equipamento + ' · ' + r.modelo, s, f, r);
    }
    const div = (a, b) => (b ? a / b : null);
    const out = [...nos.values()].map((n) => {
      const os = n.os_preventiva + n.os_preditiva + n.os_corretiva;
      const util = div(n.dias_locados, n.dias_frota), disp = n.horas_periodo ? 1 - n.horas_parada / n.horas_periodo : null;
      return {
        id: n.id, chave: n.chave, nivel: n.nivel, periodo: n.periodo, rotulo: n.rotulo, segmento: n.segmento, filial: n.filial,
        maquinas: n.eqs.size, receita: n.receita, custo_manut: n.custo_manut, depreciacao: n.depreciacao, horas_trab: n.horas_trab,
        dias_locados: n.dias_locados, dias_frota: n.dias_frota, vencido: n.vencido, os_total: os,
        util_fisica: util, disponibilidade: disp, ociosidade: util != null && disp != null ? disp - util : null,
        margem: n.receita ? (n.receita - n.custo_manut - n.depreciacao) / n.receita : null,
        custo_hora: div(n.custo_manut, n.horas_trab), inadimplencia: div(n.vencido, n.receita), atraso_medio: div(n.atraso_soma, n.atraso_n),
        pct_corretiva: div(n.os_corretiva, os), mtbf: div(n.horas_trab, n.os_corretiva), mttr: div(n.horas_parada_corretiva, n.os_corretiva),
        receita_maquina: div(n.receita, n.eqs.size),
      };
    });
    const por = new Map(out.map((o) => [o.id, o]));
    for (const o of out) {
      o.part_receita = div(o.receita, (por.get('T|' + o.periodo) || {}).receita);
      if (o.periodo !== '2025') continue;
      const a = por.get(o.chave + '|2024');
      const dif = (k) => (a && o[k] != null && a[k] != null ? o[k] - a[k] : null);
      const rel = (k) => (a && a[k] && o[k] != null ? o[k] / a[k] - 1 : null);
      Object.assign(o, {d_receita: rel('receita'), d_util: dif('util_fisica'), d_disp: dif('disponibilidade'), d_margem: dif('margem'),
        d_custo_hora: rel('custo_hora'), d_inad: dif('inadimplencia'), d_pct_corretiva: dif('pct_corretiva')});
    }
    return out;
  },
});

dash.calc('drill_leads', {
  inputs: ['leads_det'], title: 'Leads por segmento, cidade e modelo',
  description: 'Conta os leads de 2026 por segmento, cidade, segmento × cidade e modelo pedido, no ano e por mês de envio.',
  fn: (leads_det) => {
    const nos = new Map();
    const add = (chave, nivel, periodo, rotulo, seg, cid, r) => {
      const id = chave + '|' + periodo;
      let n = nos.get(id);
      if (!n) { n = {id, chave, nivel, periodo, rotulo, segmento: seg, filial: cid, leads: 0, fechados: 0, perdidos: 0, indisp: 0, dias_soma: 0}; nos.set(id, n); }
      n.leads += 1;
      if (r.status === 'Fechado') { n.fechados += 1; n.dias_soma += Number(r.dias_fechamento); }
      if (r.status === 'Perdidos') { n.perdidos += 1; if (r.motivo_perda === 'Indisponibilidade de máquina') n.indisp += 1; }
    };
    for (const r of leads_det) {
      const s = r.segmento, c = r.cidade;
      const grupos = [['T', 'T', 'Todos os leads', '', ''], ['S|' + s, 'S', s, s, ''], ['F|' + c, 'F', c, '', c], ['SF|' + s + '|' + c, 'SF', s + ' · ' + c, s, c]];
      for (const [k, nv, rot, gs, gc] of grupos) { add(k, nv, '2026', rot, gs, gc, r); add(k, nv, r.mes_envio, rot, gs, gc, r); }
      add('M|' + r.modelo, 'M', '2026', r.modelo, s, '', r);
    }
    return [...nos.values()].map((n) => {
      const d = n.fechados + n.perdidos;
      return {id: n.id, chave: n.chave, nivel: n.nivel, periodo: n.periodo, rotulo: n.rotulo, segmento: n.segmento, filial: n.filial,
        leads: n.leads, fechados: n.fechados, perdidos: n.perdidos, desfecho: d,
        conversao: d ? n.fechados / d : null, perda_indisp: d ? n.indisp / d : null, tempo_medio: n.fechados ? n.dias_soma / n.fechados : null};
    });
  },
});

// Estado do detalhamento: parâmetros drill (indicador), dim (S, F ou M), seg e fil.
window.lmDrill = (() => {
  const p = () => dash.params();
  const leads = () => p().drill === 'leads';
  const periodo = () => (leads() ? '2026' : '2025');
  const no = () => { const {seg, fil} = p(); return seg && fil ? `SF|${seg}|${fil}` : seg ? `S|${seg}` : fil ? `F|${fil}` : 'T'; };
  // Linhas da tabela no nível atual e o passo seguinte de cada uma.
  const linhas = (rows) => {
    const {dim = 'S', seg, fil} = p(), L = leads();
    const r = rows.filter((x) => x.periodo === periodo());
    if (dim === 'M') return r.filter((x) => x.nivel === 'M');
    if (dim === 'F') {
      if (!fil) return r.filter((x) => x.nivel === 'F');
      if (L || !seg) return r.filter((x) => x.nivel === 'SF' && x.filial === fil);
      return r.filter((x) => x.nivel === 'M' && x.filial === fil && x.segmento === seg);
    }
    if (!seg) return r.filter((x) => x.nivel === 'S');
    if (L) return r.filter((x) => x.nivel === 'M' && x.segmento === seg);
    if (!fil) return r.filter((x) => x.nivel === 'SF' && x.segmento === seg);
    return r.filter((x) => x.nivel === 'M' && x.segmento === seg && x.filial === fil);
  };
  const proximo = (row) => {
    if (row.nivel === 'S') return {seg: row.segmento};
    if (row.nivel === 'F') return {fil: row.filial};
    if (row.nivel === 'SF' && !leads()) return {seg: row.segmento, fil: row.filial};
    return null;
  };
  const fonte = () => (leads() ? 'drill_leads' : 'drill');
  return {p, leads, periodo, no, linhas, proximo, fonte, ordem: {}};
})();

(() => {
  const painel = document.getElementById('detalhe');
  let origem = null;
  const sync = () => {
    const pr = dash.params(), kpi = pr.drill || null;
    if (painel) painel.hidden = !kpi;
    document.querySelectorAll('#detalhe [data-kpi]').forEach((e) => { e.hidden = e.dataset.kpi !== kpi; });
    document.querySelectorAll('#detalhe [data-so]').forEach((e) => { e.hidden = (kpi === 'leads') !== (e.dataset.so === 'leads'); });
    document.querySelectorAll('#detalhe [data-dim]').forEach((b) => b.setAttribute('aria-pressed', String((pr.dim || 'S') === b.dataset.dim)));
    document.querySelectorAll('[data-abrir]').forEach((b) => b.setAttribute('aria-expanded', String(b.dataset.abrir === kpi)));
  };
  const fechar = () => {
    dash.setParams({drill: null, dim: null, seg: null, fil: null}); sync();
    if (origem && origem.scrollIntoView) origem.scrollIntoView({block: 'center'});
    dash.setLink('topo');
  };
  window.lmAbrir = (kpi, extra = {}, de = null) => {
    const pr = dash.params();
    if (pr.drill === kpi && de && de === origem) { fechar(); return; }
    origem = de;
    dash.setParams({drill: kpi, dim: 'S', seg: extra.seg ?? null, fil: extra.fil ?? null}); sync();
    if (painel) requestAnimationFrame(() => painel.scrollIntoView({behavior: 'smooth', block: 'start'}));
    dash.setLink('detalhe');
  };
  document.querySelectorAll('[data-abrir]').forEach((el) => {
    el.addEventListener('click', (ev) => { if (ev.target.closest('#segmentos tbody')) return; window.lmAbrir(el.dataset.abrir, {}, el); });
    el.addEventListener('keydown', (ev) => {
      if (el.tagName !== 'BUTTON' && (ev.key === 'Enter' || ev.key === ' ')) { ev.preventDefault(); window.lmAbrir(el.dataset.abrir, {}, el); }
    });
  });
  document.querySelectorAll('#detalhe [data-fechar]').forEach((b) => b.addEventListener('click', fechar));
  document.querySelectorAll('#detalhe [data-dim]').forEach((b) => b.addEventListener('click', () => { dash.setParams({dim: b.dataset.dim, seg: null, fil: null}); sync(); }));
  document.querySelectorAll('#detalhe .lm-migalha').forEach((nav) => nav.addEventListener('click', (ev) => {
    const b = ev.target.closest('button[data-ir]');
    if (!b) return;
    if (b.dataset.ir === 'raiz') dash.setParams({seg: null, fil: null});
    else if (b.dataset.ir === 'seg') dash.setParams({fil: null});
    else if (b.dataset.ir === 'fil') dash.setParams({seg: null});
    sync();
  }));
  // Clique numa linha desce um nível; clique no cabeçalho ordena.
  if (painel) painel.addEventListener('click', (ev) => {
    const th = ev.target.closest('th button[data-ordem]');
    if (th) {
      const kpi = dash.params().drill, campo = th.dataset.ordem, atual = lmDrill.ordem[kpi];
      lmDrill.ordem[kpi] = {campo, desc: atual && atual.campo === campo ? !atual.desc : campo !== 'rotulo'};
      th.closest('tr').querySelectorAll('th').forEach((x) => x.removeAttribute('aria-sort'));
      th.parentElement.setAttribute('aria-sort', lmDrill.ordem[kpi].desc ? 'descending' : 'ascending');
      dash.draw('drilltab');
      return;
    }
    const tr = ev.target.closest('tr.lm-clicavel[data-key]');
    if (tr) { dash.setParams({seg: tr.dataset.seg || dash.params().seg || null, fil: tr.dataset.fil || dash.params().fil || null}); sync(); }
  });
  dash.onData(sync);
  sync();
})();

// Números do nó selecionado.
dash.draw('dv', (el) => {
  const src = el.dataset.source, id = lmDrill.no() + '|' + lmDrill.periodo();
  el.dataset.where = 'id=' + encodeURIComponent(id);
  if (dash.data(src).status !== 'ok') { el.textContent = '—'; return; }
  const row = dash.data(src).data.find((r) => r.id === id);
  lm.escrever(el, row ? row[el.dataset.field] : null);
});

// Caminho percorrido: segmento e filial (ou cidade) escolhidos.
dash.draw('migalha', (el) => {
  const {dim = 'S', seg, fil} = lmDrill.p();
  const passos = (dim === 'F' ? [['fil', fil], ['seg', seg]] : [['seg', seg], ['fil', fil]]).filter(([, v]) => v);
  el.replaceChildren(...passos.map(([ir, v], i) => {
    const b = document.createElement('button'); b.type = 'button'; b.dataset.ir = ir; b.textContent = v;
    b.className = 'lm-passo' + (i === passos.length - 1 ? ' lm-atual' : '');
    return b;
  }));
});

// Série mensal do nó selecionado.
const LM_SERIES = {
  receita: {y: 'brl', s: [['receita', 'Receita', 'var(--lm-verde)', 'brlc']]},
  uso: {y: 'pct0', dom: [0, 1], s: [['disponibilidade', 'Disponibilidade', 'var(--lm-verde)', 'pct'], ['util_fisica', 'Utilização', 'var(--lm-laranja)', 'pct']]},
  margem: {y: 'pct0', s: [['margem', 'Margem', 'var(--lm-verde)', 'pct']]},
  custo: {y: 'brl2', s: [['custo_hora', 'R$/h', 'var(--lm-terra)', 'brl2']]},
  manut: {y: 'pct0', s: [['pct_corretiva', 'Corretivas', 'var(--lm-laranja)', 'pct']]},
  inad: {y: 'pct0', s: [['inadimplencia', 'Inadimplência', 'var(--lm-laranja)', 'pct']]},
  leads: {y: 'int', s: [['leads', 'Leads', 'var(--lm-verde)', 'int'], ['fechados', 'Fechados', 'var(--lm-laranja)', 'int']]},
};
dash.draw('serie', (el) => {
  const src = el.dataset.source;
  if (!lm.pronto(el, src)) return;
  const cfg = LM_SERIES[el.dataset.serie], chave = lmDrill.no();
  const rows = dash.data(src).data.filter((r) => r.chave === chave && /^\d{4}-\d{2}$/.test(r.periodo)).sort((a, b) => a.periodo.localeCompare(b.periodo));
  const rot = rows.map((r) => lm.mesAno(r.periodo));
  lm.linhas(el, {
    rotulos: rot, titulos: rot, yDom: cfg.dom, yFmt: lm.fmts[cfg.y],
    series: cfg.s.map(([k, nome, cor, f]) => ({nome, cor, values: rows.map((r) => r[k]), tipFmt: lm.fmts[f]})),
  });
});

// Tabela de abertura: colunas, formatos e cores vêm dos cabeçalhos.
dash.draw('drilltab', (el) => {
  const table = el.closest('table'), src = table.dataset.source, kpi = el.closest('[data-kpi]').dataset.kpi;
  if (dash.data(src).status !== 'ok') { el.replaceChildren(); return; }
  const cols = [...table.querySelectorAll('th[data-field]')].map((th) => th.dataset);
  const ord = lmDrill.ordem[kpi] || {campo: el.dataset.ordemPadrao, desc: true};
  const rows = lmDrill.linhas(dash.data(src).data).slice().sort((a, b) => {
    const va = a[ord.campo], vb = b[ord.campo];
    const c = ord.campo === 'rotulo' ? String(va).localeCompare(String(vb), 'pt-BR') : (va ?? -Infinity) - (vb ?? -Infinity);
    return ord.desc ? -c : c;
  });
  const maxes = Object.fromEntries(cols.filter((c) => c.barra).map((c) => [c.field, d3.max(rows, (r) => Math.abs(r[c.field] ?? 0)) || 1]));
  el.replaceChildren(...rows.map((r) => {
    const tr = document.createElement('tr'); tr.dataset.key = r.id;
    const nx = lmDrill.proximo(r);
    if (nx) { tr.classList.add('lm-clicavel'); if (nx.seg) tr.dataset.seg = nx.seg; if (nx.fil) tr.dataset.fil = nx.fil; tr.title = 'Clique para detalhar'; }
    const pequeno = src === 'drill_leads' ? r.desfecho < 5 : r.nivel !== 'M' && r.maquinas < 3;
    if (pequeno) tr.classList.add('lm-n-baixo');
    cols.forEach((c) => {
      const td = document.createElement('td'), v = r[c.field];
      if (c.field === 'rotulo') { td.textContent = v; tr.appendChild(td); return; }
      const ok = v != null && isFinite(v);
      const txt = ok ? lm.fmts[c.fmt](v) : '—';
      if (c.barra && ok) {
        const w = document.createElement('span'); w.className = 'lm-cel-barra';
        const i = document.createElement('i'); i.style.width = (Math.abs(v) / maxes[c.field] * 3.5) + 'rem';
        const s = document.createElement('span'); s.textContent = txt; w.append(i, s); td.appendChild(w);
      } else td.textContent = txt;
      if (ok && c.bom && Math.abs(v) > 1e-9) td.className = (c.bom === 'desce' ? v < 0 : v > 0) ? 'lm-bom' : 'lm-ruim';
      if (ok && c.negativo && v < 0) td.className = 'lm-ruim';
      tr.appendChild(td);
    });
    return tr;
  }));
});


window.lmRedesenhar();
