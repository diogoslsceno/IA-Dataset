// Regras puras de análise; não conhecem DOM, arquivos ou rede.
export const valid = r => r.fez_teste === 1 && Number.isFinite(r.total) && r.replica_pre !== 1;
export const mean = values => values.length ? values.reduce((a,b) => a+b, 0)/values.length : null;
export const unique = values => new Set(values).size;
export const format = (n, digits=0) => n == null ? '—' : new Intl.NumberFormat('pt-BR', {maximumFractionDigits:digits,minimumFractionDigits:digits}).format(n);

export function filtered(records, school, classroom) {
  return records.filter(r => (!school || r.escola === school) && (!classroom || r.turma === classroom));
}

export function indicators(vocab, tde) {
  const all = [...vocab,...tde];
  return {
    students: unique(all.map(r => r.id_aluno)),
    classes: unique(all.map(r => `${r.escola}\u0000${r.turma}`)),
    vocab: vocab.filter(valid).length,
    tde: tde.filter(valid).length
  };
}

export function pairs(records) {
  const byKey = new Map();
  for (const r of records.filter(valid)) {
    const key = `${r.id_aluno}\u0000${r.fase}`;
    const p = byKey.get(key) || {};
    p[r.momento] = r;
    byKey.set(key,p);
  }
  return [...byKey.values()].filter(p => p['Pré'] && p['Pós']);
}

export function pairedComparison(records) {
  const p = pairs(records);
  const deltas = p.map(x => x['Pós'].total-x['Pré'].total);
  const avgDelta = mean(deltas);
  const variance = deltas.length > 1 ? deltas.reduce((s,x) => s+(x-avgDelta)**2,0)/(deltas.length-1) : null;
  const sd = variance == null ? null : Math.sqrt(variance);
  let ganho = 0, estavel = 0, queda = 0;
  for (const d of deltas) {
    if (d > 0) ganho++;
    else if (d === 0) estavel++;
    else queda++;
  }
  return {
    n: p.length,
    pre: mean(p.map(x=>x['Pré'].total)),
    post: mean(p.map(x=>x['Pós'].total)),
    delta: avgDelta,
    sd,
    dz: sd > 0 ? avgDelta/sd : null,
    dist: { ganho, estavel, queda }
  };
}

export function trend(records) {
  const periods = ['Fase 2','Fase 3','Fase 4'];
  return periods.map(fase => {
    const current = records.filter(r => r.fase === fase && valid(r));
    const pre = current.filter(r => r.momento === 'Pré');
    const post = current.filter(r => r.momento === 'Pós');
    return {fase,pre:mean(pre.map(r=>r.total)),post:mean(post.map(r=>r.total)),nPre:pre.length,nPost:post.length};
  });
}

export function longitudinal(records) {
  const moments = ['Fase 2|Pré','Fase 2|Pós','Fase 3|Pré','Fase 3|Pós','Fase 4|Pré','Fase 4|Pós'];
  const byStudent = new Map();
  for (const r of records.filter(valid)) {
    if (!byStudent.has(r.id_aluno)) byStudent.set(r.id_aluno,new Map());
    byStudent.get(r.id_aluno).set(`${r.fase}|${r.momento}`,r.total);
  }
  const cohort = [...byStudent.values()].filter(values=>moments.every(key=>values.has(key)));
  const points = ['Fase 2','Fase 3','Fase 4'].map(fase=>({
    fase,
    pre:mean(cohort.map(values=>values.get(`${fase}|Pré`))),
    post:mean(cohort.map(values=>values.get(`${fase}|Pós`))),
    nPre:cohort.length,nPost:cohort.length
  }));
  return {points,n:cohort.length};
}

export function socioeconomic(records, dimension) {
  const groups = new Map();
  for (const r of records.filter(valid)) {
    const key = r[dimension] || 'Não informado';
    if (!groups.has(key)) groups.set(key, []);
    groups.get(key).push(r.total);
  }
  return [...groups].map(([name,scores])=>({name,n:scores.length,mean:mean(scores)})).sort((a,b)=>b.n-a.n);
}
