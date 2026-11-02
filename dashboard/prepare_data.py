#!/usr/bin/env python3
"""Consolida as avaliações já tratadas, preservando os dois instrumentos separados.

Somente a biblioteca padrão é necessária. Execute na raiz: python3 dashboard/prepare_data.py
"""
from __future__ import annotations

import csv
import json
import math
import re
import unicodedata
import shutil
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = Path(__file__).resolve().parent
SPECS = {
    "vocabulario": ("1 - Vocabulario", "Q", 50, 50),
    "tde": ("2 - TDE", "P", 40, 40),
}
FIELDS = ["id_aluno", "escola", "turma", "fase", "periodo", "momento", "categoria",
          "fez_teste", "total", "sexo", "cor_raca", "zona", "idade", "modalidade",
          "serie_ano", "distorcao_idade_serie", "nivel_desempenho", "imputado_item",
          "replica_pre", "fonte"]


def clean(value: object) -> str:
    return str(value or "").strip()


def norm(value: object) -> str:
    value = unicodedata.normalize("NFKD", clean(value))
    return re.sub(r"\s+", " ", "".join(c for c in value if not unicodedata.combining(c)).upper()).strip()


def field(row: dict, *names: str) -> str:
    for name in names:
        value = clean(row.get(name))
        if value and value.lower() not in ("nan", "none"):
            return value
    return ""


def number(value: object, lower: float, upper: float) -> float | None:
    try:
        n = float(clean(value).replace(",", "."))
        return n if math.isfinite(n) and lower <= n <= upper else None
    except ValueError:
        return None


def school(value: str, ident: str = "") -> str:
    if ident == "ALUNO_764274EFB1D807FD" and (not value or norm(value) in ("NAO INFORMADO", "NAO INFORMADA")):
        return "EMEB PROFESSORA MARIA QUEIROZ FERRO"
    return norm(value) if value else "Não informada"


def group(value: str, ident: str = "") -> str:
    value = norm(value)
    if value in ("1.0", "1") or ident == "ALUNO_764274EFB1D807FD":
        return "8º ANO C"
    if value in ("0.0", "0") or ident == "ALUNO_050DA4B2B6C022B3":
        return "7º ANO C"
    # Correção de artefatos de preenchimento automático do Excel (ex.: 10 ANO / 11 ANO -> 9º ANO)
    value = re.sub(r"\b(?:10|11)\s*(?:O|º|°)?\s*ANO\b", "9º ANO", value)
    value = re.sub(r"\b(\d+)\s*(?:O|º|°)?\s*(ANO|PERIODO)\b", r"\1º \2", value)
    return value if value else "Não informada"


def category_value(value: str, allowed: tuple[str, ...]) -> str:
    return value if value in allowed else "Não informado"


def load_one(path: Path, category: str, prefix: str, count: int, maximum: int,
             audit: Counter) -> list[dict]:
    phase_number = int(re.search(r"Fase(\d+)", str(path)).group(1))
    phase = f"Fase {phase_number}"
    period = {2: "2023.2", 3: "2024.1", 4: "2024.2"}[phase_number]
    moment = "Pós" if path.parent.name == "Pos_teste" else "Pré"
    result = []
    with path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream, delimiter=";")
        if not reader.fieldnames or "fez_teste" not in reader.fieldnames:
            raise ValueError(f"CSV tratado sem campo fez_teste: {path}")
        for row in reader:
            audit["linhas_lidas"] += 1
            ident = field(row, "Nome", "NOME DO ESTUDANTE", "NOME ESTUDANTE", "NOME DO ALUNO")
            if not re.fullmatch(r"ALUNO_[0-9A-F]+", ident):
                audit["ids_invalidos"] += 1
                continue
            present = field(row, "fez_teste") == "1"

            # Nova regra de pontuação (escala unificada 0-1):
            # 1. Pontuação 0: incorretas ou em branco
            # 2. Pontuação 1: qualquer acerto (parcial ou total)
            # 3. Nota máxima: 1 por questão (escala total: 50 para Vocabulário, 40 para TDE)
            items = {}
            for i in range(1, count + 1):
                raw_item = number(row.get(f"{prefix}{i}"), 0, 2 if prefix == "P" else 1)
                if present:
                    if raw_item is not None:
                        items[f"{prefix}{i}"] = 1.0 if raw_item > 0 else 0.0
                    else:
                        items[f"{prefix}{i}"] = 0.0
                else:
                    items[f"{prefix}{i}"] = None

            if present:
                score = sum(items.values())
            else:
                score = None

            if not present and clean(row.get("Total")):
                audit["escores_faltosos_descartados"] += 1
            age = number(row.get("Idade"), 0, 120)
            obj = {
                "id_aluno": ident,
                "escola": school(field(row, "Escola", "ESCOLA"), ident),
                "turma": group(field(row, "Turma", "TURMA"), ident),
                "fase": phase,
                "periodo": period,
                "momento": moment,
                "categoria": category,
                "fez_teste": int(present),
                "total": score,
                "sexo": category_value(field(row, "Sexo"), ("F", "M")),
                "cor_raca": category_value(field(row, "Cor/Raça"),
                    ("Branca", "Parda", "Preta", "Amarela", "Indígena")),
                "zona": category_value(field(row, "Zona"), ("Rural", "Urbana")),
                "idade": age,
                "modalidade": category_value(field(row, "Modalidade_Ensino"), ("Regular", "EJA")),
                "serie_ano": field(row, "Serie_Ano"),
                "distorcao_idade_serie": int(field(row, "distorcao_idade_serie") == "1"),
                "nivel_desempenho": field(row, "Nivel_Desempenho") or "Não informado",
                "imputado_item": int(field(row, "imputado_item") == "1"),
                "replica_pre": 0,
                "fonte": str(path.relative_to(ROOT)),
            }
            obj.update(items)
            result.append(obj)
    return result


def rank(row: dict) -> tuple:
    prefix, count = ("Q", 50) if row["categoria"] == "vocabulario" else ("P", 40)
    return (row["fez_teste"], row["total"] is not None,
            sum(row[f"{prefix}{i}"] is not None for i in range(1, count + 1)),
            sum(row[k] != "Não informado" for k in ("sexo", "cor_raca", "zona", "modalidade")),
            row["idade"] is not None)


def prepare(category: str, audit: Counter) -> list[dict]:
    folder, prefix, count, maximum = SPECS[category]
    paths = sorted(ROOT.glob(f"Fases/Fase*Tratada/{folder}/*/*.csv"))
    if not paths:
        raise FileNotFoundError(f"Nenhum arquivo para {category}")

    all_rows: list[dict] = []
    for path in paths:
        audit["arquivos"] += 1
        all_rows.extend(load_one(path, category, prefix, count, maximum, audit))

    # 1. Perfil cadastral consolidado por estudante (coalescência demográfica)
    student_profiles: dict[str, dict] = {}
    for r in all_rows:
        sid = r["id_aluno"]
        score_prof = (
            sum(r[k] != "Não informado" for k in ("sexo", "cor_raca", "zona", "modalidade")),
            r["idade"] is not None,
            r["escola"] != "Não informada",
            r["turma"] != "Não informada"
        )
        if sid not in student_profiles or score_prof > student_profiles[sid][0]:
            student_profiles[sid] = (score_prof, r)

    # 2. Consolidação do Pré-teste por (id_aluno, fase)
    best_pre: dict[tuple[str, str], dict] = {}
    for r in [x for x in all_rows if x["momento"] == "Pré"]:
        key = (r["id_aluno"], r["fase"])
        old = best_pre.get(key)
        if old is None or rank(r) > rank(old):
            best_pre[key] = r

    # 3. Consolidação do Pós-teste com checagem de réplicas
    best_pos: dict[tuple[str, str], dict] = {}
    for r in [x for x in all_rows if x["momento"] == "Pós"]:
        key = (r["id_aluno"], r["fase"])
        pre_row = best_pre.get(key)
        is_rep = False
        if pre_row and r["fez_teste"] and pre_row["fez_teste"] and r["total"] is not None and pre_row["total"] is not None and r["total"] > 0:
            vec_r = tuple(r[f"{prefix}{i}"] for i in range(1, count + 1))
            vec_pre = tuple(pre_row[f"{prefix}{i}"] for i in range(1, count + 1))
            if vec_r == vec_pre:
                is_rep = True
        r["replica_pre"] = int(is_rep)

        old = best_pos.get(key)
        if old is None:
            best_pos[key] = r
        else:
            audit["duplicatas_resolvidas"] += 1
            if old["total"] != r["total"] and old["total"] is not None and r["total"] is not None:
                audit["duplicatas_com_escore_distinto"] += 1
            # Prioriza prova real (não cópia) e depois maior rank
            rank_r = (not bool(r["replica_pre"]), *rank(r))
            rank_old = (not bool(old["replica_pre"]), *rank(old))
            if rank_r > rank_old:
                best_pos[key] = r

    # 4. Agrupamento final e enriquecimento cadastral
    combined: list[dict] = list(best_pre.values()) + list(best_pos.values())
    for r in combined:
        sid = r["id_aluno"]
        prof = student_profiles.get(sid, (None, {}))[1]
        for demo in ("sexo", "cor_raca", "zona", "modalidade"):
            if r[demo] == "Não informado" and prof.get(demo) and prof[demo] != "Não informado":
                r[demo] = prof[demo]
        if r["idade"] is None and prof.get("idade") is not None:
            r["idade"] = prof["idade"]
        if r["escola"] == "Não informada" and prof.get("escola") and prof["escola"] != "Não informada":
            r["escola"] = prof["escola"]
        if r["turma"] == "Não informada" and prof.get("turma") and prof["turma"] != "Não informada":
            r["turma"] = prof["turma"]

    rows = sorted(combined, key=lambda r: (r["fase"], r["momento"], r["id_aluno"]))
    audit["avaliacoes_consolidadas"] = len(rows)
    audit["avaliacoes_realizadas"] = sum(r["fez_teste"] and r["total"] is not None for r in rows)
    audit["alunos_unicos"] = len({r["id_aluno"] for r in rows})
    audit["turmas_unicas"] = len({(r["escola"], r["turma"]) for r in rows})
    audit["replicas_detectadas"] = sum(r.get("replica_pre", 0) == 1 for r in rows)

    columns = FIELDS + [f"{prefix}{i}" for i in range(1, count + 1)]
    with (OUT / "data" / f"{category}.csv").open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=columns, delimiter=";")
        writer.writeheader()
        writer.writerows(rows)

    # O dashboard usa somente campos analíticos; respostas individuais ficam no CSV local.
    export = [{k: r[k] for k in FIELDS if k != "fonte"} for r in rows]
    with (OUT / "dist" / "data" / f"{category}.json").open("w", encoding="utf-8") as stream:
        json.dump(export, stream, ensure_ascii=False, separators=(",", ":"))
    return rows


def main() -> None:
    (OUT / "data").mkdir(parents=True, exist_ok=True)
    (OUT / "dist" / "data").mkdir(parents=True, exist_ok=True)
    if (OUT / "src").exists():
        shutil.copytree(OUT / "src", OUT / "dist" / "src", dirs_exist_ok=True)
    report = {}
    for category in SPECS:
        audit = Counter()
        prepare(category, audit)
        report[category] = dict(audit)
    with (OUT / "data" / "auditoria.json").open("w", encoding="utf-8") as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2)
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
