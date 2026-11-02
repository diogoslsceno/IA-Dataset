import {loadDatasets} from '../src/infrastructure/repository.js';
import {dashboardView} from '../src/application/dashboard.js';
import {format} from '../src/domain/analysis.js';
import {comparisonHTML,trendHTML,socioeconomicHTML} from '../src/presentation/charts.js';
import {initChatWidget} from '../src/presentation/chat.js';

const $ = id => document.getElementById(id);
let data;
const inputs = {school:$('school'),classroom:$('classroom'),category:$('category'),dimension:$('dimension'),scaleMode:$('scale-mode')};

function option(value) {const o=document.createElement('option');o.value=value;o.textContent=value;return o;}
function options(select,values,caption) {const current=select.value;select.replaceChildren(option(''),...[...values].sort((a,b)=>a.localeCompare(b,'pt-BR')).map(option));select.options[0].textContent=caption;if(values.has(current))select.value=current;}
function updateOptions() {
  const all=[...data.vocab,...data.tde];
  options(inputs.school,new Set(all.map(r=>r.escola)),'Todas as escolas');
  options(inputs.classroom,new Set(all.filter(r=>!inputs.school.value||r.escola===inputs.school.value).map(r=>r.turma)),'Todas as turmas');
}
function render() {
  const view=dashboardView(data,{school:inputs.school.value,classroom:inputs.classroom.value,category:inputs.category.value,dimension:inputs.dimension.value});
  const {indicators:k,comparison:c}=view;
  $('kpi-students').textContent=format(k.students);$('kpi-classes').textContent=format(k.classes);
  $('kpi-vocab').textContent=format(k.vocab);$('kpi-tde').textContent=format(k.tde);
  
  const isPercent = inputs.scaleMode.value === 'percent';
  const rawMax = view.category === 'tde' ? 40 : 50;
  const factor = isPercent ? (100 / rawMax) : 1;
  const max = isPercent ? 100 : rawMax;
  
  const scaledComparison = {
    ...c,
    pre: c.pre != null ? c.pre * factor : null,
    post: c.post != null ? c.post * factor : null,
    delta: c.delta != null ? c.delta * factor : null
  };
  const scaledPoints = view.longitudinal.points.map(p => ({
    ...p,
    pre: p.pre != null ? p.pre * factor : null,
    post: p.post != null ? p.post * factor : null
  }));
  const scaledSocio = view.socioeconomic.map(s => ({
    ...s,
    mean: s.mean != null ? s.mean * factor : null
  }));

  $('scale-chip').textContent=isPercent ? '0–100% de aproveitamento' : `0–${rawMax} pontos`;
  $('comparison').innerHTML=comparisonHTML(scaledComparison,max);
  $('pair-note').textContent=c.n?`${format(c.n)} pares completos · variação média ${c.delta>=0?'+':''}${format(scaledComparison.delta,1)} ${isPercent?'p.p.':'pontos'}`:'Pares exigem pré e pós na mesma fase e categoria.';
  
  if (c.n && c.dist) {
    const pctG = Math.round(c.dist.ganho / c.n * 100);
    const pctE = Math.round(c.dist.estavel / c.n * 100);
    const pctQ = Math.round(c.dist.queda / c.n * 100);
    $('delta-dist').innerHTML = `Distribuição: <b>▲ Ganho:</b> ${format(c.dist.ganho)} (${pctG}%) &nbsp;|&nbsp; <b>■ Estável:</b> ${format(c.dist.estavel)} (${pctE}%) &nbsp;|&nbsp; <b>▼ Regressão:</b> ${format(c.dist.queda)} (${pctQ}%)`;
  } else {
    $('delta-dist').textContent = '';
  }

  $('effect-value').textContent=format(c.dz,2);
  const magnitude=c.dz==null?'Sem dados suficientes':Math.abs(c.dz)<.2?'Muito pequeno':Math.abs(c.dz)<.5?'Pequeno':Math.abs(c.dz)<.8?'Médio':'Grande';
  $('effect-label').textContent=magnitude;
  $('effect-detail').textContent=c.dz==null?'É preciso ter ao menos 2 pares com variação entre as diferenças.':`${format(c.n)} pares · ${c.dz<0?'queda':'ganho'} médio padronizado`;
  $('effect-ring-value').textContent=c.dz==null?'—':format(Math.abs(c.dz),2);
  $('effect-ring').style.setProperty('--fill',`${c.dz==null?0:Math.min(100,Math.abs(c.dz)/.8*100)}%`);
  $('trend').innerHTML=trendHTML(scaledPoints,max);
  $('trend-note').textContent=view.longitudinal.n?`Mesma coorte de ${format(view.longitudinal.n)} alunos com pré e pós completos nas três fases.`:'Não há alunos com as seis avaliações completas nos filtros atuais.';
  $('socio').innerHTML=socioeconomicHTML(scaledSocio,max);
  $('socio-note').textContent='Categorias não informadas são exibidas separadamente; esta associação é descritiva, não causal.';
  $('status').textContent='';
}

try {
  data=await loadDatasets();
  updateOptions();
  inputs.school.addEventListener('change',()=>{inputs.classroom.value='';updateOptions();render();});
  for(const key of ['classroom','category','dimension','scaleMode']) inputs[key].addEventListener('change',render);
  $('clear').addEventListener('click',()=>{inputs.school.value='';inputs.classroom.value='';inputs.category.value='vocabulario';inputs.dimension.value='zona';inputs.scaleMode.value='raw';updateOptions();render();});
  render();
  initChatWidget();
} catch(error) { $('status').textContent=`Erro ao carregar dados: ${error.message}. Execute python3 dashboard/prepare_data.py e abra via servidor HTTP local.`; }
