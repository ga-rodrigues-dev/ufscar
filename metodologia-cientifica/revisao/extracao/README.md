# Leitura completa — decisões e situação dos 28 candidatos (Scopus)

Rascunho de 22/11/2026, preparado com apoio de IA (Claude Code com subagentes de leitura). **Todas as decisões dependem de revisão do aluno.** O número do arquivo corresponde à coluna `ficha` de [../dados/triagem-scopus.csv](../dados/triagem-scopus.csv). As páginas citadas nas fichas referem-se à versão lida. A seção de avaliação de qualidade das fichas foi descartada no protocolo 0.2 e é apenas registro histórico.

## Incluídos (12)

| ID no artigo | Ficha | Estudo | Critério | Versão lida |
|---|---|---|---|---|
| E1 | [017](017.md) | Durieux et al. (2020), MSR | IN2 | arXiv 2003.11772v2 |
| E2 | [022](022.md) | Ahmad, Leifler e Sandahl (2021), STVR | IN1 | Versão publicada na STVR (leitura inicial no preprint arXiv 1906.00673) |
| E3 | [026](026.md) | Ahlgren et al. (2021), ICSE-SEIP | IN1, IN2 | Repositório UCL |
| E4 | [032](032.md) | Parry et al. (2022), ICSE-SEIP | IN1, IN2 | White Rose (versão dos autores) |
| E5 | [039](039.md) | Henderson et al. (2023), ICST | IN2 | Página do autor |
| E6 | [050](050.md) | Berndt, Bach e Baltes (2024), ESEM | IN1 | arXiv 2409.10062 |
| E7 | [055](055.md) | Silva et al. (2024), IEEE TSE | IN1, IN2 | arXiv 2310.12132v1 (anterior à versão da TSE) |
| E8 | [098](098.md) | Hashemi et al. (2026), ICST | IN1, IN2 | arXiv 2602.19098 |
| E9 | [118](118.md) | Xiao et al. (2026), IEEE TSE | IN1 | arXiv 2602.09311v2 |
| E10 | [157](157.md) | Kumar (2026), JIDMIS | IN1, IN2 | PDF da editora |
| E11 | [166](166.md) | Leinen, Perathoner e Pretschner (2024), FTW | IN1 | PDF da editora (ACM) |
| E12 | [168](168.md) | Lampel et al. (2021), ESEC/FSE | IN1 | PDF da editora (ACM) |

## Excluídos na leitura completa (2)

| Ficha | Estudo | Motivo | Observação |
|---|---|---|---|
| [035](035.md) | Habchi et al. (2022), ICSME | Sem contexto de CI (CI apenas como motivação) | Exclusão confirmada pelo aluno (regra estrita) |
| [100](100.md) | Kim et al. (2026), JSS | Sem contexto de CI (execuções em cluster HPC) | Exclusão confirmada pelo aluno (regra estrita) |

As fichas [042](042.md) (Verma, 2023) e [084](084.md) (Barbosa, 2025) vêm da busca exploratória no OpenAlex (protocolo v0.1–v0.2). Esses estudos não estão indexados na Scopus e não fazem parte da revisão.

## Não recuperados (14) — obter via CAFe/UFSCar

| seq | Estudo | DOI |
|---|---|---|
| 012 | Lam et al. (2019), Root causing flaky tests in a large-scale industrial setting, ISSTA | 10.1145/3293882.3330570 |
| 014 | Presler-Marshall et al. (2019), Wait, Wait. No, Tell Me…, AST | 10.1109/ast.2019.000-1 |
| 019 | Kowalczyk et al. (2020), Modeling and ranking flaky tests at Apple, ICSE-SEIP | 10.1145/3377813.3381370 |
| 061 | Mani e Attaranasl (2025), Adaptive Test Healing using LLM/GPT and RL, ICSTW | 10.1109/icstw64639.2025.10962516 |
| 072 | Gan, Liang e Brown (2025), UI Testing in CI/CD, ICST | 10.1109/icst62969.2025.10988972 |
| 076 | Mehta (2025), Self-Healing Automation Frameworks for Flaky CI, ICCA | 10.1109/icca66035.2025.11430985 |
| 079 | Mani e Attaranasl (2025), Adaptive Test Healing with GNN, AITest | 10.1109/aitest66680.2025.00023 |
| 092 | Andreyev (2025), The Art of Managing Flaky Tests at Scale, ICSTW | 10.1109/icstw64639.2025.10962486 |
| 110 | Leinen et al. (2026), Detected and Undetected Flaky Test Failures in CI, IEEE TSE | 10.1109/tse.2026.3729363 |
| 122 | Javvadi et al. (2026), Decision Catalogue for Flaky Tests in CI, ICOSAAS | 10.1109/icosaas68663.2026.11648759 |
| 149 | Parry et al. (2026), Systemic Flakiness, IEEE TSE | 10.1109/tse.2026.3750452 |
| 152 | Jungwirth, Gruber e Fraser (2026), A New Sheriff in Town…, ICSTW | 10.1109/icstw72326.2026.00021 |
| 158 | Andreyev et al. (2026), Beyond Detection: Evaluating Flaky Test Fix Effectiveness, ICSTW | 10.1109/ICSTW72326.2026.00022 |
| 163 | Mani et al. (2025), GraphQL-Aware Healing in Service-Oriented Architectures, SOSE | 10.1109/SOSE67019.2025.00021 |

O registro 110 é de acesso aberto (CC BY) segundo o Semantic Scholar, mas o PDF não foi obtido automaticamente. Para o 149 existe uma versão de conferência anterior (arXiv 2504.16777), que não foi usada porque não é o registro retornado pela busca.
