"""
checks/c5_7_isso.py  —  Check 5.7.1: ISSO PU/PD tables
=========================================================
5.7.1  AUTO: [ISSO PU] and [ISSO PD] present for output-capable models
             Endpoint correlations: Isso_pd(0)=Ipd(Vcc), Isso_pu(0)=Ipu(Vcc),
                                    Isso_pd(Vcc)≈0,       Isso_pu(Vcc)≈0
"""

from __future__ import annotations
from typing import Optional, TYPE_CHECKING

from checks.base import CheckModule, CheckResult, Status
from config import ISSO_ENDPOINT_TOL, ISSO_REQUIRED_TYPES, ECL_TYPES, INPUT_TYPES

if TYPE_CHECKING:
    from parser.ibis_parser import IBISFile, Model, IVTable


class Check5_7_1_ISSO(CheckModule):
    check_ids  = ["5.7.1"]
    iq_level   = "LEVEL 4"
    auto_class = "auto"

    def run(self, ibis_file: "IBISFile") -> list[CheckResult]:
        results = []
        for model in ibis_file.models.values():
            results.extend(self._check_model(model))
        return results

    def _check_model(self, model: "Model") -> list[CheckResult]:
        mt = model.model_type_lower
        subj = model.name

        # NA for input-only and ECL (ISSO not applicable)
        if mt in INPUT_TYPES:
            return [self._na("5.7.1", subj,
                f"Input model ({model.model_type}) — ISSO not required, NA",
                spec_ref="Quality Spec §5.7.1")]
        if mt in ECL_TYPES:
            return [self._na("5.7.1", subj,
                f"ECL model ({model.model_type}) — ISSO not applicable, NA",
                spec_ref="Quality Spec §5.7.1")]
        if mt not in ISSO_REQUIRED_TYPES:
            return [self._na("5.7.1", subj,
                f"Model_type '{model.model_type}' does not require ISSO tables, NA",
                spec_ref="Quality Spec §5.7.1")]

        results = []

        # ── Presence check ────────────────────────────────────────────────────
        if model.isso_pd is None:
            results.append(self._fail("5.7.1", subj,
                "[ISSO PD] table missing for output-capable model",
                spec_ref="Quality Spec §5.7.1"))
        if model.isso_pu is None:
            results.append(self._fail("5.7.1", subj,
                "[ISSO PU] table missing for output-capable model",
                spec_ref="Quality Spec §5.7.1"))
        if model.isso_pd is None or model.isso_pu is None:
            return results

        results.append(self._pass("5.7.1", subj,
            "[ISSO PD] and [ISSO PU] tables present",
            spec_ref="Quality Spec §5.7.1"))

        # ── Endpoint correlation ──────────────────────────────────────────────
        vcc = model.resolve_vcc()
        if vcc is None:
            results.append(self._error("5.7.1", subj,
                "Cannot resolve Vcc — skipping ISSO endpoint check",
                spec_ref="Quality Spec §5.7.1"))
            return results

        endpoint_issues = []

        # Isso_pd(0) should equal Ipd(Vcc)
        isso_pd_at_0  = model.isso_pd.interpolate(0.0, col=1)
        ipd_at_vcc    = model.pulldown.interpolate(vcc, col=1) if model.pulldown else None

        if isso_pd_at_0 is not None and ipd_at_vcc is not None and abs(ipd_at_vcc) > 1e-12:
            err = abs(isso_pd_at_0 - ipd_at_vcc) / abs(ipd_at_vcc)
            if err > ISSO_ENDPOINT_TOL:
                endpoint_issues.append(
                    f"Isso_pd(0)={isso_pd_at_0*1000:.3f}mA ≠ "
                    f"Ipd(Vcc={vcc:.2f}V)={ipd_at_vcc*1000:.3f}mA "
                    f"({err*100:.1f}% error, limit {ISSO_ENDPOINT_TOL*100:.0f}%)")

        # Isso_pu(0) should equal Ipu(Vcc)
        isso_pu_at_0  = model.isso_pu.interpolate(0.0, col=1)
        ipu_at_vcc = model.pullup.interpolate(vcc, col=1) if model.pullup else None

        if isso_pu_at_0 is not None and ipu_at_vcc is not None and abs(ipu_at_vcc) > 1e-12:
            err = abs(isso_pu_at_0 - ipu_at_vcc) / abs(ipu_at_vcc)
            if err > ISSO_ENDPOINT_TOL:
                endpoint_issues.append(
                    f"Isso_pu(0)={isso_pu_at_0*1000:.3f}mA ≠ "
                    f"Ipu(Vcc={vcc:.2f}V)={ipu_at_vcc*1000:.3f}mA "
                    f"({err*100:.1f}% error, limit {ISSO_ENDPOINT_TOL*100:.0f}%)")

        # Isso_pd(Vcc) ≈ 0
        isso_pd_at_vcc = model.isso_pd.interpolate(vcc, col=1)
        if isso_pd_at_vcc is not None and abs(isso_pd_at_vcc) > abs(ipd_at_vcc or 1.0) * ISSO_ENDPOINT_TOL:
            endpoint_issues.append(
                f"Isso_pd(Vcc={vcc:.2f}V)={isso_pd_at_vcc*1000:.3f}mA, expected ≈ 0")

        # Isso_pu(Vcc) ≈ 0
        isso_pu_at_vcc = model.isso_pu.interpolate(vcc, col=1)
        if isso_pu_at_vcc is not None and abs(isso_pu_at_vcc) > abs(ipu_at_vcc or 1.0) * ISSO_ENDPOINT_TOL:
            endpoint_issues.append(
                f"Isso_pu(Vcc={vcc:.2f}V)={isso_pu_at_vcc*1000:.3f}mA, expected ≈ 0")

        if endpoint_issues:
            results.append(self._fail("5.7.1", subj,
                f"ISSO endpoint equation violation(s)",
                details=endpoint_issues, spec_ref="Quality Spec §5.7.1"))
        else:
            details = []
            if isso_pd_at_0 is not None and ipd_at_vcc is not None:
                details.append(f"Isso_pd(0)={isso_pd_at_0*1000:.3f}mA ≈ "
                                f"Ipd(Vcc)={ipd_at_vcc*1000:.3f}mA ✓")
            if isso_pu_at_0 is not None and ipu_at_vcc is not None:
                details.append(f"Isso_pu(0)={isso_pu_at_0*1000:.3f}mA ≈ "
                                f"Ipu(Vcc)={ipu_at_vcc*1000:.3f}mA ✓")
            results.append(self._pass("5.7.1", subj,
                "ISSO endpoint equations satisfied",
                details=details, spec_ref="Quality Spec §5.7.1"))

        return results
