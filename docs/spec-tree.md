# IBIS Quality Specification 3.0 Tree

Generated from `data/ibis_quality_spec_3_0.json`.

Legend:

- `LEVEL n`: required check for the corresponding IQ level.
- `OPTIONAL`: good-practice check that does not affect the IQ score.
- `auto`: intended to be fully machine-checkable.
- `semi_auto`: machine can collect evidence, but reviewer confirmation may be needed.
- `manual`: requires datasheet, extraction, correlation, or engineering judgment.

Check counts by automation class:

- `auto`: 22
- `semi_auto`: 25
- `manual`: 20
- `optional`: 1

```text
IBIS Quality Specification 3.0
|-- 1. IBIS Quality Designator
|   |-- 1.1. IBIS Quality Level Definitions
|   |   |-- 1.1.1. IQ0 - Not Checked
|   |   |-- 1.1.2. IQ1 - Passes IBISCHK
|   |   |-- 1.1.3. IQ2 - Suitable for Waveform Simulation
|   |   |-- 1.1.4. IQ3 - Suitable for Timing Analysis
|   |   `-- 1.1.5. IQ4 - Suitable for Power-Aware Analysis
|   |-- 1.2. Special Designators
|   |   |-- 1.2.1. Designator "G" - Contains Golden Waveforms
|   |   |-- 1.2.2. Designator "M" - Measurement Correlated
|   |   |-- 1.2.3. Designator "S" - Simulation Correlated
|   |   `-- 1.2.4. Designator "X" - Exceptions
|   |-- 1.3. OPTIONAL Checks
|   `-- 1.4. IBIS Quality Summary
|-- 2. General Header Section Requirements
|   `-- 2.1 [LEVEL 1, auto] IBIS file passes IBISCHK
|-- 3. Component Section
|   |-- 3.1. Component Package Requirements
|   |   |-- 3.1.1 [LEVEL 2, auto] [Package] must have typ/min/max values
|   |   |-- 3.1.2 [LEVEL 2, semi_auto] [Package] model values must be reasonable
|   |   |-- 3.1.3 [LEVEL 4, manual] Package model includes power and ground pins
|   |   `-- 3.1.4 [LEVEL 4, manual] On-die and on-package decoupling included
|   |-- 3.2. Component Pin Requirements
|   |   |-- 3.2.1 [LEVEL 2, semi_auto] [Pin] section complete
|   |   `-- 3.2.2 [LEVEL 3, auto] [Pin] RLC values are present and reasonable
|   |-- 3.3. Component Diff Pin Requirements
|   |   |-- 3.3.1 [LEVEL 2, auto] [Diff Pin] referenced pin models match
|   |   `-- 3.3.2 [LEVEL 3, auto] [Diff Pin] Vdiff and Tdelay_* complete and reasonable
|   `-- 3.4. Component Pin Mapping Requirements
|       |-- 3.4.1 [LEVEL 4, auto] [Pin Mapping] section is included for each component
|       |-- 3.4.2 [LEVEL 4, semi_auto] [Pin Mapping] table includes power and ground pins
|       `-- 3.4.3 [LEVEL 4, auto] Specify [Merged Pins] keyword if applicable
|-- 4. [Model Selector] Section
|   |-- 4.1 [LEVEL 2, semi_auto] [Model Selector] entries have reasonable descriptions
|   `-- 4.2 [LEVEL 2, manual] Default [Model Selector] entries are consistent
|-- 5. Model Section
|   |-- 5.1. Model General Requirements
|   |   |-- 5.1.1 [LEVEL 2, semi_auto] [Model] parameters have correct typ/min/max order
|   |   |-- 5.1.2 [LEVEL 2, semi_auto] [Model] C_comp is reasonable
|   |   |-- 5.1.3 [LEVEL 2, manual] [Temperature Range] is reasonable
|   |   `-- 5.1.4 [LEVEL 2, semi_auto] [Voltage Range] or [* Reference] is reasonable
|   |-- 5.2. Model Switching Behavior Requirements
|   |   |-- 5.2.1 [LEVEL 3, manual] [Model] Vinl and Vinh reasonable
|   |   |-- 5.2.2 [LEVEL 3, manual] [Model Spec] Vinl and Vinh reasonable
|   |   |-- 5.2.3 [LEVEL 3, manual] [Model Spec] Vinl+/- and Vinh+/- complete and reasonable
|   |   |-- 5.2.4 [OPTIONAL, optional] [Model Spec] Pulse subparameters complete
|   |   |-- 5.2.5 [LEVEL 2, manual] [Model Spec] S_Overshoot subparameters complete and match data sheet
|   |   |-- 5.2.6 [LEVEL 2, semi_auto] [Model Spec] S_Overshoot subparameters track typ/min/max
|   |   |-- 5.2.7 [LEVEL 2, manual] [Model Spec] D_Overshoot_* subparameters complete and match data sheet
|   |   |-- 5.2.8 [LEVEL 2, semi_auto] [Model Spec] D_Overshoot_* subparameters track typ/min/max
|   |   |-- 5.2.9 [LEVEL 3, manual] [Receiver Thresholds] Vth present and matches data sheet, if needed
|   |   |-- 5.2.10 [LEVEL 3, manual] [Receiver Thresholds] Vth_min and Vth_max present and match data sheet, if needed
|   |   |-- 5.2.11 [LEVEL 3, manual] [Receiver Thresholds] Vinh_ac, Vinl_ac present and match data sheet, if needed
|   |   |-- 5.2.12 [LEVEL 3, manual] [Receiver Thresholds] Vinh_dc, Vinl_dc present and match data sheet, if needed
|   |   |-- 5.2.13 [LEVEL 3, manual] [Receiver Thresholds] Tslew_ac/Tdiffslew_ac present and match data sheet, if needed
|   |   `-- 5.2.14 [LEVEL 3, manual] [Receiver Thresholds] Threshold_sensitivity and Ext_ref present and match data sheet, if needed
|   |-- 5.3. Model I-V Table Requirements
|   |   |-- 5.3.1 [LEVEL 2, auto] I-V tables have correct typ/min/max order
|   |   |-- 5.3.2 [LEVEL 2, auto] [Pullup] voltage sweep range is correct
|   |   |-- 5.3.3 [LEVEL 2, auto] [Pulldown] voltage sweep range is correct
|   |   |-- 5.3.4 [LEVEL 2, auto] [POWER Clamp] voltage sweep range is correct
|   |   |-- 5.3.5 [LEVEL 2, auto] [GND Clamp] voltage sweep range is correct
|   |   |-- 5.3.6 [LEVEL 2, semi_auto] I-V tables do not exhibit stair-stepping
|   |   |-- 5.3.7 [LEVEL 2, auto] Combined I-V tables are monotonic
|   |   |-- 5.3.8 [LEVEL 2, auto] [Pulldown] I-V tables pass through zero/zero
|   |   |-- 5.3.9 [LEVEL 2, auto] [Pullup] I-V tables pass through zero/zero
|   |   |-- 5.3.10 [LEVEL 2, semi_auto] No leakage current in clamp I-V tables
|   |   |-- 5.3.11 [LEVEL 2, manual] I-V behavior not double-counted
|   |   |-- 5.3.12 [LEVEL 2, manual] On-die termination modeling documented
|   |   |-- 5.3.13 [LEVEL 2, auto] ECL models I-V tables swept from -Vcc to +2 * Vcc.
|   |   `-- 5.3.14 [LEVEL 2, semi_auto] Point distributions in I-V tables should be sufficient
|   |-- 5.4. Model V-T Table Requirements
|   |   |-- 5.4.1 [LEVEL 2, semi_auto] Output and I/O buffers have sufficient V-T tables
|   |   |-- 5.4.2 [LEVEL 2, semi_auto] V-T tables have reasonable point distribution
|   |   |-- 5.4.3 [LEVEL 3, semi_auto] V-T table duration is not excessive
|   |   `-- 5.4.4 [LEVEL 2, semi_auto] V-T table endpoints match fixture voltages
|   |-- 5.5. Model [Ramp] Data Requirements
|   |   |-- 5.5.1 [LEVEL 2, auto] [Ramp] R_load present if value other than 50 ohms
|   |   |-- 5.5.2 [LEVEL 2, semi_auto] [Ramp] typ/min/max order is correct
|   |   |-- 5.5.3 [LEVEL 2, auto] [Ramp] dV value is consistent with I-V table calculations
|   |   `-- 5.5.4 [LEVEL 2, semi_auto] [Ramp] dt is consistent with 20%-80% crossing time
|   |-- 5.6. Output Timing Checks
|   |   |-- 5.6.1 [LEVEL 3, manual] [Model Spec] Vmeas and Vref used if typ/min/max variation
|   |   `-- 5.6.2 [LEVEL 3, semi_auto] Vref consistent for Open-drain, Open-source, and ECL Model_types
|   |-- 5.7. Model ISSO Table Requirements
|   |   |-- 5.7.1 [LEVEL 4, auto] All output-capable models include [ISSO PU] and [ISSO PD] tables
|   |   |-- 5.7.2 [LEVEL 4, semi_auto] ISSO tables have correct typ/min/max order
|   |   |-- 5.7.3 [LEVEL 4, semi_auto] ISSO tables have sufficient point distribution
|   |   `-- 5.7.4 [LEVEL 4, semi_auto] ISSO tables voltage sweep range is correct
|   `-- 5.8. Model I-T Table Requirements
|       |-- 5.8.1 [LEVEL 4, auto] Each [Rising Waveform] and [Falling Waveform] table includes a [Composite Current] table
|       |-- 5.8.2 [LEVEL 4, auto] [Composite Current] waveform data points cover the same time range as the corresponding V-T waveforms
|       |-- 5.8.3 [LEVEL 4, semi_auto] [Composite Current] waveforms must be time-aligned with corresponding V-T waveforms
|       |-- 5.8.4 [LEVEL 4, manual] [Composite Current] includes pre-driver behavior
|       |-- 5.8.5 [LEVEL 4, semi_auto] Start and end points [Composite Current] values correlate with pullup and pulldown tables
|       |-- 5.8.6 [LEVEL 4, manual] [Composite Current] data includes current from correct voltage rails
|       |-- 5.8.7 [LEVEL 4, semi_auto] [Composite Current] curve is flat at start and end
|       `-- 5.8.8 [LEVEL 4, auto] [Composite Current] table values should start or end at 0 when V_fixture = 0
|-- 6. Correlation
`-- Appendix A. Smoothness checking algorithm
```
