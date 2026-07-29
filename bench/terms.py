#!/usr/bin/env python3
"""
Term generator for the TRVM cross-runtime benchmark.

Everything here emits IC surface syntax (the language `spec/conformance/README.md`
pins): `λ`, application `(f x)`, superposition `&L{a,b}`, duplication
`!&L{a,b}=v; body`, eraser `*`.

The one rule that governs every generator below: **IC binders are linear**. A
lambda-bound variable may be used exactly once. Any second use must go through an
explicit `!&L{a,b}=v;` duplicator, and *independent* duplicators must carry
*distinct* labels -- reusing a label across independent duplications reduces
incorrectly by design (it is not a bug in the runtime, it is the Lamping
labelling discipline). So every generator takes a label allocator and never
reuses a label.

Nothing here imports from the runtimes; these are pure strings, so the same bytes
go to all six backends.
"""


class Labels:
    """Monotone label allocator. Every call returns a label never returned before."""

    def __init__(self, start=1):
        self.n = start

    def next(self):
        self.n += 1
        return self.n


def church(n, lab):
    """A Church numeral `n` in explicitly-linear form.

    `λf.λx.(f (f ... x))` uses `f` n times, which is illegal for a linear binder.
    The linear form threads `f` through an n-1 deep chain of duplicators:

        λf.λx. !&L1{c0,t0}=f; !&L2{c1,t1}=t0; ... ; (c0 (c1 (... (c_{n-1} x))))

    Each duplicator gets its own fresh label from `lab`.
    """
    if n == 0:
        return "λf.λx.x"
    if n == 1:
        return "λf.λx.(f x)"
    cs = [f"c{i}" for i in range(n)]
    src = []
    cur = "f"
    for i in range(n - 1):
        L = lab.next()
        # the last duplicator splits into the final TWO copies, not copy+tail
        nxt = f"t{i}" if i < n - 2 else cs[-1]
        src.append(f"!&{L}{{{cs[i]},{nxt}}}={cur};")
        cur = nxt
    body = "x"
    for c in reversed(cs):
        body = f"({c} {body})"
    return "λf.λx." + "".join(src) + body


# ---------------------------------------------------------------------------
# Booleans -- all linear already (each binder used once)
# ---------------------------------------------------------------------------
TRUE = "λa.λb.a"
FALSE = "λa.λb.b"
NOT = "λp.λt.λf.((p f) t)"


# ---------------------------------------------------------------------------
# Workload term builders. Each returns (term, expected_normal_form_description).
# ---------------------------------------------------------------------------

def w_mult(n, m, lab):
    """n * m, read back as s^(n*m).  ((N (M s)) z)"""
    return f"(({church(n, lab)} ({church(m, lab)} s)) z)"


def w_exp(a, b, lab):
    """b^a, read back as s^(b^a).  (((A B) s) z)  -- (A B) is B^A."""
    return f"((({church(a, lab)} {church(b, lab)}) s) z)"


def w_tetration(base, height, lab):
    """base^^height -- the true right-associated power tower -- read back as s^tower.

    Since `(A B)` computes `B^A`, the tower must be built LEFT-associated in the
    surface syntax to mean a right-associated exponentiation:
        `((B B) B)` = `(B^B B)` = B^(B^B).
    Each numeral instance is generated separately so it gets its own labels.
    """
    t = church(base, lab)
    for _ in range(height - 1):
        t = f"({t} {church(base, lab)})"
    return f"(({t} s) z)"


def w_parity_pow2(N, lab):
    """Parity of 2^N, computed as NOT applied 2^N times to TRUE.

    This is the optimal-sharing headline: the *semantics* is 2^N sequential
    negations, but a sharing-correct runtime does it in O(N) interactions because
    the repeated NOT applications are shared rather than expanded. Parity of
    16.7 million negations in a few hundred interactions.

    `(((N 2) NOT) TRUE)` = NOT^(2^N) TRUE.  2^N is even for N>=1, so the answer
    is TRUE = λa.λb.a.
    """
    return f"((({church(N, lab)} {church(2, lab)}) {NOT}) {TRUE})"


def w_sum_to_n(n, lab):
    """Gauss triangular number T(n) = n(n+1)/2, via mult+add-free construction.

    Built as sum_{i=1..n} i by nesting: ((1 s) ((2 s) (... ((n s) z))))
    Each numeral is separately generated so labels stay distinct.
    """
    body = "z"
    for i in range(n, 0, -1):
        body = f"(({church(i, lab)} s) {body})"
    return body


# ---------------------------------------------------------------------------
# Linear combinator library. MUL and the pair combinators are already linear;
# SUCC and ADD both need `f` twice, so each gets a fresh duplicator.
# ---------------------------------------------------------------------------

def SUCC(lab):
    L = lab.next()
    return f"λn.λf.λx.!&{L}{{f1,f2}}=f;(f1 ((n f2) x))"


def ADD(lab):
    L = lab.next()
    return f"λm.λn.λf.λx.!&{L}{{f1,f2}}=f;((m f1) ((n f2) x))"


MUL = "λm.λn.λf.(m (n f))"
PAIR = "λa.λb.λf.((f a) b)"
FST = "λp.(p λa.λb.a)"
SND = "λp.(p λa.λb.b)"


def w_fib(n, lab):
    """Fibonacci via Church-pair iteration: (a,b) -> (b, a+b), n times from (0,1).

    Stresses the runtime harder than plain arithmetic: the step function itself
    contains duplicators, so iterating it duplicates a duplicator.
    """
    L = lab.next()
    step = f"λp.(p λa.λb.!&{L}{{b1,b2}}=b;(({PAIR} b1) (({ADD(lab)} a) b2)))"
    init = f"(({PAIR} {church(0, lab)}) {church(1, lab)})"
    return f"((({FST} (({church(n, lab)} {step}) {init})) s) z)"


def w_fact(n, lab):
    """Factorial via Church-pair iteration: (i,acc) -> (i+1, i*acc), n times from (1,1)."""
    L = lab.next()
    step = f"λp.(p λi.λa.!&{L}{{i1,i2}}=i;(({PAIR} ({SUCC(lab)} i1)) (({MUL} i2) a)))"
    init = f"(({PAIR} {church(1, lab)}) {church(1, lab)})"
    return f"((({SND} (({church(n, lab)} {step}) {init})) s) z)"


def w_pred(n, lab):
    """Kleene's predecessor via pairs: (a,b) -> (b, b+1), n times from (0,0)."""
    L = lab.next()
    step = f"λp.(p λa.λb.!&{L}{{b1,b2}}=b;(({PAIR} b1) ({SUCC(lab)} b2)))"
    init = f"(({PAIR} {church(0, lab)}) {church(0, lab)})"
    return f"((({FST} (({church(n, lab)} {step}) {init})) s) z)"


def w_ackermann(m, n, lab):
    """Ackermann via Church numerals: ack = λm. m (λf.λn. n f (f 1)) succ.

    NOTE: only m <= 1 is inside IC's safe labelling fragment. For m >= 2 the
    iteration duplicates `inner`, whose duplicator label is then shared by two
    independent duplicators, and reduction diverges. That divergence is a
    property of the encoding, not a defect of any runtime -- it is kept as a
    workload precisely to check that all six runtimes agree on diverging.
    """
    L = lab.next()
    inner = f"λf.λn.!&{L}{{f1,f2}}=f;((n f1) (f2 {church(1, lab)}))"
    ack_m = f"(({church(m, lab)} {inner}) {SUCC(lab)})"
    return f"((({ack_m} {church(n, lab)}) s) z)"


def w_dup_stress(depth, lab):
    """A pure duplication stress: duplicate a lambda `depth` times, nested.

    Exercises the DUP-LAM rule and the floating-dup machinery specifically,
    independent of Church arithmetic.
    """
    src = []
    cur = "λq.q"
    for i in range(depth):
        L = lab.next()
        src.append(f"!&{L}{{a{i},b{i}}}={cur};")
        cur = f"(a{i} b{i})"
    return "".join(src) + cur
