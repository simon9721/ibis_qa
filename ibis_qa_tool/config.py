"""
config.py  —  Numeric thresholds and constants
===============================================
Centralise every "magic number" so checks never contain
hard-coded tolerances. Adjust here for calibration.
"""

# ── 3.1 Package limits (Quality Spec §3.1.2) ─────────────────────────────────
PKG_L_MAX_H   = 100e-9    # 100 nH
PKG_C_MAX_F   = 100e-12   # 100 pF
PKG_R_MAX_OHM = 10.0      # 10 Ω

# ── 3.2 Pin RLC limits (Quality Spec §3.2.2) ─────────────────────────────────
PIN_TD_MAX_S  = 300e-12   # 300 ps  (TD = √(LC))
PIN_Z0_MAX_OHM = 100.0    # 100 Ω   (Z0 = √(L/C))

# ── 3.1.4 Bare-die detection ──────────────────────────────────────────────────
# Components whose [Package] stub values are all ≤ this are treated as bare-die
BARE_DIE_L_MAX_H  = 0.01e-9   # 0.01 nH
BARE_DIE_C_MAX_F  = 0.01e-12  # 0.01 pF
BARE_DIE_R_MAX_OHM = 0.01     # 0.01 Ω

# ── 5.3 I-V table sweep limits ────────────────────────────────────────────────
# Minimum coverage as a fraction of Vcc (allow small endpoint shortfall)
IV_RANGE_TOLERANCE = 0.02      # 2% of Vcc allowed shortfall at endpoints

# ── 5.3.7 Monotonicity tolerance ─────────────────────────────────────────────
MONO_TOLERANCE_A   = 1e-9      # 1 nA — current differences smaller than this
                                # are treated as equal (floating-point noise)

IV_ORDER_ABS_TOL_A = 1e-9      # 1 nA absolute tolerance for near-overlay curves
IV_ORDER_REL_TOL   = 0.01      # 1% relative tolerance for corner ordering

# ── 5.3.8 / 5.3.9 Zero-crossing tolerance ────────────────────────────────────
ZERO_CROSS_TOL_A   = 1e-6      # 1 µA — max |I| at 0V for PASS

# ── 5.3.14 / 5.7.3 Smoothness (Appendix A) ───────────────────────────────────
# Fraction of peak-to-peak current that the interpolation delta may not exceed
SMOOTHNESS_THRESHOLD = 0.02    # 2% — tune empirically
STAIRSTEP_REVIEW_THRESHOLD = 0.10  # semi-auto roughness threshold for visual review
MIN_TABLE_POINTS = 20          # minimum point count evidence threshold
MIN_WAVEFORM_POINTS = 20       # minimum V-T/Composite Current point count
VT_ENDPOINT_TOL_V = 0.02       # 20 mV endpoint-to-fixture evidence tolerance
VT_DURATION_MAX_S = 1e-6       # 1 us evidence threshold for excessive duration
CC_FLAT_SLOPE_TOL_A = 1e-6     # 1 uA edge flatness evidence tolerance
CLAMP_LEAKAGE_TOL_A = 1e-6     # 1 uA clamp leakage evidence tolerance

# ── 5.5.3 Ramp dV vs I-V load-line ──────────────────────────────────────────
RAMP_DV_TOLERANCE   = 0.10     # 10%
RAMP_DV_FRACTION    = 0.60     # use 60% of (Vhigh - Vlow)

# ── 5.7.1 ISSO endpoint tolerance ────────────────────────────────────────────
ISSO_ENDPOINT_TOL   = 0.02     # 2% — Isso_pd(0) vs Ipd(Vcc)

# ── 5.8.2 Composite Current time match ───────────────────────────────────────
TIME_MATCH_TOL_S    = 1e-15    # 1 fs — essentially exact equality

# ── 5.8.8 Composite Current zero endpoint ────────────────────────────────────
CC_ZERO_TOL_A       = 1e-6     # 1 µA

# ── Model types ───────────────────────────────────────────────────────────────
# Types that have [Pulldown] and [Pullup] tables
OUTPUT_TYPES   = {"output", "i/o", "3-state", "open_drain", "open_source",
                  "open_sink", "output_ecl", "i/o_ecl"}
INPUT_TYPES    = {"input", "input_ecl", "terminator"}
IO_TYPES       = {"i/o", "i/o_ecl"}
OPEN_TYPES     = {"open_drain", "open_source", "open_sink"}
ECL_TYPES      = {"output_ecl", "input_ecl", "i/o_ecl"}

# Zero-crossing exceptions: these model types do NOT need to pass through 0
ZERO_CROSS_EXCEPTIONS = {"ttl", "pecl", "lvds", "serdes"}

# Model types that require ISSO PU/PD tables for IQ4
ISSO_REQUIRED_TYPES = OUTPUT_TYPES  # excludes pure input/terminator
