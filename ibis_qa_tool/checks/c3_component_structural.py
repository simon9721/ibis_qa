"""
checks/c3_component_structural.py  —  Component structural checks
==================================================================
3.2.2  AUTO: [Pin] RLC values present and reasonable
3.3.1  AUTO: [Diff Pin] model names match (or comment present)
3.3.2  AUTO: [Diff Pin] Vdiff/Tdelay rules per model type
3.4.1  AUTO: [Pin Mapping] present for each component
3.4.3  AUTO: [Merged Pins] required when package model merges pins
"""

from __future__ import annotations
import math
from typing import TYPE_CHECKING

from checks.base import CheckModule, CheckResult, Status
from config import PIN_TD_MAX_S, PIN_Z0_MAX_OHM

if TYPE_CHECKING:
    from parser.ibis_parser import IBISFile
    from parser.ibis_parser import Component, DiffPinEntry


class Check3_2_2_PinRLC(CheckModule):
    check_ids  = ["3.2.2"]
    iq_level   = "LEVEL 3"
    auto_class = "auto"

    def run(self, ibis_file: "IBISFile") -> list[CheckResult]:
        results = []
        RESERVED = {'power', 'gnd', 'nc', 'circuitcall'}
        # model types that may lack per-pin RLC (covered by package model)
        has_pkg_model = {comp.name: comp.pkg_model_ref
                         for comp in ibis_file.components}

        for comp in ibis_file.components:
            subj = comp.name
            if comp.is_bare_die:
                results.append(self._na("3.2.2", subj,
                    "Bare-die component - per-pin package RLC completeness is not required",
                    spec_ref="Quality Spec §3.2.2"))
                continue

            issues = []
            for pin in comp.pins:
                if pin.model_name.lower() in RESERVED:
                    continue
                # Must have RLC OR component has a [Package Model] reference
                has_rlc = (pin.l_pin is not None and pin.c_pin is not None)
                if not has_rlc:
                    if comp.pkg_model_ref:
                        continue  # covered by package model — NA
                    issues.append(f"Pin {pin.pin_name}: missing L/C values")
                    continue
                # TD and Z0 checks
                L, C = pin.l_pin, pin.c_pin
                if L > 0 and C > 0:
                    td = math.sqrt(L * C)
                    z0 = math.sqrt(L / C)
                    if td > PIN_TD_MAX_S:
                        issues.append(
                            f"Pin {pin.pin_name}: TD={td*1e12:.1f}ps > {PIN_TD_MAX_S*1e12:.0f}ps limit")
                    if z0 > PIN_Z0_MAX_OHM:
                        issues.append(
                            f"Pin {pin.pin_name}: Z0={z0:.1f}Ω > {PIN_Z0_MAX_OHM:.0f}Ω limit")

            if issues:
                results.append(self._fail("3.2.2", subj,
                    f"{len(issues)} pin RLC issue(s)",
                    details=issues[:10],   # cap at 10 for readability
                    spec_ref="Quality Spec §3.2.2"))
            else:
                results.append(self._pass("3.2.2", subj,
                    "All signal pin RLC values present and within TD/Z0 limits",
                    spec_ref="Quality Spec §3.2.2"))
        return results


class Check3_3_DiffPin(CheckModule):
    check_ids  = ["3.3.1", "3.3.2"]
    iq_level   = "LEVEL 2"
    auto_class = "auto"

    def run(self, ibis_file: "IBISFile") -> list[CheckResult]:
        results = []
        for comp in ibis_file.components:
            subj = comp.name
            if not comp.diff_pins:
                # No [Diff Pin] section — NA for this component
                results.append(self._na("3.3.1", subj,
                    "No [Diff Pin] section — check NA",
                    spec_ref="Quality Spec §3.3.1"))
                results.append(self._na("3.3.2", subj,
                    "No [Diff Pin] section — check NA",
                    spec_ref="Quality Spec §3.3.2"))
                continue

            # Build a pin→model_name lookup from [Pin] section
            pin_model = {p.pin_name: p.model_name for p in comp.pins}

            # ── 3.3.1: model names match ──────────────────────────────────────
            mismatch_issues = []
            for dp in comp.diff_pins:
                m1 = pin_model.get(dp.pin_name, "")
                m2 = pin_model.get(dp.inv_pin, "")
                if m1 and m2 and m1 != m2:
                    # Check if a comment/notes entry explains this
                    # We look in raw_lines for a comment near [Diff_pin]
                    has_explanation = self._has_diff_pin_comment(
                        ibis_file, dp.pin_name, dp.inv_pin)
                    if not has_explanation:
                        mismatch_issues.append(
                            f"Pins {dp.pin_name}/{dp.inv_pin}: "
                            f"model {m1} ≠ {m2}, no explanatory comment found")

            if mismatch_issues:
                results.append(self._fail("3.3.1", subj,
                    f"{len(mismatch_issues)} diff pin model mismatch(es) without explanation",
                    details=mismatch_issues, spec_ref="Quality Spec §3.3.1"))
            else:
                results.append(self._pass("3.3.1", subj,
                    "All [Diff Pin] model names match or have explanatory comments",
                    spec_ref="Quality Spec §3.3.1"))

            # ── 3.3.2: Vdiff / Tdelay rules ──────────────────────────────────
            rule_issues = []
            review_issues = []
            for dp in comp.diff_pins:
                model = ibis_file.models.get(pin_model.get(dp.pin_name, ""))
                if not model:
                    continue
                mt = model.model_type_lower
                is_input  = 'input' in mt and 'output' not in mt
                is_output = 'output' in mt and 'input' not in mt
                is_io     = 'i/o' in mt

                if is_input:
                    if dp.vdiff is None:
                        rule_issues.append(f"Pin {dp.pin_name}: Input — Vdiff must be defined")
                    elif dp.vdiff <= 0:
                        rule_issues.append(f"Pin {dp.pin_name}: Input — Vdiff must be positive")
                    if dp.tdelay_typ is not None and dp.tdelay_typ != 0:
                        review_issues.append(
                            f"Pin {dp.pin_name}: Input Tdelay is nonzero; confirm intent")

                elif is_output:
                    if dp.vdiff is not None:
                        rule_issues.append(f"Pin {dp.pin_name}: Output — Vdiff must be NA")
                    if dp.tdelay_typ is None:
                        rule_issues.append(f"Pin {dp.pin_name}: Output — Tdelay_typ must be defined")

                elif is_io:
                    if dp.vdiff is None or dp.vdiff <= 0:
                        rule_issues.append(f"Pin {dp.pin_name}: I/O — Vdiff must be defined and positive")
                    if dp.tdelay_typ is None:
                        rule_issues.append(f"Pin {dp.pin_name}: I/O — Tdelay_typ must be defined")

            if rule_issues:
                results.append(self._fail("3.3.2", subj,
                    f"{len(rule_issues)} Vdiff/Tdelay rule violation(s)",
                    details=rule_issues, spec_ref="Quality Spec §3.3.2"))
            elif review_issues:
                results.append(self._warn("3.3.2", subj,
                    f"{len(review_issues)} input Tdelay item(s) need review",
                    details=review_issues,
                    spec_ref="Quality Spec §3.3.2",
                    automation_class="semi_auto",
                    review_required=True))
            else:
                results.append(self._pass("3.3.2", subj,
                    "All [Diff Pin] Vdiff/Tdelay values consistent with model type",
                    spec_ref="Quality Spec §3.3.2"))

        return results

    def _has_diff_pin_comment(self, ibis_file: "IBISFile",
                              pin_a: str, pin_b: str) -> bool:
        """Check raw lines near [Diff_pin] for an explanatory comment."""
        in_diff_section = False
        for line in ibis_file.raw_lines:
            ls = line.strip()
            if '[diff_pin]' in ls.lower() or '[diff pin]' in ls.lower():
                in_diff_section = True
            if in_diff_section and ls.startswith('|'):
                if pin_a in ls or pin_b in ls:
                    return True
            if in_diff_section and ls.startswith('[') and 'diff' not in ls.lower():
                break
        return False


class Check3_4_PinMapping(CheckModule):
    check_ids  = ["3.4.1"]
    iq_level   = "LEVEL 4"
    auto_class = "auto"

    def run(self, ibis_file: "IBISFile") -> list[CheckResult]:
        results = []
        ibis_ver = self._parse_ver(ibis_file.ibis_ver)

        for comp in ibis_file.components:
            subj = comp.name

            # Bare-die: NA
            if comp.is_bare_die:
                results.append(self._na("3.4.1", subj,
                    "Bare-die component — [Pin Mapping] not required, NA",
                    spec_ref="Quality Spec §3.4.1"))
                continue

            # Check [Pin Mapping] presence
            if not comp.pin_mapping:
                results.append(self._fail("3.4.1", subj,
                    "[Pin Mapping] section missing",
                    spec_ref="Quality Spec §3.4.1"))
                continue

            # Check all non-POWER/GND/NC pins are covered
            pm_pins = {e.pin_name for e in comp.pin_mapping}
            RESERVED = {'power', 'gnd', 'nc', 'circuitcall'}
            missing = [
                p.pin_name for p in comp.pins
                if p.model_name.lower() not in RESERVED
                and p.pin_name not in pm_pins
            ]

            # For IBIS ver < 7.0: POWER/GND pins must also be in [Pin Mapping]
            if ibis_ver < 7.0:
                pwr_gnd_missing = [
                    p.pin_name for p in comp.pins
                    if p.model_name.lower() in ('power', 'gnd')
                    and p.pin_name not in pm_pins
                ]
                missing += pwr_gnd_missing

            if missing:
                results.append(self._fail("3.4.1", subj,
                    f"{len(missing)} pin(s) not covered in [Pin Mapping]",
                    details=missing[:20],
                    spec_ref="Quality Spec §3.4.1"))
            else:
                results.append(self._pass("3.4.1", subj,
                    "[Pin Mapping] present and covers all required pins",
                    spec_ref="Quality Spec §3.4.1"))

        return results

    def _parse_ver(self, ver_str: str) -> float:
        try:
            return float(ver_str)
        except (ValueError, TypeError):
            return 5.0


class Check3_4_3_MergedPins(CheckModule):
    check_ids  = ["3.4.3"]
    iq_level   = "LEVEL 4"
    auto_class = "auto"

    def run(self, ibis_file: "IBISFile") -> list[CheckResult]:
        results = []

        if not ibis_file.pkg_models:
            results.append(self._na("3.4.3", ibis_file.file_name,
                "No [Define Package Model] sections found — check NA",
                spec_ref="Quality Spec §3.4.3"))
            return results

        for pkg_name, pkgm in ibis_file.pkg_models.items():
            subj = pkg_name
            from collections import Counter
            node_counts = Counter(node for node, _ in pkgm.pin_numbers)
            merged_nodes = {k: v for k, v in node_counts.items() if v > 1}

            if merged_nodes:
                # [Merged Pins] keyword must be present
                if pkgm.has_merged_pins:
                    results.append(self._pass("3.4.3", subj,
                        f"Merged pins detected ({len(merged_nodes)} node(s)) "
                        f"and [Merged Pins] keyword is present",
                        spec_ref="Quality Spec §3.4.3"))
                else:
                    details = [f"Node '{n}': {c} physical pins merged"
                               for n, c in merged_nodes.items()]
                    results.append(self._fail("3.4.3", subj,
                        f"[Pin Numbers] has {len(merged_nodes)} merged node(s) "
                        f"but [Merged Pins] keyword is absent",
                        details=details,
                        spec_ref="Quality Spec §3.4.3"))
            else:
                results.append(self._pass("3.4.3", subj,
                    "No merged pins in [Define Package Model] — "
                    "[Merged Pins] not required",
                    spec_ref="Quality Spec §3.4.3"))

        return results
