"""wrl_sugar.py v0.2 -- the WRL surface SUGAR pre-pass.

Two tiers live here, added in two phases:

  VALUE sugar        (Phase 3B-4)  named rotor constants + concise clocks
  STRUCTURAL sugar   (L-0 tier)    `*` replication-by-position + `{...}` fan-out

Both are source-to-source rewrites in front of the untouched `parse_wrl_core`.

THE LAW, stated precisely (GPT-5.6, L-0 ruling): there is **no sugar-specific
identity**. Desugaring is not exempt from identity -- it is *upstream* of it. A
sugared program and its explicit twin lower to identical canonical bytes because
the sugar is gone before a graph exists, so no separate identity is minted for
the sugared spelling and none can be. It is NOT the stronger (and false) claim
that a sugar edit cannot change an identity: changing `rotor=identity` to
`rotor=quarter_turn_z`, or `sp*3` to `sp*4`, changes the program and therefore
changes the SemanticArtifactID, exactly as the explicit spelling would.

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

STRUCTURAL SUGAR (v0.2) adds one-to-MANY expansion, which brings two obligations
that value sugar never had, both mandated by the L-0 ruling:

  BOUNDS   `[spinner:sp*1000000000]` must be a typed rejection BEFORE any list
           is allocated -- see REPLICATION_MAX / FANOUT_MAX / EXPANSION_MAX_LINES.
  MAPPING  one-to-many breaks "emitted line N == authored line N", which every
           downstream tool assumes. `desugar_core_mapped` returns a
           `SugarSourceMap` carrying each generated line back to the line the
           author actually typed.
"""
import math
import os
import re
import sys
from collections import namedtuple

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import wrl_ir as W
import wrl_canonical as WC
import wrl_spans as S

# v2: structural sugar (`*` replication, `{...}` fan-out), expansion bounds, and
# the generated-line -> authored-line SugarSourceMap.
SUGAR_VERSION = "sugar.v2"

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


# ------------------------------------------------ structural sugar (L-0 tier)
# Two frozen-but-dead surface symbols are activated here, both as PURE
# source-to-source expansions, so they inherit the whole prepass discipline: a
# sugared world and its explicit twin lower to IDENTICAL canonical bytes and the
# formatter emits only the explicit form.
#
#   `*` REPLICATION   Core 0.1.1 s4 freezes `*` as "wildcard match, or
#                     REPLICATION-BY-POSITION". Declaration position mints a
#                     group; edge-endpoint position references the whole group.
#
#                         [spinner:sp*3](w=8, n=4, rotor=identity){sig_in, socket}
#                             -> [spinner:sp0]... [spinner:sp1]... [spinner:sp2]...
#
#   `{...}` FAN-OUT   an edge whose DESTINATION is a brace group is one edge per
#                     member. (On a node declaration `{...}` is the frozen port
#                     projection, so this form is recognized only on a line that
#                     already carries `-->` -- the two can never collide.)
#
#                         [p0] --sig--> {[a], [b]}   ->   two edges
#
# THREE AUTONOMOUS DECISIONS, flagged for GPT-5.6 (none is load-bearing for
# identity -- every one of them is washed out before the graph is built):
#
#   D-a  group members are ZERO-BASED (`sp*3` -> sp0, sp1, sp2), because
#        "replication-by-POSITION" reads as an index, not an ordinal.
#   D-b  `*` on BOTH endpoints of an edge pairs POSITIONALLY (i-th to i-th) and
#        requires equal counts -- again because the frozen gloss says
#        "by-position", not "by-product". A cartesian product would need its own
#        spelling, and none is proposed. Unequal counts are a typed rejection,
#        never a silent truncation or a silent broadcast.
#   D-c  an inline `;` comment on an expanded line attaches to the FIRST emitted
#        line only, rather than being repeated N times.
#
# Expansion enforces ONLY its own preconditions (well-formed spelling, matching
# counts, and the expansion BOUNDS below). It does NOT judge topology: an
# expansion that produces an illegal graph -- e.g. a fan-IN, which the frozen
# registry forbids because a node admits at most one `sig_in`, or a generated
# name that collides with an explicit declaration -- reaches the SEAL and is
# rejected there with the ordinary typed code. That is the v0.4-2 rule ("an op
# enforces its own precondition, the SEAL judges structural legality") applied
# to the surface.
#
# SCOPE (ruled, 0.1.2 errata): only the REPLICATION-BY-POSITION meaning of `*`
# is implemented. The wildcard-match meaning stays RESERVED and unimplemented.
REPLICATION_BASE = 0

# ------------------------------------------------------------ expansion bounds
# A prepass that expands 1 -> N is a denial-of-service surface: `[spinner:sp*
# 1000000000]` would otherwise allocate a billion strings before any validator
# ever sees the program. These caps are enforced BEFORE any list is built, and
# they are a SURFACE-TOOLING limit -- they constrain what a human may SPELL, not
# what the semantic graph may CONTAIN. A world with 5000 hand-written spinners
# remains perfectly legal; it simply cannot be written with one `*`.
REPLICATION_MAX = 1024          # members mintable by a single `*`
FANOUT_MAX = 1024               # members in a single `{...}` group
EXPANSION_MAX_LINES = 65536     # total emitted lines for one desugar
_MAX_COUNT_DIGITS = 9           # reject absurd literals before int() sees them

_REPL_DECL_RE = re.compile(r"^\s*\[(\w+):(\w+)\*(\d+)\]\s*(.*)$")
_REPL_REF_RE = re.compile(r"^((?:\w+:)?)(\w+)\*(\d+)$")
_FANOUT_RE = re.compile(r"^\s*\[([^\]]+)\]\s*--(\w+)-->\s*\{([^}]*)\}\s*$")
_EDGE_SUGAR_RE = re.compile(r"^\s*\[([^\]]+)\]\s*--(\w+)-->\s*\[([^\]]+)\]\s*$")


def _checked_count(digits, where):
    """Parse a replication count and BOUND it before anything is allocated."""
    if len(digits) > _MAX_COUNT_DIGITS:
        WC._fail(WC.WRL_NUMERIC_RANGE,
                 "replication count in %r has %d digits; the maximum is %d"
                 % (where, len(digits), REPLICATION_MAX))
    n = int(digits)
    if n < 1:
        WC._fail(WC.WRL_NUMERIC_RANGE,
                 "replication count must be >= 1, got %r" % (where,))
    if n > REPLICATION_MAX:
        WC._fail(WC.WRL_NUMERIC_RANGE,
                 "replication count %d in %r exceeds REPLICATION_MAX=%d; write "
                 "the members explicitly if a group this large is intended"
                 % (n, where, REPLICATION_MAX))
    return n


def _member(prefix, base, i):
    return "%s%s%d" % (prefix, base, REPLICATION_BASE + i)


def _repl_parts(endpoint):
    """`sp*3` / `spinner:sp*3` -> (prefix, base, 3); a plain endpoint -> None."""
    m = _REPL_REF_RE.match(endpoint.strip())
    if not m:
        return None
    return m.group(1), m.group(2), _checked_count(m.group(3), endpoint.strip())


def _desugar_decl_replication(code):
    """`[role:name*N](cfg){ports}` -> N explicit declarations, or None."""
    m = _REPL_DECL_RE.match(code)
    if not m:
        return None
    role, base, tail = m.group(1), m.group(2), m.group(4)
    n = _checked_count(m.group(3), code.strip())
    return ["[%s:%s]%s" % (role, _member("", base, i), tail) for i in range(n)]


def _desugar_edge_replication(code):
    """Expand `*` on either or both edge endpoints, or None if neither has it."""
    m = _EDGE_SUGAR_RE.match(code)
    if not m:
        return None
    src, tag, dst = m.group(1), m.group(2), m.group(3)
    rs, rd = _repl_parts(src), _repl_parts(dst)
    if rs is None and rd is None:
        return None
    if rs is not None and rd is not None:
        if rs[2] != rd[2]:
            WC._fail(WC.WRL_NUMERIC_RANGE,
                     "positional replication needs equal counts, got %d and %d "
                     "in %r" % (rs[2], rd[2], code.strip()))
        return ["[%s] --%s--> [%s]"
                % (_member(rs[0], rs[1], i), tag, _member(rd[0], rd[1], i))
                for i in range(rs[2])]
    if rs is not None:
        return ["[%s] --%s--> [%s]" % (_member(rs[0], rs[1], i), tag, dst.strip())
                for i in range(rs[2])]
    return ["[%s] --%s--> [%s]" % (src.strip(), tag, _member(rd[0], rd[1], i))
            for i in range(rd[2])]


def _desugar_fanout(code):
    """`[a] --tag--> {[b], [c]}` -> one edge per member, or None."""
    m = _FANOUT_RE.match(code)
    if not m:
        return None
    src, tag, body = m.group(1), m.group(2), m.group(3)
    members = [t.strip() for t in body.split(",") if t.strip()]
    if not members:
        WC._fail(WC.WRL_UNSUPPORTED_FEATURE,
                 "empty fan-out group in %r" % (code.strip(),))
    if len(members) > FANOUT_MAX:
        WC._fail(WC.WRL_NUMERIC_RANGE,
                 "fan-out group in %r has %d members; the maximum is %d"
                 % (code.strip(), len(members), FANOUT_MAX))
    out = []
    for tok in members:
        if not (tok.startswith("[") and tok.endswith("]")):
            WC._fail(WC.WRL_UNSUPPORTED_FEATURE,
                     "fan-out member %r must be a bracketed endpoint" % (tok,))
        out.append("[%s] --%s--> [%s]" % (src.strip(), tag, tok[1:-1].strip()))
    return out


def _desugar_structural(code):
    """Apply the structural expansions to one already-value-desugared line.
    Returns a LIST of code lines (length 1 when nothing expanded)."""
    if not code.strip():
        return [code]
    if "-->" in code:
        fan = _desugar_fanout(code)
        if fan is not None:
            # a fanned-out member may itself carry `*`. The two bounds compose
            # multiplicatively, so the product is checked as it accumulates --
            # never after the fact.
            out = []
            for ln in fan:
                out.extend(_desugar_edge_replication(ln) or [ln])
                if len(out) > EXPANSION_MAX_LINES:
                    WC._fail(WC.WRL_NUMERIC_RANGE,
                             "fan-out x replication in %r exceeds "
                             "EXPANSION_MAX_LINES=%d"
                             % (code.strip(), EXPANSION_MAX_LINES))
            return out
        return _desugar_edge_replication(code) or [code]
    return _desugar_decl_replication(code) or [code]


# ------------------------------------------------------ sugar -> source mapping
# One-to-many expansion destroys the naive "emitted line N == authored line N"
# assumption that every downstream tool (diagnostics, SemanticDiff, completion,
# canvas click-through) relies on. `wrl_spans` maps CANONICAL KEYS to spans in
# the text it was handed -- but after desugaring, that text is the GENERATED
# text, not what the author typed. This sidecar is the missing arrow: it maps
# each generated line back to the authored line that produced it, so the two
# compose into authored-source spans for a sugared program.
#
# It is a PRESENTATION sidecar, exactly like WrlSourceMap: it is not hashed, it
# enters no artifact, and discarding it changes no identity.
class SugarOrigin(namedtuple(
        "SugarOrigin",
        "emitted_line source_line source_text expanded member_index "
        "member_count emitted_text")):
    """One generated line's provenance. Lines are 1-based. `expanded` is False
    for a line that passed through untouched, in which case member_index is 0
    and member_count is 1. `emitted_text` is the generated line itself, which is
    what makes column-exact remapping decidable -- see `verbatim`."""
    __slots__ = ()

    @property
    def verbatim(self):
        """True when the generated line is BYTE-IDENTICAL to the authored line.

        This is the exact condition under which COLUMNS survive the prepass, and
        it is the honest test rather than a proxy: value sugar (`rotor=
        quarter_turn_z` -> `rotor=16.0.0.0`) changes the line's length, so every
        column to its right shifts even though the line did not expand. Testing
        `not expanded` would therefore be WRONG -- a line can be unexpanded and
        still have moved its columns."""
        return self.emitted_text == self.source_text


class SugarRemap(namedtuple("SugarRemap", "span exact origin")):
    """The result of mapping a GENERATED span back to authored coordinates.

    `exact` is True when the authored span is column-precise, False when it was
    COLLAPSED to the authored construct. A collapse is not a failure: for a
    generated member (`sp1` out of `sp*3`) there is no authored column to point
    at, because the author never typed that text. Pointing at the sugar they DID
    type is the correct answer, and `exact=False` is how a consumer knows the
    span denotes a construct rather than a character range."""
    __slots__ = ()


class SugarSourceMap(object):
    """Read-only generated-line -> authored-line index for one desugar."""

    __slots__ = ("source_text", "emitted_text", "_origins", "_by_emitted",
                 "_src_starts")

    def __init__(self, source_text, origins, emitted_text=""):
        object.__setattr__(self, "source_text", source_text)
        object.__setattr__(self, "emitted_text", emitted_text)
        object.__setattr__(self, "_origins", tuple(origins))
        object.__setattr__(self, "_by_emitted",
                           {o.emitted_line: o for o in origins})
        object.__setattr__(self, "_src_starts", S._line_starts(source_text))

    def __setattr__(self, n, v):
        raise AttributeError("SugarSourceMap is read-only (cannot set %r)" % (n,))

    def __delattr__(self, n):
        raise AttributeError("SugarSourceMap is read-only (cannot del %r)" % (n,))

    @property
    def origins(self):
        return self._origins

    def origin_for_emitted_line(self, line_no):
        """The authored provenance of 1-based generated line `line_no`."""
        return self._by_emitted.get(line_no)

    def authored_line(self, line_no):
        """The 1-based AUTHORED line number behind a generated line."""
        o = self._by_emitted.get(line_no)
        return None if o is None else o.source_line

    def expanded_lines(self):
        """Every generated line that came from a sugar expansion."""
        return tuple(o for o in self._origins if o.expanded)

    def group_for_source_line(self, source_line):
        """All generated lines produced by one authored line -- the inverse
        arrow, used to highlight a whole expansion from one cursor position."""
        return tuple(o for o in self._origins if o.source_line == source_line)

    def is_identity(self):
        """True when no line moved: every generated line sits at its authored
        line number. Guaranteed for sugar-free source."""
        return all(o.emitted_line == o.source_line and not o.expanded
                   for o in self._origins)

    # -------------------------------------------------- the remapping seam
    # Everything above indexes LINES. A tool does not consume lines, it consumes
    # `wrl_spans.SourceSpan` -- so a line index alone does not make a toolchain
    # authored-coordinate-correct, it only makes one manually traceable. The
    # methods below are the actual seam: GENERATED SourceSpan -> AUTHORED
    # SourceSpan, which is what lets an UNMODIFIED span consumer (diagnostics,
    # SemanticDiff locators, canvas click-through) operate on sugared source.
    def authored_line_span(self, source_line, file_id=S.DEFAULT_FILE_ID):
        """The span of the CODE content of one authored line -- the construct
        the author actually typed, comment and surrounding whitespace excluded.
        This is what a generated member collapses onto."""
        if source_line < 1 or source_line > len(self._src_starts):
            return None
        raw = self.source_text.splitlines()[source_line - 1]
        got = S._content_span(file_id, raw, source_line,
                              self._src_starts[source_line - 1], ";")
        return None if got is None else got[0]

    def remap(self, span):
        """A GENERATED span -> `SugarRemap` in AUTHORED coordinates.

        Two cases, and the distinction is the whole point:

          * the generating line is VERBATIM -- the author's own text passed
            through untouched. Columns are preserved EXACTLY; only the line
            number is corrected for any expansion that happened ABOVE it. This
            is the case the ruling calls "later error retains line and column".

          * the generating line was rewritten or expanded. There is no authored
            column to report, so the span COLLAPSES onto the authored construct
            and `exact` is False.

        A span this map does not cover is returned unchanged with `exact=False`
        and `origin=None` -- never dropped, because silently losing a location
        is worse for a tool than an imprecise one."""
        o = self._by_emitted.get(span.start_line)
        if o is None:
            return SugarRemap(span, False, None)
        collapsed = self.authored_line_span(o.source_line, span.file_id)
        if not o.verbatim or span.start_line != span.end_line:
            return SugarRemap(collapsed or span, False, o)
        base = self._src_starts[o.source_line - 1]
        return SugarRemap(S.SourceSpan(
            span.file_id,
            base + span.start_column, base + span.end_column,
            o.source_line, span.start_column,
            o.source_line, span.end_column), True, o)

    def remap_span(self, span):
        """`remap(span).span` -- the arrow alone, for callers that only need the
        authored location and not whether it was column-exact."""
        return self.remap(span).span


def desugar_core_mapped(src):
    """`desugar_core`, plus the generated-line -> authored-line sidecar.

    Returns `(text, SugarSourceMap)`. `text` is byte-identical to what
    `desugar_core(src)` returns -- the map is strictly additive, so no caller
    that ignores it can observe a difference."""
    out, origins = [], []
    for src_line_no, raw in enumerate(src.splitlines(), start=1):
        code, sep, comment = raw.partition(";")
        tail = sep + comment if sep else ""
        expansion = _desugar_structural(_desugar_code(code))
        if len(out) + len(expansion) > EXPANSION_MAX_LINES:
            WC._fail(WC.WRL_NUMERIC_RANGE,
                     "desugaring this source would emit more than "
                     "EXPANSION_MAX_LINES=%d lines" % (EXPANSION_MAX_LINES,))
        expanded = len(expansion) > 1
        for i, line in enumerate(expansion):
            # line 0 is the ORIGINAL line's slot -- its layout (and its comment,
            # per D-c) is preserved byte-for-byte, which is what keeps desugar a
            # true no-op on sugar-free source. Lines 1..N-1 are newly minted, so
            # they carry no inherited alignment padding.
            out.append(line + tail if i == 0 else line.rstrip())
            origins.append(SugarOrigin(
                emitted_line=len(out), source_line=src_line_no,
                source_text=raw, expanded=expanded,
                member_index=i, member_count=len(expansion),
                emitted_text=out[-1]))
    nl = "\n" if src.endswith("\n") else ""
    text = "\n".join(out) + nl
    return text, SugarSourceMap(src, origins, text)


def sugar_failure_line(src):
    """The 1-based AUTHORED line whose desugaring raises, or None if no single
    line is responsible.

    A pure LOCATOR, built on exactly the pattern `wrl_diagnostics._loc_bad_config`
    already uses: it re-runs the SAME per-line desugar and reports which line
    raised. It duplicates no logic and re-decides nothing --
    `desugar_core_mapped` remains the sole authority on whether a source
    desugars, and this function is consulted only AFTER that authority has
    already rejected it.

    It exists because the prepass raises BEFORE any desugared text exists, so a
    sugar rejection would otherwise be the one diagnostic with no location at
    all -- the worst possible case, since the offending text is text the author
    typed by hand.

    Returns None when no individual line raises. That is the honest answer for a
    whole-source bound like EXPANSION_MAX_LINES, which no single line violates:
    the rejection is about the source in aggregate, and inventing a line for it
    would be a guess."""
    for line_no, raw in enumerate(src.splitlines(), start=1):
        try:
            _desugar_structural(_desugar_code(raw.partition(";")[0]))
        except WC.WrlValidationError:
            return line_no
    return None


def authored_span_for_line(src, line_no, file_id=S.DEFAULT_FILE_ID):
    """The content span of one 1-based AUTHORED line of `src` (comment and
    surrounding whitespace excluded), or None. The span a prepass rejection is
    reported against, and the same arithmetic `SugarSourceMap.authored_line_span`
    uses -- sourced from `wrl_spans` so the two can never drift."""
    lines = src.splitlines()
    if line_no is None or line_no < 1 or line_no > len(lines):
        return None
    got = S._content_span(file_id, lines[line_no - 1], line_no,
                          S._line_starts(src)[line_no - 1], ";")
    return None if got is None else got[0]


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
    verbose clocks, explicit replication groups and fan-out edges). Idempotent,
    and a no-op on already-explicit source. `;` comments and layout are
    preserved; only the code portion of a line is rewritten.

    A line may now expand to SEVERAL lines (`*` replication, `{...}` fan-out).
    Per decision D-c an inline comment attaches to the FIRST emitted line.

    This is the text-only face of `desugar_core_mapped`; callers that need to
    report a diagnostic against what the author actually typed should use that
    instead and keep the `SugarSourceMap`."""
    return desugar_core_mapped(src)[0]


# ------------------------------------------------- authored-coordinate tooling
# The composition that makes the seam USEFUL rather than merely available.
#
# `wrl_spans` maps canonical keys -> spans in whatever text it was handed. Hand
# it desugared text and every span it produces is in GENERATED coordinates,
# which is wrong for every editor-facing purpose. Remapping the WrlSourceMap
# ITSELF -- rather than asking each consumer to remember to compose two maps --
# means an UNMODIFIED span consumer becomes authored-correct. That is the
# difference between "a mapping exists" and "the toolchain is correct": the
# former is a data structure, the latter is a property of every caller.
def authored_source_map(sugar_map, generated_map, file_id=S.DEFAULT_FILE_ID):
    """A generated-coordinate `WrlSourceMap` -> the same map in AUTHORED
    coordinates. Canonical keys are untouched (they are identity, not location);
    only the spans move."""
    return S.WrlSourceMap(file_id, tuple(
        o._replace(span=sugar_map.remap_span(o.span))
        for o in generated_map.origins))


def parse_sugared_with_spans(src, file_id=S.DEFAULT_FILE_ID):
    """Sugared WRL Core source -> `(graph, WrlSourceMap, SugarSourceMap)` where
    the WrlSourceMap is in AUTHORED coordinates.

    The sugar-aware twin of `wrl_spans.parse_core_with_spans`. Note the ordering
    obligation: the span scan must run over the DESUGARED text (that is the text
    the parser saw, so it is the only text whose lines correspond to canonical
    keys), and the remap must then run over the result. Scanning the authored
    text directly would be simpler and wrong -- it cannot see the generated
    members at all."""
    dtext, sugar_map = desugar_core_mapped(src)
    graph = W.parse_wrl_core(dtext)
    gen_map = S._scan_core_spans(dtext, file_id)
    return graph, authored_source_map(sugar_map, gen_map, file_id), sugar_map


def lower_sugared_with_spans(src, file_id=S.DEFAULT_FILE_ID):
    """`lower_core_sugared`, plus the AUTHORED-coordinate span sidecar.
    Returns `(LoweredProgram, WrlSourceMap, SugarSourceMap)`."""
    dtext, sugar_map = desugar_core_mapped(src)
    prog = W.lower_program(dtext, W.parse_wrl_core)
    gen_map = S._scan_core_spans(dtext, file_id)
    return prog, authored_source_map(sugar_map, gen_map, file_id), sugar_map


def diff_sugared_sources_located(sa, sb, file_id=S.DEFAULT_FILE_ID):
    """SemanticDiff between two SUGARED sources, with every change LOCATED in
    AUTHORED coordinates. Returns `(SemanticDiff, tuple[LocatedChange])`.

    This is the composition that makes SemanticDiff editor-correct on sugared
    source, and it is deliberately thin: `wrl_diff.locate_changes` stays entirely
    sugar-unaware and simply consumes the AUTHORED-coordinate maps built here.
    That is the dividend of remapping the WrlSourceMap itself rather than
    teaching each consumer about sugar -- the consumer needed no changes at all.

    `wrl_diff` is imported lazily: it is needed only by this one composition, and
    a deferred import keeps `wrl_sugar` (which `wrl_complete` and
    `wrl_diagnostics` both sit on top of) from pulling the diff layer into every
    import graph that touches sugar."""
    import wrl_diff as DF
    ga, ma, _ = parse_sugared_with_spans(sa, file_id)
    gb, mb, _ = parse_sugared_with_spans(sb, file_id)
    diff = DF.diff_graphs(ga, gb)
    return diff, DF.locate_changes(diff, ma, mb)


def parse_core_sugared(src):
    """Sugar-aware WRL Core parse: desugar to the canonical surface, then hand
    the UNTOUCHED `parse_wrl_core` the numeric text. Identity is a pure function
    of the desugared (numeric) graph."""
    return W.parse_wrl_core(desugar_core(src))


def lower_core_sugared(src):
    """Sugar-aware lowering: `lower_program(desugar_core(src))` -- byte-identical
    to lowering the numeric twin."""
    return W.lower_program(desugar_core(src), W.parse_wrl_core)


# ----------------------------------------------------- legacy document mouths
# The explicitly-named legacy twins (L-0 Q2). Sugar is orthogonal to the
# document boundary -- it rewrites values and structure, never run inputs -- so
# these differ from the pair above ONLY in which parser mouth they hand the
# desugared text to.
def parse_legacy_sugared(src):
    """Sugar-aware parse of a pre-v0.4-0 COMBINED document."""
    return W.parse_wrl_legacy_document(desugar_core(src))


def lower_legacy_sugared(src):
    """Sugar-aware lowering of a pre-v0.4-0 COMBINED document."""
    return W.lower_program(desugar_core(src), W.parse_wrl_legacy_document)
