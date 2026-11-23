"""Replay the equation cases, branch checks, and the class-conversion table."""
from __future__ import annotations

import argparse
import ast
from collections import Counter
import csv
from io import StringIO
import itertools
import json
import math
import operator
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "analysis" / "mathematics"
OPERATIONS = {
    ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
    ast.Div: operator.truediv, ast.Pow: operator.pow,
}
FUNCTIONS = {"ceil": math.ceil, "floor": math.floor, "sqrt": math.sqrt, "log10": math.log10, "ln": math.log}


def calculate(expression, arguments):
    """Parse simple numerical notation. Only the listed operations are meaningful."""
    def visit(node):
        if isinstance(node, ast.Constant) and type(node.value) in (float, int):
            return node.value
        if isinstance(node, ast.Name):
            if node.id == "pi":
                return math.pi
            return arguments[node.id]
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
            return -visit(node.operand)
        if isinstance(node, ast.BinOp) and type(node.op) in OPERATIONS:
            return OPERATIONS[type(node.op)](visit(node.left), visit(node.right))
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            if node.func.id in FUNCTIONS and len(node.args) == 1 and not node.keywords:
                return FUNCTIONS[node.func.id](visit(node.args[0]))
        raise ValueError(f"Unsupported notation: {expression}")
    return visit(ast.parse(expression, mode="eval").body)


def forward(x):
    return x ** math.log10(x)


def csv_string(fieldnames, rows):
    buffer = StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return buffer.getvalue()


def reference_audit(source_rows, target_rows, field):
    target_keys = [r["id"] for r in target_rows]
    source_keys = [r["id"] for r in source_rows]
    pairs = [(r["id"], key) for r in source_rows for key in r[field]]
    matched = [(k, v) for k, v in pairs if v in set(target_keys)]
    return {
        "source_records": len(source_keys), "target_records": len(target_keys),
        "source_id_duplicates": [k for k, n in Counter(source_keys).items() if n > 1],
        "target_id_duplicates": [k for k, n in Counter(target_keys).items() if n > 1],
        "duplicate_reference_pairs": [k for k, n in Counter(pairs).items() if n > 1],
        "reference_rows_before_match": len(pairs), "reference_rows_after_match": len(matched),
        "unmatched_source_references": [k for k in pairs if k not in set(matched)],
        "target_ids_without_incoming_reference": sorted(set(target_keys) - {v for k, v in matched}),
    }


def evaluate():
    equations = json.loads((ROOT / "data/equations.json").read_text(encoding="utf-8"))
    glossary = json.loads((ROOT / "data/glossary.json").read_text(encoding="utf-8"))
    rows = []
    for eq in equations:
        if not eq["formulas"]:
            raise ValueError(f"No test cases for {eq['id']}")
        for case in eq["formulas"]:
            result = calculate(case["expression"], case["inputs"])
            expected = case["expected"]
            if not math.isclose(expected, result, rel_tol=1e-10, abs_tol=1e-11):
                raise ValueError(f"{eq['id']}: expected {expected}, found {result}")
            rows.append({"equation": eq["id"], "expression": case["expression"],
                         "inputs": json.dumps(case["inputs"], sort_keys=True),
                         "result": format(result, ".12g"), "expected": format(expected, ".12g")})

    inputs = [0.01, 0.1, 0.5, 1, 2, 5, 10, 16, 18, 19, 20, 25, 30, 40, 100, 1000]
    table = []
    for x in inputs:
        u = math.log10(x)
        y = forward(x)
        lo = 10 ** -math.sqrt(math.log10(y))
        hi = 10 ** math.sqrt(math.log10(y))
        assert math.isclose(x, lo if x < 1 else hi, rel_tol=1e-12)
        assert math.isclose(y, forward(1 / x), rel_tol=1e-12)
        assert math.isclose(y, 10 ** (u * u), rel_tol=1e-12)
        table.append(dict(input=x, next_class=format(y, ".12g"),
                          low_inverse=format(lo, ".12g"), high_inverse=format(hi, ".12g"),
                          log10_after_two_steps=format(u**4, ".12g")))

    totals = [sum(faces) for faces in itertools.product(range(1, 7), repeat=3)]
    high = [t for t in totals if t >= 12]
    assert len(high) == 81 and len(totals) == 216
    assert math.ceil(.66 * 150) == 99 and math.ceil(2 * 150 / 3) == 100
    assert round(10**math.sqrt(math.log10(35))-10) == 7 and round(17.7-10) == 8
    joins = {"equation_dependencies": reference_audit(equations, equations, "dependencies"),
             "glossary_related": reference_audit(glossary, glossary, "related")}
    for name, audit in joins.items():
        for key in ("source_id_duplicates", "target_id_duplicates", "duplicate_reference_pairs",
                    "unmatched_source_references"):
            if audit[key]:
                raise ValueError(f"{name}: {key}: {audit[key]}")
    report = {
        "edition": "v0.30", "registry_records": len(equations), "registry_cases": len(rows),
        "glossary_records": len(glossary),
        "positive_class_inputs": len(inputs), "inverse_reciprocal_and_identity_checks_per_input": 3,
        "three_d6_filter": {"population": "ordered outcomes of three fair six-sided dice",
                            "condition": "total >= 12", "rows_before": len(totals),
                            "rows_after": len(high), "probability": len(high)/len(totals)},
        "larger_pool_test": {"pool": "25d6", "maximum": 150, "at_66_percent": 99,
                             "at_two_thirds": 100, "status": "hypothetical denominator"},
        "roll_under_arithmetic": {"printed": 8, "recomputed": 7},
        "joins": joins,
        "scope": "Tests of explicitly interpreted arithmetic. They do not validate physical or social claims.",
    }
    return {
        "equation_cases.csv": csv_string(rows[0].keys(), rows),
        "class_conversion.csv": csv_string(table[0].keys(), table),
        "checks.json": json.dumps(report, indent=2, ensure_ascii=False) + "\n",
    }, report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true", help="regenerate the checked-in results")
    args = parser.parse_args()
    outputs, report = evaluate()
    for name, content in outputs.items():
        path = OUTPUT / name
        if args.write:
            OUTPUT.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content.encode("utf-8"))
        elif not path.exists() or path.read_text(encoding="utf-8") != content:
            raise SystemExit(f"Stale or missing output {path.name}. Use --write to regenerate.")
    print(f"{report['registry_records']} registry records, {report['registry_cases']} numerical cases, "
          f"{report['positive_class_inputs']} class rows. 3d6 filter: 216 before, 81 after.")
    for name, audit in report["joins"].items():
        print(f"{name}: {audit['reference_rows_before_match']} reference rows before, "
              f"{audit['reference_rows_after_match']} matched. "
              f"Unmatched links and duplicate keys: 0. "
              f"Targets with no incoming link: {len(audit['target_ids_without_incoming_reference'])} "
              "(listed in checks.json).")


if __name__ == "__main__":
    main()
