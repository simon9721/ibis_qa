# IBIS QA Checks by Quality Level

Generated from `data/ibis_quality_spec_3_0.json`.

The IQ score is cumulative: an IQ3 file must pass the IQ1, IQ2, and IQ3 required checks. Optional checks are visible good-practice items and do not affect the summary IQ score.

## Summary

- `IQ0`: 0 checks - Not Checked
- `IQ1`: 1 checks - Passes IBISCHK
- `IQ2`: 35 checks - Suitable for Waveform Simulation
- `IQ3`: 14 checks - Suitable for Timing Analysis
- `IQ4`: 17 checks - Suitable for Power-Aware Analysis
- `OPTIONAL`: 1 checks - non-gating good-practice items

## IQ0: Not Checked

No documented quality checking has been performed.

Checks at this exact level: 0

## IQ1: Passes IBISCHK

IBISCHK has been run with zero errors and documented handling of warnings.

Checks at this exact level: 1

- `2.1` `auto` - IBIS file passes IBISCHK (2 General Header Section Requirements)

## IQ2: Suitable for Waveform Simulation

IQ1 plus all LEVEL 2 checks for basic waveform simulation data.

Checks at this exact level: 35

- `3.1.1` `auto` - [Package] must have typ/min/max values (3.1 Component Package Requirements)
- `3.1.2` `semi_auto` - [Package] model values must be reasonable (3.1 Component Package Requirements)
- `3.2.1` `semi_auto` - [Pin] section complete (3.2 Component Pin Requirements)
- `3.3.1` `auto` - [Diff Pin] referenced pin models match (3.3 Component Diff Pin Requirements)
- `4.1` `semi_auto` - [Model Selector] entries have reasonable descriptions (4 [Model Selector] Section)
- `4.2` `manual` - Default [Model Selector] entries are consistent (4 [Model Selector] Section)
- `5.1.1` `semi_auto` - [Model] parameters have correct typ/min/max order (5.1 Model General Requirements)
- `5.1.2` `semi_auto` - [Model] C_comp is reasonable (5.1 Model General Requirements)
- `5.1.3` `manual` - [Temperature Range] is reasonable (5.1 Model General Requirements)
- `5.1.4` `semi_auto` - [Voltage Range] or [* Reference] is reasonable (5.1 Model General Requirements)
- `5.2.5` `manual` - [Model Spec] S_Overshoot subparameters complete and match data sheet (5.2 Model Switching Behavior Requirements)
- `5.2.6` `semi_auto` - [Model Spec] S_Overshoot subparameters track typ/min/max (5.2 Model Switching Behavior Requirements)
- `5.2.7` `manual` - [Model Spec] D_Overshoot_* subparameters complete and match data sheet (5.2 Model Switching Behavior Requirements)
- `5.2.8` `semi_auto` - [Model Spec] D_Overshoot_* subparameters track typ/min/max (5.2 Model Switching Behavior Requirements)
- `5.3.1` `auto` - I-V tables have correct typ/min/max order (5.3 Model I-V Table Requirements)
- `5.3.2` `auto` - [Pullup] voltage sweep range is correct (5.3 Model I-V Table Requirements)
- `5.3.3` `auto` - [Pulldown] voltage sweep range is correct (5.3 Model I-V Table Requirements)
- `5.3.4` `auto` - [POWER Clamp] voltage sweep range is correct (5.3 Model I-V Table Requirements)
- `5.3.5` `auto` - [GND Clamp] voltage sweep range is correct (5.3 Model I-V Table Requirements)
- `5.3.6` `semi_auto` - I-V tables do not exhibit stair-stepping (5.3 Model I-V Table Requirements)
- `5.3.7` `auto` - Combined I-V tables are monotonic (5.3 Model I-V Table Requirements)
- `5.3.8` `auto` - [Pulldown] I-V tables pass through zero/zero (5.3 Model I-V Table Requirements)
- `5.3.9` `auto` - [Pullup] I-V tables pass through zero/zero (5.3 Model I-V Table Requirements)
- `5.3.10` `semi_auto` - No leakage current in clamp I-V tables (5.3 Model I-V Table Requirements)
- `5.3.11` `manual` - I-V behavior not double-counted (5.3 Model I-V Table Requirements)
- `5.3.12` `manual` - On-die termination modeling documented (5.3 Model I-V Table Requirements)
- `5.3.13` `auto` - ECL models I-V tables swept from -Vcc to +2 * Vcc. (5.3 Model I-V Table Requirements)
- `5.3.14` `semi_auto` - Point distributions in I-V tables should be sufficient (5.3 Model I-V Table Requirements)
- `5.4.1` `semi_auto` - Output and I/O buffers have sufficient V-T tables (5.4 Model V-T Table Requirements)
- `5.4.2` `semi_auto` - V-T tables have reasonable point distribution (5.4 Model V-T Table Requirements)
- `5.4.4` `semi_auto` - V-T table endpoints match fixture voltages (5.4 Model V-T Table Requirements)
- `5.5.1` `auto` - [Ramp] R_load present if value other than 50 ohms (5.5 Model [Ramp] Data Requirements)
- `5.5.2` `semi_auto` - [Ramp] typ/min/max order is correct (5.5 Model [Ramp] Data Requirements)
- `5.5.3` `auto` - [Ramp] dV value is consistent with I-V table calculations (5.5 Model [Ramp] Data Requirements)
- `5.5.4` `semi_auto` - [Ramp] dt is consistent with 20%-80% crossing time (5.5 Model [Ramp] Data Requirements)

## IQ3: Suitable for Timing Analysis

IQ2 plus all LEVEL 3 checks for timing analysis data.

Checks at this exact level: 14

- `3.2.2` `auto` - [Pin] RLC values are present and reasonable (3.2 Component Pin Requirements)
- `3.3.2` `auto` - [Diff Pin] Vdiff and Tdelay_* complete and reasonable (3.3 Component Diff Pin Requirements)
- `5.2.1` `manual` - [Model] Vinl and Vinh reasonable (5.2 Model Switching Behavior Requirements)
- `5.2.2` `manual` - [Model Spec] Vinl and Vinh reasonable (5.2 Model Switching Behavior Requirements)
- `5.2.3` `manual` - [Model Spec] Vinl+/- and Vinh+/- complete and reasonable (5.2 Model Switching Behavior Requirements)
- `5.2.9` `manual` - [Receiver Thresholds] Vth present and matches data sheet, if needed (5.2 Model Switching Behavior Requirements)
- `5.2.10` `manual` - [Receiver Thresholds] Vth_min and Vth_max present and match data sheet, if needed (5.2 Model Switching Behavior Requirements)
- `5.2.11` `manual` - [Receiver Thresholds] Vinh_ac, Vinl_ac present and match data sheet, if needed (5.2 Model Switching Behavior Requirements)
- `5.2.12` `manual` - [Receiver Thresholds] Vinh_dc, Vinl_dc present and match data sheet, if needed (5.2 Model Switching Behavior Requirements)
- `5.2.13` `manual` - [Receiver Thresholds] Tslew_ac/Tdiffslew_ac present and match data sheet, if needed (5.2 Model Switching Behavior Requirements)
- `5.2.14` `manual` - [Receiver Thresholds] Threshold_sensitivity and Ext_ref present and match data sheet, if needed (5.2 Model Switching Behavior Requirements)
- `5.4.3` `semi_auto` - V-T table duration is not excessive (5.4 Model V-T Table Requirements)
- `5.6.1` `manual` - [Model Spec] Vmeas and Vref used if typ/min/max variation (5.6 Output Timing Checks)
- `5.6.2` `semi_auto` - Vref consistent for Open-drain, Open-source, and ECL Model_types (5.6 Output Timing Checks)

## IQ4: Suitable for Power-Aware Analysis

IQ3 plus all LEVEL 4 checks for power-aware modeling data.

Checks at this exact level: 17

- `3.1.3` `manual` - Package model includes power and ground pins (3.1 Component Package Requirements)
- `3.1.4` `manual` - On-die and on-package decoupling included (3.1 Component Package Requirements)
- `3.4.1` `auto` - [Pin Mapping] section is included for each component (3.4 Component Pin Mapping Requirements)
- `3.4.2` `semi_auto` - [Pin Mapping] table includes power and ground pins (3.4 Component Pin Mapping Requirements)
- `3.4.3` `auto` - Specify [Merged Pins] keyword if applicable (3.4 Component Pin Mapping Requirements)
- `5.7.1` `auto` - All output-capable models include [ISSO PU] and [ISSO PD] tables (5.7 Model ISSO Table Requirements)
- `5.7.2` `semi_auto` - ISSO tables have correct typ/min/max order (5.7 Model ISSO Table Requirements)
- `5.7.3` `semi_auto` - ISSO tables have sufficient point distribution (5.7 Model ISSO Table Requirements)
- `5.7.4` `semi_auto` - ISSO tables voltage sweep range is correct (5.7 Model ISSO Table Requirements)
- `5.8.1` `auto` - Each [Rising Waveform] and [Falling Waveform] table includes a [Composite Current] table (5.8 Model I-T Table Requirements)
- `5.8.2` `auto` - [Composite Current] waveform data points cover the same time range as the corresponding V-T waveforms (5.8 Model I-T Table Requirements)
- `5.8.3` `semi_auto` - [Composite Current] waveforms must be time-aligned with corresponding V-T waveforms (5.8 Model I-T Table Requirements)
- `5.8.4` `manual` - [Composite Current] includes pre-driver behavior (5.8 Model I-T Table Requirements)
- `5.8.5` `semi_auto` - Start and end points [Composite Current] values correlate with pullup and pulldown tables (5.8 Model I-T Table Requirements)
- `5.8.6` `manual` - [Composite Current] data includes current from correct voltage rails (5.8 Model I-T Table Requirements)
- `5.8.7` `semi_auto` - [Composite Current] curve is flat at start and end (5.8 Model I-T Table Requirements)
- `5.8.8` `auto` - [Composite Current] table values should start or end at 0 when V_fixture = 0 (5.8 Model I-T Table Requirements)

## Optional

These checks are recommended by the spec but are not required to achieve any IQ level.

Checks: 1

- `5.2.4` `optional` - [Model Spec] Pulse subparameters complete (5.2 Model Switching Behavior Requirements)
