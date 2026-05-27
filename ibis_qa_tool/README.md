# ibis_qa — IBIS Quality Specification v3.0 Checker

A Python tool that evaluates IBIS `.ibs` files against the
[IBIS Quality Specification v3.0](https://ibis.org/quality_ver3.0/) (ratified Sep 15, 2023).

The canonical data source for all check definitions, automation classes, and
implementation guidance is `ibis_quality_spec_3_0.json`, included in this
repository. Every check ID, title, level, and `how-to-automate` description
in this README is drawn directly from that file.

---

## Background

The IBIS Quality Specification defines 68 check items across four IQ levels
plus a set of special correlation designators. Each check is classified by
how much can be verified from the IBIS file alone:

| Class | Count | Meaning |
|-------|------:|---------|
| `auto` | 17 | Fully deterministic — parser rules and numeric checks, no reviewer needed |
| `semi_auto` | 30 | Tool computes evidence; reviewer confirms edge cases or technology exceptions |
| `manual` | 20 | Requires external data — datasheet, SPICE model, or extraction documentation |
| `optional` | 1 | Good practice; does not affect the IQ score |

This tool currently implements **22 of the 17 `auto` checks** (all of them,
plus a few partially-automatable `semi_auto` checks) and produces a
structured report that surfaces evidence for the remaining checks so a
reviewer can work efficiently.

---

## Requirements

- Python 3.9 or later
- No third-party packages — standard library only
- `ibischk` or `ibischk7` on PATH (optional): enables check 2.1 execution

---

## Quick Start

```bash
# Default: show failures, warnings, and errors only
python ibis_qa.py my_model.ibs

# Show everything including PASS and NA
python ibis_qa.py my_model.ibs --verbose

# Structured JSON output for downstream tooling
python ibis_qa.py my_model.ibs --json > report.json
```

### Sample output

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
  FAIL  : 83   WARN  : 8   PASS  : 238   NA  : 184   ERROR : 0
========================================================================
```

| Symbol | Status | Meaning |
|--------|--------|---------|
| ✓ | PASS | Rule satisfied |
| ✗ | FAIL | Rule violated |
| — | NA | Rule does not apply to this item |
| ⚠ | WARN | Noteworthy finding; not a spec-mandated failure |
| ! | ERROR | Check itself failed (parse issue or missing data) |

---

## File Structure

```
ibis_qa/
├── ibis_qa.py                   Entry point (CLI)
├── config.py                    All numeric tolerances — tune here
├── runner.py                    Auto-discovers and runs all check modules
├── reporter.py                  Text and JSON output formatting
├── ibis_quality_spec_3_0.json   Canonical check definitions (source of truth)
├── parser/
│   └── ibis_parser.py           Single-pass IBIS tokeniser → IBISFile object
└── checks/
    ├── base.py                  CheckResult, Status, CheckModule base class
    ├── c2_1_ibischk.py          Check 2.1
    ├── c3_1_package.py          Checks 3.1.1, 3.1.2
    ├── c3_component_structural.py   Checks 3.2.2, 3.3.1, 3.3.2, 3.4.1, 3.4.3
    ├── c5_3_iv_tables.py        Checks 5.3.2–5.3.9, 5.3.13, 5.3.7
    ├── c5_ramp_waveform.py      Checks 5.5.1, 5.5.3, 5.8.1, 5.8.2, 5.8.8
    └── c5_7_isso.py             Check 5.7.1
```

---

## Check Coverage

### IQ Level 1

| ID | Title | Class | Status |
|----|-------|-------|--------|
| 2.1 | IBIS file passes IBISCHK | `auto` | ✅ implemented |

**How (from spec JSON):** Run the appropriate IBISCHK version for the file's
`[IBIS Ver]`, capture the full output, parse version/errors/warnings/cautions,
fail on any error, and require `[Notes]`/comments plus the X designator for
unresolved warnings.

> **Note on §1.4 (IQ score in file):** The spec requires the IQ score string
> to be written inside the `.ibs` file itself, not only in an external quality
> report. This tool checks for the `|IQ Score:` tag as part of check 2.1.

---

### IQ Level 2 — 35 checks

| ID | Title | Class | Status |
|----|-------|-------|--------|
| 3.1.1 | `[Package]` must have typ/min/max values | `auto` | ✅ implemented |
| 3.1.2 | `[Package]` model values must be reasonable | `semi_auto` | ✅ auto portion |
| 3.2.1 | `[Pin]` section complete | `semi_auto` | ⬜ not yet |
| 3.3.1 | `[Diff Pin]` referenced pin models match | `semi_auto` | ✅ auto portion |
| 4.1 | `[Model Selector]` entries have reasonable descriptions | `semi_auto` | ⬜ not yet |
| 4.2 | Default `[Model Selector]` entries are consistent | `manual` | — out of scope |
| 5.1.1 | `[Model]` parameters have correct typ/min/max order | `semi_auto` | ⬜ not yet |
| 5.1.2 | `[Model]` C_comp is reasonable | `semi_auto` | ⬜ not yet |
| 5.1.3 | `[Temperature Range]` is reasonable | `manual` | — out of scope |
| 5.1.4 | `[Voltage Range]` or `[* Reference]` is reasonable | `semi_auto` | ⬜ not yet |
| 5.2.5 | `[Model Spec]` S_Overshoot complete and match datasheet | `manual` | — out of scope |
| 5.2.6 | `[Model Spec]` S_Overshoot track typ/min/max | `semi_auto` | ⬜ not yet |
| 5.2.7 | `[Model Spec]` D_Overshoot complete and match datasheet | `manual` | — out of scope |
| 5.2.8 | `[Model Spec]` D_Overshoot track typ/min/max | `semi_auto` | ⬜ not yet |
| 5.3.1 | I-V tables have correct typ/min/max order | `semi_auto` | ⬜ not yet |
| 5.3.2 | `[Pullup]` voltage sweep range is correct | `auto` | ✅ implemented |
| 5.3.3 | `[Pulldown]` voltage sweep range is correct | `auto` | ✅ implemented |
| 5.3.4 | `[POWER Clamp]` voltage sweep range is correct | `auto` | ✅ implemented |
| 5.3.5 | `[GND Clamp]` voltage sweep range is correct | `auto` | ✅ implemented |
| 5.3.6 | I-V tables do not exhibit stair-stepping | `semi_auto` | ⬜ not yet |
| 5.3.7 | Combined I-V tables are monotonic | `auto` | ✅ implemented |
| 5.3.8 | `[Pulldown]` I-V tables pass through zero/zero | `semi_auto` | ✅ auto portion |
| 5.3.9 | `[Pullup]` I-V tables pass through zero/zero | `semi_auto` | ✅ auto portion |
| 5.3.10 | No leakage current in clamp I-V tables | `semi_auto` | ⬜ not yet |
| 5.3.11 | I-V behavior not double-counted | `manual` | — out of scope |
| 5.3.12 | On-die termination modeling documented | `manual` | — out of scope |
| 5.3.13 | ECL models I-V tables swept from −Vcc to +2×Vcc | `auto` | ✅ implemented |
| 5.3.14 | Point distributions in I-V tables should be sufficient | `semi_auto` | ⬜ not yet |
| 5.4.1 | Output and I/O buffers have sufficient V-T tables | `semi_auto` | ⬜ not yet |
| 5.4.2 | V-T tables have reasonable point distribution | `semi_auto` | ⬜ not yet |
| 5.4.4 | V-T table endpoints match fixture voltages | `semi_auto` | ⬜ not yet |
| 5.5.1 | `[Ramp]` R_load present if value other than 50Ω | `auto` | ✅ implemented |
| 5.5.2 | `[Ramp]` typ/min/max order is correct | `semi_auto` | ⬜ not yet |
| 5.5.3 | `[Ramp]` dV consistent with I-V load-line | `auto` | ✅ implemented |
| 5.5.4 | `[Ramp]` dt consistent with 20–80% crossing time | `semi_auto` | ⬜ not yet |

---

### IQ Level 3 — 14 checks

| ID | Title | Class | Status |
|----|-------|-------|--------|
| 3.2.2 | `[Pin]` RLC values present and reasonable | `auto` | ✅ implemented |
| 3.3.2 | `[Diff Pin]` Vdiff and Tdelay_* complete and reasonable | `auto` | ✅ implemented |
| 5.2.1 | `[Model]` Vinl and Vinh reasonable | `manual` | — out of scope |
| 5.2.2 | `[Model Spec]` Vinl and Vinh reasonable | `manual` | — out of scope |
| 5.2.3 | `[Model Spec]` Vinl+/− and Vinh+/− complete and reasonable | `manual` | — out of scope |
| 5.2.9 | `[Receiver Thresholds]` Vth present and matches datasheet | `manual` | — out of scope |
| 5.2.10 | `[Receiver Thresholds]` Vth_min and Vth_max match datasheet | `manual` | — out of scope |
| 5.2.11 | `[Receiver Thresholds]` Vinh_ac, Vinl_ac match datasheet | `manual` | — out of scope |
| 5.2.12 | `[Receiver Thresholds]` Vinh_dc, Vinl_dc match datasheet | `manual` | — out of scope |
| 5.2.13 | `[Receiver Thresholds]` Tslew_ac/Tdiffslew_ac match datasheet | `manual` | — out of scope |
| 5.2.14 | `[Receiver Thresholds]` Threshold_sensitivity and Ext_ref | `manual` | — out of scope |
| 5.4.3 | V-T table duration is not excessive | `semi_auto` | ⬜ not yet |
| 5.6.1 | `[Model Spec]` Vmeas and Vref used if typ/min/max variation | `manual` | — out of scope |
| 5.6.2 | Vref consistent for Open-drain, Open-source, ECL | `semi_auto` | ⬜ not yet |

---

### IQ Level 4 — 17 checks

| ID | Title | Class | Status |
|----|-------|-------|--------|
| 3.1.3 | Package model includes power and ground pins | `manual` | — out of scope |
| 3.1.4 | On-die and on-package decoupling included | `manual` | — out of scope |
| 3.4.1 | `[Pin Mapping]` section included for each component | `auto` | ✅ implemented |
| 3.4.2 | `[Pin Mapping]` includes power and ground pins | `semi_auto` | ⬜ not yet |
| 3.4.3 | `[Merged Pins]` keyword present when applicable | `auto` | ✅ implemented |
| 5.7.1 | Output-capable models include `[ISSO PU]` and `[ISSO PD]` | `semi_auto` | ✅ auto portion |
| 5.7.2 | ISSO tables have correct typ/min/max order | `semi_auto` | ⬜ not yet |
| 5.7.3 | ISSO tables have sufficient point distribution | `semi_auto` | ⬜ not yet |
| 5.7.4 | ISSO tables voltage sweep range is correct | `semi_auto` | ⬜ not yet |
| 5.8.1 | Every `[Rising/Falling Waveform]` includes `[Composite Current]` | `auto` | ✅ implemented |
| 5.8.2 | `[Composite Current]` covers same time range as V-T | `auto` | ✅ implemented |
| 5.8.3 | `[Composite Current]` time-aligned with V-T | `semi_auto` | ⬜ not yet |
| 5.8.4 | `[Composite Current]` includes pre-driver behavior | `manual` | — out of scope |
| 5.8.5 | `[Composite Current]` start/end correlates with I-V | `semi_auto` | ⬜ not yet |
| 5.8.6 | `[Composite Current]` current from correct rails | `manual` | — out of scope |
| 5.8.7 | `[Composite Current]` curve flat at start and end | `semi_auto` | ⬜ not yet |
| 5.8.8 | `[Composite Current]` = 0 at start/end when V_fixture=0 | `auto` | ✅ implemented |

---

### Optional

| ID | Title | Class | Status |
|----|-------|-------|--------|
| 5.2.4 | `[Model Spec]` Pulse subparameters complete | `optional` | — out of scope |

---

## NA Handling

**NA** means the rule does not apply to this specific item. It is not a
failure and does not block any IQ level claim. Key NA conditions:

- **Bare-die components** (stub `[Package]` values ≈0.001nH/pF): checks
  3.1.1, 3.1.2, 3.4.1 are NA
- **Input-only models** (no `[Pullup]`/`[Pulldown]` tables): checks 5.3.2,
  5.3.3, 5.3.8, 5.3.9, 5.7.1 are NA
- **ECL models**: check 5.7.1 (ISSO) is NA
- **Components without `[Diff Pin]`**: checks 3.3.1, 3.3.2 are NA
- **Technology exceptions** for zero-crossing (TTL, PECL, LVDS, SERDES):
  checks 5.3.8 and 5.3.9 are NA — detected automatically from `Model_type`

---

## Numeric Tolerances

All thresholds live in `config.py`. Calibrate here for your technology:

| Constant | Default | Check |
|----------|---------|-------|
| `PKG_L_MAX_H` | 100 nH | 3.1.2 |
| `PKG_C_MAX_F` | 100 pF | 3.1.2 |
| `PKG_R_MAX_OHM` | 10 Ω | 3.1.2 |
| `PIN_TD_MAX_S` | 300 ps | 3.2.2 |
| `PIN_Z0_MAX_OHM` | 100 Ω | 3.2.2 |
| `IV_RANGE_TOLERANCE` | 2% of Vcc | 5.3.2–5.3.5 |
| `ZERO_CROSS_TOL_A` | 1 µA | 5.3.8, 5.3.9 |
| `RAMP_DV_TOLERANCE` | 5% | 5.5.3 |
| `ISSO_ENDPOINT_TOL` | 2% | 5.7.1 |
| `CC_ZERO_TOL_A` | 1 µA | 5.8.8 |
| `TIME_MATCH_TOL_S` | 1 fs | 5.8.2 |

---

## Adding a New Check

1. Create `checks/c<id>_<topic>.py`
2. Subclass `CheckModule`, set `check_ids`, `iq_level`, `auto_class`
3. Implement `run(self, ibis_file) -> list[CheckResult]`

The runner discovers it automatically — no registration step needed.

```python
from checks.base import CheckModule, CheckResult
from parser.ibis_parser import IBISFile

class Check5_3_6(CheckModule):
    check_ids  = ["5.3.6"]
    iq_level   = "LEVEL 2"
    auto_class = "semi_auto"

    def run(self, ibis_file: IBISFile) -> list[CheckResult]:
        results = []
        for model in ibis_file.models.values():
            # compute Appendix A smoothness metric...
            results.append(self._pass("5.3.6", model.name, "Smoothness OK"))
        return results
```

The `automation.how` field in `ibis_quality_spec_3_0.json` gives the
authoritative implementation guidance for each check ID.

---

## Known Calibration Items

Findings from running against Micron DDR4 z41c (reference file, IBIS 5.0):

| Check | Observation | Fix needed |
|-------|-------------|-----------|
| 3.2.2 | Bare-die pins are numbered differently and have no RLC — flagged incorrectly | Add bare-die NA to per-pin loop |
| 3.3.2 | Inverting pin model type looked up via non-inverting pin — CLKIN misclassified | Look up `inv_pin` model separately |
| 5.5.3 | Load-line intersection fails for DDR4 (Vcc-relative convention not fully applied before solving) | Apply Vcc offset before intersection |
| 5.7.1 | ISSO PU voltage axis mismatch for some model types | Align ISSO PU axis with [Pullup] convention |
| 5.8.8 | ±1µA tolerance is borderline for DDR4 ODT models (1.1–1.3µA observed) | Raise to ±2µA or make technology-conditional |

---

## Out of Scope

The following are not evaluated by this tool and require a qualified
engineer with the referenced external data:

- All 20 **`manual`** checks — require datasheet, SPICE model, or extraction
  documentation
- **Special designators G and M** — require hardware measurements or SPICE
  simulation results; see the
  [I/O Buffer Accuracy Handbook](https://www.ibis.org/accuracy/)
- **Special designator S** — requires SPICE model and simulation results
- **IQ score computation** — the tool reports findings; writing the final
  score into the file is the user's responsibility

---

## References

- [IBIS Quality Specification v3.0](https://ibis.org/quality_ver3.0/) (Sep 2023)
- [IBIS Specification v8.0](https://ibis.org/ver8.0/) (Dec 2025)
- [I/O Buffer Accuracy Handbook](https://www.ibis.org/accuracy/)
- [IBISCHK parser](https://ibis.org/ibischk/)