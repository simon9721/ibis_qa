"""
checks/c5_ramp_waveform.py  —  Ramp and Composite Current AUTO checks
=======================================================================
5.5.1  [Ramp] R_load present if not 50Ω
5.5.3  [Ramp] dV consistent with I-V load-line
5.8.1  [Composite Current] present under each waveform
5.8.2  [Composite Current] time range matches V-T
5.8.8  [Composite Current] zero endpoint when V_fixture=0
"""

from __future__ import annotations
from typing import Optional, TYPE_CHECKING

from checks.base import CheckModule, CheckResult, Status
from config import RAMP_DV_TOLERANCE, RAMP_DV_FRACTION, CC_ZERO_TOL_A, TIME_MATCH_TOL_S

if TYPE_CHECKING:
    from parser.ibis_parser import IBISFile, Model, IVTable, Waveform


class Check5_5_Ramp(CheckModule):
    check_ids  = ["5.5.1", "5.5.3"]
    iq_level   = "LEVEL 2"
    auto_class = "auto"

    def run(self, ibis_file: "IBISFile") -> list[CheckResult]:
        results = []
        for model in ibis_file.models.values():
            if model.ramp is None:
                continue
            subj = model.name
            ramp = model.ramp
            DEFAULT_RLOAD = 50.0

            # ── 5.5.1: R_load present if not default ─────────────────────────
            r_load = ramp.r_load if ramp.r_load is not None else DEFAULT_RLOAD
            if ramp.r_load is None:
                # No R_load — default 50Ω assumed, always OK
                results.append(self._pass("5.5.1", subj,
                    "R_load absent — 50Ω default assumed",
                    spec_ref="Quality Spec §5.5.1"))
            else:
                results.append(self._pass("5.5.1", subj,
                    f"R_load = {ramp.r_load:.1f}Ω documented",
                    spec_ref="Quality Spec §5.5.1"))

            # ── 5.5.3: dV vs I-V load-line ───────────────────────────────────
            vcc = model.resolve_vcc()
            if vcc is None:
                results.append(self._error("5.5.3", subj,
                    "Cannot resolve Vcc — skipping dV consistency check",
                    spec_ref="Quality Spec §5.5.3"))
                continue

            v_fixture_rise = 0.0    # rising waveform: V_fixture = GND = 0V
            v_fixture_fall = vcc    # falling waveform: V_fixture = Vcc

            # For rising: output transitions from 0 toward Vcc into R_load to GND
            # Vhigh = load-line intersection of Pullup vs R_load to V_fixture=0
            # Vlow  = load-line intersection of Pulldown vs R_load to V_fixture=0
            v_high = self._loadline_voltage(model.pullup, r_load, v_fixture_rise, vcc, vcc_relative=True)
            v_low  = self._loadline_voltage(model.pulldown, r_load, v_fixture_rise, 0.0, vcc_relative=False)

            if v_high is None or v_low is None:
                results.append(self._warn("5.5.3", subj,
                    "Could not compute load-line intersection for dV check "
                    "(missing [Pullup] or [Pulldown] table)",
                    spec_ref="Quality Spec §5.5.3"))
                continue

            expected_dv = RAMP_DV_FRACTION * (v_high - v_low)

            issues = []
            for corner_idx, corner_name in enumerate(['typ', 'min', 'max']):
                ramp_dv = ramp.dv_r[corner_idx] if ramp.dv_r[corner_idx] is not None else None
                if ramp_dv is None:
                    continue
                if expected_dv > 0:
                    err = abs(ramp_dv - expected_dv) / expected_dv
                    if err > RAMP_DV_TOLERANCE:
                        issues.append(
                            f"Rise dV/{corner_name}: ramp={ramp_dv:.4g}V, "
                            f"expected≈{expected_dv:.4g}V ({err*100:.1f}% error)")

            if issues:
                results.append(self._fail("5.5.3", subj,
                    f"[Ramp] dV inconsistent with I-V load-line ({len(issues)} corner(s))",
                    details=issues, spec_ref="Quality Spec §5.5.3"))
            else:
                results.append(self._pass("5.5.3", subj,
                    f"[Ramp] dV consistent with I-V load-line "
                    f"(Vhigh={v_high:.3f}V, Vlow={v_low:.3f}V, "
                    f"60%·ΔV≈{expected_dv:.3f}V)",
                    spec_ref="Quality Spec §5.5.3"))

        return results

    def _loadline_voltage(self, table: Optional["IVTable"],
                          r_load: float, v_fixture: float,
                          v_ref: float, vcc_relative: bool) -> Optional[float]:
        """
        Find the DC output voltage where the device I-V curve intersects
        the resistive load line: I_load = (V - V_fixture) / R_load

        For Vcc-relative tables (Pullup): Vtable = Vcc - Vout
        Returns Vout at intersection.
        """
        if table is None or not table.rows:
            return None
        # Sample the load line and device curve over a voltage range
        # Use the table's voltage range
        vs = table.voltages()
        if not vs:
            return None

        for i in range(len(table.rows) - 1):
            v_tab_a = table.rows[i][0]
            v_tab_b = table.rows[i + 1][0]
            i_dev_a = table.rows[i][1]    # typ column
            i_dev_b = table.rows[i + 1][1]
            if i_dev_a is None or i_dev_b is None:
                continue

            # Convert table voltage to output voltage
            if vcc_relative:
                # Vout = Vcc - Vtable  (but we don't know Vcc here — use v_ref)
                vout_a = v_ref - v_tab_a
                vout_b = v_ref - v_tab_b
            else:
                vout_a = v_tab_a
                vout_b = v_tab_b

            i_load_a = (vout_a - v_fixture) / r_load
            i_load_b = (vout_b - v_fixture) / r_load

            # Check for sign change between device current and load current
            diff_a = i_dev_a - i_load_a
            diff_b = i_dev_b - i_load_b
            if diff_a * diff_b <= 0:  # sign change — intersection
                # Linear interpolation
                if abs(diff_b - diff_a) < 1e-15:
                    return (vout_a + vout_b) / 2
                frac = -diff_a / (diff_b - diff_a)
                return vout_a + frac * (vout_b - vout_a)
        return None


class Check5_8_CompositeCurrentAuto(CheckModule):
    check_ids  = ["5.8.1", "5.8.2", "5.8.8"]
    iq_level   = "LEVEL 4"
    auto_class = "auto"

    def run(self, ibis_file: "IBISFile") -> list[CheckResult]:
        results = []
        for model in ibis_file.models.values():
            if not model.waveforms:
                continue
            subj = model.name
            results.extend(self._check_model(subj, model))
        return results

    def _check_model(self, subj: str, model: "Model") -> list[CheckResult]:
        results = []

        for i, wf in enumerate(model.waveforms):
            wf_label = f"{wf.direction.capitalize()} Waveform #{i+1}"

            # ── 5.8.1: CC present ────────────────────────────────────────────
            if wf.composite_current is None:
                results.append(self._fail("5.8.1", subj,
                    f"{wf_label}: [Composite Current] absent — IQ4 requires CC "
                    "under every waveform. If intentionally omitted, apply X "
                    "designator with documented justification.",
                    spec_ref="Quality Spec §5.8.1"))
                continue  # No point checking 5.8.2 and 5.8.8 without CC

            cc = wf.composite_current
            results.append(self._pass("5.8.1", subj,
                f"{wf_label}: [Composite Current] present",
                spec_ref="Quality Spec §5.8.1"))

            # ── 5.8.2: Time range match ───────────────────────────────────────
            if wf.vt.rows and cc.rows:
                vt_t0 = wf.vt.rows[0][0]
                vt_tn = wf.vt.rows[-1][0]
                cc_t0 = cc.rows[0][0]
                cc_tn = cc.rows[-1][0]

                t_issues = []
                if abs(cc_t0 - vt_t0) > TIME_MATCH_TOL_S:
                    t_issues.append(
                        f"Start: V-T t={vt_t0:.3e}s, CC t={cc_t0:.3e}s "
                        f"(diff={abs(cc_t0-vt_t0):.3e}s)")
                if abs(cc_tn - vt_tn) > TIME_MATCH_TOL_S:
                    t_issues.append(
                        f"End:   V-T t={vt_tn:.3e}s, CC t={cc_tn:.3e}s "
                        f"(diff={abs(cc_tn-vt_tn):.3e}s)")

                if t_issues:
                    results.append(self._fail("5.8.2", subj,
                        f"{wf_label}: CC time range does not match V-T",
                        details=t_issues, spec_ref="Quality Spec §5.8.2"))
                else:
                    results.append(self._pass("5.8.2", subj,
                        f"{wf_label}: CC time range matches V-T "
                        f"({vt_t0:.3e}s — {vt_tn:.3e}s)",
                        spec_ref="Quality Spec §5.8.2"))
            else:
                results.append(self._warn("5.8.2", subj,
                    f"{wf_label}: V-T or CC table is empty — cannot check time range",
                    spec_ref="Quality Spec §5.8.2"))

            # ── 5.8.8: Zero endpoint when V_fixture=0 ────────────────────────
            v_fix = wf.vt.v_fixture
            if v_fix is not None and abs(v_fix) < 1e-9:  # V_fixture ≈ 0
                if cc.rows:
                    if wf.direction == 'rising':
                        # First current value should be ≈ 0
                        target_i = cc.rows[0][1]  # typ column
                        label_pos = "start"
                    else:
                        # Last current value should be ≈ 0
                        target_i = cc.rows[-1][1]
                        label_pos = "end"

                    if target_i is not None and abs(target_i) > CC_ZERO_TOL_A:
                        results.append(self._fail("5.8.8", subj,
                            f"{wf_label}: CC {label_pos} current = {target_i*1e6:.2f}µA "
                            f"(limit ±{CC_ZERO_TOL_A*1e6:.0f}µA) when V_fixture=0",
                            spec_ref="Quality Spec §5.8.8"))
                    else:
                        results.append(self._pass("5.8.8", subj,
                            f"{wf_label}: CC {label_pos} ≈ 0 when V_fixture=0 "
                            f"({target_i*1e6:.2f}µA)",
                            spec_ref="Quality Spec §5.8.8"))
                else:
                    results.append(self._warn("5.8.8", subj,
                        f"{wf_label}: CC table empty — cannot check zero endpoint",
                        spec_ref="Quality Spec §5.8.8"))

        return results
