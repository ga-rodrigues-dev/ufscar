# Protocolo da revisão sistemática — versão 0.1 (rascunho)

> **Status:** rascunho preparado com apoio de IA em 22/11/2026 para avaliação do aluno. Nenhuma decisão aqui é definitiva até ser revisada e aceita pelo aluno. Os desvios em relação às orientações da disciplina estão listados na seção 10.

## 1. Questão de pesquisa

**QP:** Quais causas e estratégias de mitigação de testes intermitentes (*flaky tests*) no contexto de integração contínua são relatadas em estudos empíricos?

Subquestões de extração (de [tema-do-tcc.md](../tema-do-tcc.md)):

- **QP1:** Quais causas de intermitência são identificadas pelos estudos?
- **QP2:** Quais estratégias são utilizadas ou propostas para essas causas?
- **QP3:** Que evidências de avaliação, resultados e limitações acompanham cada estratégia?

## 2. PICOC

| Elemento | Definição |
|---|---|
| População | Testes automatizados de software executados em integração contínua (CI) |
| Intervenção | Identificação de causas e estratégias de mitigação (correção, prevenção, contenção/gestão) |
| Comparação | Não se aplica |
| Resultado (*Outcome*) | Causas relatadas; estratégias e evidências de sua efetividade |
| Contexto | Projetos de código aberto e industriais; estudos empíricos revisados por pares |

## 3. Fontes e estratégia de busca

- **Fonte executada:** OpenAlex (API pública, `https://api.openalex.org/works`), filtro `title_and_abstract.search` (título e resumo). Executada em **22/11/2026**. Registros completos em [dados/busca-openalex-2026-11-22.json](dados/busca-openalex-2026-11-22.json).
- **Fonte recomendada pela disciplina e ainda não executada:** Scopus. A API da Scopus retornou HTTP 401 sem credencial institucional; a busca deve ser reexecutada pelo aluno via CAFe com a string equivalente abaixo, e os resultados mesclados (com remoção de duplicatas) antes da versão final.

**String executada no OpenAlex:**

```
("flaky test" OR "flaky tests" OR "test flakiness" OR "flaky build" OR "flaky builds" OR "intermittent test" OR "intermittent tests" OR "non-deterministic test" OR "non-deterministic tests" OR "nondeterministic test" OR "nondeterministic tests") AND ("continuous integration" OR "CI")
```

**String equivalente para a Scopus (a executar):**

```
TITLE-ABS-KEY ( ( "flaky test*" OR "test flakiness" OR "flaky build*" OR "intermittent test*" OR "non-deterministic test*" OR "nondeterministic test*" ) AND ( "continuous integration" OR "CI" ) )
```

Sem filtros de ano, área ou idioma na busca (seguindo a orientação de não limitar por área ou ano — [Perguntas & Respostas, p. 1](../materiais/PerguntasRespostasDicas-2026.pdf)). Idioma e tipo de publicação são tratados nos critérios.

## 4. Critérios de seleção

Um estudo é **incluído** se atende a IN1 **ou** IN2 e a nenhum critério de exclusão.

| Código | Critério |
|---|---|
| IN1 | Estudo primário empírico que identifica ou caracteriza causas (fontes, fatores ou categorias de causa raiz) de testes intermitentes em contexto de CI. |
| IN2 | Estudo primário empírico que aplica ou avalia estratégia de mitigação (correção, prevenção ou contenção/gestão) de testes intermitentes em contexto de CI. |
| EX1 | Fora do tema (não trata de testes intermitentes de software). |
| EX2 | Testes intermitentes apenas periféricos a outro objeto (seleção/priorização de testes, CI ou automação em geral). |
| EX3 | Não relata causas nem estratégias de mitigação (foco exclusivo em detecção/predição/classificação, prevalência, impacto ou custo). |
| EX4 | Não é estudo primário empírico (revisão, mapeamento, proposta conceitual ou sem avaliação empírica, opinião). |
| EX5 | Não publicado em periódico ou conferência com revisão por pares (preprint, tese, dissertação, conjunto de dados, software, relatório técnico). |
| EX6 | Idioma diferente de inglês ou português. |
| DUP | Duplicata ou versão preliminar de estudo já presente (mantida a versão mais completa). |

"Contexto de CI" significa que o estudo situa explicitamente os testes, os dados ou a estratégia em integração contínua (pipelines, *builds*, serviços de CI, testes pré/pós-*merge*). O acesso aberto **não** é critério; estudos cujo texto completo não pôde ser obtido são registrados como "não recuperados" e permanecem pendentes, não excluídos.

## 5. Avaliação de qualidade

Cada estudo lido integralmente recebe 1 (sim), 0,5 (parcial) ou 0 (não) em:

- **QA1** objetivo/questões de pesquisa claros;
- **QA2** método empírico descrito de forma replicável;
- **QA3** contexto (projetos/organização, linguagens, tipos de teste, CI) descrito;
- **QA4** conclusões sustentadas pelos dados apresentados;
- **QA5** ameaças à validade/limitações discutidas.

A pontuação (0–5) é usada para ponderar a síntese, e não como critério de exclusão.

## 6. Formulário de extração

Referência e versão lida; decisão e critérios; QA1–QA5; contexto (organização/OSS, linguagens, tipos de teste, sistema de CI, escala); definição de teste intermitente; método e amostra; causas (com página e trecho); estratégias de mitigação (descrição, causas tratadas, situação — avaliada / observada na prática / apenas recomendada —, resultados, custos, página e trecho); limitações; observações. Fichas em [extracao/](extracao/).

## 7. Síntese

Síntese qualitativa por agrupamento temático (*thematic synthesis*): causas agrupadas em categorias recorrentes; estratégias agrupadas por tipo (prevenção/correção, contenção, infraestrutura, processo/organização); matriz causa × estratégia × evidência. Contagens referem-se a estudos, não a testes, salvo indicação.

## 8. Execução registrada

| Etapa | Registros |
|---|---|
| Identificados (OpenAlex, 22/11/2026) | 156 |
| Duplicatas removidas | 6 |
| Triados por título e resumo | 150 |
| Excluídos na triagem | 124 (EX1: 7; EX2: 37; EX3: 25; EX4: 20; EX5: 34; EX6: 1) |
| Selecionados para texto completo | 26 |
| Textos completos não recuperados | 13 (ver [extracao/README.md](extracao/README.md)) |
| Avaliados na leitura completa | 13 (excluídos: 4) |
| Incluídos | 9 |

Decisões registro a registro: [dados/triagem-titulo-resumo.csv](dados/triagem-titulo-resumo.csv).

## 9. Recuperação dos textos completos

Recuperação apenas por vias de acesso aberto (arXiv, repositórios institucionais, páginas dos autores, SBC OpenLib), entre 22/11/2026. Quando lida uma versão de autor/preprint de estudo publicado, isso é indicado na ficha; as páginas citadas referem-se à versão lida. PDFs ficam em `textos-completos/` (ignorado pelo Git).

## 10. Desvios e pendências

1. **Scopus não executada** (sem credencial) — pendência obrigatória antes da versão final.
2. **StArt não utilizada** nesta versão; a triagem foi registrada em CSV. As instruções escritas da disciplina descrevem o uso da StArt; em aula de 02/10 foi dito que seu uso não é obrigatório. Confirmar com a docente.
3. **Triagem e extração com apoio de IA**, sem segundo revisor humano até o momento — o aluno deve revisar todas as decisões.
4. **Snowballing** não realizado.
5. **Textos completos não recuperados** por acesso aberto devem ser obtidos via CAFe/UFSCar e avaliados.
