"""wrl_legacy.py -- the CanvasGraphV1 compatibility boundary (Slice B, Commit 0).

WRL Core 0.1.3 §15.1.1 froze `CanvasGraphV1` as an immutable, retired legacy
COMBINED document: it carries world content, run inputs (`periods` / `batches`)
and presentation in one place, which is exactly the conflation the v0.4-0
document boundary repealed. The ruled disposition is not to migrate it but to
preserve ONE named compatibility importer that splits it THREE ways.

    import_canvas_graph_v1(canvas)
        -> LegacyCanvasImportV1(world, scenario, presentation)

      world         the canonical WORLD projection, run inputs EXCLUDED
      scenario      a `ScenarioV1` preserving `periods` and the ordered epoch
                    claim batches EXACTLY (None iff the document had no periods)
      presentation  a `CanvasLayoutV1`

Three, not two. A two-way split (world + everything else) would fold
presentation into world content, and presentation reaching the world is the one
thing that moves a `SemanticArtifactID` that must not move.

Why this lives in a NEW module rather than in `wrl_canvas.py`
-------------------------------------------------------------
Because §15.1.1 point 1 says CanvasGraphV1 is immutable and retired, and point 2
forbids new semantic fields on it. An importer added INSIDE the retired module
would be an edit to the frozen surface, and the next construct would be added
there too "since the file is already open". The boundary is easier to keep when
it is a file boundary: this module DEPENDS on `wrl_canvas`, and `wrl_canvas`
knows nothing about it.

Why the export check is COMPUTED and not a list of forbidden constructs
-----------------------------------------------------------------------
§15.1.1 point 6 requires that exporting a route-bearing successor back to V1 be
a TYPED rejection rather than a V1 document that silently drops the routes. The
obvious implementation is a list of constructs V1 cannot hold, checked on the
way out. That implementation is a fork of V1's vocabulary -- a second spelling
of one definition, which is the defect class that produced four separate bugs in
the L-0 round (see WRL Core §18) -- and it has a worse property besides: it must
be EDITED every time a construct is added, so the one commit that introduces
`AsyncRouteDecl` is exactly the commit that can forget to add it, and the
forgetting is silent.

So `export_canvas_graph_v1` names no constructs at all. It emits the V1
document, reads it back through V1's own reader, and compares. Anything V1
cannot represent fails one of two ways and both are caught:

  * V1 REJECTS it -- e.g. `Mailbox`, a registry role with no entry in V1's
    frozen `_CFG_KEYS` table. The typed rejection is wrapped, not swallowed.
  * V1 SILENTLY DROPS it -- a construct with no field to land in. The
    round-trip then loses it, and the recomputed identity no longer matches.

The second case is the dangerous one and the reason the check is a round-trip
rather than a validation: a dropped field passes every validator ever written,
because there is nothing left to validate. `AsyncRouteDecl` will be rejected by
this function on the day it is introduced, with no edit to this file.
"""
import copy
import os
import sys
from collections import namedtuple

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import wrl_canonical as WC
import wrl_canvas as WV
import wrl_ir as W
import wrl_scenario as WS

LEGACY_IMPORT_VERSION = "legacy.canvas.import.v1"

# A legacy document that cannot be split faithfully. Distinct from
# WRL_BAD_SCENARIO / WRL_MALFORMED_ARTIFACT because the fault is neither the
# world's nor the scenario's -- it is the CONFLATED document's, and an author
# reading the message needs to know the import is what failed.
WRL_LEGACY_IMPORT = "WRL_LEGACY_IMPORT"
# An export that would produce a V1 document meaning less than its input.
WRL_LEGACY_EXPORT_LOSSY = "WRL_LEGACY_EXPORT_LOSSY"

# The run-input fields of a canonical graph -- named by EXCLUSION (as in
# binding_run6) so that a field a later slice adds is treated as world content
# by default rather than silently escaping the world projection.
RUN_INPUT_FIELDS = ("periods", "batches")


class LegacyCanvasImportV1(namedtuple("LegacyCanvasImportV1",
                                      "world scenario presentation")):
    """The three-way split of one legacy `canvas.v1` document.

    `world` is a `WrlGraph` (canonical, run inputs empty), `scenario` is a
    `ScenarioV1` dict or None, `presentation` is a `CanvasLayoutV1` dict. The
    three are deliberately three DIFFERENT types: nothing downstream can pass
    one where another is wanted, which is the structural half of the separation
    the battery asserts semantically."""
    __slots__ = ()

    @property
    def world_semantic_id(self):
        """The `SemanticArtifactID` of the world half. Equal to the id of the
        whole legacy document, because run inputs and presentation were never
        in it -- that equality is the importer's central claim (battery L1)."""
        return W.lower_graph(self.world).semantic_artifact_id


# ------------------------------------------------------------------ helpers
def _world_projection(g):
    """Every canonical field EXCEPT the run inputs, as a comparable tuple."""
    cg = WC.canonicalize_graph(g)
    return tuple((f, getattr(cg, f)) for f in sorted(vars(cg))
                 if f not in RUN_INPUT_FIELDS)


def _run_inputs(g):
    """The run inputs alone, as a comparable value."""
    cg = WC.canonicalize_graph(g)
    return (cg.periods, [list(b) for b in cg.batches])


def _world_only(g):
    """A copy of `g` with the run inputs REMOVED rather than emptied in place.

    Emptying in place would mutate the caller's graph, and the caller here is a
    legacy document being read -- an importer that damages its own input is a
    migration tool nobody can run twice."""
    w = W.WrlGraph()
    w.profile = g.profile
    w.nodes = copy.deepcopy(list(g.nodes))
    w.edges = copy.deepcopy(list(g.edges))
    w.periods = 0
    w.batches = []
    return w


def _claim_record(claim, loc):
    """One legacy claim -> one `ScenarioV1` claim record.

    The legacy form is a positional payload tuple; ScenarioV1 splits it into
    `operation` / `target` / `payload`. The split is total over IR v1's two
    operations and a typed rejection otherwise -- never a pass-through of an
    unrecognised tuple, which would produce a scenario that validates and then
    means something else at replay."""
    wid, seq = claim.get("writer_id"), claim.get("sequence")
    if not isinstance(wid, int) or isinstance(wid, bool) or \
            not isinstance(seq, int) or isinstance(seq, bool):
        # The runtime harness defaults an absent writer to `(1, epoch)`. That is
        # fine for a fold, which only needs SOME identity, and wrong here: a
        # defaulted writer/sequence enters the canonical claim and therefore the
        # ScenarioDigest, so the import would mint an identity for run inputs
        # the legacy author never wrote. Refusing is the honest option.
        WC._fail(WRL_LEGACY_IMPORT,
                 "%s: claim has no explicit writer_id/sequence (%r, %r); a "
                 "defaulted writer would enter the ScenarioDigest as if it had "
                 "been authored" % (loc, wid, seq), primary_locator=loc)
    payload = tuple(claim.get("payload") or ())
    if payload[:1] == ("SetRotor",) and len(payload) == 3:
        op, target = "SetRotor", payload[1]
        body = {"rotor": [int(v) for v in payload[2]]}
    elif payload[:1] == ("ResetFault",) and len(payload) == 2:
        op, target, body = "ResetFault", payload[1], {}
    else:
        WC._fail(WRL_LEGACY_IMPORT,
                 "%s: unrecognised legacy claim payload %r (IR v1 has exactly "
                 "SetRotor|ResetFault)" % (loc, payload), primary_locator=loc)
    return {"writer_id": wid, "sequence": seq, "operation": op,
            "target": target, "payload": body}


def _scenario_from_graph(g, world_semantic_id):
    """The run-input half as a `ScenarioV1`, or None when there is none.

    None rather than an empty scenario, because `ScenarioV1` requires a
    non-empty `epochs` list by construction: a zero-period document has no run
    inputs to describe, and a synthesised one-epoch scenario would add a period
    the legacy document did not have. `periods == 0 <-> scenario is None` is
    itself the exact preservation law for that case."""
    if g.periods == 0:
        return None
    epochs = []
    for i in range(g.periods):
        batch = g.batches[i] if i < len(g.batches) else []
        loc = "epoch:%d" % (i + 1)
        epochs.append({
            "epoch": i + 1,
            # The legacy surface has no label field. Empty is honest and inert:
            # labels are excluded from the ScenarioDigest, so inventing one
            # would move nothing but would still be an invention.
            "label": "",
            "claims": [_claim_record(c, loc) for c in batch],
        })
    scenario = {
        "scenario_version": WS.SCENARIO_VERSION,
        "world_semantic_id": world_semantic_id,
        # `canvas.v1` never carried initial runtime state. Empty is a fact about
        # the legacy format, not a default chosen here.
        "initial_runtime": {"numeric_faults": []},
        "epochs": epochs,
    }
    return WS.validate_scenario_v1(scenario)


# -------------------------------------------------------------- the importer
def import_canvas_graph_v1(canvas):
    """Split one legacy `canvas.v1` document three ways (WRL Core §15.1.1).

    Returns `LegacyCanvasImportV1(world, scenario, presentation)`. Every stage
    reuses V1's OWN gate and reader (`validate_canvas_v1`, `canvas_to_graph`)
    rather than re-reading the document here: a private reader would be a second
    opinion about what a V1 document means, and the two would disagree the first
    time either was touched.

    The scenario is bound to the world half's `SemanticArtifactID`, so a
    subsequent `check_world_binding` passes by construction -- the import cannot
    emit a scenario that is already stale against the world it came from."""
    WV.validate_canvas_v1(canvas)
    g = WV.canvas_to_graph(canvas)
    world = _world_only(g)
    scenario = _scenario_from_graph(g, W.lower_graph(world).semantic_artifact_id)
    presentation = WV.validate_layout_v1(WV.layout_from_canvas_v1(canvas))
    return LegacyCanvasImportV1(world, scenario, presentation)


# --------------------------------------------------------------- the export
def canvas_v1_export_loss(g):
    """The reasons `g` cannot be expressed as a `canvas.v1` document, computed.

    Returns a tuple of human-readable reasons; empty means the export is
    faithful. Nothing in this function names a construct: it emits, reads back
    through V1's own reader, and compares the world projection, the identity and
    the run inputs. A construct V1 rejects surfaces as its own typed code; a
    construct V1 has nowhere to put simply fails to come back."""
    try:
        canvas = WV.graph_to_canvas(g)
        WV.validate_canvas_v1(canvas)
        back = WV.canvas_to_graph(canvas)
    except WC.WrlValidationError as ex:
        return ("canvas.v1 rejects it (%s: %s)" % (ex.code, ex.message),)
    reasons = []
    if _world_projection(back) != _world_projection(g):
        reasons.append("the world projection does not survive the round-trip")
    try:
        if W.lower_graph(back).semantic_artifact_id != \
                W.lower_graph(g).semantic_artifact_id:
            reasons.append("the SemanticArtifactID does not survive the "
                           "round-trip")
    except WC.WrlValidationError as ex:
        reasons.append("the round-tripped world no longer seals (%s)" % ex.code)
    if _run_inputs(back) != _run_inputs(g):
        reasons.append("the run inputs do not survive the round-trip")
    return tuple(reasons)


def export_canvas_graph_v1(g):
    """Export a canonical graph back to a legacy `canvas.v1` document, or refuse.

    §15.1.1 point 6: a lossy downgrade is a TYPED error, never a V1 document
    that silently means less than its input. Succeeding with a partial document
    is the worst outcome available here -- the caller gets a file that looks
    complete, and the loss is discovered later by someone who cannot tell where
    it happened."""
    loss = canvas_v1_export_loss(g)
    if loss:
        WC._fail(WRL_LEGACY_EXPORT_LOSSY,
                 "refusing a lossy downgrade to canvas.v1 (retired, frozen): "
                 + "; ".join(loss))
    return WV.graph_to_canvas(g)
