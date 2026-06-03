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
| `auto` | 22 | Fully deterministic — parser rules and numeric checks, no reviewer needed |
| `semi_auto` | 25 | Tool computes evidence; reviewer confirms edge cases or technology exceptions |
| `manual` | 20 | Requires external data — datasheet, SPICE model, or extraction documentation |
| `optional` | 1 | Good practice; does not affect the IQ score |

This tool currently implements all **22 `auto` checks** plus evidence
collectors for all **25 `semi_auto` checks**, and produces a
structured report that surfaces evidence for the remaining checks so a
reviewer can work efficiently.

For the detailed item-by-item implementation reference, including exact
thresholds, PASS/FAIL/WARN/NA behavior, review flags, and known judgement
calls, see [`../docs/implemented-checks.md`](../docs/implemented-checks.md).
For manual items that still require datasheet, extraction, package, or circuit
review, see [`../docs/manual-checks.md`](../docs/manual-checks.md).

---

## Requirements

- Python 3.9 or later
- No third-party packages — standard library only
- `ibischk` or `ibischk7` on PATH (optional): enables check 2.1 execution

---

## Quick Start

```bash
# Default: run through IQ3 and show failures, warnings, and errors only
python ibis_qa.py my_model.ibs

# Run through IQ3 and show everything including PASS and NA
python ibis_qa.py my_model.ibs --verbose

# Structured JSON output for downstream tooling
python ibis_qa.py my_model.ibs --json > report.json

# JSON with a non-default load impedance for reported Zout estimates
python ibis_qa.py my_model.ibs --json --zout-rload 40 > report.json

# Model-maker-facing Markdown report
python ibis_qa.py my_model.ibs --markdown > report.md

# Model-maker-facing Markdown report with per-model SVG visual curves
python ibis_qa.py my_model.ibs --markdown --plot-dir report_assets > report.md

# Standalone shareable HTML report with embedded SVG visual curves
python ibis_qa.py my_model.ibs --html --plot-dir report_assets > report.html

# Explicitly run and report only checks up to IQ3
python ibis_qa.py my_model.ibs --max-level 3 --markdown --plot-dir report_assets > report.md

# Include IQ4 checks
python ibis_qa.py my_model.ibs --max-level 4 --markdown --plot-dir report_assets > report.md

# Spreadsheet checklist report, compatible with Excel
python ibis_qa.py my_model.ibs --spreadsheet report.xlsx

# IQ3 run with saved GUI review decisions applied to the spreadsheet
python ibis_qa.py my_model.ibs --spreadsheet report.xlsx --max-level 3 --review report.review.json

# Simple GUI for running QA and recording semi-auto review decisions
python gui.py
```

From the repository root, launch the same GUI with:

```powershell
python ibis_qa_tool\gui.py
```

### GUI review workflow

The GUI lets a reviewer choose an IBIS file, run the same parser/checker
pipeline as the CLI, inspect non-passing findings, and work through the
semi-auto `review_required` queue. Reviewer decisions are saved separately
as `*.review.json`, preserving the generated QA report and attaching each
comment/decision to a stable `result_id`.

Spreadsheet generation can optionally apply that `*.review.json` overlay.
Accepted items render as `PASS`, exceptions render as `EXCEPTION`, rejected
items remain blocking, and not-applicable decisions render as `NA`. By default,
CLI and GUI runs target IQ3. Use
`--max-level 1|2|3|4` to run and report only checks up to the requested target
IQ level. The older `--target-level` spelling is kept as a CLI alias. For
example, `--max-level 3` skips IQ4 checks entirely, omits IQ4 results from JSON,
Markdown, and spreadsheet outputs, and caps candidate scores at IQ3. Use
`--max-level 4` when IQ4 evidence should be generated.

Each JSON result includes `check_id`, `iq_level`, and `numeric_level` so
findings and review decisions preserve the originating IQ quality level.
Each JSON model entry also includes a `zout` block with typ/min/max
Pullup/Pulldown load-line output-impedance estimates when the model has usable
driver I-V tables. The same Zout summary appears in the Markdown, HTML, and
spreadsheet reports, and Markdown/HTML visual assets include per-model Zout
load-line plots with operating-point markers. These values are characterization
data and do not affect PASS/FAIL status or candidate IQ scoring.
When saving a QA report from the GUI, the tool writes `*.qa.json`, a matching
model-maker-facing `*.qa.md` report, a `*_assets/` folder of per-model SVG
visual curves, a shareable `*.qa.html` report, and a checklist-style `*.qa.xlsx`
spreadsheet report. The SVG
assets include broad overview plots for I-V, ISSO, and V-T/Composite Current
tables when the source model contains that data. The plots include relevant
FAIL/WARN/ERROR attention callouts when a related visual-family check needs
review. I-V output is split into a main figure that shows the actual available
combined or clamp/driver curves, a clamp-only detail figure for `5.3.10`
leakage review, and a pullup/pulldown zero-current detail figure for
`5.3.8`/`5.3.9` review. Zout output is shown as a separate load-line figure
for each model with usable Pullup/Pulldown driver tables.
WARN/FAIL QA rows link to the relevant curve figure, and each linked figure
links back to the related QA item. The Markdown
report omits local file paths and tool workflow fields,
adds a table of contents, lists every required check item by IQ level and
scope/type, includes IBISCHK execution evidence under check `2.1`, shows
per-model candidate scores with visual curves, and keeps IQ level and special
designator explanations in appendices.
The HTML report embeds those SVG curves directly as data URIs, so the `.html`
file can be shared by itself; the asset folder is still written for the
Markdown report and for inspection/debugging.

Candidate scores are intentionally optimistic: they report the highest
implemented IQ level with no `FAIL` or `ERROR`. `WARN`/review-required items do
not lower the candidate score by themselves, but they remain visible and require
reviewer acceptance before a final IQ score is assigned.

### Sample output

```
========================================================================
IBIS QA Report — AUTO Checks and SEMI-AUTO Evidence
File   : z41c.ibs
IBIS Ver: 5.0   File Rev: 2.3   Date: 6/19/2022
IQ Score in file: (not found)
========================================================================

[2.1] ✓  (0 fail, 3 pass, 0 NA, total 3)
  ✓ [z41c.ibs] No existing '|IQ Score:' tag found inside the .ibs file.
  ✓ [z41c.ibs] IBISCHK: 0 errors, 0 warning(s)

[3.1.1] ✓  (0 fail, 3 pass, 3 NA, total 6)

[5.8.1] ✗  (2 fail, 24 pass, 0 NA, total 26)
  ✗ [ALERT] Falling Waveform #1: [Composite Current] absent

========================================================================
SUMMARY
  FAIL  : 34   WARN  : 100   PASS  : 633   NA  : 735   ERROR : 0
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
├── gui.py                       Tkinter GUI for QA review workflow
├── config.py                    All numeric tolerances — tune here
├── runner.py                    Auto-discovers and runs all check modules
├── reporter.py                  Text, JSON, and Markdown output formatting
├── plotting.py                  SVG plot generation for report visual curves
├── spreadsheet.py               Excel .xlsx checklist report generation
├── zout.py                      Pullup/Pulldown load-line Zout estimates
├── ibis_quality_spec_3_0.json   Canonical check definitions (source of truth)
├── parser/
│   └── ibis_parser.py           Single-pass IBIS tokeniser → IBISFile object
└── checks/
    ├── base.py                  CheckResult, Status, CheckModule base class
    ├── c2_1_ibischk.py          Check 2.1
    ├── c3_1_package.py          Checks 3.1.1, 3.1.2
    ├── c3_component_structural.py   Checks 3.2.2, 3.3.1, 3.3.2, 3.4.1, 3.4.3
    ├── c3_semiauto_structural.py    Checks 3.2.1, 3.4.2, 4.1
    ├── c5_3_iv_tables.py        Checks 5.3.1–5.3.9, 5.3.13
    ├── c5_semiauto_ordering.py  Checks 5.1.1, 5.2.6, 5.2.8, 5.5.2, 5.7.2
    ├── c5_semiauto_wave_quality.py  Evidence for remaining 5.x semi-auto checks
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

> **Note on §1.4 (IQ score in file):** The spec requires the final IQ score
> string to be written inside the `.ibs` file itself, not only in an external
> quality report. Because this tool is intended to help assign that score,
> a missing existing `|IQ Score:` tag is reported as a writeback note and does
> not fail check 2.1.
> Missing in-file IBISCHK version documentation is also reported as a note,
> not as a Level 1 blocker.

---

### IQ Level 2 — 35 checks

| ID | Title | Class | Status |
|----|-------|-------|--------|
| 3.1.1 | `[Package]` must have typ/min/max values | `auto` | ✅ implemented |
| 3.1.2 | `[Package]` model values must be reasonable | `semi_auto` | ✅ auto portion |
| 3.2.1 | `[Pin]` section complete | `semi_auto` | ✅ evidence |
| 3.3.1 | `[Diff Pin]` referenced pin models match | `semi_auto` | ✅ auto portion |
| 4.1 | `[Model Selector]` entries have reasonable descriptions | `semi_auto` | ✅ evidence |
| 4.2 | Default `[Model Selector]` entries are consistent | `manual` | — out of scope |
| 5.1.1 | `[Model]` parameters have correct typ/min/max order | `semi_auto` | ✅ evidence |
| 5.1.2 | `[Model]` C_comp is reasonable | `semi_auto` | ✅ evidence |
| 5.1.3 | `[Temperature Range]` is reasonable | `manual` | — out of scope |
| 5.1.4 | `[Voltage Range]` or `[* Reference]` is reasonable | `semi_auto` | ✅ evidence |
| 5.2.5 | `[Model Spec]` S_Overshoot complete and match datasheet | `manual` | — out of scope |
| 5.2.6 | `[Model Spec]` S_Overshoot track typ/min/max | `semi_auto` | ✅ evidence |
| 5.2.7 | `[Model Spec]` D_Overshoot complete and match datasheet | `manual` | — out of scope |
| 5.2.8 | `[Model Spec]` D_Overshoot track typ/min/max | `semi_auto` | ✅ evidence |
| 5.3.1 | I-V tables have correct typ/min/max order | `auto` | ✅ implemented |
| 5.3.2 | `[Pullup]` voltage sweep range is correct | `auto` | ✅ implemented |
| 5.3.3 | `[Pulldown]` voltage sweep range is correct | `auto` | ✅ implemented |
| 5.3.4 | `[POWER Clamp]` voltage sweep range is correct | `auto` | ✅ implemented |
| 5.3.5 | `[GND Clamp]` voltage sweep range is correct | `auto` | ✅ implemented |
| 5.3.6 | I-V tables do not exhibit stair-stepping | `semi_auto` | ✅ evidence |
| 5.3.7 | Combined I-V tables are monotonic | `auto` | ✅ implemented |
| 5.3.8 | `[Pulldown]` I-V tables pass through zero/zero | `semi_auto` | ✅ auto portion |
| 5.3.9 | `[Pullup]` I-V tables pass through zero/zero | `semi_auto` | ✅ auto portion |
| 5.3.10 | No leakage current in clamp I-V tables | `semi_auto` | ✅ evidence |
| 5.3.11 | I-V behavior not double-counted | `manual` | — out of scope |
| 5.3.12 | On-die termination modeling documented | `manual` | — out of scope |
| 5.3.13 | ECL models I-V tables swept from −Vcc to +2×Vcc | `auto` | ✅ implemented |
| 5.3.14 | Point distributions in I-V tables should be sufficient | `semi_auto` | ✅ evidence |
| 5.4.1 | Output and I/O buffers have sufficient V-T tables | `semi_auto` | ✅ evidence |
| 5.4.2 | V-T tables have reasonable point distribution | `semi_auto` | ✅ evidence |
| 5.4.4 | V-T table endpoints match fixture voltages | `semi_auto` | ✅ evidence |
| 5.5.1 | `[Ramp]` R_load present if value other than 50Ω | `auto` | ✅ implemented |
| 5.5.2 | `[Ramp]` typ/min/max order is correct | `semi_auto` | ✅ evidence |
| 5.5.3 | `[Ramp]` dV consistent with I-V load-line | `auto` | ✅ implemented |
| 5.5.4 | `[Ramp]` dt consistent with 20–80% crossing time | `semi_auto` | ✅ evidence |

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
| 5.4.3 | V-T table duration is not excessive | `semi_auto` | ✅ evidence |
| 5.6.1 | `[Model Spec]` Vmeas and Vref used if typ/min/max variation | `manual` | — out of scope |
| 5.6.2 | Vref consistent for Open-drain, Open-source, ECL | `semi_auto` | ✅ evidence |

---

### IQ Level 4 — 17 checks

| ID | Title | Class | Status |
|----|-------|-------|--------|
| 3.1.3 | Package model includes power and ground pins | `manual` | — out of scope |
| 3.1.4 | On-die and on-package decoupling included | `manual` | — out of scope |
| 3.4.1 | `[Pin Mapping]` section included for each component | `auto` | ✅ implemented |
| 3.4.2 | `[Pin Mapping]` includes power and ground pins | `semi_auto` | ✅ evidence |
| 3.4.3 | `[Merged Pins]` keyword present when applicable | `auto` | ✅ implemented |
| 5.7.1 | Output-capable models include `[ISSO PU]` and `[ISSO PD]` | `semi_auto` | ✅ auto portion |
| 5.7.2 | ISSO tables have correct typ/min/max order | `semi_auto` | ✅ evidence |
| 5.7.3 | ISSO tables have sufficient point distribution | `semi_auto` | ✅ evidence |
| 5.7.4 | ISSO tables voltage sweep range is correct | `semi_auto` | ✅ evidence |
| 5.8.1 | Every `[Rising/Falling Waveform]` includes `[Composite Current]` | `auto` | ✅ implemented |
| 5.8.2 | `[Composite Current]` covers same time range as V-T | `auto` | ✅ implemented |
| 5.8.3 | `[Composite Current]` time-aligned with V-T | `semi_auto` | ✅ evidence |
| 5.8.4 | `[Composite Current]` includes pre-driver behavior | `manual` | — out of scope |
| 5.8.5 | `[Composite Current]` start/end correlates with I-V | `semi_auto` | ✅ evidence |
| 5.8.6 | `[Composite Current]` current from correct rails | `manual` | — out of scope |
| 5.8.7 | `[Composite Current]` curve flat at start and end | `semi_auto` | ✅ evidence |
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
  3.1.1, 3.1.2, 3.2.2, 3.4.1 are NA
- **Input-only models** (no `[Pullup]`/`[Pulldown]` tables): checks 5.3.2,
  5.3.3, 5.3.8, 5.3.9, 5.7.1 are NA
- **Single-ended open models**: open-drain/open-sink models without
  `[Pullup]` and open-source models without `[Pulldown]` report NA for the
  corresponding I-V sweep and zero-crossing rows
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

| Check | Observation | Current status |
|-------|-------------|----------------|
| 3.2.2 | Bare-die pins are numbered differently and have no packaged per-pin RLC | Bare-die components now report NA |
| 3.3.2 | Micron uses input differential `Tdelay_typ=0ns` rows that the strict rule treated as failures | Zero-valued input-side `Tdelay_typ` now passes; hard Vdiff issues still fail and nonzero input Tdelay remains review evidence |
| 5.3.8/5.3.9 | ±1µA zero-current tolerance is borderline for some DDR4 rows and the spec allows special cases | Any over-limit zero-current row now reports review-required WARN instead of FAIL |
| 5.7.1 | ISSO PU voltage axis mismatch for DQ/DQS models | Endpoint comparison now uses `Ipu(Vcc)` |
| 5.8.8 | ±1µA tolerance is borderline for DDR4 ODT models (1.1–1.3µA observed) | Still pending calibration |

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
