"""Translate the pure-IC subset of HVM4 surface syntax into TRVM IC syntax."""
import re, sys, os

SUB={'\u2080':'_0','\u2081':'_1'}

def tokenize(s):
    s=re.sub(r'//[^\n]*','',s)
    toks=[];i=0
    while i<len(s):
        c=s[i]
        if c.isspace(): i+=1; continue
        if c in 'λ().,!&{}=;*@': toks.append(c); i+=1; continue
        m=re.match(r'[^\s().,!&{}=;*@λ]+',s[i:])
        if not m: raise SyntaxError(f"bad char {c!r} at {i}")
        toks.append(m.group(0)); i+=len(m.group(0))
    return toks

class P:
    def __init__(self,toks): self.t=toks; self.i=0
    def peek(self,k=0): return self.t[self.i+k] if self.i+k<len(self.t) else None
    def eat(self,x=None):
        v=self.t[self.i]
        if x is not None and v!=x: raise SyntaxError(f"expected {x!r} got {v!r}")
        self.i+=1; return v
    def term(self):
        c=self.peek()
        if c=='λ':
            self.eat('λ'); v=self.eat(); self.eat('.')
            return ('lam',v,self.term())
        if c=='!':
            self.eat('!'); v=self.eat(); self.eat('&'); lab=self.eat(); self.eat('=')
            val=self.term(); self.eat(';')
            return ('dup',v,lab,val,self.term())
        if c=='&':
            self.eat('&'); lab=self.eat(); self.eat('{')
            a=self.term(); self.eat(','); b=self.term(); self.eat('}')
            return ('sup',lab,a,b)
        return self.app()
    def app(self):
        f=self.atom()
        while self.peek()=='(':
            self.eat('(')
            args=[self.term()]
            while self.peek()==',': self.eat(','); args.append(self.term())
            self.eat(')')
            for a in args: f=('app',f,a)
        return f
    def atom(self):
        c=self.peek()
        if c=='*': self.eat('*'); return ('era',)
        if c=='@': self.eat('@'); return ('ref',self.eat())
        if c=='(':
            self.eat('('); t=self.term(); self.eat(')'); return t
        v=self.eat()
        for k,r in SUB.items(): v=v.replace(k,r)
        return ('var',v)

def parse_book(path,seen=None):
    seen=seen or set()
    if path in seen: return {}
    seen.add(path)
    defs={}
    src=open(path,encoding='utf-8').read()
    for m in re.finditer(r'#include\s+"([^"]+)"',src):
        defs.update(parse_book(os.path.join(os.path.dirname(path),m.group(1)),seen))
    src=re.sub(r'#include\s+"[^"]+"','',src)
    src=re.sub(r'//[^\n]*','',src)
    for m in re.finditer(r'@(\w+)\s*=',src):
        name=m.group(1); start=m.end()
        nxt=re.search(r'\n\s*@\w+\s*=',src[start:])
        body=src[start:start+nxt.start()] if nxt else src[start:]
        defs[name]=body.strip()
    return defs

class Emit:
    def __init__(self,defs,fresh_labels=True):
        self.defs=defs; self.fresh=fresh_labels; self.n=0; self.labmap={}; self.uid=0
    def lab(self,name,scope):
        key=(scope,name) if self.fresh else name
        if key not in self.labmap:
            self.n+=1; self.labmap[key]=self.n
        return self.labmap[key]
    def go(self,t,scope=0,ren=None):
        ren=ren or {}
        k=t[0]
        if k=='var':
            v=t[1]; return ren.get(v,v)
        if k=='era': return '*'
        if k=='lam':
            self.uid+=1; nv=f"v{self.uid}"
            r=dict(ren); r[t[1]]=nv
            return f"λ{nv}.{self.go(t[2],scope,r)}"
        if k=='app':
            return f"({self.go(t[1],scope,ren)} {self.go(t[2],scope,ren)})"
        if k=='sup':
            return f"&{self.lab(t[1],scope)}{{{self.go(t[2],scope,ren)},{self.go(t[3],scope,ren)}}}"
        if k=='dup':
            _,v,lab,val,body=t
            self.uid+=1; a=f"d{self.uid}a"; b=f"d{self.uid}b"
            r=dict(ren); r[v+'_0']=a; r[v+'_1']=b
            return (f"!&{self.lab(lab,scope)}{{{a},{b}}}={self.go(val,scope,ren)};"
                    f"{self.go(body,scope,r)}")
        if k=='ref':
            name=t[1]
            if name not in self.defs: raise KeyError(f"undefined @{name}")
            self.uid+=1; sc=self.uid if self.fresh else 0
            return self.go(parse_all(self.defs[name]),sc,{})
        raise ValueError(k)

def parse_all(src):
    """Parse a complete term. Leftover tokens mean the source used syntax
    outside the pure-IC fragment (`+`, `===`, `#Ctr`, ...); truncating there
    would silently benchmark a different program, so it is an error."""
    p=P(tokenize(src))
    t=p.term()
    if p.i!=len(p.t):
        raise SyntaxError(f"trailing tokens from {p.peek()!r}")
    return t

def translate(path,fresh=True):
    defs=parse_book(path)
    if 'main' not in defs: raise KeyError("no @main")
    e=Emit(defs,fresh)
    return e.go(parse_all(defs['main']))

if __name__=='__main__':
    print(translate(sys.argv[1], fresh=(len(sys.argv)<3 or sys.argv[2]!='verbatim')))
