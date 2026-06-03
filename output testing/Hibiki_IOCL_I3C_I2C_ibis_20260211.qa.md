# IBIS QA Report

## File Summary

- Generated: 2026-05-29T17:25:44-05:00
- IBIS file: `Hibiki_IOCL_I3C_I2C_ibis_20260211.ibs`
- IBIS version: 4.2
- File revision: 1.0
- IBIS file date: Tue Feb 26 19:11:02 2026
- IQ score in file: (not found)
- Components: 1
- Models: 4
- Package models: 0

## Score Assessment

| Field | Value |
|---|---|
| Final IQ score | To be assigned by the model maker after resolving or documenting findings |
| Candidate level from checked items | Below IQ1 |
| Note | Manual checks, accepted exceptions, and correlation designators require model-maker documentation. |

## Result Summary

| Status | Count |
|---|---:|
| PASS | 66 |
| FAIL | 26 |
| WARN | 6 |
| NA | 65 |
| ERROR | 0 |
| Total | 163 |

## Passed Items Per Level

| Level | Required Items | Checked | Passed | NA | Needs Review | Failed | Error | Manual/External Review |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| LEVEL 1 | 1 | 1 | 0 | 0 | 0 | 1 | 0 | 0 |
| LEVEL 2 | 35 | 28 | 19 | 5 | 3 | 1 | 0 | 7 |
| LEVEL 3 | 14 | 4 | 1 | 2 | 0 | 1 | 0 | 10 |
| LEVEL 4 | 17 | 11 | 0 | 9 | 0 | 2 | 0 | 6 |

## General / Shared Check Items

| Level | Check Item | Outcome | Scope / Subject | Fail | Warn | Why attention is needed |
|---|---|---|---|---:|---:|---|
| **LEVEL 1** |  |  |  |  |  |  |
| LEVEL 1 | 2.1 - IBIS file passes IBISCHK | FAIL | file: a11486_ibis-00001760_20260211_1855.ibs | 1 | 0 | IBISCHK: 1 error(s), 0 warning(s): IBISCHK7 V7.2.1;  |
| **LEVEL 3** |  |  |  |  |  |  |
| LEVEL 3 | 3.2.2 - [Pin] RLC values are present and reasonable | FAIL | component: A11486_IBIS-00001760 | 1 | 0 | 2 pin RLC issue(s): Pin IO: missing L/C values; Pin IO2: missing L/C values |

## Model Check Items

### Model: `I3C_RX_RPU0RPD0_rx`

- Candidate model score from model-scoped checked items: Below IQ1
- Model type: Input
- Waveform tables: 0

| Level | Check Item | Outcome | Scope / Subject | Fail | Warn | Why attention is needed |
|---|---|---|---|---:|---:|---|
| **LEVEL 2** |  |  |  |  |  |  |
| LEVEL 2 | 5.3.6 - I-V tables do not exhibit stair-stepping | WARN | model: I3C_RX_RPU0RPD0_rx | 0 | 1 | I-V stair-step evidence needs review: [GND Clamp]: roughness=0.262 > 0.1; [POWER Clamp]: roughness=0.2 > 0.1 |
| LEVEL 2 | 5.3.7 - Combined I-V tables are monotonic | FAIL | model: I3C_RX_RPU0RPD0_rx | 2 | 0 | [GND Clamp] non-monotonic (1 violation(s)): V=1.238: current decreases from 4.698e-06mA to 0mA<br>[POWER Clamp] non-monotonic (25 violation(s)): V=-1.163: current decreases from 1134mA to 906.9mA; V=-1.125: current decreases from 906.9mA to 692.1mA |

### Model: `I2C_RX_RPU1RPD0_rx`

- Candidate model score from model-scoped checked items: Below IQ1
- Model type: Input
- Waveform tables: 0

| Level | Check Item | Outcome | Scope / Subject | Fail | Warn | Why attention is needed |
|---|---|---|---|---:|---:|---|
| **LEVEL 2** |  |  |  |  |  |  |
| LEVEL 2 | 5.3.6 - I-V tables do not exhibit stair-stepping | WARN | model: I2C_RX_RPU1RPD0_rx | 0 | 1 | I-V stair-step evidence needs review: [GND Clamp]: roughness=0.262 > 0.1; [POWER Clamp]: roughness=0.2 > 0.1 |
| LEVEL 2 | 5.3.7 - Combined I-V tables are monotonic | FAIL | model: I2C_RX_RPU1RPD0_rx | 2 | 0 | [GND Clamp] non-monotonic (1 violation(s)): V=1.238: current decreases from 4.695e-06mA to 0mA<br>[POWER Clamp] non-monotonic (25 violation(s)): V=-1.163: current decreases from 1134mA to 907mA; V=-1.125: current decreases from 907mA to 692.1mA |
| LEVEL 2 | 5.3.10 - No leakage current in clamp I-V tables | WARN | model: I2C_RX_RPU1RPD0_rx | 0 | 1 | Clamp leakage evidence needs review: [GND Clamp]: I(0V)=-17.8 uA |

### Model: `I2C_TX_8mA_tx`

- Candidate model score from model-scoped checked items: Below IQ1
- Model type: I/O
- Waveform tables: 4

| Level | Check Item | Outcome | Scope / Subject | Fail | Warn | Why attention is needed |
|---|---|---|---|---:|---:|---|
| **LEVEL 2** |  |  |  |  |  |  |
| LEVEL 2 | 5.3.6 - I-V tables do not exhibit stair-stepping | WARN | model: I2C_TX_8mA_tx | 0 | 1 | I-V stair-step evidence needs review: [GND Clamp]: roughness=0.262 > 0.1; [POWER Clamp]: roughness=0.2 > 0.1 |
| LEVEL 2 | 5.3.7 - Combined I-V tables are monotonic | FAIL | model: I2C_TX_8mA_tx | 4 | 0 | [Pulldown] non-monotonic (18 violation(s)): V=1.725: current decreases from 43.22mA to 43.1mA; V=1.762: current decreases from 43.1mA to 42.84mA<br>[Pullup] non-monotonic (63 violation(s)): V=-1.163: current decreases from 19.84mA to 19.58mA; V=-1.125: current decreases from 19.58mA to 19.32mA<br>[GND Clamp] non-monotonic (1 violation(s)): V=1.238: current decreases from 4.698e-06mA to 0mA<br>1 more finding type(s) |
| LEVEL 2 | 5.5.3 - [Ramp] dV value is consistent with I-V table calculations | WARN | model: I2C_TX_8mA_tx | 0 | 1 | Could not compute load-line intersection for dV check (missing [Pullup] or [Pulldown] table) |
| **LEVEL 4** |  |  |  |  |  |  |
| LEVEL 4 | 5.7.1 - All output-capable models include [ISSO PU] and [ISSO PD] tables | FAIL | model: I2C_TX_8mA_tx | 2 | 0 | [ISSO PD] table missing for output-capable model<br>[ISSO PU] table missing for output-capable model |
| LEVEL 4 | 5.8.1 - Each [Rising Waveform] and [Falling Waveform] table includes a [Composite Current] table | FAIL | model: I2C_TX_8mA_tx | 4 | 0 | Rising Waveform #1: [Composite Current] absent — IQ4 requires CC under every waveform. If intentionally omitted, apply X designator with documented justification.<br>Rising Waveform #2: [Composite Current] absent — IQ4 requires CC under every waveform. If intentionally omitted, apply X designator with documented justification.<br>Falling Waveform #3: [Composite Current] absent — IQ4 requires CC under every waveform. If intentionally omitted, apply X designator with documented justification.<br>1 more finding type(s) |

### Model: `I3C_TX_0p125mA_tx`

- Candidate model score from model-scoped checked items: Below IQ1
- Model type: I/O
- Waveform tables: 4

| Level | Check Item | Outcome | Scope / Subject | Fail | Warn | Why attention is needed |
|---|---|---|---|---:|---:|---|
| **LEVEL 2** |  |  |  |  |  |  |
| LEVEL 2 | 5.3.6 - I-V tables do not exhibit stair-stepping | WARN | model: I3C_TX_0p125mA_tx | 0 | 1 | I-V stair-step evidence needs review: [GND Clamp]: roughness=0.262 > 0.1; [POWER Clamp]: roughness=0.2 > 0.1 |
| LEVEL 2 | 5.3.7 - Combined I-V tables are monotonic | FAIL | model: I3C_TX_0p125mA_tx | 4 | 0 | [Pulldown] non-monotonic (17 violation(s)): V=1.762: current decreases from 1.128mA to 1.125mA; V=1.8: current decreases from 1.125mA to 1.118mA<br>[Pullup] non-monotonic (66 violation(s)): V=-1.163: current decreases from 0.4964mA to 0.4907mA; V=-1.125: current decreases from 0.4907mA to 0.4851mA<br>[GND Clamp] non-monotonic (1 violation(s)): V=1.238: current decreases from 4.698e-06mA to 0mA<br>1 more finding type(s) |
| **LEVEL 4** |  |  |  |  |  |  |
| LEVEL 4 | 5.7.1 - All output-capable models include [ISSO PU] and [ISSO PD] tables | FAIL | model: I3C_TX_0p125mA_tx | 2 | 0 | [ISSO PD] table missing for output-capable model<br>[ISSO PU] table missing for output-capable model |
| LEVEL 4 | 5.8.1 - Each [Rising Waveform] and [Falling Waveform] table includes a [Composite Current] table | FAIL | model: I3C_TX_0p125mA_tx | 4 | 0 | Rising Waveform #1: [Composite Current] absent — IQ4 requires CC under every waveform. If intentionally omitted, apply X designator with documented justification.<br>Rising Waveform #2: [Composite Current] absent — IQ4 requires CC under every waveform. If intentionally omitted, apply X designator with documented justification.<br>Falling Waveform #3: [Composite Current] absent — IQ4 requires CC under every waveform. If intentionally omitted, apply X designator with documented justification.<br>1 more finding type(s) |


## Appendix A: IQ Levels

| Level | Name | Meaning |
|---|---|---|
| IQ0 | Not Checked | No documented quality checking has been performed. |
| IQ1 | Passes IBISCHK | IBISCHK has been run with zero errors and documented handling of warnings. |
| IQ2 | Suitable for Waveform Simulation | IQ1 plus all LEVEL 2 checks for basic waveform simulation data. |
| IQ3 | Suitable for Timing Analysis | IQ2 plus all LEVEL 3 checks for timing analysis data. |
| IQ4 | Suitable for Power-Aware Analysis | IQ3 plus all LEVEL 4 checks for power-aware modeling data. |

## Appendix B: Special Designators

Special letters may be appended to the IQ score when the supporting evidence is documented.

| Designator | Name | Meaning |
|---|---|---|
| G | Contains Golden Waveforms | The file contains golden waveform data using [Test Data] and [Test Load] or equivalent external documentation. |
| M | Measurement Correlated | IBIS simulation has been correlated against hardware measurements with documented methods/results. |
| S | Simulation Correlated | IBIS simulation has been correlated against a reference simulation such as SPICE with documented methods/results. |
| X | Exceptions | One or more checks require documented exceptions in [Notes] or comments. |

## Appendix C: Scoring Notes

- Base level: The summary IQ number is the highest level for which all required checks at that level and below pass, are NA, or are accepted exceptions.
- Optional checks: OPTIONAL checks are good practice but do not change the summary IQ number.
- Correlation designators: Append M, S, and/or G when measurement correlation, simulation correlation, and/or golden waveform evidence is documented for a reasonable set of models.
- Exception designator: Append X when any check passes only by documented exception or any remaining parser warning needs user attention.
- Writeback: The summary IQ score must be written into the IBIS file, preferably in [Notes]; detailed per-check status is better stored in a quality report.
