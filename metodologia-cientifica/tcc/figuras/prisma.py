"""Gera o fluxograma PRISMA 2020 (figuras/prisma.png) com os números de protocolo.md."""
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path
W, H = 1800, 1250
img = Image.new("RGB", (W, H), "white"); d = ImageDraw.Draw(img)
F = "/System/Library/Fonts/Helvetica.ttc"
f = ImageFont.truetype(F, 30); fb = ImageFont.truetype(F, 30, index=1); fs = ImageFont.truetype(F, 27)

def box(x, y, w, h, lines, fill="#ffffff"):
    d.rectangle([x, y, x + w, y + h], outline="black", width=3, fill=fill)
    ty = y + (h - sum(36 if i else 38 for i in range(len(lines)))) // 2
    for i, ln in enumerate(lines):
        font = fb if i == 0 else fs
        tw = d.textlength(ln, font=font); d.text((x + (w - tw) / 2, ty), ln, fill="black", font=font); ty += 38 if i == 0 else 36
    return (x, y, w, h)

def arrow(x1, y1, x2, y2):
    d.line([x1, y1, x2, y2], fill="black", width=3)
    if x1 == x2: d.polygon([(x2 - 10, y2 - 18), (x2 + 10, y2 - 18), (x2, y2)], fill="black")
    else: d.polygon([(x2 - 18, y2 - 10), (x2 - 18, y2 + 10), (x2, y2)], fill="black")

# faixas laterais
for (y, h, t) in [(30, 230, "Identificação"), (300, 610, "Triagem"), (950, 270, "Inclusão")]:
    d.rectangle([20, y, 90, y + h], fill="#dde6f0", outline="black", width=2)
    lab = Image.new("RGBA", (h, 70), (0, 0, 0, 0)); ld = ImageDraw.Draw(lab)
    tw = ld.textlength(t, font=fb); ld.text(((h - tw) / 2, 18), t, fill="black", font=fb)
    lab = lab.rotate(90, expand=True); img.paste(lab, (20, y), lab)

L, BW, R, RW = 140, 700, 1000, 760
box(L, 40, BW, 190, ["Registros identificados", "Scopus (TITLE-ABS-KEY)", "22/11/2026: n = 89"])
box(R, 40, RW, 190, ["Removidos antes da triagem", "Duplicatas e versões", "preliminares: n = 3"])
arrow(L + BW, 135, R, 135)
box(L, 310, BW, 150, ["Registros triados", "(título e resumo): n = 86"])
box(R, 290, RW, 250, ["Registros excluídos: n = 58", "EX1 fora do tema: 2", "EX2 periférico: 24", "EX3 sem causa/mitigação: 24", "EX4 não empírico: 8"])
arrow(L + BW // 2, 230, L + BW // 2, 310); arrow(L + BW, 385, R, 385)
box(L, 590, BW, 130, ["Textos completos buscados", "n = 28"])
box(R, 590, RW, 130, ["Textos completos", "não recuperados: n = 16"])
arrow(L + BW // 2, 460, L + BW // 2, 590); arrow(L + BW, 655, R, 655)
box(L, 780, BW, 130, ["Avaliados na leitura completa", "n = 12"])
box(R, 760, RW, 170, ["Excluídos: n = 2", "Sem contexto de CI: 2"])
arrow(L + BW // 2, 720, L + BW // 2, 780); arrow(L + BW, 845, R, 845)
box(L, 1010, BW, 150, ["Estudos incluídos na síntese", "n = 10"], fill="#eef5ea")
arrow(L + BW // 2, 910, L + BW // 2, 1010)
img.save(Path(__file__).with_name("prisma.png"), dpi=(300, 300)); print("ok", img.size)
