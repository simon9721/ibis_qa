#!/usr/bin/env python3
"""Render IBIS Quality checks grouped by IQ level."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = ROOT / "data" / "ibis_quality_spec_3_0.json"
DEFAULT_OUTPUT = ROOT / "docs" / "quality-levels.md"


def sort_key(check: dict) -> tuple[int, str]:
    return (check.get("source_line") or 0, check["id"])


def checks_for_level(data: dict, level: int) -> list[dict]:
    return sorted(
        [check for check in data["checks"] if check.get("numeric_level") == level],
        key=sort_key,
    )


def optional_checks(data: dict) -> list[dict]:
    return sorted([check for check in data["checks"] if check.get("optional")], key=sort_key)


def render_check_line(check: dict) -> str:
    automation = check["automation"]["class"]
    section = f"{check['section_id']} {check['section_title']}" if check.get("section_id") else "n/a"
    return f"- `{check['id']}` `{automation}` - {check['title']} ({section})"


def render_level_section(level: dict, checks: list[dict]) -> list[str]:
    level_id = level["id"]
    lines = [
        f"## {level_id}: {level['title']}",
        "",
        level["meaning"],
        "",
        f"Checks at this exact level: {len(checks)}",
        "",
    ]
    if checks:
        lines.extend(render_check_line(check) for check in checks)
    else:
        lines.append("- None")
    lines.append("")
    return lines


def render_markdown(data: dict) -> str:
    level_counts = {
        level["id"]: len(checks_for_level(data, level["numeric_level"]))
        for level in data["quality_levels"]
    }
    optional = optional_checks(data)

    lines = [
        "# IBIS QA Checks by Quality Level",
        "",
        "Generated from `data/ibis_quality_spec_3_0.json`.",
        "",
        "The IQ score is cumulative: an IQ3 file must pass the IQ1, IQ2, and IQ3 required checks. Optional checks are visible good-practice items and do not affect the summary IQ score.",
        "",
        "## Summary",
        "",
    ]

    for level in data["quality_levels"]:
        lines.append(f"- `{level['id']}`: {level_counts[level['id']]} checks - {level['title']}")
    lines.append(f"- `OPTIONAL`: {len(optional)} checks - non-gating good-practice items")
    lines.append("")

    for level in data["quality_levels"]:
        if level["numeric_level"] == 0:
            lines.extend(
                [
                    f"## {level['id']}: {level['title']}",
                    "",
                    level["meaning"],
                    "",
                    "Checks at this exact level: 0",
                    "",
                ]
            )
            continue
        lines.extend(render_level_section(level, checks_for_level(data, level["numeric_level"])))

    lines.extend(
        [
            "## Optional",
            "",
            "These checks are recommended by the spec but are not required to achieve any IQ level.",
            "",
            f"Checks: {len(optional)}",
            "",
        ]
    )
    if optional:
        lines.extend(render_check_line(check) for check in optional)
    else:
        lines.append("- None")
    lines.append("")

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
