"""binding_run41.py -- v0.7-3.1 TEMPLATE REOPEN CLOSURE battery (PC25-PC30).

GPT-5.6's v0.7-3.1 ruling (BEFORE any visual polish): close the two reopen gaps
left by the v0.7-3 Immutable Template Catalog.

  1. The manifest `canvas_layout` was dead data -- neither Explore (preview) nor
     Use applied it. It must now seed the presentation in BOTH paths, so Explore
     and Use begin with a presentation-equivalent layout BY OBJECT ID + EDGE KEY,
     WHILE layout stays outside semantic identity.
  2. Template scenarios were not rehydrated on reopen: the client re-read the
     GLOBAL /api/scenario golden/bench presets, so a reopened Blank ran Golden.
     The MODEL is "templates seed projects; once created, the project OWNS its
     scenario documents and no longer depends on the template catalog." So the
     server returns `scenario_documents` + `selected_scenario_document_id` on
     project open, and the client loads THOSE for every project.

This introduces NO new semantic profile, IR version, artifact identity, actor
role, edge type, graph transaction, or runtime law: layout + copy are release
presentation metadata that move no identity, and the demo world still seals to
the frozen DEMO_WORLD_SEMANTIC_ID with ic_ref == ic32 == Fixture green (PC30).

  PC25 Explore (preview) applies the manifest canvas_layout exactly
  PC26 Use applies the SAME layout to the new project; Explore + Use begin with
       presentation-equivalent layouts BY OBJECT ID + EDGE KEY (invariant)
  PC27 reopening the Acceptance Bench restores its bound default scenario and
       folds the full 9-epoch run from the PROJECT's OWN scenario docs
  PC28 REAL RESTART: create-from-Blank -> persist -> drop the in-memory cache ->
       reopen from disk -> the open payload selects idle -> run -> exactly one
       epoch over the Blank's own world (not Golden/Bench)
  PC29 reopen restores the project's own scenarios with NO template/provenance
       lookup (works even with the catalog + provenance sidecar removed)
  PC30 editing a project's layout moves NO semantic identity and NO template
       bytes; the REOPENED Golden-derived project source (after a persisted
       layout edit + fresh-cache reopen) still folds
       ic_ref == ic32 == Fixture                                       (native)

Gates:

    python3 binding_run41.py --gate smoke    # PC25-PC29 (fast, no compiler)
    python3 binding_run41.py --gate native   # PC30 (compiler; ic_ref==ic32==oracle)
    python3 binding_run41.py                  # all of the above
"""
import argparse
import copy
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


def _pres_map(layout):
    """Presentation of a CanvasLayoutV1 keyed by node object_id / edge edge_key,
    order-independent -- the shape a byte-for-byte presentation comparison needs
    (the reconciled layout keeps draft ORDER, so a positional compare is wrong)."""
    m = {}
    for n in (layout or {}).get("nodes", []):
        m["n:" + n["object_id"]] = n["presentation"]
    for e in (layout or {}).get("edges", []):
        m["e:" + e["edge_key"]] = e["presentation"]
    return m


def main():
    ap = argparse.ArgumentParser(description="Template reopen closure battery.")
    ap.add_argument("--gate", default="all", choices=["all", "smoke", "native"])
    args = ap.parse_args()
    do_smoke = args.gate in ("all", "smoke")
    do_native = args.gate in ("all", "native") and not SKIP_NATIVE

    print("[BINDING wrl-%s] template reopen closure -- PC25-PC30 (gate=%s)"
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

    data_root = tempfile.mkdtemp(prefix="forge-pc31-data-")
    project_root = os.path.join(data_root, "projects")
    os.environ["FORGE_PROJECT_ROOT"] = project_root
    import spinner_bench as SB
    import wrl_templates as TP
    import wrl_project as PJ
    DEMO_SEM = SB.DEMO_WORLD_SEMANTIC_ID
    CAT = SB._TEMPLATE_CATALOG

    js = _read(os.path.join(HERE, "spinner_bench.js"))

    golden = CAT.get(TP.GOLDEN_ADMIT_ID)
    bench = CAT.get(TP.ACCEPTANCE_BENCH_ID)
    blank = CAT.get(TP.BLANK_SPINNER_ID)

    if do_smoke:
        # ---- PC25 Explore applies the manifest canvas_layout exactly ---------
        # Preview rebuilds the in-memory `main` session seeded with the manifest
        # layout; its presentation must equal the manifest's presentation for
        # every node + edge key.
        pv = SB._template_preview_payload({"template_id": TP.BLANK_SPINNER_ID})
        pv_sess = SB._DEMO_SESSIONS.get(SB._DEMO_ID)
        preview_pres = _pres_map(pv_sess.layout if pv_sess else None)
        manifest_pres = _pres_map(blank["canvas_layout"])
        pc25 = (pv.get("ok") and bool(manifest_pres)
                and preview_pres == manifest_pres)
        rep(pc25, None, "PC25) Explore (preview) applies the manifest "
            "canvas_layout exactly (presentation matches for every node + edge)")

        # ---- PC26 Use applies the SAME layout; Explore + Use byte-equivalent -
        u = SB._template_use_payload({"template_id": TP.BLANK_SPINNER_ID,
                                      "project_id": "pc26", "name": "pc26"})
        doc = SB._PROJECT_CACHE._store.load("pc26")
        project_pres = _pres_map(doc.get("canvas_layout"))
        pc26 = (u.get("ok")
                and project_pres == manifest_pres          # Use == manifest
                and project_pres == preview_pres)          # Use == Explore
        rep(pc26, None, "PC26) Use applies the SAME manifest layout to the new "
            "project -- Explore + Use begin with presentation-equivalent layouts "
            "BY OBJECT ID + EDGE KEY (order-independent; outside semantic identity)")

        # ---- PC27 reopen the Bench restores its default + folds 9 epochs ------
        SB._template_use_payload({"template_id": TP.ACCEPTANCE_BENCH_ID,
                                  "project_id": "pc27", "name": "pc27"})
        ov = SB._project_open_payload({"project_id": "pc27"})
        sel = ov.get("selected_scenario_document_id")
        docs = {d["name"]: d for d in (ov.get("scenario_documents") or [])}
        r27 = None
        if sel in docs:
            r27 = SB._run_payload(ov["view"]["text"], docs[sel]["scenario"])
        pc27 = (ov.get("ok") and sel == "bench" and set(docs) == {"golden", "bench"}
                and r27 and r27.get("ok") and len(r27.get("epochs", [])) == 9
                and r27.get("semantic_artifact_id") == DEMO_SEM
                and r27.get("scenario_digest")
                    == bench["expected_scenario_digests"]["bench"])
        rep(pc27, None, "PC27) reopening the Acceptance Bench restores its bound "
            "default scenario and folds the full 9-epoch run from the PROJECT's "
            "own scenario documents")

        # ---- PC28 REAL RESTART: create-from-Blank, persist, drop cache, reopen
        SB._template_use_payload({"template_id": TP.BLANK_SPINNER_ID,
                                  "project_id": "pc28", "name": "pc28"})
        # simulate a full process restart: a brand-new store + session cache over
        # the SAME on-disk root, discarding every in-memory session.
        fresh_store = PJ.ForgeProjectStore(project_root)
        SB._PROJECT_CACHE = PJ.ProjectSessionCache(
            fresh_store, SB.DEMO_WORLD_SOURCE,
            scenarios_for=SB._default_scenarios,
            project_version=PJ.PROJECT_V2_VERSION)
        ov28 = SB._project_open_payload({"project_id": "pc28"})
        sel28 = ov28.get("selected_scenario_document_id")
        docs28 = {d["name"]: d for d in (ov28.get("scenario_documents") or [])}
        r28 = None
        if sel28 in docs28:
            r28 = SB._run_payload(ov28["view"]["text"], docs28[sel28]["scenario"])
        pc28 = (ov28.get("ok") and sel28 == "idle" and set(docs28) == {"idle"}
                and ov28["view"].get("active_semantic_id")
                    == blank["world_semantic_id"]
                and r28 and r28.get("ok") and len(r28.get("epochs", [])) == 1
                and r28.get("semantic_artifact_id") == blank["world_semantic_id"])
        rep(pc28, None, "PC28) after a REAL RESTART (persist -> drop cache -> "
            "reopen from disk) a Blank project restores its idle selection and "
            "folds exactly one epoch over its OWN world -- never Golden/Bench")

        # ---- PC29 reopen needs NO template / provenance lookup ---------------
        # Remove the provenance sidecar AND hide the catalog: a plain reopen must
        # still restore the project's own scenarios (the project, not the
        # catalog, owns them).
        prov_path = os.path.join(SB._PROVENANCE_DIR, "pc28.json")
        prov_before = os.path.isfile(prov_path)
        if prov_before:
            os.remove(prov_path)
        saved_cat = SB._TEMPLATE_CATALOG
        SB._TEMPLATE_CATALOG = None            # a reopen must not touch the catalog
        try:
            ov29 = SB._project_open_payload({"project_id": "pc28"})
        finally:
            SB._TEMPLATE_CATALOG = saved_cat
        docs29 = {d["name"]: d for d in (ov29.get("scenario_documents") or [])}
        pc29 = (prov_before and ov29.get("ok")
                and ov29.get("selected_scenario_document_id") == "idle"
                and set(docs29) == {"idle"}
                and not os.path.isfile(prov_path))
        rep(pc29, None, "PC29) reopen restores the project's own scenarios with "
            "NO template/provenance lookup (works with the catalog + sidecar gone)")

        # ---- PC30 (smoke half) layout edit moves no id + no template bytes ----
        # Golden-derived project: a presentation-only gesture, persisted and then
        # reopened from a fresh cache, must leave the active SemanticArtifactID +
        # the immutable template bytes untouched while the moved presentation
        # survives.
        SB._template_use_payload({"template_id": TP.GOLDEN_ADMIT_ID,
                                  "project_id": "pc30", "name": "pc30"})
        tpl_path = os.path.join(SB._TEMPLATE_DIR, "golden-admit-v1.json")
        tpl_before = _read(tpl_path)
        sess30 = SB._PROJECT_CACHE.open("pc30")
        id_before = sess30.draft.active_semantic_id
        target = sess30.layout["nodes"][0]["object_id"]
        moved = sess30.apply_gesture(
            {"kind": "set_presentation", "object_id": target,
             "presentation": {"x": 999, "y": 777}})
        SB._PROJECT_CACHE.persist("pc30")
        # reopen from a fresh cache so the assertion reads persisted disk state.
        SB._PROJECT_CACHE = PJ.ProjectSessionCache(
            PJ.ForgeProjectStore(project_root), SB.DEMO_WORLD_SOURCE,
            scenarios_for=SB._default_scenarios,
            project_version=PJ.PROJECT_V2_VERSION)
        ov30 = SB._project_open_payload({"project_id": "pc30"})
        moved_pres = _pres_map(SB._PROJECT_CACHE.open("pc30").layout)
        id_after = ov30["view"].get("active_semantic_id")
        tpl_after = _read(tpl_path)
        pc30_smoke = (moved.get("gesture") == "presentation"
                      and id_after == id_before == golden["world_semantic_id"]
                      and moved_pres.get("n:" + target, {}).get("x") == 999
                      and tpl_before == tpl_after and tpl_before != "")
        rep(pc30_smoke, None, "PC30) a presentation-only layout edit moves NO "
            "semantic identity and NO template bytes (persists across reopen)")

    # ---- PC30 (native half) the REOPENED project source folds full chain ----
    # Self-contained per the ruling so the label and the assertion coincide: the
    # native gate independently (1) creates the Golden-derived project, (2)
    # changes its layout, (3) persists, (4) reopens from a FRESH cache, and (5)
    # verifies the REOPENED PROJECT SOURCE (never the template source) still
    # folds ic_ref == ic32 == Fixture to the Golden world identity.
    if do_native:
        SB._template_use_payload({"template_id": TP.GOLDEN_ADMIT_ID,
                                  "project_id": "pc30n", "name": "pc30n"})
        sess30n = SB._PROJECT_CACHE.open("pc30n")
        target30 = sess30n.layout["nodes"][0]["object_id"]
        sess30n.apply_gesture(
            {"kind": "set_presentation", "object_id": target30,
             "presentation": {"x": 314, "y": 271}})
        SB._PROJECT_CACHE.persist("pc30n")
        # a fresh cache over the same on-disk root = a real reopen from disk.
        SB._PROJECT_CACHE = PJ.ProjectSessionCache(
            PJ.ForgeProjectStore(project_root), SB.DEMO_WORLD_SOURCE,
            scenarios_for=SB._default_scenarios,
            project_version=PJ.PROJECT_V2_VERSION)
        ov30n = SB._project_open_payload({"project_id": "pc30n"})
        cg = SB._verify_payload(ov30n["view"]["text"], oracle=True)
        pc30_ref = bool(cg["ok"] and cg.get("oracle", {}).get("match") is True
                        and cg["semantic_artifact_id"] == golden["world_semantic_id"])
        pc30_nat = bool(cg.get("native") is True and cg.get("parity") is True)
        rep(pc30_ref, pc30_nat, "PC30-native) the REOPENED Golden-derived project "
            "source (after a persisted layout edit + fresh-cache reopen) still "
            "folds ic_ref == ic32 == Fixture to the Golden identity")

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
    print("  [note] v0.7-3.1 is the Template Reopen Closure: the manifest "
          "canvas_layout is now applied identically by Explore + Use (PC25/PC26) "
          "as presentation metadata that moves no identity (PC30); a project owns "
          "its scenario documents, so a reopen -- including after a real restart "
          "(PC28) and with the catalog + provenance sidecar removed (PC29) -- "
          "restores the project's OWN scenarios + bound default and folds them "
          "(PC27/PC28), never the global golden/bench presets. NO new semantic "
          "profile, IR version, identity, actor role, edge type, graph "
          "transaction, or runtime law.")
    return 0 if allok else 1


if __name__ == "__main__":
    sys.exit(main())
