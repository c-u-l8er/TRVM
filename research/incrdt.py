"""
incrdt.py -- the cheap decisive experiment: is `merge = union + reduce` a CRDT?

A CRDT's merge must be commutative, associative, and IDEMPOTENT. Claim under test:
for interaction-calculus "knowledge", confluence gives commutativity/associativity
for free, but idempotence is the crux -- a NAIVE union fails it, and content-
addressing (structural dedup) is what recovers it.

Knowledge = a set of derivations (IC terms whose normal forms are derived facts).
Two replicas overlap. For each merge we measure, under two strategies:
  NAIVE = union as a MULTISET (keep duplicates), reduce each
  CA    = content-addressed: dedup by alpha-canonical structure, reduce distinct once
metrics:
  RESULT = set of normal-form facts   SIZE = representation size   WORK = interactions

Reducer for WORK/RESULT: ic_float (via run()). SIZE/dedup: own structural parser.
Run: python3 incrdt.py
"""
import ic_float

# ---------------------------------------------------------------- knowledge model
def church(n):
    if n == 0: return "λf.λx.x"
    if n == 1: return "λf.λx.(f x)"
    cs = [f"c{i}" for i in range(n)]; src = []; cur = "f"
    for i in range(n-1):
        L = 1000 + n*10 + i                       # FIXED labels: identical derivations are byte-identical
        nxt = f"t{i}" if i < n-2 else cs[-1]
        src.append(f"!&{L}{{{cs[i]},{nxt}}}={cur};"); cur = nxt
    body = "x"
    for c in reversed(cs): body = f"({c} {body})"
    return "λf.λx." + "".join(src) + body

NOT = "λp.λt.λf.((p f) t)"; TRUE = "λa.λb.a"; FALSE = "λa.λb.b"
def deriv(n, b): return f"(({church(n)} {NOT}) {b})"   # 'agent computed NOT^n(b)'

# ---------------------------------------------------------------- structural parser (for SIZE/dedup)
def parse_tree(txt):
    pos = [0]
    def ws():
        while pos[0] < len(txt) and txt[pos[0]] in " \t\n\r": pos[0] += 1
    def peek():
        ws(); return txt[pos[0]] if pos[0] < len(txt) else ""
    def eat(c):
        ws(); assert txt[pos[0]] == c, f"want {c!r} at {pos[0]}"; pos[0] += 1
    def name():
        ws(); j = pos[0]
        while pos[0] < len(txt) and (txt[pos[0]].isalnum() or txt[pos[0]] == "_"): pos[0] += 1
        return txt[j:pos[0]]
    def uint():
        ws(); j = pos[0]
        while pos[0] < len(txt) and txt[pos[0]].isdigit(): pos[0] += 1
        return int(txt[j:pos[0]]) if pos[0] > j else 0
    def term():
        c = peek()
        if c in ("λ", "\\"): pos[0] += 1; v = name(); eat("."); return ("lam", v, term())
        if c == "*": pos[0] += 1; return ("era",)
        if c == "(": eat("("); f = term(); a = term(); eat(")"); return ("app", f, a)
        if c == "&": eat("&"); lab = uint(); eat("{"); l = term(); eat(","); r = term(); eat("}"); return ("sup", lab, l, r)
        if c == "!":
            eat("!"); lab = 0
            if peek() == "&": eat("&"); lab = uint()
            eat("{"); a = name(); eat(","); b = name(); eat("}"); eat("=")
            val = term(); eat(";"); return ("dup", lab, a, b, val, term())
        return ("var", name())
    return term()

def canon(t, env=None, depth=0):
    if env is None: env = {}
    tag = t[0]
    if tag == "var": return ("b" + str(depth-1-env[t[1]])) if t[1] in env else ("F" + t[1])
    if tag == "era": return "*"
    if tag == "lam":
        e = dict(env); e[t[1]] = depth; return "L(" + canon(t[2], e, depth+1) + ")"
    if tag == "app": return "@(" + canon(t[1], env, depth) + "," + canon(t[2], env, depth) + ")"
    if tag == "sup": return f"S{t[1]}(" + canon(t[2], env, depth) + "," + canon(t[3], env, depth) + ")"
    if tag == "dup":
        cv = canon(t[4], env, depth); e = dict(env); e[t[2]] = depth; e[t[3]] = depth+1
        return f"D{t[1]}(" + cv + ";" + canon(t[5], e, depth+2) + ")"

def all_nodes(t, acc, env=None, depth=0):
    if env is None: env = {}
    acc.add(canon(t, env, depth)); tag = t[0]
    if tag == "lam":
        e = dict(env); e[t[1]] = depth; all_nodes(t[2], acc, e, depth+1)
    elif tag == "app":
        all_nodes(t[1], acc, env, depth); all_nodes(t[2], acc, env, depth)
    elif tag == "sup":
        all_nodes(t[2], acc, env, depth); all_nodes(t[3], acc, env, depth)
    elif tag == "dup":
        all_nodes(t[4], acc, env, depth); e = dict(env); e[t[2]] = depth; e[t[3]] = depth+1
        all_nodes(t[5], acc, e, depth+2)
    return acc

def treesize(t):
    tag = t[0]
    if tag in ("var", "era"): return 1
    if tag == "lam": return 1 + treesize(t[2])
    if tag == "app": return 1 + treesize(t[1]) + treesize(t[2])
    if tag == "sup": return 1 + treesize(t[2]) + treesize(t[3])
    if tag == "dup": return 1 + treesize(t[4]) + treesize(t[5])

# ---------------------------------------------------------------- merge evaluation
def reduce_one(src):
    nf, total, _ = ic_float.run(src)         # (normal-form string, interactions, ctr)
    return nf, total

def evaluate(multiset):
    key = {s: canon(parse_tree(s)) for s in set(multiset)}
    distinct = {}
    for s in multiset: distinct[key[s]] = s
    distinct_srcs = list(distinct.values())

    facts = set(); naive_work = 0
    for s in multiset:
        nf, w = reduce_one(s); facts.add(nf); naive_work += w
    ca_work = sum(reduce_one(s)[1] for s in distinct_srcs)

    naive_size = sum(treesize(parse_tree(s)) for s in multiset)
    nodes = set()
    for s in distinct_srcs: all_nodes(parse_tree(s), nodes)
    return {"facts": frozenset(facts), "naive_work": naive_work, "ca_work": ca_work,
            "naive_size": naive_size, "ca_size": len(nodes),
            "n": len(multiset), "nd": len(distinct_srcs)}

# ---------------------------------------------------------------- experiment
if __name__ == "__main__":
    A = [deriv(2, FALSE), deriv(3, TRUE),  deriv(5, FALSE)]
    B = [deriv(2, FALSE), deriv(4, TRUE),  deriv(7, FALSE)]   # shares deriv(2,F)
    C = [deriv(3, TRUE),  deriv(7, FALSE), deriv(2, FALSE)]
    def merge(*reps):
        out = []
        for r in reps: out += r
        return out

    print("IN-CRDT axiom test:  is  merge = union + reduce  a CRDT?")
    print("Replicas = sets of interaction-calculus derivations (overlapping).")
    print("="*76)

    ab, ba = evaluate(merge(A, B)), evaluate(merge(B, A))
    print("\n[1] COMMUTATIVITY  merge(A,B) vs merge(B,A)")
    print(f"    result facts equal : {ab['facts']==ba['facts']}")
    print(f"    CA work equal      : {ab['ca_work']==ba['ca_work']}  ({ab['ca_work']} vs {ba['ca_work']})")
    print(f"    CA size equal      : {ab['ca_size']==ba['ca_size']}  ({ab['ca_size']} vs {ba['ca_size']})")

    l, r = evaluate(merge(merge(A, B), C)), evaluate(merge(A, merge(B, C)))
    print("\n[2] ASSOCIATIVITY  merge(merge(A,B),C) vs merge(A,merge(B,C))")
    print(f"    result facts equal : {l['facts']==r['facts']}")
    print(f"    CA work equal      : {l['ca_work']==r['ca_work']}  ({l['ca_work']} vs {r['ca_work']})")
    print(f"    CA size equal      : {l['ca_size']==r['ca_size']}  ({l['ca_size']} vs {r['ca_size']})")

    aa, a = evaluate(merge(A, A)), evaluate(A)
    print("\n[3] IDEMPOTENCE  merge(A,A) vs A     <-- the crux")
    print(f"    RESULT facts equal           : {aa['facts']==a['facts']}   (#facts={len(a['facts'])})")
    print(f"    SIZE  naive : {a['naive_size']:4} -> {aa['naive_size']:4}   idempotent? {aa['naive_size']==a['naive_size']}")
    print(f"    SIZE  CA    : {a['ca_size']:4} -> {aa['ca_size']:4}   idempotent? {aa['ca_size']==a['ca_size']}")
    print(f"    WORK  naive : {a['naive_work']:4} -> {aa['naive_work']:4}   idempotent? {aa['naive_work']==a['naive_work']}")
    print(f"    WORK  CA    : {a['ca_work']:4} -> {aa['ca_work']:4}   idempotent? {aa['ca_work']==a['ca_work']}")

    print("\n" + "-"*76)
    print("READING:")
    print(" * RESULT (set of facts) is idempotent either way: identical normal forms")
    print("   collapse. A data CRDT over the facts alone is trivial (a G-Set).")
    print(" * NAIVE union is NOT idempotent in SIZE or WORK: merge(A,A) keeps two copies")
    print("   and re-runs reduction. So naive union+reduce is NOT a CRDT.")
    print(" * CONTENT-ADDRESSING restores idempotence in SIZE and WORK (merge(A,A)==A),")
    print("   while commutativity/associativity hold (confluence + set semantics).")
    print(f" * Bonus: CA also COMPRESSES non-idempotent merges. merge(A,B): naive size")
    print(f"   {ab['naive_size']} vs CA {ab['ca_size']} (shared sub-structure across derivations dedups).")

    print("\n" + "="*76)
    print("[4] SUB-COMPUTATION SHARING (the harder, IN-specific case)")
    print("    Two DIFFERENT derivations sharing a sub-computation NOT4 = (church4 NOT).")
    NOT4 = f"({church(4)} {NOT})"
    _, w1 = reduce_one(f"({NOT4} {FALSE})")
    _, w2 = reduce_one(f"({NOT4} {TRUE})")
    sep = w1 + w2
    shared = f"!&7{{n1,n2}}={NOT4}; λs.((s (n1 {FALSE})) (n2 {TRUE}))"
    _, wsh = reduce_one(shared)
    print(f"    separate (NOT4 reduced twice) : {sep} interactions  ({w1}+{w2})")
    print(f"    shared   (NOT4 dup, reduced ~once): {wsh} interactions")
    verdict = "SAVES work" if wsh < sep else "does NOT save work"
    print(f"    => sharing {verdict}: {sep} -> {wsh}" + (f"  ({sep/wsh:.2f}x)" if wsh else ""))
    print("    NOT4 is higher-order (a function); sharing it across uses is exactly the")
    print("    higher-order-duplication case the floating reducer handles.")

    print("\n" + "="*76)
    print("VERDICT: merge=union+reduce is a CRDT IFF the union is content-addressed.")
    print("Confluence => commutativity + associativity. Content-addressing (hash-consing,")
    print("the machinery e-graphs use) => idempotence. The open hard part is keeping the")
    print("shared sub-computation canonical UNDER reduction (maximal-sharing-under-")
    print("rewriting). The cheap experiment's answer: the IN-CRDT is viable at the")
    print("structural level; the research lives in that last step.")
