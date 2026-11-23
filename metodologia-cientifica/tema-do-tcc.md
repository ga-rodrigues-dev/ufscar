# Tema do TCC — Testes intermitentes em integração contínua

## Status e decisão inicial

- **Data da escolha:** 2026-11-06.
- **Status:** tema escolhido pelo aluno como ponto de partida; título, pergunta e delimitação ainda podem ser ajustados após a leitura piloto.
- **Prioridade:** desenvolver um trabalho enxuto, claro e defensável, relacionado à prática profissional e viável para uma pessoa.
- **Tipo de trabalho previsto:** revisão sistemática da literatura, conforme as orientações da disciplina. Este documento registra a direção inicial; o protocolo da revisão ainda será definido.

## Título provisório

**Causas e estratégias de mitigação de testes intermitentes em integração contínua: uma revisão sistemática da literatura.**

Termos centrais: *flaky tests*, testes intermitentes, *test flakiness*, integração contínua e *continuous integration*.

## Problema e motivação

Testes intermitentes são testes que podem apresentar resultados de aprovação e falha sem mudanças no código sob teste. Essa definição aparece no resumo de [Parry et al. (2022)](https://doi.org/10.1145/3510457.3513037). O interesse inicial é compreender as causas relatadas desse comportamento no contexto de integração contínua e as estratégias utilizadas para tratá-lo.

A motivação profissional vem de tarefas do aluno relacionadas à confiabilidade e à manutenção de testes. Em particular, a descrição da EMS-12453 registra falhas aleatórias no CI associadas à geração aleatória de dados de teste e propõe sua remoção para aumentar a robustez. Fonte interna de contexto: [captura do ticket na base Experian](/Users/c24580q/source-code/experian-kb/raw/jira/2026-09-21-ems-12453.md).

A experiência profissional orienta a motivação e a compreensão do problema. As evidências e conclusões da revisão serão obtidas dos estudos científicos selecionados. O desenho inicial prevê uma revisão de estudos públicos, com leitura, extração e síntese dos resultados já publicados.

## Pergunta de pesquisa provisória

**Quais causas e estratégias de mitigação de testes intermitentes no contexto de integração contínua são relatadas em estudos empíricos?**

A extração deverá permitir responder:

1. Quais causas de intermitência são identificadas pelos estudos?
2. Quais estratégias são utilizadas ou propostas para essas causas?
3. Que evidências de avaliação, resultados e limitações acompanham cada estratégia?

## Objetivo

Identificar e organizar as causas de testes intermitentes e as estratégias de mitigação relatadas em estudos empíricos no contexto de integração contínua, distinguindo estratégias avaliadas de recomendações ainda não avaliadas.

A síntese pretendida relacionará **causa identificada, estratégia de mitigação e evidência relatada**, oferecendo uma visão prática do problema. As categorias e conclusões serão construídas a partir dos estudos efetivamente analisados.

## Delimitação inicial proposta

- **Objeto:** testes automatizados com resultados intermitentes, no contexto de integração contínua.
- **Fontes de evidência pretendidas:** estudos empíricos publicados em periódicos ou conferências com revisão por pares.
- **Conteúdo relevante:** causas identificadas e/ou estratégias de mitigação, com descrição do contexto e dos resultados disponíveis.
- **Tecnologias:** considerar diferentes linguagens e ferramentas, registrando as utilizadas em cada estudo. A experiência com Scala e serviços de dados serve de motivação, sem determinar uma restrição tecnológica inicial.
- **Relação com CI:** verificar no texto completo se o contexto de integração contínua é efetivamente tratado. A viabilidade dessa delimitação será avaliada na leitura piloto.
- **Quantidade de estudos:** determinada pelos critérios do protocolo; os três estudos da leitura piloto não representam uma meta para o conjunto final.
- **Período e idiomas:** ainda a definir e justificar no protocolo. Não foi estabelecido um corte temporal.

Possíveis exclusões, a formalizar antes da execução: estudos sem relação com testes intermitentes; publicações sem pesquisa empírica; estudos fora do contexto delimitado; e duplicatas. Revisões anteriores podem apoiar a fundamentação e a descoberta de estudos, preservando a distinção entre evidência primária e síntese secundária.

## Leitura piloto e campos de extração

O primeiro passo será obter e ler integralmente três estudos candidatos para testar a pergunta, a delimitação e a possibilidade de extrair dados comparáveis.

Campos iniciais propostos:

- Referência, DOI ou identificador verificável e origem do artigo.
- Contexto: projeto, linguagem, tipo de teste e ambiente de execução.
- Relação explícita com integração contínua e definição de intermitência adotada.
- Método empírico e objeto/amostra estudados.
- Causas identificadas, com página ou seção de suporte.
- Estratégias de mitigação e causas às quais se aplicam.
- Situação da estratégia: avaliada no estudo, observada na prática ou apenas recomendada.
- Resultados e métricas relatados, custos e limitações.

A síntese inicial será qualitativa e descritiva. Comparações e contagens deverão respeitar as diferenças de contexto, unidade de análise e método entre os estudos.

## Estudos candidatos para a leitura inicial

Os metadados e resumos abaixo foram consultados na exploração inicial. A leitura integral e a decisão de elegibilidade permanecem pendentes; esta lista não representa o conjunto de estudos incluídos na revisão.

1. **Luo, Qingzhou; Hariri, Farah; Eloussi, Lamyaa; Marinov, Darko. (2014). _An Empirical Analysis of Flaky Tests_.** FSE 2014, p. 643–653. DOI: [10.1145/2635868.2635920](https://doi.org/10.1145/2635868.2635920). [Registro na instituição dos autores](https://experts.illinois.edu/en/publications/an-empirical-analysis-of-flaky-tests/). Candidato por analisar causas e formas de correção; sua aderência ao recorte de CI precisa ser conferida no texto completo.
2. **Parry, Owain; Kapfhammer, Gregory M.; Hilton, Michael; McMinn, Phil. (2022). _Surveying the Developer Experience of Flaky Tests_.** ICSE-SEIP 2022, p. 253–262. DOI: [10.1145/3510457.3513037](https://doi.org/10.1145/3510457.3513037). [Registro e versão dos autores](https://eprints.whiterose.ac.uk/id/eprint/230090/). Candidato por investigar experiências, causas e ações relatadas por desenvolvedores, incluindo a relação com CI.

O terceiro estudo da leitura piloto ainda será identificado.

## Próximos passos

1. Obter os textos completos dos candidatos e identificar um terceiro estudo para a leitura piloto.
2. Testar os campos de extração e verificar se a delimitação a CI permite uma síntese útil e viável.
3. Ajustar a pergunta e registrar o protocolo: fontes de identificação dos estudos, consultas e datas, critérios de seleção, tratamento de duplicatas, avaliação de qualidade, extração e síntese.
4. Executar a identificação e a seleção dos estudos conforme o protocolo, preservando os registros e as justificativas das decisões.
5. Consolidar os resultados, discutir as limitações e organizar a escrita conforme o template da disciplina.

A obtenção dos PDFs poderá seguir os métodos escolhidos pelo aluno. A origem dos registros e os procedimentos de identificação e seleção continuarão documentados para permitir a reprodução da revisão.

## Estado do trabalho e orientações

**Atualização de 22/11/2026:** foi produzido, com apoio de IA, um rascunho completo do protocolo, da execução e do artigo. A busca foi executada no OpenAlex (156 registros) e 9 estudos foram incluídos. A busca na Scopus, a obtenção de 13 textos completos e a revisão de todas as decisões pelo aluno continuam pendentes. Ver [protocolo](revisao/protocolo.md), [decisões da leitura completa](revisao/extracao/README.md) e [rascunho do TCC](tcc/tcc.md).

**Realizado:** escolha provisória do tema, identificação da relação com o trabalho e consulta exploratória de metadados e resumos de dois candidatos.

**Pendente:** leitura integral, leitura piloto, protocolo, buscas reproduzíveis, seleção, avaliação de qualidade, extração, síntese e redação do artigo. Não há resultados da revisão neste momento.

As decisões e interpretações serão validadas pelo aluno.

Consultar o [inventário do Moodle](materiais-do-moodle.md), a [visão geral da disciplina](00-disciplina.md) e a [Parte 1 — Alinhamentos Iniciais](materiais/Parte1-AlinhamentosIniciais2026.pdf), especialmente a página 11 sobre o escopo do estudo secundário. Requisitos de entrega e formatação devem ser conferidos nas orientações vigentes do curso.

**Prazo (informado pelo aluno em 22/11/2026):** extensão concedida para entregar a versão para a banca até o fim de 23/11/2026.

**Atualização de 22/11/2026 (protocolo v0.3):** a revisão passou a usar apenas a Scopus, consultada pela API com a chave do aluno. Foram 89 registros, 28 selecionados para leitura completa e 10 estudos incluídos; o novo incluído é Kumar (2026). A busca no OpenAlex ficou registrada como exploratória no [protocolo](revisao/protocolo.md).

**Decisões de 22/11/2026 (protocolo v0.3):** o aluno adotou a regra estrita de contexto de CI, o que confirma a exclusão de Habchi et al. (2022) e Kim et al. (2026). Kumar (2026) foi mantido: o protocolo não tem critério de qualidade, e as fragilidades do estudo são declaradas no artigo. Ficam 10 estudos incluídos.

**Atualização de 22/11/2026 (noite):** com os PDFs obtidos pelo aluno, Leinen, Perathoner e Pretschner (2024) e Lampel et al. (2021) foram lidos e incluídos por IN1, aplicando a regra estrita de contexto de CI. Ahmad et al. (2021) foi conferido na versão publicada da STVR. A revisão passa a ter 12 estudos incluídos e 14 textos não recuperados.
