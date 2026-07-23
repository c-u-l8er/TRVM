"""wrl_scenario.py v0.1 -- ScenarioV1: the structured run-input document and its
identity, `ScenarioDigest` (Spinner Bench v0.3, GPT-5.6's scenario-authoring
ruling).

The three documents must NEVER be conflated (GPT-5.6):
  * WorldDraftV1  -> earns a SemanticArtifactID (the world's identity);
  * CanvasLayoutV1 -> presentation only, never changes identity;
  * ScenarioV1    -> the RUN INPUTS (initial runtime overrides + per-epoch claim
                     batches). It never changes the world's identity; it gets its
                     OWN identity, the `ScenarioDigest`.

Identity ladder (GPT-5.6):
    SemanticArtifactID = identity of the world
    ScenarioDigest     = identity of the canonical run inputs
    ReplayBundleID     = H(SemanticArtifactID, ScenarioDigest, initial runtime)

The ScenarioDigest is computed over the CANONICAL RUNTIME inputs ONLY -- the
initial_runtime + one claim batch per epoch (positionally) -- NOT the world it
targets and NOT the UI labels (both deliberately EXCLUDED, GPT-5.6 v0.4-0). So a
world edit moves the SemanticArtifactID while leaving the ScenarioDigest fixed
(acceptance 1), a claim edit moves the ScenarioDigest while leaving the
SemanticArtifactID fixed (acceptance 2), and a LABEL-only edit moves NEITHER (a
label is documentation, not runtime input). The world it targets is bound only at
REPLAY time, via the ReplayBundleID. `world_semantic_id` is carried as validation
metadata (which world the scenario was authored against) and is excluded from the
digest. Labels remain part of the editable ScenarioV1 document -- just not its
runtime identity.

A ScenarioV1 is a pure DATA document; it introduces NO runtime construct. It
lowers to the exact `(initial_faults, script)` the existing admit driver folds, so
the golden demo expressed as a ScenarioV1 reproduces byte-identical films.
"""
import wrl_canonical as WC
from admit import mk_claim, WK, MAX_BATCH

SCENARIO_VERSION = "scenario.v1"

WRL_BAD_SCENARIO = "WRL_BAD_SCENARIO"
WRL_SCENARIO_WORLD_MISMATCH = "WRL_SCENARIO_WORLD_MISMATCH"

_OPERATIONS = ("SetRotor", "ResetFault")
_TOP_KEYS = ("scenario_version", "world_semantic_id", "initial_runtime",
             "epochs")
_INIT_KEYS = ("numeric_faults",)
_EPOCH_KEYS = ("epoch", "label", "claims")
_CLAIM_KEYS = ("writer_id", "sequence", "operation", "target", "payload")


# ------------------------------------------------------------- claim helpers
def _payload_tuple(claim):
    """Rebuild the admit payload TUPLE from a ScenarioV1 claim record.
        SetRotor   -> ("SetRotor", target, (r0, r1, r2, r3))
        ResetFault -> ("ResetFault", target)"""
    op, target, payload = claim["operation"], claim["target"], claim["payload"]
    if op == "SetRotor":
        return ("SetRotor", target, tuple(int(v) for v in payload["rotor"]))
    return ("ResetFault", target)


def _claim_sort_key(c):
    """Order-independent canonical claim key (admit ACCEPT is atomic per batch,
    so a scenario's claims carry no meaningful intra-epoch order)."""
    p = c["payload"]
    rotor = tuple(int(v) for v in p.get("rotor", ())) if isinstance(p, dict) \
        else ()
    return (int(c["writer_id"]), int(c["sequence"]), c["operation"],
            c["target"], rotor)


# --------------------------------------------------------------- validation
def _req(cond, msg, locator=None, field=None):
    if not cond:
        WC._fail(WRL_BAD_SCENARIO, msg, primary_locator=locator,
                 field_path=field)


def _int_field(v, name, lo, hi, loc):
    _req(isinstance(v, int) and not isinstance(v, bool) and lo <= v < hi,
         "%s must be an int in [%d, %d), got %r" % (name, lo, hi, v), loc, name)


def validate_scenario_v1(scenario):
    """Structural gate for a ScenarioV1. Raises WrlValidationError
    (WRL_BAD_SCENARIO) on any violation; returns the scenario on success. This is
    a STRUCTURAL validator only: it does NOT reject a claim whose target is not a
    live object of some world -- an out-of-world target is a VALID scenario that
    exercises the admit Rejected-receipt path (the golden demo's `zz` claim). The
    world binding is checked at replay, not here."""
    _req(isinstance(scenario, dict), "scenario must be an object")
    _req(scenario.get("scenario_version") == SCENARIO_VERSION,
         "unknown scenario_version %r (only %s)"
         % (scenario.get("scenario_version"), SCENARIO_VERSION))
    missing = [k for k in _TOP_KEYS if k not in scenario]
    _req(not missing, "scenario missing field(s) %s" % missing)
    extra = [k for k in scenario if k not in _TOP_KEYS]
    _req(not extra, "scenario has unknown field(s) %s" % sorted(extra))

    _req(WC._SEM_ID_RE.match(scenario["world_semantic_id"] or ""),
         "bad world_semantic_id %r" % (scenario["world_semantic_id"],),
         field="world_semantic_id")

    ir = scenario["initial_runtime"]
    _req(isinstance(ir, dict), "initial_runtime must be an object",
         field="initial_runtime")
    ir_extra = [k for k in ir if k not in _INIT_KEYS]
    _req(not ir_extra, "initial_runtime has unknown field(s) %s"
         % sorted(ir_extra), field="initial_runtime")
    faults = ir.get("numeric_faults", [])
    _req(isinstance(faults, list)
         and all(isinstance(o, str) and o for o in faults),
         "initial_runtime.numeric_faults must be a list of object ids",
         field="initial_runtime.numeric_faults")
    _req(len(set(faults)) == len(faults),
         "initial_runtime.numeric_faults has duplicates",
         field="initial_runtime.numeric_faults")

    epochs = scenario["epochs"]
    _req(isinstance(epochs, list) and epochs, "epochs must be a non-empty list",
         field="epochs")
    nums = [e.get("epoch") if isinstance(e, dict) else None for e in epochs]
    _req(nums == list(range(1, len(epochs) + 1)),
         "epoch numbers must be the contiguous sequence 1..N (idle epochs are "
         "explicit with empty claims); got %r" % (nums,), field="epochs")
    for e in epochs:
        loc = "epoch:%s" % e.get("epoch")
        e_extra = [k for k in e if k not in _EPOCH_KEYS]
        _req(not e_extra, "%s has unknown field(s) %s" % (loc, sorted(e_extra)),
             loc)
        _req(isinstance(e["label"], str), "%s label must be a string" % loc, loc)
        claims = e["claims"]
        _req(isinstance(claims, list), "%s claims must be a list" % loc, loc)
        _req(len(claims) <= MAX_BATCH,
             "%s has %d claims, exceeds MAX_BATCH=%d"
             % (loc, len(claims), MAX_BATCH), loc)
        for c in claims:
            _validate_claim(c, loc)
    return scenario


def check_world_binding(scenario, world_semantic_id):
    """Enforce that a ScenarioV1 is bound to the world it is about to run against
    (GPT-5.6 v0.4-0 ruling #3). Structural validation does NOT do this -- an
    out-of-world claim target is a valid intentional-rejection case (the `zz`
    claim) -- but NORMAL EXECUTION must refuse a scenario authored against a
    DIFFERENT world, because once the world is editable a stale binding would
    silently fold the wrong run inputs. Raises WrlValidationError
    (WRL_SCENARIO_WORLD_MISMATCH) on a mismatch; returns the scenario on success.
    A world edit may rebind a scenario only through the explicit compatibility
    procedure (v0.4 ScenarioCompatibilityReport), never implicitly here."""
    got = scenario.get("world_semantic_id")
    if got != world_semantic_id:
        WC._fail(WRL_SCENARIO_WORLD_MISMATCH,
                 "scenario is bound to world %r but the active world is %r; "
                 "rebind it through the scenario/world compatibility procedure"
                 % (got, world_semantic_id),
                 field_path="world_semantic_id")
    return scenario


def rebind_scenario(scenario, new_world_semantic_id):
    """Rebind a ScenarioV1 to a NEW world id (the compatible branch of the
    commit-time scenario/world compatibility procedure, GPT-5.6 v0.4-4b). Only
    the `world_semantic_id` VALIDATION METADATA moves; the run inputs are
    untouched, so the `ScenarioDigest` is invariant (world id is excluded from
    the digest domain) while the `ReplayBundleID` -- which binds a concrete world
    -- moves. Returns a fresh rebound scenario; the input is not mutated. The new
    id must be a well-formed SemanticArtifactID. This performs the metadata
    rebind ONLY; whether the two worlds are actually compatible (same live
    targets) is the caller's decision -- an incompatible commit detaches the
    scenario instead of rebinding it."""
    _req(WC._SEM_ID_RE.match(new_world_semantic_id or ""),
         "bad new_world_semantic_id %r" % (new_world_semantic_id,),
         field="world_semantic_id")
    validate_scenario_v1(scenario)
    rebound = WC._plain(scenario)
    rebound["world_semantic_id"] = new_world_semantic_id
    return rebound


def _validate_claim(c, loc):
    _req(isinstance(c, dict), "%s: claim must be an object" % loc, loc)
    missing = [k for k in _CLAIM_KEYS if k not in c]
    _req(not missing, "%s: claim missing field(s) %s" % (loc, missing), loc)
    extra = [k for k in c if k not in _CLAIM_KEYS]
    _req(not extra, "%s: claim has unknown field(s) %s" % (loc, sorted(extra)),
         loc)
    _int_field(c["writer_id"], "writer_id", 0, 1 << WK, loc)
    _int_field(c["sequence"], "sequence", 0, 1 << WK, loc)
    _req(c["operation"] in _OPERATIONS,
         "%s: operation must be one of %s, got %r"
         % (loc, list(_OPERATIONS), c["operation"]), loc, "operation")
    _req(isinstance(c["target"], str) and c["target"],
         "%s: target must be a non-empty string" % loc, loc, "target")
    p = c["payload"]
    _req(isinstance(p, dict), "%s: payload must be an object" % loc, loc,
         "payload")
    if c["operation"] == "SetRotor":
        _req(list(p.keys()) == ["rotor"],
             "%s: SetRotor payload must be exactly {rotor:[4 ints]}" % loc, loc,
             "payload.rotor")
        rot = p["rotor"]
        _req(isinstance(rot, list) and len(rot) == 4
             and all(isinstance(v, int) and not isinstance(v, bool)
                     for v in rot),
             "%s: SetRotor rotor must be 4 ints" % loc, loc, "payload.rotor")
    else:
        _req(p == {}, "%s: ResetFault payload must be empty {}" % loc, loc,
             "payload")


# --------------------------------------------------------- canonical + digest
def canonicalize_scenario_v1(scenario):
    """Validate then return the CANONICAL run-input form: numeric_faults sorted,
    epochs in 1..N order, each epoch's claims sorted by the order-independent
    claim key, world_semantic_id preserved as metadata. Two scenarios that differ
    only in claim order (or fault order) canonicalize identically."""
    validate_scenario_v1(scenario)
    epochs = []
    for e in scenario["epochs"]:
        claims = sorted(e["claims"], key=_claim_sort_key)
        epochs.append({"epoch": e["epoch"], "label": e["label"],
                       "claims": WC._plain(claims)})
    return {
        "scenario_version": SCENARIO_VERSION,
        "world_semantic_id": scenario["world_semantic_id"],
        "initial_runtime": {
            "numeric_faults": sorted(scenario["initial_runtime"]
                                     ["numeric_faults"]),
        },
        "epochs": epochs,
    }


def _digest_domain(canon):
    """The digest DOMAIN (GPT-5.6 v0.4-0 ruling): the RUNTIME inputs only --
    `initial_runtime` + one canonical claim batch per epoch, positionally.
    Labels are UI-only and are DELIBERATELY EXCLUDED (a label-only edit produces
    identical runtime inputs, so it must not move the digest). Epoch numbers are
    the contiguous 1..N sequence and carry no extra information beyond list
    position, so an EMPTY batch preserves the idle epoch and the total duration
    without hashing the number. The world id is likewise excluded."""
    return {"initial_runtime": canon["initial_runtime"],
            "epoch_batches": [e["claims"] for e in canon["epochs"]]}


def scenario_digest(scenario):
    """`scen-`+sha256 over the RUNTIME inputs (initial_runtime + per-epoch claim
    batches). Independent of the world it targets (world_semantic_id is excluded)
    AND of the UI labels (excluded per the v0.4-0 ruling), so it is orthogonal to
    the SemanticArtifactID and stable across label-only edits."""
    canon = canonicalize_scenario_v1(scenario)
    return "scen-" + WC._sha(WC.serialize_artifact(_digest_domain(canon)))


def replay_bundle_id(world_semantic_id, scen_digest, initial_runtime):
    """`replay-`+sha256(SemanticArtifactID, ScenarioDigest, initial runtime) --
    the identity of one concrete run: a sealed world bound to a scenario's inputs
    (GPT-5.6's identity ladder)."""
    body = [world_semantic_id, scen_digest,
            {"numeric_faults": sorted(initial_runtime["numeric_faults"])}]
    return "replay-" + WC._sha(WC.serialize_artifact(body))


# -------------------------------------------------------- scenario -> script
def scenario_to_script(scenario):
    """Lower a ScenarioV1 to the `(initial_faults, script)` the admit driver
    folds. `initial_faults` is the sorted numeric_faults tuple; `script` is
    `[(label, [claim_envelope, ...]), ...]` in epoch order, each envelope built
    by the untouched `admit.mk_claim`. Claims are emitted in canonical order (the
    reducer is order-independent, so this only fixes the digest, not the effect)."""
    canon = canonicalize_scenario_v1(scenario)
    initial_faults = tuple(canon["initial_runtime"]["numeric_faults"])
    script = []
    for e in canon["epochs"]:
        batch = [mk_claim(c["writer_id"], c["sequence"], _payload_tuple(c))
                 for c in e["claims"]]
        script.append((e["label"], batch))
    return initial_faults, script


# ------------------------------------------------------ the golden demo scenario
def demo_scenario(world_semantic_id):
    """The Golden ADMIT Demo expressed as a ScenarioV1 (the immutable preset).
    Reproduces the historical hard-coded 7-step SCRIPT byte-for-byte: orb `ob`
    starts faulted; 7 epochs (set qtz 181.0.0.181 . idle . 256.0.0.0 . reset ob .
    128.0.128.0 . idle . 10.0.0.0 + an unknown-object `zz` claim)."""
    def sr(w, s, target, rotor):
        return {"writer_id": w, "sequence": s, "operation": "SetRotor",
                "target": target, "payload": {"rotor": list(rotor)}}

    def rf(w, s, target):
        return {"writer_id": w, "sequence": s, "operation": "ResetFault",
                "target": target, "payload": {}}

    return {
        "scenario_version": SCENARIO_VERSION,
        "world_semantic_id": world_semantic_id,
        "initial_runtime": {"numeric_faults": ["ob"]},
        "epochs": [
            {"epoch": 1, "label": "set rotor = quarter_turn_z (181.0.0.181)",
             "claims": [sr(1, 1, "sp", (181, 0, 0, 181))]},
            {"epoch": 2, "label": "idle pulse tick", "claims": []},
            {"epoch": 3, "label": "set rotor = 256.0.0.0 (full-scale)",
             "claims": [sr(2, 2, "sp", (256, 0, 0, 0))]},
            {"epoch": 4, "label": "reset orb fault latch",
             "claims": [rf(3, 3, "ob")]},
            {"epoch": 5, "label": "set rotor = 128.0.128.0 (mixed)",
             "claims": [sr(4, 4, "sp", (128, 0, 128, 0))]},
            {"epoch": 6, "label": "idle pulse tick", "claims": []},
            {"epoch": 7, "label": "set rotor = 10.0.0.0 + unknown-obj claim",
             "claims": [sr(5, 5, "sp", (10, 0, 0, 0)),
                        sr(6, 6, "zz", (9, 0, 0, 0))]},
        ],
    }


# --------------------------------------------- the ADMIT acceptance-bench preset
def bench_scenario(world_semantic_id):
    """The ADMIT Acceptance Bench expressed as a ScenarioV1 (a SECOND immutable
    preset, additional to `demo_scenario`). It walks the seven ADMIT acceptance
    behaviours from the v0.3 roadmap, each given its own headroom so it reads
    cleanly (no fact-capacity overflow masking a `disputed`), on the SAME demo
    world with NO new runtime construct -- every behaviour is existing physics:

      1 ep1  accept SetRotor            -> w1s1 receipt Applied, rotor set
      2 ep2  exact retransmit           -> same envelope, NO new fact/effect
      3 ep3  conflicting payload,       -> w3s3 recognition `disputed`, the
             same event key                first receipt stays immutable
      -  ep4/ep5 idle                   -> saturation runway (spinner accumulates
                                           the max rotor set in ep1 toward overflow)
      4 ep6  saturating rotor           -> orb fault LATCHES (0 -> 1) on overflow
      5 ep7  reset in a safe epoch      -> non-firing epoch, fault CLEARS (1 -> 0)
      6 ep8  reset + same-epoch overflow-> firing epoch: COMMIT clears the old
                                           fault but REACT re-latches -> stays 1
      7 ep9  idle / replay verify       -> fault remains latched, run is replayable

    The saturating rotor is the full-scale value for the demo spinner's width
    (w=16 -> 2^15-1 = 32767); it is set ONCE in ep1 (which doubles as the accept
    step) and the world's every-2 pulser needs two firings to overflow, so the
    first latch lands at ep6. Total observed facts = 5 (<= MAX_FACTS = 6), so the
    `disputed` in ep3 is a true recognition split, never a capacity fault."""
    sat = (1 << 15) - 1  # 32767: full-scale rotor for the demo spinner (w=16)

    def sr(w, s, target, rotor):
        return {"writer_id": w, "sequence": s, "operation": "SetRotor",
                "target": target, "payload": {"rotor": list(rotor)}}

    def rf(w, s, target):
        return {"writer_id": w, "sequence": s, "operation": "ResetFault",
                "target": target, "payload": {}}

    return {
        "scenario_version": SCENARIO_VERSION,
        "world_semantic_id": world_semantic_id,
        "initial_runtime": {"numeric_faults": []},
        "epochs": [
            {"epoch": 1, "label": "1 accept SetRotor (full-scale 32767)",
             "claims": [sr(1, 1, "sp", (sat, 0, 0, 0))]},
            {"epoch": 2, "label": "2 exact retransmit (no 2nd effect)",
             "claims": [sr(1, 1, "sp", (sat, 0, 0, 0))]},
            {"epoch": 3, "label": "3 conflicting payload, same event key -> disputed",
             "claims": [sr(3, 3, "sp", (sat, 0, 0, 0)),
                        sr(3, 3, "sp", (sat, 0, 0, 1))]},
            {"epoch": 4, "label": "idle (saturation runway)", "claims": []},
            {"epoch": 5, "label": "idle (saturation runway)", "claims": []},
            {"epoch": 6, "label": "4 saturating rotor -> fault latches", "claims": []},
            {"epoch": 7, "label": "5 reset in safe epoch -> clears",
             "claims": [rf(7, 7, "ob")]},
            {"epoch": 8, "label": "6 reset + same-epoch overflow -> stays latched",
             "claims": [rf(8, 8, "ob")]},
            {"epoch": 9, "label": "7 idle / replay verify", "claims": []},
        ],
    }
