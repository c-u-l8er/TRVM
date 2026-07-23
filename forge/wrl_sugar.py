"""wrl_sugar.py v0.1 -- Phase 3B-4: named rotor constants + concise clocks.

GPT-5.6's 3B priority ruling: after the formatter (3B-2) and stable diagnostics
(3B-3), 3B-4 adds surface SUGAR that canonicalizes to the frozen numeric values:

    concise clocks   `(every 2)`            -> `(mode=periodic, period=2, phase=0)`
                     `(every 2, phase 1)`   -> `(mode=periodic, period=2, phase=1)`
                     `(once at 5)`          -> `(mode=once, epoch=5)`
    named rotors     `rotor=identity`       -> `rotor=<2^n>.0.0.0`   (per spinner n)
                     `rotor=reverse_x`      -> `rotor=0.<2^n>.0.0`
                     `rotor=reverse_y`      -> `rotor=0.0.<2^n>.0`
                     `rotor=reverse_z`      -> `rotor=0.0.0.<2^n>`

Sugar is a source-to-source PRE-PASS: `desugar_core(src)` rewrites the sugar to
the canonical WRL Core surface, then the UNTOUCHED `wrl_ir.parse_wrl_core` builds
the graph. So sugar can NEVER introduce a new identity -- a sugared program and
its numeric twin lower to identical bytes (proven in binding_run11). The
canonical FORMAT (3B-2) still emits the numeric surface, so the sugar simply
washes out, exactly like declaration order or whitespace.

FROZEN NAMED-ROTOR TABLE v1 is deliberately EXACT-ONLY: identity and the three
axis 180-degree reversals are representable with zero rounding at ANY fractional
width n (their quaternion components are 0 or 1).

POLICY-GOVERNED NAMED ROTORS (Phase 3B.5.1 follow-on, GPT-5.6 ruling): an
irrational-valued name like `quarter_turn_z` (a 90-degree turn about z =
sqrt(2)/2 per component) is NOT exact, so its integer projection at the spinner's
fractional width n is pinned by a NAMED policy -- `forge_named_rotor_rne_sym_v1`
(Round-to-Nearest, SYMmetric). The projection is the geometry-dependent symmetric
integer quaternion

    quarter_turn_z(n) = (round(2^n / sqrt(2)), 0, 0, round(2^n / sqrt(2)))

with NO residual redistribution (the two equal lanes are each rounded to nearest
INDEPENDENTLY; the norm is NOT renormalized back to 2^2n). `round(2^n/sqrt(2))` is
computed by EXACT INTEGER arithmetic (no float): with U = 2^n,

    q0 = isqrt(2*U*U) // 2                       # = floor(U / sqrt(2))
    q  = q0 + 1  if  2*U*U > 4*q0*q0 + 4*q0 + 1  # nearest-integer tie test
         else q0

so q4=(11,0,0,11), q8=(181,0,0,181), q16=(46341,0,0,46341). The canonical sign is
scalar>0 (lane 0 positive). Because the value depends on n, the SemanticArtifactID
is GEOMETRY-DEPENDENT: the SAME `rotor=quarter_turn_z` at a different spinner n
lowers to a DIFFERENT numeric rotor and hence a different id -- exactly as ruled.
The policy id is recorded as build provenance (`named_rotor_policy(name)`,
`NAMED_ROTOR_RNE_SYM_POLICY`); it does NOT enter the artifact bytes (sugar still
washes out -- `rotor=quarter_turn_z`@n8 and its numeric twin `rotor=181.0.0.181`
seal to identical bytes, preserving the pre-pass discipline).

An unknown name, or a policy-governed name with no `n` on its declaration, is
still a typed `WRL_UNSUPPORTED_FEATURE` rejection, never a silent guess.
"""
import math
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import wrl_ir as W
import wrl_canonical as WC

SUGAR_VERSION = "sugar.v1"

# ------------------------------------------------------ authoritative registries
# (Phase 3B.5.1) The named-rotor table and the concise-clock forms are now
# SINGLE-SOURCED here as authoritative surface registries. Every layer consumes
# them: `named_rotor` resolves lanes from NAMED_ROTOR_TABLE, `_desugar_clock`
# rewrites the CLOCK_SUGAR_FORMS, and wrl_complete offers exactly these names and
# form templates -- no layer re-declares the vocabulary, so completion cannot
# drift from what the desugarer accepts.
#
# NAMED_ROTOR_TABLE maps each frozen EXACT name to a pure function of the
# spinner's fractional width n -> its length-4 integer lane tuple. The four
# entries (identity + the three axis 180-degree reversals) are exact at ANY n
# because their quaternion components are 0 or 1 (unit = 1 << n).
NAMED_ROTOR_TABLE = {
    "identity":  lambda n: (1 << n, 0, 0, 0),
    "reverse_x": lambda n: (0, 1 << n, 0, 0),
    "reverse_y": lambda n: (0, 0, 1 << n, 0),
    "reverse_z": lambda n: (0, 0, 0, 1 << n),
}
# the frozen EXACT named-rotor table v1 NAMES, DERIVED from the table so the two
# can never diverge (kept as a tuple for the stable tooling projection).
ROTOR_TABLE_NAMES = tuple(NAMED_ROTOR_TABLE)

# ------------------------------------------------ policy-governed named rotors
# The named POLICY for the geometry-dependent symmetric integer projection of an
# irrational-valued rotor. Recorded as build PROVENANCE (never enters the artifact
# bytes -- the projected numeric rotor does, exactly like the exact table).
NAMED_ROTOR_RNE_SYM_POLICY = "forge_named_rotor_rne_sym_v1"


def _round_u_over_sqrt2(n):
    """round(2^n / sqrt(2)) by EXACT integer arithmetic (no float). With U=2^n:
    q0 = floor(U/sqrt(2)) = isqrt(2*U*U)//2; round up iff 2*U*U > 4*q0^2+4*q0+1
    (the squared form of U/sqrt(2) > q0 + 1/2)."""
    u = 1 << n
    two_uu = 2 * u * u
    q0 = math.isqrt(two_uu) // 2
    return q0 + 1 if two_uu > 4 * q0 * q0 + 4 * q0 + 1 else q0


def _quarter_turn_z(n):
    """The `forge_named_rotor_rne_sym_v1` projection of a 90-degree turn about z:
    (q,0,0,q) with q=round(2^n/sqrt(2)), each lane rounded INDEPENDENTLY to
    nearest, NO residual redistribution, canonical sign scalar>0."""
    q = _round_u_over_sqrt2(n)
    return (q, 0, 0, q)


# NAMED_ROTOR_POLICY_TABLE maps each policy-governed (non-exact) name to
# (policy_id, projection(n)). Kept SEPARATE from the exact table so the exact
# table's zero-rounding invariant (and binding_run11 N3) stays intact.
NAMED_ROTOR_POLICY_TABLE = {
    "quarter_turn_z": (NAMED_ROTOR_RNE_SYM_POLICY, _quarter_turn_z),
}
POLICY_ROTOR_NAMES = tuple(NAMED_ROTOR_POLICY_TABLE)

# the FULL accepted named-rotor vocabulary (exact + policy-governed), the single
# source of truth for tooling/completion so a name the desugarer accepts is
# always offered and vice versa.
ALL_ROTOR_NAMES = ROTOR_TABLE_NAMES + POLICY_ROTOR_NAMES

# the frozen concise-clock surface FORM templates (K/P/E are metavariables).
CLOCK_SUGAR_FORMS = ("every K", "every K, phase P", "once at E")

# a named rotor NAME must be an identifier (never digits/dots -- so a numeric
# rotor like `16.0.0.0` is left untouched by the pre-pass).
_ROTOR_NAME_RE = re.compile(r"rotor=([A-Za-z_]\w*)")
_N_RE = re.compile(r"\bn=(\d+)")
_PAREN_RE = re.compile(r"\(([^)]*)\)")


def named_rotor(name, n):
    """The accepted named rotor `name`, projected to the spinner's own Q-format
    (n fractional bits, `unit = 1 << n`). Resolves the frozen EXACT table first
    (exact at any n), then the POLICY-governed table (e.g. `quarter_turn_z` under
    `forge_named_rotor_rne_sym_v1`). An unknown name is a typed rejection, never a
    silent guess."""
    if name in NAMED_ROTOR_TABLE:
        return NAMED_ROTOR_TABLE[name](n)
    if name in NAMED_ROTOR_POLICY_TABLE:
        return NAMED_ROTOR_POLICY_TABLE[name][1](n)
    WC._fail(
        WC.WRL_UNSUPPORTED_FEATURE,
        "named rotor %r not in the accepted vocabulary %s (exact table %s + "
        "policy-governed %s)" % (name, sorted(ALL_ROTOR_NAMES),
                                 sorted(NAMED_ROTOR_TABLE),
                                 sorted(NAMED_ROTOR_POLICY_TABLE)))


def named_rotor_policy(name):
    """The build-provenance policy id that governs a named rotor's projection:
    an EXACT-table name is exact (returns None); a policy-governed name returns
    its policy id (e.g. `quarter_turn_z` -> `forge_named_rotor_rne_sym_v1`); an
    unknown name is a typed rejection."""
    if name in NAMED_ROTOR_TABLE:
        return None
    if name in NAMED_ROTOR_POLICY_TABLE:
        return NAMED_ROTOR_POLICY_TABLE[name][0]
    WC._fail(WC.WRL_UNSUPPORTED_FEATURE,
             "named rotor %r not in the accepted vocabulary" % (name,))


def _desugar_clock(body):
    """`every K` / `every K, phase P` / `once at E` -> a canonical pulser kv
    group body, or None if `body` is already the verbose (mode=...) form."""
    if "mode=" in body or "period=" in body or "epoch=" in body:
        return None
    toks = body.replace(",", " ").split()
    if not toks:
        return None
    if toks[0] == "every":
        period = int(toks[1])
        phase = 0
        if "phase" in toks:
            phase = int(toks[toks.index("phase") + 1])
        return "mode=periodic, period=%d, phase=%d" % (period, phase)
    if toks[:2] == ["once", "at"]:
        return "mode=once, epoch=%d" % int(toks[2])
    return None


def _desugar_code(code):
    """Desugar the CODE portion of one core line (comment already split off).
    A no-op unless the line carries a named rotor or a concise pulser clock."""
    # named rotor -> numeric lanes at the spinner's n
    mrot = _ROTOR_NAME_RE.search(code)
    if mrot:
        mn = _N_RE.search(code)
        if mn is None:
            WC._fail(WC.WRL_UNSUPPORTED_FEATURE,
                     "named rotor %r needs the spinner fractional width n on the "
                     "same declaration" % (mrot.group(1),))
        lanes = named_rotor(mrot.group(1), int(mn.group(1)))
        code = (code[:mrot.start()] + "rotor=" + ".".join(str(v) for v in lanes)
                + code[mrot.end():])
    # concise clock -> verbose kv, only inside a pulser paren group
    if code.lstrip().startswith("[pulser:"):
        mg = _PAREN_RE.search(code)
        if mg:
            new = _desugar_clock(mg.group(1))
            if new is not None:
                code = code[:mg.start()] + "(" + new + ")" + code[mg.end():]
    return code


def desugar_core(src):
    """WRL Core source with sugar -> canonical WRL Core source (numeric rotors,
    verbose clocks). Idempotent, and a no-op on already-numeric source. `;`
    comments and layout are preserved; only the code portion of a line is
    rewritten."""
    out = []
    for raw in src.splitlines():
        code, sep, comment = raw.partition(";")
        out.append(_desugar_code(code) + (sep + comment if sep else ""))
    tail = "\n" if src.endswith("\n") else ""
    return "\n".join(out) + tail


def parse_core_sugared(src):
    """Sugar-aware WRL Core parse: desugar to the canonical surface, then hand
    the UNTOUCHED `parse_wrl_core` the numeric text. Identity is a pure function
    of the desugared (numeric) graph."""
    return W.parse_wrl_core(desugar_core(src))


def lower_core_sugared(src):
    """Sugar-aware lowering: `lower_program(desugar_core(src))` -- byte-identical
    to lowering the numeric twin."""
    return W.lower_program(desugar_core(src), W.parse_wrl_core)
