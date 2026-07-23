#!/usr/bin/env python3
"""build_templates.py -- (re)generate the immutable Template Catalog (v0.7-3).

Emits the release-owned `templates/` directory: `catalog.json` (an ordered index)
plus one `TemplateManifestV1` JSON per shipped template. Every identity in each
manifest (world_semantic_id, per-scenario ScenarioDigest, ReplayBundleID) is
DERIVED from the sealed world source + scenario documents via
`wrl_templates.build_template_manifest`, then the manifest is re-verified before
it is written -- so a generated catalog can never disagree with its content.

The three templates:
  1. Golden ADMIT Demo     -- the frozen 6-node demo world + golden 7-epoch run.
  2. ADMIT Acceptance Bench -- the SAME world, defaulting to the 9-epoch bench.
  3. Blank Spinner World    -- the empirically smallest valid Spinner->Orb world.

Output is deterministic (sorted keys, 2-space indent, trailing newline) so two
runs produce byte-identical files and the release MANIFEST.sha256 is stable.

Usage:
    python3 tools/build_templates.py [--out DIR]   (default forge/templates)
"""
import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
FORGE = os.path.dirname(HERE)
sys.path.insert(0, FORGE)

import wrl_ir as W          # noqa: E402
import wrl_sugar as SG      # noqa: E402
import wrl_scenario as SC   # noqa: E402
import wrl_converge as CG   # noqa: E402
import wrl_templates as TP  # noqa: E402

# ---- the frozen world sources (kept in lock-step with spinner_bench.py) ----
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

# the empirically smallest world accepted by forge.world.core.v1: exactly one
# Spinner, one Orb, one legal SocketControl connection. The Spinner's frozen port
# signature is ['sig_in', 'socket'], so both ports must be declared even without a
# driving pulser; there is no authored claim and no initial numeric fault.
BLANK_WORLD_SOURCE = """profile forge.world.core.v1

[spinner:sp](w=16, n=8, rotor=quarter_turn_z, configurable){sig_in, socket}
[orb:ob]{pose}

[spinner:sp] --socket--> [orb:ob]
"""


def _layout_for(source):
    """The deterministic default CanvasLayoutV1 the session builds for a world."""
    prog = W.lower_program(SG.desugar_core(source), W.parse_wrl_core)
    return CG.new_session(prog, "template").layout


def _blank_scenario(world_semantic_id):
    """One idle epoch, no faults, no claims -- the minimal valid ScenarioV1."""
    return {
        "scenario_version": SC.SCENARIO_VERSION,
        "world_semantic_id": world_semantic_id,
        "initial_runtime": {"numeric_faults": []},
        "epochs": [{"epoch": 1, "label": "idle", "claims": []}],
    }


def _demo_world_id():
    prog = W.lower_program(SG.desugar_core(DEMO_WORLD_SOURCE), W.parse_wrl_core)
    return prog.semantic_artifact_id


def _blank_world_id():
    prog = W.lower_program(SG.desugar_core(BLANK_WORLD_SOURCE), W.parse_wrl_core)
    return prog.semantic_artifact_id


def _templates():
    demo_id = _demo_world_id()
    blank_id = _blank_world_id()
    golden = SC.demo_scenario(demo_id)
    bench = SC.bench_scenario(demo_id)
    blank = _blank_scenario(blank_id)

    golden_admit = TP.build_template_manifest(
        template_id=TP.GOLDEN_ADMIT_ID,
        name="Golden ADMIT Demo",
        short_description="The canonical 6-node ADMIT world with its 7-epoch "
                          "golden run.",
        purpose="Learn the ADMIT pipeline end to end: a pulser-driven spinner "
                "sets an orb's fault latch, and the golden scenario walks accept, "
                "reset, and an unknown-object rejection.",
        difficulty="intro",
        world_source=DEMO_WORLD_SOURCE,
        layout=_layout_for(DEMO_WORLD_SOURCE),
        named_scenarios=[("golden", golden), ("bench", bench)],
        default_scenario_document_id="golden",
        suggested_first_edit="Change the Spinner's rotor (e.g. from "
                             "quarter_turn_z to 256.0.0.0).",
        expected_edit_effect="The candidate SemanticArtifactID moves while the "
                             "active world stays fixed until you commit.",
        guide_steps=[
            "Press Run to fold the golden 7-epoch scenario and watch the film.",
            "Open the WRL editor and read the six-node world source.",
            "Change the Spinner rotor and Apply to see a new candidate identity.",
            "Commit to make the edited world active, then Run again.",
        ],
    )

    acceptance_bench = TP.build_template_manifest(
        template_id=TP.ACCEPTANCE_BENCH_ID,
        name="ADMIT Acceptance Bench",
        short_description="The SAME frozen world as the Golden Demo, defaulting "
                          "to the complete 9-epoch acceptance scenario.",
        purpose="Exercise the full ADMIT acceptance suite on the demo world: "
                "accept, exact retransmit, equivocation/disputed, saturating "
                "fault latch, safe reset, reset+relatch, and idle replay.",
        difficulty="core",
        world_source=DEMO_WORLD_SOURCE,
        layout=_layout_for(DEMO_WORLD_SOURCE),
        named_scenarios=[("golden", golden), ("bench", bench)],
        default_scenario_document_id="bench",
        suggested_first_edit="Compare the golden and bench scenario identities in "
                             "the scenario panel.",
        expected_edit_effect="Same world identity, different ScenarioDigest and "
                             "ReplayBundleID -- a scenario edit never moves the "
                             "world's SemanticArtifactID.",
        guide_steps=[
            "Press Run to fold the 9-epoch bench and read the seven behaviors.",
            "Note the disputed receipt in epoch 3 and the fault latch in epoch 6.",
            "Switch to the golden scenario to confirm the world id is unchanged.",
            "Verify (native) to confirm ic_ref, ic32, and the oracle all agree.",
        ],
    )

    blank_spinner = TP.build_template_manifest(
        template_id=TP.BLANK_SPINNER_ID,
        name="Blank Spinner World",
        short_description="The smallest valid Spinner->Orb scaffold: one Spinner, "
                          "one Orb, one SocketControl connection.",
        purpose="Start from the minimal legal world and build up your own: no "
                "pulser, no authored claims, one idle epoch.",
        difficulty="intro",
        world_source=BLANK_WORLD_SOURCE,
        layout=_layout_for(BLANK_WORLD_SOURCE),
        named_scenarios=[("idle", blank)],
        default_scenario_document_id="idle",
        suggested_first_edit="Add a pulser and wire it to the Spinner's sig_in "
                             "port to drive it.",
        expected_edit_effect="Adding an object moves the candidate "
                             "SemanticArtifactID to a new world identity.",
        guide_steps=[
            "Run the idle scenario to confirm the blank world folds cleanly.",
            "Open the WRL editor: the world has exactly a Spinner and an Orb.",
            "Add a pulser (every 2) and wire it to the Spinner to drive it.",
            "Author a scenario in the scenario panel, then Run it.",
        ],
    )
    return [golden_admit, acceptance_bench, blank_spinner]


def _write_json(path, obj):
    with open(path, "w") as f:
        json.dump(obj, f, sort_keys=True, indent=2)
        f.write("\n")


_FILES = {
    TP.GOLDEN_ADMIT_ID: "golden-admit-v1.json",
    TP.ACCEPTANCE_BENCH_ID: "acceptance-bench-v1.json",
    TP.BLANK_SPINNER_ID: "blank-spinner-v1.json",
}


def build(out_dir):
    os.makedirs(out_dir, exist_ok=True)
    manifests = _templates()
    index = {"catalog_version": TP.CATALOG_VERSION, "templates": []}
    for m in manifests:
        fname = _FILES[m["template_id"]]
        _write_json(os.path.join(out_dir, fname), m)
        index["templates"].append({"template_id": m["template_id"],
                                   "file": fname})
    _write_json(os.path.join(out_dir, "catalog.json"), index)
    # verify the freshly-written catalog loads + re-derives cleanly.
    cat = TP.TemplateCatalog.load_dir(out_dir)
    print("BUILT %d templates in %s" % (cat.count, out_dir))
    for tid in cat.ids():
        m = cat.get(tid)
        print("  %-38s world=%s" % (tid, m["world_semantic_id"]))
    return 0


def main():
    ap = argparse.ArgumentParser(description="Regenerate the template catalog.")
    ap.add_argument("--out", default=os.path.join(FORGE, "templates"),
                    help="output directory (default forge/templates)")
    args = ap.parse_args()
    return build(args.out)


if __name__ == "__main__":
    sys.exit(main())
