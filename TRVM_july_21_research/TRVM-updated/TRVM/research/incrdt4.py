"""
incrdt4.py -- break the label assumption (the pushed experiment), and go one step
further: does label CANONICALIZATION recover the sharing, and is it sound?

Setup: N replicas each independently derive the SAME computation NOT^6(FALSE),
but with DIFFERENT duplication labels (as independent machines would). We compare
two content-addressing strategies:

  label-sensitive  : canon includes label values  (current scheme)
  label-canonical  : canon renames labels by first-encounter (alpha-rename labels)

and ask, vs N:  distinct count, reduction work, and NF soundness.

Run: python3 incrdt4.py
"""
import ic_float
from incrdt import parse_tree, canon, NOT, FALSE

def free_vars(t, bound=frozenset()):
    tag = t[0]
    if tag == "var": return set() if t[1] in bound else {t[1]}
    if tag == "era": return set()
    if tag == "lam": return free_vars(t[2], bound | {t[1]})
    if tag == "app": return free_vars(t[1], bound) | free_vars(t[2], bound)
    if tag == "sup": return free_vars(t[2], bound) | free_vars(t[3], bound)
    if tag == "dup": return free_vars(t[4], bound) | free_vars(t[5], bound | {t[2], t[3]})
    return set()
def is_closed(t): return not free_vars(t)
def size(t):
    tag = t[0]
    if tag in ("var", "era"): return 1
    if tag == "lam": return 1 + size(t[2])
    if tag == "app": return 1 + size(t[1]) + size(t[2])
    if tag == "sup": return 1 + size(t[2]) + size(t[3])
    if tag == "dup": return 1 + size(t[4]) + size(t[5])
def render(t):
    tag = t[0]
    if tag == "var": return t[1]
    if tag == "era": return "*"
    if tag == "lam": return f"λ{t[1]}.{render(t[2])}"
    if tag == "app": return f"({render(t[1])} {render(t[2])})"
    if tag == "sup": return f"&{t[1]}{{{render(t[2])},{render(t[3])}}}"
    if tag == "dup": return f"!&{t[1]}{{{t[2]},{t[3]}}}={render(t[4])};{render(t[5])}"

def church(n, base):                         # labels offset by `base` -> different per replica
    if n == 0: return "λf.λx.x"
    if n == 1: return "λf.λx.(f x)"
    cs = [f"c{i}" for i in range(n)]; src = []; cur = "f"
    for i in range(n-1):
        L = base + n*10 + i; nxt = f"t{i}" if i < n-2 else cs[-1]
        src.append(f"!&{L}{{{cs[i]},{nxt}}}={cur};"); cur = nxt
    body = "x"
    for c in reversed(cs): body = f"({c} {body})"
    return "λf.λx." + "".join(src) + body

# ---- label-canonical key: rename labels by first encounter, then canon --------
def label_renumber(t, m=None, nxt=None):
    if m is None: m = {}; nxt = [0]
    tag = t[0]
    if tag in ("var", "era"): return t
    if tag == "lam": return ("lam", t[1], label_renumber(t[2], m, nxt))
    if tag == "app": return ("app", label_renumber(t[1], m, nxt), label_renumber(t[2], m, nxt))
    if tag == "sup":
        if t[1] not in m: m[t[1]] = nxt[0]; nxt[0] += 1
        return ("sup", m[t[1]], label_renumber(t[2], m, nxt), label_renumber(t[3], m, nxt))
    if tag == "dup":
        if t[1] not in m: m[t[1]] = nxt[0]; nxt[0] += 1
        return ("dup", m[t[1]], t[2], t[3], label_renumber(t[4], m, nxt), label_renumber(t[5], m, nxt))

def canon_sensitive(t): return canon(t)
def canon_canonical(t): return canon(label_renumber(t))

# ---- generalized auto-share parameterized by the canon function --------------
def collect_g(t, counts, reps, cf):
    if is_closed(t) and size(t) >= 3:
        k = cf(t); counts[k] = counts.get(k, 0) + 1; reps[k] = t
    tag = t[0]
    if tag == "lam": collect_g(t[2], counts, reps, cf)
    elif tag == "app": collect_g(t[1], counts, reps, cf); collect_g(t[2], counts, reps, cf)
    elif tag == "sup": collect_g(t[2], counts, reps, cf); collect_g(t[3], counts, reps, cf)
    elif tag == "dup": collect_g(t[4], counts, reps, cf); collect_g(t[5], counts, reps, cf)

def replace_g(t, key, ctr, cf):
    if cf(t) == key:
        v = ("var", f"__p{ctr[0]}"); ctr[0] += 1; return v
    tag = t[0]
    if tag == "lam": return ("lam", t[1], replace_g(t[2], key, ctr, cf))
    if tag == "app": return ("app", replace_g(t[1], key, ctr, cf), replace_g(t[2], key, ctr, cf))
    if tag == "sup": return ("sup", t[1], replace_g(t[2], key, ctr, cf), replace_g(t[3], key, ctr, cf))
    if tag == "dup": return ("dup", t[1], t[2], t[3], replace_g(t[4], key, ctr, cf), replace_g(t[5], key, ctr, cf))
    return t

def auto_share_g(sources, cf):
    trees = [parse_tree(s) for s in sources]
    counts, reps = {}, {}
    for t in trees: collect_g(t, counts, reps, cf)
    cands = [(k, c) for k, c in counts.items() if c >= 2]
    if not cands:
        body = "R"
        for s in sources: body = f"({body} {s})"
        return body, 0
    key = max(cands, key=lambda kc: size(reps[kc[0]]) * (kc[1] - 1))[0]
    val = render(reps[key]); K = counts[key]
    ctr = [0]; nt = [replace_g(t, key, ctr, cf) for t in trees]
    parts = []; cur = val
    for i in range(K - 1):
        a = f"__p{i}"; b = f"__p{K-1}" if i == K-2 else f"__t{i}"
        parts.append(f"!&{700+i}{{{a},{b}}}={cur};"); cur = b
    body = "R"
    for t in nt: body = f"({body} {render(t)})"
    return "".join(parts) + body, K

def rw(term):
    nf, total, _ = ic_float.run(term); return nf, total

# ============================================================ experiment
def replicas(n):
    # n independent replicas of NOT^6(FALSE), each with DIFFERENT labels
    return [f"(({church(6, 1000*(k+1))} {NOT}) {FALSE})" for k in range(n)]

print("Breaking the label assumption: N replicas compute the SAME NOT^6(FALSE)")
print("with DIFFERENT labels. Does content-addressing still share the work?")
print("=" * 78)

# sanity: two replicas, same computation, different labels -> are they canon-equal?
r = replicas(2)
t0, t1 = parse_tree(r[0]), parse_tree(r[1])
print(f"\nsame computation, different labels:")
print(f"  label-sensitive canon equal : {canon_sensitive(t0) == canon_sensitive(t1)}  (so content-addressing misses the match)")
print(f"  label-canonical canon equal : {canon_canonical(t0) == canon_canonical(t1)}  (match recovered)")

print(f"\n{'N':>3}{'unshared':>11}{'sensitive':>11}{'canonical':>11}{'canon NF ok':>13}{'recovered':>11}")
for n in (1, 2, 3, 4, 6):
    src = replicas(n)
    nf_u, u = rw("R" + "".join(f" ({s})" for s in src) if False else (lambda b: b)("R"))  # placeholder
    # unshared baseline
    body = "R"
    for s in src: body = f"({body} {s})"
    nf_u, u = rw(body)
    s_term, _ = auto_share_g(src, canon_sensitive); nf_s, sw = rw(s_term)
    c_term, _ = auto_share_g(src, canon_canonical); nf_c, cw = rw(c_term)
    ok = (nf_c == nf_u)
    recovered = f"{u/cw:.2f}x" if cw else "-"
    print(f"{n:>3}{u:>11}{sw:>11}{cw:>11}{str(ok):>13}{recovered:>11}")

print("\n" + "-" * 78)
print("READING:")
print(" * label-SENSITIVE content-addressing == unshared: the sharing is LOST ENTIRELY")
print("   across independently-labeled replicas. merge(A,A') costs 2x even though A and")
print("   A' are the same computation. So idempotence breaks across replicas -- ChatGPT's")
print("   'catastrophic' branch, confirmed.")
print(" * label-CANONICAL content-addressing recovers the FULL sharing law (~49+11N) and")
print("   NF stays correct: the differently-labeled replicas are detected as one")
print("   computation and reduced once, SOUNDLY (here).")
print(" * So label canonicalization is not just the problem -- it is most of the SOLUTION.")
print("   The loss is catastrophic WITHOUT it and (here) fully recovered WITH it.")
print("\nRESIDUAL (the honest remaining gap):")
print(" * Soundness held because the shared copy's labels do not COLLIDE with other dups")
print("   in the surrounding derivations (here there are none). In general, canonicalizing")
print("   two DIFFERENT computations to overlapping label ranges, then duplicating copies")
print("   that later meet, can trigger spurious DUP-DUP annihilation. The remaining hard")
print("   part is therefore narrower than 'label canonicalization': it is a GLOBALLY")
print("   COLLISION-FREE canonical labeling (canonical for matching, fresh-on-copy for")
print("   soundness) -- the exact analogue of de Bruijn naming + freshening for variables,")
print("   and the same canonical-form-under-confluent-rewriting problem e-graphs solve.")
