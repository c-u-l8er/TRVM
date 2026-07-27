"""binding_run8.py -- Phase 3B-1: source spans + origin mapping battery (S1-S13).

GPT-5.6's 3B priority ruling leads broad 3B with "canonical formatter + source
spans". 3B-1 is the span layer (wrl_spans.py): parsing emits source information
ALONGSIDE -- but strictly OUTSIDE -- the semantic graph.

The whole burden of proof for 3B-1 is that spans/filenames are a pure sidecar:
they resolve every canonical object/edge back to the text it came from, yet they
provably cannot perturb the SemanticArtifactID / CompilePlanDigest /
BackendArtifactID -- nor the compiled native backend.

  S1  spanned lowering is BYTE-identical to plain lowering (artifact + sem id)
  S2  a file_id change leaves the SemanticArtifactID unchanged (spans differ)
  S3  a file_id change leaves the CompilePlanDigest AND BackendArtifactID unchanged
  S4  reformatting the SAME source (comments/blank lines/indent) moves spans,
      not the SemanticArtifactID
  S5  every canonical IR object has a resolvable origin span (all worlds)
  S6  every canonical IR edge has a resolvable origin span (all worlds)
  S7  each origin span points at the text it names (slice contains the token)
  S8  bootstrap & core surfaces: same sem id AND identical canonical origin keys
  S9  canvas bridge: every canvas node object_id resolves to an origin
  S10 reverse lookup origin_at(offset) inside a node span returns that node
  S11 the sidecar is immutable (WrlSourceMap read-only; span/origin namedtuples)
  S12 file_id + span fields never appear anywhere in the sealed artifact bytes
  S13 the spanned-lowered program runs ic_ref == ic32 == golden       (native)

Native is gated exactly like the sibling batteries (TRVM_SKIP_NATIVE=1 -> ref).
"""
import os
import sys
import copy
import json
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "runtime", "python"))
sys.path.insert(0, os.path.join(HERE, "..", "research"))

import wrl_ir as W
import wrl_canonical as WC
import wrl_canvas as CV
import wrl_plan as P
import wrl_spans as S
import compiler as C
import admit as AD
import binding_run3o as O
import binding_run7 as B7
from admit import mk_claim, film_bytes_v7
from fixture import init_state_v6

SKIP_NATIVE = os.environ.get("TRVM_SKIP_NATIVE") == "1"

WORLDS = B7.WORLDS          # the same 6 core-surface worlds as 3D

# a bootstrap world and its byte-equivalent core world (two-surface, S8)
BOOT_SRC = (
    "profile forge.world.core.v1\n"
    "periods 3\n"
    "pulser p0 periodic 2 0\n"
    "relay r0\n"
    "spinner sp w=8 n=4 rotor=16,0,0,0 configurable\n"
    "orb ob\n"
    "wire p0 -> r0\n"
    "wire r0 -> sp\n"
    "socket sp -> ob\n"
    "epoch 1: SetRotor sp 16,0,10,0 @1,1\n")
CORE_SRC = (
    "profile forge.world.core.v1\n"
    "periods 3\n"
    "[pulser:p0](mode=periodic, period=2, phase=0)\n"
    "[relay:r0]\n"
    "[spinner:sp](w=8, n=4, rotor=16.0.0.0, configurable)\n"
    "[orb:ob]\n"
    "[p0] --sig--> [r0]\n"
    "[r0] --sig--> [sp]\n"
    "[sp] --socket--> [ob]\n"
    "[epoch:1] @1,1 SetRotor sp 16.0.10.0\n")


def _canon_keys(art):
    objs = {o["object_id"] for o in art["objects"]}
    edges = {S.edge_key(e["kind"], e["src"], e["dst"]) for e in art["edges"]}
    return objs, edges


def main():
    print("[BINDING wrl-3b1] source spans + origin mapping")
    allok = True
    native_ok = True
    t0 = time.time()

    def rep(ok, okn, label):
        nonlocal allok, native_ok
        allok &= bool(ok)
        tag = "PASS" if ok else "FAIL"
        if okn is False:
            native_ok = False
            tag = "FAIL(native)"
        print(f"  [{tag}] {label}")

    # ---- S1 spanned lowering is BYTE-identical to plain lowering
    s1 = True
    for nm, txt in WORLDS:
        plain = W.lower_program(txt, W.parse_wrl_legacy_document)
        sp, _sm = S.lower_legacy_document_with_spans(txt, "world_%s.wrl" % nm)
        if (WC.serialize_artifact(plain.artifact)
                != WC.serialize_artifact(sp.artifact)
                or plain.semantic_artifact_id != sp.semantic_artifact_id):
            s1 = False
    rep(s1, None, "S1) spanned lowering == plain lowering (artifact bytes + "
                  f"sem id), {len(WORLDS)} worlds")

    # ---- S2 file_id change leaves the SemanticArtifactID unchanged
    s2 = True
    for nm, txt in WORLDS:
        pa, sma = S.lower_legacy_document_with_spans(txt, "aaa.wrl")
        pb, smb = S.lower_legacy_document_with_spans(txt, "bbb.wrl")
        same_id = pa.semantic_artifact_id == pb.semantic_artifact_id
        # spans DID capture the different file_id (sidecar is genuinely present)
        differ = all(o.span.file_id == "aaa.wrl" for o in sma.origins) and \
            all(o.span.file_id == "bbb.wrl" for o in smb.origins) and \
            len(sma.origins) > 0
        if not (same_id and differ):
            s2 = False
    rep(s2, None, "S2) file_id change leaves SemanticArtifactID unchanged")

    # ---- S3 file_id change leaves CompilePlanDigest + BackendArtifactID
    s3 = True
    prof = B7._prof("auto")
    for nm, txt in WORLDS:
        pa, _ = S.lower_legacy_document_with_spans(txt, "aaa.wrl")
        pb, _ = S.lower_legacy_document_with_spans(txt, "zzz.wrl")
        ca = W.compile_program(pa, prof)
        cb = W.compile_program(pb, prof)
        if (ca.sealed_plan.compile_plan_digest
                != cb.sealed_plan.compile_plan_digest
                or ca.backend_artifact_id != cb.backend_artifact_id
                or ca.backend_content_hash != cb.backend_content_hash):
            s3 = False
    rep(s3, None, "S3) file_id change leaves CompilePlanDigest + "
                  "BackendArtifactID unchanged")

    # ---- S4 reformatting the SAME source moves spans, not the sem id
    noisy = ("; leading banner comment\n\n"
             + CORE_SRC.replace("[relay:r0]\n",
                                "    [relay:r0]   ; indented + inline comment\n")
             + "\n; trailing comment\n")
    base_p, base_sm = S.lower_legacy_document_with_spans(CORE_SRC, "base.wrl")
    noisy_p, noisy_sm = S.lower_legacy_document_with_spans(noisy, "noisy.wrl")
    moved = (base_sm.origin_for_object("r0").span
             != noisy_sm.origin_for_object("r0").span)
    s4 = (base_p.semantic_artifact_id == noisy_p.semantic_artifact_id) and moved
    rep(s4, None, "S4) source reformat (comments/blank lines/indent) moves "
                  "spans, not the SemanticArtifactID")

    # ---- S5/S6 every canonical object / edge has a resolvable origin span
    s5 = s6 = True
    for nm, txt in WORLDS:
        sp, sm = S.lower_legacy_document_with_spans(txt, "w.wrl")
        missing = S.unresolved_ir_elements(sp.artifact, sm)
        if any(k == "object" for k, _ in missing):
            s5 = False
        if any(k == "edge" for k, _ in missing):
            s6 = False
    rep(s5, None, "S5) every canonical IR object has a resolvable origin span")
    rep(s6, None, "S6) every canonical IR edge has a resolvable origin span")

    # ---- S7 each origin span points at the text it names
    s7 = True
    for nm, txt in WORLDS:
        sp, sm = S.lower_legacy_document_with_spans(txt, "w.wrl")
        for o in sm.origins:
            frag = txt[o.span.start_offset:o.span.end_offset]
            if o.construct_kind == S.NODE:
                # `[role:object_id]...` -- the object_id must be in the slice
                if o.canonical_object_id not in frag:
                    s7 = False
            elif o.construct_kind == S.EDGE:
                if "-->" not in frag:
                    s7 = False
    rep(s7, None, "S7) each origin span slice contains the token it names")

    # ---- S8 bootstrap & core surfaces: same sem id + identical origin keys
    bp, bsm = S.lower_bootstrap_with_spans(BOOT_SRC, "b.wrl")
    cp, csm = S.lower_legacy_document_with_spans(CORE_SRC, "c.wrl")
    same_id = bp.semantic_artifact_id == cp.semantic_artifact_id
    art_objs, art_edges = _canon_keys(cp.artifact)
    bkeys = (set(bsm.objects()), set(bsm.edges()))
    ckeys = (set(csm.objects()), set(csm.edges()))
    s8 = (same_id and bkeys == ckeys
          and bkeys[0] == art_objs and bkeys[1] == art_edges)
    rep(s8, None, "S8) bootstrap & core surfaces: same sem id + identical "
                  "canonical origin keys (span<->WrlGraph<->IR bridge)")

    # ---- S9 canvas bridge: every canvas node object_id resolves to an origin
    s9 = True
    for nm, txt in WORLDS:
        g = W.parse_wrl_legacy_document(txt)
        _sp, sm = S.parse_legacy_document_with_spans(txt, "w.wrl"), None
        _, sm = S.parse_legacy_document_with_spans(txt, "w.wrl")
        canvas = CV.graph_to_canvas(g)
        for node in canvas["nodes"]:
            if sm.origin_for_object(node["object_id"]) is None:
                s9 = False
        # canvas connections carry the canonical edge triple too
        for con in canvas["connections"]:
            if sm.origin_for_edge(con["kind"], con["src"], con["dst"]) is None:
                s9 = False
    rep(s9, None, "S9) canvas node/connection <-> canonical object_id/edge <-> "
                  "origin span (all resolve)")

    # ---- S10 reverse lookup origin_at(offset) inside a node span -> that node
    _sp, sm = S.parse_legacy_document_with_spans(CORE_SRC, "c.wrl")
    org = sm.origin_for_object("sp")
    mid = (org.span.start_offset + org.span.end_offset) // 2
    hit = sm.origin_at(mid)
    s10 = (hit is not None and hit.canonical_object_id == "sp"
           and hit.construct_kind == S.NODE)
    rep(s10, None, "S10) origin_at(offset) inside a node span returns that node")

    # ---- S11 the sidecar is immutable
    s11 = True
    try:
        sm.file_id = "x"
        s11 = False
    except AttributeError:
        pass
    try:
        org.span.start_offset  # readable
        org.span.__setattr__("start_offset", 0)   # namedtuple -> AttributeError
        s11 = False
    except AttributeError:
        pass
    try:
        org.canonical_object_id = "y"
        s11 = False
    except AttributeError:
        pass
    rep(s11, None, "S11) sidecar is immutable (WrlSourceMap read-only; "
                   "SourceSpan/SourceOrigin namedtuples)")

    # ---- S12 file_id + span fields never appear in the sealed artifact bytes
    marker = "SENTINEL_FILE_MARKER_98765.wrl"
    spm, smm = S.lower_legacy_document_with_spans(CORE_SRC, marker)
    blob = spm.sealed_artifact.canonical_bytes
    text_blob = blob.decode()
    no_marker = marker not in text_blob
    art = json.loads(text_blob)

    def _has_span_key(x):
        if isinstance(x, dict):
            if any(k in x for k in ("span", "file_id", "start_offset",
                                    "source_origin", "start_line")):
                return True
            return any(_has_span_key(v) for v in x.values())
        if isinstance(x, list):
            return any(_has_span_key(v) for v in x)
        return False
    s12 = no_marker and not _has_span_key(art)
    rep(s12, None, "S12) file_id + span fields never appear in the sealed "
                   "artifact bytes")

    # ---- S13 the spanned-lowered program runs ic_ref == ic32 == golden
    progS, _smS = S.lower_legacy_document_with_spans(B7.W_CORE, "native.wrl")
    planS = P.artifact_to_compile_plan_v1(progS.sealed_artifact)
    viewS = P.plan_view(planS)
    fxS = progS.as_fixture_for_test()
    batches = [[mk_claim(1, 1, B7.S((16, 0, 10, 0)))],
               [mk_claim(2, 2, B7.S((16, 0, 20, 0))), mk_claim(3, 3, B7.Rf)],
               [mk_claim(4, 4, B7.S((16, 0, 30, 0)))]]
    world0 = init_state_v6(O.FX)
    world0["fault_ob"] = 1
    gold = O._golden_traj(AD.init_claimstate(), world0, batches, 1)

    def _traj(reducer):
        claim = AD.init_claimstate()
        world = copy.deepcopy(world0)
        out = []
        step, _ = C.compile_step_v6(viewS)
        for e, batch in enumerate(batches):
            claim, cfg_map, resets = AD.admit_step(claim, batch, 1 + e, fxS)
            ec = C.enc_config_bundle(viewS, cfg_map, resets)
            world = C.dec_state_v6(viewS, reducer(
                f"(({step} {ec}) {C.enc_state_v6(viewS, world)})"))
            out.append(copy.deepcopy(world))
        return out

    ref = _traj(O.norm)
    s13r = all(ref[e] == gold[e][0] for e in range(len(batches)))
    s13n = None
    if not SKIP_NATIVE:
        nat = _traj(O.native)
        s13n = all(nat[e] == gold[e][0] for e in range(len(batches)))
    rep(s13r, s13n, "S13) spanned-lowered program runs ic_ref == ic32 == golden")

    dt = time.time() - t0
    if SKIP_NATIVE:
        verdict = "PASS_REF_ONLY (native skipped)" if allok else "FAIL"
    elif not native_ok:
        verdict = "REF_ONLY (native MISMATCH)"
        allok = False
    else:
        verdict = "PASS_REF_AND_NATIVE" if allok else "FAIL"
    print(f"\n[wrl-3b1] {'ALL PASS' if allok else 'FAILURES'} -- {verdict} "
          f"({dt:.0f}s)")
    print("  [note] source spans are a pure sidecar: they resolve every "
          "canonical object/edge to its text yet never enter identity.")
    return 0 if allok else 1


if __name__ == "__main__":
    sys.exit(main())
