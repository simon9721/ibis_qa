# Implemented IBIS Quality Checks

This document describes the checks that are currently implemented by
`ibis_qa_tool`, item by item. It covers every check item whose automation class
in `data/ibis_quality_spec_3_0.json` is `auto` or `semi_auto`.

It is intentionally implementation-focused. The generated catalog documents
explain the IBIS Quality Specification plan; this document explains what the
Python tool actually does today, including thresholds, result severity, review
flags, and known judgement calls.

## Current Coverage

The runner currently registers all auto and semi-auto items from the structured
spec data:

| Automation class | Spec items | Implemented / registered | Current implementation style |
|---|---:|---:|---|
| `auto` | 22 | 22 | Deterministic parser, numeric, or external-tool checks |
| `semi_auto` | 25 | 25 | Evidence collection plus reviewer-facing warnings where judgement is needed |
| Total | 47 | 47 | No auto or semi-auto item is missing from the runner |

Manual and optional checks are not described here except where an implemented
semi-auto check explicitly produces evidence for later manual review.

## Result Semantics

| Status | Meaning in the tool |
|---|---|
| `PASS` | The implemented rule or evidence test is satisfied. |
| `FAIL` | A deterministic auto rule is violated. |
| `WARN` | A soft or semi-auto finding needs reviewer attention. For most semi-auto items this is paired with `review_required=true`. |
| `NA` | The item does not apply to the checked object, or the needed section is absent in a way that makes the item not applicable. |
| `ERROR` | The checker could not complete the check because of tool execution, missing required data, or malformed table data. |

For semi-auto checks, `WARN` does not mean the IBIS model is automatically
wrong. It means the tool found evidence that needs engineering judgement,
external data, technology context, or visual review.

## Common Implementation Details

| Area | Threshold or rule | Source |
|---|---|---|
| Package L limit | 100 nH | `PKG_L_MAX_H` |
| Package C limit | 100 pF | `PKG_C_MAX_F` |
| Package R limit | 10 ohm | `PKG_R_MAX_OHM` |
| Pin delay estimate | `TD = sqrt(L * C)`, max 300 ps | `PIN_TD_MAX_S` |
| Pin impedance estimate | `Z0 = sqrt(L / C)`, max 100 ohm | `PIN_Z0_MAX_OHM` |
| I-V sweep endpoint tolerance | 2 percent of expected sweep span | `IV_RANGE_TOLERANCE` |
| I-V and ISSO typ/min/max current order tolerance | max of 1 nA and 1 percent of current magnitude | `IV_ORDER_ABS_TOL_A`, `IV_ORDER_REL_TOL` |
| I-V monotonicity tolerance | 1 nA | `MONO_TOLERANCE_A` |
| Pulldown/Pullup zero-crossing tolerance | 1 uA | `ZERO_CROSS_TOL_A` |
| Pulldown/Pullup zero-crossing review reference | above 1 uA | `ZERO_CROSS_TOL_A` |
| Minimum I-V, ISSO, and waveform point count evidence | 20 points | `MIN_TABLE_POINTS`, `MIN_WAVEFORM_POINTS` |
| I-V stair-step evidence threshold | max adjacent typ-current step greater than 10 percent of current span | `STAIRSTEP_REVIEW_THRESHOLD` |
| Clamp leakage evidence threshold | 1 uA at 0 V | `CLAMP_LEAKAGE_TOL_A` |
| V-T endpoint evidence threshold | 20 mV from `V_fixture` | `VT_ENDPOINT_TOL_V` |
| V-T duration evidence threshold | 1 us | `VT_DURATION_MAX_S` |
| Ramp dV load-line tolerance | 5 percent | `RAMP_DV_TOLERANCE` |
| Ramp dV fraction | 60 percent of load-line voltage swing | `RAMP_DV_FRACTION` |
| Ramp dt vs V-T 20%-80% tolerance | 20 percent relative difference | implemented in `c5_semiauto_wave_quality.py` |
| ISSO endpoint tolerance | 2 percent | `ISSO_ENDPOINT_TOL` |
| Composite Current time match tolerance | 1 fs | `TIME_MATCH_TOL_S` |
| Composite Current zero endpoint tolerance | 1 uA | `CC_ZERO_TOL_A` |
| Composite Current edge flatness threshold | 1 uA adjacent edge delta | `CC_FLAT_SLOPE_TOL_A` |

## Implementation Inventory

| Check IDs | Module | Main scope |
|---|---|---|
| `2.1` | `checks/c2_1_ibischk.py` | File |
| `3.1.1`, `3.1.2` | `checks/c3_1_package.py` | Component |
| `3.2.1`, `3.4.2`, `4.1` | `checks/c3_semiauto_structural.py` | Component / file |
| `3.2.2`, `3.3.1`, `3.3.2`, `3.4.1`, `3.4.3` | `checks/c3_component_structural.py` | Component / package model |
| `5.1.1`, `5.2.6`, `5.2.8`, `5.5.2`, `5.7.2` | `checks/c5_semiauto_ordering.py` | Model |
| `5.1.2`, `5.1.4`, `5.3.6`, `5.3.10`, `5.3.14`, `5.4.1`, `5.4.2`, `5.4.3`, `5.4.4`, `5.5.4`, `5.6.2`, `5.7.3`, `5.7.4`, `5.8.3`, `5.8.5`, `5.8.7` | `checks/c5_semiauto_wave_quality.py` | Model |
| `5.3.1`, `5.3.2`, `5.3.3`, `5.3.4`, `5.3.5`, `5.3.7`, `5.3.8`, `5.3.9`, `5.3.13` | `checks/c5_3_iv_tables.py` | Model |
| `5.5.1`, `5.5.3`, `5.8.1`, `5.8.2`, `5.8.8` | `checks/c5_ramp_waveform.py` | Model / waveform |
| `5.7.1` | `checks/c5_7_isso.py` | Model |

## Level 1

### 2.1 - IBIS file passes IBISCHK

- Automation class: `auto`
- IQ level: `LEVEL 1`
- Module: `checks/c2_1_ibischk.py`
- Scope: file
- Inputs used: raw IBIS file path, parsed `[IBIS Ver]`, raw comment/notes text, local IBISCHK executable if available.

What the tool checks:

- Searches the parsed file metadata for an existing `|IQ Score:` tag.
- Searches the parsed file metadata for in-file IBISCHK version documentation.
- Finds an IBISCHK executable from PATH names such as `ibischk`, `ibischk7`, `ibischk7_64`, or repo-local bundles such as `ibischk721_win_64/ibischk7_64.exe`.
- Runs IBISCHK against the IBIS file with a 60 second timeout.
- Counts `ERROR` and `WARNING` tokens in IBISCHK stdout/stderr.
- Records full IBISCHK stdout/stderr in JSON under `result.data.ibischk.output`, along with executable path, return code, parsed version, error count, warning count, and caution count.

Result behavior:

- `PASS`: existing IQ score tag found, or missing IQ score tag is reported as a non-blocking writeback note.
- `PASS`: existing IBISCHK version documentation found, or missing in-file IBISCHK version documentation is reported as a non-blocking documentation note.
- `PASS`: IBISCHK executes and reports zero errors. Warnings are counted in the message but do not currently fail Level 1.
- `FAIL`: IBISCHK executes and reports one or more errors.
- `WARN`: no IBISCHK executable can be found, so execution is skipped.
- `ERROR`: IBISCHK times out or raises an execution exception.

Judgement calls:

- Missing `|IQ Score:` is not a failure because the tool's purpose is to help assign the score.
- Missing in-file IBISCHK version documentation is not a Level 1 blocker.
- IBISCHK warnings are reported but not automatically failed. The spec can require documentation and an `X` designator for unresolved warnings; that judgement is not fully automated here.

## Level 2

### 3.1.1 - [Package] must have typ/min/max values

- Automation class: `auto`
- IQ level: `LEVEL 2`
- Module: `checks/c3_1_package.py`
- Scope: component
- Inputs used: parsed `[Component]` and `[Package]` R/L/C tuples.

What the tool checks:

- For each component, reads `R_pkg`, `L_pkg`, and `C_pkg`.
- Requires typ, min, and max values for all three package parameters.
- Detects bare-die components using very small package stub values and treats this check as not applicable for those components.

Result behavior:

- `PASS`: all package R/L/C fields have typ, min, and max values.
- `FAIL`: any package parameter is missing one or more typ/min/max values.
- `NA`: component is detected as bare die.

Judgement calls:

- Bare-die components are assumed to intentionally use package stub values.

### 3.1.2 - [Package] model values must be reasonable

- Automation class in spec data: `semi_auto`
- Current module behavior: numeric auto portion in `checks/c3_1_package.py`
- IQ level: `LEVEL 2`
- Scope: component
- Inputs used: parsed `[Package]` R/L/C tuples.

What the tool checks:

- Applies hard numeric review limits to package typ values:
  - `R_pkg` typ must be no more than 10 ohm.
  - `L_pkg` typ must be no more than 100 nH.
  - `C_pkg` typ must be no more than 100 pF.
- Checks typ/min/max order for each complete tuple using `min <= typ <= max`.
- Skips missing typ values inside this check because check `3.1.1` owns completeness.
- Marks bare-die components as not applicable.

Result behavior:

- `PASS`: all available package typ values are under limits and all complete tuples satisfy `min <= typ <= max`.
- `FAIL`: package typ value exceeds the configured limit, or min/typ/max ordering is violated.
- `NA`: component is detected as bare die.

Judgement calls and limitations:

- The spec classifies this as semi-auto because true package reasonableness depends on package style and modeling assumptions.
- The tool implements the deterministic numeric portion only. It does not independently review whether the package topology or modeling method is appropriate.
- Because this lives in the package auto module today, generated result entries may appear as `automation_class="auto"` even though the spec data class is `semi_auto`.

### 3.2.1 - [Pin] section complete

- Automation class: `semi_auto`
- IQ level: `LEVEL 2`
- Module: `checks/c3_semiauto_structural.py`
- Scope: component
- Inputs used: parsed `[Pin]` entries, parsed `[Model]` names, raw `[Model Selector]` sections.

What the tool checks:

- Confirms each component has parsed pin entries.
- For each pin, checks that pin name, signal name, and model name are present.
- Treats `POWER`, `GND`, `NC`, and `CIRCUITCALL` as reserved model names that do not need a parsed `[Model]`.
- Accepts model names that resolve either to a parsed `[Model]` or to an entry in a parsed `[Model Selector]`.

Result behavior:

- `PASS`: pins exist and every non-reserved model reference can be resolved.
- `WARN` with `review_required=true`: pin section is missing/empty, required fields are blank, or a non-reserved model reference cannot be resolved.

Judgement calls:

- This is semi-auto because pin list completeness ultimately depends on the package/pinout source. The tool can detect obvious structural gaps but cannot prove the pinout matches the datasheet.

### 3.3.1 - [Diff Pin] referenced pin models match

- Automation class: `auto`
- IQ level: `LEVEL 2`
- Module: `checks/c3_component_structural.py`
- Scope: component
- Inputs used: parsed `[Pin]` entries, parsed `[Diff Pin]` entries, raw comment lines near `[Diff Pin]`.

What the tool checks:

- If a component has no `[Diff Pin]` section, the check is not applicable.
- Builds a pin-to-model lookup from the component `[Pin]` section.
- For each differential pin pair, compares the two referenced pin model names.
- If model names differ, searches raw comment lines near the `[Diff Pin]` section for either pin name as an explanation indicator.

Result behavior:

- `PASS`: all differential pairs use matching model names, or mismatches have nearby explanatory comments.
- `FAIL`: one or more differential pairs use different model names and no nearby explanatory comment is found.
- `NA`: no `[Diff Pin]` section exists for the component.

Judgement calls:

- The comment search is intentionally lightweight. It detects that an explanation appears to exist, but it does not judge the technical quality of that explanation.

### 4.1 - [Model Selector] entries have reasonable descriptions

- Automation class: `semi_auto`
- IQ level: `LEVEL 2`
- Module: `checks/c3_semiauto_structural.py`
- Scope: file
- Inputs used: raw `[Model Selector]` sections.

What the tool checks:

- Parses each raw `[Model Selector]` section.
- Captures each model name and the remaining text on the row as the description.
- Flags weak descriptions if they are blank, shorter than four characters, or equal to generic words such as `na`, `n/a`, `none`, `default`, or `model`.

Result behavior:

- `PASS`: every selector entry has a non-trivial description.
- `WARN` with `review_required=true`: one or more selector descriptions are weak or missing.
- `NA`: no `[Model Selector]` sections are parsed.

Judgement calls:

- The tool checks description presence and obvious weakness. A reviewer still decides whether the description is useful enough for model users.

### 5.1.1 - [Model] parameters have correct typ/min/max order

- Automation class: `semi_auto`
- IQ level: `LEVEL 2`
- Module: `checks/c5_semiauto_ordering.py`
- Scope: model
- Inputs used: parsed model scalar tuples.

What the tool checks:

- Evaluates complete typ/min/max tuples for:
  - `C_comp`
  - `C_comp_pullup`
  - `C_comp_pulldown`
  - `C_comp_power_clamp`
  - `C_comp_gnd_clamp`
  - `Voltage Range`
  - `Temperature Range`
  - `Pullup Reference`
  - `Pulldown Reference`
  - `POWER Clamp Reference`
  - `GND Clamp Reference`
- Uses numeric ordering with tolerance: if max-min is within tolerance, the tuple is treated as an overlay and accepted.
- Otherwise flags tuples where typ is below min or above max beyond tolerance.

Result behavior:

- `PASS`: one or more complete tuples are present and all have acceptable order.
- `WARN` with `review_required=true`: any complete tuple appears out of order.
- `NA`: no complete typ/min/max parameter tuples are parsed.

Judgement calls:

- This is evidence only. Some technologies or extraction flows may intentionally produce unusual corner relationships and need reviewer confirmation.

### 5.1.2 - [Model] C_comp is reasonable

- Automation class: `semi_auto`
- IQ level: `LEVEL 2`
- Module: `checks/c5_semiauto_wave_quality.py`
- Scope: model
- Inputs used: parsed C_comp-related tuples.

What the tool checks:

- Looks at available typ/min/max values for:
  - `C_comp`
  - `C_comp_pullup`
  - `C_comp_pulldown`
  - `C_comp_power_clamp`
  - `C_comp_gnd_clamp`
- Flags any negative capacitance value.
- Flags any capacitance value above the current 20 pF review threshold.

Result behavior:

- `PASS`: at least one C_comp field is present, all parsed values are non-negative, and all are at or below 20 pF.
- `WARN` with `review_required=true`: any negative value or value above 20 pF is found.
- `NA`: no C_comp values are parsed.

Judgement calls:

- The 20 pF threshold is a review trigger, not a universal physical limit. Large devices can legitimately exceed it.

### 5.1.4 - [Voltage Range] or [* Reference] is reasonable

- Automation class: `semi_auto`
- IQ level: `LEVEL 2`
- Module: `checks/c5_semiauto_wave_quality.py`
- Scope: model
- Inputs used: parsed voltage and reference tuples.

What the tool checks:

- Reviews values parsed from:
  - `Voltage Range`
  - `Pullup Reference`
  - `Pulldown Reference`
  - `POWER Clamp Reference`
  - `GND Clamp Reference`
- Resolves IBIS default relationships before judging the values:
  - `Pullup Reference` defaults to `Voltage Range` when absent.
  - `Pulldown Reference` and `GND Clamp Reference` default to 0 V when absent.
  - `POWER Clamp Reference` defaults to `Voltage Range` when absent.
- Reports each resolved tuple and whether it was explicit or defaulted.
- Checks complete typ/min/max tuples for basic order.
- For `Voltage Range`, `Pullup Reference`, and `POWER Clamp Reference`, flags non-positive supply/reference values.
- Flags `Pullup Reference` or `POWER Clamp Reference` typ values that differ materially from `Voltage Range` typ.

Result behavior:

- `PASS`: at least one voltage/reference set is parsed and no basic polarity issue is found.
- `WARN` with `review_required=true`: a positive-supply/reference field is zero or negative, a tuple is out of order, or a positive reference does not match the resolved voltage-range nominal value.
- `NA`: no voltage/reference values are parsed.

Judgement calls:

- The tool checks consistency and polarity inside the IBIS file. It does not compare against datasheet supply ranges.

### 5.2.6 - [Model Spec] S_Overshoot subparameters track typ/min/max

- Automation class: `semi_auto`
- IQ level: `LEVEL 2`
- Module: `checks/c5_semiauto_ordering.py`
- Scope: model
- Inputs used: parsed `[Model Spec]` S_overshoot tuples.

What the tool checks:

- If `[Model Spec]` is absent, the check is not applicable.
- Checks complete typ/min/max tuples for:
  - `S_overshoot_high`
  - `S_overshoot_low`
- Applies the same typ/min/max ordering tolerance used by other numeric semi-auto order checks.

Result behavior:

- `PASS`: one or more complete S_Overshoot tuples are present and ordered.
- `WARN` with `review_required=true`: any complete tuple appears out of order.
- `NA`: no `[Model Spec]` exists or no complete S_Overshoot tuple is parsed.

Judgement calls:

- The tool checks numeric tracking only. It does not confirm overshoot limits against a datasheet.

### 5.2.8 - [Model Spec] D_Overshoot_* subparameters track typ/min/max

- Automation class: `semi_auto`
- IQ level: `LEVEL 2`
- Module: `checks/c5_semiauto_ordering.py`
- Scope: model
- Inputs used: parsed `[Model Spec]` D_overshoot tuples and commented D_overshoot evidence rows.

What the tool checks:

- If `[Model Spec]` is absent, the check is not applicable unless commented D_overshoot evidence rows are found under the current model.
- Checks complete typ/min/max tuples for:
  - `D_overshoot_high`
  - `D_overshoot_low`
  - `D_overshoot_time`
- Also scans comment lines for vendor-style dynamic overshoot evidence such as `D_overshoot_ampl_h`, `D_overshoot_ampl_l`, `D_overshoot_area_h`, and `D_overshoot_area_l`.
- Applies the same typ/min/max ordering tolerance used by other numeric semi-auto order checks.

Result behavior:

- `PASS`: one or more complete D_Overshoot tuples are present and ordered.
- `WARN` with `review_required=true`: any complete tuple appears out of order.
- `WARN` with `review_required=true`: only commented dynamic overshoot rows are found; these are evidence for reviewer confirmation, not parsed IBIS data.
- `NA`: no `[Model Spec]` exists or no complete D_Overshoot tuple is parsed.

Judgement calls:

- The tool checks numeric tracking only. It does not compare dynamic overshoot limits or conversion method against the datasheet.

### 5.3.1 - I-V tables have correct typ/min/max order

- Automation class: `auto`
- IQ level: `LEVEL 2`
- Module: `checks/c5_3_iv_tables.py`
- Scope: model / I-V table
- Inputs used: parsed `[Pulldown]`, `[Pullup]`, `[GND Clamp]`, and `[POWER Clamp]` rows.

What the tool checks:

- For every present I-V table, verifies that the table is non-empty.
- For each row, requires at least four parsed numeric columns: voltage, typ current, min current, and max current.
- For `[Pulldown]` and `[Pullup]`, checks active-region current ordering only where `0 < voltage < Vcc`.
- Compares absolute currents so that source/sink sign conventions do not by themselves create false failures.
- Treats nearly overlaid corners as acceptable if the absolute spread is within max of 1 nA and 1 percent of current magnitude.
- Flags active-region rows where `|typ|` is below `|min|` or `|max|` is below `|typ|` beyond tolerance.

Result behavior:

- `PASS`: table rows have the required columns and active-region ordering is clean.
- `FAIL`: a row is malformed, or active-region `[Pulldown]`/`[Pullup]` current ordering is violated.
- `ERROR`: a present table has no rows.

Judgement calls:

- Clamp table row shape is checked, but active-region corner ordering is only applied to `[Pulldown]` and `[Pullup]`.
- The code contains a branch for clamp-region crossover warnings, but because ordering is currently skipped for clamp tables, that branch is not normally reached.

### 5.3.2 - [Pullup] voltage sweep range is correct

- Automation class: `auto`
- IQ level: `LEVEL 2`
- Module: `checks/c5_3_iv_tables.py`
- Scope: model / `[Pullup]`
- Inputs used: parsed `[Pullup]` rows and resolved Vcc.

What the tool checks:

- For models with a `[Pullup]` table and a resolvable Vcc, checks that voltage coverage extends approximately from `-Vcc` to `2 * Vcc`.
- Allows endpoint shortfall up to 2 percent of the expected sweep span.
- For input-only models without `[Pullup]`, reports not applicable.

Result behavior:

- `PASS`: sweep coverage reaches the expected low and high ends within tolerance.
- `FAIL`: low or high endpoint coverage is insufficient.
- `ERROR`: present `[Pullup]` table is empty.
- `NA`: input-type model has no `[Pullup]`.

Judgement calls:

- If Vcc cannot be resolved, no result is emitted for this specific check.

### 5.3.3 - [Pulldown] voltage sweep range is correct

- Automation class: `auto`
- IQ level: `LEVEL 2`
- Module: `checks/c5_3_iv_tables.py`
- Scope: model / `[Pulldown]`
- Inputs used: parsed `[Pulldown]` rows and resolved Vcc.

What the tool checks:

- For models with a `[Pulldown]` table and a resolvable Vcc, checks that voltage coverage extends approximately from `-Vcc` to `2 * Vcc`.
- Allows endpoint shortfall up to 2 percent of the expected sweep span.
- For input-only models without `[Pulldown]`, reports not applicable.

Result behavior:

- `PASS`: sweep coverage reaches the expected low and high ends within tolerance.
- `FAIL`: low or high endpoint coverage is insufficient.
- `ERROR`: present `[Pulldown]` table is empty.
- `NA`: input-type model has no `[Pulldown]`.

Judgement calls:

- If Vcc cannot be resolved, no result is emitted for this specific check.

### 5.3.4 - [POWER Clamp] voltage sweep range is correct

- Automation class: `auto`
- IQ level: `LEVEL 2`
- Module: `checks/c5_3_iv_tables.py`
- Scope: model / `[POWER Clamp]`
- Inputs used: parsed `[POWER Clamp]` rows and resolved power-clamp Vcc.

What the tool checks:

- For models with a `[POWER Clamp]` table and a resolvable power-clamp reference, checks that voltage coverage extends approximately from `-Vcc` to `2 * Vcc`.
- Allows endpoint shortfall up to 2 percent of expected sweep span.

Result behavior:

- `PASS`: sweep coverage reaches the expected low and high ends within tolerance.
- `FAIL`: low or high endpoint coverage is insufficient.
- `ERROR`: present `[POWER Clamp]` table is empty.

Judgement calls:

- The tool intentionally enforces the stronger project policy of `-Vcc` to `2 * Vcc` for clamp tables so the same range expectation is applied to all I-V tables.
- If the table or reference voltage is absent, no result is emitted for this check.

### 5.3.5 - [GND Clamp] voltage sweep range is correct

- Automation class: `auto`
- IQ level: `LEVEL 2`
- Module: `checks/c5_3_iv_tables.py`
- Scope: model / `[GND Clamp]`
- Inputs used: parsed `[GND Clamp]` rows and resolved power-clamp Vcc.

What the tool checks:

- For models with a `[GND Clamp]` table and a resolvable reference, checks that voltage coverage extends approximately from `-Vcc` to `2 * Vcc`.
- Allows endpoint shortfall up to 2 percent of the expected sweep span.

Result behavior:

- `PASS`: sweep coverage reaches the expected low and high ends within tolerance.
- `FAIL`: low or high endpoint coverage is insufficient.
- `ERROR`: present `[GND Clamp]` table is empty.

Judgement calls:

- If the table or reference voltage is absent, no result is emitted for this check.

### 5.3.6 - I-V tables do not exhibit stair-stepping

- Automation class: `semi_auto`
- IQ level: `LEVEL 2`
- Module: `checks/c5_semiauto_wave_quality.py`
- Scope: model / I-V table set
- Inputs used: parsed I-V table typ current columns.

What the tool checks:

- Computes a roughness ratio for each present I-V table:
  - current span = max typ current - min typ current.
  - largest adjacent step = max absolute difference between adjacent typ currents.
  - roughness ratio = largest adjacent step / absolute current span.
- Flags any table whose roughness ratio is greater than 0.10.
- Tables with fewer than three usable current points do not produce roughness evidence.

Result behavior:

- `PASS`: all present I-V table roughness ratios are within threshold, or no table has enough data to exceed it.
- `WARN` with `review_required=true`: any table exceeds the roughness threshold.
- `NA`: no I-V tables are parsed.

Judgement calls:

- This is evidence for visual review. A roughness ratio is not a substitute for plotted curve inspection.

### 5.3.7 - Combined I-V tables are monotonic

- Automation class: `auto`
- IQ level: `LEVEL 2`
- Module: `checks/c5_3_iv_tables.py`
- Scope: model / I-V table
- Inputs used: parsed typ columns from `[Pulldown]`, `[Pullup]`, `[GND Clamp]`, and `[POWER Clamp]`.

What the tool checks:

- Builds a combined typ-current curve for `[Pulldown] + [GND Clamp]` by taking the union of table voltages and interpolating/summing current from the present tables.
- Builds a combined typ-current curve for `[Pullup] + [POWER Clamp]` the same way.
- Requires the pulldown/gnd-clamp combined curve to be nondecreasing as table voltage increases.
- Requires the pullup/power-clamp combined curve to be nonincreasing as table voltage increases, matching the Vcc-relative pullup table convention used by IBIS.
- Emits one result per combined curve group that has sufficient data.

Result behavior:

- `PASS`: the combined typ-current curve is monotonic within tolerance.
- `FAIL`: the combined typ-current curve violates the expected direction beyond tolerance.
- `ERROR`: a present combined group has insufficient usable points.

Judgement calls and limitations:

- The check currently uses the typ column for combined-curve monotonicity. Typ/min/max combined monotonicity could be added if a stricter review policy is needed.

### 5.3.8 - [Pulldown] I-V tables pass through zero/zero

- Automation class: `auto`
- IQ level: `LEVEL 2`
- Module: `checks/c5_3_iv_tables.py`
- Scope: model / `[Pulldown]`
- Inputs used: parsed `[Pulldown]` table, model type.

What the tool checks:

- For every present `[Pulldown]`, interpolates typ, min, and max currents at table voltage 0 V.
- Requires each interpolated current to be within +/- 1 uA of 0 A.
- Treats values above 1 uA as reviewer evidence rather than an immediate hard failure.
- Treats model types containing exception strings such as `ttl`, `pecl`, `lvds`, or `serdes` as not applicable.
- For input-only and open-source models without `[Pulldown]`, reports not applicable.

Result behavior:

- `PASS`: all interpolated columns are within zero-crossing tolerance.
- `WARN` with `review_required=true`: an interpolated column is outside the pass tolerance.
- `NA`: technology exception applies, or the model type does not require `[Pulldown]`.

Judgement calls:

- The warning behavior is a judgement call based on the quality-spec note that special cases may not pass through zero current at 0 V. A reviewer should decide whether the current is acceptable for the technology and model intent.

### 5.3.9 - [Pullup] I-V tables pass through zero/zero

- Automation class: `auto`
- IQ level: `LEVEL 2`
- Module: `checks/c5_3_iv_tables.py`
- Scope: model / `[Pullup]`
- Inputs used: parsed `[Pullup]` table, model type.

What the tool checks:

- For every present `[Pullup]`, interpolates typ, min, and max currents at table voltage 0 V.
- Because `[Pullup]` voltage is Vcc-relative, table voltage 0 V corresponds to output at Vcc.
- Requires each interpolated current to be within +/- 1 uA of 0 A.
- Treats values above 1 uA as reviewer evidence rather than an immediate hard failure.
- Treats model types containing exception strings such as `ttl`, `pecl`, `lvds`, or `serdes` as not applicable.
- For input-only, open-drain, and open-sink models without `[Pullup]`, reports not applicable.

Result behavior:

- `PASS`: all interpolated columns are within zero-crossing tolerance.
- `WARN` with `review_required=true`: an interpolated column is outside the pass tolerance.
- `NA`: technology exception applies, or the model type does not require `[Pullup]`.

Judgement calls:

- The warning behavior is a judgement call based on the quality-spec note that special cases may not pass through zero current at 0 V. A reviewer should decide whether the current is acceptable for the technology and model intent.

### 5.3.10 - No leakage current in clamp I-V tables

- Automation class: `semi_auto`
- IQ level: `LEVEL 2`
- Module: `checks/c5_semiauto_wave_quality.py`
- Scope: model / clamp I-V tables
- Inputs used: parsed `[GND Clamp]` and `[POWER Clamp]` typ current columns.

What the tool checks:

- Interpolates typ current at 0 V for each present clamp table.
- Flags clamp leakage if absolute current is greater than 1 uA.

Result behavior:

- `PASS`: all present clamp tables are within leakage threshold at 0 V.
- `WARN` with `review_required=true`: any clamp table exceeds leakage threshold.
- `NA`: no clamp I-V tables are parsed.

Judgement calls:

- This is a leakage evidence trigger. The reviewer decides whether the current is acceptable for the technology and datasheet limits.

### 5.3.13 - ECL models I-V tables swept from -Vcc to +2 * Vcc

- Automation class: `auto`
- IQ level: `LEVEL 2`
- Module: `checks/c5_3_iv_tables.py`
- Scope: ECL model / I-V table
- Inputs used: model type, pullup/pulldown references, voltage range, I-V table rows.

What the tool checks:

- Applies only to model types in the configured ECL set: `output_ecl`, `input_ecl`, and `i/o_ecl`.
- Computes effective Vcc from the most positive supply/reference minus the most negative pulldown reference, falling back to zero for the negative side if absent.
- Checks `[Pulldown]` and `[Pullup]` tables, when present, for sweep coverage from `-effective Vcc` to `2 * effective Vcc`.
- Uses the same 2 percent endpoint tolerance as other sweep checks.

Result behavior:

- `PASS`: ECL table sweep coverage reaches expected endpoints within tolerance.
- `FAIL`: low or high endpoint coverage is insufficient.
- `ERROR`: the tool cannot determine the ECL supply range.

Judgement calls:

- Non-ECL models produce no explicit `NA` result for this item to avoid noise.

### 5.3.14 - Point distributions in I-V tables should be sufficient

- Automation class: `semi_auto`
- IQ level: `LEVEL 2`
- Module: `checks/c5_semiauto_wave_quality.py`
- Scope: model / I-V table set
- Inputs used: parsed I-V table row counts.

What the tool checks:

- Counts rows in every present I-V table.
- Flags each table with fewer than 20 points.

Result behavior:

- `PASS`: every present I-V table has at least 20 rows.
- `WARN` with `review_required=true`: one or more tables have fewer than 20 rows.
- `NA`: no I-V tables are parsed.

Judgement calls:

- Point count alone does not prove good distribution; it is evidence for review.

### 5.4.1 - Output and I/O buffers have sufficient V-T tables

- Automation class: `semi_auto`
- IQ level: `LEVEL 2`
- Module: `checks/c5_semiauto_wave_quality.py`
- Scope: model / waveform set
- Inputs used: parsed `[Rising Waveform]` and `[Falling Waveform]` sections.

What the tool checks:

- Counts rising and falling V-T waveform tables per model.
- Flags absence of rising waveform data.
- Flags absence of falling waveform data.

Result behavior:

- `PASS`: at least one rising and at least one falling waveform are parsed.
- `WARN` with `review_required=true`: either direction is missing.
- `NA`: no V-T waveform tables are parsed.

Judgement calls:

- The checker does not yet scale required waveform count by model type, fixture variety, or voltage corner intent.

### 5.4.2 - V-T tables have reasonable point distribution

- Automation class: `semi_auto`
- IQ level: `LEVEL 2`
- Module: `checks/c5_semiauto_wave_quality.py`
- Scope: model / waveform
- Inputs used: parsed V-T table row counts.

What the tool checks:

- For every parsed waveform, counts V-T rows.
- Flags waveforms with fewer than 20 points.

Result behavior:

- `PASS`: every waveform has at least 20 V-T points.
- `WARN` with `review_required=true`: any waveform has fewer than 20 points.
- `NA`: no V-T waveform tables are parsed.

Judgement calls:

- Point count is evidence only. A reviewer still needs to judge whether points are well distributed around transitions.

### 5.4.4 - V-T table endpoints match fixture voltages

- Automation class: `semi_auto`
- IQ level: `LEVEL 2`
- Module: `checks/c5_semiauto_wave_quality.py`
- Scope: model / waveform
- Inputs used: parsed V-T first/last voltage values and waveform `V_fixture`.

What the tool checks:

- For waveforms with at least two rows and a parsed `V_fixture`, compares both endpoint voltages to `V_fixture`.
- Flags a waveform if neither endpoint is within 20 mV of `V_fixture`.

Result behavior:

- `PASS`: every comparable waveform has at least one endpoint near `V_fixture`.
- `WARN` with `review_required=true`: a comparable waveform has neither endpoint near `V_fixture`.
- `NA`: no V-T waveform tables are parsed.

Judgement calls:

- This is a fixture endpoint evidence check, not a complete waveform correctness check.

### 5.5.1 - [Ramp] R_load present if value other than 50 ohms

- Automation class: `auto`
- IQ level: `LEVEL 2`
- Module: `checks/c5_ramp_waveform.py`
- Scope: model / `[Ramp]`
- Inputs used: parsed `[Ramp]` data.

What the tool checks:

- Runs only when a `[Ramp]` section exists.
- If `R_load` is absent, assumes the IBIS default of 50 ohm and passes.
- If `R_load` is present, passes and reports the documented value.

Result behavior:

- `PASS`: `[Ramp]` exists and either uses the default 50 ohm load or documents `R_load`.

Judgement calls and limitations:

- This implementation does not fail any present `[Ramp]` section for this item. It assumes an absent `R_load` means default 50 ohm, which satisfies the "if other than 50 ohms" condition.
- If `[Ramp]` is absent, no result is emitted.

### 5.5.2 - [Ramp] typ/min/max order is correct

- Automation class: `semi_auto`
- IQ level: `LEVEL 2`
- Module: `checks/c5_semiauto_ordering.py`
- Scope: model / `[Ramp]`
- Inputs used: parsed `dV/dt_r` and `dV/dt_f` ramp tuples.

What the tool checks:

- If `[Ramp]` is absent, the check is not applicable.
- Checks complete typ/min/max tuples for rising and falling ramp slew.
- Uses absolute values before ordering, because slew sign conventions can vary.
- Applies the common typ/min/max ordering tolerance.

Result behavior:

- `PASS`: one or more complete ramp slew tuples are present and ordered.
- `WARN` with `review_required=true`: any complete ramp slew tuple appears out of order.
- `NA`: no `[Ramp]` data or no complete ramp dV/dt tuple is parsed.

Judgement calls:

- The absolute-value comparison is a deliberate sign-convention guard.

### 5.5.3 - [Ramp] dV value is consistent with I-V table calculations

- Automation class: `auto`
- IQ level: `LEVEL 2`
- Module: `checks/c5_ramp_waveform.py`
- Scope: model / `[Ramp]`
- Inputs used: parsed `[Ramp]`, `[Pullup]`, `[Pulldown]`, resolved Vcc, and per-corner I-V columns.

What the tool checks:

- Runs only when `[Ramp]` exists.
- Resolves Vcc.
- Uses `R_load` if present, otherwise assumes 50 ohm.
- Computes per-corner load-line intersections using `I_table + I_load = 0`, with `[Pullup]` table voltages converted from the Vcc-relative IBIS convention to output voltage.
- For push-pull models:
  - Rising dV uses a 0 V fixture.
  - Falling dV uses a Vcc fixture.
  - High state comes from `[Pullup]`; low state comes from `[Pulldown]`.
- For single-ended pulldown/open-sink style models with no `[Pullup]`, high state is Vcc and low state comes from the `[Pulldown]` load-line into an external pullup to Vcc.
- For single-ended pullup/open-source style models with no `[Pulldown]`, low state is 0 V and high state comes from the `[Pullup]` load-line into an external pulldown to ground.
- Computes expected dV as 60 percent of `abs(Vhigh - Vlow)`.
- Compares rising and falling ramp dV typ/min/max values against the matching per-corner expected dV.
- Fails if relative error is greater than 5 percent.

Result behavior:

- `PASS`: all available rising and falling ramp dV corners are within tolerance.
- `FAIL`: any available rising or falling ramp dV corner differs by more than 5 percent.
- `WARN`: load-line intersection cannot be computed because needed I-V data is missing.
- `ERROR`: Vcc cannot be resolved.

Judgement calls and limitations:

- The open-sink/open-source handling is a modelling judgement: when one driver table is absent, the tool uses the external resistive fixture endpoint as the missing steady-state rail.

### 5.5.4 - [Ramp] dt is consistent with 20%-80% crossing time

- Automation class: `semi_auto`
- IQ level: `LEVEL 2`
- Module: `checks/c5_semiauto_wave_quality.py`
- Scope: model / ramp and waveform set
- Inputs used: parsed `[Ramp]` dt values and V-T waveform rows.

What the tool checks:

- Requires both `[Ramp]` and at least one V-T waveform.
- Computes a 20%-80% crossing time span for each waveform where crossings can be found.
- Averages available waveform 20%-80% spans.
- Averages available typ ramp dt values from `dt_r` and `dt_f`.
- Computes relative difference between average ramp dt and average V-T 20%-80% span.
- Flags differences greater than 20 percent.

Result behavior:

- `PASS`: average ramp dt is within 20 percent of average V-T 20%-80% span.
- `WARN` with `review_required=true`: relative difference exceeds 20 percent.
- `NA`: ramp or waveform data is absent, or no comparable crossing/span pair can be computed.

Judgement calls:

- The average-based comparison is evidence. It does not replace per-fixture, per-corner waveform review.

## Level 3

### 3.2.2 - [Pin] RLC values are present and reasonable

- Automation class: `auto`
- IQ level: `LEVEL 3`
- Module: `checks/c3_component_structural.py`
- Scope: component / pin
- Inputs used: parsed `[Pin]` L/C values and component package-model reference.

What the tool checks:

- Ignores reserved model names: `POWER`, `GND`, `NC`, and `CIRCUITCALL`.
- Treats detected bare-die components as not applicable for per-pin package RLC completeness.
- Requires signal pins to have both `L_pin` and `C_pin`, unless the component has a package model reference.
- For pins with positive L and C, estimates:
  - `TD = sqrt(L * C)` and checks it is no more than 300 ps.
  - `Z0 = sqrt(L / C)` and checks it is no more than 100 ohm.
- Caps details to the first 10 pin issues for readability.

Result behavior:

- `PASS`: all signal pin L/C values are present or covered by a package model, and all computed TD/Z0 values are within limits.
- `FAIL`: missing L/C with no package model, TD too high, or Z0 too high.
- `NA`: component is detected as bare die.

Judgement calls:

- Components with package model references are treated as covered for missing per-pin L/C.
- Bare-die components are assumed to be intentionally outside the packaged per-pin RLC completeness requirement.

### 3.3.2 - [Diff Pin] Vdiff and Tdelay_* complete and reasonable

- Automation class: `auto`
- IQ level: `LEVEL 3`
- Module: `checks/c3_component_structural.py`
- Scope: component
- Inputs used: parsed `[Diff Pin]` entries, component `[Pin]` model references, parsed `[Model]` type.

What the tool checks:

- If no `[Diff Pin]` section exists, the check is not applicable.
- For input-only differential models:
  - `Vdiff` must be present and positive.
  - `Tdelay_typ` may be absent/NA or exactly zero.
  - Nonzero `Tdelay_typ` is surfaced for review rather than failed immediately.
- For output-only differential models:
  - `Vdiff` must be absent/NA.
  - `Tdelay_typ` must be present.
- For I/O differential models:
  - `Vdiff` must be present and positive.
  - `Tdelay_typ` must be present.

Result behavior:

- `PASS`: all checked differential pairs follow the model-type rule.
- `FAIL`: any pair violates a hard `Vdiff` condition or output/I/O `Tdelay_typ` condition.
- `WARN` with `review_required=true`: input differential pins include nonzero `Tdelay_typ` but otherwise satisfy the deterministic Vdiff rule.
- `NA`: no `[Diff Pin]` section exists for the component.

Judgement calls:

- Missing or invalid Vdiff remains a hard deterministic failure. Zero-valued input-side Tdelay is treated like no effective delay. Nonzero input-side Tdelay is a softer judgement because vendor checklists may accept it as documented timing evidence.

### 5.4.3 - V-T table duration is not excessive

- Automation class: `semi_auto`
- IQ level: `LEVEL 3`
- Module: `checks/c5_semiauto_wave_quality.py`
- Scope: model / waveform
- Inputs used: parsed V-T waveform first/last timestamps.

What the tool checks:

- For each waveform with at least two rows, computes duration as last time minus first time.
- Flags durations greater than 1 us.

Result behavior:

- `PASS`: all comparable waveform durations are no more than 1 us.
- `WARN` with `review_required=true`: any waveform duration exceeds 1 us.
- `NA`: no V-T waveform tables are parsed.

Judgement calls:

- A long duration is not automatically wrong. This is a review trigger for possible excessive table length or slow settling behavior.

### 5.6.2 - Vref consistent for Open-drain, Open-source, and ECL Model_types

- Automation class: `semi_auto`
- IQ level: `LEVEL 3`
- Module: `checks/c5_semiauto_wave_quality.py`
- Scope: model
- Inputs used: model type and parsed scalar `Vref`.

What the tool checks:

- Applies only when the model type string contains `open_drain`, `open_source`, `open_sink`, or `ecl`.
- If applicable, checks that scalar `Vref` was parsed.
- The parser accepts both `Vref value` and `Vref = value` scalar syntax.

Result behavior:

- `PASS`: applicable model has a parsed `Vref`.
- `WARN` with `review_required=true`: applicable model lacks parsed `Vref`.
- `NA`: model type does not require this Vref consistency evidence.

Judgement calls:

- The tool checks presence only. It does not determine whether Vref is numerically correct for the technology or datasheet.

## Level 4

### 3.4.1 - [Pin Mapping] section is included for each component

- Automation class: `auto`
- IQ level: `LEVEL 4`
- Module: `checks/c3_component_structural.py`
- Scope: component
- Inputs used: parsed `[Pin]`, `[Pin Mapping]`, parsed IBIS version, bare-die detection.

What the tool checks:

- Bare-die components are not applicable.
- Requires `[Pin Mapping]` to exist for each non-bare-die component.
- Requires all non-reserved signal pins to be covered by `[Pin Mapping]`.
- For IBIS versions below 7.0, also requires POWER and GND pins to be covered.

Result behavior:

- `PASS`: `[Pin Mapping]` exists and covers required pins.
- `FAIL`: `[Pin Mapping]` is missing or required pins are not covered.
- `NA`: component is detected as bare die.

Judgement calls:

- Coverage rules differ by IBIS version for POWER/GND pins.

### 3.4.2 - [Pin Mapping] table includes power and ground pins

- Automation class: `semi_auto`
- IQ level: `LEVEL 4`
- Module: `checks/c3_semiauto_structural.py`
- Scope: component
- Inputs used: parsed `[Pin]` and `[Pin Mapping]`.

What the tool checks:

- Collects pins whose model name is `POWER` or `GND`.
- If there are no parsed POWER/GND pins, the check is not applicable.
- If `[Pin Mapping]` is absent, flags for review.
- If POWER/GND pins exist, checks whether they are represented in `[Pin Mapping]`.

Result behavior:

- `PASS`: all parsed POWER/GND pins are represented in `[Pin Mapping]`.
- `WARN` with `review_required=true`: `[Pin Mapping]` is absent or POWER/GND pins are missing from it.
- `NA`: no parsed POWER/GND pins exist for the component.

Judgement calls:

- The tool checks rail representation, but not whether rail grouping, domains, or mapping names are electrically complete.

### 3.4.3 - Specify [Merged Pins] keyword if applicable

- Automation class: `auto`
- IQ level: `LEVEL 4`
- Module: `checks/c3_component_structural.py`
- Scope: package model
- Inputs used: parsed `[Define Package Model]`, `[Pin Numbers]`, and `[Merged Pins]` state.

What the tool checks:

- If no package model sections exist, the check is not applicable.
- For each package model, counts occurrences of each package node in `[Pin Numbers]`.
- Treats any node mapped to more than one physical pin as a merged-node condition.
- Requires `[Merged Pins]` when merged nodes exist.

Result behavior:

- `PASS`: merged nodes exist and `[Merged Pins]` is present, or no merged nodes exist.
- `FAIL`: merged nodes exist but `[Merged Pins]` is absent.
- `NA`: no `[Define Package Model]` sections exist.

Judgement calls:

- The tool checks keyword presence, not correctness of the merged-pin electrical model.

### 5.7.1 - All output-capable models include [ISSO PU] and [ISSO PD] tables

- Automation class: `auto`
- IQ level: `LEVEL 4`
- Module: `checks/c5_7_isso.py`
- Scope: model
- Inputs used: model type, parsed `[ISSO PD]`, `[ISSO PU]`, `[Pulldown]`, `[Pullup]`, and resolved Vcc.

What the tool checks:

- Marks input-only models as not applicable.
- Marks ECL models as not applicable.
- Marks model types outside configured output-capable ISSO-required types as not applicable.
- For required models, checks presence of both `[ISSO PD]` and `[ISSO PU]`.
- If both ISSO tables are present, checks endpoint relationships:
  - `Isso_pd(0)` should match `Ipd(Vcc)` within 2 percent when a reference current is available.
  - `Isso_pu(0)` should match `Ipu(Vcc)` within 2 percent when a reference current is available.
  - `Isso_pd(Vcc)` should be approximately zero relative to the reference current.
  - `Isso_pu(Vcc)` should be approximately zero relative to the reference current.

Result behavior:

- `PASS`: tables are present, and endpoint equations are satisfied.
- `FAIL`: one or both ISSO tables are missing, or endpoint equations are violated.
- `ERROR`: Vcc cannot be resolved after both ISSO tables are present.
- `NA`: ISSO is not required for the model type.

Judgement calls:

- Endpoint equations are deterministic evidence. They do not prove full ISSO quality across the curve.

### 5.7.2 - ISSO tables have correct typ/min/max order

- Automation class: `semi_auto`
- IQ level: `LEVEL 4`
- Module: `checks/c5_semiauto_ordering.py`
- Scope: model / ISSO table
- Inputs used: parsed `[ISSO PD]` and `[ISSO PU]` rows.

What the tool checks:

- For each present ISSO table, requires row shape: voltage, typ, min, max.
- Uses absolute current values for typ/min/max ordering.
- Applies the common current ordering tolerance.

Result behavior:

- `PASS`: each present ISSO table has clean typ/min/max order evidence.
- `WARN` with `review_required=true`: malformed rows or out-of-order currents are found.
- `NA`: no ISSO tables are parsed.

Judgement calls:

- Current ordering evidence still needs review because ISSO behavior depends on simultaneous-switching assumptions.

### 5.7.3 - ISSO tables have sufficient point distribution

- Automation class: `semi_auto`
- IQ level: `LEVEL 4`
- Module: `checks/c5_semiauto_wave_quality.py`
- Scope: model / ISSO table
- Inputs used: parsed ISSO table row counts.

What the tool checks:

- Counts rows in each present `[ISSO PD]` and `[ISSO PU]` table.
- Flags ISSO tables with fewer than 20 points.

Result behavior:

- `PASS`: all present ISSO tables have at least 20 rows.
- `WARN` with `review_required=true`: any ISSO table has fewer than 20 rows.
- `NA`: no ISSO tables are parsed.

Judgement calls:

- Point count is evidence only. The checker does not judge whether points are concentrated in the right curve regions.

### 5.7.4 - ISSO tables voltage sweep range is correct

- Automation class: `semi_auto`
- IQ level: `LEVEL 4`
- Module: `checks/c5_semiauto_wave_quality.py`
- Scope: model / ISSO table
- Inputs used: parsed ISSO table voltages and resolved Vcc.

What the tool checks:

- For each present ISSO table, expects voltage sweep coverage from approximately 0 V to Vcc.
- Allows 2 percent endpoint tolerance based on Vcc.
- If Vcc cannot be resolved, flags this as evidence needing review.

Result behavior:

- `PASS`: all present ISSO tables cover approximately 0 V to Vcc.
- `WARN` with `review_required=true`: endpoint coverage is short or Vcc cannot be resolved.
- `NA`: no ISSO tables are parsed.

Judgement calls:

- Sweep coverage evidence does not validate all ISSO curve content.

### 5.8.1 - Each [Rising Waveform] and [Falling Waveform] table includes a [Composite Current] table

- Automation class: `auto`
- IQ level: `LEVEL 4`
- Module: `checks/c5_ramp_waveform.py`
- Scope: model / waveform
- Inputs used: parsed waveform sections and nested `[Composite Current]` sections.

What the tool checks:

- Runs for models with parsed waveforms.
- For every rising or falling waveform, checks whether a nested `[Composite Current]` table is present.

Result behavior:

- `PASS`: waveform has a `[Composite Current]` table.
- `FAIL`: waveform lacks a `[Composite Current]` table.

Judgement calls:

- If a model has no parsed waveforms, no result is emitted for this check.

### 5.8.2 - [Composite Current] waveform data points cover the same time range as corresponding V-T waveforms

- Automation class: `auto`
- IQ level: `LEVEL 4`
- Module: `checks/c5_ramp_waveform.py`
- Scope: model / waveform
- Inputs used: parsed V-T rows and nested Composite Current rows.

What the tool checks:

- Runs only for waveforms with a `[Composite Current]` table.
- Compares the first and last V-T timestamps to the first and last Composite Current timestamps.
- Requires both start and end timestamps to match within 1 fs.

Result behavior:

- `PASS`: Composite Current start/end times match the V-T start/end times.
- `FAIL`: start or end timestamp differs by more than 1 fs.
- `WARN`: V-T or Composite Current table is empty.

Judgement calls:

- This checks time-range endpoints, not full sample-by-sample alignment. That deeper alignment is handled as semi-auto evidence in `5.8.3`.

### 5.8.3 - [Composite Current] waveforms must be time-aligned with corresponding V-T waveforms

- Automation class: `semi_auto`
- IQ level: `LEVEL 4`
- Module: `checks/c5_semiauto_wave_quality.py`
- Scope: model / waveform
- Inputs used: parsed V-T and Composite Current row counts.

What the tool checks:

- Reviews only waveforms that have Composite Current data.
- Compares number of V-T rows to number of Composite Current rows.
- Flags a row-count mismatch as alignment evidence needing review.

Result behavior:

- `PASS`: every reviewed waveform has matching V-T and Composite Current point counts.
- `WARN` with `review_required=true`: any reviewed waveform has a point-count mismatch.
- `NA`: no Composite Current tables are parsed.

Judgement calls:

- Matching point count is not full time alignment. It is a low-cost evidence check to focus reviewer attention.

### 5.8.5 - Start and end points [Composite Current] values correlate with pullup and pulldown tables

- Automation class: `semi_auto`
- IQ level: `LEVEL 4`
- Module: `checks/c5_semiauto_wave_quality.py`
- Scope: model / waveform
- Inputs used: parsed Composite Current first/last typ current values.

What the tool checks:

- Reviews only waveforms with Composite Current data.
- Reads first and last Composite Current typ current values.
- Flags the waveform if both endpoint currents are greater than the clamp leakage threshold of 1 uA.

Result behavior:

- `PASS`: each reviewed Composite Current table has at least one endpoint near zero.
- `WARN` with `review_required=true`: both endpoint currents are non-negligible.
- `NA`: no Composite Current tables are parsed.

Judgement calls and limitations:

- The spec title refers to correlation with pullup and pulldown tables. The current implementation uses endpoint current evidence only; it does not compute a full I-V/Composite Current correlation.

### 5.8.7 - [Composite Current] curve is flat at start and end

- Automation class: `semi_auto`
- IQ level: `LEVEL 4`
- Module: `checks/c5_semiauto_wave_quality.py`
- Scope: model / waveform
- Inputs used: parsed Composite Current edge typ current samples.

What the tool checks:

- Reviews only waveforms with Composite Current data.
- Requires at least four Composite Current rows for edge flatness evidence.
- Compares the first two typ current samples and the last two typ current samples.
- Flags if either edge delta exceeds 1 uA.

Result behavior:

- `PASS`: all reviewed Composite Current edge deltas are within threshold.
- `WARN` with `review_required=true`: start or end edge delta exceeds threshold.
- `NA`: no Composite Current tables are parsed.

Judgement calls:

- Two-point edge flatness is a simple evidence trigger. A reviewer should still inspect the actual curve shape.

### 5.8.8 - [Composite Current] table values should start or end at 0 when V_fixture = 0

- Automation class: `auto`
- IQ level: `LEVEL 4`
- Module: `checks/c5_ramp_waveform.py`
- Scope: model / waveform
- Inputs used: waveform direction, V-T fixture voltage, Composite Current typ current rows.

What the tool checks:

- Runs only for waveforms with Composite Current data.
- Applies only when parsed `V_fixture` is approximately 0 V.
- For rising waveforms, checks that the first Composite Current typ value is within +/- 1 uA of zero.
- For falling waveforms, checks that the last Composite Current typ value is within +/- 1 uA of zero.

Result behavior:

- `PASS`: required endpoint current is near zero.
- `FAIL`: required endpoint current exceeds 1 uA.
- `WARN`: Composite Current table is empty.

Judgement calls:

- If `V_fixture` is absent or not near 0 V, no result is emitted for this item.

## Semi-Auto Review Workflow

Semi-auto checks are implemented as evidence collectors. In the JSON report:

- `automation_class` identifies whether a result came from an auto or semi-auto module.
- `review_required=true` is used for semi-auto warnings that need reviewer action.
- `review_queue` collects all results where `review_required=true`.
- The GUI lets reviewers enter a decision and comment for those queued results.
- Reviewer decisions are saved separately as `*.review.json` so the generated QA evidence is preserved.

Current semi-auto evidence is intentionally conservative:

- Obvious structural or numeric evidence can pass automatically.
- Ambiguous evidence becomes `WARN` plus `review_required=true`.
- External-data checks, datasheet comparisons, SPICE/measurement correlation, and official final IQ assignment still require human review.
