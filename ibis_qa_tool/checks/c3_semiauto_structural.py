"""Semi-auto structural evidence for pin completeness and pin mapping."""

from __future__ import annotations
from typing import TYPE_CHECKING

from checks.base import CheckModule, CheckResult

if TYPE_CHECKING:
    from parser.ibis_parser import IBISFile


class Check3SemiAutoStructural(CheckModule):
    check_ids = ["3.2.1", "3.4.2", "4.1"]
    iq_level = "LEVEL 2/4"
    auto_class = "semi_auto"

    def run(self, ibis_file: "IBISFile") -> list[CheckResult]:
        results = []
        for comp in ibis_file.components:
            results.append(self._check_pin_completeness(ibis_file, comp))
            results.append(self._check_pin_mapping_rails(comp))
        results.extend(self._check_model_selector_descriptions(ibis_file))
        return results

    def _pass_sa(self, check_id: str, subject: str, msg: str, **kw) -> CheckResult:
        kw.setdefault("automation_class", "semi_auto")
        kw.setdefault("review_required", False)
        return self._pass(check_id, subject, msg, **kw)

    def _warn_sa(self, check_id: str, subject: str, msg: str, **kw) -> CheckResult:
        kw.setdefault("automation_class", "semi_auto")
        kw.setdefault("review_required", True)
        return self._warn(check_id, subject, msg, **kw)

    def _na_sa(self, check_id: str, subject: str, msg: str, **kw) -> CheckResult:
        kw.setdefault("automation_class", "semi_auto")
        kw.setdefault("review_required", False)
        return self._na(check_id, subject, msg, **kw)

    def _check_pin_completeness(self, ibis_file: "IBISFile", comp) -> CheckResult:
        if not comp.pins:
            return self._warn_sa("3.2.1", comp.name,
                "[Pin] section is missing or empty",
                spec_ref="Quality Spec §3.2.1")
        reserved = {"power", "gnd", "nc", "circuitcall"}
        selector_names = {name for name, _ in self._extract_model_selectors(ibis_file)}
        issues = []
        for pin in comp.pins:
            if not pin.pin_name or not pin.signal_name or not pin.model_name:
                issues.append(f"Pin {pin.pin_name or '(blank)'}: missing pin/signal/model field")
            elif (pin.model_name.lower() not in reserved
                  and pin.model_name not in ibis_file.models
                  and pin.model_name not in selector_names):
                issues.append(f"Pin {pin.pin_name}: model '{pin.model_name}' not found in [Model] sections")
        if issues:
            return self._warn_sa("3.2.1", comp.name,
                f"{len(issues)} [Pin] completeness item(s) need review",
                details=issues[:20],
                spec_ref="Quality Spec §3.2.1")
        return self._pass_sa("3.2.1", comp.name,
            f"[Pin] has {len(comp.pins)} complete entry/entries with resolvable model references",
            spec_ref="Quality Spec §3.2.1")

    def _check_pin_mapping_rails(self, comp) -> CheckResult:
        rail_pins = [
            pin.pin_name for pin in comp.pins
            if pin.model_name.lower() in ("power", "gnd")
        ]
        if not rail_pins:
            return self._na_sa("3.4.2", comp.name,
                "No POWER/GND pins parsed for this component",
                spec_ref="Quality Spec §3.4.2")
        if not comp.pin_mapping:
            return self._warn_sa("3.4.2", comp.name,
                "[Pin Mapping] absent; POWER/GND rail coverage needs review",
                spec_ref="Quality Spec §3.4.2")
        mapped = {entry.pin_name for entry in comp.pin_mapping}
        missing = [pin for pin in rail_pins if pin not in mapped]
        if missing:
            return self._warn_sa("3.4.2", comp.name,
                "Pin-mapping POWER/GND rail evidence needs review",
                details=["POWER/GND pins missing from [Pin Mapping]: " + ", ".join(missing[:20])],
                spec_ref="Quality Spec §3.4.2")
        return self._pass_sa("3.4.2", comp.name,
            "POWER/GND pins are represented in [Pin Mapping] evidence",
            spec_ref="Quality Spec §3.4.2")

    def _check_model_selector_descriptions(self, ibis_file: "IBISFile") -> list[CheckResult]:
        selectors = self._extract_model_selectors(ibis_file)
        if not selectors:
            return [self._na_sa("4.1", ibis_file.file_name,
                "No [Model Selector] sections parsed from raw file",
                spec_ref="Quality Spec §4.1")]
        results = []
        weak_words = {"", "na", "n/a", "none", "default", "model"}
        for selector_name, rows in selectors:
            issues = []
            for model_name, description in rows:
                desc = description.strip()
                if desc.lower() in weak_words or len(desc) < 4:
                    issues.append(f"{model_name}: weak or missing description")
            if issues:
                results.append(self._warn_sa("4.1", ibis_file.file_name,
                    f"[Model Selector] {selector_name} description evidence needs review",
                    details=issues[:20],
                    spec_ref="Quality Spec §4.1"))
            else:
                results.append(self._pass_sa("4.1", ibis_file.file_name,
                    f"[Model Selector] {selector_name} has descriptions for {len(rows)} entry/entries",
                    spec_ref="Quality Spec §4.1"))
        return results

    def _extract_model_selectors(self, ibis_file: "IBISFile") -> list[tuple[str, list[tuple[str, str]]]]:
        selectors = []
        current_name = None
        current_rows = []
        in_selector = False
        for raw in ibis_file.raw_lines:
            line = raw.strip()
            lower = line.lower()
            if lower.startswith("[model selector]"):
                if current_name is not None:
                    selectors.append((current_name, current_rows))
                parts = line.split("]", 1)
                current_name = parts[1].strip() if len(parts) > 1 else "(unnamed)"
                current_rows = []
                in_selector = True
                continue
            if in_selector and line.startswith("["):
                selectors.append((current_name or "(unnamed)", current_rows))
                current_name = None
                current_rows = []
                in_selector = False
            if not in_selector or not line or line.startswith("|"):
                continue
            toks = line.split(None, 1)
            if toks:
                current_rows.append((toks[0], toks[1] if len(toks) > 1 else ""))
        if in_selector and current_name is not None:
            selectors.append((current_name, current_rows))
        return selectors
