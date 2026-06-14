"""
checks/c5_9_zout.py  —  Output-impedance plausibility check
=============================================================
5.9.1  Estimated Zout (worst-case corner) ≤ ZOUT_WARN_OHM

Derives Zout from Pullup/Pulldown I-V tables using the Westerhoff load-line
method (same as the visualisation in the reporter). Emits WARN when the
worst corner across pulldown-typ/min/max and pullup-typ/min/max exceeds the
threshold so the finding surfaces in the default-expanded attention section
and includes the load-line plot.
"""

from __future__ import annotations
from typing import TYPE_CHECKING

from checks.base import CheckModule, Status
from config import ZOUT_WARN_OHM, ZOUT_RLOAD_OHM, OUTPUT_TYPES

if TYPE_CHECKING:
    from parser.ibis_parser import IBISFile


class Check5_9_Zout(CheckModule):
    check_ids  = ["5.9.1"]
    iq_level   = "LEVEL 2"
    auto_class = "auto"

    def run(self, ibis_file: "IBISFile") -> list:
        from zout import estimate_zout_for_model
        results = []
        for name, model in ibis_file.models.items():
            mt = (model.model_type or "").lower()
            if mt not in OUTPUT_TYPES:
                results.append(self._na(
                    "5.9.1", name,
                    f"Model_type={model.model_type} has no Pullup/Pulldown — Zout NA",
                    spec_ref="Quality §5.9.1",
                ))
                continue

            zout = estimate_zout_for_model(model, ZOUT_RLOAD_OHM)
            estimated = [e for e in zout.get("estimates", []) if e.get("status") == "estimated"]

            if not estimated:
                results.append(self._na(
                    "5.9.1", name,
                    "Zout could not be estimated (no load-line intersection found)",
                    spec_ref="Quality §5.9.1",
                ))
                continue

            worst_item = max(estimated, key=lambda e: e.get("zout_ohm") or 0.0)
            worst_ohm  = worst_item.get("zout_ohm") or 0.0

            by_corner = {
                f"{e['table']} {e['corner']}": e["zout_ohm"]
                for e in estimated
            }
            corner_lines = [
                f"{label}: {v:.1f}Ω"
                for label, v in sorted(by_corner.items(), key=lambda kv: -(kv[1] or 0))
            ]

            if worst_ohm > ZOUT_WARN_OHM:
                results.append(self._warn(
                    "5.9.1", name,
                    f"Zout worst-case {worst_ohm:.1f}Ω exceeds {ZOUT_WARN_OHM:.0f}Ω "
                    f"({worst_item['table']} {worst_item['corner']}, "
                    f"Rload={ZOUT_RLOAD_OHM:.0f}Ω)",
                    details=corner_lines,
                    spec_ref="Quality §5.9.1",
                    data={
                        "zout_worst_ohm": worst_ohm,
                        "zout_threshold_ohm": ZOUT_WARN_OHM,
                        "zout_rload_ohm": ZOUT_RLOAD_OHM,
                        "zout_by_corner": by_corner,
                    },
                ))
            else:
                results.append(self._pass(
                    "5.9.1", name,
                    f"Zout worst-case {worst_ohm:.1f}Ω within {ZOUT_WARN_OHM:.0f}Ω threshold",
                    spec_ref="Quality §5.9.1",
                ))
        return results
