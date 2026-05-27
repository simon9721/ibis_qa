"""
Semi-auto ordering evidence for model scalar, ramp, overshoot, and ISSO data.

These checks collect deterministic evidence from the IBIS file. They emit PASS
when the parsed data is clean, NA when the relevant data is absent, and WARN
when reviewer attention is needed. WARN is used instead of FAIL for ordering
evidence because these checks are classified as semi_auto in the spec JSON.
"""

from __future__ import annotations
from typing import TYPE_CHECKING

from checks.base import CheckModule, CheckResult
from config import IV_ORDER_ABS_TOL_A, IV_ORDER_REL_TOL

if TYPE_CHECKING:
    from parser.ibis_parser import IBISFile, IVTable, Model


class Check5SemiAutoOrdering(CheckModule):
    check_ids = ["5.1.1", "5.2.6", "5.2.8", "5.5.2", "5.7.2"]
    iq_level = "LEVEL 2/4"
    auto_class = "semi_auto"

    def run(self, ibis_file: "IBISFile") -> list[CheckResult]:
        results = []
        for model in ibis_file.models.values():
            results.extend(self._check_model_params(model))
            results.extend(self._check_model_spec_overshoot(model))
            results.extend(self._check_ramp_order(model))
            results.extend(self._check_isso_order(model))
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

    def _check_model_params(self, model: "Model") -> list[CheckResult]:
        fields = {
            "C_comp": model.c_comp,
            "C_comp_pullup": model.c_comp_pullup,
            "C_comp_pulldown": model.c_comp_pulldown,
            "C_comp_power_clamp": model.c_comp_power_clamp,
            "C_comp_gnd_clamp": model.c_comp_gnd_clamp,
            "Voltage Range": model.voltage_range,
            "Temperature Range": model.temp_range,
            "Pullup Reference": model.pullup_ref,
            "Pulldown Reference": model.pulldown_ref,
            "POWER Clamp Reference": model.power_clamp_ref,
            "GND Clamp Reference": model.gnd_clamp_ref,
        }
        comparable = []
        issues = []
        for name, values in fields.items():
            result = self._check_typ_min_max(values, mode="numeric")
            if result is None:
                continue
            comparable.append(name)
            if result:
                issues.append(f"{name}: {self._format_tmm(values)}")

        if issues:
            return [self._warn_sa("5.1.1", model.name,
                "Model parameter typ/min/max order needs review",
                details=issues,
                spec_ref="Quality Spec §5.1.1")]
        if comparable:
            return [self._pass_sa("5.1.1", model.name,
                f"{len(comparable)} model parameter set(s) have typ/min/max order evidence",
                details=comparable,
                spec_ref="Quality Spec §5.1.1")]
        return [self._na_sa("5.1.1", model.name,
            "No complete typ/min/max model parameter sets parsed",
            spec_ref="Quality Spec §5.1.1")]

    def _check_model_spec_overshoot(self, model: "Model") -> list[CheckResult]:
        if model.model_spec is None:
            return [
                self._na_sa("5.2.6", model.name, "No [Model Spec] S_Overshoot data parsed",
                    spec_ref="Quality Spec §5.2.6"),
                self._na_sa("5.2.8", model.name, "No [Model Spec] D_Overshoot data parsed",
                    spec_ref="Quality Spec §5.2.8"),
            ]

        ms = model.model_spec
        return [
            self._check_tuple_family(
                "5.2.6", model.name,
                {
                    "S_overshoot_high": ms.s_overshoot_high,
                    "S_overshoot_low": ms.s_overshoot_low,
                },
                "S_Overshoot typ/min/max tracking needs review",
                "S_Overshoot typ/min/max tracking evidence is ordered",
                "No complete S_Overshoot typ/min/max values parsed",
                "Quality Spec §5.2.6",
            ),
            self._check_tuple_family(
                "5.2.8", model.name,
                {
                    "D_overshoot_high": ms.d_overshoot_high,
                    "D_overshoot_low": ms.d_overshoot_low,
                    "D_overshoot_time": ms.d_overshoot_time,
                },
                "D_Overshoot typ/min/max tracking needs review",
                "D_Overshoot typ/min/max tracking evidence is ordered",
                "No complete D_Overshoot typ/min/max values parsed",
                "Quality Spec §5.2.8",
            ),
        ]

    def _check_ramp_order(self, model: "Model") -> list[CheckResult]:
        if model.ramp is None:
            return [self._na_sa("5.5.2", model.name,
                "No [Ramp] data parsed",
                spec_ref="Quality Spec §5.5.2")]

        return [self._check_tuple_family(
            "5.5.2", model.name,
            {
                "dV/dt_r": model.ramp.dv_dt_r,
                "dV/dt_f": model.ramp.dv_dt_f,
            },
            "Ramp typ/min/max slew order needs review",
            "Ramp typ/min/max slew order evidence is ordered",
            "No complete Ramp dV/dt typ/min/max values parsed",
            "Quality Spec §5.5.2",
            mode="abs",
        )]

    def _check_isso_order(self, model: "Model") -> list[CheckResult]:
        results = []
        tables = {
            "[ISSO PD]": model.isso_pd,
            "[ISSO PU]": model.isso_pu,
        }
        present = False
        for label, table in tables.items():
            if table is None:
                continue
            present = True
            issues = self._check_table_typ_min_max(table)
            if issues:
                results.append(self._warn_sa("5.7.2", model.name,
                    f"{label} typ/min/max current order needs review",
                    details=issues[:10],
                    spec_ref="Quality Spec §5.7.2"))
            else:
                results.append(self._pass_sa("5.7.2", model.name,
                    f"{label} typ/min/max current order evidence is clean",
                    spec_ref="Quality Spec §5.7.2"))

        if not present:
            results.append(self._na_sa("5.7.2", model.name,
                "No ISSO tables parsed",
                spec_ref="Quality Spec §5.7.2"))
        return results

    def _check_tuple_family(
        self,
        check_id: str,
        subject: str,
        fields: dict[str, tuple],
        issue_msg: str,
        pass_msg: str,
        na_msg: str,
        spec_ref: str,
        mode: str = "numeric",
    ) -> CheckResult:
        comparable = []
        issues = []
        for name, values in fields.items():
            result = self._check_typ_min_max(values, mode=mode)
            if result is None:
                continue
            comparable.append(name)
            if result:
                issues.append(f"{name}: {self._format_tmm(values)}")

        if issues:
            return self._warn_sa(check_id, subject, issue_msg,
                details=issues, spec_ref=spec_ref)
        if comparable:
            return self._pass_sa(check_id, subject, pass_msg,
                details=comparable, spec_ref=spec_ref)
        return self._na_sa(check_id, subject, na_msg, spec_ref=spec_ref)

    def _check_typ_min_max(self, values: tuple, mode: str) -> bool | None:
        if len(values) < 3 or any(value is None for value in values[:3]):
            return None
        typ, min_val, max_val = values[:3]
        if mode == "abs":
            typ, min_val, max_val = abs(typ), abs(min_val), abs(max_val)
        tolerance = max(IV_ORDER_ABS_TOL_A, max(abs(typ), abs(min_val), abs(max_val)) * IV_ORDER_REL_TOL)
        if max_val - min_val <= tolerance:
            return False
        return typ + tolerance < min_val or max_val + tolerance < typ

    def _check_table_typ_min_max(self, table: "IVTable") -> list[str]:
        issues = []
        for row_index, row in enumerate(table.rows, start=1):
            if len(row) < 4 or any(value is None for value in row[:4]):
                issues.append(f"Row {row_index}: expected voltage typ min max")
                continue
            voltage, typ, min_current, max_current = row[:4]
            result = self._check_typ_min_max((typ, min_current, max_current), mode="abs")
            if result:
                issues.append(
                    f"Row {row_index} V={voltage:.4g}: "
                    f"|min|={abs(min_current):.4g}A, |typ|={abs(typ):.4g}A, "
                    f"|max|={abs(max_current):.4g}A")
        return issues

    def _format_tmm(self, values: tuple) -> str:
        typ, min_val, max_val = values[:3]
        return f"typ={typ:.4g}, min={min_val:.4g}, max={max_val:.4g}"
