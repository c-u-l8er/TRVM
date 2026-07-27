#!/usr/bin/env python3
"""Generate the two scaling families used for the HVM4 head-to-head, in HVM4
surface syntax so `hvm4_translate.py` can carry the same bytes to TRVM.

Both families compute the same thing -- the parity of 2^N, i.e. NOT applied
2^N times to TRUE -- but build the iteration count two different ways, and
that difference turns out to be the whole story:

  cnot_N   an N-level doubling chain, every level reusing the SAME label,
           exactly the shape of HVM4's own `devs/bench/cnot_24.hvm`.
           Costs ~2^N interactions on both engines: no sharing collapse.

  par_N    Church exponentiation -- `(A B)` computes `B^A`, so `(N 2)` is the
           numeral 2^N. Costs 20N-2 interactions on both engines: the
           optimal-sharing collapse, 16.7M negations in 478 interactions.

Comparing cnot_24 on one engine against par_24 on the other is what produced
the bogus "478 vs 234,881,124" gap. Run both families on both engines instead.
"""
import os, sys


def _label(i):
    """A, B, ... Z, AA, ... -- HVM4 labels are names, TRVM's are integers, and
    `hvm4_translate.py` maps between them."""
    s = ""
    i += 1
    while i:
        i, r = divmod(i - 1, 26)
        s = chr(65 + r) + s
    return s


def cnot_chain(n):
    """N-level doubling chain, single shared label, as HVM4's bench writes it."""
    return "\n".join(
        ["@ctru = λt.λf.t",
         "@cfal = λt.λf.f",
         "@cnot = λx.x(@cfal,@ctru)",
         "@P = λf.",
         "  ! F &A = f;"]
        + [f"  ! F &A = λk. F\u2080(F\u2081(k)); // 2^{i+1}" for i in range(n)]
        + ["  λk. F\u2080(F\u2081(k))",
           "@main = @P(@cnot,@ctru)"]) + "\n"


def _church(n, lab):
    """Church numeral n, explicitly linear: IC binders are used exactly once,
    so every reuse of `f` goes through a duplicator with a fresh label."""
    if n == 0:
        return "(λf.λx.x)"
    if n == 1:
        return "(λf.λx.f(x))"
    src, cur, heads = [], "f", []
    for _ in range(n - 1):
        L = _label(next(lab))
        v = "D" + L
        src.append(f"!{v}&{L}={cur};")
        heads.append(f"{v}\u2080")
        cur = f"{v}\u2081"
    heads.append(cur)
    body = "x"
    for h in reversed(heads):
        body = f"{h}({body})"
    return "(λf.λx." + "".join(src) + body + ")"


def parity_exp(n):
    """((N 2) NOT) TRUE -- exponentiation, not a doubling chain."""
    lab = iter(range(100000))
    return (f"@main = {_church(n, lab)}({_church(2, lab)})"
            f"((λp.λt.λf.p(f,t)))((λa.λb.a))\n")


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else "/tmp/cnot"
    os.makedirs(out, exist_ok=True)
    for n in range(1, 25):
        open(os.path.join(out, f"cnot_{n:02d}.hvm"), "w").write(cnot_chain(n))
        open(os.path.join(out, f"par_{n:02d}.hvm"), "w").write(parity_exp(n))
    print(f"wrote cnot_01..24 and par_01..24 to {out}")


if __name__ == "__main__":
    main()
