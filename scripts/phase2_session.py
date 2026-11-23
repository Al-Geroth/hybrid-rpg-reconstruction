"""Render the two readings of the Lantern House rescue without client-side dependencies."""
from html import escape
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEXT = ROOT / "manuscript" / "phase2"
LAYERS = {
    "A": "Explicit source procedure",
    "B": "Supported reconstruction",
    "C": "Uncertain interpretation",
    "D": "Referee decision or editorial addition",
}


def source(name):
    return json.loads((TEXT / (name + ".json")).read_text(encoding="utf-8"))


def references(numbers):
    return " · ".join(f'<a href="catalogue.html#rule-{int(number)}">Rule {int(number)}</a>'
                      for number in numbers)


def notes(title, content):
    return f'<details class="note"><summary>{escape(title)}</summary>{content}</details>'


def paragraphs(*texts):
    return "".join(f"<p>{escape(text)}</p>" for text in texts)


def cast(scene):
    rows = []
    for person in scene["people"]:
        value = f'{person["dp"]} {person["scale"]} DP'
        if "ls" in person:
            value += f' · {person["ls"]} LS · {person["pl"]} PL (same scale)'
        if "com" in person:
            value += f' · appearance allocation {person["com"]} C3'
        rows.append("<tr><th scope=\"row\">" + escape(person["name"]) + "</th><td>"
                    + escape(f'{person["player"]} · {person["role"]}') + "</td><td>"
                    + escape(value) + "</td></tr>")
    table = ('<div class="scrollbox"><table class="data-table"><thead><tr>'
             '<th scope="col">Character</th><th scope="col">At the table</th>'
             '<th scope="col">Starting sheet</th></tr></thead><tbody>'
             + "".join(rows) + "</tbody></table></div>")
    reasons = "".join(f'<p><strong>{escape(p["name"])}.</strong> {escape(p["reason"])} '
                      f'{references(p["refs"])}</p>' for p in scene["people"])
    intentions = "".join(f"<li>{escape(i)}</li>" for i in scene["intentions"])
    return (table + notes("Where the starting numbers come from", reasons)
            + notes("Intentions fixed for both readings", "<ul>" + intentions + "</ul>"))


def dialogue(beats):
    parts = []
    for index, beat in enumerate(beats, 1):
        parts.append(f'<section id="beat-{index}"><h2>{escape(beat["title"])}</h2>'
                     + paragraphs(beat["lead"]))
        for turn in beat["moves"]:
            speaker, layer, move, line, note, refs, *extra = turn
            adopted = extra[0].split() if extra else []
            anchors = [references(refs)] if refs else []
            anchors.extend(f'<a href="adaptation.html#{r}">{r.upper()}</a>' for r in adopted)
            evidence = paragraphs(note)
            if anchors:
                evidence += '<p class="refs">' + " · ".join(anchors) + "</p>"
            parts.append(f'<div class="session-turn" id="move-{move}"><p><strong>{escape(speaker)}</strong> '
                         f'“{escape(line)}”</p>'
                         + notes(f"{layer} · {LAYERS[layer]}", evidence) + "</div>")
        parts.append("</section>")
    return "".join(parts)


def session_html():
    scene = source("session")
    return ('<div class="prose">'
            + paragraphs(scene["premise"],
                         "This written playtest has two players and a GM. Follow Jo and Ren’s choices first. Each expandable letter explains who supplied the procedure. The last exchange records exactly how the table reached an ending.")
            + '<h2>Who sits down to play?</h2>' + cast(scene)
            + dialogue(scene["original"])
            + '<p><a href="configurations.html">Test smaller complete loops</a> · '
              '<a href="replay.html">See the same lift under the experimental rules</a></p></div>')


def configurations_html():
    data = source("configurations")
    out = ['<div class="prose">', paragraphs(data["intro"])]
    for index, (name, verdict, refs, setup, result, boundary) in enumerate(data["trials"], 1):
        out.append(f'<section id="trial-{index}"><h2>{escape(name)}</h2>'
                   f'<p class="fine">{escape(verdict)}</p>' + paragraphs(setup, result, boundary)
                   + f'<p class="refs">{references(refs)}</p></section>')
    out.append('<p><a href="adaptation.html">Read the four house rules used to close an opposed rescue</a>'
               ' · <a href="session.html">Return to the original table</a></p></div>')
    return "".join(out)


def adaptation_html():
    data = source("adaptation")
    out = ['<div class="prose">',
           paragraphs(data["purpose"], data["setup"])]
    labels = [("gap", "Gap addressed"), ("refs", "Relevant original rules"),
              ("alternatives", "Alternatives considered"), ("minimal", "Why this addition is small"),
              ("effect", "Effect in play"), ("philosophy", "Effect on the design")]
    for rule in data["rules"]:
        parts = []
        for field, label in labels:
            val = references(rule["refs"]) if field == "refs" else escape(rule[field])
            parts.append(f"<dt>{escape(label)}</dt><dd>{val}</dd>")
        out.append(f'<section id="{rule["id"]}"><h2>{rule["id"].upper()}. {escape(rule["name"])}</h2>'
                   '<p class="fine">D · Experimental house rule</p>' + paragraphs(rule["procedure"])
                   + notes("Design choices and source passages", '<dl class="datafields">'
                           + "".join(parts) + '</dl>') + '</section>')
    out.append('<h2>Between sessions</h2>' + paragraphs(data["advancement"])
               + '<p class="refs">' + references([45,123,125]) + '</p>'
               '<p><a href="replay.html">Play through the lift again with these four additions</a></p></div>')
    return "".join(out)


def replay_html():
    data = source("replay")
    scene = source("session")
    return ('<div class="prose">' + paragraphs(data["intro"])
            + notes("Same cast, ratings and intentions", cast(scene))
            + dialogue(data["beats"]) + '<h2>What changed?</h2>' + paragraphs(data["comparison"])
            + '<p><a href="session.html">Read the source-led exchange</a> · '
              '<a href="adaptation.html">Inspect the four additional rules</a></p></div>')
