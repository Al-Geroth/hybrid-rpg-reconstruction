"""Verify edition-specific boundaries and reference disambiguation against private bytes."""
import csv
import json
from collections import Counter

import corpus


def verify():
    def load(name):
        return json.loads((corpus.DATA / name).read_text(encoding="utf8"))
    rules, segments = load("rules.json"), load("segments.json")
    blocks = corpus.normalized_blocks(corpus.CACHE.read_bytes())[1][:-1]
    flat = "\n".join(blocks)
    assert [r["original_id"] for r in rules] == list(map(str,range(204)))
    assert rules[109]["original_heading"] == "RULE 109"
    assert rules[151]["end_block"] == rules[151]["start_block"] + 1
    assert len({s["id"] for s in segments}) == len(segments)
    assert segments[0]["start_offset"] == 0 and segments[-1]["end_offset"] == len(flat)
    for a,b in zip(segments,segments[1:]):
        assert a["end_offset"] == b["start_offset"]
    for s in segments:
        assert s["start_offset"] < s["end_offset"]
        if s["rule_id"]:
            parent = rules[int(s["original_id"])]
            assert parent["id"] == s["rule_id"]
            assert parent["start_block"] <= s["start_block"] <= s["end_block"] <= parent["end_block"]
    with (corpus.DATA / "cross_references.csv").open(encoding="utf8",newline="") as f:
        refs=list(csv.DictReader(f))
    assert all(r["resolution"]=="resolved" for r in refs)
    assert all(r["target_rule_id"]==rules[int(r["target_original_id"])]["id"] for r in refs)
    context = Counter((r["source_original_id"],r["target_original_id"]) for r in refs if r["notation"]=="context")
    assert context == Counter({(str(n),t):1 for n,l in corpus.EXTRA_REFS.items() for _,t in l})
    ranges = [int(r["target_original_id"]) for r in refs if r["notation"]=="range"]
    assert ranges == list(range(131,140))
    assert not any(r["source_original_id"]=="140" and r["target_original_id"]=="2" for r in refs)
    assert not any(r["source_original_id"]=="130" and r["target_original_id"]=="10" and "Warp" in flat[int(r["offset"]):int(r["offset"])+6] for r in refs)
    for n, num in [(84,17),(17,188),(188,17),(94,135),(111,74)]:
        assert any(r["source_original_id"]==str(n) and r["target_original_id"]==str(num) for r in refs)
    print(f"Verified {len(rules)} headings, {len(segments)} contiguous annotation spans, and {len(refs)} numerical reference rows.")
    print("Verified hashless and parenthetical shorthand, genuine self-reference, local equation numbering, warp labels and the range in #177.")


if __name__ == "__main__":
    verify()
