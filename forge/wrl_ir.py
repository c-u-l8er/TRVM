"""wrl_ir.py v0.2 -- WRL lowering front-half (Slice 2, the identity spine).

    WRL surface text  ->  canonical WRL graph  ->  Forge Semantic IR v1
                                                 ->  current Fixture adapter

Two concrete surfaces lower to the SAME canonical graph (and therefore the
same canonical artifact bytes, Slice 2 two-surface equivalence):

  * parse_wrl_bootstrap -- the line-oriented bootstrap DSL (`pulser p0 ...`);
  * parse_wrl_core      -- WRL process notation
      `[pulser:p0](mode=periodic, period=2, phase=0){sig_out}`
      `[pulser:p0] --sig--> [spinner:sp]`.

The frozen registries, typed structural validation (stable error codes), the
canonicalization, and the SemanticArtifactID/BackendArtifactID identity split
all live in wrl_canonical.py; this module is the surface + adapter. The STATIC
semantic artifact carries NO run inputs (D3): the claim batches / run plan are
threaded separately in a LoweredProgram, and NOTHING but the frozen semantic
graph feeds the SemanticArtifactID.

Everything outside the frozen scope raises WrlUnsupported (or a typed
WrlValidationError subclass) with a clear diagnostic -- NEVER a speculative
lowering.
"""
import os
import re
import sys
from collections import namedtuple

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import wrl_canonical as WC
from wrl_canonical import (
    IR_VERSION, PROFILE_ID, RULEPACK_ID, ADMIT_POLICY_ID, FILM_SCHEMA_ID,
    semantic_surface_for_roles, mailbox_decls_of_artifact, roles_of_artifact,
    NUMERIC_POLICY_IDS, SCHEMA_IDS, SCHEMA_IDS_V1_1, schemas_for_roles,
    ROLE_IDS, MAILBOX_ROLE, EDGE_KINDS, PORTS,
    WrlUnsupported, WrlValidationError,
    WRL_UNSUPPORTED_FEATURE, WRL_EPOCH_RANGE, WRL_NUMERIC_RANGE,
    WRL_PORT_SIGNATURE,
    validate_graph, canonicalize_graph, validate_port_projection, object_ports,
    port_projection,
    validate_artifact_v1, seal_artifact, serialize_artifact,
    deserialize_artifact, semantic_artifact_id, backend_artifact_id,
)


# ============================================================ canonical graph
class WrlGraph:
    def __init__(self):
        self.profile = PROFILE_ID
        self.periods = 0
        self.nodes = []      # (role, name, config_dict)
        self.edges = []      # (kind, src, dst)
        # Slice B AsyncRouteDecl records: {source_id, route_tag, mailbox_id,
        # body}. A SEPARATE list from `edges` and not a new edge kind, because
        # D8 holds: a mailbox has no port and is never wired. A route is a
        # static declaration that the world will emit one `Send`.
        self.routes = []
        self.batches = []    # [ [claim, ...], ... ]  indexed by epoch


# a single lowered program: the SEALED semantic artifact + the SEPARATE run
# inputs (D3). Phase 3D: lowering builds NO Fixture -- the production compile
# contract is the CompilePlanV1 (wrl_plan), and the Fixture survives ONLY as an
# independent test oracle, reachable lazily via `as_fixture_for_test()`.
# `initial_claim_state` is ONLY the semantic claim projection (facts, receipts,
# capacity faults); the physical clock/rotor/pose/wire state is derived later
# from the compile plan -- so it is NOT a full initial runtime state (2.1).
class LoweredProgram(namedtuple(
        "LoweredProgram",
        "sealed_artifact semantic_artifact_id initial_claim_state "
        "run_plan epoch_inputs canonical_graph")):
    __slots__ = ()

    @property
    def artifact(self):
        """The frozen canonical semantic artifact (a fresh isolated dict)."""
        return self.sealed_artifact.artifact

    @property
    def graph(self):
        return self.canonical_graph

    def as_fixture_for_test(self):
        """Build the independent legacy Fixture oracle from the sealed artifact.
        Phase 3D: this is a TEST/oracle path only -- production lowering and
        compilation never construct a Fixture. The import is lazy so the
        production frontend never imports the Fixture module (D14)."""
        return ir_to_fixture(self.artifact)

    # back-compat accessor for the batteries; production code uses the plan.
    @property
    def fixture(self):
        return self.as_fixture_for_test()


# ------------------------------------------------------------ shared helpers
def _rotor_commas(tok):
    parts = tok.split(",")
    if len(parts) != 4:
        raise WrlValidationError(WRL_NUMERIC_RANGE,
                                 "rotor must have 4 lanes, got %r" % (tok,))
    return tuple(int(x) for x in parts)


def _rotor_dots(tok):
    parts = tok.split(".")
    if len(parts) != 4:
        raise WrlValidationError(WRL_NUMERIC_RANGE,
                                 "rotor must have 4 lanes, got %r" % (tok,))
    return tuple(int(x) for x in parts)


def _body_dots(tok):
    """`0.0.0.7` -> the four-lane route body tuple (Slice B commit 3).

    Dot-separated like a rotor, and NOT `_rotor_dots` even though the two agree
    on 4 today. A rotor's arity is the spinner's; a body's arity is
    `WC.ROUTE_BODY_LANES`, which is derived from ADMIT's Send payload. They are
    two constants that currently coincide, so calling `_rotor_dots` here would
    read as a shared definition and would silently stop being right the moment
    either arity moved -- with a diagnostic that said `rotor` about a body."""
    parts = tok.split(".")
    if len(parts) != WC.ROUTE_BODY_LANES:
        raise WrlValidationError(
            WRL_NUMERIC_RANGE,
            "route body must have %d lanes, got %r"
            % (WC.ROUTE_BODY_LANES, tok))
    try:
        return tuple(int(x) for x in parts)
    except ValueError:
        # `int()` raising ValueError here would be an untyped crash standing in
        # for a typed rejection -- the exact defect mutation testing found in
        # `route_body_in_range`. A non-numeric lane is a surface error and must
        # arrive wearing a WRL_ code like every other one.
        raise WrlValidationError(WRL_NUMERIC_RANGE,
                                 "route body lanes must be integers, got %r"
                                 % (tok,))


# The WRL Core TEXT SURFACE: surface lexeme -> registry role id.
#
# This is a PROJECTION of `wrl_canonical.ROLE_IDS`, not a copy of it. Treating
# this table as if it were the registry is what produced three separate defects
# (a crashing completion API, a role that cannot be written down, and a
# rejection message that denied the existence of a role the registry defines),
# so the relationship is stated here rather than assumed at each call site.
#
# Slice B commit 1 adds `mailbox`, which makes the projection TOTAL today --
# `unwritable_role_ids()` computes to `()`. That is a fact about the current
# contents, NOT a new invariant: the next registry role arrives unwritable and
# every consumer must keep handling that, so nothing downstream may start
# assuming the two sets are equal. Totality is the state; projection is the law.
_ROLE_TOKEN = {"pulser": "Pulser", "relay": "Relay", "door": "Door",
               "spinner": "Spinner", "orb": "Orb", "mailbox": "Mailbox"}
_EDGE_TAG = {"sig": "SignalWire", "socket": "SocketControl"}


def writable_role_ids():
    """The registry roles that WRL Core text can actually SPELL."""
    return tuple(sorted(set(_ROLE_TOKEN.values())))


def unwritable_role_ids():
    """The registry roles with NO WRL Core surface lexeme -- roles that are
    fully specified semantically (ports, config schema, identity) but that no
    author can write down in text today.

    This is deliberately COMPUTED, not a hand-listed allowlist. A hand-listed
    one would be a fourth spelling of the same vocabulary and would drift in
    exactly the way the other three did. Computed, it shrinks to `()` by itself
    the moment a surface lexeme is added, and it grows by itself the moment a
    role is added to the registry without one."""
    return tuple(sorted(set(WC.ROLE_IDS) - set(_ROLE_TOKEN.values())))


def _add_claim(g, epoch, wid, seq, body_tokens, rotor_parse):
    if not (1 <= epoch <= g.periods):
        raise WrlValidationError(WRL_EPOCH_RANGE,
                                 "epoch %d out of range [1, %d]"
                                 % (epoch, g.periods))
    op = body_tokens[0]
    if op == "SetRotor":
        payload = ("SetRotor", body_tokens[1], rotor_parse(body_tokens[2]))
    elif op == "ResetFault":
        payload = ("ResetFault", body_tokens[1])
    else:
        raise WrlValidationError(WRL_UNSUPPORTED_FEATURE,
                                 "claim op %r (only SetRotor|ResetFault in "
                                 "IR v1)" % (op,))
    g.batches[epoch - 1].append({"writer_id": wid, "sequence": seq,
                                  "payload": payload})


# --------------------------------------------------------- bootstrap surface
def parse_wrl_bootstrap(text):
    """Line-oriented bootstrap DSL -> canonical WRL graph. Restricted,
    unambiguous; any unrecognized directive is an unsupported feature."""
    g = WrlGraph()
    for raw in text.splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line:
            continue
        tok = line.split()
        head = tok[0]
        if head == "profile":
            g.profile = tok[1]
        elif head == "periods":
            g.periods = int(tok[1])
            g.batches = [[] for _ in range(g.periods)]
        elif head == "pulser":
            name = tok[1]
            if tok[2] == "periodic":
                cfg = {"clock": ("periodic", int(tok[3]), int(tok[4]))}
            elif tok[2] == "once":
                cfg = {"clock": ("once", int(tok[3]))}
            else:
                raise WrlValidationError(WRL_UNSUPPORTED_FEATURE,
                                         "pulser clock mode %r (only "
                                         "periodic|once)" % (tok[2],))
            g.nodes.append(("Pulser", name, cfg))
        elif head == "relay":
            g.nodes.append(("Relay", tok[1], {}))
        elif head == "door":
            g.nodes.append(("Door", tok[1], {}))
        elif head == "spinner":
            name = tok[1]
            kv = dict(re.findall(r"(\w+)=([^\s]+)", line))
            cfg = {"w": int(kv["w"]) if "w" in kv else None,
                   "n": int(kv["n"]) if "n" in kv else None,
                   "rotor": _rotor_commas(kv["rotor"]) if "rotor" in kv
                   else None,
                   "configurable": ("configurable" in tok[2:])}
            g.nodes.append(("Spinner", name, cfg))
        elif head == "orb":
            g.nodes.append(("Orb", tok[1], {}))
        elif head == "wire":
            g.edges.append(("SignalWire", tok[1], tok[3]))
        elif head == "socket":
            g.edges.append(("SocketControl", tok[1], tok[3]))
        elif head == "epoch":
            m = re.match(r"epoch\s+(\d+)\s*:\s*(.*)$", line)
            if not m:
                raise WrlValidationError(WRL_UNSUPPORTED_FEATURE,
                                         "bad epoch directive %r" % (line,))
            epoch = int(m.group(1))
            body = m.group(2).split()
            wid = seq = None
            wm = re.search(r"@(\d+),(\d+)", line)
            if wm:
                wid, seq = int(wm.group(1)), int(wm.group(2))
                body = [b for b in body if not b.startswith("@")]
            _add_claim(g, epoch, wid, seq, body, _rotor_commas)
        elif head in _ROLE_TOKEN:
            # A role the WRL CORE surface can spell, reached here only because
            # the bootstrap chain above has no directive for it. `mailbox` used
            # to sit in the reserved list below and be reported as "outside
            # Forge Semantic IR v1" -- true when written, false since the v1.1
            # registry admitted `Mailbox`, and false in a way that sends the
            # author to look for a spec change that already happened.
            #
            # The bootstrap DSL is a frozen migration bridge, not a surface
            # that grows: it gets no `mailbox` directive, and that is a
            # DELIBERATE non-extension, so the message names the surface that
            # does have one. Computed membership (`head in _ROLE_TOKEN`) means
            # the next Core-writable role inherits this message instead of the
            # wrong one.
            raise WrlValidationError(
                WRL_UNSUPPORTED_FEATURE,
                "%r is a WRL Core role, but the bootstrap surface is a frozen "
                "migration bridge and has no `%s` directive; write it in WRL "
                "Core process notation instead" % (head, head))
        elif head in ("gate", "seal", "supervisor", "fragment",
                      "stencil", "derive", "capability"):
            raise WrlValidationError(WRL_UNSUPPORTED_FEATURE,
                                     "%r is outside Forge Semantic IR v1 "
                                     "(profile %s); reserved/Proposed"
                                     % (head, PROFILE_ID))
        elif "~~" in line:
            # `~~` USED to be grouped with `!!` and `==` under "transition
            # classes, not IR v1 edges". That was true when written and is now
            # false twice over: an AsyncRouteDecl IS an IR v1.1 construct, and
            # it was never an edge in the first place (D8). Leaving the old
            # message would send an author to look for a spec change that
            # already happened -- the identical defect that the `mailbox`
            # bootstrap rejection above was corrected for.
            #
            # The bootstrap DSL still gets no route directive, for the same
            # reason it gets no `mailbox` one: it is a frozen migration bridge,
            # not a surface that grows. So this is a DELIBERATE non-extension,
            # and the message names the surface that does have the construct.
            raise WrlValidationError(
                WRL_UNSUPPORTED_FEATURE,
                "async route texture `~~` in %r: routes are a WRL Core "
                "construct, but the bootstrap surface is a frozen migration "
                "bridge and has no route directive; write it in WRL Core "
                "process notation instead" % (line,))
        elif "!!" in line or "==" in line:
            raise WrlValidationError(WRL_UNSUPPORTED_FEATURE,
                                     "route texture in %r: fault !! / verified "
                                     "== are transition classes, not IR v1 "
                                     "edges" % (line,))
        else:
            raise WrlValidationError(WRL_UNSUPPORTED_FEATURE,
                                     "unrecognized WRL directive %r" % (head,))
    return g


# canonical alias (the bootstrap DSL is the historical default entry point)
parse_wrl = parse_wrl_bootstrap


# -------------------------------------------------------------- core surface
_NODE_RE = re.compile(
    r"^\[(\w+):(\w+)\]\s*(\([^)]*\))?\s*(\{[^}]*\})?$")
_EDGE_RE = re.compile(
    r"^\[(?:\w+:)?(\w+)\]\s*--(\w+)-->\s*\[(?:\w+:)?(\w+)\]$")
_EPOCH_RE = re.compile(r"^\[epoch:(\d+)\]\s*(.*)$")

# Slice B commit 3 -- the AsyncRouteDecl surface, ruled Q1:
#
#     [p0] ~~msg~~> [mb] (body=0.0.0.7)
#
# Deliberately shaped like the edge form (`--tag-->`) and deliberately NOT the
# same shape: `~~` reads as asynchronous where `--` reads as a wire, and the
# difference is exactly D8's -- an edge connects two PORTS and a route does not.
# The role prefix is optional at both ends, as on an edge, because the role is
# already fixed by the object's own declaration line.
#
# The body group is REQUIRED (Q1). It is not optional-with-a-default, because a
# default the emitter knows and the surface does not is how an identity-bearing
# field goes missing from the one artifact a human reads -- the same reason the
# MailboxDecl emitter always writes both `w` and `cap`.
_ROUTE_RE = re.compile(
    r"^\[(?:\w+:)?(\w+)\]\s*~~(\w+)~~>\s*\[(?:\w+:)?(\w+)\]\s*(\([^)]*\))?$")
_ROUTE_KEYS = ("body",)


def _paren_kv(group):
    """Parse a `(k=v, k=v, bareflag)` group -> (dict, set_of_flags)."""
    kv, flags = {}, set()
    if not group:
        return kv, flags
    body = group.strip()[1:-1].strip()
    if not body:
        return kv, flags
    for item in body.split(","):
        item = item.strip()
        if not item:
            continue
        if "=" in item:
            k, v = item.split("=", 1)
            kv[k.strip()] = v.strip()
        else:
            flags.add(item)
    return kv, flags


def _ports_set(group):
    """`{a, b}` -> {'a','b'}; `{}` -> set(). WRL brace group tokens."""
    body = group.strip()[1:-1]
    return {t.strip() for t in body.split(",") if t.strip()}


# ------------------------------------------------------- the document boundary
# v0.4-0 moved RUN INPUTS (`periods N` and `[epoch:N] ...` claim batches) out of
# the world document and into ScenarioV1. They never entered the
# SemanticArtifactID (D3). But the PARSER kept accepting them, which left the
# language with TWO MOUTHS: `wrl_draft.replace_world_source` rejected exactly
# the syntax `parse_wrl_core` silently swallowed.
#
# GPT-5.6's ruling (L-0 Q2): the STRICT world parser is NORMATIVE. The permissive
# behaviour survives only behind an explicitly-named compatibility path, so that
# accepting run-input syntax is always a decision a caller made on purpose.
#
#     parse_wrl_core(text)            -- strict WORLD source
#     parse_wrl_legacy_document(text) -- pre-v0.4-0 COMBINED document
#     split_legacy_document(text)     -- the migration TARGET: world | run inputs
WRL_WORLD_SOURCE_HAS_SCENARIO = "WRL_WORLD_SOURCE_HAS_SCENARIO"

# THE AUTHORITATIVE run-input line forms, and the ONLY definition of them.
#
# These are ANCHORED LINE FORMS, not substrings, and the distinction is
# load-bearing. A substring test for `periods` also fires on an object named
# `[orb:periods_display]`; a substring test for `@` is far worse still, because
# `@` is frozen for WORLD addressing/placement and therefore appears in
# perfectly ordinary world source. A scanner built from substrings will
# eventually classify a legal world document as scenario material, which is the
# one mistake the document boundary exists to prevent.
#
# `SetRotor` / `ResetFault` are deliberately ABSENT: they are operation names
# INSIDE a claim, and every claim line is already caught by the `[epoch:` form.
# Listing them separately would add no coverage and two more false-positive
# surfaces (an object may legitimately be named `[relay:ResetFault_gate]`).
#
# Anything that needs to recognize run-input syntax -- parsers, splitters,
# lexical assertions in the batteries -- MUST consume `is_run_input_line` rather
# than re-spell these forms. A second, hand-rolled spelling is not a copy, it is
# a fork: it drifts silently and its drift is invisible until it misclassifies.
WRL_WORLD_SOURCE_HAS_SCENARIO_FORMS = (r"^\s*periods\b", r"^\s*\[epoch:")
_RUN_INPUT_RE = re.compile("|".join(WRL_WORLD_SOURCE_HAS_SCENARIO_FORMS))


def is_run_input_line(line):
    """True when one line carries ScenarioV1 run-input syntax (`periods N` or
    an `[epoch:N] ...` claim batch).

    Matches the ANCHORED line forms, so it is correct on a RAW line as well as a
    stripped one. The caller is still responsible for removing any `;` comment
    first -- a `periods` inside a comment is prose, not syntax."""
    return _RUN_INPUT_RE.match(line) is not None


# retained private alias: this predicate is called on already-stripped lines
# throughout the parser body.
_is_run_input_line = is_run_input_line


def _run_input_lines(text):
    """Every (1-based line number, stripped line) carrying ScenarioV1 syntax."""
    out = []
    for n, raw in enumerate(text.splitlines(), start=1):
        line = raw.split(";", 1)[0].strip()
        if _is_run_input_line(line):
            out.append((n, line))
    return out


def parse_wrl_core(text):
    """STRICT WRL Core WORLD source -> canonical WRL graph. Node:
    `[role:name](k=v, ...){ports}`; edge: `[a] --tag--> [b]`. Lowers to the SAME
    canonical graph as the bootstrap surface (two-surface equivalence).

    RUN INPUTS ARE NOT WORLD SOURCE. A `periods N` line or an `[epoch:N] ...`
    claim is refused with WRL_WORLD_SOURCE_HAS_SCENARIO; they belong to
    ScenarioV1. To read a pre-v0.4-0 combined document, call
    `parse_wrl_legacy_document` and say so.

    Lexical law (Slice 2.1): comments are `;` (full-line or inline) because
    slash/`#` forms are reserved -- `#` is preserved for content identity and
    tags and is NEVER treated as a comment marker here. A `{ports}` brace group
    is a CHECKED projection of the role's frozen ports, not decoration."""
    offenders = _run_input_lines(text)
    if offenders:
        n, line = offenders[0]
        raise WrlValidationError(
            WRL_WORLD_SOURCE_HAS_SCENARIO,
            "run inputs are not world source: line %d, %r -- run inputs live in "
            "ScenarioV1 (v0.4-0 document boundary). Use "
            "parse_wrl_legacy_document() to read a combined document."
            % (n, line))
    return _parse_core_permissive(text)


def parse_wrl_legacy_document(text):
    """COMPATIBILITY PATH -- a pre-v0.4-0 COMBINED document (world source with
    run inputs inlined) -> the combined canonical WRL graph, byte-for-byte what
    `parse_wrl_core` returned before the boundary was enforced.

    A MIGRATION BRIDGE, not the normative surface. New code should parse a world
    with `parse_wrl_core` and carry run inputs as a ScenarioV1."""
    return _parse_core_permissive(text)


def _split_line_ending(chunk):
    """One `splitlines(keepends=True)` chunk -> (content, ending). The ending is
    whatever the file actually used (`\\n`, `\\r\\n`, `\\r`, or `""` on a final
    line with no terminator) and is echoed back verbatim."""
    for end in ("\r\n", "\n", "\r"):
        if chunk.endswith(end):
            return chunk[:-len(end)], end
    return chunk, ""


def split_legacy_document(text):
    """The migration TARGET for the legacy path: a combined document ->
    `(world_source, run_input_source)` -- two texts, the first of which parses
    STRICTLY and the second of which is the ScenarioV1 material.

    The split is LEXICAL and POSITION-PRESERVING. Every line goes to exactly one
    side and none is rewritten; the side that does NOT receive a line gets an
    empty line in its place. The precise invariant is:

        for every line N of the input, N sits at index N of whichever side
        received it, and the two sides RECOMBINE to the input exactly.

    (Stated that way rather than as "both sides have the same line count",
    because a final EMPTY line with no terminator is textually invisible: if the
    input's last line is unterminated and lands on one side, the other side's
    trailing placeholder cannot be represented at all. That costs nothing --
    it is empty and last -- but claiming equal counts would be false.)

    That property is the whole point of splitting this way rather than
    compacting. A migration bridge that renumbered lines would hand every
    downstream diagnostic, span and editor annotation a coordinate that no
    longer refers to the document the author is looking at -- the same defect
    that makes generated coordinates useless for sugared source. Line endings
    (`\\n`, `\\r\\n`, `\\r`) and the presence or absence of a final terminator
    are preserved exactly, so a CRLF document does not silently become LF.

    Because no line is rewritten and no line moves, no identity can move across
    the split. Note that the run-input side of a document with NO run inputs is
    therefore blank lines rather than the empty string; test it with
    `.strip()`."""
    world, runs = [], []
    for chunk in text.splitlines(keepends=True):
        content, end = _split_line_ending(chunk)
        if _is_run_input_line(content.split(";", 1)[0].strip()):
            runs.append(content + end)
            world.append(end)
        else:
            world.append(content + end)
            runs.append(end)
    return "".join(world), "".join(runs)


def _parse_core_permissive(text):
    """The historical parser body: accepts world source AND run inputs. Reached
    only through the two named entry points above."""
    g = WrlGraph()
    for raw in text.splitlines():
        line = raw.split(";", 1)[0].strip()
        if not line:
            continue
        if line.startswith("profile "):
            g.profile = line.split()[1]
            continue
        if line.startswith("periods "):
            g.periods = int(line.split()[1])
            g.batches = [[] for _ in range(g.periods)]
            continue

        me = _EPOCH_RE.match(line)
        if me:
            epoch = int(me.group(1))
            body = me.group(2).split()
            wid = seq = None
            wm = re.search(r"@(\d+),(\d+)", me.group(2))
            if wm:
                wid, seq = int(wm.group(1)), int(wm.group(2))
                body = [b for b in body if not b.startswith("@")]
            _add_claim(g, epoch, wid, seq, body, _rotor_dots)
            continue

        if "~~" in line:
            # Tested BEFORE the edge form and keyed on the TEXTURE, not on a
            # successful match. Falling through to `_NODE_RE` would report
            # "unrecognized WRL notation" for a route with one tilde too few --
            # a message that denies the construct exists, which is precisely
            # the failure the Mailbox rejection was corrected for in commit 1.
            m = _ROUTE_RE.match(line)
            if not m:
                raise WrlValidationError(
                    WRL_UNSUPPORTED_FEATURE,
                    "bad async route notation %r -- the form is "
                    "`[src] ~~tag~~> [mailbox] (body=b0.b1.b2.b3)`" % (line,))
            src, tag, dst = m.group(1), m.group(2), m.group(3)
            if m.group(4) is None:
                raise WrlValidationError(
                    WRL_UNSUPPORTED_FEATURE,
                    "async route %s ~~%s~~> %s has no body; the body group is "
                    "REQUIRED (a route with an implied body would put an "
                    "identity-bearing field in the compiler and not in the "
                    "source)" % (src, tag, dst))
            kv, flags = _paren_kv(m.group(4))
            unknown = sorted(set(kv) - set(_ROUTE_KEYS)) + sorted(flags)
            if unknown:
                raise WrlValidationError(
                    WRL_UNSUPPORTED_FEATURE,
                    "async route %s ~~%s~~> %s has unknown key(s) %s (only %s)"
                    % (src, tag, dst, unknown, list(_ROUTE_KEYS)))
            if "body" not in kv:
                raise WrlValidationError(
                    WRL_UNSUPPORTED_FEATURE,
                    "async route %s ~~%s~~> %s is missing `body`"
                    % (src, tag, dst))
            # Endpoint roles, the one-shot source law, the body range and the
            # duplicate/budget rules are ALL the seal's -- `_validate_routes`
            # already owns them and owns them for a route that arrived from any
            # surface. The parser's job stops at "this line says a route".
            g.routes.append({"source_id": src, "route_tag": tag,
                             "mailbox_id": dst,
                             "body": _body_dots(kv["body"])})
            continue

        if "-->" in line:
            m = _EDGE_RE.match(line)
            if not m:
                raise WrlValidationError(WRL_UNSUPPORTED_FEATURE,
                                         "bad edge notation %r" % (line,))
            src, tag, dst = m.group(1), m.group(2), m.group(3)
            if tag not in _EDGE_TAG:
                raise WrlValidationError(WRL_UNSUPPORTED_FEATURE,
                                         "edge tag %r (only sig|socket in "
                                         "IR v1)" % (tag,))
            g.edges.append((_EDGE_TAG[tag], src, dst))
            continue

        m = _NODE_RE.match(line)
        if not m:
            raise WrlValidationError(WRL_UNSUPPORTED_FEATURE,
                                     "unrecognized WRL notation %r" % (line,))
        rtok, name = m.group(1), m.group(2)
        if rtok not in _ROLE_TOKEN:
            # Two DIFFERENT rejections wear the same code, and conflating them
            # produced a message that denied the existence of a role the
            # registry defines. `mailbox` is a real v1 registry role with ports
            # and a config schema; it simply has no text spelling yet. Telling
            # an author it "is not in the registry" sends them to fix the wrong
            # thing entirely.
            hit = [r for r in unwritable_role_ids() if r.lower() == rtok.lower()]
            if hit:
                raise WrlValidationError(
                    WRL_UNSUPPORTED_FEATURE,
                    "role %r is in the frozen v1 registry but has no WRL Core "
                    "surface form yet" % (hit[0],))
            raise WrlValidationError(WRL_UNSUPPORTED_FEATURE,
                                     "role %r not in the frozen v1 registry"
                                     % (rtok,))
        role = _ROLE_TOKEN[rtok]
        if m.group(4) is not None:            # visible ports are checked, not ignored
            validate_port_projection(role, _ports_set(m.group(4)), name)
        elif not port_projection(role):
            # A role with ports may ABBREVIATE by omitting the brace group --
            # frozen behaviour, and harmless, because the omission cannot be
            # confused with anything: the signature is non-empty, so there is
            # no reading under which the author meant "no ports".
            #
            # A role whose frozen signature is EMPTY has no such luck. `[...]`
            # and `[...]{}` would mean the same thing, so an author who simply
            # forgot the block writes something indistinguishable from an
            # author who deliberately declared emptiness -- and for Mailbox the
            # emptiness is the whole point (D8: not wireable). So the ruling
            # requires `{}` to be WRITTEN, and it is required here.
            #
            # The condition is COMPUTED from the frozen port table, not spelled
            # `role == "Mailbox"`. A named role would be a fork of the table
            # that has to be edited by whichever commit adds the next portless
            # role -- and the forgetting would be silent, because the parser
            # would simply keep accepting the abbreviation.
            # Raised through `WC._fail` rather than `raise WrlValidationError`
            # so it arrives LOCATED. The surrounding parser predates the
            # locator spine and still raises bare; a new rejection introduced
            # in the same commit that discharges the locator obligation has no
            # excuse to be the next unlocated one.
            WC._fail(
                WRL_PORT_SIGNATURE,
                "%s %s: the port block is required and must be written `{}` -- "
                "%s has an empty frozen port signature, so an omitted block "
                "cannot be told apart from a forgotten one"
                % (role, name, role),
                primary_locator=WC.ObjectKey(name), field_path="ports")
        kv, flags = _paren_kv(m.group(3))
        if role == "Pulser":
            mode = kv.get("mode", "periodic")
            if mode == "periodic":
                cfg = {"clock": ("periodic", int(kv["period"]),
                                 int(kv["phase"]))}
            elif mode == "once":
                cfg = {"clock": ("once", int(kv["epoch"]))}
            else:
                raise WrlValidationError(WRL_UNSUPPORTED_FEATURE,
                                         "pulser clock mode %r (only "
                                         "periodic|once)" % (mode,))
            g.nodes.append(("Pulser", name, cfg))
        elif role == "Spinner":
            cfg = {"w": int(kv["w"]) if "w" in kv else None,
                   "n": int(kv["n"]) if "n" in kv else None,
                   "rotor": _rotor_dots(kv["rotor"]) if "rotor" in kv
                   else None,
                   "configurable": ("configurable" in flags
                                    or kv.get("configurable") == "true")}
            g.nodes.append(("Spinner", name, cfg))
        elif role == MAILBOX_ROLE:
            # MailboxDecl (D7) surface form: `[mailbox:mb](w=8, cap=4){}`.
            # `w` and `cap` are REQUIRED -- but "required" is enforced by the
            # SEAL, not here. `_validate_config` already rejects a missing
            # `w`/`cap` with a located, typed diagnostic, and it does so for a
            # mailbox that arrived from ANY surface (Core text, a canvas, a
            # draft edit, a deserialized artifact). A parse-time check would be
            # a second place that decides what "required" means, and the two
            # would eventually disagree about a value like `w=0` -- which is
            # present, so a presence check passes it, and out of range, so the
            # validator does not. Absence flows through as None exactly as the
            # Spinner branch above has always done.
            cfg = {"w": int(kv["w"]) if "w" in kv else None,
                   "cap": int(kv["cap"]) if "cap" in kv else None}
            g.nodes.append((MAILBOX_ROLE, name, cfg))
        else:
            g.nodes.append((role, name, {}))
    return g


# ============================================================ graph -> IR v1
def _ports_for(role):
    return object_ports(role)


def graph_to_ir(g):
    """Canonical WRL graph -> ForgeSemanticArtifactV1 (frozen top-level form),
    the STATIC semantic artifact ONLY. Validates against the frozen registries
    (typed rejections). Objects are emitted IDENTITY-FIRST by (object_id, role)
    and edges canonically so the serialized bytes are declaration-order
    independent. Run inputs (periods / claim batches) are NOT part of this
    artifact (D3). The result is SEALED (Slice 2.1): a non-null rulepack and a
    fully validated record before it can earn a SemanticArtifactID."""
    validate_graph(g)
    objects = []
    for role, name, cfg in sorted(g.nodes, key=lambda t: (t[1], t[0])):
        objects.append({"object_id": name, "role": role,
                        "static_config": cfg,
                        "state_schema_ref": "state.%s.v1" % role.lower(),
                        "ports": _ports_for(role)})
    edges = []
    for kind, s, d in sorted(g.edges):
        edges.append({"kind": kind, "src": s, "dst": d})
    # D6/Q2: the ENTIRE semantic surface follows the ROLES PRESENT -- IR
    # revision, ADMIT policy, film schema and runtime state schema are decided
    # together by one selector so they cannot drift apart. A mailbox-free world
    # emits the frozen v1 values byte-for-byte, so every existing
    # SemanticArtifactID is preserved exactly.
    _roles = [r for r, _n, _c in g.nodes]
    surface = semantic_surface_for_roles(_roles)
    art = {
        "ir_version": surface["ir_version"],
        "profile_id": g.profile,
        "semantic_policies": {
            "rulepack_id": RULEPACK_ID,
            "numeric_policy_ids": list(NUMERIC_POLICY_IDS),
            "admit_policy_id": surface["admit_policy_id"],
            "film_schema_id": surface["film_schema_id"],
        },
        "schemas": schemas_for_roles(_roles),
        "objects": objects,
        "edges": edges,
    }
    # Canonically omitted when empty (Slice B commit 2): a route-free world
    # emits EXACTLY the pre-Slice-B key set, so its bytes -- and therefore its
    # SemanticArtifactID -- are unchanged.
    routes = WC.routes_of(g)
    if routes:
        art["async_routes"] = [dict(r) for r in
                               sorted(routes, key=WC.route_key)]
    validate_artifact_v1(art)          # seal-before-return
    return art


# ============================================================ IR v1 -> Fixture
def ir_to_fixture(art):
    """INDEPENDENT TEST ORACLE (Phase 3D): the legacy Fixture builder, retained
    only so batteries can cross-check the CompilePlanV1 against the hand-built
    Fixture. It is NOT on the production lowering/compile path -- `lower_graph`
    no longer calls it -- and the Fixture module is imported LAZILY here so that
    importing this frontend never imports Fixture (D14). Reads the STATIC
    artifact only; run inputs are threaded separately by the runner (D3)."""
    from fixture import Fixture
    if art["profile_id"] != PROFILE_ID:
        raise WrlValidationError(WRL_UNSUPPORTED_FEATURE,
                                 "adapter serves only %s" % (PROFILE_ID,))
    # COMMIT 4 LIFTED THE ROUTE REFUSAL THAT STOOD HERE.
    #
    # Through commits 2 and 3 this function refused a route-bearing artifact,
    # because a Fixture built from one would have silently dropped the routes
    # and become an oracle for a DIFFERENT world -- a cross-check that agrees
    # about the wrong thing, which is worse than none.
    #
    # Commit 4 makes the dropping correct rather than silent. A route's runtime
    # image is a CLAIM (`wrl_fold.route_claims`), not structure: it has no
    # ports, no state, no edge, and it changes nothing the Fixture models. The
    # Fixture of a route-bearing world is therefore EXACTLY the Fixture of its
    # route-free twin, and the whole difference between the two worlds now
    # lives in the observation batch, where the reducer can see it.
    #
    # That is a claim, so binding_run49 proves it rather than asserting it (the
    # EXPLICIT TWIN proof): the route-bearing world folded with its injected
    # claim must produce films byte-identical to the route-free twin folded
    # with the same claim written out by hand as a scenario claim. Note that
    # the twin is route-free, so writer 15 is legal against it -- the Q4
    # reservation is exactly what makes the twin expressible.
    pulsers, relays, doors, spinners, orbs, configurable = \
        {}, [], [], {}, [], set()
    mailboxes = {}
    for o in art["objects"]:
        role, name, cfg = o["role"], o["object_id"], o["static_config"]
        if role == "Pulser":
            pulsers[name] = tuple(cfg["clock"])          # JSON-plain -> tuple
        elif role == "Relay":
            relays.append(name)
        elif role == "Door":
            doors.append(name)
        elif role == "Spinner":
            spinners[name] = (cfg["w"], cfg["n"], tuple(cfg["rotor"]))
            if cfg.get("configurable"):
                configurable.add(name)
        elif role == "Orb":
            orbs.append(name)
        elif role == MAILBOX_ROLE:
            # MailboxDecl -> the oracle's mailbox surface. D8: a mailbox
            # contributes NO edge, so it never appears in sig_edges/sockets.
            mailboxes[name] = (cfg["w"], cfg["cap"])
    sig_edges = [(e["src"], e["dst"]) for e in art["edges"]
                 if e["kind"] == "SignalWire"]
    sockets = [(e["src"], e["dst"]) for e in art["edges"]
               if e["kind"] == "SocketControl"]
    conf = None if configurable == set(spinners) else configurable
    return Fixture(pulsers, relays, doors, sig_edges,
                   spinners=spinners, orbs=orbs, sockets=sockets,
                   configurable=conf, mailboxes=mailboxes or None)


# =============================================================== programs
def _initial_claim_state(artifact=None):
    """The initial CLAIM projection only (facts, receipts, capacity faults).
    The physical world init (clock/rotor/pose/wire) is a function of the
    Fixture, built by the runner via init_state_v6 -- this partial object is
    deliberately NOT called the full initial runtime state (Slice 2.1).

    D6: the mailbox sibling fields appear here IFF the artifact declares a
    mailbox, matching the runtime state schema the artifact declares. A
    mailbox-free program's projection is byte-identical to pre-v1.1."""
    st = {"claim_facts": [], "acceptance_receipts": [],
          "fact_capacity_fault": 0, "receipt_capacity_fault": 0}
    decls = mailbox_decls_of_artifact(artifact) if artifact else {}
    if decls:
        st["mailbox_states"] = {mb: {"inbox": [], "next_inbox": []}
                                for mb in sorted(decls)}
        st["mailbox_capacity_fault"] = 0
    return st


def lower_graph(g):
    """Canonical WRL graph -> LoweredProgram. Canonicalizes + validates, SEALS
    the semantic artifact, then separates it from the run inputs (D3). The
    single lowering seam shared by every surface (text OR canvas), so all
    surfaces converge on the same artifact bytes and run inputs (Phase 3C).
    Phase 3D: this builds NO Fixture -- the compile contract is the
    CompilePlanV1 (see `compile_program`)."""
    g = canonicalize_graph(g)
    art = graph_to_ir(g)
    sealed = WC.SealedArtifact(art)
    run_plan = {"periods": g.periods, "epoch0": 1}
    epoch_inputs = [{"claim_batch": list(batch)} for batch in g.batches]
    return LoweredProgram(sealed, sealed.semantic_id,
                          _initial_claim_state(art),
                          run_plan, epoch_inputs, g)


def lower_program(text, parser=parse_wrl_bootstrap):
    """WRL text -> LoweredProgram. `parser` selects the surface; both surfaces
    lower through the shared `lower_graph` seam (D3)."""
    return lower_graph(parser(text))


def compile_program(program, lowering_profile):
    """LoweredProgram + lowering profile -> CompiledProgram (CompilePlanV1 +
    ic term + BackendArtifactID), through the EXISTING compiler machinery. The
    import is lazy so the pure lowering frontend pulls in neither the compiler
    nor the Fixture (Phase 3D)."""
    import wrl_plan
    return wrl_plan.compile_artifact(program.sealed_artifact, lowering_profile)


def lower_wrl(text, parser=parse_wrl_bootstrap):
    """Back-compat front-half: WRL text -> (Fixture oracle, static artifact,
    graph). The Fixture here is the independent test oracle, not a production
    lowering product (Phase 3D)."""
    p = lower_program(text, parser)
    return p.fixture, p.artifact, p.graph
