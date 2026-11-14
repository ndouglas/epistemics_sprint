"""Check the report's tagged numbers against results/claims.json, then render it.

    uv run python -m sprint.build_report

Write a number as [claim.id=value]. The build stops if a tag is unknown or its
value differs from the claims file; otherwise it replaces each tag with its
value. Everything after `<!-- appendices -->` is left out of the page count.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TAG = re.compile(r"\[([a-zA-Z0-9_.\-]+)=([^\]]+)\]")
OPTS = ["-V", "geometry:margin=1in", "-V", "papersize=letter", "-V", "fontsize=11pt", "--pdf-engine=xelatex"]


def pages(pdf: Path) -> int:
    info = subprocess.run(["pdfinfo", str(pdf)], capture_output=True, text=True, check=True).stdout
    return int(re.search(r"Pages:\s+(\d+)", info).group(1))


def main() -> int:
    src, out = ROOT / "report" / "report.md", ROOT / "report" / "build"
    out.mkdir(exist_ok=True)
    claims = json.loads((ROOT / "results" / "claims.json").read_text())
    text = src.read_text()
    bad = [f"{k}: report says {v!r}, data says {claims.get(k, 'NO SUCH CLAIM')!r}"
           for k, v in TAG.findall(text) if claims.get(k) != v]
    if bad:
        print("\n".join(bad))
        return 1
    md = TAG.sub(lambda m: m.group(2), text)
    body = md.split("<!-- appendices -->")[0]
    (out / "report.md").write_text(md)
    (out / "body.md").write_text(body)
    style = (ROOT / "report" / "apart.tex").read_text().replace("../report/fonts/", str(ROOT / "report" / "fonts") + "/")
    (out / "style.tex").write_text(style)
    for name in ("report", "body"):
        subprocess.run(["pandoc", str(out / f"{name}.md"), "-o", str(out / f"{name}.pdf"), *OPTS, "-H", str(out / "style.tex"),
                        "--resource-path", str(ROOT / "report")], check=True)
    subprocess.run(["pandoc", str(out / "report.md"), "-o", str(out / "report.docx"), "--reference-doc",
                    str(ROOT / "report" / "apart-reference.docx"), "--resource-path", str(ROOT / "report")], check=True)
    words = len(re.sub(r"<!--.*?-->", "", body, flags=re.S).split())
    print(f"{len(TAG.findall(text))} tagged numbers check out. Main body: {pages(out / 'body.pdf')} pages "
          f"(limit 8), ~{words} words; full PDF: {pages(out / 'report.pdf')} pages -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
