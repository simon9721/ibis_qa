"""Output-impedance estimates derived from parsed IBIS I-V tables.

The calculation follows the same Westerhoff-style load-line approach used by
the standalone ``ibis_zout_report.py`` prototype, but operates on the QA
tool's parsed ``IBISFile`` object and returns plain dictionaries for reports.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from parser.ibis_parser import IBISFile, IVTable, Model


DEFAULT_ZOUT_RLOAD_OHM = 50.0

_CORNERS = (
    ("typ", 1, 0),
    ("min", 2, 1),
    ("max", 3, 2),
)


def estimate_zout_for_ibis(
    ibis_file: "IBISFile",
    r_load_ohm: float = DEFAULT_ZOUT_RLOAD_OHM,
) -> dict[str, dict]:
    """Return Zout estimates for every parsed model."""
    return {
        name: estimate_zout_for_model(model, r_load_ohm)
        for name, model in ibis_file.models.items()
    }


def summarize_zout_results(zout_by_model: dict[str, dict]) -> dict:
    """Return compact report-level counts for the Zout data block."""
    estimate_count = 0
    models_with_estimates = 0
    for model_zout in zout_by_model.values():
        model_estimates = [
            item for item in model_zout.get("estimates", [])
            if item.get("status") == "estimated"
        ]
        estimate_count += len(model_estimates)
        if model_estimates:
            models_with_estimates += 1

    r_load = None
    for model_zout in zout_by_model.values():
        r_load = model_zout.get("r_load_ohm")
        break

    return {
        "method": "Westerhoff load-line estimate from IBIS Pullup/Pulldown tables",
        "r_load_ohm": r_load,
        "model_count": len(zout_by_model),
        "models_with_estimates": models_with_estimates,
        "estimate_count": estimate_count,
    }


def estimate_zout_for_model(
    model: "Model",
    r_load_ohm: float = DEFAULT_ZOUT_RLOAD_OHM,
) -> dict:
    """Estimate model Zout at typ/min/max corners for Pullup/Pulldown tables."""
    estimates = []
    notes = []

    for side in ("pulldown", "pullup"):
        table = getattr(model, side, None)
        if table is None or len(table.rows) < 2:
            notes.append(f"No usable [{side.capitalize()}] table for Zout estimate.")
            continue
        for corner_name, table_col, value_index in _CORNERS:
            vcc = _corner_vcc(model, value_index)
            if vcc is None:
                estimates.append(_unavailable(side, corner_name, "missing_vcc"))
                continue
            estimate = (
                _estimate_pulldown(table, corner_name, table_col, vcc, r_load_ohm)
                if side == "pulldown"
                else _estimate_pullup(table, corner_name, table_col, vcc, r_load_ohm)
            )
            estimates.append(estimate)

    available = any(item.get("status") == "estimated" for item in estimates)
    if not estimates:
        notes.append("No Pullup/Pulldown load-line estimates could be attempted.")

    return {
        "available": available,
        "method": "Westerhoff load-line estimate",
        "r_load_ohm": float(r_load_ohm),
        "model_type": model.model_type,
        "estimates": estimates,
        "summary": _summary_by_side(estimates),
        "notes": notes,
    }


def _estimate_pulldown(
    table: "IVTable",
    corner_name: str,
    col: int,
    vcc: float,
    r_load_ohm: float,
) -> dict:
    point = _loadline_intersection_pulldown(table, vcc, r_load_ohm, col)
    if point is None:
        return _unavailable("pulldown", corner_name, "no_intersection", vcc)
    v_op, i_op = point
    if abs(i_op) <= 1e-15:
        return _unavailable("pulldown", corner_name, "zero_current", vcc, v_op, i_op)
    zout = v_op / i_op
    return {
        "table": "pulldown",
        "corner": corner_name,
        "status": "estimated",
        "load_connection": "Rload to Vdd",
        "vcc_v": vcc,
        "table_voltage_v": v_op,
        "output_voltage_v": v_op,
        "i_op_a": i_op,
        "zout_ohm": zout,
        "r_series_ohm": r_load_ohm - zout,
    }


def _estimate_pullup(
    table: "IVTable",
    corner_name: str,
    col: int,
    vcc: float,
    r_load_ohm: float,
) -> dict:
    point = _loadline_intersection_pullup(table, vcc, r_load_ohm, col)
    if point is None:
        return _unavailable("pullup", corner_name, "no_intersection", vcc)
    table_voltage, i_op = point
    if abs(i_op) <= 1e-15:
        return _unavailable("pullup", corner_name, "zero_current", vcc, table_voltage, i_op)
    rail_drop = table_voltage
    zout = rail_drop / abs(i_op)
    return {
        "table": "pullup",
        "corner": corner_name,
        "status": "estimated",
        "load_connection": "Rload to GND",
        "vcc_v": vcc,
        "table_voltage_v": table_voltage,
        "output_voltage_v": vcc - table_voltage,
        "i_op_a": i_op,
        "zout_ohm": zout,
        "r_series_ohm": r_load_ohm - zout,
    }


def _loadline_intersection_pulldown(
    table: "IVTable",
    vcc: float,
    r_load_ohm: float,
    col: int,
) -> tuple[float, float] | None:
    """[Pulldown] load line: Rload to Vdd, Iload = (Vcc - V) / Rload."""
    for row_a, row_b in zip(table.rows, table.rows[1:]):
        if len(row_a) <= col or len(row_b) <= col:
            continue
        v_a, v_b = row_a[0], row_b[0]
        i_a, i_b = row_a[col], row_b[col]
        if None in (v_a, v_b, i_a, i_b):
            continue
        load_a = (vcc - v_a) / r_load_ohm
        load_b = (vcc - v_b) / r_load_ohm
        diff_a = i_a - load_a
        diff_b = i_b - load_b
        if diff_a * diff_b <= 0:
            frac = _intersection_fraction(diff_a, diff_b)
            v_op = v_a + frac * (v_b - v_a)
            i_op = (vcc - v_op) / r_load_ohm
            return v_op, i_op
    return None


def _loadline_intersection_pullup(
    table: "IVTable",
    vcc: float,
    r_load_ohm: float,
    col: int,
) -> tuple[float, float] | None:
    """[Pullup] uses IBIS Vcc-relative voltage; load line is Rload to GND."""
    for row_a, row_b in zip(table.rows, table.rows[1:]):
        if len(row_a) <= col or len(row_b) <= col:
            continue
        v_a, v_b = row_a[0], row_b[0]
        i_a, i_b = row_a[col], row_b[col]
        if None in (v_a, v_b, i_a, i_b):
            continue
        load_a = -(vcc - v_a) / r_load_ohm
        load_b = -(vcc - v_b) / r_load_ohm
        diff_a = i_a - load_a
        diff_b = i_b - load_b
        if diff_a * diff_b <= 0:
            frac = _intersection_fraction(diff_a, diff_b)
            table_voltage = v_a + frac * (v_b - v_a)
            i_op = -(vcc - table_voltage) / r_load_ohm
            return table_voltage, i_op
    return None


def _intersection_fraction(diff_a: float, diff_b: float) -> float:
    denom = diff_b - diff_a
    if abs(denom) <= 1e-20:
        return 0.5
    return -diff_a / denom


def _corner_vcc(model: "Model", index: int) -> float | None:
    """Prefer Pullup Reference, matching the prototype script, then Voltage Range."""
    for values in (model.pullup_ref, model.voltage_range):
        if isinstance(values, (list, tuple)) and len(values) > index and values[index] is not None:
            return float(values[index])
    return None


def _unavailable(
    table: str,
    corner: str,
    reason: str,
    vcc: float | None = None,
    table_voltage: float | None = None,
    i_op: float | None = None,
) -> dict:
    return {
        "table": table,
        "corner": corner,
        "status": reason,
        "vcc_v": vcc,
        "table_voltage_v": table_voltage,
        "output_voltage_v": None,
        "i_op_a": i_op,
        "zout_ohm": None,
        "r_series_ohm": None,
    }


def _summary_by_side(estimates: list[dict]) -> dict:
    summary: dict[str, dict[str, float | None]] = {
        "pulldown": {},
        "pullup": {},
    }
    for item in estimates:
        side = item.get("table")
        corner = item.get("corner")
        if side in summary and corner:
            summary[side][corner] = item.get("zout_ohm")
    return summary
