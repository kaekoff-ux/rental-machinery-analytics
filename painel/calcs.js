// Cálculos do painel: as fórmulas do dashboard do Cowork (09/11/2026), agora para qualquer
// filtro (filial, segmento, cidade) e período (ano ou mês), com o período de comparação.
window.lmCalc = (() => {
  const D = window.LOCAMAQ_DADOS;
  const tabela = (t) => D[t].linhas.map((l) => Object.fromEntries(D[t].colunas.map((c, i) => [c, l[i]])));
  const EM = tabela('equip_mes'), OS = tabela('os_det'), LEADS = tabela('leads_det');
  const M = ['receita', 'dias_locados', 'dias_frota', 'horas_periodo', 'horas_parada', 'horas_trab', 'custo_manut', 'depreciacao',
    'os_preventiva', 'os_preditiva', 'os_corretiva', 'os_corretiva_h', 'horas_parada_corretiva', 'vencido', 'atraso_soma', 'atraso_n'];
  const MESES_OP = [...new Set(EM.map((r) => r.mes))].sort();
  const MESES_LEADS = [...new Set(LEADS.map((r) => r.mes_envio))].sort();
  const div = (a, b) => (b ? a / b : null);
  const dois = (n) => String(n).padStart(2, '0');

  // Período: '2025' (ano) ou '2025-03' (mês). Comparação: 'anterior' (mês ou ano anterior)
  // ou 'ano' (mesmo mês do ano anterior; para um ano inteiro, os dois são o ano anterior).
  const meses = (per, universo) => (per.length === 4 ? universo.filter((m) => m.startsWith(per)) : [per]);
  const comparado = (per, modo) => {
    if (per.length === 4) return String(+per - 1);
    const [a, m] = per.split('-').map(Number);
    if (modo === 'ano') return `${a - 1}-${dois(m)}`;
    return m === 1 ? `${a - 1}-12` : `${a}-${dois(m - 1)}`;
  };
  const fimDo = (per) => (per.length === 4 ? `${per}-12-31` : `${per}-${dois(new Date(+per.slice(0, 4), +per.slice(5, 7), 0).getDate())}`);
  const inicioDo = (per) => (per.length === 4 ? `${per}-01-01` : `${per}-01`);

  // ----- Operação (receita, frota, manutenção, financeiro): soma máquina-mês e aplica as fórmulas.
  const kpis = (rows) => {
    const s = {}; M.forEach((k) => { s[k] = 0; });
    const eqs = new Set();
    for (const r of rows) { M.forEach((k) => { s[k] += r[k]; }); if (r.dias_frota > 0) eqs.add(r.id_equipamento); }
    if (!rows.length || !s.dias_frota) return null;
    const os = s.os_preventiva + s.os_preditiva + s.os_corretiva;
    const util = div(s.dias_locados, s.dias_frota), disp = s.horas_periodo ? 1 - s.horas_parada / s.horas_periodo : null;
    return {
      maquinas: eqs.size, receita: s.receita, custo_manut: s.custo_manut, depreciacao: s.depreciacao, vencido: s.vencido,
      os_total: os, os_corretiva: s.os_corretiva, horas_trab: s.horas_trab,
      util_fisica: util, disponibilidade: disp, ociosidade: util != null && disp != null ? disp - util : null,
      margem: s.receita ? (s.receita - s.custo_manut - s.depreciacao) / s.receita : null,
      custo_hora: div(s.custo_manut, s.horas_trab), inadimplencia: div(s.vencido, s.receita), atraso_medio: div(s.atraso_soma, s.atraso_n),
      pct_corretiva: div(s.os_corretiva, os), mtbf: div(s.horas_trab, s.os_corretiva), mttr: div(s.horas_parada_corretiva, s.os_corretiva_h),
      receita_maquina: div(s.receita, eqs.size),
    };
  };
  const filtroOp = (f) => (r) => (!f.filial || r.filial === f.filial) && (!f.segmento || r.segmento === f.segmento);
  const doPeriodo = (per, universo) => { const ms = new Set(meses(per, universo)); return (r) => ms.has(r.mes); };
  const op = (f, per) => kpis(EM.filter((r) => filtroOp(f)(r) && doPeriodo(per, MESES_OP)(r)));
  const opPor = (f, per, campo) => {
    const grupos = new Map();
    for (const r of EM.filter((x) => filtroOp(f)(x) && doPeriodo(per, MESES_OP)(x))) {
      const k = r[campo];
      if (!grupos.has(k)) grupos.set(k, {rotulo: campo === 'id_equipamento' ? `${k} · ${r.modelo}` : k, chave: k, rows: []});
      grupos.get(k).rows.push(r);
    }
    return [...grupos.values()].map((g) => ({rotulo: g.rotulo, chave: g.chave, ...kpis(g.rows)})).filter((g) => g.maquinas != null);
  };
  const opMensal = (f) => MESES_OP.map((m) => ({mes: m, ...(op(f, m) || {})}));
  const meta = (f, per) => {
    const atual = op(f, per), base = op(f, comparado(per, 'ano'));
    if (!atual || !base || !base.receita) return null;
    return {receita: atual.receita, meta: base.receita * 1.05, atingimento: atual.receita / (base.receita * 1.05)};
  };

  // ----- Oficina: ordens de serviço; "na oficina" = aberta até o fim do período e não concluída até lá.
  const diasEntre = (a, b) => Math.round((Date.parse(b) - Date.parse(a)) / 864e5);
  const P90 = {};
  for (const t of new Set(OS.map((o) => o.tipo))) {
    const s = OS.filter((o) => o.tipo === t && o.data_conclusao).map((o) => diasEntre(o.data_abertura, o.data_conclusao)).sort((a, b) => a - b);
    const pos = (s.length - 1) * 0.9, i = Math.floor(pos);
    P90[t] = s[i] + (s[Math.min(i + 1, s.length - 1)] - s[i]) * (pos - i);
  }
  const filtroOS = (f) => (o) => (!f.filial || o.filial === f.filial) && (!f.segmento || o.segmento === f.segmento);
  const oficinaRows = (rows, per) => {
    const ini = inicioDo(per), fim = fimDo(per), eqs = new Set();
    let naOficina = 0, acima = 0, abertas = 0, concluidas = 0, corrN = 0, corrDias = 0, maior = null, servico = '';
    for (const o of rows) {
      if (o.data_abertura <= fim && (!o.data_conclusao || o.data_conclusao > fim)) {
        const idade = diasEntre(o.data_abertura, fim);
        naOficina += 1; eqs.add(o.id_equipamento);
        if (idade > P90[o.tipo]) acima += 1;
        if (maior == null || idade > maior) { maior = idade; servico = o.descricao_falha; }
      }
      if (o.data_abertura >= ini && o.data_abertura <= fim) abertas += 1;
      if (o.data_conclusao && o.data_conclusao >= ini && o.data_conclusao <= fim) {
        concluidas += 1;
        if (o.tipo === 'Corretiva') { corrN += 1; corrDias += diasEntre(o.data_abertura, o.data_conclusao); }
      }
    }
    return {na_oficina: naOficina, maquinas: eqs.size, acima_prazo: acima, abertas, concluidas,
      prazo_corretiva: corrN ? corrDias / corrN : null, n_corretivas: corrN, dias_aberta: maior, servico};
  };
  const oficina = (f, per) => oficinaRows(OS.filter(filtroOS(f)), per);
  const oficinaPor = (f, per, campo) => {
    const grupos = new Map();
    for (const o of OS.filter(filtroOS(f))) {
      const k = o[campo];
      if (!grupos.has(k)) grupos.set(k, {rotulo: campo === 'id_equipamento' ? `${k} · ${o.modelo}` : k, chave: k, rows: []});
      grupos.get(k).rows.push(o);
    }
    return [...grupos.values()].map((g) => ({rotulo: g.rotulo, chave: g.chave, ...oficinaRows(g.rows, per)}));
  };
  const oficinaMensal = (f) => MESES_OP.map((m) => ({mes: m, ...oficina(f, m)}));
  const linhasOS = (f, per) => {
    const fim = fimDo(per);
    return OS.filter((o) => filtroOS(f)(o) && o.data_abertura <= fim && (!o.data_conclusao || o.data_conclusao > fim))
      .map((o) => ({...o, dias_aberta: diasEntre(o.data_abertura, fim), prazo_p90: Math.round(P90[o.tipo])}));
  };

  // ----- Comercial: leads pelo mês de envio; conversão sobre os leads com desfecho.
  const filtroLead = (f) => (r) => (!f.cidade || r.cidade === f.cidade) && (!f.segmento || r.segmento === f.segmento);
  const resumoLeads = (rows) => {
    if (!rows.length) return null;
    let fechados = 0, perdidos = 0, indisp = 0, dias = 0;
    for (const r of rows) {
      if (r.status === 'Fechado') { fechados += 1; dias += r.dias_fechamento; }
      if (r.status === 'Perdidos') { perdidos += 1; if (r.motivo_perda === 'Indisponibilidade de máquina') indisp += 1; }
    }
    const d = fechados + perdidos;
    return {leads: rows.length, fechados, perdidos, em_andamento: rows.length - d, desfecho: d,
      conversao: d ? fechados / d : null, perda_indisp: d ? indisp / d : null, tempo_medio: fechados ? dias / fechados : null};
  };
  const leads = (f, per) => {
    const ms = new Set(meses(per, MESES_LEADS));
    return resumoLeads(LEADS.filter((r) => filtroLead(f)(r) && ms.has(r.mes_envio)));
  };
  const leadsPor = (f, per, campo) => {
    const ms = new Set(meses(per, MESES_LEADS)), grupos = new Map();
    for (const r of LEADS.filter((x) => filtroLead(f)(x) && ms.has(x.mes_envio))) {
      if (!grupos.has(r[campo])) grupos.set(r[campo], []);
      grupos.get(r[campo]).push(r);
    }
    return [...grupos.entries()].map(([k, rows]) => ({rotulo: k, chave: k, ...resumoLeads(rows)}));
  };
  const leadsMensal = (f) => MESES_LEADS.map((m) => ({mes: m, ...(leads(f, m) || {leads: 0, fechados: 0, perdidos: 0, desfecho: 0})}));

  const valores = (campo, universo) => [...new Set(universo.map((r) => r[campo]))].sort((a, b) => a.localeCompare(b, 'pt-BR'));
  return {
    MESES_OP, MESES_LEADS, P90, gerado_em: D.gerado_em,
    filiais: valores('filial', EM), segmentos: valores('segmento', EM), cidades: valores('cidade', LEADS),
    comparado, meses, op, opPor, opMensal, meta, oficina, oficinaPor, oficinaMensal, linhasOS, leads, leadsPor, leadsMensal,
  };
})();
