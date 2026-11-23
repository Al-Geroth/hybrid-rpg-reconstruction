"""Locate mathematical passages without reprinting their text. Requires the cached primary witness."""
import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import re

import corpus
from math_check import csv_string


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "analysis/mathematics"

# These are direct, individually read evidence locations, rather than a join
# to every segment under a cited rule. Several records can share one location.
DIRECT = {
    "cubic-mass": "142-a", "clone-alternatives": "128-a 128-b 128-c",
    "factorial-strength": "78-a", "engine-hull": "132-a", "mixed-base-flight": "178-a",
    "version-dating": "0-a", "creation-total": "107-b", "successive-advantages": "123-b",
    "ordered-multiplier": "46-a", "fictional-defense": "183-b", "astral-time": "170-a",
    "warp-range": "130-a", "size-proportion": "37-a", "cyborg-calibration": "114-a",
    "warp-fuel": "155-a 158-a", "workshop-size": "77-a",
    "class-step": "front-006 3-a 45-a 46-a 161-a", "class-inverse": "45-a 188-b",
    "iterated-scale": "45-a 161-a 200-a", "opposite-operations": "3-a 183-a",
    "lifespan-years": "6-a", "ambs": "8-a 49-a", "tcp-linear": "8-a 122-a",
    "tcp-log": "8-a 122-a", "c0-psyche": "5-b", "brute-strength": "5-a 40-a 107-c",
    "martial-grade": "2-a", "pool-size": "17-a 35-a", "roll-high": "front-004 35-a",
    "roll-low": "188-b", "recast-rating": "45-b", "letters": "55-a 55-b 58-a",
    "c0-immortality": "31-a", "clone-ratio": "18-a", "soul-comparison": "34-a",
    "running-speed": "39-a 63-a", "mutant-movement": "64-a", "phasing": "53-a",
    "ghost-reading": "27-a 72-a", "teleport-distance": "23-a", "fictional-warp": "30-a",
    "time-travel-rating": "22-a 62-a", "mutant-damage": "146-a",
    "one-use-damage": "14-a 73-a 118-a", "ideal-allocation": "79-a",
    "minimum-advantage": "141-a", "work-time": "96-b", "fictional-return": "87-b",
    "grade-load": "89-a 164-a", "fictional-salary": "202-a",
    "technology-level": "8-a 145-a", "appearance": "124-a 197-a",
    "planet-calibration": "25-a", "infinity-notation": "200-a",
}

# These segments contain numerical mappings, changes or ratios in prose that
# may elude an equals-sign search. Include them for retrieval, even if only a
# single comparison is present.
VERBAL = set("""front-004 front-019 front-021 front-023 front-039 front-055
rule-23-b rule-45-b rule-47-a rule-52-a rule-79-a rule-149-a rule-150-a
rule-179-a rule-181-d rule-182-a rule-185-a rule-198-a rule-203-b""".split())
FORMULA = re.compile(r"=|\^|(?:log10|ln)\s*\(|\d+\s*[*/×]\s*\d+|\d+\s*:\s*\d+", re.I)


def duplicates(keys):
    return sorted(k for k, n in Counter(keys).items() if n > 1)


def build():
    data = ROOT / "data"
    segments = json.loads((data/"segments.json").read_text(encoding="utf8"))
    registry = json.loads((data/"equations.json").read_text(encoding="utf8"))
    seen_ids = [r["id"] for r in segments]
    registry_ids = [r["id"] for r in registry]
    raw = corpus.CACHE.read_bytes()
    if hashlib.sha256(raw).hexdigest() != corpus.SHA:
        raise ValueError("Unrecognized witness")
    _, blocks = corpus.normalized_blocks(raw)
    if blocks[-1] != "Membre de ClickFR, Reseau francophone Paie-Par-Click":
        raise ValueError("Unexpected footer")
    flat = "\n".join(blocks[:-1])
    evidence = defaultdict(list)
    pairs = []
    for family, codes in DIRECT.items():
        for code in codes.split():
            seg = code if code.startswith("front-") else "rule-"+code
            evidence[seg].append(family)
            pairs.append((family, seg))
    broken = sorted(set(evidence) - set(seen_ids))
    unknown = sorted(set(DIRECT) ^ set(registry_ids))
    if broken or unknown or duplicates(pairs) or duplicates(seen_ids) or duplicates(registry_ids):
        raise ValueError(f"Locator join mismatch: segments {broken}, registry {unknown}")
    if VERBAL-set(seen_ids):
        raise ValueError("Unmatched editorial verbal-relationship locators")
    rows = []
    for s in segments:
        k = s["id"]
        passage = flat[s["start_offset"]:s["end_offset"]]
        cues = []
        if FORMULA.search(passage):
            cues.append("notation")
        if "Mathematical model" in [s["primary_category"], *s["secondary_categories"]]:
            cues.append("catalogue math tag")
        if k in VERBAL:
            cues.append("verbal rating or relation")
        if k in evidence:
            cues.append("direct registry evidence")
        rows.append({
            "segment_id": k, "rule": s["original_id"] or "", "order": s["order"],
            "title": s["title"], "start_offset": s["start_offset"], "end_offset": s["end_offset"],
            "candidate": int(bool(cues)), "basis": " | ".join(cues),
            "detailed_records": " | ".join(evidence.get(k, [])),
            "scope": ("quantitative recipe passage outside the game" if k=="front-026" else
                      "direct evidence for a registered reading" if k in evidence else
                      "locator only" if cues else "no selected cue"),
        })
    candidates = [r for r in rows if r["candidate"]]
    detailed = [r for r in candidates if r["detailed_records"]]
    summary = {
        "unit": "An editorial segment, not an equation. A segment can contain multiple or repeated expressions.",
        "source_blocks_before_ad_footer_filter": len(blocks),
        "source_blocks_after_ad_footer_filter": len(blocks)-1,
        "all_segments": len(rows), "all_segments_after_left_join": len(rows),
        "candidate_filter": [len(rows), len(candidates)],
        "registered_direct_evidence_filter": [len(candidates),len(detailed)],
        "candidate_segments_with_locator_only": len(candidates)-len(detailed),
        "no_selected_cue": len(rows)-len(candidates),
        "registry_records_linked": len(registry_ids), "equation_segment_pairs_before_join": len(pairs),
        "equation_segment_pairs_after_join": len(pairs), "duplicate_segment_ids": duplicates(seen_ids),
        "duplicate_registry_ids": duplicates(registry_ids), "duplicate_pairs": duplicates(pairs),
        "unmatched_equation_keys": unknown, "unmatched_segment_keys": broken,
        "unmatched_segments_without_direct_register_pair": sorted(set(seen_ids)-set(evidence)),
        "limits": "The candidate search includes marks in non-gameplay passages, numerical comparisons and references to calculations. Direct evidence means a checked segment supports at least one detailed registry reading. Neither count equals a complete number of algebraically distinct equations.",
    }
    return (csv_string(rows[0], rows), json.dumps(summary,ensure_ascii=False,indent=2)+"\n"), summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    outputs, summary = build()
    for name, content in zip(("equation_locators.csv","locator_audit.json"), outputs):
        path = OUT/name
        if args.write:
            path.write_bytes(content.encode("utf8"))
        elif path.read_text(encoding="utf8") != content:
            raise SystemExit(f"Stale locator output: {name}")
    print(f"Candidate filter {summary['candidate_filter']}. Detailed evidence filter "
          f"{summary['registered_direct_evidence_filter']}. {summary['registry_records_linked']} "
          f"registry records. {summary['equation_segment_pairs_after_join']} matched pairs. "
          "Duplicate and broken keys: zero. See locator_audit.json for left-only segments.")


if __name__ == "__main__":
    main()
