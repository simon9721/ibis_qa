"""
ibis_qa.py  —  IBIS Quality Specification v3.0 Automated Checker
================================================================
Entry point. Parse one or more .ibs files, run all AUTO checks,
and emit a structured report.

Usage:
    python ibis_qa.py <file.ibs> [--json] [--verbose]

Architecture overview
---------------------
                        ┌─────────────────────────────┐
  .ibs file ──► Parser ─►        IBISFile object        │
                        │  .components[]                │
                        │  .models{}                    │
                        │  .header{}                    │
                        │  .pkg_models{}                │
                        └────────────┬────────────────-─┘
                                     │
                    ┌────────────────▼──────────────────┐
                    │          CheckRunner               │
                    │  runs all registered CheckModule   │
                    │  instances in order               │
                    └────────────────┬──────────────────┘
                                     │
                         ┌───────────▼──────────┐
                         │  List[CheckResult]    │
                         │  .check_id            │
                         │  .status (PASS/FAIL/  │
                         │           NA/ERROR)   │
                         │  .message             │
                         │  .details             │
                         └───────────┬──────────┘
                                     │
                    ┌────────────────▼──────────────────┐
                    │            Reporter                │
                    │  plain text  │  JSON  │  (future) │
                    └───────────────────────────────────┘

Design principles
-----------------
1. SINGLE PARSE: the file is tokenised once into an IBISFile object.
   All checks operate on that object — no re-reading the file.

2. PLUG-IN CHECKS: each check (or small family of related checks)
   lives in its own module under checks/. The CheckRunner discovers
   them automatically. Adding a new check = adding one file.

3. TOLERANCE CONSTANTS: numeric thresholds (±1µA leakage, 5% dV
   tolerance, 300ps TD limit) live in config.py so they can be
   tuned without touching check logic.

4. NA vs FAIL: checks return NA when the rule genuinely does not
   apply to this model/component (e.g. 5.3.8 on an Input model).
   NA is not a failure and does not block an IQ level claim.

5. CONTEXT-AWARE: each check receives the full IBISFile so it can
   cross-reference keywords (e.g. resolve Vcc from multiple sources).
"""

import argparse
import json
import sys
from pathlib import Path

from parser.ibis_parser import IBISParser
from runner import CheckRunner
from reporter import Reporter


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")

    ap = argparse.ArgumentParser(description="IBIS Quality Spec v3.0 AUTO checker")
    ap.add_argument("ibis_file", help="Path to .ibs file")
    ap.add_argument("--json", action="store_true", help="Output JSON report")
    ap.add_argument("--verbose", "-v", action="store_true", help="Show NA results too")
    args = ap.parse_args()

    path = Path(args.ibis_file)
    if not path.exists():
        print(f"ERROR: file not found: {path}", file=sys.stderr)
        sys.exit(1)

    # 1. Parse
    print(f"Parsing {path.name} ...", file=sys.stderr)
    parser = IBISParser()
    ibis_file = parser.parse(path)
    print(f"  {len(ibis_file.components)} component(s), "
          f"{len(ibis_file.models)} model(s)", file=sys.stderr)

    # 2. Run checks
    runner = CheckRunner()
    results = runner.run(ibis_file)

    # 3. Report
    reporter = Reporter(results, ibis_file, verbose=args.verbose)
    if args.json:
        print(reporter.as_json())
    else:
        print(reporter.as_text())


if __name__ == "__main__":
    main()
