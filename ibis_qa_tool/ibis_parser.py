"""
parser/ibis_parser.py  —  IBIS file tokeniser and object builder
=================================================================
Produces an IBISFile object that all checks operate on.

IBIS format rules (from spec §3):
  - Lines starting with | are comments (ignored for data)
  - Keywords are enclosed in square brackets: [Keyword]
  - Values on the same or following lines, whitespace-delimited
  - Numbers may carry SI suffix: nH, pF, mV, ps, ns, etc.
  - CRLF and LF both accepted
  - Case-insensitive keywords (we normalise to lower)
"""

from __future__ import annotations
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

# ── SI unit parser ────────────────────────────────────────────────────────────
_SI = {
    'f': 1e-15, 'p': 1e-12, 'n': 1e-9, 'u': 1e-6, 'µ': 1e-6,
    'm': 1e-3,  'k': 1e3,   'M': 1e6,  'G': 1e9,
}
_UNIT_RE = re.compile(
    r'^\s*([+-]?\d+\.?\d*(?:[eE][+-]?\d+)?)'  # mantissa
    r'\s*([fpnuµmkMG]?)'                        # SI prefix
    r'(?:H|F|V|A|Ohm|Ω|s|hz|Hz)?\s*$',         # optional unit
    re.IGNORECASE
)

def parse_si(s: str) -> Optional[float]:
    """Parse an IBIS numeric value with optional SI prefix/unit. Returns None on failure."""
    s = s.strip()
    if s.upper() == 'NA':
        return None
    m = _UNIT_RE.match(s)
    if not m:
        # Try bare float (e.g. temperature values like "50.0")
        try:
            return float(s)
        except ValueError:
            return None
    mantissa = float(m.group(1))
    prefix   = m.group(2)
    return mantissa * _SI.get(prefix, 1.0)


def parse_typ_min_max(tokens: list[str]) -> tuple[Optional[float], Optional[float], Optional[float]]:
    """Parse up to 3 whitespace-separated values as (typ, min, max)."""
    vals = [parse_si(t) for t in tokens[:3]]
    while len(vals) < 3:
        vals.append(None)
    return tuple(vals)


# ── Data classes ─────────────────────────────────────────────────────────────

@dataclass
class PackageData:
    r_pkg: tuple = (None, None, None)  # (typ, min, max)
    l_pkg: tuple = (None, None, None)
    c_pkg: tuple = (None, None, None)


@dataclass
class PinEntry:
    pin_name:    str
    signal_name: str
    model_name:  str
    r_pin:  Optional[float] = None
    l_pin:  Optional[float] = None
    c_pin:  Optional[float] = None


@dataclass
class PinMappingEntry:
    pin_name:        str
    pulldown_ref:    Optional[str] = None
    pullup_ref:      Optional[str] = None
    gnd_clamp_ref:   Optional[str] = None
    power_clamp_ref: Optional[str] = None
    ext_ref:         Optional[str] = None


@dataclass
class DiffPinEntry:
    pin_name:    str
    inv_pin:     str
    vdiff:       Optional[float] = None
    tdelay_typ:  Optional[float] = None
    tdelay_min:  Optional[float] = None
    tdelay_max:  Optional[float] = None


@dataclass
class Component:
    name:         str
    manufacturer: str                      = ""
    pkg_model_ref: Optional[str]           = None   # [Package Model] reference name
    package:      PackageData              = field(default_factory=PackageData)
    pins:         list[PinEntry]           = field(default_factory=list)
    pin_mapping:  list[PinMappingEntry]    = field(default_factory=list)
    diff_pins:    list[DiffPinEntry]       = field(default_factory=list)
    # Derived
    is_bare_die:  bool                     = False


@dataclass
class IVTable:
    """One I-V or ISSO table: list of (voltage, typ, min, max) rows."""
    rows: list[tuple] = field(default_factory=list)

    def voltages(self) -> list[float]:
        return [r[0] for r in self.rows]

    def currents_typ(self) -> list[float]:
        return [r[1] for r in self.rows]

    def currents_min(self) -> list[float]:
        return [r[2] for r in self.rows]

    def currents_max(self) -> list[float]:
        return [r[3] for r in self.rows]

    def interpolate(self, v_target: float, col: int = 1) -> Optional[float]:
        """Linear interpolation of column col at v_target. col: 1=typ,2=min,3=max."""
        vs = [r[0] for r in self.rows]
        cs = [r[col] for r in self.rows if r[col] is not None]
        if len(vs) < 2:
            return None
        # find bracket
        for i in range(len(vs) - 1):
            if vs[i] <= v_target <= vs[i + 1]:
                frac = (v_target - vs[i]) / (vs[i + 1] - vs[i])
                return self.rows[i][col] + frac * (self.rows[i + 1][col] - self.rows[i][col])
        # out of range — return nearest endpoint
        if v_target <= vs[0]:
            return self.rows[0][col]
        return self.rows[-1][col]


@dataclass
class VTTable:
    """One V-T (waveform) table."""
    r_fixture: Optional[float] = None
    v_fixture: Optional[float] = None
    rows: list[tuple] = field(default_factory=list)   # (time, typ, min, max)

    def times(self) -> list[float]:
        return [r[0] for r in self.rows]


@dataclass
class CompositeCurrentTable:
    """[Composite Current] table attached to a waveform."""
    rows: list[tuple] = field(default_factory=list)   # (time, typ, min, max)

    def times(self) -> list[float]:
        return [r[0] for r in self.rows]


@dataclass
class Waveform:
    """A [Rising Waveform] or [Falling Waveform] entry."""
    direction:         str                            # 'rising' | 'falling'
    vt:                VTTable                        = field(default_factory=VTTable)
    composite_current: Optional[CompositeCurrentTable] = None


@dataclass
class RampData:
    dv_dt_r: tuple = (None, None, None)  # (typ, min, max) as (dV, dt) pairs? No — store as float dV/dt
    dv_dt_f: tuple = (None, None, None)
    r_load:  Optional[float] = None
    # Raw strings for dV and dt separately (needed for 5.5.3 check)
    dv_r: tuple = (None, None, None)
    dt_r: tuple = (None, None, None)
    dv_f: tuple = (None, None, None)
    dt_f: tuple = (None, None, None)


@dataclass
class ReceiverThresholds:
    vth:                 Optional[float] = None
    vth_min:             Optional[float] = None
    vth_max:             Optional[float] = None
    vinh_ac:             Optional[float] = None
    vinl_ac:             Optional[float] = None
    vinh_dc:             Optional[float] = None
    vinl_dc:             Optional[float] = None
    tslew_ac:            Optional[float] = None
    tdiffslew_ac:        Optional[float] = None
    threshold_sensitivity: Optional[float] = None
    reference_supply:    Optional[str]   = None


@dataclass
class ModelSpec:
    vinl:     tuple = (None, None, None)
    vinh:     tuple = (None, None, None)
    vref:     tuple = (None, None, None)
    vmeas:    tuple = (None, None, None)
    s_overshoot_high: tuple = (None, None, None)
    s_overshoot_low:  tuple = (None, None, None)
    d_overshoot_high: tuple = (None, None, None)
    d_overshoot_low:  tuple = (None, None, None)
    d_overshoot_time: tuple = (None, None, None)


@dataclass
class Model:
    name:           str
    model_type:     str                         = ""
    # Scalar params
    vinl:           Optional[float]             = None
    vinh:           Optional[float]             = None
    vmeas:          Optional[float]             = None
    vref:           Optional[float]             = None
    c_comp:         tuple                       = (None, None, None)
    c_comp_pullup:  tuple                       = (None, None, None)
    c_comp_pulldown: tuple                      = (None, None, None)
    c_comp_power_clamp: tuple                   = (None, None, None)
    c_comp_gnd_clamp:   tuple                   = (None, None, None)
    voltage_range:  tuple                       = (None, None, None)
    temp_range:     tuple                       = (None, None, None)
    pullup_ref:     tuple                       = (None, None, None)
    pulldown_ref:   tuple                       = (None, None, None)
    power_clamp_ref: tuple                      = (None, None, None)
    gnd_clamp_ref:  tuple                       = (None, None, None)
    # Tables
    pulldown:       Optional[IVTable]           = None
    pullup:         Optional[IVTable]           = None
    gnd_clamp:      Optional[IVTable]           = None
    power_clamp:    Optional[IVTable]           = None
    isso_pd:        Optional[IVTable]           = None
    isso_pu:        Optional[IVTable]           = None
    ramp:           Optional[RampData]          = None
    waveforms:      list[Waveform]              = field(default_factory=list)
    model_spec:     Optional[ModelSpec]         = None
    receiver_thresholds: Optional[ReceiverThresholds] = None
    add_submodels:  list[str]                   = field(default_factory=list)
    # Derived helpers
    model_type_lower: str                       = ""

    def __post_init__(self):
        self.model_type_lower = self.model_type.lower().replace(" ", "_")

    def resolve_vcc(self) -> Optional[float]:
        """Return typical Vcc: prefer [Pullup Reference] typ, fall back to [Voltage Range] typ."""
        if self.pullup_ref[0] is not None:
            return self.pullup_ref[0]
        if self.voltage_range[0] is not None:
            return self.voltage_range[0]
        return None

    def resolve_power_clamp_vcc(self) -> Optional[float]:
        """Vcc for POWER/GND Clamp sweep checks."""
        if self.power_clamp_ref[0] is not None:
            return self.power_clamp_ref[0]
        return self.resolve_vcc()


@dataclass
class DefinePackageModel:
    name:         str
    description:  str                           = ""
    num_pins:     int                           = 0
    # pin_numbers: list of (model_node, physical_pin_label)
    pin_numbers:  list[tuple[str, str]]         = field(default_factory=list)
    has_merged_pins: bool                       = False


@dataclass
class IBISFile:
    path:           Path
    ibis_ver:       str                         = ""
    file_name:      str                         = ""
    date:           str                         = ""
    file_rev:       str                         = ""
    source:         str                         = ""
    notes:          str                         = ""
    iq_score_in_file: Optional[str]             = None   # parsed from |IQ Score: tag
    ibischk_ver_in_file: Optional[str]         = None
    components:     list[Component]             = field(default_factory=list)
    models:         dict[str, Model]            = field(default_factory=dict)
    pkg_models:     dict[str, DefinePackageModel] = field(default_factory=dict)
    raw_lines:      list[str]                   = field(default_factory=list)


# ── Parser ────────────────────────────────────────────────────────────────────

class IBISParser:
    """
    Single-pass line-by-line IBIS parser.

    State machine: we track the current keyword context and dispatch
    each non-comment line to the appropriate handler.
    """

    def parse(self, path: Path) -> IBISFile:
        with open(path, encoding="utf-8", errors="replace") as f:
            raw = f.read()

        lines = raw.replace('\r\n', '\n').replace('\r', '\n').split('\n')
        ibis = IBISFile(path=path, raw_lines=lines)

        self._ibis  = ibis
        self._lines = lines
        self._i     = 0               # current line index
        self._cur_component: Optional[Component] = None
        self._cur_model:     Optional[Model]     = None
        self._cur_pkg_model: Optional[DefinePackageModel] = None
        self._context = "header"      # tracks what section we're in

        while self._i < len(lines):
            line = lines[self._i]
            stripped = line.strip()

            # Skip pure comment lines and blank lines for keyword detection
            if stripped.startswith('|') or not stripped:
                # But scan comments for IQ Score / IBISCHK version
                self._scan_comment(stripped)
                self._i += 1
                continue

            # Keyword line?
            kw_match = re.match(r'^\[([^\]]+)\]', stripped)
            if kw_match:
                kw = kw_match.group(1).strip().lower().replace(' ', '_')
                rest = stripped[kw_match.end():].strip()
                self._dispatch_keyword(kw, rest)
            else:
                # Data line — dispatch to current context handler
                self._dispatch_data(stripped)

            self._i += 1

        # Post-process: detect bare-die components
        for comp in ibis.components:
            self._detect_bare_die(comp)

        # Post-process: detect merged pins in package models
        for pkgm in ibis.pkg_models.values():
            from collections import Counter
            node_counts = Counter(node for node, _ in pkgm.pin_numbers)
            pkgm.has_merged_pins = any(v > 1 for v in node_counts.values())

        return ibis

    # ── Comment scanning ──────────────────────────────────────────────────────

    def _scan_comment(self, line: str):
        """Pick up |IQ Score: and IBISCHK version from comment lines."""
        lo = line.lower()
        if 'iq score' in lo or 'iq3' in lo or 'iq4' in lo or 'iq2' in lo:
            m = re.search(r'(IQ\d+[GSMX]*)', line, re.IGNORECASE)
            if m:
                self._ibis.iq_score_in_file = m.group(1)
        if 'ibischk' in lo:
            m = re.search(r'ibischk\s+v?(\d[\d.]+)', line, re.IGNORECASE)
            if m:
                self._ibis.ibischk_ver_in_file = m.group(1)

    # ── Keyword dispatcher ────────────────────────────────────────────────────

    def _dispatch_keyword(self, kw: str, rest: str):
        handlers = {
            'ibis_ver':               self._kw_ibis_ver,
            'file_name':              self._kw_file_name,
            'date':                   self._kw_date,
            'file_rev':               self._kw_file_rev,
            'source':                 self._kw_source,
            'notes':                  self._kw_notes,
            'component':              self._kw_component,
            'package_model':          self._kw_package_model_ref,
            'manufacturer':           self._kw_manufacturer,
            'package':                self._kw_package,
            'pin':                    self._kw_pin,
            'pin_mapping':            self._kw_pin_mapping,
            'diff_pin':               self._kw_diff_pin,
            'model_selector':         self._kw_model_selector,
            'model':                  self._kw_model,
            'model_spec':             self._kw_model_spec,
            'voltage_range':          self._kw_voltage_range,
            'temperature_range':      self._kw_temperature_range,
            'pullup_reference':       lambda r: self._kw_ref('pullup_ref', r),
            'pulldown_reference':     lambda r: self._kw_ref('pulldown_ref', r),
            'power_clamp_reference':  lambda r: self._kw_ref('power_clamp_ref', r),
            'gnd_clamp_reference':    lambda r: self._kw_ref('gnd_clamp_ref', r),
            'pulldown':               lambda r: self._kw_iv_table('pulldown'),
            'pullup':                 lambda r: self._kw_iv_table('pullup'),
            'gnd_clamp':              lambda r: self._kw_iv_table('gnd_clamp'),
            'power_clamp':            lambda r: self._kw_iv_table('power_clamp'),
            'isso_pd':                lambda r: self._kw_iv_table('isso_pd'),
            'isso_pu':                lambda r: self._kw_iv_table('isso_pu'),
            'ramp':                   self._kw_ramp,
            'rising_waveform':        lambda r: self._kw_waveform('rising'),
            'falling_waveform':       lambda r: self._kw_waveform('falling'),
            'composite_current':      self._kw_composite_current,
            'receiver_thresholds':    self._kw_receiver_thresholds,
            'add_submodel':           self._kw_add_submodel,
            'define_package_model':   self._kw_define_package_model,
            'pin_numbers':            self._kw_pin_numbers,
            'merged_pins':            self._kw_merged_pins,
            'end':                    self._kw_end,
        }
        handler = handlers.get(kw)
        if handler:
            handler(rest)
        else:
            # Unknown keyword — just update context so data lines are ignored
            self._context = f"unknown:{kw}"

    # ── Header keywords ───────────────────────────────────────────────────────

    def _kw_ibis_ver(self, rest):
        self._ibis.ibis_ver = rest.split()[0] if rest.split() else ""
        self._context = "header"

    def _kw_file_name(self, rest): self._ibis.file_name = rest; self._context = "header"
    def _kw_date(self, rest):      self._ibis.date = rest;      self._context = "header"
    def _kw_file_rev(self, rest):  self._ibis.file_rev = rest;  self._context = "header"
    def _kw_source(self, rest):    self._ibis.source = rest;    self._context = "source"
    def _kw_notes(self, rest):     self._context = "notes"
    def _kw_end(self, rest):       self._context = "eof"

    # ── Component ─────────────────────────────────────────────────────────────

    def _kw_component(self, rest):
        comp = Component(name=rest.split()[0] if rest.split() else "")
        self._ibis.components.append(comp)
        self._cur_component = comp
        self._cur_model = None
        self._context = "component"

    def _kw_package_model_ref(self, rest):
        if self._cur_component:
            self._cur_component.pkg_model_ref = rest.split()[0] if rest.split() else None

    def _kw_manufacturer(self, rest):
        if self._cur_component:
            self._cur_component.manufacturer = rest

    def _kw_package(self, rest):
        self._context = "package"

    def _kw_pin(self, rest):
        # [Pin] header line — just set context; data lines will parse entries
        self._context = "pin"

    def _kw_pin_mapping(self, rest):
        # [Pin Mapping] header line
        self._context = "pin_mapping"

    def _kw_diff_pin(self, rest):
        self._context = "diff_pin"

    def _kw_model_selector(self, rest):
        self._context = "model_selector"

    # ── Model ─────────────────────────────────────────────────────────────────

    def _kw_model(self, rest):
        name = rest.split()[0] if rest.split() else ""
        model = Model(name=name)
        self._ibis.models[name] = model
        self._cur_model = model
        self._context = "model"

    def _kw_model_spec(self, rest):
        if self._cur_model:
            if self._cur_model.model_spec is None:
                self._cur_model.model_spec = ModelSpec()
        self._context = "model_spec"

    def _kw_voltage_range(self, rest):
        if self._cur_model:
            toks = rest.split()
            self._cur_model.voltage_range = parse_typ_min_max(toks)
        self._context = "model"

    def _kw_temperature_range(self, rest):
        if self._cur_model:
            toks = rest.split()
            self._cur_model.temp_range = parse_typ_min_max(toks)
        self._context = "model"

    def _kw_ref(self, attr: str, rest: str):
        if self._cur_model:
            toks = rest.split()
            setattr(self._cur_model, attr, parse_typ_min_max(toks))
        self._context = "model"

    # ── I-V tables ────────────────────────────────────────────────────────────

    def _kw_iv_table(self, attr: str):
        if self._cur_model:
            table = IVTable()
            setattr(self._cur_model, attr, table)
            self._context = f"iv:{attr}"

    # ── Ramp ──────────────────────────────────────────────────────────────────

    def _kw_ramp(self, rest):
        if self._cur_model:
            self._cur_model.ramp = RampData()
        self._context = "ramp"

    # ── Waveforms ─────────────────────────────────────────────────────────────

    def _kw_waveform(self, direction: str):
        if self._cur_model is not None:
            wf = Waveform(direction=direction, vt=VTTable())
            self._cur_model.waveforms.append(wf)
            self._context = f"waveform:{direction}"

    def _kw_composite_current(self, rest):
        if self._cur_model and self._cur_model.waveforms:
            cc = CompositeCurrentTable()
            self._cur_model.waveforms[-1].composite_current = cc
            self._context = "composite_current"

    # ── Receiver Thresholds ───────────────────────────────────────────────────

    def _kw_receiver_thresholds(self, rest):
        if self._cur_model:
            self._cur_model.receiver_thresholds = ReceiverThresholds()
        self._context = "receiver_thresholds"

    # ── Add Submodel ──────────────────────────────────────────────────────────

    def _kw_add_submodel(self, rest):
        if self._cur_model:
            name = rest.split()[0] if rest.split() else ""
            if name:
                self._cur_model.add_submodels.append(name)
        self._context = "model"

    # ── Define Package Model ──────────────────────────────────────────────────

    def _kw_define_package_model(self, rest):
        name = rest.split()[0] if rest.split() else ""
        pkgm = DefinePackageModel(name=name)
        self._ibis.pkg_models[name] = pkgm
        self._cur_pkg_model = pkgm
        self._context = "define_pkg_model"

    def _kw_pin_numbers(self, rest):
        self._context = "pin_numbers"

    def _kw_merged_pins(self, rest):
        if self._cur_pkg_model:
            self._cur_pkg_model.has_merged_pins = True
        self._context = "define_pkg_model"

    # ── Data line dispatcher ──────────────────────────────────────────────────

    def _dispatch_data(self, line: str):
        ctx = self._context
        if ctx == "package":
            self._data_package(line)
        elif ctx == "pin":
            self._data_pin(line)
        elif ctx == "pin_mapping":
            self._data_pin_mapping(line)
        elif ctx == "diff_pin":
            self._data_diff_pin(line)
        elif ctx == "model":
            self._data_model_params(line)
        elif ctx == "model_spec":
            self._data_model_spec(line)
        elif ctx.startswith("iv:"):
            self._data_iv_row(line, ctx[3:])
        elif ctx == "ramp":
            self._data_ramp(line)
        elif ctx.startswith("waveform:"):
            self._data_waveform_row(line)
        elif ctx == "composite_current":
            self._data_cc_row(line)
        elif ctx == "receiver_thresholds":
            self._data_receiver_thresholds(line)
        elif ctx == "pin_numbers":
            self._data_pin_numbers(line)
        elif ctx == "define_pkg_model":
            self._data_define_pkg_model(line)
        # other contexts: header, notes, source, eof, unknown — ignore data

    # ── Package data ──────────────────────────────────────────────────────────

    def _data_package(self, line: str):
        if not self._cur_component:
            return
        toks = line.split()
        if not toks:
            return
        key = toks[0].lower()
        vals = parse_typ_min_max(toks[1:])
        pkg = self._cur_component.package
        if key == 'r_pkg':
            pkg.r_pkg = vals
        elif key == 'l_pkg':
            pkg.l_pkg = vals
        elif key == 'c_pkg':
            pkg.c_pkg = vals

    # ── Pin data ──────────────────────────────────────────────────────────────

    def _data_pin(self, line: str):
        if not self._cur_component:
            return
        toks = line.split('|')[0].split()  # strip inline comments
        if len(toks) < 3:
            return
        # Skip header lines (first token is 'pin_name' or similar non-pin)
        if toks[0].lower() in ('pin', 'signal_name', 'model_name', 'r_pin'):
            return
        entry = PinEntry(
            pin_name=toks[0],
            signal_name=toks[1],
            model_name=toks[2],
            r_pin=parse_si(toks[3]) if len(toks) > 3 else None,
            l_pin=parse_si(toks[4]) if len(toks) > 4 else None,
            c_pin=parse_si(toks[5]) if len(toks) > 5 else None,
        )
        self._cur_component.pins.append(entry)

    # ── Pin mapping data ──────────────────────────────────────────────────────

    def _data_pin_mapping(self, line: str):
        if not self._cur_component:
            return
        toks = line.split('|')[0].split()
        if len(toks) < 2:
            return
        if toks[0].lower() in ('pin_mapping', 'pulldown_ref'):
            return  # header line
        def nc(s): return None if s.upper() == 'NC' else s
        entry = PinMappingEntry(
            pin_name=toks[0],
            pulldown_ref=nc(toks[1]) if len(toks) > 1 else None,
            pullup_ref=nc(toks[2])   if len(toks) > 2 else None,
            gnd_clamp_ref=nc(toks[3]) if len(toks) > 3 else None,
            power_clamp_ref=nc(toks[4]) if len(toks) > 4 else None,
            ext_ref=nc(toks[5])      if len(toks) > 5 else None,
        )
        self._cur_component.pin_mapping.append(entry)

    # ── Diff Pin data ─────────────────────────────────────────────────────────

    def _data_diff_pin(self, line: str):
        if not self._cur_component:
            return
        toks = line.split('|')[0].split()
        if len(toks) < 2:
            return
        if toks[0].lower() in ('diff_pin', 'inv_pin', 'vdiff'):
            return
        entry = DiffPinEntry(
            pin_name=toks[0],
            inv_pin=toks[1],
            vdiff=parse_si(toks[2])     if len(toks) > 2 else None,
            tdelay_typ=parse_si(toks[3]) if len(toks) > 3 else None,
            tdelay_min=parse_si(toks[4]) if len(toks) > 4 else None,
            tdelay_max=parse_si(toks[5]) if len(toks) > 5 else None,
        )
        self._cur_component.diff_pins.append(entry)

    # ── Model scalar params ───────────────────────────────────────────────────

    def _data_model_params(self, line: str):
        m = self._cur_model
        if not m:
            return
        toks = line.split('|')[0].split()
        if not toks:
            return
        key = toks[0].lower()
        rest_toks = toks[1:]

        scalar_map = {
            'model_type': lambda: setattr(m, 'model_type', ' '.join(rest_toks)) or setattr(m, 'model_type_lower', m.model_type.lower()),
            'vinl': lambda: setattr(m, 'vinl', parse_si(rest_toks[0]) if rest_toks else None),
            'vinh': lambda: setattr(m, 'vinh', parse_si(rest_toks[0]) if rest_toks else None),
            'vmeas': lambda: setattr(m, 'vmeas', parse_si(rest_toks[0]) if rest_toks else None),
            'vref': lambda: setattr(m, 'vref', parse_si(rest_toks[0]) if rest_toks else None),
        }
        tmm_map = {
            'c_comp':               'c_comp',
            'c_comp_pullup':        'c_comp_pullup',
            'c_comp_pulldown':      'c_comp_pulldown',
            'c_comp_power_clamp':   'c_comp_power_clamp',
            'c_comp_gnd_clamp':     'c_comp_gnd_clamp',
        }

        if key in scalar_map:
            scalar_map[key]()
        elif key in tmm_map:
            setattr(m, tmm_map[key], parse_typ_min_max(rest_toks))

    # ── Model Spec data ───────────────────────────────────────────────────────

    def _data_model_spec(self, line: str):
        if not self._cur_model or not self._cur_model.model_spec:
            return
        toks = line.split('|')[0].split()
        if not toks:
            return
        ms = self._cur_model.model_spec
        key = toks[0].lower()
        tmm = parse_typ_min_max(toks[1:])
        attr_map = {
            'vinl': 'vinl', 'vinh': 'vinh',
            'vref': 'vref', 'vmeas': 'vmeas',
            's_overshoot_high': 's_overshoot_high',
            's_overshoot_low':  's_overshoot_low',
            'd_overshoot_high': 'd_overshoot_high',
            'd_overshoot_low':  'd_overshoot_low',
            'd_overshoot_time': 'd_overshoot_time',
        }
        if key in attr_map:
            setattr(ms, attr_map[key], tmm)

    # ── I-V table rows ────────────────────────────────────────────────────────

    def _data_iv_row(self, line: str, attr: str):
        toks = line.split('|')[0].split()
        if len(toks) < 2:
            return
        try:
            row = tuple(parse_si(t) for t in toks[:4])
            if row[0] is None:
                return
            table = getattr(self._cur_model, attr, None)
            if table:
                table.rows.append(row)
        except Exception:
            pass

    # ── Ramp data ─────────────────────────────────────────────────────────────

    _RAMP_RE = re.compile(
        r'(dv/dt_[rf])\s+'
        r'([+-]?\d+\.?\d*(?:[eE][+-]?\d+)?[a-zA-Z]*)'
        r'\s*/\s*'
        r'([+-]?\d+\.?\d*(?:[eE][+-]?\d+)?[a-zA-Z]*)'
        r'(?:\s+'
        r'([+-]?\d+\.?\d*(?:[eE][+-]?\d+)?[a-zA-Z]*)'
        r'\s*/\s*'
        r'([+-]?\d+\.?\d*(?:[eE][+-]?\d+)?[a-zA-Z]*)'
        r')?'
        r'(?:\s+'
        r'([+-]?\d+\.?\d*(?:[eE][+-]?\d+)?[a-zA-Z]*)'
        r'\s*/\s*'
        r'([+-]?\d+\.?\d*(?:[eE][+-]?\d+)?[a-zA-Z]*)'
        r')?',
        re.IGNORECASE
    )

    def _data_ramp(self, line: str):
        if not self._cur_model or not self._cur_model.ramp:
            return
        ramp = self._cur_model.ramp
        toks = line.split('|')[0].strip()
        key = toks.split()[0].lower() if toks.split() else ''

        if key in ('dv/dt_r', 'dv/dt_f'):
            # Format: dV/dt_r  dV_typ/dt_typ  dV_min/dt_min  dV_max/dt_max
            # Split on whitespace first, then each token is dV/dt pair
            parts = toks.split()[1:]  # skip the key
            dv_vals, dt_vals = [], []
            for part in parts[:3]:
                if '/' in part:
                    a, b = part.split('/', 1)
                    dv_vals.append(parse_si(a))
                    dt_vals.append(parse_si(b))
                else:
                    dv_vals.append(parse_si(part))
                    dt_vals.append(None)
            while len(dv_vals) < 3: dv_vals.append(None)
            while len(dt_vals) < 3: dt_vals.append(None)
            if key == 'dv/dt_r':
                ramp.dv_r = tuple(dv_vals)
                ramp.dt_r = tuple(dt_vals)
                # compute dV/dt float for each corner
                ramp.dv_dt_r = tuple(
                    dv/dt if (dv is not None and dt and dt != 0) else None
                    for dv, dt in zip(dv_vals, dt_vals)
                )
            else:
                ramp.dv_f = tuple(dv_vals)
                ramp.dt_f = tuple(dt_vals)
                ramp.dv_dt_f = tuple(
                    dv/dt if (dv is not None and dt and dt != 0) else None
                    for dv, dt in zip(dv_vals, dt_vals)
                )
        elif key == 'r_load':
            parts = toks.split()
            if len(parts) >= 2:
                ramp.r_load = parse_si(parts[1])

    # ── Waveform data rows ────────────────────────────────────────────────────

    def _data_waveform_row(self, line: str):
        if not self._cur_model or not self._cur_model.waveforms:
            return
        toks = line.split('|')[0].split()
        if not toks:
            return
        wf = self._cur_model.waveforms[-1]
        vt = wf.vt
        key = toks[0].lower()
        if key == 'r_fixture':
            vt.r_fixture = parse_si(toks[-1]) if '=' in line else parse_si(toks[1])
        elif key == 'v_fixture':
            vt.v_fixture = parse_si(toks[-1]) if '=' in line else parse_si(toks[1])
        else:
            # Numeric row
            try:
                row = tuple(parse_si(t) for t in toks[:4])
                if row[0] is not None:
                    vt.rows.append(row)
            except Exception:
                pass

    # ── Composite Current rows ────────────────────────────────────────────────

    def _data_cc_row(self, line: str):
        if not self._cur_model or not self._cur_model.waveforms:
            return
        toks = line.split('|')[0].split()
        if not toks:
            return
        wf = self._cur_model.waveforms[-1]
        if wf.composite_current is None:
            return
        try:
            row = tuple(parse_si(t) for t in toks[:4])
            if row[0] is not None:
                wf.composite_current.rows.append(row)
        except Exception:
            pass

    # ── Receiver Thresholds data ──────────────────────────────────────────────

    def _data_receiver_thresholds(self, line: str):
        if not self._cur_model or not self._cur_model.receiver_thresholds:
            return
        toks = line.split('|')[0].split()
        if not toks:
            return
        rt = self._cur_model.receiver_thresholds
        key = toks[0].lower()
        val = parse_si(toks[1]) if len(toks) > 1 else None
        attr_map = {
            'vth': 'vth', 'vth_min': 'vth_min', 'vth_max': 'vth_max',
            'vinh_ac': 'vinh_ac', 'vinl_ac': 'vinl_ac',
            'vinh_dc': 'vinh_dc', 'vinl_dc': 'vinl_dc',
            'tslew_ac': 'tslew_ac', 'tdiffslew_ac': 'tdiffslew_ac',
            'threshold_sensitivity': 'threshold_sensitivity',
        }
        if key in attr_map:
            setattr(rt, attr_map[key], val)
        elif key == 'reference_supply':
            rt.reference_supply = toks[1] if len(toks) > 1 else None

    # ── Package model data ────────────────────────────────────────────────────

    def _data_define_pkg_model(self, line: str):
        if not self._cur_pkg_model:
            return
        toks = line.split('|')[0].split()
        if not toks:
            return
        key = toks[0].lower()
        if key == '[manufacturer]':
            pass
        elif key == 'description' or key == '[description]':
            self._cur_pkg_model.description = ' '.join(toks[1:])
        elif key == '[number_of_pins]' or key == 'number_of_pins':
            try:
                self._cur_pkg_model.num_pins = int(toks[1])
            except (IndexError, ValueError):
                pass

    def _data_pin_numbers(self, line: str):
        if not self._cur_pkg_model:
            return
        # Format:  model_node  |  physical_pin_name
        # or sometimes:  model_node   physical_pin_name  (no pipe)
        parts = line.split('|')
        if len(parts) >= 2:
            node = parts[0].strip().split()[0] if parts[0].strip() else None
            phys = parts[1].strip().split()[0] if parts[1].strip() else None
        else:
            toks = line.split()
            node = toks[0] if toks else None
            phys = toks[1] if len(toks) > 1 else None
        if node and phys and not node.startswith('['):
            self._cur_pkg_model.pin_numbers.append((node, phys))

    # ── Bare die detection ────────────────────────────────────────────────────

    def _detect_bare_die(self, comp: Component):
        """Mark bare-die components by detecting stub package values."""
        from config import BARE_DIE_L_MAX_H, BARE_DIE_C_MAX_F, BARE_DIE_R_MAX_OHM
        pkg = comp.package
        checks = []
        if pkg.l_pkg[0] is not None:
            checks.append(pkg.l_pkg[0] <= BARE_DIE_L_MAX_H)
        if pkg.c_pkg[0] is not None:
            checks.append(pkg.c_pkg[0] <= BARE_DIE_C_MAX_F)
        if pkg.r_pkg[0] is not None:
            checks.append(pkg.r_pkg[0] <= BARE_DIE_R_MAX_OHM)
        # Also check name heuristic
        name_hint = any(x in comp.name.lower() for x in ('bare', 'die', 'z41c'))
        comp.is_bare_die = (len(checks) > 0 and all(checks)) or (name_hint and len(checks) > 0 and all(checks))
