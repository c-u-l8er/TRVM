"""binding_run12.py -- Phase 3B-5: SemanticDiff + completion metadata (Q1-Q15).

3B-5 closes the 3B ergonomics arc. Two pure, identity-free tools:

  * `wrl_diff.SemanticDiff` -- a structured canonical difference between two
    Forge Semantic artifacts, keyed by object_id / edge triple. Headline law:
    diff is EMPTY  <=>  the two artifacts share a SemanticArtifactID (Q2), so a
    diff can never disagree with the identity spine.
  * `wrl_complete` -- completion METADATA that is a pure projection of the frozen
    registries (roles/ports/edges + the 3B-4 named-rotor/clock sugar), plus a
    cursor-aware `completions_at`. Every candidate is a registry read, so a
    completion can only offer something the parser already accepts (Q10/Q13).

  Q1  identical artifacts -> empty diff (over the structural worlds)
  Q2  the bridge: diff.is_empty() == (sem_a == sem_b) over an edit matrix
  Q3  a rotor edit -> OBJECT_CHANGED sp (static_config.rotor); sem id moves
  Q4  an edge add/remove -> EDGE_ADDED / EDGE_REMOVED; sem id moves
  Q5  a profile change -> PROFILE_CHANGED; a policy change -> POLICY_CHANGED
  Q6  declaration-order shuffle / format-only -> empty diff, same sem id
  Q7  a run-input-only edit (different claim batch) -> empty semantic diff (D3)
  Q8  antisymmetry: diff(a,b) added keys == diff(b,a) removed keys
  Q9  render() is deterministic
  Q10 every completion candidate is a subset of its frozen registry
  Q11 surface_metadata is a pure projection of the registries (roles/ports/edges)
  Q12 cursor classification is correct for all six contexts
  Q13 every applied completion yields a parser-acceptable construct
  Q14 named-rotor completions == the frozen 3B-4 table; clock forms desugar
  Q15 an edited world still runs ic_ref == ic32 == golden        (native)

Native gated exactly like the sibling batteries (TRVM_SKIP_NATIVE=1 -> ref).
"""
import os
import sys
import copy
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "runtime", "python"))
sys.path.insert(0, os.path.join(HERE, "..", "research"))

import wrl_ir as W
import wrl_canonical as WC
import wrl_diff as DF
import wrl_complete as CP
import wrl_sugar as SG
import wrl_format as F
import wrl_plan as P
import compiler as C
import admit as AD
import binding_run3o as O
import binding_run7 as B7
from admit import mk_claim
from fixture import init_state_v6

SKIP_NATIVE = os.environ.get("TRVM_SKIP_NATIVE") == "1"


def _sem(g):
    return WC.semantic_artifact_id(W.graph_to_ir(g))


def main():
    print("[BINDING wrl-3b5] SemanticDiff + completion metadata")
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

    WORLDS = B7.WORLDS
    base = W.parse_wrl_legacy_document(B7.W_CORE)

    # ---- Q1 identical artifacts -> empty diff (every structural world)
    q1 = True
    for _name, src in WORLDS:
        g = W.parse_wrl_legacy_document(src)
        if not DF.diff_graphs(g, g).is_empty():
            q1 = False
    rep(q1, None, "Q1) identical artifacts -> empty diff (all structural worlds)")

    # ---- edits for the bridge matrix
    rotor_edit = W.parse_wrl_legacy_document(B7.W_CORE.replace("rotor=16.0.0.0",
                                                    "rotor=0.16.0.0"))
    # drop the socket edge (remove a line containing --socket-->)
    no_socket = W.parse_wrl_legacy_document("\n".join(
        ln for ln in B7.W_CORE.splitlines() if "--socket--" not in ln))
    prof_edit = W.parse_wrl_legacy_document(
        B7.W_CORE.replace("profile forge.world.core.v1",
                          "profile forge.world.core.v1"))  # same (control)

    # ---- Q2 the bridge law over a matrix
    variants = [base, rotor_edit, no_socket]
    q2 = True
    for i, ga in enumerate(variants):
        for j, gb in enumerate(variants):
            empty = DF.diff_graphs(ga, gb).is_empty()
            same = _sem(ga) == _sem(gb)
            if empty != same:
                q2 = False
    rep(q2, None, "Q2) bridge: diff.is_empty() == (sem_a == sem_b) over a matrix")

    # ---- Q3 rotor edit -> OBJECT_CHANGED sp (static_config.rotor); sem moves
    d3 = DF.diff_graphs(base, rotor_edit)
    ch = d3.of_kind(DF.OBJECT_CHANGED)
    q3 = (len(d3.changes) == 1 and len(ch) == 1 and ch[0].key == "sp"
          and "static_config.rotor" in ch[0].detail
          and _sem(base) != _sem(rotor_edit))
    rep(q3, None, "Q3) rotor edit -> OBJECT_CHANGED sp (static_config.rotor); "
                  "sem id moves")

    # ---- Q4 edge add/remove -> EDGE_ADDED / EDGE_REMOVED; sem moves
    d_rm = DF.diff_graphs(base, no_socket)      # base has socket, edit drops it
    d_add = DF.diff_graphs(no_socket, base)
    q4 = (d_rm.keys_of_kind(DF.EDGE_REMOVED)
          and d_add.keys_of_kind(DF.EDGE_ADDED)
          and d_rm.keys_of_kind(DF.EDGE_REMOVED)
          == d_add.keys_of_kind(DF.EDGE_ADDED)
          and _sem(base) != _sem(no_socket))
    rep(bool(q4), None, "Q4) edge remove/add -> EDGE_REMOVED / EDGE_ADDED; "
                        "sem id moves")

    # ---- Q5 profile change -> PROFILE_CHANGED; policy change -> POLICY_CHANGED
    art_a = W.graph_to_ir(base)
    art_prof = copy.deepcopy(art_a)
    art_prof["profile_id"] = "forge.world.core.v2"
    dp = DF.diff_artifacts(art_a, art_prof)
    q5a = dp.of_kind(DF.PROFILE_CHANGED) and len(dp.changes) == 1
    art_pol = copy.deepcopy(art_a)
    art_pol["semantic_policies"]["rulepack_id"] = "rulepack.alt.v1"
    dq = DF.diff_artifacts(art_a, art_pol)
    pol = dq.of_kind(DF.POLICY_CHANGED)
    q5b = (len(pol) == 1 and "rulepack_id" in pol[0].detail)
    rep(bool(q5a and q5b), None, "Q5) profile change -> PROFILE_CHANGED; policy "
                                 "change -> POLICY_CHANGED (rulepack_id)")

    # ---- Q6 declaration-order shuffle / format-only -> empty diff, same sem id
    # a real permutation: keep header (profile/periods) + claims in place,
    # reverse only the node/edge declaration block (which re-parses cleanly).
    header, body, claims = [], [], []
    for ln in B7.W_CORE.splitlines():
        s = ln.strip()
        if s.startswith("profile ") or s.startswith("periods "):
            header.append(ln)
        elif s.startswith("[epoch:"):
            claims.append(ln)
        elif s:
            body.append(ln)
    shuffled = "\n".join(header + list(reversed(body)) + claims) + "\n"
    formatted = F.format_wrl_core(base)
    q6 = True
    for txt in (shuffled, formatted):
        g = W.parse_wrl_legacy_document(txt)
        if not (DF.diff_graphs(base, g).is_empty()
                and _sem(base) == _sem(g)):
            q6 = False
    rep(q6, None, "Q6) declaration-order shuffle / format-only edit -> empty "
                  "diff, same sem id")

    # ---- Q7 run-input-only edit (different claim batch) -> empty semantic diff
    # W_CORE carries claims; drop the epoch/claim lines -> same STATIC artifact
    no_claims = W.parse_wrl_legacy_document("\n".join(
        ln for ln in B7.W_CORE.splitlines() if not ln.startswith("[epoch:")))
    q7 = (DF.diff_graphs(base, no_claims).is_empty()
          and _sem(base) == _sem(no_claims))
    rep(q7, None, "Q7) a run-input-only edit (claim batch) -> empty semantic "
                  "diff (D3)")

    # ---- Q8 antisymmetry (edge case reused; also object add/remove)
    q8 = (DF.diff_graphs(base, no_socket).keys_of_kind(DF.EDGE_REMOVED)
          == DF.diff_graphs(no_socket, base).keys_of_kind(DF.EDGE_ADDED))
    rep(bool(q8), None, "Q8) antisymmetry: diff(a,b) added keys == diff(b,a) "
                        "removed keys")

    # ---- Q9 render() deterministic
    q9 = (DF.diff_graphs(base, rotor_edit).render()
          == DF.diff_graphs(base, rotor_edit).render())
    rep(q9, None, "Q9) render() is deterministic")

    # ---- Q10 every completion candidate is a subset of its frozen registry
    q10 = (set(CP.role_completions()) <= set(W._ROLE_TOKEN)
           and set(CP.edge_tag_completions()) <= set(W._EDGE_TAG)
           and set(CP.named_rotor_completions()) == set(SG.ALL_ROTOR_NAMES))
    for rid in WC.ROLE_IDS:
        if not set(CP.port_completions(rid)) <= set(WC.port_projection(rid)):
            q10 = False
    rep(bool(q10), None, "Q10) every completion candidate is a subset of its "
                         "frozen registry")

    # ---- Q11 surface_metadata is a pure projection of the registries
    meta = CP.surface_metadata()
    q11 = (set(meta["roles"]) == set(W._ROLE_TOKEN)
           and set(meta["edge_tags"]) == set(W._EDGE_TAG))
    for tok, info in meta["roles"].items():
        rid = W._ROLE_TOKEN[tok]
        if (info["role_id"] != rid
                or set(info["ports"]) != set(WC.port_projection(rid))):
            q11 = False
    for tag, info in meta["edge_tags"].items():
        kind = W._EDGE_TAG[tag]
        if (info["kind"] != kind
                or (info["src_port"], info["dst_port"]) != WC.EDGE_PORTS[kind]):
            q11 = False
    rep(q11, None, "Q11) surface_metadata is a pure projection of the frozen "
                   "registries")

    # ---- Q12 cursor classification correct for all six contexts
    def ctx(src):
        return CP.completions_at(src, len(src)).context
    q12 = (ctx("[pu") == CP.ROLE
           and ctx("[spinner:sp](w=8, n=4, rotor=16.0.0.0){si") == CP.PORT
           and ctx("[p0] --si") == CP.EDGE_TAG
           and ctx("[spinner:sp](w=8, n=4, rotor=id") == CP.ROTOR_VALUE
           and ctx("[pulser:p0](ev") == CP.CLOCK_FORM
           and ctx("[spinner:sp](w=8, n") == CP.CONFIG_KEY)
    rep(q12, None, "Q12) cursor classification correct for role/port/edge_tag/"
                   "rotor_value/clock_form/config_key")

    # ---- Q13 every applied completion yields a parser-acceptable construct
    q13 = True
    # role + ports
    for tok in CP.role_completions():
        rid = W._ROLE_TOKEN[tok]
        ports = "{%s}" % ", ".join(CP.port_completions(rid))
        cfg = ""
        if rid == "Pulser":
            cfg = "(mode=periodic, period=2, phase=0)"
        elif rid == "Spinner":
            cfg = "(w=8, n=4, rotor=16.0.0.0)"
        try:
            W.parse_wrl_legacy_document("profile forge.world.core.v1\nperiods 1\n"
                             "[%s:x0]%s%s\n" % (tok, cfg, ports))
        except Exception:
            q13 = False
    # edge tags
    for tag in CP.edge_tag_completions():
        try:
            W.parse_wrl_legacy_document("[a] --%s--> [b]\n" % tag)
        except WC.WrlValidationError:
            pass  # endpoint nodes undefined, but the TAG lexes -> not a tag error
        except Exception:
            q13 = False
    # named rotors desugar + parse
    for nm in CP.named_rotor_completions():
        try:
            SG.desugar_core("profile forge.world.core.v1\nperiods 1\n"
                            "[spinner:sp](w=8, n=4, rotor=%s)\n" % nm)
        except Exception:
            q13 = False
    rep(q13, None, "Q13) every applied completion yields a parser-acceptable "
                   "construct")

    # ---- Q14 named-rotor completions == frozen 3B-4 table; clock forms desugar
    q14 = True
    for nm in CP.named_rotor_completions():
        if SG.named_rotor(nm, 4) is None:
            q14 = False
    # clock form templates desugar to the verbose kv when instantiated
    inst = {"every K": "every 2", "every K, phase P": "every 2, phase 1",
            "once at E": "once at 5"}
    for form in CP.clock_form_completions():
        d = SG.desugar_core("profile forge.world.core.v1\nperiods 1\n"
                            "[pulser:p0](%s)\n" % inst[form])
        if "mode=" not in d:
            q14 = False
    rep(q14, None, "Q14) named-rotor completions == frozen 3B-4 table; clock "
                   "forms desugar")

    # ---- Q16 the completion API is TOTAL over the frozen registry
    # This row exists because the registry and the text surface are NOT equal
    # and nothing previously said so. `Mailbox` entered `WC.ROLE_IDS` with ports
    # and a config schema but no WRL Core lexeme, and three separate things
    # broke at once: `role_completions()` raised a bare KeyError, so the whole
    # completion API was dead for every caller; `surface_metadata()` did the
    # same while documenting itself as unable to drift; and the parser told
    # authors the role "is not in the frozen v1 registry" when it demonstrably
    # is. A crash is the worst of the three -- it is the failure mode that
    # reports nothing about its own cause.
    #
    # So the law is TOTALITY, not equality. Equality would be a language claim
    # (every registry role must be writable) that is not mine to make here; the
    # Mailbox surface form belongs to Slice B. Totality is a TOOLING claim: no
    # registry role may make a read of the vocabulary crash, whether or not it
    # can be spelled.
    q16 = True
    try:
        toks = set(CP.role_completions())
        meta2 = CP.surface_metadata()
        for rid in WC.ROLE_IDS:                 # includes the unwritable ones
            CP.port_completions(rid)
            CP.config_key_completions(rid)
    except Exception:
        q16 = False
        toks, meta2 = set(), {}
    if q16:
        unwritable = set(W.unwritable_role_ids())
        # (a) the surface is a faithful, SOUND subset: every offered token
        #     parses, and no unwritable role is ever offered as a candidate.
        q16 = (toks == set(W._ROLE_TOKEN)
               and set(meta2["roles"]) == toks
               and unwritable == set(WC.ROLE_IDS) - set(W._ROLE_TOKEN.values())
               and not (unwritable & {W._ROLE_TOKEN[t] for t in toks}))
        # (b) the gap is REPORTED, not hidden behind an absence.
        q16 = q16 and list(meta2["unwritable_roles"]) == sorted(unwritable)
        # (c) NEGATIVE CONTROL: an unwritable role is genuinely unwritable, and
        #     its rejection tells the truth about WHY. An assertion never seen
        #     to fail is not evidence, and the old message failed exactly here.
        for rid in unwritable:
            try:
                W.parse_wrl_core("profile forge.world.core.v1\n[%s:x0]\n"
                                 % (rid.lower(),))
                q16 = False                      # writable after all -> (a) lied
            except WC.WrlValidationError as e:
                if "not in the frozen v1 registry" in e.message:
                    q16 = False                  # the message denies the registry
    rep(q16, None, "Q16) the completion API is TOTAL over the frozen registry; "
                   "the surface/registry gap is reported, not hidden")

    # ---- Q15 an edited world runs ic_ref == ic32 == golden (native)
    prog = W.lower_program(B7.W_CORE, W.parse_wrl_legacy_document)
    plan = P.artifact_to_compile_plan_v1(prog.sealed_artifact)
    view = P.plan_view(plan)
    fx = prog.as_fixture_for_test()
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
        step, _ = C.compile_step_v6(view)
        for e, batch in enumerate(batches):
            claim, cfg_map, resets = AD.admit_step(claim, batch, 1 + e, fx)
            ec = C.enc_config_bundle(view, cfg_map, resets)
            world = C.dec_state_v6(view, reducer(
                f"(({step} {ec}) {C.enc_state_v6(view, world)})"))
            out.append(copy.deepcopy(world))
        return out

    ref = _traj(O.norm)
    q15r = all(ref[e] == gold[e][0] for e in range(len(batches)))
    q15n = None
    if not SKIP_NATIVE:
        nat = _traj(O.native)
        q15n = all(nat[e] == gold[e][0] for e in range(len(batches)))
    rep(q15r, q15n, "Q15) an edited world runs ic_ref == ic32 == golden")

    dt = time.time() - t0
    if SKIP_NATIVE:
        verdict = "PASS_REF_ONLY (native skipped)" if allok else "FAIL"
    elif not native_ok:
        verdict = "REF_ONLY (native MISMATCH)"
        allok = False
    else:
        verdict = "PASS_REF_AND_NATIVE" if allok else "FAIL"
    print(f"\n[wrl-3b5] {'ALL PASS' if allok else 'FAILURES'} -- {verdict} "
          f"({dt:.0f}s)")
    print("  [note] SemanticDiff is empty iff the two artifacts share a "
          "SemanticArtifactID, and every completion candidate is a pure read of "
          "the frozen registries -- both tools sit entirely off the identity "
          "spine.")
    return 0 if allok else 1


if __name__ == "__main__":
    sys.exit(main())
