# Manual IBIS Quality Checks

This document explains the quality check items classified as `manual` in
`docs/qa-methods.md` and `data/ibis_quality_spec_3_0.json`.

The purpose is not just to list them. The purpose is to make clear why each
item cannot be fully decided by an IBIS-file parser alone, what outside evidence
is required, and what software can still do to help a reviewer.

## What Manual Means

In this project, `manual` does not mean "ignored" or "not important." It means
the final PASS/FAIL decision depends on information that is not guaranteed to be
inside the `.ibs` file.

Typical reasons a check is manual:

- It requires a component datasheet or product configuration guide.
- It requires package, PDN, or circuit extraction knowledge.
- It requires knowing why the model maker chose a value, not just seeing the value.
- It requires interpreting an I/O standard, threshold convention, or measurement method.
- It requires reviewing external files such as Touchstone, IBIS-ISS, EMD, SPICE, or extraction documentation.
- It requires comparing the IBIS model to reference simulation, measurement, or golden waveform data.

The tool can still assist manual checks by extracting candidate values,
highlighting missing keywords, listing related models, and preparing review
tables. But it should not claim final conformance without the external evidence.

## Manual Check Summary

| ID | Level | Check item | Primary reason final decision is manual |
|---|---|---|---|
| `3.1.3` | LEVEL 4 | Package model includes power and ground pins | Requires package topology and coupling review, often in external files. |
| `3.1.4` | LEVEL 4 | On-die and on-package decoupling included | Requires PDN/extraction knowledge and sufficiency judgement. |
| `4.2` | LEVEL 2 | Default `[Model Selector]` entries are consistent | Requires product configuration intent and likely-use context. |
| `5.1.3` | LEVEL 2 | `[Temperature Range]` is reasonable | Requires extraction conditions, die-temperature interpretation, and datasheet limits. |
| `5.2.1` | LEVEL 3 | `[Model]` Vinl and Vinh reasonable | Requires datasheet threshold comparison and Vmeas intent. |
| `5.2.2` | LEVEL 3 | `[Model Spec]` Vinl and Vinh reasonable | Requires datasheet threshold ranges and supply-variation interpretation. |
| `5.2.3` | LEVEL 3 | `[Model Spec]` Vinl+/- and Vinh+/- complete and reasonable | Requires knowing whether hysteresis or edge-specific thresholds apply. |
| `5.2.5` | LEVEL 2 | `[Model Spec]` S_Overshoot subparameters complete and match data sheet | Requires datasheet functional overshoot limits. |
| `5.2.7` | LEVEL 2 | `[Model Spec]` D_Overshoot_* subparameters complete and match data sheet | Requires datasheet dynamic overshoot rules and conversion method review. |
| `5.2.9` | LEVEL 3 | `[Receiver Thresholds]` Vth present and matches data sheet, if needed | Requires deciding whether receiver thresholds are needed for the I/O standard. |
| `5.2.10` | LEVEL 3 | `[Receiver Thresholds]` Vth_min and Vth_max present and match data sheet, if needed | Requires datasheet tolerance interpretation. |
| `5.2.11` | LEVEL 3 | `[Receiver Thresholds]` Vinh_ac, Vinl_ac present and match data sheet, if needed | Requires datasheet AC threshold values and offset conversion. |
| `5.2.12` | LEVEL 3 | `[Receiver Thresholds]` Vinh_dc, Vinl_dc present and match data sheet, if needed | Requires datasheet DC threshold values and offset conversion. |
| `5.2.13` | LEVEL 3 | `[Receiver Thresholds]` Tslew_ac/Tdiffslew_ac present and match data sheet, if needed | Requires datasheet slew-limit values and receiver applicability. |
| `5.2.14` | LEVEL 3 | `[Receiver Thresholds]` Threshold_sensitivity and Ext_ref present and match data sheet, if needed | Requires reference-supply behavior from datasheet or I/O standard. |
| `5.3.11` | LEVEL 2 | I-V behavior not double-counted | Requires curve/context review of driver, clamp, and termination decomposition. |
| `5.3.12` | LEVEL 2 | On-die termination modeling documented | Requires knowing whether ODT exists and whether the documented method is sufficient. |
| `5.6.1` | LEVEL 3 | `[Model Spec]` Vmeas and Vref used if typ/min/max variation | Requires deciding whether Vmeas/Vref variation exists across corners. |
| `5.8.4` | LEVEL 4 | `[Composite Current]` includes pre-driver behavior | Requires circuit/extraction knowledge about pre-driver current paths. |
| `5.8.6` | LEVEL 4 | `[Composite Current]` data includes current from correct voltage rails | Requires extraction documentation for multi-rail current aggregation. |

## Item-by-Item Rationale

### 3.1.3 - Package model includes power and ground pins

- Level: `LEVEL 4`
- Related IBIS data: `[Define Package Model]`, `[External Circuit]`, `[Interconnect Model]`, `[EMD Model]`, package-model references, power and ground pins.

Why this is manual:

- The IBIS file can show that some package-model mechanism exists, but that does not prove that power and ground pins are included correctly.
- Power/ground coupling may live in external Touchstone, IBIS-ISS, EMD, or SPICE-like files. The `.ibs` file may only reference those files.
- Port names, node names, and bus labels are not always enough to prove that the return path, loop inductance, signal-power-ground coupling, and rail interactions are represented.
- A package model can include signal pins but still omit meaningful coupling to power/ground pins.
- A package model can include power/ground pins by name but model them with insufficient topology.

Evidence needed for reviewer signoff:

- The actual package model files or embedded package-model sections.
- A pin/port map tying package-model nodes to component signal, power, and ground pins.
- Evidence that signal, power, and ground coupling is included, not just signal-only coupling.
- Documentation of any simplification, such as omitted rail coupling or a single loop inductance approximation.

What software can assist with:

- Detect package-model mechanisms and external references.
- List package-model names and referenced files.
- List POWER/GND pins and whether their names appear in package-model mappings.
- Flag missing package-model references or obvious absence of rail-like nodes.

Why software should not decide alone:

- Presence of names or files does not prove correct electrical coupling.
- Correctness depends on package extraction setup and the intended simulation use case.

### 3.1.4 - On-die and on-package decoupling included

- Level: `LEVEL 4`
- Related IBIS data: `[Interconnect Model]`, `[External Circuit]`, `[Circuit Call]`, `[PDN Domain]`, `[PDN Model]`, `C_pdn`, `R_pdn`, `R_leak`, package-model references.

Why this is manual:

- On-die and on-package decoupling strongly affects SSO and power-aware simulations, but its adequacy cannot be inferred from keyword presence alone.
- A PDN-related keyword may exist while representing only part of the real decoupling network.
- The correct amount, placement, ESR/ESL behavior, leakage, and rail association come from extraction or design knowledge outside the `.ibs` syntax.
- Some decoupling may be intentionally excluded because the model is targeted at non-power-aware usage. That intent must be documented.

Evidence needed for reviewer signoff:

- PDN extraction notes or package/IC design documentation.
- On-die decap values and topology, or a reason they are embedded in another model.
- On-package decap values and topology, if applicable.
- Mapping from decoupling elements to the correct power/ground domains.
- Notes explaining omissions or simplifications.

What software can assist with:

- Detect PDN and decoupling-related keywords.
- Report whether `C_pdn`, `R_pdn`, `R_leak`, `[PDN Model]`, or related external circuits appear.
- Show which components and rails have package/PDN model references.

Why software should not decide alone:

- Decoupling sufficiency is a modeling-quality judgement, not a syntactic condition.
- The `.ibs` file usually cannot prove what physical decoupling was extracted.

### 4.2 - Default [Model Selector] entries are consistent

- Level: `LEVEL 2`
- Related IBIS data: `[Model Selector]`.

Why this is manual:

- The first entry in each `[Model Selector]` is the EDA-tool default, but whether a set of defaults is consistent depends on product configuration intent.
- A parser can identify first entries but cannot know legal combinations across selectors.
- The "best" default may be the most frequently used setting, a recommended configuration, a safe fallback, or a vendor-defined nominal mode.
- Some selectors are coupled. For example, output impedance, ODT, voltage mode, slew rate, and drive strength may need matching defaults.

Evidence needed for reviewer signoff:

- Datasheet configuration tables or register defaults.
- Vendor recommendation for default drive/ODT/slew/voltage modes.
- Product-specific explanation when defaults differ across pins or buffers.
- Confirmation that the default entries together describe a plausible real device state.

What software can assist with:

- Extract every `[Model Selector]` name.
- Show the first/default entry for each selector.
- Group selectors by component, pin usage, or model family.
- Flag weak descriptions or selector entries that point to missing models.

Why software should not decide alone:

- Consistency is a system-level configuration question, not an IBIS syntax question.

### 5.1.3 - [Temperature Range] is reasonable

- Level: `LEVEL 2`
- Related IBIS data: `[Temperature Range]`.

Why this is manual:

- The correct temperature range depends on extraction conditions and datasheet operating limits.
- IBIS temperature is chip die temperature, not ambient temperature.
- The meaning of "minimum" and "maximum" corners depends on process technology. For example, CMOS and bipolar behavior can have different slow/fast temperature relationships.
- A syntactically valid `[Temperature Range]` can still be physically wrong if it does not match the model extraction setup.
- The range may intentionally differ from the datasheet ambient range if self-heating or measurement setup is considered.

Evidence needed for reviewer signoff:

- Datasheet operating temperature limits.
- Extraction or measurement temperatures for typ/min/max model corners.
- Technology explanation for which temperature corner corresponds to slow/weak and fast/strong behavior.
- Notes explaining any difference between die temperature and ambient temperature.

What software can assist with:

- Parse `[Temperature Range]`.
- Check that values are present.
- Check basic numeric ordering patterns and unusual values.
- Compare against user-supplied datasheet limits if those are provided in a future review workflow.

Why software should not decide alone:

- Reasonableness depends on external temperature definitions and extraction intent.

### 5.2.1 - [Model] Vinl and Vinh reasonable

- Level: `LEVEL 3`
- Related IBIS data: `[Model]`, `[Model Spec]`, `Vinl`, `Vinh`, `Vmeas`.

Why this is manual:

- `Vinl` and `Vinh` must match the device threshold behavior described in the datasheet.
- The `.ibs` file contains threshold numbers but not the authoritative threshold specification.
- For I/O models, the relationship between `Vinl`, `Vinh`, and `Vmeas` may require technology context.
- `[Model Spec]` values, if present, can refine or override simpler `[Model]` values, so the reviewer must understand which source is intended.
- Exceptions can be valid but must be explained in comments.

Evidence needed for reviewer signoff:

- Datasheet DC input threshold tables.
- Model-maker explanation of how `[Model]` thresholds map to datasheet values.
- Comparison to `[Model Spec]` thresholds when present.
- Comment review for exceptions around `Vmeas`.

What software can assist with:

- Extract `Vinl`, `Vinh`, `Vmeas`, and related `[Model Spec]` values.
- Flag missing values for input and I/O models.
- Show potential inconsistencies between `[Model]` and `[Model Spec]`.

Why software should not decide alone:

- The datasheet values and intended threshold interpretation are external to the IBIS file.

### 5.2.2 - [Model Spec] Vinl and Vinh reasonable

- Level: `LEVEL 3`
- Related IBIS data: `[Model Spec]`, `[Model]`, `[Voltage Range]`, `Vinl`, `Vinh`.

Why this is manual:

- `[Model Spec]` threshold ranges often represent behavior across supply variation.
- Correct min/max interpretation depends on how the datasheet defines threshold variation.
- A parser can compare values numerically but cannot know whether supply, process, temperature, or test condition effects are included correctly.
- The values are needed only for input and I/O model types where they represent real receiver behavior.

Evidence needed for reviewer signoff:

- Datasheet threshold ranges across supply and operating conditions.
- Mapping between `[Voltage Range]` typ/min/max values and threshold typ/min/max values.
- Explanation of whether threshold range includes supply variation, PVT variation, or both.
- Confirmation that thresholds apply to the modeled I/O standard.

What software can assist with:

- Extract `[Model Spec]` threshold values.
- Compare typ/min/max ordering.
- Show the related `[Voltage Range]` values beside threshold ranges.

Why software should not decide alone:

- Correctness depends on datasheet interpretation, not just numeric order.

### 5.2.3 - [Model Spec] Vinl+/- and Vinh+/- complete and reasonable

- Level: `LEVEL 3`
- Related IBIS data: `[Model Spec]`, `Vinl+`, `Vinl-`, `Vinh+`, `Vinh-`, `Vmeas`.

Why this is manual:

- Edge-specific thresholds are required only for input buffers with different rising/falling thresholds, such as hysteresis or Schmitt trigger behavior.
- The `.ibs` file cannot prove whether the real device has hysteresis if the datasheet or design notes are absent.
- Completeness depends on whether edge-specific threshold behavior is applicable.
- The reasonableness of the four threshold values must be checked against the datasheet and comments.
- For I/O buffers, exceptions involving `Vmeas` require explanation.

Evidence needed for reviewer signoff:

- Datasheet hysteresis or Schmitt trigger threshold data.
- Confirmation whether edge-specific thresholds apply to each input or I/O model.
- Comparison table of datasheet thresholds to IBIS `Vinl+`, `Vinl-`, `Vinh+`, and `Vinh-`.
- Comments explaining exceptions.

What software can assist with:

- Extract edge-specific threshold values.
- Flag incomplete sets when any of the four values are present.
- Show models with comments mentioning hysteresis or Schmitt behavior.

Why software should not decide alone:

- The applicability of edge-specific thresholds comes from device behavior, not syntax.

### 5.2.5 - [Model Spec] S_Overshoot subparameters complete and match data sheet

- Level: `LEVEL 2`
- Related IBIS data: `[Model Spec]`, `S_overshoot_high`, `S_overshoot_low`.

Why this is manual:

- Static overshoot limits must match functional overshoot limits in the datasheet.
- Functional overshoot limits are not always the same as absolute maximum ratings.
- Some datasheets do not state functional limits directly, or state them differently for different pins, supplies, or operating modes.
- Completeness depends on model type and datasheet coverage for input and I/O buffers.

Evidence needed for reviewer signoff:

- Datasheet functional overshoot high/low limits.
- Mapping from datasheet pins or I/O standards to IBIS models.
- Explanation when functional overshoot limits are absent from the datasheet.
- Confirmation that values are not merely copied from absolute maximum ratings unless that is justified.

What software can assist with:

- Extract `S_overshoot_high` and `S_overshoot_low`.
- Flag missing values for input and I/O models.
- Check typ/min/max tracking when values exist, as semi-auto evidence.

Why software should not decide alone:

- Matching the datasheet requires external functional-limit data and interpretation.

### 5.2.7 - [Model Spec] D_Overshoot_* subparameters complete and match data sheet

- Level: `LEVEL 2`
- Related IBIS data: `[Model Spec]`, `D_overshoot_high`, `D_overshoot_low`, `D_overshoot_time`.

Why this is manual:

- Dynamic overshoot is defined by what the datasheet allows for short durations.
- Datasheets may express dynamic overstress as voltage/time limits, current limits, or time-voltage area limits.
- Converting non-IBIS datasheet language into `D_overshoot_high`, `D_overshoot_low`, and `D_overshoot_time` requires judgement.
- The conversion method should be documented, and the parser cannot validate undocumented engineering assumptions.

Evidence needed for reviewer signoff:

- Datasheet dynamic overshoot or transient overstress rules.
- Conversion method from datasheet rules to IBIS D_Overshoot parameters.
- Per-model or per-I/O-standard comparison table.
- Comments in the IBIS file or external report locating the conversion evidence.

What software can assist with:

- Extract D_Overshoot values.
- Flag missing values for applicable input and I/O models.
- Check typ/min/max tracking when values exist, as semi-auto evidence.

Why software should not decide alone:

- The core check is a datasheet conversion and documentation review.

### 5.2.9 - [Receiver Thresholds] Vth present and matches data sheet, if needed

- Level: `LEVEL 3`
- Related IBIS data: `[Receiver Thresholds]`, `Vth`.

Why this is manual:

- `[Receiver Thresholds]` are needed only for certain I/O standards or timing models.
- Whether they are needed cannot be known reliably from generic IBIS syntax alone.
- `Vth` must match the datasheet timing measurement threshold, which may differ from DC input thresholds.
- Single-ended and differential receivers have different applicability rules.

Evidence needed for reviewer signoff:

- Datasheet timing measurement threshold.
- I/O standard documentation explaining whether `[Receiver Thresholds]` are required.
- Mapping from receiver model to datasheet threshold definition.
- Explanation when `[Receiver Thresholds]` are intentionally omitted.

What software can assist with:

- Extract `[Receiver Thresholds]` and `Vth`.
- List models that appear to be receivers.
- Flag missing `Vth` when `[Receiver Thresholds]` is present.

Why software should not decide alone:

- Applicability and correct value both depend on the datasheet or I/O standard.

### 5.2.10 - [Receiver Thresholds] Vth_min and Vth_max present and match data sheet, if needed

- Level: `LEVEL 3`
- Related IBIS data: `[Receiver Thresholds]`, `Vth_min`, `Vth_max`, `Vth`.

Why this is manual:

- `Vth_min` and `Vth_max` describe threshold tolerance under typical supply, process, and temperature conditions.
- Datasheet tolerances may be stated as percentages, absolute voltages, or equations tied to supply.
- Supply variation may be separate from threshold tolerance unless the datasheet defines it otherwise.
- A parser cannot know which variation components should be included.

Evidence needed for reviewer signoff:

- Datasheet Vth tolerance or receiver threshold range.
- Calculation showing whether values are absolute voltages or functions of VDD/VDDQ.
- Explanation that supply variation has or has not been included as intended.
- Comparison of datasheet values to IBIS `Vth_min` and `Vth_max`.

What software can assist with:

- Extract `Vth`, `Vth_min`, and `Vth_max`.
- Check basic ordering.
- Compute simple formulas if a reviewer supplies the datasheet rule.

Why software should not decide alone:

- Correct interpretation of threshold tolerance is external and standard-specific.

### 5.2.11 - [Receiver Thresholds] Vinh_ac, Vinl_ac present and match data sheet, if needed

- Level: `LEVEL 3`
- Related IBIS data: `[Receiver Thresholds]`, `Vinh_ac`, `Vinl_ac`, `Vth`.

Why this is manual:

- AC thresholds define the input levels that must be crossed for guaranteed state change.
- Datasheets may give AC thresholds as absolute voltages, while IBIS receiver thresholds may require offsets from `Vth`.
- The need for AC thresholds depends on receiver technology and datasheet timing method.
- Conversion can depend on nominal supply and reference voltage assumptions.

Evidence needed for reviewer signoff:

- Datasheet AC input threshold values.
- `Vth` value and any reference-voltage assumption used for conversion.
- Calculation converting absolute datasheet values to IBIS offsets when needed.
- Explanation when AC thresholds are not applicable.

What software can assist with:

- Extract `Vinh_ac`, `Vinl_ac`, and `Vth`.
- Check whether offsets are present when `[Receiver Thresholds]` exists.
- Perform conversion if the reviewer supplies absolute datasheet thresholds.

Why software should not decide alone:

- The parser cannot infer the datasheet's threshold convention or conversion basis.

### 5.2.12 - [Receiver Thresholds] Vinh_dc, Vinl_dc present and match data sheet, if needed

- Level: `LEVEL 3`
- Related IBIS data: `[Receiver Thresholds]`, `Vinh_dc`, `Vinl_dc`, `Vth`.

Why this is manual:

- DC thresholds define boundary conditions where the receiver will not change state.
- Datasheets may state DC thresholds as absolute voltages, while IBIS may require offsets from `Vth`.
- The need for DC thresholds depends on the receiver and I/O standard.
- Correct conversion depends on the same reference assumptions used for `Vth`.

Evidence needed for reviewer signoff:

- Datasheet DC input threshold values.
- Calculation converting datasheet values to IBIS offsets from `Vth` when needed.
- Confirmation that the thresholds apply to the modeled receiver.
- Explanation when DC thresholds are not required.

What software can assist with:

- Extract `Vinh_dc`, `Vinl_dc`, and `Vth`.
- Check value presence and basic sign/order.
- Prepare a comparison table for reviewer-supplied datasheet values.

Why software should not decide alone:

- The correct values and whether they are needed come from datasheet interpretation.

### 5.2.13 - [Receiver Thresholds] Tslew_ac/Tdiffslew_ac present and match data sheet, if needed

- Level: `LEVEL 3`
- Related IBIS data: `[Receiver Thresholds]`, `Tslew_ac`, `Tdiffslew_ac`, `Vinh_ac`, `Vinl_ac`.

Why this is manual:

- These parameters apply when the datasheet specifies maximum input transition time.
- Single-ended and differential receivers use different parameters.
- Datasheet slew limits may be specified between different voltage points than the IBIS receiver-threshold definitions.
- A parser cannot decide applicability without knowing the I/O standard and timing specification.

Evidence needed for reviewer signoff:

- Datasheet maximum input transition time or slew-rate requirement.
- Whether the receiver is single-ended or differential.
- The voltage points used for the datasheet slew limit.
- Mapping to `Tslew_ac` or `Tdiffslew_ac`.

What software can assist with:

- Extract `Tslew_ac`, `Tdiffslew_ac`, and related AC thresholds.
- Flag missing slew parameters when receiver thresholds exist.
- Compare against reviewer-supplied datasheet limits.

Why software should not decide alone:

- Applicability and measurement basis are datasheet-defined.

### 5.2.14 - [Receiver Thresholds] Threshold_sensitivity and Ext_ref present and match data sheet, if needed

- Level: `LEVEL 3`
- Related IBIS data: `[Receiver Thresholds]`, `Threshold_sensitivity`, `Reference_supply`, `Ext_ref`.

Why this is manual:

- Some receiver thresholds depend on an external reference or supply voltage.
- Whether this behavior exists is determined by the datasheet, I/O standard, or design.
- The correct `Threshold_sensitivity` value is not always obvious from the IBIS file.
- `Reference_supply` must identify the correct reference source, such as `Ext_ref`, when applicable.

Evidence needed for reviewer signoff:

- Datasheet statement that threshold tracks an external reference or supply.
- I/O standard requirement for reference-tracking behavior.
- Expected sensitivity relationship, such as threshold movement per reference movement.
- Confirmation that `Reference_supply` names the correct source.

What software can assist with:

- Extract `Threshold_sensitivity` and `Reference_supply`.
- Flag missing values in models that already use receiver thresholds.
- Search comments and model names for standards commonly associated with external references.

Why software should not decide alone:

- Reference dependence is a behavioral property that may not be encoded anywhere else in the `.ibs` file.

### 5.3.11 - I-V behavior not double-counted

- Level: `LEVEL 2`
- Related IBIS data: `[Pulldown]`, `[Pullup]`, `[GND Clamp]`, `[POWER Clamp]`, on-die termination behavior.

Why this is manual:

- The check asks whether clamp, driver, and termination behavior has been decomposed correctly across I-V tables.
- A parser can plot or combine curves, but it cannot know which physical current belongs in which table without extraction context.
- On-die termination can be especially ambiguous because termination current may appear clamp-like, driver-like, or mode-dependent.
- Some extraction tools have known behaviors, such as placing full termination characteristics in both clamp tables, but detecting that reliably requires curve review and model intent.
- Apparent overlap between tables may be correct for one technology and double-counting for another.

Evidence needed for reviewer signoff:

- Plots of individual and combined I-V tables.
- Extraction method explaining how clamp, driver, and termination currents were separated.
- Datasheet or design evidence for on-die termination modes.
- Comments explaining any intentional overlap or table decomposition method.

What software can assist with:

- Plot I-V tables and combined curves.
- Identify large overlapping currents near clamp/termination regions.
- Search comments for on-die termination notes.
- Flag suspicious duplicated clamp behavior for reviewer attention.

Why software should not decide alone:

- Correct decomposition depends on physical circuit behavior and extraction method, not just numeric table shape.

### 5.3.12 - On-die termination modeling documented

- Level: `LEVEL 2`
- Related IBIS data: `[GND Clamp]`, `[POWER Clamp]`, `[Add Submodel]`, comments, `[Notes]`.

Why this is manual:

- The tool can search for terms related to on-die termination, but it cannot know whether a device actually has ODT unless datasheet or design information is available.
- If ODT exists, the acceptable modeling method depends on whether termination is always present, mode-dependent, active only in non-driving mode, or controlled by configuration.
- Documentation quality is subjective: a keyword or comment may mention ODT without explaining enough for a model user.
- ODT may be embedded in clamp tables, submodels, selected models, or external circuits.

Evidence needed for reviewer signoff:

- Datasheet statement identifying ODT behavior and modes.
- IBIS comments or `[Notes]` explaining where ODT is modeled.
- Evidence that clamp tables, `[Add Submodel]`, or model selectors represent ODT correctly.
- Explanation when ODT is intentionally omitted.

What software can assist with:

- Search for ODT-related terms in comments and notes.
- Detect `[Add Submodel]` and clamp-table presence.
- List model selectors that may represent ODT states.

Why software should not decide alone:

- Documentation sufficiency and ODT applicability require device knowledge and human reading.

### 5.6.1 - [Model Spec] Vmeas and Vref used if typ/min/max variation

- Level: `LEVEL 3`
- Related IBIS data: `[Model Spec]`, `Vmeas`, `Vref`, typ/min/max corners.

Why this is manual:

- `Vmeas` and `Vref` should be used when their values vary across typ/min/max conditions.
- Whether they should vary depends on the I/O standard, supply tracking, measurement definitions, and extraction setup.
- A parser can see if values are present, but not whether variation should exist.
- Some technologies use fixed thresholds; others scale with supply or reference voltage.

Evidence needed for reviewer signoff:

- Datasheet timing measurement definitions.
- I/O standard rule for Vmeas/Vref supply tracking.
- Extraction or simulation setup showing typ/min/max reference values.
- Comparison of expected values against `[Model Spec]`.

What software can assist with:

- Extract `Vmeas` and `Vref` values.
- Show whether typ/min/max tuples are complete.
- Compare values to `[Voltage Range]` if a reviewer supplies the expected relationship.

Why software should not decide alone:

- The key question is whether variation is required, and that is defined outside the `.ibs` file.

### 5.8.4 - [Composite Current] includes pre-driver behavior

- Level: `LEVEL 4`
- Related IBIS data: `[Composite Current]`, `[Rising Waveform]`, `[Falling Waveform]`, `Pullup Reference`.

Why this is manual:

- The requirement applies when the pre-driver draws current from the same pullup reference rail as the main driver.
- The IBIS file may show Composite Current waveforms but not identify which circuit blocks contributed to them.
- Pre-driver current may occur before the output voltage transition, but early current changes can also come from other effects.
- Whether waveform tables need inactive time at the beginning depends on extraction setup and circuit timing.

Evidence needed for reviewer signoff:

- Extraction documentation identifying current contributors included in Composite Current.
- Circuit knowledge showing whether the pre-driver draws from the pullup reference rail.
- Waveform plots showing any pre-transition current behavior.
- Explanation when pre-driver current is excluded because it is on another rail or not relevant.

What software can assist with:

- Plot Composite Current against V-T waveforms.
- Look for significant Composite Current activity before voltage transition.
- Check time alignment and edge flatness evidence.

Why software should not decide alone:

- The parser cannot know which internal circuit currents are included in the extracted Composite Current.

### 5.8.6 - [Composite Current] data includes current from correct voltage rails

- Level: `LEVEL 4`
- Related IBIS data: `[Composite Current]`, `[Pullup Reference]`, `[POWER Clamp Reference]`, `[Voltage Range]`, `[Pin Mapping]`.

Why this is manual:

- Multi-rail buffers may draw current from more than one supply node.
- Composite Current should include the correct rail currents and exclude rails that should not contribute based on power-clamp reference and pin-mapping bus labels.
- The IBIS file contains final waveform values, but not a proof of which physical rail currents were summed during extraction.
- Supply rail naming and bus labels can be ambiguous without extraction documentation.
- The spec explicitly notes that this cannot be checked from the IBIS data alone; the extraction assumptions should be documented.

Evidence needed for reviewer signoff:

- Extraction documentation listing which rail currents were summed.
- Mapping from physical supply rails to `[Pullup Reference]`, `[POWER Clamp Reference]`, `[Voltage Range]`, and `[Pin Mapping]` bus labels.
- Explanation for any excluded rail current.
- Confirmation that multi-rail aggregation matches the model's intended simulation behavior.

What software can assist with:

- List supply/reference keywords for each model.
- Extract `[Pin Mapping]` bus labels for power rails.
- Identify models with multiple references or potentially multi-rail behavior.
- Flag missing documentation references.

Why software should not decide alone:

- The correctness of Composite Current rail aggregation is an extraction-process fact, not an observable IBIS syntax fact.

## Reviewer Checklist Template

For each manual item, a reviewer should record:

| Field | Purpose |
|---|---|
| Check ID | The IBIS Quality Specification check item, such as `5.2.11`. |
| Scope | File, component, model, model selector, package model, or waveform. |
| External evidence used | Datasheet section, extraction note, schematic, package model, simulation setup, or measurement report. |
| IBIS evidence reviewed | Related keywords, values, comments, and generated QA findings. |
| Decision | PASS, FAIL, NA, or accepted exception. |
| Reason | Short explanation of why the evidence supports the decision. |
| Required model-maker action | Missing documentation, value correction, clarification, or no action. |

## Relationship To The Tool

The current `ibis_qa_tool` intentionally does not mark these manual items as
implemented auto checks. That is the right behavior. A future GUI workflow can
still make them easier by adding a manual-review queue, pre-filled evidence
tables, links to relevant IBIS keywords, and reviewer comment fields.

The boundary should stay clear:

- The tool may gather and organize evidence.
- The reviewer makes the final decision when external data or engineering
  intent is required.
- The final report should identify which manual checks were reviewed, what
  evidence was used, and any exceptions the model maker accepted.
