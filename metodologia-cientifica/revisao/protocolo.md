# Protocolo da revisão sistemática — versão 0.3 (rascunho)

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

- **Fonte:** Scopus, via Scopus Search API (`https://api.elsevier.com/content/search/scopus`, visão STANDARD), com chave de API do aluno. Executada em **22/11/2026**: 89 registros. Registros completos em [dados/busca-scopus-2026-11-22.json](dados/busca-scopus-2026-11-22.json). A chave não é armazenada no repositório.
- A visão STANDARD não retorna resumos. Os resumos usados na triagem foram obtidos no OpenAlex pelo DOI ou pelo título de cada registro.
- **Histórico (v0.1–v0.2):** antes do acesso à Scopus, uma busca equivalente foi executada no OpenAlex (156 registros; [dados/busca-openalex-2026-11-22.json](dados/busca-openalex-2026-11-22.json), triagem em [dados/triagem-titulo-resumo.csv](dados/triagem-titulo-resumo.csv)). Na v0.3, por decisão do aluno, a revisão passou a usar apenas a Scopus, a base indicada pela disciplina. Dos 89 registros da Scopus, 75 já haviam sido triados no OpenAlex com os mesmos critérios, e essas decisões foram reaproveitadas; os 14 restantes foram triados na v0.3. Registros que só aparecem no OpenAlex não fazem parte da revisão.

**String executada na Scopus:**

```
TITLE-ABS-KEY ( ( "flaky test*" OR "test flakiness" OR "flaky build*" OR "intermittent test*" OR "non-deterministic test*" OR "nondeterministic test*" ) AND ( "continuous integration" OR "CI" ) )
```

Sem filtros de ano, área ou idioma na busca (seguindo a orientação de não limitar por área ou ano — [Perguntas & Respostas, p. 1](../materiais/PerguntasRespostasDicas-2026.pdf)). O tipo de publicação é tratado nos critérios. Não há critério de idioma: o critério EX6 (idioma diferente de inglês ou português) foi removido na v0.3, seguindo a orientação de não excluir estudos apenas pelo idioma (Parte 3, p. 20). Ele não havia excluído nenhum registro da Scopus.

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
| DUP | Duplicata ou versão preliminar de estudo já presente (mantida a versão mais completa). |

"Contexto de CI" (regra estrita, confirmada pelo aluno na v0.3) significa que os dados foram coletados em CI, a estratégia foi aplicada ou avaliada em um *pipeline* de CI (*builds*, serviços de CI, testes pré/pós-*merge*, execuções disparadas por *build*), ou o estudo tem questão de pesquisa específica sobre CI. Estudos que citam a CI apenas como motivação ou implicação não atendem. Por isso, Silva et al. (2024) é incluído (RQ3 sobre custo de CI) e Kim et al. (2026) é excluído, embora os dois usem *clusters* próprios. O acesso aberto **não** é critério; estudos cujo texto completo não pôde ser obtido são registrados como "não recuperados" e permanecem pendentes, não excluídos.

## 5. Avaliação de qualidade

Não realizada. A disciplina dispensa essa fase no TCC (Parte 3, p. 23). Uma pontuação QA1–QA5 chegou a ser atribuída na versão 0.1, mas foi descartada na versão 0.2 (22/11/2026) por decisão do aluno: os níveis de pontuação não tinham regra explícita e a nota não tinha uso definido na síntese. As seções de QA nas fichas de extração são registro histórico e não são usadas.

## 6. Formulário de extração

Referência e versão lida; decisão e critérios; contexto (organização/OSS, linguagens, tipos de teste, sistema de CI, escala); definição de teste intermitente; método e amostra; causas (com página e trecho); estratégias de mitigação (descrição, causas tratadas, situação — avaliada / observada na prática / apenas recomendada —, resultados, custos, página e trecho); limitações; observações. Fichas em [extracao/](extracao/).

## 7. Síntese

Síntese qualitativa por agrupamento temático (*thematic synthesis*): causas agrupadas em categorias recorrentes; estratégias agrupadas por tipo (prevenção/correção, contenção, infraestrutura, processo/organização); matriz causa × estratégia × evidência. Contagens referem-se a estudos, não a testes, salvo indicação.

## 8. Execução registrada

| Etapa | Registros |
|---|---|
| Identificados (Scopus, 22/11/2026) | 89 |
| Duplicatas removidas | 3 |
| Triados por título e resumo | 86 |
| Excluídos na triagem | 58 (EX1: 2; EX2: 24; EX3: 24; EX4: 8) |
| Selecionados para texto completo | 28 |
| Textos completos não recuperados | 14 (ver [extracao/README.md](extracao/README.md)) |
| Avaliados na leitura completa | 14 (excluídos: 2) |
| Incluídos | 12 |

Decisões registro a registro: [dados/triagem-scopus.csv](dados/triagem-scopus.csv). A coluna `ficha` aponta para a ficha de extração em [extracao/](extracao/).

## 9. Recuperação dos textos completos

Recuperação por vias de acesso aberto (editora, arXiv, repositórios institucionais, páginas dos autores) e, para três estudos, por download feito pelo aluno, em 22/11/2026. Quando lida uma versão de autor/preprint de estudo publicado, isso é indicado na ficha; as páginas citadas referem-se à versão lida. PDFs ficam em `textos-completos/` (ignorado pelo Git).

## 10. Desvios e pendências

1. **Fonte única (Scopus).** Segue a orientação da disciplina; IEEE Xplore e ACM DL ficam como possível extensão.
2. **StArt não utilizada.** Não é um desvio: na aula de 02/10/2026 ([00:02:30]) foi dito que seu uso não é obrigatório, apenas recomendado. A triagem e a seleção foram registradas em CSV ([dados/triagem-scopus.csv](dados/triagem-scopus.csv)), com decisão e justificativa por registro.
3. **Triagem e extração com apoio de IA**, sem segundo revisor humano até o momento — o aluno deve revisar todas as decisões.
4. **Snowballing** não realizado, seguindo a orientação da disciplina de não usá-lo no TCC (Parte 3, p. 22). Não é um desvio; fica registrado como possível extensão.
5. **Textos completos não recuperados** (14) devem ser obtidos via CAFe/UFSCar e avaliados. Os PDFs de Leinen et al. (2024), Lampel et al. (2021) e da versão publicada de Ahmad et al. (2021) foram obtidos pelo aluno em 22/11/2026.
