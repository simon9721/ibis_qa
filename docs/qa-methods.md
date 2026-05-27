# IBIS QA Methods Map

This document is generated from `quality_ver3.0.md` and `ibis_quality_3.0_checklist_auto.xlsx`.
Use `data/ibis_quality_spec_3_0.json` as the canonical structured source for software work.

## Source Coverage

- PDF/Markdown checks captured: 68
- Workbook checklist entries captured: 67
- In spec but not workbook: 5.2.4
- In workbook but not spec: 3.0

Known mismatches:
- Workbook summary uses 3.0 for 'IBIS file passes IBISCHK'; the PDF section is 2.1.
- The PDF has an OPTIONAL Pulse subparameter check that is not present in the workbook checklist.

## Suggested MVP Scope

- Implement `auto` checks first: IBISCHK parsing, structural presence checks, table range checks, and numeric tolerance checks.
- Add `semi_auto` checks as evidence collectors: compute the numeric evidence, plot or summarize the data, and require reviewer confirmation where the spec depends on reasonableness or technology exceptions.
- Keep `manual` checks in the report template from day one so nothing disappears from the process.
- Treat `optional` checks as visible non-gating items.

## Automation Classes

### Auto

- `2.1` LEVEL 1: IBIS file passes IBISCHK
- `3.1.1` LEVEL 2: [Package] must have typ/min/max values
- `3.2.2` LEVEL 3: [Pin] RLC values are present and reasonable
- `3.3.2` LEVEL 3: [Diff Pin] Vdiff and Tdelay_* complete and reasonable
- `3.4.1` LEVEL 4: [Pin Mapping] section is included for each component
- `3.4.3` LEVEL 4: Specify [Merged Pins] keyword if applicable
- `5.3.2` LEVEL 2: [Pullup] voltage sweep range is correct
- `5.3.3` LEVEL 2: [Pulldown] voltage sweep range is correct
- `5.3.4` LEVEL 2: [POWER Clamp] voltage sweep range is correct
- `5.3.5` LEVEL 2: [GND Clamp] voltage sweep range is correct
- `5.3.7` LEVEL 2: Combined I-V tables are monotonic
- `5.3.13` LEVEL 2: ECL models I-V tables swept from -Vcc to +2 * Vcc.
- `5.5.1` LEVEL 2: [Ramp] R_load present if value other than 50 ohms
- `5.5.3` LEVEL 2: [Ramp] dV value is consistent with I-V table calculations
- `5.8.1` LEVEL 4: Each [Rising Waveform] and [Falling Waveform] table includes a [Composite Current] table
- `5.8.2` LEVEL 4: [Composite Current] waveform data points cover the same time range as the corresponding V-T waveforms
- `5.8.8` LEVEL 4: [Composite Current] table values should start or end at 0 when V_fixture = 0

### Semi-Auto

- `3.1.2` LEVEL 2: [Package] model values must be reasonable
- `3.2.1` LEVEL 2: [Pin] section complete
- `3.3.1` LEVEL 2: [Diff Pin] referenced pin models match
- `3.4.2` LEVEL 4: [Pin Mapping] table includes power and ground pins
- `4.1` LEVEL 2: [Model Selector] entries have reasonable descriptions
- `5.1.1` LEVEL 2: [Model] parameters have correct typ/min/max order
- `5.1.2` LEVEL 2: [Model] C_comp is reasonable
- `5.1.4` LEVEL 2: [Voltage Range] or [* Reference] is reasonable
- `5.2.6` LEVEL 2: [Model Spec] S_Overshoot subparameters track typ/min/max
- `5.2.8` LEVEL 2: [Model Spec] D_Overshoot_* subparameters track typ/min/max
- `5.3.1` LEVEL 2: I-V tables have correct typ/min/max order
- `5.3.6` LEVEL 2: I-V tables do not exhibit stair-stepping
- `5.3.8` LEVEL 2: [Pulldown] I-V tables pass through zero/zero
- `5.3.9` LEVEL 2: [Pullup] I-V tables pass through zero/zero
- `5.3.10` LEVEL 2: No leakage current in clamp I-V tables
- `5.3.14` LEVEL 2: Point distributions in I-V tables should be sufficient
- `5.4.1` LEVEL 2: Output and I/O buffers have sufficient V-T tables
- `5.4.2` LEVEL 2: V-T tables have reasonable point distribution
- `5.4.3` LEVEL 3: V-T table duration is not excessive
- `5.4.4` LEVEL 2: V-T table endpoints match fixture voltages
- `5.5.2` LEVEL 2: [Ramp] typ/min/max order is correct
- `5.5.4` LEVEL 2: [Ramp] dt is consistent with 20%-80% crossing time
- `5.6.2` LEVEL 3: Vref consistent for Open-drain, Open-source, and ECL Model_types
- `5.7.1` LEVEL 4: All output-capable models include [ISSO PU] and [ISSO PD] tables
- `5.7.2` LEVEL 4: ISSO tables have correct typ/min/max order
- `5.7.3` LEVEL 4: ISSO tables have sufficient point distribution
- `5.7.4` LEVEL 4: ISSO tables voltage sweep range is correct
- `5.8.3` LEVEL 4: [Composite Current] waveforms must be time-aligned with corresponding V-T waveforms
- `5.8.5` LEVEL 4: Start and end points [Composite Current] values correlate with pullup and pulldown tables
- `5.8.7` LEVEL 4: [Composite Current] curve is flat at start and end

### Manual

- `3.1.3` LEVEL 4: Package model includes power and ground pins
- `3.1.4` LEVEL 4: On-die and on-package decoupling included
- `4.2` LEVEL 2: Default [Model Selector] entries are consistent
- `5.1.3` LEVEL 2: [Temperature Range] is reasonable
- `5.2.1` LEVEL 3: [Model] Vinl and Vinh reasonable
- `5.2.2` LEVEL 3: [Model Spec] Vinl and Vinh reasonable
- `5.2.3` LEVEL 3: [Model Spec] Vinl+/- and Vinh+/- complete and reasonable
- `5.2.5` LEVEL 2: [Model Spec] S_Overshoot subparameters complete and match data sheet
- `5.2.7` LEVEL 2: [Model Spec] D_Overshoot_* subparameters complete and match data sheet
- `5.2.9` LEVEL 3: [Receiver Thresholds] Vth present and matches data sheet, if needed
- `5.2.10` LEVEL 3: [Receiver Thresholds] Vth_min and Vth_max present and match data sheet, if needed
- `5.2.11` LEVEL 3: [Receiver Thresholds] Vinh_ac, Vinl_ac present and match data sheet, if needed
- `5.2.12` LEVEL 3: [Receiver Thresholds] Vinh_dc, Vinl_dc present and match data sheet, if needed
- `5.2.13` LEVEL 3: [Receiver Thresholds] Tslew_ac/Tdiffslew_ac present and match data sheet, if needed
- `5.2.14` LEVEL 3: [Receiver Thresholds] Threshold_sensitivity and Ext_ref present and match data sheet, if needed
- `5.3.11` LEVEL 2: I-V behavior not double-counted
- `5.3.12` LEVEL 2: On-die termination modeling documented
- `5.6.1` LEVEL 3: [Model Spec] Vmeas and Vref used if typ/min/max variation
- `5.8.4` LEVEL 4: [Composite Current] includes pre-driver behavior
- `5.8.6` LEVEL 4: [Composite Current] data includes current from correct voltage rails

### Optional

- `5.2.4` OPTIONAL: [Model Spec] Pulse subparameters complete

## Data Shape

Each check in the JSON has:

- `id`, `level`, `numeric_level`, `optional`, `title`
- `section_id` and `section_title`
- `ibis_keywords` extracted from the check text
- `paragraphs` with the normalized source detail from the spec
- `automation.class`, `automation.rationale`, and `automation.how`

The scoring model is represented under `scoring_rules`; report fields are represented under `report_requirements`.
