"""
lc2.py - tagged interaction-net lambda evaluator (HVM2-style rules) + Church arithmetic.
Agents: LAM(var,body) APP(arg,ret) FAN[L](o0,o1) SUC(pred) ZERO ERA. Principal = port 0.
Rules (principal~principal): APP~LAM beta; FAN~LAM dup-lambda; APP~FAN app-sup;
FAN~FAN annihilate(same label)/commute(diff); FAN~SUC & FAN~ZERO copy; ERA~x erase.
Each numeral gets a FRESH fan label so distinct duplicators don't wrongly annihilate.
"""
import itertools
_ac = itertools.count()
class Port:
    __slots__=("agent","idx","link","flabel")
    def __init__(s,a,i): s.agent=a; s.idx=i; s.link=None; s.flabel=None
class Agent:
    __slots__=("kind","label","ports","aid","dead")
    AR={"LAM":3,"APP":3,"FAN":3,"SUC":2,"ZERO":1,"ERA":1}
    def __init__(s,kind,label=None):
        s.kind=kind; s.label=label; s.aid=next(_ac); s.dead=False
        s.ports=[Port(s,i) for i in range(s.AR[kind])]
    @property
    def principal(s): return s.ports[0]
def link(p,q):
    if p is not None: p.link=q
    if q is not None: q.link=p
def fp(l): p=Port(None,-1); p.flabel=l; return p
class Net:
    def __init__(s): s.agents=[]; s.free=[]
    def add(s,a): s.agents.append(a); return a

def active(net):
    seen=set(); out=[]
    for a in net.agents:
        if a.dead: continue
        q=a.principal.link
        if q is not None and q.agent is not None and not q.agent.dead and q.idx==0 and a.aid!=q.agent.aid:
            k=frozenset((a.aid,q.agent.aid))
            if k not in seen: seen.add(k); out.append((a,q.agent))
    return out

def N(net,k,l=None): return net.add(Agent(k,l))

def rewrite(net,a,b):
    ka,kb=a.kind,b.kind; ks={ka,kb}
    def kill(*xs):
        for x in xs: x.dead=True
    if "ERA" in ks:
        e,o=(a,b) if ka=="ERA" else (b,a); kill(e,o)
        for i in range(1,len(o.ports)): link(N(net,"ERA").principal,o.ports[i].link)
        return
    if ks=={"APP","LAM"}:
        ap,la=(a,b) if ka=="APP" else (b,a)
        link(ap.ports[1].link, la.ports[1].link); link(ap.ports[2].link, la.ports[2].link); kill(ap,la); return
    if ks=={"FAN","LAM"}:
        f,la=(a,b) if ka=="FAN" else (b,a)
        fo0,fo1=f.ports[1].link,f.ports[2].link; lv,lb=la.ports[1].link,la.ports[2].link; L=f.label; kill(f,la)
        L0=N(net,"LAM"); L1=N(net,"LAM"); Fb=N(net,"FAN",L); Fv=N(net,"FAN",L)
        link(L0.principal,fo0); link(L1.principal,fo1)
        link(Fb.principal,lb); link(L0.ports[2],Fb.ports[1]); link(L1.ports[2],Fb.ports[2])
        link(Fv.principal,lv); link(L0.ports[1],Fv.ports[1]); link(L1.ports[1],Fv.ports[2]); return
    if ks=={"APP","FAN"}:
        ap,f=(a,b) if ka=="APP" else (b,a)
        ar,rt=ap.ports[1].link,ap.ports[2].link; f0,f1=f.ports[1].link,f.ports[2].link; L=f.label; kill(ap,f)
        A0=N(net,"APP"); A1=N(net,"APP"); Fa=N(net,"FAN",L); Fr=N(net,"FAN",L)
        link(A0.principal,f0); link(A1.principal,f1)
        link(Fa.principal,ar); link(A0.ports[1],Fa.ports[1]); link(A1.ports[1],Fa.ports[2])
        link(Fr.principal,rt); link(A0.ports[2],Fr.ports[1]); link(A1.ports[2],Fr.ports[2]); return
    if ka=="FAN" and kb=="FAN":
        if a.label==b.label:
            link(a.ports[1].link,b.ports[1].link); link(a.ports[2].link,b.ports[2].link); kill(a,b); return
        a1,a2=a.ports[1].link,a.ports[2].link; b1,b2=b.ports[1].link,b.ports[2].link; la,lb=a.label,b.label; kill(a,b)
        B1=N(net,"FAN",lb); B2=N(net,"FAN",lb); A1=N(net,"FAN",la); A2=N(net,"FAN",la)
        link(B1.principal,a1); link(B2.principal,a2); link(A1.principal,b1); link(A2.principal,b2)
        link(B1.ports[1],A1.ports[1]); link(B1.ports[2],A2.ports[1]); link(B2.ports[1],A1.ports[2]); link(B2.ports[2],A2.ports[2]); return
    if "SUC" in ks and "FAN" in ks:
        s,f=(a,b) if ka=="SUC" else (b,a)
        fo0,fo1=f.ports[1].link,f.ports[2].link; sp=s.ports[1].link; L=f.label; kill(s,f)
        S0=N(net,"SUC"); S1=N(net,"SUC"); Fp=N(net,"FAN",L)
        link(S0.principal,fo0); link(S1.principal,fo1); link(Fp.principal,sp)
        link(S0.ports[1],Fp.ports[1]); link(S1.ports[1],Fp.ports[2]); return
    if "ZERO" in ks and "FAN" in ks:
        z,f=(a,b) if ka=="ZERO" else (b,a)
        fo0,fo1=f.ports[1].link,f.ports[2].link; kill(z,f)
        link(N(net,"ZERO").principal,fo0); link(N(net,"ZERO").principal,fo1); return
    raise Exception(f"no rule: {ka}~{kb}")

def reduce(net,cap=200000):
    n=0
    while n<cap:
        ap=active(net)
        if not ap: break
        rewrite(net,*ap[0]); n+=1
    net.agents=[a for a in net.agents if not a.dead]
    return n

# ---- compiler ----
def Var(n): return ('var',n)
def Lam(n,b): return ('lam',n,b)
def App(f,a): return ('app',f,a)
Suc=lambda t:('suc',t); Zero=('zero',)
def church(k):
    body=Var('x')
    for _ in range(k): body=App(Var('f'),body)
    return Lam('f',Lam('x',body))

def compile(term):
    net=Net(); lbl=itertools.count(1)
    def go(t,env):
        if t[0]=='var': p=fp(t[1]); env.setdefault(t[1],[]).append(p); return p
        if t[0]=='zero': return N(net,"ZERO").principal
        if t[0]=='suc':
            s=N(net,"SUC"); link(s.ports[1],go(t[1],env)); return s.principal
        if t[0]=='lam':
            _,nm,bd=t; la=N(net,"LAM"); inner=dict(env); inner[nm]=[]
            link(la.ports[2],go(bd,inner))
            uses=[p.link for p in inner[nm]]; bnd=la.ports[1]
            if len(uses)==0: link(bnd,N(net,"ERA").principal)
            elif len(uses)==1: link(bnd,uses[0])
            else:
                L=next(lbl); leaves=[bnd]
                while len(leaves)<len(uses):
                    q=leaves.pop(); d=N(net,"FAN",L); link(d.principal,q); leaves+=[d.ports[1],d.ports[2]]
                for lf,u in zip(leaves,uses): link(lf,u)
            for kk,vv in inner.items():
                if kk!=nm:
                    for p in vv:
                        if p not in env.get(kk,[]): env.setdefault(kk,[]).append(p)
            return la.principal
        _,f,a=t; ap=N(net,"APP"); link(ap.ports[0],go(f,env)); link(ap.ports[1],go(a,env)); return ap.ports[2]
    r=go(term,{}); o=fp("R"); link(o,r); net.free=[o]; return net

def decode(net):
    o=[f for f in net.free if f.flabel=="R"][0]; p=o.link; c=0
    while p is not None and p.agent is not None:
        if p.agent.kind=="SUC": c+=1; p=p.agent.ports[1].link
        elif p.agent.kind=="ZERO": return c
        else: return f"<non-nat: {p.agent.kind}>"
    return "<dangling>"

S=Lam('n',Suc(Var('n')))
for name,term,exp in [("S Z",App(S,Zero),1),
                      ("2 S Z",App(App(church(2),S),Zero),2),
                      ("3 S Z",App(App(church(3),S),Zero),3),
                      ("2 2 S Z",App(App(App(church(2),church(2)),S),Zero),4),
                      ("3 2 S Z",App(App(App(church(3),church(2)),S),Zero),8)]:
    net=compile(term); steps=reduce(net); got=decode(net)
    print(f"{name:10s} = {got!s:6s} (expect {exp})  [{steps} interactions]  {'OK' if got==exp else 'FAIL'}")
