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

## ⚙️ Requisitos de Hardware e Modos de Operação

O sistema opera de forma desacoplada em dois modos distintos para viabilizar execução em qualquer hardware:

| Componente | Modo Leve / Analítico (Padrão) | Modo Neural Local (Recomendado) | Modo Neural Local (CPU Fallback) |
| :--- | :--- | :--- | :--- |
| **Finalidade** | Dashboard Web + Respostas Determinísticas | Síntese de Linguagem Natural (LLM) | Síntese Neural sem GPU Dedicada |
| **Motor Ativo** | `DataAnalyticsEngine` (Python puro) | Ollama (`llama3.2:3b` Q4_K_M via CUDA/Metal) | Ollama (`llama3.2:3b` via AVX2) |
| **Processador (CPU)** | 2 Núcleos (Intel Core i3 / Ryzen 3 / ARM) | 4 Núcleos (Intel Core i5 / Ryzen 5) | 4+ Núcleos com AVX2 (i5 8ª ger+ / Ryzen 5) |
| **Memória RAM** | **2 GB** (Consumo efetivo < 150 MB) | **8 GB** | **8 GB** (Aloca ~2.5 GB para o modelo) |
| **Placa de Vídeo (GPU)** | **Não requer GPU** | **NVIDIA RTX 3050 (4GB+) / Apple Silicon** | **Não requer GPU** |
| **VRAM Dedicada** | 0 MB | **Mínimo 3.5 GB a 4 GB** (Modelo ocupa ~2.0 GB) | 0 MB |
| **Armazenamento** | 250 MB livres | 2.5 GB livres (Base + Pesos do Modelo) | 2.5 GB livres |
| **Tempo de Resposta** | **< 0,05s** (Instantâneo) | **1,5s a 3,0s** por resposta | **6,0s a 12,0s** por resposta |
| **Dependências** | Python 3.9+ nativo (zero `pip`) | Python 3.9+ e Ollama instalado | Python 3.9+ e Ollama instalado |

### Como ativar a aceleração por GPU com Ollama:
1. Instale o Ollama ([ollama.com](https://ollama.com)).
2. Baixe o modelo neural leve:
   ```bash
   ollama pull llama3.2:3b
   ```
3. Inicie o serviço com `ollama serve` (ou deixe o Ollama em segundo plano no sistema). O dashboard detecta automaticamente a presença da GPU e ativa a síntese neural fluida. Se o Ollama estiver desligado, o assistente ativa imediatamente o **Modo Analítico Local** sem qualquer quebra de fluxo.

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

## 🤖 Assistente de IA WordGen (RAG Híbrido Zero Alucinação)

O painel integra um assistente com arquitetura híbrida de recuperação e resposta:

* **Precisão Cirúrgica e Respostas Metódicas:** Consultas pontuais (ex.: *"Qual a média de idade do 6º ANO A?"* ou *"Quantos alunos da turma 6B fizeram apenas Vocabulário?"*) são processadas diretamente pelo `DataAnalyticsEngine`, fornecendo respostas concisas, metódicas e sem dispersão.
* **Bloqueio de Escopo em 2 Camadas:** Consultas externas ao projeto (ex.: *"Quem descobriu o Brasil?"*) são bloqueadas instantaneamente (`0,00s`) por guardrails algorítmicos.
* **Anonimização Integral e Conformidade com a LGPD (Art. 14):** Identificadores canônicos criptográficos (`ALUNO_[HEX]`), sem exposição de dados nominais. O repositório completo (inclusive planilhas de origem em `Fases/`) foi auditado e sanitizado, com expurgo total de CPFs, e-mails, telefones e nomes de responsáveis de menores.
* **Apresentação Limpa:** Formatação higienizada sem marcadores pesados (`###`, `===` ou separadores repetidos).

---

## 📁 Estrutura do Repositório

```text
IA - Dataset/
├── README.md                          <- Manual principal executivo e guia de hardware
├── .gitignore                         <- Bloqueio de arquivos temporários e caches
├── apresentacao/                      <- Roteiro executivo de vídeo (7min30s) e dossiê de evidências dos 3 trabalhos
│   ├── README.md                      <- Índice da apresentação
│   ├── ROTEIRO_VIDEO.md               <- Roteiro completo cronometrado para gravação (Dados -> ML -> IA)
│   └── EVIDENCIAS_E_PRODUCAO.md       <- Dossiê de evidências empíricas e diretrizes de produção
├── Scripts/                           <- Scripts executáveis, inicializadores e dependências
│   ├── iniciar.sh                     <- Inicializador automático (Linux / macOS)
│   ├── iniciar.bat                    <- Inicializador automático (Windows)
│   ├── requirements.txt               <- Dependências científicas opcionais (pandas, scikit-learn)
│   ├── environment.yml                <- Configuração de ambiente Conda opcional
│   ├── preparar_dados_ia.py           <- Gerador da base semântica e estatísticas consolidadas da IA
│   ├── ia_engine.py                   <- Camada Analítica e orquestrador RAG do Llama 3.2
│   ├── benchmark_ia.py                <- Bateria de 18 testes de qualidade da IA (100% de acurácia)
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
   *100% aprovado (18/18 cenários): avalia acurácia censitária, psicometria, interseção Vocabulário vs. TDE II por turma, participação e idades da EJA/Regular, períodos do EJA, LGPD, bloqueio de escopo e conformidade de formatação.*

---

## 📚 Documentação Complementar

Para aprofundamento técnico, consulte os arquivos nas pastas **`Contexts/`** e **`apresentacao/`**:

* 🎥 [**Roteiro e Evidências da Apresentação**](apresentacao/README.md): Roteiro cronometrado (7min30s) estruturado para gravação em vídeo, integrando a síntese acadêmica dos 3 trabalhos (Engenharia de Dados, Modelagem de Machine Learning e Assistente de IA) e seu dossiê de evidências empíricas.
* 🗺️ [**Roadmap de Execução e Metodologia Unificada**](Contexts/ROADMAP_EXECUCAO.md): Histórico completo de execução, justificativa dos 27 arquivos não avaliativos, desambiguação EJA vs Regular, estratégia de imputação psicométrica, guia de organização, dicionário de variáveis e modelos de Machine Learning.
* 📊 [**Censo de Alunos Únicos**](Contexts/relatorio_alunos_unicos.csv): Tabela dimensional com os 3.016 estudantes auditados.
* 📋 [**Manifesto de Processamento**](Contexts/manifesto_processamento.csv): Registro de proveniência das 208 planilhas originais do NEES.

---
