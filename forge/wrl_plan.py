"""wrl_plan.py v0.3 -- CompilePlanV1 + SealedCompilePlanV1: the deterministic,
representation-NEUTRAL compile plan and its cryptographic binding (Phase 3D.1),
hardened for sealed-object integrity (Phase 3D.1.1): the sealed plan stores
CANONICAL BYTES, is immutable, and the compile boundary rejects counterfeits and
re-verifies plan/semantic integrity from the bytes.

GPT-5.6's Phase 3D ruling extracted a deterministic `CompilePlanV1` consumed by
the EXISTING backend machinery; both the frozen Forge IR and the legacy Fixture
produce that SAME plan, fed to `compile_step_v6` through a NON-TEST shim so the
plan -- not the Fixture -- is the production lowering contract.

GPT-5.6's Phase 3D.1 correction (Backend Identity Closure) tightened four things:

  A. The lowering profile is now OPERATIVE. `_PlanView(plan, profile)` drives the
     counter representation from the profile (`counter_encoding` +
     `onehot_max`, via `lowering_policy.counter_spec_for`), so forcing one-hot
     vs binary yields DIFFERENT backend terms but IDENTICAL films.

  B. CompilePlanV1 carries NO representation. Its three signatures fingerprint the
     SEMANTIC counter SHAPE (the clock), never onehot/binp/width. The
     representation-full fingerprint is the `backend_layout_signature`, computed
     at COMPILE time from the profile-driven view, together with a
     `backend_content_hash` of the emitted term -- both live on the
     CompiledProgram, never in the plan.

  C. Production compiles only a `SealedCompilePlanV1`: sealing recomputes the
     three neutral signatures, reconstructs the Forge IR from the plan and
     recomputes the SemanticArtifactID to prove the plan is BOUND to its
     semantic artifact, checks the canonical ordering / object_index bijection /
     exact key set, and isolates a frozen deep copy so later mutation of a raw
     plan cannot affect an issued compilation.

  D. The onehot/binp THRESHOLD moved out of `fixture.py` into `lowering_policy`,
     so the production compile path imports neither `fixture` nor its constant.

Identity law (GPT-5.6):
  * SemanticArtifactID  -- moves iff the semantic graph moves;
  * CompilePlanDigest   -- test-only; moves iff the plan moves (== semantic);
  * BackendArtifactID   -- moves iff the SemanticArtifactID OR lowering profile
                           moves (a different counter_encoding/onehot_max moves
                           it while leaving the SemanticArtifactID fixed).
"""
import os
import re
import sys
from collections import namedtuple

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
sys.path.insert(0, os.path.join(_HERE, "..", "runtime", "python"))
sys.path.insert(0, os.path.join(_HERE, "..", "research"))
import wrl_canonical as WC
import compiler as C
from lowering_policy import counter_spec_for, DEFAULT_ONEHOT_MAX   # NOT fixture

COMPILE_PLAN_VERSION = "compileplan.v1"

WRL_BAD_COMPILE_PLAN = "WRL_BAD_COMPILE_PLAN"

# The production compile result. It carries the SEALED plan (not the raw plan),
# the BackendArtifactID, and the two COMPILE-TIME backend fingerprints that DO
# depend on the representation the profile selected. The plan itself stays
# representation-neutral (Phase 3D.1-B).
CompiledProgram = namedtuple(
    "CompiledProgram",
    "sealed_plan backend_artifact_id backend_layout_signature "
    "backend_content_hash ic_term fields")


# ===================================================================
# _PlanView -- the NON-TEST compiler shim, now PROFILE-AWARE (3D.1-A).
#
# It duck-types the exact read interface `compile_step_v6`, `enc_state_v6`,
# `dec_state_v6`, `enc_config_bundle`, `state_to_film_args_v6` and `init_state_v6`
# consume from a Fixture, reconstructed from a CompilePlanV1. It is NOT the
# Fixture class (so the Fixture stays an independent oracle) and it performs NO
# construction-time validation or model building. The ONLY policy it applies is
# the counter representation, which it now reads from the lowering profile via
# the shared `lowering_policy` module -- when no profile is supplied it uses the
# canonical `auto` / DEFAULT_ONEHOT_MAX rule, matching the Fixture oracle.
# ===================================================================
class _PlanView:
    __slots__ = ("pulsers", "spinners", "orbs", "relays", "doors",
                 "edges", "sockets", "_conf", "_encoding", "_onehot_max")

    def __init__(self, plan, profile=None):
        self.pulsers = {p["id"]: tuple(p["clock"]) for p in plan["pulsers"]}
        self.spinners = {s["id"]: (s["w"], s["n"], tuple(s["rotor"]))
                         for s in plan["spinners"]}
        self._conf = {s["id"]: bool(s["configurable"])
                      for s in plan["spinners"]}
        self.orbs = list(plan["orbs"])
        self.relays = list(plan["relays"])
        self.doors = list(plan["doors"])
        self.edges = [tuple(e) for e in plan["signal_edges"]]
        self.sockets = [tuple(x) for x in plan["socket_controls"]]
        if profile is None:
            self._encoding = "auto"
            self._onehot_max = DEFAULT_ONEHOT_MAX
        else:
            self._encoding = profile["counter_encoding"]
            self._onehot_max = profile["onehot_max"]

    def kinds(self):
        k = {r: "pulser" for r in self.pulsers}
        k.update({r: "relay" for r in self.relays})
        k.update({r: "door" for r in self.doors})
        k.update({r: "spinner" for r in self.spinners})
        k.update({r: "orb" for r in self.orbs})
        return k

    def controller_of(self, orb):
        for (s, o) in self.sockets:
            if o == orb:
                return s
        return ""

    def orb_of(self, spinner):
        for (s, o) in self.sockets:
            if s == spinner:
                return o
        return ""

    def is_configurable(self, spinner):
        return self._conf.get(spinner, True)

    def wire_role(self, s, d):
        return "w__%s__%s" % (s, d)

    def wires(self):
        return sorted(self.wire_role(s, d) for s, d in self.edges)

    def layout(self):
        return (sorted(self.pulsers), self.wires(), self.doors, self.relays)

    def counter_spec(self, role):
        """The compiler's counter_spec -- the ONLY place representation is
        chosen, now driven by the lowering profile via the shared policy."""
        return counter_spec_for(self.pulsers[role], self._encoding,
                                self._onehot_max)

    def in_wires(self, role):
        return sorted(self.wire_role(s, d) for s, d in self.edges
                      if d == role)

    def out_wires(self, role):
        return sorted(self.wire_role(s, d) for s, d in self.edges
                      if s == role)


# ===================================================================
# Deterministic, representation-NEUTRAL signatures (Phase 3D.1-B). They
# fingerprint the SEMANTIC counter SHAPE -- the clock tuple itself, never the
# onehot/binp/width the backend later chooses -- so a lowering-profile change
# leaves every plan signature (and thus the CompilePlanDigest) fixed while any
# semantic change moves them.
# ===================================================================
def _state_layout_signature(view):
    ppl, wires, doors, relays = view.layout()
    layout = []
    for r in ppl:
        layout.append(["counter", r, list(view.pulsers[r])])   # NEUTRAL clock
    for f in wires:
        layout.append(["wire", f])
    for f in doors:
        layout.append(["door", f])
    for f in relays:
        layout.append(["relay", f])
    for o in view.orbs:
        s = view.controller_of(o)
        w_ = view.spinners[s][0] if s else 8
        layout.append(["pose", o, w_])
        layout.append(["fault", o])
    for o in view.orbs:
        s = view.controller_of(o)
        if not s:
            continue
        layout.append(["rotor", s, view.spinners[s][0]])
    return "slay-" + WC._sha(WC.serialize_artifact(layout))


def _epoch_input_signature(view):
    ctrl = [view.controller_of(o) for o in view.orbs if view.controller_of(o)]
    rbundle = [[s, view.spinners[s][0]] for s in ctrl]
    fbundle = list(view.orbs)
    return "epin-" + WC._sha(WC.serialize_artifact([rbundle, fbundle]))


def _observable_signature(view):
    obs = []
    for r in sorted(view.pulsers):
        obs.append(["pulser", r, view.pulsers[r][0]])
    for r in view.doors:
        obs.append(["door", r])
    for r in view.relays:
        obs.append(["relay", r])
    for wr in view.wires():
        obs.append(["wire", wr])
    for s in sorted(view.spinners):
        w_, n_, _ = view.spinners[s]
        obs.append(["spinner", s, w_, n_, view.orb_of(s),
                    "configurable" if view.is_configurable(s) else "fixed"])
    for o in view.orbs:
        s = view.controller_of(o)
        w_ = view.spinners[s][0] if s else 8
        n_ = view.spinners[s][1] if s else 4
        obs.append(["orb", o, w_, n_, s])
    return "obsv-" + WC._sha(WC.serialize_artifact(obs))


# ===================================================================
# The COMPILE-TIME backend fingerprints (Phase 3D.1-B). Unlike the three plan
# signatures above, these DO carry the representation the profile selected, so
# forcing one-hot vs binary moves them while leaving the plan (and its digest)
# untouched. They are attached to the CompiledProgram, never to the plan.
# ===================================================================
def backend_layout_signature(view):
    """The representation-FULL encoded-state layout, from the profile-driven
    counter_spec. Moves with the counter_encoding/onehot_max the profile picks;
    it is NOT part of the plan and NOT part of the SemanticArtifactID."""
    ppl, wires, doors, relays = view.layout()
    layout = []
    for r in ppl:
        layout.append(["counter", r, list(view.counter_spec(r))])  # FULL spec
    for f in wires:
        layout.append(["wire", f])
    for f in doors:
        layout.append(["door", f])
    for f in relays:
        layout.append(["relay", f])
    for o in view.orbs:
        s = view.controller_of(o)
        w_ = view.spinners[s][0] if s else 8
        layout.append(["pose", o, w_])
        layout.append(["fault", o])
    for o in view.orbs:
        s = view.controller_of(o)
        if not s:
            continue
        layout.append(["rotor", s, view.spinners[s][0]])
    return "blay-" + WC._sha(WC.serialize_artifact(layout))


# The compiler emits the step function as a lambda-term STRING whose bound
# variable names and interaction-net DUP labels carry a monotonic gensym suffix
# (`ec84176`, `&32983`, ...) that differs between two otherwise-identical
# compiles. Those suffixes are alpha-detail, not backend content, so the content
# hash canonicalizes them first: every generated identifier and `&`-label is
# renamed to a first-occurrence-ordered slot. This leaves BARE integer literals
# (semantic constants like a period) untouched, is stable across compiles of the
# same artifact+profile (D26), and still differs when the representation (and
# hence the term STRUCTURE) differs (D16).
_TERM_TOKEN = re.compile(r"&\d+|[A-Za-z_][A-Za-z_0-9]*")


def _canonicalize_term(term):
    mapping = {}

    def _repl(m):
        tok = m.group(0)
        slot = mapping.get(tok)
        if slot is None:
            slot = ("&%d" if tok[0] == "&" else "$%d") % len(mapping)
            mapping[tok] = slot
        return slot

    return _TERM_TOKEN.sub(_repl, term)


def _backend_content_hash(step, fields):
    """A deterministic digest of the ACTUAL emitted backend term + fields. The
    term string is alpha-canonicalized (gensym suffixes + DUP labels normalized)
    so the same artifact+profile reproduce an identical hash (D26) while a forced
    one-hot vs binary lowering -- which changes the term STRUCTURE -- hashes
    differently (D16)."""
    body = [_canonicalize_term(step), list(fields)]
    return "bcnt-" + WC._sha(WC.serialize_artifact(body))


# ===================================================================
# The single canonical plan builder. Both entry points normalize their
# source into these parts and call it, so the two plans are BYTE-identical.
# ===================================================================
def _plan_from_parts(sem_id, profile_id, semantic_policies, pulsers, relays,
                     doors, spinners, orbs, sig_edges, sockets, conf):
    """pulsers: {id: clock-tuple}; spinners: {id: (w, n, rotor-tuple)};
    conf: {spinner_id: bool}; relays/doors/orbs: [id]; sig_edges/sockets:
    [(src, dst)]. Everything is canonicalized (sorted) so declaration order
    cannot leak into the plan."""
    order = sorted(list(pulsers) + list(relays) + list(doors)
                   + list(spinners) + list(orbs))
    plan = {
        "compile_plan_version": COMPILE_PLAN_VERSION,
        "semantic_artifact_id": sem_id,
        "profile_id": profile_id,
        "rulepack_id": semantic_policies["rulepack_id"],
        "numeric_policy_ids": sorted(semantic_policies["numeric_policy_ids"]),
        "admit_policy_id": semantic_policies["admit_policy_id"],
        "film_schema_id": semantic_policies["film_schema_id"],
        "object_order": order,
        "object_index": {oid: i for i, oid in enumerate(order)},
        "pulsers": [{"id": r, "clock": list(pulsers[r])}
                    for r in sorted(pulsers)],
        "relays": sorted(relays),
        "doors": sorted(doors),
        "spinners": [{"id": s, "w": spinners[s][0], "n": spinners[s][1],
                      "rotor": list(spinners[s][2]),
                      "configurable": bool(conf.get(s, True))}
                     for s in sorted(spinners)],
        "orbs": sorted(orbs),
        "signal_edges": sorted([list(e) for e in sig_edges]),
        "socket_controls": sorted([list(x) for x in sockets]),
    }
    view = _PlanView(plan)                 # neutral (no profile) for signatures
    plan["state_layout_signature"] = _state_layout_signature(view)
    plan["epoch_input_signature"] = _epoch_input_signature(view)
    plan["observable_signature"] = _observable_signature(view)
    return plan


# ------------------------------------------------------ IR -> CompilePlanV1
def artifact_to_compile_plan_v1(artifact):
    """Forge Semantic IR (a SealedArtifact or a raw/reordered artifact dict)
    -> CompilePlanV1. The artifact is canonicalized first, so a reorder-
    equivalent artifact yields a byte-identical plan (3D-1 D2)."""
    if isinstance(artifact, WC.SealedArtifact):
        sem_id = artifact.semantic_id
        art = artifact.artifact
    else:
        sem_id = WC.semantic_artifact_id(artifact)
        art = WC.canonicalize_artifact_v1(artifact)
    pulsers, relays, doors, spinners, orbs, conf = {}, [], [], {}, [], {}
    for o in art["objects"]:
        role, name, cfg = o["role"], o["object_id"], o["static_config"]
        if role == "Pulser":
            pulsers[name] = tuple(cfg["clock"])
        elif role == "Relay":
            relays.append(name)
        elif role == "Door":
            doors.append(name)
        elif role == "Spinner":
            spinners[name] = (cfg["w"], cfg["n"], tuple(cfg["rotor"]))
            conf[name] = bool(cfg.get("configurable"))
        elif role == "Orb":
            orbs.append(name)
    sig_edges = [(e["src"], e["dst"]) for e in art["edges"]
                 if e["kind"] == "SignalWire"]
    sockets = [(e["src"], e["dst"]) for e in art["edges"]
               if e["kind"] == "SocketControl"]
    return _plan_from_parts(sem_id, art["profile_id"],
                            art["semantic_policies"], pulsers, relays, doors,
                            spinners, orbs, sig_edges, sockets, conf)


# ------------------------------------------------- Fixture -> CompilePlanV1
def fixture_to_compile_plan_v1(fx, sem_id, semantic_policies=None,
                               profile_id=None):
    """Fixture (the independent test oracle) -> CompilePlanV1, IDENTICAL to the
    plan the frozen IR produces for the same world (3D-1 D1). The Fixture does
    not itself carry the semantic id or policy bundle, so they are supplied by
    the caller (the sealed artifact's own values), keeping the Fixture a pure
    structural builder."""
    semantic_policies = semantic_policies or {
        "rulepack_id": WC.RULEPACK_ID,
        "numeric_policy_ids": list(WC.NUMERIC_POLICY_IDS),
        "admit_policy_id": WC.ADMIT_POLICY_ID,
        "film_schema_id": WC.FILM_SCHEMA_ID,
    }
    profile_id = profile_id or WC.PROFILE_ID
    pulsers = {r: tuple(spec) for r, spec in fx.pulsers.items()}
    spinners = {s: (w_, n_, tuple(rq))
                for s, (w_, n_, rq) in fx.spinners.items()}
    conf = {s: fx.is_configurable(s) for s in fx.spinners}
    return _plan_from_parts(sem_id, profile_id, semantic_policies, pulsers,
                            list(fx.relays), list(fx.doors), spinners,
                            list(fx.orbs), list(fx.edges), list(fx.sockets),
                            conf)


# ----------------------------------------------- plan -> Forge IR (binding)
def _plan_to_artifact(plan):
    """Reconstruct the frozen Forge Semantic IR artifact from a CompilePlanV1,
    so its SemanticArtifactID can be recomputed and compared against the id the
    plan claims (Phase 3D.1-C / D22). The reconstruction mirrors `graph_to_ir`
    exactly (identity-first objects with frozen schema refs + ports, canonical
    edges); `WC.semantic_artifact_id` then re-canonicalizes and hashes it, so a
    plan whose body was tampered but whose stored id was not gets rejected."""
    objects = []
    for name in plan["object_order"]:
        if name in {p["id"] for p in plan["pulsers"]}:
            role = "Pulser"
            clock = next(p["clock"] for p in plan["pulsers"] if p["id"] == name)
            cfg = {"clock": list(clock)}
        elif name in set(plan["relays"]):
            role, cfg = "Relay", {}
        elif name in set(plan["doors"]):
            role, cfg = "Door", {}
        elif name in {s["id"] for s in plan["spinners"]}:
            role = "Spinner"
            sp = next(s for s in plan["spinners"] if s["id"] == name)
            cfg = {"w": sp["w"], "n": sp["n"], "rotor": list(sp["rotor"]),
                   "configurable": bool(sp["configurable"])}
        elif name in set(plan["orbs"]):
            role, cfg = "Orb", {}
        else:
            WC._fail(WRL_BAD_COMPILE_PLAN,
                     "object %r in object_order is not a declared object"
                     % (name,))
        objects.append({"object_id": name, "role": role,
                        "static_config": cfg,
                        "state_schema_ref": "state.%s.v1" % role.lower(),
                        "ports": WC.object_ports(role)})
    edges = [{"kind": "SignalWire", "src": s, "dst": d}
             for s, d in plan["signal_edges"]]
    edges += [{"kind": "SocketControl", "src": s, "dst": d}
              for s, d in plan["socket_controls"]]
    return {
        "ir_version": WC.IR_VERSION,
        "profile_id": plan["profile_id"],
        "semantic_policies": {
            "rulepack_id": plan["rulepack_id"],
            "numeric_policy_ids": list(plan["numeric_policy_ids"]),
            "admit_policy_id": plan["admit_policy_id"],
            "film_schema_id": plan["film_schema_id"],
        },
        "schemas": dict(WC.SCHEMA_IDS),
        "objects": objects,
        "edges": edges,
    }


# --------------------------------------------------------- plan validation
_PLAN_KEYS = ("compile_plan_version", "semantic_artifact_id", "profile_id",
              "rulepack_id", "numeric_policy_ids", "admit_policy_id",
              "film_schema_id", "object_order", "object_index", "pulsers",
              "relays", "doors", "spinners", "orbs", "signal_edges",
              "socket_controls", "state_layout_signature",
              "epoch_input_signature", "observable_signature")
_PLAN_KEY_SET = frozenset(_PLAN_KEYS)


def validate_compile_plan_v1(plan):
    """Structural gate for a CompilePlanV1: version, EXACT key set (no unknown
    fields), well-formed semantic id, canonical object_order + object_index
    bijection, and that every declared edge/socket endpoint is a declared
    object. Raises a typed WrlValidationError(WRL_BAD_COMPILE_PLAN). Returns the
    plan on success."""
    if not isinstance(plan, dict):
        WC._fail(WRL_BAD_COMPILE_PLAN, "compile plan must be an object")
    if plan.get("compile_plan_version") != COMPILE_PLAN_VERSION:
        WC._fail(WRL_BAD_COMPILE_PLAN,
                 "unknown compile plan version %r (only %s)"
                 % (plan.get("compile_plan_version"), COMPILE_PLAN_VERSION))
    missing = [k for k in _PLAN_KEYS if k not in plan]
    if missing:
        WC._fail(WRL_BAD_COMPILE_PLAN,
                 "compile plan missing field(s) %s" % missing)
    extra = [k for k in plan if k not in _PLAN_KEY_SET]
    if extra:
        WC._fail(WRL_BAD_COMPILE_PLAN,
                 "compile plan has unknown field(s) %s" % sorted(extra))
    if not WC._SEM_ID_RE.match(plan["semantic_artifact_id"] or ""):
        WC._fail(WRL_BAD_COMPILE_PLAN,
                 "bad semantic_artifact_id %r" % (plan["semantic_artifact_id"],))
    ids = ([p["id"] for p in plan["pulsers"]] + list(plan["relays"])
           + list(plan["doors"]) + [s["id"] for s in plan["spinners"]]
           + list(plan["orbs"]))
    if plan["object_order"] != sorted(ids):
        WC._fail(WRL_BAD_COMPILE_PLAN,
                 "object_order is not the canonical sort of the declared "
                 "objects")
    if plan["object_index"] != {oid: i
                                for i, oid in enumerate(plan["object_order"])}:
        WC._fail(WRL_BAD_COMPILE_PLAN,
                 "object_index is not the object_order bijection")
    order = set(plan["object_order"])
    for src, dst in plan["signal_edges"]:
        if src not in order or dst not in order:
            WC._fail(WRL_BAD_COMPILE_PLAN,
                     "signal edge (%s -> %s) references an undeclared object"
                     % (src, dst))
    for s, o in plan["socket_controls"]:
        if s not in order or o not in order:
            WC._fail(WRL_BAD_COMPILE_PLAN,
                     "socket (%s -> %s) references an undeclared object"
                     % (s, o))
    return plan


def compile_plan_digest(plan):
    """TEST-ONLY canonical plan hash. Not a runtime id: it must move iff the
    plan (== the semantic graph) moves, and stay fixed under presentation-only
    edits AND under lowering-profile changes (the plan is now representation-
    neutral), so a battery can pin plan/semantic co-movement."""
    validate_compile_plan_v1(plan)
    return "plan-" + WC._sha(WC.serialize_artifact(plan))


# ===================================================================
# SealedCompilePlanV1 -- the plan cryptographically BOUND to its semantic
# artifact and isolated from mutation (Phase 3D.1-C). Production compiles ONLY a
# sealed plan.
# ===================================================================
class SealedCompilePlanV1:
    """A CompilePlanV1 that has passed sealing: its three neutral signatures
    recompute, its reconstructed Forge IR re-hashes to the SemanticArtifactID it
    claims, and its canonical ordering / object_index bijection / key set are
    exact.

    Phase 3D.1.1 -- SEALED OBJECT INTEGRITY. The seal stores the CANONICAL BYTES
    of the plan, not a mutable dictionary. `.canonical_plan` deserializes a FRESH
    isolated copy on every read (mutating it can never touch the seal, D31); the
    SemanticArtifactID and CompilePlanDigest are DERIVED at construction and are
    exposed as read-only properties. The object is immutable: any attribute
    assignment or deletion raises WRL_SEALED_IMMUTABLE (D32)."""
    __slots__ = ("_canonical_bytes", "_semantic_artifact_id",
                 "_compile_plan_digest")

    def __init__(self, canonical_plan, semantic_artifact_id,
                 compile_plan_digest):
        object.__setattr__(self, "_canonical_bytes",
                           WC.serialize_artifact(canonical_plan))
        object.__setattr__(self, "_semantic_artifact_id", semantic_artifact_id)
        object.__setattr__(self, "_compile_plan_digest", compile_plan_digest)

    def __setattr__(self, name, value):
        WC._fail(WC.WRL_SEALED_IMMUTABLE,
                 "SealedCompilePlanV1 is immutable; cannot assign %r" % (name,))

    def __delattr__(self, name):
        WC._fail(WC.WRL_SEALED_IMMUTABLE,
                 "SealedCompilePlanV1 is immutable; cannot delete %r" % (name,))

    @property
    def canonical_bytes(self):
        """The frozen canonical serialization the CompilePlanDigest is over."""
        return self._canonical_bytes

    @property
    def canonical_plan(self):
        """A FRESH isolated copy of the canonical plan on every read (D31)."""
        return WC.deserialize_artifact(self._canonical_bytes)

    @property
    def semantic_artifact_id(self):
        return self._semantic_artifact_id

    @property
    def compile_plan_digest(self):
        return self._compile_plan_digest


def seal_compile_plan(plan, sealed_artifact=None):
    """CompilePlanV1 -> SealedCompilePlanV1. Verifies (a) structure + canonical
    ordering + object_index bijection + exact key set (`validate_compile_plan_v1`),
    (b) the three neutral signatures recompute from the plan (D23), (c) the Forge
    IR reconstructed from the plan re-hashes to the claimed SemanticArtifactID so
    the plan is BOUND to its semantic artifact (D22), and (d) -- when a
    SealedArtifact is supplied -- that the plan actually ORIGINATES from it. On
    success it stores a frozen, isolated deep copy (D21)."""
    validate_compile_plan_v1(plan)
    view = _PlanView(plan)                              # neutral view
    recomputed = {
        "state_layout_signature": _state_layout_signature(view),
        "epoch_input_signature": _epoch_input_signature(view),
        "observable_signature": _observable_signature(view),
    }
    for key, val in recomputed.items():
        if plan.get(key) != val:
            WC._fail(WRL_BAD_COMPILE_PLAN,
                     "stale %s (plan %r != recomputed %r)"
                     % (key, plan.get(key), val))
    sem = WC.semantic_artifact_id(_plan_to_artifact(plan))
    if sem != plan["semantic_artifact_id"]:
        WC._fail(WRL_BAD_COMPILE_PLAN,
                 "plan is not bound to its semantic artifact "
                 "(claims %r, reconstructs to %r)"
                 % (plan["semantic_artifact_id"], sem))
    if sealed_artifact is not None and sealed_artifact.semantic_id != sem:
        WC._fail(WRL_BAD_COMPILE_PLAN,
                 "plan does not originate from the supplied sealed artifact "
                 "(%r != %r)" % (sem, sealed_artifact.semantic_id))
    canon = WC._plain(plan)
    return SealedCompilePlanV1(canon, sem, compile_plan_digest(canon))


# ------------------------------------------- sealed plan -> IC + backend ids
def compile_sealed_plan(sealed_plan, lowering_profile):
    """SealedCompilePlanV1 + lowering profile -> CompiledProgram. The plan is
    already bound to its semantic artifact; the profile now OPERATIVELY selects
    the counter representation (via the profile-aware `_PlanView`), so two
    profiles that force one-hot vs binary produce different backend terms and
    different backend fingerprints but the SAME SemanticArtifactID and film.

    Phase 3D.1.1 -- the compilation boundary does NOT trust that the argument was
    'sealed earlier'. It (a) rejects anything that is not EXACTLY a
    SealedCompilePlanV1 (a counterfeit sealed-plan-shaped object, D33), and (b)
    re-verifies the seal's own integrity from its canonical bytes: the bytes must
    still hash to the claimed CompilePlanDigest AND the plan reconstructed from
    them must still re-hash to the claimed SemanticArtifactID -- so tampered
    canonical bytes fail here rather than silently compiling a counterfeit
    semantic id into a BackendArtifactID (D34)."""
    if not isinstance(sealed_plan, SealedCompilePlanV1):
        WC._fail(WRL_BAD_COMPILE_PLAN,
                 "compile requires a SealedCompilePlanV1, got %r"
                 % (type(sealed_plan).__name__,))
    WC.validate_lowering_profile_v1(lowering_profile)
    plan = sealed_plan.canonical_plan                  # fresh isolated copy
    if compile_plan_digest(plan) != sealed_plan.compile_plan_digest:
        WC._fail(WRL_BAD_COMPILE_PLAN,
                 "sealed plan integrity failure: canonical bytes do not hash to "
                 "the sealed CompilePlanDigest (tampered plan body)")
    sem = WC.semantic_artifact_id(_plan_to_artifact(plan))
    if sem != sealed_plan.semantic_artifact_id:
        WC._fail(WRL_BAD_COMPILE_PLAN,
                 "sealed plan integrity failure: reconstructed semantic id %r != "
                 "sealed SemanticArtifactID %r"
                 % (sem, sealed_plan.semantic_artifact_id))
    view = _PlanView(plan, lowering_profile)
    step, fields = C.compile_step_v6(view)
    blay = backend_layout_signature(view)
    bcnt = _backend_content_hash(step, fields)
    bknd = WC.backend_artifact_id(sealed_plan.semantic_artifact_id,
                                  lowering_profile)
    return CompiledProgram(sealed_plan, bknd, blay, bcnt, step, fields)


def plan_view(plan, lowering_profile=None):
    """Expose the (optionally profile-driven) compiler view of a plan for the
    state/film helpers that take a Fixture-shaped object (init_state_v6,
    enc_state_v6, dec_state_v6, enc_config_bundle, state_to_film_args_v6). With
    no profile it uses the canonical `auto` rule, matching the Fixture oracle."""
    validate_compile_plan_v1(plan)
    return _PlanView(plan, lowering_profile)


def compile_artifact(sealed_artifact, lowering_profile):
    """Production compile path (Phase 3D.1): a SEALED Forge IR artifact +
    lowering profile -> CompiledProgram. Derives the CompilePlanV1, SEALS it
    (binding it to the semantic artifact), then compiles ONLY the sealed plan.
    No Fixture is constructed and no `fixture` symbol is imported on this path."""
    if not isinstance(sealed_artifact, WC.SealedArtifact):
        WC._fail(WRL_BAD_COMPILE_PLAN,
                 "production compile requires a SealedArtifact, got %r"
                 % (type(sealed_artifact).__name__,))
    plan = artifact_to_compile_plan_v1(sealed_artifact)
    sealed_plan = seal_compile_plan(plan, sealed_artifact)
    return compile_sealed_plan(sealed_plan, lowering_profile)
