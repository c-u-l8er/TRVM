#!/usr/bin/env python3
"""
TRVM conformance runner (the §6 oracle, portable edition).

Validates the language-agnostic vectors in spec/conformance/vectors/normalize.json
against every available implementation, then runs the behavioral conformance
batteries the SPEC §6 enumerates. Exits nonzero on any failure so `make test` / CI
catches regressions.

Coverage map (SPEC §6):
  §6.1 Confluence (N random reduction orders -> identical NF + interaction count)  [inet.py]
  §6.2 Distributed == sequential                                                   [dist_ic.py]
  §6.3 Exactly-once boundary                                                        [dist_ic.py / inet.py]
  §6.4 Snapshot round-trip                                                          NOT YET COVERED (gap)
  §6.5 REF unfolding                                                                NOT YET COVERED (gap)

The normalize.json vectors additionally pin cross-runtime normal-form agreement
(python reference ic_float, oracle ic_ref, native ic32, wasm ic32) — the practical
audit any new implementation (Zig/Rust/Go/...) runs first.

Run:  python3 runtime/python/conformance.py        (from repo root)
   or  make test
"""
import json, os, subprocess, sys, shutil

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))          # runtime/python -> repo root
sys.path.insert(0, HERE)                                # ic_ref / ic_float / inet
sys.path.insert(0, os.path.join(REPO, "distribution"))

import ic_ref, ic_float                                 # noqa: E402

VECTORS = os.path.join(REPO, "spec", "conformance", "vectors", "normalize.json")
IC32    = os.path.join(REPO, "runtime", "c", "ic32")
WRUN    = os.path.join(REPO, "runtime", "wasm", "wrun.js")
WASM    = os.path.join(REPO, "runtime", "wasm", "ic32.wasm")

GREEN, RED, DIM, RST = "\033[32m", "\033[31m", "\033[2m", "\033[0m"
def ok(m):   print(f"  {GREEN}PASS{RST} {m}")
def bad(m):  print(f"  {RED}FAIL{RST} {m}")
def note(m): print(f"  {DIM}····{RST} {m}")

failures = 0
def fail(m):
    global failures
    failures += 1
    bad(m)


def c_nf(term):
    r = subprocess.run([IC32], input=term, capture_output=True, text=True)
    if r.returncode != 0:
        return f"<ic32 exit {r.returncode}: {r.stderr.strip()}>"
    return r.stdout.strip()

def wasm_nf(term):
    r = subprocess.run(["node", WRUN], input=term, capture_output=True, text=True)
    if r.returncode != 0:
        return f"<wrun exit {r.returncode}: {r.stderr.strip()}>"
    return r.stdout.strip()


def run_vectors():
    print("\n[vectors] cross-runtime normal-form agreement")
    with open(VECTORS) as f:
        data = json.load(f)
    vecs = data["vectors"]

    have_c    = os.path.exists(IC32)
    have_node = shutil.which("node") is not None and os.path.exists(WASM)
    if not have_c:
        note(f"native ic32 not built ({IC32}) — skipping C check (run: make -C runtime/c)")
    if not have_node:
        note("node or ic32.wasm unavailable — skipping wasm check")

    for v in vecs:
        term, nf = v["term"], v["nf"]
        # python reference (ic_float): NF + interaction count are pinned
        f_nf, f_inter, _ = ic_float.run(term)
        tag = v["name"]
        if f_nf != nf:
            fail(f"{tag}: ic_float NF {f_nf!r} != expected {nf!r}"); continue
        if f_inter != v["ref_interactions"]:
            fail(f"{tag}: ic_float interactions {f_inter} != recorded {v['ref_interactions']}"); continue
        # oracle agreement (ic_ref) where it terminates
        if v.get("ic_ref_agrees"):
            r_nf, _, _ = ic_ref.run(term)
            if r_nf != nf:
                fail(f"{tag}: ic_ref NF {r_nf!r} != expected {nf!r}"); continue
        # native + wasm cross-runtime NF
        if have_c:
            cn = c_nf(term)
            if cn != nf:
                fail(f"{tag}: ic32(C) NF {cn!r} != expected {nf!r}"); continue
        if have_node:
            wn = wasm_nf(term)
            if wn != nf:
                fail(f"{tag}: ic32.wasm NF {wn!r} != expected {nf!r}"); continue
        ok(f"{tag}: {nf}")
    runtimes = "ic_float" + (", ic_ref" if any(v.get("ic_ref_agrees") for v in vecs) else "") \
               + (", ic32(C)" if have_c else "") + (", ic32.wasm" if have_node else "")
    note(f"{len(vecs)} vectors checked across: {runtimes}")


def run_confluence():
    print("\n[§6.1] confluence — 300 random reduction orders (interaction combinators)")
    import inet
    D = 3
    n_int, rb = inet.test_confluence(lambda: inet.make_demo_net(D), trials=300)
    # cross-check fixed policies also agree
    agree = True
    for pol in ("first", "last"):
        net = inet.make_demo_net(D)
        inet.reduce_net(net, pol)
        if inet.readback(net) != rb:
            agree = False
    if agree:
        ok(f"300 random orders + first/last policies -> identical NF; {n_int} interactions each (order-invariant)")
    else:
        fail("reduction order changed the normal form (confluence violated)")


def _run_battery(script, success_markers, failure_markers):
    path = os.path.join(REPO, script)
    r = subprocess.run([sys.executable, path], capture_output=True, text=True,
                       cwd=REPO, env={**os.environ,
                       "PYTHONPATH": os.pathsep.join([HERE, os.path.join(REPO, "distribution"),
                                                      os.path.join(REPO, "research")])})
    out = r.stdout + r.stderr
    bad_hit = [m for m in failure_markers if m in out]
    good_hit = [m for m in success_markers if m in out]
    return r.returncode, out, good_hit, bad_hit


def run_distributed():
    print("\n[§6.2/§6.3] distributed == sequential + exactly-once boundary")
    rc, out, good, bad_hit = _run_battery(
        "distribution/dist_ic.py",
        success_markers=["ALL MATCH", "schedule/partition-independent"],
        failure_markers=["mismatch", "DISCREPANC", "PARTITION-DEPENDENT", "FAIL"])
    if rc == 0 and len(good) == 2 and not bad_hit:
        ok("dist_ic.py: single-node == ic_float oracle; all distributed configs partition/schedule-independent")
    else:
        fail(f"dist_ic.py battery (rc={rc}, matched={good}, problems={bad_hit})")
        print(DIM + out[-800:] + RST)

    rc, out, good, bad_hit = _run_battery(
        "runtime/python/inet.py",
        success_markers=["exactly-once", "no run needed a lock"],
        failure_markers=["FAIL", "DISCREP"])
    if rc == 0 and good:
        ok("inet.py: boundary exports == boundary rewrites every run (exactly-once)")
    else:
        fail(f"inet.py boundary battery (rc={rc}, matched={good}, problems={bad_hit})")


def report_gaps():
    print("\n[§6.4/§6.5] standing conformance gaps (honestly uncovered)")
    note("§6.4 snapshot round-trip — no snapshot()/restore() in the reference yet (see FINDINGS.md limits)")
    note("§6.5 REF unfolding — recursive supercombinator REFs not exercised by the current battery")


def main():
    print(f"TRVM conformance runner  (repo: {REPO})")
    run_vectors()
    run_confluence()
    run_distributed()
    report_gaps()
    print()
    if failures:
        print(f"{RED}CONFORMANCE FAILED: {failures} failure(s){RST}")
        sys.exit(1)
    print(f"{GREEN}CONFORMANCE OK{RST}  (vectors + §6.1–§6.3; §6.4–§6.5 are documented gaps)")


if __name__ == "__main__":
    main()
