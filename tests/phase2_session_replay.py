"""Replay the two transcripts against independently specified provenance and state transitions."""
from collections import Counter
from html.parser import HTMLParser
import json
import math
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import phase2_session as publication


class Markup(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = []
        self.h1 = 0

    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        self.h1 += int(tag == "h1")
        if "id" in values:
            self.ids.append(values["id"])


# These are the test's evidential readings of the decisions, independent of their display labels.
ORIGINAL = [
    ("setup", "D"), ("human-baseline", "A"), ("hero-baseline", "B"), ("grant-power", "D"),
    ("state-pace", "D"), ("pace-cost", "A"), ("pace-outcome", "B"), ("copy-count", "A"),
    ("copy-agency", "C"), ("allow-caller", "D"), ("trade-arithmetic", "A"), ("offer-trade", "C"),
    ("check-other-tests", "B"), ("offer-bargain", "D"), ("consensual-end", "D"), ("original-record", "B"),
]
REPLAY = [
    ("setup", "D"), ("human-baseline", "A"), ("hero-baseline", "B"), ("grant-power", "D"),
    ("state-pace", "D"), ("pace-cost", "A"), ("pace-outcome", "B"), ("copy-count", "A"),
    ("allow-caller", "D"), ("opposition", "D"), ("offer-trade", "D"), ("trade-arithmetic", "A"),
    ("resolve-contest", "D"), ("offer-bargain", "D"), ("close-scene", "D"), ("recovery", "D"),
]
SOURCE_DECISIONS = {
    "human-baseline": 49, "hero-baseline": 182, "pace-cost": 39, "pace-outcome": 39,
    "copy-count": 18, "copy-agency": 128, "trade-arithmetic": 3, "check-other-tests": 188,
    "original-record": 45,
}
HOUSE_DECISIONS = {
    "setup": {"r2"}, "grant-power": {"r1", "r2", "r4"}, "state-pace": {"r2"},
    "allow-caller": {"r2"}, "opposition": {"r3"}, "offer-trade": {"r4"},
    "resolve-contest": {"r2", "r3"}, "offer-bargain": {"r2"}, "close-scene": {"r2", "r4"},
    "recovery": {"r4"},
}


def audit_dialogue(beats, expected, ids, adapted):
    turns = [turn for beat in beats for turn in beat["moves"]]
    assert [(turn[2], turn[1]) for turn in turns] == expected
    cited = []
    for turn in turns:
        speaker, layer, event, line, note, refs, *rest = turn
        assert speaker and line and note
        cited.extend(refs)
        if event in SOURCE_DECISIONS:
            assert SOURCE_DECISIONS[event] in refs
        if layer in "ABC":
            assert refs and not any(rest), event
        if adapted and layer == "D":
            assert set(rest[0].split()) == HOUSE_DECISIONS[event], event
        if not adapted:
            assert not rest, "Original transcript silently imported a house-rule key"
    missing = set(cited) - ids
    assert not missing, missing
    return {
        "decision_rows_before": len(turns), "decision_rows_after": len(turns),
        "status_counts": dict(Counter(turn[1] for turn in turns)),
        "source_reference_occurrences": len(cited), "source_reference_matches": len(cited),
        "unmatched_source_keys": sorted(missing),
    }


def replay(scene, moves, adapted):
    people = {p["name"]: p for p in scene["people"]}
    params = scene["inputs"]
    kit, double, vale = [people[k] for k in ("Kit", "Double", "Vale")]
    state = dict(ls=kit["ls"], pl=kit["pl"], dp=kit["dp"], route=params["initial_route"],
                 copies=None, calls=0, ended=False, active_trade=False)
    snapshots = {}
    for step, _ in moves:
        if step == "human-baseline":
            state["ambs"] = math.sqrt(kit["dp"])
        elif step == "pace-cost":
            state["required_c2"] = 10 * (1 + math.log10(params["pace_mph"]))
        elif step == "pace-outcome":
            state["at_selector"] = kit["dp"] >= state["required_c2"]
        elif step == "copy-count":
            state["copies"] = double["dp"] / params["copy_rating_c3"] - 1
            state["alternative_copies"] = double["dp"] / params["alternative_copy_rating_c3"] - 1
            assert state["copies"].is_integer()
        elif step == "allow-caller":
            assert state["copies"] == 1
            state["calls"] = 1 + int(state["copies"])
        elif step == "trade-arithmetic":
            f = params["boost_factor"]
            new_ls, new_pl = kit["ls"] / f, kit["pl"] * f
            state["proposed_trade"] = [new_ls, new_pl]
            if adapted:
                assert state["active_trade"] and not state["ended"]
                state.update(ls=new_ls, pl=new_pl)
        elif step == "offer-trade" and adapted:
            assert not state["active_trade"]
            state["active_trade"] = True
        elif step == "resolve-contest":
            assert adapted and state["at_selector"] and state["calls"] == params["required_callers"]
            if state["pl"] > vale["pl"]:
                state["route"] = params["rescue_route"]
        elif step == "consensual-end":
            assert not adapted and state["at_selector"] and state["calls"] == params["required_callers"]
            state.update(ended=True, route=params["rescue_route"])
        elif step == "close-scene":
            assert adapted and state["active_trade"]
            state.update(ended=True, copies=0)
        elif step == "recovery":
            assert state["ended"] and state["active_trade"]
            state.update(ls=kit["ls"], pl=kit["pl"], active_trade=False)
        snapshots[step] = state.copy()
    return snapshots


def check():
    scene = publication.source("session")
    adapted = publication.source("replay")
    trials = publication.source("configurations")["trials"]
    rules = publication.source("adaptation")["rules"]
    source_rows = json.loads((ROOT / "data/rules.json").read_text(encoding="utf-8"))
    source_keys = [int(row["original_id"]) for row in source_rows]
    assert len(source_keys) == len(set(source_keys))
    ids = set(source_keys)
    original_audit = audit_dialogue(scene["original"], ORIGINAL, ids, False)
    adapted_audit = audit_dialogue(adapted["beats"], REPLAY, ids, True)

    expected_fields = {"id", "name", "procedure", "gap", "refs", "alternatives", "minimal", "effect", "philosophy"}
    assert [rule["id"] for rule in rules] == ["r1", "r2", "r3", "r4"]
    for rule in rules:
        assert set(rule) == expected_fields and all(rule.values())
        assert set(rule["refs"]) <= ids
    assert len(trials) == 5
    for name, verdict, refs, setup, outcome, limit in trials:
        assert all((name, verdict, refs, setup, outcome, limit))
        assert set(refs) <= ids

    orig = replay(scene, ORIGINAL, False)
    alt = replay(scene, REPLAY, True)
    for trace in (orig, alt):
        assert trace["human-baseline"]["ambs"] == 4
        assert math.isclose(trace["pace-cost"]["required_c2"], 14.771212547196624)
        assert trace["pace-outcome"]["at_selector"]
        assert (trace["copy-count"]["copies"], trace["copy-count"]["alternative_copies"]) == (1, 3)
        assert trace["copy-count"]["calls"] == 0 and trace["allow-caller"]["calls"] == 2

    # A calculable offer does not enact the operation in the source-led reading.
    assert orig["trade-arithmetic"]["proposed_trade"] == [8, 32]
    assert orig["offer-bargain"]["route"] == "west"
    assert all((row["ls"], row["pl"]) == (16, 16) for row in orig.values())
    assert orig["original-record"]["route"] == "east" and orig["original-record"]["copies"] == 1
    assert alt["opposition"]["route"] == "west"
    assert (alt["trade-arithmetic"]["ls"], alt["trade-arithmetic"]["pl"]) == (8, 32)
    assert alt["resolve-contest"]["route"] == "east"
    assert alt["close-scene"]["copies"] == 0 and alt["close-scene"]["active_trade"]
    assert (alt["recovery"]["ls"], alt["recovery"]["pl"], alt["recovery"]["dp"]) == (16, 16, 16)
    assert alt["recovery"]["route"] == "east"

    # Re-run the contested move without taking the option, and then with equal ratings.
    no_trade = [(e, l) for e, l in REPLAY if e not in {"offer-trade", "trade-arithmetic", "close-scene", "recovery"}]
    assert replay(scene, no_trade, True)["resolve-contest"]["route"] == "west"
    tie_scene = json.loads(json.dumps(scene))
    tie_scene["people"][0]["pl"] = tie_scene["people"][2]["pl"]
    assert replay(tie_scene, no_trade, True)["resolve-contest"]["route"] == "west"
    assert 16 < 10 * (1 + math.log10(10))
    assert round(10 ** math.sqrt(math.log10(35)) - 10) == 7
    assert round(17.7 - 10) == 8

    for renderer in (publication.session_html, publication.configurations_html,
                     publication.adaptation_html, publication.replay_html):
        page = Markup()
        page.feed(renderer())
        assert page.h1 == 0 and len(page.ids) == len(set(page.ids))
    return {
        "casestudy": scene["id"], "original_dialogue": original_audit,
        "adapted_dialogue": adapted_audit, "source_rule_keys_checked": len(ids),
        "duplicate_original_ids": len(source_keys) - len(ids), "source_edition": "v0.30",
        "configurations_checked": len(trials), "adaptation_rules_checked": len(rules),
        "additional_design_fields_per_rule": 6,
        "observed_original": "east by consent, Kit 16 LS / 16 PL; one copy created, expiry open",
        "observed_adapted": "east by contest, Kit 8 LS / 32 PL until rest; zero copies after close",
        "counterfactuals": {"decline_trade": "west", "tie_at_18": "west"},
        "result": "pass",
    }


if __name__ == "__main__":
    print(json.dumps(check(), indent=2))
