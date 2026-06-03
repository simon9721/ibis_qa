"""
ibis_qa.py  —  IBIS Quality Specification v3.0 Automated Checker
================================================================
Entry point. Parse one or more .ibs files, run all AUTO checks,
and emit a structured report.

Usage:
    python ibis_qa.py <file.ibs> [--json | --markdown | --html] [--verbose]

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
from spreadsheet import write_spreadsheet_report


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")

    ap = argparse.ArgumentParser(description="IBIS Quality Spec v3.0 AUTO checker")
    ap.add_argument("ibis_file", help="Path to .ibs file")
    output = ap.add_mutually_exclusive_group()
    output.add_argument("--json", action="store_true", help="Output JSON report")
    output.add_argument("--markdown", action="store_true", help="Output Markdown report")
    output.add_argument("--html", action="store_true", help="Output HTML report")
    ap.add_argument("--spreadsheet", help="Write an .xlsx spreadsheet report to this path")
    ap.add_argument("--max-level", "--target-level", dest="max_level",
                    type=int, choices=[1, 2, 3, 4],
                    default=3,
                    help="Run and report only checks up to the requested IQ level (default: 3)")
    ap.add_argument("--review", help="Apply a GUI *.review.json decision overlay to the spreadsheet")
    ap.add_argument("--plot-dir", help="Write SVG visual-curve assets to this directory")
    ap.add_argument("--zout-rload", type=float, default=50.0,
                    help="Load impedance in ohms for reported Zout estimates (default: 50)")
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
    print(f"  Target level IQ{args.max_level}: skipping higher-level checks", file=sys.stderr)

    # 2. Run checks
    runner = CheckRunner(max_level=args.max_level)
    results = runner.run(ibis_file)

    # 3. Report
    reporter = Reporter(
        results,
        ibis_file,
        verbose=args.verbose,
        max_level=args.max_level,
        zout_rload_ohm=args.zout_rload,
    )
    report_dict = None
    if args.spreadsheet:
        report_dict = reporter.as_dict()
        spreadsheet_path = write_spreadsheet_report(
            report_dict,
            args.spreadsheet,
            target_level=args.max_level,
            review_decisions=args.review,
        )
        print(f"Wrote spreadsheet report: {spreadsheet_path}", file=sys.stderr)

    if args.json:
        print(json.dumps(report_dict or reporter.as_dict(), indent=2))
    elif args.markdown:
        if report_dict is None:
            print(reporter.as_markdown(args.plot_dir))
        else:
            from reporter import render_markdown_report
            print(render_markdown_report(report_dict, args.plot_dir))
    elif args.html:
        if report_dict is None:
            print(reporter.as_html(args.plot_dir))
        else:
            from reporter import render_html_report
            print(render_html_report(report_dict, args.plot_dir))
    else:
        print(reporter.as_text())


if __name__ == "__main__":
    main()
