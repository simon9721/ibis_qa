# ibis_qa — IBIS Quality Specification v3.0 Automated Checker

A Python tool that runs the **AUTO-class checks** defined in the
[IBIS Quality Specification v3.0](https://ibis.org/quality_ver3.0/)
against any `.ibs` file.

---

## Background

The IBIS Quality Specification defines 67 check items across four IQ levels
(IQ1–IQ4) plus special correlation designators (G, M, S, X). Each check is
classified as:

| Class | Count | Meaning |
|-------|------:|---------|
| AUTO | 16 | Fully deterministic — parser rules and numeric checks only |
| SEMI-AUTO | 31 | Tool computes evidence; reviewer confirms edge cases |
| MANUAL | 20 | Requires external data (datasheet, SPICE model, extraction docs) |
| OPTIONAL | 1 | Good practice; not required for any IQ level |

This tool covers all **16 AUTO checks** plus the automatable portions of
several SEMI-AUTO checks. MANUAL and OPTIONAL checks are outside scope and
must be evaluated by a qualified engineer using the appropriate external
references.

---

## Requirements

- Python 3.9 or later
- No third-party dependencies — standard library only
- IBISCHK executable (optional): if `ibischk` or `ibischk7` is on your PATH,
  check 2.1 will also run the parser and report error/warning counts

---

## Quick Start

```bash
# Basic run — shows only failures, warnings, and errors
python ibis_qa.py my_model.ibs

# Show everything including PASS and NA results
python ibis_qa.py my_model.ibs --verbose

# Output structured JSON (for downstream tooling)
python ibis_qa.py my_model.ibs --json > report.json
```

### Example output

```
========================================================================
IBIS QA Report — AUTO Checks
File   : z41c.ibs
IBIS Ver: 5.0   File Rev: 2.3   Date: 6/19/2022
IQ Score in file: (not found)
========================================================================

[2.1] ✗  (1 fail, 1 pass, 0 NA, total 3)
  ✗ [z41c.ibs] No '|IQ Score:' tag found inside the .ibs file.
  ⚠ [z41c.ibs] IBISCHK not found on PATH — skipping execution check.

[3.1.1] ✓  (0 fail, 3 pass, 3 NA, total 6)

[5.8.1] ✗  (2 fail, 24 pass, 0 NA, total 26)
  ✗ [ALERT] Falling Waveform #1: [Composite Current] absent

========================================================================
SUMMARY
  FAIL  : 83
  WARN  : 8
  PASS  : 238
  NA    : 184
  ERROR : 0
  Total results: 513
========================================================================
```

**Status symbols:**

| Symbol | Status | Meaning |
|--------|--------|---------|
| ✓ | PASS | Rule satisfied |
| ✗ | FAIL | Rule violated |
| — | NA | Rule does not apply to this item |
| ⚠ | WARN | Soft finding — noteworthy but not a spec-mandated failure |
| ! | ERROR | Check itself failed (parse issue or missing data) |

---

## File Structure

```
ibis_qa/
├── ibis_qa.py              Entry point (CLI)
├── config.py               All numeric tolerances — tune here
├── runner.py               Discovers and runs all check modules
├── reporter.py             Text and JSON output formatting
├── parser/
│   └── ibis_parser.py      Single-pass IBIS file tokeniser
└── checks/
    ├── base.py             CheckResult, Status, CheckModule base class
    ├── c2_1_ibischk.py     Check 2.1  — IBISCHK + IQ score in file
    ├── c3_1_package.py     Checks 3.1.1, 3.1.2 — [Package] values
    ├── c3_component_structural.py
    │                       Checks 3.2.2, 3.3.1, 3.3.2, 3.4.1, 3.4.3
    ├── c5_3_iv_tables.py   Checks 5.3.2–5.3.9, 5.3.13, 5.3.7
    ├── c5_ramp_waveform.py Checks 5.5.1, 5.5.3, 5.8.1, 5.8.2, 5.8.8
    └── c5_7_isso.py        Check 5.7.1 — ISSO PU/PD tables
```

---

## Checks Implemented

### IQ Level 1

| ID | Description | Class |
|----|-------------|-------|
| 2.1 | IBIS file passes IBISCHK with zero errors; IQ score tag present in file | AUTO |

> **Note on 2.1:** The spec (§1.4) requires the IQ score string to be embedded
> inside the `.ibs` file itself (in `[Notes]` or a comment line). Referencing
> an external quality report document does not satisfy this requirement.
> Professional vendor files commonly omit this — the tool will flag it.

### IQ Level 2

| ID | Description | Class |
|----|-------------|-------|
| 3.1.1 | `[Package]` has typ/min/max values (no NA) | AUTO |
| 3.1.2 | `[Package]` values within limits (L<100nH, C<100pF, R<10Ω) and min≤typ≤max | AUTO |
| 3.3.1 | `[Diff Pin]` model names match; mismatches have explanatory comment | AUTO |
| 3.3.2 | `[Diff Pin]` Vdiff/Tdelay columns correct per model type | AUTO |
| 5.3.2 | `[Pullup]` voltage sweep covers −Vcc to +2×Vcc | AUTO |
| 5.3.3 | `[Pulldown]` voltage sweep covers −Vcc to +2×Vcc | AUTO |
| 5.3.4 | `[POWER Clamp]` voltage sweep covers at least −Vcc to 0 | AUTO |
| 5.3.5 | `[GND Clamp]` voltage sweep covers −Vcc to +Vcc | AUTO |
| 5.3.7 | I-V tables are monotonically non-decreasing | AUTO |
| 5.3.8 | `[Pulldown]` passes through ≈0mA at 0V (CMOS; exceptions auto-detected) | AUTO |
| 5.3.9 | `[Pullup]` passes through ≈0mA at Vtable=0 (CMOS; exceptions auto-detected) | AUTO |
| 5.3.13 | ECL model I-V tables swept from −Vcc to +2×Vcc | AUTO |
| 5.5.1 | `[Ramp]` R_load present when load ≠ 50Ω | AUTO |
| 5.5.3 | `[Ramp]` dV consistent with I-V load-line within 5% | AUTO |

### IQ Level 3

| ID | Description | Class |
|----|-------------|-------|
| 3.2.2 | `[Pin]` RLC values present; TD=√(LC)<300ps and Z0=√(L/C)<100Ω | AUTO |

### IQ Level 4

| ID | Description | Class |
|----|-------------|-------|
| 3.4.1 | `[Pin Mapping]` present for each component (bare-die exempt) | AUTO |
| 3.4.3 | `[Merged Pins]` present when package model merges physical pins | AUTO |
| 5.7.1 | `[ISSO PU]` and `[ISSO PD]` present; endpoint equations satisfied | AUTO |
| 5.8.1 | Every `[Rising/Falling Waveform]` has a `[Composite Current]` table | AUTO |
| 5.8.2 | `[Composite Current]` time range matches parent V-T waveform | AUTO |
| 5.8.8 | `[Composite Current]` starts or ends at 0A when V_fixture=0 | AUTO |

---

## NA Handling

A result of **NA** means the rule genuinely does not apply to that item — it
is not a failure and does not block any IQ level claim. Key NA conditions:

- **Bare-die components** (detected by stub package values ≈0.001nH/pF):
  checks 3.1.1, 3.1.2, 3.4.1 are NA
- **Input-only models** (no `[Pullup]`/`[Pulldown]`):
  checks 5.3.2, 5.3.3, 5.3.8, 5.3.9, 5.7.1 are NA
- **ECL models**: check 5.7.1 (ISSO) is NA
- **Components without `[Diff Pin]`**: checks 3.3.1, 3.3.2 are NA
- **Technology exceptions** for zero-crossing (TTL, PECL, LVDS, SERDES):
  checks 5.3.8, 5.3.9 are NA — detected from Model_type

---

## Numeric Tolerances

All thresholds are in `config.py`. Adjust to calibrate for your technology:

| Constant | Default | Used in |
|----------|---------|---------|
| `PKG_L_MAX_H` | 100 nH | 3.1.2 |
| `PKG_C_MAX_F` | 100 pF | 3.1.2 |
| `PKG_R_MAX_OHM` | 10 Ω | 3.1.2 |
| `PIN_TD_MAX_S` | 300 ps | 3.2.2 |
| `PIN_Z0_MAX_OHM` | 100 Ω | 3.2.2 |
| `IV_RANGE_TOLERANCE` | 2% | 5.3.2–5.3.5 |
| `ZERO_CROSS_TOL_A` | 1 µA | 5.3.8, 5.3.9 |
| `RAMP_DV_TOLERANCE` | 5% | 5.5.3 |
| `ISSO_ENDPOINT_TOL` | 2% | 5.7.1 |
| `CC_ZERO_TOL_A` | 1 µA | 5.8.8 |
| `TIME_MATCH_TOL_S` | 1 fs | 5.8.2 |

---

## Adding a New Check

1. Create a file `checks/c<id>_<topic>.py`
2. Define a class inheriting from `CheckModule`
3. Set `check_ids`, `iq_level`, and `auto_class`
4. Implement `run(self, ibis_file) -> list[CheckResult]`

The runner discovers it automatically — no registration needed.

```python
from checks.base import CheckModule, CheckResult
from parser.ibis_parser import IBISFile

class CheckMyNew(CheckModule):
    check_ids  = ["5.3.6"]
    iq_level   = "LEVEL 2"
    auto_class = "semi_auto"

    def run(self, ibis_file: IBISFile) -> list[CheckResult]:
        results = []
        for model in ibis_file.models.values():
            # ... your logic ...
            results.append(self._pass("5.3.6", model.name, "Looks good"))
        return results
```

---

## Known Calibration Items

These are findings from running against the Micron DDR4 z41c reference file
that require algorithm refinement before production use:

| Check | Issue | Fix needed |
|-------|-------|-----------|
| 3.2.2 | Bare-die components have numeric pin names without RLC — flagged incorrectly | Add bare-die NA logic to pin-level loop |
| 3.3.2 | Inverting-pin model type looked up via non-inverting pin — CLKIN misclassified | Look up inv_pin model type separately |
| 5.5.3 | Load-line intersection fails for DDR4 push-pull models (Vcc-relative convention not fully applied before solving) | Apply Vcc offset before intersection search |
| 5.7.1 | ISSO PU voltage axis convention mismatch for some model types | Align ISSO PU table axis with Pullup convention |
| 5.8.8 | ±1µA tolerance is borderline for DDR4 ODT models (1.1–1.3µA observed) | Raise to ±2µA or make technology-conditional |

---

## What This Tool Does NOT Cover

The following require human review with external reference data:

- **MANUAL checks** (20 items): all threshold/overshoot/timing checks that
  require comparison against a datasheet (5.2.x, 5.1.3, etc.)
- **SPICE-dependent checks**: 5.8.4, 5.8.6 (pre-driver circuit topology)
- **SEMI-AUTO review step**: the tool may flag items for review, but the
  reviewer must apply engineering judgment and external references
- **Special designators G, M, S**: Golden Waveforms, Measurement Correlation,
  and Simulation Correlation all require hardware or SPICE data
- **IQ score computation**: the tool reports what it finds; computing the
  final IQ level and writing the in-file score is the user's responsibility

---

## References

- [IBIS Quality Specification v3.0](https://ibis.org/quality_ver3.0/) (ratified Sep 15, 2023)
- [IBIS Specification v8.0](https://ibis.org/ver8.0/) (ratified Dec 5, 2025)
- [I/O Buffer Accuracy Handbook](https://www.ibis.org/accuracy/) (for M and S correlation methods)
- [IBISCHK parser](https://ibis.org/ibischk/) (required for check 2.1 execution)
