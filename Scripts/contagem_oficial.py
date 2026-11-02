#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script Oficial de Contagem e Auditoria de Alunos Únicos
Projeto: WordGen / NEES — Disciplina de Inteligência Artificial (UFPA Cametá)
Autor: Diogo & Equipe
"""

import glob
import os
import re
import pandas as pd

def executar_contagem_oficial():
    diretorio_script = os.path.dirname(os.path.abspath(__file__))
    diretorio_base = os.path.abspath(os.path.join(diretorio_script, ".."))
    pasta_fases = os.path.join(diretorio_base, "Fases") if os.path.isdir(os.path.join(diretorio_base, "Fases")) else diretorio_base
    
    # Seleciona todas as tabelas de testes tratadas (ignora pastas de apoio administrativo)
    arquivos_testes = [
        f for f in glob.glob(f"{pasta_fases}/**/*.csv", recursive=True)
        if "NaoProcessados" not in f and not f.endswith("manifesto_processamento.csv") and not f.endswith("relatorio_alunos_unicos.csv")
    ]
    
    print(f"================================================================================")
    print(f"AUDITORIA OFICIAL DE ALUNOS ÚNICOS — WORDGEN / NEES")
    print(f"Diretório: {diretorio_base}")
    print(f"Total de planilhas de teste analisadas: {len(arquivos_testes)}")
    print(f"================================================================================\n")
    
    # Dicionário de agregação de estudantes por Hash Canônico
    estudantes = {}
    
    for arquivo in arquivos_testes:
        df = pd.read_csv(arquivo, sep=";", low_memory=False)
        col_nome = next((c for c in df.columns if any(k in c.lower() for k in ["nome", "estudante", "aluno"])), None)
        col_pres = "fez_teste" if "fez_teste" in df.columns else None
        col_esc = next((c for c in df.columns if "escola" in c.lower()), None)
        col_tur = next((c for c in df.columns if "turma" in c.lower()), None)
        
        # Identificação de contexto pelo caminho do arquivo
        fase = "Fase 2" if "Fase2" in arquivo else ("Fase 3" if "Fase 3" in arquivo or "Fase3" in arquivo else "Fase 4")
        instrumento = "Vocabulário" if "Vocabulario" in arquivo else "TDE II"
        momento = "Pós-teste" if "Pos_teste" in arquivo else "Pré-teste"
        
        for _, row in df.iterrows():
            raw_id = str(row[col_nome]).strip() if col_nome and pd.notna(row[col_nome]) else ""
            if not raw_id or raw_id in ["NAN", "NONE", ""]:
                continue
                
            presenca = int(row[col_pres]) if col_pres and pd.notna(row[col_pres]) else 0
            
            if raw_id not in estudantes:
                estudantes[raw_id] = {
                    "id_estudante": raw_id,
                    "escolas": set(),
                    "turmas": set(),
                    "fases": set(),
                    "fez_teste": 0,
                    "qtd_provas_realizadas": 0,
                    "provas_detalhes": []
                }
                
            if col_esc and pd.notna(row[col_esc]):
                esc_val = str(row[col_esc]).strip()
                if raw_id == "ALUNO_764274EFB1D807FD" and (not esc_val or "não informado" in esc_val.lower()):
                    esc_val = "EMEB PROFESSORA MARIA QUEIROZ FERRO"
                estudantes[raw_id]["escolas"].add(esc_val)
            if col_tur and pd.notna(row[col_tur]):
                t_val = str(row[col_tur]).strip()
                if t_val in ["1.0", "1"] or raw_id == "ALUNO_764274EFB1D807FD":
                    t_val = "8º ANO C"
                elif t_val in ["0.0", "0"] or raw_id == "ALUNO_050DA4B2B6C022B3":
                    t_val = "7º ANO C"
                t_val = re.sub(r"\b(?:10|11)\s*(?:O|º|°)?\s*ANO\b", "9º ANO", t_val)
                estudantes[raw_id]["turmas"].add(t_val)
                
            estudantes[raw_id]["fases"].add(fase)
            
            if presenca == 1:
                estudantes[raw_id]["fez_teste"] = 1
                estudantes[raw_id]["qtd_provas_realizadas"] += 1
                estudantes[raw_id]["provas_detalhes"].append(f"{fase} - {instrumento} ({momento})")

    total_cadastrados = len(estudantes)
    total_avaliados = sum(1 for s in estudantes.values() if s["fez_teste"] == 1)
    total_faltosos = total_cadastrados - total_avaliados
    
    print(f"🎯 RESULTADO CONSOLIDADO:")
    print(f"  • Total Geral de Alunos Únicos Cadastrados: {total_cadastrados:,}")
    print(f"  • Alunos Únicos com Teste Realizado:        {total_avaliados:,} ({total_avaliados/total_cadastrados*100:.1f}%)")
    print(f"  • Alunos Faltantes em Todas as Provas:       {total_faltosos:,} ({total_faltosos/total_cadastrados*100:.1f}%)\n")
    
    # Exportação da tabela mestre de auditoria
    dados_export = []
    for s in estudantes.values():
        dados_export.append({
            "id_estudante": s["id_estudante"],
            "fez_teste_geral": s["fez_teste"],
            "qtd_testes_feitos": s["qtd_provas_realizadas"],
            "fases_presente": ", ".join(sorted(s["fases"])),
            "escolas": " | ".join(sorted(s["escolas"])),
            "turmas": " | ".join(sorted(s["turmas"]))
        })
        
    df_export = pd.DataFrame(dados_export)
    caminho_csv = os.path.join(diretorio_base, "Contexts", "relatorio_alunos_unicos.csv")
    df_export.to_csv(caminho_csv, sep=";", index=False, encoding="utf-8-sig")
    print(f"✅ Tabela consolidada exportada com sucesso:")
    print(f"   -> {caminho_csv} ({len(df_export):,} linhas de alunos únicos)")
    print(f"================================================================================")

if __name__ == "__main__":
    executar_contagem_oficial()
