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
from review import (
    apply_review_decisions,
    compare_reports,
    load_review_decisions,
    make_review_payload,
    run_cli_review,
    write_review_payload,
)
from spreadsheet import write_spreadsheet_report


def _update_ibis_local_db(args, ibs_path, review_json_path: str) -> None:
    """Write the review decisions JSON path into the ibis-local DB if --ibis-local-db given."""
    if not getattr(args, "ibis_local_db", None):
        return
    try:
        import hashlib
        from pathlib import Path as _Path
        db_path = _Path(args.ibis_local_db)
        if not db_path.exists():
            print(f"WARNING: --ibis-local-db path not found: {db_path}", file=sys.stderr)
            return
        checksum = hashlib.sha256(ibs_path.read_bytes()).hexdigest()
        # Use ibis-local's Store directly
        import sys as _sys
        _sys.path.insert(0, str(db_path.parent))
        from ibis_library.store import Store
        store = Store(db_path)
        file_id = store.find_by_checksum(checksum)
        if file_id is None:
            print(f"WARNING: IBIS file not found in ibis-local DB (checksum mismatch)", file=sys.stderr)
            return
        store.update_review_decisions_path(file_id, review_json_path)
        print(f"Updated ibis-local DB: file_id={file_id} → review_decisions={review_json_path}",
              file=sys.stderr)
    except Exception as exc:
        print(f"WARNING: could not update ibis-local DB: {exc}", file=sys.stderr)


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
    ap.add_argument("--review", help="Apply a *.review.json decision overlay to all generated reports")
    ap.add_argument("--review-template", help="Write a pending review template JSON to this path")
    ap.add_argument("--review-out", help="Write review decisions/template to this path")
    ap.add_argument("--review-interactive", action="store_true",
                    help="Prompt for semi-auto and manual review decisions in the terminal")
    ap.add_argument("--reviewer", default="", help="Reviewer name for review exports")
    ap.add_argument("--reviewer-org", default="", help="Reviewer organization for review exports")
    ap.add_argument("--approval-date", default="", help="Approval date for review exports")
    ap.add_argument("--compare-report", help="Compare this run against a previous QA JSON report")
    ap.add_argument("--ibis-local-db", metavar="DB_PATH",
                    help="Path to ibis-local SQLite DB. When review decisions are "
                         "written (--review-out / --review-template), also stores the "
                         "decisions JSON path in the DB under the matching IBIS file entry.")
    ap.add_argument("--apply-fixes", metavar="REVIEW_JSON",
                    help="Apply approved fix proposals from REVIEW_JSON to the IBIS file "
                         "in-place (creates .bak backup). Review entries need "
                         "\"fix_approved\": true; optionally add \"fix_vcc_min\" / "
                         "\"fix_vcc_max\" to also update the min/max corners.")
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

    # 2. Run checks (unless this is a package/pin-mapping fragment, not a
    # standalone IBIS model file)
    file_classification = ibis_file.package_pin_only_info()
    if file_classification:
        print(
            "  PACKAGE/PIN-MAPPING FRAGMENT DETECTED — bypassing QA checks. "
            f"Unresolved [Pin] model name(s): "
            f"{', '.join(file_classification['unresolved_models'])} "
            f"({file_classification['unresolved_pin_count']} of "
            f"{file_classification['total_pin_count']} pins)",
            file=sys.stderr,
        )
        results = []
    else:
        runner = CheckRunner(max_level=args.max_level)
        results = runner.run(ibis_file)

    # 3. Report
    reporter = Reporter(
        results,
        ibis_file,
        verbose=args.verbose,
        max_level=args.max_level,
        zout_rload_ohm=args.zout_rload,
        review_decisions=args.review,
        file_classification=file_classification,
    )
    report_dict = reporter.as_dict()
    active_review_decisions = args.review

    if args.review_interactive:
        existing = load_review_decisions(args.review)
        payload = run_cli_review(
            report_dict,
            existing_decisions=existing,
            reviewer=args.reviewer,
            organization=args.reviewer_org,
            approval_date=args.approval_date,
        )
        report_dict = apply_review_decisions(report_dict, payload)
        active_review_decisions = payload
        if args.review_out:
            review_path = write_review_payload(payload, args.review_out)
            print(f"Wrote review decisions: {review_path}", file=sys.stderr)

    if args.review_template:
        payload = make_review_payload(
            report_dict,
            load_review_decisions(args.review),
            reviewer=args.reviewer,
            organization=args.reviewer_org,
            approval_date=args.approval_date,
        )
        review_path = write_review_payload(payload, args.review_template)
        print(f"Wrote review template: {review_path}", file=sys.stderr)

    if args.review_out and not args.review_interactive:
        payload = make_review_payload(
            report_dict,
            load_review_decisions(args.review),
            reviewer=args.reviewer,
            organization=args.reviewer_org,
            approval_date=args.approval_date,
        )
        review_path = write_review_payload(payload, args.review_out)
        print(f"Wrote review decisions: {review_path}", file=sys.stderr)
        _update_ibis_local_db(args, path, str(review_path))

    if args.review_template and not args.review_interactive:
        _update_ibis_local_db(args, path, args.review_template)

    if args.apply_fixes:
        from fixer import collect_approved_fixes, apply_fixes as _apply_fixes
        from review import load_review_decisions
        review_data = load_review_decisions(args.apply_fixes) or {}
        fixes = collect_approved_fixes(report_dict, review_data)
        if fixes:
            changes = _apply_fixes(path, fixes)
            for c in changes:
                print(f"  {'Applied' if not c.startswith('WARNING') else ''}{c}", file=sys.stderr)
            applied = sum(1 for c in changes if not c.startswith("WARNING"))
            print(f"Applied {applied} fix(es) to {path.name} (backup: {path.name}.bak)",
                  file=sys.stderr)
        else:
            print("No approved fixes found in review JSON.", file=sys.stderr)

    if args.compare_report:
        report_dict["report_diff"] = compare_reports(report_dict, args.compare_report)

    if args.spreadsheet:
        spreadsheet_path = write_spreadsheet_report(
            report_dict,
            args.spreadsheet,
            target_level=args.max_level,
            review_decisions=active_review_decisions,
        )
        print(f"Wrote spreadsheet report: {spreadsheet_path}", file=sys.stderr)

    if args.json:
        print(json.dumps(report_dict, indent=2))
    elif args.markdown:
        from reporter import render_markdown_report
        print(render_markdown_report(report_dict, args.plot_dir))
    elif args.html:
        from reporter import render_html_report
        print(render_html_report(report_dict, args.plot_dir))
    else:
        print(reporter.as_text())
        signoff = report_dict.get("signoff_summary") or {}
        semi = signoff.get("semi_auto") or {}
        manual = signoff.get("manual") or {}
        if signoff:
            print("")
            print("REVIEW SIGNOFF")
            print(f"  Final signoff ready : {'YES' if signoff.get('final_ready') else 'NO'}")
            print(f"  Hard blockers       : {signoff.get('hard_blockers', 0)}")
            print(f"  Semi-auto pending   : {semi.get('pending', 0)} / {semi.get('total_review_items', 0)}")
            print(f"  Manual pending      : {manual.get('pending', 0)} / {manual.get('total_review_items', 0)}")


if __name__ == "__main__":
    main()
