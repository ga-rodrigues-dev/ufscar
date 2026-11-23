<!-- Fonte do TCC. Gere o DOCX com: python3 build_docx.py -->
<!-- RASCUNHO preparado com apoio de IA em 22/11/2026. Todo conteúdo deve ser revisado pelo aluno. -->
# Causas e estratégias de mitigação de testes intermitentes em integração contínua: uma revisão sistemática da literatura
@autor Gabriel Rodrigues da Silva
@email gabriel.rodrigues47@estudante.ufscar.br

**Resumo.** **Contexto:** testes intermitentes (*flaky tests*) passam e falham sem alteração no código e comprometem a confiabilidade dos *pipelines* de integração contínua (CI). **Objetivo:** identificar as causas e as estratégias de mitigação de testes intermitentes em CI relatadas em estudos empíricos, distinguindo estratégias avaliadas de recomendações. **Metodologia:** foi conduzida uma revisão sistemática com busca no OpenAlex, critérios de inclusão e exclusão definidos em protocolo e avaliação de qualidade. **Resultados:** 156 registros foram identificados; após a remoção de 6 duplicatas e a triagem, 26 estudos foram selecionados para leitura completa, 13 foram recuperados e 9 foram incluídos. As causas mais recorrentes estão no ambiente de execução da CI (recursos computacionais, desempenho do *host*, sistema operacional, eventos transitórios e dependências externas), além de causas no código de teste, como *setup/teardown*, espera assíncrona e concorrência. A reexecução é a estratégia mais adotada, mas tem custo elevado; apenas 4 dos 9 estudos avaliam estratégias. **Conclusões:** a evidência aponta a infraestrutura de CI como fonte central de intermitência e indica a necessidade de mais avaliações de estratégias além da reexecução.

## 1. Introdução

Testes automatizados de regressão pressupõem que o resultado de um teste dependa apenas do código sob teste. Testes intermitentes violam esse pressuposto: são testes que podem passar e falhar sem mudanças no código (LUO et al., 2014; PARRY et al., 2021). Na integração contínua (CI, do inglês *Continuous Integration*), em que cada mudança é verificada por um *build* automatizado com testes (FOWLER, 2024), uma falha intermitente interrompe o *pipeline*, consome tempo de investigação e reduz a confiança nos resultados.

Luo et al. (2014) relatam que, no sistema de testes da Google, 4,56% das falhas diárias eram causadas por testes intermitentes, e que as respostas mais comuns, como reexecutar ou ignorar o teste, eram paliativos que não tratavam as causas.

A motivação deste trabalho vem da prática profissional do autor com a manutenção de testes automatizados em CI, em que falhas aleatórias associadas a dados de teste gerados aleatoriamente comprometiam a confiabilidade do *pipeline*. Sendo assim, este estudo tem como objetivo aprofundar os conhecimentos sobre testes intermitentes no contexto de CI, respondendo à questão: quais causas e estratégias de mitigação de testes intermitentes no contexto de integração contínua são relatadas em estudos empíricos?

Este artigo está organizado da seguinte forma: na Seção 2 são apresentados os conceitos de integração contínua e de testes intermitentes; na Seção 3 é descrito o método de pesquisa e sua execução; na Seção 4 são apresentados e discutidos os resultados; por fim, na Seção 5, são apresentadas as conclusões.

## 2. Fundamentação teórica

### 2.1. Integração contínua

Integração contínua é a prática de desenvolvimento em que cada membro da equipe integra suas alterações a uma base de código comum, ao menos diariamente, e cada integração é verificada por um *build* automatizado, incluindo testes, para detectar erros de integração o mais cedo possível (FOWLER, 2024). Em projetos de código aberto, Hilton et al. (2016) analisaram 34.544 projetos do GitHub e 1.529.291 *builds*, e encontraram evidências de que a CI é amplamente adotada pelos projetos mais populares e ajuda a lançar versões com mais frequência.

### 2.2. Testes intermitentes

Um teste é considerado intermitente (*flaky*) quando apresenta resultados de aprovação e falha sem alterações no código sob teste (PARRY et al., 2021). Luo et al. (2014) realizaram o primeiro estudo extenso sobre o tema, analisando 201 *commits* que provavelmente corrigiam testes intermitentes em 51 projetos de código aberto. As três categorias de causa mais frequentes foram espera assíncrona (*async wait*), concorrência e dependência da ordem de execução dos testes; os autores também observaram que 78% dos testes intermitentes já eram intermitentes quando foram escritos (LUO et al., 2014). Na revisão de Parry et al. (2021), que reúne 76 artigos, a literatura é organizada em quatro frentes: causas, custos e consequências, detecção, e mitigação e reparo.

Neste trabalho, **causa** designa a fonte de não determinismo que leva o teste a falhar de forma intermitente, e **estratégia de mitigação** designa qualquer ação para corrigir, prevenir ou conter o efeito dos testes intermitentes. Técnicas que apenas detectam ou classificam testes intermitentes não foram consideradas estratégias de mitigação, pois a detecção é, em geral, uma etapa anterior à correção ou à contenção.

## 3. Método de pesquisa

O método utilizado foi a revisão sistemática da literatura, conduzida segundo as diretrizes de Kitchenham e Charters (2007), com relato do processo de seleção inspirado no PRISMA 2020 (PAGE et al., 2021). O planejamento foi registrado em protocolo.

A questão de pesquisa foi: **"Quais causas e estratégias de mitigação de testes intermitentes no contexto de integração contínua são relatadas em estudos empíricos?"**, desdobrada em: (QP1) quais causas são identificadas; (QP2) quais estratégias são utilizadas ou propostas para essas causas; e (QP3) que evidências de avaliação, resultados e limitações acompanham cada estratégia.

A busca foi executada em 22/11/2026 no OpenAlex, índice aberto de publicações científicas (PRIEM; PIWOWAR; ORR, 2022), com o filtro de título e resumo e a seguinte *string*: ("flaky test" OR "flaky tests" OR "test flakiness" OR "flaky build" OR "flaky builds" OR "intermittent test" OR "intermittent tests" OR "non-deterministic test" OR "non-deterministic tests" OR "nondeterministic test" OR "nondeterministic tests") AND ("continuous integration" OR "CI"). Não foram aplicados filtros de ano, área ou idioma. A busca equivalente na Scopus, base recomendada pela disciplina, não pôde ser executada nesta versão por falta de acesso institucional à interface programática.

### 3.1. Execução – identificação e seleção dos estudos

Os critérios de seleção são apresentados na Tabela 1. Um estudo foi incluído quando atendeu a IN1 ou IN2 e a nenhum critério de exclusão. Considerou-se "contexto de CI" quando o estudo situa explicitamente os testes, os dados ou a estratégia em integração contínua. O acesso aberto não foi critério de seleção.

Tabela 1. Critérios de inclusão (IN) e de exclusão (EX)
| Código | Critério |
|---|---|
| IN1 | Estudo primário empírico que identifica ou caracteriza causas de testes intermitentes em contexto de CI |
| IN2 | Estudo primário empírico que aplica ou avalia estratégia de mitigação (correção, prevenção ou contenção) em contexto de CI |
| EX1 | Fora do tema (não trata de testes intermitentes de software) |
| EX2 | Testes intermitentes apenas periféricos a outro objeto (por exemplo, seleção ou priorização de testes) |
| EX3 | Não relata causas nem mitigação (foco exclusivo em detecção, predição, prevalência, impacto ou custo) |
| EX4 | Não é estudo primário empírico (revisão, proposta conceitual ou relato sem dados) |
| EX5 | Não publicado em periódico ou conferência com revisão por pares |
| EX6 | Idioma diferente de inglês ou português |

A busca retornou 156 registros. Foram removidos 6 registros duplicados ou versões preliminares de outros registros, e os 150 restantes foram triados por título e resumo. Nessa etapa, 124 foram excluídos: 7 por EX1, 37 por EX2, 25 por EX3, 20 por EX4, 34 por EX5 e 1 por EX6. Dos 26 estudos selecionados para leitura completa, 13 tiveram o texto obtido por vias de acesso aberto (versões dos autores, repositórios institucionais e arXiv) e 13 não puderam ser recuperados nesta versão. Na leitura completa, 4 estudos foram excluídos: dois por não situarem os dados em CI (a CI aparecia apenas como motivação) e dois por EX4, por não apresentarem dados empíricos. Assim, 9 estudos foram incluídos, como apresentado na Figura 1.

![Figura 1. Fluxograma de identificação e seleção dos estudos (adaptado de PAGE et al., 2021)](figuras/prisma.png){11}

### 3.2. Execução – extração dos dados

Para cada estudo lido integralmente, um formulário registrou: referência e versão lida; decisão e critérios; contexto (organização ou projetos, linguagens, tipos de teste e sistema de CI); definição de teste intermitente adotada; método e amostra; causas identificadas; estratégias de mitigação, com as causas que tratam, a situação da evidência (avaliada no estudo, observada na prática ou apenas recomendada), os resultados e os custos; e as limitações relatadas. Cada estudo também recebeu uma nota de qualidade de 0 a 5, somando cinco questões (objetivo claro, método replicável, contexto descrito, conclusões sustentadas pelos dados e ameaças à validade discutidas), com 1, 0,5 ou 0 ponto por questão. A nota foi usada para ponderar a síntese, e não para excluir estudos. A síntese foi qualitativa, com agrupamento temático das causas e das estratégias.

## 4. Resultados e discussões

### 4.1. Visão geral dos estudos incluídos

Os nove estudos incluídos foram publicados entre 2020 e 2026 e são apresentados na Tabela 2. Quatro analisam contextos industriais (Facebook, Google, SAP e quatro empresas escandinavas), quatro analisam projetos de código aberto e um combina um *survey* com desenvolvedores e a análise do StackOverflow. Os métodos incluem mineração de repositórios, experimentos controlados, estudos de caso industriais e *surveys*. A nota média de qualidade foi 4,1 de 5; as menores notas couberam a um relato industrial sem questões de pesquisa nem discussão de ameaças (E3) e a um estudo baseado em percepções com inconsistências na contagem de participantes (E2).

Tabela 2. Estudos incluídos na revisão
| ID | Estudo | Contexto e método | Qualidade |
|---|---|---|---|
| E1 | Durieux et al. (2020) | *Builds* reiniciados no Travis CI; mineração de 3,3 milhões de *builds* | 4,5 |
| E2 | Ahmad, Leifler e Sandahl (2021) | Quatro empresas; *survey* e *workshops* com praticantes | 3,0 |
| E3 | Ahlgren et al. (2021) | Facebook; implantação de testes metamórficos na CI | 2,5 |
| E4 | Parry et al. (2022) | *Survey* com 170 desenvolvedores e 38 tópicos do StackOverflow | 4,5 |
| E5 | Henderson et al. (2023) | Google; localização de *commits* culpados com 13.600 quebras de teste | 4,0 |
| E6 | Berndt, Bach e Baltes (2024) | SAP HANA; testes de sistema no CI pré-*submit* | 4,5 |
| E7 | Silva et al. (2024) | 52 projetos Java, Python e JavaScript; experimento com 27 configurações de recursos | 5,0 |
| E8 | Hashemi et al. (2026) | 116 projetos JavaScript no GitHub Actions; matriz de ambientes | 4,0 |
| E9 | Xiao et al. (2026) | Ecossistema OpenStack (Zuul CI); 649 projetos | 4,5 |

Os estudos mais recentes (E6 a E9) deslocam o foco do código do teste para o ambiente em que ele é executado, o que se reflete nas causas discutidas a seguir.

### 4.2. Causas de testes intermitentes em CI (QP1)

As causas relatadas foram agrupadas em quatro categorias, apresentadas na Tabela 3. A categoria mais recorrente, presente em oito dos nove estudos, é o **ambiente e a infraestrutura de execução**.

Tabela 3. Categorias de causa e estudos que as relatam
| Categoria | Causas relatadas | Estudos |
|---|---|---|
| Ambiente e infraestrutura de CI | Escassez de CPU e memória; *host* lento e testes longos; sistema operacional, versão do *runtime* e navegador; *timeouts* e limites do serviço de CI; eventos transitórios e configuração de máquinas virtuais; diferenças entre ambiente local e CI; versão instável do servidor de CI | E1, E2, E3, E4, E5, E6, E7, E8, E9 |
| Código e projeto do teste | *Setup/teardown* inadequado; espera assíncrona; concorrência; dependência entre testes; *sleep* e esperas fixas; aleatoriedade sem semente fixa | E2, E3, E4, E6, E7 |
| Dependências e estado externos | Rede; serviços e *backends* fora do ar; atualização de versões de dependências; estado externo mutável | E1, E3, E4, E9 |
| Fatores organizacionais | Requisitos pouco claros; falta de experiência; testes antigos não atualizados; desconhecimento do ambiente | E2 |

No estudo de Silva et al. (2024), 46,5% dos testes intermitentes detectados (283 de 608) são sensíveis à disponibilidade de recursos computacionais, com a CPU como fator mais influente em projetos Java e JavaScript e a memória em projetos Python. Em um contexto industrial, Berndt, Bach e Baltes (2024) encontram correlação positiva entre o tempo médio de execução dos testes e a taxa de intermitência (r = 0,74 nos dados de produção e r = 0,79 no experimento) e entre o desempenho mais baixo do *host* e a intermitência; contrariando hipóteses iniciais, a carga da infraestrutura não apresentou correlação, e testes distribuídos foram menos intermitentes que os executados em uma única máquina. Hashemi et al. (2026) mostram que a própria matriz de ambientes da CI é um gatilho: em 65 dos 116 projetos JavaScript analisados no GitHub Actions houve falhas dependentes de ambiente, sobretudo de sistema operacional, com o Windows concentrando a maior parte das falhas desse tipo.

No ecossistema OpenStack, Xiao et al. (2026) codificaram 110 testes com intermitência inconsistente e atribuíram 89% dos casos a eventos externos ou transitórios, como servidores de *backend* fora do ar e recursos temporariamente indisponíveis, seguidos de problemas de dependências e de configuração do ambiente (21% cada). No nível do *build*, Durieux et al. (2020) identificam as falhas de teste como a causa mais frequente de reinício, seguidas de limitações do Travis CI (como *timeout*) e de falhas de rede e de instalação de dependências.

As causas no código do teste aparecem principalmente nos estudos com desenvolvedores. No *survey* de Parry et al. (2022), *setup/teardown* inadequado é a causa relatada com maior frequência, seguida de rede e de causas desconhecidas; espera assíncrona e concorrência ocupam apenas a quarta e a quinta posições. Essa ordem diverge da observada por Luo et al. (2014) em *commits* de correção, possivelmente porque *surveys* medem percepção, enquanto *commits* registram apenas causas corrigidas. O mesmo estudo aponta, de forma explícita, as diferenças entre o ambiente local e a CI como causa reconhecida pelos desenvolvedores (PARRY et al., 2022). Ahmad, Leifler e Sandahl (2021) acrescentam fatores organizacionais, como requisitos pouco claros e falta de experiência da equipe, que nenhum outro estudo incluído investiga. Por fim, a categoria "causa desconhecida", terceira mais frequente no *survey* de Parry et al. (2022), indica que uma parcela relevante dos testes intermitentes nunca chega a ser diagnosticada.

### 4.3. Estratégias de mitigação e evidências (QP2 e QP3)

As estratégias identificadas são apresentadas na Tabela 4, com a situação da evidência em cada estudo. Apenas quatro estudos (E3, E5, E7 e E8) avaliam empiricamente uma estratégia; nos demais, as estratégias são práticas observadas ou recomendações dos autores.

Tabela 4. Estratégias de mitigação, causas tratadas e situação da evidência
| Estratégia | Causas tratadas | Evidência | Estudos |
|---|---|---|---|
| Reexecutar o teste, o *job* ou o *build* | Qualquer (contenção) | Observada, com custo medido | E1, E4, E6, E9 |
| Tolerar a intermitência na localização do *commit* culpado | Qualquer (contenção) | Avaliada | E5 |
| Pular ou isolar testes por ambiente (quarentena) | Sistema operacional, *runtime* e navegador | Avaliada | E8 |
| Dimensionar os recursos dos *runners* de CI | Escassez de recursos | Avaliada | E7 |
| Isolar o estado externo (*snapshot*) | Estado externo mutável | Avaliada | E3 |
| Corrigir o teste (esperar por condição, *mocks*, *setup/teardown*, semente fixa) | Código do teste | Observada | E2, E3, E4, E7 |
| Dividir testes longos e definir *timeouts* globais | Testes longos e *host* lento | Recomendada ou observada | E6 |
| Padronizar o ambiente de CI e validar dependências | Configuração e dependências | Recomendada | E8, E9 |
| Reparar cedo e rastrear centralmente | Qualquer (processo) | Recomendada | E4, E9 |

**Reexecução.** É a estratégia mais adotada e a mais bem documentada quanto ao custo. No *survey* de Parry et al. (2022), reexecutar o *build* que falhou é a ação mais comum, enquanto a quarentena é a menos usada. Durieux et al. (2020) observam que 46,77% dos *builds* reiniciados após falha passam a ser aprovados, mas a taxa de sucesso é menor quando a falha é de teste, e os reinícios triplicam o tempo mediano de integração de *pull requests*, de 16 para 48 horas. No SAP HANA, 500 horas diárias de computação são dedicadas a reexecuções causadas por falhas intermitentes (BERNDT; BACH; BALTES, 2024), e no OpenStack a intermitência acumulou 1.156 dias de tempo adicional em revisões de código (XIAO et al., 2026). Desenvolvedores do OpenStack relatam, ainda, que a reexecução indiscriminada mascarou defeitos reais (XIAO et al., 2026). Henderson et al. (2023) mostram, no CI da Google, que aumentar o número de reexecuções na bisseção estabiliza a acurácia enquanto o custo cresce linearmente; o algoritmo bayesiano proposto, que modela a taxa de intermitência de cada teste, foi mais preciso que todas as variantes de bisseção com reexecuções. Nesse estudo, cerca de 40% das quebras investigadas decorriam de falhas intermitentes.

**Contenção por isolamento.** Hashemi et al. (2026) propõem uma ferramenta que pula e registra testes conforme o sistema operacional, a versão do Node.js ou o navegador, por meio de anotações. Nos sete projetos avaliados, todas as falhas ambientais conhecidas foram contidas sem falsos positivos ou negativos, permitindo que o *build* prosseguisse; o teste, porém, deixa de ser executado naquele ambiente, e o tempo de execução aumentou em alguns projetos. Ahlgren et al. (2021) avaliam o isolamento do estado externo: ao executar os testes sobre um *snapshot* pré-computado do grafo social, em vez do sistema real, a intermitência caiu de cerca de 50% dos testes no modo *online* para 0% no modo *offline*, com execução uma ordem de grandeza mais rápida, embora sem garantia de que o modo *offline* revele os mesmos defeitos. A evidência desse estudo é a mais frágil do conjunto (três dias de medição e oito testes).

**Infraestrutura.** Silva et al. (2024) avaliam o dimensionamento de recursos: a configuração com 0,5 CPU e 2 GiB de memória foi a mais custo-efetiva no conjunto estudado, mas a melhor configuração depende do projeto, e aumentar os recursos além de certo ponto não trouxe ganho significativo. Dos 14 projetos contatados com a sugestão de documentar requisitos mínimos de recursos, 6 responderam e 4 alteraram o projeto conforme as sugestões. Berndt, Bach e Baltes (2024) recomendam dividir testes longos, a um custo adicional de preparação do ambiente, e relatam o uso de um *timeout* global de duas horas; Xiao et al. (2026) relatam ajustes de concorrência e de configuração da CI e recomendam padronizar ambientes com contêineres.

**Correção e processo.** As correções no código do teste aparecem como práticas observadas: esperar por uma condição em vez de usar atrasos fixos, usar *mocks*, corrigir *setup/teardown* e isolar estado compartilhado (PARRY et al., 2022); controlar a semente pseudoaleatória e executar em sequência os testes dependentes de ordem (AHLGREN et al., 2021); manter testes pequenos e simples (AHMAD; LEIFLER; SANDAHL, 2021). Nenhum estudo incluído mede o efeito dessas correções em CI. No plano do processo, recomenda-se reparar os testes intermitentes o quanto antes (PARRY et al., 2022) e substituir o padrão de "reexecutar e esperar" por intervenção precoce e rastreamento centralizado (XIAO et al., 2026).

### 4.4. Discussão

A questão de pesquisa deste estudo é "quais causas e estratégias de mitigação de testes intermitentes no contexto de integração contínua são relatadas em estudos empíricos?". Observados os resultados, a resposta tem três partes. Primeiro, em CI, as causas mais documentadas estão no ambiente de execução (recursos, *host*, sistema operacional, rede, serviços externos e configuração), e não apenas no código do teste, como enfatizavam as taxonomias iniciais (LUO et al., 2014). Segundo, a estratégia predominante na prática é a reexecução, cujo custo é bem quantificado, mas cuja efetividade é limitada e que não trata a causa. Terceiro, as estratégias avaliadas (isolamento por ambiente, isolamento do estado externo, dimensionamento de recursos e tolerância à intermitência na localização de culpados) atuam sobre o ambiente ou sobre o efeito da falha, enquanto as correções no código, embora recomendadas, não foram avaliadas em CI pelos estudos incluídos.

Para a prática, esses resultados sugerem relacionar a estratégia à causa: falhas de ambiente favorecem padronização e dimensionamento da infraestrutura; falhas de código favorecem correção (por exemplo, fixar a semente de dados aleatórios, situação que motivou este trabalho); e a reexecução deve ser limitada e acompanhada de registro, para não ocultar defeitos. Os custos das estratégias avaliadas, como o tempo adicional da quarentena (HASHEMI et al., 2026) ou a perda de realismo do modo *offline* (AHLGREN et al., 2021), indicam que não há solução única.

Esta revisão tem limitações. A busca usou apenas o OpenAlex e exigiu o termo "CI" ou "continuous integration" no título ou no resumo, o que deixa de fora estudos clássicos que não mencionam CI no resumo. Metade dos estudos selecionados para leitura completa não pôde ser recuperada por acesso aberto, e alguns textos foram lidos em versões preliminares dos autores. A triagem e a extração foram realizadas com apoio de IA, sem um segundo revisor independente. Por fim, os estudos usam definições e unidades de análise diferentes (teste, *build*, *job*), o que impede somar ou comparar diretamente suas proporções.

## 5. Conclusões

Este estudo relata uma revisão sistemática sobre as causas e as estratégias de mitigação de testes intermitentes em integração contínua. Dos 156 registros identificados no OpenAlex, 26 foram selecionados para leitura completa e 9 estudos empíricos foram incluídos, publicados entre 2020 e 2026, em contextos industriais e de código aberto.

Foi possível identificar que, em CI, a intermitência decorre sobretudo do ambiente de execução, como a escassez de recursos, o desempenho do *host*, as diferenças de sistema operacional e os eventos transitórios de infraestrutura, além de causas conhecidas no código do teste, como *setup/teardown*, espera assíncrona e concorrência. A reexecução é a resposta mais comum e tem custo elevado e documentado. Apenas quatro estudos avaliam estratégias, todas voltadas ao ambiente ou à contenção do efeito da falha.

Como trabalhos futuros, sugere-se complementar a busca na Scopus e com *snowballing*, obter os 13 textos não recuperados e avaliar, em *pipelines* reais, a efetividade das correções no código do teste em comparação com a reexecução.

## Declaração de Uso de Inteligência Artificial

Este trabalho utilizou o assistente Claude (Anthropic), por meio da ferramenta Claude Code, nas seguintes atividades: execução da busca no OpenAlex e registro dos resultados; triagem por título e resumo; recuperação dos textos completos em acesso aberto; leitura completa, avaliação de qualidade e preenchimento dos formulários de extração; elaboração do fluxograma; e redação da versão preliminar deste artigo. As decisões de seleção, os dados extraídos e o texto final foram revisados pelo autor, que é responsável pelo conteúdo. Os registros da busca, da triagem e da extração estão disponíveis para auditoria.

## Referências

::ref AHLGREN, J.; BEREZIN, M. E.; BOJARCZUK, K.; DULSKYTE, E.; DVORTSOVA, I.; GEORGE, J.; GUCEVSKA, N.; HARMAN, M.; LOMELI, M.; MEIJER, E.; SAPORA, S.; SPAHR-SUMMERS, J. Testing web enabled simulation at scale using metamorphic testing. In: INTERNATIONAL CONFERENCE ON SOFTWARE ENGINEERING: SOFTWARE ENGINEERING IN PRACTICE (ICSE-SEIP), 43., 2021, Madrid. **Proceedings** [...]. Piscataway: IEEE, 2021. p. 140-149. DOI: 10.1109/ICSE-SEIP52600.2021.00023.
::ref AHMAD, A.; LEIFLER, O.; SANDAHL, K. Empirical analysis of practitioners' perceptions of test flakiness factors. **Software Testing, Verification and Reliability**, v. 31, n. 8, e1791, 2021. DOI: 10.1002/stvr.1791.
::ref BERNDT, A.; BACH, T.; BALTES, S. Do test and environmental complexity increase flakiness? An empirical study of SAP HANA. In: ACM/IEEE INTERNATIONAL SYMPOSIUM ON EMPIRICAL SOFTWARE ENGINEERING AND MEASUREMENT (ESEM), 18., 2024, Barcelona. **Proceedings** [...]. New York: ACM, 2024. p. 572-581. DOI: 10.1145/3674805.3695407.
::ref DURIEUX, T.; LE GOUES, C.; HILTON, M.; ABREU, R. Empirical study of restarted and flaky builds on Travis CI. In: INTERNATIONAL CONFERENCE ON MINING SOFTWARE REPOSITORIES (MSR), 17., 2020, Seoul. **Proceedings** [...]. New York: ACM, 2020. p. 254-264. DOI: 10.1145/3379597.3387460.
::ref FOWLER, M. **Continuous Integration**. 18 jan. 2024. Disponível em: https://martinfowler.com/articles/continuousIntegration.html. Acesso em: 22 nov. 2026.
::ref HASHEMI, N.; TAHIR, A.; SHI, A.; RASHEED, S.; BLAGOJEVIC, R. A systematic evaluation of environmental flakiness in JavaScript tests. In: IEEE INTERNATIONAL CONFERENCE ON SOFTWARE TESTING, VERIFICATION AND VALIDATION (ICST), 2026. **Proceedings** [...]. Piscataway: IEEE, 2026. p. 105-116. DOI: 10.1109/ICST69053.2026.00025.
::ref HENDERSON, T. A. D.; DORWARD, B.; NICKELL, E.; JOHNSTON, C.; KONDAREDDY, A. Flake aware culprit finding. In: IEEE CONFERENCE ON SOFTWARE TESTING, VERIFICATION AND VALIDATION (ICST), 2023, Dublin. **Proceedings** [...]. Piscataway: IEEE, 2023. p. 362-373. DOI: 10.1109/ICST57152.2023.00041.
::ref HILTON, M.; TUNNELL, T.; HUANG, K.; MARINOV, D.; DIG, D. Usage, costs, and benefits of continuous integration in open-source projects. In: IEEE/ACM INTERNATIONAL CONFERENCE ON AUTOMATED SOFTWARE ENGINEERING (ASE), 31., 2016, Singapore. **Proceedings** [...]. New York: ACM, 2016. p. 426-437. DOI: 10.1145/2970276.2970358.
::ref KITCHENHAM, B.; CHARTERS, S. **Guidelines for performing systematic literature reviews in software engineering**. Keele: Keele University; Durham: Durham University, 2007. (Technical Report EBSE-2007-01).
::ref LUO, Q.; HARIRI, F.; ELOUSSI, L.; MARINOV, D. An empirical analysis of flaky tests. In: ACM SIGSOFT INTERNATIONAL SYMPOSIUM ON FOUNDATIONS OF SOFTWARE ENGINEERING (FSE), 22., 2014, Hong Kong. **Proceedings** [...]. New York: ACM, 2014. p. 643-653. DOI: 10.1145/2635868.2635920.
::ref PAGE, M. J. et al. The PRISMA 2020 statement: an updated guideline for reporting systematic reviews. **BMJ**, v. 372, n71, 2021. DOI: 10.1136/bmj.n71.
::ref PARRY, O.; KAPFHAMMER, G. M.; HILTON, M.; MCMINN, P. A survey of flaky tests. **ACM Transactions on Software Engineering and Methodology**, v. 31, n. 1, p. 1-74, 2021. DOI: 10.1145/3476105.
::ref PARRY, O.; KAPFHAMMER, G. M.; HILTON, M.; MCMINN, P. Surveying the developer experience of flaky tests. In: INTERNATIONAL CONFERENCE ON SOFTWARE ENGINEERING: SOFTWARE ENGINEERING IN PRACTICE (ICSE-SEIP), 44., 2022, Pittsburgh. **Proceedings** [...]. New York: ACM, 2022. p. 253-262. DOI: 10.1145/3510457.3513037.
::ref PRIEM, J.; PIWOWAR, H.; ORR, R. **OpenAlex**: a fully-open index of scholarly works, authors, venues, institutions, and concepts. arXiv:2205.01833, 2022. Disponível em: https://arxiv.org/abs/2205.01833. Acesso em: 22 nov. 2026.
::ref SILVA, D.; GRUBER, M.; GOKHALE, S.; ARTECA, E.; TURCOTTE, A.; D'AMORIM, M.; LAM, W.; WINTER, S.; BELL, J. The effects of computational resources on flaky tests. **IEEE Transactions on Software Engineering**, v. 50, n. 12, p. 3104-3121, 2024. DOI: 10.1109/TSE.2024.3462251.
::ref XIAO, T.; WANG, D.; MCINTOSH, S.; HATA, H.; KAMEI, Y. Cross-project flakiness: a case study of the OpenStack ecosystem. **IEEE Transactions on Software Engineering**, v. 52, n. 6, p. 1875-1890, 2026. DOI: 10.1109/TSE.2026.3685588.
