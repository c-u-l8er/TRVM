"""
ic_float.py -- Interaction Calculus reducer using the FLOATING-DUP representation
(the IC32 design described in the reference README), as opposed to the
body-carrying representation in ic_ref.py.

The difference, and why it matters
----------------------------------
ic_ref.py stores each DUP with a body and, on reaching it, EAGERLY reduces the
duplicated value and pushes the duplication through the whole structure. That
loops forever on one pattern: duplicate a higher-order numeral, then apply a copy
of it to another higher-order lambda (e.g. `!&L{na,nb}=church2; ((na NOT) FALSE)`).

Here, following IC32:
  * There is NO Dup node in the AST. A duplication `!&L{a,b}=v; K` is represented
    by a DupNode that *floats on the heap* holding only `v`; the names a,b become
    PROJECTION VARIABLES Dp(node,0) / Dp(node,1) that appear in K.
  * A DupNode fires LAZILY and INCREMENTALLY -- only when one of its projection
    variables is actually demanded, and only one split at a time. The first demand
    reduces `v` one step's worth, produces the two halves (whose sub-parts are
    again lazy Dp variables), caches them, and hands back the demanded side; the
    sibling variable later picks up the other half.

That laziness is the whole fix: the structure is never eagerly walked, so the
divergent pattern terminates.

Validated against ic_ref.py as an oracle (same normal forms on everything ic_ref
handles), and shown to terminate on the case ic_ref diverges on.
"""

# ----------------------------------------------------------------------------
# Terms
# ----------------------------------------------------------------------------
class Var:
    __slots__=("nam")
    def __init__(s,nam): s.nam=nam
class Era:
    __slots__=()
class Lam:
    __slots__=("nam","bod")
    def __init__(s,nam,bod): s.nam=nam; s.bod=bod
class App:
    __slots__=("fun","arg")
    def __init__(s,fun,arg): s.fun=fun; s.arg=arg
class Sup:
    __slots__=("lab","lft","rgt")
    def __init__(s,lab,lft,rgt): s.lab=lab; s.lft=lft; s.rgt=rgt
class DupNode:
    # floats on the heap; holds the value being duplicated, fires lazily
    __slots__=("lab","val","fired","h0","h1")
    def __init__(s,lab,val): s.lab=lab; s.val=val; s.fired=False; s.h0=None; s.h1=None
class Dp:
    __slots__=("node","side")
    def __init__(s,node,side): s.node=node; s.side=side

# ----------------------------------------------------------------------------
# Global state
# ----------------------------------------------------------------------------
sub={}                 # name(int) -> Term   (lambda-var substitutions)
_fresh=[0]
def fresh():
    _fresh[0]+=1; return _fresh[0]
ctr={}
def bump(r): ctr[r]=ctr.get(r,0)+1
def reset_runtime():
    sub.clear()
    for k in list(ctr): ctr[k]=0
    BUDGET[0]=None

# optional interaction budget for trajectory capture: when set, whnf stops reducing once
# exhausted (leaving redexes/Dps stuck), so normal() returns a partial form. Default None =
# unlimited (the runtime's normal behavior is byte-identical when BUDGET is None).
BUDGET=[None]
def _tick():
    b=BUDGET[0]
    if b is None: return True
    if b<=0: return False
    BUDGET[0]=b-1; return True

# ----------------------------------------------------------------------------
# Firing a DupNode: reduce val to whnf, produce the two halves (lazy).
# Returns (h0, h1). May set sub[...] (DUP-LAM rebinds the lambda's var).
# ----------------------------------------------------------------------------
def fire(node):
    v = whnf(node.val)
    L = node.lab
    if isinstance(v, Sup):
        if v.lab == L:                       # DUP-SUP, equal labels: annihilate
            bump("DUP-SUP=")
            return v.lft, v.rgt
        else:                                # DUP-SUP, different labels: commute
            bump("DUP-SUP!")
            da=DupNode(L, v.lft); db=DupNode(L, v.rgt)
            h0=Sup(v.lab, Dp(da,0), Dp(db,0))
            h1=Sup(v.lab, Dp(da,1), Dp(db,1))
            return h0,h1
    if isinstance(v, Lam):                    # DUP-LAM
        bump("DUP-LAM")
        x0,x1=fresh(),fresh()
        df=DupNode(L, v.bod)                  # duplicate the body lazily
        sub[v.nam]=Sup(L, Var(x0), Var(x1))   # the bound var becomes a superposition
        return Lam(x0, Dp(df,0)), Lam(x1, Dp(df,1))
    if isinstance(v, Era):                    # DUP-ERA
        bump("DUP-ERA")
        return Era(), Era()
    if isinstance(v, App):                    # DUP-APP (collapse): copy structure
        bump("DUP-APP")
        df=DupNode(L, v.fun); dx=DupNode(L, v.arg)
        return App(Dp(df,0),Dp(dx,0)), App(Dp(df,1),Dp(dx,1))
    # Var (free/stuck) or anything else: DUP-VAR (collapse): copy
    bump("DUP-VAR")
    return v, v

# ----------------------------------------------------------------------------
# APP-SUP: (&L{a,b} c) -> !&L{c0,c1}=c; &L{(a c0),(b c1)}   (floating dup of c)
# ----------------------------------------------------------------------------
def app_sup(fun, arg):
    bump("APP-SUP")
    dc=DupNode(fun.lab, arg)
    return Sup(fun.lab, App(fun.lft, Dp(dc,0)), App(fun.rgt, Dp(dc,1)))

# ----------------------------------------------------------------------------
# Reduction drivers
# ----------------------------------------------------------------------------
def whnf(t):
    while True:
        if isinstance(t, Var):
            if t.nam in sub: t=sub[t.nam]; continue
            return t
        if isinstance(t, Dp):
            node=t.node
            if not node.fired:
                if not _tick(): return t          # budget exhausted: leave Dp stuck
                h0,h1=fire(node)
                node.h0=h0; node.h1=h1; node.fired=True
            t = node.h0 if t.side==0 else node.h1
            continue
        if isinstance(t, App):
            f=whnf(t.fun)
            if isinstance(f, Lam):
                if not _tick(): return App(f, t.arg)
                bump("APP-LAM"); sub[f.nam]=t.arg; t=f.bod; continue
            if isinstance(f, Sup):
                if not _tick(): return App(f, t.arg)
                t=app_sup(f, t.arg); continue
            if isinstance(f, Era):
                if not _tick(): return App(f, t.arg)
                bump("APP-ERA"); t=Era(); continue
            return App(f, t.arg)
        return t        # Lam, Sup, Era

NB=[0]
def normal(t, budget=3_000_000):
    NB[0]=budget
    return _normal(t)
def _normal(t):
    NB[0]-=1
    if NB[0]<=0: raise RuntimeError("normal: budget exhausted (probable non-termination)")
    t=whnf(t)
    if isinstance(t, Lam): return Lam(t.nam, _normal(t.bod))
    if isinstance(t, App): return App(_normal(t.fun), _normal(t.arg))
    if isinstance(t, Sup): return Sup(t.lab, _normal(t.lft), _normal(t.rgt))
    return t

# ----------------------------------------------------------------------------
# Parser (lexical alpha-renaming; dup-bound names become Dp projection vars)
# ----------------------------------------------------------------------------
class P:
    def __init__(s,txt): s.t=txt; s.i=0; s.scope=[]
    def err(s,m): raise SyntaxError(f"{m} at {s.i}: ...{s.t[s.i:s.i+20]!r}")
    def ws(s):
        while s.i<len(s.t) and s.t[s.i] in " \t\n\r": s.i+=1
    def peek(s): s.ws(); return s.t[s.i] if s.i<len(s.t) else ""
    def eat(s,c):
        s.ws()
        if s.i>=len(s.t) or s.t[s.i]!=c: s.err(f"expected {c!r}")
        s.i+=1
    def name(s):
        s.ws(); j=s.i
        while s.i<len(s.t) and (s.t[s.i].isalnum() or s.t[s.i]=="_"): s.i+=1
        if s.i==j: s.err("expected name")
        return s.t[j:s.i]
    def uint(s):
        s.ws(); j=s.i
        while s.i<len(s.t) and s.t[s.i].isdigit(): s.i+=1
        return int(s.t[j:s.i]) if s.i>j else 0
    def lookup(s,src):
        for d in reversed(s.scope):
            if src in d: return d[src]
        return None
    def term(s):
        c=s.peek()
        if c in ("λ","\\"): return s.lam()
        if c=="*": s.i+=1; return Era()
        if c=="(": return s.app()
        if c=="&": return s.sup()
        if c=="{": return s.sup0()
        if c=="!": return s.dup()
        src=s.name(); u=s.lookup(src)
        return u if u is not None else Var(("free",src))
    def lam(s):
        s.i+=1; src=s.name(); s.eat(".")
        u=fresh(); s.scope.append({src:Var(u)})
        bod=s.term(); s.scope.pop()
        return Lam(u,bod)
    def app(s):
        s.eat("("); f=s.term(); a=s.term(); s.eat(")"); return App(f,a)
    def sup(s):
        s.eat("&"); lab=s.uint(); s.eat("{")
        l=s.term(); s.eat(","); r=s.term(); s.eat("}"); return Sup(lab,l,r)
    def sup0(s):
        s.eat("{"); l=s.term(); s.eat(","); r=s.term(); s.eat("}"); return Sup(0,l,r)
    def dup(s):
        s.eat("!"); lab=0
        if s.peek()=="&": s.eat("&"); lab=s.uint()
        s.eat("{"); a=s.name(); s.eat(","); b=s.name(); s.eat("}"); s.eat("=")
        val=s.term(); s.eat(";")                 # val in OUTER scope
        node=DupNode(lab, val)
        s.scope.append({a:Dp(node,0), b:Dp(node,1)})   # projections bound in body
        bod=s.term(); s.scope.pop()
        return bod                                # the dup floats; body IS the term
def parse(txt):
    p=P(txt); t=p.term(); p.ws()
    if p.i!=len(txt): p.err("trailing input")
    return t

# ----------------------------------------------------------------------------
# Stringifier (canonical: names a,b,c... in encounter order)
# ----------------------------------------------------------------------------
def show(term):
    names={}; counter=[0]
    def nm(u):
        if u not in names:
            i=counter[0]; counter[0]+=1
            names[u]=chr(ord('a')+i) if i<26 else f"v{i}"
        return names[u]
    def go(t):
        if isinstance(t,Var):
            if isinstance(t.nam,tuple) and t.nam[0]=="free": return t.nam[1]
            return nm(t.nam)
        if isinstance(t,Era): return "*"
        if isinstance(t,Lam): return f"λ{nm(t.nam)}.{go(t.bod)}"
        if isinstance(t,App): return f"({go(t.fun)} {go(t.arg)})"
        if isinstance(t,Sup): return f"&{t.lab}{{{go(t.lft)},{go(t.rgt)}}}"
        if isinstance(t,Dp):  return f"DP{t.side}"   # should not survive normalization
        return "?"
    return go(term)

def run(txt):
    reset_runtime()
    nf=normal(parse(txt))
    return show(nf), sum(ctr.values()), dict(ctr)

# ----------------------------------------------------------------------------
# Self-test: equivalence with ic_ref where ic_ref terminates, plus the cases
# ic_ref diverges on (which this representation handles).   run: python3 ic_float.py
# ----------------------------------------------------------------------------
if __name__ == "__main__":
    import ic_ref
    NOT='λp.λt.λf.((p f) t)'; TRUE='λa.λb.a'; FALSE='λa.λb.b'
    _LAB=[1000]
    def _ch(n):
        if n==0: return 'λf.λx.x'
        if n==1: return 'λf.λx.(f x)'
        cs=[f'c{i}' for i in range(n)]; src=[]; cur='f'
        for i in range(n-1):
            _LAB[0]+=1; L=_LAB[0]; nxt=f't{i}' if i<n-2 else cs[-1]
            src.append(f'!&{L}{{{cs[i]},{nxt}}}={cur};'); cur=nxt
        body='x'
        for c in reversed(cs): body=f'({c} {body})'
        return 'λf.λx.'+''.join(src)+body

    # 1) equivalence sweep -- ic_float and ic_ref must agree where ic_ref terminates
    eq_terms=[
        '(λx.λt.(t x) λy.y)',
        '(λb.λt.λf.((b f) t) λT.λF.T)',
        '!{a,b} = {λx.x,λy.y}; (a b)',
        '({λx.x,λy.y} λz.z)',
        '((λf.λx.!{f0,f1}=f;(f0 (f1 x)) λB.λT.λF.((B F) T)) λa.λb.a)',
    ]
    for n in range(7): eq_terms.append(f'(({_ch(n)} S) Z)')
    for a,b in [(2,2),(3,2),(2,3),(2,4),(3,3),(4,2),(2,5)]:
        _LAB[0]=1000; eq_terms.append(f'(({_ch(a)} {_ch(b)}) S)')
    for n in [2,3,4,5]:
        _LAB[0]=1000; eq_terms.append(f'((({_ch(n)} {NOT}) {TRUE}) X)')
    fails=0
    for t in eq_terms:
        r1,_,_=ic_ref.run(t); r2,_,_=run(t)
        if r1!=r2: fails+=1; print(f"  DISAGREE on {t[:40]!r}: ref={r1} float={r2}")
    print(f"equivalence sweep: {len(eq_terms)} terms, {'ALL AGREE' if fails==0 else str(fails)+' DISAGREE'}")

    # 2) the divergent pattern: ic_ref must diverge, ic_float must terminate correctly
    C2='λf.λx.!&1001{f0,f1}=f;(f0 (f1 x))'
    C3='λf.λx.!&1001{a,p}=f;!&1002{b,c}=p;(a (b (c x)))'
    pair2=f'λs.((s ((na {NOT}) {FALSE})) ((nb {NOT}) {TRUE}))'
    pair3=f'λs.((s ((na {NOT}) {FALSE})) ((nb {NOT}) {FALSE}))'
    div_cases=[
        (f'!&8{{na,nb}}={C2}; ((((na {NOT}) {FALSE}) A) B)', 'B'),
        (f'!&8{{na,nb}}={C2}; ({pair2} λp.λq.p)', 'λa.λb.b'),
        (f'!&8{{na,nb}}={C2}; ({pair2} λp.λq.q)', 'λa.λb.a'),
        (f'!&8{{na,nb}}={C3}; ({pair3} λp.λq.p)', 'λa.λb.a'),
    ]
    dok=0
    for t,exp in div_cases:
        ref_div=False
        try: ic_ref.run(t)
        except (RuntimeError,RecursionError): ref_div=True
        try: got,_,_=run(t)
        except Exception as e: got=f'ERR:{type(e).__name__}'
        ok = ref_div and got==exp
        dok += ok
        print(f"  ref={'DIVERGES' if ref_div else 'terminates'}  float={got:8} exp={exp:8} {'OK' if ok else 'FAIL'}")
    print(f"divergent-pattern cases: {dok}/{len(div_cases)} show ref-diverges & float-correct")
