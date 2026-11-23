"""Index observable forms in the pinned witness. A chart mention is not a data table."""

import csv
import re


# Document position, type and paraphrased interpretation checked against the witness.
FORMS = [
    (0, "Host paratext", "Title, credits and links placed around the author's material."),
    (11, "Disclaimer", "Warnings about three numbered entries recur at block 33."),
    (12, "Disclaimer", "An extended authorial disclaimer also introduces the game's use of dice."),
    (27, "Administrative inventory", "The author reports page, rule and equation totals."),
    (38, "Numbered examples", "Examples 1–6 occupy blocks 38–43. They are independent of the rule numbering."),
    (45, "Inline numbered list", "Three narrative alternatives in a television comparison."),
    (46, "Disclaimer", "Authorial qualification of the preceding HERO theory."),
    (47, "Recipe", "An unnumbered culinary digression, followed by a return to the game."),
    (49, "Preface", "The author's account of the origin of the magnitudes and the central expression."),
    (51, "Introduction", "A grade calculation precedes the glossary and reviews."),
    (52, "Reading index", "Sixteen hints direct readers to examples. They are not entries in a definition dictionary."),
    (69, "Reviews of other games", "Reviews span blocks 69–86."),
    (70, "Inline numbered list", "Two reasons for a narrative interpretation of fictional creatures."),
    (73, "External table", "References to armour and life-point comparisons in Synnibarr."),
    (76, "External table", "d20 Modern size modifiers."),
    (87, "Film reviews", "Three films occupy blocks 88–90."),
    (91, "Core-rules heading", "The words announcing the numbered series abut in the source markup."),
    (97, "Inline numbered alternatives", "Rule 5 numbers four C0 psyche mappings. These numbers are local to the entry."),
    (113, "Inline table", "Rule 21 lists materials and assigned numerical strengths in prose."),
    (123, "Inline alternatives", "Rule 31 describes a second immortality formula and compares it to the first."),
    (147, "Inline value series", "Rule 55 gives letter positions, multipliers and resulting values."),
    (157, "Table comparison", "Rule 65 contrasts a table of advantages with values derived from the author's rule."),
    (161, "Inline table", "Rule 69 lists rating bands and population exponents."),
    (185, "Inline table", "Rule 93 supplies medium-specific coefficients in a sentence."),
    (192, "Inline table", "Rule 100 calls a sequence of rating-dependent values a chart."),
    (195, "Inline numbered procedure", "Rule 103 enumerates seven operations for a character's appearance and power."),
    (201, "Inline alternatives", "Rule 109 distinguishes two further shrinking equations."),
    (215, "Inline sequence", "Rule 123 demonstrates four consecutive advantage costs."),
    (220, "Inline alternatives", "Rule 128 describes three alternative clone counts."),
    (231, "External table", "Rule 139 compares HERO and Marvel object statistics."),
    (234, "Inline table", "Rule 142 aligns four heights with masses in two units inside a prose paragraph."),
    (237, "Table comparison", "Rule 145 discusses the low end of a technology-level chart."),
    (238, "Inline table", "Rule 146 lists five C2 ratings and corresponding damage pools."),
    (244, "External table", "Rule 151 continues across a paragraph break with a GURPS technology-table comparison."),
    (256, "Inline numbered chronology", "Rule 163 numbers three successive IQ formulas and separately lists four materials."),
    (259, "Inline sequence", "Rule 166 distinguishes a first treatment as a mutant and a second robot-specific assessment."),
    (264, "Inline numbered alternatives", "Rule 171 distinguishes two modes of travelling in time."),
    (281, "External tables", "Rule 188 refers to tables in HERO and d20 Modern and reinterprets their values."),
    (282, "Inline numbered alternatives", "Rule 189 numbers three DCV conventions and refers to a HERO table."),
    (296, "Inline numbered alternatives", "Rule 203 numbers an education calculation and its geopolitical extrapolation."),
]
TABLES = [
    (0,"Host tracking and credit strip"), (1,"Title panel"), (4,"Navigation bar"),
    (5,"Edition links and page wrapper"), (10,"Opening title and disclaimers"),
    (27,"Edition masthead"), (28,"Statistics and introductory prose"),
    (47,"Recipe panel"), (49,"Preface panel"), (50,"Cosmic-character note"),
    (51,"Introduction, indexes and reviews"), (91,"Numbered core-rules panel"),
    (None,"Blank spacing before the host advertisement"),
]


def build(raw, segments, offsets, blocks, target):
    rows = []
    def append(form, block, text, byte="", segment=None):
        if segment is None and block is not None:
            off = offsets[block]
            segment = next(s for s in segments if s["start_offset"]<=off<s["end_offset"])
        rows.append(dict(form=form, segment_id=segment["id"] if segment else "",
                         rule_number=segment["original_id"] if segment else "", block=block,
                         raw_byte_offset=byte, editorial_note=text))
    tables = list(re.finditer(br"<table\b[^>]*>", raw,re.I))
    if len(tables)!=len(TABLES):
        raise ValueError("Layout-table inventory no longer matches the witness.")
    for (block, purpose), m in zip(TABLES,tables,strict=True):
        append("HTML layout table",block,purpose,m.start())
    for block,form,text in FORMS:
        append(form,block,text)
    for segment in segments:
        if "Equation notation" in segment["source_features"]:
            append("Mathematical notation",segment["start_block"],
                   "Equality, power or common-log notation occurs in this segment. This index does not count distinct equations.",
                   segment=segment)
    with target.open("w",encoding="utf8",newline="") as f:
        out=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator="\n")
        out.writeheader()
        out.writerows(rows)
    return {"html_tables":len(tables),"identified_tabular_gameplay_html_elements":0,
            "notation_segments_before":len(segments),"notation_segments_after":sum(r["form"]=="Mathematical notation" for r in rows),
            "forms_reviewed":len(FORMS),"rows":len(rows),
            "appendix_label_occurrences":sum(len(re.findall(r"\bappendi(?:x|ces)\b",b,re.I)) for b in blocks),
            "lettered_or_decimal_rule_labels":sum(len(re.findall(r"\brule\s*#\s*\d+(?:[a-z]|\.\d+)\b",b,re.I)) for b in blocks)}
