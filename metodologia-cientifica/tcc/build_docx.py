"""Gera o DOCX do TCC a partir de tcc.md usando a formatação do template SBC da disciplina.

Uso: python3 build_docx.py  (lê tcc.md, escreve TCC-rascunho.docx ao lado)

Sintaxe aceita em tcc.md (subconjunto de Markdown):
  # Título                      -> título do artigo
  @autor / @afiliacao / @email  -> bloco de identificação
  **Resumo.** ...               -> resumo (recuado, itálico)
  ## 1. Seção                   -> seção numerada (Times 13 negrito)
  ### 1.1. Subseção             -> subseção (Times 12 negrito)
  Tabela N. legenda + tabela pipe logo abaixo
  ![Figura N. legenda](arquivo.png){largura_cm}
  linhas iniciadas por "- "     -> lista com marcador
  ::ref texto                   -> item de referência (ABNT)
  *itálico*, **negrito**
"""
import re, shutil, struct, sys, zipfile
from pathlib import Path
from xml.sax.saxutils import escape

HERE = Path(__file__).resolve().parent
TEMPLATE = HERE.parent / "materiais" / "MeuTCC-explicacoesGerais 2026.docx"
SRC = HERE / "tcc.md"
OUT = HERE / "TCC-rascunho.docx"

NOBDR = '<w:pBdr><w:top w:val="nil"/><w:left w:val="nil"/><w:bottom w:val="nil"/><w:right w:val="nil"/><w:between w:val="nil"/></w:pBdr>'
HELV = '<w:rFonts w:ascii="Helvetica Neue" w:eastAsia="Helvetica Neue" w:hAnsi="Helvetica Neue" w:cs="Helvetica Neue"/>'


def runs(text, base=""):
    """Converte *itálico* e **negrito** em runs WordprocessingML."""
    out = []
    text = text.replace("\\*", "\x00")  # \* = asterisco literal (ex.: truncamento na string de busca)
    for tok in re.split(r"(\*\*[^*]+\*\*|\*[^*]+\*)", text):
        if not tok:
            continue
        rpr = base
        if tok.startswith("**"):
            tok, rpr = tok[2:-2], base + "<w:b/>"
        elif tok.startswith("*"):
            tok, rpr = tok[1:-1], base + "<w:i/>"
        tok = tok.replace("\x00", "*")
        out.append(f'<w:r><w:rPr>{rpr}<w:color w:val="000000"/></w:rPr><w:t xml:space="preserve">{escape(tok)}</w:t></w:r>')
    return "".join(out)


def para(text, ppr="", rbase=""):
    return f"<w:p><w:pPr>{NOBDR}{ppr}</w:pPr>{runs(text, rbase)}</w:p>"


def heading(text, level):
    size = 26 if level == 1 else 24
    return (f'<w:p><w:pPr><w:keepNext/>{NOBDR}<w:spacing w:before="240"/><w:jc w:val="left"/></w:pPr>'
            f'<w:r><w:rPr><w:b/><w:color w:val="000000"/><w:sz w:val="{size}"/><w:szCs w:val="{size}"/></w:rPr>'
            f'<w:t xml:space="preserve">{escape(text)}</w:t></w:r></w:p>')


def caption(text, keep_next=False):
    kn = "<w:keepNext/>" if keep_next else ""
    rb = HELV + '<w:b/><w:sz w:val="20"/><w:szCs w:val="20"/>'
    return (f'<w:p><w:pPr>{kn}{NOBDR}<w:spacing w:before="120" w:after="120"/><w:ind w:left="454" w:right="454"/><w:jc w:val="center"/></w:pPr>'
            f'{runs(text, rb)}</w:p>')


def table(rows, total=8505):
    ncol = len(rows[0])
    # largura proporcional ao maior conteúdo de cada coluna (mínimo 9%)
    lens = [max(len(r[c]) for r in rows) for c in range(ncol)]
    weights = [max(l, sum(lens) * 0.09) for l in lens]
    widths = [int(total * w / sum(weights)) for w in weights]
    widths[-1] = total - sum(widths[:-1])
    b = '<w:{0} w:val="single" w:sz="4" w:space="0" w:color="000000"/>'
    borders = "".join(b.format(s) for s in ["top", "left", "bottom", "right", "insideH", "insideV"])
    x = [f'<w:tbl><w:tblPr><w:tblW w:w="{total}" w:type="dxa"/><w:jc w:val="center"/><w:tblBorders>{borders}</w:tblBorders>'
         f'<w:tblLayout w:type="fixed"/><w:tblCellMar><w:left w:w="57" w:type="dxa"/><w:right w:w="57" w:type="dxa"/></w:tblCellMar></w:tblPr><w:tblGrid>']
    x += [f'<w:gridCol w:w="{w}"/>' for w in widths]
    x.append("</w:tblGrid>")
    for i, r in enumerate(rows):
        hdr = '<w:trPr><w:tblHeader/><w:cantSplit/></w:trPr>' if i == 0 else '<w:trPr><w:cantSplit/></w:trPr>'
        x.append(f"<w:tr>{hdr}")
        for c, cell in enumerate(r):
            rb = '<w:sz w:val="18"/><w:szCs w:val="18"/>' + ("<w:b/>" if i == 0 else "")
            x.append(f'<w:tc><w:tcPr><w:tcW w:w="{widths[c]}" w:type="dxa"/></w:tcPr>'
                     f'<w:p><w:pPr>{NOBDR}<w:keepNext/><w:spacing w:before="20" w:after="20"/><w:jc w:val="left"/></w:pPr>{runs(cell.strip(), rb)}</w:p></w:tc>')
        x.append("</w:tr>")
    x.append("</w:tbl>")
    return "".join(x)


def png_size(path):
    with open(path, "rb") as f:
        head = f.read(24)
    return struct.unpack(">II", head[16:24])


def image(rid, path, width_cm, n):
    wpx, hpx = png_size(path)
    cx = int(width_cm * 360000)
    cy = int(cx * hpx / wpx)
    return (f'<w:p><w:pPr>{NOBDR}<w:keepNext/><w:spacing w:before="120"/><w:jc w:val="center"/></w:pPr><w:r><w:drawing>'
            f'<wp:inline distT="0" distB="0" distL="0" distR="0"><wp:extent cx="{cx}" cy="{cy}"/><wp:docPr id="{100+n}" name="Figura {n}"/>'
            f'<a:graphic xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"><a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/picture">'
            f'<pic:pic xmlns:pic="http://schemas.openxmlformats.org/drawingml/2006/picture"><pic:nvPicPr><pic:cNvPr id="{100+n}" name="fig{n}.png"/><pic:cNvPicPr/></pic:nvPicPr>'
            f'<pic:blipFill><a:blip r:embed="{rid}"/><a:stretch><a:fillRect/></a:stretch></pic:blipFill>'
            f'<pic:spPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="{cx}" cy="{cy}"/></a:xfrm><a:prstGeom prst="rect"><a:avLst/></a:prstGeom></pic:spPr></pic:pic>'
            f'</a:graphicData></a:graphic></wp:inline></w:drawing></w:r></w:p>')


def build():
    lines = SRC.read_text(encoding="utf-8").splitlines()
    meta, body, images = {}, [], []
    first_in_section = True
    i = 0
    while i < len(lines):
        ln = lines[i].rstrip()
        if not ln or ln.startswith("<!--"):
            i += 1
            continue
        if ln.startswith("# "):
            meta["title"] = ln[2:]
        elif ln.startswith("@"):
            k, v = ln[1:].split(" ", 1)
            meta[k] = v
        elif ln.startswith("**Resumo.**"):
            body.append(para(ln, '<w:spacing w:before="240" w:after="120"/><w:ind w:left="454" w:right="454"/>', "<w:i/>"))
        elif ln.startswith("## "):
            body.append(heading(ln[3:], 1)); first_in_section = True
        elif ln.startswith("### "):
            body.append(heading(ln[4:], 2)); first_in_section = True
        elif re.match(r"^Tabela \d+\.", ln):
            body.append(caption(ln, keep_next=True))
            rows = []
            i += 1
            while i < len(lines) and lines[i].startswith("|"):
                cells = lines[i].strip().strip("|").split("|")
                if not re.match(r"^\s*:?-+", cells[0]):
                    rows.append(cells)
                i += 1
            body.append(table(rows))
            body.append('<w:p><w:pPr><w:spacing w:before="0" w:after="0"/></w:pPr></w:p>')
            continue
        elif ln.startswith("!["):
            m = re.match(r"!\[(.+?)\]\((.+?)\)(?:\{([\d.]+)\})?", ln)
            cap, p, w = m.group(1), HERE / m.group(2), float(m.group(3) or 14)
            n = len(images) + 1
            rid = f"rIdImg{n}"
            images.append((rid, p, n))
            body.append(image(rid, p, w, n))
            body.append(caption(cap))
        elif ln.startswith("- "):
            body.append(para("• " + ln[2:], '<w:spacing w:before="60"/><w:ind w:left="567" w:hanging="283"/>'))
        elif ln.startswith("::ref "):
            body.append(para(ln[6:], '<w:spacing w:before="0" w:after="120"/><w:jc w:val="left"/>'))
        else:
            ind = "" if first_in_section else '<w:ind w:firstLine="397"/>'
            body.append(para(ln, ind))
            first_in_section = False
        i += 1

    work = Path(sys.argv[1]) if len(sys.argv) > 1 else HERE / ".build"
    if work.exists():
        shutil.rmtree(work)
    zipfile.ZipFile(TEMPLATE).extractall(work)
    doc = (work / "word" / "document.xml").read_text(encoding="utf-8")
    ps = re.findall(r"<w:p[ >].*?</w:p>", doc, re.S)
    head_open = doc[: doc.index("<w:body>") + len("<w:body>")]
    sect_final = re.findall(r"<w:sectPr(?:(?!<w:sectPr).)*?</w:sectPr>\s*</w:body>", doc, re.S)[-1]
    if 'xmlns:wp=' not in head_open:
        head_open = head_open.replace("<w:document ", '<w:document xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing" ', 1)

    def set_text(p, text):
        """Mantém a formatação do parágrafo do template e substitui o texto."""
        ppr = re.search(r"<w:pPr>.*?</w:pPr>", p, re.S).group(0)
        rpr = re.search(r"<w:r>.*?(<w:rPr>.*?</w:rPr>)", p, re.S)
        rpr = rpr.group(1) if rpr else ""
        return f'<w:p>{ppr}<w:r>{rpr}<w:t xml:space="preserve">{escape(text)}</w:t></w:r></w:p>'

    title = set_text(ps[0], meta["title"])
    author = ps[1].replace(">MeuNome<", f">{escape(meta['autor'])}<")
    author = re.sub(r"<w:t>MeuNome</w:t>", f"<w:t>{escape(meta['autor'])}</w:t>", author)
    affil = ps[2]
    email = set_text(ps[3], meta.get("email", ""))  # o pPr do parágrafo 3 contém a quebra de seção
    new = head_open + title + author + affil + email + "".join(body) + sect_final + "</w:document>"
    (work / "word" / "document.xml").write_text(new, encoding="utf-8")

    rels = work / "word" / "_rels" / "document.xml.rels"
    r = rels.read_text(encoding="utf-8")
    for rid, p, n in images:
        shutil.copy(p, work / "word" / "media" / f"fig{n}.png")
        r = r.replace("</Relationships>", f'<Relationship Id="{rid}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="media/fig{n}.png"/></Relationships>')
    rels.write_text(r, encoding="utf-8")

    core = work / "docProps" / "core.xml"
    if core.exists():
        c = core.read_text(encoding="utf-8")
        c = re.sub(r"<dc:title>.*?</dc:title>", f"<dc:title>{escape(meta['title'])}</dc:title>", c)
        c = re.sub(r"<dc:creator>.*?</dc:creator>", f"<dc:creator>{escape(meta['autor'])}</dc:creator>", c)
        core.write_text(c, encoding="utf-8")

    if OUT.exists():
        OUT.unlink()
    with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED) as z:
        for f in sorted(work.rglob("*")):
            if f.is_file():
                z.write(f, f.relative_to(work).as_posix())
    shutil.rmtree(work)
    print(OUT, OUT.stat().st_size, "bytes;", len(body), "blocos")


if __name__ == "__main__":
    build()
