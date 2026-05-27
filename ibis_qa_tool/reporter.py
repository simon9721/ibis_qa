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
        lines.append(f"IBIS QA Report — AUTO Checks")
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

    def as_json(self) -> str:
        out = {
            "file": str(self.ibis_file.path),
            "ibis_ver": self.ibis_file.ibis_ver,
            "file_rev": self.ibis_file.file_rev,
            "iq_score_in_file": self.ibis_file.iq_score_in_file,
            "results": [
                {
                    "check_id": r.check_id,
                    "status":   r.status.value,
                    "subject":  r.subject,
                    "message":  r.message,
                    "details":  r.details,
                    "spec_ref": r.spec_ref,
                }
                for r in self.results
            ],
            "summary": {
                s.value: sum(1 for r in self.results if r.status == s)
                for s in Status
            }
        }
        return json.dumps(out, indent=2)

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
