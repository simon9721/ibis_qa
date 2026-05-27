#!/usr/bin/env python3
"""Render auto/semi-auto/manual categorization details from the spec JSON."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = ROOT / "data" / "ibis_quality_spec_3_0.json"
DEFAULT_OUTPUT = ROOT / "docs" / "automation-categories.md"

CATEGORY_ORDER = ["auto", "semi_auto", "manual", "optional"]
CATEGORY_TITLES = {
    "auto": "Auto",
    "semi_auto": "Semi-Auto",
    "manual": "Manual",
    "optional": "Optional",
}
CATEGORY_DESCRIPTIONS = {
    "auto": "Checks that should be implemented as deterministic parser, numeric, or external-tool checks.",
    "semi_auto": "Checks where software can collect strong evidence, but a reviewer may need to confirm context, technology exceptions, or datasheet intent.",
    "manual": "Checks that depend on datasheet interpretation, extraction knowledge, correlation judgment, or model-maker intent.",
    "optional": "Good-practice checks that should remain visible but do not gate the IQ score.",
}


def sort_key(check: dict) -> tuple[int, str]:
    return (check.get("source_line") or 0, check["id"])


def level_label(check: dict) -> str:
    if check.get("optional"):
        return "OPTIONAL"
    return f"LEVEL {check['numeric_level']}"


def render_check(check: dict) -> list[str]:
    automation = check["automation"]
    keywords = ", ".join(f"`{keyword}`" for keyword in check.get("ibis_keywords", [])) or "none detected"
    section = f"{check['section_id']} {check['section_title']}" if check.get("section_id") else "n/a"
    return [
        f"### `{check['id']}` {level_label(check)} - {check['title']}",
        "",
        f"- Section: {section}",
        f"- Keywords: {keywords}",
        f"- Why: {automation['rationale']}",
        f"- How: {automation['how']}",
        "",
    ]


def render_markdown(data: dict) -> str:
    checks_by_category = {
        category: sorted(
            [check for check in data["checks"] if check["automation"]["class"] == category],
            key=sort_key,
        )
        for category in CATEGORY_ORDER
    }

    lines = [
        "# IBIS QA Automation Categories",
        "",
        "Generated from `data/ibis_quality_spec_3_0.json`.",
        "",
        "This catalog groups every IBIS Quality Specification 3.0 check by the current automation plan. The `Why` field explains the classification; the `How` field describes the intended implementation or review workflow.",
        "",
        "## Summary",
        "",
    ]

    for category in CATEGORY_ORDER:
        lines.append(f"- `{category}`: {len(checks_by_category[category])} checks")

    lines.append("")

    for category in CATEGORY_ORDER:
        title = CATEGORY_TITLES[category]
        lines.extend(
            [
                f"## {title}",
                "",
                CATEGORY_DESCRIPTIONS[category],
                "",
            ]
        )
        for check in checks_by_category[category]:
            lines.extend(render_check(check))

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
