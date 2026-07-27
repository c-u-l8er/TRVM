"""probe5 -- C.4.4: verified local admission into the V1 executor.

The ruling separates three capabilities. A transport may relay a projection.
An ingress verifier may establish it. Only the executor runs -- and what it
runs is the artifact THIS side derived, never one that arrived.

So this probe starts where probe3 stopped: it takes the admission, hands the
`execution_artifact` to Forge's ordinary production compile path, and asks the
executor's own sealer what that artifact's id is. Nothing here is special-cased
for the wire; `SealedArtifact` and `compile_artifact` are the same functions
every other Forge caller uses.

The result worth reading is the last one. `named-relations` is a V2 record --
a world Forge's frozen V1 reader REFUSES, and correctly. Admitted through the
adapter it compiles to the same backend term, byte for byte, as the pinned V1
demo world. Two encodings, one world, one execution.

A SEPARATION THIS PROBE MADE VISIBLE, and which I did not expect to find here.
Identity is exact at every magnitude and costs nothing: the 2^63-1 rotor world
seals, projects and verifies instantly (probe3, probe4). EXECUTION of that same
world is a different question. A lane of 2^63-1 is only representable at w=64,
and the backend term is quadratic in w with a large constant -- measured on
this machine, holding everything else fixed:

    w= 8    0.2s     2,108,528 chars
    w=16    1.6s     9,095,226 chars
    w=24    5.7s    20,890,304 chars
    w=32   17.3s    39,122,450 chars
    w=40   47.6s    61,842,093 chars

which puts w=64 near 1.6e8 characters of term. That is a cost cliff, not a
hang, and it is not a defect in anything C.4 built -- but it does mean the
artifact domain admits worlds that are cheaply VERIFIABLE and impractically
EXECUTABLE, and those are not the same property. The BigInt vectors are
identity vectors; they are carried through the admission step below like every
other, and stop before the compiler on purpose, with the reason named rather
than skipped silently.

Run from a COPY of forge/:  PYTHONDONTWRITEBYTECODE=1 python3 probe5.py
"""
import json
import os
import sys

sys.dont_write_bytecode = True

import wrl_canonical as WC
import wrl_plan
import wrl_projection as P

HERE = os.path.dirname(os.path.abspath(__file__))

DEMO_SEM = ("sem-8ae91fe9cbc5fd086ce4356d587c403211e5c7b2b3ebdd3164963674"
            "29ecfe4a")

LP = {"counter_encoding": "one_hot", "onehot_max": 32, "numeric_backend": "ic",
      "compiler_hash": "a" * 64, "target": "ic32",
      "lowering_profile_version": "1.0"}

# Run inputs are NOT world state (v0.5-0) and so are NOT on this wire. The
# executor supplies its own; that is the point of the split, and this list is
# here so that a future field named like one of these is caught.
RUN_INPUT_KEYS = ("periods", "batches", "epoch_inputs", "run_plan",
                  "initial_claim_state", "epoch0", "claim_batch")

# Above this spinner width the backend term is large enough that compiling it
# measures the machine rather than the protocol. See the module docstring: this
# is a stated budget, not a hidden skip.
COMPILE_WIDTH_BUDGET = 32

passed = 0
failed = 0


def ok(name, cond, detail=""):
    global passed, failed
    if cond:
        passed += 1
        print("  ok   %-44s %s" % (name, detail))
    else:
        failed += 1
        print("  FAIL %-44s %s" % (name, detail))


def main():
    doc = json.load(open(os.path.join(HERE, "_vectors.json")))
    built = {}
    views = {}

    for vec in doc["vectors"]:
        name = vec["name"]
        print("[%s]" % name)
        adm = P.verify_runtime_projection(vec["wire"])

        # The wire carries a world, not a run.
        stray = [k for k in RUN_INPUT_KEYS if k in adm.semantic_artifact]
        ok("%s/carries-no-run-inputs" % name, not stray, ",".join(stray))

        # THE ADMISSION STEP. The executor seals what it was handed, with its
        # own sealer, and that seal is what the view id has to equal. If the
        # verifier had merely copied the sender's number, this is where it
        # would come apart.
        try:
            sealed = WC.SealedArtifact(adm.execution_artifact)
        except Exception as e:  # noqa
            ok("%s/seals-locally" % name, False,
               "%s: %s" % (type(e).__name__, e))
            print("")
            continue
        ok("%s/seals-locally" % name, True, sealed.semantic_id[:24] + "...")
        views[name] = adm.execution_view_id
        ok("%s/seal-is-the-view-id" % name,
           sealed.semantic_id == adm.execution_view_id,
           "" if sealed.semantic_id == adm.execution_view_id
           else "%s != %s" % (sealed.semantic_id, adm.execution_view_id))

        width = max([o.get("static_config", {}).get("w", 0)
                     for o in adm.execution_artifact["objects"]] or [0])
        if width > COMPILE_WIDTH_BUDGET:
            print("       -- not compiled: spinner w=%d exceeds the stated "
                  "budget of %d." % (width, COMPILE_WIDTH_BUDGET))
            print("          This world's IDENTITY is fully established above; "
                  "only its\n          backend term is out of budget. See the "
                  "module docstring.\n")
            continue

        # The ordinary production compile path -- no wire-specific entry.
        try:
            prog = wrl_plan.compile_artifact(sealed, LP)
        except Exception as e:  # noqa
            ok("%s/compiles" % name, False, "%s: %s" % (type(e).__name__, e))
            print("")
            continue
        ok("%s/compiles" % name, True,
           "bcnt %s..." % prog.backend_content_hash[:20])

        built[name] = (sealed.semantic_id, prog.backend_content_hash,
                       prog.backend_layout_signature)
        print("")

    print("cross-encoding agreement\n")

    # THE HEADLINE. A V2 record -- bytes the frozen V1 reader refuses outright
    # -- compiles, through the ordinary path, to the same backend term as the
    # V1 world it is an encoding of.
    for v1, v2 in (("pinned-fixture", "named-relations"),):
        if v1 not in built or v2 not in built:
            ok("%s/executes-as-%s" % (v2, v1), False, "a leg did not build")
            continue
        a, b = built[v1], built[v2]
        ok("%s/executes-as-%s" % (v2, v1), a == b,
           "same view id, same backend term" if a == b
           else "%s vs %s" % (a, b))

    # The out-of-budget pair agrees on the thing that WAS established: the
    # execution view id. Stating the weaker claim is the honest move -- the
    # backend terms were never built, so nothing here may speak about them.
    a = views.get("bigint-rotor")
    b = views.get("bigint-rotor-named")
    ok("bigint-rotor-named/projects-to-the-same-view", a is not None and a == b,
       "%s (identity only; neither was compiled)" % a)

    if "pinned-fixture" in built:
        ok("the-pinned-world-is-unmoved", built["pinned-fixture"][0] == DEMO_SEM,
           built["pinned-fixture"][0])

    print("\n%d passed, %d failed" % (passed, failed))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
