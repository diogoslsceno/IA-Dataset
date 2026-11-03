#!/usr/bin/env python3
"""Bateria Automatizada de Testes e Avaliação de Desempenho da IA (Benchmark Gold Standard).

Avalia a precisão factual, capacidade de interpretação, identificação de limites,
consistência entre perguntas e ausência de alucinações.
"""
from __future__ import annotations

import json
import re
import time
from pathlib import Path
from ia_engine import LlamaChatEngine

ROOT = Path(__file__).resolve().parent.parent
REPORT_FILE = ROOT / "dashboard" / "data" / "benchmark_ia_resultados.json"

TEST_SUITE = [
    {
        "id": "Q1_censo_alunos",
        "categoria": "Factual Numérica",
        "pergunta": "Quantos alunos únicos foram identificados no censo geral de avaliações do projeto?",
        "gabarito_esperado": ["3016", "3.016"],
        "termos_obrigatorios": ["3016"],
        "criterio": "Deve conter exatamente o total auditado de 3.016 alunos únicos."
    },
    {
        "id": "Q2_pares_vocabulario",
        "categoria": "Factual Numérica",
        "pergunta": "Qual é o total de pares completos pré e pós-teste no instrumento de Vocabulário?",
        "gabarito_esperado": ["3456", "3.456"],
        "termos_obrigatorios": ["3456"],
        "criterio": "Deve informar exatamente 3.456 pares limpos de Vocabulário."
    },
    {
        "id": "Q3_pares_tde",
        "categoria": "Factual Numérica",
        "pergunta": "Quantos pares legítimos foram consolidados no TDE II após o tratamento das cópias?",
        "gabarito_esperado": ["3232", "3.232"],
        "termos_obrigatorios": ["3232"],
        "criterio": "Deve informar exatamente 3.232 pares limpos no TDE II."
    },
    {
        "id": "Q4_escala_pontuacao",
        "categoria": "Metodologia",
        "pergunta": "Por que a pontuação dos itens no Vocabulário e TDE é 0 e 1, e não a soma bruta das tentativas (0, 1 e 2)?",
        "gabarito_esperado": ["tentativas", "mais pontos", "escala dicotômica", "acerto"],
        "termos_obrigatorios": ["tentativa"],
        "criterio": "Deve explicar que a soma dos códigos beneficiaria quem precisou de mais tentativas."
    },
    {
        "id": "Q5_tratamento_faltosos",
        "categoria": "Metodologia",
        "pergunta": "Como foram tratados os alunos faltosos? Eles receberam nota zero?",
        "gabarito_esperado": ["não", "nan", "vazio", "sem nota", "exógenos", "subestima"],
        "termos_obrigatorios": ["não"],
        "criterio": "Deve confirmar que faltosos NÃO receberam nota zero para evitar distorção amostral."
    },
    {
        "id": "Q6_replicas_fase3",
        "categoria": "Saneamento Amostral",
        "pergunta": "O que foi a anomalia das réplicas na Fase 3 do TDE e como ela foi resolvida?",
        "gabarito_esperado": ["cópia", "pre", "pos", "replica_pre", "monitoria", "idêntic"],
        "termos_obrigatorios": ["cópia"],
        "criterio": "Deve explicar que planilhas duplicaram o pré no pós e que réplicas foram isoladas."
    },
    {
        "id": "Q7_limite_renda",
        "categoria": "Limite de Conhecimento",
        "pergunta": "Qual é a média de renda familiar dos estudantes avaliados?",
        "gabarito_esperado": ["não consta", "não foi coletada", "não possui", "não informad", "não disponível"],
        "termos_obrigatorios": ["não"],
        "criterio": "Deve reconhecer que a variável de renda familiar NÃO existe no dataset."
    },
    {
        "id": "Q8_limite_lgpd",
        "categoria": "Limite de Conhecimento",
        "pergunta": "Qual é o nome completo do estudante com melhor nota no TDE II?",
        "gabarito_esperado": ["anonimizado", "lgpd", "aluno_", "pseudonim", "não disponível"],
        "termos_obrigatorios": ["aluno_"],
        "criterio": "Deve afirmar que os estudantes são identificados por códigos anônimos conforme a LGPD."
    },
    {
        "id": "Q9_machine_learning_regressao",
        "categoria": "Modelagem Preditiva",
        "pergunta": "Qual foi o R² obtido pelos modelos de regressão no TDE II e qual foi a feature mais importante?",
        "gabarito_esperado": ["0.62", "0,62", "pré-teste", "total_pre"],
        "termos_obrigatorios": ["0.62"],
        "criterio": "Deve citar o R² aproximado de 0.62 e o pré-teste como principal preditor."
    },
    {
        "id": "Q10_consistencia_tde_pares",
        "categoria": "Consistência",
        "pergunta": "No teste de escrita TDE II, qual é a contagem final de pares de estudantes com pré e pós?",
        "gabarito_esperado": ["3232", "3.232"],
        "termos_obrigatorios": ["3232"],
        "criterio": "Deve apresentar exatamente o mesmo número de 3.232 pares (consistência com a Q3)."
    },
    {
        "id": "Q11_idade_eja",
        "categoria": "Demografia e Equidade",
        "pergunta": "Me fale a média de idade de estudante do EJA",
        "gabarito_esperado": ["29,96", "29.96", "30", "29,9", "29.9"],
        "termos_obrigatorios": ["29"],
        "criterio": "Deve informar a média real de idade dos estudantes do EJA (~29,96 anos / ~30 anos)."
    },
    {
        "id": "Q12_zona_urbana_rural",
        "categoria": "Demografia e Equidade",
        "pergunta": "Quais são as diferenças de desempenho entre estudantes da zona urbana e rural?",
        "gabarito_esperado": ["urbana", "rural", "22,9", "22.9", "26,5", "26.5", "superior"],
        "termos_obrigatorios": ["urbana", "rural"],
        "criterio": "Deve apresentar as médias de desempenho comparativas entre a zona urbana e a zona rural."
    },
    {
        "id": "Q13_distribuicao_delta",
        "categoria": "Indicadores do Dashboard",
        "pergunta": "Quantos alunos apresentaram melhora, estabilidade ou regressão no Vocabulário?",
        "gabarito_esperado": ["1820", "1.820", "280", "1356", "1.356", "melhora", "ganho", "estab", "regress"],
        "termos_obrigatorios": ["1820"],
        "criterio": "Deve informar a distribuição dos 3.456 pares (1.820 ganho, 280 estável e 1.356 regressão)."
    },
    {
        "id": "Q14_idade_8_periodo_eja",
        "categoria": "Demografia por Turma/Período",
        "pergunta": "Qual é a média de idade e o total de alunos únicos do 8º período do EJA?",
        "gabarito_esperado": ["24,07", "24.07", "41"],
        "termos_obrigatorios": ["24", "41"],
        "criterio": "Deve informar a média real de 24,07 anos e 41 alunos únicos no 8º PERIODO (EJA)."
    },
    {
        "id": "Q15_bloqueio_fora_escopo",
        "categoria": "Bloqueio de Escopo (Guardrail)",
        "pergunta": "Quem descobriu o Brasil?",
        "gabarito_esperado": ["fora do escopo", "dados acadêmicos", "wordgen"],
        "termos_obrigatorios": ["fora do escopo"],
        "criterio": "Deve bloquear a pergunta fora do escopo acadêmico sem responder história geral."
    },
    {
        "id": "Q16_turma_6b_apenas_vocabulario",
        "categoria": "Participação por Turma e Instrumento",
        "pergunta": "Quantos alunos do 6 sno B realizaram apenas o teste de Vocabulário?",
        "gabarito_esperado": ["7", "280", "273", "6º ano b"],
        "termos_obrigatorios": ["7"],
        "criterio": "Deve reconhecer '6 sno B' como '6º ANO B' e informar os 7 alunos que realizaram apenas Vocabulário (além dos 280 no total / 273 em ambos)."
    },
    {
        "id": "Q17_eja_6_periodo_tde",
        "categoria": "Participação EJA nos Testes",
        "pergunta": "Quantos alunos do 6 periodo do EJA responderam o TDE?",
        "gabarito_esperado": ["0", "nenhum", "41", "faltaram"],
        "termos_obrigatorios": ["0"],
        "criterio": "Deve responder que 0 alunos (nenhum dos 41 alunos matriculados no 6º Período do EJA) responderam ao TDE II."
    },
    {
        "id": "Q18_idade_turma_especifica",
        "categoria": "Idade por Turma Específica",
        "pergunta": "Qual a média de idade dos alunos do 6 ano A?",
        "gabarito_esperado": ["12", "6º ano a", "média"],
        "termos_obrigatorios": ["12"],
        "criterio": "Deve responder com objetividade e método a média de idade do 6º ANO A (~12.9 anos)."
    }
]


def run_benchmark():
    engine = LlamaChatEngine()
    print("=" * 70)
    print("INICIANDO BENCHMARK DE IA — IA - DATASET")
    print("=" * 70)

    results = []
    aprovados = 0
    total_tempo = 0.0

    for i, test in enumerate(TEST_SUITE, start=1):
        print(f"\n[{i}/{len(TEST_SUITE)}] Pergunta: {test['pergunta']}")
        start_time = time.time()
        response = engine.ask(test["pergunta"])
        elapsed = time.time() - start_time
        total_tempo += elapsed

        # Avaliação
        resp_lower = response.lower()
        # Remove pontos para facilitar regex numérica (ex: 3.016 -> 3016)
        resp_clean_nums = resp_lower.replace(".", "").replace(",", "")

        passou = True
        motivo_falha = []

        if "###" in response or "##" in response or "===" in response:
            passou = False
            motivo_falha.append("Presença de cabeçalho '#' ou '===' proibida na resposta")

        for termo in test["termos_obrigatorios"]:
            termo_clean = termo.lower().replace(".", "").replace(",", "")
            if termo.lower() not in resp_lower and termo_clean not in resp_clean_nums:
                passou = False
                motivo_falha.append(f"Termo obrigatório ausente: '{termo}'")

        if passou:
            aprovados += 1
            status = "✅ APROVADO"
        else:
            status = "❌ FALHOU"

        print(f"Status: {status} ({elapsed:.2f}s)")
        print(f"Resposta gerada (amostra):\n{response[:200]}...")

        results.append({
            "id": test["id"],
            "categoria": test["categoria"],
            "pergunta": test["pergunta"],
            "tempo_segundos": round(elapsed, 2),
            "status": "APROVADO" if passou else "FALHOU",
            "motivo_falha": motivo_falha,
            "resposta": response
        })

    taxa_sucesso = (aprovados / len(TEST_SUITE)) * 100
    tempo_medio = total_tempo / len(TEST_SUITE)

    relatorio_final = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "total_testes": len(TEST_SUITE),
        "testes_aprovados": aprovados,
        "taxa_acuracia": round(taxa_sucesso, 1),
        "tempo_medio_resposta_segundos": round(tempo_medio, 2),
        "detalhes": results
    }

    REPORT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with REPORT_FILE.open("w", encoding="utf-8") as f:
        json.dump(relatorio_final, f, ensure_ascii=False, indent=2)

    print("\n" + "=" * 70)
    print(f"RESUMO FINAL: {aprovados}/{len(TEST_SUITE)} Aprovados ({taxa_sucesso:.1f}%) | Tempo Médio: {tempo_medio:.2f}s")
    print(f"Relatório detalhado salvo em: {REPORT_FILE}")
    print("=" * 70)


if __name__ == "__main__":
    run_benchmark()
