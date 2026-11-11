#!/usr/bin/env python3
"""Build obsidian-tutorial.pdf from obsidian-tutorial.md.

Images are resized to 660px wide before embedding: LibreOffice's HTML
import lays images out at ~96dpi, so wider files overflow the A4 page.
Supports fenced code blocks and inline `code` in addition to the
tutorial pipeline's headings/tables/lists/images.
"""
import re
import sys
from pathlib import Path

from PIL import Image

SRC = Path(__file__).with_name("obsidian-tutorial.md")
OUT_HTML = Path(__file__).with_name("obsidian-tutorial.html")
MAX_W = 660


def resized(rel_src):
    """Return the path (relative to the HTML file) of a print-sized copy."""
    src = Path(__file__).parent / rel_src
    dest_dir = src.parent / "pdf"
    dest_dir.mkdir(exist_ok=True)
    dest = dest_dir / src.name
    if not dest.exists() or src.stat().st_mtime > dest.stat().st_mtime:
        im = Image.open(src)
        if im.width > MAX_W:
            h = round(im.height * MAX_W / im.width)
            im = im.resize((MAX_W, h), Image.LANCZOS)
        im.save(dest)
    return str(dest.relative_to(Path(__file__).parent))


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def inline(s):
    # split on backticks: odd parts are inline code (bold NOT applied inside)
    parts = s.split("`")
    out = []
    for i, p in enumerate(parts):
        if i % 2 == 1:
            out.append("<code>" + esc(p) + "</code>")
        else:
            e = esc(p)
            e = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", e)
            out.append(e)
    return "".join(out)


def parse_table(lines, i):
    def cells(row):
        row = row.strip()
        if row.startswith("|"):
            row = row[1:]
        if row.endswith("|"):
            row = row[:-1]
        return [c.strip() for c in row.split("|")]

    header = cells(lines[i])
    rows = []
    j = i + 2
    while j < len(lines) and lines[j].strip().startswith("|"):
        rows.append(cells(lines[j]))
        j += 1
    html = ["<table><thead><tr>"]
    html += ["<th>" + inline(c) + "</th>" for c in header]
    html += ["</tr></thead><tbody>"]
    for r in rows:
        html.append("<tr>" + "".join("<td>" + inline(c) + "</td>" for c in r) + "</tr>")
    html.append("</tbody></table>")
    return "".join(html), j


def md_to_html(text):
    lines = text.split("\n")
    out = []
    i = 0
    while i < len(lines):
        line = lines[i]
        s = line.strip()
        if not s:
            i += 1
            continue
        if s.startswith("```"):
            # fenced code block
            buf = []
            i += 1
            while i < len(lines) and not lines[i].strip().startswith("```"):
                buf.append(lines[i])
                i += 1
            i += 1  # skip closing fence
            out.append("<pre><code>" + esc("\n".join(buf)) + "</code></pre>")
            continue
        if s.startswith("|") and i + 1 < len(lines) and re.match(r"^\|?[\s:|-]+\|?$", lines[i + 1].strip()) and "-" in lines[i + 1]:
            table_html, i = parse_table(lines, i)
            out.append(table_html)
            continue
        if s.startswith("### "):
            out.append("<h3>" + inline(s[4:]) + "</h3>")
        elif s.startswith("## "):
            out.append("<h2>" + inline(s[3:]) + "</h2>")
        elif s.startswith("# "):
            out.append("<h1>" + inline(s[2:]) + "</h1>")
        elif s.startswith("!["):
            run = []
            while i < len(lines):
                s2 = lines[i].strip()
                if not s2:
                    i += 1
                    continue
                m2 = re.match(r"!\[.*?\]\((.+?)\)", s2)
                if not m2:
                    break
                run.append(m2.group(1))
                i += 1
            for src in run:
                cls = "fig cover" if "cover.png" in src else "fig"
                out.append('<p class="' + cls + '"><img src="' + resized(src) + '"/></p>')
            continue
        elif s == "---":
            out.append("<hr/>")
        elif s.startswith("- "):
            items = []
            while i < len(lines) and lines[i].strip().startswith("- "):
                items.append("<li>" + inline(lines[i].strip()[2:]) + "</li>")
                i += 1
            out.append("<ul>" + "".join(items) + "</ul>")
            continue
        elif re.match(r"^\d+\.\s", s):
            items = []
            while i < len(lines) and re.match(r"^\d+\.\s", lines[i].strip()):
                items.append("<li>" + inline(re.sub(r"^\d+\.\s", "", lines[i].strip())) + "</li>")
                i += 1
            out.append("<ol>" + "".join(items) + "</ol>")
            continue
        else:
            out.append("<p>" + inline(s) + "</p>")
        i += 1
    return "\n".join(out)


CSS = """
@page { size: A4; margin: 18mm 16mm; }
body { font-family: 'Noto Serif CJK SC', 'Noto Sans CJK SC', serif; font-size: 11pt; line-height: 1.7; color: #222; }
h1 { font-size: 20pt; line-height: 1.4; margin: 0 0 4pt 0; }
h2 { font-size: 14pt; margin: 16pt 0 6pt 0; padding-bottom: 3pt; border-bottom: 1.5pt solid #333; page-break-after: avoid; }
h3 { font-size: 12pt; margin: 12pt 0 4pt 0; page-break-after: avoid; }
p { margin: 4pt 0; }
ul, ol { margin: 4pt 0 4pt 16pt; padding: 0; }
li { margin: 2pt 0; }
table { border-collapse: collapse; width: 100%; margin: 8pt 0; font-size: 9.5pt; line-height: 1.5; page-break-inside: avoid; }
th, td { border: 0.7pt solid #999; padding: 4pt 5pt; text-align: left; }
th { background: #eee; }
hr { border: none; border-top: 0.7pt solid #999; margin: 12pt 0; }
strong { font-weight: bold; }
code { font-family: 'Noto Sans Mono CJK SC', monospace; font-size: 9.5pt; background: #f2f2f2; padding: 0 3pt; }
pre { background: #f2f2f2; padding: 8pt 10pt; font-size: 9.5pt; line-height: 1.5; page-break-inside: avoid; white-space: pre-wrap; }
pre code { background: none; padding: 0; }
p.fig { text-align: center; margin: 8pt 0; page-break-inside: avoid; }
p.fig img { width: 96%; }
p.fig.cover { page-break-after: always; margin: 0; }
p.fig.cover img { width: 100%; }
"""

def main():
    text = SRC.read_text(encoding="utf-8")
    body = md_to_html(text)
    html = f"""<!DOCTYPE html><html lang="zh-CN"><head><meta charset="utf-8"/>
<style>{CSS}</style></head><body>{body}</body></html>"""
    OUT_HTML.write_text(html, encoding="utf-8")
    print(f"wrote {OUT_HTML}")

if __name__ == "__main__":
    main()
