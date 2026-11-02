# Roadmaps, evidências e plano de produção

**Escopo conferido em 02/11/2026.** A inspeção cobriu a árvore completa do repositório (255 arquivos), os 208 CSVs em `Fases/`, dois notebooks, dois CSVs consolidados, relatórios JSON/CSV, documentação, pipeline de ML, servidor, interface e benchmark. Foram conferidas diretamente as contagens e estatísticas pareadas dos CSVs consolidados, sem modificar os projetos. Os arquivos Excel que precederam a extração não estão nesta cópia.

## Roadmap 1 — dados e visualização

1. **Objetivo:** tornar comparáveis os resultados pré e pós de Vocabulário e TDE II Escrita nas fases 2 (2023.2), 3 (2024.1) e 4 (2024.2), preservando contexto escolar e demográfico.
2. **Origem:** 208 CSVs em `Fases/`, dos quais 181 avaliativos tratados e 27 administrativos separados. O [manifesto](../Contexts/manifesto_processamento.csv) documenta a procedência por arquivo e aba; as planilhas `.xlsx` de origem não estão no repositório. Há 70.217 linhas nos arquivos da fase, segundo a [auditoria documentada](../Contexts/ROADMAP_EXECUCAO.md).
3. **Exploração:** inspeção de cabeçalhos, delimitadores, itens Q1–Q50 e P1–P40, presença, notas, campos sociodemográficos, duplicidades e coerência temporal. Os dois [notebooks](../Notebooks/) documentam o tratamento, mas não contêm saídas executadas salvas.
4. **Tratamento:** limpeza de erros de planilha e grafias, diferenciação entre EJA e regular, identificador pseudonimizado, separação de faltosos e omissões de alunos presentes, harmonização dos itens em 0/1, reconciliação de aplicações repetidas e sinalização de réplicas de pós-teste. A consolidação preserva dois datasets separados.
5. **Comparação antes/depois:** o relatório de [auditoria da consolidação](../dashboard/data/auditoria.json) registra 17.290 linhas lidas de Vocabulário em 90 arquivos e 32.522 linhas de TDE II em 91 arquivos. Foram resolvidas 2.393 e 9.145 duplicidades, respectivamente. As bases finais têm 11.807 e 12.516 aplicações únicas; 438 registros TDE têm sinalização de réplica. “Linhas lidas”, “duplicatas resolvidas” e “aplicações finais” têm escopos diferentes e não formam uma subtração direta.
6. **Resultados:** o censo integrado tem 3.016 estudantes cadastrados para avaliações, 2.673 com algum teste e 343 sem teste realizado. Há 8.882 avaliações com escore em Vocabulário e 9.049 em TDE II; 3.456 e 3.232 pares válidos, respectivamente. A auditoria de qualidade marca unicidade e coerência entre itens e total em 1,0 para ambos; a consistência livre de réplicas no TDE aparece como 0,965, porque as réplicas permanecem sinalizadas na base.
7. **Interpretação:** Vocabulário teve média pareada 23,16 → 23,89, diferença +0,73 e Cohen d_z ≈ 0,11; TDE II 25,84 → 25,30, diferença −0,54 e d_z ≈ −0,065. Em Vocabulário, melhora/estabilidade/queda = 1.820/280/1.356; em TDE II = 1.515/280/1.437. O tratamento evita que cópias distorçam pares e indicadores. Os resultados não estabelecem efeito causal da intervenção.
8. **Continuidade:** os [CSVs consolidados](../dashboard/data/) abastecem painel e ML; o catálogo [estatístico](../Contexts/estatisticas_consolidadas.json) e a [base de conhecimento](../Contexts/base_conhecimento.json) alimentam o assistente.

**Fontes principais:** [README do painel](../dashboard/README.md), [auditoria](../dashboard/data/auditoria.json), [qualidade](../dashboard/data/qualidade_6_dimensoes.csv), [censo](../Contexts/relatorio_alunos_unicos.csv), [Vocabulário](../dashboard/data/vocabulario.csv), [TDE II](../dashboard/data/tde.csv), [consolidador](../dashboard/prepare_data.py).

### Resultados qualitativos comprovados

- A separação entre ausência à prova e omissão de item evita interpretar faltosos como alunos de escore zero.
- A identificação canônica e o desempate de aplicações reduzem contagem duplicada; a origem escolhida fica registrada na base final.
- A sinalização das réplicas de TDE II permite preservá-las para auditoria enquanto os pares analíticos as excluem.
- A distinção EJA/regular impede misturar períodos da EJA com anos escolares regulares na análise de idade.
- O painel permite examinar diferenças descritivas por escola, turma, fase, instrumento e características cadastradas, inclusive quando não há coorte completa para determinada seleção.
- A classificação de risco apresenta capacidade de discriminação limitada pelas AUCs observadas; serve como experimento preditivo, não como decisão pedagógica individual automatizada.

## Roadmap 2 — aprendizado de máquina

1. **Problemas:** prever o escore pós-teste (regressão) e classificar ganho nulo ou negativo, definido por pós − pré ≤ 0.
2. **Dados:** pares limpos dos mesmos alunos por fase e instrumento: 3.456 em 80 turmas de Vocabulário; 3.232 em 85 turmas de TDE II. Pós-testes marcados como réplica ficam fora desses pares.
3. **Entradas:** escore pré, idade, distorção idade-série, sexo, cor/raça, zona, modalidade e fase. O script preenche idades ausentes pela mediana e codifica categorias para treino.
4. **Treinamento e teste:** `GroupKFold` com cinco divisões por escola e turma. Em cada divisão, modelos são treinados nos grupos de treino e avaliados nos grupos restantes; os valores abaixo são médias das cinco divisões, não resultados de um único teste separado.
5. **Regressão:** baseline de média, Ridge, Random Forest e Gradient Boosting. Métricas: raiz do erro quadrático médio (RMSE), erro absoluto médio (MAE) e R².
6. **Classificação:** baseline majoritária, Regressão Logística, Árvore de Decisão, Random Forest e Gradient Boosting. Métricas: acurácia, F1 e área sob a curva ROC (AUC).
7. **Conclusão:** no Vocabulário, Random Forest tem maior R² médio; no TDE II, Ridge tem maior R² médio. Para classificação, a melhor acurácia média é da Regressão Logística em Vocabulário e de Gradient Boosting no TDE II. As taxas observadas de ganho não positivo são 47,34% e 53,13%, respectivamente.

### Resultados quantitativos salvos de ML

| Instrumento e tarefa | Modelo | Métricas médias de validação |
| --- | --- | --- |
| Vocabulário, regressão | Baseline de média | RMSE 9,596; MAE 8,137; R² −0,012 |
| Vocabulário, regressão | Ridge | RMSE 6,284; MAE 4,715; R² 0,564 |
| Vocabulário, regressão | Random Forest | RMSE 6,125; MAE 4,603; R² 0,586 |
| Vocabulário, regressão | Gradient Boosting | RMSE 6,136; MAE 4,621; R² 0,585 |
| TDE II, regressão | Baseline de média | RMSE 12,440; MAE 10,735; R² −0,020 |
| TDE II, regressão | Ridge | RMSE 7,546; MAE 5,660; R² 0,623 |
| TDE II, regressão | Random Forest | RMSE 7,585; MAE 5,649; R² 0,619 |
| TDE II, regressão | Gradient Boosting | RMSE 7,593; MAE 5,623; R² 0,618 |
| Vocabulário, classificação | Baseline majoritária | Acurácia 52,67%; F1 0,000; AUC 0,500 |
| Vocabulário, classificação | Regressão Logística | Acurácia 57,98%; F1 0,525; AUC 0,617 |
| Vocabulário, classificação | Árvore de Decisão | Acurácia 55,61%; F1 0,536; AUC 0,589 |
| Vocabulário, classificação | Random Forest | Acurácia 57,70%; F1 0,533; AUC 0,612 |
| Vocabulário, classificação | Gradient Boosting | Acurácia 57,70%; F1 0,538; AUC 0,611 |
| TDE II, classificação | Baseline majoritária | Acurácia 53,12%; F1 0,693; AUC 0,500 |
| TDE II, classificação | Regressão Logística | Acurácia 60,83%; F1 0,646; AUC 0,658 |
| TDE II, classificação | Árvore de Decisão | Acurácia 64,48%; F1 0,683; AUC 0,697 |
| TDE II, classificação | Random Forest | Acurácia 63,99%; F1 0,680; AUC 0,705 |
| TDE II, classificação | Gradient Boosting | Acurácia 65,81%; F1 0,679; AUC 0,712 |

**Atributo predominante:** o escore pré representa 94,28% da importância da Random Forest ajustada ao conjunto completo em Vocabulário e 88,13% em TDE II. Essa importância é do ajuste descritivo final e não uma estimativa de validação nem causalidade. Fonte: [resultados_ml.json](../dashboard/data/resultados_ml.json) e [pipeline](../Scripts/modelagem_ml.py).

**Predições individuais e agrupamentos:** não há arquivo de predições por estudante/dobra, modelo serializado, notebook de ML executado ou resultado de K-Means neste repositório. A referência a K-Means no [roadmap mestre](../Contexts/ROADMAP_EXECUCAO.md) descreve proposta ou estado anterior e não é confirmada pelo pipeline atual. Portanto, quantidade de clusters, critérios, rótulos, características e exemplos reais não podem ser apresentados. Para uma versão futura da demonstração, é preciso registrar predições de casos de teste, respectivos valores reais e grupos de validação, e realizar/documentar o agrupamento caso ele faça parte do escopo efetivo.

**Limite metodológico a confirmar:** no [pipeline](../Scripts/modelagem_ml.py), a mediana da idade e a codificação categórica são calculadas antes das cinco divisões. Isso não invalida as métricas salvas como relato do experimento, mas a ausência de transformação ajustada dentro de cada dobra impede afirmar blindagem completa contra vazamento de pré-processamento.

## Roadmap 3 — assistente com recuperação e LLM

1. **Objetivo:** responder em português a consultas sobre avaliações, censo, turmas, metodologia e métricas por uma interface de conversa no dashboard.
2. **Conhecimento:** sete tópicos estruturados em [base_conhecimento.json](../Contexts/base_conhecimento.json), catálogo de estatísticas em [estatisticas_consolidadas.json](../Contexts/estatisticas_consolidadas.json) e consultas analíticas implementadas sobre os dados. O catálogo deriva dos datasets tratados e de resultados do projeto.
3. **Organização e recuperação:** a base está dividida em entradas temáticas de JSON; o motor seleciona trechos e estatísticas por entidades, intenção e regras. Não foi localizado pipeline de fragmentação de documentos, geração de embeddings, índice vetorial, ChromaDB, FAISS ou outro banco vetorial. ChromaDB/LangChain aparecem como proposta na documentação, sem implementação nos arquivos presentes.
4. **Geração:** o contexto recuperado entra no prompt do modelo local `llama3.2:3b` via Ollama, quando o serviço está disponível. Se indisponível, o sistema devolve o contexto analítico diretamente, identificado como modo local. Portanto, o sistema combina recuperação estruturada, cálculo determinístico e geração por LLM apenas no modo neural.
5. **Interface e recursos:** widget de chat no dashboard, `POST /api/chat`, `GET /api/status`, resposta para perguntas fora do escopo e proteção de identificadores. Não há integração Telegram localizada. O servidor e modo local usam biblioteca padrão Python; a interface usa JavaScript/HTML/CSS.
6. **Resultado registrado:** o [benchmark](../dashboard/data/benchmark_ia_resultados.json) contém 17/17 casos marcados como aprovados e tempo médio salvo de 3,01 segundos. Há ao menos uma aprovação indevida: a resposta do caso Q5 afirma que faltosos receberam zero, enquanto o [README do dashboard](../dashboard/README.md) e os dados estabelecem escore vazio para faltosos. Assim, “17/17 aprovados pelo critério automatizado” pode ser dito; “100% de exatidão factual” não pode.

**Arquitetura para animação:** pergunta → verificação de escopo → seleção de fatos em JSON e cálculos → montagem do contexto → Ollama/Llama 3.2 se ativo, ou resposta analítica local → interface do chat. Fontes: [motor](../Scripts/ia_engine.py), [servidor](../dashboard/server_com_chat.py), [widget](../dashboard/src/presentation/chat.js).

## Perguntas e respostas verificadas para o chat

Use as perguntas exatas abaixo no widget. As respostas são transcrições do benchmark salvo, não promessas de que uma nova execução neural produzirá texto idêntico. Grave a resposta efetiva e valide números antes da montagem.

| Pergunta para digitar | Resposta registrada | O que demonstra |
| --- | --- | --- |
| Quantos alunos únicos foram identificados no censo geral de avaliações do projeto? | “**3016** alunos únicos foram identificados no censo geral de avaliações do projeto.” | Consulta direta ao censo auditado. |
| Qual é o total de pares completos pré e pós-teste no instrumento de Vocabulário? | “O total de pares completos pré e pós-teste no instrumento de Vocabulário é de 3456 pares.” | Recuperação de indicador longitudinal. |
| Quantos pares legítimos foram consolidados no TDE II após o tratamento das cópias? | “Após o tratamento das cópias, foram consolidados 3.232 pares legítimos no TDE II.” | Explicita o efeito do saneamento amostral. |
| Me fale a média de idade de estudante do EJA | “A média de idade do estudante do EJA é de 29,96 anos.” | Consulta demográfica por modalidade. |

## Tecnologias, técnicas, modelos e armazenamento comprovados

| Trabalho | Componentes verificados |
| --- | --- |
| Dados e painel | Python, pandas nos notebooks, CSV, JSON, HTML, CSS, JavaScript puro, gráficos SVG, arquitetura em camadas; normalização, deduplicação, pareamento pré/pós, escala dicotômica, coorte longitudinal e Cohen d_z. |
| ML | Python, pandas, NumPy, scikit-learn; GroupKFold, codificação one-hot, regressão, classificação, baselines, Ridge, Regressão Logística, Árvore de Decisão, Random Forest e Gradient Boosting. |
| Assistente | Python standard library, HTTP local, base temática e catálogo estatístico em JSON, recuperação estruturada por regras, contexto no prompt, Ollama e Llama 3.2 3B quando ativos, fallback analítico. |

**Armazenamento:** arquivos CSV/JSON locais. Não foi identificado banco relacional ou vetorial em operação.

## Telas e interações a gravar

1. **Visão geral:** abertura do `dist/`, filtros vazios, quatro KPIs. Conferir se o servidor de chat está ativo.
2. **Filtros:** selecionar escola e turma com amostra; registrar atualização simultânea de KPIs, comparação e efeito. Voltar a “Todas as escolas” para os valores globais.
3. **Instrumento e escala:** alternar Vocabulário ↔ TDE II; mostrar barras pré/pós e distribuição de melhora/estabilidade/queda; trocar pontos brutos ↔ percentual.
4. **Evolução:** mostrar o gráfico longitudinal apenas se a seleção possuir coorte completa nas três fases; caso contrário, escolher filtro mais amplo e não simular uma linha.
5. **Perfil:** alternar Zona, Cor/Raça, Sexo e Modalidade. Usar “Modalidade” para explicar EJA versus ensino regular; evitar linguagem causal ou renda familiar, que não foi coletada.
6. **ML:** inserir cartões/gráficos gerados a partir do JSON de métricas; identificar sempre instrumento, tarefa e métrica. Não usar captura de terminal como principal demonstração.
7. **Chat:** abrir “Perguntar à IA” e gravar as quatro consultas acima, incluindo entrada, envio, espera e resposta completa. Registrar o status real do Ollama antes da gravação.

## Instruções para a IA produtora do vídeo

- Usar o texto da coluna “Narração” do [roteiro](ROTEIRO_VIDEO.md) como locução principal, com pausas nas transições e pronúncia “T-D-E dois”, “R ao quadrado”, “d zê de Cohen” e “E-J-A”.
- Produzir três capítulos visuais separados por cartões de título; conservar os tempos de cada linha, com duração total alvo de 7min30s.
- Usar captura real do dashboard e do chat. Se o Ollama estiver indisponível, identificar visualmente o “modo analítico local”; não inserir uma fala que atribua essa resposta ao LLM.
- Redigir etiquetas e números a partir das tabelas desta pasta. Identificar denominadores e unidades: estudante único, aplicação, par e turma são contagens distintas.
- Cobrir identificadores individuais em CSVs, mesmo pseudonimizados, quando não forem necessários. Usar recortes de cabeçalho e estatísticas agregadas.
- Não criar tela de Telegram, gráfico de clusters, caso individual previsto, modelo serializado, banco vetorial ou indicador de significância estatística.
- Após gravar, comparar os valores visíveis no dashboard e as quatro respostas reais com as métricas deste documento. Se divergirem, atualizar a edição e registrar a divergência, sem substituir o valor na imagem.

## Informações ausentes e pontos que precisam de confirmação

1. **Planilhas de origem:** os `.xlsx` não estão presentes. O manifesto permite rastrear nomes, abas e saídas, mas não uma auditoria direta das células originais.
2. **Efeito global conflitante:** o [README principal](../README.md) informa d_z 0,30 (Vocabulário) e 0,32 (TDE II), enquanto o [catálogo estatístico](../Contexts/estatisticas_consolidadas.json) e o recálculo direto dos pares dos CSVs resultam em 0,11 e −0,065. Confirmar a versão e o recorte que originaram os valores do README; a gravação deve usar os valores atuais do painel/CSVs.
3. **Significância estatística:** o README principal menciona ganho significativo, mas não foi encontrado teste inferencial e seu efeito global conflita com o catálogo. Não afirmar significância.
4. **Exemplos individuais de ML:** ausentes predições por caso e valores reais correspondentes. Necessários para demonstrar exemplos reais, erros por aluno ou acertos de classificação.
5. **Agrupamento:** não foram encontrados treino de K-Means, quantidade de grupos, critérios, rótulos, perfis nem exemplos de integrantes. Confirmar se houve trabalho externo não incluído neste repositório.
6. **LLM em execução:** a presença de código para Ollama não prova que o modelo estará ativo na gravação. Conferir `GET /api/status`; o benchmark salvo não identifica claramente quais respostas vieram do LLM e quais do fallback.
7. **Benchmark do chatbot:** corrigir ou reavaliar o caso Q5 sobre faltosos antes de reivindicar precisão factual geral. Outras respostas longas também devem ser revisadas por especialistas antes de uso acadêmico.
8. **Créditos:** nomes de autores, instituição, disciplina, orientador e logomarcas autorizadas para a peça final devem ser fornecidos ou confirmados.

