# Dashboard WordGen · etapa 1

## Executar

Na raiz do repositório:

```bash
# Preparar dados estáticos (se necessário atualizar os JSONs)
python3 dashboard/prepare_data.py

# Iniciar o Servidor Integrado (Dashboard + Chatbot de IA Llama 3.2):
python3 dashboard/server_com_chat.py
```

O comando inicia o servidor HTTP e os endpoints de IA na porta `8765`:
- **Dashboard Web:** Abra `http://localhost:8765/dist/` em seu navegador.
- **Chatbot Integrado:** Disponível via ícone flutuante no canto inferior direito do dashboard (ou via API `POST /api/chat`).
- **Relatório de Benchmark da IA:** Disponível via `GET /api/benchmark`.

*(Observação: Caso deseje executar apenas o servidor estático simples sem o chatbot de IA, utilize: `python3 -m http.server 8765 --bind 127.0.0.1 --directory dashboard`).*

Para testar as regras de domínio do dashboard: `cd dashboard && npm test`.
Para reexecutar o benchmark de qualidade do Llama 3.2: `python3 Scripts/benchmark_ia.py`.

## Arquitetura

| Camada | Local | Responsabilidade |
| --- | --- | --- |
| Infraestrutura | `prepare_data.py`, `src/infrastructure` | Lê os 181 CSVs tratados, consolida cada instrumento e carrega as bases locais. |
| Domínio | `src/domain` | Identidade, KPIs, pares, estatísticas e agregações sem acesso à interface. |
| Aplicação | `src/application` | Aplica filtros às duas bases e compõe os resultados do painel. |
| Apresentação | `dist`, `src/presentation` | Interface responsiva e gráficos SVG/HTML. |

O pipeline gera `data/vocabulario.csv` e `data/tde.csv` **separados**, com itens Q1–Q50 ou P1–P40, indicadores de presença, atributos sociodemográficos e origem do arquivo. Os JSONs em `dist/data` contêm somente os campos analíticos necessários ao painel. `data/auditoria.json` contém contagens e conflitos observados. O dashboard é local porque os registros pseudonimizados incluem atributos individuais sensíveis.

## Organização dos datasets (`dashboard/data/`)

| Arquivo em `data/` | Finalidade e conteúdo | Registros consolidados |
| --- | --- | ---: |
| [`vocabulario.csv`](data/vocabulario.csv) | Avaliação de Vocabulário: identificador anônimo, escola, turma, fase, momento, presença, total (0–50), itens Q1–Q50, perfil informado, `replica_pre` e arquivo de origem. | 11.807 |
| [`tde.csv`](data/tde.csv) | TDE II Escrita: os mesmos campos comuns, total na escala dicotômica unificada (0–40), itens P1–P40 e flag `replica_pre` para isolamento de réplicas de monitoria. | 12.516 |

## Regras analíticas

- Cada avaliação é identificada por **aluno canônico + fase + momento + instrumento**. Em duplicatas, tem prioridade o registro presente com escore válido, depois o de maior cobertura de itens e metadados. Conflitos de escore são contabilizados na auditoria; a origem vencedora fica no CSV consolidado.
- As grafias de escola e turma são normalizadas para caixa alta, remoção de acentos e espaços; turmas são contadas pelo par **escola + turma**. A identificação da pessoa usa exclusivamente o código `ALUNO_[HEX]`.
- Faltosos ficam com `total` vazio, mesmo se o CSV de origem contém valor. Escore válido: 0–50 em Vocabulário e 0–40 em TDE (escala dicotômica unificada: 0 para erro/branco e 1 para acerto total ou parcial). Um total ausente de aluno presente é recalculado somente quando há itens válidos. Dados sem escore não entram nas médias ou na contagem de avaliações realizadas.
- O par pré/pós exige o **mesmo aluno, fase e instrumento**, ambos presentes, com escore válido e sem réplica de itens (`replica_pre !== 1`). Provas de pós-teste que sejam cópias literais do pré-teste são sinalizadas e expurgadas da formação de pares primários, garantindo estimativas de ganho fidedignas (3.456 pares em Vocabulário e 3.232 em TDE II). A comparação exibe as médias dos pares e a distribuição do $\Delta$ (proporção de alunos com ganho ▲, estabilidade ■ ou regressão ▼).
- O seletor de **Escala** permite comutar a visualização entre **Pontos brutos** (0–50 em Vocabulário ou 0–40 em TDE) e **Normalizado (0–100% de aproveitamento)**, viabilizando a análise comparativa direta entre os dois instrumentos no mesmo gráfico.
- O tamanho do efeito é `d_z` de Cohen, a média das diferenças dividida pelo desvio padrão **amostral** das diferenças. Não é calculado com menos de dois pares ou desvio zero. Os limiares visuais de magnitude são 0,2/0,5/0,8 e devem ser interpretados com contexto pedagógico.
- A série longitudinal usa uma **coorte completa**: os mesmos alunos com escore no pré e pós de todas as três fases. Quando o filtro não contém tal coorte, o gráfico fica vazio. As análises de zona, cor/raça, sexo e modalidade são descritivas, sem inferência causal. Renda familiar não consta dos CSVs tratados, portanto não é exibida.
- O filtro de escola/turma afeta as duas bases e todos os KPIs. O filtro de categoria escolhe a base dos gráficos e do tamanho do efeito; os KPIs de avaliações continuam separados para facilitar a comparação de cobertura.

O pipeline reaproveita o tratamento psicométrico já registrado nos notebooks e na documentação. Não executa uma segunda imputação nem substitui os arquivos originais.
