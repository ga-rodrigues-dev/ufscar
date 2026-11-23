# UFSCar — TCC workspace

This repository brings together the course sources and working documents for an individual TCC in Desenvolvimento de Software. The current research direction is recorded in the topic document below.

## Start here

- [TCC topic and next steps](metodologia-cientifica/tema-do-tcc.md) — provisional question, scope, candidate studies, and research state.
- [TCC requirements](metodologia-cientifica/exigencias-do-tcc.md) — course instructions, source references, exceptions, and unresolved conflicts.
- [Course materials and Moodle inventory](metodologia-cientifica/materiais-do-moodle.md) — original source links, local materials, and historically captured deadlines.
- [Lecture recordings and transcripts](metodologia-cientifica/gravacoes/README.md) — local videos, reviewed transcripts, download history, and processing notes.
- [Visual supplements](metodologia-cientifica/capturas/README.md) — document reproductions, video checkpoints, and cases reviewed without an image.
- [Review protocol (draft)](metodologia-cientifica/revisao/protocolo.md) — search string, criteria, screening record, and full-text extraction sheets under `revisao/`.
- [TCC draft](metodologia-cientifica/tcc/tcc.md) — AI-assisted first draft of the article; `tcc/build_docx.py` generates `TCC-rascunho.docx` in the SBC template.

## Where things belong

- `AGENTS.md` contains agent instructions and routes to the documents above.
- `metodologia-cientifica/` contains the working TCC documents and course sources. [The Notion export context](metodologia-cientifica/00-disciplina.md) is a historical snapshot, not the current file inventory.
- `metodologia-cientifica/materiais/` contains course PDFs, slides, templates, and examples. `derivados/` and `exemplos/` contain usable derivatives of the original presentation and ZIP.
- `metodologia-cientifica/transcricoes/*.pt.md` are the reviewed reading copies. `raw/` retains the Soniox originals, timed JSON, and provenance.
- `metodologia-cientifica/gravacoes/` contains the source videos and the audio-removal receipt. `capturas/materiais/` contains document reproductions and their manifest.
- [Paper retrieval tools](tools/paper-retrieval-mcp/README.md) are a separate Python subproject. Its ignored `.data/` directory contains operational downloads and experiments, not a selected TCC corpus.

Agent instructions, skills, and agent prompts are maintained in English. Academic notes, transcripts, and TCC working documents use Brazilian Portuguese; original source wording is preserved.
