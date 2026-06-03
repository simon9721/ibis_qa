# Engineering Todo Review

Reviewed against `todos.md` on 2026-05-31.
Updated for Markdown/HTML visual curves on 2026-06-02.

## Summary

| Todo | Status | Notes |
|---|---|---|
| Record full IBISCHK output in JSON | Implemented | Check `2.1` now stores the full IBISCHK stdout/stderr under `result.data.ibischk.output`, along with path, return code, parsed version, errors, warnings, and cautions. |
| Review whether `5.1.4` detail is enough | Implemented | Evidence now reports explicit/defaulted voltage-reference tuples, checks typ/min/max ordering, checks positive supply/reference polarity, and compares Pullup/POWER Clamp references against the resolved `Voltage Range` nominal value. |
| Review `5.3.2`-`5.3.5` sweep ranges | Implemented | The tool now enforces the project policy that Pullup, Pulldown, POWER Clamp, and GND Clamp I-V sweeps cover approximately `-Vcc` to `2*Vcc` when the relevant table/reference is present. |
| Combine curves for `5.3.7` and related checks | Implemented | `5.3.7` now constructs combined typ-current curves for `[Pulldown] + [GND Clamp]` and `[Pullup] + [POWER Clamp]`, then checks the expected monotonic direction for each combined curve. |
| Add plots to Markdown report | Implemented | Markdown reports generate broad overview SVGs for I-V typ/min/max, ISSO typ/min/max, and stacked V-T/Composite Current waveforms when the source data exists. Plot-family attention panels remain embedded where related FAIL/WARN/ERROR findings exist. Heatmap and bar-style diagnostic SVGs were removed from report generation. |
| Add target IQ level control | Implemented | CLI `--max-level` / `--target-level` and the GUI Max Level selector now run and report only checks at or below the selected IQ level; higher-level check results are omitted from JSON, Markdown, spreadsheet output, and review queues. |
| Refine `5.5.3` | Implemented | Ramp dV is now checked for rising and falling typ/min/max corners using the load-line balance `I_table + I_load = 0`; push-pull and single-ended open-sink/open-source cases are handled separately. |

## Recommended Next Actions

1. Consider adding golden/reference waveform overlays if the workflow later includes trusted measured or simulated reference data.
2. Consider adding geometric per-point violation markers for checks that need exact location highlighting after those result payloads expose stable point coordinates.
3. Keep datasheet and extraction-document comparisons in the manual/semi-auto review workflow; those cannot be proven from the IBIS file alone.
