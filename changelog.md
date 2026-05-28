# Changelog

## 2026-05-27

### Added

- Added automatic discovery of the bundled IBISCHK executable at `ibischk721_win_64/ibischk7_64.exe`, in addition to existing PATH-based discovery.
- Added scoped JSON report sections:
  - `header` for shared file-level metadata.
  - `file_results` for file/header-level checks such as `2.1`.
  - `components` for component metadata and component-scoped results.
  - `models` for per-model metadata and model-scoped results.
  - `package_models` for package-model metadata and package-model-scoped results.
  - `ungrouped_results` for any result that cannot be classified.
- Kept the existing top-level `results` array for backward compatibility, now enriched with `scope`, `component_name`, `model_name`, and `package_model_name`.
- Added `tools/render_qa_methods.py` so `docs/qa-methods.md` can be regenerated from `data/ibis_quality_spec_3_0.json` without rebuilding or overwriting the manually edited JSON.
- Made `tools/render_qa_methods.py` report output paths correctly even when `--output` points outside the repository.
- Implemented check `5.3.1` for I-V table row shape and active-region typ/min/max current ordering.
- Added semi-auto evidence collectors for all 25 `semi_auto` checks in `data/ibis_quality_spec_3_0.json`, including structural, I-V, V-T, Ramp, ISSO, and Composite Current evidence.
- Added `automation_class` and `review_required` fields to JSON result entries.
- Added stable `result_id`, top-level `review_queue`, and `review_summary` fields to JSON reports so semi-auto review decisions can be tied back to specific generated findings.
- Added a standard-library Tkinter GUI at `ibis_qa_tool/gui.py` for choosing an IBIS file, running QA, reviewing semi-auto evidence, entering reviewer comments, choosing decisions, and exporting separate `*.review.json` decision files.
- Configured CLI stdout/stderr as UTF-8 on Python builds that support stream reconfiguration, preventing Windows text-report encoding errors.

### Tested

- Retested root-level `Micron/` IBIS files with bundled IBISCHK enabled:

| File | PASS | FAIL | WARN | NA | ERROR |
|---|---:|---:|---:|---:|---:|
| `y32a.ibs` | 861 | 106 | 76 | 1109 | 0 |
| `z41c.ibs` | 590 | 83 | 107 | 735 | 0 |
| `z41c_it.ibs` | 668 | 77 | 35 | 735 | 0 |

- IBISCHK reported `0 errors, 0 warning(s)` for all three Micron files.
- Check `5.3.1` produced no failures for the Micron files.
- Semi-auto evidence produced review-required warnings where reviewer judgment is needed:
  - `y32a.ibs`: 69 review items
  - `z41c.ibs`: 100 review items
  - `z41c_it.ibs`: 28 review items
- Judgment note: semi-auto evidence uses `WARN` with `review_required=true` instead of hard `FAIL` unless a finding is already covered by an auto check, because these checks depend on technology intent, datasheet comparison, or visual/engineering review.
- All Micron report results were classified into file, component, model, or package-model scopes; `ungrouped_results` is empty for all three reports.
- Verified the new GUI module imports cleanly and the CLI JSON output includes the new review workflow fields.

### Updated Artifacts

- Regenerated:
  - `docs/spec-tree.md`
  - `docs/automation-categories.md`
  - `docs/quality-levels.md`
  - `docs/qa-methods.md`
  - `reports/micron/y32a.json`
  - `reports/micron/z41c.json`
  - `reports/micron/z41c_it.json`
