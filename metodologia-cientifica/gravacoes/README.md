# Gravações e transcrições das aulas

Os links de origem no Moodle, nos encurtadores e no Drive estão no [inventário de materiais](../materiais-do-moodle.md). Este guia reúne os arquivos locais e o histórico de obtenção e processamento. As datas abaixo descrevem verificações históricas.

## Download pelo servidor oficial do Drive

Os pares de links Moodle/Drive das aulas de 16/10 e 30/10 foram fornecidos pelo aluno em 06/11/2026; o redirecionamento pelo Moodle não foi verificado nesta atualização. Nos testes locais, as páginas em `drive.google.com` retornaram `403 URLBlocked` do filtro corporativo, enquanto o servidor oficial `drive.usercontent.google.com` respondeu com os arquivos MP4.

O endereço usado foi `https://drive.usercontent.google.com/download?id=ID_DO_ARQUIVO&export=download`. Para os dois vídeos, o Google apresentou primeiro um formulário de confirmação devido ao tamanho; o download foi iniciado pelo próprio formulário, preservando seus campos. Não foi necessário alterar DNS, proxy ou configurações de segurança. Essa disponibilidade foi verificada em 06/11/2026 e pode mudar.

### Recuperação dos destinos encurtados de setembro

Em 06/11/2026, as páginas autenticadas do Moodle, abertas com `forceview=1&redirect=0`, expuseram somente os links `acesse.one/GqHX6x0`, `acesse.one/jYxWT4M` e `acesse.one/2msrCSH`. As páginas de redirecionamento tinham apresentado bloqueio corporativo.

A página pública [Desencurtar link](https://www.encurtador.dev/pt-BR/desencurtar-link.html) abriu no Chrome. Sua função de prévia consultava a rota de estatísticas, que não revelou os destinos. O código público do site identificou a API `https://api.encurtador.dev/encurtamentos`. Requisições GET a `https://api.encurtador.dev/encurtamentos/CODIGO`, feitas no próprio Chrome com `credentials: 'omit'`, retornaram HTTP 200 e o campo `url` para os três códigos. Esses resultados forneceram os links diretos registrados no inventário de materiais. Não foram usados proxies de terceiros nem alteradas configurações de DNS, TLS ou do filtro corporativo.

Os três vídeos de setembro foram então baixados pelo servidor oficial do Drive, com os campos atuais do formulário de confirmação e cookies temporários da própria transferência.

## Vídeos locais

- Aula 18/09: [MP4 local](2026-09-18%201849%20-%20Metodologia%20de%20Pesquisa%20-%20Aula%201.mp4), 1.404.976.565 bytes, duração aproximada de **03:01:19**. Nome original no Drive: `Metodologia de Pesquisa - FDS 1, Aula 1 - 2026/09/18 18:49 GMT-03:00 - Recording.mp4`.
- Aula 19/09 — Parte 1: [MP4 local](2026-09-19%200756%20-%20Metodologia%20de%20Pesquisa%20-%20Aula%202%20-%20Parte%201.mp4), 2.434.758.694 bytes, duração aproximada de **05:22:43**. Nome original no Drive: `Metodologia de Pesquisa - FDS 1, Aula 2 - 2026/09/19 07:56 GMT-03:00 - Recording.mp4`.
- Aula 19/09 — Parte 2: [MP4 local](2026-09-19%201333%20-%20Metodologia%20de%20Pesquisa%20-%20Aula%202%20-%20Parte%202.mp4), 836.220.974 bytes, duração aproximada de **01:22:33**. Nome original no Drive: `Metodologia de Pesquisa - FDS 1, Aula 2 - 2026/09/19 13:33 GMT-03:00 - Recording.mp4`.
- Aula 02/10: [MP4 local](2026-10-02%201854%20-%20Metodologia%20de%20Pesquisa.mp4), 222.402.086 bytes, duração aproximada de **01:13:32**. Nome original no Drive: `rgm-nxhu-ynv (2026-10-02 18:54 GMT-3).mp4`.
- Aula 16/10: [MP4 local](2026-10-16%20-%20Metodologia%20de%20Pesquisa.mp4), 278.048.849 bytes, duração de **00:23:58**. Nome original no Drive: `imo-nzfn-ygs (2026-10-16 18:53 GMT-3).mp4`.
- Aula 30/10: [MP4 local](2026-10-30%20-%20Metodologia%20de%20Pesquisa.mp4), 3.070.937.320 bytes, duração aproximada de **01:26:43**. Nome original no Drive: `Metodologia de Pesquisa - FDS 4, Aula 1 - 2026_10_30.mp4`.

Os seis vídeos foram baixados em 06/11/2026. Os três vídeos de outubro já constavam como baixados e validados e não foram baixados novamente nesta execução. Para os três novos vídeos de setembro, a resposta GET final foi HTTP 200 com tipo `video/mp4`, e o tamanho de cada arquivo correspondeu ao `Content-Length` dessa resposta. O `ffprobe` identificou vídeo e áudio, e a leitura de todos os pacotes com `ffmpeg` terminou sem erros nos três novos arquivos. Na validação anterior à remoção dos áudios, as durações diferiam das dos áudios locais correspondentes em menos de 0,1 segundo. Essas verificações não estabelecem se as gravações cobrem as aulas inteiras nem validam seu conteúdo por audição.

SHA-256 dos três vídeos de setembro, calculados após o download:

```text
fcc606f6ce5c6a21c8d45004e7efac95c24f79c343c37341aca544ce7317cd5f  2026-09-18 1849 - Metodologia de Pesquisa - Aula 1.mp4
e0e492998350d9cb670f845b8af4932609e14e7ea166b9072a908b075cd939b4  2026-09-19 0756 - Metodologia de Pesquisa - Aula 2 - Parte 1.mp4
3bafd056b7b4c065d7b2afd429a566f9e816968b5b4b632106d725c92fce27f4  2026-09-19 1333 - Metodologia de Pesquisa - Aula 2 - Parte 2.mp4
```

## Transcrições Soniox

As transcrições `*.pt.md` em [`transcricoes/`](../transcricoes/) são as cópias revisadas para leitura e consulta. As saídas originais do Soniox (`stt-async-v5` nas primeiras gravações; `stt-async-v6` nas aulas de 16/10 e 30/10) e os metadados ficam em [`transcricoes/raw/`](../transcricoes/raw/) e não devem ser usados como fonte principal para consultas. A revisão por IA conferiu terminologia e coerência com as notas, os slides ou quadros selecionados do vídeo, conforme indicado em cada cópia. Também examinou as trocas de fala e marcou blocos em que o Soniox agrupou vozes distintas ou trocou o número atribuído ao docente. A [revisão da diarização](../transcricoes/raw/revisao-diarizacao.md) registra os trechos das primeiras gravações; as observações das aulas de 16/10 e 30/10 estão nas próprias cópias revisadas. Não houve audição integral nem validação humana; identificações de pessoas são inferências do diálogo. Os arquivos JSON em `transcricoes/raw/` preservam a resposta completa do provedor, inclusive os tempos e as palavras individuais.

- Aula 18/09: [cópia revisada](../transcricoes/2026-09-18%201849%20-%20Metodologia%20de%20Pesquisa%20-%20Aula%201.pt.md) · [original Soniox](../transcricoes/raw/2026-09-18%201849%20-%20Metodologia%20de%20Pesquisa%20-%20Aula%201.soniox-original.pt.md)
- Aula 19/09, parte 1: [00:00–02:40 revisada](../transcricoes/2026-09-19%200756%20-%20Metodologia%20de%20Pesquisa%20-%20Aula%202%20-%20Parte%201%20-%20Segmento%201.pt.md) · [original](../transcricoes/raw/2026-09-19%200756%20-%20Metodologia%20de%20Pesquisa%20-%20Aula%202%20-%20Parte%201%20-%20Segmento%201.soniox-original.pt.md) · [02:40–05:22 revisada](../transcricoes/2026-09-19%200756%20-%20Metodologia%20de%20Pesquisa%20-%20Aula%202%20-%20Parte%201%20-%20Segmento%202.pt.md) · [original](../transcricoes/raw/2026-09-19%200756%20-%20Metodologia%20de%20Pesquisa%20-%20Aula%202%20-%20Parte%201%20-%20Segmento%202.soniox-original.pt.md). A gravação foi dividida para respeitar o limite de duração do Soniox; os horários nas transcrições referem-se à gravação original.
- Aula 19/09, parte 2: [cópia revisada](../transcricoes/2026-09-19%201333%20-%20Metodologia%20de%20Pesquisa%20-%20Aula%202%20-%20Parte%202.pt.md) · [original Soniox](../transcricoes/raw/2026-09-19%201333%20-%20Metodologia%20de%20Pesquisa%20-%20Aula%202%20-%20Parte%202.soniox-original.pt.md)
- Aula 02/10: [cópia revisada](../transcricoes/2026-10-02%201854%20-%20Metodologia%20de%20Pesquisa.pt.md) · [original Soniox](../transcricoes/raw/2026-10-02%201854%20-%20Metodologia%20de%20Pesquisa.soniox-original.pt.md)

- Aula 16/10: [cópia revisada](../transcricoes/2026-10-16%20-%20Metodologia%20de%20Pesquisa.pt.md) · [original Soniox](../transcricoes/raw/2026-10-16%20-%20Metodologia%20de%20Pesquisa.soniox-original.pt.md).
- Aula 30/10: [cópia revisada com imagens](../transcricoes/2026-10-30%20-%20Metodologia%20de%20Pesquisa.pt.md) · [original Soniox](../transcricoes/raw/2026-10-30%20-%20Metodologia%20de%20Pesquisa.soniox-original.pt.md).

O programa de transcrição usa o contexto registrado em [`transcription-context.json`](../transcricoes/raw/transcription-context.json), pode retomar trabalhos interrompidos e exclui os recursos remotos ao concluir. Nas duas transcrições de 06/11/2026, os trabalhos e arquivos de áudio remotos foram excluídos após a obtenção dos resultados.

## Complemento visual

O [guia visual das aulas](../capturas/README.md) reúne as imagens reproduzidas dos materiais originais, os pontos de conferência nos vídeos e as justificativas dos trechos revisados sem imagem. O manifesto e os limites dessa revisão estão documentados no mesmo guia.

## Remoção dos áudios locais

Em 06/11/2026, a pedido do aluno, foram removidos os seis M4A das aulas e dois segmentos temporários usados no Soniox, após conferir que os seis MP4 correspondentes têm trilhas de vídeo e áudio. Vídeos, transcrições, resultados originais e materiais visuais permanecem disponíveis. O [registro da remoção](audios-removidos.json) conserva caminhos, tamanhos, hashes e o vídeo correspondente a cada áudio.

Os links das cópias revisadas apontam agora para os vídeos. Os originais Soniox foram preservados, inclusive seus links históricos para áudios removidos; nesses casos, use o MP4 do mesmo nome-base ou o registro acima. Para uma nova transcrição, o áudio pode ser extraído novamente do vídeo; o script de transcrição espera um M4A local.
