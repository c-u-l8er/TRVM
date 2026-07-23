"""
dist_ic.py -- a coordination-free DISTRIBUTED reducer for the IC32 interaction
calculus (the model ic32.c / ic_float.py implement).

The claim being demonstrated
----------------------------
Interaction-calculus reduction is confluent by construction. Confluence means the
result is independent of the order in which redexes fire. So a single term's heap
can be SHARDED across nodes and reduced with NO locks and NO consensus: each
interaction is performed by the node that *owns* its principal node, dereferencing
across node boundaries on demand. The only thing that must be globally true is
that everyone eventually stops -- and in this demand-driven (call/return) model
termination is structural (the root normalization returns), so even that needs no
separate detector. (The autonomous redex-bag model, where Safra-style termination
detection IS needed, is the harder regime that p2.py handles for combinators.)

What this file proves, empirically, against ic_float as oracle:
  1. Distributed reduction yields the SAME normal form as single-node, for every
     term in the battery (including the ones ic_ref diverges on).
  2. The result is INDEPENDENT of the partition (which node owns which nodes) and
     of the evaluation order (which child of a node is normalized first).
     => coordination-free, exactly as confluence predicts.
  3. Cross-node interaction counts are reported (the communication volume).

Model / fidelity
----------------
Each "node" has its OWN heap (its own dict of slots) -- isolated, as in a real
deployment. A reference is a global (node, addr). Reads/writes dispatch to the
owning node; a cross-node interaction is counted as remote communication. This is
a faithful simulation of the data placement + message structure; running the
nodes as real OS processes (as p2.py does for combinators, and dsearch does with
multiprocessing) is the engineering follow-on, not a change to the semantics.
"""

import sys, random
import ic_float   # oracle

# ----------------------------------------------------------------- terms
class T:
    __slots__=("tag","lab","ref")
    def __init__(s, tag, lab=0, ref=None): s.tag=tag; s.lab=lab; s.ref=ref
def ERA(): return T("ERA")
def is_sub(x): return isinstance(x, tuple) and x[0]=="SUB"
def sub_val(x): return x[1]

# ----------------------------------------------------------------- the net
class Net:
    def __init__(s, nworkers):
        s.W=nworkers
        s.heaps=[dict() for _ in range(nworkers)]
        s.next=[1]*nworkers
        s.units=[[] for _ in range(nworkers)]   # (base,size) allocation units per node
        s.inter=0
        s.remote=0
        s.child_order="lr"                       # 'lr' or 'rl' (evaluation-order knob)
    def alloc(s, node, n=1):
        a=s.next[node]; s.next[node]+=n
        s.units[node].append((a,n))
        return (node,a)
    def read(s, ref):  return s.heaps[ref[0]][ref[1]]
    def write(s, ref, val): s.heaps[ref[0]][ref[1]]=val
    def off(s, ref, k): return (ref[0], ref[1]+k)

# ----------------------------------------------------------------- interactions
def fire(net, dref, L, k):
    net.inter+=1
    dn=dref[0]
    v=whnf(net, net.read(dref))
    if v.ref is not None and v.tag in ("LAM","APP","SUP") and v.ref[0]!=dn:
        net.remote+=1
    if v.tag=="SUP":
        a=net.read(v.ref); b=net.read(net.off(v.ref,1))
        if v.lab==L:
            h0,h1=a,b
        else:
            Da=net.alloc(dn); net.write(Da,a)
            Db=net.alloc(dn); net.write(Db,b)
            S0=net.alloc(dn,2); net.write(S0,T("DP0",L,Da)); net.write(net.off(S0,1),T("DP0",L,Db))
            S1=net.alloc(dn,2); net.write(S1,T("DP1",L,Da)); net.write(net.off(S1,1),T("DP1",L,Db))
            h0=T("SUP",v.lab,S0); h1=T("SUP",v.lab,S1)
    elif v.tag=="LAM":
        Lv=v.ref
        Lx0=net.alloc(dn); Lx1=net.alloc(dn)
        Df=net.alloc(dn); net.write(Df, net.read(Lv))
        net.write(Lx0,T("DP0",L,Df)); net.write(Lx1,T("DP1",L,Df))
        Ss=net.alloc(dn,2); net.write(Ss,T("VAR",0,Lx0)); net.write(net.off(Ss,1),T("VAR",0,Lx1))
        net.write(Lv, ("SUB", T("SUP",L,Ss)))
        h0=T("LAM",0,Lx0); h1=T("LAM",0,Lx1)
    elif v.tag=="ERA":
        h0=ERA(); h1=ERA()
    elif v.tag=="APP":
        A=v.ref; f=net.read(A); a=net.read(net.off(A,1))
        Df=net.alloc(dn); net.write(Df,f); Dx=net.alloc(dn); net.write(Dx,a)
        A0=net.alloc(dn,2); net.write(A0,T("DP0",L,Df)); net.write(net.off(A0,1),T("DP0",L,Dx))
        A1=net.alloc(dn,2); net.write(A1,T("DP1",L,Df)); net.write(net.off(A1,1),T("DP1",L,Dx))
        h0=T("APP",0,A0); h1=T("APP",0,A1)
    else:   # VAR free / stuck
        h0=v; h1=v
    if k==0: net.write(dref, ("SUB",h1)); return h0
    else:    net.write(dref, ("SUB",h0)); return h1

def app_sup(net, sup, arg, an):
    net.inter+=1
    L=sup.lab
    a=net.read(sup.ref); b=net.read(net.off(sup.ref,1))
    Dc=net.alloc(an); net.write(Dc,arg)
    Aa=net.alloc(an,2); net.write(Aa,a); net.write(net.off(Aa,1),T("DP0",L,Dc))
    Ab=net.alloc(an,2); net.write(Ab,b); net.write(net.off(Ab,1),T("DP1",L,Dc))
    Sn=net.alloc(an,2); net.write(Sn,T("APP",0,Aa)); net.write(net.off(Sn,1),T("APP",0,Ab))
    return T("SUP",L,Sn)

def whnf(net, t):
    while True:
        if t.tag=="VAR":
            w=net.read(t.ref)
            if is_sub(w): t=sub_val(w); continue
            return t
        if t.tag in ("DP0","DP1"):
            w=net.read(t.ref)
            if is_sub(w): t=sub_val(w); continue
            t=fire(net, t.ref, t.lab, 0 if t.tag=="DP0" else 1); continue
        if t.tag=="APP":
            an=t.ref[0]
            f=whnf(net, net.read(t.ref))
            if f.tag=="LAM":
                net.inter+=1
                if f.ref[0]!=an: net.remote+=1
                arg=net.read(net.off(t.ref,1))
                body=net.read(f.ref)
                net.write(f.ref, ("SUB",arg))
                t=body; continue
            if f.tag=="SUP":
                if f.ref[0]!=an: net.remote+=1
                t=app_sup(net, f, net.read(net.off(t.ref,1)), an); continue
            if f.tag=="ERA":
                net.inter+=1; t=ERA(); continue
            net.write(t.ref, f)     # stuck: memoize reduced fun
            return t
        return t   # LAM, SUP, ERA

def normal(net, t):
    t=whnf(net, t)
    if t.tag=="LAM":
        net.write(t.ref, normal(net, net.read(t.ref))); return t
    if t.tag=="APP":
        r0=t.ref; r1=net.off(t.ref,1)
        if net.child_order=="lr":
            net.write(r0, normal(net, net.read(r0))); net.write(r1, normal(net, net.read(r1)))
        else:
            net.write(r1, normal(net, net.read(r1))); net.write(r0, normal(net, net.read(r0)))
        return t
    if t.tag=="SUP":
        r0=t.ref; r1=net.off(t.ref,1)
        if net.child_order=="lr":
            net.write(r0, normal(net, net.read(r0))); net.write(r1, normal(net, net.read(r1)))
        else:
            net.write(r1, normal(net, net.read(r1))); net.write(r0, normal(net, net.read(r0)))
        return t
    return t

# ----------------------------------------------------------------- parser (onto node 0)
class P:
    def __init__(s, net, txt): s.net=net; s.t=txt; s.i=0; s.scope=[]; s.freelocs={}; s.freenm={}
    def ws(s):
        while s.i<len(s.t) and s.t[s.i] in " \t\n\r": s.i+=1
    def isl(s): return s.t[s.i:s.i+1] in ("\\","λ")
    def eatl(s): s.i+=1   # both '\\' and 'λ' are one char
    def err(s,m): raise SyntaxError(f"{m} at {s.i}: ...{s.t[s.i:s.i+20]!r}")
    def expect(s,c):
        s.ws()
        if s.t[s.i:s.i+1]!=c: s.err(f"expected {c!r}")
        s.i+=1
    def name(s):
        s.ws(); j=s.i
        while s.i<len(s.t) and (s.t[s.i].isalnum() or s.t[s.i]=="_"): s.i+=1
        if s.i==j: s.err("name"); 
        return s.t[j:s.i]
    def uint(s):
        s.ws(); j=s.i
        while s.i<len(s.t) and s.t[s.i].isdigit(): s.i+=1
        return int(s.t[j:s.i]) if s.i>j else 0
    def freeref(s, nm):
        if nm in s.freelocs: return s.freelocs[nm]
        ref=s.net.alloc(0); s.net.write(ref, ERA()); s.freelocs[nm]=ref; s.freenm[ref]=nm
        return ref
    def term(s):
        s.ws(); c=s.t[s.i:s.i+1]
        if s.isl():
            s.eatl(); nm=s.name(); s.expect(".")
            ref=s.net.alloc(0)
            s.scope.append((nm, T("VAR",0,ref)))
            bod=s.term(); s.scope.pop()
            s.net.write(ref, bod)
            return T("LAM",0,ref)
        if c=="*": s.i+=1; return ERA()
        if c=="(":
            s.i+=1; f=s.term(); a=s.term(); s.expect(")")
            ref=s.net.alloc(0,2); s.net.write(ref,f); s.net.write(s.net.off(ref,1),a)
            return T("APP",0,ref)
        if c=="&":
            s.i+=1; lab=s.uint(); s.expect("{"); l=s.term(); s.expect(","); r=s.term(); s.expect("}")
            ref=s.net.alloc(0,2); s.net.write(ref,l); s.net.write(s.net.off(ref,1),r)
            return T("SUP",lab,ref)
        if c=="{":
            s.i+=1; l=s.term(); s.expect(","); r=s.term(); s.expect("}")
            ref=s.net.alloc(0,2); s.net.write(ref,l); s.net.write(s.net.off(ref,1),r)
            return T("SUP",0,ref)
        if c=="!":
            s.i+=1; lab=0; s.ws()
            if s.t[s.i:s.i+1]=="&": s.i+=1; lab=s.uint()
            s.expect("{"); a=s.name(); s.expect(","); b=s.name(); s.expect("}"); s.expect("=")
            dref=s.net.alloc(0)
            val=s.term(); s.net.write(dref,val); s.expect(";")
            s.scope.append((a, T("DP0",lab,dref))); s.scope.append((b, T("DP1",lab,dref)))
            bod=s.term(); s.scope.pop(); s.scope.pop()
            return bod
        nm=s.name()
        for (n,t) in reversed(s.scope):
            if n==nm: return t
        return T("VAR",0,s.freeref(nm))

def parse(net, txt):
    p=P(net, txt); t=p.term(); p.ws()
    if p.i!=len(txt): p.err("trailing")
    return t, p.freenm

# ----------------------------------------------------------------- stringify
def show(net, t, freenm):
    names={}; ctr=[0]
    def nm(ref):
        if ref in freenm: return freenm[ref]
        if ref not in names:
            i=ctr[0]; ctr[0]+=1
            names[ref]=chr(ord('a')+i) if i<26 else f"v{i}"
        return names[ref]
    def go(t):
        if t.tag=="VAR": return nm(t.ref)
        if t.tag=="ERA": return "*"
        if t.tag=="LAM": return f"λ{nm(t.ref)}.{go(net.read(t.ref))}"
        if t.tag=="APP": return f"({go(net.read(t.ref))} {go(net.read(net.off(t.ref,1)))})"
        if t.tag=="SUP": return f"&{t.lab}{{{go(net.read(t.ref))},{go(net.read(net.off(t.ref,1)))}}}"
        if t.tag in ("DP0","DP1"): return t.tag
        return "?"
    return go(t)

# ----------------------------------------------------------------- scatter (partition across workers)
def remap_term(t, remap):
    if t.ref is None: return t
    base=(t.ref[0], t.ref[1])
    if base in remap: return T(t.tag, t.lab, remap[base])
    return t
def scatter(net, assign):
    """Relocate every node-0 allocation unit to a worker chosen by assign(idx).
       Preserves the graph exactly (all refs remapped). Returns remap fn for roots."""
    units=list(net.units[0])
    old=net.heaps[0]
    remap={}
    # 1st pass: assign new homes (contiguous per unit)
    newheaps=[dict() for _ in range(net.W)]
    newnext=[1]*net.W
    newunits=[[] for _ in range(net.W)]
    for idx,(base,size) in enumerate(units):
        w=assign(idx) % net.W
        nb=newnext[w]; newnext[w]+=size; newunits[w].append((nb,size))
        for k in range(size): remap[(0,base+k)]=(w,nb+k)
    # 2nd pass: copy contents with refs remapped
    for (base,size) in units:
        for k in range(size):
            src=(0,base+k); dst=remap[src]; content=old[base+k]
            if is_sub(content): content=("SUB", remap_term(sub_val(content), remap))
            else: content=remap_term(content, remap)
            newheaps[dst[0]][dst[1]]=content
    net.heaps=newheaps; net.next=newnext; net.units=newunits
    return lambda ref: remap.get((ref[0],ref[1]), ref)

# ----------------------------------------------------------------- run helpers
def run_single(txt, child_order="lr"):
    net=Net(1); net.child_order=child_order
    root,freenm=parse(net, txt)
    nf=normal(net, root)
    return show(net, nf, freenm), net.inter, net.remote

def run_distributed(txt, W, assign, child_order="lr"):
    net=Net(W); 
    root,freenm=parse(net, txt)
    rm=scatter(net, assign)
    net.child_order=child_order
    root=remap_term(root, {(0,a):rm((0,a)) for (b,sz) in [] for a in []}) if False else (T(root.tag,root.lab,rm(root.ref)) if root.ref else root)
    # remap free-var name table to new locations
    freenm2={rm(ref):nm for ref,nm in freenm.items()}
    nf=normal(net, root)
    return show(net, nf, freenm2), net.inter, net.remote

# ----------------------------------------------------------------- self-test
if __name__=="__main__":
    LAB=[1000]
    def _ch(n):
        if n==0: return 'λf.λx.x'
        if n==1: return 'λf.λx.(f x)'
        cs=[f'c{i}' for i in range(n)]; src=[]; cur='f'
        for i in range(n-1):
            LAB[0]+=1; L=LAB[0]; nxt=f't{i}' if i<n-2 else cs[-1]
            src.append(f'!&{L}{{{cs[i]},{nxt}}}={cur};'); cur=nxt
        body='x'
        for c in reversed(cs): body=f'({c} {body})'
        return 'λf.λx.'+''.join(src)+body
    NOT='λp.λt.λf.((p f) t)'; TRUE='λa.λb.a'; FALSE='λa.λb.b'
    C2='λf.λx.!&1001{f0,f1}=f;(f0 (f1 x))'
    pair2=f'λs.((s ((na {NOT}) {FALSE})) ((nb {NOT}) {TRUE}))'
    battery=['(λx.λt.(t x) λy.y)','({λx.x,λy.y} λz.z)',
             '((λf.λx.!{f0,f1}=f;(f0 (f1 x)) λB.λT.λF.((B F) T)) λa.λb.a)']
    for n in range(6): battery.append(f'(({_ch(n)} S) Z)')
    for a,b in [(2,2),(3,2),(2,3),(3,3),(4,2)]:
        LAB[0]=1000; battery.append(f'(({_ch(a)} {_ch(b)}) S)')
    for n in [2,3,4,5]:
        LAB[0]=1000; battery.append(f'((({_ch(n)} {NOT}) {TRUE}) X)')
    LAB[0]=1000; battery.append(f'!&8{{na,nb}}={C2}; ((((na {NOT}) {FALSE}) A) B)')
    LAB[0]=1000; battery.append(f'!&8{{na,nb}}={C2}; ({pair2} λp.λq.p)')

    import ic_float as ORACLE
    f1=0
    for t in battery:
        o,_,_=ORACLE.run(t); d,_,_=run_single(t)
        if o!=d: f1+=1; print("single mismatch:",t)
    print(f"single-node vs ic_float: {len(battery)} terms, {'ALL MATCH' if f1==0 else str(f1)+' FAIL'}")

    import random
    bad=0; total_conf=0
    for t in battery:
        single,_,_=run_single(t); results={single}
        net0=Net(1); _r,_=parse(net0,t); nu=len(net0.units[0])
        for W in (2,3,4):
            assigns={'rr':(lambda i:i),'blk':(lambda i,nu=nu,W=W:i//max(1,nu//W+1))}
            for sd in range(2):
                rnd=[random.Random(7*W+sd).randrange(W) for _ in range(nu)]
                assigns[f'r{sd}']=(lambda i,rnd=rnd:rnd[i])
            for af in assigns.values():
                for order in ('lr','rl'):
                    r,_,_=run_distributed(t,W,af,child_order=order); results.add(r); total_conf+=1
        if len(results)!=1: bad+=1; print("PARTITION-DEPENDENT:",t,results)
    print(f"distributed invariance: {len(battery)} terms x {total_conf//len(battery)} configs each = {total_conf} runs; "
          f"{'every run == single-node (schedule/partition-independent)' if bad==0 else str(bad)+' DISCREPANCIES'}")
