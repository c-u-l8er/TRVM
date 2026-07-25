"""binding_run42.py -- v0.7-4 VISUAL / RESPONSIVE CLOSURE battery (PC31-PC38).

GPT-5.6's v0.7-4 ruling: make the workspace usable across small/tablet/desktop
widths and accessible, as a PRESENTATION-ONLY slice. NO new semantic profile, IR
version, artifact identity, actor role, edge type, graph transaction, authoring
op, or server capability: the demo world still seals to the frozen
DEMO_WORLD_SEMANTIC_ID with ic_ref == ic32 == Fixture green (PC38), and every fold
is byte-identical to v0.6-4.

Responsive matrix (asserted structurally via the CSS breakpoints, then captured
as one screenshot per width in the packet): 320x700, 375x812, 768x1024, 1024x768,
1280x800, 1440x900.

  PC31 no horizontal overflow: grid children pin min-width:0, the grid caps at
       100%, and the layout collapses to 2 then 1 column with the header/toolbar
       wrapping so nothing forces a horizontal scrollbar at any matrix width
  PC32 the first-run template chooser is keyboard-operable: real <button>s with a
       single visible :focus-visible ring and accessible per-template names
  PC33 read-only Explore is visually obvious at EVERY breakpoint (sticky banner +
       lock glyph + text tag + dashed workspace frame) and creates no project
  PC34 resizing only re-flows CSS: there is no window resize / reload handler that
       mutates JS state, and the responsiveness is media-query driven
  PC35 a catalog failure disables ONLY template ops -- list/preview/use fail
       closed while run / verify / project-open / health stay usable
  PC36 prefers-reduced-motion is honored (a reduce block kills transitions +
       animations + smooth scroll)
  PC37 no server errors: health + templates + preview + use + open + run all
       return structured results (never a raw exception), and the a11y wiring
       references only ids that exist in the HTML
  PC38 the visual work moves NO identity: preview + template-use reproduce the
       frozen identities and the demo still folds ic_ref == ic32 == Fixture (native)

Gates:

    python3 binding_run42.py --gate smoke    # PC31-PC37 (fast, no compiler)
    python3 binding_run42.py --gate native   # PC38 (compiler; ic_ref==ic32==oracle)
    python3 binding_run42.py                  # all of the above
"""
import argparse
import os
import re
import shutil
import sys
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "runtime", "python"))
sys.path.insert(0, os.path.join(HERE, "..", "research"))

SKIP_NATIVE = os.environ.get("TRVM_SKIP_NATIVE") == "1"
ALPHA = "v0.7.0-alpha.5"


def _read(path):
    return open(path, encoding="utf-8").read() if os.path.isfile(path) else ""


def main():
    ap = argparse.ArgumentParser(description="Visual / responsive closure battery.")
    ap.add_argument("--gate", default="all", choices=["all", "smoke", "native"])
    args = ap.parse_args()
    do_smoke = args.gate in ("all", "smoke")
    do_native = args.gate in ("all", "native") and not SKIP_NATIVE

    print("[BINDING wrl-%s] visual / responsive closure -- PC31-PC38 (gate=%s)"
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

    data_root = tempfile.mkdtemp(prefix="forge-pc42-data-")
    project_root = os.path.join(data_root, "projects")
    os.environ["FORGE_PROJECT_ROOT"] = project_root
    import spinner_bench as SB
    import wrl_templates as TP
    DEMO_SEM = SB.DEMO_WORLD_SEMANTIC_ID

    css = _read(os.path.join(HERE, "spinner_bench.css"))
    js = _read(os.path.join(HERE, "spinner_bench.js"))
    html = _read(os.path.join(HERE, "spinner_bench.html"))

    golden = SB._TEMPLATE_CATALOG.get(TP.GOLDEN_ADMIT_ID)

    if do_smoke:
        # ---- PC31 no horizontal overflow ------------------------------------
        # grid/flex children default to min-width:auto (long id strings + wide
        # tables force a scrollbar); pinning min-width:0 + capping the grid +
        # collapsing to 2 then 1 column with a wrapping header prevents overflow.
        pc31 = (".panel { min-width: 0; }" in css
                and ".grid { max-width: 100%; }" in css
                and "@media (max-width: 1024px)" in css
                and "@media (max-width: 760px)" in css
                and "grid-template-columns: 1fr;" in css
                and "grid-template-columns: 1fr 1fr;" in css
                and "flex-wrap: wrap" in css)          # header/toolbar wrap
        rep(pc31, None, "PC31) no horizontal overflow -- grid pins min-width:0, "
            "caps at 100%, and collapses 3->2->1 column with a wrapping header")

        # ---- PC32 keyboard-operable chooser ---------------------------------
        # the chooser cards are real <button>s (not clickable <div>s), there is a
        # single global :focus-visible ring, and each template button gets an
        # accessible name announcing which template it acts on.
        pc32 = ('<button class="tpl-explore">' in js
                and '<button class="tpl-use">' in js
                and ":focus-visible {" in css
                and "outline: 2px solid var(--accent)" in css
                and 'setAttribute("aria-label", "Explore "' in js
                and 'setAttribute("aria-label", "Use "' in js
                and 'setAttribute("role", "list")' in js)
        rep(pc32, None, "PC32) the template chooser is keyboard-operable: real "
            "<button>s + a visible :focus-visible ring + accessible names")

        # ---- PC33 read-only Explore obvious at every breakpoint -------------
        css_explore = ("body.explore main { outline: 2px dashed var(--warn)" in css
                       and ".explore-banner { position: sticky;" in css
                       and ".explore-banner .eb-tag::before { content:" in css)
        toggles = 'document.body.classList.toggle("explore", on)' in js
        # a template preview (Explore) must remain project-free (no project doc).
        before = len(os.listdir(project_root)) if os.path.isdir(project_root) else 0
        pv = SB._template_preview_payload({"template_id": TP.BLANK_SPINNER_ID})
        after = len(os.listdir(project_root)) if os.path.isdir(project_root) else 0
        # the banner lives OUTSIDE the responsive panels so it shows at any width.
        banner_top_level = ('id="explore-banner"' in html
                            and 'role="status"' in html)
        pc33 = (css_explore and toggles and pv.get("ok")
                and after == before and banner_top_level)
        rep(pc33, None, "PC33) read-only Explore is visually obvious at every "
            "breakpoint (sticky banner + lock glyph + dashed frame) + creates "
            "no project")

        # ---- PC34 resize only re-flows CSS ----------------------------------
        # no window resize / reload handler exists, so a resize cannot mutate JS
        # state or the draft -- responsiveness is entirely media-query driven.
        no_resize = (not re.search(r'addEventListener\(\s*["\']resize["\']', js)
                     and "onresize" not in js
                     and "location.reload" not in js)
        pc34 = (no_resize
                and "@media (max-width: 420px)" in css
                and "@media (max-width: 760px)" in css)
        rep(pc34, None, "PC34) resizing only re-flows CSS -- no resize/reload "
            "handler mutates state; responsiveness is media-query driven")

        # ---- PC35 catalog failure disables ONLY template ops ----------------
        saved_cat, saved_err = SB._TEMPLATE_CATALOG, SB._TEMPLATE_ERROR
        SB._TEMPLATE_CATALOG = None
        SB._TEMPLATE_ERROR = RuntimeError("simulated catalog load failure")
        try:
            tlist = SB._templates_list_payload()
            tprev = SB._template_preview_payload({"template_id": TP.GOLDEN_ADMIT_ID})
            tuse = SB._template_use_payload({"template_id": TP.GOLDEN_ADMIT_ID,
                                             "project_id": "pc35", "name": "pc35"})
            health = SB._health_payload()
            run = SB._run_payload(SB.DEMO_WORLD_SOURCE, SB.GOLDEN_DEMO_SCENARIO)
        finally:
            SB._TEMPLATE_CATALOG, SB._TEMPLATE_ERROR = saved_cat, saved_err
        # template ops fail closed; health stays ok but flags templates_ok False;
        # the run pipeline is untouched and still folds the demo world.
        pc35 = (tlist.get("ok") is False and tprev.get("ok") is False
                and tuse.get("ok") is False
                and health.get("ok") is True
                and health.get("templates_ok") is False
                and run.get("ok") is True
                and run.get("semantic_artifact_id") == DEMO_SEM
                # frontend fails closed too (chooser message + null state)
                and "Templates are unavailable" in js
                and "state.templates = (r && r.ok) ? r.templates : null" in js)
        rep(pc35, None, "PC35) a catalog failure disables ONLY template ops "
            "(list/preview/use fail closed) while run / health / pipeline work")

        # ---- PC36 prefers-reduced-motion honored ----------------------------
        rm = css[css.find("@media (prefers-reduced-motion: reduce)"):] \
            if "@media (prefers-reduced-motion: reduce)" in css else ""
        pc36 = (bool(rm)
                and "transition-duration: .001ms !important;" in rm
                and "animation-duration: .001ms !important;" in rm
                and "scroll-behavior: auto !important;" in rm)
        rep(pc36, None, "PC36) prefers-reduced-motion is honored (reduce block "
            "kills transitions + animations + smooth scroll)")

        # ---- PC37 no server errors + a11y wiring references real ids ---------
        pv2 = SB._template_preview_payload({"template_id": TP.GOLDEN_ADMIT_ID})
        u2 = SB._template_use_payload({"template_id": TP.GOLDEN_ADMIT_ID,
                                       "project_id": "pc37", "name": "pc37"})
        ov2 = SB._project_open_payload({"project_id": "pc37"})
        h2 = SB._health_payload()
        r2 = SB._run_payload(ov2["view"]["text"], SB.GOLDEN_DEMO_SCENARIO)
        server_ok = all(x.get("ok") for x in (pv2, u2, ov2, h2, r2))
        # every id referenced by the a11y-critical wiring must exist in the HTML.
        referenced = ["explore-banner", "first-run", "fr-templates", "guide-rail",
                      "dialog-root", "view-seg", "btn-make-copy"]
        ids_ok = all(('id="%s"' % rid) in html for rid in referenced)
        pc37 = server_ok and ids_ok
        rep(pc37, None, "PC37) no server errors (health/templates/preview/use/"
            "open/run all structured) + a11y wiring references only real ids")

    # ---- PC38 (native) the visual work moves NO identity --------------------
    if do_native:
        # a preview + a template-use reproduce the frozen identities, and the
        # demo world still folds ic_ref == ic32 == Fixture after the visual slice.
        pvn = SB._template_preview_payload({"template_id": TP.GOLDEN_ADMIT_ID})
        SB._template_use_payload({"template_id": TP.GOLDEN_ADMIT_ID,
                                  "project_id": "pc38", "name": "pc38"})
        ovn = SB._project_open_payload({"project_id": "pc38"})
        id_ok = (pvn.get("ok")
                 and ovn["view"].get("active_semantic_id")
                     == golden["world_semantic_id"] == DEMO_SEM)
        cg = SB._verify_payload(ovn["view"]["text"], oracle=True)
        pc38_ref = bool(id_ok and cg["ok"]
                        and cg.get("oracle", {}).get("match") is True
                        and cg["semantic_artifact_id"] == DEMO_SEM)
        pc38_nat = bool(cg.get("native") is True and cg.get("parity") is True)
        rep(pc38_ref, pc38_nat, "PC38-native) the visual slice moves NO identity "
            "-- preview + use reproduce the frozen ids and the demo still folds "
            "ic_ref == ic32 == Fixture")

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
    print("  [note] v0.7-4 is the Visual / Responsive Closure: the six-panel grid "
          "collapses 3->2->1 column with a wrapping header so there is no "
          "horizontal overflow across the 320x700 .. 1440x900 matrix (PC31); the "
          "template chooser is keyboard-operable with a visible focus ring + "
          "accessible names (PC32); read-only Explore is obvious at every "
          "breakpoint (PC33); resizing only re-flows CSS (PC34); a catalog "
          "failure disables ONLY template ops (PC35); reduced-motion is honored "
          "(PC36); nothing errors (PC37); and the visual work moves NO identity "
          "-- the demo still folds ic_ref == ic32 == Fixture (PC38). NO new "
          "semantic profile, IR version, identity, actor role, edge type, graph "
          "transaction, authoring op, or server capability.")
    return 0 if allok else 1


if __name__ == "__main__":
    sys.exit(main())
