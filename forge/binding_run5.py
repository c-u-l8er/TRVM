"""binding_run5.py -- WRL Slice 2: Canonical Identity (the identity spine).

GPT-5.6 Ruling B: before widening WRL features, prove the identity spine is
green. This battery exercises the twelve Slice-2 checks:

  C1  two DECLARATION ORDERS lower to identical canonical artifact bytes.
  C2  the BOOTSTRAP surface and the WRL PROCESS NOTATION lower to identical
      canonical bytes (two-surface equivalence) -- and identical run inputs.
  C3  claim batches do NOT affect the SemanticArtifactID (run inputs are
      separated from the static artifact, D3).
  C4  a different INITIAL ROTOR (static_config) DOES change it.
  C5  a different NUMERIC POLICY changes it.
  C6  one-hot vs binary LOWERING retains the SemanticArtifactID (backend only)
      while changing the BackendArtifactID.
  C7  a different backend COMPILER identity changes the BackendArtifactID.
  C8  duplicate object ids are a TYPED rejection (WRL_DUPLICATE_ID).
  C9  an illegal port pair is a TYPED rejection (WRL_ILLEGAL_PORT_PAIR).
  C10 ALL THREE epochs -- including the rejected invalid-target claim -- have
      full Film v0.7 parity (the projection gap is closed: rejected target
      names are non-authoritative and canonicalize identically on both sides).
  C11 the canonical artifact round-trips through serialization (bytes stable).
  C12 ic_ref == ic32 == golden over the whole WRL-lowered trajectory.

Slice 2.1 sealing / lexical errata (GPT-5.6):

  C13 an unsealed policy (null/empty rulepack) is a TYPED rejection at hash
      time (WRL_UNSEALED_POLICY) -- an artifact cannot earn an identity without
      naming the transition law that gives it meaning.
  C14 a different rulepack_id changes the SemanticArtifactID.
  C15 a WRL `{ports}` brace group is a CHECKED projection of the role's frozen
      ports: bogus/empty is WRL_PORT_SIGNATURE; the honest projection lowers
      identically to the registry-derived ports (no silently ignored source).
  C16 the core parser obeys WRL's lexical law: `;` comments (full-line +
      inline), and `#` is preserved for identity (never a comment marker).
  C17 a half-specified backend lowering profile is WRL_BAD_LOWERING_PROFILE
      (no official-looking BackendArtifactID for an incomplete backend).
  C18 objects are emitted in identity-first canonical order (object_id).

Phase 3C-0 sealing preflight (GPT-5.6): canonical artifact sealing is the
opening sub-slice of 3C -- reorder-equivalent valid artifacts must seal to
identical bytes and SemanticArtifactIDs, sealed values must be isolated from
caller mutation, and backend identities must reject malformed semantic ids,
unknown encodings and unsupported profile versions:

  C19 artifact-order invariance + isolation: reversing objects/edges, reordering
      numeric_policy_ids, and a JSON round-trip all seal to identical bytes and
      SemanticArtifactID; and mutating the source dict after sealing cannot
      change an already-issued identity.
  C20 backend-profile domain: a well-formed pair earns a BackendArtifactID, but
      a malformed/short/uppercase-hex semantic id, an unknown encoding, or an
      unsupported lowering_profile_version are all WRL_BAD_LOWERING_PROFILE.

C10/C12 reuse the proven 3b.5f-2b fold harness (binding_run3o) since the
WRL-lowered adapter fixture equals its mkfx(8,4).
"""
import os
import sys
import copy
import time

sys.setrecursionlimit(2_000_000)
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import admit as AD
import wrl_ir as W
import wrl_canonical as WC
import binding_run3o as O
from binding_run3j import mkfx
from admit import mk_claim
from fixture import init_state_v6

SKIP_NATIVE = os.environ.get("TRVM_SKIP_NATIVE") == "1"

# ---- the grounded circuit-world, mkfx(8,4) topology, 3 epochs. Epoch 3's
# SetRotor targets a non-existent spinner "zz": accepted as a fact, receipted
# Rejected(unknown_spinner), no world effect -- the rejected-claim case C10
# closes.
BOOTSTRAP_SRC = """
profile forge.world.core.v1
periods 3

pulser  p0 periodic 2 0
door    d0
spinner sp w=8 n=4 rotor=16,0,0,0 configurable
orb     ob

wire   p0 -> sp
socket sp -> ob

epoch 1: @1,1 SetRotor   sp 16,0,10,0
epoch 2: @2,2 ResetFault ob
epoch 3: @3,3 SetRotor   zz 16,0,30,0
"""

# the SAME program in WRL process notation (rotor lanes dot-separated so the
# comma-delimited (k=v, ...) group is unambiguous).
CORE_SRC = """
profile forge.world.core.v1
periods 3

[pulser:p0](mode=periodic, period=2, phase=0){sig_out}
[door:d0]{sig_in}
[spinner:sp](w=8, n=4, rotor=16.0.0.0, configurable){sig_in, socket}
[orb:ob]{pose}

[pulser:p0] --sig--> [spinner:sp]
[spinner:sp] --socket--> [orb:ob]

[epoch:1] @1,1 SetRotor sp 16.0.10.0
[epoch:2] @2,2 ResetFault ob
[epoch:3] @3,3 SetRotor zz 16.0.30.0
"""

# a declaration-reordered bootstrap (objects and edges permuted, epochs shuffled)
REORDERED_SRC = """
profile forge.world.core.v1
periods 3

orb     ob
spinner sp w=8 n=4 rotor=16,0,0,0 configurable
door    d0
pulser  p0 periodic 2 0

socket sp -> ob
wire   p0 -> sp

epoch 3: @3,3 SetRotor   zz 16,0,30,0
epoch 1: @1,1 SetRotor   sp 16,0,10,0
epoch 2: @2,2 ResetFault ob
"""


def _sid(text, parser=W.parse_wrl_bootstrap):
    prog = W.lower_program(text, parser)
    return WC.semantic_artifact_id(prog.artifact), prog


def _fx_sig(fx):
    return (dict(fx.pulsers), sorted(fx.doors), sorted(fx.relays),
            sorted(fx.edges), dict(fx.spinners), sorted(fx.orbs),
            sorted(fx.sockets), fx.configurable)


def _batches_from_program(prog):
    out = []
    for e, ei in enumerate(prog.epoch_inputs):
        batch = []
        for c in ei["claim_batch"]:
            wid = c["writer_id"] if c["writer_id"] is not None else 1
            seq = c["sequence"] if c["sequence"] is not None else e + 1
            batch.append(mk_claim(wid, seq, c["payload"]))
        out.append(batch)
    return out


# ------------------------------------------------------------------- checks
def c1_declaration_order():
    a, _ = _sid(BOOTSTRAP_SRC)
    b, _ = _sid(REORDERED_SRC)
    assert a == b, "declaration order changed the SemanticArtifactID"
    print("  C1 two declaration orders -> identical SemanticArtifactID  OK")
    return a


def c2_two_surface(bootstrap_sid):
    core_sid, core_prog = _sid(CORE_SRC, W.parse_wrl_core)
    boot_prog = W.lower_program(BOOTSTRAP_SRC)
    assert core_sid == bootstrap_sid, \
        "bootstrap and core surfaces produced different SemanticArtifactIDs"
    assert (WC.serialize_artifact(core_prog.artifact)
            == WC.serialize_artifact(boot_prog.artifact)), "artifact bytes differ"
    # run inputs must also coincide (canonical batches)
    assert core_prog.graph.batches == boot_prog.graph.batches, \
        "two surfaces disagree on canonical claim batches"
    print("  C2 bootstrap surface == WRL process notation (bytes + run "
          "inputs)  OK")


def c3_batches_irrelevant(base_sid):
    # same topology, DIFFERENT claim batches -> same SemanticArtifactID
    variant = BOOTSTRAP_SRC.replace("SetRotor   sp 16,0,10,0",
                                    "SetRotor   sp 16,0,77,0")
    sid, _ = _sid(variant)
    assert sid == base_sid, "claim batches leaked into the SemanticArtifactID"
    print("  C3 claim batches do NOT affect the SemanticArtifactID  OK")


def c4_initial_rotor(base_sid):
    variant = BOOTSTRAP_SRC.replace("rotor=16,0,0,0", "rotor=16,0,50,0")
    sid, _ = _sid(variant)
    assert sid != base_sid, "initial rotor did not affect the identity"
    print("  C4 a different initial rotor DOES change it  OK")


def c5_numeric_policy(base_prog_sid_art):
    art = copy.deepcopy(base_prog_sid_art)
    art["semantic_policies"]["numeric_policy_ids"] = ["POLICY_OTHER"]
    assert WC.semantic_artifact_id(art) != WC.semantic_artifact_id(
        base_prog_sid_art), "numeric policy did not affect the identity"
    print("  C5 a different numeric policy changes it  OK")


def c6_c7_backend(art):
    sem = WC.semantic_artifact_id(art)
    lp_onehot = {"counter_encoding": "one_hot", "onehot_max": 32,
                 "numeric_backend": "Q32.32",
                 "compiler_hash": "cc-abc", "target": "ic32",
                 "lowering_profile_version": "1.0"}
    lp_binary = dict(lp_onehot, counter_encoding="binary")
    lp_cc2 = dict(lp_onehot, compiler_hash="cc-xyz")
    b_onehot = WC.backend_artifact_id(sem, lp_onehot)
    b_binary = WC.backend_artifact_id(sem, lp_binary)
    b_cc2 = WC.backend_artifact_id(sem, lp_cc2)
    # C6: encoding is backend-only -- SemanticArtifactID fixed, BackendId moves
    assert WC.semantic_artifact_id(art) == sem
    assert b_onehot != b_binary, "one-hot/binary must move the BackendId"
    print("  C6 one-hot vs binary retains SemanticArtifactID, moves "
          "BackendArtifactID  OK")
    # C7: a different compiler identity moves the BackendId
    assert b_cc2 != b_onehot, "compiler identity must move the BackendId"
    print("  C7 a different backend compiler identity changes the "
          "BackendArtifactID  OK")


def c8_duplicate_id():
    src = ("profile forge.world.core.v1\nperiods 0\n"
           "door d0\ndoor d0\n")
    try:
        W.lower_program(src)
    except W.WrlValidationError as ex:
        assert ex.code == WC.WRL_DUPLICATE_ID, ex.code
        print("  C8 duplicate object id -> %s  OK" % ex.code)
        return
    raise AssertionError("duplicate id was not rejected")


def c9_illegal_port():
    src = ("profile forge.world.core.v1\nperiods 0\n"
           "pulser p0 periodic 2 0\norb ob\nwire p0 -> ob\n")
    try:
        W.lower_program(src)
    except W.WrlValidationError as ex:
        assert ex.code == WC.WRL_ILLEGAL_PORT_PAIR, ex.code
        print("  C9 illegal port pair (wire into orb) -> %s  OK" % ex.code)
        return
    raise AssertionError("illegal port pair was not rejected")


def c10_c12_trajectory():
    prog = W.lower_program(BOOTSTRAP_SRC)
    fx = prog.fixture
    assert _fx_sig(fx) == _fx_sig(O.FX), "adapter fixture must match mkfx(8,4)"
    batches = _batches_from_program(prog)

    # fault-carrying world so the epoch-2 reset renders a physical change
    world0 = init_state_v6(O.FX)
    world0["fault_ob"] = 1
    claim0 = AD.init_claimstate()
    gold = O._golden_traj(claim0, world0, batches, epoch0=1)

    import admit_ic as X
    from compiler import enc_state_v6
    fv0 = X.enc_factvec([], O.CAP)
    rv0 = X.enc_factvec([], O.RCAP)
    term = O._build_fold(batches, fv0, rv0, enc_state_v6(O.FX, world0))
    K = len(batches)

    dec_ref = O._decode_fold(O.norm(term), K)
    assert O._traj_summary(dec_ref) == O._golden_summary(gold), \
        "ref trajectory != golden"

    # C10: FULL Film v0.7 parity, EVERY epoch (epoch 3 is the rejected
    # invalid-target claim -- the closed projection gap).
    claims_ref = O._project_claims(dec_ref, epoch0=1)
    for e in range(K):
        f_ref = O._film(dec_ref[e][0], claims_ref[e], e + 1)
        f_g = O._film(gold[e][0], gold[e][1], e + 1)
        assert f_ref == f_g, "Film v0.7 mismatch at epoch %d" % (e + 1)
    print("  C10 full Film v0.7 parity over ALL %d epochs (rejected-claim "
          "gap closed)  OK" % K)

    tag = "ref"
    if not SKIP_NATIVE:
        dec_nat = O._decode_fold(O.native(term), K)
        assert O._traj_summary(dec_nat) == O._traj_summary(dec_ref), \
            "native trajectory != ref"
        claims_nat = O._project_claims(dec_nat, epoch0=1)
        for e in range(K):
            f_nat = O._film(dec_nat[e][0], claims_nat[e], e + 1)
            f_g = O._film(gold[e][0], gold[e][1], e + 1)
            assert f_nat == f_g, "native Film v0.7 mismatch epoch %d" % (e + 1)
        tag = "ref==native"
    print("  C12 ic_ref==ic32==golden trajectory (%s), %d epochs  OK"
          % (tag, K))


def c11_roundtrip(art):
    blob = WC.serialize_artifact(art)
    art2 = WC.deserialize_artifact(blob)
    blob2 = WC.serialize_artifact(art2)
    assert blob == blob2, "canonical artifact did not round-trip"
    assert WC.semantic_artifact_id(art) == WC.semantic_artifact_id(art2)
    print("  C11 canonical artifact round-trips through serialization  OK")


# ---------------------------------------------------- Slice 2.1 errata checks
def c13_sealing(art):
    # a non-null rulepack is emitted, and the artifact SEALS cleanly
    assert art["semantic_policies"]["rulepack_id"] == WC.RULEPACK_ID
    sealed = WC.seal_artifact(art)
    assert sealed.semantic_id == WC.semantic_artifact_id(art)
    # a null rulepack is a TYPED rejection at hash time (cannot earn identity)
    bad = copy.deepcopy(art)
    bad["semantic_policies"]["rulepack_id"] = None
    try:
        WC.semantic_artifact_id(bad)
    except W.WrlValidationError as ex:
        assert ex.code == WC.WRL_UNSEALED_POLICY, ex.code
    else:
        raise AssertionError("null rulepack was hashed anyway")
    empty = copy.deepcopy(art)
    empty["semantic_policies"]["rulepack_id"] = ""
    try:
        WC.seal_artifact(empty)
    except W.WrlValidationError as ex:
        assert ex.code == WC.WRL_UNSEALED_POLICY, ex.code
    else:
        raise AssertionError("empty rulepack was sealed anyway")
    print("  C13 unsealed policy (null/empty rulepack) -> %s  OK"
          % WC.WRL_UNSEALED_POLICY)


def c14_rulepack_identity(art, base_sid):
    other = copy.deepcopy(art)
    other["semantic_policies"]["rulepack_id"] = "forge.world.core.rules.v2"
    assert WC.semantic_artifact_id(other) != base_sid, \
        "the transition-law identity did not affect the SemanticArtifactID"
    print("  C14 a different rulepack_id changes the SemanticArtifactID  OK")


def c15_port_projection():
    # a correct brace projection is accepted (already exercised by C2);
    # a bogus or empty brace group is a TYPED rejection, not silently ignored.
    for ports in ("bogus", ""):
        src = ("profile forge.world.core.v1\nperiods 0\n"
               "[door:d0]{%s}\n" % ports)
        try:
            W.lower_program(src, W.parse_wrl_core)
        except W.WrlValidationError as ex:
            assert ex.code == WC.WRL_PORT_SIGNATURE, ex.code
        else:
            raise AssertionError("bogus/empty ports {%s} not rejected" % ports)
    # and the honest projection lowers the same as no braces (bootstrap)
    ok = W.lower_program("profile forge.world.core.v1\nperiods 0\n"
                         "[door:d0]{sig_in}\n", W.parse_wrl_core)
    boot = W.lower_program("profile forge.world.core.v1\nperiods 0\ndoor d0\n")
    assert (WC.serialize_artifact(ok.artifact)
            == WC.serialize_artifact(boot.artifact)), \
        "checked ports must lower identically to the registry projection"
    print("  C15 WRL {ports} is a checked projection -> %s on mismatch  OK"
          % WC.WRL_PORT_SIGNATURE)


def c16_semicolon_lexis(base_sid):
    # `;` full-line and inline comments; `#` is NOT a comment (identity-reserved)
    commented = ("; a full-line WRL comment\n" + CORE_SRC).replace(
        "[orb:ob]{pose}", "[orb:ob]{pose}   ; inline comment")
    sid, _ = _sid(commented, W.parse_wrl_core)
    assert sid == base_sid, "semicolon comments changed the artifact"
    # a trailing `#tag` must NOT be stripped as a comment -> it breaks the node
    try:
        W.lower_program("profile forge.world.core.v1\nperiods 0\n"
                        "[door:d0]{sig_in} #tag\n", W.parse_wrl_core)
    except W.WrlValidationError as ex:
        assert ex.code == WC.WRL_UNSUPPORTED_FEATURE, ex.code
    else:
        raise AssertionError("'#' was treated as a comment (identity hazard)")
    print("  C16 `;` comments obeyed, `#` preserved for identity  OK")


def c17_lowering_profile(art):
    sem = WC.semantic_artifact_id(art)
    partial = {"counter_encoding": "one_hot", "onehot_max": 32,
               "numeric_backend": "Q32.32",
               "compiler_hash": "cc-abc", "target": "ic32"}  # no version
    try:
        WC.backend_artifact_id(sem, partial)
    except W.WrlValidationError as ex:
        assert ex.code == WC.WRL_BAD_LOWERING_PROFILE, ex.code
    else:
        raise AssertionError("half-specified backend earned a BackendId")
    print("  C17 half-specified lowering profile -> %s  OK"
          % WC.WRL_BAD_LOWERING_PROFILE)


def c18_identity_first_order(art):
    ids = [o["object_id"] for o in art["objects"]]
    assert ids == sorted(ids), \
        "objects are not in identity-first canonical order: %r" % (ids,)
    print("  C18 objects emitted in identity-first canonical order  OK")


# ------------------------------------------------- Phase 3C-0 sealing preflight
def c19_order_invariance(art):
    # (a) any reorder-equivalent artifact SEALS to identical bytes + identity:
    #     reverse objects, reverse edges, reorder numeric_policy_ids, and a
    #     JSON round-trip (tuples -> lists) must all collapse to one seal.
    import json
    scrambled = copy.deepcopy(art)
    scrambled["objects"] = list(reversed(scrambled["objects"]))
    scrambled["edges"] = list(reversed(scrambled["edges"]))
    scrambled["semantic_policies"]["numeric_policy_ids"] = list(reversed(
        scrambled["semantic_policies"]["numeric_policy_ids"]))
    # a JSON round-trip mimics an artifact that arrived over the wire
    scrambled = json.loads(json.dumps(scrambled))
    s0 = WC.seal_artifact(art)
    s1 = WC.seal_artifact(scrambled)
    assert s0.semantic_id == s1.semantic_id, \
        "reorder-equivalent artifacts sealed to different SemanticArtifactIDs"
    assert (WC.serialize_artifact(s0.artifact)
            == WC.serialize_artifact(s1.artifact)), \
        "reorder-equivalent artifacts sealed to different bytes"
    # (b) the sealed value is ISOLATED from later caller mutation.
    raw = copy.deepcopy(art)
    sealed = WC.seal_artifact(raw)
    frozen_id = sealed.semantic_id
    frozen_bytes = WC.serialize_artifact(sealed.artifact)
    raw["objects"][0]["object_id"] = "MUTATED"
    raw["semantic_policies"]["rulepack_id"] = "forge.world.core.rules.vX"
    raw["objects"].append({"object_id": "ghost"})
    assert sealed.semantic_id == frozen_id, \
        "caller mutation changed an issued SemanticArtifactID"
    assert WC.serialize_artifact(sealed.artifact) == frozen_bytes, \
        "caller mutation changed a sealed artifact's bytes"
    print("  C19 reorder-equivalent artifacts seal identically; sealed "
          "value isolated from caller mutation  OK")


def c20_backend_domain(art):
    sem = WC.semantic_artifact_id(art)
    good = {"counter_encoding": "one_hot", "onehot_max": 32,
            "numeric_backend": "Q32.32",
            "compiler_hash": "cc-abc", "target": "ic32",
            "lowering_profile_version": "1.0"}
    # a well-formed pair still earns a BackendId (sanity anchor)
    assert WC.backend_artifact_id(sem, good).startswith("bknd-")
    cases = [
        ("malformed semantic id", "sem-not-hex", good),
        ("short semantic id", "sem-abc", good),
        ("uppercase-hex semantic id", "sem-" + "A" * 64, good),
        ("unknown encoding", sem, dict(good, counter_encoding="ternary")),
        ("bad onehot_max", sem, dict(good, onehot_max=0)),
        ("unsupported version", sem, dict(good, lowering_profile_version="2.0")),
    ]
    for label, sid, lp in cases:
        try:
            WC.backend_artifact_id(sid, lp)
        except W.WrlValidationError as ex:
            assert ex.code == WC.WRL_BAD_LOWERING_PROFILE, (label, ex.code)
        else:
            raise AssertionError("%s earned a BackendArtifactID" % label)
    print("  C20 backend identity rejects malformed sem ids, unknown "
          "encodings, unsupported versions -> %s  OK"
          % WC.WRL_BAD_LOWERING_PROFILE)


def main():
    print("[BINDING wrl-slice2] WRL Canonical Identity spine")
    t0 = time.time()
    base_sid = c1_declaration_order()
    c2_two_surface(base_sid)
    boot_prog = W.lower_program(BOOTSTRAP_SRC)
    art = boot_prog.artifact
    c3_batches_irrelevant(base_sid)
    c4_initial_rotor(base_sid)
    c5_numeric_policy(art)
    c6_c7_backend(art)
    c8_duplicate_id()
    c9_illegal_port()
    c11_roundtrip(art)
    c13_sealing(art)
    c14_rulepack_identity(art, base_sid)
    c15_port_projection()
    c16_semicolon_lexis(WC.semantic_artifact_id(
        W.lower_program(CORE_SRC, W.parse_wrl_core).artifact))
    c17_lowering_profile(art)
    c18_identity_first_order(art)
    c19_order_invariance(art)
    c20_backend_domain(art)
    c10_c12_trajectory()
    verdict = "PASS_REF" if SKIP_NATIVE else "PASS_REF_AND_NATIVE"
    print("[BINDING wrl-slice2] %s  (%.0fs)" % (verdict, time.time() - t0))


if __name__ == "__main__":
    main()
