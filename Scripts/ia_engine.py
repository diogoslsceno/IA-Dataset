#!/usr/bin/env python3
"""Motor Analítico e Orquestrador de IA para o Llama 3.2.

Combina uma Camada Analítica Estruturada (consultas dinâmicas aos microdados e indicadores do dashboard)
com o modelo de linguagem Llama 3.2 3B para síntese em linguagem natural fundamentada e sem alucinações.
"""
from __future__ import annotations

import json
import re
import urllib.request
import urllib.error
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONTEXT_DIR = ROOT / "Contexts"
OLLAMA_API_URL = "http://127.0.0.1:11434/api"


class DataAnalyticsEngine:
    """Motor de consulta e cálculo analítico sobre os dados reais do projeto."""

    def __init__(self):
        kb_path = CONTEXT_DIR / "base_conhecimento.json"
        stats_path = CONTEXT_DIR / "estatisticas_consolidadas.json"

        with kb_path.open(encoding="utf-8") as f:
            self.knowledge_base = json.load(f)

        with stats_path.open(encoding="utf-8") as f:
            self.stats = json.load(f)

    # Entidades estritas do domínio acadêmico/educacional do projeto WordGen / NEES
    DOMAIN_ENTITIES = [
        # Projeto, bases e painel
        "wordgen", "nees", "stari", "dataset", "microdado", "dashboard", "painel", "projeto",
        "planilha", "tabela", "csv", "base de dados", "conjunto de dados",
        # Instrumentos, provas e psicometria
        "vocab", "tde", "escrita", "prova", "teste", "avalia", "instrumento",
        "escore", "pontua", "nota", "acert", "tentativa", "dicot", "escala", "item", "itens",
        # Sujeitos, escolas e turmas
        "aluno", "estudante", "discente", "participa", "censo", "matricul", "chamado", "chamada",
        "escola", "emeb", "emef", "unidade", "rede", "turma",
        "natanael", "anchieta", "mousinho", "queiroz", "ricardo vieira", "expedito", "porfirio", "porfírio",
        # Modalidades, séries, períodos e fases
        "eja", "regular", "modalidade", "período", "periodo", "série", "serie", "ano", "sno",
        "6º", "6°", "7º", "7°", "8º", "8°", "9º", "9°", "6o", "7o", "8o", "9o",
        "6 ", "7 ", "8 ", "9 ", "6a", "6b", "6c", "6d", "6e", "6f", "7a", "7b", "7c", "7d", "7e", "7f",
        "8a", "8b", "8c", "8d", "8e", "9a", "9b", "9c", "9d", "9e", "9f", "9g",
        "sexto", "sétimo", "setimo", "oitavo", "nono",
        "fase", "ciclo", "2023", "2024", "pré", "pre-teste", "pós", "pos-teste", "longitudinal", "coorte", "trajetória", "trajetoria",
        # Métricas estatísticas do estudo
        "pares", "paread", "delta", "ganho", "melhora", "estab", "regress", "queda",
        "cohen", "dz", "tamanho do efeito", "effect size", "impacto", "desempenho", "proficiência", "proficiencia",
        # Demografia, equidade e variáveis escolares
        "idade", "faixa etária", "faixa etaria", "defasagem", "distorção", "distorcao",
        "zona", "urbana", "rural", "sexo", "gênero", "genero", "menina", "menino", "feminino", "masculino",
        "cor", "raça", "raca", "equidade", "socioecon", "renda", "salário", "salario", "classe social",
        "disciplina", "matemática", "matematica", "ciências", "ciencias",
        # Saneamento, qualidade, ML e governança
        "falta", "faltoso", "ausente", "imputa", "omiss", "réplica", "replica", "cópia", "copia",
        "qualidade", "dimens", "completude", "unicidade", "validade", "consistência", "consistencia", "acurácia", "acuracia", "temporalidade",
        "machine learning", "predit", "r²", "r2", "rmse", "auc", "random forest", "ridge", "boosting", "feature",
        "lgpd", "anonim", "pseudonim", "hash"
    ]

    GREETINGS = ["olá", "ola", "oi", "bom dia", "boa tarde", "boa noite", "ajuda", "quem é você", "quem e voce", "o que você faz", "o que voce faz"]

    def is_in_domain(self, query: str, history: list[dict] | None = None) -> tuple[bool, str]:
        """Verifica se a pergunta pertence estritamente ao escopo dos dados acadêmicos do projeto."""
        q_curr = query.lower().strip()

        # Verifica se há alguma entidade do domínio acadêmico na pergunta atual
        if any(ent in q_curr for ent in self.DOMAIN_ENTITIES):
            return True, "domain"

        # Verifica se é uma correção ou continuação direta de uma pergunta anterior válida no histórico
        is_followup_phrase = any(k in q_curr for k in ["errei", "quis dizer", "na verdade", "e no ", "e na ", "e do ", "e da ", "e o ", "e a ", "e sobre", "e quanto"])
        if history and is_followup_phrase:
            user_hist = [m.get("content", "").lower() for m in history if m.get("role") == "user"]
            if user_hist and any(ent in user_hist[-1] for ent in self.DOMAIN_ENTITIES):
                return True, "domain"

        # Verifica se é apenas uma saudação inicial ou pedido de ajuda sobre o assistente
        if any(q_curr == g or q_curr.startswith(g + " ") or q_curr.startswith(g + ",") or q_curr.startswith(g + "!") for g in self.GREETINGS):
            return False, "greeting"

        return False, "out_of_scope"

    def _extract_turmas_series(self, text: str) -> tuple[list[str], list[str], list[str]]:
        """Extrai turmas (ex: '6º ANO B'), séries ('6º ANO') e períodos EJA ('8º PERIODO (EJA)') mesmo com erros de digitação ('6 sno B', '6b')."""
        norm = text.lower()
        for word, num in [("sexto", "6"), ("sétimo", "7"), ("setimo", "7"), ("oitavo", "8"), ("nono", "9")]:
            norm = re.sub(rf"\b{word}\b", num, norm)

        matched_turmas = []
        matched_series = []
        matched_eja = []

        # 1. Turmas com letra (ex: "6 sno b", "6º ano b", "6b", "8° a")
        for m in re.finditer(r"\b([6789])\s*(?:º|°|o)?\s*(?:ano|sno|anos|serie|série|turma)?\s*([a-g])\b", norm):
            num, letter = m.group(1), m.group(2).upper()
            cand = f"{num}º ANO {letter}"
            if cand in self.stats.get("demografia", {}).get("idade", {}).get("por_turma", {}) and cand not in matched_turmas:
                matched_turmas.append(cand)

        # 2. Períodos do EJA (ex: "6 periodo", "8º período do eja")
        for m in re.finditer(r"\b([678])\s*(?:º|°|o)?\s*(?:periodo|período)\b", norm):
            num = m.group(1)
            cand = f"{num}º PERIODO (EJA)"
            if cand not in matched_eja:
                matched_eja.append(cand)
        if "eja" in norm and not matched_eja:
            for m in re.finditer(r"\b([678])\s*(?:º|°|o)?\b", norm):
                cand = f"{m.group(1)}º PERIODO (EJA)"
                if cand not in matched_eja:
                    matched_eja.append(cand)

        # 3. Séries gerais (ex: "6º ano", "6 sno", "7 ano") quando não há letra ou além da turma
        for m in re.finditer(r"\b([6789])\s*(?:º|°|o)?\s*(?:ano|sno|anos|serie|série)\b", norm):
            cand = f"{m.group(1)}º ANO"
            if cand not in matched_series:
                matched_series.append(cand)

        return matched_turmas, matched_series, matched_eja

    def retrieve_context(self, query: str, history: list[dict] | None = None) -> str:
        """Identifica a intenção da pergunta (incluindo histórico recente em follow-ups) e extrai os dados exatos."""
        q_curr = query.lower()
        is_followup = any(k in q_curr for k in ["errei", "quis dizer", "na verdade", "e no ", "e na ", "e do ", "e da ", "e o ", "e a ", "e sobre"]) or len(q_curr.split()) <= 5
        combined_text = query
        if history and is_followup:
            user_hist = [m.get("content", "") for m in history if m.get("role") == "user"]
            if user_hist:
                combined_text = user_hist[-1] + " " + query
        q_lower = combined_text.lower()
        facts_blocks = []
        methodology_blocks = []

        # Extração inteligente de turmas, séries e períodos EJA (priorizando a pergunta atual se houver)
        curr_turmas, curr_series, curr_eja = self._extract_turmas_series(query)
        comb_turmas, comb_series, comb_eja = self._extract_turmas_series(combined_text)
        matched_turmas = curr_turmas or comb_turmas
        matched_series = curr_series or comb_series
        matched_eja = curr_eja or comb_eja

        # -------------------------------------------------------------
        # 0. Checagem de Nomes Pessoais / Identificação / LGPD
        # -------------------------------------------------------------
        privacy_terms = ["chamado", "chamada", "nome", "sobrenome", "joão", "joao", "maria", "silva", "santos",
                         "cpf", "rg", " matrícula", "matricula", "identidade", "anonimiz", "lgpd", "pessoal"]
        if any(term in q_curr for term in privacy_terms):
            facts_blocks.append(
                "**Proteção de Dados Pessoais e Anonimização (LGPD)**\n"
                "- Nenhum nome civil (como 'João', 'Maria' ou sobrenomes) consta na base de dados.\n"
                "- Em cumprimento estrito à Lei Geral de Proteção de Dados (LGPD - Lei nº 13.709/2018) e à proteção de menores, "
                "todos os nomes próprios foram substituídos de forma irreversível por identificadores canônicos em hash hexadecimal "
                "no formato `ALUNO_[16 dígitos HEX]` (ex.: `ALUNO_0002855DF62AC8AF`).\n"
                "- Portanto, não é possível consultar estudantes pelo nome civil, apenas analisar os 3.016 estudantes únicos de forma anonimizada."
            )
            if not any(t in q_curr for t in ["idade", "eja", "nota", "média", "media", "escola", "turma", "zona"]):
                return "=== DADOS ESTATÍSTICOS AUDITADOS DO PROJETO ===\n" + "\n\n".join(facts_blocks)

        # -------------------------------------------------------------
        # 1. Checagem de Variáveis Ausentes / Não Coletadas
        # -------------------------------------------------------------
        missing_terms = ["renda", "salário", "salario", "dinheiro", "financeir", "classe social", 
                         "classe econômica", "classe economica", "profissão", "profissao",
                         "matemática", "matematica", "ciências", "ciencias", "história", "historia"]
        if any(term in q_lower for term in missing_terms):
            facts_blocks.append(
                "**Informação sobre Variáveis Ausentes no Projeto**\n"
                "- A variável consultada (renda familiar, classe socioeconômica ou outras disciplinas escolares) "
                "NÃO foi coletada nos instrumentos do projeto WordGen / NEES.\n"
                "- O projeto concentrou-se exclusivamente na avaliação de proficiência linguística (Vocabulário e TDE II Escrita) "
                "e em atributos demográficos cadastrais (Idade, Sexo, Cor/Raça, Modalidade de Ensino e Zona Escolar).\n"
                "- IMPORTANTE: Essa ausência não decorre de anonimização, mas de não ter feito parte do escopo de coleta da pesquisa."
            )

        # -------------------------------------------------------------
        # 1B. Detalhamento Prioritário de Turma Específica (Regular ou Período EJA)
        # -------------------------------------------------------------
        turmas_all = self.stats.get("demografia", {}).get("idade", {}).get("por_turma", {})
        periodos_eja_all = self.stats.get("demografia", {}).get("idade", {}).get("por_periodo_eja", {})

        for p_nome in matched_eja:
            p_info = periodos_eja_all.get(p_nome)
            if p_info:
                esc_str = ", ".join(f"{k} ({v} alunos)" for k, v in p_info.get("escolas", {}).items())
                facts_blocks.append(
                    f"**Dados Completos e Auditados do {p_nome}**\n"
                    f"- Total de alunos únicos matriculados/cadastrados no {p_nome}: **{p_info['alunos_unicos']} alunos** (distribuídos em {p_info['turmas_escolas']} escolas na Fase 2: {esc_str}).\n"
                    f"- Quantos alunos do {p_nome} responderam / realizaram o teste de TDE II? **0 alunos (nenhum aluno respondeu ao TDE II)**. Todos os {p_info['alunos_unicos']} alunos cadastrados no {p_nome} faltaram à aplicação da prova (`fez_teste = 0`).\n"
                    f"- Quantos alunos do {p_nome} responderam / realizaram o teste de Vocabulário? **0 alunos (nenhum aluno respondeu ao Vocabulário)**. Todos os {p_info['alunos_unicos']} alunos cadastrados no {p_nome} faltaram à aplicação da prova (`fez_teste = 0`).\n"
                    f"- Participação detalhada por instrumento no {p_nome}:\n"
                    f"  * Alunos que responderam ao TDE II (total ou apenas TDE II): **0 alunos** (0 provas com escore).\n"
                    f"  * Alunos que responderam ao Vocabulário (total ou apenas Vocabulário): **0 alunos** (0 provas com escore).\n"
                    f"  * Alunos que responderam a ambos os testes: **0 alunos**.\n"
                    f"  * Alunos faltosos/ausentes em todas as provas no {p_nome}: **{p_info['alunos_unicos']} alunos** (100% de ausência nas provas da Fase 2).\n"
                    f"- Perfil Etário do {p_nome}: média de idade de **{p_info['idade_media']} anos** | mediana de {p_info['idade_mediana']} anos | desvio padrão de {p_info['idade_desvio_padrao']} anos | mínima de {p_info['idade_minima']} anos e máxima de {p_info['idade_maxima']} anos."
                )

        for t_nome in matched_turmas:
            t_info = turmas_all.get(t_nome)
            if t_info:
                esc_lines = []
                for esc_k, esc_v in t_info.get("por_escola", {}).items():
                    esc_lines.append(
                        f"    * {esc_k}: {esc_v['alunos_unicos']} alunos únicos | "
                        f"Responderam Vocabulário: {esc_v['alunos_vocab_total']} (apenas Vocabulário: {esc_v['alunos_apenas_vocab']}) | "
                        f"Responderam TDE II: {esc_v['alunos_tde_total']} (apenas TDE II: {esc_v['alunos_apenas_tde']}) | "
                        f"Responderam ambos os testes: {esc_v['alunos_ambos_testes']} | Faltosos: {esc_v['alunos_faltosos']}"
                    )
                esc_block = "\n".join(esc_lines)
                facts_blocks.append(
                    f"**Dados Completos e Auditados da Turma {t_nome} (Todas as Escolas Consolidado)**\n"
                    f"- Total de alunos únicos cadastrados no {t_nome}: {t_info['alunos_unicos']} estudantes (presentes em {t_info['escolas_unicas']} escolas).\n"
                    f"- Alunos únicos avaliados (responderam ao menos um teste): {t_info['alunos_avaliados']} alunos.\n"
                    f"- Alunos únicos faltosos em todas as provas: {t_info['alunos_faltosos']} alunos.\n"
                    f"- Participação por Instrumento Avaliativo no {t_nome}:\n"
                    f"  * Alunos únicos que responderam/realizaram APENAS o teste de Vocabulário (e não realizaram o TDE II): **{t_info['alunos_apenas_vocab']} alunos**.\n"
                    f"  * Alunos únicos que responderam/realizaram APENAS o teste de TDE II (e não realizaram o Vocabulário): **{t_info['alunos_apenas_tde']} alunos**.\n"
                    f"  * Alunos únicos que responderam/realizaram AMBOS os testes (Vocabulário e TDE II): **{t_info['alunos_ambos_testes']} alunos**.\n"
                    f"  * Total de alunos únicos que responderam/realizaram o teste de Vocabulário (apenas Vocabulário + ambos): **{t_info['alunos_vocab_total']} alunos** (totalizando {t_info['vocab_avaliacoes']} avaliações/provas aplicadas).\n"
                    f"  * Total de alunos únicos que responderam/realizaram o teste de TDE II (apenas TDE II + ambos): **{t_info['alunos_tde_total']} alunos** (totalizando {t_info['tde_avaliacoes']} avaliações/provas aplicadas).\n"
                    f"- Desempenho e Pares Pré/Pós no {t_nome}:\n"
                    f"  * Vocabulário: média geral {t_info['vocab_media']} pontos | {t_info['vocab_pares']} pares Pré/Pós (Pré: {t_info['vocab_media_pre']} -> Pós: {t_info['vocab_media_pos']}, Delta: {t_info['vocab_delta']}, dz: {t_info['vocab_dz']}).\n"
                    f"  * TDE II Escrita: média geral {t_info['tde_media']} pontos | {t_info['tde_pares']} pares Pré/Pós (Pré: {t_info['tde_media_pre']} -> Pós: {t_info['tde_media_pos']}, Delta: {t_info['tde_delta']}, dz: {t_info['tde_dz']}).\n"
                    f"- Perfil Etário do {t_nome}: média de {t_info['idade_media']} anos (mediana {t_info['idade_mediana']}, DP {t_info['idade_desvio_padrao']}, mín {t_info['idade_minima']} e máx {t_info['idade_maxima']} anos).\n"
                    f"- Detalhamento da Turma {t_nome} por Escola:\n{esc_block}"
                )

        # -------------------------------------------------------------
        # 2. Idade, Modalidade (EJA vs Regular), Períodos do EJA e Séries/Turmas
        # -------------------------------------------------------------
        age_terms = ["idade", "faixa etária", "faixa etaria", "anos de vida", "velho", "jovem", "eja", "regular",
                     "modalidade", "defasagem", "distorção", "distorcao", "período", "periodo", "série", "serie",
                     "6º", "6°", "7º", "7°", "8º", "8°", "9º", "9°", "6o", "7o", "8o", "9o"]
        pure_age_query = any(t in q_lower for t in ["idade", "faixa", "velho", "jovem", "anos de vida", "mediana", "defasagem", "distor"])
        if (any(term in q_lower for term in age_terms) or matched_series or matched_eja or ("estudante" in q_lower and "méd" in q_lower)) and (not (matched_turmas or matched_eja) or pure_age_query):
            demo_idade = self.stats.get("demografia", {}).get("idade", {})
            eja_info = demo_idade.get("eja", {})
            reg_info = demo_idade.get("regular", {})
            dist_pct = self.stats.get("demografia", {}).get("distorcao_idade_serie_regular_pct", 10.03)
            periodos_eja = demo_idade.get("por_periodo_eja", {})
            series_reg = demo_idade.get("por_serie_ano", {})

            block = ["**Indicadores de Idade, Modalidade (EJA e Regular) e Períodos/Séries (Dados Reais Auditados)**"]
            if "eja" in q_lower or "período" in q_lower or "periodo" in q_lower or matched_eja or not ("regular" in q_lower or matched_series or matched_turmas):
                block.append(
                    f"- Modalidade EJA Geral (Ensino de Jovens e Adultos):\n"
                    f"  * Total de estudantes únicos matriculados/cadastrados no EJA: {eja_info.get('alunos_unicos', 125)} alunos (registrados na Fase 2 - 2023.2)\n"
                    f"  * Quantos alunos do EJA responderam ao Vocabulário ou ao TDE II? **0 alunos (nenhum aluno respondeu)** — todos os 125 alunos do EJA faltaram às provas (`fez_teste = 0`).\n"
                    f"  * Média de idade geral do EJA: {eja_info.get('media', 29.96)} anos (~30 anos)\n"
                    f"  * Desvio padrão: {eja_info.get('desvio_padrao', 11.91)} anos | Mediana: {eja_info.get('mediana', 26.0)} anos\n"
                    f"  * Faixa etária geral do EJA: de {eja_info.get('minima', 16)} a {eja_info.get('maxima', 60)} anos"
                )
                if periodos_eja:
                    block.append("- Detalhamento Exato por Período do EJA (6º, 7º e 8º Período):")
                    for p_nome, p_info in periodos_eja.items():
                        esc_str = ", ".join(f"{k} ({v} alunos)" for k, v in p_info.get("escolas", {}).items())
                        block.append(
                            f"  * {p_nome}:\n"
                            f"    - Alunos únicos matriculados: {p_info['alunos_unicos']} estudantes distribuídos em {p_info['turmas_escolas']} turmas/escolas ({esc_str})\n"
                            f"    - Média de idade: {p_info['idade_media']} anos | Mediana: {p_info['idade_mediana']} anos | DP: {p_info['idade_desvio_padrao']} anos\n"
                            f"    - Faixa etária: mínima de {p_info['idade_minima']} anos e máxima de {p_info['idade_maxima']} anos\n"
                            f"    - Alunos que responderam às provas: Vocabulário = **0 alunos** | TDE II = **0 alunos** (todos os {p_info['alunos_unicos']} alunos do {p_nome} faltaram às provas na Fase 2, `fez_teste = 0`)"
                        )
            if "regular" in q_lower or matched_series or matched_turmas or not ("eja" in q_lower and "regular" not in q_lower):
                block.append(
                    f"- Modalidade Ensino Regular Geral:\n"
                    f"  * Total de estudantes únicos cadastrados: {reg_info.get('alunos_unicos', 2891)} alunos\n"
                    f"  * Média de idade: {reg_info.get('media', 14.14)} anos (~14 anos)\n"
                    f"  * Desvio padrão: {reg_info.get('desvio_padrao', 2.04)} anos | Mediana: {reg_info.get('mediana', 14.0)} anos\n"
                    f"  * Faixa etária: de {reg_info.get('minima', 10)} a {reg_info.get('maxima', 35)} anos\n"
                    f"  * Taxa de distorção idade-série no Regular: {dist_pct}% dos alunos têm defasagem >= 2 anos."
                )
                if series_reg:
                    block.append("- Detalhamento por Série/Ano do Ensino Regular:")
                    for s_nome, s_info in series_reg.items():
                        block.append(
                            f"  * {s_nome}: {s_info['alunos_unicos']} alunos únicos (avaliados: {s_info['alunos_avaliados']}, faltosos: {s_info['alunos_faltosos']}) | "
                            f"Fizeram Vocabulário: {s_info['alunos_vocab_total']} alunos (apenas Vocabulário: {s_info['alunos_apenas_vocab']}) | "
                            f"Fizeram TDE II: {s_info['alunos_tde_total']} alunos (apenas TDE II: {s_info['alunos_apenas_tde']}) | "
                            f"Ambos os testes: {s_info['alunos_ambos_testes']} alunos | "
                            f"Média de idade: {s_info['idade_media']} anos (mín {s_info['idade_minima']}, máx {s_info['idade_maxima']}, mediana {s_info['idade_mediana']}) | "
                            f"Média Vocabulário: {s_info['vocab_media']} ({s_info['vocab_avaliacoes']} provas) | "
                            f"Média TDE II: {s_info['tde_media']} ({s_info['tde_avaliacoes']} provas)"
                        )
            facts_blocks.append("\n".join(block))

        # -------------------------------------------------------------
        # 3. Zona Urbana vs Zona Rural e Equidade
        # -------------------------------------------------------------
        if any(term in q_lower for term in ["zona", "urbana", "rural", "localiza", "campo"]):
            z = self.stats.get("demografia", {}).get("zona", {})
            u = z.get("urbana", {})
            r = z.get("rural", {})
            facts_blocks.append(
                "**Comparativo por Localização (Zona Urbana vs Rural)**\n"
                f"- Vocabulário (escala 0 a 50 pontos):\n"
                f"  * Zona Urbana: {u.get('vocab_avaliados', 4506)} avaliações | Média: {u.get('vocab_media', 22.92)} pontos\n"
                f"  * Zona Rural: {r.get('vocab_avaliados', 3236)} avaliações | Média: {r.get('vocab_media', 22.76)} pontos\n"
                f"  * Diferença: estudantes da zona urbana tiveram média +0,16 pontos superior.\n"
                f"- TDE II Escrita (escala 0 a 40 pontos):\n"
                f"  * Zona Urbana: {u.get('tde_avaliados', 4724)} avaliações | Média: {u.get('tde_media', 26.56)} pontos\n"
                f"  * Zona Rural: {r.get('tde_avaliados', 3689)} avaliações | Média: {r.get('tde_media', 25.06)} pontos\n"
                f"  * Diferença: estudantes da zona urbana tiveram pontuação +1,50 ponto superior aos da zona rural."
            )

        # -------------------------------------------------------------
        # 4. Sexo / Gênero
        # -------------------------------------------------------------
        if any(term in q_lower for term in ["sexo", "gênero", "genero", "menina", "menino", "feminino", "masculino", "mulher", "homem"]):
            s = self.stats.get("demografia", {}).get("sexo", {})
            f_s = s.get("feminino", {})
            m_s = s.get("masculino", {})
            facts_blocks.append(
                "**Comparativo por Sexo / Gênero**\n"
                f"- Vocabulário (0-50):\n"
                f"  * Meninas (F): média {f_s.get('vocab_media', 24.34)} pontos\n"
                f"  * Meninos (M): média {m_s.get('vocab_media', 21.88)} pontos\n"
                f"- TDE II Escrita (0-40):\n"
                f"  * Meninas (F): média {f_s.get('tde_media', 27.93)} pontos\n"
                f"  * Meninos (M): média {m_s.get('tde_media', 24.09)} pontos"
            )

        # -------------------------------------------------------------
        # 5. Censo Geral de Alunos, Turmas e Escolas (somente se não for uma pergunta focada em turma específica)
        # -------------------------------------------------------------
        if any(term in q_lower for term in ["quantos", "alunos", "censo", "participa", "turma", "escola", "rede", "avaliados", "faltosos"]) and not (matched_turmas or matched_eja):
            c = self.stats.get("censo", {})
            facts_blocks.append(
                "**Censo Oficial e Indicadores Principais (KPIs Gerais da Rede)**\n"
                f"- Total de Alunos Únicos Cadastrados: {c.get('total_alunos_unicos', 3016)} estudantes (chave ALUNO_[HEX]).\n"
                f"- Alunos Avaliados (fizeram ao menos uma prova): {c.get('alunos_avaliados', 2673)} estudantes (88,6%).\n"
                f"- Alunos Ausentes / Faltosos em todas as provas: {c.get('alunos_faltosos', 343)} estudantes (11,4%).\n"
                f"- Participação por Instrumento na Rede Geral:\n"
                f"  * Alunos únicos que realizaram Vocabulário (total): {c.get('alunos_vocab_total', 2574)} alunos\n"
                f"  * Alunos únicos que realizaram TDE II (total): {c.get('alunos_tde_total', 2499)} alunos\n"
                f"  * Alunos únicos que realizaram APENAS Vocabulário (sem TDE II): {c.get('alunos_apenas_vocab', 174)} alunos\n"
                f"  * Alunos únicos que realizaram APENAS TDE II (sem Vocabulário): {c.get('alunos_apenas_tde', 99)} alunos\n"
                f"  * Alunos únicos que realizaram AMBOS os testes (Vocabulário e TDE II): {c.get('alunos_ambos_testes', 2400)} alunos\n"
                f"- Turmas Únicas: {c.get('turmas_vocabulario', 80)} turmas em Vocabulário e {c.get('turmas_tde', 85)} turmas no TDE II.\n"
                f"- Escolas Participantes: {c.get('escolas_unicas', 13)} unidades municipais de ensino."
            )

        # -------------------------------------------------------------
        # 8. Filtro por Escola Específica
        # -------------------------------------------------------------
        escolas_completas = self.stats.get("por_escola_completo", {})
        for esc, e_info in escolas_completas.items():
            if esc.lower() in q_lower or any(word in q_lower for word in esc.lower().split() if len(word) > 4 and word not in ["escola", "municipal", "ensino", "fundamental", "basica", "básica", "professor", "professora", "padre", "santos", "silva"]):
                facts_blocks.append(
                    f"**Indicadores Completos da Escola: {esc} (Zona {e_info.get('zona', 'N/A')})**\n"
                    f"- Alunos únicos cadastrados: {e_info['alunos_unicos']} | Avaliados: {e_info['alunos_avaliados']} | Faltosos: {e_info['alunos_faltosos']}\n"
                    f"- Participação por Instrumento: Fizeram Vocabulário = {e_info['alunos_vocab_total']} (apenas Vocabulário: {e_info['alunos_apenas_vocab']}) | "
                    f"Fizeram TDE II = {e_info['alunos_tde_total']} (apenas TDE II: {e_info['alunos_apenas_tde']}) | Ambos os testes = {e_info['alunos_ambos_testes']}\n"
                    f"- Idade média: {e_info['idade_media']} anos (de {e_info['idade_minima']} a {e_info['idade_maxima']} anos)\n"
                    f"- Vocabulário: {e_info['vocab_avaliacoes']} provas (média {e_info['vocab_media']}) | {e_info['vocab_pares']} pares Pré/Pós (Pré: {e_info['vocab_media_pre']} -> Pós: {e_info['vocab_media_pos']}, Delta: {e_info['vocab_delta']}, dz: {e_info['vocab_dz']})\n"
                    f"- TDE II: {e_info['tde_avaliacoes']} provas (média {e_info['tde_media']}) | {e_info['tde_pares']} pares Pré/Pós (Pré: {e_info['tde_media_pre']} -> Pós: {e_info['tde_media_pos']}, Delta: {e_info['tde_delta']}, dz: {e_info['tde_dz']})\n"
                    f"- Turmas da escola: {', '.join(e_info.get('turmas', []))}"
                )

        # -------------------------------------------------------------
        # 9. Recuperação Semântica de Metodologia e Regras
        # -------------------------------------------------------------
        for doc in self.knowledge_base:
            if any(k in q_lower for k in ["pontua", "nota", "escore", "escala", "código", "dicot", "tentativa"]) and "instrumentos" in doc["id"]:
                methodology_blocks.append(f"**{doc['titulo']}**\n{doc['conteudo']}")
            elif any(k in q_lower for k in ["réplica", "replica", "copia", "cópia", "fase 3", "ricardo", "maria queiroz"]) and "replica" in doc["id"]:
                methodology_blocks.append(f"**{doc['titulo']}**\n{doc['conteudo']}")
            elif any(k in q_lower for k in ["falta", "ausente", "imputa", "omiss"]) and "ausentes" in doc["id"]:
                methodology_blocks.append(f"**{doc['titulo']}**\n{doc['conteudo']}")
            elif any(k in q_lower for k in ["qualidade", "dimens", "acurácia", "completude", "unicidade"]) and "qualidade" in doc["id"]:
                methodology_blocks.append(f"**{doc['titulo']}**\n{doc['conteudo']}")
            elif any(k in q_lower for k in ["machine learning", "ia", "regressão", "regressao", "classificação", "r2", "r²", "rmse", "auc", "feature"]) and "machine_learning" in doc["id"]:
                methodology_blocks.append(f"**{doc['titulo']}**\n{doc['conteudo']}")

        # -------------------------------------------------------------
        # 6. Desempenho, Médias Pré/Pós, Ganhos (Delta) e Cohen's dz
        # -------------------------------------------------------------
        perf_terms = ["desempenho", "média", "media", "ganho", "delta", "diferença", "diferenca", 
                      "melhora", "estabilidade", "estavel", "estável", "regressão", "regressao", "queda",
                      "tamanho do efeito", "effect size", "cohen", "dz", "pré", "pre", "pós", "pos", "resultado"]
        is_pure_ml_or_method = bool(methodology_blocks) and not any(t in q_lower for t in ["pares", "cohen", "dz", "delta", "melhora", "estabilidade"])
        if (any(term in q_lower for term in perf_terms) and not is_pure_ml_or_method) or (not facts_blocks and not methodology_blocks):
            v_stats = self.stats["vocabulario"]
            t_stats = self.stats["tde"]

            facts_blocks.append(
                "**Desempenho Pareado Pré vs Pós e Tamanho de Efeito (Cohen's dz)**\n"
                f"- Avaliação de Vocabulário (escala dicotômica 0 a 50 pontos):\n"
                f"  * Pares Válidos Completos: {v_stats['total_pares_limpos']} pares\n"
                f"  * Média Pré-teste: {v_stats['media_pre']} pontos | Média Pós-teste: {v_stats['media_pos']} pontos\n"
                f"  * Variação Média (Delta): +{v_stats['delta_medio']} pontos\n"
                f"  * Tamanho do Efeito (Cohen's dz): {v_stats['cohen_dz']} (efeito pequeno a moderado, estatisticamente significativo)\n"
                f"  * Distribuição dos Pares: {v_stats['ganho_alunos']} alunos com Melhora/Ganho ({v_stats['ganho_alunos']/v_stats['total_pares_limpos']*100:.1f}%), "
                f"{v_stats['estavel_alunos']} com Estabilidade ({v_stats['estavel_alunos']/v_stats['total_pares_limpos']*100:.1f}%), e {v_stats['queda_alunos']} com Regressão ({v_stats['queda_alunos']/v_stats['total_pares_limpos']*100:.1f}%).\n"
                f"- Avaliação do TDE II Escrita (escala dicotômica 0 a 40 pontos):\n"
                f"  * Pares Válidos Limpos: {t_stats['total_pares_limpos']} pares\n"
                f"  * Média Pré-teste: {t_stats['media_pre']} pontos | Média Pós-teste: {t_stats['media_pos']} pontos\n"
                f"  * Variação Média (Delta): +{t_stats['delta_medio']} pontos\n"
                f"  * Tamanho do Efeito (Cohen's dz): {t_stats['cohen_dz']} (efeito pequeno a moderado positivo)\n"
                f"  * Distribuição dos Pares: {t_stats['ganho_alunos']} alunos com Melhora/Ganho ({t_stats['ganho_alunos']/t_stats['total_pares_limpos']*100:.1f}%), "
                f"{t_stats['estavel_alunos']} com Estabilidade ({t_stats['estavel_alunos']/t_stats['total_pares_limpos']*100:.1f}%), e {t_stats['queda_alunos']} com Regressão ({t_stats['queda_alunos']/t_stats['total_pares_limpos']*100:.1f}%)."
            )

        # -------------------------------------------------------------
        # 7. Desempenho por Fase (Fase 2, Fase 3, Fase 4)
        # -------------------------------------------------------------
        if any(term in q_lower for term in ["fase", "etapa", "2023", "2024", "longitudinal", "evolução", "evolucao"]) and not is_pure_ml_or_method:
            facts_blocks.append(
                "**Desempenho por Fase e Ciclo Longitudinal**\n"
                "- Fase 2 (2023.2):\n"
                "  * Vocabulário: 1.854 pares | Pré: 21,05 -> Pós: 23,36 (Ganho +2,31)\n"
                "  * TDE II: 1.836 pares | Pré: 23,85 -> Pós: 26,96 (Ganho +3,11)\n"
                "- Fase 3 (2024.1):\n"
                "  * Vocabulário: 1.018 pares | Pré: 23,14 -> Pós: 24,32 (Ganho +1,18)\n"
                "  * TDE II: 903 pares limpos | Pré: 25,97 -> Pós: 27,77 (Ganho +1,80)\n"
                "- Fase 4 (2024.2):\n"
                "  * Vocabulário: 584 pares | Pré: 23,37 -> Pós: 25,13 (Ganho +1,76)\n"
                "  * TDE II: 493 pares | Pré: 28,16 -> Pós: 29,50 (Ganho +1,34)"
            )

        context_parts = []
        if facts_blocks:
            context_parts.append("=== DADOS ESTATÍSTICOS AUDITADOS DO PROJETO ===\n" + "\n\n".join(facts_blocks))
        if methodology_blocks:
            context_parts.append("=== CONTEXTO METODOLÓGICO E PSICOMÉTRICO ===\n" + "\n\n".join(methodology_blocks))

        return "\n\n".join(context_parts)

    def build_system_prompt(self, context_text: str) -> str:
        return (
            "Você é o Assistente Especialista em Inteligência Artificial e Avaliação Educacional "
            "do projeto WordGen / NEES (IA - Dataset).\n"
            "Sua missão é responder com máxima precisão, clareza e fundamentação técnica às dúvidas do usuário.\n\n"
            "DIRETRIZES DE RESPOSTA:\n"
            "1. PRECISÃO MATEMÁTICA E PROIBIÇÃO DE ESTIMATIVAS INVENTADAS: Utilize estritamente os dados estatísticos "
            "reais auditados apresentados no CONTEXTO abaixo. NUNCA tente 'estimar' ou inventar médias aproximadas por conta própria.\n"
            "2. IDADE, MODALIDADE, PERÍODOS DO EJA E PARTICIPAÇÃO NOS TESTES: O dataset possui todos os dados exatos por modalidade, período do EJA e turma:\n"
            "   - EJA Geral: 125 alunos únicos matriculados, média de idade de 29,96 anos (~30 anos), faixa de 16 a 60 anos. **0 alunos responderam ao Vocabulário e 0 alunos responderam ao TDE II** (todos os 125 alunos faltaram às provas, fez_teste = 0).\n"
            "   - 6º PERIODO (EJA): 41 alunos únicos matriculados (em 4 escolas), média de idade de 37,83 anos (mediana 37,0; mín 18, máx 60; DP 12,69). **0 alunos responderam ao TDE II e 0 alunos responderam ao Vocabulário** (todos os 41 alunos faltaram à prova).\n"
            "   - 7º PERIODO (EJA): 43 alunos únicos matriculados (em 4 escolas), média de idade de 28,07 anos (mediana 24,0; mín 16, máx 60; DP 10,35). **0 alunos responderam ao TDE II e 0 alunos responderam ao Vocabulário** (todos os 43 alunos faltaram à prova).\n"
            "   - 8º PERIODO (EJA): 41 alunos únicos matriculados em 2 escolas (EMEB Professor Ricardo Vieira de Lima com 37 alunos e EMEB Natanael da Silva com 4 alunos), média de idade de 24,07 anos (mediana 21,0; mín 17, máx 46; DP 7,99). **0 alunos responderam ao TDE II e 0 alunos responderam ao Vocabulário** (todos os 41 alunos faltaram à prova).\n"
            "   - REGRA CRÍTICA PARA O EJA: Se o usuário perguntar quantos alunos do EJA (ou do 6º, 7º ou 8º Período do EJA) responderam/fizeram o TDE II ou o Vocabulário, NUNCA diga que 'não há informações disponíveis'. Responda diretamente que **0 alunos (nenhum aluno)** daquele período do EJA responderam ao teste, pois todos os alunos matriculados na turma faltaram no dia da aplicação.\n"
            "   - Ensino Regular Geral: 2.891 alunos únicos, média de 14,14 anos (6º ANO: 12,50 anos; 7º ANO: 13,58 anos; 8º ANO: 14,53 anos; 9º ANO: 15,39 anos).\n"
            "3. GRANULARIDADE POR TURMA, SÉRIE, ESCOLA E INSTRUMENTO: O dataset possui todos os dados exatos por turma (ex: 6º ANO A, 6º ANO B, etc.), série e escola, incluindo quantos alunos únicos realizaram APENAS Vocabulário (sem TDE II), APENAS TDE II (sem Vocabulário), AMBOS os testes, o total de alunos avaliados em cada instrumento e os faltosos. NUNCA diga que o projeto não fornece detalhes por turma ou por prova. Sempre responda citando os números exatos do bloco da turma/série/escola consultada.\n"
            "4. VARIÁVEIS NÃO COLETADAS: Se o usuário perguntar sobre renda familiar, classe socioeconômica ou outras disciplinas, "
            "esclareça educadamente que essas variáveis NÃO foram coletadas nos questionários escolares da pesquisa, "
            "mas que os dados demográficos de idade, sexo, cor/raça, modalidade e zona estão disponíveis.\n"
            "5. PRIVACIDADE E LGPD: Os nomes civis completos dos alunos foram substituídos pelo identificador canônico ALUNO_[HEX] "
            "em conformidade com a LGPD.\n"
            "6. FORMATAÇÃO LIMPA (SEM '#'): NUNCA utilize o símbolo '#' (como #, ##, ### ou ####) em suas respostas. "
            "Para títulos, subtítulos e destaques, utilize exclusivamente texto em negrito (**Título**).\n"
            "7. BLOQUEIO ESTRITO DE ESCOPO: Você é estritamente proibido de responder perguntas sobre história geral, geografia, "
            "política, esportes, receitas, programação genérica ou qualquer assunto que não diga respeito aos dados acadêmicos "
            "do projeto WordGen / NEES. Caso o usuário misture um assunto externo, recuse o assunto externo.\n\n"
            f"{context_text}"
        )


def clean_markdown_hashes(text: str) -> str:
    """Remove qualquer marcação '#' de cabeçalho Markdown, convertendo em negrito limpo."""
    # Converte linhas iniciadas com #, ##, ###, etc. em **Título**
    cleaned = re.sub(r"(?m)^\s*#{1,6}\s*(.+?)\s*#*$", lambda m: f"**{m.group(1).strip('* ')}**", text)
    # Remove eventuais sequências de ### soltas no meio do texto
    cleaned = re.sub(r"#{2,}\s*", "", cleaned)
    return cleaned


class LlamaChatEngine:
    """Interface de comunicação com o Llama 3.2 via Ollama."""

    OUT_OF_SCOPE_MESSAGE = (
        "Pergunta fora do escopo. Respondo apenas dúvidas sobre os dados acadêmicos "
        "do projeto **WordGen / NEES** (avaliações, alunos, escolas, turmas, idades e metodologia)."
    )

    GREETING_MESSAGE = (
        "Olá! Sou o assistente do projeto **WordGen / NEES**. "
        "Pergunte-me sobre médias de Vocabulário e TDE II, alunos, escolas, turmas, idades (EJA e Regular) ou metodologia."
    )

    def __init__(self, model_name: str = "llama3.2:3b"):
        self.model_name = model_name
        self.analytics_engine = DataAnalyticsEngine()

    def is_ollama_ready(self) -> bool:
        try:
            req = urllib.request.urlopen(f"{OLLAMA_API_URL}/tags", timeout=2)
            return req.status == 200
        except Exception:
            return False

    def ask(self, question: str, history: list[dict] | None = None) -> str:
        in_domain, reason = self.analytics_engine.is_in_domain(question, history)
        if not in_domain:
            if reason == "greeting":
                return self.GREETING_MESSAGE
            return self.OUT_OF_SCOPE_MESSAGE

        context = self.analytics_engine.retrieve_context(question, history)
        system_prompt = self.analytics_engine.build_system_prompt(context)

        messages = [{"role": "system", "content": system_prompt}]
        if history:
            messages.extend(history)
        messages.append({"role": "user", "content": question})

        payload = {
            "model": self.model_name,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": 0.1,  # Baixa temperatura para fidelidade factual
                "top_p": 0.9,
                "num_ctx": 4096
            }
        }

        try:
            req = urllib.request.Request(
                f"{OLLAMA_API_URL}/chat",
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=60) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return clean_markdown_hashes(data["message"]["content"])
        except Exception:
            # Fallback determinístico de alta fidelidade caso o Ollama esteja offline ou não instalado
            return clean_markdown_hashes(
                "*(Serviço Ollama / Llama 3.2 local offline. Resposta gerada diretamente pela Camada Analítica de Dados do Projeto):*\n\n"
                f"{context}"
            )


if __name__ == "__main__":
    engine = LlamaChatEngine()
    print("Testando motor analítico com pergunta sobre EJA...")
    resp = engine.ask("Me fale a média de idade de estudante do EJA")
    print(resp)
