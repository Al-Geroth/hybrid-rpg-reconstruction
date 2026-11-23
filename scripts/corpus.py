"""Extract a pinned HTML witness and align original editorial annotations to it."""

import argparse
import bisect
import csv
import hashlib
import html
import json
import re
import urllib.request
from collections import Counter, defaultdict
from pathlib import Path

from corpus_forms import build as build_forms


ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / "sources/raw/v030.html"
URL = "https://web.archive.org/web/20030213163300id_/http://perso.wanadoo.fr/philippe.tromeur/hybrid.htm"
SHA = "b71d98a0582301d4cb2f83efbb193bfe6c71fa6ccb56e068a4fc14ae553c73ec"
ANALYSIS = ROOT / "analysis/classification"
DATA = ROOT / "data"
EDITION = "0.30"
HEADING = re.compile(r"^(RULE\s*#?\s*(\d+))\s*:", re.I)
CATEGORIES = dict(core="Core mechanic", derived="Derived mechanic", character="Character creation",
                  action="Action resolution", combat="Combat", powers="Powers", math="Mathematical model",
                  physical="Physical simulation", world="Game-world assumptions", example="Worked example",
                  external="External RPG reference", pop="Pop-culture reference", design="Design commentary",
                  phil="Philosophical commentary", personal="Personal commentary",
                  prejudice="Prejudicial commentary", pseudo="Pseudoscientific claim",
                  admin="Administrative material", unresolved="Unresolved material")
STATUS = dict(E="Executable", P="Partially executable", A="Ambiguous", X="Non-executable", N="Non-mechanical")
CONFIDENCE = dict(H="High", M="Medium", L="Low")

# A dependency is separately interpreted. Explicit cross-references are indexed even
# when they merely recommend more reading or appear to point to the wrong subject.
DEPENDENCIES = {
    3: [45], 6: [3, 45], 11: [3], 16: [7], 22: [45], 30: [10], 36: [18, 34],
    41: [22], 44: [43], 46: [45], 50: [49], 51: [37], 56: [7], 62: [22],
    63: [30], 66: [40], 68: [48, 53], 69: [49, 34], 84: [82, 17], 91: [22, 90],
    95: [10, 30], 96: [18, 34], 98: [7, 16, 97], 101: [97], 102: [93],
    107: [3, 45], 109: [18], 123: [49], 129: [128], 133: [130], 139: [45],
    141: [3], 143: [3], 152: [134], 156: [155], 157: [155], 158: [155], 161: [45],
    165: [3, 25], 168: [167], 169: [162, 88, 116, 130, 132, 135, 158],
    171: [170], 174: [34], 179: [158, 16], 183: [3], 188: [45], 191: [7, 8],
    192: [10, 30], 194: [45], 203: [34, 198, 164],
}

RPG = {
    "HERO / Champions": r"\b(?:HERO\s*(?:rpg|5th|system)|CHAMPIONS)\b",
    "GURPS": r"GURPS", "D&D": r"D&D|Dungeons & Dragons", "d20 Modern": r"d20 Modern",
    "d20": r"\bd20\b", "Marvel SAGA": r"MU SAGA|Marvel SAGA",
    "Marvel Super Heroes (TSR)": r"MU TSR|TSR (?:MU|MARVEL)", "Nobilis": r"Nobilis",
    "Synnibarr": r"Synnibarr", "Aberrant": r"Aberrant", "Rifts": r"\bRIFTS\b",
    "Mage: The Ascension": r"Mage.{1,4}(?:the\s*)?Ascension",
    "BESM": r"\bBESM\b", "Mutants & Masterminds": r"Mutants\s*(?:&|and)\s*Masterminds",
    "Fuzion": r"Fuzion", "Dragon Ball Z": r"Dragon\s*ball.?Z",
}
CONCEPTS = {
    "Psyche": r"psyche", "DP": r"(?<![a-z])DP(?![a-z])|default psyche",
    "PL": r"(?<![a-z])PL(?![a-z])|power level", "LS": r"(?<![a-z])LS(?![a-z])|life.span",
    **{c: rf"(?<![a-z]){c}(?![a-z0-9])" for c in ["CA","C0","C1","C2","C3","C4","IQ","AMBS","COM","STR","TL","DCV","MAG","PK","DEF","BOD"]},
    "advantage": r"\badvantage", "limitation": r"\blimitation", "cloning": r"\bclon",
    "soul comparison": r"soul equation|binary equation", "warp": r"\bwarp",
    "dice": r"\bdice\b|\bd\d+\b|\dd\d+", "common logarithm": r"log10",
    "natural logarithm": r"\bLN\b", "factorial": r"\bfactorial",
}
NOTES = {
    0: "The author's stated total of 203 differs from the 204 numbered headings when zero is counted.",
    17: "The opening fourth example and rule 188 explicitly identify a conflict.",
    51: "Rule 37 concerns a proportion. Rule 38 more explicitly names shape-changing.",
    84: "The source cites 17 for cloning. Rule 17 concerns a dice pool, while 18 explicitly defines a clone count.",
    88: "These numerical assignments are fictional character conventions.",
    96: "The source identifies a conflict between its simple ratio and its soul comparison.",
    109: "Printed as RULE 109 without a hash mark.",
    135: "The author notes disagreement with rule 25 and invokes rule 136 as a qualification.",
    142: "At one metre, the stated 3.28 feet cubed gives about 35.3 pounds, against a table value of 282.30.",
    145: "Neither the written inverse nor the proposed special case resolves the inconsistency.",
    151: "The entry continues after a paragraph break.",
    157: "Rule 10 is cited as conflicting with the spaceship threshold.",
    163: "The author's retrospective dating is internal testimony.",
    188: "The source expressly identifies rule 17 as a conflicting route.",
    200: "An unbounded exponent cannot yield the stated finite value under the usual limiting interpretation.",
}


def fetch():
    if not CACHE.is_file():
        with urllib.request.urlopen(URL, timeout=90) as response:
            payload = response.read()
        if hashlib.sha256(payload).hexdigest() != SHA:
            raise ValueError("Archive returned different bytes. Investigate before adding a witness.")
        CACHE.parent.mkdir(parents=True, exist_ok=True)
        with CACHE.open("xb") as f:
            f.write(payload)
    return CACHE.read_bytes()


def normalized_blocks(raw):
    # Text normalization is edition-specific, intentionally independent of browser display.
    # CP1252 agrees with HTML's decoding of the site's declared ISO-8859-1 encoding.
    source = raw.decode("cp1252")
    source = re.sub(r"(?is)<(script|iframe)\b.*?</\1>", "", source)
    source = re.sub(r"(?i)</?(?:p|h[12]|tr|li|br|center|ol|table)\b[^>]*>", "\n", source)
    source = re.sub(r"<[^>]*>", "", source)
    lines = html.unescape(source).splitlines()
    return lines, [" ".join(line.split()) for line in lines if line.strip()]


def load_annotations(path):
    lines = path.read_text(encoding="utf8").splitlines()
    records = []
    for line in lines:
        if not line or line.startswith("#"):
            continue
        loc, categories, grading, title, paraphrase = line.split("|")
        label, _, anchor = loc.partition("@")
        records.append((label, anchor, [CATEGORIES[c] for c in categories.split()], grading, title, paraphrase))
    return lines, records


def refs(text):
    # Match explicit list starters and local tails; a bare # can mean "number",
    # so unqualified numerical markers require editorial confirmation below.
    starter = re.compile(r"(?i)(?:rules?|\brule\(s\)|equations\s+are)\s*#\s*(\d+)")
    tail = re.compile(r"(?i)\s*(?:,\s*(?:and|or|&)?|&|and|or)\s*#\s*(\d+)")
    reach = re.compile(r"(?i)\s*(?:through|to|-)\s*#\s*(\d+)")
    found = []
    for token in starter.finditer(text):
        start = int(token[1])
        found.append((token.start(), str(start), "named"))
        cursor = token.end()
        while m := tail.match(text, cursor):
            found.append((m.start(), m[1], "list"))
            cursor = m.end()
        if m := reach.match(text, cursor):
            # One attested interval (rule 177); retain range expansion provenance.
            for n in range(start + 1, int(m[1]) + 1):
                found.append((m.start(), str(n), "range"))
    return found


def export_json(path, data):
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fetch", action="store_true", help="Fetch privately only if the pinned raw file is absent.")
    args = parser.parse_args()
    raw = fetch() if args.fetch else CACHE.read_bytes()
    if hashlib.sha256(raw).hexdigest() != SHA:
        raise ValueError("Unexpected witness digest")
    raw_lines, all_blocks = normalized_blocks(raw)
    if all_blocks[-1] != "Membre de ClickFR, Reseau francophone Paie-Par-Click":
        raise ValueError("Unexpected host footer")
    blocks = all_blocks[:-1]
    flat = "\n".join(blocks)
    offsets = []
    cursor = 0
    originals = defaultdict(list)
    rules = []
    for i, block in enumerate(blocks):
        offsets.append(cursor)
        cursor += len(block) + 1
        if m := HEADING.match(block):
            n = m[2]
            ident = "rule-" + n
            if originals[n]:
                ident += "-occurrence-" + str(len(originals[n]) + 1)
            row = dict(id=ident, original_id=n, original_heading=m[1], edition=EDITION, order=len(rules)+1,
                       start_block=i, end_block=i)
            originals[n].append(row)
            rules.append(row)
    for i, rule in enumerate(rules):
        rule["end_block"] = rules[i+1]["start_block"]-1 if i+1 < len(rules) else len(blocks)-1
    front_lines, front = load_annotations(ANALYSIS / "front.txt")
    body_lines, body = load_annotations(ANALYSIS / "numbered.txt")
    annotated = []
    unresolved = []
    for label, anchor, cats, grade, title, paraphrase in front+body:
        if label.startswith("f"):
            b = int(label[1:])
            section = blocks[b]
            parent = None
        else:
            if len(originals[label]) != 1:
                raise ValueError(f"Annotation target must resolve to one occurrence: {label}")
            rule = originals[label][0]
            b = rule["start_block"]
            section = "\n".join(blocks[b:rule["end_block"]+1])
            parent = rule
        cut = int(anchor) if anchor.isdigit() else section.find(anchor)
        if not 0 <= cut < len(section):
            unresolved.append((label, cut))
            continue
        start = offsets[b] + cut
        annotated.append((start, parent, cats, grade, title, paraphrase))
    if unresolved:
        raise ValueError(f"Anchors absent: {unresolved}")
    annotated.sort(key=lambda row:row[0])
    if len({row[0] for row in annotated}) != len(annotated) or annotated[0][0] != 0:
        raise ValueError("Duplicate cut or gap before first segment")
    seen = Counter()
    segments = []
    xrefs = []
    numeric_issues = defaultdict(list)
    issues_path = DATA / "contradictions.csv"
    with issues_path.open(encoding="utf-8-sig", newline="") as f:
        issue_rows = list(csv.DictReader(f))
    for issue in issue_rows:
        for ref in issue["references"].split("|"):
            if ref.isdigit():
                numeric_issues[ref].append(issue["id"])
    for i, (start, parent, cats, grade, title, paraphrase) in enumerate(annotated):
        end = annotated[i+1][0] if i+1 < len(annotated) else len(flat)
        n = parent["original_id"] if parent else None
        pkey = parent["id"] if parent else None
        seen[pkey] += 1
        ident = (pkey+"-"+chr(96+seen[pkey])) if pkey else f"front-{seen[None]:03d}"
        source = flat[start:end]
        matches = refs(source)
        if parent and seen[pkey] == 1 and HEADING.match(source):
            matches = [r for r in matches if r[0] >= HEADING.match(source).end()]
        # These bare numbers are explicitly introduced as a numbered rule in their local
        # context but fall outside the strict list grammar. Byte-pinned position matching,
        # rather than matching every '# N', avoids fictional stat and page numerals.
        for literal, target in EXTRA_REFS.get(int(n) if n is not None else None, []):
            if literal in source:
                matches.append((source.index(literal), target, "context"))
        matches.sort()
        for pos, target, kind in matches:
            mapped = originals.get(target, [])
            xrefs.append(dict(source_segment_id=ident, source_rule_id=pkey or "",
                              source_original_id=n or "", target_original_id=target,
                              target_rule_id=mapped[0]["id"] if len(mapped)==1 else "",
                              resolution="resolved" if len(mapped)==1 else "absent" if not mapped else "duplicate",
                              notation=kind, offset=start+pos))
        concepts = [name for name,pattern in CONCEPTS.items() if re.search(pattern,source,re.I)]
        games = [name for name,pattern in RPG.items() if re.search(pattern,source,re.I)]
        features = []
        for name, pattern in [
            ("Equation notation", r"=|\bLOG10\s*\(|\^"),
            ("Tabulation or chart mentioned", r"\b(?:table|chart)s?\b"),
            ("Illustration marker", r"(?i)\bexample|for instance|\bsuch as"),
            ("Disclaimer or warning", r"\b(?:disclaimer|warning)\b"),
        ]:
            if re.search(pattern, source, re.I):
                features.append(name)
        if games and "External RPG reference" not in cats:
            cats = cats + ["External RPG reference"]
        if "Worked example" not in cats and re.search(r"(?i)\b(?:for example|e\.g\.)\b",source):
            cats = cats + ["Worked example"]
        relevance = "None" if grade[0]=="N" else "Indirect" if cats[0] in {
            "Physical simulation","Pseudoscientific claim","Prejudicial commentary","Game-world assumptions",
            "Design commentary","Administrative material","External RPG reference"} else "Direct"
        printed = int(n) if parent else None
        deps = DEPENDENCIES.get(printed,[])
        indexed_refs = list(dict.fromkeys(r[1] for r in matches))
        # For subdivided rules keep only locally mentioned dependencies. For a single
        # segment a reviewed dependency can be implicit even without a printed numeral.
        count = len([r for r in annotated if parent and r[1] and r[1]["id"]==pkey])
        deps = [f"Rule {num}" for num in deps if count==1 or str(num) in indexed_refs]
        notes = NOTES.get(printed,"")
        segments.append(dict(id=ident, rule_id=pkey, original_id=n, edition=EDITION, order=i+1,
                             start_block=bisect.bisect_right(offsets,start)-1,
                             end_block=bisect.bisect_right(offsets,end-1)-1, start_offset=start, end_offset=end,
                             title=title, paraphrase=paraphrase, primary_category=cats[0],
                             secondary_categories=cats[1:], relevance=relevance, confidence=CONFIDENCE[grade[1]],
                             executability=STATUS[grade[0]], concepts=concepts, external_systems=games, source_features=features,
                             references=indexed_refs, dependencies=deps, contradictions=numeric_issues.get(n,[]),
                             notes=notes, layer="B" if grade[0] in "PAX" else "A",
                             layer_scope="Editorial paraphrase of an explicit passage" if grade[0] in "EN" else "Editorial reconstruction or assessment of the passage"))
    for r in rules:
        children = [s for s in segments if s["rule_id"] == r["id"]]
        if not children:
            raise ValueError(f"No annotations for {r['id']}")
        r["title"] = children[0]["title"]
        r["segments"] = [s["id"] for s in children]
    expected = set(range(min(map(int,originals)),max(map(int,originals))+1))
    absent = sorted(expected - set(map(int,originals)))
    n_num = sum(bool(s["rule_id"]) for s in segments)
    counts = Counter(s["executability"] for s in segments)
    pairs = Counter((x["source_segment_id"],x["target_original_id"]) for x in xrefs)
    audit = dict(witness_sha256=SHA, numbering=dict(source_claim=203, identified_headings=len(rules),
                 unique_numbers=len(originals), first=rules[0]["original_id"], last=rules[-1]["original_id"],
                 missing_in_observed_span=absent, duplicate_numbers={n:len(rs) for n,rs in originals.items() if len(rs)>1}),
                 filters=[
                    ["nonempty normalized blocks",len(raw_lines),len(all_blocks)],
                    ["exclude host advertising footer",len(all_blocks),len(blocks)],
                    ["heading detection in retained blocks",len(blocks),len(rules)],
                    ["front annotation file excluding comments and empty lines",len(front_lines),len(front)],
                    ["numbered annotation file excluding comments and empty lines",len(body_lines),len(body)],
                    ["numbered segments from all segments",len(segments),n_num],
                    ["unnumbered segments from all segments",len(segments),len(segments)-n_num]],
                 joins={
                    "numbered annotation to heading":{"annotation_rows":len(body),"heading_rows":len(rules),
                       "matched_annotations":n_num,"unmatched_heading_keys":[],"unmatched_annotation_keys":[],
                       "duplicate_heading_keys":[],"repeated_annotation_parent_keys":{k:v for k,v in seen.items() if k and v>1}},
                    "reference occurrence to heading":{"reference_rows":len(xrefs),"heading_rows":len(rules),
                       "matched_rows":sum(x["resolution"]=="resolved" for x in xrefs),
                       "unmatched_target_keys":sorted({x["target_original_id"] for x in xrefs if x["resolution"]!="resolved"}),
                       "unreferenced_heading_keys":sorted(set(originals)-{x["target_original_id"] for x in xrefs},key=int),
                       "duplicate_lookup_keys":[], "repeated_reference_target_keys":{k:v for k,v in Counter(x["target_original_id"] for x in xrefs).items() if v>1},
                       "repeated_segment_target_pairs":{f"{p} → {q}":v for (p,q),v in pairs.items() if v>1}},
                    "contradiction annotations by numbered parent":{"issue_rows":len(issue_rows),
                       "duplicate_issue_ids":[k for k,v in Counter(z["id"] for z in issue_rows).items() if v>1],
                       "unmatched_numbered_keys":sorted(set(numeric_issues)-set(originals)),
                       "non_numeric_reference_literals":sorted({ref for z in issue_rows for ref in z["references"].split("|") if not ref.isdigit()}),
                       "rules_without_listed_tensions":sorted(set(originals)-set(numeric_issues),key=int),
                       "multiple_tensions_for_number":{k:len(v) for k,v in numeric_issues.items() if len(v)>1}}},
                 normalized_text=dict(blocks=len(blocks),characters=len(flat),first_offset=segments[0]["start_offset"],
                                     last_offset=segments[-1]["end_offset"],gap_characters=0),
                 segments=len(segments), numbered_segments=n_num, unnumbered_segments=len(segments)-n_num,
                 statuses=dict(counts), primary_categories=dict(Counter(s["primary_category"] for s in segments)),
                 all_category_assignments=dict(Counter(c for s in segments for c in [s["primary_category"],*s["secondary_categories"]])))
    export_json(DATA / "rules.json",rules)
    export_json(DATA / "segments.json",segments)
    audit["source_forms"] = build_forms(raw,segments,offsets,blocks,ANALYSIS / "source_forms.csv")
    export_json(ANALYSIS / "audit.json",audit)
    with (DATA / "cross_references.csv").open("w",encoding="utf8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(xrefs[0]),lineterminator="\n")
        w.writeheader()
        w.writerows(xrefs)
    print(f"{len(rules)} headings, {len(segments)} segments ({n_num} numbered), {len(xrefs)} explicit reference occurrences.")
    print("See analysis/classification/audit.json for filtering and join counts.")


EXTRA_REFS = {
    17: [("principle as # 17","17")], 31: [("equation of # 31","31")],
    94: [("RULE 135","135")], 111: [("& #74","74")], 158: [("Equation : # 155","155")],
    177: [("favorite is # 132","132")], 189: [("}, # 158,","158")],
}
if __name__ == "__main__":
    main()
