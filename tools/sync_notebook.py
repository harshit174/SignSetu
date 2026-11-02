"""Keep SignSetu.ipynb the single source of truth for the generated files.

The notebook writes app.py, isl_core.py, isl_lang.py and .streamlit/config.toml with `%%writefile` cells.
When those files are edited directly, run this script (from the repo root or anywhere) to copy them back
into their notebook cells, so a later Run All regenerates exactly the same code:

    python tools/sync_notebook.py          # update the notebook in place (idempotent)
    python tools/sync_notebook.py --check  # exit 1 if the notebook is out of sync (for CI / pre-commit)

The tools/ folder holds developer utilities only; nothing here is imported by the app. Standard library only.
"""
import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
NB = ROOT / "SignSetu.ipynb"
FILES = ["isl_core.py", "isl_lang.py", "app.py", ".streamlit/config.toml"]
LANG_MD = (
    "### 3b · Language layer (`isl_lang.py`)\n"
    "ISL is topic-comment and often question-final (\"ME DOCTOR WHERE\" = \"Where is the doctor?\"). This module holds:\n"
    "* the offline **gloss → sentence engine** that turns the recognised sign sequence into natural English and Hindi,\n"
    "* the real-life **situations** (Everyday, Hospital, Emergency, Bank & Office, Classroom, Shopping): focused vocabularies, "
    "scripted demos and quick phrases,\n"
    "* the **encouragement engine** for Learn & Practice (levels, praise, landmark-based coaching tips).\n"
    "An optional Claude polish step is used only when `ANTHROPIC_API_KEY` is set.")


def to_source(text):
    """Notebook source list: one string per line, each keeping its newline (last line without one)."""
    lines = text.splitlines(keepends=True)
    if lines and lines[-1].endswith("\n"):
        lines[-1] = lines[-1][:-1]
        if lines[-1] == "":
            lines.pop()
    return lines


def writefile_target(cell):
    if cell.get("cell_type") != "code":
        return None
    src = "".join(cell.get("source", []))
    first = src.split("\n", 1)[0].strip()
    return first[len("%%writefile"):].strip() if first.startswith("%%writefile") else None


def new_id(seed):
    return hashlib.sha1(seed.encode()).hexdigest()[:8]


def sync(nb):
    cells = nb["cells"]
    targets = {writefile_target(c): i for i, c in enumerate(cells) if writefile_target(c)}
    if "isl_lang.py" not in targets and "isl_core.py" in targets:
        at = targets["isl_core.py"] + 1
        cells[at:at] = [
            {"cell_type": "markdown", "id": new_id("isl_lang-md"), "metadata": {}, "source": to_source(LANG_MD)},
            {"cell_type": "code", "execution_count": None, "id": new_id("isl_lang-code"), "metadata": {}, "outputs": [],
             "source": ["%%writefile isl_lang.py\n"]},
        ]
        targets = {writefile_target(c): i for i, c in enumerate(cells) if writefile_target(c)}
    for rel in FILES:
        path = ROOT / rel
        if rel not in targets:
            raise SystemExit(f"no %%writefile {rel} cell in {NB.name}")
        if not path.exists():
            raise SystemExit(f"missing {rel}")
        content = path.read_text(encoding="utf-8")
        cell = cells[targets[rel]]
        want = to_source(f"%%writefile {rel}\n" + content)
        if cell["source"] != want:
            cell["source"] = want
            cell["outputs"] = []
            cell["execution_count"] = None
    return nb


def dump(nb):
    return json.dumps(nb, indent=1, ensure_ascii=False) + "\n"


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--check", action="store_true", help="exit 1 if the notebook is out of sync; do not write")
    a = ap.parse_args()
    before = NB.read_text(encoding="utf-8")
    after = dump(sync(json.loads(before)))
    if a.check:
        if after != before:
            print(f"{NB.name} is out of sync with {', '.join(FILES)} - run: python tools/sync_notebook.py")
            sys.exit(1)
        print(f"{NB.name} is in sync")
        return
    if after != before:
        NB.write_text(after, encoding="utf-8")
        print(f"updated {NB.name}")
    else:
        print(f"{NB.name} already in sync")


if __name__ == "__main__":
    main()
