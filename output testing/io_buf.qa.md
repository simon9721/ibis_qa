# IBIS QA Report

## File Summary

- Generated: 2026-05-29T17:20:21-05:00
- IBIS file: `io_buf.ibs`
- IBIS version: 6.0
- File revision: 0.1
- IBIS file date: December 6, 2025
- IQ score in file: (not found)
- Components: 1
- Models: 1
- Package models: 0

## Score Assessment

| Field | Value |
|---|---|
| Final IQ score | To be assigned by the model maker after resolving or documenting findings |
| Candidate level from checked items | IQ1 |
| Note | Manual checks, accepted exceptions, and correlation designators require model-maker documentation. |

## Result Summary

| Status | Count |
|---|---:|
| PASS | 40 |
| FAIL | 7 |
| WARN | 6 |
| NA | 10 |
| ERROR | 0 |
| Total | 63 |

## Passed Items Per Level

| Level | Required Items | Checked | Passed | NA | Needs Review | Failed | Error | Manual/External Review |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| LEVEL 1 | 1 | 1 | 1 | 0 | 0 | 0 | 0 | 0 |
| LEVEL 2 | 35 | 28 | 18 | 6 | 1 | 3 | 0 | 7 |
| LEVEL 3 | 14 | 4 | 1 | 2 | 0 | 1 | 0 | 10 |
| LEVEL 4 | 17 | 13 | 7 | 2 | 4 | 0 | 0 | 4 |

## General / Shared Check Items

| Level | Check Item | Outcome | Scope / Subject | Fail | Warn | Why attention is needed |
|---|---|---|---|---:|---:|---|
| **LEVEL 3** |  |  |  |  |  |  |
| LEVEL 3 | 3.2.2 - [Pin] RLC values are present and reasonable | FAIL | component: MCM | 1 | 0 | 1 pin RLC issue(s): Pin out: missing L/C values |
| **LEVEL 4** |  |  |  |  |  |  |
| LEVEL 4 | 3.4.2 - [Pin Mapping] table includes power and ground pins | WARN | component: MCM | 0 | 1 | [Pin Mapping] absent; POWER/GND rail coverage needs review |

## Model Check Items

### Model: `driver`

- Candidate model score from model-scoped checked items: IQ1
- Model type: I/O
- Waveform tables: 4

| Level | Check Item | Outcome | Scope / Subject | Fail | Warn | Why attention is needed |
|---|---|---|---|---:|---:|---|
| **LEVEL 2** |  |  |  |  |  |  |
| LEVEL 2 | 5.3.1 - I-V tables have correct typ/min/max order | FAIL | model: driver | 1 | 0 | [Pulldown] typ/min/max current ordering violated: Row 35 V=0.1: \|min\|=0.004255A, \|typ\|=0.004004A, \|max\|=0.003856A; Row 36 V=0.2: \|min\|=0.008279A, \|typ\|=0.007826A, \|max\|=0.007561A |
| LEVEL 2 | 5.3.7 - Combined I-V tables are monotonic | FAIL | model: driver | 4 | 0 | [Pulldown] non-monotonic (19 violation(s)): V=-3.2: current decreases from -14.11mA to -15.51mA; V=-3.1: current decreases from -15.51mA to -17.09mA<br>[Pullup] non-monotonic (94 violation(s)): V=-2.7: current decreases from 57.4mA to 57.27mA; V=-2.6: current decreases from 57.27mA to 56.78mA<br>[GND Clamp] non-monotonic (26 violation(s)): V=-3.233: current decreases from -34.82mA to -35.58mA; V=-3.167: current decreases from -35.58mA to -36.37mA<br>1 more finding type(s) |
| LEVEL 2 | 5.5.3 - [Ramp] dV value is consistent with I-V table calculations | FAIL | model: driver | 1 | 0 | [Ramp] dV inconsistent with I-V load-line (3 corner(s)): Rise dV/typ: ramp=0.9222V, expected≈0.2013V (358.1% error); Rise dV/min: ramp=0.7428V, expected≈0.2013V (268.9% error) |
| LEVEL 2 | 5.5.4 - [Ramp] dt is consistent with 20%-80% crossing time | WARN | model: driver | 0 | 1 | Ramp dt versus V-T 20-80% evidence needs review: avg Ramp dt=6.176e-10s, avg V-T 20-80% span=4.524e-10s, diff=36.5% |
| **LEVEL 4** |  |  |  |  |  |  |
| LEVEL 4 | 5.7.2 - ISSO tables have correct typ/min/max order | WARN | model: driver | 0 | 2 | [ISSO PD] typ/min/max current order needs review: Row 29 V=-0.5: \|min\|=0.06317A, \|typ\|=0.06091A, \|max\|=0.06518A; Row 30 V=-0.4: \|min\|=0.05969A, \|typ\|=0.05894A, \|max\|=0.06344A<br>[ISSO PU] typ/min/max current order needs review: Row 1 V=3.3: \|min\|=2.529e-08A, \|typ\|=1.305e-23A, \|max\|=5.423e-07A; Row 44 V=-1: \|min\|=0.03081A, \|typ\|=0.03007A, \|max\|=0.03304A |
| LEVEL 4 | 5.8.5 - Start and end points [Composite Current] values correlate with pullup and pulldown tables | WARN | model: driver | 0 | 1 | Composite Current endpoint correlation evidence needs review: rising waveform #2: CC endpoints 4.522e-05A, 5.488e-05A |
| LEVEL 4 | 5.8.7 - [Composite Current] curve is flat at start and end | WARN | model: driver | 0 | 1 | Composite Current edge flatness evidence needs review: rising waveform #1: edge deltas start=1.066e-03A, end=0.000e+00A; rising waveform #2: edge deltas start=1.075e-03A, end=4.040e-07A |


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
