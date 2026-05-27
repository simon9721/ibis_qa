"""
checks/c3_1_package.py  —  Checks 3.1.1 and 3.1.2: [Package] values
=====================================================================
3.1.1 AUTO: typ/min/max all present (non-NA)
3.1.2 AUTO/SEMI: limits + ordering (auto part only)

Bare-die components are skipped (NA) — they use stub values by design.
"""

from __future__ import annotations
from typing import TYPE_CHECKING

from checks.base import CheckModule, CheckResult, Status
from config import PKG_L_MAX_H, PKG_C_MAX_F, PKG_R_MAX_OHM

if TYPE_CHECKING:
    from parser.ibis_parser import IBISFile


class Check3_1_Package(CheckModule):
    check_ids  = ["3.1.1", "3.1.2"]
    iq_level   = "LEVEL 2"
    auto_class = "auto"  # 3.1.1 full auto; 3.1.2 auto portion

    def run(self, ibis_file: "IBISFile") -> list[CheckResult]:
        results = []
        for comp in ibis_file.components:
            subj = comp.name

            # Bare-die: NA
            if comp.is_bare_die:
                results.append(self._na("3.1.1", subj,
                    "Bare-die component — stub package values expected, check NA",
                    spec_ref="Quality Spec §3.1.1"))
                results.append(self._na("3.1.2", subj,
                    "Bare-die component — package limits check NA",
                    spec_ref="Quality Spec §3.1.2"))
                continue

            pkg = comp.package
            params = {
                'R_pkg': (pkg.r_pkg, PKG_R_MAX_OHM, 'Ω'),
                'L_pkg': (pkg.l_pkg, PKG_L_MAX_H,  'H'),
                'C_pkg': (pkg.c_pkg, PKG_C_MAX_F,  'F'),
            }

            # ── 3.1.1: all typ/min/max must be non-NA ────────────────────────
            missing = [k for k, (v, _, _) in params.items()
                       if any(x is None for x in v)]
            if missing:
                results.append(self._fail("3.1.1", subj,
                    f"Missing typ/min/max values for: {', '.join(missing)}",
                    spec_ref="Quality Spec §3.1.1"))
            else:
                results.append(self._pass("3.1.1", subj,
                    "All [Package] R/L/C have typ, min, and max values",
                    spec_ref="Quality Spec §3.1.1"))

            # ── 3.1.2: limits and ordering ────────────────────────────────────
            limit_issues = []
            order_issues = []

            for param, (vals, limit, unit) in params.items():
                typ, mn, mx = vals
                if typ is None:
                    continue
                # Limit check
                if abs(typ) > limit:
                    limit_issues.append(
                        f"{param} typ={typ:.3g}{unit} exceeds limit {limit}{unit}")
                # Ordering: min ≤ typ ≤ max
                if mn is not None and mx is not None:
                    if not (mn <= typ <= mx):
                        order_issues.append(
                            f"{param}: min={mn:.3g} typ={typ:.3g} max={mx:.3g} "
                            f"— order violation")

            issues = limit_issues + order_issues
            if issues:
                results.append(self._fail("3.1.2", subj,
                    f"{len(issues)} issue(s) found",
                    details=issues,
                    spec_ref="Quality Spec §3.1.2"))
            else:
                results.append(self._pass("3.1.2", subj,
                    "Package values within limits and min≤typ≤max",
                    spec_ref="Quality Spec §3.1.2"))

        return results
