"""Collect comparison witnesses into an immutable, ignored cache. Python 3.10+."""
import csv
import hashlib
import json
import re
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / "sources/raw"
WANADOO = "http://perso.wanadoo.fr/philippe.tromeur/"
WAYBACK = "https://web.archive.org/web/"
STAMP = "20030213163300"
TARGETS = [
    ("reference", "0.30", "Primary, host edition", WAYBACK + STAMP + "id_/" + WANADOO + "hybrid.htm",
     "Reference witness. Cover and disclaimers distinguish host, author and publication conditions."),
    *[("earlier-" + n, v, "Primary, linked witness", WAYBACK + STAMP + "id_/" + WANADOO + "hybrid" + n + ".htm",
       "Earlier version linked by the reference page. The host's label gives an approximate composition date.")
      for n, v in [("005","0.05"),("010","0.10"),("015","0.15"),("020","0.20")]],
    ("mirror-005", "0.05 link", "Primary, mirror", WAYBACK + "20030225115130id_/http://philippe.tromeur.free.fr/hybrid005.htm",
     "The mirror retained a page at the earlier-version link. See the witness comparison for its internal title."),
    ("december", "December witness", "Primary, mirror main page", WAYBACK + "20021223084210id_/http://philippe.tromeur.free.fr/hybrid.htm",
     "Earlier main-page capture located through the Wayback CDX index. Edition assigned from the body."),
    ("sister", "0.30 comparison", "Primary, mirror main page", WAYBACK + "20030211010513id_/http://philippe.tromeur.free.fr/hybrid.htm",
     "A second host preserved the February edition two days earlier."),
    ("later", "0.21", "Primary, later host witness", WAYBACK + "20071014102242id_/http://philippe.tromeur.free.fr/hybrid.htm",
     "Separate capture of the host's later page. Its rules are excluded from the reference catalogue."),
    ("files", "multiple", "Secondary, file catalogue", "https://rpggeek.com/files/thing/83822",
     "Indexed listings distinguish v0.30 from similarly numbered files and attribute upload dates to the uploader. Download access may require login."),
    ("rpgnet", "multiple", "Secondary, bibliographic entry", "https://index.rpg.net/display-entry.phtml?mainid=4345",
     "The index describes later material including v0.21. Its 551-rule figure belongs to that account."),
    ("stack", "0.30 / later", "Secondary, location history", "https://rpg.stackexchange.com/questions/45394/where-can-i-find-the-rpg-hybrid",
     "The 2014 answer links the February capture and reports later blog installments. Its assessment of playability is reception evidence."),
    ("blog", "later", "Attributed author blog", "https://hybrid-rpg.blogspot.com/",
     "Later postings are a separate witness. Blog access or an age/interstitial page cannot establish the contents of an individual post."),
]

def fetch(row):
    key, version, role, url, note = row
    record = dict(id=key, edition=version, role=role, url=url, resolved_url="", capture="", retrieved="", status="", bytes="", sha256="", note=note)
    name = CACHE / (key + ".html")
    meta = CACHE / (key + ".meta.json")
    if meta.exists() and name.exists():
        previous = json.loads(meta.read_text(encoding="utf-8"))
        if previous["sha256"] != hashlib.sha256(name.read_bytes()).hexdigest():
            raise ValueError("Local witness differs from receipt: " + key)
        previous.update(edition=version, note=note)
        return previous
    record["retrieved"] = datetime.now(timezone.utc).date().isoformat()
    try:
        req = urllib.request.Request(url, headers={"User-Agent":"Mozilla/5.0 (archival research)"})
        with urllib.request.urlopen(req, timeout=35) as resp:
            payload = resp.read()
            dest = resp.geturl()
            stamp = re.search(r"/web/(\d{14})", dest)
            record.update(resolved_url=dest, capture=resp.headers.get("Memento-Datetime") or (stamp[1] if stamp else ""),
                          status=str(resp.status), bytes=len(payload), sha256=hashlib.sha256(payload).hexdigest())
            if key == "reference" and record["sha256"] != "b71d98a0582301d4cb2f83efbb193bfe6c71fa6ccb56e068a4fc14ae553c73ec":
                raise ValueError("Reference digest mismatch")
            if name.exists():
                if name.read_bytes() != payload:
                    raise ValueError("Existing payload differs: " + key)
            else:
                with name.open("xb") as f:
                    f.write(payload)
            with meta.open("x", encoding="utf-8") as f:
                json.dump(record, f, indent=2)
    except (OSError, TimeoutError) as exc:
        record["status"] = f"Unavailable: {exc}"
        record["resolved_url"] = getattr(exc, "url", "")
    return record

if __name__ == "__main__":
    CACHE.mkdir(parents=True,exist_ok=True)
    with ThreadPoolExecutor(max_workers=5) as pool:
        records = list(pool.map(fetch, TARGETS))
    for row in records:
        if row['id'] in ('earlier-005','earlier-020') and row['sha256']:
            body = (CACHE / (row['id'] + '.html')).read_bytes().lower()
            if b'wanadoo' in body and b'hybrid' not in body:
                row['status'] += ' / archived host error page'
    out = ROOT / "sources/source_manifest.csv"
    with out.open("w",newline="",encoding="utf-8") as f:
        writer = csv.DictWriter(f,fieldnames=list(records[0]))
        writer.writeheader()
        writer.writerows(records)
    for record in records:
        print(record["id"],record["status"],record["capture"],record["bytes"])
