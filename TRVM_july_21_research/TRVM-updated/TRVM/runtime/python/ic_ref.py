"""
ic_ref.py  --  A reference-faithful Interaction Calculus reducer.

Transcribed directly from the reduction rules + pseudocode in
github.com/VictorTaelin/Interaction-Calculus (the calculus HVM3/HVM4 implement).

Why this file exists
--------------------
Earlier hand-rolled reducers (lc2.py, linet.py) reconstructed the interaction
rules from memory by rewiring ports, and kept hitting a correctness bug when a
*higher-order* term was duplicated (e.g. Church 2 applied to Church 2). The
reference fixes that with two ideas I wasn't using:

  1. SUBSTITUTION IS A GLOBAL MAP, not port rewiring.
     Variables are AFFINE (occur <= 1 time) and globally unique, so a
     substitution `x <- t` is just `sub[x] = t`. No traversal, no name capture.

  2. There is a total rule for EVERY interaction (no stuck/error states),
     including the "collapse" rules DUP-VAR / DUP-APP that copy a free/stuck
     term -- exactly what's needed to duplicate things like a free `S`.

This is the per-node engine. Once it's correct, the coordination-free
distribution layer goes on top (superposed search is the monotone, CALM-friendly
workload). Correctness first.
"""

from dataclasses import dataclass
from typing import Optional

# ----------------------------------------------------------------------------
# Term representation
# ----------------------------------------------------------------------------
# We use the simple "body-carrying" representation from the spec's pseudocode
# (Dup carries its body), with named variables resolved through a global `sub`
# map. Names are globally unique integers produced by fresh().

@dataclass
class Var:  __slots__=("nam"); nam: int
@dataclass
class Era:  pass
@dataclass
class Lam:  __slots__=("nam","bod"); nam: int; bod: object
@dataclass
class App:  __slots__=("fun","arg"); fun: object; arg: object
@dataclass
class Sup:  __slots__=("lab","lft","rgt"); lab: int; lft: object; rgt: object
@dataclass
class Dup:  __slots__=("lab","lft","rgt","val","bod"); lab:int; lft:int; rgt:int; val:object; bod:object

# Make the slotted dataclasses actually work (dataclass+__slots__ needs care):
for _c in (Var,Lam,App,Sup,Dup):
    pass

# ----------------------------------------------------------------------------
# Global state
# ----------------------------------------------------------------------------
sub = {}            # name(int) -> Term      (the global substitution map)
_fresh = [0]
def fresh():
    _fresh[0]+=1
    return _fresh[0]

# interaction counters, by rule
ctr = {}
def bump(rule):
    ctr[rule]=ctr.get(rule,0)+1

def reset_runtime():
    sub.clear()
    for k in list(ctr): ctr[k]=0

# ----------------------------------------------------------------------------
# Interaction rules  (one-to-one with the spec pseudocode)
# ----------------------------------------------------------------------------
def app_lam(app, lam):
    bump("APP-LAM")
    sub[lam.nam] = app.arg
    return lam.bod

def app_sup(app, sup):
    # (&L{a,b} c)  -->  !&L{c0,c1}=c; &L{(a c0),(b c1)}
    bump("APP-SUP")
    x0,x1 = fresh(),fresh()
    return Dup(sup.lab, x0, x1, app.arg,
               Sup(sup.lab, App(sup.lft, Var(x0)), App(sup.rgt, Var(x1))))

def app_era(app, era):
    bump("APP-ERA")
    return Era()

def dup_lam(dup, lam):
    # !&L{r,s}=λx.f; K  -->  r<-λx0.f0 ; s<-λx1.f1 ; x<-&L{x0,x1} ; !&L{f0,f1}=f; K
    bump("DUP-LAM")
    x0,x1,f0,f1 = fresh(),fresh(),fresh(),fresh()
    sub[dup.lft] = Lam(x0, Var(f0))
    sub[dup.rgt] = Lam(x1, Var(f1))
    sub[lam.nam] = Sup(dup.lab, Var(x0), Var(x1))
    return Dup(dup.lab, f0, f1, lam.bod, dup.bod)

def dup_sup(dup, sup):
    if dup.lab == sup.lab:
        # equal labels: pair projection (annihilation)
        bump("DUP-SUP=")
        sub[dup.lft] = sup.lft
        sub[dup.rgt] = sup.rgt
        return dup.bod
    else:
        # different labels: commute
        bump("DUP-SUP!")
        a0,a1,b0,b1 = fresh(),fresh(),fresh(),fresh()
        sub[dup.lft] = Sup(sup.lab, Var(a0), Var(b0))
        sub[dup.rgt] = Sup(sup.lab, Var(a1), Var(b1))
        return Dup(dup.lab, a0, a1, sup.lft,
               Dup(dup.lab, b0, b1, sup.rgt, dup.bod))

def dup_era(dup, era):
    bump("DUP-ERA")
    sub[dup.lft] = Era()
    sub[dup.rgt] = Era()
    return dup.bod

# --- collapse rules: duplicating a free var / stuck application / number ------
def dup_var(dup, var):
    # !&L{x0,x1}=x; K  -->  x0<-x ; x1<-x ; K     (copy a free variable)
    bump("DUP-VAR")
    sub[dup.lft] = var
    sub[dup.rgt] = var
    return dup.bod

def dup_app(dup, app):
    # !&L{a0,a1}=(f x); K  -->  a0<-(f0 x0); a1<-(f1 x1); !&L{f0,f1}=f; !&L{x0,x1}=x; K
    bump("DUP-APP")
    f0,f1,x0,x1 = fresh(),fresh(),fresh(),fresh()
    sub[dup.lft] = App(Var(f0), Var(x0))
    sub[dup.rgt] = App(Var(f1), Var(x1))
    return Dup(dup.lab, f0, f1, app.fun,
           Dup(dup.lab, x0, x1, app.arg, dup.bod))

# ----------------------------------------------------------------------------
# Reduction drivers
# ----------------------------------------------------------------------------
WHNF_STEPS = [10**9]
def whnf(term):
    """Reduce to weak head normal form."""
    while True:
        WHNF_STEPS[0]-=1
        if WHNF_STEPS[0]<=0:
            raise RuntimeError("whnf: step budget exhausted (probable non-termination)")
        if isinstance(term, Var):
            if term.nam in sub:
                term = sub[term.nam]
                continue
            return term
        if isinstance(term, App):
            fun = whnf(term.fun)
            if isinstance(fun, Lam):
                term = app_lam(term, fun); continue
            if isinstance(fun, Sup):
                term = app_sup(term, fun); continue
            if isinstance(fun, Era):
                term = app_era(term, fun); continue
            return App(fun, term.arg)        # stuck application
        if isinstance(term, Dup):
            val = whnf(term.val)
            if isinstance(val, Lam):
                term = dup_lam(term, val); continue
            if isinstance(val, Sup):
                term = dup_sup(term, val); continue
            if isinstance(val, Era):
                term = dup_era(term, val); continue
            if isinstance(val, Var):
                term = dup_var(term, val); continue
            if isinstance(val, App):
                term = dup_app(term, val); continue
            # numbers etc. would copy here; fall through
            term = dup_var(term, val); continue
        return term     # Lam, Sup, Era

# guard against runaway loops in tests
NORMAL_BUDGET = [0]
def normal(term, budget=2_000_000):
    NORMAL_BUDGET[0]=budget
    WHNF_STEPS[0]=budget
    return _normal(term)

def _normal(term):
    NORMAL_BUDGET[0]-=1
    if NORMAL_BUDGET[0]<=0:
        raise RuntimeError("normal: budget exhausted (probable non-termination)")
    term = whnf(term)
    if isinstance(term, Lam):
        return Lam(term.nam, _normal(term.bod))
    if isinstance(term, App):
        return App(_normal(term.fun), _normal(term.arg))
    if isinstance(term, Sup):
        return Sup(term.lab, _normal(term.lft), _normal(term.rgt))
    if isinstance(term, Dup):   # stuck dup leftover (open terms)
        return Dup(term.lab, term.lft, term.rgt, _normal(term.val), _normal(term.bod))
    return term

# ----------------------------------------------------------------------------
# Parser  (lexical alpha-renaming to globally-unique names)
# ----------------------------------------------------------------------------
class P:
    def __init__(s, txt):
        s.t=txt; s.i=0
        s.scope=[]          # list of dicts: source-name -> unique int
    def err(s,msg): raise SyntaxError(f"{msg} at {s.i}: ...{s.t[s.i:s.i+20]!r}")
    def ws(s):
        while s.i<len(s.t) and s.t[s.i] in " \t\n\r": s.i+=1
    def peek(s):
        s.ws(); return s.t[s.i] if s.i<len(s.t) else ""
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
    # scope helpers
    def bind(s, src):
        u=fresh(); s.scope.append({src:u}); return u
    def bind_into(s, d): s.scope.append(d)
    def pop(s): s.scope.pop()
    def lookup(s, src):
        for d in reversed(s.scope):
            if src in d: return d[src]
        return None     # free / global

    def term(s):
        c=s.peek()
        if c in ("λ","\\"):      return s.lam()
        if c=="*":  s.i+=1;      return Era()
        if c=="(":               return s.app()
        if c=="&":               return s.sup()
        if c=="{":               return s.sup0()
        if c=="!":               return s.dup()
        # variable
        src=s.name()
        u=s.lookup(src)
        return Var(u) if u is not None else Var(("free",src))
    def lam(s):
        s.i+=1               # consume λ or backslash
        src=s.name(); s.eat(".")
        u=s.bind(src)
        bod=s.term(); s.pop()
        return Lam(u, bod)
    def app(s):
        s.eat("("); f=s.term(); a=s.term(); s.eat(")")
        return App(f,a)
    def sup(s):
        s.eat("&"); lab=s.uint(); s.eat("{")
        l=s.term(); s.eat(","); r=s.term(); s.eat("}")
        return Sup(lab,l,r)
    def sup0(s):
        s.eat("{"); l=s.term(); s.eat(","); r=s.term(); s.eat("}")
        return Sup(0,l,r)
    def dup(s):
        s.eat("!")
        lab=0
        if s.peek()=="&": s.eat("&"); lab=s.uint()
        s.eat("{"); a=s.name(); s.eat(","); b=s.name(); s.eat("}")
        s.eat("=")
        val=s.term()                       # val is in the OUTER scope
        s.eat(";")
        ua,ub=fresh(),fresh()
        s.bind_into({a:ua, b:ub})          # a,b scope over the body
        bod=s.term(); s.pop()
        return Dup(lab, ua, ub, val, bod)

def parse(txt):
    p=P(txt); t=p.term(); p.ws()
    if p.i!=len(txt): p.err("trailing input")
    return t

# ----------------------------------------------------------------------------
# Stringifier  (assign pretty names per binder, dups float to the top)
# ----------------------------------------------------------------------------
def show(term):
    names={}
    counter=[0]
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
        if isinstance(t,Dup):
            return f"!&{t.lab}{{{nm(t.lft)},{nm(t.rgt)}}}={go(t.val)};{go(t.bod)}"
        return "?"
    return go(term)

# ----------------------------------------------------------------------------
# Helpers for tests
# ----------------------------------------------------------------------------
def run(txt):
    """Parse, normalize, return (string, total_interactions, counters)."""
    reset_runtime()
    t=parse(txt)
    nf=normal(t)
    s=show(nf)
    total=sum(ctr.values())
    return s, total, dict(ctr)

def church_int(numeral_src):
    """Apply a Church numeral to free S and Z, normalize, count S's."""
    reset_runtime()
    t=parse(f"(({numeral_src} S) Z)")
    nf=normal(t)
    # walk: (S (S (... Z)))
    n=0; cur=nf
    while isinstance(cur,App) and isinstance(cur.fun,Var) and cur.fun.nam==("free","S"):
        n+=1; cur=cur.arg
    ok = isinstance(cur,Var) and cur.nam==("free","Z")
    return (n if ok else None), show(nf), sum(ctr.values())

# ----------------------------------------------------------------------------
# Self-test  (run: python3 ic_ref.py)
# ----------------------------------------------------------------------------
if __name__ == "__main__":
    _LAB=[100]
    def _lab():
        _LAB[0]+=1; return _LAB[0]
    def _church(n):
        if n==0: return 'λf.λx.x'
        if n==1: return 'λf.λx.(f x)'
        cs=[f'c{i}' for i in range(n)]; src=[]; cur='f'
        for i in range(n-1):
            L=_lab(); nxt = f't{i}' if i< n-2 else cs[-1]
            src.append(f'!&{L}{{{cs[i]},{nxt}}}={cur};'); cur=nxt
        body='x'
        for c in reversed(cs): body=f'({c} {body})'
        return 'λf.λx.'+''.join(src)+body
    def _as_int(src):
        reset_runtime(); nf=normal(parse(f'(({src} S) Z)'))
        n=0; cur=nf
        while isinstance(cur,App) and isinstance(cur.fun,Var) and cur.fun.nam==('free','S'):
            n+=1; cur=cur.arg
        return n if (isinstance(cur,Var) and cur.nam==('free','Z')) else None

    fails=0
    # Ex5: the reference's own "tests all interactions" term
    s,tot,_=run('((λf.λx.!{f0,f1}=f;(f0 (f1 x)) λB.λT.λF.((B F) T)) λa.λb.a)')
    assert tot==16, f"Ex5 interaction count {tot} != 16"; print(f"Ex5 default test term: {s} in {tot} interactions  OK")
    # Church arithmetic + exponentiation (higher-order duplication)
    for n in range(7):
        _LAB[0]=100
        if _as_int(_church(n))!=n: fails+=1; print(f"  church({n}) FAIL")
    for a,b in [(2,2),(3,2),(2,3),(2,4),(3,3),(4,2)]:
        _LAB[0]=100
        got=_as_int(f'({_church(a)} {_church(b)})')
        if got!=b**a: fails+=1; print(f"  ({a} {b}) -> {got} != {b**a} FAIL")
    print("ALL CHURCH/EXP TESTS PASS" if fails==0 else f"{fails} FAILURES")
