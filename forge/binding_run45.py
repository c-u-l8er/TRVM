"""binding_run45.py -- Slice B, Commit 0: the three-way CanvasGraphV1 importer.

WRL Core 0.1.3 §15.1.1 / §16.3. `CanvasGraphV1` is frozen as an immutable,
retired legacy COMBINED document; the one thing preserved is a named
compatibility importer that splits it three ways:

    import_canvas_graph_v1(canvas)
        -> LegacyCanvasImportV1(world, scenario, presentation)

The ruling names five things this battery must prove. They are rows L1, L2, L3,
L4 and L6 below; the remaining rows exist because building it surfaced cases the
five do not reach.

  L1  SEMANTIC-ID PRESERVATION -- the world half seals to the SAME
      SemanticArtifactID (and the same artifact BYTES) as the whole legacy
      document, because run inputs and presentation were never in it.
  L2  RUN-INPUT PRESERVATION -- `periods` and the ORDERED epoch claim batches
      survive exactly; every claim recovers its original payload tuple.
  L3  PRESENTATION INERTNESS -- corrupting every presentation block in the
      legacy document moves neither the world identity nor the ScenarioDigest,
      and DOES move the presentation output (an inertness claim that cannot
      distinguish "inert" from "ignored" proves nothing).
  L4  STRICT THREE-WAY SEPARATION -- structural, not by inspection: the world
      carries no run inputs and no presentation values, the scenario carries no
      world structure, and the presentation is a CanvasLayoutV1 which rejects
      run inputs and semantic config by its own gate.
  L5  WORLD BINDING -- the emitted scenario is bound to the world it came from,
      so the import cannot produce an already-stale pair.
  L6  LOSSY EXPORT IS A TYPED REJECTION -- both ways a construct can be lost:
      one V1 REJECTS (`Mailbox`) and one V1 SILENTLY DROPS.
  L7  ZERO-PERIOD DOCUMENT -- `periods == 0` <-> `scenario is None`.
  L8  PURITY -- the importer is idempotent and does not mutate its input.
  L9  RUNTIME-FILM PRESERVATION -- the film folded from the SPLIT is
      byte-identical to the film folded from the whole legacy document.
  L10 NATIVE -- ic_ref == ic32 == golden, over the split.

On the negative control for the silent-drop half of L6
------------------------------------------------------
The construct that will exercise that path for real is `AsyncRouteDecl`, which
does not exist yet -- it is Commit 2, and this is Commit 0. Inventing a fake
construct would prove nothing about the real one: a fake has no canonical form,
so nothing would carry it into the comparison in the first place. The control
therefore REMOVES a construct that does exist (it patches the V1 emitter to drop
connections) and proves the detector fires. That tests the mechanism the real
construct will meet, rather than a mock of the construct.
"""
import copy
import os
import sys
import time

sys.setrecursionlimit(2_000_000)
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import admit as AD
import wrl_canonical as WC
import wrl_canvas as CV
import wrl_ir as W
import wrl_legacy as LG
import wrl_scenario as WS
import binding_run3o as O
import binding_run5 as B5
from fixture import init_state_v6

SKIP_NATIVE = os.environ.get("TRVM_SKIP_NATIVE") == "1"

# The battery defines its OWN legacy source rather than reusing `B5.CORE_SRC`,
# for one reason: B5's document has exactly ONE claim per epoch, and a law about
# ORDERED claim batches cannot be tested against batches of size one. Mutation
# testing caught this -- reversing intra-epoch claim order left every row green.
#
# Epoch 1 therefore carries TWO claims. Their order carries no RUNTIME meaning
# (ADMIT accepts a batch atomically, and `canonicalize_scenario_v1` sorts claims
# before hashing, so a reorder does not move the ScenarioDigest either). That is
# exactly why L2 asserts the order POSITIONALLY rather than through the digest:
# the digest is the wrong instrument here, because it is designed not to see
# this. An importer that silently reordered what the author wrote would be
# invisible to every identity in the system, and would still be wrong -- the
# document round-trips through an editor, not only through a reducer.
LEGACY_SRC = """
profile forge.world.core.v1
periods 3

[pulser:p0](mode=periodic, period=2, phase=0){sig_out}
[door:d0]{sig_in}
[spinner:sp](w=8, n=4, rotor=16.0.0.0, configurable){sig_in, socket}
[orb:ob]{pose}

[pulser:p0] --sig--> [spinner:sp]
[spinner:sp] --socket--> [orb:ob]

[epoch:1] @1,1 SetRotor sp 16.0.10.0
[epoch:1] @2,7 SetRotor sp 64.0.0.1
[epoch:2] @2,2 ResetFault ob
[epoch:3] @3,3 SetRotor zz 16.0.30.0
"""

_FAILED = []


def rep(ok, label):
    print("  [%s] %s" % ("PASS" if ok else "FAIL", label))
    if not ok:
        _FAILED.append(label)


def _legacy_canvas():
    """The legacy combined document under test: a `canvas.v1` carrying world
    content, run inputs and presentation together -- exactly the conflation the
    v0.4-0 boundary repealed and this importer exists to undo."""
    base = W.lower_program(LEGACY_SRC, W.parse_wrl_legacy_document)
    return base, CV.graph_to_canvas(base.graph)


def _typed(fn, code):
    """Run `fn`; True iff it raised the expected typed WRL error."""
    try:
        fn()
    except WC.WrlValidationError as ex:
        return ex.code == code
    return False


# ------------------------------------------------------------------- L1
def l1_semantic_id(base, canvas):
    imp = LG.import_canvas_graph_v1(canvas)
    whole = WC.semantic_artifact_id(base.artifact)
    half = W.lower_graph(imp.world)
    ok = (imp.world_semantic_id == whole
          and WC.semantic_artifact_id(half.artifact) == whole
          # bytes, not just the digest: two artifacts could in principle agree
          # on an id we computed wrong, and the bytes are what a second
          # implementation would read.
          and WC.serialize_artifact(half.artifact)
          == WC.serialize_artifact(base.artifact))
    # NEGATIVE CONTROL: the id is not preserved by being insensitive. A world
    # edit must move it, or L1 would pass for an importer that returned a
    # constant.
    moved = copy.deepcopy(imp.world)
    moved.nodes = [(r, n, dict(c, rotor=(1, 2, 3, 4)) if r == "Spinner" else c)
                   for r, n, c in moved.nodes]
    ok = ok and W.lower_graph(moved).semantic_artifact_id != whole
    rep(ok, "L1) the world half seals to the SAME SemanticArtifactID and the "
            "SAME artifact bytes as the whole legacy document")
    return imp


# ------------------------------------------------------------------- L2
def l2_run_inputs(base, canvas, imp):
    g = CV.canvas_to_graph(canvas)
    scen = imp.scenario
    ok = scen is not None and len(scen["epochs"]) == canvas["periods"] == 3
    # The fixture must actually contain a batch big enough to HAVE an order.
    # Asserted rather than assumed, so that simplifying LEGACY_SRC later trips
    # this row instead of quietly making the order law vacuous again.
    ok = ok and any(len(ep["claims"]) >= 2 for ep in scen["epochs"])
    if ok:
        for i, ep in enumerate(scen["epochs"]):
            src = g.batches[i]
            ok = ok and ep["epoch"] == i + 1 and len(ep["claims"]) == len(src)
            for c_out, c_in in zip(ep["claims"], src):
                # ORDER is asserted positionally, and the payload is asserted by
                # ROUND-TRIP through the scenario's own reader rather than by
                # re-deriving the tuple here -- a second derivation would be a
                # fork of `_payload_tuple` and would agree with it by accident.
                ok = (ok
                      and c_out["writer_id"] == c_in["writer_id"]
                      and c_out["sequence"] == c_in["sequence"]
                      and WS._payload_tuple(c_out) == tuple(c_in["payload"]))
    # NEGATIVE CONTROL: losing a claim must be visible in the run-input
    # identity, or "preserved exactly" is untested.
    thin = copy.deepcopy(scen)
    thin["epochs"][0]["claims"] = []
    ok = ok and WS.scenario_digest(thin) != WS.scenario_digest(scen)
    # SECOND NEGATIVE CONTROL, and the reason L2 is written positionally: a
    # reordered batch is a DIFFERENT document that the ScenarioDigest cannot
    # see, because canonicalization sorts claims before hashing. Asserting both
    # halves here records that the digest was consulted and found blind, rather
    # than leaving a reader to assume it was the instrument used.
    flipped = copy.deepcopy(scen)
    flipped["epochs"][0]["claims"].reverse()
    ok = (ok and flipped["epochs"][0]["claims"] != scen["epochs"][0]["claims"]
          and WS.scenario_digest(flipped) == WS.scenario_digest(scen))
    rep(ok, "L2) periods and the ORDERED epoch claim batches survive exactly; "
            "dropping a claim moves the ScenarioDigest, reordering one does "
            "not -- so order is asserted positionally")


# ------------------------------------------------------------------- L3
def l3_presentation_inert(canvas, imp):
    ugly = copy.deepcopy(canvas)
    for n in ugly["nodes"]:
        n["presentation"] = {"x": -9999, "y": -9999, "color": "#000000",
                             "collapsed": True, "junk": [1, 2, 3]}
    for c in ugly["connections"]:
        c["presentation"] = {"paint": "#000000", "control_points": [[7, 7]]}
    imp2 = LG.import_canvas_graph_v1(ugly)
    ok = (imp2.world_semantic_id == imp.world_semantic_id
          and WS.scenario_digest(imp2.scenario)
          == WS.scenario_digest(imp.scenario))
    # NEGATIVE CONTROL: the presentation half must actually CHANGE. Without
    # this, an importer that discarded presentation entirely would pass the
    # inertness rows -- inert and ignored are different claims.
    ok = ok and imp2.presentation != imp.presentation
    rep(ok, "L3) corrupting every presentation block moves NEITHER the world "
            "identity nor the ScenarioDigest, and DOES move the presentation")


# ------------------------------------------------------------------- L4
def l4_separation(canvas, imp):
    world, scen, pres = imp

    # (a) the world carries no run inputs, and none of the presentation VALUES.
    world_bytes = WC.serialize_artifact(W.lower_graph(world).artifact)
    colours = {n["presentation"]["color"] for n in canvas["nodes"]}
    ok = (world.periods == 0 and world.batches == []
          and not any(c.encode() in world_bytes for c in colours))

    # (b) the scenario carries run inputs ONLY -- its key set is exactly
    #     ScenarioV1's, so no world structure can be riding along.
    ok = ok and set(scen) == set(WS._TOP_KEYS)
    ok = ok and not ({"nodes", "edges", "connections", "presentation"} & set(scen))

    # (c) the presentation is a CanvasLayoutV1, whose OWN gate is what rejects
    #     run inputs and semantic config -- the separation is structural, not a
    #     promise this battery makes on the layout's behalf.
    ok = ok and CV.validate_layout_v1(pres) is pres
    ok = ok and pres["layout_version"] == CV.LAYOUT_VERSION

    # NEGATIVE CONTROL: that gate is real. Run inputs put back into the
    # presentation are a typed rejection, not a tolerated extra key.
    leaky = dict(pres, periods=3)
    ok = ok and _typed(lambda: CV.validate_layout_v1(leaky),
                       WC.WRL_UNSUPPORTED_FEATURE)
    rep(ok, "L4) strict three-way separation: world has no run inputs and no "
            "presentation values; scenario has no world structure; the layout "
            "gate rejects run inputs")


# ------------------------------------------------------------------- L5
def l5_binding(imp):
    ok = True
    try:
        WS.check_world_binding(imp.scenario, imp.world_semantic_id)
    except WC.WrlValidationError:
        ok = False
    other = "sem-" + ("0" * 64)
    ok = ok and _typed(lambda: WS.check_world_binding(imp.scenario, other),
                       WS.WRL_SCENARIO_WORLD_MISMATCH)
    rep(ok, "L5) the emitted scenario is bound to the world it came from; a "
            "foreign world is WRL_SCENARIO_WORLD_MISMATCH")


# ------------------------------------------------------------------- L6
def l6_lossy_export(base):
    # (a) faithful export succeeds -- otherwise "it refuses lossy exports" is
    #     satisfied by refusing everything.
    ok = LG.export_canvas_graph_v1(base.graph)["canvas_version"] == \
        CV.CANVAS_VERSION
    ok = ok and LG.canvas_v1_export_loss(base.graph) == ()

    # (b) V1 REJECTS it: `Mailbox` is a registry role with no canvas.v1 column.
    mb = copy.deepcopy(base.graph)
    mb.nodes.append(("Mailbox", "mb", {"w": 8, "cap": 4}))
    ok = ok and _typed(lambda: LG.export_canvas_graph_v1(mb),
                       LG.WRL_LEGACY_EXPORT_LOSSY)
    # and the reason it gives is TRUE. §18 consequence 5: a rejection must not
    # deny the existence of a role the registry defines. canvas.v1 said exactly
    # that until this commit.
    reason = LG.canvas_v1_export_loss(mb)[0]
    ok = ok and "no canvas.v1 representation" in reason
    ok = ok and "not in the frozen v1 registry" not in reason

    # (c) V1 SILENTLY DROPS it. See the module docstring: the control removes a
    #     construct that exists rather than mocking one that does not.
    real_emit = CV.graph_to_canvas

    def dropping_emit(g):
        c = real_emit(g)
        c["connections"] = []
        return c

    CV.graph_to_canvas = dropping_emit
    try:
        loss = LG.canvas_v1_export_loss(base.graph)
        ok = ok and loss and any("round-trip" in r for r in loss)
        ok = ok and _typed(lambda: LG.export_canvas_graph_v1(base.graph),
                           LG.WRL_LEGACY_EXPORT_LOSSY)
    finally:
        CV.graph_to_canvas = real_emit
    ok = ok and LG.canvas_v1_export_loss(base.graph) == ()
    rep(ok, "L6) a faithful export succeeds; a REJECTED construct and a "
            "SILENTLY DROPPED one are both WRL_LEGACY_EXPORT_LOSSY")


# ------------------------------------------------------------------- L7
def l7_zero_periods(canvas):
    empty = copy.deepcopy(canvas)
    empty["periods"], empty["batches"] = 0, []
    imp = LG.import_canvas_graph_v1(empty)
    # None, not an empty ScenarioV1: ScenarioV1 requires a non-empty `epochs`
    # by construction, so a synthesised one would ADD a period the document did
    # not have. `periods == 0 <-> scenario is None` is the preservation law here.
    ok = (imp.scenario is None
          and imp.world_semantic_id
          == LG.import_canvas_graph_v1(canvas).world_semantic_id
          and CV.validate_layout_v1(imp.presentation) is imp.presentation)
    rep(ok, "L7) a zero-period legacy document yields scenario=None and the "
            "SAME world identity -- no period is invented")


# ------------------------------------------------------------------- L8
def l8_purity(canvas):
    before = copy.deepcopy(canvas)
    a = LG.import_canvas_graph_v1(canvas)
    b = LG.import_canvas_graph_v1(canvas)
    ok = (canvas == before                       # input untouched
          and a.world_semantic_id == b.world_semantic_id
          and a.scenario == b.scenario
          and a.presentation == b.presentation)
    # the world half is a COPY, not an alias of the caller's graph
    a.world.nodes.append(("Orb", "spurious", {}))
    ok = ok and len(CV.canvas_to_graph(canvas).nodes) == len(before["nodes"])
    rep(ok, "L8) the importer is idempotent and mutates neither its input nor "
            "any graph it hands back")


# ------------------------------------------------------------------- L9/L10
def _fold(fx, batches):
    """Fold `batches` over fixture `fx`, returning the Film v0.7 rows, plus the
    golden reference rows -- the same harness binding_run6 V12 uses."""
    import admit_ic as X
    from compiler import enc_state_v6
    world0 = init_state_v6(fx)
    claim0 = AD.init_claimstate()
    gold = O._golden_traj(claim0, world0, batches, epoch0=1)
    term = O._build_fold(batches, X.enc_factvec([], O.CAP),
                         X.enc_factvec([], O.RCAP), enc_state_v6(fx, world0))
    K = len(batches)
    dec_ref = O._decode_fold(O.norm(term), K)
    claims_ref = O._project_claims(dec_ref, epoch0=1)
    films_ref = [O._film(dec_ref[e][0], claims_ref[e], e + 1) for e in range(K)]
    films_gold = [O._film(gold[e][0], gold[e][1], e + 1) for e in range(K)]
    return term, K, films_ref, films_gold


def l9_l10_films(canvas, imp):
    # (a) the whole legacy document, folded directly.
    whole = CV.lower_canvas(canvas)
    batches_whole = B5._batches_from_program(whole)

    # (b) the SPLIT: world from the world half, run inputs from the scenario.
    split = W.lower_graph(imp.world)
    faults, script = WS.scenario_to_script(imp.scenario)
    batches_split = [b for _label, b in script]

    ok = (B5._fx_sig(split.fixture) == B5._fx_sig(whole.fixture)
          == B5._fx_sig(O.FX)
          and faults == ()          # canvas.v1 never carried initial faults
          and len(batches_split) == len(batches_whole))

    _t, _k, films_w, gold_w = _fold(whole.fixture, batches_whole)
    term, K, films_s, gold_s = _fold(split.fixture, batches_split)
    ok = ok and films_s == films_w == gold_s == gold_w
    rep(ok, "L9) the film folded from the SPLIT is byte-identical to the film "
            "folded from the whole legacy document (%d epochs, ic_ref==golden)"
            % K)

    if SKIP_NATIVE:
        print("       (native skipped: TRVM_SKIP_NATIVE=1)")
        return False
    dec_nat = O._decode_fold(O.native(term), K)
    claims_nat = O._project_claims(dec_nat, epoch0=1)
    films_nat = [O._film(dec_nat[e][0], claims_nat[e], e + 1) for e in range(K)]
    nat_ok = films_nat == films_s == gold_s
    rep(nat_ok, "L10) ic_ref == ic32 == golden over the SPLIT world+scenario")
    return nat_ok


def main():
    print("[BINDING wrl-sliceB-c0] the three-way CanvasGraphV1 importer")
    t0 = time.time()
    base, canvas = _legacy_canvas()
    imp = l1_semantic_id(base, canvas)
    l2_run_inputs(base, canvas, imp)
    l3_presentation_inert(canvas, imp)
    l4_separation(canvas, imp)
    l5_binding(imp)
    l6_lossy_export(base)
    l7_zero_periods(canvas)
    l8_purity(canvas)
    native_ok = l9_l10_films(canvas, imp)

    print()
    if _FAILED:
        for f in _FAILED:
            print("  FAILED: %s" % f)
        print("VERDICT: FAILURES (%d) in %ds" % (len(_FAILED), time.time() - t0))
        return 1
    mode = ("PASS_REF_ONLY (native skipped)" if SKIP_NATIVE
            else ("PASS_REF_AND_NATIVE" if native_ok
                  else "REF_ONLY (native MISMATCH)"))
    print("VERDICT: %s -- Slice B Commit 0 closed in %ds"
          % (mode, time.time() - t0))
    return 0 if (SKIP_NATIVE or native_ok) else 1


if __name__ == "__main__":
    sys.exit(main())
