import test from 'node:test';
import assert from 'node:assert/strict';
import {indicators, pairedComparison, longitudinal} from '../src/domain/analysis.js';

const r=(id,categoria,fase,momento,total,fez_teste=1)=>({id_aluno:id,categoria,fase,momento,total,fez_teste,escola:'ESCOLA',turma:'6º ANO A'});

test('alunos e turmas são únicos entre instrumentos; só provas com escore contam',()=>{
  const x=indicators([r('A','vocabulario','Fase 2','Pré',20),r('A','vocabulario','Fase 2','Pós',null,0)], [r('A','tde','Fase 2','Pré',40),r('B','tde','Fase 2','Pré',null,0)]);
  assert.deepEqual(x,{students:2,classes:1,vocab:1,tde:1});
});

test('effect size usa diferenças pareadas e ignora faltosos e fases cruzadas',()=>{
  const rows=[r('A','vocabulario','Fase 2','Pré',10),r('A','vocabulario','Fase 2','Pós',14),r('B','vocabulario','Fase 2','Pré',20),r('B','vocabulario','Fase 2','Pós',26),r('C','vocabulario','Fase 2','Pré',30),r('C','vocabulario','Fase 3','Pós',35),r('D','vocabulario','Fase 2','Pré',10),r('D','vocabulario','Fase 2','Pós',null,0)];
  const x=pairedComparison(rows);
  assert.equal(x.n,2);assert.equal(x.pre,15);assert.equal(x.post,20);assert.equal(x.delta,5);
  assert.ok(Math.abs(x.dz-3.5355339059)<1e-8);
});

test('provas marcadas como replica_pre são ignoradas nos indicadores e pares',()=>{
  const rows=[
    r('A','tde','Fase 3','Pré',15),
    {...r('A','tde','Fase 3','Pós',15), replica_pre: 1},
    r('B','tde','Fase 3','Pré',10),
    r('B','tde','Fase 3','Pós',20)
  ];
  const c = pairedComparison(rows);
  assert.equal(c.n, 1);
  assert.equal(c.pre, 10);
  assert.equal(c.post, 20);
  assert.equal(c.dist.ganho, 1);
  assert.equal(c.dist.estavel, 0);
  assert.equal(c.dist.queda, 0);
});

test('série longitudinal mantém a mesma coorte nos seis pontos',()=>{
  const rows=[];
  for(const fase of ['Fase 2','Fase 3','Fase 4']) for(const momento of ['Pré','Pós']) rows.push(r('A','vocabulario',fase,momento,10));
  rows.push(r('B','vocabulario','Fase 2','Pré',50));
  const x=longitudinal(rows);
  assert.equal(x.n,1);assert.equal(x.points.length,3);assert.equal(x.points[0].pre,10);assert.equal(x.points[2].post,10);
});
