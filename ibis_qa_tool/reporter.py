"""
reporter.py  —  Format CheckResult lists into text or JSON reports
===================================================================
"""

from __future__ import annotations
import json
from collections import Counter
from typing import TYPE_CHECKING

from checks.base import CheckResult, Status

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


class Reporter:
    def __init__(self, results: list[CheckResult],
                 ibis_file: "IBISFile", verbose: bool = False):
        self.results   = results
        self.ibis_file = ibis_file
        self.verbose   = verbose

    # ── Text report ───────────────────────────────────────────────────────────

    def as_text(self) -> str:
        lines = []
        f = self.ibis_file

        lines.append("=" * 72)
        lines.append(f"IBIS QA Report — AUTO Checks and SEMI-AUTO Evidence")
        lines.append(f"File   : {f.path}")
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
        return {
            "file": str(f.path),
            "ibis_ver": f.ibis_ver,
            "file_rev": f.file_rev,
            "iq_score_in_file": f.iq_score_in_file,
            "header": self._header_dict(),
            "components": self._components_dict(scoped_results),
            "models": self._models_dict(scoped_results),
            "package_models": self._package_models_dict(scoped_results),
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
        }

    def as_json(self) -> str:
        return json.dumps(self.as_dict(), indent=2)

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
        return {
            "result_id": f"R{result_index:05d}",
            "check_id": r.check_id,
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

    def _models_dict(self, scoped_results: list[dict]) -> dict:
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
                "results": [
                    r for r in scoped_results
                    if r["scope"] == "model"
                    and r["model_name"] == name
                ],
            }
        return out

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
