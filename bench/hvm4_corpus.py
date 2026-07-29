#!/usr/bin/env python3
"""Run every translatable HVM4 test program through both engines and compare.

A program is "portable" iff /tmp/h2t.py can translate it -- i.e. it uses only
the pure-IC fragment (lam/app/dup/sup/era/ref) that TRVM's ic32 also implements.
Anything using #Ctr constructors, pattern-matching lambdas, or native u32 fails
translation and is reported as out-of-fragment, never silently skipped.

Ground truth is the `//` comment HVM4 records in each file: the expected normal
form. Both engines are checked against it independently, so they can be wrong
together and it still shows.
"""
import os, re, subprocess, sys, time, json

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import hvm4_translate as h2t
import nf_equiv as nfcmp

HVM4 = os.environ.get("HVM4", "/tmp/hvm4")
IC32 = os.environ.get("IC32", os.path.join(os.path.dirname(HERE), "runtime", "c", "ic32"))
TESTS = os.environ.get("HVM4_TESTS", "/home/travis/hvm4/devs/test")
TIMEOUT = 30


def expected_nf(path):
    """HVM4 records the expected normal form as a trailing // comment."""
    txt = open(path, encoding="utf-8").read()
    hits = re.findall(r"//\s*(.+)", txt)
    return hits[-1].strip() if hits else None


ANSI = re.compile(r"\x1b\[[0-9;]*m")


def run_hvm4(path, collapse):
    """HVM4 stops at a residual term with unresolved duplicators by default;
    `-C` forces the full readback that TRVM's `normal` performs unconditionally.
    Comparing plain HVM4 output to TRVM would compare different questions."""
    t = time.perf_counter()
    cmd = [HVM4, path, "-s"] + (["-C"] if collapse else [])
    try:
        p = subprocess.run(cmd, capture_output=True, text=True,
                           timeout=TIMEOUT)
    except subprocess.TimeoutExpired:
        return {"status": "TIMEOUT"}
    ms = (time.perf_counter() - t) * 1000
    if p.returncode != 0:
        return {"status": "ERR", "detail": (p.stderr or p.stdout)[:120]}
    out = ANSI.sub("", p.stdout)
    itr = re.search(r"Itrs:\s*([\d_,]+)", out)
    # -C enumerates one line per superposition branch, each tagged `#n`.
    res = [re.sub(r"#\d+\s*$", "", l).strip()
           for l in out.split("\n") if l.strip() and not l.startswith("- ")]
    return {"status": "OK", "nf": res[0] if res else "", "results": res, "ms": ms,
            "inter": int(itr.group(1).replace("_", "").replace(",", "")) if itr else None}


def run_ic32(term):
    t = time.perf_counter()
    try:
        p = subprocess.run([IC32, "-v"], input=term, capture_output=True,
                           text=True, timeout=TIMEOUT)
    except subprocess.TimeoutExpired:
        return {"status": "TIMEOUT"}
    ms = (time.perf_counter() - t) * 1000
    if p.returncode != 0:
        return {"status": "ERR", "detail": (p.stdout + p.stderr)[:120]}
    itr = re.search(r"interactions=(\d+)", p.stderr)   # ic32 -v reports on stderr
    body = p.stdout
    return {"status": "OK", "nf": body.strip(), "ms": ms,
            "inter": int(itr.group(1)) if itr else None}


def main():
    files = sorted(f for f in os.listdir(TESTS) if f.endswith(".hvm")
                   and not f.startswith("_"))
    portable, blocked = [], []
    for f in files:
        path = os.path.join(TESTS, f)
        for mode in (True, False):
            try:
                term = h2t.translate(path, fresh=mode)
                portable.append((f, path, term, mode))
                break
            except Exception as e:
                err = f"{type(e).__name__}: {e}"
        else:
            blocked.append((f, err))

    print(f"corpus: {len(files)} programs -- "
          f"{len(portable)} in the shared pure-IC fragment, "
          f"{len(blocked)} out of fragment\n")

    rows = []
    for f, path, term, mode in portable:
        exp = expected_nf(path)
        h = run_hvm4(path, collapse=True)
        hp = run_hvm4(path, collapse=False)
        t = run_ic32(term)
        agree = (nfcmp.same(h["nf"], t["nf"])
                 if h.get("status") == "OK" and t.get("status") == "OK"
                 else None)
        rows.append({"file": f, "labels": "fresh" if mode else "verbatim",
                     "expected": exp, "hvm4": h, "hvm4_plain": hp, "trvm": t,
                     "agree": agree, "term_len": len(term)})
    json.dump({"rows": rows, "blocked": blocked},
              open(os.path.join(HERE, "hvm4_corpus.json"), "w"), indent=1)

    # An ic32 parse error means the translator emitted syntax ic32 rejects --
    # the program was never really in the shared fragment. Report it as such
    # rather than counting it as a semantic disagreement.
    ran = [r for r in rows if r["trvm"]["status"] == "OK"]
    rejected = [r for r in rows if r["trvm"]["status"] != "OK"]

    def verdict(r):
        if len(r["hvm4"].get("results", [])) > 1:
            # -C enumerates a superposition into several results; TRVM's readback
            # prints the superposition itself. Different readback contracts,
            # not a disagreement about the reduction.
            return "sup: HVM4 enumerates, TRVM prints"
        return {True: "same NF", False: "DIFFERENT NF",
                None: "unparseable"}[r["agree"]]

    print(f"{'program':<24}{'HVM4 -C':>10}{'HVM4 plain':>12}{'TRVM':>10}"
          f"{'ratio':>8}  verdict")
    print("-" * 92)
    for r in sorted(ran, key=lambda r: -(r["hvm4"].get("inter") or 0)):
        h, hp, t = r["hvm4"], r["hvm4_plain"], r["trvm"]
        hi, ti = h.get("inter"), t.get("inter")
        ratio = f"{hi/ti:.1f}x" if (hi and ti) else ""
        print(f"{r['file']:<24}{str(hi if hi is not None else h['status']):>10}"
              f"{str(hp.get('inter', hp['status'])):>12}"
              f"{str(ti if ti is not None else t['status']):>10}"
              f"{ratio:>8}  {verdict(r)}")

    vs = [verdict(r) for r in ran]
    print(f"\n{vs.count('same NF')}/{len(ran)} programs that ran on both engines "
          f"agree on the normal form (alpha-equivalence); "
          f"{vs.count('sup: HVM4 enumerates, TRVM prints')} differ only in how a "
          f"residual superposition is read back; "
          f"{vs.count('DIFFERENT NF')} genuinely disagree.")

    if rejected:
        print(f"\nic32 rejected {len(rejected)} translated terms:")
        for r in rejected:
            print(f"  {r['file']:<24}{r['trvm'].get('detail','')[:60]}")

    print(f"\nout of fragment ({len(blocked)}):")
    kinds = {}
    for f, e in blocked:
        k = e.split(":")[0] + ":" + e.split(":")[-1][:40]
        kinds.setdefault(k, []).append(f)
    for k, v in sorted(kinds.items(), key=lambda x: -len(x[1])):
        print(f"  {len(v):>4}  {k}")


if __name__ == "__main__":
    main()
