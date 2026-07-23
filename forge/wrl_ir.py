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
    NUMERIC_POLICY_IDS, SCHEMA_IDS,
    ROLE_IDS, EDGE_KINDS, PORTS,
    WrlUnsupported, WrlValidationError,
    WRL_UNSUPPORTED_FEATURE, WRL_EPOCH_RANGE, WRL_NUMERIC_RANGE,
    validate_graph, canonicalize_graph, validate_port_projection, object_ports,
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


_ROLE_TOKEN = {"pulser": "Pulser", "relay": "Relay", "door": "Door",
               "spinner": "Spinner", "orb": "Orb"}
_EDGE_TAG = {"sig": "SignalWire", "socket": "SocketControl"}


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
        elif head in ("mailbox", "gate", "seal", "supervisor", "fragment",
                      "stencil", "derive", "capability"):
            raise WrlValidationError(WRL_UNSUPPORTED_FEATURE,
                                     "%r is outside Forge Semantic IR v1 "
                                     "(profile %s); reserved/Proposed"
                                     % (head, PROFILE_ID))
        elif "~~" in line or "!!" in line or "==" in line:
            raise WrlValidationError(WRL_UNSUPPORTED_FEATURE,
                                     "route texture in %r: async ~~ / fault "
                                     "!! / verified == are transition classes,"
                                     " not IR v1 edges" % (line,))
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


def parse_wrl_core(text):
    """WRL process notation -> canonical WRL graph. Node:
    `[role:name](k=v, ...){ports}`; edge: `[a] --tag--> [b]`; claim:
    `[epoch:N] @w,s Op args`. Lowers to the SAME canonical graph as the
    bootstrap surface (two-surface equivalence).

    Lexical law (Slice 2.1): comments are `;` (full-line or inline) because
    slash/`#` forms are reserved -- `#` is preserved for content identity and
    tags and is NEVER treated as a comment marker here. A `{ports}` brace group
    is a CHECKED projection of the role's frozen ports, not decoration."""
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
            raise WrlValidationError(WRL_UNSUPPORTED_FEATURE,
                                     "role %r not in the frozen v1 registry"
                                     % (rtok,))
        role = _ROLE_TOKEN[rtok]
        if m.group(4) is not None:            # visible ports are checked, not ignored
            validate_port_projection(role, _ports_set(m.group(4)))
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
    art = {
        "ir_version": IR_VERSION,
        "profile_id": g.profile,
        "semantic_policies": {
            "rulepack_id": RULEPACK_ID,
            "numeric_policy_ids": list(NUMERIC_POLICY_IDS),
            "admit_policy_id": ADMIT_POLICY_ID,
            "film_schema_id": FILM_SCHEMA_ID,
        },
        "schemas": dict(SCHEMA_IDS),
        "objects": objects,
        "edges": edges,
    }
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
    pulsers, relays, doors, spinners, orbs, configurable = \
        {}, [], [], {}, [], set()
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
    sig_edges = [(e["src"], e["dst"]) for e in art["edges"]
                 if e["kind"] == "SignalWire"]
    sockets = [(e["src"], e["dst"]) for e in art["edges"]
               if e["kind"] == "SocketControl"]
    conf = None if configurable == set(spinners) else configurable
    return Fixture(pulsers, relays, doors, sig_edges,
                   spinners=spinners, orbs=orbs, sockets=sockets,
                   configurable=conf)


# =============================================================== programs
def _initial_claim_state():
    """The initial CLAIM projection only (facts, receipts, capacity faults).
    The physical world init (clock/rotor/pose/wire) is a function of the
    Fixture, built by the runner via init_state_v6 -- this partial object is
    deliberately NOT called the full initial runtime state (Slice 2.1)."""
    return {"claim_facts": [], "acceptance_receipts": [],
            "fact_capacity_fault": 0, "receipt_capacity_fault": 0}


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
    return LoweredProgram(sealed, sealed.semantic_id, _initial_claim_state(),
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
