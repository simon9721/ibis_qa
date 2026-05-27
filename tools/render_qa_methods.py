#!/usr/bin/env python3
"""Render the IBIS QA methods map from the structured spec JSON."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = ROOT / "data" / "ibis_quality_spec_3_0.json"
DEFAULT_OUTPUT = ROOT / "docs" / "qa-methods.md"


def render_markdown(data: dict) -> str:
    checks = data["checks"]
    by_class: dict[str, list[dict]] = {}
    for check in checks:
        by_class.setdefault(check["automation"]["class"], []).append(check)

    lines = [
        "# IBIS QA Methods Map",
        "",
        "Generated from `data/ibis_quality_spec_3_0.json`.",
        "",
        "Use this as the implementation map for the IBIS QA tool. The JSON is the canonical structured source for check IDs, levels, automation classes, and how-to-automate guidance.",
        "",
        "## Source Coverage",
        "",
        f"- Spec checks captured: {data['coverage']['spec_check_count']}",
        f"- Workbook checklist entries captured: {data['coverage']['workbook_check_count']}",
        f"- In spec but not workbook: {', '.join(data['coverage']['in_spec_not_workbook']) or 'none'}",
        f"- In workbook but not spec: {', '.join(data['coverage']['in_workbook_not_spec']) or 'none'}",
        "",
        "Known mismatches:",
    ]
    for mismatch in data["coverage"]["known_mismatches"]:
        lines.append(f"- {mismatch['description']}")

    lines.extend(
        [
            "",
            "## Suggested MVP Scope",
            "",
            "- Implement `auto` checks first: IBISCHK parsing, structural presence checks, table range checks, and numeric tolerance checks.",
            "- Add `semi_auto` checks as evidence collectors: compute the numeric evidence, plot or summarize the data, and require reviewer confirmation where the spec depends on reasonableness or technology exceptions.",
            "- Keep `manual` checks in the report template from day one so nothing disappears from the process.",
            "- Treat `optional` checks as visible non-gating items.",
            "",
            "## Automation Classes",
            "",
        ]
    )

    class_order = ["auto", "semi_auto", "manual", "optional"]
    class_names = {
        "auto": "Auto",
        "semi_auto": "Semi-Auto",
        "manual": "Manual",
        "optional": "Optional",
    }
    for class_name in class_order:
        items = by_class.get(class_name, [])
        lines.append(f"### {class_names[class_name]}")
        lines.append("")
        if not items:
            lines.append("- None")
        for check in items:
            lines.append(f"- `{check['id']}` {check['level']}: {check['title']}")
        lines.append("")

    lines.extend(
        [
            "## Data Shape",
            "",
            "Each check in the JSON has:",
            "",
            "- `id`, `level`, `numeric_level`, `optional`, `title`",
            "- `section_id` and `section_title`",
            "- `ibis_keywords` extracted from the check text",
            "- `paragraphs` with the normalized source detail from the spec",
            "- `automation.class`, `automation.rationale`, and `automation.how`",
            "",
            "The scoring model is represented under `scoring_rules`; report fields are represented under `report_requirements`.",
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
    try:
        output_label = args.output.relative_to(ROOT)
    except ValueError:
        output_label = args.output
    print(f"Wrote {output_label}")


if __name__ == "__main__":
    main()
