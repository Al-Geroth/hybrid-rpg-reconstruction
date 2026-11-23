"""Validate the built edition, links, witness boundaries and editorial relations."""
import csv
import hashlib
import json
import re
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote,urlsplit

ROOT=Path(__file__).resolve().parents[1]
DOCS=ROOT/"docs"

class Page(HTMLParser):
    def __init__(self):
        super().__init__(); self.ids=[];self.urls=[];self.titles=0;self.lang=None
    def handle_starttag(self,tag,attrs):
        d=dict(attrs)
        if d.get("id"):self.ids.append(d["id"])
        if tag=="h1":self.titles+=1
        if tag=="html":self.lang=d.get("lang")
        for key in ("href","src"):
            if d.get(key):self.urls.append(d[key])

def read_json(name):
    return json.loads((ROOT/name).read_text(encoding="utf-8"))

def check():
    pages={}
    for p in DOCS.glob("*.html"):
        page=Page();page.feed(p.read_text(encoding="utf-8"));pages[p.resolve()]=page
        assert len(page.ids)==len(set(page.ids)),f"Repeated HTML id in {p}"
        assert page.titles==1 and page.lang=="en",p
    relations=[]
    for p,page in pages.items():
        relations.extend((p,url) for url in page.urls)
    graph=read_json("analysis/dependencies/graph.json")
    relations.extend((DOCS/"architecture.html",n["link"]) for n in graph["nodes"])
    search=json.loads((DOCS/"assets/index.js").read_text(encoding="utf-8").removeprefix("window.EDITION_INDEX=").rstrip(";\n"))
    relations.extend((DOCS/"search.html",r[0]) for r in search)
    local=[(p,urlsplit(u)) for p,u in relations if not urlsplit(u).scheme]
    missing=[]
    for p,url in local:
        target=(p.parent/unquote(url.path)).resolve() if url.path else p.resolve()
        if not target.is_file() or (url.fragment and (target not in pages or unquote(url.fragment) not in pages[target].ids)):
            missing.append([p.name,url.geturl()])
    assert not missing,missing[:30]
    names=Counter((p.name,u.path,u.fragment) for p,u in local)
    rules=read_json("data/rules.json");segments=read_json("data/segments.json")
    assert [r["original_id"] for r in rules]==list(map(str,range(204)))
    assert len(set(s["id"] for s in segments))==len(segments)
    assert {s["rule_id"] for s in segments if s["rule_id"]}=={r["id"] for r in rules}
    for segment in segments:
        assert segment["title"] and segment["paraphrase"] and segment["primary_category"]
    permissions=[".html",".css",".js",".png",".ttf",".txt",".csv"]
    for p in DOCS.rglob("*"):
        if p.is_file():assert p.name==".nojekyll" or p.suffix in permissions,p
    with (ROOT/"sources/source_manifest.csv").open(encoding="utf8",newline="") as f:
        manifest={r["id"]:r for r in csv.DictReader(f)}
    assert manifest["reference"]["sha256"]==manifest["sister"]["sha256"]=="b71d98a0582301d4cb2f83efbb193bfe6c71fa6ccb56e068a4fc14ae553c73ec"
    for key in ("earlier-005","earlier-020"):assert "error page" in manifest[key]["status"]
    report={"html_pages":len(pages),"checked_links_before_local_filter":len(relations),"local_link_occurrences_after_filter":len(local),"duplicate_html_ids":0,"unmatched_internal_destinations":[],"repeated_source_target_link_keys":sum(n>1 for n in names.values()),"rules":len(rules),"segments":len(segments),"searchable_entries":len(search),"graph_nodes_checked":len(graph["nodes"])}
    print(json.dumps(report,indent=2));return report

if __name__=="__main__":check()
