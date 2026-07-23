"""binding_run40.py -- v0.7-3 IMMUTABLE TEMPLATE CATALOG battery (PC1-PC24).

GPT-5.6's v0.7-3 ruling: ship a curated, read-only STARTING catalog of exactly
three release-owned templates -- Golden ADMIT Demo, ADMIT Acceptance Bench, and
Blank Spinner World -- as schema-validated `TemplateManifestV1` documents whose
every Forge identity is RE-DERIVED (never trusted) at load. It introduces NO new
semantic profile, IR version, artifact identity, actor role, edge type, graph
transaction, or runtime law: the demo world still seals to the frozen
DEMO_WORLD_SEMANTIC_ID and ic_ref == ic32 == Fixture oracle stays green (PC24).

Like binding_run37/38/39 it splits into a SERVER / IDENTITY layer (in-process,
temp FORGE_PROJECT_ROOT) and a FRONTEND layer (static assertions over
spinner_bench.js / .html / .css).

  PC1  the catalog holds EXACTLY three templates
  PC2  each template has a unique, versioned template_id (a catalog id, not a
       Forge semantic identity)
  PC3  each template re-derives its world SemanticArtifactID from its source
  PC4  each template re-derives every ScenarioDigest from its scenario docs
  PC5  each template re-derives every ReplayBundleID
  PC6  the Golden ADMIT Demo identities are byte-for-byte the frozen preset
  PC7  the Acceptance Bench shares the Golden world's SemanticArtifactID
  PC8  the Acceptance Bench has a DIFFERENT ScenarioDigest + ReplayBundleID
  PC9  the Acceptance Bench default scenario folds the full 9-epoch run
  PC10 the Blank Spinner World is the specified minimal scaffold (Spinner+Orb+socket)
  PC11 the Blank Spinner World has its OWN genuine semantic identity
  PC12 Explore (preview) creates NO project
  PC13 Explore (preview) creates NO recovery journal and NO last-session pointer
  PC14 Explore (preview) is read-only (locks every authoring surface)
  PC15 Use Template creates a project ONLY after an explicit id confirmation
  PC16 a new project preserves the template's initial identities
  PC17 editing a template-derived project can NOT alter the template bytes
  PC18 two projects from one template are fully independent
  PC19 the created_from_template provenance moves NO Forge identity
  PC20 a corrupted template fails closed with FORGE_TEMPLATE_IDENTITY
  PC21 shallow GET /api/health reports 3 valid templates
  PC22 the catalog + files are in the deterministic release MANIFEST.sha256
  PC23 the extracted release ships a valid, identity-verified catalog
  PC24 ic_ref == ic32 == Fixture oracle stays green                    (native)

Gates:

    python3 binding_run40.py --gate smoke    # PC1-PC23 (fast, no compiler)
    python3 binding_run40.py --gate native   # PC24 (compiler; ic_ref==ic32==oracle)
    python3 binding_run40.py                  # all of the above
"""
import argparse
import importlib.util
import os
import shutil
import sys
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "runtime", "python"))
sys.path.insert(0, os.path.join(HERE, "..", "research"))

SKIP_NATIVE = os.environ.get("TRVM_SKIP_NATIVE") == "1"
ALPHA = "v0.7.0-alpha.4"

def _read(path):
    return open(path, encoding="utf-8").read() if os.path.isfile(path) else ""


def _slice(text, start_marker, end_marker):
    i = text.find(start_marker)
    if i < 0:
        return ""
    j = text.find(end_marker, i + len(start_marker))
    return text[i:] if j < 0 else text[i:j]


def main():
    ap = argparse.ArgumentParser(description="Immutable template catalog battery.")
    ap.add_argument("--gate", default="all", choices=["all", "smoke", "native"])
    args = ap.parse_args()
    do_smoke = args.gate in ("all", "smoke")
    do_native = args.gate in ("all", "native") and not SKIP_NATIVE

    print("[BINDING wrl-%s] immutable template catalog -- PC1-PC24 (gate=%s)"
          % (ALPHA, args.gate))
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

    data_root = tempfile.mkdtemp(prefix="forge-pc-data-")
    project_root = os.path.join(data_root, "projects")
    os.environ["FORGE_PROJECT_ROOT"] = project_root
    import spinner_bench as SB
    import wrl_templates as TP
    import wrl_scenario as SC
    import wrl_canonical as WC
    import wrl_ir as W
    import wrl_sugar as SG
    import wrl_project as PJ
    DEMO_SEM = SB.DEMO_WORLD_SEMANTIC_ID
    CAT = SB._TEMPLATE_CATALOG

    js = _read(os.path.join(HERE, "spinner_bench.js"))
    htmldoc = _read(os.path.join(HERE, "spinner_bench.html"))

    explore_block = _slice(js, "async function enterExploreTemplate",
                           "async function doUseTemplate")
    use_block = _slice(js, "async function doUseTemplate", "async function doMakeCopy")

    golden = CAT.get(TP.GOLDEN_ADMIT_ID) if CAT else None
    bench = CAT.get(TP.ACCEPTANCE_BENCH_ID) if CAT else None
    blank = CAT.get(TP.BLANK_SPINNER_ID) if CAT else None

    if do_smoke:
        # ---- PC1 exactly three templates ------------------------------------
        pc1 = (CAT is not None and CAT.count == 3
               and set(CAT.ids()) == {TP.GOLDEN_ADMIT_ID, TP.ACCEPTANCE_BENCH_ID,
                                      TP.BLANK_SPINNER_ID})
        rep(pc1, None, "PC1) the loaded catalog holds EXACTLY the three "
            "release-owned templates")

        # ---- PC2 unique versioned ids ---------------------------------------
        ids = CAT.ids() if CAT else []
        pc2 = (len(set(ids)) == 3
               and all(i.startswith("forge.template.") and i.endswith(".v1")
                       for i in ids)
               and all(not i.startswith(("sem-", "scen-", "replay-")) for i in ids))
        rep(pc2, None, "PC2) each template_id is unique + versioned and is a "
            "catalog identifier, not a Forge semantic identity")

        # ---- PC3/PC4/PC5 each template RE-DERIVES its identities -------------
        pc3 = pc4 = pc5 = True
        for m in (golden, bench, blank):
            try:
                TP.verify_template_identity(m)
            except Exception:
                pc3 = pc4 = pc5 = False
                break
            prog = W.lower_program(SG.desugar_core(m["canonical_world_source"]),
                                   W.parse_wrl_core)
            if prog.semantic_artifact_id != m["world_semantic_id"]:
                pc3 = False
            for doc in m["scenarios"]:
                if SC.scenario_digest(doc["scenario"]) != doc["scenario_digest"]:
                    pc4 = False
                ir = SC.canonicalize_scenario_v1(doc["scenario"])["initial_runtime"]
                rep_id = SC.replay_bundle_id(m["world_semantic_id"],
                                             doc["scenario_digest"], ir)
                if rep_id != m["expected_replay_bundle_ids"][doc["name"]]:
                    pc5 = False
        rep(pc3, None, "PC3) each template re-lowers its source to the recorded "
            "world SemanticArtifactID")
        rep(pc4, None, "PC4) each template re-digests every scenario to the "
            "recorded ScenarioDigest")
        rep(pc5, None, "PC5) each template re-computes every ReplayBundleID")

        # ---- PC6 Golden identities are the frozen preset --------------------
        g_def = golden["default_scenario_document_id"]
        demo_scen = SC.demo_scenario(DEMO_SEM)
        pc6 = (golden["world_semantic_id"] == DEMO_SEM
               and g_def == "golden"
               and golden["expected_scenario_digests"]["golden"]
                   == SC.scenario_digest(demo_scen))
        rep(pc6, None, "PC6) the Golden ADMIT Demo world + default scenario "
            "identities are byte-for-byte the frozen preset")

        # ---- PC7 Bench shares the Golden world id ---------------------------
        pc7 = (bench["world_semantic_id"] == golden["world_semantic_id"] == DEMO_SEM)
        rep(pc7, None, "PC7) the Acceptance Bench shares the Golden world's "
            "SemanticArtifactID (a scenario edit never moves the world id)")

        # ---- PC8 Bench has a different digest + replay ----------------------
        b_def = bench["default_scenario_document_id"]
        g_dig = golden["expected_scenario_digests"][g_def]
        b_dig = bench["expected_scenario_digests"][b_def]
        g_rep = golden["expected_replay_bundle_ids"][g_def]
        b_rep = bench["expected_replay_bundle_ids"][b_def]
        pc8 = (b_def == "bench" and g_dig != b_dig and g_rep != b_rep)
        rep(pc8, None, "PC8) the Acceptance Bench default has a DIFFERENT "
            "ScenarioDigest and ReplayBundleID than the Golden default")

        # ---- PC9 Bench default folds the full 9-epoch run -------------------
        bench_scen = next(d["scenario"] for d in bench["scenarios"]
                          if d["name"] == b_def)
        r = SB._run_payload(bench["canonical_world_source"], bench_scen)
        pc9 = (r.get("ok") and len(r.get("epochs", [])) == 9
               and r.get("semantic_artifact_id") == DEMO_SEM
               and r.get("scenario_digest") == b_dig)
        rep(pc9, None, "PC9) the Acceptance Bench default scenario folds the "
            "complete 9-epoch acceptance run over the frozen world")

        # ---- PC10 Blank is the specified minimal scaffold -------------------
        # minimal per the ruling = exactly one Spinner + one Orb + one legal
        # SocketControl connection, no authored claims, one idle epoch -- and it
        # FOLDS cleanly. (Lowering alone does not reject a lone spinner, so
        # minimality is asserted by the scaffold's exact shape, not by rejecting
        # something smaller.)
        blank_ok = True
        blank_ir = None
        try:
            blank_lp = W.lower_program(
                SG.desugar_core(blank["canonical_world_source"]), W.parse_wrl_core)
            blank_ir = blank_lp.artifact
        except Exception:
            blank_ok = False
        roles = sorted(o["role"] for o in (blank_ir or {}).get("objects", []))
        b_edges = (blank_ir or {}).get("edges", [])
        blank_scen = blank["scenarios"]
        b_ep = blank_scen[0]["scenario"]["epochs"] if blank_scen else []
        folds = False
        if blank_ok:
            rr = SB._run_payload(blank["canonical_world_source"],
                                 blank_scen[0]["scenario"])
            folds = rr.get("ok") and len(rr.get("epochs", [])) == 1
        pc10 = (blank_ok and roles == ["Orb", "Spinner"]
                and len(b_edges) == 1 and b_edges[0]["kind"] == "SocketControl"
                and len(blank_scen) == 1 and len(b_ep) == 1
                and b_ep[0].get("claims") == [] and folds)
        rep(pc10, None, "PC10) the Blank Spinner World is exactly one Spinner + one "
            "Orb + one SocketControl connection, no authored claims, one idle "
            "epoch, and folds cleanly (minimal scaffold)")

        # ---- PC11 Blank has its own genuine identity ------------------------
        pc11 = (blank["world_semantic_id"].startswith("sem-")
                and blank["world_semantic_id"] != DEMO_SEM
                and blank["world_semantic_id"] != bench["world_semantic_id"])
        rep(pc11, None, "PC11) the Blank Spinner World carries its OWN genuine "
            "SemanticArtifactID (not the demo's)")

        # ---- PC12 preview creates no project --------------------------------
        before = {p["project_id"] for p in SB._PROJECT_CACHE.list_infos()}
        last_before = SB._LAST_SESSION.get()
        pv = SB._template_preview_payload({"template_id": TP.BLANK_SPINNER_ID})
        after = {p["project_id"] for p in SB._PROJECT_CACHE.list_infos()}
        pc12 = (pv.get("ok") and pv.get("template_id") == TP.BLANK_SPINNER_ID
                and after == before)
        rep(pc12, None, "PC12) Explore (preview) rebuilds the in-memory session "
            "and creates NO project")

        # ---- PC13 preview creates no recovery journal + no pointer ----------
        last_after = SB._LAST_SESSION.get()
        no_prov = not os.path.isfile(os.path.join(SB._PROVENANCE_DIR, "main.json"))
        rec_dir = os.path.join(os.path.dirname(os.path.abspath(project_root)),
                               ".recovery")
        no_rec = not os.path.isfile(os.path.join(rec_dir, "main.json"))
        pc13 = (last_after == last_before and no_prov and no_rec)
        rep(pc13, None, "PC13) Explore (preview) writes NO recovery journal and "
            "leaves the last-session pointer untouched")

        # ---- PC14 preview is read-only --------------------------------------
        pc14 = ("/api/template/preview" in explore_block
                and "setExplore(true)" in explore_block
                and "_EXPLORE_DISABLED" in js and "readOnly = on" in js
                and "#btn-apply" in js and "#btn-commit" in js)
        rep(pc14, None, "PC14) Explore (preview) enters read-only mode "
            "(setExplore locks every authoring surface)")

        # ---- PC15 Use creates a project only after confirmation -------------
        pc15 = (use_block.find("dialogForm") >= 0
                and use_block.find("dialogForm") < use_block.find("/api/template/use")
                and "project_id: f.pid" in use_block)
        server_needs_id = SB._template_use_payload(
            {"template_id": TP.GOLDEN_ADMIT_ID, "project_id": None})
        pc15 = pc15 and (server_needs_id.get("ok") is not True)
        rep(pc15, None, "PC15) Use Template creates a project ONLY after an "
            "explicit project-id confirmation")

        # ---- PC16 a new project preserves the template identities ------------
        u = SB._template_use_payload({"template_id": TP.GOLDEN_ADMIT_ID,
                                      "project_id": "pc16", "name": "pc16"})
        ov = SB._project_open_payload({"project_id": "pc16"})
        doc = SB._PROJECT_CACHE._store.load("pc16")
        saved_scen = PJ._scenarios_of(doc)
        saved_digs = {d["name"]: d["scenario_digest"] for d in saved_scen}
        pc16 = (u.get("ok")
                and PJ._active_world_id_of(doc) == golden["world_semantic_id"]
                and ov["view"].get("active_semantic_id") == golden["world_semantic_id"]
                and saved_digs == golden["expected_scenario_digests"])
        rep(pc16, None, "PC16) a project made from a template preserves its "
            "initial world + scenario identities")

        # ---- PC17 editing a project can NOT alter the template bytes ---------
        tpl_path = os.path.join(SB._TEMPLATE_DIR, "golden-admit-v1.json")
        tpl_before = _read(tpl_path)
        SB._project_save_payload({"session_id": "pc16"})
        SB._PROJECT_CACHE.rename("pc16", "pc16 renamed")
        tpl_after = _read(tpl_path)
        pc17 = (tpl_before == tpl_after and tpl_before != "")
        rep(pc17, None, "PC17) editing/saving a template-derived project never "
            "touches the immutable template bytes")

        # ---- PC18 two projects from one template are independent -------------
        SB._template_use_payload({"template_id": TP.GOLDEN_ADMIT_ID,
                                  "project_id": "pc18a", "name": "A"})
        SB._template_use_payload({"template_id": TP.GOLDEN_ADMIT_ID,
                                  "project_id": "pc18b", "name": "B"})
        SB._PROJECT_CACHE.rename("pc18a", "A renamed")
        da = SB._PROJECT_CACHE._store.load("pc18a")
        db = SB._PROJECT_CACHE._store.load("pc18b")
        pids = {p["project_id"] for p in SB._PROJECT_CACHE.list_infos()}
        pc18 = ("pc18a" in pids and "pc18b" in pids
                and da["name"] == "A renamed" and db["name"] == "B"
                and PJ._active_world_id_of(da) == PJ._active_world_id_of(db)
                    == golden["world_semantic_id"])
        rep(pc18, None, "PC18) two projects from one template are fully "
            "independent (renaming one leaves the other untouched)")

        # ---- PC19 provenance moves no Forge identity ------------------------
        prov = SB._read_provenance("pc16")
        pc19 = (isinstance(prov, dict)
                and prov.get("template_id") == TP.GOLDEN_ADMIT_ID
                and "created_from_template" not in doc
                and PJ._active_world_id_of(doc) == golden["world_semantic_id"])
        rep(pc19, None, "PC19) created_from_template is a non-authoritative "
            "sidecar -- it is absent from the project doc and moves no identity")

        # ---- PC20 a corrupted template fails closed -------------------------
        def _fails_identity(mutate):
            m = CAT.get(TP.GOLDEN_ADMIT_ID)
            mutate(m)
            try:
                TP.load_template_manifest(m)
                return False
            except WC.WrlValidationError as ex:
                return ex.code == TP.FORGE_TEMPLATE_IDENTITY
            except Exception:
                return False

        def _tamper_source(m):
            m["canonical_world_source"] = m["canonical_world_source"].replace(
                "quarter_turn_z", "256.0.0.0")

        def _tamper_digest(m):
            m["expected_scenario_digests"][m["default_scenario_document_id"]] = \
                "scen-" + "0" * 64

        pc20 = _fails_identity(_tamper_source) and _fails_identity(_tamper_digest)
        rep(pc20, None, "PC20) a tampered template (moved world source OR a wrong "
            "expected digest) fails closed with FORGE_TEMPLATE_IDENTITY")

        # ---- PC21 shallow health reports 3 valid templates ------------------
        hp = SB._health_payload()
        pc21 = (hp.get("templates_ok") is True and hp.get("template_count") == 3
                and hp.get("identity_ok") is True)
        rep(pc21, None, "PC21) shallow GET /api/health reports templates_ok + "
            "template_count == 3 (folding nothing)")

        # ---- PC22 catalog + files in the deterministic manifest -------------
        spec = importlib.util.spec_from_file_location(
            "bfr", os.path.join(HERE, "tools", "build_forge_release.py"))
        bfr = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(bfr)
        out_a = os.path.join(data_root, "rel-a")
        out_b = os.path.join(data_root, "rel-b")
        zip_a = os.path.join(data_root, "a.zip")
        zip_b = os.path.join(data_root, "b.zip")
        rc_a = bfr.build(out_a, zip_path=zip_a, force=True)
        rc_b = bfr.build(out_b, zip_path=zip_b, force=True)
        man_a = _read(os.path.join(out_a, "MANIFEST.sha256"))
        tpl_files = ["forge/templates/catalog.json",
                     "forge/templates/golden-admit-v1.json",
                     "forge/templates/acceptance-bench-v1.json",
                     "forge/templates/blank-spinner-v1.json"]
        ships = all(f in man_a for f in tpl_files)
        byte_equal = (os.path.isfile(zip_a) and os.path.isfile(zip_b)
                      and open(zip_a, "rb").read() == open(zip_b, "rb").read())
        pc22 = (rc_a == 0 and rc_b == 0 and ships and byte_equal
                and "wrl_templates.py" in bfr.FORGE_MODULES)
        rep(pc22, None, "PC22) the release ships the catalog + all three template "
            "files in a deterministic (byte-identical) MANIFEST.sha256")

        # ---- PC23 the extracted release ships a valid, verified catalog -----
        ext_dir = os.path.join(out_a, "forge", "templates")
        ext_cat = TP.TemplateCatalog.load_dir(ext_dir)
        src_bytes = {f: _read(os.path.join(SB._TEMPLATE_DIR, os.path.basename(f)))
                     for f in tpl_files}
        ext_bytes = {f: _read(os.path.join(out_a, f)) for f in tpl_files}
        pc23 = (ext_cat.count == 3 and src_bytes == ext_bytes
                and set(ext_cat.ids()) == set(CAT.ids()))
        rep(pc23, None, "PC23) the extracted release catalog loads + re-verifies "
            "and its files byte-match the source templates")

    # ---- PC24 native parity over the template worlds ------------------------
    # The Golden world is driven, so it verifies through the full oracle chain
    # ic_ref == ic32 == Fixture. The Blank scaffold is deliberately UN-driven
    # (its Spinner has no sig-in connection), which is legal for the production
    # reducers but outside the Fixture oracle's constructible domain -- so it is
    # held to native parity ic_ref == ic32 only. Both re-derive their world id.
    if do_native:
        cg = SB._verify_payload(golden["canonical_world_source"], oracle=True)
        cb = SB._verify_payload(blank["canonical_world_source"], oracle=False)
        pc24_ref = bool(
            cg["ok"] and cg.get("oracle", {}).get("match") is True
            and cg["semantic_artifact_id"] == golden["world_semantic_id"]
            and cb["ok"]
            and cb["semantic_artifact_id"] == blank["world_semantic_id"])
        pc24_nat = bool(cg.get("native") is True and cg.get("parity") is True
                        and cb.get("native") is True and cb.get("parity") is True)
        rep(pc24_ref, pc24_nat, "PC24) native parity holds over the template worlds "
            "(Golden ic_ref==ic32==Fixture; Blank ic_ref==ic32, un-driven)")

    shutil.rmtree(data_root, ignore_errors=True)

    dt = time.time() - t0
    if SKIP_NATIVE:
        verdict = "PASS_REF_ONLY (native skipped)" if allok else "FAIL"
    elif not native_ok:
        verdict = "REF_ONLY (native MISMATCH)"
        allok = False
    else:
        verdict = "PASS_REF_AND_NATIVE" if allok else "FAIL"
    print(f"\n[wrl-{ALPHA}] {'ALL PASS' if allok else 'FAILURES'} -- {verdict} "
          f"({dt:.0f}s)")
    print("  [note] v0.7-3 is the Immutable Template Catalog: exactly three "
          "release-owned templates (PC1) whose Forge identities are RE-DERIVED, "
          "never trusted (PC3-PC5); the Golden identities are the frozen preset "
          "(PC6); the Bench shares the world id but moves the scenario/replay "
          "(PC7/PC8) and folds all 9 epochs (PC9); the Blank is minimal (PC10) "
          "with its own id (PC11); Explore is project-free + read-only (PC12-PC14) "
          "while Use creates an independent project preserving identities "
          "(PC15/PC16/PC18); template bytes are immutable (PC17) and provenance "
          "moves no identity (PC19); corruption fails closed (PC20); and the "
          "release ships a deterministic, re-verified catalog (PC22/PC23). NO new "
          "semantic profile, IR version, identity, actor role, edge type, graph "
          "transaction, or runtime law.")
    return 0 if allok else 1


if __name__ == "__main__":
    sys.exit(main())
