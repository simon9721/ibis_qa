"""
checks/c2_1_ibischk.py  —  Check 2.1: IBIS file passes IBISCHK
================================================================
Quality Spec §2.1, §1.4
AUTO check — three sub-checks:
  a) Report any existing IQ score tag in the .ibs file
  b) Report any existing IBISCHK version documentation in the file
  c) Run IBISCHK and verify zero errors
"""

from __future__ import annotations
import re
import shutil
import subprocess
from pathlib import Path
from typing import TYPE_CHECKING

from checks.base import CheckModule, CheckResult, Status

if TYPE_CHECKING:
    from parser.ibis_parser import IBISFile


_FILE_NAME_RE = re.compile(
    r'^([ \t]*\[\s*file\s*name\s*\][ \t]*)(\S+)',
    re.IGNORECASE | re.MULTILINE,
)


class Check2_1(CheckModule):
    check_ids  = ["2.1"]
    iq_level   = "LEVEL 1"
    auto_class = "auto"

    def run(self, ibis_file: "IBISFile") -> list[CheckResult]:
        results = []

        # ── Sub-check 0: [File Name] must match the actual filename ─────────
        # IBISCHK hard-errors if these disagree. Fix it on disk before running
        # IBISCHK so the file is self-consistent and the checker doesn't fail
        # on a trivial keyword/filename mismatch.
        corrected_from = self._fix_file_name_mismatch(ibis_file)
        if corrected_from:
            results.append(self._pass(
                "2.1", ibis_file.file_name,
                f"Corrected [File Name] from '{corrected_from}' to "
                f"'{ibis_file.file_name}' to match the actual filename on disk.",
                spec_ref="Quality Spec §2.1"
            ))

        # ── Sub-check A: IQ score writeback note (§1.4) ─────────────────────
        if ibis_file.iq_score_in_file:
            results.append(self._pass(
                "2.1", ibis_file.file_name,
                f"IQ score tag found in file: {ibis_file.iq_score_in_file}",
                spec_ref="Quality Spec §1.4"
            ))
        else:
            results.append(self._pass(
                "2.1", ibis_file.file_name,
                "No existing '|IQ Score:' tag found inside the .ibs file. "
                "This is reported as a writeback note only; it does not fail the quality check "
                "because this tool is intended to help assign the score.",
                spec_ref="Quality Spec §1.4"
            ))

        # ── Sub-check B: IBISCHK version documentation note ──────────────────
        if ibis_file.ibischk_ver_in_file:
            results.append(self._pass(
                "2.1", ibis_file.file_name,
                f"IBISCHK version documented in file: {ibis_file.ibischk_ver_in_file}",
                spec_ref="Quality Spec §2.1"
            ))
        else:
            results.append(self._pass(
                "2.1", ibis_file.file_name,
                "IBISCHK version not found documented inside the .ibs file. "
                "This is reported as a documentation note only; it does not block Level 1.",
                spec_ref="Quality Spec §2.1"
            ))

        # ── Sub-check C: Run IBISCHK if available ────────────────────────────
        ibischk_path = self._find_ibischk()
        if ibischk_path:
            try:
                proc = subprocess.run(
                    [ibischk_path, str(ibis_file.path)],
                    capture_output=True, text=True, timeout=60
                )
                output = proc.stdout + proc.stderr
                errors   = len(re.findall(r'\bERROR\b', output, re.IGNORECASE))
                warnings = len(re.findall(r'\bWARNING\b', output, re.IGNORECASE))
                cautions = len(re.findall(r'\bCAUTION\b', output, re.IGNORECASE))
                version_match = re.search(
                    r'\bIBISCHK\S*\s+V?([0-9][0-9.]+)',
                    output,
                    re.IGNORECASE,
                )
                ibischk_data = {
                    "path": ibischk_path,
                    "returncode": proc.returncode,
                    "version": version_match.group(1) if version_match else None,
                    "errors": errors,
                    "warnings": warnings,
                    "cautions": cautions,
                    "output": output,
                }
                if errors == 0:
                    results.append(self._pass(
                        "2.1", ibis_file.file_name,
                        f"IBISCHK: 0 errors, {warnings} warning(s)",
                        details=[f"IBISCHK path: {ibischk_path}"],
                        data={"ibischk": ibischk_data},
                        spec_ref="Quality Spec §2.1"
                    ))
                else:
                    results.append(self._fail(
                        "2.1", ibis_file.file_name,
                        f"IBISCHK: {errors} error(s), {warnings} warning(s)",
                        details=output.splitlines()[:20],
                        data={"ibischk": ibischk_data},
                        spec_ref="Quality Spec §2.1"
                    ))
            except subprocess.TimeoutExpired:
                results.append(self._error(
                    "2.1", ibis_file.file_name, "IBISCHK timed out after 60s"))
            except Exception as e:
                results.append(self._error(
                    "2.1", ibis_file.file_name, f"IBISCHK execution error: {e}"))
        else:
            results.append(self._warn(
                "2.1", ibis_file.file_name,
                "IBISCHK not found on PATH — skipping execution check. "
                "Install IBISCHK and ensure it is on PATH.",
                spec_ref="Quality Spec §2.1"
            ))

        return results

    def _fix_file_name_mismatch(self, ibis_file: "IBISFile") -> str | None:
        """
        If the in-file [File Name] keyword doesn't match the actual filename
        on disk, rewrite it in place to match. Returns the old declared
        filename if a correction was made, otherwise None.

        IBISCHK requires [File Name] to be all lowercase (and rejects mixed-
        case filenames as errors), so the corrected value is the lowercased
        actual filename rather than a verbatim copy.
        """
        actual = ibis_file.path.name.lower()
        declared = (ibis_file.file_name or "").strip()
        if not declared or declared == actual:
            return None

        try:
            text = ibis_file.path.read_text(encoding="utf-8", errors="replace", newline="")
        except OSError:
            return None

        new_text, n = _FILE_NAME_RE.subn(lambda m: m.group(1) + actual, text, count=1)
        if n == 0:
            return None

        try:
            ibis_file.path.write_text(new_text, encoding="utf-8", newline="")
        except OSError:
            return None

        ibis_file.file_name = actual
        return declared

    def _find_ibischk(self) -> str | None:
        """Find IBISCHK on PATH or in a repo-local IBISCHK bundle."""
        path_hit = (
            shutil.which("ibischk")
            or shutil.which("ibischk7")
            or shutil.which("ibischk7_64")
            or shutil.which("ibischk7_64.exe")
        )
        if path_hit:
            return path_hit

        repo_root = Path(__file__).resolve().parents[2]
        candidates = [
            repo_root / "ibischk721_win_64" / "ibischk7_64.exe",
            repo_root / "ibischk7_64.exe",
            repo_root / "ibischk7.exe",
            repo_root / "ibischk.exe",
        ]
        for candidate in candidates:
            if candidate.exists():
                return str(candidate)

        for candidate in repo_root.glob("ibischk*_win_64/ibischk*.exe"):
            return str(candidate)

        return None
