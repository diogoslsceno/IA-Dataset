import {format} from '../domain/analysis.js';

const esc = x => String(x).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const empty = message => `<div class="empty">${esc(message)}</div>`;

export function comparisonHTML(value,max) {
  if (!value.n) return empty('Não há pares pré e pós completos para os filtros selecionados.');
  const rows = [['Pré',value.pre,'pre'],['Pós',value.post,'post']];
  return `<div style="padding-top:29px">${rows.map(([label,score,cls])=>`<div class="bar-row"><span class="label">${label}</span><div class="track"><div class="bar ${cls}" style="width:${Math.max(0,Math.min(100,score/max*100))}%"></div></div><b>${format(score,1)}</b></div>`).join('')}<div class="axis"><span>0</span><span>${max/2}</span><span>${max}</span></div><div class="legend"><span>Pré-teste</span><span>Pós-teste</span></div></div>`;
}

export function trendHTML(rows,max) {
  if (rows.every(r=>r.pre==null && r.post==null)) return empty('Não há avaliações realizadas para compor a série.');
  const x = i => 56+i*150;
  const y = n => 172-(n/max)*135;
  const line = (key,cls) => {
    const segments=[]; let current=[];
    rows.forEach((r,i)=>{if(r[key]==null){if(current.length)segments.push(current);current=[];}else current.push([x(i),y(r[key])]);});
    if(current.length)segments.push(current);
    return segments.map(s=>`<polyline class="line-${cls}" points="${s.map(p=>p.join(',')).join(' ')}"/>`).join('') + rows.map((r,i)=>r[key]==null?'':`<circle class="point-${cls}" cx="${x(i)}" cy="${y(r[key])}" r="5"><title>${esc(r.fase)} ${cls==='pre'?'Pré':'Pós'}: ${format(r[key],1)} pontos · n=${r[cls==='pre'?'nPre':'nPost']}</title></circle>`).join('');
  };
  return `<svg class="line-chart" viewBox="0 0 420 215" role="img" aria-label="Médias por fase e momento">${[0,.5,1].map(t=>`<line class="line-grid" x1="45" x2="380" y1="${y(max*t)}" y2="${y(max*t)}"/><text class="line-axis" x="10" y="${y(max*t)+4}">${format(max*t)}</text>`).join('')}${line('pre','pre')}${line('post','post')}${rows.map((r,i)=>`<text class="line-axis" x="${x(i)-18}" y="200">${esc(r.fase)}</text>`).join('')}</svg><div class="legend" style="margin:0 0 0 55px"><span>Pré-teste</span><span>Pós-teste</span></div>`;
}

export function socioeconomicHTML(rows,max) {
  if (!rows.length) return empty('Não há escores para o perfil selecionado.');
  return `<div style="padding-top:4px">${rows.map(r=>`<div class="socio-row"><div><label title="${esc(r.name)}">${esc(r.name)}</label><small>n = ${format(r.n)}</small></div><div class="track"><div class="bar" style="width:${Math.max(0,Math.min(100,r.mean/max*100))}%"></div></div><b>${format(r.mean,1)}</b></div>`).join('')}<div class="axis" style="margin-left:112px"><span>0</span><span>${max/2}</span><span>${max}</span></div></div>`;
}
