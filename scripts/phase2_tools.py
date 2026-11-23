"""Static character materials and progressive enhancement hooks for the Learn and Play route."""
import html
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FIELD_GROUPS = [
    ("Required for a typed rating", "Identity and concept", "Give the character a name and a short role. Rule 47 includes a name and age in its humanoid notation. A concept is this edition’s aid for play.", [47]),
    ("Required for a typed rating", "Campaign scale and starting DP", "Record the number, class, statistic and how the starting value was obtained. The GM selects a campaign magnitude. A benchmark and a rolled C1 baseline are different starting routes.", [11,107]),
    ("Optional", "Age, occupation and source of a comparison", "These establish who is acting. They do not grant a numerical skill, an initiative modifier or an experience award.", [47]),
    ("Derived when the inputs exist", "C2 baseline and AMBS", "Convert an equivalent rating when needed. The square root of C2 DP gives an average of Mind, Body and Soul. The three separate scores cannot be recovered from their average.", [45,49]),
    ("Derived when the inputs exist", "Working PL and LS", "Declare whether both start at default, then name the operation and its amount. The result of a trade depends on the operation chosen.", [3,23,183]),
    ("Derived when the inputs exist", "Lifespan in years", "Convert working C2 LS to C3, then apply the multiplier in rule 6. The reading below 20 C2 is interpretive and can yield more years than a higher rating.", [6,31]),
    ("Optional", "Appearance allocation and remainder", "Rule 47 sketches COM plus remaining power points. A worked case in rule 6 compares C2 PL and C2 COM. Supply both on a common scale before subtracting.", [6,47]),
    ("Power-specific", "Advantages, effect, scope and limitations", "Record each choice and the modified baseline. Add a range, duration, percentage or pool only when a passage gives one. A named limitation alone has no general refund price.", [53,123,138,147,183]),
    ("Power-specific", "Action procedure and unit", "Name a specific use, such as an unobstructed running speed in mph. Record the rule and which of its branches is being used.", [35,39,64,188]),
    ("Unresolved unless a local rule supplies it", "Difficulty, injury, recovery and advancement", "Leave room for a referee’s decision and identify its author. Borrowed health-point comparisons and permissions to take more advantages do not establish a general injury or reward schedule.", [79,147,161]),
]
CHOICES = [
    ["Agility","Increased height","Martial arts"],
    ["Minor force field","Agility","Increased height","Martial arts","Minor resistance to toxins"],
    ["Camouflage","Force field","Minor shape-shifting","Minor healing factor","Minor energy projection","Minor telepathy to control insects"],
    ["Shape-shifting"],
]
SCALES = ["CA","C1","C2","C3","C4","C0"]
POWERS = [("none","No individual effect"),("running","Running · rule 39"),
          ("camouflage","Camouflage · rule 123"),("phase","Desolidification · rule 183"),
          ("time-sight","Two-direction time perception · rule 183"),("cloak","Phasing percentage · rule 53")]


def esc(value):
    return html.escape(str(value), quote=True)


def cases():
    return json.loads((ROOT / "data/phase2/worked_characters.json").read_text(encoding="utf8"))


def assets():
    return '<link rel="stylesheet" href="assets/phase2-tools.css"><script defer src="assets/phase2-tools.js"></script>'


def refs(values):
    return '<span class="tool-refs">'+ ' · '.join(
        f'<a href="catalogue.html#rule-{n}">#{n}</a>' for n in values) + '</span>'


def print_button(target, label):
    return f'<button type="button" class="print-tool" data-print="{target}">{esc(label)}</button>'


def fmt(value):
    return f'{value:,.4f}'.rstrip('0').rstrip('.')


def labelled(label, control):
    return f'<label>{esc(label)}{control}</label>'


def select(name, choices, default=""):
    parts = [f'<select name="{name}">']
    for option in choices:
        value, label = option if isinstance(option,tuple) else (option,option)
        selected = " selected" if value == default else ""
        parts.append(f'<option value="{esc(value)}"{selected}>{esc(label)}</option>')
    return ''.join(parts)+'</select>'


def number(name, value="", minimum=None, step="any"):
    floor = '' if minimum is None else f' min="{minimum}"'
    return f'<input type="number" name="{name}" value="{esc(value)}" step="{step}"{floor}>'


def step_rows(character):
    a, v = character["inputs"], character["expected"]
    origin = f'{a["rating"]} {a["scale"]} DP'
    if a["route"] == "dice":
        origin = f'{a["dice"].replace(",", " + ")} = 40 C1 DP'
    if a["route"] == "mutant":
        origin = '9 C2 → 18 → 27 → 36 C2 DP'
    rows = [
        ("Starting route",origin),
        ("Equivalent baseline", f'{fmt(v["dp"])} C2 DP · {fmt(v["c3"])} C3 DP'),
        ("Average Mind, Body and Soul",f'√{fmt(v["dp"])} = {fmt(v["ambs"])} AMBS'),
        ("Working power and lifespan", f'{fmt(v["pl"])} C2 PL · {fmt(v["ls"])} C2 LS'),
    ]
    return rows


def sheet(character=None, extended=False, key=None):
    key = key or (("full-" if extended else "minimal-")+(character["id"] if character else "blank"))
    label = "Full character sheet" if extended else "Minimal character sheet"
    if character:
        a, v = character["inputs"], character["expected"]
        rows=[("Name and age",f'{a["name"]}, {a["age"]}'),("Role",character["concept"]),*step_rows(character),
              ("Named capability",character["capability"])]
        if extended:
            rows.extend([
                ("Starting route and source",character["decisions"][0]),
                ("Advantages and limitations",", ".join(a["gifts"]) or "No priced modifier selected"),
                ("Trade operation","Divide LS by two and double PL." if a["trade"]=="multiply" else "Equal default pair selected."),
                ("Longevity projection",fmt(v["years"])+" years under the rule 6 reading"),
                ("COM and remaining points","Unassigned. No numeric appearance allocation was chosen."),
                ("Local measure", (fmt(v["speed"])+" mph by rule 39") if v["speed"] is not None else "Use the named effect and its source conditions."),
                ("Open procedure",character["open"]),("Injury, recovery and advancement","Unresolved for this template."),
            ])
    else:
        rows = [(x,"") for x in ["Name and age","Role","Campaign class and starting DP","Source or assumption","Working PL and LS","Named capability and limits"]]
        if extended:
            rows += [(x,"") for x in ["Converted C2 and C3 DP","Average Mind, Body and Soul","Advantages in order","Trade operation and amount","COM and same-scale remainder","Duration, range and units","Local action procedure","Projected lifespan in years","Injury, recovery and advancement","Referee decisions and open questions"]]
    out = f'<section class="sheet-shell" id="{key}"><h3>{esc(label)}'
    if character:
        out += " · "+esc(character["inputs"]["name"])
    out += '</h3><dl class="worksheet">'
    for term,val in rows:
        out += '<dt>'+esc(term)+'</dt><dd>'+ (esc(val) if val else '<span class="blank-field" aria-label="Blank writing space"></span>') +'</dd>'
    out+='</dl><p class="fine">Reconstructed worksheet · '+refs(character["refs"] if character else [3,11,45,47,49,123])+'</p></section>'
    return out+print_button(key,"Print "+("completed " if character else "blank ")+("full sheet" if extended else "minimal sheet"))


def sheets_html():
    out=assets()+'<p>To bring a character to the table, write down who they are, their starting Psyche with its class label, and one thing you want to try. Add a calculation only when a decision calls for it. Rule 47 supplies a compact humanoid profile. These two printable layouts are editorial reconstructions.</p>'
    out+='<p><a href="builder.html">Fill a sheet in the character builder</a> · <a href="characters.html">Read five completed examples</a></p>'
    out+='<h2>Blank worksheets</h2>'+sheet()+sheet(extended=True)
    out+='<h2>What belongs in each field?</h2><p>“Required” below means needed for a typed rating in this worksheet. A source-wide list of mandatory fields has not been recovered.</p>'
    for kind,title,explain,source in FIELD_GROUPS:
        out+=f'<section class="field-note"><h3>{esc(title)}</h3><span class="fine">{esc(kind)}</span><p>{esc(explain)} {refs(source)}</p></section>'
    out+='<h2>Two completed worksheets</h2><p>Mara uses the ordinary human benchmark. Her unassigned fields are deliberate. These print controls include only the selected sheet.</p>'
    first=cases()[0]
    return out+sheet(first)+sheet(first,True)


def characters_html():
    out=assets()+'<p>These five new characters borrow specific numerical examples from the February rules. Their names, occupations, ages and stories are editorial. Each starts at a different decision: choose a benchmark, follow a build, trade one rating for another, or choose a dice pool.</p>'
    out+='<ol class="entry-list">'+''.join(f'<li><a href="#{c["id"]}">{esc(c["inputs"]["name"])}</a> · {esc(c["archetype"])}</li>' for c in cases())+'</ol>'
    for c in cases():
        a,v=c["inputs"],c["expected"]
        out+=f'<section id="{c["id"]}" class="worked-character"><h2>{esc(a["name"])}</h2><p class="character-role">{esc(c["archetype"])}</p><p>{esc(c["concept"])}</p><ol>'+''.join('<li>'+esc(s)+'</li>' for s in c["decisions"])+'</ol>'
        out+=f'<h3>Replay the numbers</h3><p>{esc(step_rows(c)[0][1])}. '
        if a["scale"]=="C1":
            out+='40 raised to log₁₀ 40 gives '+fmt(v["dp"])+' C2. '
        out+=f'The C3 equivalent is {fmt(v["dp"])} raised to log₁₀ {fmt(v["dp"])}, giving {fmt(v["c3"])} C3 DP. Taking the square root of {fmt(v["dp"])} gives {fmt(v["ambs"])} AMBS. '
        if a["trade"]=="multiply":
            out+='Multiply 40 by 2 to get 80 C2 PL and divide 40 by 2 to get 20 C2 LS. '
        else:
            out+='The selected default pair makes PL and LS equal to the C2 baseline. '
        ls=v["ls"];m=22-ls if ls<20 else 2
        out+=f'The rule 6 reading gives {fmt(m)} × ({fmt(ls)} raised to log₁₀ {fmt(ls)}) = {fmt(v["years"])} years.'
        if v["speed"] is not None:
            out+=f' Rule 39 gives 10^({fmt(v["dp"])}/10 − 1) = {fmt(v["speed"])} mph.'
        out+='</p><p>'+esc(c["capability"])+'</p><p><strong>Still open.</strong> '+esc(c["open"])+'</p><p>'+refs(c["refs"])+'</p>'
        out+='<p><a href="builder.html?character='+c["id"]+'">Open this character in the builder</a></p>'+sheet(c,True)+'</section>'
    return out


def builder_html():
    out=assets()+'<p>Choose a source route, then try changing one decision. The working sheet records every operation. Empty fields stay open. Supplied character choices and comparisons do not award a complete playable sheet.</p>'
    out+='<div class="tool-controls preset-box">'+labelled("Worked example",select("preset",[(c["id"],c["inputs"]["name"]+" · "+c["archetype"]) for c in cases()]).replace('<select ','<select id="preset" ',1))+'<button type="button" id="load-preset">Load example</button></div>'
    out+='<form id="character-builder" class="tool-form" autocomplete="off"><fieldset><legend>Character and starting route</legend><div class="tool-grid">'
    out+=labelled("Name",'<input type="text" name="name" maxlength="80">')+labelled("Age (optional)",number("age","",0,1))+labelled("Concept (your description)",'<input name="concept" maxlength="180">')
    out+=labelled("Starting route",select("route",[("benchmark","Supplied baseline or benchmark"),("dice","Rolled faces at C1 · #107"),("mutant","9 C2 mutant template · #123")],"benchmark"))+'</div>'
    out+='<div class="tool-grid" data-route="benchmark">'+labelled("Scale",select("scale",SCALES,"C2"))+labelled("Starting Psyche",number("rating"))+'</div>'
    branches=[("","Choose a branch"),("high","Increasing · original at or above 1"),("low","Reciprocal · original at or below 1")]
    out+='<div data-inverse hidden>'+labelled("Inverse to the C2 working scale",select("branch",branches))+'</div>'
    out+='<div class="tool-grid" data-route="dice" hidden>'+labelled("Sides per die",number("sides",6,2,1))+labelled("Faces, separated by commas",'<input name="dice" placeholder="6, 6, 6">')+'</div>'
    out+='<div data-route="mutant" hidden><p>Start at 9 C2 DP and select the advantages in order. Each choice applies to the newly calculated baseline. The first three menus paraphrase the source lists. For the optional fourth step, shape-shifting is the example the source names.</p><div class="tool-grid">'
    for i, opts in enumerate(CHOICES):
        out+=f'<div data-gift-index="{i}">'+labelled("Choice "+str(i+1),select("gift"+str(i+1),[("","Stop here"),*opts]))+'</div>'
    out+='</div></div></fieldset><fieldset><legend>Power and lifespan</legend><label class="check-label"><input type="checkbox" name="defaultPair"> Start with LS and PL equal to the C2 baseline (B · #23)</label>'
    out+='<div data-trade-options hidden class="tool-grid">'+labelled("Trade",select("trade",[("none","Keep the default pair"),("multiply","Multiply PL and divide LS"),("add","Add to PL and subtract from LS")],"none"))+'<div data-trade-amount hidden>'+labelled("Factor or signed point adjustment",number("amount"))+'</div></div></fieldset>'
    out+='<fieldset><legend>Effect and optional allocations</legend><div class="tool-grid">'+labelled("Effect to examine",select("power",POWERS,"none"))
    out+='<div data-cloak-source hidden>'+labelled("Rule 53 total (hypothetical)",select("cloakSource",[("","Leave unspecified"),("dp","Use DP"),("pl","Use working PL")]))+'</div>'
    out+=labelled("COM allocation in C2 (optional)",number("com","",0))+labelled("Limitation in your own words",'<input name="limitation" maxlength="180">')+'</div></fieldset><button type="button" id="clear-builder">Reset builder</button></form>'
    out+='<noscript><p>Enable JavaScript to calculate interactively. Blank sheets and all five worked replays are also available as ordinary HTML.</p></noscript>'
    out+='<section id="built-sheet" class="sheet-shell" aria-live="polite"><h2>Your working sheet</h2></section>'+print_button("built-sheet","Print this character sheet")
    return out+'<script type="application/json" id="character-presets">'+json.dumps(cases(),ensure_ascii=False).replace("<","\\u003c")+'</script>'


def demo(key, title, explanation, controls, boundary, rules):
    return f'<section id="{key}" class="play-demo"><h2>{esc(title)}</h2><p>{esc(explanation)}</p><form class="tool-form" data-demo="{key}"><div class="tool-grid">{controls}</div><output aria-live="polite"></output><button type="reset">Reset {esc(title.lower())}</button></form><p class="fine">{esc(boundary)} {refs(rules)}</p></section>'


def playground_html():
    out=assets()+'<p>Each instrument answers a question a player can ask at the table. Change values to explore its limits. Only the dice demonstration assumes fair, independent dice.</p>'
    branches=[("","Choose a branch"),("high","Increasing branch"),("low","Reciprocal branch")]
    out+=demo("scale","Equivalent scales","How would the same rating look elsewhere on the class ladder? Preserve DP, PL or LS while changing its numeral.",
        labelled("Numerical rating",number("rating",20))+labelled("From",select("from",SCALES,"C2"))+labelled("To",select("to",SCALES,"C3"))+labelled("Branch for backwards conversion",select("branch",branches)),
        "Positive inputs only. A backwards step from an output greater than one has two roots. C0 needs a local definition.",[5,45,161])
    out+=demo("trade","Power and lifespan","Starting at equal DP, PL and LS, spend lifespan to increase effective power. A fractional multiplier or a negative addition reverses the direction.",
        labelled("Starting C2 DP",number("dp",40))+labelled("Operation",select("operation",[("multiply","Multiply PL / divide LS"),("add","Add to PL / subtract from LS")],"multiply"))+labelled("Factor or adjustment",number("amount",2)),
        "Keep the resulting ratings positive. The multiplier and the offset preserve different quantities. The final conversion to years uses an interpreted branch (B).",[3,6,183])
    out+=demo("speed","Running and mutant movement","Use the same supplied baseline with either movement passage. One route calibrates running on C2. The other reads a mutant’s numerical C3 rating as mph.",
        labelled("C2 baseline",number("dp",20))+labelled("Movement rule",select("law",[("running","Running · #39"),("mutant","Mutant movement · #64")],"running")),
        "Use a positive rating. Comparing both results for one runner assumes that rule 64 covers running. Neither output answers an opposed chase.",[39,64])
    out+=demo("advantages","Successive advantages","Follow one path through the low-mutant build. The demonstration chooses a named effect at each stage. The builder lets you change these choices.",
        labelled("Number of advantages",select("count",["0","1","2","3","4"],"3")),
        "The template illustrates four steps. Extending it to other character types or treating each step as an experience award requires another rule.",[123,147])
    out+=demo("damage","Fictional damage dice","Find the pool yielded by a specified game effect. The mutant calculation takes C2 DP. The two one-use alternatives take C3 PL. Changing the selector changes the meaning of the input numeral.",
        labelled("Rating in the selected rule’s units",number("rating",49))+labelled("Fictional effect",select("law",[("subtract","One-use C3 PL · subtract one die"),("root","Alternative C3 PL · square root"),("mutant","Mutant C2 DP · square of tenths")],"subtract")),
        "Use positive ratings. Fractional dice, injury, resistance, recovery and accumulated damage require decisions beyond these pool formulas.",[73,118,146])
    out+=demo("roll","Success thresholds","Compare two readings of the source’s high-roll language, or test the specific low-roll example. These procedures require different inputs.",
        labelled("Threshold reading",select("law",[("66","66% of maximum · hypothetical"),("two-thirds","Two thirds of maximum · hypothetical"),("under","Roll under a desired rating · #188")],"66"))+
        '<div data-roll-input="high">'+labelled("Number of d6",number("count",3,1,1))+'</div><div data-roll-input="under" hidden>'+labelled("Desired C3 rating",number("c3",35))+'</div><div data-roll-input="under" hidden>'+labelled("Starting C2 baseline",number("baseline",10))+'</div><div data-roll-input="under" hidden>'+labelled("Inverse branch",select("branch",branches,"high"))+'</div>',
        "Fair d6 probabilities support 1–40 dice in this reader. The denominator in the high-roll interpretation is C. Rule 188 gives an inclusive low target but does not specify a probability distribution here.",[17,35,45,188])
    return out+'<noscript><p>These controls require JavaScript. The <a href="mathematics.html">equation register</a> gives static numerical examples.</p></noscript>'
