"""
checks/base.py  —  CheckResult and CheckModule base class
=========================================================
Every check returns a list of CheckResult objects.
Status values:
  PASS  — rule satisfied
  FAIL  — rule violated
  NA    — rule does not apply to this item (not a failure)
  WARN  — soft finding (not spec-mandated failure, but noteworthy)
  ERROR — check itself failed (parse issue, missing data)
"""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from parser.ibis_parser import IBISFile


class Status(str, Enum):
    PASS  = "PASS"
    FAIL  = "FAIL"
    NA    = "NA"
    WARN  = "WARN"
    ERROR = "ERROR"


@dataclass
class CheckResult:
    check_id:   str                    # e.g. "2.1", "3.1.1"
    status:     Status
    subject:    str                    # what was checked (component/model name)
    message:    str                    # one-line summary
    details:    list[str]              = field(default_factory=list)  # extra lines
    spec_ref:   str                    = ""   # Quality Spec section
    automation_class: str              = "auto"
    review_required: bool              = False
    data:       dict                   = field(default_factory=dict)


class CheckModule:
    """
    Base class for a check module. Each module covers one or a small
    family of closely related check IDs.

    Subclasses implement run(ibis_file) -> list[CheckResult].

    The check_ids class attribute declares which IQ check IDs this
    module covers, for registration and reporting purposes.
    """
    check_ids: list[str] = []
    iq_level:  str = ""     # "LEVEL 1", "LEVEL 2", etc.
    auto_class: str = "auto"
    enabled_check_ids: set[str] | None = None

    def run(self, ibis_file: "IBISFile") -> list[CheckResult]:
        raise NotImplementedError

    def is_check_enabled(self, check_id: str) -> bool:
        return (
            self.enabled_check_ids is None
            or check_id in self.enabled_check_ids
        )

    # ── Convenience helpers ───────────────────────────────────────────────────

    def _pass(self, check_id: str, subject: str, msg: str, **kw) -> CheckResult:
        return CheckResult(check_id=check_id, status=Status.PASS,
                           subject=subject, message=msg, **kw)

    def _fail(self, check_id: str, subject: str, msg: str, **kw) -> CheckResult:
        return CheckResult(check_id=check_id, status=Status.FAIL,
                           subject=subject, message=msg, **kw)

    def _na(self, check_id: str, subject: str, msg: str, **kw) -> CheckResult:
        return CheckResult(check_id=check_id, status=Status.NA,
                           subject=subject, message=msg, **kw)

    def _warn(self, check_id: str, subject: str, msg: str, **kw) -> CheckResult:
        return CheckResult(check_id=check_id, status=Status.WARN,
                           subject=subject, message=msg, **kw)

    def _error(self, check_id: str, subject: str, msg: str, **kw) -> CheckResult:
        return CheckResult(check_id=check_id, status=Status.ERROR,
                           subject=subject, message=msg, **kw)
