"""Build the static reading edition from public editorial data, without network access."""
import csv
import html
import json
import re
import shutil
import unicodedata
import math
from collections import Counter, defaultdict
from pathlib import Path
from urllib.parse import quote
from architecture import build as graph_build

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs"
WEB = ROOT / "web"
REPO = "https://github.com/Al-Geroth/hybrid-rpg-reconstruction"
ARCHIVE = "https://web.archive.org/web/20030213163300/http://perso.wanadoo.fr/philippe.tromeur/hybrid.htm"
NAV = [("index","Start here"),("quickstart","Quickstart"),("rulebook","Reconstructed rulebook"),("catalogue","Rule catalogue"),("glossary","Glossary"),("mathematics","Mathematics"),("architecture","System architecture"),("playability","Playability trials"),("assessment","Critical assessment"),("appendix","Editorial appendix"),("sources","Sources and method")]
LAYERS = {"A":"A · Explicit original mechanic","B":"B · Reconstructed reading","C":"C · Hypothetical reading","D":"D · Editorial addition"}
INDEX = []
E = lambda value: html.escape(str(value),quote=True)

def js(path):
    return json.loads((ROOT/path).read_text(encoding="utf-8-sig"))

def rows(path):
    with (ROOT/path).open(encoding="utf-8-sig",newline="") as f:
        return list(csv.DictReader(f))

def link(url,title):
    return f'<a href="{E(url)}">{E(title)}</a>'

def refs(values):
    if not values:
        return ""
    links = [link("catalogue.html#rule-"+str(i),"#"+str(i)) if str(i).isdigit() else link("catalogue.html#front",str(i).capitalize()) for i in values]
    return '<p class="refs">Source passages · '+" · ".join(links)+"</p>"

def details(title,body):
    return '<details class="note"><summary>'+E(title)+'</summary>'+body+'</details>'

def fields(pairs):
    return '<dl class="datafields">'+''.join('<dt>'+E(k)+'</dt><dd>'+v+'</dd>' for k,v in pairs if v)+'</dl>'

def table(titles,data):
    return '<div class="scrollbox"><table class="data-table"><thead><tr>'+''.join('<th scope="col">'+E(t)+'</th>' for t in titles)+'</tr></thead><tbody>'+''.join('<tr>'+''.join('<td>'+v+'</td>' for v in record)+'</tr>' for record in data)+'</tbody></table></div>'

def bullet(items):
    return '<ul class="entry-list">'+''.join('<li>'+E(value)+'</li>' for value in items)+'</ul>' if items else ''

def heading(title,kicker,sub=""):
    return '<header><div class="eyebrow">'+E(kicker)+'</div><h1>'+E(title)+'</h1>'+(f'<p>{E(sub)}</p>' if sub else '')+'</header>'

def page(slug,title,body,selected=None,home=False):
    selected = selected or slug
    def nav():
        return '<nav aria-label="Edition contents">'+''.join('<a '+('aria-current="page" ' if key==selected else '')+'href="'+key+'.html">'+label+'</a>' for key,label in NAV)+'</nav>'
    mast='<header class="mast"><div class="bar"><a class="brand" href="index.html"><span aria-hidden="true" class="seal">h</span> HYBRID / Reading edition</a><a class="shortcut" href="rulebook.html">Rulebook</a><a class="shortcut" href="catalogue.html">Catalogue</a><a class="searchlink" href="search.html">Search</a><details><summary>Contents</summary>'+nav()+'</details></div></header>'
    shell=('<main class="shell" id="content">'+body+'</main>' if home else '<main class="shell layout" id="content"><aside class="rail"><h2>Reading edition</h2>'+nav()+'</aside><article class="chapter">'+body+'</article></main>')
    extra = '<script defer src="assets/index.js"></script>' if slug=="search" else ''
    document='<!doctype html>\n<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><meta name="theme-color" content="#172f32"><title>'+E(title)+' | HYBRID reading edition</title><link rel="stylesheet" href="assets/site.css">'+extra+'<script defer src="assets/site.js"></script></head><body><a class="skip" href="#content">Skip to content</a>'+mast+shell+'<footer><div class="footer-in"><strong>HYBRID / Reading edition</strong><span>Reference edition · February 2003</span>'+link(REPO,"Repository")+'</div></footer></body></html>\n'
    (OUT/(slug+".html")).write_text(document,encoding="utf-8")

def index(href,title,category,text):
    INDEX.append([href,title,category,text])

def prose(record,slug,terms):
    blocks=[]
    for i,s in enumerate(record["sections"],1):
        ident=f"section-{i}"
        index(slug+".html#"+ident,s["title"],record["title"],s["text"])
        text=''.join('<p>'+E(p)+'</p>' for p in s["text"].split('\n\n') if p)
        layer=LAYERS.get(s.get("layer"),"")
        blocks.append('<section id="'+ident+'"><h2>'+E(s["title"])+'</h2>'+text+('<span class="chip">'+E(layer)+'</span>' if layer else '')+refs(s.get("refs",[]))+'</section>')
    mentions=[]
    fulltext=" ".join(s["text"] for s in record["sections"])
    for term in terms:
        if re.search(r'(?<!\w)'+re.escape(term["term"])+r'(?!\w)',fulltext,re.I):
            mentions.append(link("glossary.html#"+term["id"],term["term"]))
    return '<div class="prose">'+''.join(blocks)+'</div>'+('<p class="refs">In the glossary · '+" · ".join(mentions[:12])+'</p>' if mentions else '')

def filters(kind,labels):
    inputs = ['<label class="wide">Search<input type="search" name="q" placeholder="Words or symbols"></label>']
    for key,label,values in labels:
        if values is None:
            inputs.append('<label>'+E(label)+'<input name="'+key+'" inputmode="numeric" placeholder="Exact number"></label>')
        else:
            inputs.append('<label>'+E(label)+'<select name="'+key+'"><option value="">All</option>'+''.join('<option>'+E(v)+'</option>' for v in sorted(set(values),key=str.casefold) if v)+'</select></label>')
    return '<form class="filters" data-kind="'+kind+'">'+''.join(inputs)+'<button type="reset">Reset</button></form><p class="matchcount" id="matches" aria-live="polite"></p><noscript><p>All entries appear below. Your browser’s find command can locate a word or rule number.</p></noscript>'

def attributes(words,**filters):
    words=unicodedata.normalize("NFKD",words.lower())
    clean="".join(c for c in words if not unicodedata.combining(c))
    return 'data-row data-words="'+E(clean)+'" '+ ' '.join('data-'+k+'="'+E(v)+'"' for k,v in filters.items())

def chart():
    return '<figure class="plate"><div class="platehead"><span>Magnitude conversion</span><span>Rule 45</span></div><div class="formula" aria-label="x raised to log base ten of x">x<sup>log<sub>10</sub> x</sup></div><img src="assets/magnitude.png" width="1100" height="630" alt="On logarithmic input and output axes, the conversion falls from 10,000 at x = .01 to 1 at x = 1, then rises to 10,000 at x = 100."><figcaption class="plate-foot" style="color:inherit"><span>Input across · output up</span><span>Logarithmic axes</span></figcaption></figure>'

def home():
    body='<div class="hero"><div><div class="eyebrow">A critical reconstruction · v0.30</div><h1>Deciphering<br><i>HYBRID</i></h1><p class="lede">An early web roleplaying game tried to put ordinary people, superheroes and planets on the same scale. How much of it can you actually play?</p><div class="actions"><a class="button" href="quickstart.html">Read the quickstart</a><a href="rulebook.html">Open the rulebook</a></div></div>'+chart()+'</div>'
    body+='<section class="routes"><div><div class="eyebrow">Explore the edition</div><h2>Ways into the text</h2><p>Matthew/C++ wrote HYBRID. This edition follows the version Philippe Tromeur hosted in February 2003.</p></div><div class="paths">'
    for url,title,desc in [('catalogue','Follow a rule','Browse the numbered entries and their editorial segments.'),('glossary','Look up a symbol','Read C2, DP or Psyche in the context of a rule.'),('mathematics','Check the arithmetic','Trace a conversion and inspect its inverse.'),('playability','Try a scene','Follow seven attempts from character creation to the next session.'),('assessment','Read the findings','See where a calculation becomes a playable decision.'),('sources','Inspect the witnesses','Compare surviving editions, capture dates and evidence.')]:
        body+=f'<a href="{url}.html"><strong>{title}</strong><span>{desc}</span></a>'
    page("index","Deciphering HYBRID",body+'</div></section>',home=True)

def catalogue(rules,segments,contradictions):
    locators={r["segment_id"]:r for r in rows("analysis/mathematics/equation_locators.csv")}
    rule_ids={r["id"] for r in rules}
    seen=set()
    intro=f'{len(rules)} numbered entries in source order. Each smaller entry below is an editorial unit. A numbered heading can contain more than one subject.'
    body=heading("Rule catalogue","Reference edition · v0.30",intro)
    body+=filters("segments",[("number","Rule number",None),("topic","Topic",[c for s in segments for c in [s["primary_category"],*s["secondary_categories"]]]),("relevance","Gameplay relevance",[s["relevance"] for s in segments]),("confidence","Confidence",[s["confidence"] for s in segments]),("status","Executability",[s["executability"] for s in segments]),("edition","Source edition",[s["edition"] for s in segments])])
    body+='<div id="front"></div>'
    for s in segments:
        parent=s["rule_id"]; number=s["original_id"]; categories=[s["primary_category"],*s["secondary_categories"]]
        label="Unnumbered" if number is None else "Rule "+str(number)
        anchor=''
        if parent and parent not in seen:
            if parent not in rule_ids: raise ValueError("Unknown parent "+parent)
            anchor='<span id="'+E(parent)+'"></span>';seen.add(parent)
        ident=s["id"]
        desc=s["paraphrase"]
        index("catalogue.html#"+ident,label+" · "+s["title"],"Catalogue",desc+" "+" ".join(categories))
        attrs=attributes(" ".join([label,ident,s["title"],desc,*categories,*s["concepts"]]),number=number if number is not None else "",topic="|".join(categories),relevance=s["relevance"],confidence=s["confidence"],status=s["executability"],edition=s["edition"])
        fields_to_show=[("Edition",E(s["edition"])+" · "+link(ARCHIVE,"Archived witness")),("Text locator",f'Blocks {s["start_block"]}–{s["end_block"]}, normalized offsets {s["start_offset"]:,}–{s["end_offset"]:,}'),("Category",E(" · ".join(categories))),("Gameplay",E(s["relevance"])),("Confidence",E(s["confidence"])),("Layer",E(s["layer"]+" · "+s["layer_scope"])),("Concepts",E(", ".join(s["concepts"]))),("Other games",E(", ".join(s["external_systems"]))),("Dependencies"," · ".join(link("#rule-"+v[5:],v) if re.fullmatch(r"Rule \d+",v) else E(v) for v in s["dependencies"])),("Tensions"," · ".join(link("assessment.html#"+v,v) for v in s["contradictions"])),("Editorial note",E(s["notes"]))]
        equation_ids=locators[ident]["detailed_records"].split(" | ") if locators[ident]["detailed_records"] else []
        fields_to_show.extend([("Source forms",E(", ".join(s["source_features"]))),("Equations"," · ".join(link("mathematics.html#"+key,key) for key in equation_ids))])
        body+=f'<section class="entry" id="{E(ident)}" {attrs}>{anchor}<div class="kicker">{E(label)} · {E(ident)}</div><h2>{link("#"+ident,s["title"])}</h2><p class="definition">{E(desc)}</p><span class="chip">{E(s["executability"])}</span><span class="chip">{E(s["primary_category"])}</span>'+details("Classification and source details",fields(fields_to_show)+refs(s["references"]))+'</section>'
    if seen!=rule_ids: raise ValueError(f"Rules without segments: {rule_ids-seen}")
    page("catalogue","Rule catalogue",body)

def glossary(terms):
    body=heading("Glossary","Vocabulary","A rating in HYBRID has three parts to keep track of. Its number, class and use can each change what the other two mean.")+filters("terms",[])
    for t in sorted(terms,key=lambda x:x["term"].casefold()):
        index("glossary.html#"+t["id"],t["term"],"Glossary",t["definition"]+" "+t["expansion"])
        attrs=attributes(" ".join(str(t[x]) for x in ["term","expansion","definition","related","function"]))
        body+='<section class="entry" id="'+E(t["id"])+'" '+attrs+'><h2>'+link("#"+t["id"],t["term"])+'</h2>'+('<div class="fine">'+E(t["expansion"])+'</div>' if t["expansion"] else '')+'<p class="definition">'+E(t["definition"])+'</p>'+fields([("Use",E(t["function"])),("Units or domain",E(t["domain"])),("Example",E(t["example"])),("Uncertainty",E(t["ambiguity"])),("Interpretation",E(t["confidence"])+' · '+E(LAYERS.get(t["layer"],t["layer"]))),("Related"," · ".join(link("#"+n,n) for n in t["related"]))])+refs(t["references"])+'</section>'
    page("glossary","Glossary",body)

def formula(record):
    x='<mi>x</mi>'; y='<mi>y</mi>'; ten='<mn>10</mn>'; log='<msub><mi>log</mi>'+ten+'</msub>'
    symbols={
        "class-step":y+'<mo>=</mo><msup>'+x+'<mrow>'+log+x+'</mrow></msup>',
        "class-inverse":x+'<mo>=</mo><msup>'+ten+'<mrow><mo>±</mo><msqrt>'+log+y+'</msqrt></mrow></msup>',
        "ambs":'<mi>A</mi><mo>=</mo><msqrt><mi>d</mi></msqrt>',
        "pool-size":'<mi>n</mi><mo>=</mo><mfrac><mi>r</mi><mn>6</mn></mfrac>',
        "martial-grade":'<mi>m</mi><mo>=</mo><mn>1</mn><mo>−</mo><mfrac><mn>1</mn><msqrt><mi>d</mi></msqrt></mfrac>'
    }
    inner = '<math aria-label="'+E(record["notation"])+'"><mrow>'+symbols[record["id"]]+'</mrow></math>' if record["id"] in symbols else typeset(record["notation"])
    return '<div class="equation">'+inner+'</div>'

def typeset(s):
    # Keep editorial alternatives and conditions inline. Raise balanced caret groups.
    chunks=[]; i=0
    while i<len(s):
        if s[i]!='^' or i+1==len(s):
            chunks.append(E(s[i])); i+=1; continue
        i+=1
        if s[i] in '([':
            opener=s[i]; closer=')' if opener=='(' else ']'; start=i+1; depth=1; i+=1
            while i<len(s) and depth:
                depth += (s[i]==opener)-(s[i]==closer); i+=1
            val=s[start:i-1] if depth==0 else s[start:]
        else:
            match=re.match(r'[\w∞±−]+',s[i:])
            val=match.group() if match else s[i]; i+=len(val)
        chunks.append('<sup>'+typeset(val)+'</sup>')
    return ''.join(chunks)

def mathematics(equations):
    evidence=defaultdict(list)
    for row in rows("analysis/mathematics/equation_locators.csv"):
        if row["detailed_records"]:
            for key in row["detailed_records"].split(" | "):
                evidence[key].append(link("catalogue.html#"+row["segment_id"],row["title"]))
    body=heading("Mathematics","The equation register","What survives a change of scale? Start with one conversion, then follow the register into lifespan, movement, points and dice.")
    body+='<div class="prose"><section><h2>One number, two scales</h2><p>Write 20 C2 on a character sheet. Rule 45 lets you express that rating as about 49.28 C3. You gained digits on the page. The character gained no power. Rule 45 also describes a different operation, in which the numeral stays put while the character changes class. Recording the operation alongside the number matters.</p>'+refs(["45"])+'</section><section><h2>Why the curve turns</h2><p>Write the input as 10 raised to <i>u</i>. The output is then 10 raised to <i>u</i> squared. Inputs 0.1 and 10 both give 10, since −1 and +1 have the same square. The real-valued formula takes positive inputs and yields values of at least one. An inverse therefore needs a branch. The increasing branch matches the ordinary positive ratings above one used in the cited examples.</p>'+refs(["45","188"])+'</section></div>'
    body+=table(["Input x","log₁₀ x","Converted magnitude"],[[E(f"{x:g}"),E(f"{math.log10(x):.3g}"),E(f"{10**math.log10(x)**2:,.4f}".rstrip("0").rstrip("."))] for x in [.01,.1,1,10,16,20,100]])
    body+='<p class="fine">Editorial numerical demonstration, including fractional inputs to expose the domain. '+link("index.html","View the logarithmic plot")+'.</p>'
    body+='<h2>The equation register</h2><p>Each record gives a normalized reading. Several describe local calibrations, proposals, or rival readings of one passage. The number of records counts these analytical entries.</p>'
    audit=js("analysis/mathematics/locator_audit.json")
    body+='<p class="fine">Of '+str(audit["all_segments"])+' segments, '+str(audit["candidate_filter"][1])+' carry a notation, topic or verbal cue. The '+str(len(equations))+' detailed records draw on '+str(audit["registered_direct_evidence_filter"][1])+' of those segments. The other '+str(audit["candidate_segments_with_locator_only"])+' candidates have catalogue locators. '+link("assets/equation_locators.csv","Download the complete locator table (CSV)")+'.</p>'
    for item in equations:
        ident=item["id"]; index("mathematics.html#"+ident,item["title"],"Mathematics",item["notation"]+" "+item["interpretation"])
        body+='<section class="entry" id="'+E(ident)+'"><h2>'+link("#"+ident,item["title"])+'</h2>'+formula(item)+'<p class="definition">'+E(item["interpretation"])+'</p>'+fields([("Numerical check",E(item["test"])),("Uncertainty",E(item["issue"]))])+details("Variables, domain and dependencies",fields([("Variables",E(item["variables"])),("Domain",E(item["domain"])),("Dimensions",E(item["dimensions"])),("Depends on"," · ".join(link("#"+d,d) for d in item["dependencies"])),("Reading",E(item["confidence"])+" · "+E(LAYERS.get(item["layer"],item["layer"])))]))+refs(item["references"])+'</section>'
        body+='<div class="refs">Evidence segments · '+" · ".join(evidence[ident])+'</div>'
    page("mathematics","Mathematics",body)

def architecture(graph):
    nodes={n["id"]:n for n in graph["nodes"]}
    def nlink(k):
        n=nodes[k];return link(n["link"],n["label"])
    def path(*steps):
        return '<div class="chain">'+''.join(nlink(s) if i%2==0 else '<span>'+E(s)+'</span>' for i,s in enumerate(steps))+'</div>'
    body=heading("System architecture","Evidence graph","A rule can name another rule, define a calculation or rely on an input. Each edge in the graph records which relationship the evidence supports.")
    body+='<h2>Three paths through the rules</h2>'+path("rule-45","states →","eq-class-step","feeds the reading of →","eq-class-inverse")+path("rule-17","states →","eq-pool-size","can supply dice for →","eq-roll-high")+path("eq-roll-high","uses the opposite direction to →","eq-roll-low","worked in →","rule-188")
    body+='<p>Only the first path supplies a mathematical inverse. Pool size can set up a roll, but it cannot settle which direction counts as success. A reference to another passage can lead to an example or a disagreement as easily as to a prerequisite.</p>'
    body+='<h2>Most connected entries</h2>'
    relation_audit=graph["audit"]["relations"]
    for kind,title in [("explicit reference","Original rules cited by the most distinct sources"),("requires calculation","Equations used by the most other registered equations"),("related concept","Glossary concepts linked from the most entries")]:
        ranking=relation_audit[kind]["top_incoming"]
        body+='<h3>'+title+'</h3>'+table(["Entry","Incoming links"],[[nlink(row["id"]),str(row["incoming"])] for row in ranking])
    body+='<p class="fine">Each table counts distinct directed pairs within one relationship and omits self-links. Multiple appearances of a target in one numbered rule count once. Each unnumbered segment is a separate source. The equation and glossary rankings reflect the selected entries.</p>'
    origins=graph["audit"]["reference_origins"]
    body+=details("How the reference counts were obtained",table(["Source unit","Mentions","Matched","Distinct pairs","Repeated pairs","Unmatched"],[[label,str(origins[key]["rows_before_target_join"]),str(origins[key]["matched_rows"]),str(origins[key]["distinct_pairs"]),str(origins[key]["repeated_pair_mentions"]),str(origins[key]["unmatched_rows"])] for key,label in [("numbered_rule","Numbered rule"),("unnumbered_segment","Unnumbered segment")]])+'<p>The calculation and term definitions illustrated in this graph are selected examples. A written percentage can support an interpretation while leaving its denominator open.</p>')
    relevant=[(e["source"],e["target"]) for e in graph["edges"] if e["type"]=="requires calculation"]
    def cycles(stack,found):
        for a,b in relevant:
            if a!=stack[-1]: continue
            if b==stack[0]:found.add(tuple(sorted(stack)))
            elif b not in stack:cycles(stack+[b],found)
    found=set()
    for k in set(x[0] for x in relevant):cycles([k],found)
    cycletext='No cycle occurs in the registered calculation-dependency edges.' if not found else 'Registered cycles involve '+', '.join(' / '.join(c) for c in sorted(found))+'.'
    body+='<p>'+E(cycletext)+' Rules which cite each other can still be read independently. Conversely, a missing input can stop a procedure without producing a graph cycle.</p>'
    body+='<div class="note"><h2>Explore a neighbourhood</h2><label for="node">Choose a rule, term, equation or trial</label> <select id="node">'+''.join('<option value="'+E(k)+'"'+(' selected' if k=="eq-class-step" else '')+'>'+E(v["label"])+' ('+E(v["kind"])+')</option>' for k,v in nodes.items())+'</select><div id="neighbours" aria-live="polite"></div></div><script defer src="assets/graph.js"></script><script defer src="assets/neighbours.js"></script>'
    body+='<p>'+link(REPO+"/blob/master/analysis/dependencies/graph.json","Download the typed graph from the repository")+'</p>'
    page("architecture","System architecture",body)

def sourcepage(manifest,segments,rules):
    body=heading("Sources and method","Textual apparatus","The unit of evidence is a dated witness. The number on its cover is only one clue to its position in the publication history.")
    body+='<div class="prose"><section><h2>The copy behind this edition</h2><p>The reference is the February 13, 2003 capture of Philippe Tromeur’s Wanadoo page. Its cover credits Matthew/C++. A February 11 capture on Tromeur’s Free.fr host has exactly the same 431,957 bytes and SHA-256 digest. The archive timestamp dates preservation. It cannot date every paragraph.</p><p>'+link(ARCHIVE,"Read the reference witness in the Wayback Machine")+'</p></section><section><h2>What the versions change</h2><p>The host linked v0.05, v0.10, v0.15 and v0.20. Two linked addresses replay Wanadoo error pages with HTTP 200. The numbered v0.05 file on Free.fr and its December 23, 2002 homepage recover the missing texts. The v0.15 header recalls having briefly used the label 0.3. That makes matching the host, header and capture especially important.</p><p>Rule 45 in v0.15 already walks from CA through C3. The December v0.20 page already has the optional pool in #17 and the roll-high wording in #35. The February v0.30 page also includes the contrary roll-under example in #188. By October 2007 the host labels the text v0.21, extends the chain in #45 to C4 there and adds a coin option to #35. Importing that coin toss would change the February game.</p></section><section><h2>Archives, catalogues and reception</h2><p>RPGGeek indexes uploads and version descriptions. Its file list was visible through the search index, while direct retrieval returned 403. RPGnet’s bibliographic entry discusses a later, much larger text. The Stack Exchange answer was readable through the web reader despite 403 from the byte downloader. It supplies the February link and reports a later blog. The blog homepage was retrievable, and its title identifies a later tri-stat version. None of those observations establish a February rule.</p></section><section><h2>Editorial method</h2><p>Record the author’s identifier and the position of the passage separately. Divide mixed passages at subject changes. Give each unit a primary category, secondary topics where applicable, a gameplay judgment, and an interpretation confidence. A mathematician can evaluate a formula with chosen inputs while a player still lacks the means to obtain those inputs. The scenario verdicts therefore answer a different question from the catalogue tags.</p><p>Segments are editorial boundaries. A different editor could reasonably split an example differently. Source order, heading counts and the checksum allow independent comparison. Notes preserve conflicting directions, exceptions and proposed interpretations. The mathematical registry concentrates on recurring, consequential or diagnostic constructions. The catalogue records the wider terrain.</p></section><section><h2>Rights and redistribution</h2><p>The disclaimer promises free reading on the host’s page, discusses a possible commercial hard copy, and acknowledges rights in third-party character material. We found no general grant to redistribute the complete text. The repository publishes new descriptions, mathematical notation, indexes and links. Source HTML, graphics from the original and derivative full-text dumps stay outside its release. Instrument Serif and Instrument Sans retain their accompanying SIL Open Font Licenses.</p><p>'+link("https://www.copyright.gov/register/tx-games.html","U.S. Copyright Office guidance on game methods and expressive text")+'</p></section></div>'
    audit=js("analysis/classification/audit.json")
    body+='<h2>Coverage and classification</h2><p>The masthead gives 203. Counting the heading for Rule 0 brings the observed total to '+str(len(rules))+'. Rule 109 omits the hash sign. The numbered headings run consecutively through 203, with no repeated identifier. We retain the host navigation as an opening locator and exclude the advertising footer.</p>'
    body+=table(["Extraction or selection","Rows before","Rows after"],[[E(name),str(before),str(after)] for name,before,after in audit["filters"]])
    body+='<p>All thirteen HTML tables serve page layout. The author also tabulates values inside prose, as in '+link("catalogue.html#rule-142","Rule 142")+'. The front matter contains six numbered examples outside the rule series. The source-form inventory distinguishes those examples and local enumerations from rule headings. It found no labelled appendix or formal lettered or decimal subrule series.</p><p>'+link("assets/source_forms.csv","Download the catalogue of source forms (CSV)")+'</p>'
    body+='<h3>Primary and secondary topics</h3>'+table(["Topic","Primary","Any assignment"],[[E(name),str(audit["primary_categories"].get(name,0)),str(n)] for name,n in sorted(audit["all_category_assignments"].items())])
    body+='<h3>Executability of segments</h3>'+table(["Assessment","Segments"],[[E(name),str(n)] for name,n in audit["statuses"].items()])
    body+='<p class="fine">Every segment contributes once to the primary category and executability columns. Each can contribute to several rows under any assignment. The seven scenario verdicts are reported separately.</p>'
    body+='<p>'+link(REPO+"/blob/master/analysis/classification/audit.json","Heading, reference and join diagnostics")+' · '+link(REPO+"/blob/master/analysis/review/independent-reading.md","Independent internal critical review")+'</p>'
    body+='<h2>Witness register</h2><p>The checksum describes the bytes returned, including archived error pages. Empty fields indicate that the byte downloader obtained no payload.</p>'
    for row in manifest:
        label=row["id"]
        extra={"mirror-005":"The cover identifies v0.05.","december":"The cover identifies v0.20.","sister":"The payload matches the reference digest.","blog":"The retrieved title identifies a later tri-stat version."}.get(label,"")
        body+='<section class="entry" id="w-'+E(label)+'"><h3>'+link(row["url"],label+" · "+row["edition"])+'</h3><div class="fine">'+E(row["role"])+'</div><p>'+E(row["note"]+" "+extra)+'</p>'+fields([("Retrieved",E(row["retrieved"])),("Status",E(row["status"])),("Capture",E(row["capture"])),("Bytes",E(row["bytes"])),("SHA-256",E(row["sha256"]))])+'</section>'
    body+='<p>'+link(REPO+"/blob/master/sources/source_manifest.csv","Machine-readable manifest and resolved URLs")+'</p>'
    page("sources","Sources and method",body)

def main():
    OUT.mkdir(exist_ok=True)
    assets=OUT/"assets"
    shutil.copytree(WEB,assets,dirs_exist_ok=True)
    for src in ["analysis/mathematics/equation_locators.csv","analysis/classification/source_forms.csv"]:
        shutil.copy2(ROOT/src,assets/Path(src).name)
    (OUT/".nojekyll").touch()
    rules,segments,terms,eqs=[js("data/"+s+".json") for s in ("rules","segments","glossary","equations")]
    conflicts=rows("data/contradictions.csv"); scenarios=js("analysis/playability/scenarios.json")
    book=js("manuscript/book.json")
    home(); catalogue(rules,segments,conflicts);glossary(terms);mathematics(eqs)
    toc='<ol class="contents">'+''.join('<li>'+link("book-"+c["id"]+".html",c["title"])+'</li>' for c in book)+'</ol>'
    page("rulebook","Reconstructed rulebook",heading("Reconstructed rulebook","The reading path","Read in order, or open the chapter that answers your question. Each chapter links back to the February text through its catalogue entries.")+toc+'<p class="notice">A labels an explicit source mechanic. B marks a reconstruction, C a hypothetical reading, and D an editorial addition. These letters describe where a statement comes from. The catalogue separately judges whether a procedure can run.</p>')
    for i,c in enumerate(book):
        slug="book-"+c["id"]
        body=heading(c["title"],f"Reconstructed rulebook · Chapter {i+1}")+prose(c,slug,terms)
        previous=book[i-1] if i else None
        following=book[i+1] if i+1<len(book) else None
        body+='<div class="chapter-nav">'+(link("book-"+previous["id"]+".html","Previous · "+previous["title"]) if previous else link("rulebook.html","Rulebook contents"))+(link("book-"+following["id"]+".html","Next · "+following["title"]) if following else link("playability.html","Read the playability trials"))+'</div>'
        page(slug,c["title"],body,"rulebook")
    for file,slug,kicker in [("quickstart","quickstart","At the table"),("critical","assessment","Critical assessment"),("appendix","appendix","Editorial appendix")]:
        record=js("manuscript/"+file+".json")
        body=heading(record["title"],kicker)+prose(record,slug,terms)
        if slug=="assessment":
            body+='<h2>Contradictions and alternatives</h2>'
            for c in conflicts:
                body+='<section class="entry" id="'+E(c["id"])+'"><h3>'+link("#"+c["id"],c["title"])+'</h3><span class="chip">'+E(c["kind"])+'</span><p>'+E(c["observation"])+'</p><p>'+E(c["consequence"])+'</p>'+refs(c["references"].split("|"))+'</section>'
        page(slug,record["title"],body)
    body=heading("Seven playability trials","At the table","Each trial starts with a declared task and ends at the first decision the sources cannot settle, or at a reproducible result.")
    for s in scenarios:
        index("playability.html#"+s["id"],s["title"],"Playability",s["determinate"])
        body+='<section class="scenario" id="'+E(s["id"])+'"><span class="chip">'+E(s["status"])+'</span><h2>'+link("#"+s["id"],s["title"])+'</h2><p class="outcome">'+E(s["determinate"])+'</p><h3>Inputs</h3>'+bullet(s["inputs"])+'<h3>Procedure</h3><ol>'+''.join('<li>'+E(x)+'</li>' for x in s["steps"])+'</ol>'+fields([(k,bullet(s[v])) for k,v in [("Missing","missing"),("Tensions","conflicts"),("Assumptions","assumptions")]])+refs(s["refs"])+'</section>'
    page("playability","Seven playability trials",body)
    graph=graph_build(rules,terms,eqs,scenarios,conflicts,rows("data/cross_references.csv"),segments)
    architecture(graph)
    (assets/"graph.js").write_text("window.EDITION_GRAPH="+json.dumps(graph,ensure_ascii=False,separators=(',',':'))+";\n",encoding="utf-8")
    sourcepage(rows("sources/source_manifest.csv"),segments,rules)
    page("search","Search the edition",heading("Search the edition","Reading tools")+filters("search",[])+'<ul class="search-results entry-list" id="search-results"></ul>')
    for slug,title in NAV:
        index(slug+".html",title,"Reading path","")
    (assets/"index.js").write_text("window.EDITION_INDEX="+json.dumps(INDEX,ensure_ascii=False,separators=(',',':'))+";\n",encoding="utf-8")
    stats=dict(rules=len(rules),segments=len(segments),glossary=len(terms),equations=len(eqs),issues=len(conflicts),indexed=len(INDEX),categories=Counter(s["primary_category"] for s in segments),executability=Counter(s["executability"] for s in segments),trials=Counter(s["status"] for s in scenarios),graph=graph["audit"])
    (ROOT/"analysis/edition-counts.json").write_text(json.dumps(stats,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print(json.dumps(stats,indent=2,ensure_ascii=True))

if __name__=="__main__":
    main()
