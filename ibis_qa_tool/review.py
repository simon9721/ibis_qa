"""Review-decision helpers for IBIS QA reports.

The QA report is generated evidence. A review overlay is the reviewer-owned
layer that records judgement for semi-auto findings and manual check items.
This module keeps that behavior shared by CLI, GUI, Markdown/HTML, and XLSX.
"""

from __future__ import annotations

import copy
import hashlib
import json
import re
from collections import Counter
from datetime import datetime
from pathlib import Path


DECISIONS = [
    "Pending",
    "Accepted",
    "Exception",
    "Rejected",
    "Not Applicable",
]

DECISION_TO_STATUS = {
    "Accepted": "PASS",
    "Exception": "EXCEPTION",
    "Rejected": "FAIL",
    "Not Applicable": "NA",
}

EFFECTIVE_STATUS_ORDER = ["FAIL", "ERROR", "WARN", "EXCEPTION", "PASS", "NA"]

_SPEC_PATH = Path(__file__).resolve().parent.parent / "data" / "ibis_quality_spec_3_0.json"

_COMPONENT_MANUAL_PREFIXES = ("3.", "4.")
_DEFAULT_SCHEMA_VERSION = 2


def load_check_metadata() -> dict[str, dict]:
    try:
        data = json.loads(_SPEC_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return {
        item["id"]: {
            "id": item.get("id"),
            "level": item.get("level"),
            "iq_level": item.get("level"),
            "numeric_level": item.get("numeric_level"),
            "title": item.get("title"),
            "automation_class": (item.get("automation") or {}).get("class"),
            "rationale": (item.get("automation") or {}).get("rationale"),
            "how": (item.get("automation") or {}).get("how"),
            "optional": item.get("optional", False),
            "section_id": item.get("section_id"),
            "section_title": item.get("section_title"),
            "source_line": item.get("source_line"),
        }
        for item in data.get("checks", [])
        if item.get("id")
    }


_CHECK_METADATA = load_check_metadata()


def assign_stable_result_ids(results: list[dict]) -> None:
    """Attach deterministic review keys to generated result rows in-place."""
    seen: Counter[str] = Counter()
    for index, result in enumerate(results):
        base_key = stable_result_key(result)
        seen[base_key] += 1
        review_key = base_key if seen[base_key] == 1 else f"{base_key}-{seen[base_key]}"
        result["legacy_result_id"] = f"R{index:05d}"
        result["result_key"] = review_key
        result["review_key"] = review_key
        result["result_id"] = review_key


def stable_result_key(result: dict) -> str:
    check_id = str(result.get("check_id") or "unknown")
    scope = str(result.get("scope") or "unknown")
    subject = str(result.get("subject") or "")
    component = str(result.get("component_name") or "")
    model = str(result.get("model_name") or "")
    package_model = str(result.get("package_model_name") or "")
    status = str(result.get("status") or "")
    message = str(result.get("message") or "")
    details = "\n".join(str(item) for item in (result.get("details") or [])[:4])
    base = "|".join([
        check_id,
        scope,
        subject,
        component,
        model,
        package_model,
        status,
        message,
        details,
    ])
    digest = hashlib.sha1(base.encode("utf-8", "replace")).hexdigest()[:12]
    prefix = _slug(f"{check_id}-{scope}-{subject or model or component or package_model}", 46)
    return f"{prefix}-{digest}"


def manual_review_key(entry: dict) -> str:
    check_id = str(entry.get("check_id") or "unknown")
    scope = str(entry.get("scope") or "unknown")
    subject = str(entry.get("subject") or "")
    component = str(entry.get("component_name") or "")
    model = str(entry.get("model_name") or "")
    base = "|".join([check_id, scope, subject, component, model])
    digest = hashlib.sha1(base.encode("utf-8", "replace")).hexdigest()[:12]
    prefix = _slug(f"manual-{check_id}-{scope}-{subject or model or component}", 46)
    return f"{prefix}-{digest}"


def _slug(value: str, limit: int = 60) -> str:
    text = re.sub(r"[^A-Za-z0-9_.-]+", "-", str(value).strip()).strip("-")
    text = re.sub(r"-+", "-", text)
    return (text or "item")[:limit].strip("-") or "item"


def load_review_decisions(review_decisions: dict | str | Path | None) -> dict[str, dict]:
    """Load review decisions and index them by every known stable key."""
    if not review_decisions:
        return {}
    if isinstance(review_decisions, (str, Path)):
        try:
            payload = json.loads(Path(review_decisions).read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return {}
    else:
        payload = review_decisions

    if isinstance(payload, dict):
        decisions = payload.get("decisions", [])
    elif isinstance(payload, list):
        decisions = payload
    else:
        decisions = []

    indexed: dict[str, dict] = {}
    for raw in decisions:
        if not isinstance(raw, dict):
            continue
        item = dict(raw)
        for key in _decision_keys(item):
            indexed[key] = item
    return indexed


def _decision_keys(item: dict) -> list[str]:
    keys = []
    for field in (
        "review_key",
        "result_key",
        "manual_key",
        "result_id",
        "legacy_result_id",
    ):
        value = item.get(field)
        if value:
            keys.append(str(value))
    source = item.get("source_result") or item.get("source_item") or {}
    if isinstance(source, dict):
        for field in (
            "review_key",
            "result_key",
            "manual_key",
            "result_id",
            "legacy_result_id",
        ):
            value = source.get(field)
            if value:
                keys.append(str(value))
    return list(dict.fromkeys(keys))


def decision_for_item(item: dict, decisions: dict[str, dict]) -> dict | None:
    for key in _item_keys(item):
        decision = decisions.get(key)
        if decision:
            return decision
    return None


def _item_keys(item: dict) -> list[str]:
    keys = []
    for field in (
        "review_key",
        "result_key",
        "manual_key",
        "result_id",
        "legacy_result_id",
    ):
        value = item.get(field)
        if value:
            keys.append(str(value))
    return list(dict.fromkeys(keys))


def decision_status(decision: str) -> str | None:
    return DECISION_TO_STATUS.get(str(decision or ""))


def effective_status(item: dict, decisions: dict[str, dict] | None = None) -> str:
    decision = decision_for_item(item, decisions or {})
    if decision:
        mapped = decision_status(decision.get("decision", ""))
        if mapped:
            return mapped
    return item.get("effective_status") or item.get("status") or "PENDING"


def build_manual_review_queue(report: dict) -> list[dict]:
    max_level = report.get("max_level")
    entries: list[dict] = []
    for check_id, metadata in sorted(_CHECK_METADATA.items(), key=lambda kv: _check_sort_key(kv[0])):
        if metadata.get("automation_class") != "manual":
            continue
        numeric_level = metadata.get("numeric_level")
        if max_level is not None and numeric_level is not None and numeric_level > max_level:
            continue
        if check_id.startswith(_COMPONENT_MANUAL_PREFIXES):
            components = report.get("components") or []
            if components:
                for component in components:
                    entries.append(_manual_entry(metadata, "component", component.get("name", "")))
            else:
                entries.append(_manual_entry(metadata, "file", Path(report.get("file", "")).name))
        else:
            models = report.get("models") or {}
            if models:
                for model_name in models:
                    entries.append(_manual_entry(metadata, "model", model_name))
            else:
                entries.append(_manual_entry(metadata, "file", Path(report.get("file", "")).name))

    for entry in entries:
        key = manual_review_key(entry)
        entry["manual_key"] = key
        entry["review_key"] = key
    return entries


def _manual_entry(metadata: dict, scope: str, subject: str) -> dict:
    return {
        "item_type": "manual",
        "check_id": metadata.get("id"),
        "iq_level": metadata.get("iq_level") or metadata.get("level"),
        "numeric_level": metadata.get("numeric_level"),
        "scope": scope,
        "component_name": subject if scope == "component" else None,
        "model_name": subject if scope == "model" else None,
        "package_model_name": None,
        "subject": subject,
        "title": metadata.get("title", ""),
        "automation_class": "manual",
        "review_required": True,
        "status": "MANUAL REVIEW",
        "effective_status": "PENDING",
        "message": "Manual review requires external evidence.",
        "details": [
            metadata.get("rationale")
            or "Requires datasheet, extraction, package, circuit, or model-maker evidence."
        ],
        "spec_ref": metadata.get("section_id") or "",
    }


def apply_review_decisions(
    report: dict,
    review_decisions: dict | str | Path | None = None,
    *,
    copy_report: bool = False,
) -> dict:
    """Attach review decisions, effective statuses, and signoff summary."""
    out = copy.deepcopy(report) if copy_report else report
    decisions = load_review_decisions(review_decisions)
    if "manual_review_queue" not in out:
        out["manual_review_queue"] = build_manual_review_queue(out)

    for result in out.get("results", []):
        decision = decision_for_item(result, decisions)
        _apply_decision_fields(result, decision)

    # Nested result lists share object identity in freshly generated reports,
    # but JSON-loaded reports do not. Refresh them by key after applying.
    by_key = {
        result.get("review_key") or result.get("result_id"): result
        for result in out.get("results", [])
    }
    _refresh_nested_results(out, by_key)

    for item in out.get("review_queue", []):
        decision = decision_for_item(item, decisions)
        _apply_decision_fields(item, decision)

    for item in out.get("manual_review_queue", []):
        decision = decision_for_item(item, decisions)
        _apply_decision_fields(item, decision, manual=True)

    out["review_overlay"] = _overlay_summary(review_decisions, decisions)
    out["effective_summary"] = _effective_summary(out.get("results", []))
    out["manual_review_summary"] = _manual_summary(out.get("manual_review_queue", []))
    out["review_summary"] = _review_summary(out)
    out["signoff_summary"] = _signoff_summary(out)
    out["reviewed_level_summary"] = _reviewed_level_summary(out.get("results", []), out.get("max_level"))
    out["score_summary"] = _score_summary(out)
    return out


def _apply_decision_fields(item: dict, decision: dict | None, manual: bool = False) -> None:
    if decision:
        normalized = _normalized_decision_payload(decision)
        item["review_decision"] = normalized
        mapped = decision_status(normalized.get("decision", ""))
        item["effective_status"] = mapped or ("PENDING" if manual else item.get("status"))
        item["review_state"] = normalized.get("decision", "Pending")
    else:
        item["review_decision"] = None
        item["effective_status"] = "PENDING" if manual else item.get("status")
        item["review_state"] = "Pending" if item.get("review_required") else "Not Required"


def _normalized_decision_payload(decision: dict) -> dict:
    return {
        "decision": decision.get("decision", "Pending") or "Pending",
        "comment": decision.get("comment", "") or "",
        "external_evidence": decision.get("external_evidence", "") or "",
        "datasheet_section": decision.get("datasheet_section", "") or "",
        "model_maker_action": decision.get("model_maker_action", "") or "",
        "reviewer": decision.get("reviewer", "") or "",
        "organization": decision.get("organization", "") or "",
        "approval_date": decision.get("approval_date", "") or "",
    }


def _refresh_nested_results(report: dict, by_key: dict[str, dict]) -> None:
    def refresh(results: list[dict]) -> list[dict]:
        out = []
        for result in results:
            key = result.get("review_key") or result.get("result_id")
            out.append(by_key.get(key, result))
        return out

    report["file_results"] = refresh(report.get("file_results", []))
    report["ungrouped_results"] = refresh(report.get("ungrouped_results", []))
    report["review_queue"] = refresh(report.get("review_queue", []))
    for component in report.get("components", []):
        component["results"] = refresh(component.get("results", []))
    for model in (report.get("models") or {}).values():
        model["results"] = refresh(model.get("results", []))
    for package in (report.get("package_models") or {}).values():
        package["results"] = refresh(package.get("results", []))


def _overlay_summary(review_input, decisions: dict[str, dict]) -> dict:
    if not review_input:
        return {
            "loaded": False,
            "decision_count": 0,
            "reviewer": "",
            "organization": "",
            "approval_date": "",
        }
    payload = {}
    if isinstance(review_input, (str, Path)):
        try:
            payload = json.loads(Path(review_input).read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            payload = {}
    elif isinstance(review_input, dict):
        payload = review_input
    review_info = payload.get("reviewer_info", {}) if isinstance(payload, dict) else {}
    return {
        "loaded": bool(decisions),
        "decision_count": len({id(item): item for item in decisions.values()}),
        "reviewer": review_info.get("reviewer", payload.get("reviewer", "") if isinstance(payload, dict) else ""),
        "organization": review_info.get("organization", payload.get("organization", "") if isinstance(payload, dict) else ""),
        "approval_date": review_info.get("approval_date", payload.get("approval_date", "") if isinstance(payload, dict) else ""),
    }


def _effective_summary(results: list[dict]) -> dict[str, int]:
    counts = Counter(result.get("effective_status") or result.get("status", "") for result in results)
    for status in ("PASS", "FAIL", "WARN", "NA", "ERROR", "EXCEPTION"):
        counts.setdefault(status, 0)
    return dict(counts)


def _manual_summary(manual_items: list[dict]) -> dict[str, int]:
    counts = Counter(item.get("effective_status", "PENDING") for item in manual_items)
    for status in ("PASS", "FAIL", "NA", "EXCEPTION", "PENDING"):
        counts.setdefault(status, 0)
    counts["total"] = len(manual_items)
    return dict(counts)


def _review_summary(report: dict) -> dict:
    queue = report.get("review_queue", [])
    states = Counter(item.get("review_state", "Pending") for item in queue)
    return {
        "review_required": len(queue),
        "semi_auto_results": sum(
            1 for r in report.get("results", [])
            if r.get("automation_class") == "semi_auto"
        ),
        "accepted": states.get("Accepted", 0),
        "exceptions": states.get("Exception", 0),
        "rejected": states.get("Rejected", 0),
        "not_applicable": states.get("Not Applicable", 0),
        "pending": sum(1 for item in queue if item.get("review_state") in {"Pending", None}),
    }


def _signoff_summary(report: dict) -> dict:
    generated = Counter(result.get("status", "") for result in report.get("results", []))
    effective = Counter(result.get("effective_status") or result.get("status", "") for result in report.get("results", []))
    semi_queue = report.get("review_queue", [])
    manual_queue = report.get("manual_review_queue", [])
    semi_decisions = Counter(item.get("review_state", "Pending") for item in semi_queue)
    manual_effective = Counter(item.get("effective_status", "PENDING") for item in manual_queue)
    unresolved_semi = sum(1 for item in semi_queue if item.get("review_state") in {"Pending", None})
    unresolved_manual = manual_effective.get("PENDING", 0)
    hard_blockers = effective.get("FAIL", 0) + effective.get("ERROR", 0)
    final_ready = hard_blockers == 0 and unresolved_semi == 0 and unresolved_manual == 0
    return {
        "generated_status": dict(generated),
        "effective_status": dict(effective),
        "semi_auto": {
            "total_review_items": len(semi_queue),
            "accepted": semi_decisions.get("Accepted", 0),
            "exceptions": semi_decisions.get("Exception", 0),
            "rejected": semi_decisions.get("Rejected", 0),
            "not_applicable": semi_decisions.get("Not Applicable", 0),
            "pending": unresolved_semi,
        },
        "manual": {
            "total_review_items": len(manual_queue),
            "accepted": manual_effective.get("PASS", 0),
            "exceptions": manual_effective.get("EXCEPTION", 0),
            "rejected": manual_effective.get("FAIL", 0),
            "not_applicable": manual_effective.get("NA", 0),
            "pending": unresolved_manual,
        },
        "hard_blockers": hard_blockers,
        "final_ready": final_ready,
        "note": (
            "Final IQ assignment is ready only when hard blockers are zero and "
            "all semi-auto and manual review items have documented decisions."
        ),
    }


def _reviewed_level_summary(results: list[dict], max_level: int | None) -> list[dict]:
    rows = []
    score_cap = max_level or 4
    for level in range(1, score_cap + 1):
        level_results = [
            result for result in results
            if result.get("numeric_level") == level
        ]
        if not level_results:
            continue
        counts = Counter(result.get("effective_status") or result.get("status", "") for result in level_results)
        rows.append({
            "iq_level": f"LEVEL {level}",
            "numeric_level": level,
            "result_count": len(level_results),
            "pass": counts.get("PASS", 0),
            "na": counts.get("NA", 0),
            "warn": counts.get("WARN", 0),
            "fail": counts.get("FAIL", 0),
            "error": counts.get("ERROR", 0),
            "exception": counts.get("EXCEPTION", 0),
        })
    return rows


def _score_summary(report: dict) -> dict:
    level_summary = report.get("level_summary") or []
    reviewed_level_summary = report.get("reviewed_level_summary") or []
    implemented_score = _candidate_from_level_rows(level_summary, "failed_items", "error_items")
    reviewed_score = _candidate_from_reviewed_rows(reviewed_level_summary)
    return {
        "final_score": "Not assigned by tool",
        "tool_score": implemented_score,
        "implemented_check_score": implemented_score,
        "reviewed_candidate_score": reviewed_score,
        "first_blocked_level": None,
        "note": (
            "Official IQ score assignment still requires reviewer decisions, "
            "manual-check evidence, accepted-exception documentation, and any "
            "required correlation or exception designators."
        ),
    }


def _candidate_from_level_rows(rows: list[dict], fail_field: str, error_field: str) -> str:
    candidate = 0
    for row in sorted(rows, key=lambda r: r.get("numeric_level") or 99):
        if row.get(fail_field, 0) + row.get(error_field, 0):
            break
        candidate = row.get("numeric_level") or candidate
    return f"IQ{candidate}" if candidate else "Below IQ1"


def _candidate_from_reviewed_rows(rows: list[dict]) -> str:
    candidate = 0
    for row in sorted(rows, key=lambda r: r.get("numeric_level") or 99):
        if row.get("fail", 0) + row.get("error", 0):
            break
        candidate = row.get("numeric_level") or candidate
    return f"IQ{candidate}" if candidate else "Below IQ1"


def make_review_payload(
    report: dict,
    decisions: dict[str, dict] | None = None,
    *,
    reviewer: str = "",
    organization: str = "",
    approval_date: str = "",
) -> dict:
    indexed = decisions or {}
    items = list(report.get("review_queue", [])) + list(report.get("manual_review_queue", []))
    payload_decisions = []
    for item in items:
        existing = decision_for_item(item, indexed) if indexed else None
        normalized = _normalized_decision_payload(existing or {})
        if reviewer and not normalized.get("reviewer"):
            normalized["reviewer"] = reviewer
        if organization and not normalized.get("organization"):
            normalized["organization"] = organization
        if approval_date and not normalized.get("approval_date"):
            normalized["approval_date"] = approval_date
        payload_decisions.append({
            "review_key": item.get("review_key") or item.get("result_key") or item.get("manual_key") or item.get("result_id"),
            "result_id": item.get("result_id", ""),
            "result_key": item.get("result_key", ""),
            "manual_key": item.get("manual_key", ""),
            "item_type": item.get("item_type") or (
                "manual" if item.get("automation_class") == "manual" else "semi_auto"
            ),
            "check_id": item.get("check_id", ""),
            "iq_level": item.get("iq_level", ""),
            "numeric_level": item.get("numeric_level"),
            "scope": item.get("scope", ""),
            "subject": item.get("subject", ""),
            "decision": normalized.get("decision", "Pending"),
            "comment": normalized.get("comment", ""),
            "external_evidence": normalized.get("external_evidence", ""),
            "datasheet_section": normalized.get("datasheet_section", ""),
            "model_maker_action": normalized.get("model_maker_action", ""),
            "reviewer": normalized.get("reviewer", ""),
            "organization": normalized.get("organization", ""),
            "approval_date": normalized.get("approval_date", ""),
            "source_item": item,
        })

    return {
        "schema_version": _DEFAULT_SCHEMA_VERSION,
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "ibis_file": report.get("file", ""),
        "reviewer_info": {
            "reviewer": reviewer,
            "organization": organization,
            "approval_date": approval_date,
        },
        "summary": report.get("summary", {}),
        "review_summary": report.get("review_summary", {}),
        "manual_review_summary": report.get("manual_review_summary", {}),
        "decision_summary": dict(Counter(item["decision"] for item in payload_decisions)),
        "decisions": payload_decisions,
    }


def write_review_payload(payload: dict, path: str | Path) -> Path:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return output


def load_report(path: str | Path) -> dict:
    try:
        return json.loads(Path(path).read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError):
        return {}


def compare_reports(current: dict, previous: dict | str | Path | None) -> dict:
    if not previous:
        return {}
    previous_report = load_report(previous) if isinstance(previous, (str, Path)) else previous
    if not previous_report:
        return {
            "available": False,
            "note": "Previous report could not be loaded.",
        }

    current_index = {_diff_key(result): result for result in current.get("results", [])}
    previous_index = {_diff_key(result): result for result in previous_report.get("results", [])}
    current_keys = set(current_index)
    previous_keys = set(previous_index)

    added = [current_index[key] for key in sorted(current_keys - previous_keys)]
    resolved = [previous_index[key] for key in sorted(previous_keys - current_keys)]
    common = current_keys & previous_keys
    changed = []
    for key in sorted(common):
        old = previous_index[key]
        new = current_index[key]
        old_status = old.get("effective_status") or old.get("status")
        new_status = new.get("effective_status") or new.get("status")
        if old_status != new_status:
            changed.append({
                "key": key,
                "check_id": new.get("check_id"),
                "scope": new.get("scope"),
                "subject": new.get("subject"),
                "previous_status": old_status,
                "current_status": new_status,
                "message": new.get("message") or old.get("message", ""),
            })

    return {
        "available": True,
        "previous_file": previous_report.get("file", ""),
        "current_file": current.get("file", ""),
        "previous_result_count": len(previous_index),
        "current_result_count": len(current_index),
        "added_count": len(added),
        "resolved_count": len(resolved),
        "status_changed_count": len(changed),
        "added": [_diff_item(item) for item in added[:100]],
        "resolved": [_diff_item(item) for item in resolved[:100]],
        "status_changed": changed[:100],
    }


def _diff_key(result: dict) -> str:
    parts = [
        result.get("check_id", ""),
        result.get("scope", ""),
        result.get("component_name", ""),
        result.get("model_name", ""),
        result.get("package_model_name", ""),
        result.get("subject", ""),
        result.get("message", ""),
    ]
    return "|".join(str(part) for part in parts)


def _diff_item(result: dict) -> dict:
    return {
        "check_id": result.get("check_id"),
        "iq_level": result.get("iq_level"),
        "scope": result.get("scope"),
        "subject": result.get("subject"),
        "status": result.get("effective_status") or result.get("status"),
        "message": result.get("message", ""),
    }


def run_cli_review(
    report: dict,
    *,
    existing_decisions: dict[str, dict] | None = None,
    reviewer: str = "",
    organization: str = "",
    approval_date: str = "",
) -> dict:
    decisions = dict(existing_decisions or {})
    items = list(report.get("review_queue", [])) + list(report.get("manual_review_queue", []))
    print(f"Review items: {len(items)}")
    print("Decision keys: [p]ending, [a]ccepted, [e]xception, [r]ejected, [n]ot applicable, [s]kip, [q]uit")
    for index, item in enumerate(items, start=1):
        key = item.get("review_key") or item.get("result_id") or item.get("manual_key")
        current = decision_for_item(item, decisions)
        if current and current.get("decision") not in {"", "Pending"}:
            continue
        print("")
        print(f"[{index}/{len(items)}] {item.get('check_id')} {item.get('iq_level')} {item.get('scope')} {item.get('subject')}")
        print(item.get("message") or item.get("title") or "")
        for detail in (item.get("details") or [])[:3]:
            print(f"  - {detail}")
        choice = input("Decision [p/a/e/r/n/s/q]: ").strip().lower()
        if choice == "q":
            break
        if choice in {"", "s"}:
            continue
        decision = {
            "p": "Pending",
            "a": "Accepted",
            "e": "Exception",
            "r": "Rejected",
            "n": "Not Applicable",
        }.get(choice)
        if not decision:
            print("Unrecognized decision; skipped.")
            continue
        comment = input("Comment: ").strip()
        while decision == "Exception" and not comment:
            print("Exception decisions require a comment.")
            comment = input("Comment: ").strip()
        external_evidence = ""
        datasheet_section = ""
        model_maker_action = ""
        if item.get("automation_class") == "manual" or item.get("item_type") == "manual":
            external_evidence = input("External evidence: ").strip()
            datasheet_section = input("Datasheet / reference section: ").strip()
            model_maker_action = input("Model-maker action: ").strip()
        entry = {
            "review_key": key,
            "result_id": item.get("result_id", ""),
            "result_key": item.get("result_key", ""),
            "manual_key": item.get("manual_key", ""),
            "item_type": item.get("item_type") or (
                "manual" if item.get("automation_class") == "manual" else "semi_auto"
            ),
            "check_id": item.get("check_id", ""),
            "iq_level": item.get("iq_level", ""),
            "numeric_level": item.get("numeric_level"),
            "scope": item.get("scope", ""),
            "subject": item.get("subject", ""),
            "decision": decision,
            "comment": comment,
            "external_evidence": external_evidence,
            "datasheet_section": datasheet_section,
            "model_maker_action": model_maker_action,
            "reviewer": reviewer,
            "organization": organization,
            "approval_date": approval_date,
            "source_item": item,
        }
        for decision_key in _decision_keys(entry):
            decisions[decision_key] = entry
    return make_review_payload(
        report,
        decisions,
        reviewer=reviewer,
        organization=organization,
        approval_date=approval_date,
    )


def _check_sort_key(check_id: str) -> tuple:
    try:
        return tuple(int(part) for part in str(check_id).split("."))
    except ValueError:
        return (999,)
