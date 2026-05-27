The goal of this project is to build an IBIS Quality Assessment Tool. The two documents are from IBIS.org, and we will use them as our starting point.

Below is from another document, which shows the current plan:

IBIS Quality Assessment (IBIS QA)
Objective: To ensure the quality of the IBIS models in our IBIS Library, a quality assessment layer is necessary. This quality assessment tool should be used before any model goes into the Website's official database.

General work flow:
A new IBIS model is available
IBIS QA check the model
If PASSED:
Check-in the model
If FAILED:
DO NOT checkin, has a standalone system to store failed one and also:
Send back to vendor to fix (if possible)
Keep track of model status (for example buffer_1.ibs failed, sent to vendor and awaiting for update, buffer_2.ibs failed, N/A for vendor fixing)

For PASSED model:
Generate Quality Report and include the report in the same place as the IBIS file
Include IBIS QA result in IBIS model's JSON file (details to be discussed)
Goal: be able to easily identify suitable IBIS model for a specific simulation


Some initial ideas for IBIS QA:
https://ibis.org/quality_ver3.0/ (IBIS Quality Specification 3.0)
IBISCHK
Switching Coefficient Extraction & Analysis
Tx drive strength / Rx termination (ohms)
IBIS V/T curve vs. simulated curve (under same termination) correlation
Visual waveform examination (may not be practical?)

Timeline for IBIS QA:
Week of May 25: Gather & brainstorm QA methods. Create a new document and record findings
Week of June 1: Review methods & start working on software implementation part
Week of June 8: Provide version 0 for review
Week of June 15: Continue based on review

Current structured source files:

- `quality_ver3.0.md`: Markdown conversion of the IBIS Quality Specification 3.0 PDF.
- `ibis_quality_3.0_checklist_auto.xlsx`: IBIS.org checklist workbook.
- `data/ibis_quality_spec_3_0.json`: generated canonical structured data for software work.
- `docs/qa-methods.md`: generated human-readable method map and MVP scope.
- `docs/spec-tree.md`: generated tree view of the structured spec.
- `docs/automation-categories.md`: generated auto/semi-auto/manual/optional catalog with why/how notes.
- `docs/quality-levels.md`: generated catalog of checks grouped by IQ level.
- `tools/build_spec_data.py`: generator that rebuilds the JSON and method map from the Markdown and workbook.
- `tools/render_spec_tree.py`: generator that renders the spec JSON as a Markdown tree.
- `tools/render_automation_catalog.py`: generator that renders the automation category catalog.
- `tools/render_level_catalog.py`: generator that renders checks grouped by IQ level.

Regenerate structured data with:

```powershell
python tools/build_spec_data.py
```

Regenerate the tree view with:

```powershell
python tools/render_spec_tree.py
```

Regenerate the automation category catalog with:

```powershell
python tools/render_automation_catalog.py
```

Regenerate the quality-level catalog with:

```powershell
python tools/render_level_catalog.py
```
# ibis_qa
