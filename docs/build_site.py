#!/usr/bin/env python3
"""Gera docs/index.html (GitHub Pages) a partir de COMO-USAR.md.

Uso:
    python docs/build_site.py
"""

from __future__ import annotations

from pathlib import Path

import markdown

DOCS = Path(__file__).resolve().parent
ROOT = DOCS.parent
SRC = ROOT / "COMO-USAR.md"
OUT = DOCS / "index.html"
REPO_URL = "https://github.com/ricb86/riffusion-cpu-local"

TEMPLATE = """<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Riffusion Local (CPU) — como usar</title>
<meta name="description" content="Gere música com IA 100% local em CPU, sem CUDA/ROCm: instalação sem sudo, interface em português e desempenho medido.">
<style>
  :root {{ color-scheme: dark; }}
  * {{ box-sizing: border-box; }}
  body {{
    margin: 0;
    background: #12131a;
    color: #e9e9ee;
    font-family: ui-sans-serif, system-ui, -apple-system, "Segoe UI", Roboto, Ubuntu, sans-serif;
    line-height: 1.65;
    -webkit-font-smoothing: antialiased;
  }}
  header {{
    position: sticky; top: 0; z-index: 10;
    display: flex; justify-content: flex-end; gap: 1rem;
    padding: .7rem 1.25rem;
    background: rgba(18, 19, 26, .82);
    border-bottom: 1px solid #23252f;
    backdrop-filter: blur(8px);
  }}
  header a {{ color: #e0a44a; text-decoration: none; font-weight: 600; font-size: .9rem; }}
  header a:hover {{ text-decoration: underline; }}
  main {{ max-width: 880px; margin: 0 auto; padding: 2.25rem 1.25rem 4rem; }}
  h1 {{ font-size: 2rem; line-height: 1.2; margin: 0 0 1rem; letter-spacing: -.02em; }}
  h2 {{ font-size: 1.35rem; margin: 2.25rem 0 .75rem; padding-top: .5rem; border-top: 1px solid #23252f; }}
  h3 {{ font-size: 1.08rem; margin: 1.5rem 0 .5rem; }}
  p, li {{ color: #d7d7de; }}
  a {{ color: #e0a44a; }}
  strong {{ color: #fff; }}
  figure {{ margin: 1.5rem 0 2rem; }}
  img {{ max-width: 100%; height: auto; border-radius: 12px; border: 1px solid #2a2d3a; display: block; }}
  code {{
    background: #1c1e27; border: 1px solid #2a2d3a; border-radius: 5px;
    padding: .12em .38em; font-size: .88em;
    font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  }}
  pre {{ background: #1c1e27; border: 1px solid #2a2d3a; border-radius: 10px; padding: 1rem 1.1rem; overflow-x: auto; }}
  pre code {{ background: none; border: 0; padding: 0; font-size: .86rem; line-height: 1.55; }}
  blockquote {{
    margin: 1.25rem 0; padding: .6rem 1rem; color: #c9c9d1;
    background: #181a23; border-left: 3px solid #e0a44a; border-radius: 0 8px 8px 0;
  }}
  table {{ width: 100%; border-collapse: collapse; margin: 1.25rem 0; font-size: .93rem; display: block; overflow-x: auto; }}
  th, td {{ border: 1px solid #2a2d3a; padding: .55rem .7rem; text-align: left; vertical-align: top; }}
  th {{ background: #1c1e27; color: #fff; }}
  hr {{ border: 0; border-top: 1px solid #23252f; margin: 2rem 0; }}
  footer {{ border-top: 1px solid #23252f; padding: 2rem 1.25rem; text-align: center; color: #8b8d99; font-size: .85rem; }}
  footer a {{ color: #b9bac4; }}
  @media (max-width: 600px) {{
    main {{ padding-top: 1.5rem; }}
    h1 {{ font-size: 1.6rem; }}
  }}
</style>
</head>
<body>
<header>
  <a href="{repo}">Repositório no GitHub ↗</a>
</header>
<main>
<article class="markdown-body">
{body}
</article>
</main>
<footer>
  Baseado em <a href="https://github.com/riffusion/riffusion-hobby">riffusion/riffusion-hobby</a> (MIT) ·
  <a href="{repo}">código-fonte</a>
</footer>
</body>
</html>
"""


def build() -> Path:
    body = markdown.markdown(
        SRC.read_text(encoding="utf-8"),
        extensions=["fenced_code", "tables", "toc", "sane_lists"],
    )
    body = body.replace(
        "</h1>",
        '</h1>\n<figure><img src="screenshot.png" alt="Interface do Riffusion Local"></figure>',
        1,
    )
    OUT.write_text(TEMPLATE.format(body=body, repo=REPO_URL), encoding="utf-8")
    return OUT


if __name__ == "__main__":
    out = build()
    print(f"gerado {out} ({out.stat().st_size // 1024} KB)")
