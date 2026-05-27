# IBIS QA Automation Categories

Generated from `data/ibis_quality_spec_3_0.json`.

This catalog groups every IBIS Quality Specification 3.0 check by the current automation plan. The `Why` field explains the classification; the `How` field describes the intended implementation or review workflow.

## Summary

- `auto`: 22 checks
- `semi_auto`: 25 checks
- `manual`: 20 checks
- `optional`: 1 checks

## Auto

Checks that should be implemented as deterministic parser, numeric, or external-tool checks.

### `2.1` LEVEL 1 - IBIS file passes IBISCHK

- Section: 2 General Header Section Requirements
- Keywords: `[IBIS Ver]`, `[Notes]`
- Why: Run IBISCHK, parse version/errors/warnings/cautions, and require documented exceptions for any remaining warnings.
- How: Run the appropriate IBISCHK version for the file's [IBIS Ver], capture the full output, parse version/errors/warnings/cautions, fail on any error, and require [Notes]/comments plus the X designator for unresolved warnings. Additionally verify per §1.4 that an |IQ Score: tag appears inside the .ibs file itself (in [Notes] or a comment line) and that the IBISCHK version used is documented in-file; referencing an external quality report does not satisfy this requirement.

### `3.1.1` LEVEL 2 - [Package] must have typ/min/max values

- Section: 3.1 Component Package Requirements
- Keywords: `[Package]`
- Why: Parse [Package] values and require typ/min/max values instead of NA.
- How: Parse each [Package] R_pkg, L_pkg, and C_pkg row and require populated typical, minimum, and maximum values for the target IQ level.

### `3.2.2` LEVEL 3 - [Pin] RLC values are present and reasonable

- Section: 3.2 Component Pin Requirements
- Keywords: `[Package Model]`, `[Package]`, `[Pin]`
- Why: Presence of pin RLC or [Package Model], plus TD and Z0 limits, can be computed from the IBIS data.
- How: For every signal pin, require R/L/C values or a [Package Model], compute TD = sqrt(LC) and Z0 = sqrt(L/C), and compare them to the spec limits.

### `3.3.1` LEVEL 2 - [Diff Pin] referenced pin models match

- Section: 3.3 Component Diff Pin Requirements
- Keywords: `[Diff Pin]`, `[Model]`, `[Notes]`
- Why: Model-name matching is a deterministic string comparison. When names differ, comment/[Notes] presence is a text search. Both steps are fully parseable with no reviewer judgment required.
- How: Compare the model names on each [Diff Pin] pair. If they differ, search for an explanatory comment or [Notes] entry referencing those pins. Pass if names match or a comment is found; fail if names differ and no explanation is present.

### `3.3.2` LEVEL 3 - [Diff Pin] Vdiff and Tdelay_* complete and reasonable

- Section: 3.3 Component Diff Pin Requirements
- Keywords: `[Diff Pin]`
- Why: Presence, polarity, zero/NA rules, and output/input applicability can be checked from [Diff Pin] and model types.
- How: Use [Diff Pin] entries and referenced model types to check Vdiff/Tdelay presence, positive/zero/NA rules, and input/output applicability.

### `3.4.1` LEVEL 4 - [Pin Mapping] section is included for each component

- Section: 3.4 Component Pin Mapping Requirements
- Keywords: `[Pin Mapping]`, `[Pin]`
- Why: Presence and coverage of [Pin Mapping] can be checked from [Pin] and IBIS version rules.
- How: For each [Component], require [Pin Mapping] coverage for the non-POWER/GND/NC pins per IBIS version rules. Bare-die components (detectable by stub [Package] values of approximately 0.001nH/pF or bare-die naming) are exempt and should be marked NA rather than failed.

### `3.4.3` LEVEL 4 - Specify [Merged Pins] keyword if applicable

- Section: 3.4 Component Pin Mapping Requirements
- Keywords: `[Define Package Model]`, `[Merged Pins]`, `[Model Data]`
- Why: If package model data uses merged pins, require [Merged Pins].
- How: Detect merged pin usage in package-model data and require a matching [Merged Pins] keyword.

### `5.3.1` LEVEL 2 - I-V tables have correct typ/min/max order

- Section: 5.3 Model I-V Table Requirements
- Keywords: `[POWER Clamp]`
- Why: Column order is a positional parse. Active-region current ordering is a numeric comparison. Technology crossover exceptions are handleable with a tolerance band. IBISCHK already performs this check.
- How: Parse every I-V table. Verify column order is voltage/typ/min/max. In the active region check that |Imax| >= |Ityp| >= |Imin| at each voltage step, allowing a small tolerance band for near-overlay cases and single crossover points near clamping onset.

### `5.3.2` LEVEL 2 - [Pullup] voltage sweep range is correct

- Section: 5.3 Model I-V Table Requirements
- Keywords: `[Pullup Reference]`, `[Pullup]`, `[Voltage Range]`
- Why: Voltage sweep range can be checked from [Pullup Reference] or [Voltage Range].
- How: Resolve Vcc from [Pullup Reference] or [Voltage Range] and check [Pullup] voltage coverage from -Vcc to +2*Vcc.

### `5.3.3` LEVEL 2 - [Pulldown] voltage sweep range is correct

- Section: 5.3 Model I-V Table Requirements
- Keywords: `[Pulldown]`, `[Pullup Reference]`, `[Voltage Range]`
- Why: Voltage sweep range can be checked from [Pullup Reference] or [Voltage Range].
- How: Resolve Vcc from [Pullup Reference] or [Voltage Range] and check [Pulldown] voltage coverage from -Vcc to +2*Vcc.

### `5.3.4` LEVEL 2 - [POWER Clamp] voltage sweep range is correct

- Section: 5.3 Model I-V Table Requirements
- Keywords: `[POWER Clamp Reference]`, `[POWER Clamp]`, `[Voltage Range]`
- Why: Voltage sweep range can be checked from [POWER Clamp Reference] or [Voltage Range].
- How: Resolve Vcc from [POWER Clamp Reference] or [Voltage Range] and check [POWER Clamp] coverage at least from -Vcc to 0.

### `5.3.5` LEVEL 2 - [GND Clamp] voltage sweep range is correct

- Section: 5.3 Model I-V Table Requirements
- Keywords: `[GND Clamp]`, `[POWER Clamp Reference]`, `[Voltage Range]`
- Why: Voltage sweep range can be checked from [POWER Clamp Reference] or [Voltage Range].
- How: Resolve Vcc from [POWER Clamp Reference] or [Voltage Range] and check [GND Clamp] coverage at least from -Vcc to +Vcc.

### `5.3.7` LEVEL 2 - Combined I-V tables are monotonic

- Section: 5.3 Model I-V Table Requirements
- Keywords: none detected
- Why: Combined-table monotonicity can be checked numerically and by IBISCHK.
- How: Combine I-V tables according to IBIS rules and check for monotonically increasing current with no slope reversals; optionally cross-check with IBISCHK output.

### `5.3.8` LEVEL 2 - [Pulldown] I-V tables pass through zero/zero

- Section: 5.3 Model I-V Table Requirements
- Keywords: `[Pulldown]`
- Why: Interpolating [Pulldown] at 0V and checking against a tolerance is deterministic. Technology exceptions (TTL, PECL, LVDS, SERDES) are enumerated in the spec and auto-detectable from Model_type. Input-only models without [Pulldown] are NA.
- How: Interpolate [Pulldown] typ/min/max currents at V=0.0V. For CMOS-class Model_types require all three values within +/-1uA. Auto-detect technology exceptions from Model_type (TTL, PECL, LVDS, SERDES) and mark those as NA. Models without [Pulldown] are NA.

### `5.3.9` LEVEL 2 - [Pullup] I-V tables pass through zero/zero

- Section: 5.3 Model I-V Table Requirements
- Keywords: `[Pullup]`
- Why: Same as 5.3.8 for [Pullup]. The Vcc-relative convention (Vtable=0 corresponds to Voutput=Vcc) is deterministic once applied correctly. Technology exceptions are enumerated and auto-detectable from Model_type.
- How: Interpolate [Pullup] typ/min/max currents at Vtable=0.0V (which corresponds to Voutput=Vcc in the Vcc-relative convention). For CMOS-class Model_types require all three values within +/-1uA. Auto-detect technology exceptions from Model_type and mark as NA. Models without [Pullup] are NA.

### `5.3.13` LEVEL 2 - ECL models I-V tables swept from -Vcc to +2 * Vcc.

- Section: 5.3 Model I-V Table Requirements
- Keywords: none detected
- Why: Conditional ECL sweep range can be checked when model type/supplies are known.
- How: For ECL model types, resolve the effective supply span and check I-V table voltage coverage from -Vcc to +2*Vcc.

### `5.5.1` LEVEL 2 - [Ramp] R_load present if value other than 50 ohms

- Section: 5.5 Model [Ramp] Data Requirements
- Keywords: `[Ramp]`
- Why: Require R_load when [Ramp] load differs from 50 ohms.
- How: Parse [Ramp] data and require an explicit R_load when the load is not the 50 ohm default.

### `5.5.3` LEVEL 2 - [Ramp] dV value is consistent with I-V table calculations

- Section: 5.5 Model [Ramp] Data Requirements
- Keywords: `[Ramp]`
- Why: Calculate dV from I-V load-line values and compare against the 5 percent tolerance.
- How: Use [Ramp] R_load and I-V load-line calculations to derive high/low voltages, compute 60 percent dV, and require agreement within 5 percent.

### `5.7.1` LEVEL 4 - All output-capable models include [ISSO PU] and [ISSO PD] tables

- Section: 5.7 Model ISSO Table Requirements
- Keywords: `[ISSO PD]`, `[ISSO PU]`
- Why: ISSO table presence is a structural check. Endpoint equations (Isso_pd(0)=Ipd(Vcc), Isso_pu(0)=Ipu(Vcc), Isso_pd(Vcc)~0, Isso_pu(Vcc)~0) are explicit numeric formulas from the spec. IBISCHK7 performs both checks. Validated at 0.01% error on real DDR4 data.
- How: For every output-capable model (excluding Input, Terminator, and ECL types), require both [ISSO PU] and [ISSO PD] tables. Interpolate endpoint values and verify: Isso_pd(0)=Ipd(Vcc), Isso_pu(0)=Ipu(Vtable=0), Isso_pd(Vcc)~0, Isso_pu(Vcc)~0, each within a 2% tolerance. Reuse IBISCHK7 output where available.

### `5.8.1` LEVEL 4 - Each [Rising Waveform] and [Falling Waveform] table includes a [Composite Current] table

- Section: 5.8 Model I-T Table Requirements
- Keywords: `[Composite Current]`, `[Falling Waveform]`, `[Rising Waveform]`
- Why: Require [Composite Current] under each rising/falling waveform.
- How: Walk each [Rising Waveform] and [Falling Waveform] table and require a subordinate [Composite Current] table.

### `5.8.2` LEVEL 4 - [Composite Current] waveform data points cover the same time range as the corresponding V-T waveforms

- Section: 5.8 Model I-T Table Requirements
- Keywords: `[Composite Current]`
- Why: Compare first/last time points against the parent V-T waveform.
- How: Compare first and last time points of each [Composite Current] table to the parent waveform time range.

### `5.8.8` LEVEL 4 - [Composite Current] table values should start or end at 0 when V_fixture = 0

- Section: 5.8 Model I-T Table Requirements
- Keywords: `[Composite Current]`, `[Falling Waveform]`, `[Rising Waveform]`
- Why: V_fixture=0 start/end zero-current rules can be checked from waveform data.
- How: When V_fixture = 0, check that falling-waveform composite current ends at 0 A and rising-waveform composite current starts at 0 A.

## Semi-Auto

Checks where software can collect strong evidence, but a reviewer may need to confirm context, technology exceptions, or datasheet intent.

### `3.1.2` LEVEL 2 - [Package] model values must be reasonable

- Section: 3.1 Component Package Requirements
- Keywords: `[Package]`
- Why: Numeric limits and typ/min/max ordering can be checked automatically; modeling assumptions still need review.
- How: Check package R/L/C values against the spec limits, verify min < typ < max, and surface any missing comments about modeling assumptions for reviewer confirmation.

### `3.2.1` LEVEL 2 - [Pin] section complete

- Section: 3.2 Component Pin Requirements
- Keywords: `[Model Selector]`, `[Model]`, `[Pin]`
- Why: Parser can check pin syntax and NC/POWER/GND naming; completeness versus the datasheet requires external data.
- How: Parse [Pin] entries, check NC/POWER/GND conventions, and compare model assignments against an external pin list or datasheet when available.

### `3.4.2` LEVEL 4 - [Pin Mapping] table includes power and ground pins

- Section: 3.4 Component Pin Mapping Requirements
- Keywords: `[Bus Label]`, `[Die Supply Pads]`, `[EMD Model]`, `[IBIS Ver]`, `[Interconnect Model]`, `[Pin Mapping]`, `[Pin]`
- Why: Version-dependent coverage can be checked; rail-label intent may need review.
- How: Check POWER/GND mapping requirements using [Pin Mapping], [Bus Label], and [Die Supply Pads], then have a reviewer confirm rail-label intent.

### `4.1` LEVEL 2 - [Model Selector] entries have reasonable descriptions

- Section: 4 [Model Selector] Section
- Keywords: `[Model Selector]`, `[Model]`, `[Notes]`
- Why: The tool can detect missing descriptions; reasonableness and usefulness are reviewer judgments.
- How: For every [Model Selector] entry, verify that it has both a referenced model and a non-empty description; flag generic descriptions for reviewer judgment.

### `5.1.1` LEVEL 2 - [Model] parameters have correct typ/min/max order

- Section: 5.1 Model General Requirements
- Keywords: `[Model]`, `[Temperature]`
- Why: Column order can be checked numerically, but technology-specific weak/strong exceptions require review.
- How: Parse typ/min/max data scoped by [Model], check ordering against weak/slow and strong/fast conventions, and route technology exceptions to review.

### `5.1.2` LEVEL 2 - [Model] C_comp is reasonable

- Section: 5.1 Model General Requirements
- Keywords: `[Model]`, `[Notes]`
- Why: C_comp positivity and C_comp_* sums can be computed; plausibility and comments above 20 pF require review.
- How: Check that C_comp and C_comp_* values are positive, that C_comp_* sums match C_comp by corner when both forms exist, and that values above 20 pF have comments.

### `5.1.4` LEVEL 2 - [Voltage Range] or [* Reference] is reasonable

- Section: 5.1 Model General Requirements
- Keywords: `[* Reference]`, `[Component]`, `[GND Clamp Reference]`, `[Model Selector]`, `[Model]`, `[POWER Clamp Reference]`, `[Pulldown Reference]`, `[Pullup Reference]`, `[Voltage Range]`
- Why: Voltage presence/order/consistency can be checked; extraction and datasheet fit require review.
- How: Resolve [Voltage Range] and reference keyword defaults, check normal min < typ < max ordering and same-nominal-voltage consistency, then compare against datasheet/extraction evidence.

### `5.2.6` LEVEL 2 - [Model Spec] S_Overshoot subparameters track typ/min/max

- Section: 5.2 Model Switching Behavior Requirements
- Keywords: `[Model Spec]`
- Why: Corner tracking can be checked when values exist; correctness of limits still needs datasheet context.
- How: When S_overshoot corners differ, compare their trend with supply/process corners and flag inconsistent corner tracking.

### `5.2.8` LEVEL 2 - [Model Spec] D_Overshoot_* subparameters track typ/min/max

- Section: 5.2 Model Switching Behavior Requirements
- Keywords: `[Model Spec]`
- Why: Corner tracking can be checked when values exist; correctness of limits still needs datasheet context.
- How: When D_overshoot corners differ, compare their trend with supply/process corners and flag inconsistent corner tracking.

### `5.3.6` LEVEL 2 - I-V tables do not exhibit stair-stepping

- Section: 5.3 Model I-V Table Requirements
- Keywords: none detected
- Why: Smoothness/stair-step metrics can flag problems, with plot review as backup.
- How: Run a stair-step or smoothness metric over I-V curves and generate plots so the reviewer can confirm whether flat sections and abrupt jumps are real issues.

### `5.3.10` LEVEL 2 - No leakage current in clamp I-V tables

- Section: 5.3 Model I-V Table Requirements
- Keywords: none detected
- Why: Leakage thresholds can be checked; special technologies and extrapolation need review.
- How: Measure clamp current in the normal operating range, including extrapolated values where needed, and flag leakage above 1 uA unless technology exceptions are documented.

### `5.3.14` LEVEL 2 - Point distributions in I-V tables should be sufficient

- Section: 5.3 Model I-V Table Requirements
- Keywords: none detected
- Why: Point-density and smoothness metrics can flag sparse inflection regions.
- How: Measure point density near inflection regions and run the smoothness metric from Appendix A to flag undersampled I-V curves.

### `5.4.1` LEVEL 2 - Output and I/O buffers have sufficient V-T tables

- Section: 5.4 Model V-T Table Requirements
- Keywords: `[Falling Waveform]`, `[Pulldown Reference]`, `[Pullup Reference]`, `[Ramp]`, `[Rising Waveform]`
- Why: Waveform count and fixture values can be checked; technology sufficiency needs review.
- How: Count [Rising Waveform] and [Falling Waveform] tables by model type, inspect fixture coverage, and require comments when fewer than the expected tables are present.

### `5.4.2` LEVEL 2 - V-T tables have reasonable point distribution

- Section: 5.4 Model V-T Table Requirements
- Keywords: none detected
- Why: Point density and smoothness can be measured, with visual review for curve quality.
- How: Measure V-T point density and second-derivative smoothness through transitions, and provide plots for reviewer confirmation.

### `5.4.3` LEVEL 3 - V-T table duration is not excessive

- Section: 5.4 Model V-T Table Requirements
- Keywords: none detected
- Why: Duration and ending slope can be measured; max-rate target may need datasheet input.
- How: Compare waveform duration to the expected data rate/frequency when available, check final DC settling and ending slope, and preserve relative timing evidence.

### `5.4.4` LEVEL 2 - V-T table endpoints match fixture voltages

- Section: 5.4 Model V-T Table Requirements
- Keywords: `[Falling Waveform]`, `[Pulldown]`, `[Pullup]`, `[Rising Waveform]`, `[Voltage Range]`
- Why: Endpoint/fixture comparison can be checked; technology exceptions need review.
- How: Compare V-T start/end voltages against V_fixture when fixture/reference conditions imply rail endpoints, then route technology exceptions to review.

### `5.5.2` LEVEL 2 - [Ramp] typ/min/max order is correct

- Section: 5.5 Model [Ramp] Data Requirements
- Keywords: `[Ramp]`
- Why: The tool can compare ordering to extraction corners; corner intent may need review.
- How: Compare [Ramp] typ/min/max entries with the extraction corner labels used for I-V data and flag apparent numeric sorting or inconsistent corner order.

### `5.5.4` LEVEL 2 - [Ramp] dt is consistent with 20%-80% crossing time

- Section: 5.5 Model [Ramp] Data Requirements
- Keywords: `[Falling Waveform]`, `[Pullup Reference]`, `[Ramp]`, `[Rising Waveform]`, `[Voltage Range]`
- Why: 20-80 percent crossing can be measured when matching V-T tables exist; alternate references need review.
- How: Select matching V-T fixtures when present, measure 20-80 percent crossing times, compare dt within 10 percent, and document any alternate reference.

### `5.6.2` LEVEL 3 - Vref consistent for Open-drain, Open-source, and ECL Model_types

- Section: 5.6 Output Timing Checks
- Keywords: `[Model Spec]`, `[Model]`, `[Pulldown Reference]`, `[Pullup Reference]`
- Why: Model-type reference-voltage rules can be checked, with exceptions reviewed.
- How: Check Vref relative to Vmeas and pullup/pulldown references for Open-drain, Open-source/Open-sink, and ECL model types.

### `5.7.2` LEVEL 4 - ISSO tables have correct typ/min/max order

- Section: 5.7 Model ISSO Table Requirements
- Keywords: `[ISSO PD]`, `[ISSO PU]`
- Why: Typ/min/max order can be checked numerically; short curve crossovers need review.
- How: Compare ISSO typ/min/max current magnitudes across voltage points and flag sustained violations while allowing reviewer-approved short crossovers.

### `5.7.3` LEVEL 4 - ISSO tables have sufficient point distribution

- Section: 5.7 Model ISSO Table Requirements
- Keywords: none detected
- Why: Point-density and smoothness metrics can flag sparse inflection regions.
- How: Measure ISSO point density near inflection regions and run smoothness checks to flag interpolation risks.

### `5.7.4` LEVEL 4 - ISSO tables voltage sweep range is correct

- Section: 5.7 Model ISSO Table Requirements
- Keywords: `[ISSO PD]`, `[ISSO PU]`
- Why: Sweep coverage can be checked; negative-side breakdown exceptions need review.
- How: Check [ISSO PU]/[ISSO PD] sweep coverage against +/- Vcc and require the +Vcc endpoint; route negative-side breakdown exceptions to review.

### `5.8.3` LEVEL 4 - [Composite Current] waveforms must be time-aligned with corresponding V-T waveforms

- Section: 5.8 Model I-T Table Requirements
- Keywords: `[Composite Current]`
- Why: Time alignment can be measured, but expected current peak shape may need review.
- How: Interpolate composite-current and V-T data onto a common time grid, verify current peaks align with the transition region, and plot evidence.

### `5.8.5` LEVEL 4 - Start and end points [Composite Current] values correlate with pullup and pulldown tables

- Section: 5.8 Model I-T Table Requirements
- Keywords: `[Composite Current]`
- Why: Endpoint current load-line checks can be computed; waived cases need comments.
- How: Compute load-line endpoint currents from pullup/pulldown tables and compare with [Composite Current] start/end values; require comments for waived cases.

### `5.8.7` LEVEL 4 - [Composite Current] curve is flat at start and end

- Section: 5.8 Model I-T Table Requirements
- Keywords: `[Composite Current]`
- Why: Start/end derivative flatness can be measured numerically.
- How: Estimate the derivative of [Composite Current] at the start and end of each table and flag non-flat endpoints.

## Manual

Checks that depend on datasheet interpretation, extraction knowledge, correlation judgment, or model-maker intent.

### `3.1.3` LEVEL 4 - Package model includes power and ground pins

- Section: 3.1 Component Package Requirements
- Keywords: `[Define Package Model]`, `[EMD Model]`, `[External Circuit]`, `[Ground Clamp Reference]`, `[Interconnect Model]`, `[Pulldown Reference]`
- Why: The tool can detect package-model mechanisms, but inclusion of power/ground coupling and method quality require engineering review.
- How: Detect package-model mechanisms such as [Define Package Model], [Interconnect Model], [External Circuit], or EMD references, then have a reviewer confirm power/ground pins and coupling are actually represented.

### `3.1.4` LEVEL 4 - On-die and on-package decoupling included

- Section: 3.1 Component Package Requirements
- Keywords: `[Circuit Call]`, `[External Circuit]`, `[Interconnect Model]`, `[PDN Domain]`, `[PDN Model]`
- Why: The tool can detect PDN/decoupling-related keywords, but sufficiency of on-die/on-package decoupling is a modeling judgment.
- How: Detect PDN/decoupling-related keywords and package-model references, then require reviewer evidence that on-die and on-package decoupling are included sufficiently for SSO/power-aware use.

### `4.2` LEVEL 2 - Default [Model Selector] entries are consistent

- Section: 4 [Model Selector] Section
- Keywords: `[Model Selector]`
- Why: Default model selector consistency depends on product configuration and likely use cases.
- How: Present each selector's first/default entry side by side and have a reviewer confirm the defaults describe one plausible product configuration.

### `5.1.3` LEVEL 2 - [Temperature Range] is reasonable

- Section: 5.1 Model General Requirements
- Keywords: `[Temperature Range]`
- Why: Requires extraction conditions, technology behavior, and datasheet operating temperature comparison.
- How: Compare [Temperature Range] with extraction conditions and datasheet safe operating limits, including technology-specific interpretation of minimum and maximum corners.

### `5.2.1` LEVEL 3 - [Model] Vinl and Vinh reasonable

- Section: 5.2 Model Switching Behavior Requirements
- Keywords: `[Model Spec]`, `[Model]`
- Why: Requires comparing thresholds against datasheet and Vmeas intent.
- How: Compare [Model] Vinl/Vinh to datasheet values, [Model Spec] values when present, and Vmeas expectations for I/O models.

### `5.2.2` LEVEL 3 - [Model Spec] Vinl and Vinh reasonable

- Section: 5.2 Model Switching Behavior Requirements
- Keywords: `[Model Spec]`, `[Model]`, `[Voltage Range]`
- Why: Requires datasheet threshold ranges and supply variation interpretation.
- How: Compare [Model Spec] Vinl/Vinh ranges against datasheet thresholds and the supply variation represented by [Voltage Range].

### `5.2.3` LEVEL 3 - [Model Spec] Vinl+/- and Vinh+/- complete and reasonable

- Section: 5.2 Model Switching Behavior Requirements
- Keywords: `[Model Spec]`
- Why: Requires datasheet/hysteresis intent plus comment review for exceptions.
- How: Determine from the datasheet whether edge-specific or hysteresis thresholds are required, then compare Vinl+/Vinl-/Vinh+/Vinh- and comments.

### `5.2.5` LEVEL 2 - [Model Spec] S_Overshoot subparameters complete and match data sheet

- Section: 5.2 Model Switching Behavior Requirements
- Keywords: `[Model Spec]`
- Why: Requires datasheet functional overshoot limits.
- How: Compare S_overshoot_high and S_overshoot_low values to datasheet functional overshoot limits for each input or I/O model.

### `5.2.7` LEVEL 2 - [Model Spec] D_Overshoot_* subparameters complete and match data sheet

- Section: 5.2 Model Switching Behavior Requirements
- Keywords: `[Model Spec]`
- Why: Requires datasheet dynamic overshoot limits and documented conversion method.
- How: Compare D_overshoot_high, D_overshoot_low, and D_overshoot_time to datasheet dynamic overshoot rules and review any documented conversion method.

### `5.2.9` LEVEL 3 - [Receiver Thresholds] Vth present and matches data sheet, if needed

- Section: 5.2 Model Switching Behavior Requirements
- Keywords: `[Receiver Thresholds]`
- Why: Requires datasheet timing threshold and receiver-threshold applicability.
- How: Decide whether [Receiver Thresholds] are needed for the I/O standard, then compare Vth with the datasheet timing measurement threshold.

### `5.2.10` LEVEL 3 - [Receiver Thresholds] Vth_min and Vth_max present and match data sheet, if needed

- Section: 5.2 Model Switching Behavior Requirements
- Keywords: `[Receiver Thresholds]`
- Why: Requires datasheet Vth tolerance interpretation.
- How: Compare Vth_min and Vth_max against datasheet typical-condition threshold tolerance, excluding supply variation unless the datasheet defines it that way.

### `5.2.11` LEVEL 3 - [Receiver Thresholds] Vinh_ac, Vinl_ac present and match data sheet, if needed

- Section: 5.2 Model Switching Behavior Requirements
- Keywords: `[Model Spec]`, `[Model]`, `[Receiver Thresholds]`
- Why: Requires datasheet AC threshold values and offset conversion review.
- How: Convert datasheet AC thresholds to IBIS offsets from Vth when necessary and compare Vinh_ac/Vinl_ac.

### `5.2.12` LEVEL 3 - [Receiver Thresholds] Vinh_dc, Vinl_dc present and match data sheet, if needed

- Section: 5.2 Model Switching Behavior Requirements
- Keywords: `[Receiver Thresholds]`
- Why: Requires datasheet DC threshold values and offset conversion review.
- How: Convert datasheet DC thresholds to IBIS offsets from Vth when necessary and compare Vinh_dc/Vinl_dc.

### `5.2.13` LEVEL 3 - [Receiver Thresholds] Tslew_ac/Tdiffslew_ac present and match data sheet, if needed

- Section: 5.2 Model Switching Behavior Requirements
- Keywords: `[Receiver Thresholds]`
- Why: Requires datasheet slew-limit values and differential/single-ended applicability.
- How: Compare Tslew_ac or Tdiffslew_ac to the datasheet maximum input transition time for the applicable single-ended or differential receiver.

### `5.2.14` LEVEL 3 - [Receiver Thresholds] Threshold_sensitivity and Ext_ref present and match data sheet, if needed

- Section: 5.2 Model Switching Behavior Requirements
- Keywords: `[Receiver Thresholds]`
- Why: Requires datasheet/reference-supply behavior.
- How: Review datasheet/reference-supply behavior and require Threshold_sensitivity plus Reference_supply/Ext_ref when Vth depends on an external or supply reference.

### `5.3.11` LEVEL 2 - I-V behavior not double-counted

- Section: 5.3 Model I-V Table Requirements
- Keywords: `[GND Clamp]`, `[POWER Clamp]`, `[Pulldown]`, `[Pullup]`
- Why: Double-counting of clamp, driver, and termination behavior needs curve/context review.
- How: Review plotted and combined clamp/driver/termination curves to confirm clamping and on-die termination behavior is not duplicated across tables.

### `5.3.12` LEVEL 2 - On-die termination modeling documented

- Section: 5.3 Model I-V Table Requirements
- Keywords: `[Add Submodel]`, `[GND Clamp]`, `[POWER Clamp]`
- Why: Requires documentation review for on-die termination modeling method.
- How: Search comments/[Notes] for on-die termination labeling and modeling method, then have a reviewer confirm the description is sufficient.

### `5.6.1` LEVEL 3 - [Model Spec] Vmeas and Vref used if typ/min/max variation

- Section: 5.6 Output Timing Checks
- Keywords: `[Model Spec]`
- Why: Requires deciding whether Vmeas/Vref variation exists across corners.
- How: Review whether Vref/Vmeas should vary across typ/min/max conditions and confirm [Model Spec] represents that variation when needed.

### `5.8.4` LEVEL 4 - [Composite Current] includes pre-driver behavior

- Section: 5.8 Model I-T Table Requirements
- Keywords: `[Composite Current]`
- Why: Pre-driver current inclusion requires circuit/extraction knowledge.
- How: Review extraction/circuit documentation and waveform timing to determine whether pre-driver current is included when it draws from the pullup reference rail.

### `5.8.6` LEVEL 4 - [Composite Current] data includes current from correct voltage rails

- Section: 5.8 Model I-T Table Requirements
- Keywords: `[Composite Current]`, `[POWER Clamp Reference]`, `[Pin Mapping]`, `[Pullup Reference]`, `[Voltage Range]`
- Why: Correct supply-rail aggregation cannot be proven from the IBIS file alone.
- How: Review extraction documentation for multi-rail current aggregation and confirm excluded rails match [Pin Mapping] bus-label intent.

## Optional

Good-practice checks that should remain visible but do not gate the IQ score.

### `5.2.4` OPTIONAL - [Model Spec] Pulse subparameters complete

- Section: 5.2 Model Switching Behavior Requirements
- Keywords: `[Model Spec]`
- Why: Optional good-practice check; depends on datasheet pulse behavior and IBIS representability.
- How: If the datasheet defines pulse immunity behavior, check for Pulse_high, Pulse_low, and Pulse_time in [Model Spec] or document why the optional data is omitted.
