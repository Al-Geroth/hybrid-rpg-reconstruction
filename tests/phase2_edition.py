"""Validate the handbook, the two reading paths and compatibility with Phase I.

Run on a Git checkout containing the pinned Phase I commit. No network is used.
"""
import json
import math
import re
import subprocess
from html.parser import HTMLParser
from pathlib import Path

from check_publication import check

ROOT = Path(__file__).resolve().parents[1]
BASE = "6fbd40e1bb4718b0ccd5b6cf26e9524e3fd94946"
NEW = {
    "handbook", "sheets", "characters", "builder", "playground", "atlas", "session",
    "configurations", "adaptation", "replay", "reference",
}


class Markup(HTMLParser):
    def __init__(self, text):
        super().__init__()
        self.ids = []
        self.destinations = []
        self.words = []
        self.open = []
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        d = dict(attrs)
        if d.get("id"):
            self.ids.append(d["id"])
        if d.get("href"):
            self.destinations.append(d["href"])
        if tag in {"script", "style", "details"}:
            self.open.append(tag)

    def handle_endtag(self, tag):
        if self.open and tag == self.open[-1]:
            self.open.pop()

    def handle_data(self, data):
        if not self.open:
            self.words.extend(data.split())


def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT)


def main():
    result = check()
    names = git("ls-tree", "-r", "--name-only", BASE, "docs").decode().splitlines()
    old = [name for name in names if name.endswith(".html")]
    missing = []
    count = 0
    for name in old:
        before = Markup(git("show", BASE + ":" + name).decode("utf-8"))
        after = Markup((ROOT / name).read_text(encoding="utf-8"))
        count += len(before.ids)
        missing.extend((name, key) for key in before.ids if key not in after.ids)
    assert not missing, missing
    original_data = git(
        "diff", BASE, "--", "data/rules.json", "data/segments.json", "data/glossary.json",
        "data/equations.json", "data/contradictions.csv", "data/cross_references.csv",
        "sources/source_manifest.csv", "analysis/mathematics", "analysis/classification",
        "analysis/dependencies", "analysis/playability", "analysis/edition-counts.json",
    )
    assert not original_data, "Unexpected change to a frozen Phase I register"
    for slug in NEW:
        doc = (ROOT / "docs" / (slug + ".html")).read_text(encoding="utf-8")
        assert 'aria-label="Edition contents"' in doc
        assert "Learn and play" in doc and "Research and reference" in doc
    source = (ROOT / "manuscript/phase2/handbook.html").read_text(encoding="utf-8")
    handbook = Markup(source)
    assert 2000 <= len(handbook.words) <= 4000
    assert {"the-game", "a-rating", "scales", "creation", "actions", "opposition", "model"} <= set(handbook.ids)
    rows = re.findall(r'<th scope="row">[^<]+</th>((?:<td>[^<]+</td>){5})', source)
    assert len(rows) == 3
    for row in rows:
        values = [float(s.replace(",", "")) for s in re.findall(r'<td>([^<]+)</td>', row)]
        middle = math.log10(values[2])
        for observed, exponent in zip(values, [middle**.25, middle**.5, middle, middle**2, middle**4]):
            assert abs(observed - 10**exponent) <= .00500001
    print(json.dumps({
        "phase1_tree_files_before_html_filter": len(names), "phase1_pages_after_filter": len(old),
        "phase1_html_ids": count, "unmatched_legacy_fragments": missing,
        "phase2_pages": len(NEW), "handbook_words_outside_technical_notes": len(handbook.words),
        "scale_table_rows_checked": len(rows), "publication": result,
    }, indent=2))


if __name__ == "__main__":
    main()
