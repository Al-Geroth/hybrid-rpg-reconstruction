"""Navigation, reading paths and search entries for the Learn and Play edition."""
from html import escape
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEARN = [
    ("handbook", "HYBRID in Plain English"),
    ("sheets", "Creating a character"),
    ("characters", "Worked characters"),
    ("builder", "Character builder"),
    ("handbook.html#scales", "Understanding the scales"),
    ("playground", "Mathematical playground"),
    ("session", "An example session"),
    ("configurations", "Minimum playable configurations"),
    ("adaptation", "Experimental reconstruction"),
    ("replay", "The session replayed"),
]


def href(key):
    return key if ".html#" in key else key + ".html"


def nav_items(items, current):
    links = []
    for key, label in items:
        active = ' aria-current="page"' if current == key else ''
        links.append(f'<a{active} href="{href(key)}">{escape(label)}</a>')
    return ''.join(links)


def navigation(reference_items, current, menu):
    research = [("reference", "Research and reference"), *reference_items, ("atlas", "Mathematical atlas")]
    learn = [("index", "Start here"), *LEARN]
    groups = [("Learn and play", learn), ("Research and reference", research)]
    if not menu:
        groups = [groups[0] if current in dict(learn) else groups[1]]
    sections = []
    for label, items in groups:
        sections.append(f'<div class="nav-section"><h2>{label}</h2>{nav_items(items, current)}</div>')
    return '<nav aria-label="Edition contents">' + ''.join(sections) + '</nav>'


def paths(items):
    return '<div class="paths">' + ''.join(
        f'<a href="{href(key)}"><strong>{escape(title)}</strong><span>{escape(desc)}</span></a>'
        for key, title, desc in items
    ) + '</div>'


def research_html():
    return paths([
        ("rulebook", "Reconstructed rulebook", "Eleven chapters with a passage behind every substantive procedure."),
        ("quickstart", "Read the quickstart", "Work through one starting rating and its consequences."),
        ("catalogue", "Rule catalogue", "Search the numbered rules and the unnumbered passages."),
        ("glossary", "Glossary", "Look up a symbol and the contexts in which it changes meaning."),
        ("mathematics", "Detailed mathematical register", "Read the domains, numerical checks and competing interpretations."),
        ("atlas", "Mathematical atlas", "Follow the remaining candidates into play and see which calculations end there."),
        ("architecture", "System architecture", "Explore the typed graph of calculations and citations."),
        ("playability", "Seven playability trials", "Inspect the starting inputs and the last recoverable step."),
        ("assessment", "Critical assessment", "Read the argument and the register of conflicts."),
        ("appendix", "Editorial appendix", "How the edition treats commentary and grades evidence."),
        ("sources", "Sources and methodology", "Consult the archived witnesses, digests and extraction audit."),
    ])


def landing_html(curve):
    sheet = """
    <figure class="plate build-plate">
      <div class="platehead"><span>Character sheet</span><span>Rule 123</span></div>
      <div class="build-name">A low-powered mutant</div>
      <div class="build-line"><span>Starting baseline</span><b>9</b><small>C2 DP</small></div>
      <div class="build-line"><span>Choose agility</span><b>18</b><small>× 2</small></div>
      <div class="build-line"><span>Add height</span><b>27</b><small>× 1½</small></div>
      <div class="build-line"><span>Take camouflage</span><b>36</b><small>× 1⅓</small></div>
      <figcaption class="plate-foot"><span>Final baseline · 36 C2 DP</span><a href="characters.html">Worked sheets</a></figcaption>
    </figure>"""
    start = """<div class="hero"><div><div class="eyebrow">Learn and play · HYBRID v0.30</div>
    <h1>Deciphering<br><i>HYBRID</i></h1><p class="lede">Give a mutant camouflage. Find out whether a courier can keep up with a moving float. Follow the players through the moment a number on a sheet changes the scene.</p>
    <div class="actions"><a class="button" href="handbook.html">Read the handbook</a><a href="builder.html">Build a character</a></div></div>"""
    learn_paths = paths([
        ("handbook", "HYBRID in Plain English", "Start with a person, a power and an action."),
        ("sheets", "Make a character sheet", "Choose a creation route and print a sheet for the table."),
        ("characters", "Meet five characters", "See each choice, its arithmetic and the blank fields it leaves."),
        ("playground", "Try the mathematics", "Change a rating and see what the character can do."),
        ("session", "Sit in on a session", "Listen to two players and a referee run a rescue."),
        ("adaptation", "Play the experimental game", "Use explicit house rules to carry a conflict through recovery."),
    ])
    reference_paths = paths([
        ("reference", "Research and reference", "Browse the complete critical edition and its methods."),
        ("quickstart", "Read the quickstart", "Walk through the shortest reconstruction."),
        ("catalogue", "Rule catalogue", "Find a passage by number, topic or executability."),
        ("atlas", "Mathematical atlas", "Trace the inputs, outputs and limits of each family."),
    ])
    return (start + sheet + '</div><section class="routes"><div><h2>Learn and play</h2>'
            '<p>Choose a character, bring the sheet to the table and see what happens next.</p></div>'
            + learn_paths + '</section><section class="routes"><div><h2>Research and reference</h2>'
            '<p>Follow a question back to Matthew/C++’s text or check how a result was calculated.</p></div>'
            + reference_paths + '</section><details class="note home-plot" id="magnitude-plate">'
            '<summary>View the Rule 45 magnitude curve</summary>' + curve + '</details>')


class SearchSections(HTMLParser):
    """Index complete sections with stable fragment IDs, plus the page introduction."""
    def __init__(self):
        super().__init__()
        self.records = {}
        self.stack = []
        self.skip = 0
        self.in_heading = False

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag in ("script", "style"):
            self.skip += 1
        if tag in ("section", "article"):
            self.stack.append(attrs.get("id") or (self.stack[-1] if self.stack else ""))
        if tag in ("h2", "h3"):
            self.in_heading = True

    def handle_endtag(self, tag):
        if tag in ("section", "article") and self.stack:
            self.stack.pop()
        if tag in ("script", "style"):
            self.skip -= 1
        if tag in ("h2", "h3"):
            self.in_heading = False

    def handle_data(self, data):
        if self.skip or not data.strip():
            return
        key = self.stack[-1] if self.stack else ""
        record = self.records.setdefault(key, {"title": "", "text": []})
        if self.in_heading and not record["title"]:
            record["title"] = data.strip()
        record["text"].append(data)


def publish(page, heading, index):
    from phase2_atlas import atlas_html
    from phase2_session import adaptation_html, configurations_html, replay_html, session_html
    from phase2_tools import builder_html, characters_html, playground_html, sheets_html

    handbook = (ROOT / "manuscript/phase2/handbook.html").read_text(encoding="utf-8")
    pages = [
        ("handbook", "HYBRID in Plain English", handbook),
        ("sheets", "Creating a character", sheets_html()),
        ("characters", "Worked characters", characters_html()),
        ("builder", "Character builder", builder_html()),
        ("playground", "Mathematical playground", playground_html()),
        ("session", "An example session", session_html()),
        ("configurations", "Minimum playable configurations", configurations_html()),
        ("adaptation", "HYBRID: Minimal Playable Reconstruction", adaptation_html()),
        ("replay", "The session replayed", replay_html()),
        ("atlas", "Mathematical atlas", atlas_html()),
        ("reference", "Research and reference", research_html()),
    ]
    for slug, title, content in pages:
        if slug in {"atlas", "reference"}:
            path = "Research and reference"
        elif slug in {"adaptation", "replay"}:
            path = "Learn and play · Experimental game"
        else:
            path = "Learn and play"
        parser = SearchSections()
        parser.feed(content)
        index(slug + ".html", title, path, " ".join(parser.records.get("", {}).get("text", []))[:3500])
        for anchor, record in parser.records.items():
            if anchor and record["title"]:
                index(slug + ".html#" + anchor, record["title"], title, " ".join(record["text"]))
        page(slug, title, heading(title, path) + content)
