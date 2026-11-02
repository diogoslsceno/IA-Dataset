#!/usr/bin/env python3
"""Pipeline de Modelagem e Machine Learning sem Data Leakage.

Realiza validação cruzada agrupada por Turma/Escola (GroupKFold) sobre os pares
genuínos de Vocabulário e TDE II, avaliando tarefas de Regressão e Classificação.
"""
from __future__ import annotations

import json
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.dummy import DummyRegressor, DummyClassifier
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier, GradientBoostingRegressor, GradientBoostingClassifier
from sklearn.linear_model import Ridge, LogisticRegression
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score, accuracy_score, f1_score, roc_auc_score
from sklearn.model_selection import GroupKFold
from sklearn.preprocessing import OneHotEncoder
from sklearn.tree import DecisionTreeClassifier

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "dashboard" / "data"


def load_pairs(category: str) -> pd.DataFrame:
    path = DATA_DIR / f"{category}.csv"
    if not path.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {path}")
    df = pd.read_csv(path, sep=";")
    valid = df[(df["fez_teste"] == 1) & (df["total"].notna())].copy()
    pre = valid[valid["momento"] == "Pré"].copy()
    pos = valid[(valid["momento"] == "Pós") & (valid.get("replica_pre", 0) == 0)].copy()

    merged = pd.merge(
        pre, pos,
        on=["id_aluno", "fase"],
        suffixes=("_pre", "_pos")
    )
    merged["delta"] = merged["total_pos"] - merged["total_pre"]
    merged["risco_baixo_ganho"] = (merged["delta"] <= 0).astype(int)
    merged["turma_grupo"] = merged["escola_pre"].astype(str) + "___" + merged["turma_pre"].astype(str)
    return merged


def prepare_features(df: pd.DataFrame) -> tuple[np.ndarray, list[str]]:
    # Variáveis sociodemográficas e de contexto
    cat_cols = ["sexo_pre", "cor_raca_pre", "zona_pre", "modalidade_pre", "fase"]
    num_cols = ["total_pre", "idade_pre", "distorcao_idade_serie_pre"]

    # Imputação pela mediana em idade se necessário
    idade = df["idade_pre"].copy()
    if idade.isna().any():
        idade = idade.fillna(idade.median())
    
    distorcao = df["distorcao_idade_serie_pre"].fillna(0)
    total_pre = df["total_pre"]

    X_num = np.column_stack([total_pre.values, idade.values, distorcao.values])
    num_names = ["total_pre", "idade", "distorcao_idade_serie"]

    # One-Hot Encoding das categóricas
    df_cat = df[cat_cols].fillna("Não informado").astype(str)
    encoder = OneHotEncoder(drop="first", sparse_output=False, handle_unknown="ignore")
    X_cat = encoder.fit_transform(df_cat)
    cat_names = encoder.get_feature_names_out(cat_cols).tolist()

    X = np.hstack([X_num, X_cat])
    feature_names = num_names + cat_names
    return X, feature_names


def evaluate_regression(X: np.ndarray, y: np.ndarray, groups: np.ndarray, names: list[str]) -> dict:
    gkf = GroupKFold(n_splits=5)
    models = {
        "Baseline (Média)": DummyRegressor(strategy="mean"),
        "Ridge Regression": Ridge(alpha=1.0),
        "Random Forest Regressor": RandomForestRegressor(n_estimators=100, max_depth=6, random_state=42),
        "Gradient Boosting Regressor": GradientBoostingRegressor(n_estimators=80, max_depth=4, random_state=42)
    }

    results = {}
    for name, model in models.items():
        rmse_list, mae_list, r2_list = [], [], []
        for train_idx, test_idx in gkf.split(X, y, groups=groups):
            X_tr, X_te = X[train_idx], X[test_idx]
            y_tr, y_te = y[train_idx], y[test_idx]

            model.fit(X_tr, y_tr)
            preds = model.predict(X_te)

            rmse_list.append(np.sqrt(mean_squared_error(y_te, preds)))
            mae_list.append(mean_absolute_error(y_te, preds))
            r2_list.append(r2_score(y_te, preds))

        results[name] = {
            "RMSE": float(np.mean(rmse_list)),
            "MAE": float(np.mean(mae_list)),
            "R2": float(np.mean(r2_list))
        }

    # Importância das características usando Random Forest treinado no conjunto completo
    rf = RandomForestRegressor(n_estimators=100, max_depth=6, random_state=42)
    rf.fit(X, y)
    importances = sorted(
        [{"feature": f, "importance": float(imp)} for f, imp in zip(names, rf.feature_importances_)],
        key=lambda x: x["importance"],
        reverse=True
    )
    return {"modelos": results, "top_features": importances[:6]}


def evaluate_classification(X: np.ndarray, y: np.ndarray, groups: np.ndarray) -> dict:
    gkf = GroupKFold(n_splits=5)
    models = {
        "Baseline (Majoritária)": DummyClassifier(strategy="most_frequent"),
        "Regressão Logística": LogisticRegression(max_iter=1000, random_state=42),
        "Árvore de Decisão": DecisionTreeClassifier(max_depth=4, random_state=42),
        "Random Forest Classifier": RandomForestClassifier(n_estimators=100, max_depth=6, random_state=42),
        "Gradient Boosting Classifier": GradientBoostingClassifier(n_estimators=80, max_depth=3, random_state=42)
    }

    results = {}
    for name, model in models.items():
        acc_list, f1_list, auc_list = [], [], []
        for train_idx, test_idx in gkf.split(X, y, groups=groups):
            X_tr, X_te = X[train_idx], X[test_idx]
            y_tr, y_te = y[train_idx], y[test_idx]

            model.fit(X_tr, y_tr)
            preds = model.predict(X_te)
            acc_list.append(accuracy_score(y_te, preds))
            f1_list.append(f1_score(y_te, preds, zero_division=0))

            if hasattr(model, "predict_proba"):
                try:
                    probs = model.predict_proba(X_te)[:, 1]
                    auc_list.append(roc_auc_score(y_te, probs))
                except Exception:
                    auc_list.append(0.5)
            else:
                auc_list.append(0.5)

        results[name] = {
            "Acuracia": float(np.mean(acc_list)),
            "F1_Score": float(np.mean(f1_list)),
            "ROC_AUC": float(np.mean(auc_list))
        }
    return results


def main() -> None:
    output = {}
    for category in ["vocabulario", "tde"]:
        print(f"=== Modelando {category.upper()} ===")
        df = load_pairs(category)
        print(f"Pares carregados: {len(df)} em {df['turma_grupo'].nunique()} turmas distintas")

        X, names = prepare_features(df)
        groups = df["turma_grupo"].values

        # Tarefa 1: Predição do total pós-teste (Regressão)
        y_reg = df["total_pos"].values
        reg_results = evaluate_regression(X, y_reg, groups, names)

        # Tarefa 2: Classificação do risco de estagnação/baixo ganho (delta <= 0)
        y_clf = df["risco_baixo_ganho"].values
        clf_results = evaluate_classification(X, y_clf, groups)

        output[category] = {
            "n_pares": len(df),
            "n_turmas": int(df["turma_grupo"].nunique()),
            "taxa_risco_estagnacao": float(np.mean(y_clf)),
            "regressao": reg_results,
            "classificacao": clf_results
        }

    out_file = DATA_DIR / "resultados_ml.json"
    with out_file.open("w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\nResultados salvos com sucesso em: {out_file}")
    print(json.dumps(output, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
