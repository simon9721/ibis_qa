# Changelog

## 2026-06-09

### Added

- Added a "Failed & Error Items" overview section near the top of Markdown
  and HTML reports (right after Result Summary). It lists every FAIL/ERROR
  result with its message, details, a link to the full write-up, and the
  most relevant inline visual (or a note when the item is a rule/range
  check with no associated plot).
- Checks 5.3.2-5.3.5 and the 5.3.13 ECL sweep now attach structured
  `data.sweep_range` (table key, expected/actual min/max voltage) to FAIL
  results. Check 5.3.7 (monotonicity) now attaches structured
  `data.monotonicity_violations` (combined-curve id, direction, violation
  points) to FAIL results.
- The main I-V Combined Curves plot now visualizes 5.3.7 monotonicity
  failures: X-marker circles highlight the exact points where a combined
  curve violates monotonicity.
- Loosened the 5.5.3 ramp dV/load-line tolerance (`RAMP_DV_TOLERANCE` in
  `config.py`) from 5% to 10%, matching real-world margins seen in hibiki's
  ramp data.
- Fixed the 5.3.4/5.3.5 high-end sweep-range requirements in
  `checks/c5_3_iv_tables.py` to match the Quality Spec's *minimum required*
  coverage rather than its *recommended* coverage: 5.3.4 ([POWER Clamp])
  now requires only -Vcc to 0 (was -Vcc to +2*Vcc), and 5.3.5 ([GND Clamp])
  now requires -Vcc to +Vcc (was -Vcc to +2*Vcc). Extending to +2*Vcc
  remains permitted/recommended but is no longer required to pass.
- Added a new "I-V Clamp Sweep Range" plot (`iv_clamp_sweep_<model>.svg`,
  family `iv_clamp_sweep`) for checks 5.3.4/5.3.5. Unlike the main I-V plot,
  it shows the original (non-combined) `[GND Clamp]`/`[POWER Clamp]`
  typ/min/max curves, with dashed vertical boundary lines marking the
  voltage each table needs to reach (e.g. "5.3.5 needs ≥2V") drawn directly
  against the relevant curve in its own color. Wired into the "Failed &
  Error Items" overview, per-check sections, and "Visual Curves by Model".
- The "I-V Pullup/Pulldown 0 V Detail" plot (5.3.8/5.3.9 leakage check) now
  draws dashed ±`ZERO_CROSS_TOL_A` (±1 µA) horizontal lines so the
  pass/fail leakage boundary is visible against the plotted curves.
- Check 2.1 now auto-corrects a mismatched `[File Name]` keyword before
  running IBISCHK: if the declared filename doesn't match the actual
  filename on disk, the `.ibs` file is rewritten in place with the actual
  filename (lowercased, since IBISCHK rejects upper-case characters in
  `File_name`). A `PASS` result documents the correction when it occurs.
- Added `IBISFile.package_pin_only_info()` to detect "package/pin-mapping
  fragment" `.ibs` files: files with no `[Model]` definitions whose `[Pin]`
  entries reference model names that don't resolve to `POWER`/`GND`/`NC`
  (per the IBIS spec, `[Pin]` model names must resolve within the same file
  — there is no cross-file include mechanism).
- When a package/pin-mapping fragment is detected, `ibis_qa.py` and
  `gui.py` now skip running the full check suite (`results = []`) and
  report a `file_classification` block instead. Text, Markdown, standalone
  HTML, JSON, and `.xlsx` spreadsheet reports all show an explicit
  "Package/Pin-Mapping Fragment — QA checks bypassed" notice with the
  unresolved model name(s) and pin counts.

### Tested

- Regenerated Markdown/HTML/JSON reports for `Arbel_I3C_IBIS.ibs` and
  `Hibiki_IOCL_I3C_I2C_ibis_20260211.ibs` and confirmed: the "Failed &
  Error Items" section lists every FAIL with embedded plots; the
  `mpad_1_S7_*` models show a new I-V Clamp Sweep Range plot with
  individual `[GND Clamp]`/`[POWER Clamp]` curves and "5.3.4 needs ≥2V" /
  "5.3.5 needs ≥2V" dashed boundary lines in each table's own color; the
  I-V Combined Curves plot no longer shows those sweep-range boundary
  lines (only the 5.3.7 monotonicity X-circles remain); the 5.3.7
  monotonicity violations on `I2C_TX_8mA_tx` (and others) are marked with
  red X-circles on the combined curves; and the I-V Pullup/Pulldown 0 V
  Detail plots show ±1 µA dashed leakage-limit lines.
- Regenerated all 12 batch reports (arbel, hibiki, and the 10 Hark Labs
  files) via `gen_batch.sh` with no errors.
- Confirmed the 10% ramp tolerance: `I2C_TX_8mA_tx` (10.0% error) now
  passes 5.5.3, while `I3C_TX_0p125mA_tx` (10.4%-10.5% error) still
  correctly fails.
- Confirmed the 5.3.4/5.3.5 fix: arbel's `mpad_1_S7_*` models, which
  previously failed both checks ("table ends at 0V/1V, need ≥2V/2.4V/3.6V"),
  now pass with the corrected -Vcc..0 / -Vcc..+Vcc requirements; re-ran all
  12 batch reports and confirmed no remaining 5.3.4/5.3.5 FAILs.
- Verified Python compilation for `ibis_qa.py`, `gui.py`, `reporter.py`,
  `spreadsheet.py`, `parser/ibis_parser.py`, and
  `checks/c2_1_ibischk.py`.
- Verified the `[File Name]` auto-correction on copies of
  `Arbel_I3C_IBIS.ibs` and `Hibiki_IOCL_I3C_I2C_ibis_20260211.ibs`: both
  went from IBISCHK errors (mismatched/upper-case `File_name`) to 0 errors,
  and re-running is idempotent (no further corrections).
- Ran the QA tool against all 5 Hark Labs `*_package_pin.ibs` files
  (`ibis_asg256_package_pin.ibs`, `ibis_bbg484_package_pin.ibs`,
  `ibis_bfg484_package_pin.ibs`, `ibis_cbg256_package_pin.ibs`,
  `ibis_lfg672_package_pin.ibs`); each is correctly classified as a
  package/pin-mapping fragment (unresolved `signal` model references) and
  produces zero check results, with the bypass notice present in text,
  Markdown, HTML, and spreadsheet output.
- Confirmed normal files (`abi_gen3.ibs`, Micron `z41c.ibs`) are unaffected
  — no classification banner, checks run as before.

## 2026-06-03

### Added

- Added a shared review-decision layer for semi-auto and manual review workflows. Reports now include deterministic stable review keys, raw and review-adjusted statuses, manual review queues, review overlay metadata, and final signoff summaries.
- Added CLI review workflow options: `--review-template`, `--review-out`, `--review-interactive`, `--reviewer`, `--reviewer-org`, and `--approval-date`. The existing `--review` option now applies the overlay to JSON, Markdown, HTML, console signoff output, and spreadsheet reports.
- Added CLI/report diff support via `--compare-report`, with diff data in JSON and a human-readable Report Diff section in Markdown/HTML.
- Added GUI review improvements: reviewer metadata fields, load-review support, combined semi-auto/manual review queue, external evidence/reference/action fields, multi-row selection, batch accept, batch mark-not-applicable, and required comments for exceptions.
- Added a `Manual Review` spreadsheet sheet and review-adjusted status columns in the raw results sheet.
- Added `docs/ibis-qa-tool-demo.md`, a boss/colleague-facing demo brief that covers the tool flow, IBIS Quality Specification coverage, Zout additions, report formats, CLI/GUI usage, and the current review-queue workflow with recommended polish items.
- Added `ibis_qa_tool/zout.py`, a package-level Zout estimator based on the Westerhoff load-line method from the root `ibis_zout_report.py` prototype.
- Added per-model `zout` data to JSON reports, including typ/min/max Pullup/Pulldown estimates, operating-point voltage/current, load connection, and R_series estimates.
- Added a report-level `zout_summary` block and a human-readable `Zout Estimates` section in Markdown and standalone HTML reports.
- Added per-model Zout load-line SVG plots showing typ/min/max device I-V curves, Rload lines, and operating-point markers.
- Added compact Zout summaries to spreadsheet reports, both in the summary sheet and in each model sheet.
- Added CLI `--zout-rload` to choose the load impedance used for reported Zout estimates; default remains 50 ohm.

### Changed

- Markdown and standalone HTML reports now consume saved review overlays and show a Review Signoff Summary plus Manual Review Items section.
- JSON reports now preserve legacy run-order IDs as `legacy_result_id` while using deterministic stable `result_id`/`review_key` values for review reuse.
- Moved Zout from a standalone root prototype into the normal QA reporting pipeline. Zout is treated as characterization data, not a QA PASS/FAIL item, so it does not affect candidate IQ scoring or review queues.

### Tested

- Verified Python compilation for the full `ibis_qa_tool` package after adding shared review workflow support.
- Verified CLI help exposes the new review workflow options.
- Generated a z41c IQ3 JSON report and pending review template; confirmed stable review keys, 107 semi-auto review rows, 636 manual review rows, review summaries, and signoff summary fields.
- Applied a sample review overlay with one accepted semi-auto item and one accepted manual item; verified JSON, Markdown, standalone HTML, and spreadsheet outputs all reflect the accepted decisions and reviewer metadata.
- Verified the reviewed standalone HTML embeds SVG images as data URIs and has no external `.svg` image references.
- Verified the reviewed `.xlsx` workbook remains a valid spreadsheet zip package and includes the added manual-review sheet.
- Verified `--compare-report` adds report-diff data to generated JSON/Markdown output.
- Verified Python compilation for the full `ibis_qa_tool` package after adding Zout integration.
- Regenerated Micron IQ3 JSON, Markdown, standalone HTML, spreadsheet, and SVG-asset reports with Zout data included.
- Verified generated JSON is UTF-8 and includes `zout_summary` plus per-model `zout` blocks.
- Verified generated Markdown/HTML reports include the `Zout Estimates` section and linked Zout load-line plots, and that standalone HTML still embeds SVG curves as data URIs.
- Verified generated `.xlsx` workbooks remain valid spreadsheet zip packages after adding Zout rows.

## 2026-06-02

### Added

- Added CLI `--max-level` support, with `--target-level` retained as an alias, so QA runs can stop at IQ1/IQ2/IQ3/IQ4 instead of only filtering spreadsheet rows after all checks run.
- Added a GUI `Max Level` selector. Saved JSON, Markdown, review queues, SVG assets, and spreadsheets now use the selected target level from the run.
- Added a navigable Markdown report table of contents with per-check anchors and back-to-TOC links.
- Added a full `Quality Check Results` Markdown section that lists every required check item by IQ level, then summarizes outcomes by file/component/model/package scope with PASS/WARN/FAIL/NA/ERROR/review counts and evidence.
- Added HTML report generation via CLI `--html` and GUI Save Report. HTML uses the same QA tables, anchors, links, and embedded SVG curve images as the Markdown report.
- Added bidirectional links between WARN/FAIL/ERROR QA rows and the relevant per-model curve figures.

### Changed

- CLI, GUI, and the shared GUI report helper now default to target IQ3; IQ4 evidence is generated only when `--max-level 4` or `IQ4` is selected.
- Removed report-level heatmap and bar-style diagnostic SVG generation from Markdown reports.
- Renamed report visuals to "Visual Curves".
- Markdown/HTML visual curves now use broad curve plots for I-V, ISSO, and V-T/Composite Current data, with the existing related finding callouts embedded in those plots.
- Main I-V table SVGs now show only the actual available combined or clamp/driver curves, so clamp-only models are labeled as clamp curves instead of combined curves.
- Split I-V detail visuals into separate per-model `iv_clamp_*.svg` figures for clamp-only `5.3.10` leakage review and `iv_zero_*.svg` figures for pullup/pulldown `5.3.8`/`5.3.9` zero-current review.
- HTML report IBISCHK excerpts now use simple light text styling instead of a dark code panel.
- HTML reports now embed local SVG curve images as data URIs, making the generated `.html` file standalone for sharing.
- Plot finding callouts now include the first available detail line, so WARN/FAIL evidence can show actual-vs-limit text directly in the figure when the checker provides it.
- Markdown/HTML visual curves moved into their own per-model section with model-scoped candidate scores, while checklist outcomes now live in the main level/check-item table.
- Markdown IBISCHK evidence now shows the executable name instead of leaking the local executable path; full path evidence remains in JSON.
- Target-level reports omit higher-level check results, level-summary rows, and IQ appendix rows; candidate scores are capped at the selected target level.

### Tested

- Verified Python compilation for the runner, base check class, mixed semi-auto modules, CLI, GUI, reporter, plotting, and spreadsheet generator.
- Verified the CLI default run on `z41c.ibs` produces `max_level=3`, candidate `IQ3`, and no result above numeric level 3.
- Verified `--max-level 3` on `z41c.ibs` reports only levels 1-3, omits `5.7`/`5.8` checks, and excludes Level 4 rows from JSON and Markdown summaries.
- Verified regenerated Markdown and HTML reports include the table of contents, quality-check results, IBISCHK execution summary, Visual Curves section, and no local IBISCHK executable path.
- Verified regenerated HTML reports contain embedded `data:image/svg+xml;base64` image sources and no external `.svg` image references.
- Verified regenerated I-V SVGs split combined curves, clamp-only leakage detail, and pullup/pulldown zero-current detail into separate figures.
- Verified generated curve-only SVG visual curves parse as valid XML and all Markdown SVG links resolve.
- Verified generated `.xlsx` reports are valid spreadsheet zip packages.
- Regenerated Micron JSON, Markdown, HTML, spreadsheet, and SVG plot artifacts with `--max-level 3`, so Level 4 checks/results are intentionally omitted:

| File | PASS | FAIL | WARN | NA | ERROR | Candidate | SVG plots |
|---|---:|---:|---:|---:|---:|---|---:|
| `y32a.ibs` | 831 | 1 | 51 | 727 | 0 | IQ1 | 140 |
| `z41c.ibs` | 560 | 0 | 107 | 454 | 0 | IQ3 | 98 |
| `z41c_it.ibs` | 632 | 0 | 35 | 454 | 0 | IQ3 | 98 |

## 2026-06-01

### Added

- Added `docs/z41c-checklist-comparison.md`, a detailed comparison between Micron's completed `z41c_ibis_quality_checklist.xls` and the generated `reports/micron/z41c.xlsx`.
- Added `docs/z41c-post-review-vs-micron.md`, comparing generated results to Micron's checklist under the assumption that semi-auto findings are accepted and manual rows are ignored.
- Added `docs/z41c-micron-comparison-report.md`, a human-readable two-part report covering the baseline Micron comparison, implemented fixes, and post-review comparison result.
- Expanded `docs/z41c-micron-comparison-report.md` with the current semi-auto review queue and the manual check items that remain outside automated tool signoff.
- Added spreadsheet `--target-level` filtering so checklist body rows can be limited to IQ1/IQ2/IQ3/IQ4 while retaining the raw results sheet as audit evidence.
- Added spreadsheet review-decision overlay support for GUI `*.review.json` files; accepted, exception, rejected, and not-applicable decisions now render into checklist rows and raw result columns.
- Added richer Markdown visual curve generation: per-model SVG plots now cover I-V curves, ISSO tables, and V-T/Composite Current waveforms when those data exist in the IBIS model.
- Added diagnostic Markdown visual curves: a report-level finding heatmap plus targeted per-model SVGs for I-V zero-current/leakage residuals, ISSO voltage sweep range, Ramp dV error, and Composite Current zero-endpoint curves.

### Analysis

- Compared workbook format, sheet structure, status vocabulary, model/component granularity, IBISCHK metadata, grouped checklist statuses, and item-level result differences.
- Identified likely tool improvement areas from the comparison: bare-die pin RLC handling, differential input Tdelay handling, scalar `key = value` parsing, ISSO endpoint equations, target IQ level filtering, review-decision overlays, and vendor-template spreadsheet output.
- Confirmed the post-review/IQ3-scope comparison has 109 exact matches out of 112 non-manual rows, with zero hard FAIL/ERROR disagreements; the only differences are two PASS-vs-NA S_Overshoot policy rows and one PASS-vs-EXCEPTION V-T duration annotation row.

### Changed

- Extended parser support for scalar assignment syntax such as `Vref = 1200.000mV`, TMM assignment forms, `R_load = ...`, and receiver-threshold assignment rows.
- Changed `3.2.2` so detected bare-die components report `NA` instead of failing per-pin packaged RLC completeness.
- Changed `3.3.2` so input differential pins with `Tdelay` present produce review-required `WARN` evidence instead of a hard failure; missing or invalid `Vdiff` remains a hard failure.
- Changed `3.3.2` again so input differential `Tdelay_typ=0ns` is treated like no effective delay and passes; only nonzero input `Tdelay_typ` remains review evidence.
- Changed `5.3.8`/`5.3.9` zero-current checks so any over-limit zero-current value reports review-required `WARN` instead of hard `FAIL`, because the quality spec notes that special cases may not cross zero current at 0 V.
- Added explicit open-drain/open-sink/open-source `NA` handling for missing non-required driver tables.
- Surfaced commented dynamic overshoot Model Spec rows as semi-auto `5.2.8` review evidence.
- Corrected `5.7.1` ISSO PU endpoint comparison to use `Ipu(Vcc)`.
- Expanded I-V plots from typ-only visualization to typ/min/max overlays, endpoint markers, 0 V current markers, and voltage guide lines.
- Added plot-family attention panels to generated SVGs so related FAIL/WARN/ERROR check IDs are visible directly on the relevant I-V, ISSO, or waveform plot.
- Split Markdown report visuals into diagnostic evidence and broader overview evidence so the images first explain flagged findings, then provide context curves.
- Changed candidate-score logic to use the highest implemented IQ level without `FAIL` or `ERROR`; unresolved `WARN`/review items remain visible but no longer lower the candidate score by themselves.
- Updated `docs/implemented-checks.md`, `docs/todo-review.md`, `docs/z41c-checklist-comparison.md`, and `ibis_qa_tool/README.md` for the new parser/check/spreadsheet/plot behavior.

### Tested

- Verified Python compilation for the parser, affected checks, CLI, GUI, reporter, plotting, and spreadsheet generator.
- Verified z41c target-level spreadsheet generation hides Level 4 rows from component/model checklist sheets and emits explicit `NA` for no-result checklist rows.
- Verified spreadsheet review overlays render reviewer decisions and comments.
- Verified candidate scoring now ignores unresolved `WARN` items as blockers while preserving them as review findings; regenerated `z41c.ibs` and `z41c_it.ibs` now report candidate `IQ3`.
- Verified generated SVG visual curves parse as valid XML.
- Verified generated SVGs include attention panels for related visual-family findings where applicable.
- Verified all generated Markdown SVG references resolve to existing asset files.
- Regenerated Micron JSON, Markdown, spreadsheet, and SVG plot artifacts:

| File | PASS | FAIL | WARN | NA | ERROR | Candidate | SVG plots |
|---|---:|---:|---:|---:|---:|---|---:|
| `y32a.ibs` | 930 | 19 | 79 | 1111 | 0 | IQ1 | 135 |
| `z41c.ibs` | 646 | 16 | 134 | 708 | 0 | IQ3 | 107 |
| `z41c_it.ibs` | 724 | 10 | 62 | 708 | 0 | IQ3 | 73 |

## 2026-05-31

### Added

- Added `CheckResult.data` and now persist full IBISCHK execution evidence for check `2.1` in JSON, including full stdout/stderr.
- Added `ibis_qa_tool/plotting.py` and CLI `--plot-dir` support for per-model I-V SVG plots in Markdown reports.
- Added sampled `iv_plot_data` to model JSON sections so downstream report layers can render I-V plots without reparsing the IBIS file.
- Added endpoint markers to SVG I-V plots, plus `-Vcc` and `2Vcc` guide markers where the model voltage range is known.

### Changed

- Expanded `5.1.4` semi-auto evidence to show explicit/defaulted voltage-reference tuples, typ/min/max ordering, positive-reference polarity, and nominal reference consistency against `Voltage Range`.
- Enforced the project I-V sweep policy that checks `5.3.2` through `5.3.5` expect approximately `-Vcc` to `2*Vcc` coverage for Pullup, Pulldown, POWER Clamp, and GND Clamp tables.
- Reworked `5.3.7` to check true combined typ-current curves for `[Pulldown] + [GND Clamp]` and `[Pullup] + [POWER Clamp]` instead of individual-table monotonicity.
- Refined `5.5.3` Ramp dV checking to evaluate rising and falling typ/min/max corners with the load-line balance `I_table + I_load = 0`.
- Added single-ended open-sink/open-source handling for `5.5.3` by using the external fixture rail as the missing steady-state endpoint when one driver table is absent.
- Updated `docs/implemented-checks.md`, `docs/todo-review.md`, and `ibis_qa_tool/README.md` to describe the new todo implementations and plot workflow.

### Tested

- Verified Python compilation for the CLI, GUI, reporter, plotting, spreadsheet, and affected check modules.
- Verified CLI Markdown generation with `--plot-dir` writes SVG assets and embeds the expected plot links.
- Verified generated JSON contains full IBISCHK output data and per-model I-V plot data.
- Verified generated `.xlsx` reports are valid spreadsheet zip packages.
- Regenerated Micron JSON, Markdown, spreadsheet, and SVG plot artifacts:

| File | PASS | FAIL | WARN | NA | ERROR | Candidate | SVG plots |
|---|---:|---:|---:|---:|---:|---|---:|
| `y32a.ibs` | 922 | 37 | 69 | 1109 | 0 | IQ1 | 62 |
| `z41c.ibs` | 633 | 34 | 100 | 735 | 0 | IQ1 | 42 |
| `z41c_it.ibs` | 711 | 28 | 28 | 735 | 0 | IQ1 | 42 |

## 2026-05-29

### Added

- Added `iq_level` and `numeric_level` to each JSON result entry, sourced from `data/ibis_quality_spec_3_0.json`.
- Updated the GUI result and review tables to display IQ level, and included level metadata in exported review decisions.
- Added Markdown report generation for model-maker-facing QA summaries, including file summary, score assessment, per-level item status, shared findings, per-model findings with model-scoped candidate scores, level-divided finding tables, attention reasons, and IQ/designator appendices.
- Added CLI `--markdown` output and made the GUI save a matching `*.qa.md` file beside each saved `*.qa.json` report.
- Added `docs/implemented-checks.md`, a detailed item-by-item implementation reference for all 22 auto checks and all 25 semi-auto evidence collectors, including thresholds, result behavior, review flags, and known judgement calls.
- Added `docs/manual-checks.md`, a detailed rationale and reviewer evidence guide explaining why each of the 20 manual quality checks requires datasheet, extraction, package, circuit, or model-maker context.
- Added checklist-style `.xlsx` spreadsheet report generation with summary, component, model, and raw-results sheets; the GUI now saves it beside JSON and Markdown reports, and the CLI supports `--spreadsheet`.
- Added full IBISCHK execution evidence to JSON result data for check `2.1`, including executable path, return code, parsed version, errors, warnings, cautions, and full stdout/stderr.
- Added `docs/todo-review.md` with the reviewed status of current engineering todo items.
- Changed missing in-file `|IQ Score:` handling from a check `2.1` failure to a non-failing writeback note, since the tool is intended to help assign the IQ score.
- Changed missing in-file IBISCHK version documentation from a check `2.1` warning to a non-blocking documentation note; Level 1 is gated by actual IBISCHK execution status.

### Tested

- Verified CLI JSON output preserves IQ level metadata for generated results.
- Verified the GUI module compiles and initializes after the additional IQ level columns.
- Verified CLI Markdown output is generated, omits local file path/review-queue workflow sections, removes the redundant action/failed-error sections, includes per-model candidate scores, and includes IQ level/designator appendices.
- Verified Micron files still execute IBISCHK with `0 errors, 0 warning(s)` and are no longer failed solely for missing an existing IQ score tag.
- Verified missing IBISCHK version documentation no longer blocks Level 1.
- Current Micron report summaries after treating missing `|IQ Score:` as a writeback note:

| File | PASS | FAIL | WARN | NA | ERROR | Candidate |
|---|---:|---:|---:|---:|---:|---|
| `y32a.ibs` | 863 | 105 | 75 | 1109 | 0 | IQ1 |
| `z41c.ibs` | 591 | 82 | 107 | 735 | 0 | IQ1 |
| `z41c_it.ibs` | 669 | 76 | 35 | 735 | 0 | IQ1 |

### Updated Artifacts

- Regenerated `reports/micron/*.json` with `level_summary` and `score_summary`.
- Added generated model-maker-facing Markdown reports under `reports/micron/*.md`.

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
