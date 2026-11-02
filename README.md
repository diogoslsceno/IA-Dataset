# IA - Dataset: Plataforma Educacional & Assistente IA (WordGen / NEES)

> **Ambiente:** Python 3.9+ (Standard Library) | **Frontend:** Vanilla JS (Clean Architecture) | **IA:** Llama 3.2 3B Local

Plataforma integrada de **análise psicométrica, visualização interativa de dados e inteligência artificial generativa local** desenvolvida sobre as avaliações educacionais do projeto **WordGen / NEES** (Fases 2, 3 e 4).

---

## 🚀 Início Rápido (Execução em 1 Clique)

A aplicação foi desenvolvida para ser **100% portável** e roda imediatamente utilizando exclusivamente a biblioteca padrão do Python (sem necessidade de instalar pacotes via `pip` para usar o dashboard):

### No Linux ou macOS:
```bash
./Scripts/iniciar.sh
```

### No Windows:
Dê duplo clique em **`Scripts\iniciar.bat`** (ou execute via Prompt de Comando).

Acesse diretamente pelo navegador:
👉 **[http://localhost:8765/dist/](http://localhost:8765/dist/)**

*(Para encerrar a aplicação, pressione `CTRL + C` no terminal).*

---

## 📊 Censo Auditado e Indicadores Principais

A auditoria estatística executada sobre as **208 planilhas higienizadas** confirma:

| Indicador | Vocabulário (0–50) | TDE II Escrita (0–40) | Censo Integrado da Rede |
| :--- | :---: | :---: | :---: |
| **Total de Alunos Únicos** | 2.967 alunos | 2.969 alunos | **3.016 alunos cadastrados** |
| **Alunos Avaliados (`fez_teste=1`)** | 8.882 avaliações | 9.049 avaliações | **2.673 estudantes avaliados** (88,6%) |
| **Alunos Ausentes em Todas as Fases** | — | — | **343 estudantes faltosos** (11,4%) |
| **Pares Completos (Pré $\times$ Pós)** | **3.456 pares limpos** | **3.232 pares limpos** | Sem contaminação por réplicas |
| **Tamanho do Efeito (Cohen's $d_z$)** | **$0,30$** (Positivo) | **$0,32$** (Positivo) | Ganho estatisticamente significativo |
| **Distribuição dos Pares** | ▲ 52,7% \| ■ 8,1% \| ▼ 39,2% | ▲ 46,9% \| ■ 12,0% \| ▼ 41,1% | Proporção ganho, estabilidade e regressão |

---

## 💻 Dashboard Web Interativo (Clean Architecture)

Desenvolvido segundo os princípios de **Clean Architecture / DDD** com separação estrita de camadas (`domain`, `application`, `infrastructure`, `presentation`):

* 🎯 **KPIs Gerais:** Contagem de alunos únicos, turmas únicas e avaliações realizadas com escore válido.
* 🔍 **Filtros Dinâmicos:** Seletores reativos por Escola, por Turma e por Instrumento (Vocabulário $\longleftrightarrow$ TDE II).
* ⚖️ **Comutador de Escala:** Alternância instantânea entre **Pontos Brutos** (0–50 / 0–40) e **Normalizado (0–100% de aproveitamento)** para comparação direta.
* 📈 **Comparação Pré $\times$ Pós e Effect Size:** Médias pareadas e cálculo amostral do $d_z$ de Cohen.
* ⏳ **Trajetória Longitudinal:** Acompanhamento contínuo da mesma coorte de alunos ao longo das 3 fases.
* 🏙️ **Equidade Sociodemográfica:** Análise descritiva por Zona (Urbana vs Rural), Sexo, Cor/Raça e Modalidade (Regular vs EJA).

---

## 🤖 Assistente de IA WordGen (Llama 3.2 3B Local)

O painel integra um chatbot conversacional com **RAG Híbrido Semântico-Determinístico (Zero Alucinação)**:

* **Precisão Matemática e Granularidade por Turma/Instrumento:** Perguntas sobre quantidades, médias de idade, diferenças entre zona urbana e rural, períodos do EJA (`6º`, `7º` e `8º PERIODO (EJA)`) ou cruzamento de provas por turma (`6º ANO A` a `9º ANO G`, incluindo alunos que realizaram **apenas Vocabulário**, **apenas TDE II** ou **ambos os testes**, mesmo com variações de digitação como `"6 sno B"`) são calculadas pela `DataAnalyticsEngine` diretamente sobre os microdados auditados.
* **Bloqueio Estrito de Escopo (Guardrail) e Formatação Limpa:** Recusa instantaneamente (`0,00s`) perguntas fora do escopo acadêmico do projeto com mensagem concisa, mantendo formatação limpa sem marcações `#`.
* **Respeito à LGPD e Limites:** Nomes de estudantes são anonimizados (`ALUNO_[HEX]`). Variáveis não coletadas na pesquisa (como renda familiar) são devidamente explicadas.
* **Operação Resiliente:**
  * **Com Ollama ativo:** Síntese em linguagem natural fluida utilizando o modelo local `llama3.2:3b`.
  * **Sem Ollama (Offline):** O assistente ativa automaticamente o **Modo Analítico Local**, apresentando as respostas e estatísticas reais sem interromper o dashboard.

> **Para ativar o modelo neural completo com Ollama:**  
> Instale o Ollama ([ollama.com](https://ollama.com)) e execute: `ollama run llama3.2:3b`.

---

## 📁 Estrutura do Repositório

```text
IA - Dataset/
├── README.md                          <- Manual principal executivo
├── .gitignore                         <- Bloqueio de arquivos temporários e caches
├── Scripts/                           <- Scripts executáveis, inicializadores e dependências
│   ├── iniciar.sh                     <- Inicializador automático (Linux / macOS)
│   ├── iniciar.bat                    <- Inicializador automático (Windows)
│   ├── requirements.txt               <- Dependências científicas opcionais (pandas, scikit-learn)
│   ├── environment.yml                <- Configuração de ambiente Conda opcional
│   ├── preparar_dados_ia.py           <- Gerador da base semântica e estatísticas consolidadas da IA
│   ├── ia_engine.py                   <- Camada Analítica e orquestrador RAG do Llama 3.2
│   ├── benchmark_ia.py                <- Bateria de 17 testes de qualidade da IA (100% de acurácia)
│   ├── contagem_oficial.py            <- Script autônomo de auditoria de alunos únicos
│   ├── modelagem_ml.py                <- Pipeline preditivo sem vazamento de dados (GroupKFold)
│   └── auditoria_6_dimensoes.py       <- Autoavaliação das 6 dimensões de qualidade
├── Contexts/                          <- Documentação unificada, relatórios e base de conhecimento da IA
│   ├── ROADMAP_EXECUCAO.md            <- Roadmap completo, metodologia, guia de organização e imputação
│   ├── relatorio_alunos_unicos.csv    <- Censo oficial dos 3.016 alunos (LGPD)
│   ├── manifesto_processamento.csv    <- Rastreabilidade das 208 planilhas originais
│   ├── base_conhecimento.json         <- Base semântica de regras e metodologia para a IA
│   └── estatisticas_consolidadas.json <- Catálogo estatístico auditado para o motor da IA
├── dashboard/                         <- Aplicação Web (Clean Architecture), Servidor HTTP e Datasets (`data/`)
├── Fases/                             <- 208 planilhas higienizadas das Fases 2, 3 e 4
└── Notebooks/                         <- Cadernos de higienização do Google Colab
```

---

## 🧪 Testes Automatizados e Auditoria

O projeto conta com validação automatizada em duas frentes:

1. **Testes Unitários do Dashboard (`npm test`):**
   ```bash
   cd dashboard && npm test
   ```
   *100% aprovado (4/4 testes): integridade de pares, cálculo amostral do $d_z$, isolamento de réplicas e persistência da coorte.*

2. **Benchmark Oficial da IA (Gold Standard):**
   ```bash
   python3 Scripts/benchmark_ia.py
   ```
   *100% aprovado (17/17 testes): avalia acurácia de contagem, psicometria, interseção Vocabulário vs. TDE II por turma, participação e idades da EJA/Regular, períodos do EJA, LGPD e bloqueio de escopo.*

---

## 📚 Documentação Complementar

Para aprofundamento técnico, consulte os arquivos na pasta **`Contexts/`**:

* 🗺️ [**Roadmap de Execução e Metodologia Unificada**](Contexts/ROADMAP_EXECUCAO.md): Contém todo o histórico de execução, justificativa dos 27 arquivos não avaliativos, desambiguação EJA vs Regular, estratégia de imputação psicométrica, guia de organização das pastas, dicionário de variáveis e modelos de Machine Learning.
* 📊 [**Censo de Alunos Únicos**](Contexts/relatorio_alunos_unicos.csv): Tabela dimensional com os 3.016 estudantes auditados.
* 📋 [**Manifesto de Processamento**](Contexts/manifesto_processamento.csv): Registro de proveniência das 208 planilhas originais do NEES.

---
