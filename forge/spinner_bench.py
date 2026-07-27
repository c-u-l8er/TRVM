#!/usr/bin/env python3
"""Spinner Bench v0.7.0-alpha.1 -- a local six-panel web application backed by the
REAL WRL -> IR -> CompilePlan -> TRVM pipeline (GPT-5.6's Phase 3B follow-on).

v0.6.5 (release closure) extracts the production runtime + state adapters out of
the test batteries and the Fixture oracle: the normal Run path now imports
`forge_runtime` (ref_reduce / native_reduce over ic_ref / ic32) and
`forge_state` (init_state_v6 / state_to_film_args_v6) and imports NO
`binding_run*` module and NO Fixture. The Fixture is loaded LAZILY only for the
optional Verify-Oracle cross-check. Behavior is byte-identical to v0.6-4.

v0.6.5.1 (read-only installation closure) keeps EVERY write out of the extracted
release: the native reducer is compiled into an external runtime cache (passed in
via TRVM_IC32_PATH) and Python bytecode is redirected to an external
PYTHONPYCACHEPREFIX -- both set by the launcher. No identity/runtime change.

v0.7.0-alpha.1 (guided first run + alpha version cut) is a product-facing UI/UX
milestone: a first-run landing surface, a dismissible guided-demo rail, two
progressive-disclosure workspace views (Author / Evidence), and read-only Golden
Demo exploration with an explicit "make an editable copy" path. ALL of it lives in
the frontend + browser localStorage; the server gains NO new semantic profile, IR
version, artifact identity, actor role or runtime law. Every fold stays
byte-identical to v0.6-4 -- the demo still seals to DEMO_WORLD_SEMANTIC_ID.

Six panels (see spinner_bench.html):
  1. Canvas       -- the world graph (roles + typed edges), read from the sealed
                     Forge artifact objects/edges.
  2. WRL editor   -- sugar text with format / completion / diagnostics, all served
                     by the untouched wrl_format / wrl_complete / wrl_diagnostics
                     modules (never enters any identity).
  3. World disc   -- the 2D circuit state per epoch: spinner rotor, orb pose,
                     orb fault latch, folded through the compiled step.
  4. Film+id      -- the SemanticArtifactID (sealed, geometry-dependent), the
                     per-epoch Film v0.7 hash, and the named-rotor build
                     PROVENANCE (forge_named_rotor_rne_sym_v1) shown clearly
                     SEPARATED from the sealed id (it never enters the bytes).
  5. SemanticDiff -- the SEALED structural diff (wrl_diff.semantic_diff) between
                     the editor source and an editable variant, surfacing the
                     bridge law is_empty() <=> sem_id(a)==sem_id(b) LIVE. Falls
                     back to the TOLERANT draft_diff (no identity claim) when a
                     side is invalid/unsupported. Pure sidecar; touches no id.
  6. Scenario author -- the editable ScenarioV1 (initial runtime + per-epoch
                     inputs) whose ScenarioDigest is a RUN INPUT, never part of
                     the SemanticArtifactID; drives /api/run + /api/verify.

Every /api/run epoch is the ic_ref reducer (forge_runtime.ref_reduce). /api/verify
re-folds the SAME script through the native ic32 reducer (forge_runtime.native_reduce)
and asserts world+film parity, exactly like the forge batteries. It is gated by
TRVM_SKIP_NATIVE=1 (then verify reports ref-only). With oracle=true /api/verify
ALSO cross-checks the plan/view films against the independent Fixture oracle.

Preflight (GPT-5.6, pre-scenario-authoring): the normal run path lowers through
the CompilePlan VIEW and NEVER reconstructs a Fixture; the initial fault seed is
an EXPLICIT parameter (the ScenarioV1 initial_runtime.numeric_faults), not a
hidden mutation; only /api/run + /api/verify take the runtime lock; and sealed
programs + reference trajectories are cached by identity.

Run (public):  ./forge-bench            # locates python, builds ic32 (external
                                         # cache), picks a port, serves the app
Then open http://127.0.0.1:8765/

Developer / debugging (bytecode + native are NOT redirected off the source tree
in this mode -- use ./forge-bench for a read-only run):
    PYTHONPATH=../runtime/python:../research python3 spinner_bench.py
"""
import os
import re
import sys
import json
import threading
import collections
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "runtime", "python"))
sys.path.insert(0, os.path.join(HERE, "..", "research"))

import wrl_ir as W
import wrl_sugar as SG
import wrl_format as F
import wrl_complete as CP
import wrl_diagnostics as DG
import wrl_plan as P
import compiler as C
import admit as AD
import forge_runtime as O
import wrl_diff as WD
import wrl_scenario as SC
import wrl_fold as FD
import wrl_canvas as CV
import wrl_draft as D
import wrl_converge as CG
import wrl_project as PJ
import wrl_store as ST
import wrl_bundle as BD
import wrl_jobs as WJ
import wrl_templates as TP
import forge_errors as FE
from admit import mk_claim, film_hash_v7
from forge_state import init_state_v6, state_to_film_args_v6

SKIP_NATIVE = os.environ.get("TRVM_SKIP_NATIVE") == "1"
HOST = os.environ.get("SPINNER_BENCH_HOST", "127.0.0.1")
PORT = int(os.environ.get("SPINNER_BENCH_PORT", "8765"))
BENCH_VERSION = "v0.7.0-alpha.5"

# The ic_ref reducer (forge_runtime.ref_reduce/native_reduce) resets and reads MODULE-GLOBAL
# runtime state, so two folds must never run concurrently. Serialize ONLY the
# runtime endpoints (/api/run + /api/verify); the pure editor endpoints
# (/api/lower, /api/diff, /api/complete) touch no reducer globals and stay
# responsive even while a fold holds the lock (preflight item 2).
_PIPELINE_LOCK = threading.Lock()

# Identity-keyed caches (preflight item 3): a sealed program is a pure function
# of its source, and a reference trajectory is a pure function of
# (SemanticArtifactID, reducer, initial-fault seed) over the folded ScenarioV1.
# So a canvas move / format / repeated run reuses the sealed world and its
# trajectory instead of recompiling and re-folding.
#
# v0.6-4 (perf/release closure): each cache is a pure memo, so it is BOUNDED --
# an evicted entry is simply recomputed to byte-identical bytes and moves no
# identity. Bounding caps memory over a long-lived release/editing session where
# an author seals thousands of distinct source strings; the plain unbounded
# dicts would grow without limit. LRU by access order, thread-safe (the pure
# editor endpoints touch _PROG_CACHE off the _PIPELINE_LOCK).
_CACHE_CAP = 256


class _LruCache:
    """A bounded, thread-safe least-recently-used memo. A cache is PURE
    memoization -- an evicted key is recomputed to byte-identical bytes -- so
    bounding it caps memory for a long-lived release WITHOUT moving any identity
    (v0.6-4). `get` misses return None so callers recompute + `put`."""

    def __init__(self, cap):
        self._cap = cap
        self._d = collections.OrderedDict()
        self._lock = threading.Lock()

    def get(self, key):
        with self._lock:
            if key in self._d:
                self._d.move_to_end(key)
                return self._d[key]
            return None

    def put(self, key, value):
        with self._lock:
            self._d[key] = value
            self._d.move_to_end(key)
            while len(self._d) > self._cap:
                self._d.popitem(last=False)   # evict the least-recently-used

    def __len__(self):
        with self._lock:
            return len(self._d)

    @property
    def cap(self):
        return self._cap


_PROG_CACHE = _LruCache(_CACHE_CAP)   # src -> sealed program
_TRAJ_CACHE = _LruCache(_CACHE_CAP)   # (sem_id, reducer_name, faults_key) -> rows


# ------------------------------------------------- typed-error presentation
# v0.7-2 "Error and Progress UX": every API failure crosses to the browser as
# ONE frozen ErrorPresentationV1 (forge_errors) -- never a raw Python repr. The
# `error` key stays a human string (the presentation's domain message) for the
# legacy display; `error_presentation` carries the full typed sidecar (stable
# code, severity, retryable, action, category, and optional span/object). An
# UNKNOWN exception is sanitized to a generic internal presentation with a
# correlation error_id; its full text goes ONLY to the developer log below.
def _dev_log(error_id, exc):
    """Developer-only sink for an unknown exception (never crosses to the
    browser). A correlation `error_id` ties the sanitized presentation to this
    full traceback in the server log."""
    import traceback
    sys.stderr.write("[forge-error %s] %s\n" % (error_id, "".join(
        traceback.format_exception(type(exc), exc, exc.__traceback__))))


def _span_dict(sp):
    """A wrl_spans.SourceSpan -> the ErrorPresentationV1 source_span shape."""
    if sp is None:
        return None
    return {"file_id": sp.file_id, "start_line": sp.start_line,
            "start_column": sp.start_column, "end_line": sp.end_line,
            "end_column": sp.end_column}


def _source_locators(src):
    """Best-effort (source_span, object_id, field_path) for the FIRST diagnostic
    the authoritative parser/validator reports over `src`. Pure sidecar (never
    re-decides): used to highlight the offending span/object for a source or
    canvas error (PB4/PB5). Any failure degrades to (None, None, None)."""
    try:
        diags = DG.diagnose_core(SG.desugar_core(src))
    except Exception:
        return None, None, None
    if not diags:
        return None, None, None
    d = diags[0]
    return _span_dict(d.primary_span), d.canonical_object_id, d.field_path


def _err(ex, *, src=None, field_path=None, source_span=None, object_id=None,
         details=None):
    """Present a caught exception as {ok:False, error:<message>,
    error_presentation:<ErrorPresentationV1>}. A typed WrlValidationError is
    presented with its own domain message + stable code; an unknown exception is
    sanitized (correlation id, full text to _dev_log only). When `src` is given
    and no explicit span/object was passed, enrich a located source/canvas error
    with its span + canonical object (PB4/PB5)."""
    if src is not None and source_span is None and object_id is None:
        source_span, object_id, fp = _source_locators(src)
        if field_path is None:
            field_path = fp
    pres = FE.from_exception(ex, logger=_dev_log, field_path=field_path,
                             source_span=source_span, object_id=object_id,
                             details=details)
    return {"ok": False, "error": pres["message"], "error_presentation": pres}

# ------------------------------------------------------------- the demo world
# Pulser(every 2) -> Relay -> Spinner(quarter_turn_z @ n8) -> Orb, plus a
# once-at-1 Pulser -> Door. Demo precision w=16, n=8, so the named rotor
# lowers to (181,0,0,181).
#
# v0.5-0 Source Surface Closure (GPT-5.6): the editor seed is WORLD-ONLY. It
# carries NO run-input syntax (`periods`, `[epoch:N] ...`) -- run duration and
# per-epoch claim batches live in a ScenarioV1 (GOLDEN_DEMO_SCENARIO /
# ACCEPTANCE_BENCH_SCENARIO below), never in the world source. The seed keeps the
# ERGONOMIC surface (`every 2`, `rotor=quarter_turn_z`): Apply desugars approved
# WRL sugar directly, so pasting the seed back Applies cleanly and a sugar
# spelling seals to the same SemanticArtifactID as its numeric twin.
DEMO_WORLD_SOURCE = """profile forge.world.core.v1

[pulser:p0](every 2){sig_out}
[relay:r0]{sig_in, sig_out}
[spinner:sp](w=16, n=8, rotor=quarter_turn_z, configurable){sig_in, socket}
[orb:ob]{pose}
[pulser:p1](once at 1){sig_out}
[door:d0]{sig_in}

[pulser:p0] --sig--> [relay:r0]
[relay:r0] --sig--> [spinner:sp]
[spinner:sp] --socket--> [orb:ob]
[pulser:p1] --sig--> [door:d0]
"""

_S = lambda rot: ("SetRotor", "sp", rot)
_Rf = ("ResetFault", "ob")

# The independent golden claim ORACLE (Python literals, NOT world source -- carries
# no scenario syntax). Human labels are UI-only; the payloads are the real admit
# claims. This is deliberately a SECOND, hand-written encoding of the run inputs
# that the synthesized GOLDEN_DEMO_SCENARIO must reproduce byte-for-byte -- the
# batteries fold both and cross-check them, so it is a genuine oracle, not a copy.
SCRIPT = [
    ("set rotor = quarter_turn_z (181.0.0.181)", [mk_claim(1, 1, _S((181, 0, 0, 181)))]),
    ("idle pulse tick",                           []),
    ("set rotor = 256.0.0.0 (full-scale)",        [mk_claim(2, 2, _S((256, 0, 0, 0)))]),
    ("reset orb fault latch",                     [mk_claim(3, 3, _Rf)]),
    ("set rotor = 128.0.128.0 (mixed)",           [mk_claim(4, 4, _S((128, 0, 128, 0)))]),
    ("idle pulse tick",                           []),
    ("set rotor = 10.0.0.0 + unknown-obj claim",  [mk_claim(5, 5, _S((10, 0, 0, 0))),
                                                   mk_claim(6, 6, ("SetRotor", "zz", (9, 0, 0, 0)))]),
]


# ------------------------------------------------------------- pipeline glue
def _prog(src):
    """Desugar -> lower -> sealed program (the real production lowering),
    memoized by source (preflight item 3). The sealed program is immutable, so
    an identical source (e.g. a presentation-only canvas edit that reserializes
    to the same canonical bytes) reuses it with no recompile."""
    p = _PROG_CACHE.get(src)
    if p is None:
        p = W.lower_program(SG.desugar_core(src), W.parse_wrl_core)
        _PROG_CACHE.put(src, p)
    return p


# v0.5-0: the two shipped ScenarioV1 documents are named surfaces, distinct from
# the world source. Each carries the RUN INPUTS (initial runtime + one claim batch
# per epoch) bound to THIS world's SemanticArtifactID -- the world source carries
# none of it. GOLDEN drives the Golden ADMIT Demo; ACCEPTANCE walks the seven
# roadmap behaviours. Built once from the sealed demo world (identity-stable).
DEMO_WORLD_SEMANTIC_ID = _prog(DEMO_WORLD_SOURCE).semantic_artifact_id
GOLDEN_DEMO_SCENARIO = SC.demo_scenario(DEMO_WORLD_SEMANTIC_ID)
ACCEPTANCE_BENCH_SCENARIO = SC.bench_scenario(DEMO_WORLD_SEMANTIC_ID)


def _plan_view(src):
    """Sealed program + its CompilePlan view -- the production lowering contract
    (preflight item 1). The `_PlanView` duck-types the entire Fixture read
    interface that init_state_v6 / admit_step / state_to_film_args_v6 consume, so
    the normal run path NEVER reconstructs a Fixture."""
    prog = _prog(src)
    plan = P.artifact_to_compile_plan_v1(prog.sealed_artifact)
    return prog, P.plan_view(plan)


def _named_rotor_provenance(src, prog):
    """Scan the RAW sugar for `[spinner:ID]...rotor=<name>` and, for a
    policy-governed name, report its policy id + the geometry-dependent value at
    the spinner's n. This is BUILD PROVENANCE; the policy id never enters the
    sealed bytes (the artifact carries only the numeric rotor)."""
    n_of = {o["object_id"]: o["static_config"].get("n")
            for o in prog.sealed_artifact.artifact["objects"]
            if o["role"] == "Spinner"}
    out = []
    for m in re.finditer(r"\[spinner:([A-Za-z_]\w*)\][^\n\[]*?rotor=([A-Za-z_]\w*)",
                          src):
        sid, name = m.group(1), m.group(2)
        try:
            policy = SG.named_rotor_policy(name)
        except Exception:
            policy = None
        n = n_of.get(sid)
        value = None
        if n is not None:
            try:
                value = list(SG.named_rotor(name, n))
            except Exception:
                value = None
        out.append({"spinner": sid, "rotor_name": name, "n": n,
                    "policy": policy, "value": value})
    return out


def _lower_payload(src):
    try:
        prog = _prog(src)
    except Exception as ex:
        return _err(ex, src=src)
    art = prog.sealed_artifact.artifact
    nodes = [{"id": o["object_id"], "role": o["role"],
              "ports": o["ports"],
              "static_config": o["static_config"]} for o in art["objects"]]
    edges = [{"src": e["src"], "dst": e["dst"], "kind": e["kind"]}
             for e in art["edges"]]
    # diagnostics + formatting over the DESUGARED core surface (the authoritative
    # parser/validator surface); empty diagnostics == clean.
    core = SG.desugar_core(src)
    diags = [{"code": d.code, "message": d.message,
              "object_id": d.canonical_object_id, "render": d.render()}
             for d in DG.diagnose_core(core)]
    try:
        formatted = F.format_source(core, W.parse_wrl_core)
    except Exception as ex:
        formatted = "(format unavailable: %s)" % ex
    # initial rotor state from the plan/view (NO Fixture): init_state_v6 seeds
    # each controlling spinner's rotor from the plan's spinner config.
    view = P.plan_view(P.artifact_to_compile_plan_v1(prog.sealed_artifact))
    st0 = init_state_v6(view)
    rotor_init = {s: list(st0["rotor_" + s]) for s in sorted(view.spinners)
                  if ("rotor_" + s) in st0}
    return {"ok": True,
            "semantic_artifact_id": prog.semantic_artifact_id,
            "formatted": formatted,
            "diagnostics": diags,
            "graph": {"nodes": nodes, "edges": edges},
            "rotor_init": rotor_init,
            "provenance": _named_rotor_provenance(src, prog)}


def _resolve_scenario(src, scenario):
    """Return (sealed program, validated ScenarioV1) for `src`. The scenario is
    the AUTHORITATIVE run input (GPT-5.6's three-documents ruling): if the caller
    supplies one it is validated (typed WRL_BAD_SCENARIO on malformed) and folded
    verbatim; otherwise the immutable Golden ADMIT Demo scenario for THIS world is
    synthesized. Either way the run is driven by a ScenarioV1, not a hard-coded
    script -- the initial fault seed and every claim batch come from the document,
    so the demo's fault reset and `zz` Rejected claim are explicit scenario data."""
    prog = _prog(src)
    if scenario is None:
        return prog, SC.demo_scenario(prog.semantic_artifact_id)
    SC.validate_scenario_v1(scenario)
    # v0.4-0 ruling #3: normal execution refuses a scenario bound to a DIFFERENT
    # world (typed WRL_SCENARIO_WORLD_MISMATCH). A world edit rebinds only through
    # the explicit compatibility procedure, never implicitly here.
    # Slice B commit 3 widens this to the COMPOSED compatibility door: the
    # binding check PLUS the Q4 route-writer reservation. A route-bearing world
    # mints ADMIT facts under the reserved writer id, so a scenario that also
    # writes under it is refused here instead of colliding invisibly in the
    # film. The reservation is inert for every route-free world, which is every
    # world this bench ships.
    SC.check_world_compatibility(scenario, prog.artifact,
                                 prog.semantic_artifact_id)
    return prog, scenario


def _script_for(prog, scen):
    """Slice B commit 4: the ONE door from (world, scenario) to the batches the
    ADMIT driver folds.

    `scenario_to_script` lowers what the AUTHOR wrote; `wrl_fold.fold_script`
    adds what the WORLD sends. Both run paths below need both halves, and they
    are composed here for the reason `check_world_compatibility` gives for the
    same shape: two independent call sites drift, and the half that goes missing
    is whichever was added second. Today that is the fold, so a run path that
    forgot it would execute a route-bearing world as its route-free twin --
    green, plausible, and wrong.

    Route-free worlds take the early return in `route_claims`, so every world
    this bench ships gets a script that is byte-identical to the pre-commit-4
    one."""
    initial_faults, script = SC.scenario_to_script(scen)
    return initial_faults, FD.fold_script(prog.artifact, script)


def _admit_projection(view, claim, cfg_map, resets):
    """Structured projection of the ADMIT claim-state -- EXACTLY the fields
    Film v0.7 commits to (admit.film_bytes_v7), plus the EpochControl applied
    THIS epoch (cfg_map/resets). A pure read sidecar: it reads the same state the
    film hash already seals, so it perturbs no identity and the film hash is
    unchanged. This is what the upgraded Film panel surfaces instead of a bare
    hash: observed claim facts, immutable acceptance receipts + outcomes, derived
    recognition, the applied EpochControl, and both capacity-fault latches."""
    sp_names = set(view.spinners)
    ob_names = set(view.orbs)
    # IR v1.1 Slice A guard 3: pass the DECLARED mailbox set (empty until
    # MailboxDecl lands) rather than None, so an undeclared Send target
    # canonicalizes to INVALID_TARGET here exactly as it does in the film.
    mb_names = set(AD.mailboxes_of(view))
    facts = [{"writer": f["writer_id"], "sequence": f["sequence"],
              "digest": "%0*x" % (AD._HEX, f["digest"]),
              "payload_key": AD._pk_str(f["payload_key"]),
              "payload": AD._payload_str(f["payload"], sp_names, ob_names,
                                         mb_names)}
             for f in sorted(claim.get("facts", []), key=AD._fact_key)]
    receipts = []
    for ek in sorted(claim.get("receipts", {})):
        r = claim["receipts"][ek]
        receipts.append({"writer": ek[0], "sequence": ek[1],
                         "accepted_digest": "%0*x" % (AD._HEX,
                                                      r["accepted_digest"]),
                         "accepted_payload_key": AD._pk_str(
                             r["accepted_payload_key"]),
                         "accepted_epoch": r["accepted_epoch"],
                         "outcome": AD._outcome_str(r["outcome"])})
    ekeys = sorted({(f["writer_id"], f["sequence"])
                    for f in claim.get("facts", [])})
    recog = [{"writer": ek[0], "sequence": ek[1],
              "state": AD.recognition(claim, ek)} for ek in ekeys]
    return {"policy": AD.ACCEPTANCE_POLICY_ID,
            "fact_capacity_fault": int(claim.get("fact_capacity_fault", 0)),
            "receipt_capacity_fault": int(claim.get("receipt_capacity_fault", 0)),
            "capacity_fault": AD.capacity_fault(claim),
            "facts": facts, "receipts": receipts, "recognition": recog,
            "epoch_control": {
                "set_rotor": {sp: list(rot)
                              for sp, rot in sorted(cfg_map.items())},
                "reset_fault": sorted(ob for ob, v in resets.items() if v)}}


def _run_traj(src, reducer, reducer_name, scenario=None, progress=None,
              cancel=None, phase=None):
    """Fold a ScenarioV1's (initial_faults, script) through the compiled step
    over the PLAN VIEW of `src` -- the production lowering contract, with NO
    Fixture reconstructed (preflight item 1). Returns (SemanticArtifactID,
    ScenarioDigest, rows). Each row carries the per-object rotor/pose/fault
    projections (generalized -- no hard-coded sp/ob) plus demo-convenience
    scalars pointing at the first spinner/orb for the current disc UI. The
    initial fault seed is EXPLICIT scenario state (the ScenarioV1
    initial_runtime.numeric_faults), never a hidden mutation. Result is memoized
    by (sem_id, reducer, ScenarioDigest) (preflight item 3): the run inputs'
    identity keys the trajectory cache."""
    prog, scen = _resolve_scenario(src, scenario)
    sem = prog.semantic_artifact_id
    view = P.plan_view(P.artifact_to_compile_plan_v1(prog.sealed_artifact))
    spins = sorted(view.spinners)
    orbs = list(view.orbs)
    scen_dig = SC.scenario_digest(scen)
    initial_faults, script = _script_for(prog, scen)
    labels = [lbl for lbl, _ in script]
    ph = phase or reducer_name
    total = len(script)
    ckey = (sem, reducer_name, scen_dig)
    cached = _TRAJ_CACHE.get(ckey)
    if cached is not None:
        # v0.4-0 ruling #2: labels are EXCLUDED from the ScenarioDigest, so a
        # label-only edit is a cache HIT on the label-free trajectory. Attach the
        # CURRENT scenario's labels on the way out so the display updates even
        # though nothing was recomputed (battery E3).
        if progress is not None:
            progress(total, total, ph)     # a cache hit is instantly complete
        return sem, scen_dig, _with_labels(cached, labels)
    if progress is not None:
        progress(0, total, ph)
    world = init_state_v6(view)
    for o in initial_faults:
        if ("fault_" + o) in world:
            world["fault_" + o] = 1
    # The runtime state shape and the acceptance policy BOTH come from the
    # sealed artifact (via the plan view), never from a module default: a world
    # must execute the semantics its own SemanticArtifactID names.
    claim = AD.init_claimstate(view)
    # ... and so does the film's mailbox table. `admit_policy_id` alone is only
    # HALF of what a sealed world declares: without the declared mailboxes,
    # Film v0.7's guard 3 canonicalizes a Send target to INVALID_TARGET, so the
    # film would assert the route addressed a mailbox that does not exist while
    # `_admit_projection` (which already passes them) said otherwise. Fetching
    # both is what `wrl_fold.runtime_seams` is for. Empty for every mailbox-free
    # world, and `film_bytes_v7` gates its whole mailbox block on that, so the
    # demo's films are byte-identical.
    #
    # Core 0.2.1 §8c: fetched as ONE `RuntimeSeamsV1` and consumed through
    # `admit_step_sealed`. This is a production world execution, so there is no
    # spelling here that could name a policy the world did not seal.
    _seams = FD.runtime_seams(view, view)
    film_mbs = _seams.film_mailboxes
    step, _ = C.compile_step_v6(view)
    sp0 = spins[0] if spins else None
    ob0 = orbs[0] if orbs else None
    rows = []
    for e, (label, batch) in enumerate(script):
        # Cooperative cancellation is checked at the epoch boundary (a single
        # reducer fold is atomic). JobCancelled propagates PAST _run_payload's
        # broad except so the registry maps it to `cancelled`, not `failed`.
        if cancel is not None and cancel():
            raise WJ.JobCancelled()
        ep = 1 + e
        claim, cfg_map, resets = FD.admit_step_sealed(
            claim, batch, ep, view, _seams)
        ec = C.enc_config_bundle(view, cfg_map, resets)
        world = C.dec_state_v6(view, reducer(
            f"(({step} {ec}) {C.enc_state_v6(view, world)})"))
        if progress is not None:
            progress(ep, total, ph)
        film = film_hash_v7(*state_to_film_args_v6(view, world, ep),
                            state=claim, mailboxes=film_mbs)
        # Stored row carries NO label -- the cache is keyed by the label-free
        # ScenarioDigest, so the persisted trajectory must be label-free too.
        rows.append({"t": ep,
                     "rotors": {s: list(world["rotor_" + s]) for s in spins},
                     "poses": {o: list(world["pose_" + o]) for o in orbs},
                     "faults": {o: int(world["fault_" + o]) for o in orbs},
                     "rotor": list(world["rotor_" + sp0]) if sp0 else None,
                     "pose": list(world["pose_" + ob0]) if ob0 else None,
                     "fault": int(world["fault_" + ob0]) if ob0 else 0,
                     "film": film,
                     "admit": _admit_projection(view, claim, cfg_map, resets)})
    _TRAJ_CACHE.put(ckey, rows)
    return sem, scen_dig, _with_labels(rows, labels)


def _with_labels(rows, labels):
    """Return a shallow copy of the cached label-free trajectory rows with the
    CURRENT scenario's per-epoch labels attached (v0.4-0 ruling #2). Labels are
    display-only and never affect the numeric world/film, so re-attaching them on
    a digest cache-hit is safe and keeps the UI honest after a label edit."""
    out = []
    for r, lbl in zip(rows, labels):
        rr = dict(r)
        rr["label"] = lbl
        out.append(rr)
    return out


def _run_traj_fixture(src, reducer, scenario=None, progress=None, cancel=None):
    """Fixture ORACLE path (SELECTABLE, verify-only). Reconstructs the legacy
    Fixture and folds the SAME scenario through it, returning per-epoch film
    hashes only. Used to cross-check that the production plan/view path equals
    the independent Fixture oracle (acceptance item 9). The normal run/verify
    path never reaches here; only /api/verify with oracle=true does."""
    prog, scen = _resolve_scenario(src, scenario)
    fx = prog.as_fixture_for_test()
    view = P.plan_view(P.artifact_to_compile_plan_v1(prog.sealed_artifact))
    initial_faults, script = _script_for(prog, scen)
    total = len(script)
    world = init_state_v6(fx)
    for o in initial_faults:
        if ("fault_" + o) in world:
            world["fault_" + o] = 1
    # The Fixture is an INDEPENDENT oracle, so the state is seeded from the
    # Fixture's own declarations -- but the policy still comes from the sealed
    # artifact. If the two disagreed about which mailboxes exist, the oracle
    # cross-check would (correctly) fail rather than agree by construction.
    claim = AD.init_claimstate(fx)
    # The oracle's mailbox table comes from the FIXTURE, not the view, for the
    # same reason its claim state does: an oracle that borrowed the production
    # path's declarations would agree by construction.
    film_mbs = FD.film_mailboxes(fx)
    _oracle_policy = FD.admit_policy_of(view)
    step, _ = C.compile_step_v6(view)
    films = []
    for e, (label, batch) in enumerate(script):
        if cancel is not None and cancel():
            raise WJ.JobCancelled()
        ep = 1 + e
        # The PROBE, not the sealed seam -- deliberately, and for the same
        # reason the mailbox table above is re-derived from `fx`: this is the
        # Fixture ORACLE. It must reach the reducer by a route that does not
        # borrow the production path's declarations, or it agrees by
        # construction and stops being a second opinion. Naming the policy by
        # hand is exactly what `admit_policy_probe` is for (Core 0.2.1 §8c).
        #
        # ...but `admit_policy_of` returns None for a mailbox-free world, and
        # the probe REFUSES None by contract, so routing unconditionally
        # through it would break the demo world -- which is mailbox-free.
        # `None` names the frozen policy; `admit_step` is the entry that means
        # that. Hoisted out of the loop because the policy is a property of the
        # world, not of the epoch.
        if _oracle_policy is None:
            claim, cfg_map, resets = AD.admit_step(claim, batch, ep, fx)
        else:
            claim, cfg_map, resets = AD.admit_policy_probe(
                claim, batch, ep, fx, _oracle_policy)
        ec = C.enc_config_bundle(view, cfg_map, resets)
        world = C.dec_state_v6(view, reducer(
            f"(({step} {ec}) {C.enc_state_v6(view, world)})"))
        if progress is not None:
            progress(ep, total, "fixture")
        films.append(film_hash_v7(*state_to_film_args_v6(fx, world, ep),
                                  state=claim, mailboxes=film_mbs))
    return films


def _run_payload(src, scenario=None, progress=None, cancel=None):
    try:
        sem, scen_dig, rows = _run_traj(src, O.ref_reduce, "ic_ref", scenario,
                                        progress=progress, cancel=cancel,
                                        phase="ic_ref")
    except WJ.JobCancelled:
        raise
    except Exception as ex:
        return _err(ex)
    return {"ok": True, "semantic_artifact_id": sem, "scenario_digest": scen_dig,
            "reducer": "ic_ref", "epochs": rows}


def _verify_payload(src, oracle=False, scenario=None, progress=None,
                    cancel=None):
    """Re-fold the SAME scenario through the native ic32 reducer and assert
    world+film parity with ic_ref. When oracle=true ALSO cross-checks the
    plan/view films against the independent Fixture oracle (acceptance item 9);
    that is the ONLY path that reconstructs a Fixture. Progress is reported in
    phases (`ic_ref` then `ic32`, plus `fixture` when oracle=true); cancellation
    is honored at any epoch boundary in any phase."""
    try:
        sem, scen_dig, ref = _run_traj(src, O.ref_reduce, "ic_ref", scenario,
                                       progress=progress, cancel=cancel,
                                       phase="ic_ref")
    except WJ.JobCancelled:
        raise
    except Exception as ex:
        return _err(ex)
    oracle_report = None
    if oracle:
        try:
            fx_films = _run_traj_fixture(src, O.ref_reduce, scenario,
                                         progress=progress, cancel=cancel)
            oracle_report = {"engine": "fixture", "reducer": "ic_ref",
                             "match": [r["film"] for r in ref] == fx_films,
                             "epochs": len(fx_films)}
        except WJ.JobCancelled:
            raise
        except Exception as ex:
            pres = FE.from_exception(ex, logger=_dev_log)
            oracle_report = {"engine": "fixture", "error": pres["message"],
                             "error_presentation": pres}
    if SKIP_NATIVE:
        return {"ok": True, "native": False, "skipped": True,
                "semantic_artifact_id": sem, "scenario_digest": scen_dig,
                "oracle": oracle_report,
                "message": "native gated off (TRVM_SKIP_NATIVE=1) -- ref-only"}
    try:
        _, _, nat = _run_traj(src, O.native_reduce, "ic32", scenario,
                              progress=progress, cancel=cancel, phase="ic32")
    except WJ.JobCancelled:
        raise
    except Exception as ex:
        if getattr(ex, "code", None):
            return _err(ex)
        code = (FE.NATIVE_UNAVAILABLE if not O.native_available()
                else FE.NATIVE_BUILD_FAILED)
        pres = FE.native(code, "The native reducer could not fold this world -- "
                         "run reference-only, or retry the native build.")
        return {"ok": False, "error": pres["message"],
                "error_presentation": pres}
    epochs = []
    parity = True
    for r, n in zip(ref, nat):
        match = (r["rotors"] == n["rotors"] and r["poses"] == n["poses"]
                 and r["faults"] == n["faults"] and r["film"] == n["film"])
        parity &= match
        epochs.append({"t": r["t"], "film_ref": r["film"],
                       "film_native": n["film"], "match": match})
    return {"ok": True, "native": True, "parity": bool(parity),
            "semantic_artifact_id": sem, "scenario_digest": scen_dig,
            "oracle": oracle_report, "epochs": epochs}


# --------------------------------------------------------- v0.6-1 runtime jobs
# The long ic-reducer folds run as CANCELLABLE background jobs so a client that
# navigates away neither aborts the compute nor trips a BrokenPipeError writing
# to a dead socket. The executor reuses the EXACT synchronous fold (identical
# result payload) with progress + cancel threaded through, and shares the SAME
# _PIPELINE_LOCK so a job cannot interleave the reducer's module-global state
# with a legacy synchronous /api/run.
def _job_execute(kind, request, progress, should_cancel):
    """JobRegistry executor. `kind` in {run, verify, deep_health}; `request`
    carries the same inputs the synchronous endpoints take (src + optional
    scenario + oracle). `deep_health` runs the DEEP release verification (small
    ref + native fold + film parity + object-store round-trip) as a cancellable
    job -- it is NEVER run on boot."""
    if kind == "deep_health":
        return _deep_health_payload(progress=progress, cancel=should_cancel)
    src = request.get("src", DEMO_WORLD_SOURCE)
    scenario = request.get("scenario")
    if kind == "run":
        return _run_payload(src, scenario, progress=progress,
                            cancel=should_cancel)
    return _verify_payload(src, oracle=bool(request.get("oracle")),
                           scenario=scenario, progress=progress,
                           cancel=should_cancel)


# One worker, sharing the reducer pipeline lock. Bounded ring of recent jobs.
_JOB_REGISTRY = WJ.JobRegistry(_job_execute, lock=_PIPELINE_LOCK, max_jobs=64)


def _job_submit_payload(req):
    """POST /api/jobs: enqueue a run/verify job; returns the queued snapshot."""
    kind = req.get("kind", "run")
    request = {"src": req.get("src", DEMO_WORLD_SOURCE)}
    if req.get("scenario") is not None:
        request["scenario"] = req.get("scenario")
    if req.get("oracle"):
        request["oracle"] = True
    try:
        job_id = _JOB_REGISTRY.submit(kind, request)
        return {"ok": True, "job": _JOB_REGISTRY.get(job_id)}
    except Exception as ex:
        return _err(ex)


def _job_get_payload(job_id):
    """GET /api/jobs/<id>: the current snapshot (poll for progress/result)."""
    try:
        return {"ok": True, "job": _JOB_REGISTRY.get(job_id)}
    except Exception as ex:
        return _err(ex)


def _job_cancel_payload(job_id):
    """POST /api/jobs/<id>/cancel: request cooperative cancellation."""
    try:
        return {"ok": True, "job": _JOB_REGISTRY.cancel(job_id)}
    except Exception as ex:
        return _err(ex)


def _jobs_list_payload(limit=None):
    """GET /api/jobs: recent jobs, newest first (bounded ring)."""
    try:
        return {"ok": True, "jobs": _JOB_REGISTRY.list(limit=limit)}
    except Exception as ex:
        return _err(ex)


def _scenario_payload(src, scenario):
    """Pure validate + digest for an AUTHORED ScenarioV1 (no run, no ic-reducer).
    The Author-mode editor posts its working scenario here on every edit to get
    immediate feedback: a typed WRL_BAD_SCENARIO on malformed input, otherwise the
    ScenarioDigest + ReplayBundleID for the sealed world (acceptance 1 & 2 made
    live -- editing run inputs moves the ScenarioDigest while the world's
    SemanticArtifactID is untouched). A pure editor endpoint: it computes the two
    identities, it never mints or perturbs one, and it takes no runtime lock."""
    try:
        prog, scen = _resolve_scenario(src, scenario)
    except Exception as ex:
        return _err(ex)
    sem = prog.semantic_artifact_id
    scen_dig = SC.scenario_digest(scen)
    return {"ok": True, "world_semantic_id": sem, "scenario_digest": scen_dig,
            "replay_bundle_id": SC.replay_bundle_id(
                sem, scen_dig, scen["initial_runtime"])}


def _diff_payload(a, b):
    """SEALED SemanticDiff between two WRL sources (wrl_diff), surfacing the live
    bridge law: semantic_diff(a,b).is_empty() <=> sem_id(a) == sem_id(b). Both
    sides seal exactly as the identity spine does, so presentation-only edits
    yield an empty diff (id unmoved) and rotor/wire edits move it. If a side is
    invalid/unsupported it cannot earn an id -- we then report the seal error and
    fall back to the TOLERANT draft_diff, which makes NO identity claim."""
    def semid(s):
        try:
            return _prog(s).semantic_artifact_id, None
        except Exception as ex:
            return None, FE.from_exception(ex, logger=_dev_log)
    sa, ea = semid(a)
    sb, eb = semid(b)
    out = {"ok": True, "sem_a": sa, "sem_b": sb,
           "sem_a_error": ea, "sem_b_error": eb}
    # Diff over the DESUGARED core surface, exactly as the identity spine seals
    # (_prog desugars before parse_wrl_core); wrl_diff parses core, not sugar, so
    # named rotors etc. must be lowered to core first.
    try:
        d = WD.diff_sources(SG.desugar_core(a), SG.desugar_core(b))
        out["mode"] = "sealed"
    except Exception as ex:
        out["mode"] = "draft"
        out["seal_error"] = FE.from_exception(ex, logger=_dev_log)
        try:
            d = WD.draft_diff_sources(SG.desugar_core(a), SG.desugar_core(b))
        except Exception as ex2:
            return _err(ex2)
    out["changes"] = [{"kind": c.kind, "key": c.key,
                       "detail": list(c.detail), "render": c.render()}
                      for c in d.changes]
    out["is_empty"] = d.is_empty()
    if out["mode"] == "sealed" and sa is not None and sb is not None:
        out["ids_equal"] = (sa == sb)
        out["bridge_holds"] = (d.is_empty() == (sa == sb))
    return out


def _complete_payload(src, offset):
    offset = max(0, min(int(offset), len(src)))
    c = CP.completions_at(src, offset)
    return {"ok": True, "context": c.context, "prefix": c.prefix,
            "candidates": list(c.candidates)}


# ---------------------------------------------- v0.4-4c draft convergence
# A server-side CanvasSession per project binds the semantic WorldDraft to its
# CanvasLayoutV1. A free-form WRL Core text edit posted to /api/draft/source is
# routed through the ATOMIC wrl_draft.replace_world_source transaction (via
# CanvasSession.apply_text); the reconciled layout is projected to an SVG canvas
# view. The session is shared mutable state across requests, so a dedicated lock
# serializes its mutations -- these endpoints touch NO ic-reducer global, so they
# stay off the runtime _PIPELINE_LOCK and remain responsive during a fold.
#
# v0.5-3 session migration: the sessions are no longer a bare in-memory dict.
# A `ProjectSessionCache` backs each `project_id` with a durable ForgeProjectV1
# document on disk (rooted at FORGE_PROJECT_ROOT). A first access lazily creates
# a default project from the demo world; a COMMIT persists the session's now-
# active world back to the store (per-project exact-CAS), so committed edits
# survive a server restart. Uncommitted draft edits + the undo stack stay
# session-local (the v0.5-2 rule); `reset` reverts a session to its saved state.
_DRAFT_LOCK = threading.Lock()


def _default_data_dir():
    """The per-OS user-data directory for Forge projects (v0.6.5 release
    closure): authoring state lives OUTSIDE the source/install tree so a clean
    release contains no mutable project dir and a first run creates it
    externally. `FORGE_PROJECT_ROOT` still overrides this explicitly.

      Linux/BSD : $XDG_DATA_HOME/trvm-forge          (default ~/.local/share/...)
      macOS     : ~/Library/Application Support/TRVM Forge
      Windows   : %LOCALAPPDATA%\\TRVM Forge
    """
    if sys.platform == "darwin":
        base = os.path.expanduser("~/Library/Application Support")
        return os.path.join(base, "TRVM Forge")
    if os.name == "nt":
        base = os.environ.get("LOCALAPPDATA") or os.path.expanduser("~")
        return os.path.join(base, "TRVM Forge")
    base = os.environ.get("XDG_DATA_HOME") or os.path.expanduser("~/.local/share")
    return os.path.join(base, "trvm-forge")


# The project store lives under `<data-dir>/projects`; the crash-recovery overlay
# is a sibling `<data-dir>/.recovery` (ProjectSessionCache derives it from the
# store's parent), so neither ever lands inside the source tree by default.
_PROJECT_ROOT = os.environ.get("FORGE_PROJECT_ROOT",
                               os.path.join(_default_data_dir(), "projects"))


def _default_scenarios(sem_id):
    """The two immutable demo presets, as project scenario entries."""
    return [PJ.make_scenario_entry("golden", SC.demo_scenario(sem_id)),
            PJ.make_scenario_entry("bench", SC.bench_scenario(sem_id))]


_FORGE_STORE = PJ.ForgeProjectStore(_PROJECT_ROOT)
# v0.5.1: the demo now persists the COMPLETE authoring workspace (ForgeProjectV2)
# -- an invalid or uncommitted draft, the raw editor buffer, undo + idempotency
# state and scenario selection all survive a Save + restart. Opening is
# version-dispatched, so any pre-existing V1 project on disk still reopens.
_PROJECT_CACHE = PJ.ProjectSessionCache(
    _FORGE_STORE, DEMO_WORLD_SOURCE, scenarios_for=_default_scenarios,
    project_version=PJ.PROJECT_V2_VERSION)

# v0.5-5 immutable object substrate (content-addressed) for bundle import/export.
# Kept in a dotted sibling dir of the project docs so ForgeProjectStore, which
# only lists top-level `<pid>.json`, never sees it as a project.
_WORLD_STORE = ST.WorldObjectStore(os.path.join(_PROJECT_ROOT, ".objects",
                                                "worlds"))
_SCEN_STORE = ST.ScenarioRuntimeStore(os.path.join(_PROJECT_ROOT, ".objects",
                                                   "scen"))

# v0.6-2 startup/project UX: a single non-authoritative pointer at the LAST project
# the author opened, so a reload lands back in that project instead of the demo. It
# advances no project revision and moves no SemanticArtifactID; a pointer at a gone
# project self-heals to None (see PJ.resolve_last_session).
_LAST_SESSION = PJ.LastSessionStore(_PROJECT_ROOT)

# v0.7-3 Immutable Template Catalog: exactly three release-owned, read-only
# templates loaded + fully identity-verified from the allowlisted `templates/`
# directory that ships alongside the forge modules. A load re-derives every
# world/scenario/replay identity and FAILS CLOSED (FORGE_TEMPLATE_IDENTITY / a
# schema fault) on any drift, so a corrupted template is never surfaced. The
# catalog is release content -- it never enters a project's SemanticArtifactID or
# a normal export.
_TEMPLATE_DIR = os.path.join(HERE, "templates")
try:
    _TEMPLATE_CATALOG = TP.TemplateCatalog.load_dir(_TEMPLATE_DIR)
    _TEMPLATE_ERROR = None
except Exception as _ex:               # fail closed: no catalog, health flags it
    _TEMPLATE_CATALOG = None
    _TEMPLATE_ERROR = _ex

# v0.7-3 created_from_template provenance sidecar: a NON-AUTHORITATIVE record of
# which template a project was instantiated from. It lives in a dotted sibling dir
# (leading dot keeps it out of ForgeProjectStore.list_projects) and is DELIBERATELY
# kept OUT of the ForgeProjectV2 document -- so it can never enter the
# SemanticArtifactID / ScenarioDigest / ReplayBundleID / BackendArtifactID.
# Changing or removing it changes NO Forge identity.
_PROVENANCE_DIR = os.path.join(_PROJECT_ROOT, ".provenance")


def _write_provenance(project_id, template_id):
    """Record `{template_id, template_release_version}` for a project (atomic).
    Best-effort: a provenance write never blocks project creation."""
    rec = {"created_from_template": {"template_id": template_id,
                                     "template_release_version": BENCH_VERSION}}
    try:
        os.makedirs(_PROVENANCE_DIR, exist_ok=True)
        ST._atomic_write(os.path.join(_PROVENANCE_DIR, "%s.json" % project_id),
                         json.dumps(rec, sort_keys=True).encode("utf-8"))
    except OSError:
        pass


def _read_provenance(project_id):
    """The provenance record for a project, or None. Never raises."""
    path = os.path.join(_PROVENANCE_DIR, "%s.json" % project_id)
    try:
        with open(path, "r") as f:
            return json.load(f).get("created_from_template")
    except (OSError, ValueError):
        return None


# v0.7.0-alpha.2 First-Run State Closure: `main` is the Golden Demo pseudo-session
# behind read-only Explore. It is EPHEMERAL -- held only in memory and NEVER written
# to the project store or the recovery journal -- so exploring the demo creates no
# persisted state (OA7). The single transition out of Explore is "Make an editable
# copy" (POST /api/project/new), which creates a real, named ForgeProjectV2. Every
# named project still round-trips through the persisting ProjectSessionCache.
_DEMO_ID = "main"
_DEMO_SESSIONS = {}          # demo id -> CanvasSession (in-memory only, never saved)


def _pid(session_id):
    return session_id or _DEMO_ID


def _is_demo(session_id):
    return _pid(session_id) == _DEMO_ID


def _demo_session(project_id, rebuild=False):
    """The in-memory Golden Demo session. Built the same way the cache builds its
    default doc (lower DEMO_WORLD_SOURCE -> new_session) but held OUTSIDE the store,
    so read-only Explore writes no project document and no recovery journal."""
    sess = _DEMO_SESSIONS.get(project_id)
    if sess is None or rebuild:
        prog = W.lower_program(SG.desugar_core(DEMO_WORLD_SOURCE), W.parse_wrl_core)
        sess = CG.new_session(prog, project_id)
        _DEMO_SESSIONS[project_id] = sess
    return sess


def _get_or_open_session(session_id):
    if _is_demo(session_id):
        return _demo_session(_pid(session_id))
    return _PROJECT_CACHE.open(_pid(session_id))


def _open_session(session_id, src=None):
    # v0.5-3: reset means revert-to-saved (discard uncommitted edits), NOT wipe
    # the persisted project. The legacy `src` override is intentionally dropped;
    # authoring a NEW world is the province of the v0.5-4 Library UI. The demo
    # pseudo-session reverts to a freshly-lowered Golden Demo, still in memory.
    if _is_demo(session_id):
        return _demo_session(_pid(session_id), rebuild=True)
    return _PROJECT_CACHE.reset(_pid(session_id))


def _draft_view(session):
    """Project a CanvasSession to the SVG canvas view: one node per draft object
    (id + role + presentation), one edge per draft edge (kind/src/dst + edge_key
    + presentation), plus the live identity + convergence status and the current
    canonical WRL Core text. The presentation blocks come from the reconciled
    CanvasLayoutV1 -- they never feed the SemanticArtifactID (candidate id is read
    straight off the draft)."""
    draft, layout = session.draft, session.layout
    pres_n = {n["object_id"]: n["presentation"] for n in layout["nodes"]}
    pres_e = {e["edge_key"]: e["presentation"] for e in layout["edges"]}
    nodes = [{"id": o["object_id"], "role": o["role"],
              "static_config": o["static_config"],
              "presentation": pres_n.get(o["object_id"])}
             for o in draft.objects]
    edges = []
    for e in draft.edges:
        k = CV.edge_key(e["kind"], e["src"], e["dst"])
        edges.append({"kind": e["kind"], "src": e["src"], "dst": e["dst"],
                      "edge_key": k, "presentation": pres_e.get(k)})
    return {"draft_id": draft.draft_id,
            "profile_id": draft.profile_id,
            "semantic_revision": draft.semantic_revision,
            "candidate_semantic_id": draft.candidate_semantic_id,
            "candidate_valid": draft.candidate_error is None,
            "candidate_error": draft.candidate_error,
            "active_semantic_id": draft.active_semantic_id,
            "nodes": nodes, "edges": edges,
            "text": session.to_text(),
            "can_undo": bool(session._layout_history),
            "undo_depth": len(session._layout_history),
            "commits": list(session.commits)}


def _scenario_compat(prev_world, new_world):
    """Surface the commit-time scenario/world compatibility law for the UI: a
    scenario bound to `prev_world` (the demo scenario is the representative)
    rebinds to `new_world` with its ScenarioDigest INVARIANT (world- and
    label-independent) and ONLY its ReplayBundleID moving. Pure projection --
    computes ids, never mints or perturbs one. Identical worlds report a no-op."""
    scen = SC.demo_scenario(prev_world)
    digest = SC.scenario_digest(scen)
    rb_old = SC.replay_bundle_id(prev_world, digest, scen["initial_runtime"])
    if new_world == prev_world:
        return {"changed": False, "scenario_digest": digest,
                "digest_invariant": True,
                "replay_bundle_old": rb_old, "replay_bundle_new": rb_old,
                "replay_bundle_moved": False}
    rebound = SC.rebind_scenario(scen, new_world)
    digest_b = SC.scenario_digest(rebound)
    rb_new = SC.replay_bundle_id(new_world, digest_b, rebound["initial_runtime"])
    return {"changed": True, "scenario_digest": digest_b,
            "digest_invariant": digest_b == digest,
            "replay_bundle_old": rb_old, "replay_bundle_new": rb_new,
            "replay_bundle_moved": rb_new != rb_old}


def _draft_payload(session_id):
    with _DRAFT_LOCK:
        return {"ok": True, "view": _draft_view(_get_or_open_session(session_id))}


def _draft_reset_payload(session_id, src=None):
    with _DRAFT_LOCK:
        return {"ok": True, "view": _draft_view(_open_session(session_id, src))}


def _draft_source_payload(req):
    """POST /api/draft/source: apply a free-form WRL Core text replacement to the
    session draft as ONE atomic ReplaceWorldSourceV1 transaction and return the
    reconciled canvas view. The server builds the frozen request envelope (pinning
    the session's draft_id and, by default, its current revision) so the browser
    only sends {session_id?, replace_id, base_revision?, source}."""
    sid = req.get("session_id") or "main"
    with _DRAFT_LOCK:
        sess = _get_or_open_session(sid)
        request = {"replace_version": D.REPLACE_VERSION,
                   "replace_id": req.get("replace_id"),
                   "draft_id": sess.draft.draft_id,
                   "base_revision": req.get("base_revision",
                                            sess.draft.semantic_revision),
                   "source": req.get("source", "")}
        try:
            res = sess.apply_text(request)
        except Exception as ex:
            return _err(ex, src=req.get("source", ""))
        rep = res["replace"]
        # source_map is a WrlSourceMap object (not JSON) -- surface only the
        # JSON-plain transaction fields the UI needs.
        apply_out = {k: rep[k] for k in (
            "replace_id", "semantic_revision", "status", "semantic_noop",
            "candidate_semantic_id", "candidate_valid", "canonical_wrl",
            "diagnostics", "draft_diff", "active_semantic_id")}
        return {"ok": True, "apply": apply_out, "view": _draft_view(sess)}


def _draft_undo_payload(session_id):
    with _DRAFT_LOCK:
        sess = _get_or_open_session(session_id)
        if not sess._layout_history:
            return {"ok": True, "undone": False, "view": _draft_view(sess)}
        sess.undo()
        return {"ok": True, "undone": True, "view": _draft_view(sess)}


def _draft_commit_payload(req):
    """POST /api/draft/commit: promote the current candidate to the active world
    (explicit content-checked commit). Returns the new active id + refreshed view."""
    sid = req.get("session_id") or "main"
    if _is_demo(sid):
        # read-only Explore has no durable project to commit into -- the author
        # must "Make an editable copy" first (which creates a real project).
        return {"ok": False,
                "error": "the Golden Demo is read-only; make an editable copy "
                         "before committing"}
    with _DRAFT_LOCK:
        sess = _get_or_open_session(sid)
        commit = {"commit_version": D.COMMIT_VERSION,
                  "draft_id": sess.draft.draft_id,
                  "base_revision": req.get("base_revision",
                                           sess.draft.semantic_revision),
                  "expected_candidate_semantic_id":
                      req.get("expected_candidate_semantic_id",
                              sess.draft.candidate_semantic_id)}
        prev_world = sess.draft.active_semantic_id
        try:
            out = sess.commit(commit)
        except Exception as ex:
            return _err(ex)
        # v0.5-3: a commit is the persistence boundary -- write the session's
        # now-active world back to the durable project (per-project exact-CAS).
        try:
            saved = _PROJECT_CACHE.persist(sid)
            project_revision = PJ._revision_of(saved)
        except Exception as ex:
            pres = FE.from_exception(ex, logger=_dev_log,
                                     details={"phase": "persist_after_commit"})
            return {"ok": False,
                    "error": "committed, but persisting the project failed: "
                             + pres["message"],
                    "error_presentation": pres}
        # sealed_artifact is a SealedArtifact object (not JSON) -- drop it.
        commit_out = {"draft_id": out["draft_id"],
                      "semantic_revision": out["semantic_revision"],
                      "active_semantic_id": out["active_semantic_id"],
                      "previous_active": prev_world,
                      "project_id": sid,
                      "project_revision": project_revision}
        compat = _scenario_compat(prev_world, out["active_semantic_id"])
        return {"ok": True, "commit": commit_out, "scenario_compat": compat,
                "view": _draft_view(sess)}


def _draft_history_payload(session_id):
    with _DRAFT_LOCK:
        return {"ok": True, "history": _get_or_open_session(session_id).history()}


# ---------------------------------------------------- v0.5-4 Library panel
# The Library manages MULTIPLE named, persisted worlds over the same
# ProjectSessionCache: list / new / open / fork / rename / trash. Each project
# is its own durable ForgeProjectV1 document; the browser tracks the current
# session_id (== project_id) and drives the canvas endpoints against it. These
# are pure store/cache operations (no ic-reducer), serialized by _DRAFT_LOCK.
def _projects_payload():
    with _DRAFT_LOCK:
        return {"ok": True, "projects": _PROJECT_CACHE.list_infos()}


def _project_new_payload(req):
    pid = req.get("project_id")
    name = req.get("name") or pid
    with _DRAFT_LOCK:
        try:
            sess = _PROJECT_CACHE.create_new(pid, name)
        except Exception as ex:
            return _err(ex)
        _LAST_SESSION.set(pid)
        return {"ok": True, "project_id": pid,
                "projects": _PROJECT_CACHE.list_infos(),
                "view": _draft_view(sess)}


def _project_scenario_docs(pid):
    """The persisted scenario documents + bound default for a project, read
    straight off the durable project document. A reopen uses THESE (not the global
    golden/bench presets, and not the originating template catalog) so the UI
    always presents the project's OWN scenarios -- e.g. a reopened Blank project
    restores its one-epoch idle scenario, not Golden/Bench. Once a project is
    created it owns its scenario documents and no longer depends on any template."""
    doc = _PROJECT_CACHE._store.load(_pid(pid))
    return (PJ._scenarios_of(doc), PJ._selected_scenario_of(doc))


def _project_open_payload(req):
    pid = req.get("project_id")
    with _DRAFT_LOCK:
        try:
            sess = _PROJECT_CACHE.open(_pid(pid))
            scen, sel = _project_scenario_docs(pid)
        except Exception as ex:
            return _err(ex)
        _LAST_SESSION.set(_pid(pid))
        return {"ok": True, "project_id": _pid(pid), "view": _draft_view(sess),
                "scenario_documents": scen,
                "selected_scenario_document_id": sel}


def _project_fork_payload(req):
    src = req.get("source_id")
    pid = req.get("project_id")
    name = req.get("name")
    with _DRAFT_LOCK:
        try:
            sess = _PROJECT_CACHE.fork(_pid(src), pid, name)
            scen, sel = _project_scenario_docs(pid)
        except Exception as ex:
            return _err(ex)
        _LAST_SESSION.set(pid)
        return {"ok": True, "project_id": pid,
                "projects": _PROJECT_CACHE.list_infos(),
                "view": _draft_view(sess),
                "scenario_documents": scen,
                "selected_scenario_document_id": sel}


def _project_rename_payload(req):
    pid = req.get("project_id")
    name = req.get("name")
    with _DRAFT_LOCK:
        try:
            saved = _PROJECT_CACHE.rename(_pid(pid), name)
        except Exception as ex:
            return _err(ex)
        return {"ok": True, "project_id": _pid(pid), "name": saved["name"],
                "revision": PJ._revision_of(saved),
                "projects": _PROJECT_CACHE.list_infos()}


def _project_trash_payload(req):
    pid = req.get("project_id")
    with _DRAFT_LOCK:
        try:
            _PROJECT_CACHE.trash(_pid(pid))
        except Exception as ex:
            return _err(ex)
        return {"ok": True, "project_id": _pid(pid),
                "projects": _PROJECT_CACHE.list_infos(),
                "trash": _PROJECT_CACHE.list_trash()}


def _project_migrate_payload(req):
    """POST /api/project/migrate: forward-only, identity-preserving upgrade of a
    legacy ForgeProjectV1 project to ForgeProjectV2 (v0.6-3). A V2 server can READ a
    V1 project but cannot SAVE over it (a project is never silently up/down-graded on
    save), so a pre-existing V1 project is effectively read-only until it is migrated.
    The migration re-opens the V1 world through the same validated reopen seam and
    re-serializes it as V2 -- moving NO SemanticArtifactID and preserving the
    revision -- then re-opens the live session so the project is Save-able."""
    pid = req.get("project_id")
    with _DRAFT_LOCK:
        try:
            migrated = _PROJECT_CACHE.migrate(_pid(pid))
        except Exception as ex:
            return _err(ex)
        return {"ok": True, "project_id": _pid(pid),
                "project_version": PJ.project_version_of(migrated),
                "project_revision": PJ._revision_of(migrated),
                "projects": _PROJECT_CACHE.list_infos()}


def _templates_list_payload():
    """GET /api/templates: the read-only catalog card summaries (v0.7-3). Loaded +
    identity-verified once at startup; if the catalog failed to load we surface the
    typed fault so the chooser can fail closed rather than show a corrupt template."""
    if _TEMPLATE_CATALOG is None:
        return _err(_TEMPLATE_ERROR)
    return {"ok": True, "count": _TEMPLATE_CATALOG.count,
            "templates": _TEMPLATE_CATALOG.summaries()}


def _template_get_payload(template_id):
    """GET /api/template?template_id=... : the FULL manifest for a preview (world
    source + layout + scenarios + guide). Previewing is project-free and read-only;
    the browser renders + runs the manifest against /api/run without creating any
    project, recovery journal, or last-session pointer."""
    if _TEMPLATE_CATALOG is None:
        return _err(_TEMPLATE_ERROR)
    m = _TEMPLATE_CATALOG.get(template_id)
    if m is None:
        return {"ok": False, "error": "unknown template_id %r" % template_id}
    return {"ok": True, "template": m}


def _template_preview_payload(req):
    """POST /api/template/preview: "Explore Template" (v0.7-3). Rebuilds the
    in-memory demo pseudo-session from a template's canonical world source and
    returns its full manifest + draft view. This is the read-only preview path:
    like the Golden Demo Explore, it writes NO project document, NO recovery
    journal, and NO last-session pointer -- the session lives only in
    _DEMO_SESSIONS. Run/Verify/Film/guide all work against it, but every
    authoring surface is locked in the browser until the user makes a copy."""
    template_id = req.get("template_id")
    if _TEMPLATE_CATALOG is None:
        return _err(_TEMPLATE_ERROR)
    m = _TEMPLATE_CATALOG.get(template_id)
    if m is None:
        return {"ok": False, "error": "unknown template_id %r" % template_id}
    with _DRAFT_LOCK:
        prog = W.lower_program(SG.desugar_core(m["canonical_world_source"]),
                               W.parse_wrl_core)
        # seed the curated manifest layout so the preview shows the template's
        # intended presentation (reconciled onto the graph, moves no identity).
        # CanvasSession owns the deep-copy + validation of the seed, so the
        # shared catalog layout object is never mutated by the session.
        sess = CG.new_session(prog, _DEMO_ID, layout=m["canvas_layout"])
        _DEMO_SESSIONS[_DEMO_ID] = sess
        return {"ok": True, "template_id": template_id, "template": m,
                "view": _draft_view(sess)}


def _template_use_payload(req):
    """POST /api/template/use: "Use Template" / "Make Editable Copy" (v0.7-3). This
    is the ONLY template action that creates state: it explicitly requests a new
    project id and instantiates an INDEPENDENT ForgeProjectV2 from the template's
    world source + scenario documents (preserving the template's initial
    semantic/scenario/replay identities), records a NON-AUTHORITATIVE
    created_from_template provenance sidecar, and sets the last-session pointer. The
    immutable template bytes are never touched; two projects made from one template
    are fully independent."""
    template_id = req.get("template_id")
    pid = req.get("project_id")
    name = req.get("name") or pid
    if _TEMPLATE_CATALOG is None:
        return _err(_TEMPLATE_ERROR)
    m = _TEMPLATE_CATALOG.get(template_id)
    if m is None:
        return {"ok": False, "error": "unknown template_id %r" % template_id}
    scenarios = [dict(s) for s in m["scenarios"]]
    with _DRAFT_LOCK:
        try:
            sess = _PROJECT_CACHE.create_from_source(
                pid, name, m["canonical_world_source"], scenarios=scenarios,
                selected_scenario_document_id=m["default_scenario_document_id"],
                layout=m["canvas_layout"])
        except Exception as ex:
            return _err(ex)
        _write_provenance(pid, template_id)
        _LAST_SESSION.set(pid)
        scen, sel = _project_scenario_docs(pid)
        return {"ok": True, "project_id": pid, "template_id": template_id,
                "created_from_template": _read_provenance(pid),
                "projects": _PROJECT_CACHE.list_infos(),
                "view": _draft_view(sess),
                "scenario_documents": scen,
                "selected_scenario_document_id": sel}


def _project_save_payload(req):
    """POST /api/project/save: SAVE the full authoring workspace (v0.5.1). Unlike
    a Commit (which activates a validated candidate world), Save persists EXACTLY
    what the author sees -- a valid OR invalid draft, the raw editor buffer, the
    undo + idempotency state, the layout and scenario selection -- and leaves the
    last-committed world as the active world. Reopening restores it byte-for-byte."""
    sid = req.get("session_id") or req.get("project_id") or "main"
    with _DRAFT_LOCK:
        _get_or_open_session(sid)          # ensure the session is open
        try:
            saved = _PROJECT_CACHE.persist(_pid(sid))
        except Exception as ex:
            return _err(ex)
        return {"ok": True, "project_id": _pid(sid),
                "project_revision": PJ._revision_of(saved),
                "projects": _PROJECT_CACHE.list_infos()}


def _project_trash_list_payload():
    """GET /api/project/trash: the restorable TrashEntryV1 tombstones (v0.5.1)."""
    with _DRAFT_LOCK:
        return {"ok": True, "trash": _PROJECT_CACHE.list_trash()}


def _project_restore_payload(req):
    """POST /api/project/restore: restore a trashed project from its tombstone
    (v0.5.1). Restores under the original id when free, else a caller-supplied
    `project_id`; a live-id collision is refused, never a silent overwrite."""
    trash_id = req.get("trash_id")
    new_pid = req.get("project_id")        # optional override when the id is taken
    with _DRAFT_LOCK:
        try:
            restored = _FORGE_STORE.restore(trash_id, new_pid)
            pid = restored["project_id"]
            sess = _PROJECT_CACHE.open(pid)
        except Exception as ex:
            return _err(ex)
        return {"ok": True, "trash_id": trash_id, "project_id": pid,
                "projects": _PROJECT_CACHE.list_infos(),
                "trash": _PROJECT_CACHE.list_trash(),
                "view": _draft_view(sess)}


# ---------------------------------------------- v0.5-5 project import/export
# A project is portable as a self-contained ForgeBundleV1 that packs the project
# document TOGETHER WITH every immutable object it references. Export builds the
# bundle from the on-disk document (the active world + scenario runtimes are
# derived from it, so it is complete even if the object stores were empty; the
# module world store lets it ALSO carry historical commit worlds best-effort).
# Import unpacks an (untrusted) bundle into the module's object + project stores,
# verifying closure + identity, then CREATES the project at revision 0 (never
# clobbers) and opens it. Pure store ops, serialized by _DRAFT_LOCK.
def _project_export_payload(req):
    pid = req.get("project_id")
    export_mode = req.get("export_mode", "full")   # v0.5.1: "full" | "thin"
    with _DRAFT_LOCK:
        try:
            doc = _FORGE_STORE.load(_pid(pid))
            bundle = BD.build_bundle(doc, world_store=_WORLD_STORE,
                                     export_mode=export_mode)
        except Exception as ex:
            return _err(ex)
        return {"ok": True, "project_id": _pid(pid),
                "export_mode": bundle.get("export_mode", "full"),
                "shallow_history": bundle.get("shallow_history", False),
                "bundle_id": BD.bundle_id(bundle), "bundle": bundle}


def _project_import_payload(req):
    bundle = req.get("bundle")
    pid = req.get("project_id")            # optional override id
    name = req.get("name")                 # optional override name
    with _DRAFT_LOCK:
        try:
            created = BD.import_bundle(bundle, _FORGE_STORE, _WORLD_STORE,
                                       _SCEN_STORE, project_id=pid, name=name)
            sess = _PROJECT_CACHE.open(created["project_id"])
        except Exception as ex:
            return _err(ex)
        return {"ok": True, "project_id": created["project_id"],
                "projects": _PROJECT_CACHE.list_infos(),
                "view": _draft_view(sess)}


# ------------------------------------------------ v0.6-0 crash-recovery journal
# A RecoveryJournalV1 is a SEPARATE, non-authoritative overlay that checkpoints the
# UNSAVED workspace to its own `.recovery/` store so an unexpected exit does not
# silently lose in-progress authoring. Writing a checkpoint never touches the
# durable project (no revision bump, no identity move, no candidate activation, no
# Fork/export effect); on reopen it is NEVER auto-applied. All pure store/cache
# ops, serialized by _DRAFT_LOCK. The client debounces `checkpoint` after authoring
# changes and, on load, reads `status` to offer Recover / Inspect / Discard.
# v0.6-2 startup/project UX: the last-opened project pointer. GET resolves it
# against the live store (self-healing a pointer at a trashed/removed project to
# None); the pointer is written server-side on every open/new/fork. No identity,
# no revision, no runtime effect -- pure "land where I left off" startup state.
def _session_payload():
    """GET /api/session: the last-opened project id to restore on startup, or None
    (a fresh install or a pointer whose project is gone). Self-heals a dangling
    pointer so startup never tries to reopen a project that no longer exists."""
    with _DRAFT_LOCK:
        pid = PJ.resolve_last_session(_LAST_SESSION, _FORGE_STORE)
        return {"ok": True, "last_project_id": pid}


def _dir_writable(path):
    """True iff `path` is an existing writable directory OR can be created (its
    nearest existing ancestor is writable). A pure probe -- it never writes."""
    p = os.path.abspath(path)
    while p and not os.path.isdir(p):
        parent = os.path.dirname(p)
        if parent == p:
            break
        p = parent
    return os.path.isdir(p) and os.access(p, os.W_OK)


def _health_payload():
    """GET /api/health: the SHALLOW release self-check (v0.6.5, FAST, boot-safe).
    Re-lowers the demo world FRESH -- bypassing _PROG_CACHE -- and confirms it
    STILL reproduces DEMO_WORLD_SEMANTIC_ID, so a running release proves its
    identity spine at runtime rather than trusting a startup-time constant. It
    folds NOTHING (no reducer run): it also reports whether the external project +
    recovery dirs are writable, the persisted project schema, whether the native
    reducer is available (else ref-only), and the bounded-cache occupancy. A pure
    read -- it COMPUTES ids and probes dirs, it never mints an id or folds a run.
    The DEEP verification (small ref + native fold + film parity + object-store
    round-trip) is a SEPARATE cancellable job (kind 'deep_health'), NEVER on boot."""
    fresh = W.lower_program(SG.desugar_core(DEMO_WORLD_SOURCE), W.parse_wrl_core)
    identity_ok = fresh.semantic_artifact_id == DEMO_WORLD_SEMANTIC_ID
    recovery_dir = os.path.join(os.path.dirname(os.path.abspath(_PROJECT_ROOT)),
                                ".recovery")
    return {"ok": True,
            "mode": "shallow",
            "bench_version": BENCH_VERSION,
            "skip_native": SKIP_NATIVE,
            "native_available": O.native_available(),
            "ic32_path": O.IC32,
            "demo_semantic_id": DEMO_WORLD_SEMANTIC_ID,
            "identity_ok": identity_ok,
            "templates_ok": _TEMPLATE_CATALOG is not None,
            "template_count": (_TEMPLATE_CATALOG.count
                               if _TEMPLATE_CATALOG is not None else 0),
            "project": {
                "dir": os.path.abspath(_PROJECT_ROOT),
                "writable": _dir_writable(_PROJECT_ROOT),
                "schema": PJ.PROJECT_V2_VERSION,
                "recovery_dir": recovery_dir,
                "recovery_writable": _dir_writable(recovery_dir),
            },
            "caches": {
                "prog": {"size": len(_PROG_CACHE), "cap": _PROG_CACHE.cap},
                "traj": {"size": len(_TRAJ_CACHE), "cap": _TRAJ_CACHE.cap},
            }}


def _deep_health_payload(progress=None, cancel=None):
    """The DEEP release verification -- run ONLY as an explicit cancellable job
    (kind 'deep_health'), NEVER on boot. It exercises the full runtime + storage
    spine on the small demo world: a reference fold, a native fold (when
    available) with film parity, and an object-store WRITE/READ/CLEANUP round-trip
    in a THROWAWAY temp store (so it never touches the user's project data). Every
    reported check is a fresh computation over the frozen identity spine; it mints
    no id and mutates no user state."""
    import tempfile
    import shutil
    result = {"ok": True, "mode": "deep", "bench_version": BENCH_VERSION}

    # (1) reference fold of the demo -> per-epoch films.
    if progress is not None:
        progress(0, 3, "ref_fold")
    prog, scen = _resolve_scenario(DEMO_WORLD_SOURCE, None)
    sem, _sd, ref_rows = _run_traj(DEMO_WORLD_SOURCE, O.ref_reduce, "ic_ref",
                                   None, progress=progress, cancel=cancel,
                                   phase="ref_fold")
    result["semantic_id"] = sem
    result["identity_ok"] = (sem == DEMO_WORLD_SEMANTIC_ID)
    result["ref_fold_ok"] = bool(ref_rows) and len(ref_rows) == 7
    result["epochs"] = len(ref_rows)

    # (2) native fold (when available) + film parity vs the reference.
    if O.native_available():
        if progress is not None:
            progress(1, 3, "native_fold")
        _s2, _d2, nat_rows = _run_traj(DEMO_WORLD_SOURCE, O.native_reduce,
                                       "ic32", None, progress=progress,
                                       cancel=cancel, phase="native_fold")
        result["native_fold_ok"] = True
        result["film_parity"] = ([r["film"] for r in ref_rows]
                                 == [r["film"] for r in nat_rows])
    else:
        result["native_fold_ok"] = None
        result["film_parity"] = None
        result["native_skipped"] = True

    # (3) object-store WRITE / READ / CLEANUP round-trip in a temp store.
    if progress is not None:
        progress(2, 3, "object_store")
    tmp = tempfile.mkdtemp(prefix="forge-deephealth-")
    try:
        store = ST.WorldObjectStore(os.path.join(tmp, "worlds"))
        oid = store.put(prog.sealed_artifact)
        got = store.get(oid)
        wrote = store.has(oid)
        roundtrip = (got.semantic_id == oid == sem)
        os.remove(store._path(oid))            # explicit cleanup
        cleaned = not store.has(oid)
        result["object_store_ok"] = bool(wrote and roundtrip and cleaned)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    result["ok"] = bool(result["ref_fold_ok"] and result["identity_ok"]
                        and result["object_store_ok"]
                        and result.get("film_parity") in (True, None))
    return result


def _recovery_checkpoint_payload(req):
    """POST /api/recovery/checkpoint: write a RecoveryJournalV1 for the current
    unsaved workspace. `scenario_documents` / `selected_scenario_document_id` come
    from the client's working scenario author (default to the saved scenarios when
    omitted); `dirty_reasons` records what changed."""
    sid = req.get("session_id") or req.get("project_id") or "main"
    if _is_demo(sid):
        # the demo is ephemeral -- there is nothing to recover, so no journal is
        # ever written (the frontend also guards scheduleCheckpoint on Explore).
        return {"ok": True, "project_id": _pid(sid), "checkpointed": False}
    with _DRAFT_LOCK:
        try:
            j = _PROJECT_CACHE.checkpoint(
                _pid(sid),
                scenario_documents=req.get("scenario_documents"),
                selected_scenario_document_id=req.get(
                    "selected_scenario_document_id"),
                dirty_reasons=req.get("dirty_reasons"))
        except Exception as ex:
            return _err(ex)
        return {"ok": True, "project_id": _pid(sid),
                "recovery_revision": j["recovery_revision"],
                "base_project_revision": j["base_project_revision"],
                "checkpointed_at": j["checkpointed_at"],
                "dirty_reasons": j["dirty_reasons"]}


def _recovery_status_payload(sid):
    """GET/POST /api/recovery/status: the PERSISTED recovery state (what a fresh
    restart would find) -- `saved` / `recovery_available` / `recovery_stale`."""
    with _DRAFT_LOCK:
        try:
            return {"ok": True, "project_id": _pid(sid),
                    "recovery": _PROJECT_CACHE.recovery_status(_pid(sid))}
        except Exception as ex:
            return _err(ex)


def _recovery_inspect_payload(req):
    """POST /api/recovery/inspect: a non-destructive summary of a journal (age,
    validity, active-vs-candidate id, source status, undo depth, scenario changes,
    staleness). Never applies the journal."""
    sid = req.get("session_id") or req.get("project_id") or "main"
    with _DRAFT_LOCK:
        try:
            return {"ok": True, "project_id": _pid(sid),
                    "inspect": _PROJECT_CACHE.inspect_recovery(_pid(sid))}
        except Exception as ex:
            return _err(ex)


def _recovery_recover_payload(req):
    """POST /api/recovery/recover: load the journal as the live UNSAVED dirty
    workspace (never auto-applied, candidate NOT activated, revision NOT advanced --
    the user must still Save). Refuses a stale journal (WRL_RECOVERY_STALE)."""
    sid = req.get("session_id") or req.get("project_id") or "main"
    with _DRAFT_LOCK:
        try:
            sess, j = _PROJECT_CACHE.recover(_pid(sid))
        except Exception as ex:
            return _err(ex)
        return {"ok": True, "project_id": _pid(sid), "recovered": True,
                "recovery_revision": j["recovery_revision"],
                "scenario_documents": j["scenario_documents"],
                "selected_scenario_document_id":
                    j["selected_scenario_document_id"],
                "dirty_reasons": j["dirty_reasons"],
                "view": _draft_view(sess)}


def _recovery_discard_payload(req):
    """POST /api/recovery/discard: drop the journal (explicit Discard). The saved
    project + any open session are untouched."""
    sid = req.get("session_id") or req.get("project_id") or "main"
    with _DRAFT_LOCK:
        try:
            _PROJECT_CACHE.discard_recovery(_pid(sid))
        except Exception as ex:
            return _err(ex)
        return {"ok": True, "project_id": _pid(sid),
                "recovery": _PROJECT_CACHE.recovery_status(_pid(sid))}


def _recovery_open_as_copy_payload(req):
    """POST /api/recovery/open-as-copy: materialize a STALE journal into a BRAND-NEW
    saved project (never an auto-merge). Opens the new project."""
    sid = req.get("session_id") or req.get("project_id") or "main"
    new_pid = req.get("new_project_id")
    name = req.get("name")
    with _DRAFT_LOCK:
        try:
            sess = _PROJECT_CACHE.open_as_recovered_copy(_pid(sid), new_pid, name)
        except Exception as ex:
            return _err(ex)
        return {"ok": True, "project_id": new_pid,
                "source_project_id": _pid(sid),
                "projects": _PROJECT_CACHE.list_infos(),
                "view": _draft_view(sess)}


# ------------------------------------------------------------- http handler
_STATIC = {"/": ("spinner_bench.html", "text/html; charset=utf-8"),
           "/spinner_bench.html": ("spinner_bench.html", "text/html; charset=utf-8"),
           "/spinner_bench.js": ("spinner_bench.js", "application/javascript; charset=utf-8"),
           "/spinner_bench.css": ("spinner_bench.css", "text/css; charset=utf-8")}


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass                                    # quiet

    def _send(self, code, body, ctype="application/json; charset=utf-8"):
        data = body if isinstance(body, bytes) else body.encode("utf-8")
        try:
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
        except (BrokenPipeError, ConnectionResetError):
            # The client went away before/while we wrote the response. With
            # v0.6-1 the compute is a background job decoupled from this socket,
            # so a dropped connection is benign: swallow it (no noisy traceback)
            # and let the handler return. The job keeps running / is already done.
            self.close_connection = True

    def _json(self, obj, code=200):
        self._send(code, json.dumps(obj), "application/json; charset=utf-8")

    def do_GET(self):
        path = self.path.split("?", 1)[0]
        if path == "/api/health":
            # v0.6-4 release self-check: re-lower the demo world fresh + confirm
            # it reproduces DEMO_WORLD_SEMANTIC_ID; report version + cache stats.
            return self._json(_health_payload())
        if path == "/api/demo":
            return self._json({"src": DEMO_WORLD_SOURCE,
                               "script": [e["label"]
                                          for e in GOLDEN_DEMO_SCENARIO["epochs"]],
                               "skip_native": SKIP_NATIVE})
        if path == "/api/scenario":
            # The immutable ScenarioV1 presets for the demo world + their
            # ScenarioDigests -- the presets an Author-mode edit copies. Two are
            # shipped: `golden` (the Golden ADMIT Demo) and `bench` (the ADMIT
            # Acceptance Bench that walks the seven roadmap behaviours). `scenario`
            # / `scenario_digest` remain the golden default for existing callers.
            try:
                sem = DEMO_WORLD_SEMANTIC_ID
                golden = GOLDEN_DEMO_SCENARIO
                bench = ACCEPTANCE_BENCH_SCENARIO
                presets = {
                    "golden": {"id": "golden", "label": "Golden ADMIT Demo",
                               "scenario": golden,
                               "scenario_digest": SC.scenario_digest(golden)},
                    "bench": {"id": "bench", "label": "ADMIT Acceptance Bench",
                              "scenario": bench,
                              "scenario_digest": SC.scenario_digest(bench)},
                }
                return self._json({
                    "ok": True, "presets": presets, "default": "golden",
                    "scenario": golden,
                    "scenario_digest": presets["golden"]["scenario_digest"],
                    "world_semantic_id": sem})
            except Exception as ex:
                return self._json(_err(ex))
        if path == "/api/draft":
            # The live draft-convergence view (lazy-opens the session on the demo
            # world). Pure editor state -- no runtime lock.
            q = self.path.split("?", 1)[1] if "?" in self.path else ""
            sid = dict(p.split("=", 1) for p in q.split("&") if "=" in p
                       ).get("session_id") if q else None
            return self._json(_draft_payload(sid))
        if path == "/api/draft/history":
            # The session commit log + undo depth (commit/undo history panel).
            q = self.path.split("?", 1)[1] if "?" in self.path else ""
            sid = dict(p.split("=", 1) for p in q.split("&") if "=" in p
                       ).get("session_id") if q else None
            return self._json(_draft_history_payload(sid))
        if path == "/api/templates":
            # v0.7-3: the immutable template catalog card summaries.
            return self._json(_templates_list_payload())
        if path == "/api/template":
            # v0.7-3: one full template manifest for a project-free preview.
            q = self.path.split("?", 1)[1] if "?" in self.path else ""
            tid = dict(p.split("=", 1) for p in q.split("&") if "=" in p
                       ).get("template_id") if q else None
            return self._json(_template_get_payload(tid))
        if path == "/api/projects":
            # v0.5-4 Library: the named, persisted project list.
            return self._json(_projects_payload())
        if path == "/api/session":
            # v0.6-2 startup: the last-opened project id to restore (or None).
            return self._json(_session_payload())
        if path == "/api/project/trash":
            # v0.5.1: the restorable trash tombstones.
            return self._json(_project_trash_list_payload())
        if path == "/api/recovery/status":
            # v0.6-0: the PERSISTED crash-recovery state for a project.
            q = self.path.split("?", 1)[1] if "?" in self.path else ""
            sid = dict(p.split("=", 1) for p in q.split("&") if "=" in p
                       ).get("session_id") if q else None
            return self._json(_recovery_status_payload(sid))
        if path == "/api/jobs":
            # v0.6-1: recent runtime jobs, newest first (bounded ring).
            return self._json(_jobs_list_payload())
        if path.startswith("/api/jobs/"):
            # v0.6-1: poll a single job for state / progress / result.
            return self._json(_job_get_payload(path[len("/api/jobs/"):]))
        if path in _STATIC:
            fn, ctype = _STATIC[path]
            fp = os.path.join(HERE, fn)
            if not os.path.exists(fp):
                return self._send(404, "not found", "text/plain")
            with open(fp, "rb") as fh:
                return self._send(200, fh.read(), ctype)
        return self._send(404, "not found", "text/plain")

    def do_POST(self):
        path = self.path.split("?", 1)[0]
        try:
            n = int(self.headers.get("Content-Length", 0))
            req = json.loads(self.rfile.read(n) or b"{}")
        except Exception as ex:
            _dev_log(FE.ERROR_PRESENTATION_VERSION, ex)
            pres = FE.bad_request("The request body could not be parsed as JSON.")
            return self._json({"ok": False, "error": pres["message"],
                               "error_presentation": pres}, 400)
        src = req.get("src", DEMO_WORLD_SOURCE)
        # Pure editor endpoints -- NO ic-reducer globals -- stay responsive even
        # while a run/verify holds the runtime lock (preflight item 2).
        if path == "/api/lower":
            return self._json(_lower_payload(src))
        if path == "/api/diff":
            return self._json(_diff_payload(req.get("a", DEMO_WORLD_SOURCE),
                                            req.get("b", DEMO_WORLD_SOURCE)))
        if path == "/api/complete":
            return self._json(_complete_payload(src, req.get("offset", 0)))
        if path == "/api/scenario":
            # Pure validate + digest for the Author-mode editor (no run).
            return self._json(_scenario_payload(src, req.get("scenario")))
        # v0.4-4c draft convergence -- text -> atomic ReplaceWorldSourceV1 -> canvas.
        # Pure editor state (no ic-reducer), serialized only by _DRAFT_LOCK.
        if path == "/api/draft/source":
            return self._json(_draft_source_payload(req))
        if path == "/api/draft/reset":
            return self._json(_draft_reset_payload(req.get("session_id"),
                                                   req.get("src")))
        if path == "/api/draft/undo":
            return self._json(_draft_undo_payload(req.get("session_id")))
        if path == "/api/draft/commit":
            return self._json(_draft_commit_payload(req))
        # v0.5-4 Library management (new/open/fork/rename/trash). Pure store/cache
        # operations, serialized only by _DRAFT_LOCK.
        if path == "/api/project/new":
            return self._json(_project_new_payload(req))
        if path == "/api/project/open":
            return self._json(_project_open_payload(req))
        if path == "/api/project/fork":
            return self._json(_project_fork_payload(req))
        if path == "/api/project/rename":
            return self._json(_project_rename_payload(req))
        if path == "/api/project/trash":
            return self._json(_project_trash_payload(req))
        if path == "/api/project/migrate":
            # v0.6-3: forward-only, identity-preserving V1 -> V2 project migration
            # (closes the read-only gap for a legacy project under the V2 package).
            return self._json(_project_migrate_payload(req))
        if path == "/api/template/preview":
            # v0.7-3: "Explore Template" -- read-only preview, rebuilds the
            # in-memory demo session; creates NO project/recovery/pointer.
            return self._json(_template_preview_payload(req))
        if path == "/api/template/use":
            # v0.7-3: "Use Template" -- the ONLY template action that creates a
            # project (an independent ForgeProjectV2 preserving template identities).
            return self._json(_template_use_payload(req))
        if path == "/api/project/save":
            # v0.5.1: Save the COMPLETE workspace (invalid draft included),
            # distinct from Commit (which activates a validated candidate world).
            return self._json(_project_save_payload(req))
        if path == "/api/project/restore":
            # v0.5.1: restore a trashed project from its tombstone.
            return self._json(_project_restore_payload(req))
        if path == "/api/project/export":
            return self._json(_project_export_payload(req))
        if path == "/api/project/import":
            return self._json(_project_import_payload(req))
        # v0.6-0 crash-recovery journal (separate `.recovery/` overlay; never
        # advances the project revision, moves identity or activates a candidate).
        if path == "/api/recovery/checkpoint":
            return self._json(_recovery_checkpoint_payload(req))
        if path == "/api/recovery/status":
            return self._json(_recovery_status_payload(
                req.get("session_id") or req.get("project_id")))
        if path == "/api/recovery/inspect":
            return self._json(_recovery_inspect_payload(req))
        if path == "/api/recovery/recover":
            return self._json(_recovery_recover_payload(req))
        if path == "/api/recovery/discard":
            return self._json(_recovery_discard_payload(req))
        if path == "/api/recovery/open-as-copy":
            return self._json(_recovery_open_as_copy_payload(req))
        # v0.6-1 runtime jobs: enqueue a cancellable run/verify fold, poll it via
        # GET /api/jobs/<id>, cancel via POST /api/jobs/<id>/cancel. The compute
        # is decoupled from this request socket (a disconnect never aborts it).
        if path == "/api/jobs":
            return self._json(_job_submit_payload(req))
        if path.startswith("/api/jobs/") and path.endswith("/cancel"):
            job_id = path[len("/api/jobs/"):-len("/cancel")]
            return self._json(_job_cancel_payload(job_id))
        # Runtime endpoints fold the ic-reducer, which resets module-global
        # interpreter state -- serialize ONLY these.
        if path in ("/api/run", "/api/verify"):
            scenario = req.get("scenario")      # optional ScenarioV1 run input
            with _PIPELINE_LOCK:
                if path == "/api/run":
                    return self._json(_run_payload(src, scenario))
                return self._json(_verify_payload(
                    src, oracle=bool(req.get("oracle")), scenario=scenario))
        return self._json({"ok": False, "error": "unknown endpoint"}, 404)


def main():
    srv = ThreadingHTTPServer((HOST, PORT), Handler)
    native = "OFF (TRVM_SKIP_NATIVE=1)" if SKIP_NATIVE else "ON"
    print(f"[spinner-bench] http://{HOST}:{PORT}/  (native verify: {native})")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        srv.shutdown()


if __name__ == "__main__":
    main()
