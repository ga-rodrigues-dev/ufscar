# Paper Retrieval MCP

## CLI `papers`

O mesmo motor pode ser usado diretamente pelo terminal:

```sh
uv run --locked papers retrieve 10.1371/journal.pone.0000308
uv run --locked papers retrieve 10.1371/journal.pone.0000308 --output artigo.pdf
```

O CLI imprime uma resposta JSON com DOI, caminho, tamanho, páginas, hash e cache.
O leitor aceita defeitos estruturais recuperáveis nos originais, como chaves
duplicadas em dicionários de PDFs publicados. A cópia exportada é reescrita e
reaberta em modo estrito; o original e seu hash continuam preservados.
O arquivo entregue é, por padrão, uma cópia com o dicionário Info, os metadados
XMP (inclusive em páginas/objetos) e os identificadores do trailer removidos.
O original permanece intacto em `papers/`; a cópia padrão fica em `exports/`.
`--output` escolhe outro destino para essa cópia. O JSON inclui
`metadata_cleaned: true`; tamanho e SHA-256 descrevem a cópia entregue.
`cached` continua indicando a reutilização do download original.
Cada exportação registra os caminhos e hashes de ambas as versões em
`private/export-*.json`, com estado `pending` ou `complete`.
Conteúdo visível, links e anotações são preservados. Isso não constitui garantia
de anonimização e reescrever um PDF pode invalidar assinaturas digitais.
Falhas retornam `ok: false` e código de saída diferente de zero, sem endereços do
provedor ou traceback. Não sobrescreve um arquivo de saída existente.

A configuração local do operador fica em `.data/private/settings.json`, ignorada
pelo Git; pode ser substituída com `papers --config /caminho/settings.json retrieve DOI`.
O arquivo aceita campos de `Settings`, incluindo `provider_urls`, `host_overrides`
e `proxy_url`. As configurações do arquivo prevalecem sobre as variáveis de
ambiente; `--data-dir` prevalece sobre ambos. Diagnósticos ficam em
`.data/private/cli-errors.log`. O CLI não inicia nem importa o servidor MCP.

A interface é neutra quanto ao provedor. Isso não anonimiza o PDF e não impede
um agente com acesso ao sistema de arquivos de consultar a configuração ou os
registros de origem.

### Falhas e diagnóstico

O campo `error.code` distingue restrições do ambiente (`network_permission_denied`),
conexão (`connection_failed`), TLS (`tls_failed`), limite de requisições
(`rate_limited`), acesso negado (`access_denied`), verificação pendente
(`verification_required`), resposta sem link (`no_pdf_link`) e documento inválido
(`invalid_document`). `not_found` descreve HTTP 404 no endpoint, não uma conclusão
sobre a existência do artigo. `unavailable` fica reservado a falhas não classificadas.

Em um sandbox, `network_permission_denied` requer a autorização normal de rede da
ferramenta de execução antes de repetir o comando. O CLI não concede essa autorização.
Os diagnósticos locais registram data, código, status HTTP e tipos/errnos das causas
encadeadas. Cookies e tokens da verificação não são gravados nesses registros.

O cliente reconhece o fluxo observado de prova de trabalho ALTCHA v1 SHA-256,
mantendo os cookies somente na sessão HTTP atual. Executa no máximo uma prova por
recuperação, limitada a dois milhões de passos e dez segundos; o limite total da
recuperação continua valendo. Não executa JavaScript recebido. Formulários de
reporte de problemas não são tratados como barreiras de acesso. Outros desafios,
provas acima do limite ou uma verificação repetida retornam `verification_required`.
O protocolo v1 está descrito na [biblioteca oficial ALTCHA](https://github.com/altcha-org/altcha-lib-py#pow-v1-legacy).

Para testar a rede sem reaproveitar o cache, escolha uma coleção vazia com
`papers --data-dir /caminho/novo retrieve DOI` e confira `cached: false`.

## Download real validado em 06/11/2026

O MCP por stdio baixou do próprio Sci-Hub o artigo
*Sharing Detailed Research Data Is Associated with Increased Citation Rate*,
DOI `10.1371/journal.pone.0000308`: 91.408 bytes, cinco páginas.
Foram conferidos DOI e título no PDF, SHA-256, igualdade dos bytes do recurso
MCP com o arquivo e reutilização do cache. A nova consulta ao Crossref falhou;
o título esperado havia sido consultado no Crossref anteriormente nesta sessão.

O DNS local retornou `146.112.61.106` para todos os espelhos consultados.
O endereço público de `sci-hub.ru` observado na consulta foi `190.115.31.218`.
`PAPER_HOST_OVERRIDES` permite configurar esse destino somente no cliente MCP,
preservando hostname HTTP, SNI e verificação de certificado HTTPS.
O exemplo de configuração já inclui a rota que funcionou. IPs podem mudar;
esta validação não garante disponibilidade futura ou acesso a outros artigos.

```sh
export PAPER_PROVIDER_URLS='https://sci-hub.ru'
export PAPER_HOST_OVERRIDES='{"sci-hub.ru":"190.115.31.218"}'
uv run --locked paper-retrieval-mcp
```

Os overrides aceitam apenas hosts configurados e IPs públicos. Como alternativa,
`PAPER_PROXY_URL=socks5h://127.0.0.1:1080` permite usar um proxy SOCKS com resolução
no proxy, inclusive um túnel SSH quando a outra máquina estiver disponível.
Proxy e overrides são modos mutuamente exclusivos.

Para repetir um download real em uma coleção nova:

```sh
uv run --locked python scripts/validate_live.py \
  --doi 10.1371/journal.pone.0000308 \
  --provider-url https://sci-hub.ru \
  --resolve sci-hub.ru=190.115.31.218
```

O script grava o resultado e suas verificações em `.data/live-*/private/`.
Sua aprovação automática também depende de consultar o título no Crossref;
falhas nesse serviço ficam registradas separadamente do resultado do download.

Servidor MCP local em Python para recuperar PDFs de artigos científicos por DOI.
O LLM chama `retrieve_paper(doi)`; os espelhos de Sci-Hub são configurados pelo
operador em variáveis de ambiente. Nome, descrição, esquema, resultados e erros
da ferramenta não incluem o provedor nem suas URLs.

## Executar

Requer Python 3.11+ e [uv](https://docs.astral.sh/uv/).

```sh
cd /Users/c24580q/UFSCar/tools/paper-retrieval-mcp
uv sync --locked
export PAPER_PROVIDER_URLS='https://seu-espelho.example'
uv run --locked paper-retrieval-mcp
```

Substitua `https://seu-espelho.example` por um espelho que você tenha verificado.
O servidor usa stdio e aguarda mensagens de um cliente MCP. Nenhum espelho é
ativado por padrão. Não é necessário token para esse adaptador.

Nesta máquina, `uv` está em `/Users/c24580q/.local/bin/uv`.
Se a rede exigir a CA do sistema para instalar pacotes, use
`uv --system-certs sync --locked`; a verificação TLS continua habilitada.
O cliente HTTP de recuperação usa `ssl.create_default_context()`, que respeita
`SSL_CERT_FILE` e `SSL_CERT_DIR` quando for necessário configurar uma CA.

O arquivo [mcp-config.example.json](mcp-config.example.json) contém uma entrada
de configuração para clientes MCP com a chave `mcpServers`. Ele chama diretamente
o Python do ambiente virtual, evitando instalação de dependências na inicialização.
Edite `PAPER_PROVIDER_URLS` nessa entrada e adapte o formato ao seu cliente.

## Contrato público

Argumentos aceitos:

```json
{"doi": "10.1234/example"}
```

Também aceita `doi:10.1234/example` e
`https://doi.org/10.1234/example`. Não faz busca por título ou PMID nesta versão.

A resposta estruturada contém `doi`, `paper_id`, `file_path`, `resource_uri`,
`mime_type`, `size_bytes`, `sha256`, `page_count` e `cached`. O caminho aponta para
um PDF local; o recurso `papers://{paper_id}/pdf` entrega os mesmos bytes pelo MCP.
Clientes que não carregam recursos PDF podem usar o arquivo local.

O `paper_id` é o SHA-256 do DOI normalizado. O campo `sha256` é calculado sobre o
conteúdo do PDF. São identificadores diferentes.

## Configuração do operador

- `PAPER_PROVIDER_URLS`: URLs HTTPS dos espelhos, separadas por vírgula, na ordem
  de tentativa. Os espelhos devem aceitar o caminho `/<DOI>` e retornar um PDF
  ou uma página com `iframe`, `embed`, `object` ou link para PDF.
- `PAPER_ALLOWED_HOSTS`: hosts adicionais exatos de CDNs de PDF, separados por
  vírgula. Os hosts dos próprios espelhos já são permitidos. Não aceita curingas.
- `PAPER_DATA_DIR`: diretório de dados. No checkout com instalação editável por
  `uv`, o padrão é `.data/` neste projeto. Defina um caminho absoluto ao distribuir
  uma instalação em outro local.
- `PAPER_REQUEST_TIMEOUT`: timeout de cada operação HTTP em segundos; padrão 20.
- `PAPER_RETRIEVAL_TIMEOUT`: limite total por chamada, incluindo espera por outra
  recuperação; padrão 90 segundos.
- `PAPER_MAX_PDF_BYTES`: limite por resposta PDF; padrão 33.554.432 bytes (32 MiB).
  Páginas HTML têm limite de 2 MiB.

Só URLs HTTPS sem credenciais e na porta padrão são aceitas. Cada redirecionamento
e candidato a PDF é conferido contra os hosts configurados; redirecionamentos
têm limite de seis requisições. A configuração seleciona hosts confiáveis pelo
operador: a lista de hosts não substitui isolamento de rede nem fixa os IPs DNS.

O servidor mantém uma recuperação por vez. Chamadas repetidas usam o cache
somente se o tamanho e o SHA-256 do arquivo corresponderem ao registro. Arquivos
novos são gravados por substituição atômica após validação.

## Origem e rastreabilidade

Os PDFs ficam em `.data/papers/`. Registros de aquisição e erros ficam em
`.data/private/`, sem ferramentas ou recursos MCP que os exponham. O registro
inclui URLs de aquisição sem query/fragmento, instante UTC, DOI e hash. Ele não
contém o HTML recebido. Esses diretórios e o ambiente virtual são ignorados pelo
Git. As mensagens de diagnóstico do provedor são gravadas em arquivo local;
stdout fica reservado ao protocolo.

Essa separação abstrai o provedor na interface. Não garante que o LLM jamais
identifique a origem: o PDF original pode conter marcas, links ou metadados, e
um agente com acesso a arquivos locais pode ler a configuração e os registros.
O servidor preserva os bytes recebidos e não remove essas informações.

A validação verifica assinatura PDF, estrutura legível, presença de páginas e
ausência de criptografia. Não verifica automaticamente se autores, título e DOI
do documento correspondem ao artigo solicitado. O registro marca essa conferência
como `identity_verification: not_checked`; confira o documento antes de usá-lo
como evidência na revisão.

## Referências consultadas

Consulta em 06/11/2026; o código deste servidor foi implementado diretamente,
sem incorporar código dos projetos abaixo como dependência.

- [SciDownl](https://github.com/Tishacy/SciDownl): biblioteca/CLI com DOI, PMID e
  título, seleção de espelhos e extração de PDF configurável. O
  [módulo de download](https://github.com/Tishacy/SciDownl/blob/master/scidownl/core/downloader.py)
  usa `requests` e escreve uma barra de progresso em stdout. É uma referência
  útil para o adaptador; sua saída e suas exceções precisam de tratamento num MCP.
- [PyPaperBot](https://github.com/ferru97/PyPaperBot): busca e download por várias
  fontes, com filtros e BibTeX. O
  [Downloader.py](https://github.com/ferru97/PyPaperBot/blob/master/PyPaperBot/Downloader.py)
  imprime nomes dos provedores e endereços, além de usar chamadas síncronas.
  Seu escopo é maior que o de uma ferramenta de recuperação por DOI.
- [pyscihub](https://github.com/markkvdb/pyscihub): alternativa com CLI/API. A API
  do GitHub não identificou licença na consulta; não foi adotado como dependência.
  Isso não é uma análise jurídica dos arquivos do projeto.
- [SDK Python oficial do MCP](https://py.sdk.modelcontextprotocol.io/): a versão
  instalada e fixada no lock é 2.3.0; o servidor usa `MCPServer` e stdio.

## Verificação

```sh
uv run --locked python -m unittest discover -s tests -v
```

Os testes usam PDFs sintéticos e HTTP simulado. Verificam sucesso pelo MCP,
recurso binário, cache, integridade, fallback, limites, redirects, concorrência e
erros sem URLs do provedor. Incluem um processo real por stdio usando um PDF
sintético previamente colocado no cache; esse teste não acessa a rede.

Em 06/11/2026, uma tentativa real com `https://sci-hub.se` e o DOI
`10.1371/journal.pone.0000308` terminou em `ConnectTimeout`. O download externo
por esse espelho não foi validado nesta rede. O domínio é citado no código dos
projetos consultados; esse resultado não confirma nem descarta sua disponibilidade
em outra rede. Não houve download real bem-sucedido nessa tentativa.
