"""Assemble the annotated graph and audit the population behind each edge count."""
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "analysis/dependencies"

# Permitted source and target node types. Citations and prerequisites are distinct.
RELATIONS = {
    "cites passage": ({"eq", "term", "case"}, {"rule", "passage"}),
    "requires calculation": ({"eq"}, {"eq"}),
    "related concept": ({"term"}, {"term"}),
    "documents tension": ({"issue"}, {"rule", "passage"}),
    "explicit reference": ({"rule", "passage"}, {"rule"}),
    "states calculation": ({"rule"}, {"eq"}),
    "supports interpretation": ({"rule"}, {"eq"}),
    "defines term": ({"rule"}, {"term"}),
    "opposing roll conventions": ({"eq"}, {"eq"}),
    "gives a conflicting point estimate": ({"eq"}, {"eq"}),
}


def build(rules, terms, equations, scenarios, contradictions, xrefs, segments):
    nodes = {}
    mentions = Counter()
    unmatched = []

    def node(key, label, kind, link):
        if key in nodes:
            raise ValueError(f"Duplicate graph identifier {key}")
        nodes[key] = dict(id=key, label=label, kind=kind, link=link)

    def edge(source, target, kind):
        mentions[(source, target, kind)] += 1

    def passage(ref):
        return "front" if ref == "preface" else "rule-" + ref

    node("front", "Front matter (general citation)", "passage", "catalogue.html#front")
    for item in rules:
        node(item["id"], "Rule " + item["original_id"], "rule", "catalogue.html#" + item["id"])
    segment_parents = {}
    for segment in segments:
        key = segment["id"]
        if key in segment_parents:
            raise ValueError(f"Duplicate segment identifier {key}")
        parent = segment["rule_id"]
        if parent is not None and parent not in nodes:
            raise ValueError(f"Unknown parent {parent} for segment {key}")
        segment_parents[key] = parent
        if parent is None:
            node(key, segment["title"], "passage", "catalogue.html#" + key)

    for group, prefix, page, label in [
        (terms, "term", "glossary", "term"),
        (equations, "eq", "mathematics", "title"),
        (scenarios, "case", "playability", "title"),
        (contradictions, "issue", "assessment", "title")
    ]:
        for item in group:
            key = prefix + "-" + item["id"]
            node(key, item[label], prefix, page + ".html#" + item["id"])
            if prefix == "issue":
                for ref in item["references"].split("|"):
                    edge(key, passage(ref), "documents tension")
            else:
                for ref in item.get("refs", item.get("references", [])):
                    edge(key, passage(ref), "cites passage")
            if prefix == "eq":
                for dep in item["dependencies"]:
                    edge(key, "eq-" + dep, "requires calculation")
            if prefix == "term":
                for related in item["related"]:
                    edge(key, "term-" + related, "related concept")

    reference_counts = {"numbered_rule": Counter(), "unnumbered_segment": Counter()}
    reference_sources = {key: set() for key in reference_counts}
    reference_targets = {key: set() for key in reference_counts}
    for row in xrefs:
        segment_id = row["source_segment_id"]
        parent = row["source_rule_id"] or None
        if segment_id not in segment_parents or segment_parents[segment_id] != parent:
            raise ValueError(f"Invalid segment/parent reference at {segment_id}: {parent}")
        origin = "numbered_rule" if parent else "unnumbered_segment"
        source = parent or segment_id
        count = reference_counts[origin]
        count["rows_before_target_join"] += 1
        reference_sources[origin].add(source)
        target = row["target_rule_id"]
        if row["resolution"] != "resolved" or target not in nodes:
            unmatched.append(dict(source=segment_id, target=row["target_original_id"],
                                  resolution=row["resolution"], offset=row["offset"]))
            continue
        count["matched_rows"] += 1
        reference_targets[origin].add(target)
        edge(source, target, "explicit reference")

    # Selected positive definitions for the illustrated reading paths.
    for src, dest in [("45", "class-step"), ("49", "ambs"), ("188", "roll-low"),
                      ("39", "running-speed"), ("17", "pool-size")]:
        edge("rule-" + src, "eq-" + dest, "states calculation")
    for src, dest in [("2", "martial-grade"), ("35", "roll-high")]:
        edge("rule-" + src, "eq-" + dest, "supports interpretation")
    for src, dest in [("49", "ambs"), ("2", "mag"), ("27", "pk"), ("55", "letter"),
                      ("79", "health"), ("79", "karma"), ("50", "pc")]:
        edge("rule-" + src, "term-" + dest, "defines term")
    edge("eq-roll-high", "eq-roll-low", "opposing roll conventions")
    edge("eq-tcp-linear", "eq-tcp-log", "gives a conflicting point estimate")

    events = sum(mentions.values())
    out_edges = []
    selections = {}
    for kind, (source_kinds, target_kinds) in RELATIONS.items():
        candidates = [(a, b, n) for (a, b, relation), n in mentions.items() if relation == kind]
        incoming = Counter()
        rows = 0
        self_links = 0
        for a, b, n in sorted(candidates):
            if a not in nodes or b not in nodes:
                raise ValueError(f"Unknown endpoint on {kind}: {a} -> {b}")
            if nodes[a]["kind"] not in source_kinds or nodes[b]["kind"] not in target_kinds:
                raise ValueError(f"Invalid endpoint type for {kind}: {a} -> {b}")
            out_edges.append(dict(source=a, target=b, type=kind, occurrences=n))
            rows += n
            if kind == "explicit reference":
                origin = "numbered_rule" if nodes[a]["kind"] == "rule" else "unnumbered_segment"
                reference_counts[origin]["distinct_pairs"] += 1
            if a == b:
                self_links += 1
            else:
                incoming[b] += 1
        selections[kind] = {
            "events_before_type_filter": events, "matching_events": rows,
            "distinct_directed_pairs": len(candidates), "duplicate_pair_events": rows - len(candidates),
            "self_pairs": self_links, "pairs_ranked": len(candidates) - self_links,
            "source_kinds": sorted(source_kinds), "target_kinds": sorted(target_kinds),
            "top_incoming": [{"id": b, "incoming": n} for b, n in
                             sorted(incoming.items(), key=lambda pair: (-pair[1], pair[0]))[:5]],
        }
    if sum(s["matching_events"] for s in selections.values()) != events:
        raise ValueError("At least one graph event used an undeclared relation")

    origins = {}
    for key, counts in reference_counts.items():
        origins[key] = dict(counts)
        origins[key].update(
            distinct_sources_observed=len(reference_sources[key]),
            distinct_targets_matched=len(reference_targets[key]),
            unmatched_rows=counts["rows_before_target_join"] - counts["matched_rows"],
            repeated_pair_mentions=counts["matched_rows"] - counts["distinct_pairs"],
        )
    audit = dict(
        nodes=len(nodes), edges=len(out_edges), duplicate_node_ids=0, unmatched_endpoint_keys=0,
        input_reference_rows=len(xrefs), explicit_reference_pairs=selections["explicit reference"]["distinct_directed_pairs"],
        source_segment_keys=len(segment_parents), duplicate_source_segment_keys=0,
        unmatched_reference_rows=unmatched, reference_origins=origins, relations=selections,
        centrality_method="Distinct directed sources reaching a target by one edge type, excluding self-links. Ties are ordered by ID.",
        reference_unit="Numbered references aggregate by original rule occurrence. Unnumbered references retain the analytical segment as their origin. General editorial citations to the preface use a separate umbrella node.",
    )
    graph = dict(nodes=list(nodes.values()), edges=out_edges, audit=audit)
    OUT.mkdir(exist_ok=True, parents=True)
    (OUT / "graph.json").write_text(json.dumps(graph, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return graph
