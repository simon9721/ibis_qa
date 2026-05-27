#!/usr/bin/env python3
"""Build structured IBIS Quality Specification data from local source files."""

from __future__ import annotations

import json
import re
import zipfile
from datetime import date
from pathlib import Path
from xml.etree import ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
SPEC_MD = ROOT / "quality_ver3.0.md"
CHECKLIST_XLSX = ROOT / "ibis_quality_3.0_checklist_auto.xlsx"
DATA_OUT = ROOT / "data" / "ibis_quality_spec_3_0.json"
DOC_OUT = ROOT / "docs" / "qa-methods.md"

NS = {
    "m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
}


AUTOMATION_OVERRIDES = {
    "2.1": ("auto", "Run IBISCHK, parse version/errors/warnings/cautions, and require documented exceptions for any remaining warnings."),
    "3.1.1": ("auto", "Parse [Package] values and require typ/min/max values instead of NA."),
    "3.1.2": ("semi_auto", "Numeric limits and typ/min/max ordering can be checked automatically; modeling assumptions still need review."),
    "3.1.3": ("manual", "The tool can detect package-model mechanisms, but inclusion of power/ground coupling and method quality require engineering review."),
    "3.1.4": ("manual", "The tool can detect PDN/decoupling-related keywords, but sufficiency of on-die/on-package decoupling is a modeling judgment."),
    "3.2.1": ("semi_auto", "Parser can check pin syntax and NC/POWER/GND naming; completeness versus the datasheet requires external data."),
    "3.2.2": ("auto", "Presence of pin RLC or [Package Model], plus TD and Z0 limits, can be computed from the IBIS data."),
    "3.3.1": ("semi_auto", "Model-name matching is automatic; non-matching pairs require comment or [Notes] review."),
    "3.3.2": ("auto", "Presence, polarity, zero/NA rules, and output/input applicability can be checked from [Diff Pin] and model types."),
    "3.4.1": ("auto", "Presence and coverage of [Pin Mapping] can be checked from [Pin] and IBIS version rules."),
    "3.4.2": ("semi_auto", "Version-dependent coverage can be checked; rail-label intent may need review."),
    "3.4.3": ("auto", "If package model data uses merged pins, require [Merged Pins]."),
    "4.1": ("semi_auto", "The tool can detect missing descriptions; reasonableness and usefulness are reviewer judgments."),
    "4.2": ("manual", "Default model selector consistency depends on product configuration and likely use cases."),
    "5.1.1": ("semi_auto", "Column order can be checked numerically, but technology-specific weak/strong exceptions require review."),
    "5.1.2": ("semi_auto", "C_comp positivity and C_comp_* sums can be computed; plausibility and comments above 20 pF require review."),
    "5.1.3": ("manual", "Requires extraction conditions, technology behavior, and datasheet operating temperature comparison."),
    "5.1.4": ("semi_auto", "Voltage presence/order/consistency can be checked; extraction and datasheet fit require review."),
    "5.2.1": ("manual", "Requires comparing thresholds against datasheet and Vmeas intent."),
    "5.2.2": ("manual", "Requires datasheet threshold ranges and supply variation interpretation."),
    "5.2.3": ("manual", "Requires datasheet/hysteresis intent plus comment review for exceptions."),
    "5.2.4": ("optional", "Optional good-practice check; depends on datasheet pulse behavior and IBIS representability."),
    "5.2.5": ("manual", "Requires datasheet functional overshoot limits."),
    "5.2.6": ("semi_auto", "Corner tracking can be checked when values exist; correctness of limits still needs datasheet context."),
    "5.2.7": ("manual", "Requires datasheet dynamic overshoot limits and documented conversion method."),
    "5.2.8": ("semi_auto", "Corner tracking can be checked when values exist; correctness of limits still needs datasheet context."),
    "5.2.9": ("manual", "Requires datasheet timing threshold and receiver-threshold applicability."),
    "5.2.10": ("manual", "Requires datasheet Vth tolerance interpretation."),
    "5.2.11": ("manual", "Requires datasheet AC threshold values and offset conversion review."),
    "5.2.12": ("manual", "Requires datasheet DC threshold values and offset conversion review."),
    "5.2.13": ("manual", "Requires datasheet slew-limit values and differential/single-ended applicability."),
    "5.2.14": ("manual", "Requires datasheet/reference-supply behavior."),
    "5.3.1": ("semi_auto", "Column order and curve order can be checked; active-region exceptions need review."),
    "5.3.2": ("auto", "Voltage sweep range can be checked from [Pullup Reference] or [Voltage Range]."),
    "5.3.3": ("auto", "Voltage sweep range can be checked from [Pullup Reference] or [Voltage Range]."),
    "5.3.4": ("auto", "Voltage sweep range can be checked from [POWER Clamp Reference] or [Voltage Range]."),
    "5.3.5": ("auto", "Voltage sweep range can be checked from [POWER Clamp Reference] or [Voltage Range]."),
    "5.3.6": ("semi_auto", "Smoothness/stair-step metrics can flag problems, with plot review as backup."),
    "5.3.7": ("auto", "Combined-table monotonicity can be checked numerically and by IBISCHK."),
    "5.3.8": ("semi_auto", "Zero-crossing can be checked; technology exceptions must be documented."),
    "5.3.9": ("semi_auto", "Zero-crossing can be checked; technology exceptions must be documented."),
    "5.3.10": ("semi_auto", "Leakage thresholds can be checked; special technologies and extrapolation need review."),
    "5.3.11": ("manual", "Double-counting of clamp, driver, and termination behavior needs curve/context review."),
    "5.3.12": ("manual", "Requires documentation review for on-die termination modeling method."),
    "5.3.13": ("auto", "Conditional ECL sweep range can be checked when model type/supplies are known."),
    "5.3.14": ("semi_auto", "Point-density and smoothness metrics can flag sparse inflection regions."),
    "5.4.1": ("semi_auto", "Waveform count and fixture values can be checked; technology sufficiency needs review."),
    "5.4.2": ("semi_auto", "Point density and smoothness can be measured, with visual review for curve quality."),
    "5.4.3": ("semi_auto", "Duration and ending slope can be measured; max-rate target may need datasheet input."),
    "5.4.4": ("semi_auto", "Endpoint/fixture comparison can be checked; technology exceptions need review."),
    "5.5.1": ("auto", "Require R_load when [Ramp] load differs from 50 ohms."),
    "5.5.2": ("semi_auto", "The tool can compare ordering to extraction corners; corner intent may need review."),
    "5.5.3": ("auto", "Calculate dV from I-V load-line values and compare against the 5 percent tolerance."),
    "5.5.4": ("semi_auto", "20-80 percent crossing can be measured when matching V-T tables exist; alternate references need review."),
    "5.6.1": ("manual", "Requires deciding whether Vmeas/Vref variation exists across corners."),
    "5.6.2": ("semi_auto", "Model-type reference-voltage rules can be checked, with exceptions reviewed."),
    "5.7.1": ("semi_auto", "ISSO table presence and IBISCHK correlation equations can be checked; curve correlation may need review."),
    "5.7.2": ("semi_auto", "Typ/min/max order can be checked numerically; short curve crossovers need review."),
    "5.7.3": ("semi_auto", "Point-density and smoothness metrics can flag sparse inflection regions."),
    "5.7.4": ("semi_auto", "Sweep coverage can be checked; negative-side breakdown exceptions need review."),
    "5.8.1": ("auto", "Require [Composite Current] under each rising/falling waveform."),
    "5.8.2": ("auto", "Compare first/last time points against the parent V-T waveform."),
    "5.8.3": ("semi_auto", "Time alignment can be measured, but expected current peak shape may need review."),
    "5.8.4": ("manual", "Pre-driver current inclusion requires circuit/extraction knowledge."),
    "5.8.5": ("semi_auto", "Endpoint current load-line checks can be computed; waived cases need comments."),
    "5.8.6": ("manual", "Correct supply-rail aggregation cannot be proven from the IBIS file alone."),
    "5.8.7": ("semi_auto", "Start/end derivative flatness can be measured numerically."),
    "5.8.8": ("auto", "V_fixture=0 start/end zero-current rules can be checked from waveform data."),
}

HOW_OVERRIDES = {
    "2.1": "Run the appropriate IBISCHK version for the file's [IBIS Ver], capture the full output, parse version/errors/warnings/cautions, fail on any error, and require [Notes]/comments plus the X designator for unresolved warnings.",
    "3.1.1": "Parse each [Package] R_pkg, L_pkg, and C_pkg row and require populated typical, minimum, and maximum values for the target IQ level.",
    "3.1.2": "Check package R/L/C values against the spec limits, verify min < typ < max, and surface any missing comments about modeling assumptions for reviewer confirmation.",
    "3.1.3": "Detect package-model mechanisms such as [Define Package Model], [Interconnect Model], [External Circuit], or EMD references, then have a reviewer confirm power/ground pins and coupling are actually represented.",
    "3.1.4": "Detect PDN/decoupling-related keywords and package-model references, then require reviewer evidence that on-die and on-package decoupling are included sufficiently for SSO/power-aware use.",
    "3.2.1": "Parse [Pin] entries, check NC/POWER/GND conventions, and compare model assignments against an external pin list or datasheet when available.",
    "3.2.2": "For every signal pin, require R/L/C values or a [Package Model], compute TD = sqrt(LC) and Z0 = sqrt(L/C), and compare them to the spec limits.",
    "3.3.1": "Compare the model names on each [Diff Pin] pair; if they differ, find an explanatory comment or [Notes] entry and send it to the reviewer.",
    "3.3.2": "Use [Diff Pin] entries and referenced model types to check Vdiff/Tdelay presence, positive/zero/NA rules, and input/output applicability.",
    "3.4.1": "For each [Component], require [Pin Mapping] coverage for the non POWER/GND/NC pins required by the IBIS version rules.",
    "3.4.2": "Check POWER/GND mapping requirements using [Pin Mapping], [Bus Label], and [Die Supply Pads], then have a reviewer confirm rail-label intent.",
    "3.4.3": "Detect merged pin usage in package-model data and require a matching [Merged Pins] keyword.",
    "4.1": "For every [Model Selector] entry, verify that it has both a referenced model and a non-empty description; flag generic descriptions for reviewer judgment.",
    "4.2": "Present each selector's first/default entry side by side and have a reviewer confirm the defaults describe one plausible product configuration.",
    "5.1.1": "Parse typ/min/max data scoped by [Model], check ordering against weak/slow and strong/fast conventions, and route technology exceptions to review.",
    "5.1.2": "Check that C_comp and C_comp_* values are positive, that C_comp_* sums match C_comp by corner when both forms exist, and that values above 20 pF have comments.",
    "5.1.3": "Compare [Temperature Range] with extraction conditions and datasheet safe operating limits, including technology-specific interpretation of minimum and maximum corners.",
    "5.1.4": "Resolve [Voltage Range] and reference keyword defaults, check normal min < typ < max ordering and same-nominal-voltage consistency, then compare against datasheet/extraction evidence.",
    "5.2.1": "Compare [Model] Vinl/Vinh to datasheet values, [Model Spec] values when present, and Vmeas expectations for I/O models.",
    "5.2.2": "Compare [Model Spec] Vinl/Vinh ranges against datasheet thresholds and the supply variation represented by [Voltage Range].",
    "5.2.3": "Determine from the datasheet whether edge-specific or hysteresis thresholds are required, then compare Vinl+/Vinl-/Vinh+/Vinh- and comments.",
    "5.2.4": "If the datasheet defines pulse immunity behavior, check for Pulse_high, Pulse_low, and Pulse_time in [Model Spec] or document why the optional data is omitted.",
    "5.2.5": "Compare S_overshoot_high and S_overshoot_low values to datasheet functional overshoot limits for each input or I/O model.",
    "5.2.6": "When S_overshoot corners differ, compare their trend with supply/process corners and flag inconsistent corner tracking.",
    "5.2.7": "Compare D_overshoot_high, D_overshoot_low, and D_overshoot_time to datasheet dynamic overshoot rules and review any documented conversion method.",
    "5.2.8": "When D_overshoot corners differ, compare their trend with supply/process corners and flag inconsistent corner tracking.",
    "5.2.9": "Decide whether [Receiver Thresholds] are needed for the I/O standard, then compare Vth with the datasheet timing measurement threshold.",
    "5.2.10": "Compare Vth_min and Vth_max against datasheet typical-condition threshold tolerance, excluding supply variation unless the datasheet defines it that way.",
    "5.2.11": "Convert datasheet AC thresholds to IBIS offsets from Vth when necessary and compare Vinh_ac/Vinl_ac.",
    "5.2.12": "Convert datasheet DC thresholds to IBIS offsets from Vth when necessary and compare Vinh_dc/Vinl_dc.",
    "5.2.13": "Compare Tslew_ac or Tdiffslew_ac to the datasheet maximum input transition time for the applicable single-ended or differential receiver.",
    "5.2.14": "Review datasheet/reference-supply behavior and require Threshold_sensitivity plus Reference_supply/Ext_ref when Vth depends on an external or supply reference.",
    "5.3.1": "Parse every I-V table, confirm column order, compare typ/min/max curve ordering in the active region, and generate plots/evidence for exceptions.",
    "5.3.2": "Resolve Vcc from [Pullup Reference] or [Voltage Range] and check [Pullup] voltage coverage from -Vcc to +2*Vcc.",
    "5.3.3": "Resolve Vcc from [Pullup Reference] or [Voltage Range] and check [Pulldown] voltage coverage from -Vcc to +2*Vcc.",
    "5.3.4": "Resolve Vcc from [POWER Clamp Reference] or [Voltage Range] and check [POWER Clamp] coverage at least from -Vcc to 0.",
    "5.3.5": "Resolve Vcc from [POWER Clamp Reference] or [Voltage Range] and check [GND Clamp] coverage at least from -Vcc to +Vcc.",
    "5.3.6": "Run a stair-step or smoothness metric over I-V curves and generate plots so the reviewer can confirm whether flat sections and abrupt jumps are real issues.",
    "5.3.7": "Combine I-V tables according to IBIS rules and check for monotonically increasing current with no slope reversals; optionally cross-check with IBISCHK output.",
    "5.3.8": "Interpolate [Pulldown] currents at 0 V and check that typ/min/max are approximately 0 for full-swing technologies, with documented exceptions.",
    "5.3.9": "Interpolate [Pullup] currents at 0 V and check that typ/min/max are approximately 0 for full-swing technologies, with documented exceptions.",
    "5.3.10": "Measure clamp current in the normal operating range, including extrapolated values where needed, and flag leakage above 1 uA unless technology exceptions are documented.",
    "5.3.11": "Review plotted and combined clamp/driver/termination curves to confirm clamping and on-die termination behavior is not duplicated across tables.",
    "5.3.12": "Search comments/[Notes] for on-die termination labeling and modeling method, then have a reviewer confirm the description is sufficient.",
    "5.3.13": "For ECL model types, resolve the effective supply span and check I-V table voltage coverage from -Vcc to +2*Vcc.",
    "5.3.14": "Measure point density near inflection regions and run the smoothness metric from Appendix A to flag undersampled I-V curves.",
    "5.4.1": "Count [Rising Waveform] and [Falling Waveform] tables by model type, inspect fixture coverage, and require comments when fewer than the expected tables are present.",
    "5.4.2": "Measure V-T point density and second-derivative smoothness through transitions, and provide plots for reviewer confirmation.",
    "5.4.3": "Compare waveform duration to the expected data rate/frequency when available, check final DC settling and ending slope, and preserve relative timing evidence.",
    "5.4.4": "Compare V-T start/end voltages against V_fixture when fixture/reference conditions imply rail endpoints, then route technology exceptions to review.",
    "5.5.1": "Parse [Ramp] data and require an explicit R_load when the load is not the 50 ohm default.",
    "5.5.2": "Compare [Ramp] typ/min/max entries with the extraction corner labels used for I-V data and flag apparent numeric sorting or inconsistent corner order.",
    "5.5.3": "Use [Ramp] R_load and I-V load-line calculations to derive high/low voltages, compute 60 percent dV, and require agreement within 5 percent.",
    "5.5.4": "Select matching V-T fixtures when present, measure 20-80 percent crossing times, compare dt within 10 percent, and document any alternate reference.",
    "5.6.1": "Review whether Vref/Vmeas should vary across typ/min/max conditions and confirm [Model Spec] represents that variation when needed.",
    "5.6.2": "Check Vref relative to Vmeas and pullup/pulldown references for Open-drain, Open-source/Open-sink, and ECL model types.",
    "5.7.1": "For every output-capable model, require [ISSO PU] and [ISSO PD] tables and check IBISCHK endpoint correlation equations against pullup/pulldown curves.",
    "5.7.2": "Compare ISSO typ/min/max current magnitudes across voltage points and flag sustained violations while allowing reviewer-approved short crossovers.",
    "5.7.3": "Measure ISSO point density near inflection regions and run smoothness checks to flag interpolation risks.",
    "5.7.4": "Check [ISSO PU]/[ISSO PD] sweep coverage against +/- Vcc and require the +Vcc endpoint; route negative-side breakdown exceptions to review.",
    "5.8.1": "Walk each [Rising Waveform] and [Falling Waveform] table and require a subordinate [Composite Current] table.",
    "5.8.2": "Compare first and last time points of each [Composite Current] table to the parent waveform time range.",
    "5.8.3": "Interpolate composite-current and V-T data onto a common time grid, verify current peaks align with the transition region, and plot evidence.",
    "5.8.4": "Review extraction/circuit documentation and waveform timing to determine whether pre-driver current is included when it draws from the pullup reference rail.",
    "5.8.5": "Compute load-line endpoint currents from pullup/pulldown tables and compare with [Composite Current] start/end values; require comments for waived cases.",
    "5.8.6": "Review extraction documentation for multi-rail current aggregation and confirm excluded rails match [Pin Mapping] bus-label intent.",
    "5.8.7": "Estimate the derivative of [Composite Current] at the start and end of each table and flag non-flat endpoints.",
    "5.8.8": "When V_fixture = 0, check that falling-waveform composite current ends at 0 A and rising-waveform composite current starts at 0 A.",
}

DEFAULT_HOW_BY_CLASS = {
    "auto": "Implement as a deterministic parser/numeric check and store the computed evidence with the pass/fail result.",
    "semi_auto": "Implement as an evidence collector that computes the objective parts, then require reviewer confirmation for context-dependent cases.",
    "manual": "Represent this as a required reviewer checklist item with explicit evidence, comments, and exception tracking.",
    "optional": "Represent this as a visible non-gating checklist item with comments when the data is omitted.",
}

QUALITY_LEVELS = [
    {
        "id": "IQ0",
        "numeric_level": 0,
        "title": "Not Checked",
        "meaning": "No documented quality checking has been performed.",
    },
    {
        "id": "IQ1",
        "numeric_level": 1,
        "title": "Passes IBISCHK",
        "meaning": "IBISCHK has been run with zero errors and documented handling of warnings.",
    },
    {
        "id": "IQ2",
        "numeric_level": 2,
        "title": "Suitable for Waveform Simulation",
        "meaning": "IQ1 plus all LEVEL 2 checks for basic waveform simulation data.",
    },
    {
        "id": "IQ3",
        "numeric_level": 3,
        "title": "Suitable for Timing Analysis",
        "meaning": "IQ2 plus all LEVEL 3 checks for timing analysis data.",
    },
    {
        "id": "IQ4",
        "numeric_level": 4,
        "title": "Suitable for Power-Aware Analysis",
        "meaning": "IQ3 plus all LEVEL 4 checks for power-aware modeling data.",
    },
]

SPECIAL_DESIGNATORS = [
    {
        "letter": "G",
        "name": "Contains Golden Waveforms",
        "meaning": "The file contains golden waveform data using [Test Data] and [Test Load] or equivalent external documentation.",
    },
    {
        "letter": "M",
        "name": "Measurement Correlated",
        "meaning": "IBIS simulation has been correlated against hardware measurements with documented methods/results.",
    },
    {
        "letter": "S",
        "name": "Simulation Correlated",
        "meaning": "IBIS simulation has been correlated against a reference simulation such as SPICE with documented methods/results.",
    },
    {
        "letter": "X",
        "name": "Exceptions",
        "meaning": "One or more checks require documented exceptions in [Notes] or comments.",
    },
]


def clean_text(text: str) -> str:
    replacements = {
        "\u2013": "-",
        "\u2014": "-",
        "\u2018": "'",
        "\u2019": "'",
        "\u201c": '"',
        "\u201d": '"',
        "\u00a0": " ",
    }
    for src, dst in replacements.items():
        text = text.replace(src, dst)
    text = re.sub(r"[ \t]+", " ", text)
    return text.strip()


def strip_md_markup(text: str) -> str:
    text = clean_text(text)
    text = text.strip("# ")
    text = re.sub(r"\*\*(.*?)\*\*", r"\1", text)
    return clean_text(text)


def paragraphize(lines: list[str]) -> list[str]:
    paragraphs: list[str] = []
    current: list[str] = []
    in_code = False

    def flush() -> None:
        nonlocal current
        if current:
            paragraphs.append(clean_text(" ".join(current)))
            current = []

    for raw in lines:
        line = clean_text(raw)
        if not line:
            flush()
            continue
        if line.startswith("IBIS Quality Specification Version"):
            continue
        if re.fullmatch(r"Page \d+", line):
            continue
        if line == "---":
            continue
        if line.startswith("```"):
            if in_code:
                current.append(line)
                flush()
                in_code = False
            else:
                flush()
                current.append(line)
                in_code = True
            continue
        current.append(line)
        if in_code:
            continue
    flush()
    return [p for p in paragraphs if p]


def classify_heading(heading: str) -> tuple[str, str | None, str | None, str]:
    heading = strip_md_markup(heading)
    appendix = re.match(r"^(Appendix\s+[A-Z])\s*[-:]\s*(.+)$", heading, flags=re.I)
    if appendix:
        return "appendix", appendix.group(1), None, clean_text(appendix.group(2))

    check = re.match(
        r"^(?P<id>\d+(?:\.\d+)+)\s+\{(?P<level>LEVEL\s+\d+|OPTIONAL)\}\s+(?P<title>.+)$",
        heading,
        flags=re.I,
    )
    if check:
        return "check", check.group("id"), check.group("level").upper(), clean_text(check.group("title"))

    numbered = re.match(r"^(?P<id>\d+(?:\.\d+)*)(?:\.)?\s+(?P<title>.+)$", heading)
    if numbered:
        return "section", numbered.group("id"), None, clean_text(numbered.group("title"))

    return "note", None, None, heading


def parse_markdown() -> tuple[list[dict], list[dict], list[dict]]:
    lines = SPEC_MD.read_text(encoding="utf-8").splitlines()
    body_start = next(i for i, line in enumerate(lines) if line.startswith("## 1. IBIS Quality Designator"))
    records: list[dict] = []
    current: dict | None = None
    current_lines: list[str] = []

    def flush() -> None:
        nonlocal current, current_lines
        if current:
            current["paragraphs"] = paragraphize(current_lines)
            records.append(current)
        current = None
        current_lines = []

    for line_number, raw in enumerate(lines[body_start:], start=body_start + 1):
        stripped = raw.strip()
        normalized = strip_md_markup(stripped[3:] if stripped.startswith("## ") else stripped)

        # The PDF-to-Markdown conversion split this check heading over two
        # headings. Fold the continuation back into the previous heading.
        if stripped.startswith("## ") and normalized.lower() == "data sheet, if needed" and current:
            current["title"] = clean_text(f"{current['title']} {normalized}")
            continue

        is_heading = stripped.startswith("## ")
        is_lost_heading = bool(re.match(r"^5\.7\.1\s+\{LEVEL\s+4\}", normalized))
        if is_heading or is_lost_heading:
            kind, section_id, level, title = classify_heading(normalized)
            if kind == "note" and current and current.get("kind") == "check":
                current_lines.append(f"{title}:")
                continue
            flush()
            extra_body = []
            if section_id == "5.7.1" and " The ISSO table data " in title:
                title, extra = title.split(" The ISSO table data ", 1)
                extra_body.append(f"The ISSO table data {extra}")
            current = {
                "kind": kind,
                "id": section_id,
                "level": level,
                "title": title,
                "source_line": line_number,
            }
            current_lines.extend(extra_body)
            continue

        current_lines.append(raw)
    flush()

    sections = [record for record in records if record["kind"] in {"section", "appendix"}]
    checks = [record for record in records if record["kind"] == "check"]
    enrich_checks(checks, sections)
    return records, sections, checks


def nearest_parent_section(check_id: str, sections: list[dict]) -> dict | None:
    candidates = [
        section
        for section in sections
        if section.get("id")
        and check_id.startswith(f"{section['id']}.")
        and section["id"] != check_id
    ]
    if not candidates:
        return None
    return sorted(candidates, key=lambda item: len(item["id"]), reverse=True)[0]


def extract_keywords(text: str) -> list[str]:
    return sorted(set(re.findall(r"\[[^\]\n]+\]", text)))


def enrich_checks(checks: list[dict], sections: list[dict]) -> None:
    for check in checks:
        level = check["level"]
        optional = level == "OPTIONAL"
        numeric_level = None if optional else int(re.search(r"\d+", level).group(0))
        parent = nearest_parent_section(check["id"], sections)
        text = " ".join([check["title"], *check.get("paragraphs", [])])
        automation_class, rationale = AUTOMATION_OVERRIDES.get(
            check["id"],
            ("manual", "Not yet classified; default to reviewer-controlled until implemented."),
        )
        how = HOW_OVERRIDES.get(check["id"], DEFAULT_HOW_BY_CLASS[automation_class])
        check.update(
            {
                "numeric_level": numeric_level,
                "optional": optional,
                "section_id": parent["id"] if parent else None,
                "section_title": parent["title"] if parent else None,
                "ibis_keywords": extract_keywords(text),
                "automation": {
                    "class": automation_class,
                    "rationale": rationale,
                    "how": how,
                },
            }
        )


def excel_col(cell_ref: str) -> str:
    return re.match(r"[A-Z]+", cell_ref).group(0)


def normalize_spec_ref(value: str) -> str:
    value = clean_text(value)
    if re.fullmatch(r"\d+(?:\.\d+)?", value):
        number = float(value)
        if abs(number - round(number, 1)) < 1e-8:
            return f"{number:.1f}"
        return ("%f" % number).rstrip("0").rstrip(".")
    return value


def read_workbook() -> dict:
    with zipfile.ZipFile(CHECKLIST_XLSX) as archive:
        shared_root = ET.fromstring(archive.read("xl/sharedStrings.xml"))
        shared_strings = [
            "".join(t.text or "" for t in si.findall(".//m:t", NS))
            for si in shared_root.findall("m:si", NS)
        ]

        workbook = ET.fromstring(archive.read("xl/workbook.xml"))
        rels = ET.fromstring(archive.read("xl/_rels/workbook.xml.rels"))
        rel_map = {rel.attrib["Id"]: rel.attrib["Target"] for rel in rels}
        sheet_map: dict[str, str] = {}
        for sheet in workbook.find("m:sheets", NS):
            rel_id = sheet.attrib[f"{{{NS['r']}}}id"]
            sheet_map[sheet.attrib["name"]] = "xl/" + rel_map[rel_id]

        def cell_value(cell: ET.Element) -> str:
            value = cell.find("m:v", NS)
            if value is None:
                return ""
            raw = value.text or ""
            if cell.attrib.get("t") == "s":
                return clean_text(shared_strings[int(raw)])
            return clean_text(raw)

        sheets: dict[str, list[dict]] = {}
        for name, path in sheet_map.items():
            root = ET.fromstring(archive.read(path))
            rows: list[dict] = []
            for row in root.findall(".//m:sheetData/m:row", NS):
                cells = {
                    excel_col(cell.attrib["r"]): cell_value(cell)
                    for cell in row.findall("m:c", NS)
                }
                rows.append({"row": int(row.attrib["r"]), "cells": cells})
            sheets[name] = rows

    checklist_entries: list[dict] = []
    for sheet_name in ("summary", "components()", "models()"):
        for row in sheets.get(sheet_name, []):
            cells = row["cells"]
            spec_ref = cells.get("B", "")
            iq_level = cells.get("C", "")
            description = cells.get("D", "")
            pass_fail = cells.get("E", "")
            if re.match(r"^\d", spec_ref) and iq_level.startswith("LEVEL"):
                checklist_entries.append(
                    {
                        "sheet": sheet_name,
                        "row": row["row"],
                        "spec_ref": normalize_spec_ref(spec_ref),
                        "level": iq_level,
                        "description": description,
                        "default_result": pass_fail,
                    }
                )

    return {"sheets": list(sheet_map.keys()), "checklist_entries": checklist_entries}


def coverage_report(checks: list[dict], workbook: dict) -> dict:
    pdf_ids = [check["id"] for check in checks]
    workbook_ids = [entry["spec_ref"] for entry in workbook["checklist_entries"]]
    represented = set(workbook_ids)
    # The workbook summary row labels the IBISCHK item as 3.0 even though the
    # spec lists it as 2.1. Treat it as represented but call out the mismatch.
    if "3.0" in represented:
        represented.add("2.1")
    return {
        "spec_check_count": len(pdf_ids),
        "workbook_check_count": len(workbook_ids),
        "spec_check_ids": pdf_ids,
        "workbook_check_ids": workbook_ids,
        "in_spec_not_workbook": sorted(set(pdf_ids) - represented, key=sort_key),
        "in_workbook_not_spec": sorted(set(workbook_ids) - set(pdf_ids), key=sort_key),
        "known_mismatches": [
            {
                "type": "reference_id",
                "workbook_ref": "3.0",
                "spec_ref": "2.1",
                "description": "Workbook summary uses 3.0 for 'IBIS file passes IBISCHK'; the PDF section is 2.1.",
            },
            {
                "type": "missing_optional",
                "spec_ref": "5.2.4",
                "description": "The PDF has an OPTIONAL Pulse subparameter check that is not present in the workbook checklist.",
            },
        ],
    }


def sort_key(value: str) -> tuple:
    parts: list[int | str] = []
    for part in re.split(r"(\d+)", value):
        if part.isdigit():
            parts.append(int(part))
        elif part:
            parts.append(part)
    return tuple(parts)


def build_data() -> dict:
    records, sections, checks = parse_markdown()
    workbook = read_workbook()
    data = {
        "schema_version": "0.1",
        "generated_on": date.today().isoformat(),
        "source": {
            "document": "IBIS Quality Specification",
            "version": "3.0",
            "ratified": "2023-09-15",
            "ibis_spec_version": "7.2",
            "source_files": [
                str(SPEC_MD.relative_to(ROOT)).replace("\\", "/"),
                str(CHECKLIST_XLSX.relative_to(ROOT)).replace("\\", "/"),
            ],
        },
        "quality_levels": QUALITY_LEVELS,
        "special_designators": SPECIAL_DESIGNATORS,
        "result_values": [
            {"value": "PASS", "counts_as_pass": True},
            {"value": "NA", "counts_as_pass": True},
            {"value": "EXCEPTION", "counts_as_pass": True, "requires_designator": "X"},
            {"value": "FAIL", "counts_as_pass": False},
            {"value": "---", "counts_as_pass": False, "meaning": "unchecked/not assessed"},
        ],
        "scoring_rules": {
            "base_level": "The summary IQ number is the highest level for which all required checks at that level and below pass, are NA, or are accepted exceptions.",
            "optional_checks": "OPTIONAL checks are good practice but do not change the summary IQ number.",
            "correlation_designators": "Append M, S, and/or G when measurement correlation, simulation correlation, and/or golden waveform evidence is documented for a reasonable set of models.",
            "exception_designator": "Append X when any check passes only by documented exception or any remaining parser warning needs user attention.",
            "writeback": "The summary IQ score must be written into the IBIS file, preferably in [Notes]; detailed per-check status is better stored in a quality report.",
        },
        "report_requirements": {
            "summary_fields": [
                "vendor",
                "ibis_file",
                "file_rev",
                "date",
                "overall_iq_score",
                "ibischk_version",
                "ibischk_errors",
                "ibischk_warnings",
                "ibischk_cautions",
                "notes",
            ],
            "per_check_fields": [
                "check_id",
                "iq_level",
                "component_or_model_name",
                "result",
                "comments",
                "evidence",
            ],
            "preferred_artifacts": [
                "quality report with pass/fail status and reviewer notes",
                "correlation metrics and waveforms when M or S designators are used",
                "IBIS [Notes] or comments that locate any external correlation documentation",
            ],
        },
        "sections": sections,
        "checks": checks,
        "workbook": workbook,
        "coverage": coverage_report(checks, workbook),
    }
    return data


def write_json(data: dict) -> None:
    DATA_OUT.parent.mkdir(parents=True, exist_ok=True)
    DATA_OUT.write_text(json.dumps(data, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def write_methods_doc(data: dict) -> None:
    DOC_OUT.parent.mkdir(parents=True, exist_ok=True)
    checks = data["checks"]
    by_class: dict[str, list[dict]] = {}
    for check in checks:
        by_class.setdefault(check["automation"]["class"], []).append(check)

    lines = [
        "# IBIS QA Methods Map",
        "",
        "This document is generated from `quality_ver3.0.md` and `ibis_quality_3.0_checklist_auto.xlsx`.",
        "Use `data/ibis_quality_spec_3_0.json` as the canonical structured source for software work.",
        "",
        "## Source Coverage",
        "",
        f"- PDF/Markdown checks captured: {data['coverage']['spec_check_count']}",
        f"- Workbook checklist entries captured: {data['coverage']['workbook_check_count']}",
        f"- In spec but not workbook: {', '.join(data['coverage']['in_spec_not_workbook']) or 'none'}",
        f"- In workbook but not spec: {', '.join(data['coverage']['in_workbook_not_spec']) or 'none'}",
        "",
        "Known mismatches:",
    ]
    for mismatch in data["coverage"]["known_mismatches"]:
        lines.append(f"- {mismatch['description']}")

    lines.extend(
        [
            "",
            "## Suggested MVP Scope",
            "",
            "- Implement `auto` checks first: IBISCHK parsing, structural presence checks, table range checks, and numeric tolerance checks.",
            "- Add `semi_auto` checks as evidence collectors: compute the numeric evidence, plot or summarize the data, and require reviewer confirmation where the spec depends on reasonableness or technology exceptions.",
            "- Keep `manual` checks in the report template from day one so nothing disappears from the process.",
            "- Treat `optional` checks as visible non-gating items.",
            "",
            "## Automation Classes",
            "",
        ]
    )

    class_order = ["auto", "semi_auto", "manual", "optional"]
    class_names = {
        "auto": "Auto",
        "semi_auto": "Semi-Auto",
        "manual": "Manual",
        "optional": "Optional",
    }
    for class_name in class_order:
        items = by_class.get(class_name, [])
        lines.append(f"### {class_names[class_name]}")
        lines.append("")
        if not items:
            lines.append("- None")
        for check in items:
            level = check["level"]
            lines.append(f"- `{check['id']}` {level}: {check['title']}")
        lines.append("")

    lines.extend(
        [
            "## Data Shape",
            "",
            "Each check in the JSON has:",
            "",
            "- `id`, `level`, `numeric_level`, `optional`, `title`",
            "- `section_id` and `section_title`",
            "- `ibis_keywords` extracted from the check text",
            "- `paragraphs` with the normalized source detail from the spec",
            "- `automation.class`, `automation.rationale`, and `automation.how`",
            "",
            "The scoring model is represented under `scoring_rules`; report fields are represented under `report_requirements`.",
        ]
    )

    DOC_OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    data = build_data()
    write_json(data)
    write_methods_doc(data)
    print(f"Wrote {DATA_OUT.relative_to(ROOT)}")
    print(f"Wrote {DOC_OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
