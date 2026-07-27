#!/usr/bin/env python3
"""Alpha-equivalence for normal forms printed by two different engines.

HVM4 prints curried application as `f(x,y)` and TRVM as `((f x) y)`; both
generate their own bound-variable names and their own duplicator labels. So a
textual diff is meaningless -- the terms must be parsed and compared by
structure, with binders numbered by depth and labels numbered by first
appearance.
"""
import re

SUB = {"\u2080": "_0", "\u2081": "_1"}


def _toks(s):
    s = re.sub(r"//[^\n]*", "", s)
    out, i = [], 0
    while i < len(s):
        c = s[i]
        if c.isspace():
            i += 1
            continue
        if c in "λ().,!&{}=;*@":
            out.append(c)
            i += 1
            continue
        m = re.match(r"[^\s().,!&{}=;*@λ]+", s[i:])
        if not m:
            raise SyntaxError(f"bad char {c!r}")
        out.append(m.group(0))
        i += len(m.group(0))
    return out


class P:
    """One parser, two surfaces. `(a (a b))` is a call in HVM4 and a nested
    juxtaposition in TRVM, so the surface must be declared, not guessed."""

    def __init__(self, t, hvm4):
        self.t, self.i, self.hvm4 = t, 0, hvm4

    def peek(self, k=0):
        return self.t[self.i + k] if self.i + k < len(self.t) else None

    def eat(self, x=None):
        v = self.t[self.i]
        if x is not None and v != x:
            raise SyntaxError(f"expected {x!r} got {v!r}")
        self.i += 1
        return v

    def term(self):
        c = self.peek()
        if c == "λ":
            self.eat("λ")
            v = self.eat()
            self.eat(".")
            return ("lam", v, self.term())
        if c == "!":
            self.eat("!")
            if self.peek() == "&":            # TRVM: !&L{a,b}=v;
                self.eat("&")
                lab = self.eat()
                self.eat("{")
                a = self.eat()
                self.eat(",")
                b = self.eat()
                self.eat("}")
                self.eat("=")
                val = self.term()
                self.eat(";")
                return ("dup2", lab, a, b, val, self.term())
            v = self.eat()                    # HVM4: !X&L=v;
            self.eat("&")
            lab = self.eat()
            self.eat("=")
            val = self.term()
            self.eat(";")
            return ("dup2", lab, v + "_0", v + "_1", val, self.term())
        if c == "&":
            self.eat("&")
            lab = self.eat()
            self.eat("{")
            a = self.term()
            if self.peek() == ",":
                self.eat(",")
                b = self.term()
            else:
                b = ("era",)
            self.eat("}")
            return ("sup", lab, a, b)
        return self.app()

    def app(self):
        f = self.atom()
        while True:
            c = self.peek()
            if c == "(" and self.hvm4:         # HVM4 call: f(x,y)
                self.eat("(")
                args = []
                if self.peek() != ")":
                    args.append(self.term())
                    while self.peek() == ",":
                        self.eat(",")
                        args.append(self.term())
                self.eat(")")
                for a in args:
                    f = ("app", f, a)
                continue
            return f

    def atom(self):
        c = self.peek()
        if c == "*":
            self.eat("*")
            return ("era",)
        if c == "@":
            self.eat("@")
            return ("var", "@" + self.eat())
        if c == "(":                            # TRVM app, or grouping
            self.eat("(")
            f = self.term()
            if not self.hvm4:
                while self.peek() not in (")", None):
                    f = ("app", f, self.term())
            self.eat(")")
            return f
        v = self.eat()
        for k, r in SUB.items():
            v = v.replace(k, r)
        return ("var", v)


def canon(src, hvm4):
    """Parse a printed normal form into an engine-independent string."""
    ast = P(_toks(src.strip()), hvm4).term()
    labs, free = {}, {}

    def lab(x):
        return labs.setdefault(x, f"L{len(labs)}")

    def go(t, env):
        k = t[0]
        if k == "era":
            return "*"
        if k == "var":
            v = t[1]
            if v in env:
                return f"b{len(env) - 1 - env.index(v)}"   # de Bruijn index
            if re.fullmatch(r"[0-9]+", v):
                return f"#{v}"          # a literal is itself, never renamed
            return free.setdefault(v, f"f{len(free)}")
        if k == "lam":
            return "λ." + go(t[2], env + [t[1]])
        if k == "app":
            return f"({go(t[1], env)} {go(t[2], env)})"
        if k == "sup":
            return f"&{lab(t[1])}{{{go(t[2], env)},{go(t[3], env)}}}"
        if k == "dup2":
            _, l, a, b, val, body = t
            return (f"!&{lab(l)}{{}}={go(val, env)};"
                    f"{go(body, env + [a, b])}")
        raise ValueError(k)

    return go(ast, [])


def same(hvm4_nf, trvm_nf):
    try:
        return canon(hvm4_nf, True) == canon(trvm_nf, False)
    except Exception:
        return None            # unparseable -- report, never assume agreement
