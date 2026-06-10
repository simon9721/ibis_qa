"""SVG plot artifacts for Markdown IBIS QA reports."""

from __future__ import annotations

import math
import re
from pathlib import Path
from xml.sax.saxutils import escape

from config import IV_RANGE_TOLERANCE, ZERO_CROSS_TOL_A


_IV_COLORS = {
    "pulldown": "#1f77b4",
    "pullup": "#d62728",
    "gnd_clamp": "#2ca02c",
    "power_clamp": "#9467bd",
}
_IV_LABELS = {
    "pulldown": "[Pulldown]",
    "pullup": "[Pullup]",
    "gnd_clamp": "[GND Clamp]",
    "power_clamp": "[POWER Clamp]",
}
_IV_COMBINED_COLORS = {
    "pd_gnd": "#0f766e",
    "pu_pwr": "#7c2d12",
}
_ISSO_COLORS = {
    "isso_pd": "#1f77b4",
    "isso_pu": "#d62728",
}
_ISSO_LABELS = {
    "isso_pd": "[ISSO PD]",
    "isso_pu": "[ISSO PU]",
}
_WAVEFORM_COLORS = [
    "#1f77b4",
    "#d62728",
    "#2ca02c",
    "#9467bd",
    "#ff7f0e",
    "#17becf",
]
_ZOUT_CORNER_COLORS = {
    "typ": "#1f77b4",
    "min": "#ff7f0e",
    "max": "#2ca02c",
}
_ZOUT_CORNER_DASH = {
    "typ": "",
    "min": "5 4",
    "max": "2 4",
}
_ATTENTION_STATUSES = {"FAIL", "WARN", "ERROR"}
_ATTENTION_COLORS = {
    "FAIL": "#b42318",
    "ERROR": "#b42318",
    "WARN": "#b54708",
}
_FAMILY_PREFIXES = {
    "iv": ("5.3",),
    "iv_clamp": ("5.3",),
    "iv_zero": ("5.3",),
    "iv_clamp_sweep": ("5.3",),
    "isso": ("5.7",),
    "waveform": ("5.5", "5.8"),
}
_IV_CLAMP_CHECKS = {"5.3.10"}
_IV_ZERO_CHECKS = {"5.3.8", "5.3.9"}
_IV_CLAMP_SWEEP_CHECKS = {"5.3.4", "5.3.5"}


def write_markdown_plot_assets(
        report: dict,
        asset_dir: str | Path,
        asset_ref_prefix: str | None = None) -> dict[str, dict[str, str]]:
    """Write SVG plots used by Markdown reports.

    Returns a mapping of model name to plot-type references:
    ``{"MODEL": {"iv": "...", "isso": "...", "waveform": "..."}}``.
    """
    asset_path = Path(asset_dir)
    asset_path.mkdir(parents=True, exist_ok=True)
    ref_prefix = asset_ref_prefix if asset_ref_prefix is not None else asset_path.name
    max_level = report.get("max_level")
    include_level4 = max_level is None or max_level >= 4

    refs: dict[str, dict[str, str]] = {}
    for model_name, model_info in report.get("models", {}).items():
        model_refs: dict[str, str] = {}
        safe_model = _safe_name(model_name)

        iv_tables = model_info.get("iv_plot_data") or {}
        if _has_table_rows(iv_tables):
            iv_label = _iv_main_label(iv_tables)
            file_name = f"iv_{safe_model}.svg"
            (asset_path / file_name).write_text(
                _render_table_svg(
                    title=f"{model_name} {iv_label}",
                    model_info=model_info,
                    tables=iv_tables,
                    colors=_IV_COLORS,
                    labels=_IV_LABELS,
                    x_guides="iv",
                ),
                encoding="utf-8",
            )
            model_refs["iv"] = f"{ref_prefix.rstrip('/')}/{file_name}"
            model_refs["iv_label"] = iv_label

            clamp_svg = _render_iv_clamp_detail_svg(model_name, model_info, iv_tables)
            if clamp_svg:
                clamp_name = f"iv_clamp_{safe_model}.svg"
                (asset_path / clamp_name).write_text(clamp_svg, encoding="utf-8")
                model_refs["iv_clamp"] = f"{ref_prefix.rstrip('/')}/{clamp_name}"

            zero_svg = _render_iv_zero_detail_svg(model_name, model_info, iv_tables)
            if zero_svg:
                zero_name = f"iv_zero_{safe_model}.svg"
                (asset_path / zero_name).write_text(zero_svg, encoding="utf-8")
                model_refs["iv_zero"] = f"{ref_prefix.rstrip('/')}/{zero_name}"

            clamp_sweep_svg = _render_iv_clamp_sweep_svg(model_name, model_info, iv_tables)
            if clamp_sweep_svg:
                clamp_sweep_name = f"iv_clamp_sweep_{safe_model}.svg"
                (asset_path / clamp_sweep_name).write_text(clamp_sweep_svg, encoding="utf-8")
                model_refs["iv_clamp_sweep"] = f"{ref_prefix.rstrip('/')}/{clamp_sweep_name}"

            zout_svg = _render_zout_loadline_svg(model_name, model_info, iv_tables)
            if zout_svg:
                zout_name = f"zout_{safe_model}.svg"
                (asset_path / zout_name).write_text(zout_svg, encoding="utf-8")
                model_refs["zout"] = f"{ref_prefix.rstrip('/')}/{zout_name}"

        isso_tables = model_info.get("isso_plot_data") or {}
        if include_level4 and _has_table_rows(isso_tables):
            file_name = f"isso_{safe_model}.svg"
            (asset_path / file_name).write_text(
                _render_table_svg(
                    title=f"{model_name} ISSO Tables",
                    model_info=model_info,
                    tables=isso_tables,
                    colors=_ISSO_COLORS,
                    labels=_ISSO_LABELS,
                    x_guides="isso",
                ),
                encoding="utf-8",
            )
            model_refs["isso"] = f"{ref_prefix.rstrip('/')}/{file_name}"

        waveforms = model_info.get("waveform_plot_data") or []
        if any(waveform.get("vt_rows") for waveform in waveforms):
            file_name = f"wave_{safe_model}.svg"
            (asset_path / file_name).write_text(
                _render_waveform_svg(
                    model_name,
                    model_info,
                    waveforms,
                    include_composite_current=include_level4,
                ),
                encoding="utf-8",
            )
            model_refs["waveform"] = f"{ref_prefix.rstrip('/')}/{file_name}"

        if model_refs:
            refs[model_name] = model_refs

    return refs


def write_iv_plot_assets(
        report: dict,
        asset_dir: str | Path,
        asset_ref_prefix: str | None = None) -> dict[str, str]:
    """Backward-compatible helper returning only I-V plot references."""
    refs = write_markdown_plot_assets(report, asset_dir, asset_ref_prefix)
    return {
        model_name: model_refs["iv"]
        for model_name, model_refs in refs.items()
        if "iv" in model_refs
    }


def _render_table_svg(
        title: str,
        model_info: dict,
        tables: dict,
        colors: dict[str, str],
        labels: dict[str, str],
        x_guides: str) -> str:
    width = 800
    height = 560
    left = 78
    right = 28
    top = 52
    bottom = 160
    plot_w = width - left - right
    plot_h = height - top - bottom

    if x_guides == "iv":
        curves = _combined_iv_curves(tables)
        combined_curves = curves
        mono_points = _monotonicity_violation_points(model_info)
    else:
        curves = _table_curves(tables, colors, labels)
        combined_curves = []
        mono_points = []

    xs = [x for curve in curves for x, _y in curve["points"]]
    ys = [y for curve in curves for _x, y in curve["points"]]
    if not xs or not ys:
        return _empty_svg(width, height, title)

    for point in mono_points:
        xs.append(point["v2"])
        ys.append(point["i2"])

    x_min, x_max = _padded_range(min(xs), max(xs), 0.02)
    y_min, y_max = _padded_range(min(ys), max(ys), 0.08)

    sx = lambda value: left + (value - x_min) / (x_max - x_min) * plot_w
    sy = lambda value: top + (y_max - value) / (y_max - y_min) * plot_h

    parts = [
        _svg_open(width, height),
        '<rect width="100%" height="100%" fill="#ffffff"/>',
        f'<text x="{left}" y="25" font-family="Arial, sans-serif" font-size="16" font-weight="700">{escape(title)}</text>',
        f'<rect x="{left}" y="{top}" width="{plot_w}" height="{plot_h}" fill="#fbfbfb" stroke="#c8c8c8"/>',
    ]
    _append_xy_grid(parts, left, top, plot_w, plot_h, x_min, x_max, y_min, y_max, sx, sy)
    _append_zero_guides(parts, left, top, plot_w, plot_h, x_min, x_max, y_min, y_max, sx, sy)
    _append_voltage_guides(parts, model_info, x_guides, top, plot_h, x_min, x_max, sx)

    for curve in curves:
        points = " ".join(f"{sx(x):.2f},{sy(y):.2f}" for x, y in curve["points"])
        dash = f' stroke-dasharray="{curve["dash"]}"' if curve["dash"] else ""
        parts.append(
            f'<polyline fill="none" stroke="{curve["color"]}" stroke-width="{curve["width"]}" '
            f'opacity="{curve["opacity"]}"{dash} points="{points}"/>'
        )
        if curve["corner"] == "typ":
            for endpoint in (curve["points"][0], curve["points"][-1]):
                parts.append(
                    f'<circle cx="{sx(endpoint[0]):.2f}" cy="{sy(endpoint[1]):.2f}" '
                    f'r="3" fill="{curve["color"]}" stroke="#ffffff" stroke-width="1"/>'
                )

    if x_guides != "iv":
        _append_zero_current_markers(parts, tables, colors, labels, x_min, x_max, y_min, y_max, sx, sy)
    else:
        _append_monotonicity_markers(parts, mono_points, x_min, x_max, y_min, y_max, sx, sy)
    _append_table_legend(
        parts,
        tables,
        colors,
        labels,
        left + 10,
        top + 18,
        extra_items=[
            (curve["color"], curve["label"], curve["dash"])
            for curve in combined_curves
        ] if combined_curves else None,
        include_base_items=x_guides != "iv",
    )
    _append_findings_panel(
        parts,
        _plot_findings(model_info, x_guides),
        left,
        top + plot_h + 64,
        plot_w,
        max_lines=3,
    )

    parts.extend([
        f'<text x="{left + plot_w / 2:.2f}" y="{top + plot_h + 44:.2f}" text-anchor="middle" font-family="Arial, sans-serif" font-size="12">Table voltage (V)</text>',
        f'<text transform="translate(18 {top + plot_h / 2:.2f}) rotate(-90)" text-anchor="middle" font-family="Arial, sans-serif" font-size="12">Current (A)</text>',
        (
            '<text x="420" y="42" font-family="Arial, sans-serif" font-size="11" fill="#555">'
            + ("thick dashed=combined typ curves" if x_guides == "iv" else "solid=typ, dashed=min/max, open circles=I(0 V)")
            + "</text>"
        ),
        '</svg>',
    ])
    return "\n".join(parts)


def _render_waveform_svg(
        model_name: str,
        model_info: dict,
        waveforms: list[dict],
        include_composite_current: bool = True) -> str:
    if not include_composite_current:
        return _render_vt_waveform_svg(model_name, model_info, waveforms)

    width = 800
    height = 640
    left = 78
    right = 28
    top = 54
    gap = 46
    panel_h = 178
    panel_w = width - left - right
    vt_top = top
    cc_top = top + panel_h + gap
    bottom = height - cc_top - panel_h

    vt_curves = []
    cc_curves = []
    for index, waveform in enumerate(waveforms):
        color = _WAVEFORM_COLORS[index % len(_WAVEFORM_COLORS)]
        label = f"{waveform.get('direction', 'waveform')} #{waveform.get('index', index + 1)}"
        vt_rows = _numeric_rows(waveform.get("vt_rows", []))
        vt_points = [
            (row[0], row[1])
            for row in vt_rows
            if len(row) > 1 and row[0] is not None and row[1] is not None
        ]
        if vt_points:
            vt_curves.append((label, color, vt_points, waveform.get("v_fixture")))
        cc_rows = _numeric_rows(waveform.get("composite_current_rows", []))
        cc_points = [
            (row[0], row[1])
            for row in cc_rows
            if len(row) > 1 and row[0] is not None and row[1] is not None
        ]
        if cc_points:
            cc_curves.append((label, color, cc_points))

    all_x = [x for _label, _color, points, _fixture in vt_curves for x, _y in points]
    all_x += [x for _label, _color, points in cc_curves for x, _y in points]
    vt_y = [y for _label, _color, points, _fixture in vt_curves for _x, y in points]
    cc_y = [y for _label, _color, points in cc_curves for _x, y in points]
    if not all_x or not vt_y:
        return _empty_svg(width, height, f"{model_name} waveforms")

    x_min, x_max = _padded_range(min(all_x), max(all_x), 0.02)
    vt_min, vt_max = _padded_range(min(vt_y), max(vt_y), 0.08)
    if cc_y:
        cc_min, cc_max = _padded_range(min(cc_y), max(cc_y), 0.12)
    else:
        cc_min, cc_max = -1.0, 1.0

    sx = lambda value: left + (value - x_min) / (x_max - x_min) * panel_w
    sy_v = lambda value: vt_top + (vt_max - value) / (vt_max - vt_min) * panel_h
    sy_c = lambda value: cc_top + (cc_max - value) / (cc_max - cc_min) * panel_h

    parts = [
        _svg_open(width, height),
        '<rect width="100%" height="100%" fill="#ffffff"/>',
        f'<text x="{left}" y="25" font-family="Arial, sans-serif" font-size="16" font-weight="700">{escape(model_name)} V-T and Composite Current</text>',
    ]
    _append_panel(parts, left, vt_top, panel_w, panel_h, "Voltage (V)")
    _append_panel(parts, left, cc_top, panel_w, panel_h, "Composite Current (A)")
    _append_panel_grid(parts, left, vt_top, panel_w, panel_h, x_min, x_max, vt_min, vt_max, sx, sy_v, _fmt_time, _fmt)
    _append_panel_grid(parts, left, cc_top, panel_w, panel_h, x_min, x_max, cc_min, cc_max, sx, sy_c, _fmt_time, _fmt_current)

    for label, color, points, fixture in vt_curves:
        if fixture is not None and vt_min <= fixture <= vt_max:
            y = sy_v(fixture)
            parts.append(f'<line x1="{left}" y1="{y:.2f}" x2="{left + panel_w}" y2="{y:.2f}" stroke="{color}" opacity="0.18" stroke-dasharray="3 4"/>')
        parts.append(_polyline(points, sx, sy_v, color, "2.0"))

    if cc_curves:
        for label, color, points in cc_curves:
            parts.append(_polyline(points, sx, sy_c, color, "1.8", dash="4 4"))
            for endpoint in (points[0], points[-1]):
                parts.append(
                    f'<circle cx="{sx(endpoint[0]):.2f}" cy="{sy_c(endpoint[1]):.2f}" '
                    f'r="3" fill="{color}" stroke="#ffffff" stroke-width="1"/>'
                )
    else:
        parts.append(
            f'<text x="{left + 14}" y="{cc_top + 32}" font-family="Arial, sans-serif" '
            f'font-size="12" fill="#777">No Composite Current rows parsed for this model.</text>'
        )

    legend_x = left + 10
    legend_y = vt_top + 18
    for idx, (label, color, _points, _fixture) in enumerate(vt_curves[:8]):
        y = legend_y + idx * 18
        parts.append(f'<line x1="{legend_x}" y1="{y}" x2="{legend_x + 22}" y2="{y}" stroke="{color}" stroke-width="2.4"/>')
        parts.append(f'<text x="{legend_x + 28}" y="{y + 4}" font-family="Arial, sans-serif" font-size="12">{escape(label)}</text>')

    _append_findings_panel(
        parts,
        _plot_findings(model_info, "waveform"),
        left,
        500,
        panel_w,
        max_lines=4,
    )

    parts.extend([
        f'<text x="{left + panel_w / 2:.2f}" y="{height - max(bottom - 18, 16)}" text-anchor="middle" font-family="Arial, sans-serif" font-size="12">Time (s)</text>',
        '<text x="420" y="42" font-family="Arial, sans-serif" font-size="11" fill="#555">solid=V-T voltage, dashed=Composite Current, faint horizontal=V_fixture</text>',
        '</svg>',
    ])
    return "\n".join(parts)


def _render_iv_clamp_detail_svg(model_name: str, model_info: dict, tables: dict) -> str | None:
    return _render_iv_window_svg(
        model_name=model_name,
        model_info=model_info,
        tables=tables,
        table_names=("gnd_clamp", "power_clamp"),
        title="I-V Clamp Detail",
        family="iv_clamp",
        x_axis_label="Table voltage (V), zoomed 0..Vcc",
        note="clamp curves show typ/min/max; open circles mark clamp I(0 V)",
    )


def _render_iv_zero_detail_svg(model_name: str, model_info: dict, tables: dict) -> str | None:
    return _render_iv_window_svg(
        model_name=model_name,
        model_info=model_info,
        tables=tables,
        table_names=("pulldown", "pullup"),
        title="I-V Pullup/Pulldown 0 V Detail",
        family="iv_zero",
        x_axis_label="Table voltage (V), zoomed around 0 V",
        note="pullup/pulldown curves show typ/min/max; open circles mark I(0 V)",
    )


def _render_iv_clamp_sweep_svg(model_name: str, model_info: dict, tables: dict) -> str | None:
    clamp_tables = {
        name: tables.get(name)
        for name in ("gnd_clamp", "power_clamp")
        if (tables.get(name) or {}).get("rows")
    }
    if not clamp_tables:
        return None

    width = 800
    height = 560
    left = 78
    right = 28
    top = 52
    bottom = 160
    plot_w = width - left - right
    plot_h = height - top - bottom

    curves = _table_curves(clamp_tables, _IV_COLORS, _IV_LABELS)
    sweep_findings = [
        finding for finding in _sweep_range_findings(model_info)
        if finding["table"] in clamp_tables
    ]

    xs = [x for curve in curves for x, _y in curve["points"]]
    ys = [y for curve in curves for _x, y in curve["points"]]
    if not xs or not ys:
        return None

    for finding in sweep_findings:
        xs.append(finding["value"])

    x_min, x_max = _padded_range(min(xs), max(xs), 0.05)
    y_min, y_max = _padded_range(min(ys), max(ys), 0.08)

    sx = lambda value: left + (value - x_min) / (x_max - x_min) * plot_w
    sy = lambda value: top + (y_max - value) / (y_max - y_min) * plot_h

    parts = [
        _svg_open(width, height),
        '<rect width="100%" height="100%" fill="#ffffff"/>',
        f'<text x="{left}" y="25" font-family="Arial, sans-serif" font-size="16" font-weight="700">{escape(model_name)} I-V Clamp Sweep Range</text>',
        f'<rect x="{left}" y="{top}" width="{plot_w}" height="{plot_h}" fill="#fbfbfb" stroke="#c8c8c8"/>',
    ]
    _append_xy_grid(parts, left, top, plot_w, plot_h, x_min, x_max, y_min, y_max, sx, sy)
    _append_zero_guides(parts, left, top, plot_w, plot_h, x_min, x_max, y_min, y_max, sx, sy)
    _append_voltage_guides(parts, model_info, "iv", top, plot_h, x_min, x_max, sx)

    for curve in curves:
        points = " ".join(f"{sx(x):.2f},{sy(y):.2f}" for x, y in curve["points"])
        dash = f' stroke-dasharray="{curve["dash"]}"' if curve["dash"] else ""
        parts.append(
            f'<polyline fill="none" stroke="{curve["color"]}" stroke-width="{curve["width"]}" '
            f'opacity="{curve["opacity"]}"{dash} points="{points}"/>'
        )

    _append_sweep_range_markers(
        parts, sweep_findings, top, plot_h, x_min, x_max, sx,
        color_for=lambda finding: _IV_COLORS.get(finding["table"], "#b42318"),
    )

    _append_table_legend(parts, clamp_tables, _IV_COLORS, _IV_LABELS, left + 10, top + 18)
    _append_findings_panel(
        parts,
        _plot_findings(model_info, "iv_clamp_sweep"),
        left,
        top + plot_h + 64,
        plot_w,
        max_lines=3,
    )
    parts.extend([
        f'<text x="{left + plot_w / 2:.2f}" y="{top + plot_h + 44:.2f}" text-anchor="middle" font-family="Arial, sans-serif" font-size="12">Table voltage (V)</text>',
        f'<text transform="translate(18 {top + plot_h / 2:.2f}) rotate(-90)" text-anchor="middle" font-family="Arial, sans-serif" font-size="12">Current (A)</text>',
        '<text x="420" y="42" font-family="Arial, sans-serif" font-size="11" fill="#555">solid=typ, dashed=min/max; dashed vertical=required sweep boundary (5.3.4/5.3.5)</text>',
        '</svg>',
    ])
    return "\n".join(parts)


def _render_zout_loadline_svg(model_name: str, model_info: dict, tables: dict) -> str | None:
    zout = model_info.get("zout") or {}
    estimates = [
        item for item in zout.get("estimates", [])
        if item.get("status") == "estimated"
        and item.get("table") in {"pulldown", "pullup"}
    ]
    if not estimates:
        return None

    sides = [
        side for side in ("pulldown", "pullup")
        if any(item.get("table") == side for item in estimates)
        and _numeric_rows((tables.get(side) or {}).get("rows", []))
    ]
    if not sides:
        return None

    r_load = _safe_float(zout.get("r_load_ohm")) or 50.0
    width = 900
    height = 620
    left = 72
    right = 28
    top = 62
    gap = 40
    panel_h = 286
    panel_w = (width - left - right - gap * (len(sides) - 1)) / len(sides)
    summary_top = top + panel_h + 70

    parts = [
        _svg_open(width, height),
        '<rect width="100%" height="100%" fill="#ffffff"/>',
        f'<text x="{left}" y="26" font-family="Arial, sans-serif" font-size="16" font-weight="700">{escape(model_name)} Zout Load-Line Curves</text>',
        f'<text x="{left}" y="45" font-family="Arial, sans-serif" font-size="11" fill="#555">Rload={_fmt_number(r_load)} ohm; solid=device I-V, dashed=load line, circles=operating points</text>',
    ]

    for index, side in enumerate(sides):
        panel_left = left + index * (panel_w + gap)
        _append_zout_panel(
            parts=parts,
            side=side,
            tables=tables,
            estimates=[item for item in estimates if item.get("table") == side],
            r_load=r_load,
            x=panel_left,
            y=top,
            width=panel_w,
            height=panel_h,
        )

    _append_zout_summary_table(
        parts,
        estimates,
        left,
        summary_top,
        width - left - right,
    )
    parts.append("</svg>")
    return "\n".join(parts)


def _append_zout_panel(
        parts,
        side: str,
        tables: dict,
        estimates: list[dict],
        r_load: float,
        x: float,
        y: float,
        width: float,
        height: float) -> None:
    rows = _numeric_rows((tables.get(side) or {}).get("rows", []))
    title = "[Pulldown] Rload to Vdd" if side == "pulldown" else "[Pullup] Rload to GND"
    axis_note = "Output voltage (V)" if side == "pulldown" else "Vcc-relative table voltage (V)"

    curve_sets = []
    x_values = []
    y_values = []
    for col, corner in [(1, "typ"), (2, "min"), (3, "max")]:
        points = [
            (row[0], row[col])
            for row in rows
            if len(row) > col and row[0] is not None and row[col] is not None
        ]
        if not points:
            continue
        curve_sets.append((corner, points))
        x_values.extend(point[0] for point in points)
        y_values.extend(point[1] for point in points)

    for item in estimates:
        v_table = _safe_float(item.get("table_voltage_v"))
        i_op = _safe_float(item.get("i_op_a"))
        vcc = _safe_float(item.get("vcc_v"))
        if v_table is not None:
            x_values.append(v_table)
        if i_op is not None:
            y_values.append(i_op)
        if vcc is not None and rows:
            v_min = min(row[0] for row in rows if row and row[0] is not None)
            v_max = max(row[0] for row in rows if row and row[0] is not None)
            for vx in (v_min, v_max):
                y_values.append(_zout_loadline_current(side, vx, vcc, r_load))

    parts.append(f'<rect x="{x:.2f}" y="{y:.2f}" width="{width:.2f}" height="{height:.2f}" fill="#fbfbfb" stroke="#c8c8c8"/>')
    parts.append(f'<text x="{x + 8:.2f}" y="{y - 12:.2f}" font-family="Arial, sans-serif" font-size="13" font-weight="700">{escape(title)}</text>')

    if not x_values or not y_values:
        parts.append(f'<text x="{x + 16:.2f}" y="{y + 38:.2f}" font-family="Arial, sans-serif" font-size="12" fill="#777">No Zout plot data.</text>')
        return

    x_min, x_max = _padded_range(min(x_values), max(x_values), 0.04)
    y_min, y_max = _padded_range(min(y_values), max(y_values), 0.12)
    sx = lambda value: x + (value - x_min) / (x_max - x_min) * width
    sy = lambda value: y + (y_max - value) / (y_max - y_min) * height

    _append_zout_grid(parts, x, y, width, height, x_min, x_max, y_min, y_max, sx, sy)
    _append_zero_guides(parts, x, y, width, height, x_min, x_max, y_min, y_max, sx, sy)

    for corner, points in curve_sets:
        color = _ZOUT_CORNER_COLORS.get(corner, "#333333")
        dash = _ZOUT_CORNER_DASH.get(corner, "")
        parts.append(_polyline(points, sx, sy, color, "1.8", dash=dash))

    v_range = _ticks(x_min, x_max, 80)
    for item in sorted(estimates, key=lambda value: _zout_corner_rank(value.get("corner", ""))):
        corner = item.get("corner", "")
        vcc = _safe_float(item.get("vcc_v"))
        if vcc is None:
            continue
        color = _ZOUT_CORNER_COLORS.get(corner, "#333333")
        load_points = [
            (vx, _zout_loadline_current(side, vx, vcc, r_load))
            for vx in v_range
        ]
        parts.append(_polyline(load_points, sx, sy, color, "1.1", dash="6 4"))

        v_table = _safe_float(item.get("table_voltage_v"))
        i_op = _safe_float(item.get("i_op_a"))
        zout = _safe_float(item.get("zout_ohm"))
        if v_table is None or i_op is None:
            continue
        parts.append(
            f'<circle cx="{sx(v_table):.2f}" cy="{sy(i_op):.2f}" r="4.6" '
            f'fill="#ffffff" stroke="{color}" stroke-width="2"/>'
        )
        parts.append(
            f'<text x="{sx(v_table) + 6:.2f}" y="{sy(i_op) - 6:.2f}" '
            f'font-family="Arial, sans-serif" font-size="10" fill="{color}">'
            f'{escape(corner)} {escape(_fmt_number(zout))} ohm</text>'
        )

    legend_y = y + 18
    for index, corner in enumerate(("typ", "min", "max")):
        yy = legend_y + index * 17
        color = _ZOUT_CORNER_COLORS[corner]
        dash = _ZOUT_CORNER_DASH[corner]
        attrs = f' stroke-dasharray="{dash}"' if dash else ""
        parts.append(f'<line x1="{x + 10:.2f}" y1="{yy:.2f}" x2="{x + 32:.2f}" y2="{yy:.2f}" stroke="{color}" stroke-width="2"{attrs}/>')
        parts.append(f'<text x="{x + 38:.2f}" y="{yy + 4:.2f}" font-family="Arial, sans-serif" font-size="11">{corner}</text>')

    parts.extend([
        f'<text x="{x + width / 2:.2f}" y="{y + height + 38:.2f}" text-anchor="middle" font-family="Arial, sans-serif" font-size="11">{escape(axis_note)}</text>',
        f'<text transform="translate({x - 50:.2f} {y + height / 2:.2f}) rotate(-90)" text-anchor="middle" font-family="Arial, sans-serif" font-size="11">Current (mA)</text>',
    ])


def _append_zout_grid(parts, x, y, width, height, x_min, x_max, y_min, y_max, sx, sy) -> None:
    for tick in _ticks(x_min, x_max, 5):
        tx = sx(tick)
        parts.append(f'<line x1="{tx:.2f}" y1="{y:.2f}" x2="{tx:.2f}" y2="{y + height:.2f}" stroke="#ececec"/>')
        parts.append(f'<text x="{tx:.2f}" y="{y + height + 18:.2f}" text-anchor="middle" font-family="Arial, sans-serif" font-size="10">{_fmt(tick)}</text>')
    for tick in _ticks(y_min, y_max, 5):
        ty = sy(tick)
        parts.append(f'<line x1="{x:.2f}" y1="{ty:.2f}" x2="{x + width:.2f}" y2="{ty:.2f}" stroke="#ececec"/>')
        parts.append(f'<text x="{x - 7:.2f}" y="{ty + 4:.2f}" text-anchor="end" font-family="Arial, sans-serif" font-size="10">{_fmt_current_ma(tick)}</text>')


def _append_zout_summary_table(parts, estimates: list[dict], x: float, y: float, width: float) -> None:
    rows = [
        item for item in sorted(
            estimates,
            key=lambda value: (0 if value.get("table") == "pulldown" else 1, _zout_corner_rank(value.get("corner", ""))),
        )
        if item.get("status") == "estimated"
    ]
    if not rows:
        return

    row_h = 19
    col_x = [x + 10, x + 102, x + 170, x + 260, x + 350, x + 440]
    headers = ["Table", "Corner", "Vout", "Iop", "Zout", "Rseries"]
    height = 30 + row_h * min(len(rows), 8)
    parts.append(f'<rect x="{x:.2f}" y="{y:.2f}" width="{width:.2f}" height="{height:.2f}" fill="#ffffff" stroke="#c8c8c8"/>')
    parts.append(f'<text x="{x + 10:.2f}" y="{y + 18:.2f}" font-family="Arial, sans-serif" font-size="12" font-weight="700">Operating-point summary</text>')
    for col, header in zip(col_x, headers):
        parts.append(f'<text x="{col:.2f}" y="{y + 36:.2f}" font-family="Arial, sans-serif" font-size="10" font-weight="700" fill="#333">{header}</text>')

    for index, item in enumerate(rows[:8]):
        yy = y + 36 + (index + 1) * row_h
        color = _ZOUT_CORNER_COLORS.get(item.get("corner", ""), "#333333")
        values = [
            item.get("table", ""),
            item.get("corner", ""),
            f'{_fmt_number(_safe_float(item.get("output_voltage_v")))} V',
            f'{_fmt_current_ma(_safe_float(item.get("i_op_a")))} mA',
            f'{_fmt_number(_safe_float(item.get("zout_ohm")))} ohm',
            f'{_fmt_number(_safe_float(item.get("r_series_ohm")))} ohm',
        ]
        for col, value in zip(col_x, values):
            parts.append(f'<text x="{col:.2f}" y="{yy:.2f}" font-family="Arial, sans-serif" font-size="10" fill="{color}">{escape(str(value))}</text>')
    if len(rows) > 8:
        parts.append(f'<text x="{x + 10:.2f}" y="{y + height - 8:.2f}" font-family="Arial, sans-serif" font-size="10" fill="#555">{len(rows) - 8} more operating points in JSON.</text>')


def _zout_loadline_current(side: str, v_table: float, vcc: float, r_load: float) -> float:
    if side == "pullup":
        return -(vcc - v_table) / r_load
    return (vcc - v_table) / r_load


def _zout_corner_rank(corner: str) -> int:
    return {"typ": 0, "min": 1, "max": 2}.get(corner, 9)


def _render_iv_window_svg(
        model_name: str,
        model_info: dict,
        tables: dict,
        table_names: tuple[str, ...],
        title: str,
        family: str,
        x_axis_label: str,
        note: str) -> str | None:
    vcc = _first_number(model_info.get("voltage_range"))
    if not vcc or vcc <= 0:
        return None

    width = 800
    height = 520
    left = 78
    right = 32
    top = 54
    bottom = 160
    plot_w = width - left - right
    plot_h = height - top - bottom
    x_min, x_max = 0.0, vcc

    curves = []
    y_values = []
    for table_name in table_names:
        rows = _numeric_rows((tables.get(table_name) or {}).get("rows", []))
        if not rows:
            continue
        for col_index, corner, dash, opacity, width_px in [
            (2, "min", "4 4", "0.55", "1.2"),
            (3, "max", "4 4", "0.55", "1.2"),
            (1, "typ", "", "1.0", "2.0"),
        ]:
            points = _points_in_window(rows, x_min, x_max, col_index)
            if not points:
                continue
            curves.append({
                "table": table_name,
                "label": _IV_LABELS.get(table_name, table_name),
                "corner": corner,
                "color": _IV_COLORS.get(table_name, "#333333"),
                "dash": dash,
                "opacity": opacity,
                "width": width_px,
                "points": points,
            })
            y_values.extend(value for _voltage, value in points)

    zero_markers = []
    for table_name in table_names:
        rows = _numeric_rows((tables.get(table_name) or {}).get("rows", []))
        if not rows:
            continue
        for col_index, corner, radius in [(1, "typ", 4.0), (2, "min", 3.0), (3, "max", 3.0)]:
            value = _interpolate(rows, 0.0, col_index)
            if value is None:
                continue
            zero_markers.append({
                "table": table_name,
                "corner": corner,
                "value": value,
                "radius": radius,
                "color": _IV_COLORS.get(table_name, "#333333"),
            })
            y_values.append(value)

    if not y_values:
        return None

    if family == "iv_zero":
        y_values.append(ZERO_CROSS_TOL_A)
        y_values.append(-ZERO_CROSS_TOL_A)

    y_min, y_max = _padded_range(min(y_values), max(y_values), 0.16)
    sx = lambda value: left + (value - x_min) / (x_max - x_min) * plot_w
    sy = lambda value: top + (y_max - value) / (y_max - y_min) * plot_h

    parts = [
        _svg_open(width, height),
        '<rect width="100%" height="100%" fill="#ffffff"/>',
        f'<text x="{left}" y="25" font-family="Arial, sans-serif" font-size="16" font-weight="700">{escape(model_name)} {escape(title)}</text>',
        f'<rect x="{left}" y="{top}" width="{plot_w}" height="{plot_h}" fill="#fbfbfb" stroke="#c8c8c8"/>',
    ]
    _append_xy_grid(parts, left, top, plot_w, plot_h, x_min, x_max, y_min, y_max, sx, sy)
    _append_zero_guides(parts, left, top, plot_w, plot_h, x_min, x_max, y_min, y_max, sx, sy)
    _append_voltage_guides(parts, model_info, "isso", top, plot_h, x_min, x_max, sx)

    for curve in curves:
        data = " ".join(f"{sx(voltage):.2f},{sy(current):.2f}" for voltage, current in curve["points"])
        dash = f' stroke-dasharray="{curve["dash"]}"' if curve["dash"] else ""
        parts.append(
            f'<polyline fill="none" stroke="{curve["color"]}" stroke-width="{curve["width"]}" '
            f'opacity="{curve["opacity"]}"{dash} points="{data}"/>'
        )

    for marker in zero_markers:
        parts.append(
            f'<circle cx="{sx(0.0):.2f}" cy="{sy(marker["value"]):.2f}" r="{marker["radius"]:.1f}" '
            f'fill="#ffffff" stroke="{marker["color"]}" stroke-width="1.5"/>'
        )

    if family == "iv_zero":
        for bound_value, label in (
            (ZERO_CROSS_TOL_A, f"+{ZERO_CROSS_TOL_A * 1e6:.0f}uA leakage limit"),
            (-ZERO_CROSS_TOL_A, f"-{ZERO_CROSS_TOL_A * 1e6:.0f}uA leakage limit"),
        ):
            if y_min <= bound_value <= y_max:
                y = sy(bound_value)
                parts.append(
                    f'<line x1="{left}" y1="{y:.2f}" x2="{left + plot_w}" y2="{y:.2f}" '
                    f'stroke="#b54708" stroke-width="1.4" stroke-dasharray="5 3"/>'
                )
                parts.append(
                    f'<text x="{left + plot_w - 4}" y="{y - 4:.2f}" text-anchor="end" '
                    f'font-family="Arial, sans-serif" font-size="10" fill="#b54708">{escape(label)}</text>'
                )

    _append_table_legend(
        parts,
        {
            table_name: tables.get(table_name)
            for table_name in table_names
            if (tables.get(table_name) or {}).get("rows")
        },
        _IV_COLORS,
        _IV_LABELS,
        left + 10,
        top + 18,
    )
    parts.extend([
        f'<text x="{left + plot_w / 2:.2f}" y="{top + plot_h + 44:.2f}" text-anchor="middle" font-family="Arial, sans-serif" font-size="12">{escape(x_axis_label)}</text>',
        f'<text transform="translate(18 {top + plot_h / 2:.2f}) rotate(-90)" text-anchor="middle" font-family="Arial, sans-serif" font-size="12">Current (A)</text>',
        f'<text x="420" y="42" font-family="Arial, sans-serif" font-size="11" fill="#555">{escape(note)}</text>',
    ])
    _append_findings_panel(
        parts,
        _plot_findings(model_info, family),
        left,
        top + plot_h + 62,
        plot_w,
        max_lines=3,
    )
    parts.append('</svg>')
    return "\n".join(parts)


def _render_vt_waveform_svg(model_name: str, model_info: dict, waveforms: list[dict]) -> str:
    width = 800
    height = 450
    left = 78
    right = 28
    top = 54
    panel_h = 230
    panel_w = width - left - right

    vt_curves = []
    for index, waveform in enumerate(waveforms):
        color = _WAVEFORM_COLORS[index % len(_WAVEFORM_COLORS)]
        label = f"{waveform.get('direction', 'waveform')} #{waveform.get('index', index + 1)}"
        vt_rows = _numeric_rows(waveform.get("vt_rows", []))
        vt_points = [
            (row[0], row[1])
            for row in vt_rows
            if len(row) > 1 and row[0] is not None and row[1] is not None
        ]
        if vt_points:
            vt_curves.append((label, color, vt_points, waveform.get("v_fixture")))

    all_x = [x for _label, _color, points, _fixture in vt_curves for x, _y in points]
    vt_y = [y for _label, _color, points, _fixture in vt_curves for _x, y in points]
    if not all_x or not vt_y:
        return _empty_svg(width, height, f"{model_name} V-T waveforms")

    x_min, x_max = _padded_range(min(all_x), max(all_x), 0.02)
    vt_min, vt_max = _padded_range(min(vt_y), max(vt_y), 0.08)
    sx = lambda value: left + (value - x_min) / (x_max - x_min) * panel_w
    sy_v = lambda value: top + (vt_max - value) / (vt_max - vt_min) * panel_h

    parts = [
        _svg_open(width, height),
        '<rect width="100%" height="100%" fill="#ffffff"/>',
        f'<text x="{left}" y="25" font-family="Arial, sans-serif" font-size="16" font-weight="700">{escape(model_name)} V-T Waveforms</text>',
    ]
    _append_panel(parts, left, top, panel_w, panel_h, "Voltage (V)")
    _append_panel_grid(parts, left, top, panel_w, panel_h, x_min, x_max, vt_min, vt_max, sx, sy_v, _fmt_time, _fmt)

    for label, color, points, fixture in vt_curves:
        if fixture is not None and vt_min <= fixture <= vt_max:
            y = sy_v(fixture)
            parts.append(f'<line x1="{left}" y1="{y:.2f}" x2="{left + panel_w}" y2="{y:.2f}" stroke="{color}" opacity="0.18" stroke-dasharray="3 4"/>')
        parts.append(_polyline(points, sx, sy_v, color, "2.0"))

    legend_x = left + 10
    legend_y = top + 18
    for idx, (label, color, _points, _fixture) in enumerate(vt_curves[:8]):
        y = legend_y + idx * 18
        parts.append(f'<line x1="{legend_x}" y1="{y}" x2="{legend_x + 22}" y2="{y}" stroke="{color}" stroke-width="2.4"/>')
        parts.append(f'<text x="{legend_x + 28}" y="{y + 4}" font-family="Arial, sans-serif" font-size="12">{escape(label)}</text>')

    _append_findings_panel(
        parts,
        _plot_findings(model_info, "waveform"),
        left,
        top + panel_h + 58,
        panel_w,
        max_lines=4,
    )

    parts.extend([
        f'<text x="{left + panel_w / 2:.2f}" y="{top + panel_h + 38:.2f}" text-anchor="middle" font-family="Arial, sans-serif" font-size="12">Time (s)</text>',
        '<text x="420" y="42" font-family="Arial, sans-serif" font-size="11" fill="#555">solid=V-T voltage, faint horizontal=V_fixture</text>',
        '</svg>',
    ])
    return "\n".join(parts)


def _append_xy_grid(parts, left, top, plot_w, plot_h, x_min, x_max, y_min, y_max, sx, sy) -> None:
    for tick in _ticks(x_min, x_max, 6):
        x = sx(tick)
        parts.append(f'<line x1="{x:.2f}" y1="{top}" x2="{x:.2f}" y2="{top + plot_h}" stroke="#ececec"/>')
        parts.append(f'<text x="{x:.2f}" y="{top + plot_h + 22}" text-anchor="middle" font-family="Arial, sans-serif" font-size="11">{_fmt(tick)}</text>')
    for tick in _ticks(y_min, y_max, 6):
        y = sy(tick)
        parts.append(f'<line x1="{left}" y1="{y:.2f}" x2="{left + plot_w}" y2="{y:.2f}" stroke="#ececec"/>')
        parts.append(f'<text x="{left - 8}" y="{y + 4:.2f}" text-anchor="end" font-family="Arial, sans-serif" font-size="11">{_fmt_current(tick)}</text>')


def _append_panel(parts, left, top, width, height, label) -> None:
    parts.append(f'<rect x="{left}" y="{top}" width="{width}" height="{height}" fill="#fbfbfb" stroke="#c8c8c8"/>')
    parts.append(f'<text transform="translate(18 {top + height / 2:.2f}) rotate(-90)" text-anchor="middle" font-family="Arial, sans-serif" font-size="12">{escape(label)}</text>')


def _append_panel_grid(parts, left, top, width, height, x_min, x_max, y_min, y_max, sx, sy, fmt_x, fmt_y) -> None:
    for tick in _ticks(x_min, x_max, 6):
        x = sx(tick)
        parts.append(f'<line x1="{x:.2f}" y1="{top}" x2="{x:.2f}" y2="{top + height}" stroke="#ececec"/>')
        parts.append(f'<text x="{x:.2f}" y="{top + height + 18}" text-anchor="middle" font-family="Arial, sans-serif" font-size="10">{fmt_x(tick)}</text>')
    for tick in _ticks(y_min, y_max, 5):
        y = sy(tick)
        parts.append(f'<line x1="{left}" y1="{y:.2f}" x2="{left + width}" y2="{y:.2f}" stroke="#ececec"/>')
        parts.append(f'<text x="{left - 8}" y="{y + 4:.2f}" text-anchor="end" font-family="Arial, sans-serif" font-size="10">{fmt_y(tick)}</text>')


def _append_zero_guides(parts, left, top, plot_w, plot_h, x_min, x_max, y_min, y_max, sx, sy) -> None:
    if x_min <= 0.0 <= x_max:
        x0 = sx(0.0)
        parts.append(f'<line x1="{x0:.2f}" y1="{top}" x2="{x0:.2f}" y2="{top + plot_h}" stroke="#777" stroke-dasharray="4 4"/>')
    if y_min <= 0.0 <= y_max:
        y0 = sy(0.0)
        parts.append(f'<line x1="{left}" y1="{y0:.2f}" x2="{left + plot_w}" y2="{y0:.2f}" stroke="#777" stroke-dasharray="4 4"/>')


def _append_voltage_guides(parts, model_info, mode, top, plot_h, x_min, x_max, sx) -> None:
    vcc = _first_number(model_info.get("voltage_range"))
    if not vcc:
        return
    guides = [(-vcc, "-Vcc"), (vcc, "Vcc"), (2 * vcc, "2Vcc")] if mode == "iv" else [(0.0, "0V"), (vcc, "Vcc")]
    for marker, label in guides:
        if x_min <= marker <= x_max:
            x = sx(marker)
            parts.append(f'<line x1="{x:.2f}" y1="{top}" x2="{x:.2f}" y2="{top + plot_h}" stroke="#555" stroke-dasharray="2 4"/>')
            parts.append(f'<text x="{x + 4:.2f}" y="{top + 14}" font-family="Arial, sans-serif" font-size="11" fill="#555">{label}</text>')


def _append_zero_current_markers(parts, tables, colors, labels, x_min, x_max, y_min, y_max, sx, sy) -> None:
    if not (x_min <= 0.0 <= x_max):
        return
    for table_name, table in tables.items():
        rows = _numeric_rows(table.get("rows", []))
        color = colors.get(table_name, "#333333")
        for col_index, radius in [(1, 4.0), (2, 3.0), (3, 3.0)]:
            value = _interpolate(rows, 0.0, col_index)
            if value is None or not (y_min <= value <= y_max):
                continue
            parts.append(
                f'<circle cx="{sx(0.0):.2f}" cy="{sy(value):.2f}" r="{radius:.1f}" '
                f'fill="#ffffff" stroke="{color}" stroke-width="1.5"/>'
            )


def _append_table_legend(
        parts,
        tables,
        colors,
        labels,
        x,
        y,
        extra_items=None,
        include_base_items: bool = True) -> None:
    index = 0
    if include_base_items:
        for table_name in tables:
            if not (tables.get(table_name) or {}).get("rows"):
                continue
            color = colors.get(table_name, "#333333")
            label = labels.get(table_name, table_name)
            yy = y + index * 18
            parts.append(f'<line x1="{x}" y1="{yy}" x2="{x + 22}" y2="{yy}" stroke="{color}" stroke-width="2.4"/>')
            parts.append(f'<text x="{x + 28}" y="{yy + 4}" font-family="Arial, sans-serif" font-size="12">{escape(label)}</text>')
            index += 1
    for color, label, dash in extra_items or []:
        yy = y + index * 18
        parts.append(
            f'<line x1="{x}" y1="{yy}" x2="{x + 22}" y2="{yy}" '
            f'stroke="{color}" stroke-width="2.8" stroke-dasharray="{dash}"/>'
        )
        parts.append(f'<text x="{x + 28}" y="{yy + 4}" font-family="Arial, sans-serif" font-size="12">{escape(label)}</text>')
        index += 1


def _table_curves(tables: dict, colors: dict[str, str], labels: dict[str, str]) -> list[dict]:
    curves = []
    for table_name, table in tables.items():
        rows = _numeric_rows(table.get("rows", []))
        if not rows:
            continue
        color = colors.get(table_name, "#333333")
        label = labels.get(table_name, table_name)
        for col_index, corner, dash, opacity, width_px in [
            (2, "min", "4 4", "0.55", "1.2"),
            (3, "max", "4 4", "0.55", "1.2"),
            (1, "typ", "", "1.0", "2.0"),
        ]:
            points = [
                (row[0], row[col_index])
                for row in rows
                if len(row) > col_index and row[col_index] is not None
            ]
            if points:
                curves.append({
                    "table": table_name,
                    "label": label,
                    "corner": corner,
                    "color": color,
                    "dash": dash,
                    "opacity": opacity,
                    "width": width_px,
                    "points": points,
                })
    return curves


def _iv_main_label(tables: dict) -> str:
    has_pulldown = bool((tables.get("pulldown") or {}).get("rows"))
    has_pullup = bool((tables.get("pullup") or {}).get("rows"))
    has_gnd = bool((tables.get("gnd_clamp") or {}).get("rows"))
    has_power = bool((tables.get("power_clamp") or {}).get("rows"))
    has_combined = (has_pulldown and has_gnd) or (has_pullup and has_power)
    has_driver = has_pulldown or has_pullup
    has_clamp = has_gnd or has_power
    if has_combined:
        return "I-V Combined Curves"
    if has_clamp and not has_driver:
        return "I-V Clamp Curves"
    if has_driver and not has_clamp:
        return "I-V Pullup/Pulldown Curves"
    return "I-V Curves"


def _combined_iv_curves(tables: dict) -> list[dict]:
    combos = [
        ("pd_gnd", ["pulldown", "gnd_clamp"]),
        ("pu_pwr", ["pullup", "power_clamp"]),
    ]
    curves = []
    for combo_id, table_names in combos:
        present = []
        present_names = []
        for table_name in table_names:
            rows = _numeric_rows((tables.get(table_name) or {}).get("rows", []))
            if rows:
                present.append(rows)
                present_names.append(table_name)
        if not present:
            continue
        label = "+".join(_IV_LABELS.get(table_name, table_name) for table_name in present_names)
        voltages = sorted({
            row[0]
            for rows in present
            for row in rows
            if row and row[0] is not None
        })
        points = []
        for voltage in voltages:
            current = 0.0
            used = False
            for rows in present:
                value = _interpolate(rows, voltage, 1)
                if value is None:
                    continue
                current += value
                used = True
            if used:
                points.append((voltage, current))
        if len(points) >= 2:
            curves.append({
                "table": combo_id,
                "label": label,
                "corner": "combined typ",
                "color": _IV_COMBINED_COLORS[combo_id],
                "dash": "6 3",
                "opacity": "0.95",
                "width": "2.8",
                "points": points,
            })
    return curves


_SWEEP_TABLE_TO_COMBO = {
    "pulldown": "pd_gnd",
    "gnd_clamp": "pd_gnd",
    "pullup": "pu_pwr",
    "power_clamp": "pu_pwr",
}


def _sweep_range_findings(model_info: dict) -> list[dict]:
    """FAIL results carrying 5.3.x sweep-range data, mapped to combined curves."""
    findings = []
    for result in model_info.get("results", []):
        if result.get("status") != "FAIL":
            continue
        sweep = (result.get("data") or {}).get("sweep_range")
        if not sweep:
            continue
        combo = _SWEEP_TABLE_TO_COMBO.get(sweep.get("table", ""))
        if combo is None:
            continue
        expected_min = sweep.get("expected_min")
        expected_max = sweep.get("expected_max")
        actual_min = sweep.get("actual_min")
        actual_max = sweep.get("actual_max")
        if None in (expected_min, expected_max, actual_min, actual_max):
            continue
        table = sweep.get("table", "")
        tol = abs(expected_max - expected_min) * IV_RANGE_TOLERANCE
        if actual_min > expected_min + tol:
            findings.append({
                "check_id": result.get("check_id", ""),
                "combo": combo,
                "table": table,
                "bound": "min",
                "value": expected_min,
            })
        if actual_max < expected_max - tol:
            findings.append({
                "check_id": result.get("check_id", ""),
                "combo": combo,
                "table": table,
                "bound": "max",
                "value": expected_max,
            })
    return findings


def _monotonicity_violation_points(model_info: dict) -> list[dict]:
    """FAIL results carrying 5.3.7 monotonicity violation points."""
    points = []
    for result in model_info.get("results", []):
        if result.get("status") != "FAIL":
            continue
        mono = (result.get("data") or {}).get("monotonicity_violations")
        if not mono:
            continue
        for point in mono.get("points", []):
            v2 = point.get("v2")
            i2 = point.get("i2")
            if v2 is None or i2 is None:
                continue
            points.append({
                "check_id": result.get("check_id", ""),
                "combo": mono.get("combo"),
                "v2": v2,
                "i2": i2,
            })
    return points


def _append_sweep_range_markers(parts, findings: list[dict], top, plot_h, x_min, x_max, sx,
                                 color_for=None) -> None:
    if color_for is None:
        color_for = lambda finding: _IV_COMBINED_COLORS.get(finding.get("combo"), "#b42318")
    for index, finding in enumerate(findings):
        value = finding["value"]
        if not (x_min <= value <= x_max):
            continue
        color = color_for(finding)
        x = sx(value)
        parts.append(
            f'<line x1="{x:.2f}" y1="{top}" x2="{x:.2f}" y2="{top + plot_h}" '
            f'stroke="{color}" stroke-width="1.6" stroke-dasharray="6 3"/>'
        )
        bound_symbol = "≤" if finding["bound"] == "min" else "≥"
        label = f'{finding["check_id"]} needs {bound_symbol}{value:.3g}V'
        text_y = top + 14 + (index % 4) * 14
        parts.append(
            f'<text x="{x + 4:.2f}" y="{text_y}" font-family="Arial, sans-serif" '
            f'font-size="11" fill="{color}">{escape(label)}</text>'
        )


def _append_monotonicity_markers(parts, points: list[dict], x_min, x_max, y_min, y_max, sx, sy) -> None:
    for point in points:
        v2, i2 = point["v2"], point["i2"]
        if not (x_min <= v2 <= x_max and y_min <= i2 <= y_max):
            continue
        px, py = sx(v2), sy(i2)
        parts.append(
            f'<circle cx="{px:.2f}" cy="{py:.2f}" r="6" fill="none" '
            f'stroke="#b42318" stroke-width="2"/>'
        )
        parts.append(
            f'<line x1="{px - 5:.2f}" y1="{py - 5:.2f}" x2="{px + 5:.2f}" y2="{py + 5:.2f}" '
            f'stroke="#b42318" stroke-width="1.6"/>'
        )
        parts.append(
            f'<line x1="{px - 5:.2f}" y1="{py + 5:.2f}" x2="{px + 5:.2f}" y2="{py - 5:.2f}" '
            f'stroke="#b42318" stroke-width="1.6"/>'
        )
    if points:
        parts.append(
            f'<text x="420" y="{30}" font-family="Arial, sans-serif" font-size="11" '
            f'fill="#b42318">x = 5.3.7 monotonicity violation</text>'
        )


def _append_iv_operating_inset(
        parts,
        tables: dict,
        model_info: dict,
        colors: dict[str, str],
        labels: dict[str, str],
        x: float,
        y: float,
        width: float,
        height: float) -> None:
    vcc = _first_number(model_info.get("voltage_range"))
    if not vcc or vcc <= 0:
        return

    x_min, x_max = 0.0, vcc
    inset_curves = []
    y_values = []
    for table_name in ("gnd_clamp", "power_clamp"):
        rows = _numeric_rows((tables.get(table_name) or {}).get("rows", []))
        if not rows:
            continue
        for col_index, dash, width_px, opacity in [
            (2, "3 3", "1.0", "0.55"),
            (3, "3 3", "1.0", "0.55"),
            (1, "", "1.6", "0.95"),
        ]:
            points = _points_in_window(rows, x_min, x_max, col_index)
            if points:
                inset_curves.append((table_name, points, dash, width_px, opacity))
                y_values.extend(value for _voltage, value in points)

    zero_markers = []
    for table_name in ("pulldown", "pullup", "gnd_clamp", "power_clamp"):
        rows = _numeric_rows((tables.get(table_name) or {}).get("rows", []))
        if not rows:
            continue
        value = _interpolate(rows, 0.0, 1)
        if value is not None:
            zero_markers.append((table_name, value))
            y_values.append(value)

    if not y_values:
        return

    y_min, y_max = _padded_range(min(y_values), max(y_values), 0.18)
    sx = lambda value: x + (value - x_min) / (x_max - x_min) * width
    sy = lambda value: y + (y_max - value) / (y_max - y_min) * height

    parts.append(
        f'<rect x="{x}" y="{y}" width="{width}" height="{height}" '
        f'fill="#ffffff" stroke="#9aa4b2" rx="4"/>'
    )
    parts.append(
        f'<text x="{x + 8}" y="{y + 15}" font-family="Arial, sans-serif" '
        f'font-size="10" font-weight="700" fill="#333">0..Vcc clamp / I(0 V) detail</text>'
    )
    plot_y = y + 22
    plot_h = height - 42
    for tick in (0.0, vcc):
        tx = sx(tick)
        parts.append(f'<line x1="{tx:.2f}" y1="{plot_y}" x2="{tx:.2f}" y2="{plot_y + plot_h}" stroke="#ececec"/>')
        parts.append(f'<text x="{tx:.2f}" y="{y + height - 6}" text-anchor="middle" font-family="Arial, sans-serif" font-size="9">{_fmt(tick)}</text>')
    if y_min <= 0.0 <= y_max:
        y0 = sy(0.0)
        parts.append(f'<line x1="{x}" y1="{y0:.2f}" x2="{x + width}" y2="{y0:.2f}" stroke="#777" stroke-dasharray="2 3"/>')

    for table_name, points, dash, width_px, opacity in inset_curves:
        color = colors.get(table_name, "#333333")
        attrs = f' stroke-dasharray="{dash}"' if dash else ""
        data = " ".join(f"{sx(v):.2f},{sy(i):.2f}" for v, i in points)
        parts.append(
            f'<polyline fill="none" stroke="{color}" stroke-width="{width_px}" '
            f'opacity="{opacity}"{attrs} points="{data}"/>'
        )
    for table_name, value in zero_markers:
        color = colors.get(table_name, "#333333")
        parts.append(
            f'<circle cx="{sx(0.0):.2f}" cy="{sy(value):.2f}" r="3" '
            f'fill="#ffffff" stroke="{color}" stroke-width="1.4"/>'
        )

    legend = " / ".join(
        labels.get(table_name, table_name)
        for table_name in ("gnd_clamp", "power_clamp")
        if (tables.get(table_name) or {}).get("rows")
    )
    if legend:
        parts.append(
            f'<text x="{x + 8}" y="{y + height - 20}" font-family="Arial, sans-serif" '
            f'font-size="9" fill="#555">{escape(_shorten(legend, 42))}</text>'
        )


def _points_in_window(
        rows: list[list[float | None]],
        x_min: float,
        x_max: float,
        col: int) -> list[tuple[float, float]]:
    points = []
    for x_value in (x_min, x_max):
        value = _interpolate(rows, x_value, col)
        if value is not None:
            points.append((x_value, value))
    for row in rows:
        if len(row) <= col or row[0] is None or row[col] is None:
            continue
        if x_min <= row[0] <= x_max:
            points.append((row[0], row[col]))
    deduped = {}
    for x_value, y_value in points:
        deduped[x_value] = y_value
    return sorted(deduped.items())


def _plot_findings(model_info: dict, family: str) -> list[dict]:
    prefixes = _FAMILY_PREFIXES.get(family, ())
    if not prefixes:
        return []

    findings = []
    for result in model_info.get("results", []):
        status = result.get("status")
        check_id = result.get("check_id", "")
        if status not in _ATTENTION_STATUSES:
            continue
        if not any(check_id.startswith(prefix) for prefix in prefixes):
            continue
        if family == "iv" and check_id in (_IV_CLAMP_CHECKS | _IV_ZERO_CHECKS | _IV_CLAMP_SWEEP_CHECKS):
            continue
        if family == "iv_clamp" and check_id not in _IV_CLAMP_CHECKS:
            continue
        if family == "iv_zero" and check_id not in _IV_ZERO_CHECKS:
            continue
        if family == "iv_clamp_sweep" and check_id not in _IV_CLAMP_SWEEP_CHECKS:
            continue
        findings.append(result)
    findings.sort(key=lambda result: (
        _severity_rank(result.get("status", "")),
        _check_sort_key(result.get("check_id", "")),
    ))
    return findings


def _append_findings_panel(
        parts,
        findings: list[dict],
        x: float,
        y: float,
        width: float,
        max_lines: int) -> None:
    if not findings:
        return

    shown = findings[:max_lines]
    extra = len(findings) - len(shown)
    row_h = 16
    height = 28 + row_h * (len(shown) + (1 if extra > 0 else 0))
    parts.append(
        f'<rect x="{x}" y="{y}" width="{width}" height="{height}" '
        f'fill="#fffdf7" stroke="#d8c6a1" rx="4"/>'
    )
    parts.append(
        f'<text x="{x + 10}" y="{y + 17}" font-family="Arial, sans-serif" '
        f'font-size="11" font-weight="700" fill="#4b3b21">Findings needing attention</text>'
    )
    for index, result in enumerate(shown):
        yy = y + 34 + index * row_h
        status = result.get("status", "")
        color = _ATTENTION_COLORS.get(status, "#555555")
        check_id = result.get("check_id", "")
        details = result.get("details") or []
        detail = str(details[0]) if details else ""
        message = str(result.get("message", ""))
        if detail:
            message = f"{_shorten(message, 58)} | {_shorten(detail, 54)}"
        else:
            message = _shorten(message, 86)
        parts.append(f'<rect x="{x + 10}" y="{yy - 10}" width="7" height="7" fill="{color}"/>')
        parts.append(
            f'<text x="{x + 24}" y="{yy - 3}" font-family="Arial, sans-serif" '
            f'font-size="11" fill="#333">{escape(status)} {escape(check_id)}: {escape(message)}</text>'
        )
    if extra > 0:
        yy = y + 34 + len(shown) * row_h
        parts.append(
            f'<text x="{x + 24}" y="{yy - 3}" font-family="Arial, sans-serif" '
            f'font-size="11" fill="#555">{extra} more finding(s) in the report table</text>'
        )


def _severity_rank(status: str) -> int:
    return {
        "ERROR": 0,
        "FAIL": 1,
        "WARN": 2,
    }.get(status, 9)


def _check_sort_key(check_id: str) -> tuple[int, ...]:
    try:
        return tuple(int(part) for part in check_id.split("."))
    except ValueError:
        return (999,)


def _shorten(value: str, limit: int) -> str:
    if len(value) <= limit:
        return value
    return value[:max(limit - 3, 0)].rstrip() + "..."


def _polyline(points, sx, sy, color, width, dash: str = "") -> str:
    attrs = f' stroke-dasharray="{dash}"' if dash else ""
    data = " ".join(f"{sx(x):.2f},{sy(y):.2f}" for x, y in points)
    return f'<polyline fill="none" stroke="{color}" stroke-width="{width}"{attrs} points="{data}"/>'


def _numeric_rows(rows: list) -> list[list[float | None]]:
    clean = []
    for row in rows:
        parsed = []
        for value in row:
            try:
                number = None if value is None else float(value)
            except (TypeError, ValueError):
                number = None
            parsed.append(number if number is None or math.isfinite(number) else None)
        if parsed and parsed[0] is not None:
            clean.append(parsed)
    return clean


def _interpolate(rows: list[list[float | None]], x_value: float, col: int) -> float | None:
    points = [
        (row[0], row[col])
        for row in rows
        if len(row) > col and row[0] is not None and row[col] is not None
    ]
    if not points:
        return None
    points.sort(key=lambda item: item[0])
    if x_value < points[0][0] or x_value > points[-1][0]:
        return None
    for x, y in points:
        if x == x_value:
            return y
    for (x1, y1), (x2, y2) in zip(points, points[1:]):
        if x1 <= x_value <= x2 and x2 != x1:
            fraction = (x_value - x1) / (x2 - x1)
            return y1 + fraction * (y2 - y1)
    return None


def _has_table_rows(tables: dict) -> bool:
    return any(table.get("rows") for table in tables.values())


def _padded_range(start: float, stop: float, fraction: float) -> tuple[float, float]:
    if start == stop:
        pad = abs(start) * fraction or 1.0
    else:
        pad = (stop - start) * fraction
    return start - pad, stop + pad


def _empty_svg(width: int, height: int, title: str) -> str:
    return (
        _svg_open(width, height)
        + '<rect width="100%" height="100%" fill="#ffffff"/>'
        + f'<text x="24" y="36" font-family="Arial, sans-serif" font-size="16">{escape(title)}: no plot data</text>'
        + '</svg>'
    )


def _svg_open(width: int, height: int) -> str:
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">'


def _ticks(start: float, stop: float, count: int) -> list[float]:
    if count <= 1:
        return [start]
    step = (stop - start) / (count - 1)
    return [start + i * step for i in range(count)]


def _fmt(value: float) -> str:
    if abs(value) >= 1:
        return f"{value:.2g}"
    return f"{value:.3g}"


def _fmt_number(value: float | None) -> str:
    if value is None:
        return "NA"
    if abs(value) >= 100:
        return f"{value:.0f}"
    if abs(value) >= 10:
        return f"{value:.3g}"
    return f"{value:.4g}"


def _fmt_current(value: float) -> str:
    if abs(value) >= 1:
        return f"{value:.2g}"
    if abs(value) >= 1e-3:
        return f"{value:.3g}"
    return f"{value:.1e}"


def _fmt_current_ma(value: float | None) -> str:
    if value is None:
        return "NA"
    return _fmt(value * 1e3)


def _fmt_time(value: float) -> str:
    if abs(value) >= 1e-6:
        return f"{value:.3g}"
    if abs(value) >= 1e-9:
        return f"{value * 1e9:.3g}n"
    if abs(value) >= 1e-12:
        return f"{value * 1e12:.3g}p"
    return f"{value:.1e}"


def _safe_name(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9_.-]+", "_", value).strip("._")
    return cleaned[:80] or "model"


def _first_number(values) -> float | None:
    if isinstance(values, (list, tuple)) and values and values[0] is not None:
        return float(values[0])
    return None


def _safe_float(value) -> float | None:
    try:
        number = None if value is None else float(value)
    except (TypeError, ValueError):
        return None
    return number if number is not None and math.isfinite(number) else None
