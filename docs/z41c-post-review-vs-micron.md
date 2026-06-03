# z41c Post-Review Comparison Against Micron Checklist

Comparison date: 2026-06-01

## Purpose

This document compares the current `ibis_qa_tool` results against Micron's completed
`z41c_ibis_quality_checklist.xls` under a review-complete assumption:

- All semi-auto findings are assumed reviewed and accepted.
- Manual check items are excluded from the comparison.
- Blank PASS/FAIL cells in Micron's workbook are treated as `NA`, matching the workbook's checklist usage.
- Micron's workbook covers both `z41c.ibs` and `z41c_it.ibs`; the generated comparison aggregates both `reports/micron/z41c.json` and `reports/micron/z41c_it.json`.
- Because Micron's workbook assigns `3MSX` and its model tabs stop at IQ3, Level 4 generated findings are reported separately.

## Effective Result Policy

For generated results, the comparison uses this effective status mapping:

| Generated result | Effective status |
|---|---|
| `PASS` | `PASS` |
| `NA` | `NA` |
| `WARN` from semi-auto or review-required evidence | `PASS` |
| `FAIL`/`ERROR` from auto checks | unchanged |
| Manual check item | ignored |

For grouped Micron sheets, generated per-component and per-model results are aggregated
to one status per checklist row. Any auto `FAIL` wins. Otherwise, any applicable
`PASS` wins over `NA`; if all scoped generated results are `NA` or absent, the row is
`NA`.

## Summary

Under this assumption, the generated IQ3-scope results agree with Micron's checklist
on all hard gating rows.

| Metric | Count |
|---|---:|
| Comparable non-manual rows | 112 |
| Exact status matches | 109 |
| Non-blocking PASS vs EXCEPTION difference | 1 |
| PASS vs NA applicability/status-convention differences | 2 |
| Hard FAIL/ERROR disagreements | 0 |

At the generated-result level, both files have no Level 1-3 blockers after accepting
semi-auto findings and ignoring manual items:

| File | Effective PASS | Effective NA | Blocking FAIL/WARN/ERROR |
|---|---:|---:|---:|
| `z41c.ibs` | 667 | 454 | 0 |
| `z41c_it.ibs` | 667 | 454 | 0 |

This supports Micron's IQ3-level quality conclusion for the implemented
non-manual checks. It does not independently prove Micron's `S`, `M`, or `X`
designators, because those depend on manual correlation/exception evidence.

## Sheet-Level Comparison

| Micron sheet | Comparable rows | Exact matches | Non-blocking differences | Applicability/status differences | Hard disagreements |
|---|---:|---:|---:|---:|---:|
| `summary` | 1 | 1 | 0 | 0 | 0 |
| `components(pkg)` | 7 | 7 | 0 | 0 | 0 |
| `models(IO)` | 26 | 24 | 1 | 1 | 0 |
| `models(Input)` | 26 | 25 | 0 | 1 | 0 |
| `models(Terminator)` | 26 | 26 | 0 | 0 | 0 |
| `models(Open_drain)` | 26 | 26 | 0 | 0 | 0 |

## Remaining Row Differences

| Sheet | Check | Micron | Generated effective | Difference type | Explanation |
|---|---|---|---|---|---|
| `models(IO)` | `5.2.6` | `PASS` | `NA` | Applicability/status convention | The tool finds no complete parsed `S_overshoot_high`/`S_overshoot_low` typ/min/max data, so it treats tracking as not applicable. Micron marks the row PASS, likely after product-context review that no separate S_Overshoot tracking data was needed. |
| `models(Input)` | `5.2.6` | `PASS` | `NA` | Applicability/status convention | Same as above for the input-family sheet. This is not a numeric disagreement; it is a PASS-vs-NA policy difference. |
| `models(IO)` | `5.4.3` | `EXCEPTION` | `PASS` | Non-blocking difference | Micron explicitly records an exception that V-T length is long due to included Composite Current I-t data. The tool's current duration threshold passes these rows, so it does not require an exception. Both outcomes are non-blocking for IQ3. |

## Level 4 Note

Micron's workbook is an IQ3 checklist and does not include Level 4 model rows.
If generated Level 4 checks are included, remaining automatic failures are:

| File | Level 4 blocking failures | Check IDs |
|---|---:|---|
| `z41c.ibs` | 16 | `5.8.8` x12, `5.7.1` x2, `5.8.1` x2 |
| `z41c_it.ibs` | 10 | `5.8.8` x6, `5.7.1` x2, `5.8.1` x2 |

These are not contradictions with Micron's `3MSX` report because IQ4 is not claimed
there. They are the next items to resolve if the tool is used to assess an IQ4 target.

## Interpretation

With all semi-auto review items accepted and manual rows excluded, our generated
results essentially reproduce Micron's IQ3 checklist outcome. The only remaining
differences are:

- A PASS-vs-NA interpretation for S_Overshoot tracking (`5.2.6`).
- A missing exception annotation for a row the tool passes (`5.4.3`).

The practical improvement is not more auto checking for IQ3; it is review-overlay
polish: allow reviewers to mark PASS/NA policy decisions for non-warning rows and
record exceptions/designators even when the generated evidence already passes.
