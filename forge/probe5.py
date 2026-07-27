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
    w=64  482.3s   154,713,682 chars     (peak RSS 2.5 GB)

The w=64 row is MEASURED, and the distinction was worth the eight minutes it
cost. The first version of this note stopped at w=40 and called w=64 "a cost
cliff, not a hang" on the strength of the fit -- but the run it described had
been killed at five minutes without ever returning, so "not a hang" was an
inference wearing the clothes of an observation. In a file whose whole subject
is that a plausible derived number is the thing to distrust, that was the wrong
sentence to leave standing. Run to completion it does terminate, and the fit
was good: predicted ~1.6e8, actual 1.547e8.

So it is a cost cliff, and not a defect in anything C.4 built -- but it does
mean the artifact domain admits worlds that are cheaply VERIFIABLE and
expensively EXECUTABLE, and those are not the same property.

And the cliff is worth paying once, because the headline claim is stronger on
the far side of it. Both w=64 legs were built:

    bigint-rotor        (V1)  482.3s
    bigint-rotor-named  (V2)  573.2s

    sem-4f927defd2e60b03f3511670b0aead801c09e67facaf283a3bb9cf3857bd65d2
    bcnt-3f3aa11da1a0c6ff4c92133a1b7fa59fb4956ed4008ac8549ae37d5ffa6feff2

-- the same seal and the same backend term from both encodings, at a magnitude
where the wire's own exact-integer reader is the only reason the number
survived the trip at all. That is C.4.1 and C.4.3 checked against each other:
had `parseExactJson` rounded the lane, this term would differ and nothing else
in the probe would have noticed.

The default run stops before the compiler on those two vectors to stay fast;
`--full` lifts the budget and takes about eighteen minutes. The budget is
stated, the skip is printed with its reason, and the recorded answer above is
asserted on a `--full` run rather than merely quoted -- a number that is only
ever reported is a number nothing can falsify.

Run from a COPY of forge/:  PYTHONDONTWRITEBYTECODE=1 python3 probe5.py
                            PYTHONDONTWRITEBYTECODE=1 python3 probe5.py --full
"""
import json
import os
import sys

sys.dont_write_bytecode = True

import vector_files
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
# is a stated budget, not a hidden skip. `--full` lifts it, which costs about
# eighteen minutes and roughly 2.5 GB of resident memory for the two w=64 legs.
COMPILE_WIDTH_BUDGET = 10 ** 9 if "--full" in sys.argv else 32

# The w=64 pair, measured out of band under the lifted budget (see the module
# docstring for the timings). These are recorded so that the expensive run has
# something to be checked AGAINST rather than merely reported, and so that a
# reader who does not want to spend the eighteen minutes can still see what the
# claim is. They are asserted only on a run that actually built the term.
BIGINT_SEM = ("sem-4f927defd2e60b03f3511670b0aead801c09e67facaf283a3bb9cf3857"
              "bd65d2")
BIGINT_BCNT = ("bcnt-3f3aa11da1a0c6ff4c92133a1b7fa59fb4956ed4008ac8549ae37d5f"
               "fa6feff2")

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
    doc = vector_files.load("_vectors.json")
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
                  "only its\n          backend term is out of budget. Re-run "
                  "with --full to build it.\n")
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
    for v1, v2 in (("pinned-fixture", "named-relations"),
                   ("bigint-rotor", "bigint-rotor-named")):
        # The execution view id is established for every vector, in budget or
        # out of it, because deriving it costs nothing. Assert that much first
        # and unconditionally.
        a, b = views.get(v1), views.get(v2)
        ok("%s/projects-to-the-same-view" % v2, a is not None and a == b,
           a if a == b else "%s vs %s" % (a, b))

        # The backend claim is a strictly stronger one and may only be made on
        # a run that actually built the term. Out of budget, say so and say
        # what the recorded answer is -- reporting a measurement is not the
        # same act as passing a check, and this prints rather than scores.
        if v1 not in built or v2 not in built:
            print("       -- %s/executes-as-%s not checked: out of budget."
                  % (v2, v1))
            print("          Recorded under --full: %s" % BIGINT_BCNT)
            continue
        a, b = built[v1], built[v2]
        ok("%s/executes-as-%s" % (v2, v1), a == b,
           "same view id, same backend term" if a == b
           else "%s vs %s" % (a, b))

    # The pinned w=64 answer, checked only when the term was really built.
    if "bigint-rotor" in built:
        sem, bcnt, _ = built["bigint-rotor"]
        ok("bigint-rotor/matches-the-recorded-term",
           (sem, bcnt) == (BIGINT_SEM, BIGINT_BCNT),
           bcnt if (sem, bcnt) == (BIGINT_SEM, BIGINT_BCNT)
           else "%s / %s" % (sem, bcnt))

    if "pinned-fixture" in built:
        ok("the-pinned-world-is-unmoved", built["pinned-fixture"][0] == DEMO_SEM,
           built["pinned-fixture"][0])

    print("\n%d passed, %d failed" % (passed, failed))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
