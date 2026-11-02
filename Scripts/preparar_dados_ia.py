#!/usr/bin/env python3
"""Script de Preparação e Estruturação de Dados para a IA (Llama 3.2).

Organiza os dados do projeto IA - Dataset em dois formatos complementares:
1. Base de Conhecimento Semântica (JSON estruturado em tópicos/documentos para RAG).
2. Tabela de Estatísticas Consolidadas (médias, contagens por escola, turma e fase para consulta determinística).
"""
from __future__ import annotations

import csv
import json
from pathlib import Path
import pandas as pd
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "dashboard" / "data"
OUT_DIR = ROOT / "Contexts"


def build_knowledge_base() -> list[dict]:
    """Constrói os blocos conceituais e metodológicos para a base vetorial/semântica."""
    docs = [
        {
            "id": "visao_geral_projeto",
            "categoria": "Visão Geral",
            "titulo": "Projeto WordGen / NEES - Avaliações Educacionais",
            "conteudo": (
                "O projeto analisa o desempenho escolar de estudantes do Ensino Fundamental II "
                "(6º ao 9º ano) e EJA na rede municipal de ensino, acompanhados ao longo de três fases: "
                "Fase 2 (2023.2), Fase 3 (2024.1) e Fase 4 (2024.2). O censo oficial auditado comprova "
                "3.016 alunos únicos cadastrados nas avaliações através do identificador anonimizado canônico "
                "(ALUNO_[HEX]), dos quais 2.673 realizaram ao menos um teste e 343 faltaram em todas as aplicações. "
                "Foram avaliadas 6 escolas municipais principais: EMEB Natanael da Silva (NASI), EMEB Padre Anchieta (PEAN), "
                "EMEF Padre José dos Santos Mousinho (PJSM), EMEB Professora Maria Queiroz Ferro (PMQF), "
                "EMEB Professor Ricardo Vieira de Lima (PRVL) e EMEB Expedito Porfírio dos Santos (VEXP)."
            )
        },
        {
            "id": "instrumentos_avaliativos",
            "categoria": "Metodologia",
            "titulo": "Instrumentos Avaliativos: Vocabulário e TDE II",
            "conteudo": (
                "Foram aplicados dois instrumentos independentes: "
                "1. Avaliação de Vocabulário: Contém 50 itens (Q1 a Q50). Pontuação máxima de 50 pontos. "
                "2. Teste de Desempenho Escolar II (TDE II - Subteste de Escrita): Contém 40 itens (P1 a P40). "
                "Pontuação máxima de 40 pontos. "
                "Ambos os instrumentos utilizam a regra psicométrica de escala dicotômica unificada: "
                "nota 0 para resposta errada ou item deixado em branco por aluno presente; nota 1 para qualquer "
                "acerto (seja na primeira ou em tentativas posteriores). A soma bruta de códigos de tentativa "
                "foi descartada porque daria mais pontos a alunos que precisaram de mais tentativas para acertar."
            )
        },
        {
            "id": "valores_ausentes_imputacao",
            "categoria": "Metodologia",
            "titulo": "Tratamento de Valores Ausentes e Faltosos",
            "conteudo": (
                "Existe uma distinção rigorosa entre mecanismos de ausência: "
                "1. Alunos Faltosos (fez_teste = 0): A falta decorre de fatores exógenos (doença, transporte). "
                "Forçar nota zero nos faltosos subestimaria a proficiência real em 25%. Portanto, faltosos têm "
                "escore 'total = NaN' e não entram no cálculo de médias nem no tamanho de efeito. "
                "2. Omissão Parcial de Item em Alunos Presentes (fez_teste = 1): Quando o aluno compareceu mas "
                "não respondeu determinado item, o item computa 0.0 (imputação zero conservadora/psicométrica)."
            )
        },
        {
            "id": "tratamento_replicas_fase3",
            "categoria": "Saneamento Amostral",
            "titulo": "Detecção e Isolamento de Réplicas no Pós-Teste (Fase 3 TDE II)",
            "conteudo": (
                "Na Fase 3 do TDE II, planilhas administrativas de monitoria duplicaram vetores inteiros de "
                "respostas do pré-teste nas colunas do pós-teste (com taxas de cópia de até 98,8% na Escola Ricardo Vieira). "
                "O pipeline de consolidação implementou coalescência cadastral e priorização de provas reais. "
                "Registros onde 100% dos itens do pós-teste coincidem com o pré-teste de forma idêntica receberam a flag "
                "'replica_pre = 1' e foram expurgados da formação de pares longitudinais primários. "
                "Isso convergiu os pares de TDE de 4.025 para 3.232 pares limpos, atingindo 99,0% de concordância "
                "com a referência de auditoria oficial (3.199 pares), eliminando o falso pico de ganho zero (delta = 0)."
            )
        },
        {
            "id": "qualidade_6_dimensoes",
            "categoria": "Qualidade de Dados",
            "titulo": "Auditoria das 6 Dimensões da Qualidade",
            "conteudo": (
                "A base consolidada foi auditada formalmente conforme 6 dimensões de qualidade da informação: "
                "1. Completude: 100% dos itens respondidos nas aplicações válidas dos dois instrumentos. "
                "2. Unicidade: 100% de unicidade por chave (aluno, fase, momento). "
                "3. Validade: 100% dos itens no domínio legal dicotômico (0 ou 1). "
                "4. Consistência: 100% no Vocabulário e 96,5% no TDE II (as réplicas da Fase 3 foram isoladas). "
                "5. Acurácia: 100% de concordância exata entre a soma dos itens e o escore total registrado. "
                "6. Temporalidade: 100% dos registros possuem fase e ciclo cronológico bem definidos (2023.2 a 2024.2)."
            )
        },
        {
            "id": "machine_learning_resultados",
            "categoria": "Modelagem Preditiva",
            "titulo": "Resultados de Machine Learning sem Data Leakage",
            "conteudo": (
                "Foram treinados modelos de Aprendizado de Máquina com validação cruzada agrupada por turmas "
                "(GroupKFold com 5 splits sobre 80 turmas de Vocabulário e 85 turmas de TDE II), garantindo zero "
                "vazamento de dados entre treino e teste. "
                "Modelos de Regressão (Predição do escore pós-intervenção): "
                "- Vocabulário: Random Forest Regressor atingiu R² = 0.586 e RMSE = 6.12 (baseline R² = -0.01). "
                "- TDE II: Ridge / Random Forest atingiram R² = 0.623 e RMSE = 7.55 (baseline R² = -0.02). "
                "A feature mais importante em ambos os modelos é o escore pré-teste (88% a 94% de importância), "
                "seguida por idade, fase escolar e zona geográfica. "
                "Modelos de Classificação (Risco de baixo ganho / delta <= 0): "
                "- Gradient Boosting Classifier no TDE II atingiu ROC-AUC = 0.712 e Acurácia de 65.8% (frente a 53.1% do baseline)."
            )
        },
        {
            "id": "limites_conhecimento",
            "categoria": "Governança e Limites",
            "titulo": "Variáveis Ausentes e Limitações do Dataset",
            "conteudo": (
                "Variáveis NÃO disponíveis no conjunto de dados: "
                "1. Renda familiar, renda per capita ou classe econômica não foram coletadas nas planilhas escolares. "
                "2. Notas bimestrais ou notas de outras disciplinas (matemática, ciências, história) não constam na base. "
                "3. Nome civil completo dos estudantes foi pseudonimizado com identificadores hash (ALUNO_[HEX]) para "
                "estrito cumprimento da LGPD e proteção da privacidade dos menores de idade. "
                "Caso seja questionado sobre renda ou dados nominais, a IA deve esclarecer que essas informações não existem no dataset."
            )
        }
    ]
    return docs


def _compute_slice_metrics(grp_all: pd.DataFrame, grp_v: pd.DataFrame, grp_t: pd.DataFrame) -> dict:
    """Calcula métricas completas de participação, interseção entre instrumentos, idades e pares Pré/Pós."""
    u_all = set(grp_all["id_aluno"].unique())
    v_val = grp_v[(grp_v["fez_teste"] == 1) & (grp_v["total"].notna())]
    t_val = grp_t[(grp_t["fez_teste"] == 1) & (grp_t["total"].notna())]

    u_v = set(v_val["id_aluno"].unique())
    u_t = set(t_val["id_aluno"].unique())
    u_eval = u_v | u_t

    u_grp = grp_all.sort_values("fez_teste", ascending=False).drop_duplicates("id_aluno")
    ages = u_grp["idade"].dropna()

    # Pares Vocabulário
    v_pre = v_val[v_val["momento"] == "Pré"]
    v_pos = v_val[(v_val["momento"] == "Pós") & (v_val.get("replica_pre", 0) == 0)]
    v_pairs = pd.merge(v_pre, v_pos, on=["id_aluno", "fase"], suffixes=("_pre", "_pos"))
    v_delta = (v_pairs["total_pos"] - v_pairs["total_pre"]) if len(v_pairs) > 0 else pd.Series(dtype=float)
    v_dz = float(round(v_delta.mean() / v_delta.std(ddof=1), 3)) if len(v_pairs) > 1 and v_delta.std(ddof=1) > 0 else None

    # Pares TDE II
    t_pre = t_val[t_val["momento"] == "Pré"]
    t_pos = t_val[(t_val["momento"] == "Pós") & (t_val.get("replica_pre", 0) == 0)]
    t_pairs = pd.merge(t_pre, t_pos, on=["id_aluno", "fase"], suffixes=("_pre", "_pos"))
    t_delta = (t_pairs["total_pos"] - t_pairs["total_pre"]) if len(t_pairs) > 0 else pd.Series(dtype=float)
    t_dz = float(round(t_delta.mean() / t_delta.std(ddof=1), 3)) if len(t_pairs) > 1 and t_delta.std(ddof=1) > 0 else None

    return {
        "alunos_unicos": int(len(u_all)),
        "alunos_avaliados": int(len(u_eval)),
        "alunos_faltosos": int(len(u_all - u_eval)),
        "alunos_vocab_total": int(len(u_v)),
        "alunos_tde_total": int(len(u_t)),
        "alunos_apenas_vocab": int(len(u_v - u_t)),
        "alunos_apenas_tde": int(len(u_t - u_v)),
        "alunos_ambos_testes": int(len(u_v & u_t)),
        "escolas_unicas": int(grp_all["escola"].nunique()),
        "idade_media": float(round(ages.mean(), 2)) if len(ages) > 0 else None,
        "idade_mediana": float(round(ages.median(), 2)) if len(ages) > 0 else None,
        "idade_desvio_padrao": float(round(ages.std(ddof=1), 2)) if len(ages) > 1 else 0.0,
        "idade_minima": int(ages.min()) if len(ages) > 0 else None,
        "idade_maxima": int(ages.max()) if len(ages) > 0 else None,
        "vocab_avaliacoes": int(len(v_val)),
        "vocab_media": float(round(v_val["total"].mean(), 2)) if len(v_val) > 0 else None,
        "vocab_pares": int(len(v_pairs)),
        "vocab_media_pre": float(round(v_pairs["total_pre"].mean(), 2)) if len(v_pairs) > 0 else None,
        "vocab_media_pos": float(round(v_pairs["total_pos"].mean(), 2)) if len(v_pairs) > 0 else None,
        "vocab_delta": float(round(v_delta.mean(), 2)) if len(v_pairs) > 0 else None,
        "vocab_dz": v_dz,
        "tde_avaliacoes": int(len(t_val)),
        "tde_media": float(round(t_val["total"].mean(), 2)) if len(t_val) > 0 else None,
        "tde_pares": int(len(t_pairs)),
        "tde_media_pre": float(round(t_pairs["total_pre"].mean(), 2)) if len(t_pairs) > 0 else None,
        "tde_media_pos": float(round(t_pairs["total_pos"].mean(), 2)) if len(t_pairs) > 0 else None,
        "tde_delta": float(round(t_delta.mean(), 2)) if len(t_pairs) > 0 else None,
        "tde_dz": t_dz,
    }


def generate_statistics() -> dict:
    """Gera tabelas estatísticas exatas para a consulta determinística do chatbot."""
    stats = {}
    for cat in ["vocabulario", "tde"]:
        path = DATA_DIR / f"{cat}.csv"
        df = pd.read_csv(path, sep=";")
        valid = df[(df["fez_teste"] == 1) & (df["total"].notna())]
        pre = valid[valid["momento"] == "Pré"]
        pos = valid[(valid["momento"] == "Pós") & (valid.get("replica_pre", 0) == 0)]
        pairs = pd.merge(pre, pos, on=["id_aluno", "fase"], suffixes=("_pre", "_pos")).copy()
        pairs["delta"] = pairs["total_pos"] - pairs["total_pre"]

        # Totais gerais
        cat_stats = {
            "total_registros": len(df),
            "alunos_unicos": int(df["id_aluno"].nunique()),
            "avaliacoes_com_escore": len(valid),
            "faltosos_totais": int((df["fez_teste"] == 0).sum()),
            "total_pares_limpos": len(pairs),
            "media_pre": float(round(pairs["total_pre"].mean(), 2)),
            "media_pos": float(round(pairs["total_pos"].mean(), 2)),
            "delta_medio": float(round(pairs["delta"].mean(), 2)),
            "desvio_padrao_delta": float(round(pairs["delta"].std(ddof=1), 2)),
            "cohen_dz": float(round(pairs["delta"].mean() / pairs["delta"].std(ddof=1), 3)),
            "ganho_alunos": int((pairs["delta"] > 0).sum()),
            "estavel_alunos": int((pairs["delta"] == 0).sum()),
            "queda_alunos": int((pairs["delta"] < 0).sum()),
        }

        # Por Fase
        fases = {}
        for f in sorted(pairs["fase"].unique()):
            pf = pairs[pairs["fase"] == f]
            dz_f = float(round(pf["delta"].mean() / pf["delta"].std(ddof=1), 3)) if len(pf) > 1 and pf["delta"].std(ddof=1) > 0 else 0.0
            fases[f] = {
                "n_pares": len(pf),
                "media_pre": float(round(pf["total_pre"].mean(), 2)),
                "media_pos": float(round(pf["total_pos"].mean(), 2)),
                "delta": float(round(pf["delta"].mean(), 2)),
                "dz": dz_f
            }
        cat_stats["por_fase"] = fases

        # Por Escola
        escolas = {}
        for esc in sorted(pairs["escola_pre"].dropna().unique()):
            pe = pairs[pairs["escola_pre"] == esc]
            dz_e = float(round(pe["delta"].mean() / pe["delta"].std(ddof=1), 3)) if len(pe) > 1 and pe["delta"].std(ddof=1) > 0 else 0.0
            escolas[esc] = {
                "n_pares": len(pe),
                "media_pre": float(round(pe["total_pre"].mean(), 2)),
                "media_pos": float(round(pe["total_pos"].mean(), 2)),
                "delta": float(round(pe["delta"].mean(), 2)),
                "dz": dz_e
            }
        cat_stats["por_escola"] = escolas

        stats[cat] = cat_stats

    # Censo e Demografia Integrada (Vocabulário + TDE)
    df_v = pd.read_csv(DATA_DIR / "vocabulario.csv", sep=";")
    df_t = pd.read_csv(DATA_DIR / "tde.csv", sep=";")
    df_all = pd.concat([df_v, df_t], ignore_index=True)

    uniq_students = df_all.sort_values("fez_teste", ascending=False).drop_duplicates("id_aluno")
    rede_metrics = _compute_slice_metrics(df_all, df_v, df_t)

    stats["censo"] = {
        "total_alunos_unicos": rede_metrics["alunos_unicos"],
        "alunos_avaliados": rede_metrics["alunos_avaliados"],
        "alunos_faltosos": rede_metrics["alunos_faltosos"],
        "alunos_vocab_total": rede_metrics["alunos_vocab_total"],
        "alunos_tde_total": rede_metrics["alunos_tde_total"],
        "alunos_apenas_vocab": rede_metrics["alunos_apenas_vocab"],
        "alunos_apenas_tde": rede_metrics["alunos_apenas_tde"],
        "alunos_ambos_testes": rede_metrics["alunos_ambos_testes"],
        "turmas_vocabulario": int(df_v["turma"].nunique()),
        "turmas_tde": int(df_t["turma"].nunique()),
        "escolas_unicas": int(df_all["escola"].nunique())
    }

    eja_uniq = uniq_students[uniq_students["modalidade"] == "EJA"]
    reg_uniq = uniq_students[uniq_students["modalidade"] != "EJA"]

    # Detalhamento por Período EJA
    por_periodo_eja = {}
    for turma_eja, grp in df_all[df_all["modalidade"] == "EJA"].groupby("turma"):
        u_grp = grp.drop_duplicates("id_aluno")
        ages = u_grp["idade"].dropna()
        escolas_dict = u_grp["escola"].value_counts().to_dict()
        por_periodo_eja[turma_eja] = {
            "alunos_unicos": int(len(u_grp)),
            "turmas_escolas": int(grp["escola"].nunique()),
            "escolas": {k: int(v) for k, v in escolas_dict.items()},
            "avaliacoes_vocabulario": int((df_v[(df_v["turma"] == turma_eja) & (df_v["fez_teste"] == 1)]["total"].notna()).sum()),
            "avaliacoes_tde": int((df_t[(df_t["turma"] == turma_eja) & (df_t["fez_teste"] == 1)]["total"].notna()).sum()),
            "idade_media": float(round(ages.mean(), 2)),
            "idade_desvio_padrao": float(round(ages.std(ddof=1), 2)) if len(ages) > 1 else 0.0,
            "idade_mediana": float(round(ages.median(), 2)),
            "idade_minima": int(ages.min()),
            "idade_maxima": int(ages.max()),
            "fase_origem": "Fase 2 (2023.2)",
            "tabela_origem": "RelaçãoCompletaAlunos__lista_de_alunos.csv (Fase 2 - Pré e Pós-teste)"
        }

    # Detalhamento por Série/Ano Regular
    por_serie_ano = {}
    for serie in ["6º ANO", "7º ANO", "8º ANO", "9º ANO"]:
        grp = df_all[df_all["serie_ano"] == serie]
        gv = df_v[df_v["serie_ano"] == serie]
        gt = df_t[df_t["serie_ano"] == serie]
        por_serie_ano[serie] = _compute_slice_metrics(grp, gv, gt)

    # Detalhamento por Turma completa (incluindo subdivisão por escola)
    por_turma = {}
    for turma_nome, grp in df_all.groupby("turma"):
        gv = df_v[df_v["turma"] == turma_nome]
        gt = df_t[df_t["turma"] == turma_nome]
        t_metrics = _compute_slice_metrics(grp, gv, gt)
        por_escola_turma = {}
        for esc_nome, grp_esc in grp.groupby("escola"):
            gv_esc = gv[gv["escola"] == esc_nome]
            gt_esc = gt[gt["escola"] == esc_nome]
            em = _compute_slice_metrics(grp_esc, gv_esc, gt_esc)
            por_escola_turma[esc_nome] = {
                "alunos_unicos": em["alunos_unicos"],
                "alunos_avaliados": em["alunos_avaliados"],
                "alunos_faltosos": em["alunos_faltosos"],
                "alunos_vocab_total": em["alunos_vocab_total"],
                "alunos_tde_total": em["alunos_tde_total"],
                "alunos_apenas_vocab": em["alunos_apenas_vocab"],
                "alunos_apenas_tde": em["alunos_apenas_tde"],
                "alunos_ambos_testes": em["alunos_ambos_testes"],
                "vocab_avaliacoes": em["vocab_avaliacoes"],
                "vocab_media": em["vocab_media"],
                "tde_avaliacoes": em["tde_avaliacoes"],
                "tde_media": em["tde_media"],
            }
        t_metrics["por_escola"] = por_escola_turma
        por_turma[turma_nome] = t_metrics

    # Detalhamento completo por Escola
    por_escola_completo = {}
    for esc_nome, grp_esc in df_all.groupby("escola"):
        gv_esc = df_v[df_v["escola"] == esc_nome]
        gt_esc = df_t[df_t["escola"] == esc_nome]
        em = _compute_slice_metrics(grp_esc, gv_esc, gt_esc)
        em["turmas"] = sorted(grp_esc["turma"].dropna().unique().tolist())
        em["zona"] = grp_esc["zona"].dropna().iloc[0] if len(grp_esc["zona"].dropna()) > 0 else "N/A"
        por_escola_completo[esc_nome] = em
    stats["por_escola_completo"] = por_escola_completo

    v_val_all = df_v[(df_v["fez_teste"] == 1) & (df_v["total"].notna())]
    t_val_all = df_t[(df_t["fez_teste"] == 1) & (df_t["total"].notna())]

    stats["demografia"] = {
        "idade": {
            "eja": {
                "alunos_unicos": int(len(eja_uniq)),
                "media": float(round(eja_uniq["idade"].dropna().mean(), 2)),
                "desvio_padrao": float(round(eja_uniq["idade"].dropna().std(ddof=1), 2)),
                "mediana": float(round(eja_uniq["idade"].dropna().median(), 2)),
                "minima": int(eja_uniq["idade"].dropna().min()),
                "maxima": int(eja_uniq["idade"].dropna().max())
            },
            "regular": {
                "alunos_unicos": int(len(reg_uniq)),
                "media": float(round(reg_uniq["idade"].dropna().mean(), 2)),
                "desvio_padrao": float(round(reg_uniq["idade"].dropna().std(ddof=1), 2)),
                "mediana": float(round(reg_uniq["idade"].dropna().median(), 2)),
                "minima": int(reg_uniq["idade"].dropna().min()),
                "maxima": int(reg_uniq["idade"].dropna().max())
            },
            "por_periodo_eja": por_periodo_eja,
            "por_serie_ano": por_serie_ano,
            "por_turma": por_turma
        },
        "zona": {
            "urbana": {
                "vocab_avaliados": int((v_val_all["zona"] == "Urbana").sum()),
                "vocab_media": float(round(v_val_all[v_val_all["zona"] == "Urbana"]["total"].mean(), 2)),
                "tde_avaliados": int((t_val_all["zona"] == "Urbana").sum()),
                "tde_media": float(round(t_val_all[t_val_all["zona"] == "Urbana"]["total"].mean(), 2))
            },
            "rural": {
                "vocab_avaliados": int((v_val_all["zona"] == "Rural").sum()),
                "vocab_media": float(round(v_val_all[v_val_all["zona"] == "Rural"]["total"].mean(), 2)),
                "tde_avaliados": int((t_val_all["zona"] == "Rural").sum()),
                "tde_media": float(round(t_val_all[t_val_all["zona"] == "Rural"]["total"].mean(), 2))
            }
        },
        "sexo": {
            "feminino": {
                "vocab_media": float(round(v_val_all[v_val_all["sexo"] == "F"]["total"].mean(), 2)),
                "tde_media": float(round(t_val_all[t_val_all["sexo"] == "F"]["total"].mean(), 2))
            },
            "masculino": {
                "vocab_media": float(round(v_val_all[v_val_all["sexo"] == "M"]["total"].mean(), 2)),
                "tde_media": float(round(t_val_all[t_val_all["sexo"] == "M"]["total"].mean(), 2))
            }
        },
        "distorcao_idade_serie_regular_pct": 10.03
    }

    return stats


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    kb = build_knowledge_base()
    kb_path = OUT_DIR / "base_conhecimento.json"
    with kb_path.open("w", encoding="utf-8") as f:
        json.dump(kb, f, ensure_ascii=False, indent=2)

    stats = generate_statistics()
    stats_path = OUT_DIR / "estatisticas_consolidadas.json"
    with stats_path.open("w", encoding="utf-8") as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)

    print(f"✅ Base de conhecimento gerada com {len(kb)} tópicos em: {kb_path}")
    print(f"✅ Estatísticas consolidadas geradas com sucesso em: {stats_path}")


if __name__ == "__main__":
    main()
