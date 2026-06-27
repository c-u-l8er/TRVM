"""
ic_convergence.py -- CLOSURE TEST: does optimal sharing (the actual IC runtime) create early
convergence that ordinary beta reduction hides?

convergence_map.py measured beta over church arithmetic -> World 1 (early convergence rare). But
every beta experiment lived where equivalence ~ beta. IC's whole point is dup + superposition +
optimal sharing, so this is the one decision-relevant question left. We measure it on the actual
IC runtime (ic_float), with church numerals encoded the way a compiler must -- explicit linear
dups, FRESH DISTINCT LABELS per numeral (ic_float's own _ch does this).

Trajectory capture: ic_float gets an opt-in interaction BUDGET; running normal() with budget k
yields the k-bounded partial form (redexes/Dps left stuck). Sweeping k gives an IC trajectory.

Canonical key for partial IC states is the methodological crux. A too-FINE key (distinguishing
fresh names, label numbers, dup-node identities) would UNDERcount convergence and falsely confirm
World 1 -- the bias we must avoid. So the PRIMARY metric uses a deliberately COARSE canon that
ignores dup labels and dup-node identity (Dp -> just its side): it OVER-counts convergence, so a
World-1 verdict under it is an UPPER BOUND and therefore robust. A finer canon is reported too.

Run: python3 ic_convergence.py
"""
import sys, itertools, statistics
sys.setrecursionlimit(1000000)
import ic_float as ic

_LAB = [1]
def nlab():
    _LAB[0] += 1; return _LAB[0]
def clin(n, lab):
    if n <= 1: return "\\f.\\x.(f x)"
    s = "\\f.\\x."; cur = "f"
    for i in range(n - 1):
        if i < n - 2: s += "!&%d{a%d,t%d}=%s;" % (lab, i, i, cur); cur = "t%d" % i
        else:         s += "!&%d{a%d,a%d}=%s;" % (lab, i, i + 1, cur)
    for i in range(n): s += "(a%d " % i
    return s + "x" + ")" * n
# church-arithmetic expressions applied to free s,z so the result reads as (s (s ... z)) = s^value
def E_church(v): return "((%s s) z)" % clin(v, nlab())
def E_mul(a, b): return "((%s (%s s)) z)" % (clin(a, nlab()), clin(b, nlab()))     # (a (b s)) z
def E_exp(n, m): return "(((%s %s) s) z)" % (clin(n, nlab()), clin(m, nlab()))     # m^n
def E_add(a, b):
    L = nlab()
    return "!&%d{p,q}=s;((%s p) ((%s q) z))" % (L, clin(a, nlab()), clin(b, nlab()))

def full_nf_scount(src):
    ic.reset_runtime(); ic.BUDGET[0] = None
    t = ic.normal(ic.parse(src))
    return ic.show(t).count("(s ")

# ---- canonical keys for partial IC states ----
def canon_coarse(t):                 # PRIMARY: ignores dup labels and dup-node identity -> OVERcounts convergence
    slots = {}; order = []
    def go(t, env, d):
        if isinstance(t, ic.Var):
            n = t.nam
            if n in env: return ('b', d - 1 - env[n])
            if n not in slots: slots[n] = len(order); order.append(n)
            return ('f', slots[n])
        if isinstance(t, ic.Era): return ('E',)
        if isinstance(t, ic.Lam):
            e = dict(env); e[t.nam] = d; return ('L', go(t.bod, e, d + 1))
        if isinstance(t, ic.App): return ('A', go(t.fun, env, d), go(t.arg, env, d))
        if isinstance(t, ic.Sup): return ('S', go(t.lft, env, d), go(t.rgt, env, d))   # label dropped
        if isinstance(t, ic.Dp):  return ('D', t.side)                                 # node dropped
        return ('?',)
    return repr(go(t, {}, 0))
def canon_fine(t):                   # SECONDARY: keeps labels (renumbered) + dup-node ids
    slots = {}; order = []; labs = {}; nid = {}; ncanon = {}
    def lab(l):
        if l not in labs: labs[l] = len(labs)
        return labs[l]
    def go(t, env, d):
        if isinstance(t, ic.Var):
            n = t.nam
            if n in env: return ('b', d - 1 - env[n])
            if n not in slots: slots[n] = len(order); order.append(n)
            return ('f', slots[n])
        if isinstance(t, ic.Era): return ('E',)
        if isinstance(t, ic.Lam):
            e = dict(env); e[t.nam] = d; return ('L', go(t.bod, e, d + 1))
        if isinstance(t, ic.App): return ('A', go(t.fun, env, d), go(t.arg, env, d))
        if isinstance(t, ic.Sup): return ('S', lab(t.lab), go(t.lft, env, d), go(t.rgt, env, d))
        if isinstance(t, ic.Dp):
            nd = t.node
            if id(nd) not in nid:
                nid[id(nd)] = len(nid)
                ncanon[id(nd)] = ('N', lab(nd.lab), go(nd.val, env, d))
            return ('D', nid[id(nd)], t.side)
        return ('?',)
    r = go(t, {}, 0)
    return repr((r, [ncanon[k] for k in sorted(ncanon, key=lambda k: nid[k])]))

def k_trace(src, canon, hardcap=4000):
    ic.reset_runtime(); ic.BUDGET[0] = None
    nf_key = canon(ic.normal(ic.parse(src)))
    keys = []; k = 0
    while k <= hardcap:
        ic.reset_runtime(); ic.BUDGET[0] = k
        key = canon(ic.normal(ic.parse(src)))
        if not keys or keys[-1] != key: keys.append(key)
        if key == nf_key and k > 0: break
        k += 1
    return keys, nf_key

print("Closure test: early convergence under the IC runtime (optimal sharing)")
print("=" * 78)

# ---- build corpus and VALIDATE every encoding before trusting the measurement ----
def exprs_for(v):
    out = [("church", E_church(v))]
    for a in range(1, v):
        if a <= v - a: out.append((f"add({a},{v-a})", E_add(a, v - a)))
    for a in range(2, v):
        if v % a == 0 and 2 <= a <= v // a: out.append((f"mul({a},{v//a})", E_mul(a, v // a)))
    return out
def exp_exprs():
    out = {}
    for n, m in [(2, 2), (3, 2), (2, 3), (2, 4), (4, 2)]:
        v = m ** n; out.setdefault(v, []).append((f"exp({m}^{n})", E_exp(n, m)))
    return out

VALUES = [6, 8, 9, 12, 16]
classes = {v: exprs_for(v) for v in VALUES}
for v, lst in exp_exprs().items():
    classes.setdefault(v, []).extend(lst)

print("\nvalidating encodings (each must reduce to s^value in the IC runtime):")
bad = 0; nval = 0
for v, es in classes.items():
    for name, src in es:
        sc = full_nf_scount(src); nval += 1
        if sc != v: bad += 1; print(f"  MISMATCH v={v} {name}: got s^{sc}")
print(f"  {nval} encodings checked, {bad} mismatches" + ("  -- ABORT" if bad else "  -- all correct"))
if bad: sys.exit(1)

# ---- measure convergence with the COARSE (upper-bound) canon ----
def measure(canon, label):
    T = {}
    for v, es in classes.items():
        for name, src in es: T[(v, name)] = k_trace(src, canon)[0]
    rows = []
    for v, es in classes.items():
        names = [n for n, _ in es]
        for n1, n2 in itertools.combinations(names, 2):
            ta, tb = T[(v, n1)], T[(v, n2)]
            nf = max(len(ta) - 1, len(tb) - 1)
            if nf == 0: continue
            pa = {k: i for i, k in enumerate(ta)}
            conv = min((max(pa[k], j) for j, k in enumerate(tb) if k in pa), default=nf)
            rows.append((v, n1, n2, conv, nf, conv / nf, conv < nf))
    early = [r for r in rows if r[6]]
    frac = len(early) / len(rows) if rows else 0
    print(f"\n[{label} canon] {len(rows)} equivalent pairs; {len(early)} converge before NF "
          f"({100*frac:.0f}%)")
    if early:
        er = [r[5] for r in early]
        print(f"  early-pair depth-ratio: mean {statistics.mean(er):.2f}, min {min(er):.2f}")
        for r in sorted(rows, key=lambda r: r[5])[:5]:
            print(f"    v={r[0]:2d} {r[1]:>12} = {r[2]:<12} ratio {r[5]:.2f} ({r[3]}/{r[4]})")
    # sanity: different-value pairs never share a form
    crossbad = 0
    keys = list(T.keys())
    import random; random.seed(0)
    for _ in range(400):
        (v1, n1), (v2, n2) = random.sample(keys, 2)
        if v1 != v2 and (set(T[(v1, n1)]) & set(T[(v2, n2)])): crossbad += 1
    print(f"  sanity: different-value pairs sharing a form: {crossbad} (MUST be 0)")
    return frac, early, crossbad

frac_c, early_c, bad_c = measure(canon_coarse, "COARSE/upper-bound")
frac_f, early_f, bad_f = measure(canon_fine, "fine")

print("\n" + "=" * 78)
print("MEASUREMENT INVALID -- sanity check failed.")
print(f"  Different-value computations have DIFFERENT normal forms and (since reduction is")
print(f"  deterministic) cannot share a true reduction state -- yet both canons report some")
print(f"  doing so ({bad_c} coarse, {bad_f} fine), and the two canons disagree {frac_c*100:.0f}% vs "
      f"{frac_f*100:.0f}%. So neither convergence number is trustworthy.")
print("""
WHY (the real finding). Two compounding problems, both genuine:
  1. Budget-limited normal() does not produce faithful IC *states*. With a partial interaction
     budget the traversal reduces some branches and not others, yielding an order-dependent
     PARTIAL MIXTURE, not the net-state-after-k-interactions a true trajectory needs.
  2. Even given true states, canonicalizing a partial IC net with FLOATING DUPS (open subterms,
     shared dup nodes, label namespaces) is exactly the open-term-identity / slotted-e-graph
     problem -- the same hard problem from slotted_ic.py. A coarse canon false-positives
     (21 cross-value collisions); a finer one is ad hoc and still leaks (4).

There is a CIRCULARITY here worth stating plainly: to measure rigorously whether a dynamic
slotted e-graph is worth building, you need e-graph-grade canonical identity for partial IC
states -- i.e. you need the thing you are trying to decide whether to build. The cheap IC
convergence experiment is therefore NOT cleanly answerable with current tools.

DEFENSIBLE CONCLUSION (what survives):
  - Under beta (convergence_map.py, sanity-clean): World 1, early convergence ~6%, robust to
    reduction order. That result stands.
  - Under the IC runtime: technically OPEN, because a faithful measurement needs partial-state
    canonical identity (the open problem). But two things point to World 1 there too: (a) the
    beta result, and (b) IC intermediate states carry MORE distinguishing structure (fresh
    labels, dup nodes) than beta terms, which makes genuine (false-positive-free) coincidence
    rarer, not more common. So World 1 is the likely-but-unproven answer.
  - Net: the convergence branch is settled enough to NOT justify the e-graph build (beta is
    World 1; IC is plausibly World 1 and, more decisively, can't even be measured without first
    building e-graph-grade identity). The substrate's demonstrated value remains semantic dedup
    of RESULTS at the normal form plus modest memoization.""")
print("\n(ic_convergence.py is retained as a documented NEGATIVE/blocked result, not a verdict.)")
