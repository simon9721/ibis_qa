#!/usr/bin/env python3
"""Render the structured IBIS Quality Specification JSON as an ASCII tree."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = ROOT / "data" / "ibis_quality_spec_3_0.json"
DEFAULT_OUTPUT = ROOT / "docs" / "spec-tree.md"


def sort_key(node: dict) -> tuple[int, str]:
    return (node.get("source_line") or 0, node["id"])


def parent_id(spec_id: str) -> str | None:
    if spec_id.startswith("Appendix "):
        return None
    if "." not in spec_id:
        return None
    return spec_id.rsplit(".", 1)[0]


def node_label(node: dict) -> str:
    if node["kind"] == "check":
        level = "OPTIONAL" if node.get("optional") else f"LEVEL {node['numeric_level']}"
        automation = node.get("automation", {}).get("class", "unclassified")
        return f"{node['id']} [{level}, {automation}] {node['title']}"
    return f"{node['id']}. {node['title']}"


def build_tree(data: dict) -> list[dict]:
    nodes = []
    for section in data["sections"]:
        if section.get("id"):
            nodes.append(
                {
                    "id": section["id"],
                    "kind": section["kind"],
                    "title": section["title"],
                    "source_line": section.get("source_line"),
                    "children": [],
                }
            )
    for check in data["checks"]:
        nodes.append(
            {
                "id": check["id"],
                "kind": "check",
                "title": check["title"],
                "numeric_level": check.get("numeric_level"),
                "optional": check.get("optional", False),
                "automation": check.get("automation", {}),
                "source_line": check.get("source_line"),
                "children": [],
            }
        )

    by_id = {node["id"]: node for node in nodes}
    roots = []
    for node in sorted(nodes, key=sort_key):
        parent = parent_id(node["id"])
        if parent and parent in by_id:
            by_id[parent]["children"].append(node)
        else:
            roots.append(node)

    def sort_children(node: dict) -> None:
        node["children"].sort(key=sort_key)
        for child in node["children"]:
            sort_children(child)

    for root in roots:
        sort_children(root)
    return roots


def render_lines(nodes: list[dict], prefix: str = "") -> list[str]:
    lines = []
    for index, node in enumerate(nodes):
        last = index == len(nodes) - 1
        branch = "`-- " if last else "|-- "
        lines.append(prefix + branch + node_label(node))
        child_prefix = prefix + ("    " if last else "|   ")
        lines.extend(render_lines(node["children"], child_prefix))
    return lines


def render_markdown(data: dict) -> str:
    title = f"{data['source']['document']} {data['source']['version']}"
    roots = build_tree(data)
    class_counts = {
        name: sum(1 for check in data["checks"] if check["automation"]["class"] == name)
        for name in ("auto", "semi_auto", "manual", "optional")
    }

    lines = [
        f"# {title} Tree",
        "",
        "Generated from `data/ibis_quality_spec_3_0.json`.",
        "",
        "Legend:",
        "",
        "- `LEVEL n`: required check for the corresponding IQ level.",
        "- `OPTIONAL`: good-practice check that does not affect the IQ score.",
        "- `auto`: intended to be fully machine-checkable.",
        "- `semi_auto`: machine can collect evidence, but reviewer confirmation may be needed.",
        "- `manual`: requires datasheet, extraction, correlation, or engineering judgment.",
        "",
        "Check counts by automation class:",
        "",
    ]
    for class_name, count in class_counts.items():
        lines.append(f"- `{class_name}`: {count}")

    lines.extend(
        [
            "",
            "```text",
            title,
            *render_lines(roots),
            "```",
            "",
        ]
    )
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT, help="Path to structured spec JSON.")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help="Markdown output path.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    data = json.loads(args.input.read_text(encoding="utf-8"))
    rendered = render_markdown(data)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(rendered, encoding="utf-8")
    print(f"Wrote {args.output.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
