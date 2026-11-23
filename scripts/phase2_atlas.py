"""Build the Phase II mathematical atlas and check its source/registry joins."""
import argparse
from collections import Counter
import csv
from functools import lru_cache
import hashlib
from html import escape
import json
import math
from pathlib import Path

from math_check import calculate, csv_string


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "analysis/phase2"
LABELS = {
    "D":"Distinct gameplay equation", "V":"Variant of an existing equation",
    "E":"Numerical example", "C":"Calibration or conversion", "S":"Superseded equation",
    "A":"Mathematical assertion without gameplay relevance", "U":"Unresolved mathematical passage",
    "F":"False positive",
}
WITNESS = "b71d98a0582301d4cb2f83efbb193bfe6c71fa6ccb56e068a4fc14ae553c73ec"


def records(name, fields):
    path = OUT / f"atlas-{name}.txt"
    result = []
    for i,line in enumerate(path.read_text(encoding="utf8").splitlines(),1):
        if not line or line.startswith("#"):
            continue
        cells = line.split("|")
        if len(cells) != len(fields):
            raise ValueError(f"{path.name}:{i} needs {len(fields)} fields")
        result.append(dict(zip(fields,cells,strict=True)))
    return result


def load_csv(path):
    with path.open(encoding="utf8",newline="") as f:
        return list(csv.DictReader(f))


def load_json(path):
    return json.loads(path.read_text(encoding="utf8"))


def id_index(rows, key):
    result = {row[key]:row for row in rows}
    if len(result)!=len(rows):
        raise ValueError(f"Duplicate {key}: {[k for k,c in Counter(r[key] for r in rows).items() if c>1]}")
    return result


def audit_join(source, target, join_key):
    """A many-to-one lookup; report repeats on both sides and left/right-only keys."""
    left, right = Counter(iter(source)), Counter(iter(target))
    duplicate_target_keys = {k:v for k,v in right.items() if v>1}
    unmatched = sorted(left.keys()-right.keys())
    if duplicate_target_keys or unmatched:
        raise ValueError(f"{join_key}: duplicate targets {duplicate_target_keys}, unmatched {unmatched}")
    return dict(source_rows=sum(left.values()),target_rows=sum(right.values()),
                matched_rows=sum(left[k] for k in left.keys() & right.keys()),
                repeated_source_keys={k:v for k,v in sorted(left.items()) if v>1},
                duplicate_target_keys=duplicate_target_keys,unmatched_source_keys=unmatched,
                unused_target_keys=sorted(right.keys()-left.keys()))


def segment_id(short):
    return short if short.startswith("front-") else "rule-"+short


def verify_witness(rows):
    import corpus
    raw = corpus.CACHE.read_bytes()
    if hashlib.sha256(raw).hexdigest() != WITNESS:
        raise ValueError("Unexpected archival witness")
    _, blocks = corpus.normalized_blocks(raw)
    if not blocks[-1].startswith("Membre de ClickFR"):
        raise ValueError("Unexpected footer")
    source = "\n".join(blocks[:-1])
    for r in rows:
        text = source[r["start_offset"]:r["end_offset"]]
        if not text.strip():
            raise ValueError(f"Empty source span for {r['segment_id']}")
        if r["segment_id"].startswith("rule-") and r["segment_id"].endswith("-a"):
            heading = corpus.HEADING.match(text)
            if not heading or heading[2] != r["segment_id"].split("-")[1]:
                raise ValueError(f"Wrong source heading for {r['segment_id']}")
    return len(rows)


@lru_cache(maxsize=1)
def build_data():
    source_segments=load_json(ROOT/"data/segments.json")
    segments=id_index(source_segments,"id")
    old_equations=id_index(load_json(ROOT/"data/equations.json"),"id")
    all_locators=load_csv(ROOT/"analysis/mathematics/equation_locators.csv")
    candidates=[r for r in all_locators if r["candidate"]=="1"]
    selected=[r for r in candidates if not r["detailed_records"]]
    direct=[r for r in candidates if r["detailed_records"]]
    readings=records("readings",["segment_id","code","family","link","reason"])
    for r in readings:
        r["segment_id"]=segment_id(r["segment_id"])
    reviews=id_index(readings,"segment_id")
    families=id_index(records("families",["id","title","question","inputs","outputs","domain","connection","limit"]),"id")
    operations=id_index(records("operations",["id","title","domain","output","connection","layer"]),"id")
    connections=records("connections",["source","target","kind","reading"])
    cases=records("cases",["operation","branch","expression","inputs","expected","origin"])
    joins={}
    joins["classification to exact Phase I locator-only denominator"]=audit_join(reviews,[r["segment_id"] for r in selected],"coverage")
    if joins["classification to exact Phase I locator-only denominator"]["unused_target_keys"]:
        raise ValueError("Unreviewed locator-only segments")
    joins["reviewed segments to catalogue"]=audit_join(reviews,segments,"document")
    joins["reviewed segments to families"]=audit_join([r["family"] for r in readings],families,"families")
    joins["new and variant assignments to Phase II operations"]=audit_join(
        [r["link"].split(":")[1] for r in readings if r["link"].startswith(("new:","also:"))],operations,"new register")
    joins["primary new-operation assignments"]=audit_join(
        [r["link"].split(":")[1] for r in readings if r["link"].startswith("new:")],operations,"one primary per new operation")
    op_primary=joins["primary new-operation assignments"]
    if op_primary["repeated_source_keys"] or op_primary["unused_target_keys"]:
        raise ValueError("New operations need exactly one primary assignment each")
    joins["old links to Phase I detailed register"]=audit_join(
        [r["link"].split(":")[1] for r in readings if r["link"].startswith("old:")],old_equations,"old register")
    joins["numeric cases to new operations"]=audit_join([c["operation"] for c in cases],operations,"cases")
    if joins["numeric cases to new operations"]["unused_target_keys"]:
        raise ValueError("Every new operation needs a numerical replay")
    joined_endpoints=[p for c in connections for p in (c["source"],c["target"]) if p]
    joins["operational relationships to catalogue"]=audit_join(joined_endpoints,segments,"operational endpoints")
    indexed=[]
    primary={}
    for locator in selected:
        sid=locator["segment_id"]
        s=segments[sid]
        r=reviews[sid]
        if (r["code"]=="D") != r["link"].startswith("new:"):
            raise ValueError(f"Inconsistent distinct-operation assignment {sid}")
        if r["link"]!="-" and r["link"].partition(":")[0] not in ("old","new","also"):
            raise ValueError(f"Unknown register link {r['link']}")
        if r["link"].startswith("new:"):
            primary[r["link"].split(":")[1]]=sid
        if any(int(locator[k]) != s[k] for k in ["start_offset","end_offset"]):
            raise ValueError(f"Locator drift at {sid}")
        indexed.append(dict(segment_id=sid,title=s["title"],classification=LABELS[r["code"]],
                            family_id=r["family"],register_link=r["link"],reason=r["reason"],
                            start_offset=s["start_offset"],end_offset=s["end_offset"]))
    for c in cases:
        args = {pair.split("=")[0]:float(pair.split("=")[1]) for pair in c["inputs"].split(",")}
        val = calculate(c["expression"],args)
        if not math.isclose(val,float(c["expected"]),rel_tol=1e-11,abs_tol=1e-12):
            raise ValueError(f"Incorrect numerical case {c}: {val}")
        c["computed"]=format(val,".12g")
    stats=Counter(r["classification"] for r in indexed)
    if len(selected)!=205 or len(direct)!=70 or len(candidates)!=275 or len(source_segments)!=304:
        raise ValueError("Phase I denominator changed")
    report=dict(source_edition="0.30",source_sha256=WITNESS,
                selections={
                    "locator rows to quantitative candidates":[len(all_locators),len(candidates)],
                    "candidates directly covered by Phase I":[len(candidates),len(direct)],
                    "candidates without Phase I registry entries":[len(candidates),len(selected)],
                    "reviewed candidates to distinct gameplay operation rows":[len(indexed),len(primary)],
                    "both phases covering candidate segments":[len(candidates),len(direct)+len(indexed)],
                    "reviewed candidates to false positives":[len(indexed),stats[LABELS["F"]]]},
                classifications=dict(stats),families=len(families),new_operations=len(operations),
                distinct_preexisting_detailed_records=len(old_equations),tested_numeric_cases=len(cases),
                joins=joins,connections_by_type=dict(Counter(r["kind"] for r in connections)),
                counting_policy="One principal editorial disposition per former locator-only segment. One new operation per distinct, usable fictional input-to-output task absent as a worked mapping in the 54-record register. A new input-producing stage can count even if a later stage was registered. Rearrangements, parameter variants, examples, cross-game and world-description calibrations do not increment the count. Alternative minor calculations in mixed passages can be mentioned under their dominant use. Counting every algebraic expression would give a different and unsupported total.")
    return dict(reviews=indexed,families=families,operations=operations,primary=primary,connections=connections,
                cases=cases,report=report)


def artifacts(data):
    result = {}
    for key, file in [("reviews","atlas-review.csv"),("cases","atlas-numerical-replay.csv")]:
        rows=data[key]
        result[file]=csv_string(rows[0].keys(),rows)
    result["atlas-audit.json"]=json.dumps(data["report"],indent=2,ensure_ascii=False)+"\n"
    return result


def link(url, text):
    return '<a href="'+escape(url,quote=True)+'">'+escape(text)+'</a>'


def passage(sid):
    title = ("Rule "+sid.split("-")[1]+" · "+sid.split("-")[-1]) if sid.startswith("rule-") else "Front matter "+sid.split("-")[1]
    return link("catalogue.html#"+sid,title)


def definitions(items):
    return '<dl class="datafields">'+''.join("<dt>"+escape(k)+"</dt><dd>"+escape(v)+"</dd>" for k,v in items)+"</dl>"


def summary_details(title, text):
    return '<details class="note"><summary>'+escape(title)+'</summary>'+text+"</details>"


def atlas_html():
    data = build_data()
    review, families, ops, primary = data["reviews"],data["families"],data["operations"],data["primary"]
    counts=data["report"]["classifications"]
    parts=['<p class="lede">A rating can describe a character, set the reach of a power, or supply the input to another rule. Those are different jobs. Follow one number through play before opening the full inventory.</p>']
    parts.append('<section id="through-play"><h2>How a number reaches the table</h2>'
                 '<p>Imagine a molecular controller declaring that she will reshape an object. Rule 134 starts its example at 100.5 C2 DP. The player can divide life-span by five and multiply power by five. The resulting 502.5 C2 PL answers a question about the controller. The next step answers a question about the object. Copy the numeral 502.5 into C3 PL for the target capacity. Converting 502.5 through the scale equation would give a radically different answer.</p>'
                 '<p>The source has connected a player choice, a sheet update and a limit on a declared power. To use it for a new scene, the referee must already know the object’s size rating or decide how to assign it. The rule tells the group how much the controller may affect. It supplies no contest against another controller.</p><p class="refs">'+
                 " · ".join([passage("rule-3-a"),passage("rule-134-a"),passage("rule-152-a"),link("builder.html","Character builder"),link("playground.html","Mathematical playground")])+'</p></section>')
    parts.append('<section id="accounting"><h2>What the review added</h2>'
                 '<p>The Phase I search marked 275 of the catalogue’s 304 segments. It linked 70 of those segments directly to 54 detailed mathematical records. We read the other 205 against the same v0.30 capture. All 275 candidates now have a disposition. The other 29 catalogue segments had no selected mathematical cue.</p>'
                 '<p><strong>'+str(len(ops))+' newly registered gameplay operations</strong> have explicit inputs, a stated fictional output and at least one numerical replay. A conditional procedure may still depend on a choice of branch. Copying a number to a different stat can be a new procedure even when the arithmetic is trivial. Additional examples, alternative coefficients, cross-game translations and setting calibrations have their own categories. The total is an editorial count of distinct operations, not a count of equals signs or a score for playability.</p>')
    parts.append('<div class="scrollbox"><table class="data-table"><thead><tr><th scope="col">Disposition among the 205</th><th scope="col">Segments</th></tr></thead><tbody>'+''.join(
        '<tr><td>'+escape(label)+'</td><td>'+str(counts[label])+'</td></tr>' for label in LABELS.values())+
        '</tbody></table></div><p>The four false positives are a reader warning, a masthead, a baking recipe and the syntax of a character write-up. The last one is valuable evidence about what to record even though it computes no value.</p></section>')
    parts.append('<section id="families"><h2>Families and their uses</h2><p>Each family groups rules by the question a player or referee asks. Identical arithmetic can serve unrelated functions. Conversely, a single play decision may need several different kinds of arithmetic.</p>')
    for f in families.values():
        parts.append('<div id="family-'+f["id"]+'">'+summary_details(f["title"],'<p>'+escape(f["question"])+'</p>'+definitions([
            ("Inputs",f["inputs"]),("Outputs",f["outputs"]),("Domain",f["domain"]),("Gameplay connection",f["connection"]),("Limit",f["limit"])]))+'</div>')
    parts.append('</section><section id="handoffs"><h2>Where outputs go next</h2><p>An explicit use means the source works or directs the transition. Compatible inputs could be connected by a reader; the cited example may simply choose the second number. A scene comparison also needs a condition supplied by the fiction. An endpoint is an output for which this review found no subsequent rule performing the indicated task.</p>')
    for name in dict.fromkeys(c["kind"] for c in data["connections"]):
        items=[]
        for c in data["connections"]:
            if c["kind"]==name:
                refs=passage(c["source"])
                if c["target"]:
                    refs+=" → "+passage(c["target"])
                items.append("<li>"+escape(c["reading"])+' <span class="refs">'+refs+"</span></li>")
        parts.append(summary_details(name,"<ul class='entry-list'>"+"".join(items)+"</ul>"))
    parts.append('</section><section id="operations"><h2>New operations and numerical replays</h2><p>The numbers below test printed or explicitly labelled editorial inputs. An arithmetic match establishes the selected reading at those inputs. It does not establish the model as real-world physics.</p>')
    for key,o in ops.items():
        cases=[c for c in data["cases"] if c["operation"]==key]
        testrows="".join('<tr><td>'+escape(c["branch"])+'</td><td><code>'+escape(c["expression"])+'</code><br>'+escape(c["inputs"])+'</td><td>'+escape(c["computed"])+'</td><td>'+escape(c["origin"])+'</td></tr>' for c in cases)
        table='<div class="scrollbox"><table class="data-table"><thead><tr><th>Branch</th><th>Expression and inputs</th><th>Result</th><th>Case</th></tr></thead><tbody>'+testrows+'</tbody></table></div>'
        evidence=[s["segment_id"] for s in review if s["register_link"] in ("new:"+key,"also:"+key)]
        parts.append('<div id="operation-'+key+'">'+summary_details(o["title"],definitions([("Inputs and domain",o["domain"]),("Fictional output",o["output"]),("At the table",o["connection"])])+table+
            '<p class="refs">Layer '+o["layer"]+' · '+" · ".join(passage(sid) for sid in evidence)+'</p>')+"</div>")
    parts.append('</section><section id="readings"><h2>All 205 source readings</h2><p>Each ruling is keyed to one Phase I segment. A segment with several examples receives one principal disposition. The catalogue retains its complete source span and other subject labels.</p>')
    parts.append('<form class="filters" data-kind="readings"><label class="wide">Find a rule or subject<input type="search" name="q"></label><label>Disposition<select name="kind"><option value="">All</option>'+
                 "".join('<option>'+escape(s)+'</option>' for s in LABELS.values())+'</select></label><label>Family<select name="family"><option value="">All</option>'+
                 "".join('<option>'+escape(f["title"])+'</option>' for f in families.values())+'</select></label><button type="reset">Reset</button></form><p id="matches" class="matchcount" aria-live="polite"></p>')
    for r in review:
        kind=r["classification"]
        family=families[r["family_id"]]["title"]
        words=" ".join([r["segment_id"],r["title"],kind,family,r["reason"]]).casefold()
        links=[passage(r["segment_id"]),link("#family-"+r["family_id"],family)]
        if r["register_link"]!="-":
            typ,key=r["register_link"].split(":")
            if typ=="old":
                links.append(link("mathematics.html#"+key,"Phase I equation"))
            else:
                links.append(link("#operation-"+key,"Numerical replay"))
        parts.append('<div class="entry" id="reading-'+r["segment_id"]+'" data-row data-kind="'+escape(kind,quote=True)+'" data-family="'+escape(family,quote=True)+'" data-words="'+escape(words,quote=True)+'"><div class="kicker">'+escape(kind)+'</div><h3>'+escape(r["title"])+'</h3><p>'+escape(r["reason"])+'</p><p class="refs">'+" · ".join(links)+'</p></div>')
    parts.append('</section><p class="refs">Download the public working data · '+
                 " · ".join(link("https://github.com/Al-Geroth/hybrid-rpg-reconstruction/blob/master/analysis/phase2/"+filename,label)
                 for filename,label in [("atlas-review.csv","Segment decisions"),("atlas-numerical-replay.csv","Tested calculations"),("atlas-audit.json","Coverage and join audit")])+'</p>')
    return "".join(parts)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--write",action="store_true",help="Write public audit, linked verdicts and numerical case table.")
    p.add_argument("--source",action="store_true",help="Validate source spans against privately cached v0.30 bytes.")
    args=p.parse_args()
    data=build_data()
    if args.source:
        print("Verified pinned archival source for",verify_witness(data["reviews"]),"source spans.")
    for name,content in artifacts(data).items():
        path=OUT/name
        if args.write:
            path.write_bytes(content.encode("utf8"))
        elif path.read_text(encoding="utf8")!=content:
            raise SystemExit("Stale Phase II artefact: "+name)
    print("275 candidates = 70 direct + 205 reviewed. All 205 matched, with zero missing or duplicate review keys.")
    print(f"{len(data['operations'])} newly registered operations, {len(data['cases'])} numerical replays.")


if __name__=="__main__":
    main()
