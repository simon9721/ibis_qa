"""
fixer.py  —  Apply approved fix proposals to IBIS files
========================================================
Reads fix approvals from a review JSON and edits keyword values
([Voltage Range], [Pullup Reference], [Power Clamp Reference]) in the
IBIS file in-place, creating a .bak backup first.

Fix approval fields in a review JSON entry:
    "fix_approved": true
    "fix_vcc_min":  <float>   (optional — keep existing if omitted)
    "fix_vcc_max":  <float>   (optional — keep existing if omitted)

The typ value is always taken from the fix_proposal inferred_typ stored
in the QA report; only min/max require reviewer input.
"""

from __future__ import annotations
import re
import shutil
from pathlib import Path
from typing import Optional


def collect_approved_fixes(report: dict, review: dict) -> list[dict]:
    """
    Cross-reference QA results that carry fix_proposals with review entries
    that have fix_approved=True.

    Returns a list of fix dicts ready for apply_fixes():
        model, keyword, new_typ, new_min, new_max
    """
    decisions = review.get("decisions", [])
    approved_keys = {
        (d["check_id"], d["subject"]): d
        for d in decisions
        if d.get("fix_approved") and d.get("check_id") and d.get("subject")
    }
    if not approved_keys:
        return []

    fixes = []
    seen = set()
    for result in report.get("results", []):
        key = (result.get("check_id"), result.get("subject"))
        if key not in approved_keys:
            continue
        fp = result.get("data", {}).get("fix_proposal")
        if not fp:
            continue
        if key in seen:
            continue
        seen.add(key)
        decision = approved_keys[key]
        # Reviewer-provided corners take precedence; fall back to proportionally
        # scaled suggestions so that min/max stay consistent with the new typ.
        new_min = decision.get("fix_vcc_min")
        if new_min is None:
            new_min = fp.get("suggested_min")
        new_max = decision.get("fix_vcc_max")
        if new_max is None:
            new_max = fp.get("suggested_max")
        fixes.append({
            "model":   result["subject"],
            "keyword": fp["keyword"],
            "new_typ": fp["inferred_typ"],
            "new_min": new_min,
            "new_max": new_max,
            # carry originals for the change description
            "_cur_typ": fp.get("current_typ"),
            "_cur_min": fp.get("current_min"),
            "_cur_max": fp.get("current_max"),
        })
    return fixes


def apply_fixes(ibs_path: Path, fixes: list[dict],
                backup: bool = True) -> list[str]:
    """
    Apply a list of fix dicts to the IBIS file in-place.
    Returns a list of human-readable change descriptions.
    Creates <file>.bak before writing if backup=True.
    """
    if not fixes:
        return []

    text = ibs_path.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines(keepends=True)

    if backup:
        bak = ibs_path.with_suffix(ibs_path.suffix + ".bak")
        shutil.copy2(ibs_path, bak)

    changes = []
    for fix in fixes:
        changed, desc = _apply_single(
            lines,
            model_name = fix["model"],
            keyword    = fix["keyword"],
            new_typ    = fix["new_typ"],
            new_min    = fix.get("new_min"),
            new_max    = fix.get("new_max"),
            cur_typ    = fix.get("_cur_typ"),
        )
        changes.append(desc)

    if any(c and not c.startswith("WARNING") for c in changes):
        ibs_path.write_text("".join(lines), encoding="utf-8")

    return changes


def _kw_norm(kw_text: str) -> str:
    """Normalise a keyword name for comparison: lowercase, underscores, alnum only."""
    return re.sub(r"[^a-z0-9]", "_", kw_text.strip().lower())


def _fmt_val(v: Optional[float]) -> str:
    if v is None:
        return "NA"
    s = f"{v:.4f}".rstrip("0").rstrip(".")
    return s or "0"


def _apply_single(lines: list[str], model_name: str, keyword: str,
                  new_typ: float, new_min: Optional[float],
                  new_max: Optional[float],
                  cur_typ: Optional[float] = None) -> tuple[bool, str]:
    """
    Find `keyword` inside `[Model] model_name` and replace its values.

    [Voltage Range] has format:          typ  min  max
    [*Reference] keywords have format:   typ_vcc  typ_gnd  min_vcc  min_gnd  max_vcc  max_gnd

    Only the Vcc positions (0, 2, 4 for references; 0, 1, 2 for Voltage Range)
    are updated; gnd values are left untouched.
    """
    target_kw_norm = _kw_norm(keyword.strip("[]"))
    is_reference   = "reference" in target_kw_norm

    in_target = False

    for i, line in enumerate(lines):
        stripped = line.strip()
        if not stripped or stripped.startswith("$"):
            continue

        m = re.match(r"^\[([^\]]+)\]", stripped)
        if not m:
            continue

        found_kw = _kw_norm(m.group(1))

        if found_kw == "model":
            rest_toks = stripped[m.end():].split()
            in_target = bool(rest_toks and
                             rest_toks[0].lower() == model_name.lower())
            continue

        if found_kw in ("end_model", "end"):
            in_target = False
            continue

        if not in_target or found_kw != target_kw_norm:
            continue

        # ── Found target keyword in the right model section ──────────────────
        rest  = stripped[m.end():]
        toks  = rest.split()

        # Detect line ending
        eol = "\r\n" if line.endswith("\r\n") else ("\r" if line.endswith("\r") else "\n")
        # Preserve leading whitespace before the opening bracket
        indent = line[: len(line) - len(line.lstrip())]

        if is_reference and len(toks) >= 6:
            # 6-col format: typ_vcc  typ_gnd  min_vcc  min_gnd  max_vcc  max_gnd
            try:
                vals = [float(t) if t.upper() != "NA" else None for t in toks[:6]]
            except ValueError:
                vals = [None] * 6
            r_min = new_min if new_min is not None else vals[2]
            r_max = new_max if new_max is not None else vals[4]
            new_vals = (f"  {_fmt_val(new_typ)}  {_fmt_val(vals[1])}"
                        f"  {_fmt_val(r_min)}  {_fmt_val(vals[3])}"
                        f"  {_fmt_val(r_max)}  {_fmt_val(vals[5])}")
        else:
            # 3-col format: typ  min  max
            try:
                vals = [float(t) if t.upper() != "NA" else None for t in toks[:3]]
            except ValueError:
                vals = [None, None, None]
            r_min = new_min if new_min is not None else vals[1]
            r_max = new_max if new_max is not None else vals[2]
            new_vals = f"  {_fmt_val(new_typ)}  {_fmt_val(r_min)}  {_fmt_val(r_max)}"

        lines[i] = f"{indent}[{m.group(1)}]{new_vals}{eol}"

        old_typ_str = _fmt_val(cur_typ) if cur_typ is not None else _fmt_val(vals[0])
        desc = (f"[Model] {model_name}: {keyword} "
                f"typ {old_typ_str} → {_fmt_val(new_typ)}")
        if new_min is not None:
            desc += f", min → {_fmt_val(new_min)}"
        if new_max is not None:
            desc += f", max → {_fmt_val(new_max)}"
        return True, desc

    return False, f"WARNING: {keyword} not found in [Model] {model_name}"
