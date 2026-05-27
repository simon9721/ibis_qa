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

### Tested

- Retested root-level `Micron/` IBIS files with bundled IBISCHK enabled:

| File | PASS | FAIL | WARN | NA | ERROR |
|---|---:|---:|---:|---:|---:|
| `y32a.ibs` | 446 | 106 | 7 | 270 | 0 |
| `z41c.ibs` | 336 | 83 | 7 | 184 | 0 |
| `z41c_it.ibs` | 342 | 77 | 7 | 184 | 0 |

- IBISCHK reported `0 errors, 0 warning(s)` for all three Micron files.
- Check `5.3.1` produced no failures for the Micron files.
- All Micron report results were classified into file, component, model, or package-model scopes; `ungrouped_results` is empty for all three reports.

### Updated Artifacts

- Regenerated:
  - `docs/spec-tree.md`
  - `docs/automation-categories.md`
  - `docs/quality-levels.md`
  - `docs/qa-methods.md`
  - `reports/micron/y32a.json`
  - `reports/micron/z41c.json`
  - `reports/micron/z41c_it.json`
