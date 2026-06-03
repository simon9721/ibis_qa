"""
checks/c5_3_iv_tables.py  —  I-V table AUTO checks
====================================================
5.3.2  [Pullup]      voltage sweep range correct
5.3.3  [Pulldown]    voltage sweep range correct
5.3.4  [POWER Clamp] voltage sweep range correct
5.3.5  [GND Clamp]   voltage sweep range correct
5.3.7  Combined I-V tables monotonic
5.3.8  [Pulldown] passes through 0 at 0V  (CMOS)
5.3.9  [Pullup]   passes through 0 at 0V  (CMOS)
5.3.13 ECL models swept from -Vcc to +2*Vcc
"""

from __future__ import annotations
from typing import Optional, TYPE_CHECKING

from checks.base import CheckModule, CheckResult, Status
from config import (
    IV_RANGE_TOLERANCE, IV_ORDER_ABS_TOL_A, IV_ORDER_REL_TOL,
    MONO_TOLERANCE_A,
    ZERO_CROSS_TOL_A, ZERO_CROSS_EXCEPTIONS, ECL_TYPES,
    OUTPUT_TYPES, INPUT_TYPES
)

if TYPE_CHECKING:
    from parser.ibis_parser import IBISFile, Model, IVTable


class Check5_3_IVSweep(CheckModule):
    """Checks 5.3.1–5.3.5, 5.3.7–5.3.9, 5.3.13"""
    check_ids  = ["5.3.1", "5.3.2", "5.3.3", "5.3.4", "5.3.5",
                  "5.3.7", "5.3.8", "5.3.9", "5.3.13"]
    iq_level   = "LEVEL 2"
    auto_class = "auto"

    def run(self, ibis_file: "IBISFile") -> list[CheckResult]:
        results = []
        for model in ibis_file.models.values():
            results.extend(self._check_model(model))
        return results

    def _check_model(self, model: "Model") -> list[CheckResult]:
        results = []
        mt = model.model_type_lower
        subj = model.name
        vcc = model.resolve_vcc()
        pwr_vcc = model.resolve_power_clamp_vcc()

        # 5.3.1: I-V column order and typ/min/max current ordering
        results.extend(self._check_iv_table_order(subj, model))

        # ── 5.3.2: [Pullup] sweep ────────────────────────────────────────────
        pullup_not_required = mt in INPUT_TYPES or mt in {"open_drain", "open_sink"}
        pulldown_not_required = mt in INPUT_TYPES or mt == "open_source"

        if model.pullup is not None and vcc is not None:
            results.append(self._check_sweep(
                "5.3.2", subj, model.pullup,
                expected_min=-vcc, expected_max=2*vcc,
                label="[Pullup]",
                spec_ref="Quality Spec §5.3.2"))
        elif model.pullup is None and pullup_not_required:
            results.append(self._na("5.3.2", subj,
                f"Model_type={model.model_type} has no required [Pullup] table - NA",
                spec_ref="Quality Spec §5.3.2"))

        # ── 5.3.3: [Pulldown] sweep ───────────────────────────────────────────
        if model.pulldown is not None and vcc is not None:
            results.append(self._check_sweep(
                "5.3.3", subj, model.pulldown,
                expected_min=-vcc, expected_max=2*vcc,
                label="[Pulldown]",
                spec_ref="Quality Spec §5.3.3"))
        elif model.pulldown is None and pulldown_not_required:
            results.append(self._na("5.3.3", subj,
                f"Model_type={model.model_type} has no required [Pulldown] table - NA",
                spec_ref="Quality Spec §5.3.3"))

        # ── 5.3.4: [POWER Clamp] sweep ───────────────────────────────────────
        if model.power_clamp is not None and pwr_vcc is not None:
            results.append(self._check_sweep(
                "5.3.4", subj, model.power_clamp,
                expected_min=-pwr_vcc, expected_max=2*pwr_vcc,
                label="[POWER Clamp]",
                spec_ref="Quality Spec §5.3.4"))

        # ── 5.3.5: [GND Clamp] sweep ─────────────────────────────────────────
        if model.gnd_clamp is not None and pwr_vcc is not None:
            results.append(self._check_sweep(
                "5.3.5", subj, model.gnd_clamp,
                expected_min=-pwr_vcc, expected_max=2*pwr_vcc,
                label="[GND Clamp]",
                spec_ref="Quality Spec §5.3.5"))

        # ── 5.3.7: Monotonicity ───────────────────────────────────────────────
        if model.pulldown is not None or model.gnd_clamp is not None:
            results.extend(self._check_monotonicity(subj, model))

        # ── 5.3.8: [Pulldown] zero crossing ──────────────────────────────────
        if model.pulldown is not None:
            results.append(self._check_zero_crossing(
                "5.3.8", subj, model.pulldown, model,
                vcc_relative=False, label="[Pulldown]",
                spec_ref="Quality Spec §5.3.8"))
        elif pulldown_not_required:
            results.append(self._na("5.3.8", subj,
                f"Model_type={model.model_type} has no required [Pulldown] table - NA",
                spec_ref="Quality Spec §5.3.8"))

        # ── 5.3.9: [Pullup] zero crossing ────────────────────────────────────
        if model.pullup is not None:
            results.append(self._check_zero_crossing(
                "5.3.9", subj, model.pullup, model,
                vcc_relative=True, label="[Pullup]",
                spec_ref="Quality Spec §5.3.9"))
        elif pullup_not_required:
            results.append(self._na("5.3.9", subj,
                f"Model_type={model.model_type} has no required [Pullup] table - NA",
                spec_ref="Quality Spec §5.3.9"))

        # ── 5.3.13: ECL sweep ─────────────────────────────────────────────────
        if mt in ECL_TYPES:
            results.extend(self._check_ecl_sweep(subj, model))
        else:
            # Only emit NA if the model has I-V tables (otherwise too noisy)
            pass

        return results

    def _check_iv_table_order(self, subj: str, model: "Model") -> list[CheckResult]:
        results = []
        tables = {
            "[Pulldown]": model.pulldown,
            "[Pullup]": model.pullup,
            "[GND Clamp]": model.gnd_clamp,
            "[POWER Clamp]": model.power_clamp,
        }

        for label, table in tables.items():
            if table is None:
                continue
            if not table.rows:
                results.append(self._error("5.3.1", subj,
                    f"{label}: table is empty",
                    spec_ref="Quality Spec §5.3.1"))
                continue

            malformed = []
            ordering_issues = []
            for row_index, row in enumerate(table.rows, start=1):
                if len(row) < 4 or any(value is None for value in row[:4]):
                    malformed.append(f"Row {row_index}: expected voltage typ min max")
                    continue

                if label not in ("[Pulldown]", "[Pullup]"):
                    continue

                voltage, typ, min_current, max_current = row[:4]
                vcc = model.resolve_vcc()
                if vcc is None or not (0.0 < voltage < vcc):
                    continue

                min_abs = abs(min_current)
                typ_abs = abs(typ)
                max_abs = abs(max_current)
                peak = max(min_abs, typ_abs, max_abs)
                tolerance = max(IV_ORDER_ABS_TOL_A, peak * IV_ORDER_REL_TOL)
                nearly_overlay = max(min_abs, typ_abs, max_abs) - min(min_abs, typ_abs, max_abs) <= tolerance
                if nearly_overlay:
                    continue

                if typ_abs + tolerance < min_abs or max_abs + tolerance < typ_abs:
                    ordering_issues.append(
                        f"Row {row_index} V={voltage:.4g}: "
                        f"|min|={min_abs:.4g}A, |typ|={typ_abs:.4g}A, "
                        f"|max|={max_abs:.4g}A")

            if malformed:
                results.append(self._fail("5.3.1", subj,
                    f"{label} row format is not voltage/typ/min/max",
                    details=malformed[:10],
                    spec_ref="Quality Spec §5.3.1"))
            elif ordering_issues and label == "[POWER Clamp]":
                results.append(self._warn("5.3.1", subj,
                    f"{label} typ/min/max ordering has clamp-region crossover(s)",
                    details=ordering_issues[:10],
                    spec_ref="Quality Spec §5.3.1"))
            elif ordering_issues:
                results.append(self._fail("5.3.1", subj,
                    f"{label} typ/min/max current ordering violated",
                    details=ordering_issues[:10],
                    spec_ref="Quality Spec §5.3.1"))
            else:
                if label in ("[Pulldown]", "[Pullup]"):
                    msg = f"{label} rows are voltage/typ/min/max with expected active-region corner ordering"
                else:
                    msg = f"{label} rows are voltage/typ/min/max"
                results.append(self._pass("5.3.1", subj,
                    msg,
                    spec_ref="Quality Spec §5.3.1"))

        return results

    # ── Sweep range helper ────────────────────────────────────────────────────

    def _check_sweep(self, check_id: str, subj: str, table: "IVTable",
                     expected_min: float, expected_max: float,
                     label: str, required_max: bool = True,
                     spec_ref: str = "") -> CheckResult:
        if not table.rows:
            return self._error(check_id, subj,
                f"{label}: table is empty", spec_ref=spec_ref)
        vs = table.voltages()
        actual_min, actual_max = min(vs), max(vs)
        tol = abs(expected_max - expected_min) * IV_RANGE_TOLERANCE
        issues = []
        if actual_min > expected_min + tol:
            issues.append(
                f"Low end: table starts at {actual_min:.4g}V, "
                f"need ≤ {expected_min:.4g}V")
        if required_max and actual_max < expected_max - tol:
            issues.append(
                f"High end: table ends at {actual_max:.4g}V, "
                f"need ≥ {expected_max:.4g}V")
        if issues:
            return self._fail(check_id, subj,
                f"{label} voltage sweep insufficient", details=issues,
                spec_ref=spec_ref)
        return self._pass(check_id, subj,
            f"{label} voltage sweep OK "
            f"({actual_min:.3g}V to {actual_max:.3g}V)",
            spec_ref=spec_ref)

    # ── Monotonicity ──────────────────────────────────────────────────────────

    # ── Zero-crossing ─────────────────────────────────────────────────────────

    def _check_monotonicity(self, subj: str,
                             model: "Model") -> list[CheckResult]:
        """
        Combine [Pulldown]+[GND Clamp] and [Pullup]+[POWER Clamp], then
        check monotonicity of each combined current curve.
        """
        results = []
        groups = [
            ("[Pulldown] + [GND Clamp]", [model.pulldown, model.gnd_clamp], "nondecreasing"),
            ("[Pullup] + [POWER Clamp]", [model.pullup, model.power_clamp], "nonincreasing"),
        ]
        for label, tables, direction in groups:
            present = [table for table in tables if table is not None and len(table.rows) >= 2]
            if not present:
                continue
            points = self._combined_curve_points(present)
            if len(points) < 2:
                results.append(self._error("5.3.7", subj,
                    f"{label}: insufficient combined I-V data for monotonicity",
                    spec_ref="Quality Spec §5.3.7"))
                continue
            violations = self._monotonicity_violations(points, direction)
            if violations:
                results.append(self._fail("5.3.7", subj,
                    f"{label} combined curve non-monotonic ({len(violations)} violation(s))",
                    details=violations[:10],
                    spec_ref="Quality Spec §5.3.7"))
            else:
                results.append(self._pass("5.3.7", subj,
                    f"{label} combined curve monotonicity OK ({direction}, {len(points)} sample point(s))",
                    spec_ref="Quality Spec §5.3.7"))
        return results

    def _combined_curve_points(self, tables: list["IVTable"]) -> list[tuple[float, float]]:
        voltages = sorted({
            row[0]
            for table in tables
            for row in table.rows
            if row and row[0] is not None
        })
        points = []
        for voltage in voltages:
            current = 0.0
            used = False
            for table in tables:
                value = table.interpolate(voltage, col=1)
                if value is None:
                    continue
                current += value
                used = True
            if used:
                points.append((voltage, current))
        return points

    def _monotonicity_violations(
            self,
            points: list[tuple[float, float]],
            direction: str) -> list[str]:
        violations = []
        for (v1, i1), (v2, i2) in zip(points, points[1:]):
            if direction == "nonincreasing":
                bad = v2 > v1 and i2 > i1 + MONO_TOLERANCE_A
                wording = "increases"
            else:
                bad = v2 > v1 and i2 < i1 - MONO_TOLERANCE_A
                wording = "decreases"
            if bad:
                violations.append(
                    f"V={v2:.4g}: combined current {wording} from {i1*1000:.4g}mA "
                    f"to {i2*1000:.4g}mA")
        return violations

    def _check_zero_crossing(self, check_id: str, subj: str,
                              table: "IVTable", model: "Model",
                              vcc_relative: bool, label: str,
                              spec_ref: str) -> CheckResult:
        mt = model.model_type_lower
        # Technology exceptions — mark NA
        if any(exc in mt for exc in ZERO_CROSS_EXCEPTIONS):
            return self._na(check_id, subj,
                f"Technology exception ({model.model_type}) — zero-crossing NA",
                spec_ref=spec_ref)
        target_v = 0.0  # 0V in table (Pulldown: absolute; Pullup: Vcc-relative)
        review_issues = []
        for col in (1, 2, 3):  # typ, min, max
            val = table.interpolate(target_v, col)
            if val is None:
                continue
            if abs(val) > ZERO_CROSS_TOL_A:
                issue = (
                    f"col {col}: {val*1e6:.2f}uA, pass limit +/-{ZERO_CROSS_TOL_A*1e6:.0f}uA"
                )
                review_issues.append(issue)
        if review_issues:
            return self._warn(check_id, subj,
                f"{label} zero-current condition at 0V needs review",
                details=review_issues,
                spec_ref=spec_ref,
                automation_class="semi_auto",
                review_required=True)
        return self._pass(check_id, subj,
            f"{label} passes through near 0 at 0V (within +/-{ZERO_CROSS_TOL_A*1e6:.0f}uA)",
            spec_ref=spec_ref)

    # ── ECL sweep ─────────────────────────────────────────────────────────────

    def _check_ecl_sweep(self, subj: str,
                          model: "Model") -> list[CheckResult]:
        results = []
        # Effective Vcc = (most positive supply) - (most negative supply)
        pos_vcc = model.pullup_ref[0] if model.pullup_ref[0] else model.voltage_range[0]
        neg_vcc = model.pulldown_ref[0] if model.pulldown_ref[0] else 0.0
        if pos_vcc is None:
            results.append(self._error("5.3.13", subj,
                "Cannot determine ECL supply range — missing reference voltages"))
            return results
        eff_vcc = (pos_vcc or 0.0) - (neg_vcc or 0.0)
        for label, table in [('[Pulldown]', model.pulldown),
                              ('[Pullup]', model.pullup)]:
            if table is None:
                continue
            results.append(self._check_sweep(
                "5.3.13", subj, table,
                expected_min=-eff_vcc, expected_max=2*eff_vcc,
                label=f"ECL {label}",
                spec_ref="Quality Spec §5.3.13"))
        return results
