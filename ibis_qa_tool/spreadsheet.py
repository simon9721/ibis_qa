"""Spreadsheet report generation for IBIS QA reports.

The project intentionally avoids third-party runtime dependencies, so this
module writes a compact .xlsx package directly with the Python standard
library. The generated workbook follows the IBIS checklist shape: summary,
component sheets, model sheets, and a raw results sheet.
"""

from __future__ import annotations

import json
import re
import zipfile
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from xml.sax.saxutils import escape


_SPEC_PATH = Path(__file__).resolve().parent.parent / "data" / "ibis_quality_spec_3_0.json"

_STATUS_ORDER = ["FAIL", "ERROR", "WARN", "EXCEPTION", "PASS", "NA"]
_ATTENTION_STATUSES = {"FAIL", "ERROR", "WARN"}
_COMPONENT_CHECK_IDS = [
    "3.1.1", "3.1.2", "3.1.3", "3.1.4",
    "3.2.1", "3.2.2",
    "3.3.1", "3.3.2",
    "3.4.1", "3.4.2", "3.4.3",
    "4.1", "4.2",
]
_MODEL_CHECK_IDS = [
    "5.1.1", "5.1.2", "5.1.3", "5.1.4",
    "5.2.1", "5.2.2", "5.2.3", "5.2.5", "5.2.6", "5.2.7",
    "5.2.8", "5.2.9", "5.2.10", "5.2.11", "5.2.12", "5.2.13",
    "5.2.14",
    "5.3.1", "5.3.2", "5.3.3", "5.3.4", "5.3.5", "5.3.6",
    "5.3.7", "5.3.8", "5.3.9", "5.3.10", "5.3.11", "5.3.12",
    "5.3.13", "5.3.14",
    "5.4.1", "5.4.2", "5.4.3", "5.4.4",
    "5.5.1", "5.5.2", "5.5.3", "5.5.4",
    "5.6.1", "5.6.2",
    "5.7.1", "5.7.2", "5.7.3", "5.7.4",
    "5.8.1", "5.8.2", "5.8.3", "5.8.4", "5.8.5", "5.8.6",
    "5.8.7", "5.8.8",
]


@dataclass(frozen=True)
class Cell:
    value: object = ""
    style: int = 0


@dataclass
class Sheet:
    name: str
    rows: list[list[object]]
    widths: list[float]
    freeze_row: int | None = None


def write_spreadsheet_report(
    report: dict,
    path: str | Path,
    target_level: int | None = None,
    review_decisions: dict | str | Path | None = None,
) -> Path:
    """Write an .xlsx spreadsheet report and return the output path."""
    output_path = Path(path)
    if output_path.suffix.lower() != ".xlsx":
        output_path = output_path.with_suffix(".xlsx")

    metadata = _load_check_metadata()
    decisions = _load_review_decisions(review_decisions)
    sheets = _build_sheets(report, metadata, target_level, decisions)
    _write_xlsx(output_path, sheets)
    return output_path


def _load_check_metadata() -> dict[str, dict]:
    try:
        data = json.loads(_SPEC_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return {
        item["id"]: {
            "id": item.get("id"),
            "level": item.get("level"),
            "numeric_level": item.get("numeric_level"),
            "title": item.get("title"),
            "automation_class": (item.get("automation") or {}).get("class"),
            "rationale": (item.get("automation") or {}).get("rationale"),
            "how": (item.get("automation") or {}).get("how"),
            "optional": item.get("optional", False),
        }
        for item in data.get("checks", [])
        if item.get("id")
    }


def _load_review_decisions(review_decisions: dict | str | Path | None) -> dict[str, dict]:
    if not review_decisions:
        return {}
    if isinstance(review_decisions, (str, Path)):
        try:
            payload = json.loads(Path(review_decisions).read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return {}
    else:
        payload = review_decisions
    decisions = payload.get("decisions", []) if isinstance(payload, dict) else []
    indexed: dict[str, dict] = {}
    for item in decisions:
        if not isinstance(item, dict):
            continue
        for field in ("review_key", "result_key", "manual_key", "result_id", "legacy_result_id"):
            value = item.get(field)
            if value:
                indexed[str(value)] = item
        source = item.get("source_result") or item.get("source_item") or {}
        if isinstance(source, dict):
            for field in ("review_key", "result_key", "manual_key", "result_id", "legacy_result_id"):
                value = source.get(field)
                if value:
                    indexed[str(value)] = item
    return indexed


def _build_sheets(
    report: dict,
    metadata: dict[str, dict],
    target_level: int | None,
    review_decisions: dict[str, dict],
) -> list[Sheet]:
    used_names: set[str] = set()
    sheets = [_summary_sheet(report, used_names, target_level, review_decisions)]

    for component in report.get("components", []):
        sheets.append(_component_sheet(report, component, metadata, used_names, target_level, review_decisions))

    for model_name, model in report.get("models", {}).items():
        sheets.append(_model_sheet(report, model_name, model, metadata, used_names, target_level, review_decisions))

    sheets.append(_manual_review_sheet(report, used_names, review_decisions))
    sheets.append(_results_sheet(report, used_names, review_decisions))
    return sheets


def _summary_sheet(
    report: dict,
    used_names: set[str],
    target_level: int | None,
    review_decisions: dict[str, dict],
) -> Sheet:
    header = report.get("header", {})
    summary = report.get("summary", {})
    score = report.get("score_summary", {})
    ibischk = _ibischk_data(report)
    level1_passed = _level1_passed(report)

    rows: list[list[object]] = [
        [Cell("IBIS Quality Spreadsheet Report", 1)],
        ["Generated", datetime.now().astimezone().isoformat(timespec="seconds")],
        ["IBIS File", Path(report.get("file", "")).name],
        ["IBIS Version", report.get("ibis_ver", "")],
        ["File Rev", report.get("file_rev", "")],
        ["Date", header.get("date", "")],
        ["Source", header.get("source", "")],
        ["IQ Score in file", report.get("iq_score_in_file") or "(not found)"],
        ["Target IQ level", f"IQ{target_level}" if target_level else "All implemented levels"],
        ["Review overlay", f"{len(review_decisions)} decision(s) loaded" if review_decisions else "None"],
        ["Candidate level from checked items", score.get("tool_score") or score.get("implemented_check_score", "")],
        ["Final IQ score", "To be assigned after manual review and accepted exceptions"],
        [],
        [Cell("IBISCHK Parser Information", 3)],
        ["Version", ibischk.get("version", "")],
        ["Errors", ibischk.get("errors", "")],
        ["Warnings", ibischk.get("warnings", "")],
        ["Cautions", ibischk.get("cautions", "")],
        ["Executable", ibischk.get("path", "")],
        [],
        [Cell("Result Summary", 3)],
        [Cell("Status", 2), Cell("Count", 2)],
    ]
    for status in ("PASS", "FAIL", "WARN", "NA", "ERROR"):
        rows.append([status, summary.get(status, 0)])

    rows.extend([
        [],
        [Cell("File Header", 3)],
        [Cell("IQ Spec Reference", 2), Cell("IQ Level", 2), Cell("Description", 2), Cell("PASS/FAIL", 2), Cell("Comments", 2)],
    ])
    file_results = [r for r in report.get("results", []) if r.get("check_id") == "2.1"]
    status, comments = _status_and_comments("2.1", file_results, {"2.1": {"automation_class": "auto"}}, review_decisions)
    rows.append(["2.1", "LEVEL 1", "IBIS file passes IBISCHK", Cell(status, _status_style(status)), comments])

    rows.extend([
        [],
        [Cell("Components", 3)],
        [Cell("Component", 2), Cell("Candidate IQ Level", 2), Cell("Comments", 2)],
    ])
    for component in report.get("components", []):
        component_results = _component_results(report, component)
        rows.append([
            component.get("name", ""),
            _candidate_score(component_results, level1_passed, review_decisions, target_level),
            _scope_comment(component_results, review_decisions),
        ])

    rows.extend([
        [],
        [Cell("Models", 3)],
        [Cell("Model", 2), Cell("Type", 2), Cell("Candidate IQ Level", 2), Cell("Comments", 2)],
    ])
    for model_name, model in report.get("models", {}).items():
        model_results = model.get("results", [])
        rows.append([
            model_name,
            model.get("model_type", ""),
            _candidate_score(model_results, level1_passed, review_decisions, target_level),
            _scope_comment(model_results, review_decisions),
        ])

    rows.extend([
        [],
        [Cell("Zout Estimates", 3)],
        [Cell("Model", 2), Cell("Type", 2), Cell("Pulldown typ/min/max", 2), Cell("Pullup typ/min/max", 2), Cell("Comments", 2)],
    ])
    for model_name, model in report.get("models", {}).items():
        zout = model.get("zout") or {}
        summary = zout.get("summary") or {}
        rows.append([
            model_name,
            model.get("model_type", ""),
            _zout_triplet(summary.get("pulldown") or {}),
            _zout_triplet(summary.get("pullup") or {}),
            _zout_notes(zout),
        ])

    rows.extend([
        [],
        [Cell("Review Queue", 3)],
        ["Semi-auto review items", len(report.get("review_queue", []))],
        ["Manual review items", len(report.get("manual_review_queue", []))],
        ["Final signoff ready", "Yes" if (report.get("signoff_summary") or {}).get("final_ready") else "No"],
    ])

    return Sheet(_unique_sheet_name("summary", used_names), rows, [28, 28, 24, 18, 90])


def _component_sheet(
    report: dict,
    component: dict,
    metadata: dict[str, dict],
    used_names: set[str],
    target_level: int | None,
    review_decisions: dict[str, dict],
) -> Sheet:
    component_results = _component_results(report, component)
    level1_passed = _level1_passed(report)
    rows: list[list[object]] = [
        [Cell("COMPONENT:", 1), component.get("name", "")],
        ["IQ Level:", _candidate_score(component_results, level1_passed, review_decisions, target_level)],
        ["Exception:", ""],
        ["Correlation:", ""],
        [],
        ["Pin count", component.get("pin_count", 0)],
        ["Pin mapping entries", component.get("pin_mapping_count", 0)],
        ["Diff pin entries", component.get("diff_pin_count", 0)],
        ["Package model", component.get("pkg_model_ref", "")],
        ["Bare die", "Yes" if component.get("is_bare_die") else "No"],
        [],
        ["In column PASS/FAIL below, generated results are filled from the QA report."],
        ["MANUAL REVIEW means the item needs external evidence or reviewer judgement."],
        [],
        [Cell("IQ Spec Reference", 2), Cell("IQ Level", 2), Cell("Automation", 2), Cell("Description", 2), Cell("PASS/FAIL", 2), Cell("Comments", 2)],
    ]

    for check_id in _filter_check_ids(_COMPONENT_CHECK_IDS, metadata, target_level):
        relevant = _results_for_component_check(report, component, check_id)
        rows.append(_check_row(check_id, relevant, metadata, review_decisions))

    return Sheet(
        _unique_sheet_name(f"component {component.get('name', '')}", used_names),
        rows,
        [18, 16, 16, 54, 18, 90],
        freeze_row=15,
    )


def _model_sheet(
    report: dict,
    model_name: str,
    model: dict,
    metadata: dict[str, dict],
    used_names: set[str],
    target_level: int | None,
    review_decisions: dict[str, dict],
) -> Sheet:
    model_results = model.get("results", [])
    level1_passed = _level1_passed(report)
    rows: list[list[object]] = [
        [Cell("MODEL:", 1), model_name],
        ["IQ Level:", _candidate_score(model_results, level1_passed, review_decisions, target_level)],
        ["Exception:", ""],
        ["Correlation:", ""],
        [],
        ["Model type", model.get("model_type", "")],
        ["Components", ", ".join(model.get("component_names", []))],
        ["Waveform tables", model.get("waveform_count", 0)],
        ["Has pullup", "Yes" if model.get("has_pullup") else "No"],
        ["Has pulldown", "Yes" if model.get("has_pulldown") else "No"],
        ["Has ramp", "Yes" if model.get("has_ramp") else "No"],
        ["Zout pulldown typ/min/max", _zout_triplet(((model.get("zout") or {}).get("summary") or {}).get("pulldown") or {})],
        ["Zout pullup typ/min/max", _zout_triplet(((model.get("zout") or {}).get("summary") or {}).get("pullup") or {})],
        [],
        ["In column PASS/FAIL below, generated results are filled from the QA report."],
        ["MANUAL REVIEW means the item needs external evidence or reviewer judgement."],
        [],
        [Cell("IQ Spec Reference", 2), Cell("IQ Level", 2), Cell("Automation", 2), Cell("Description", 2), Cell("PASS/FAIL", 2), Cell("Comments", 2)],
    ]

    for check_id in _filter_check_ids(_MODEL_CHECK_IDS, metadata, target_level):
        relevant = [r for r in model_results if r.get("check_id") == check_id]
        rows.append(_check_row(check_id, relevant, metadata, review_decisions))

    return Sheet(
        _unique_sheet_name(f"model {model_name}", used_names),
        rows,
        [18, 16, 16, 62, 18, 95],
        freeze_row=18,
    )


def _manual_review_sheet(report: dict, used_names: set[str], review_decisions: dict[str, dict]) -> Sheet:
    rows: list[list[object]] = [[
        Cell("Review Key", 2),
        Cell("Check ID", 2),
        Cell("IQ Level", 2),
        Cell("Scope", 2),
        Cell("Subject", 2),
        Cell("Description", 2),
        Cell("Decision", 2),
        Cell("External Evidence", 2),
        Cell("Datasheet / Reference", 2),
        Cell("Reviewer Comment", 2),
        Cell("Model-Maker Action", 2),
    ]]
    for item in report.get("manual_review_queue", []):
        decision = _decision_for_result(item, review_decisions) or item.get("review_decision") or {}
        decision_label = decision.get("decision", "Pending") if decision else "Pending"
        rows.append([
            item.get("review_key", ""),
            item.get("check_id", ""),
            item.get("iq_level", ""),
            item.get("scope", ""),
            item.get("subject", ""),
            item.get("title", item.get("message", "")),
            Cell(decision_label, _status_style(_decision_status(decision_label) or "MANUAL REVIEW")),
            decision.get("external_evidence", "") if decision else "",
            decision.get("datasheet_section", "") if decision else "",
            decision.get("comment", "") if decision else "",
            decision.get("model_maker_action", "") if decision else "",
        ])
    if len(rows) == 1:
        rows.append(["", "", "", "", "", "No manual items in scope.", "", "", "", "", ""])
    return Sheet(
        _unique_sheet_name("manual review", used_names),
        rows,
        [18, 10, 12, 14, 28, 70, 18, 45, 45, 60, 60],
        freeze_row=1,
    )


def _results_sheet(report: dict, used_names: set[str], review_decisions: dict[str, dict]) -> Sheet:
    rows: list[list[object]] = [[
        Cell("Result ID", 2),
        Cell("Check ID", 2),
        Cell("IQ Level", 2),
        Cell("Automation", 2),
        Cell("Generated Status", 2),
        Cell("Effective Status", 2),
        Cell("Scope", 2),
        Cell("Subject", 2),
        Cell("Review Required", 2),
        Cell("Review Decision", 2),
        Cell("Review Comment", 2),
        Cell("Message", 2),
        Cell("Details", 2),
    ]]
    for result in report.get("results", []):
        status = result.get("status", "")
        effective = _effective_status(result, review_decisions)
        decision = _decision_for_result(result, review_decisions)
        rows.append([
            result.get("result_id", ""),
            result.get("check_id", ""),
            result.get("iq_level", ""),
            result.get("automation_class", ""),
            Cell(status, _status_style(_sheet_status(status))),
            Cell(effective, _status_style(_sheet_status(effective))),
            result.get("scope", ""),
            result.get("subject", ""),
            "Yes" if result.get("review_required") else "No",
            decision.get("decision", "") if decision else "",
            decision.get("comment", "") if decision else "",
            result.get("message", ""),
            _details_text(result),
        ])
    return Sheet(_unique_sheet_name("results", used_names), rows, [18, 10, 12, 14, 14, 14, 14, 28, 16, 18, 50, 60, 90], freeze_row=1)


def _check_row(
    check_id: str,
    results: list[dict],
    metadata: dict[str, dict],
    review_decisions: dict[str, dict],
) -> list[object]:
    item = metadata.get(check_id, {})
    status, comments = _status_and_comments(check_id, results, metadata, review_decisions)
    return [
        check_id,
        item.get("level", ""),
        item.get("automation_class", ""),
        item.get("title", ""),
        Cell(status, _status_style(status)),
        comments,
    ]


def _status_and_comments(
    check_id: str,
    results: list[dict],
    metadata: dict[str, dict],
    review_decisions: dict[str, dict],
) -> tuple[str, str]:
    item = metadata.get(check_id, {})
    if results:
        effective_statuses = [_effective_status(result, review_decisions) for result in results]
        worst = next(
            (status for status in _STATUS_ORDER if status in effective_statuses),
            "NA",
        )
        return _sheet_status(worst), _summarize_results(results, review_decisions)

    automation_class = item.get("automation_class", "")
    if automation_class == "manual":
        rationale = item.get("rationale") or "Requires external evidence or reviewer judgement."
        return "MANUAL REVIEW", f"Manual review required: {rationale}"
    if item.get("optional"):
        return "OPTIONAL", "Optional item; not part of required IQ score."
    return "NA", "No generated result for this scope; item appears not applicable or no section was present."


def _sheet_status(status: str) -> str:
    if status == "WARN":
        return "REVIEW"
    return status or "---"


def _status_style(status: str) -> int:
    return {
        "PASS": 4,
        "FAIL": 5,
        "ERROR": 5,
        "REVIEW": 6,
        "WARN": 6,
        "EXCEPTION": 6,
        "MANUAL REVIEW": 6,
        "NA": 7,
        "OPTIONAL": 7,
        "---": 7,
    }.get(status, 0)


def _summarize_results(results: list[dict], review_decisions: dict[str, dict]) -> str:
    counts = Counter(_effective_status(result, review_decisions) for result in results)
    prefix = ", ".join(
        f"{status}={counts[status]}"
        for status in _STATUS_ORDER
        if counts.get(status)
    )
    messages = []
    seen = set()
    for result in results:
        reason = _result_reason(result)
        decision = _decision_for_result(result, review_decisions)
        if decision and _decision_status(decision.get("decision", "")):
            comment = decision.get("comment", "")
            decision_text = f"Reviewer: {decision.get('decision')}"
            if comment:
                decision_text += f" - {comment}"
            reason = f"{reason} [{decision_text}]"
        if reason and reason not in seen:
            seen.add(reason)
            messages.append(reason)
        if len(messages) >= 4:
            break
    body = " | ".join(messages)
    if len(seen) < len({ _result_reason(r) for r in results if _result_reason(r) }):
        body += " | More finding types omitted."
    return _limit_cell(f"{prefix}. {body}".strip(". "))


def _filter_check_ids(
    check_ids: list[str],
    metadata: dict[str, dict],
    target_level: int | None,
) -> list[str]:
    if target_level is None:
        return check_ids
    filtered = []
    for check_id in check_ids:
        numeric_level = metadata.get(check_id, {}).get("numeric_level")
        if numeric_level is None or numeric_level <= target_level:
            filtered.append(check_id)
    return filtered


def _decision_for_result(result: dict, review_decisions: dict[str, dict]) -> dict | None:
    decision = None
    for field in ("review_key", "result_key", "manual_key", "result_id", "legacy_result_id"):
        value = result.get(field)
        if value and str(value) in review_decisions:
            decision = review_decisions[str(value)]
            break
    if not decision and result.get("review_decision"):
        decision = result.get("review_decision")
    if not decision:
        return None
    if not _decision_status(decision.get("decision", "")):
        return None
    return decision


def _decision_status(decision: str) -> str | None:
    mapping = {
        "Accepted": "PASS",
        "Exception": "EXCEPTION",
        "Rejected": "FAIL",
        "Not Applicable": "NA",
    }
    return mapping.get(decision)


def _effective_status(result: dict, review_decisions: dict[str, dict]) -> str:
    decision = _decision_for_result(result, review_decisions)
    if decision:
        return _decision_status(decision.get("decision", "")) or result.get("status", "")
    return result.get("effective_status") or result.get("status", "")


def _result_reason(result: dict) -> str:
    message = str(result.get("message", ""))
    details = [str(detail) for detail in (result.get("details") or [])[:2]]
    if details:
        return f"{message}: {'; '.join(details)}"
    return message


def _details_text(result: dict) -> str:
    return _limit_cell("\n".join(str(detail) for detail in result.get("details") or []))


def _zout_triplet(values: dict) -> str:
    parts = []
    for corner in ("typ", "min", "max"):
        value = values.get(corner)
        parts.append(_fmt_ohm(value) if value is not None else "NA")
    return " / ".join(parts)


def _fmt_ohm(value) -> str:
    try:
        return f"{float(value):.3g} ohm"
    except (TypeError, ValueError):
        return ""


def _zout_notes(zout: dict) -> str:
    if not zout:
        return "No Zout data generated."
    if zout.get("available"):
        return "Estimated from available Pullup/Pulldown corners."
    notes = [str(note).strip().rstrip(".") for note in (zout.get("notes") or [])]
    if (
        any("[Pulldown]" in note for note in notes)
        and any("[Pullup]" in note for note in notes)
    ):
        return "No usable Pullup/Pulldown driver table."
    return _limit_cell("; ".join(notes) or "No load-line estimate available.")


def _scope_comment(results: list[dict], review_decisions: dict[str, dict]) -> str:
    attention = [
        r for r in results
        if _result_blocks_score(r, review_decisions)
    ]
    if not attention:
        return "No generated findings need attention."
    counts = Counter(_effective_status(r, review_decisions) for r in attention)
    pieces = [f"{status}={counts[status]}" for status in _STATUS_ORDER if counts.get(status)]
    return "; ".join(pieces)


def _candidate_score(
    results: list[dict],
    level1_passed: bool,
    review_decisions: dict[str, dict] | None = None,
    target_level: int | None = None,
) -> str:
    review_decisions = review_decisions or {}
    if not level1_passed:
        return "Below IQ1"
    candidate = 1
    max_level = target_level or 4
    for level in range(2, max_level + 1):
        level_results = [r for r in results if r.get("numeric_level") == level]
        if not level_results:
            break
        if any(_result_blocks_score(r, review_decisions) for r in level_results):
            break
        candidate = level
    return f"IQ{candidate}"


def _result_blocks_score(result: dict, review_decisions: dict[str, dict]) -> bool:
    effective_status = _effective_status(result, review_decisions)
    if effective_status in {"PASS", "NA", "EXCEPTION"}:
        return False
    return effective_status in {"FAIL", "ERROR"}


def _level1_passed(report: dict) -> bool:
    level_summary = report.get("level_summary") or []
    if not level_summary:
        return False
    row = level_summary[0]
    return (
        row.get("failed_items", 0) == 0
        and row.get("error_items", 0) == 0
    )


def _component_results(report: dict, component: dict) -> list[dict]:
    results = list(component.get("results", []))
    package_name = component.get("pkg_model_ref")
    if package_name:
        package = report.get("package_models", {}).get(package_name)
        if package:
            results.extend(package.get("results", []))
    return results


def _results_for_component_check(report: dict, component: dict, check_id: str) -> list[dict]:
    local = [r for r in _component_results(report, component) if r.get("check_id") == check_id]
    if local:
        return local
    if check_id in {"4.1"}:
        return [r for r in report.get("results", []) if r.get("check_id") == check_id]
    if check_id == "3.4.3":
        return [
            r for r in report.get("results", [])
            if r.get("check_id") == check_id
            and r.get("scope") in {"file", "package_model"}
        ]
    return []


def _ibischk_data(report: dict) -> dict:
    for result in report.get("results", []):
        data = result.get("data") or {}
        ibischk = data.get("ibischk")
        if ibischk:
            return ibischk
    return {}


def _limit_cell(value: str, limit: int = 32700) -> str:
    if len(value) <= limit:
        return value
    return value[:limit - 20] + " ... [truncated]"


def _unique_sheet_name(name: str, used: set[str]) -> str:
    cleaned = re.sub(r"[\[\]:*?/\\]", "_", name).strip() or "sheet"
    cleaned = re.sub(r"\s+", " ", cleaned)
    base = cleaned[:31]
    candidate = base
    index = 2
    while candidate.lower() in used:
        suffix = f" {index}"
        candidate = f"{base[:31 - len(suffix)]}{suffix}"
        index += 1
    used.add(candidate.lower())
    return candidate


def _write_xlsx(path: Path, sheets: list[Sheet]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("[Content_Types].xml", _content_types_xml(len(sheets)))
        zf.writestr("_rels/.rels", _root_rels_xml())
        zf.writestr("xl/workbook.xml", _workbook_xml(sheets))
        zf.writestr("xl/_rels/workbook.xml.rels", _workbook_rels_xml(len(sheets)))
        zf.writestr("xl/styles.xml", _styles_xml())
        zf.writestr("docProps/core.xml", _core_props_xml())
        zf.writestr("docProps/app.xml", _app_props_xml())
        for index, sheet in enumerate(sheets, start=1):
            zf.writestr(f"xl/worksheets/sheet{index}.xml", _worksheet_xml(sheet))


def _content_types_xml(sheet_count: int) -> str:
    sheet_overrides = "".join(
        f'<Override PartName="/xl/worksheets/sheet{i}.xml" '
        'ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
        for i in range(1, sheet_count + 1)
    )
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        '<Default Extension="xml" ContentType="application/xml"/>'
        '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
        '<Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>'
        '<Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>'
        '<Override PartName="/docProps/app.xml" ContentType="application/vnd.openxmlformats-officedocument.extended-properties+xml"/>'
        f"{sheet_overrides}"
        '</Types>'
    )


def _root_rels_xml() -> str:
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>'
        '<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/>'
        '<Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties" Target="docProps/app.xml"/>'
        '</Relationships>'
    )


def _workbook_xml(sheets: list[Sheet]) -> str:
    sheet_xml = "".join(
        f'<sheet name="{escape(sheet.name)}" sheetId="{idx}" r:id="rId{idx}"/>'
        for idx, sheet in enumerate(sheets, start=1)
    )
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
        'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
        f"<sheets>{sheet_xml}</sheets>"
        '</workbook>'
    )


def _workbook_rels_xml(sheet_count: int) -> str:
    rels = "".join(
        f'<Relationship Id="rId{i}" '
        'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" '
        f'Target="worksheets/sheet{i}.xml"/>'
        for i in range(1, sheet_count + 1)
    )
    rels += (
        f'<Relationship Id="rId{sheet_count + 1}" '
        'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" '
        'Target="styles.xml"/>'
    )
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        f"{rels}"
        '</Relationships>'
    )


def _worksheet_xml(sheet: Sheet) -> str:
    cols = "".join(
        f'<col min="{idx}" max="{idx}" width="{width}" customWidth="1"/>'
        for idx, width in enumerate(sheet.widths, start=1)
    )
    sheet_views = '<sheetViews><sheetView workbookViewId="0"/></sheetViews>'
    if sheet.freeze_row:
        top_left = f"A{sheet.freeze_row + 1}"
        sheet_views = (
            '<sheetViews><sheetView workbookViewId="0">'
            f'<pane ySplit="{sheet.freeze_row}" topLeftCell="{top_left}" '
            'activePane="bottomLeft" state="frozen"/>'
            '</sheetView></sheetViews>'
        )
    row_xml = []
    for row_index, row in enumerate(sheet.rows, start=1):
        cells = []
        for col_index, raw_cell in enumerate(row, start=1):
            cell = raw_cell if isinstance(raw_cell, Cell) else Cell(raw_cell)
            cells.append(_cell_xml(row_index, col_index, cell))
        row_xml.append(f'<row r="{row_index}">{"".join(cells)}</row>')
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
        'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
        f"{sheet_views}"
        f"<cols>{cols}</cols>"
        f'<sheetData>{"".join(row_xml)}</sheetData>'
        '</worksheet>'
    )


def _cell_xml(row: int, col: int, cell: Cell) -> str:
    ref = f"{_column_name(col)}{row}"
    style = f' s="{cell.style}"' if cell.style else ""
    value = "" if cell.value is None else cell.value
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return f'<c r="{ref}"{style}><v>{value}</v></c>'
    text = escape(str(value))
    space = ' xml:space="preserve"' if text.startswith(" ") or text.endswith(" ") else ""
    return f'<c r="{ref}" t="inlineStr"{style}><is><t{space}>{text}</t></is></c>'


def _column_name(index: int) -> str:
    name = ""
    while index:
        index, rem = divmod(index - 1, 26)
        name = chr(65 + rem) + name
    return name


def _styles_xml() -> str:
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        '<fonts count="3">'
        '<font><sz val="11"/><name val="Calibri"/></font>'
        '<font><b/><sz val="11"/><name val="Calibri"/></font>'
        '<font><b/><sz val="14"/><name val="Calibri"/></font>'
        '</fonts>'
        '<fills count="6">'
        '<fill><patternFill patternType="none"/></fill>'
        '<fill><patternFill patternType="gray125"/></fill>'
        '<fill><patternFill patternType="solid"><fgColor rgb="FFD9EAF7"/><bgColor indexed="64"/></patternFill></fill>'
        '<fill><patternFill patternType="solid"><fgColor rgb="FFDDEED8"/><bgColor indexed="64"/></patternFill></fill>'
        '<fill><patternFill patternType="solid"><fgColor rgb="FFF4CCCC"/><bgColor indexed="64"/></patternFill></fill>'
        '<fill><patternFill patternType="solid"><fgColor rgb="FFFFF2CC"/><bgColor indexed="64"/></patternFill></fill>'
        '</fills>'
        '<borders count="1"><border><left/><right/><top/><bottom/><diagonal/></border></borders>'
        '<cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs>'
        '<cellXfs count="8">'
        '<xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/>'
        '<xf numFmtId="0" fontId="2" fillId="0" borderId="0" xfId="0" applyFont="1"/>'
        '<xf numFmtId="0" fontId="1" fillId="2" borderId="0" xfId="0" applyFont="1" applyFill="1"/>'
        '<xf numFmtId="0" fontId="1" fillId="0" borderId="0" xfId="0" applyFont="1"/>'
        '<xf numFmtId="0" fontId="0" fillId="3" borderId="0" xfId="0" applyFill="1"/>'
        '<xf numFmtId="0" fontId="0" fillId="4" borderId="0" xfId="0" applyFill="1"/>'
        '<xf numFmtId="0" fontId="0" fillId="5" borderId="0" xfId="0" applyFill="1"/>'
        '<xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/>'
        '</cellXfs>'
        '<cellStyles count="1"><cellStyle name="Normal" xfId="0" builtinId="0"/></cellStyles>'
        '</styleSheet>'
    )


def _core_props_xml() -> str:
    now = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" '
        'xmlns:dc="http://purl.org/dc/elements/1.1/" '
        'xmlns:dcterms="http://purl.org/dc/terms/" '
        'xmlns:dcmitype="http://purl.org/dc/dcmitype/" '
        'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">'
        '<dc:creator>ibis_qa_tool</dc:creator>'
        f'<dcterms:created xsi:type="dcterms:W3CDTF">{now}</dcterms:created>'
        f'<dcterms:modified xsi:type="dcterms:W3CDTF">{now}</dcterms:modified>'
        '</cp:coreProperties>'
    )


def _app_props_xml() -> str:
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties" '
        'xmlns:vt="http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes">'
        '<Application>ibis_qa_tool</Application>'
        '</Properties>'
    )
