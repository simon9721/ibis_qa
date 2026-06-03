"""Semi-auto evidence for I-V, V-T, ISSO, and composite-current quality."""

from __future__ import annotations
from typing import TYPE_CHECKING

from checks.base import CheckModule, CheckResult
from config import (
    CLAMP_LEAKAGE_TOL_A,
    CC_FLAT_SLOPE_TOL_A,
    IV_ORDER_ABS_TOL_A,
    IV_ORDER_REL_TOL,
    IV_RANGE_TOLERANCE,
    MIN_TABLE_POINTS,
    MIN_WAVEFORM_POINTS,
    STAIRSTEP_REVIEW_THRESHOLD,
    SMOOTHNESS_THRESHOLD,
    VT_DURATION_MAX_S,
    VT_ENDPOINT_TOL_V,
)

if TYPE_CHECKING:
    from parser.ibis_parser import IBISFile, IVTable, Model, Waveform


class Check5SemiAutoQuality(CheckModule):
    check_ids = [
        "5.1.2", "5.1.4", "5.3.6", "5.3.10", "5.3.14",
        "5.4.1", "5.4.2", "5.4.3", "5.4.4", "5.5.4",
        "5.6.2", "5.7.3", "5.7.4", "5.8.3", "5.8.5", "5.8.7",
    ]
    iq_level = "LEVEL 2/4"
    auto_class = "semi_auto"

    def run(self, ibis_file: "IBISFile") -> list[CheckResult]:
        results = []
        for model in ibis_file.models.values():
            if self.is_check_enabled("5.1.2"):
                results.append(self._check_c_comp(model))
            if self.is_check_enabled("5.1.4"):
                results.append(self._check_voltage_refs(model))
            if any(self.is_check_enabled(check_id) for check_id in ("5.3.6", "5.3.10", "5.3.14")):
                results.extend(self._check_iv_quality(model))
            if any(self.is_check_enabled(check_id) for check_id in ("5.4.1", "5.4.2", "5.4.3", "5.4.4")):
                results.extend(self._check_vt_quality(model))
            if self.is_check_enabled("5.5.4"):
                results.append(self._check_ramp_dt(model))
            if self.is_check_enabled("5.6.2"):
                results.append(self._check_vref_consistency(model))
            if any(self.is_check_enabled(check_id) for check_id in ("5.7.3", "5.7.4")):
                results.extend(self._check_isso_quality(model))
            if any(self.is_check_enabled(check_id) for check_id in ("5.8.3", "5.8.5", "5.8.7")):
                results.extend(self._check_composite_current_quality(model))
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

    def _check_c_comp(self, model: "Model") -> CheckResult:
        fields = {
            "C_comp": model.c_comp,
            "C_comp_pullup": model.c_comp_pullup,
            "C_comp_pulldown": model.c_comp_pulldown,
            "C_comp_power_clamp": model.c_comp_power_clamp,
            "C_comp_gnd_clamp": model.c_comp_gnd_clamp,
        }
        present = []
        issues = []
        for name, values in fields.items():
            vals = [value for value in values[:3] if value is not None]
            if not vals:
                continue
            present.append(name)
            if any(value < 0 for value in vals):
                issues.append(f"{name}: negative capacitance value")
            if any(value > 20e-12 for value in vals):
                issues.append(f"{name}: value above 20 pF review threshold")
        if issues:
            return self._warn_sa("5.1.2", model.name,
                "C_comp reasonableness evidence needs review",
                details=issues, spec_ref="Quality Spec §5.1.2")
        if present:
            return self._pass_sa("5.1.2", model.name,
                "C_comp evidence is positive and within review threshold",
                details=present, spec_ref="Quality Spec §5.1.2")
        return self._na_sa("5.1.2", model.name,
            "No C_comp values parsed",
            spec_ref="Quality Spec §5.1.2")

    def _check_voltage_refs(self, model: "Model") -> CheckResult:
        explicit_fields = {
            "Voltage Range": model.voltage_range,
            "Pullup Reference": model.pullup_ref,
            "Pulldown Reference": model.pulldown_ref,
            "POWER Clamp Reference": model.power_clamp_ref,
            "GND Clamp Reference": model.gnd_clamp_ref,
        }
        resolved_fields = {
            "Voltage Range": (model.voltage_range, "explicit"),
            "Pullup Reference": (
                model.pullup_ref if model.pullup_ref[0] is not None else model.voltage_range,
                "explicit" if model.pullup_ref[0] is not None else "default from Voltage Range",
            ),
            "Pulldown Reference": (
                model.pulldown_ref if model.pulldown_ref[0] is not None else (0.0, 0.0, 0.0),
                "explicit" if model.pulldown_ref[0] is not None else "default 0 V",
            ),
            "POWER Clamp Reference": (
                model.power_clamp_ref if model.power_clamp_ref[0] is not None else model.voltage_range,
                "explicit" if model.power_clamp_ref[0] is not None else "default from Voltage Range",
            ),
            "GND Clamp Reference": (
                model.gnd_clamp_ref if model.gnd_clamp_ref[0] is not None else (0.0, 0.0, 0.0),
                "explicit" if model.gnd_clamp_ref[0] is not None else "default 0 V",
            ),
        }
        details = []
        issues = []
        for name, values in explicit_fields.items():
            vals = [value for value in values[:3] if value is not None]
            if not vals:
                continue
            order_issue = self._tuple_order_issue(values)
            if order_issue:
                issues.append(f"{name}: {order_issue}")
            if name in ("Voltage Range", "Pullup Reference", "POWER Clamp Reference") and any(value <= 0 for value in vals):
                issues.append(f"{name}: expected positive supply/reference values, got {values}")
        for name, (values, source) in resolved_fields.items():
            if values[0] is None:
                details.append(f"{name}: unresolved ({source})")
            else:
                details.append(f"{name}: {self._format_tuple(values)} ({source})")
        vcc_typ = resolved_fields["Voltage Range"][0][0]
        for name in ("Pullup Reference", "POWER Clamp Reference"):
            ref_typ = resolved_fields[name][0][0]
            if vcc_typ is None or ref_typ is None:
                continue
            tol = max(1e-3, abs(vcc_typ) * 0.01)
            if abs(ref_typ - vcc_typ) > tol:
                issues.append(
                    f"{name}: typ={ref_typ:.4g}V differs from Voltage Range typ={vcc_typ:.4g}V "
                    f"by more than {tol:.4g}V; confirm this is intentional"
                )
        if issues:
            return self._warn_sa("5.1.4", model.name,
                "Voltage/reference evidence needs review",
                details=issues + details, spec_ref="Quality Spec §5.1.4")
        if any(values[0] is not None for values, _source in resolved_fields.values()):
            return self._pass_sa("5.1.4", model.name,
                "Voltage/reference evidence parsed, defaults resolved, and basic consistency looks reasonable",
                details=details, spec_ref="Quality Spec §5.1.4")
        return self._na_sa("5.1.4", model.name,
            "No voltage/reference values parsed",
            spec_ref="Quality Spec §5.1.4")

    def _check_iv_quality(self, model: "Model") -> list[CheckResult]:
        results = []
        tables = {
            "[Pulldown]": model.pulldown,
            "[Pullup]": model.pullup,
            "[GND Clamp]": model.gnd_clamp,
            "[POWER Clamp]": model.power_clamp,
        }
        present = {label: table for label, table in tables.items() if table is not None}
        if not present:
            return [
                self._na_sa("5.3.6", model.name, "No I-V tables parsed", spec_ref="Quality Spec §5.3.6"),
                self._na_sa("5.3.10", model.name, "No clamp I-V tables parsed", spec_ref="Quality Spec §5.3.10"),
                self._na_sa("5.3.14", model.name, "No I-V tables parsed", spec_ref="Quality Spec §5.3.14"),
            ]

        stair = []
        sparse = []
        for label, table in present.items():
            roughness = self._roughness_ratio(table)
            if roughness is not None and roughness > STAIRSTEP_REVIEW_THRESHOLD:
                stair.append(f"{label}: roughness={roughness:.3g} > {STAIRSTEP_REVIEW_THRESHOLD:.3g}")
            if len(table.rows) < MIN_TABLE_POINTS:
                sparse.append(f"{label}: {len(table.rows)} point(s) < {MIN_TABLE_POINTS}")
        results.append(self._warn_sa("5.3.6", model.name, "I-V stair-step evidence needs review",
            details=stair, spec_ref="Quality Spec §5.3.6") if stair else
            self._pass_sa("5.3.6", model.name, "I-V stair-step roughness evidence is within threshold",
            spec_ref="Quality Spec §5.3.6"))
        results.append(self._warn_sa("5.3.14", model.name, "I-V point distribution evidence needs review",
            details=sparse, spec_ref="Quality Spec §5.3.14") if sparse else
            self._pass_sa("5.3.14", model.name, "I-V point counts meet evidence threshold",
            spec_ref="Quality Spec §5.3.14"))

        leakage = []
        for label, table in (("[GND Clamp]", model.gnd_clamp), ("[POWER Clamp]", model.power_clamp)):
            if table is None:
                continue
            current = table.interpolate(0.0, 1)
            if current is not None and abs(current) > CLAMP_LEAKAGE_TOL_A:
                leakage.append(f"{label}: I(0V)={current*1e6:.3g} uA")
        results.append(self._warn_sa("5.3.10", model.name, "Clamp leakage evidence needs review",
            details=leakage, spec_ref="Quality Spec §5.3.10") if leakage else
            self._pass_sa("5.3.10", model.name, "Clamp leakage evidence is within threshold at 0V",
            spec_ref="Quality Spec §5.3.10"))
        return results

    def _check_vt_quality(self, model: "Model") -> list[CheckResult]:
        if not model.waveforms:
            return [
                self._na_sa("5.4.1", model.name, "No V-T waveform tables parsed", spec_ref="Quality Spec §5.4.1"),
                self._na_sa("5.4.2", model.name, "No V-T waveform tables parsed", spec_ref="Quality Spec §5.4.2"),
                self._na_sa("5.4.3", model.name, "No V-T waveform tables parsed", spec_ref="Quality Spec §5.4.3"),
                self._na_sa("5.4.4", model.name, "No V-T waveform tables parsed", spec_ref="Quality Spec §5.4.4"),
            ]
        rising = sum(1 for wf in model.waveforms if wf.direction == "rising")
        falling = sum(1 for wf in model.waveforms if wf.direction == "falling")
        count_issues = []
        if rising == 0:
            count_issues.append("No [Rising Waveform] table")
        if falling == 0:
            count_issues.append("No [Falling Waveform] table")
        sparse = []
        duration = []
        endpoints = []
        for index, wf in enumerate(model.waveforms, start=1):
            label = f"{wf.direction} waveform #{index}"
            rows = wf.vt.rows
            if len(rows) < MIN_WAVEFORM_POINTS:
                sparse.append(f"{label}: {len(rows)} point(s) < {MIN_WAVEFORM_POINTS}")
            if len(rows) >= 2:
                dt = rows[-1][0] - rows[0][0]
                if dt > VT_DURATION_MAX_S:
                    duration.append(f"{label}: duration={dt:.3e}s > {VT_DURATION_MAX_S:.3e}s")
                if wf.vt.v_fixture is not None:
                    start_delta = abs(rows[0][1] - wf.vt.v_fixture) if rows[0][1] is not None else None
                    end_delta = abs(rows[-1][1] - wf.vt.v_fixture) if rows[-1][1] is not None else None
                    if start_delta is not None and end_delta is not None and min(start_delta, end_delta) > VT_ENDPOINT_TOL_V:
                        endpoints.append(f"{label}: neither endpoint is within {VT_ENDPOINT_TOL_V:.3g}V of V_fixture")
        return [
            self._warn_sa("5.4.1", model.name, "V-T waveform count evidence needs review", details=count_issues, spec_ref="Quality Spec §5.4.1")
            if count_issues else self._pass_sa("5.4.1", model.name, f"V-T waveform evidence includes {rising} rising and {falling} falling table(s)", spec_ref="Quality Spec §5.4.1"),
            self._warn_sa("5.4.2", model.name, "V-T point distribution evidence needs review", details=sparse, spec_ref="Quality Spec §5.4.2")
            if sparse else self._pass_sa("5.4.2", model.name, "V-T point counts meet evidence threshold", spec_ref="Quality Spec §5.4.2"),
            self._warn_sa("5.4.3", model.name, "V-T duration evidence needs review", details=duration, spec_ref="Quality Spec §5.4.3")
            if duration else self._pass_sa("5.4.3", model.name, "V-T duration evidence is within threshold", spec_ref="Quality Spec §5.4.3"),
            self._warn_sa("5.4.4", model.name, "V-T endpoint fixture evidence needs review", details=endpoints, spec_ref="Quality Spec §5.4.4")
            if endpoints else self._pass_sa("5.4.4", model.name, "V-T endpoint fixture evidence is within threshold", spec_ref="Quality Spec §5.4.4"),
        ]

    def _check_ramp_dt(self, model: "Model") -> CheckResult:
        if model.ramp is None or not model.waveforms:
            return self._na_sa("5.5.4", model.name, "Ramp or V-T waveform data absent", spec_ref="Quality Spec §5.5.4")
        spans = [span for wf in model.waveforms for span in [self._crossing_span_20_80(wf)] if span is not None]
        ramp_dts = [value for value in (model.ramp.dt_r[0], model.ramp.dt_f[0]) if value is not None]
        if not spans or not ramp_dts:
            return self._na_sa("5.5.4", model.name, "No comparable 20-80% V-T span and Ramp dt pair parsed", spec_ref="Quality Spec §5.5.4")
        avg_span = sum(spans) / len(spans)
        avg_ramp_dt = sum(ramp_dts) / len(ramp_dts)
        rel_err = abs(avg_ramp_dt - avg_span) / avg_span if avg_span else 0.0
        detail = f"avg Ramp dt={avg_ramp_dt:.3e}s, avg V-T 20-80% span={avg_span:.3e}s, diff={rel_err*100:.1f}%"
        if rel_err > 0.2:
            return self._warn_sa("5.5.4", model.name, "Ramp dt versus V-T 20-80% evidence needs review", details=[detail], spec_ref="Quality Spec §5.5.4")
        return self._pass_sa("5.5.4", model.name, "Ramp dt evidence is near V-T 20-80% crossing span", details=[detail], spec_ref="Quality Spec §5.5.4")

    def _check_vref_consistency(self, model: "Model") -> CheckResult:
        mt = model.model_type_lower
        if not any(kind in mt for kind in ("open_drain", "open_source", "open_sink", "ecl")):
            return self._na_sa("5.6.2", model.name, f"Model_type={model.model_type} does not require this Vref consistency evidence", spec_ref="Quality Spec §5.6.2")
        if model.vref is None:
            return self._warn_sa("5.6.2", model.name, "Vref consistency needs review; scalar Vref not parsed", spec_ref="Quality Spec §5.6.2")
        return self._pass_sa("5.6.2", model.name, f"Vref evidence parsed for {model.model_type}: {model.vref:.4g}V", spec_ref="Quality Spec §5.6.2")

    def _check_isso_quality(self, model: "Model") -> list[CheckResult]:
        present = {label: table for label, table in {"[ISSO PD]": model.isso_pd, "[ISSO PU]": model.isso_pu}.items() if table is not None}
        if not present:
            return [
                self._na_sa("5.7.3", model.name, "No ISSO tables parsed", spec_ref="Quality Spec §5.7.3"),
                self._na_sa("5.7.4", model.name, "No ISSO tables parsed", spec_ref="Quality Spec §5.7.4"),
            ]
        sparse = [f"{label}: {len(table.rows)} point(s) < {MIN_TABLE_POINTS}" for label, table in present.items() if len(table.rows) < MIN_TABLE_POINTS]
        sweep = []
        vcc = model.resolve_vcc()
        if vcc is not None:
            tol = abs(vcc) * IV_RANGE_TOLERANCE
            for label, table in present.items():
                vs = table.voltages()
                if vs and (min(vs) > 0.0 + tol or max(vs) < vcc - tol):
                    sweep.append(f"{label}: {min(vs):.4g}V to {max(vs):.4g}V, expected approx 0V to {vcc:.4g}V")
        else:
            sweep.append("Cannot resolve Vcc for ISSO sweep evidence")
        return [
            self._warn_sa("5.7.3", model.name, "ISSO point distribution evidence needs review", details=sparse, spec_ref="Quality Spec §5.7.3")
            if sparse else self._pass_sa("5.7.3", model.name, "ISSO point counts meet evidence threshold", spec_ref="Quality Spec §5.7.3"),
            self._warn_sa("5.7.4", model.name, "ISSO voltage sweep evidence needs review", details=sweep, spec_ref="Quality Spec §5.7.4")
            if sweep else self._pass_sa("5.7.4", model.name, "ISSO voltage sweep evidence covers expected range", spec_ref="Quality Spec §5.7.4"),
        ]

    def _check_composite_current_quality(self, model: "Model") -> list[CheckResult]:
        waveforms = [wf for wf in model.waveforms if wf.composite_current is not None]
        if not waveforms:
            return [
                self._na_sa("5.8.3", model.name, "No Composite Current tables parsed", spec_ref="Quality Spec §5.8.3"),
                self._na_sa("5.8.5", model.name, "No Composite Current tables parsed", spec_ref="Quality Spec §5.8.5"),
                self._na_sa("5.8.7", model.name, "No Composite Current tables parsed", spec_ref="Quality Spec §5.8.7"),
            ]
        alignment = []
        endpoints = []
        flatness = []
        for index, wf in enumerate(waveforms, start=1):
            label = f"{wf.direction} waveform #{index}"
            vt_rows = wf.vt.rows
            cc_rows = wf.composite_current.rows if wf.composite_current else []
            if len(vt_rows) != len(cc_rows):
                alignment.append(f"{label}: V-T has {len(vt_rows)} points, CC has {len(cc_rows)} points")
            if cc_rows:
                first_i = cc_rows[0][1]
                last_i = cc_rows[-1][1]
                if first_i is not None and last_i is not None and min(abs(first_i), abs(last_i)) > CLAMP_LEAKAGE_TOL_A:
                    endpoints.append(f"{label}: CC endpoints {first_i:.3e}A, {last_i:.3e}A")
                if len(cc_rows) >= 4 and cc_rows[0][1] is not None and cc_rows[1][1] is not None and cc_rows[-1][1] is not None and cc_rows[-2][1] is not None:
                    start_delta = abs(cc_rows[1][1] - cc_rows[0][1])
                    end_delta = abs(cc_rows[-1][1] - cc_rows[-2][1])
                    if start_delta > CC_FLAT_SLOPE_TOL_A or end_delta > CC_FLAT_SLOPE_TOL_A:
                        flatness.append(f"{label}: edge deltas start={start_delta:.3e}A, end={end_delta:.3e}A")
        return [
            self._warn_sa("5.8.3", model.name, "Composite Current time-alignment evidence needs review", details=alignment, spec_ref="Quality Spec §5.8.3")
            if alignment else self._pass_sa("5.8.3", model.name, "Composite Current point alignment evidence is clean", spec_ref="Quality Spec §5.8.3"),
            self._warn_sa("5.8.5", model.name, "Composite Current endpoint correlation evidence needs review", details=endpoints, spec_ref="Quality Spec §5.8.5")
            if endpoints else self._pass_sa("5.8.5", model.name, "Composite Current endpoint evidence is near zero at one or both ends", spec_ref="Quality Spec §5.8.5"),
            self._warn_sa("5.8.7", model.name, "Composite Current edge flatness evidence needs review", details=flatness, spec_ref="Quality Spec §5.8.7")
            if flatness else self._pass_sa("5.8.7", model.name, "Composite Current edge flatness evidence is within threshold", spec_ref="Quality Spec §5.8.7"),
        ]

    def _roughness_ratio(self, table: "IVTable") -> float | None:
        currents = [row[1] for row in table.rows if len(row) > 1 and row[1] is not None]
        if len(currents) < 3:
            return None
        span = max(currents) - min(currents)
        if abs(span) < 1e-15:
            return 0.0
        max_step = max(abs(currents[i + 1] - currents[i]) for i in range(len(currents) - 1))
        return max_step / abs(span)

    def _tuple_order_issue(self, values: tuple) -> str | None:
        if len(values) < 3 or any(value is None for value in values[:3]):
            return None
        typ, min_val, max_val = values[:3]
        tolerance = max(
            IV_ORDER_ABS_TOL_A,
            max(abs(typ), abs(min_val), abs(max_val)) * IV_ORDER_REL_TOL,
        )
        if max_val - min_val <= tolerance:
            return None
        if typ + tolerance < min_val or max_val + tolerance < typ:
            return (
                f"typ/min/max order needs review "
                f"({self._format_tuple(values)}, tolerance={tolerance:.4g})"
            )
        return None

    def _format_tuple(self, values: tuple) -> str:
        names = ("typ", "min", "max")
        parts = []
        for name, value in zip(names, values[:3]):
            parts.append(f"{name}={'NA' if value is None else f'{value:.4g}V'}")
        return ", ".join(parts)

    def _crossing_span_20_80(self, wf: "Waveform") -> float | None:
        rows = wf.vt.rows
        if len(rows) < 2:
            return None
        volts = [row[1] for row in rows if row[1] is not None]
        v0, v1 = volts[0], volts[-1]
        lo = v0 + 0.2 * (v1 - v0)
        hi = v0 + 0.8 * (v1 - v0)
        t_lo = self._crossing_time(rows, lo)
        t_hi = self._crossing_time(rows, hi)
        if t_lo is None or t_hi is None:
            return None
        return abs(t_hi - t_lo)

    def _crossing_time(self, rows: list[tuple], target_v: float) -> float | None:
        for left, right in zip(rows, rows[1:]):
            t0, v0 = left[0], left[1]
            t1, v1 = right[0], right[1]
            if v0 is None or v1 is None or t0 is None or t1 is None:
                continue
            if (v0 <= target_v <= v1) or (v1 <= target_v <= v0):
                if abs(v1 - v0) < 1e-15:
                    return t0
                frac = (target_v - v0) / (v1 - v0)
                return t0 + frac * (t1 - t0)
        return None
