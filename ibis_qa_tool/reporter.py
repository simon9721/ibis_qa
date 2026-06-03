"""
reporter.py  —  Format CheckResult lists into text or JSON reports
===================================================================
"""

from __future__ import annotations
import base64
import re
import json
from collections import Counter
from datetime import datetime
from html import escape as html_escape
from pathlib import Path
from typing import TYPE_CHECKING

from checks.base import CheckResult, Status
from plotting import write_markdown_plot_assets
from zout import DEFAULT_ZOUT_RLOAD_OHM, estimate_zout_for_ibis, summarize_zout_results

if TYPE_CHECKING:
    from parser.ibis_parser import IBISFile


_STATUS_SYMBOL = {
    Status.PASS:  "✓",
    Status.FAIL:  "✗",
    Status.NA:    "—",
    Status.WARN:  "⚠",
    Status.ERROR: "!",
}
_STATUS_ORDER = [Status.FAIL, Status.ERROR, Status.WARN, Status.PASS, Status.NA]
_STATUS_VALUE_ORDER = [s.value for s in _STATUS_ORDER]
_SPEC_PATH = Path(__file__).resolve().parent.parent / "data" / "ibis_quality_spec_3_0.json"


def _load_check_metadata() -> dict[str, dict]:
    if not _SPEC_PATH.exists():
        return {}
    try:
        data = json.loads(_SPEC_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return {
        item["id"]: {
            "iq_level": item.get("level"),
            "numeric_level": item.get("numeric_level"),
            "title": item.get("title"),
            "automation_class": (item.get("automation") or {}).get("class"),
            "optional": item.get("optional", False),
            "source_line": item.get("source_line"),
            "section_id": item.get("section_id"),
            "section_title": item.get("section_title"),
        }
        for item in data.get("checks", [])
        if item.get("id")
    }


_CHECK_METADATA = _load_check_metadata()


def _load_report_context() -> dict:
    if not _SPEC_PATH.exists():
        return {}
    try:
        data = json.loads(_SPEC_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return {
        "quality_levels": data.get("quality_levels", []),
        "special_designators": data.get("special_designators", []),
        "scoring_rules": data.get("scoring_rules", {}),
    }


_REPORT_CONTEXT = _load_report_context()


def _md_cell(value) -> str:
    if value is None:
        return ""
    return str(value).replace("|", "\\|").replace("\r", " ").replace("\n", "<br>")


def _status_needs_attention(result: dict) -> bool:
    return (
        result.get("status") in {
            Status.FAIL.value,
            Status.ERROR.value,
            Status.WARN.value,
        }
        or bool(result.get("review_required"))
    )


def _check_sort_key(check_id: str) -> tuple:
    try:
        return tuple(int(part) for part in check_id.split("."))
    except ValueError:
        return (999,)


def _result_reason(result: dict) -> str:
    message = result.get("message", "")
    details = [_human_detail(detail) for detail in (result.get("details") or [])[:2]]
    if details:
        return f"{message}: {'; '.join(details)}"
    return message


def _human_detail(detail) -> str:
    text = str(detail)
    prefix = "IBISCHK path:"
    if text.startswith(prefix):
        path_text = text[len(prefix):].strip()
        return f"IBISCHK executable: {Path(path_text).name or path_text}"
    return text


def _fmt_number(value, unit: str = "", precision: int = 3) -> str:
    if value is None:
        return ""
    try:
        number = float(value)
    except (TypeError, ValueError):
        return str(value)
    text = f"{number:.{precision}g}"
    return f"{text} {unit}".strip()


def _fmt_zout_triplet(values: dict) -> str:
    parts = []
    for corner in ("typ", "min", "max"):
        value = values.get(corner)
        parts.append(_fmt_number(value, "ohm") if value is not None else "NA")
    return " / ".join(parts)


def _zout_report_notes(zout: dict) -> str:
    if not zout:
        return "No Zout data generated."
    estimates = zout.get("estimates") or []
    raw_notes = [str(note).strip().rstrip(".") for note in (zout.get("notes") or [])]
    missing_driver_tables = (
        any("[Pulldown]" in note for note in raw_notes)
        and any("[Pullup]" in note for note in raw_notes)
    )
    if not zout.get("available") and missing_driver_tables:
        return "No usable Pullup/Pulldown driver table."

    unavailable = Counter(
        item.get("status", "")
        for item in estimates
        if item.get("status") != "estimated"
    )
    notes = []
    if not zout.get("available"):
        notes.append("No load-line estimate available.")
    for reason, count in unavailable.most_common(2):
        if not reason:
            continue
        notes.append(f"{count}x {reason.replace('_', ' ')}")
    for note in raw_notes[:2]:
        if note not in notes:
            notes.append(note)
    return "; ".join(notes) if notes else "Estimated from available corners."


def _attention_reasons(check_id: str, results: list[dict], limit: int = 3) -> str:
    relevant = [
        result for result in results
        if result.get("check_id") == check_id
        and _status_needs_attention(result)
    ]
    messages = Counter(_result_reason(result) for result in relevant)
    if not messages:
        return ""

    parts = []
    for message, count in messages.most_common(limit):
        prefix = f"{count}x " if count > 1 else ""
        parts.append(f"{prefix}{message}")
    remaining = len(messages) - limit
    if remaining > 0:
        parts.append(f"{remaining} more finding type(s)")
    return "<br>".join(parts)


def _attention_subjects(check_id: str, results: list[dict], limit: int = 4) -> str:
    subjects = []
    for result in results:
        if result.get("check_id") != check_id or not _status_needs_attention(result):
            continue
        label = result.get("subject", "")
        scope = result.get("scope", "")
        value = f"{scope}: {label}" if scope and label else label or scope
        if value and value not in subjects:
            subjects.append(value)

    shown = subjects[:limit]
    if len(subjects) > limit:
        shown.append(f"{len(subjects) - limit} more")
    return "<br>".join(shown)


def _attention_infos(results: list[dict]) -> list[dict]:
    outcomes = _check_item_outcomes(results)
    attention = [
        info for info in outcomes.values()
        if info["outcome"] in {
            Status.FAIL.value,
            Status.ERROR.value,
            Status.WARN.value,
        }
    ]
    attention.sort(key=lambda info: (
        info.get("numeric_level") or 99,
        _check_sort_key(info["check_id"]),
    ))
    return attention


def _render_attention_table(lines: list[str], results: list[dict], empty_message: str) -> None:
    attention = _attention_infos(results)
    if not attention:
        lines.append(empty_message)
        return

    lines.extend([
        "| Level | Check Item | Outcome | Scope / Subject | Fail | Warn | Why attention is needed |",
        "|---|---|---|---|---:|---:|---|",
    ])
    current_level = None
    for info in attention:
        level_label = info.get("iq_level") or (
            f"LEVEL {info.get('numeric_level')}"
            if info.get("numeric_level")
            else "Unleveled"
        )
        if level_label != current_level:
            current_level = level_label
            lines.append(
                f"| **{_md_cell(level_label)}** |  |  |  |  |  |  |"
            )

        counts = info["status_counts"]
        check_item = f"{info['check_id']} - {info.get('title', '')}".strip(" -")
        lines.append(
            f"| {_md_cell(info.get('iq_level'))} "
            f"| {_md_cell(check_item)} "
            f"| {_md_cell(info['outcome'])} "
            f"| {_md_cell(_attention_subjects(info['check_id'], results))} "
            f"| {counts.get('FAIL', 0)} "
            f"| {counts.get('WARN', 0)} "
            f"| {_md_cell(_attention_reasons(info['check_id'], results))} |"
        )


def _anchor_id(value: str) -> str:
    cleaned = []
    previous_dash = False
    for char in value.lower():
        if char.isalnum():
            cleaned.append(char)
            previous_dash = False
        elif not previous_dash:
            cleaned.append("-")
            previous_dash = True
    return "".join(cleaned).strip("-") or "section"


def _scope_label(scope: str) -> str:
    return {
        "file": "File/Header",
        "component": "Component",
        "model": "Model",
        "package_model": "Package Model",
        "unknown": "Unscoped",
    }.get(scope or "unknown", scope or "Unscoped")


def _scope_sort_key(scope: str) -> int:
    return {
        "file": 0,
        "component": 1,
        "model": 2,
        "package_model": 3,
        "unknown": 4,
    }.get(scope or "unknown", 9)


def _subject_summary(results: list[dict], limit: int = 6) -> str:
    subjects = []
    for result in results:
        label = result.get("subject") or result.get("model_name") or result.get("component_name") or ""
        if label and label not in subjects:
            subjects.append(label)
    shown = subjects[:limit]
    if len(subjects) > limit:
        shown.append(f"{len(subjects) - limit} more")
    return "<br>".join(shown)


def _status_counts(results: list[dict]) -> Counter:
    counts = Counter(result.get("status", "") for result in results)
    for status in ("PASS", "FAIL", "WARN", "NA", "ERROR"):
        counts.setdefault(status, 0)
    return counts


def _outcome_from_counts(counts: Counter) -> str:
    return next(
        (status for status in _STATUS_VALUE_ORDER if counts.get(status, 0)),
        Status.NA.value,
    )


def _scope_reason(results: list[dict], limit: int = 3) -> str:
    if not results:
        return ""
    attention = [result for result in results if _status_needs_attention(result)]
    source = attention or [
        result for result in results
        if result.get("status") not in {Status.PASS.value, Status.NA.value}
    ] or results
    messages = Counter(_result_reason(result) for result in source if _result_reason(result))
    parts = []
    for message, count in messages.most_common(limit):
        prefix = f"{count}x " if count > 1 else ""
        parts.append(f"{prefix}{message}")
    remaining = len(messages) - limit
    if remaining > 0:
        parts.append(f"{remaining} more evidence message(s)")
    return "<br>".join(parts)


def _report_comment(summary: dict, score_summary: dict) -> str:
    fail_count = summary.get(Status.FAIL.value, 0)
    error_count = summary.get(Status.ERROR.value, 0)
    warn_count = summary.get(Status.WARN.value, 0)
    candidate = score_summary.get("tool_score") or score_summary.get("implemented_check_score")
    if fail_count or error_count:
        return (
            f"Candidate {candidate}; resolve the FAIL/ERROR findings before final IQ "
            "assignment. WARN and review-required items also need documented judgement."
        )
    if warn_count:
        return (
            f"Candidate {candidate}; no implemented checked item has FAIL/ERROR, but "
            "WARN and review-required items still need model-maker review."
        )
    return (
        f"Candidate {candidate}; no implemented checked item has FAIL/ERROR/WARN. "
        "Manual and external-evidence checks still need model-maker documentation."
    )


def _check_ids_for_level(level: int) -> list[str]:
    return sorted(
        [
            check_id for check_id, metadata in _CHECK_METADATA.items()
            if metadata.get("numeric_level") == level
            and not metadata.get("optional")
        ],
        key=_check_sort_key,
    )


def _toc_link_label(check_id: str) -> str:
    title = _CHECK_METADATA.get(check_id, {}).get("title", "")
    clean_title = str(title).replace("[", "(").replace("]", ")")
    return f"{check_id} - {clean_title}".strip(" -")


def _visual_anchor(model_name: str, curve_key: str) -> str:
    return f"curve-{_anchor_id(model_name)}-{_anchor_id(curve_key)}"


def _plot_keys_for_check(check_id: str) -> list[str]:
    if check_id == "5.3.10":
        return ["iv_clamp"]
    if check_id in {"5.3.8", "5.3.9"}:
        return ["iv_zero"]
    if check_id.startswith("5.3."):
        return ["iv"]
    if check_id.startswith("5.7."):
        return ["isso"]
    if check_id.startswith("5.5.") or check_id.startswith("5.8."):
        return ["waveform"]
    return []


_CURVE_LABELS = {
    "iv": "I-V curves",
    "iv_clamp": "I-V clamp detail",
    "iv_zero": "I-V pullup/pulldown 0 V detail",
    "isso": "ISSO curves",
    "waveform": "V-T curves",
    "zout": "Zout load-line curves",
}


def _visual_links_for_results(
        results: list[dict],
        plot_refs: dict[str, dict[str, str]],
        limit: int = 4) -> str:
    links = []
    seen = set()
    for result in results:
        if result.get("status") not in {Status.WARN.value, Status.FAIL.value, Status.ERROR.value}:
            continue
        model_name = result.get("model_name") or result.get("subject")
        if model_name not in plot_refs:
            continue
        for curve_key in _plot_keys_for_check(result.get("check_id", "")):
            if not plot_refs[model_name].get(curve_key):
                continue
            anchor = _visual_anchor(model_name, curve_key)
            key = (model_name, curve_key)
            if key in seen:
                continue
            seen.add(key)
            label = f"{model_name} {_CURVE_LABELS.get(curve_key, 'curves')}"
            links.append(f"[{_md_cell(label)}](#{anchor})")
    shown = links[:limit]
    if len(links) > limit:
        shown.append(f"{len(links) - limit} more")
    return "<br>".join(shown)


def _qa_links_for_visual(model_results: list[dict], curve_key: str) -> str:
    check_ids = []
    for result in model_results:
        if result.get("status") not in {Status.WARN.value, Status.FAIL.value, Status.ERROR.value}:
            continue
        check_id = result.get("check_id", "")
        if curve_key not in _plot_keys_for_check(check_id):
            continue
        if check_id not in check_ids:
            check_ids.append(check_id)
    return ", ".join(
        f"[{check_id}](#check-{_anchor_id(check_id)})"
        for check_id in sorted(check_ids, key=_check_sort_key)
    )



def _render_toc(lines: list[str], max_level: int | None) -> None:
    score_cap = max_level or 4
    lines.extend([
        "",
        "## Table of Contents",
        '<a id="table-of-contents"></a>',
        "",
        "- [Score Assessment](#score-assessment)",
        "- [Result Summary](#result-summary)",
        "- [Passed Items Per Level](#passed-items-per-level)",
        "- [Zout Estimates](#zout-estimates)",
        "- [Quality Check Results](#quality-check-results)",
    ])
    for level in range(1, score_cap + 1):
        check_ids = _check_ids_for_level(level)
        if not check_ids:
            continue
        lines.extend([
            "",
            f"**LEVEL {level} Checks**",
            "",
            f"- [LEVEL {level} check results](#level-{level}-check-results)",
        ])
        for check_id in check_ids:
            lines.append(f"- [{_md_cell(_toc_link_label(check_id))}](#check-{_anchor_id(check_id)})")
    lines.extend([
        "",
        "- [Visual Curves by Model](#visual-curves-by-model)",
        "- [Appendix A: IQ Levels](#appendix-a-iq-levels)",
        "- [Appendix B: Special Designators](#appendix-b-special-designators)",
    ])


def _render_quality_check_results(
        lines: list[str],
        results: list[dict],
        max_level: int | None,
        plot_refs: dict[str, dict[str, str]] | None = None) -> None:
    score_cap = max_level or 4
    plot_refs = plot_refs or {}
    results_by_check: dict[str, list[dict]] = {}
    for result in results:
        results_by_check.setdefault(result.get("check_id", ""), []).append(result)

    lines.extend([
        "",
        "## Quality Check Results",
        '<a id="quality-check-results"></a>',
        "",
        "Rows are grouped by IQ level and then by check item. Each check item is summarized by result type so PASS, WARN, FAIL, NA, and manual/external-review status are visible in one place.",
        "",
        "Source location note: this parser currently keeps the raw IBIS text but does not retain per-result IBIS source line numbers. The report identifies the affected scope, subject, and evidence; exact line references require parser metadata work.",
    ])

    for level in range(1, score_cap + 1):
        check_ids = _check_ids_for_level(level)
        if not check_ids:
            continue
        lines.extend([
            "",
            f"### LEVEL {level} Check Results",
            f'<a id="level-{level}-check-results"></a>',
            "",
        ])
        for check_id in check_ids:
            metadata = _CHECK_METADATA.get(check_id, {})
            check_results = results_by_check.get(check_id, [])
            title = metadata.get("title", "")
            automation = metadata.get("automation_class") or "manual"
            spec_line = metadata.get("source_line")
            section = metadata.get("section_id")
            spec_note = f"Quality spec source line {spec_line}" if spec_line else ""
            if section:
                spec_note = f"{spec_note}; section {section}" if spec_note else f"section {section}"
            lines.extend([
                "",
                f"#### {check_id} - {_md_cell(title)}",
                f'<a id="check-{_anchor_id(check_id)}"></a>',
                "",
                f"- Automation class: `{_md_cell(automation)}`",
            ])
            if spec_note:
                lines.append(f"- Spec reference: {_md_cell(spec_note)}")

            lines.extend([
                "",
                "| Type | Outcome | Pass | Warn | Fail | NA | Error | Review | Subjects | Visual Curves | Explanation / Details |",
                "|---|---|---:|---:|---:|---:|---:|---:|---|---|---|",
            ])

            if not check_results:
                lines.append(
                    "| Manual/External | MANUAL REVIEW | 0 | 0 | 0 | 0 | 0 | 1 "
                    "| Applies where relevant |  | Not executed by the automated tool; this item needs model-maker or reviewer evidence. |"
                )
            else:
                scopes = sorted(
                    {result.get("scope", "unknown") for result in check_results},
                    key=_scope_sort_key,
                )
                for scope in scopes:
                    scoped = [
                        result for result in check_results
                        if result.get("scope", "unknown") == scope
                    ]
                    counts = _status_counts(scoped)
                    outcome = _outcome_from_counts(counts)
                    review_count = sum(1 for result in scoped if result.get("review_required"))
                    lines.append(
                        f"| {_md_cell(_scope_label(scope))} "
                        f"| {_md_cell(outcome)} "
                        f"| {counts.get('PASS', 0)} "
                        f"| {counts.get('WARN', 0)} "
                        f"| {counts.get('FAIL', 0)} "
                        f"| {counts.get('NA', 0)} "
                        f"| {counts.get('ERROR', 0)} "
                        f"| {review_count} "
                        f"| {_md_cell(_subject_summary(scoped))} "
                        f"| {_md_cell(_visual_links_for_results(scoped, plot_refs))} "
                        f"| {_md_cell(_scope_reason(scoped))} |"
                    )

                _render_ibischk_excerpt(lines, check_results)

            lines.extend([
                "",
                "[Back to table of contents](#table-of-contents)",
            ])


def _render_zout_estimates(
        lines: list[str],
        report: dict,
        plot_refs: dict[str, dict[str, str]] | None = None) -> None:
    zout_summary = report.get("zout_summary") or {}
    models = report.get("models", {})
    plot_refs = plot_refs or {}
    r_load = zout_summary.get("r_load_ohm")
    r_load_text = _fmt_number(r_load, "ohm") if r_load is not None else "50 ohm"

    lines.extend([
        "",
        "## Zout Estimates",
        '<a id="zout-estimates"></a>',
        "",
        (
            "Estimated output impedance is derived from Pullup/Pulldown I-V "
            f"load-line intersections using Rload = {r_load_text}. These values "
            "are characterization data for the model maker; they are not IQ "
            "PASS/FAIL checks."
        ),
        "",
        f"- Models with estimates: {zout_summary.get('models_with_estimates', 0)} / {zout_summary.get('model_count', len(models))}",
        f"- Estimated table/corner points: {zout_summary.get('estimate_count', 0)}",
        "",
        "| Model | Type | Pulldown Zout typ/min/max | Pullup Zout typ/min/max | Load-line plot | Notes |",
        "|---|---|---:|---:|---|---|",
    ])

    if not models:
        lines.append("|  |  |  |  |  | No models parsed. |")
        return

    for model_name, model_info in models.items():
        zout = model_info.get("zout") or {}
        summary = zout.get("summary") or {}
        notes = _zout_report_notes(zout)
        plot_link = (
            f"[View plot](#{_visual_anchor(model_name, 'zout')})"
            if (plot_refs.get(model_name) or {}).get("zout")
            else ""
        )
        lines.append(
            f"| {_md_cell(model_name)} "
            f"| {_md_cell(model_info.get('model_type', ''))} "
            f"| {_md_cell(_fmt_zout_triplet((summary.get('pulldown') or {})))} "
            f"| {_md_cell(_fmt_zout_triplet((summary.get('pullup') or {})))} "
            f"| {_md_cell(plot_link)} "
            f"| {_md_cell(notes)} |"
        )


def _render_ibischk_excerpt(lines: list[str], check_results: list[dict]) -> None:
    ibischk_result = None
    for result in check_results:
        data = result.get("data") or {}
        if data.get("ibischk"):
            ibischk_result = result
            break
    if not ibischk_result:
        return

    ibischk = (ibischk_result.get("data") or {}).get("ibischk") or {}
    output = str(ibischk.get("output") or "").strip()
    executable = ibischk.get("path")
    executable_name = Path(executable).name if executable else ""
    lines.extend([
        "",
        "**IBISCHK execution summary**",
        "",
        "| Field | Value |",
        "|---|---|",
        f"| Executable | {_md_cell(executable_name)} |",
        f"| Version | {_md_cell(ibischk.get('version'))} |",
        f"| Return code | {_md_cell(ibischk.get('returncode'))} |",
        f"| Errors | {_md_cell(ibischk.get('errors'))} |",
        f"| Warnings | {_md_cell(ibischk.get('warnings'))} |",
        f"| Cautions | {_md_cell(ibischk.get('cautions'))} |",
    ])
    if output:
        excerpt = "\n".join(output.splitlines()[:25])
        lines.extend([
            "",
            "**IBISCHK output excerpt**",
            "",
            "```text",
            excerpt,
            "```",
        ])


def _candidate_score_from_results(
        results: list[dict],
        level1_passed: bool,
        max_level: int | None = None) -> str:
    if not level1_passed:
        return "Below IQ1"

    candidate = 1
    score_cap = max_level or 4
    for level in range(2, score_cap + 1):
        level_results = [
            result for result in results
            if result.get("numeric_level") == level
        ]
        if not level_results:
            break
        if any(_status_blocks_candidate(result) for result in level_results):
            break
        candidate = level
    return f"IQ{candidate}"


def _status_blocks_candidate(result: dict) -> bool:
    return result.get("status") in {Status.FAIL.value, Status.ERROR.value}


def _check_item_outcomes(results: list[dict]) -> dict[str, dict]:
    by_check: dict[str, dict] = {}
    for result in results:
        check_id = result.get("check_id", "")
        if not check_id:
            continue
        metadata = _CHECK_METADATA.get(check_id, {})
        info = by_check.setdefault(check_id, {
            "check_id": check_id,
            "iq_level": result.get("iq_level") or metadata.get("iq_level"),
            "numeric_level": result.get("numeric_level") or metadata.get("numeric_level"),
            "title": metadata.get("title", ""),
            "automation_class": result.get("automation_class") or metadata.get("automation_class"),
            "status_counts": Counter(),
            "result_count": 0,
            "review_required_count": 0,
        })
        status = result.get("status", "")
        info["status_counts"][status] += 1
        info["result_count"] += 1
        if result.get("review_required"):
            info["review_required_count"] += 1

    for info in by_check.values():
        counts = info["status_counts"]
        info["outcome"] = next(
            (status for status in _STATUS_VALUE_ORDER if counts.get(status, 0)),
            Status.NA.value,
        )
    return by_check


def _level_summary_from_results(
        results: list[dict],
        max_level: int | None = None) -> list[dict]:
    outcomes = _check_item_outcomes(results)
    rows = []
    score_cap = max_level or 4
    for level in range(1, score_cap + 1):
        spec_ids = [
            check_id for check_id, metadata in _CHECK_METADATA.items()
            if metadata.get("numeric_level") == level
            and not metadata.get("optional")
        ]
        implemented_ids = [check_id for check_id in spec_ids if check_id in outcomes]
        outcome_counts = Counter(
            outcomes[check_id]["outcome"]
            for check_id in implemented_ids
        )
        manual_or_unimplemented = len(spec_ids) - len(implemented_ids)
        rows.append({
            "iq_level": f"LEVEL {level}",
            "numeric_level": level,
            "required_items": len(spec_ids),
            "implemented_items": len(implemented_ids),
            "passed_items": outcome_counts.get(Status.PASS.value, 0),
            "not_applicable_items": outcome_counts.get(Status.NA.value, 0),
            "warning_items": outcome_counts.get(Status.WARN.value, 0),
            "failed_items": outcome_counts.get(Status.FAIL.value, 0),
            "error_items": outcome_counts.get(Status.ERROR.value, 0),
            "review_required_items": sum(
                1 for check_id in implemented_ids
                if outcomes[check_id]["review_required_count"]
            ),
            "manual_or_unimplemented_items": manual_or_unimplemented,
            "clear_items": (
                outcome_counts.get(Status.PASS.value, 0)
                + outcome_counts.get(Status.NA.value, 0)
            ),
            "result_count": sum(
                outcomes[check_id]["result_count"]
                for check_id in implemented_ids
            ),
        })
    return rows


def _score_summary_from_levels(level_summary: list[dict]) -> dict:
    implemented_level = 0
    first_blocked_level = None
    for row in sorted(level_summary, key=lambda r: r["numeric_level"]):
        blockers = row["failed_items"] + row["error_items"]
        if blockers == 0:
            implemented_level = row["numeric_level"]
            continue
        first_blocked_level = row["numeric_level"]
        break

    return {
        "final_score": "Not assigned by tool",
        "tool_score": (
            f"IQ{implemented_level}" if implemented_level else "Below IQ1"
        ),
        "implemented_check_score": (
            f"IQ{implemented_level}" if implemented_level else "Below IQ1"
        ),
        "first_blocked_level": (
            f"LEVEL {first_blocked_level}" if first_blocked_level else None
        ),
        "note": (
            "Official IQ score assignment still requires reviewer decisions "
            "and any manual checks that depend on external data."
        ),
    }


def render_markdown_report(
        report: dict,
        asset_dir: str | Path | None = None,
        asset_ref_prefix: str | None = None) -> str:
    results = report.get("results", [])
    max_level = report.get("max_level")
    level_summary = report.get("level_summary") or _level_summary_from_results(results, max_level)
    score_summary = report.get("score_summary") or _score_summary_from_levels(level_summary)
    summary = report.get("summary", {})
    header = report.get("header", {})
    zout_summary = report.get("zout_summary", {})
    quality_levels = _REPORT_CONTEXT.get("quality_levels", [])
    special_designators = _REPORT_CONTEXT.get("special_designators", [])
    scoring_rules = _REPORT_CONTEXT.get("scoring_rules", {})
    level1_passed = bool(
        level_summary
        and level_summary[0].get("failed_items", 0) == 0
        and level_summary[0].get("error_items", 0) == 0
    )
    plot_refs = (
        write_markdown_plot_assets(report, asset_dir, asset_ref_prefix)
        if asset_dir is not None
        else {}
    )

    lines = [
        "# IBIS QA Report",
        "",
        "## File Summary",
        "",
        f"- Generated: {datetime.now().astimezone().isoformat(timespec='seconds')}",
        f"- IBIS file: `{_md_cell(Path(report.get('file', '')).name)}`",
        f"- Target level: {_md_cell(f'IQ{max_level}' if max_level else 'All implemented levels')}",
        f"- IBIS version: {_md_cell(report.get('ibis_ver', ''))}",
        f"- File revision: {_md_cell(report.get('file_rev', ''))}",
        f"- IBIS file date: {_md_cell(header.get('date', ''))}",
        f"- IQ score in file: {_md_cell(report.get('iq_score_in_file') or '(not found)')}",
        f"- Components: {header.get('component_count', 0)}",
        f"- Models: {header.get('model_count', 0)}",
        f"- Package models: {header.get('package_model_count', 0)}",
        f"- Zout estimates: {zout_summary.get('models_with_estimates', 0)} model(s), {zout_summary.get('estimate_count', 0)} table/corner point(s)",
    ]

    _render_toc(lines, max_level)

    lines.extend([
        "",
        "## Score Assessment",
        '<a id="score-assessment"></a>',
        "",
        "| Field | Value |",
        "|---|---|",
        "| Final IQ score | To be assigned by the model maker after resolving or documenting findings |",
        f"| Candidate level from checked items | {_md_cell(score_summary.get('tool_score') or score_summary.get('implemented_check_score'))} |",
        f"| Tool comments | {_md_cell(_report_comment(summary, score_summary))} |",
        "| Note | Candidate level is the highest implemented level without FAIL or ERROR. WARN/review items, manual checks, accepted exceptions, and correlation designators still require model-maker documentation before final IQ assignment. |",
        "",
        "## Result Summary",
        '<a id="result-summary"></a>',
        "",
        "| Status | Count |",
        "|---|---:|",
    ])

    for status in ("PASS", "FAIL", "WARN", "NA", "ERROR"):
        lines.append(f"| {status} | {summary.get(status, 0)} |")
    lines.extend([
        f"| Total | {sum(summary.get(status, 0) for status in ('PASS', 'FAIL', 'WARN', 'NA', 'ERROR'))} |",
        "",
        "## Passed Items Per Level",
        '<a id="passed-items-per-level"></a>',
        "",
        "| Level | Required Items | Checked | Passed | NA | Needs Review | Failed | Error | Manual/External Review |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ])

    for row in level_summary:
        lines.append(
            f"| {_md_cell(row['iq_level'])} "
            f"| {row['required_items']} "
            f"| {row['implemented_items']} "
            f"| {row['passed_items']} "
            f"| {row['not_applicable_items']} "
            f"| {row['warning_items']} "
            f"| {row['failed_items']} "
            f"| {row['error_items']} "
            f"| {row['manual_or_unimplemented_items']} |"
        )

    _render_zout_estimates(lines, report, plot_refs)
    _render_quality_check_results(lines, results, max_level, plot_refs)

    lines.extend([
        "",
        "## Visual Curves by Model",
        '<a id="visual-curves-by-model"></a>',
        "",
        "Figures provide curve/table context for the linked QA items. The quality-check tables above remain the authoritative status summary.",
    ])
    for model_name, model_info in report.get("models", {}).items():
        model_results = model_info.get("results", [])
        model_score = _candidate_score_from_results(model_results, level1_passed, max_level)
        lines.extend([
            f"### Model: `{_md_cell(model_name)}`",
            "",
            f"- Candidate model score from model-scoped checked items: {model_score}",
            f"- Model type: {_md_cell(model_info.get('model_type', ''))}",
            f"- Waveform tables: {model_info.get('waveform_count', 0)}",
            "",
        ])
        model_plot_refs = plot_refs.get(model_name, {})
        if model_plot_refs:
            waveform_label = (
                "V-T waveforms"
                if max_level is not None and max_level < 4
                else "V-T and Composite Current waveforms"
            )
            overview_refs = [
                ("iv", model_plot_refs.get("iv_label", "I-V curves"), model_plot_refs.get("iv")),
                ("iv_clamp", "I-V clamp detail", model_plot_refs.get("iv_clamp")),
                ("iv_zero", "I-V pullup/pulldown 0 V detail", model_plot_refs.get("iv_zero")),
                ("zout", "Zout load-line curves", model_plot_refs.get("zout")),
                ("isso", "ISSO curves", model_plot_refs.get("isso")),
                ("waveform", waveform_label, model_plot_refs.get("waveform")),
            ]
            if any(ref for _key, _label, ref in overview_refs):
                lines.extend([
                    "",
                    "#### Visual Curves",
                    "",
                ])
            for curve_key, label, ref in overview_refs:
                if ref:
                    related_links = _qa_links_for_visual(model_results, curve_key)
                    lines.extend([
                        f"##### {label}",
                        f'<a id="{_visual_anchor(model_name, curve_key)}"></a>',
                        "",
                    ])
                    if related_links:
                        lines.extend([
                            f"Related WARN/FAIL QA items: {related_links}",
                            "",
                        ])
                    lines.extend([
                        f"![{label} for {model_name}]({ref})",
                        "",
                    ])
        else:
            lines.extend([
                "No visual curve assets were generated for this model.",
                "",
            ])
        lines.append("")

    lines.extend([
        "",
        "## Appendix A: IQ Levels",
        '<a id="appendix-a-iq-levels"></a>',
        "",
        "| Level | Name | Meaning |",
        "|---|---|---|",
    ])

    for level in quality_levels:
        numeric_level = level.get("numeric_level")
        if max_level is not None and numeric_level is not None and numeric_level > max_level:
            continue
        lines.append(
            f"| {_md_cell(level.get('id'))} "
            f"| {_md_cell(level.get('title'))} "
            f"| {_md_cell(level.get('meaning'))} |"
        )

    lines.extend([
        "",
        "## Appendix B: Special Designators",
        '<a id="appendix-b-special-designators"></a>',
        "",
        "Special letters may be appended to the IQ score when the supporting evidence is documented.",
        "",
        "| Designator | Name | Meaning |",
        "|---|---|---|",
    ])

    for designator in special_designators:
        lines.append(
            f"| {_md_cell(designator.get('letter'))} "
            f"| {_md_cell(designator.get('name'))} "
            f"| {_md_cell(designator.get('meaning'))} |"
        )

    if scoring_rules:
        lines.extend([
            "",
            "## Appendix C: Scoring Notes",
            '<a id="appendix-c-scoring-notes"></a>',
            "",
            f"- Base level: {_md_cell(scoring_rules.get('base_level', ''))}",
            f"- Optional checks: {_md_cell(scoring_rules.get('optional_checks', ''))}",
            f"- Correlation designators: {_md_cell(scoring_rules.get('correlation_designators', ''))}",
            f"- Exception designator: {_md_cell(scoring_rules.get('exception_designator', ''))}",
            f"- Writeback: {_md_cell(scoring_rules.get('writeback', ''))}",
        ])

    return "\n".join(lines) + "\n"


def render_html_report(
        report: dict,
        asset_dir: str | Path | None = None,
        asset_ref_prefix: str | None = None) -> str:
    markdown = render_markdown_report(report, asset_dir, asset_ref_prefix)
    title = f"IBIS QA Report - {Path(report.get('file', 'IBIS')).name}"
    asset_path = Path(asset_dir) if asset_dir is not None else None
    return "\n".join([
        "<!doctype html>",
        '<html lang="en">',
        "<head>",
        '<meta charset="utf-8">',
        '<meta name="viewport" content="width=device-width, initial-scale=1">',
        f"<title>{html_escape(title)}</title>",
        "<style>",
        _REPORT_CSS,
        "</style>",
        "</head>",
        "<body>",
        '<main class="report">',
        _markdown_to_html(markdown, asset_path),
        "</main>",
        "</body>",
        "</html>",
        "",
    ])


_REPORT_CSS = """
:root {
  color-scheme: light;
  --text: #1f2933;
  --muted: #52606d;
  --line: #d9e2ec;
  --header: #102a43;
  --link: #1d4ed8;
  --panel: #f8fafc;
}
body {
  margin: 0;
  background: #ffffff;
  color: var(--text);
  font-family: Arial, Helvetica, sans-serif;
  line-height: 1.5;
}
.report {
  max-width: 1180px;
  margin: 0 auto;
  padding: 32px 28px 64px;
}
h1, h2, h3, h4, h5 {
  color: var(--header);
  line-height: 1.2;
}
h1 { font-size: 30px; margin: 0 0 24px; }
h2 { font-size: 22px; margin-top: 34px; border-bottom: 1px solid var(--line); padding-bottom: 7px; }
h3 { font-size: 18px; margin-top: 28px; }
h4 { font-size: 16px; margin-top: 24px; }
h5 { font-size: 14px; margin: 18px 0 8px; }
a { color: var(--link); text-decoration: none; }
a:hover { text-decoration: underline; }
table {
  border-collapse: collapse;
  width: 100%;
  margin: 12px 0 20px;
  font-size: 13px;
}
th, td {
  border: 1px solid var(--line);
  padding: 7px 8px;
  vertical-align: top;
}
th {
  background: #eef2f7;
  color: var(--header);
  text-align: left;
}
tr:nth-child(even) td { background: #fbfdff; }
code {
  background: #eef2f7;
  border-radius: 3px;
  padding: 1px 4px;
}
pre {
  background: #ffffff;
  color: var(--text);
  border: 1px solid var(--line);
  overflow-x: auto;
  padding: 14px;
  border-radius: 4px;
  white-space: pre-wrap;
}
pre code {
  background: transparent;
  color: inherit;
  padding: 0;
}
img {
  max-width: 100%;
  height: auto;
  border: 1px solid var(--line);
  background: #ffffff;
}
ul { padding-left: 22px; }
p { margin: 9px 0; }
""".strip()


def _markdown_to_html(markdown: str, asset_dir: Path | None = None) -> str:
    lines = markdown.splitlines()
    html_lines: list[str] = []
    in_code = False
    in_list = False
    i = 0

    def close_list() -> None:
        nonlocal in_list
        if in_list:
            html_lines.append("</ul>")
            in_list = False

    while i < len(lines):
        line = lines[i]

        if line.startswith("```"):
            close_list()
            if in_code:
                html_lines.append("</code></pre>")
                in_code = False
            else:
                html_lines.append("<pre><code>")
                in_code = True
            i += 1
            continue

        if in_code:
            html_lines.append(html_escape(line))
            i += 1
            continue

        if not line.strip():
            close_list()
            i += 1
            continue

        if re.match(r'<a id="[^"]+"></a>', line.strip()):
            close_list()
            html_lines.append(line.strip())
            i += 1
            continue

        if _is_md_table_start(lines, i):
            close_list()
            table_rows = []
            while i < len(lines) and lines[i].startswith("|"):
                table_rows.append(lines[i])
                i += 1
            html_lines.append(_render_html_table(table_rows, asset_dir))
            continue

        heading = re.match(r"^(#{1,6})\s+(.*)$", line)
        if heading:
            close_list()
            level = len(heading.group(1))
            html_lines.append(f"<h{level}>{_inline_md_to_html(heading.group(2), asset_dir)}</h{level}>")
            i += 1
            continue

        image = re.match(r"!\[([^\]]*)\]\(([^)]+)\)", line.strip())
        if image:
            close_list()
            alt = html_escape(image.group(1), quote=True)
            src = html_escape(_html_image_src(image.group(2), asset_dir), quote=True)
            html_lines.append(f'<p><img src="{src}" alt="{alt}" loading="lazy"></p>')
            i += 1
            continue

        if line.startswith("- "):
            if not in_list:
                html_lines.append("<ul>")
                in_list = True
            html_lines.append(f"<li>{_inline_md_to_html(line[2:], asset_dir)}</li>")
            i += 1
            continue

        close_list()
        html_lines.append(f"<p>{_inline_md_to_html(line, asset_dir)}</p>")
        i += 1

    close_list()
    if in_code:
        html_lines.append("</code></pre>")
    return "\n".join(html_lines)


def _is_md_table_start(lines: list[str], index: int) -> bool:
    return (
        index + 1 < len(lines)
        and lines[index].startswith("|")
        and _is_md_table_separator(lines[index + 1])
    )


def _is_md_table_separator(line: str) -> bool:
    stripped = line.strip()
    if not stripped.startswith("|") or not stripped.endswith("|"):
        return False
    return all(set(cell.strip()) <= {"-", ":"} for cell in stripped.strip("|").split("|"))


def _render_html_table(rows: list[str], asset_dir: Path | None = None) -> str:
    if len(rows) < 2:
        return ""
    header = _split_md_row(rows[0])
    body = [_split_md_row(row) for row in rows[2:]]
    out = ["<table>", "<thead>", "<tr>"]
    for cell in header:
        out.append(f"<th>{_inline_md_to_html(cell.strip(), asset_dir)}</th>")
    out.extend(["</tr>", "</thead>", "<tbody>"])
    for row in body:
        out.append("<tr>")
        for cell in row:
            out.append(f"<td>{_inline_md_to_html(cell.strip(), asset_dir)}</td>")
        out.append("</tr>")
    out.extend(["</tbody>", "</table>"])
    return "\n".join(out)


def _split_md_row(row: str) -> list[str]:
    text = row.strip()
    if text.startswith("|"):
        text = text[1:]
    if text.endswith("|"):
        text = text[:-1]
    cells = []
    current = []
    escaped = False
    for char in text:
        if escaped:
            current.append(char)
            escaped = False
        elif char == "\\":
            escaped = True
        elif char == "|":
            cells.append("".join(current))
            current = []
        else:
            current.append(char)
    cells.append("".join(current))
    return cells


def _html_image_src(ref: str, asset_dir: Path | None = None) -> str:
    if not ref or re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*:", ref):
        return ref
    image_path = _resolve_report_image(ref, asset_dir)
    if image_path is None:
        return ref
    try:
        data = image_path.read_bytes()
    except OSError:
        return ref
    mime = {
        ".svg": "image/svg+xml",
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".gif": "image/gif",
        ".webp": "image/webp",
    }.get(image_path.suffix.lower(), "application/octet-stream")
    encoded = base64.b64encode(data).decode("ascii")
    return f"data:{mime};base64,{encoded}"


def _resolve_report_image(ref: str, asset_dir: Path | None = None) -> Path | None:
    ref_path = Path(ref)
    candidates = []
    if ref_path.is_absolute():
        candidates.append(ref_path)
    if asset_dir is not None:
        candidates.extend([
            asset_dir.parent / ref,
            asset_dir / ref_path.name,
            asset_dir / ref,
        ])
    candidates.append(Path.cwd() / ref)
    for candidate in candidates:
        try:
            resolved = candidate.resolve()
        except OSError:
            continue
        if resolved.is_file():
            return resolved
    return None


def _inline_md_to_html(text: str, asset_dir: Path | None = None) -> str:
    escaped = html_escape(str(text), quote=True)
    escaped = escaped.replace("&lt;br&gt;", "<br>")
    escaped = re.sub(
        r"!\[([^\]]*)\]\(([^)]+)\)",
        lambda match: (
            f'<img src="{html_escape(_html_image_src(match.group(2), asset_dir), quote=True)}" '
            f'alt="{html_escape(match.group(1), quote=True)}" loading="lazy">'
        ),
        escaped,
    )
    escaped = re.sub(
        r"\[([^\]]+)\]\(([^)]+)\)",
        lambda match: (
            f'<a href="{html_escape(match.group(2), quote=True)}">'
            f'{match.group(1)}</a>'
        ),
        escaped,
    )
    escaped = re.sub(r"`([^`]+)`", r"<code>\1</code>", escaped)
    escaped = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", escaped)
    return escaped


class Reporter:
    def __init__(self, results: list[CheckResult],
                 ibis_file: "IBISFile", verbose: bool = False,
                 max_level: int | None = None,
                 zout_rload_ohm: float = DEFAULT_ZOUT_RLOAD_OHM):
        self.results   = results
        self.ibis_file = ibis_file
        self.verbose   = verbose
        self.max_level = max_level
        self.zout_rload_ohm = zout_rload_ohm

    # ── Text report ───────────────────────────────────────────────────────────

    def as_text(self) -> str:
        lines = []
        f = self.ibis_file

        lines.append("=" * 72)
        lines.append(f"IBIS QA Report — AUTO Checks and SEMI-AUTO Evidence")
        lines.append(f"File   : {f.path}")
        lines.append(f"Target : {'IQ' + str(self.max_level) if self.max_level else 'All implemented levels'}")
        lines.append(f"IBIS Ver: {f.ibis_ver}   File Rev: {f.file_rev}   Date: {f.date}")
        lines.append(f"IQ Score in file: {f.iq_score_in_file or '(not found)'}")
        lines.append("=" * 72)

        # Group by check_id
        by_check: dict[str, list[CheckResult]] = {}
        for r in self.results:
            by_check.setdefault(r.check_id, []).append(r)

        total_pass = total_fail = total_na = total_warn = total_err = 0

        for check_id in sorted(by_check.keys(), key=self._sort_key):
            group = by_check[check_id]
            # Determine worst status for this check
            worst = self._worst(group)
            n_fail = sum(1 for r in group if r.status == Status.FAIL)
            n_pass = sum(1 for r in group if r.status == Status.PASS)
            n_na   = sum(1 for r in group if r.status == Status.NA)

            # Always show FAIL/ERROR/WARN; hide PASS and NA in non-verbose mode
            if not self.verbose and worst in (Status.PASS, Status.NA):
                total_pass += n_pass
                total_na   += n_na
                continue

            lines.append("")
            lines.append(f"[{check_id}] {_STATUS_SYMBOL[worst]}  "
                         f"({n_fail} fail, {n_pass} pass, {n_na} NA, "
                         f"total {len(group)})")

            for r in group:
                if not self.verbose and r.status in (Status.PASS, Status.NA):
                    continue
                sym = _STATUS_SYMBOL[r.status]
                lines.append(f"  {sym} [{r.subject}] {r.message}")
                for d in r.details:
                    lines.append(f"      {d}")

            total_fail  += n_fail
            total_pass  += n_pass
            total_na    += n_na
            total_warn  += sum(1 for r in group if r.status == Status.WARN)
            total_err   += sum(1 for r in group if r.status == Status.ERROR)

        lines.append("")
        lines.append("=" * 72)
        lines.append(f"SUMMARY")
        lines.append(f"  FAIL  : {total_fail}")
        lines.append(f"  WARN  : {total_warn}")
        lines.append(f"  PASS  : {total_pass}")
        lines.append(f"  NA    : {total_na}")
        lines.append(f"  ERROR : {total_err}")
        lines.append(f"  Total results: {len(self.results)}")
        lines.append("=" * 72)

        return "\n".join(lines)

    # ── JSON report ───────────────────────────────────────────────────────────

    def as_dict(self) -> dict:
        f = self.ibis_file
        scoped_results = [
            self._result_to_dict(r, result_index)
            for result_index, r in enumerate(self.results)
        ]
        level_summary = _level_summary_from_results(scoped_results, self.max_level)
        zout_by_model = estimate_zout_for_ibis(f, self.zout_rload_ohm)
        return {
            "file": str(f.path),
            "max_level": self.max_level,
            "ibis_ver": f.ibis_ver,
            "file_rev": f.file_rev,
            "iq_score_in_file": f.iq_score_in_file,
            "header": self._header_dict(),
            "components": self._components_dict(scoped_results),
            "models": self._models_dict(scoped_results, zout_by_model),
            "package_models": self._package_models_dict(scoped_results),
            "zout_summary": summarize_zout_results(zout_by_model),
            "file_results": [
                r for r in scoped_results
                if r["scope"] == "file"
            ],
            "ungrouped_results": [
                r for r in scoped_results
                if r["scope"] == "unknown"
            ],
            "results": scoped_results,
            "review_queue": [
                r for r in scoped_results
                if r["review_required"]
            ],
            "summary": {
                s.value: sum(1 for r in self.results if r.status == s)
                for s in Status
            },
            "review_summary": {
                "review_required": sum(1 for r in scoped_results if r["review_required"]),
                "semi_auto_results": sum(
                    1 for r in scoped_results
                    if r["automation_class"] == "semi_auto"
                ),
            },
            "level_summary": level_summary,
            "score_summary": _score_summary_from_levels(level_summary),
        }

    def as_json(self) -> str:
        return json.dumps(self.as_dict(), indent=2)

    def as_markdown(
            self,
            asset_dir: str | Path | None = None,
            asset_ref_prefix: str | None = None) -> str:
        return render_markdown_report(self.as_dict(), asset_dir, asset_ref_prefix)

    def as_html(
            self,
            asset_dir: str | Path | None = None,
            asset_ref_prefix: str | None = None) -> str:
        return render_html_report(self.as_dict(), asset_dir, asset_ref_prefix)

    # ── Helpers ───────────────────────────────────────────────────────────────

    @staticmethod
    def _worst(group: list[CheckResult]) -> Status:
        for s in _STATUS_ORDER:
            if any(r.status == s for r in group):
                return s
        return Status.NA

    @staticmethod
    def _sort_key(check_id: str) -> tuple:
        try:
            return tuple(int(x) for x in check_id.split('.'))
        except ValueError:
            return (999,)

    def _header_dict(self) -> dict:
        f = self.ibis_file
        return {
            "path": str(f.path),
            "file_name": f.file_name,
            "ibis_ver": f.ibis_ver,
            "date": f.date,
            "file_rev": f.file_rev,
            "source": f.source,
            "notes": f.notes,
            "iq_score_in_file": f.iq_score_in_file,
            "ibischk_ver_in_file": f.ibischk_ver_in_file,
            "component_count": len(f.components),
            "model_count": len(f.models),
            "package_model_count": len(f.pkg_models),
        }

    def _result_to_dict(self, r: CheckResult, result_index: int) -> dict:
        scope_info = self._scope_for_subject(r.subject)
        metadata = _CHECK_METADATA.get(r.check_id, {})
        return {
            "result_id": f"R{result_index:05d}",
            "check_id": r.check_id,
            "iq_level": metadata.get("iq_level"),
            "numeric_level": metadata.get("numeric_level"),
            "status": r.status.value,
            "scope": scope_info["scope"],
            "automation_class": r.automation_class,
            "review_required": r.review_required,
            "component_name": scope_info.get("component_name"),
            "model_name": scope_info.get("model_name"),
            "package_model_name": scope_info.get("package_model_name"),
            "subject": r.subject,
            "message": r.message,
            "details": r.details,
            "data": r.data,
            "spec_ref": r.spec_ref,
        }

    def _scope_for_subject(self, subject: str) -> dict:
        f = self.ibis_file
        file_subjects = {str(f.path), f.path.name, f.file_name}
        if subject in file_subjects:
            return {"scope": "file"}
        if subject in f.models:
            return {"scope": "model", "model_name": subject}
        if subject in {c.name for c in f.components}:
            return {"scope": "component", "component_name": subject}
        if subject in f.pkg_models:
            return {"scope": "package_model", "package_model_name": subject}
        return {"scope": "unknown"}

    def _components_dict(self, scoped_results: list[dict]) -> list[dict]:
        out = []
        for component in self.ibis_file.components:
            model_names = sorted({
                pin.model_name
                for pin in component.pins
                if pin.model_name in self.ibis_file.models
            })
            out.append({
                "name": component.name,
                "manufacturer": component.manufacturer,
                "pkg_model_ref": component.pkg_model_ref,
                "is_bare_die": component.is_bare_die,
                "pin_count": len(component.pins),
                "pin_mapping_count": len(component.pin_mapping),
                "diff_pin_count": len(component.diff_pins),
                "model_names": model_names,
                "results": [
                    r for r in scoped_results
                    if r["scope"] == "component"
                    and r["component_name"] == component.name
                ],
            })
        return out

    def _models_dict(self, scoped_results: list[dict], zout_by_model: dict[str, dict]) -> dict:
        model_to_components = {name: [] for name in self.ibis_file.models}
        for component in self.ibis_file.components:
            used = {
                pin.model_name
                for pin in component.pins
                if pin.model_name in self.ibis_file.models
            }
            for model_name in used:
                model_to_components[model_name].append(component.name)

        out = {}
        for name, model in self.ibis_file.models.items():
            out[name] = {
                "name": name,
                "model_type": model.model_type,
                "component_names": sorted(model_to_components[name]),
                "voltage_range": model.voltage_range,
                "pullup_ref": model.pullup_ref,
                "pulldown_ref": model.pulldown_ref,
                "power_clamp_ref": model.power_clamp_ref,
                "gnd_clamp_ref": model.gnd_clamp_ref,
                "has_pullup": model.pullup is not None,
                "has_pulldown": model.pulldown is not None,
                "has_power_clamp": model.power_clamp is not None,
                "has_gnd_clamp": model.gnd_clamp is not None,
                "has_ramp": model.ramp is not None,
                "waveform_count": len(model.waveforms),
                "iv_plot_data": self._iv_plot_data(model),
                "isso_plot_data": self._isso_plot_data(model),
                "waveform_plot_data": self._waveform_plot_data(model),
                "zout": zout_by_model.get(name, {}),
                "results": [
                    r for r in scoped_results
                    if r["scope"] == "model"
                    and r["model_name"] == name
                ],
            }
        return out

    def _iv_plot_data(self, model) -> dict:
        tables = {
            "pulldown": model.pulldown,
            "pullup": model.pullup,
            "gnd_clamp": model.gnd_clamp,
            "power_clamp": model.power_clamp,
        }
        data = {}
        for name, table in tables.items():
            if table is None or not table.rows:
                continue
            data[name] = {
                "rows": self._sample_table_rows(table.rows),
            }
        return data

    def _isso_plot_data(self, model) -> dict:
        tables = {
            "isso_pd": model.isso_pd,
            "isso_pu": model.isso_pu,
        }
        data = {}
        for name, table in tables.items():
            if table is None or not table.rows:
                continue
            data[name] = {
                "rows": self._sample_table_rows(table.rows),
            }
        return data

    def _waveform_plot_data(self, model) -> list[dict]:
        data = []
        for index, waveform in enumerate(model.waveforms, start=1):
            data.append({
                "index": index,
                "direction": waveform.direction,
                "r_fixture": waveform.vt.r_fixture,
                "v_fixture": waveform.vt.v_fixture,
                "vt_rows": self._sample_table_rows(waveform.vt.rows),
                "composite_current_rows": (
                    self._sample_table_rows(waveform.composite_current.rows)
                    if waveform.composite_current is not None
                    else []
                ),
            })
        return data

    def _sample_table_rows(self, rows: list[tuple], max_points: int = 240) -> list[list[float | None]]:
        if len(rows) <= max_points:
            selected = rows
        else:
            indexes = {
                round(i * (len(rows) - 1) / (max_points - 1))
                for i in range(max_points)
            }
            selected = [rows[index] for index in sorted(indexes)]
        return [
            [
                row[idx] if idx < len(row) else None
                for idx in range(4)
            ]
            for row in selected
        ]

    def _package_models_dict(self, scoped_results: list[dict]) -> dict:
        out = {}
        for name, pkg_model in self.ibis_file.pkg_models.items():
            out[name] = {
                "name": name,
                "description": pkg_model.description,
                "num_pins": pkg_model.num_pins,
                "pin_number_count": len(pkg_model.pin_numbers),
                "has_merged_pins": pkg_model.has_merged_pins,
                "results": [
                    r for r in scoped_results
                    if r["scope"] == "package_model"
                    and r["package_model_name"] == name
                ],
            }
        return out
