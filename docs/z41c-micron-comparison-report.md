# z41c IBIS QA Tool Comparison Report

Report date: 2026-06-01

## Executive Summary

This report compares the `ibis_qa_tool` output against Micron's completed
`z41c_ibis_quality_checklist.xls` and explains how the tool results changed
after the first improvement pass.

Micron's checklist is a manually completed IQ3 workbook for both `z41c.ibs`
and `z41c_it.ibs`. It assigns an overall quality of `3MSX`, records IBISCHK
7.0.2 with zero errors, warnings, and cautions, and includes human signoff for
manual checks, exceptions, and correlation designators.

The original generated workbook was more detailed but less vendor-like. It
checked each parsed model separately, included Level 4 checks even though
Micron claimed IQ3, and did not yet consume review decisions or exception
overlays. The first comparison exposed several tool-side gaps. After fixing
those gaps and assuming semi-auto findings have been reviewed and accepted,
the tool now aligns with Micron's IQ3 non-manual checklist outcome: 109 exact
matches out of 112 comparable rows, with zero hard FAIL/ERROR disagreements.

## Source Artifacts

| Artifact | Path | Role |
|---|---|---|
| Micron completed checklist | `Micron/z41c-ibis/z41c_ibis_quality_checklist.xls` | Reference workbook completed by Micron for `z41c.ibs` and `z41c_it.ibs`. |
| Micron IBIS files | `Micron/z41c-ibis/z41c.ibs`, `Micron/z41c-ibis/z41c_it.ibs` | IBIS files being checked. |
| Previous generated evidence | `reports/micron/z41c.json`, `reports/micron/z41c.xlsx` | Baseline tool output before the follow-up fixes. |
| Current generated evidence | `reports/micron/z41c.json`, `reports/micron/z41c_it.json` | Regenerated output after fixes. |
| Detailed comparison notes | `docs/z41c-checklist-comparison.md`, `docs/z41c-post-review-vs-micron.md` | Supporting analysis used to prepare this report. |

# Part 1 - Previous Tool Result Compared With Micron

## Baseline Result

The previous generated workbook was useful as an engineering evidence report,
but it was not equivalent to Micron's completed checklist.

| Field | Micron completed checklist | Previous generated result |
|---|---|---|
| IBIS file scope | `z41c.ibs` and `z41c_it.ibs` | `z41c.ibs` only |
| Workbook style | Compact family-level checklist | Detailed per-component/per-model evidence workbook |
| Overall quality | `3MSX` | Candidate `IQ1` |
| IBISCHK version | 7.0.2 | 7.2.1 bundled with the tool |
| IBISCHK errors/warnings/cautions | 0 / 0 / 0 | 0 / 0 / 0 |
| Level coverage | IQ1-IQ3 rows | IQ1-IQ4 rows, including Composite Current and ISSO |
| Manual/review workflow | Human-filled PASS/NA/EXCEPTION | Manual items shown as `MANUAL REVIEW`; semi-auto findings shown as `REVIEW` |

Previous generated `z41c.ibs` summary:

| PASS | FAIL | WARN | NA | ERROR | Candidate |
|---:|---:|---:|---:|---:|---|
| 633 | 34 | 100 | 735 | 0 | IQ1 |

The IBISCHK result already agreed in substance. Both Micron and the tool found
zero parser errors. The lower generated candidate score was caused by tool
workflow and check-logic differences, not by IBISCHK failure.

## Workbook-Level Differences

| Area | Micron checklist | Previous generated workbook | Effect |
|---|---|---|---|
| Sheet structure | 6 sheets: summary, one component group, four model-family sheets | 50 sheets: summary, six components, 42 models, raw results | Generated output was traceable but harder to compare directly. |
| Model grouping | Families such as `DQ_*`, `DQS_*`, `DM_*`, `TDQS_*`, `ALERT_*` | One sheet per parsed model | Micron applied family-level judgement; the tool exposed every model-specific finding. |
| Manual checks | Human completed | Left as `MANUAL REVIEW` | Correct for automation purity, but it prevented matching Micron's completed checklist. |
| Semi-auto checks | Human accepted or marked exception | Reported as review warnings | Many differences were review workflow gaps, not deterministic failures. |
| Level 4 checks | Not present in model tabs | Included by default | Level 4 findings obscured comparison to an IQ3 report. |
| Exceptions/designators | `S`, `M`, and `X` captured in workbook | No accepted exception/correlation workflow | Tool could not reproduce `3MSX` as a final signed-off score. |

## Baseline Sheet-Level Status Comparison

For the previous comparison, generated `WARN` statuses are shown as `REVIEW`.

| Micron sheet | Micron statuses | Previous generated statuses | Main source of difference |
|---|---|---|---|
| `components(pkg)` | `PASS=8` | `PASS=5`, `FAIL=2`, `MANUAL REVIEW=1` | Bare-die pin RLC handling, input differential Tdelay rule, and one manual selector item. |
| `models(IO)` | `PASS=31`, `NA=9`, `EXCEPTION=1` | `PASS=19`, `MANUAL REVIEW=15`, `NA=3`, `REVIEW=2`, `FAIL=1`, `---=1` | Manual rows, semi-auto warnings, one near-zero current failure, and absent-row formatting. |
| `models(Input)` | `PASS=25`, `NA=16` | `PASS=8`, `MANUAL REVIEW=15`, `NA=13`, `REVIEW=2`, `---=3` | Manual rows plus roughness/leakage review triggers. |
| `models(Terminator)` | `PASS=13`, `NA=28` | `PASS=8`, `MANUAL REVIEW=15`, `NA=13`, `REVIEW=2`, `---=3` | Same pattern as input models. |
| `models(Open_drain)` | `PASS=24`, `NA=17` | `PASS=19`, `MANUAL REVIEW=15`, `NA=2`, `FAIL=1`, `REVIEW=1`, `---=3` | Manual rows, scalar `Vref` parsing gap, near-zero current threshold, and absent-row formatting. |

## Main Baseline Differences

| Item | Previous generated behavior | Why it differed from Micron |
|---|---|---|
| `3.2.2` bare-die pin RLC | Failed bare-die components with missing per-pin L/C values | Micron grouped packaged and bare-die components and accepted the set; bare-die package RLC completeness should not be treated like packaged pins. |
| `3.3.2` input differential Tdelay | Failed all components where input differential pins had `Tdelay_typ=0ns` values | Micron accepted these entries. The tool rule treated zero-valued delay as meaningful timing data; it should be pass-equivalent to no effective delay. |
| `5.6.2` ALERT Vref | Reported review because scalar `Vref` was not parsed | The IBIS file used assignment syntax: `Vref = 1200.000mV`. |
| `5.3.8`/`5.3.9` near-zero current | Failed currents slightly above `1 uA` | Micron accepted these microamp-level deviations. |
| Commented overshoot evidence | Treated commented dynamic overshoot rows as absent | Micron likely used comments or external evidence as acceptable documentation. |
| ISSO PU endpoint | Reported large endpoint mismatch on DQ/DQS models | The tool compared ISSO PU against the wrong pullup endpoint convention. |
| Absent/non-applicable rows | Some rows appeared as `---` instead of `NA` | Spreadsheet output was less checklist-like than Micron's workbook. |
| Level 4 findings | Included ISSO and Composite Current failures/reviews | Micron claimed IQ3 and did not include Level 4 rows in model sheets. |

## Baseline Conclusion

The previous tool output was not wrong as an evidence report, but it was not yet
calibrated to compare cleanly with a completed vendor IQ3 checklist. Most visible
differences fell into three categories:

- Tool bugs or overly strict logic that should be fixed.
- Semi-auto or manual review findings that need an accepted-review workflow.
- Report-format differences, especially Level 4 rows and `---` versus `NA`.

# Part 2 - Fixes Completed and New Comparison Result

## Fixes Implemented

The first improvement pass addressed the highest-confidence tool-side gaps:

| Area | Fix |
|---|---|
| Parser assignment syntax | Added support for scalar/TMM forms like `Vref = 1200.000mV`, receiver-threshold assignments, and `R_load = ...`. |
| Bare-die RLC | `3.2.2` now reports `NA` for detected bare-die components instead of failing per-pin package RLC completeness. |
| Differential input Tdelay | `3.3.2` now treats input-side `Tdelay_typ=0ns` as no effective delay and passes; missing/invalid `Vdiff` still fails and nonzero input `Tdelay` remains review evidence. |
| Near-zero I-V current | `5.3.8`/`5.3.9` now report any zero-current value outside the `1 uA` pass tolerance as review-required `WARN` instead of hard `FAIL`, because the spec allows special cases that may not cross zero current at 0 V. |
| Open model applicability | Open-drain/open-sink missing pullup rows and open-source missing pulldown rows now produce explicit `NA` where appropriate. |
| Commented overshoot evidence | Commented dynamic overshoot Model Spec rows are surfaced as semi-auto evidence for review. |
| ISSO PU endpoint | `5.7.1` now compares `Isso_pu(0)` against `Ipu(Vcc)`, matching the intended equation and Micron DQ/DQS data. |
| Target-level comparison mode | Added `--max-level` / `--target-level` filtering, explicit `NA` for no-result checklist rows, and optional GUI review-decision overlays. |

## Regenerated Tool Results

After the fixes, the regenerated Micron reports are:

| File | PASS | FAIL | WARN | NA | ERROR | Candidate |
|---|---:|---:|---:|---:|---:|---|
| `z41c.ibs` | 646 | 16 | 134 | 708 | 0 | IQ3 |
| `z41c_it.ibs` | 724 | 10 | 62 | 708 | 0 | IQ3 |

The raw candidate score is now `IQ3` because candidate scoring is based on the
highest implemented level with no `FAIL` or `ERROR`. Semi-auto warnings still
require review, manual rows are still not auto-passed, and Level 4 hard failures
prevent an IQ4 candidate unless they are resolved or documented.

## Current Semi-Auto Items Needing Review

The raw generated `z41c.ibs` report still contains semi-auto items that need
human review. These are not necessarily model defects. They are cases where the
tool can collect evidence, but a reviewer must decide whether the evidence is
acceptable for the technology, datasheet, extraction method, or intended IQ
claim.

| Check | Level | Count | Affected scope | Why review is still needed |
|---|---|---:|---|---|
| `3.4.2` `[Pin Mapping]` includes power and ground pins | LEVEL 4 | 3 | Bare-die components: `MT40A2G4Z41C`, `MT40A1G8Z41C`, `MT40A512M16Z41C` | `[Pin Mapping]` is absent for bare-die components; reviewer must confirm rail coverage is acceptable for the package/bare-die representation. |
| `5.2.8` D_Overshoot typ/min/max tracking | LEVEL 2 | 32 | DQ/DQS/DM/TDQS model families | Dynamic overshoot rows are present only as comments; reviewer must confirm those comments are intentional documentation and match datasheet limits. |
| `5.3.6` I-V stair-stepping | LEVEL 2 | 36 | DQ/DQS/DM/TDQS and related ODT/input families | POWER Clamp roughness is slightly above the heuristic threshold; plotted curves should be inspected to decide whether this is real stair-stepping or benign table shape. |
| `5.3.8` Pulldown zero/zero | LEVEL 2 | 1 | `ALERT` | Pulldown current at 0 V exceeds the `1 uA` pass tolerance; the spec allows special cases, so this is review evidence rather than a hard failure. |
| `5.3.9` Pullup zero/zero | LEVEL 2 | 2 | `DQ_40_3200`, `DQS_40_3200` | Pullup current at table voltage 0 V exceeds the `1 uA` pass tolerance; reviewer must decide whether the special-case allowance applies. |
| `5.3.10` Clamp leakage | LEVEL 2 | 36 | DQ/DQS/DM/TDQS and related ODT/input families | Clamp current at 0 V is nonzero; reviewer must decide whether the magnitude is acceptable leakage or indicates duplicated/incorrect behavior. |
| `5.7.4` ISSO sweep range | LEVEL 4 | 6 | `DQ_34_3200`, `DQ_40_3200`, `DQ_48_3200`, `DQS_34_3200`, `DQS_40_3200`, `DQS_48_3200` | ISSO voltage sweeps do not match the simple `0 V` to `Vcc` expectation; reviewer should confirm ISSO axis/range conventions for these DDR4 models. |
| `5.8.3` Composite Current time alignment | LEVEL 4 | 6 | DQ/DQS output models | V-T and Composite Current point counts differ; reviewer should inspect whether the timing grids are sufficiently aligned for the intended current waveform use. |
| `5.8.5` Composite Current endpoint correlation | LEVEL 4 | 6 | DQ/DQS output models | Composite Current endpoints need correlation review against pullup/pulldown behavior; the tool provides endpoint evidence but not a full physical correlation judgement. |
| `5.8.7` Composite Current edge flatness | LEVEL 4 | 6 | DQ/DQS output models | Composite Current start/end flatness is heuristic evidence; reviewer should inspect the waveform plots and extraction intent. |

For Micron's `3MSX` claim, the LEVEL 4 semi-auto rows are outside the claimed
IQ3 scope. The LEVEL 2 semi-auto rows still require review acceptance or
documented exception before the tool should report a final IQ3-equivalent score.

## Manual Items Not Completed by the Tool

The following manual checks are not completed by the automated tool. They were
ignored in the post-review comparison only to isolate deterministic tool
behavior against Micron's already signed-off checklist. In a real signoff flow,
each row needs reviewer evidence, comment, PASS/NA/EXCEPTION decision, and any
needed `M`, `S`, `G`, or `X` designator support.

| Check | Level | Manual decision still needed |
|---|---|---|
| `4.2` Default `[Model Selector]` entries are consistent | LEVEL 2 | Confirm selector defaults represent a plausible product configuration and intended default model choice. |
| `5.1.3` `[Temperature Range]` is reasonable | LEVEL 2 | Compare extraction temperature assumptions against datasheet operating limits and die-temperature interpretation. |
| `5.2.5` S_Overshoot subparameters match data sheet | LEVEL 2 | Compare static overshoot limits against datasheet functional overshoot requirements. |
| `5.2.7` D_Overshoot subparameters match data sheet | LEVEL 2 | Compare dynamic overshoot limits and conversion method against datasheet rules. |
| `5.3.11` I-V behavior not double-counted | LEVEL 2 | Review driver, clamp, and termination decomposition to confirm behavior is not duplicated across tables. |
| `5.3.12` On-die termination modeling documented | LEVEL 2 | Confirm ODT existence, modeling method, and documentation are sufficient for the represented product modes. |
| `5.2.1` `[Model]` Vinl/Vinh reasonable | LEVEL 3 | Compare threshold values against datasheet thresholds and Vmeas intent. |
| `5.2.2` `[Model Spec]` Vinl/Vinh reasonable | LEVEL 3 | Compare threshold ranges against datasheet values and supply-variation interpretation. |
| `5.2.3` `[Model Spec]` hysteresis/edge thresholds complete and reasonable | LEVEL 3 | Decide whether hysteresis or edge-specific thresholds are required, then compare to datasheet intent. |
| `5.2.9` `[Receiver Thresholds]` Vth present and matches data sheet, if needed | LEVEL 3 | Decide whether receiver thresholds are needed for the I/O standard and compare Vth against datasheet timing thresholds. |
| `5.2.10` `[Receiver Thresholds]` Vth_min/Vth_max match data sheet, if needed | LEVEL 3 | Compare threshold tolerance against datasheet typical/min/max interpretation. |
| `5.2.11` `[Receiver Thresholds]` Vinh_ac/Vinl_ac match data sheet, if needed | LEVEL 3 | Convert and compare AC thresholds using the correct offset/reference convention. |
| `5.2.12` `[Receiver Thresholds]` Vinh_dc/Vinl_dc match data sheet, if needed | LEVEL 3 | Convert and compare DC thresholds using the correct offset/reference convention. |
| `5.2.13` `[Receiver Thresholds]` Tslew_ac/Tdiffslew_ac match data sheet, if needed | LEVEL 3 | Compare slew-limit values against applicable single-ended or differential receiver requirements. |
| `5.2.14` Threshold_sensitivity and Ext_ref match data sheet, if needed | LEVEL 3 | Confirm reference-supply behavior and threshold sensitivity requirements from datasheet or I/O standard. |
| `5.6.1` Vmeas/Vref used if typ/min/max variation exists | LEVEL 3 | Decide whether Vmeas/Vref should vary across corners and confirm `[Model Spec]` represents that variation when needed. |
| `3.1.3` Package model includes power and ground pins | LEVEL 4 | Review package topology, coupling, and external package-model files to confirm power/ground pins are represented. |
| `3.1.4` On-die and on-package decoupling included | LEVEL 4 | Review PDN/extraction evidence and decide whether decoupling representation is sufficient. |
| `5.8.4` Composite Current includes pre-driver behavior | LEVEL 4 | Review circuit/extraction evidence to confirm pre-driver current is included when relevant. |
| `5.8.6` Composite Current data includes current from correct voltage rails | LEVEL 4 | Review extraction documentation and rail aggregation to confirm the correct supply rails are included or excluded. |

## Post-Review Comparison Assumption

To compare the current tool with Micron's completed IQ3 checklist, the following
assumption was applied:

- All semi-auto findings are considered reviewed and accepted.
- Manual check items are ignored for this comparison.
- Blank Micron PASS/FAIL cells are treated as `NA`.
- Generated `z41c.ibs` and `z41c_it.ibs` are aggregated to match Micron's workbook scope.
- Level 4 findings are separated because Micron's workbook claims IQ3, not IQ4.

Effective generated status mapping:

| Generated status | Effective comparison status |
|---|---|
| `PASS` | `PASS` |
| `NA` | `NA` |
| Semi-auto/review `WARN` | `PASS` |
| Auto `FAIL`/`ERROR` | unchanged |
| Manual row | ignored |

## New Comparison Result

Under the post-review IQ3-scope assumption, the generated results now align with
Micron's completed checklist on all hard gating rows.

| Metric | Count |
|---|---:|
| Comparable non-manual rows | 112 |
| Exact status matches | 109 |
| Non-blocking PASS vs EXCEPTION differences | 1 |
| PASS vs NA applicability/status-convention differences | 2 |
| Hard FAIL/ERROR disagreements | 0 |

Effective Level 1-3 generated-result view:

| File | Effective PASS | Effective NA | Blocking FAIL/WARN/ERROR |
|---|---:|---:|---:|
| `z41c.ibs` | 667 | 454 | 0 |
| `z41c_it.ibs` | 667 | 454 | 0 |

Sheet-level comparison:

| Micron sheet | Comparable rows | Exact matches | Non-blocking differences | Applicability/status differences | Hard disagreements |
|---|---:|---:|---:|---:|---:|
| `summary` | 1 | 1 | 0 | 0 | 0 |
| `components(pkg)` | 7 | 7 | 0 | 0 | 0 |
| `models(IO)` | 26 | 24 | 1 | 1 | 0 |
| `models(Input)` | 26 | 25 | 0 | 1 | 0 |
| `models(Terminator)` | 26 | 26 | 0 | 0 | 0 |
| `models(Open_drain)` | 26 | 26 | 0 | 0 | 0 |

## Remaining Differences After Fixes

Only three non-hard differences remain in the IQ3-scope comparison:

| Sheet | Check | Micron | Tool effective result | Explanation |
|---|---|---|---|---|
| `models(IO)` | `5.2.6` | `PASS` | `NA` | The tool finds no complete parsed `S_overshoot_high`/`S_overshoot_low` typ/min/max data, so it treats tracking as not applicable. Micron marks PASS, likely based on product-context judgement that separate S_Overshoot tracking was not needed. |
| `models(Input)` | `5.2.6` | `PASS` | `NA` | Same PASS-vs-NA policy difference for the input-family sheet. |
| `models(IO)` | `5.4.3` | `EXCEPTION` | `PASS` | Micron records an exception for long V-T duration due to included Composite Current I-t data. The tool's threshold passes the row, so no exception is required by the generated evidence. Both outcomes are non-blocking. |

These are not hard disagreements. They point to review-overlay polish: the tool
should allow reviewers to record PASS-vs-NA policy decisions and exceptions even
when the generated check itself passes.

## Level 4 Note

Micron's workbook claims `3MSX`; it does not claim IQ4. If the tool's Level 4
checks are included anyway, the remaining automatic failures are:

| File | Level 4 blocking failures | Check IDs |
|---|---:|---|
| `z41c.ibs` | 16 | `5.8.8` x12, `5.7.1` x2, `5.8.1` x2 |
| `z41c_it.ibs` | 10 | `5.8.8` x6, `5.7.1` x2, `5.8.1` x2 |

These do not contradict Micron's IQ3 report. They are the next area to resolve
only if the goal is IQ4 assessment.

## Final Interpretation

Before the fixes, the generated output looked much worse than Micron's checklist
because tool bugs, strict thresholds, review workflow gaps, and Level 4 rows were
mixed together in one report.

After the fixes, and under the assumption that semi-auto findings are reviewed
and accepted, the tool reproduces Micron's IQ3 non-manual checklist result with
no hard disagreements. The remaining work is not primarily more IQ3 automation;
it is reviewer workflow and report presentation:

- Store accepted PASS/NA decisions for rows that are not currently warnings.
- Store exceptions and `S`/`M`/`X` designator evidence.
- Provide a vendor-style grouped spreadsheet/report mode in addition to the
  current detailed evidence workbook.
- Keep Level 4 checks available, but use `--max-level 3` for IQ3 reports so Level 4 checks are not run or reported.
