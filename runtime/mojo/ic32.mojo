# ic32.mojo -- a packed-word Interaction Calculus runtime, Mojo edition.
#
# The third native implementation of the IC32 typed-node, floating-dup model that
# `runtime/c/ic32.c` implements, `runtime/zig/ic32.zig` ports and
# `runtime/python/ic_float.py` pins down. Like the Zig port it exists to be a
# CONFORMANT BACKEND under `spec/conformance/README.md`: it reads one term on stdin
# and prints its normal form on stdout, and it must reproduce every `nf` in
# `spec/conformance/vectors/normalize.json`.
#
# It is deliberately a PORT, not a redesign -- same word layout, same rule set, same
# firing order, same canonical readback naming. Two implementations that made
# different structural choices would disagree for reasons that tell you nothing
# about the spec.
#
# Only the NORMAL FORM is normative across runtimes (conformance README §1); the
# recorded `ref_interactions` is pinned to the Python reference only, and nothing
# here tries to match it.
#
# Word layout (SPEC.md §2.1, spare top label bit = the IC32 substitution flag):
#
#     bits [63..32] addr (32)   heap index of the target node
#     bit  [31]     sub  (1)    set when this slot holds a substitution
#     bits [30..4]  label (27)  DUP/SUP color
#     bits [3..0]   tag  (4)    VAR LAM APP ERA SUP DP0 DP1
#
# One structural difference from C/Zig, forced by the language and called out rather
# than hidden: there are no mutable module-level globals, so every piece of runtime
# state lives in a single `VM` struct and every rule is a method on it. This is a
# packaging change only -- the state set, the transitions and the order are identical.
#
#   build: pixi run mojo build -O3 ic32.mojo -o ic32m     (from runtime/mojo/)
#   use:   echo 'TERM' | ./runtime/mojo/ic32m
from std.sys import argv, exit
from std.io.file_descriptor import FileDescriptor

alias T_VAR: UInt64 = 0
alias T_LAM: UInt64 = 1
alias T_APP: UInt64 = 2
alias T_ERA: UInt64 = 3
alias T_SUP: UInt64 = 4
alias T_DP0: UInt64 = 5
alias T_DP1: UInt64 = 6

alias SUBF: UInt64 = 1 << 31
alias HEAPCAP: Int = 1 << 24          # 16M slots
alias STEPCAP: Int = 50_000_000

# instruction opcodes for the iterative parser
alias OP_PARSE: UInt32 = 0
alias OP_APP: UInt32 = 1
alias OP_SUP: UInt32 = 2
alias OP_LAM: UInt32 = 3
alias OP_DUPVAL: UInt32 = 4
alias OP_DUPBODY: UInt32 = 5
alias OP_EXPECT: UInt32 = 6

# literal codes for the iterative readback (kind 1 work items)
alias LIT_RPAREN: UInt64 = 1
alias LIT_SPACE: UInt64 = 2
alias LIT_COMMA: UInt64 = 3
alias LIT_RBRACE: UInt64 = 4


def TAG(t: UInt64) -> UInt64:
    return t & 0xF


def LAB(t: UInt64) -> UInt32:
    return UInt32((t >> 4) & 0x7FFFFFF)


def ADDR(t: UInt64) -> UInt32:
    return UInt32(t >> 32)


def ISSUB(t: UInt64) -> Bool:
    return (t & SUBF) != 0


def SETSUB(t: UInt64) -> UInt64:
    return t | SUBF


def CLRSUB(t: UInt64) -> UInt64:
    return t & ~SUBF


def MK(tag: UInt64, lab: UInt32, addr: UInt32) -> UInt64:
    return (tag & 0xF) | ((UInt64(lab) & 0x7FFFFFF) << 4) | (UInt64(addr) << 32)


def bc(s: StringSlice) -> UInt8:
    """Byte code of a one-character literal.

    `ord()` yields an `Int`, and Mojo will not implicitly narrow that to the
    `UInt8` the byte-oriented parser and stringifier work in. Naming the
    conversion once beats sprinkling `UInt8(...)` over forty call sites.
    """
    return UInt8(ord(s))


def is_word_byte(c: UInt8) -> Bool:
    return (
        (c >= bc("a") and c <= bc("z"))
        or (c >= bc("A") and c <= bc("Z"))
        or (c >= bc("0") and c <= bc("9"))
        or c == bc("_")
    )


def emit(s: String):
    print(s, end="")


struct VM(Movable):
    # ---- heap
    var heap: List[UInt64]
    var hp: UInt32                    # 0 == null; also the high-water mark
    var interactions: Int
    # ---- free lists: the C runtime's two size classes (1-word cells, 2-word nodes).
    # Reduction is confluent and local, so a consumed redex node is dead the instant
    # its rule fires -- freeing it is the whole GC: no tracing, no pauses.
    var free1: List[UInt32]
    var free2: List[UInt32]
    var live: Int
    var peak_live: Int
    var gc_on: Bool
    var erase_on: Bool
    # ---- naming
    var free_loc: List[UInt32]
    var free_nm: List[String]
    var bnd_loc: List[UInt32]
    var bnd_nm: List[String]
    var name_ctr: Int
    # ---- parser
    var src: List[UInt8]              # NUL-terminated
    var p: Int
    var scope_nm: List[String]
    var scope_t: List[UInt64]
    var dup_a: List[String]
    var dup_b: List[String]
    # ---- output buffer
    var sb: List[UInt8]

    def __init__(out self):
        self.heap = List[UInt64](length=HEAPCAP, fill=0)
        self.hp = 1
        self.interactions = 0
        self.free1 = List[UInt32]()
        self.free2 = List[UInt32]()
        self.live = 0
        self.peak_live = 0
        self.gc_on = True
        self.erase_on = True
        self.free_loc = List[UInt32]()
        self.free_nm = List[String]()
        self.bnd_loc = List[UInt32]()
        self.bnd_nm = List[String]()
        self.name_ctr = 0
        self.src = List[UInt8]()
        self.p = 0
        self.scope_nm = List[String]()
        self.scope_t = List[UInt64]()
        self.dup_a = List[String]()
        self.dup_b = List[String]()
        self.sb = List[UInt8]()

    # ---------------------------------------------------------------- heap access
    def hget(self, a: UInt32) -> UInt64:
        return self.heap[Int(a)]

    def hset(mut self, a: UInt32, v: UInt64):
        self.heap[Int(a)] = v

    def free1_push(mut self, a: UInt32):
        self.free1.append(a)
        self.live -= 1

    def free2_push(mut self, a: UInt32):
        self.free2.append(a)
        self.live -= 2

    def alloc_n(mut self, n: UInt32) -> UInt32:
        self.live += Int(n)
        if self.live > self.peak_live:
            self.peak_live = self.live
        if self.gc_on and n == 1 and len(self.free1) > 0:
            return self.free1.pop()
        if self.gc_on and n == 2 and len(self.free2) > 0:
            return self.free2.pop()
        var a = self.hp
        self.hp += n
        if Int(self.hp) >= HEAPCAP:
            emit("FATAL: heap overflow\n")
            exit(2)
        return a

    def check_steps(self):
        if self.interactions > STEPCAP:
            emit("DIVERGES(step-cap)\n")
            exit(3)

    # ---------------------------------------------------------------- reduction
    # fire a floating DUP node at slot D, color L, demanded from side k (0|1)
    def fire(mut self, D: UInt32, L: UInt32, k: Int) -> UInt64:
        self.interactions += 1
        self.check_steps()
        var v = self.whnf(self.hget(D))
        var vt = TAG(v)
        var h0: UInt64 = 0
        var h1: UInt64 = 0
        if vt == T_SUP:
            var S = ADDR(v)
            var vl = LAB(v)
            var a = self.hget(S)
            var b = self.hget(S + 1)
            if vl == L:                      # DUP-SUP equal: annihilate
                h0 = a
                h1 = b
            else:                            # DUP-SUP different: commute
                var Da = self.alloc_n(1)
                self.hset(Da, a)
                var Db = self.alloc_n(1)
                self.hset(Db, b)
                var S0 = self.alloc_n(2)
                self.hset(S0, MK(T_DP0, L, Da))
                self.hset(S0 + 1, MK(T_DP0, L, Db))
                var S1 = self.alloc_n(2)
                self.hset(S1, MK(T_DP1, L, Da))
                self.hset(S1 + 1, MK(T_DP1, L, Db))
                h0 = MK(T_SUP, vl, S0)
                h1 = MK(T_SUP, vl, S1)
            self.free2_push(S)               # consumed superposition node is dead
        elif vt == T_LAM:                    # DUP-LAM
            var Lv = ADDR(v)
            var Lx0 = self.alloc_n(1)
            var Lx1 = self.alloc_n(1)
            var Df = self.alloc_n(1)
            self.hset(Df, self.hget(Lv))     # salvage body, dup it
            self.hset(Lx0, MK(T_DP0, L, Df))
            self.hset(Lx1, MK(T_DP1, L, Df))
            var Ss = self.alloc_n(2)
            self.hset(Ss, MK(T_VAR, 0, Lx0))
            self.hset(Ss + 1, MK(T_VAR, 0, Lx1))
            self.hset(Lv, SETSUB(MK(T_SUP, L, Ss)))   # the lambda's var becomes a SUP
            h0 = MK(T_LAM, 0, Lx0)
            h1 = MK(T_LAM, 0, Lx1)
        elif vt == T_ERA:                    # DUP-ERA
            h0 = MK(T_ERA, 0, 0)
            h1 = MK(T_ERA, 0, 0)
        elif vt == T_APP:                    # DUP-APP (collapse): copy structure
            var A = ADDR(v)
            var f = self.hget(A)
            var a2 = self.hget(A + 1)
            var Df2 = self.alloc_n(1)
            self.hset(Df2, f)
            var Dx = self.alloc_n(1)
            self.hset(Dx, a2)
            var A0 = self.alloc_n(2)
            self.hset(A0, MK(T_DP0, L, Df2))
            self.hset(A0 + 1, MK(T_DP0, L, Dx))
            var A1 = self.alloc_n(2)
            self.hset(A1, MK(T_DP1, L, Df2))
            self.hset(A1 + 1, MK(T_DP1, L, Dx))
            h0 = MK(T_APP, 0, A0)
            h1 = MK(T_APP, 0, A1)
            self.free2_push(A)               # consumed application node is dead
        else:                                # VAR free/stuck: DUP-VAR copy
            h0 = v
            h1 = v
        if k == 0:
            self.hset(D, SETSUB(h1))
            return h0
        else:
            self.hset(D, SETSUB(h0))
            return h1

    # (&L{a,b} c) -> !&L{c0,c1}=c; &L{(a c0),(b c1)}
    def app_sup(mut self, sup: UInt64, arg: UInt64) -> UInt64:
        self.interactions += 1
        self.check_steps()
        var S = ADDR(sup)
        var L = LAB(sup)
        var a = self.hget(S)
        var b = self.hget(S + 1)
        var Dc = self.alloc_n(1)
        self.hset(Dc, arg)
        var Aa = self.alloc_n(2)
        self.hset(Aa, a)
        self.hset(Aa + 1, MK(T_DP0, L, Dc))
        var Ab = self.alloc_n(2)
        self.hset(Ab, b)
        self.hset(Ab + 1, MK(T_DP1, L, Dc))
        var Sn = self.alloc_n(2)
        self.hset(Sn, MK(T_APP, 0, Aa))
        self.hset(Sn + 1, MK(T_APP, 0, Ab))
        self.free2_push(S)                   # consumed superposition node is dead
        return MK(T_SUP, L, Sn)

    # Eraser propagation: free the uniquely-owned sub-net rooted at t (the argument
    # discarded by APP-ERA). Safe because IC sharing happens ONLY through DUP nodes,
    # so this frees the APP/SUP/LAM spine above any dup and STOPS at DUP/VAR/ERA.
    # Iterative, matching C/Zig. Same honest limit: under lazy normalization a
    # discarded argument is frequently an unevaluated VAR rather than built structure,
    # so this reclaims only the already-built spine.
    def collect(mut self, root: UInt64):
        if not self.erase_on:
            return
        var stk = List[UInt64]()
        stk.append(root)
        while len(stk) > 0:
            var t = stk.pop()
            var tag = TAG(t)
            if tag == T_APP:
                var A = ADDR(t)
                stk.append(self.hget(A))
                stk.append(self.hget(A + 1))
                self.free2_push(A)
            elif tag == T_SUP:
                var S = ADDR(t)
                stk.append(self.hget(S))
                stk.append(self.hget(S + 1))
                self.free2_push(S)
            elif tag == T_LAM:
                var Lv = ADDR(t)
                stk.append(self.hget(Lv))
                self.free1_push(Lv)
            # T_VAR, T_DP0, T_DP1, T_ERA: stop (target may be shared or bound elsewhere)

    def whnf(mut self, t0: UInt64) -> UInt64:
        var t = t0
        while True:
            var tag = TAG(t)
            if tag == T_VAR:
                var w = self.hget(ADDR(t))
                if ISSUB(w):
                    t = CLRSUB(w)
                    continue
                return t                     # free / unsubstituted
            if tag == T_DP0 or tag == T_DP1:
                var D = ADDR(t)
                var w2 = self.hget(D)
                if ISSUB(w2):                # sibling already fired
                    t = CLRSUB(w2)
                    continue
                var k = 0 if tag == T_DP0 else 1
                t = self.fire(D, LAB(t), k)
                continue
            if tag == T_APP:
                var A = ADDR(t)
                var f = self.whnf(self.hget(A))
                var ft = TAG(f)
                if ft == T_LAM:              # APP-LAM
                    self.interactions += 1
                    self.check_steps()
                    var Lv = ADDR(f)
                    var arg = self.hget(A + 1)
                    var bod = self.hget(Lv)
                    self.hset(Lv, SETSUB(arg))
                    self.free2_push(A)       # consumed application node is dead
                    t = bod
                    continue
                if ft == T_SUP:
                    t = self.app_sup(f, self.hget(A + 1))
                    self.free2_push(A)
                    continue
                if ft == T_ERA:
                    self.interactions += 1
                    self.check_steps()
                    self.collect(self.hget(A + 1))
                    self.free2_push(A)
                    t = MK(T_ERA, 0, 0)
                    continue
                self.hset(A, f)              # stuck: memoize reduced fun
                return MK(T_APP, 0, A)
            return t                         # LAM, SUP, ERA

    # `(g (g ... (g z)))` built directly in the heap, k applications deep. Bypassing the
    # parser is the point: the input buffer, not the normaliser, is what caps the depth a
    # parsed term can reach, so this reaches past it.
    def build_deep(mut self, k: Int) -> UInt64:
        var g = self.free_intern("g")
        var z = self.free_intern("z")
        var acc = MK(T_VAR, 0, z)
        for _ in range(k):
            var A = self.alloc_n(2)
            self.hset(A, MK(T_VAR, 0, g))
            self.hset(A + 1, acc)
            acc = MK(T_APP, 0, A)
        return acc

    # Iterative full normaliser: an explicit stack of heap SLOT INDICES. C stores raw
    # `Term*` here; an index is used instead because the guarantee that makes those
    # pointers safe (the heap is fixed-size and never reallocated) holds either way,
    # and an index is checked. ROOT_SLOT is the sentinel for "the root, not a slot".
    def normal(mut self, t: UInt64) -> UInt64:
        var ROOT_SLOT: UInt32 = 0xFFFFFFFF
        var root = t
        var stk = List[UInt32]()
        stk.append(ROOT_SLOT)
        while len(stk) > 0:
            var slot = stk.pop()
            var inp = root if slot == ROOT_SLOT else self.hget(slot)
            var v = self.whnf(inp)
            if slot == ROOT_SLOT:
                root = v
            else:
                self.hset(slot, v)
            var tag = TAG(v)
            if tag == T_LAM:
                stk.append(ADDR(v))
            elif tag == T_APP:
                var A = ADDR(v)
                stk.append(A)
                stk.append(A + 1)
            elif tag == T_SUP:
                var S = ADDR(v)
                stk.append(S)
                stk.append(S + 1)
        return root

    # ---------------------------------------------------------------- naming
    def free_lookup(self, loc: UInt32) -> String:
        for i in range(len(self.free_loc)):
            if self.free_loc[i] == loc:
                return self.free_nm[i]
        return String("")

    def free_intern(mut self, nm: String) -> UInt32:
        for i in range(len(self.free_loc)):
            if self.free_nm[i] == nm:
                return self.free_loc[i]
        var L = self.alloc_n(1)
        self.hset(L, MK(T_ERA, 0, 0))        # sentinel (sub-clear => free)
        self.free_loc.append(L)
        self.free_nm.append(nm)
        return L

    def bnd_name(mut self, loc: UInt32) -> String:
        for i in range(len(self.bnd_loc)):
            if self.bnd_loc[i] == loc:
                return self.bnd_nm[i]
        var idx = self.name_ctr
        self.name_ctr += 1
        var s: String
        if idx < 26:
            s = String(chr(ord("a") + idx))
        else:
            s = String("v") + String(idx)
        self.bnd_loc.append(loc)
        self.bnd_nm.append(s)
        return s

    # ---------------------------------------------------------------- parser
    def cur(self) -> UInt8:
        return self.src[self.p]

    def perr(self, m: String):
        emit(String("parse error: ") + m + "\n")
        exit(4)

    def ws(mut self):
        while (
            self.cur() == bc(" ")
            or self.cur() == bc("\t")
            or self.cur() == bc("\n")
            or self.cur() == bc("\r")
        ):
            self.p += 1

    def is_lambda(self) -> Bool:
        if self.cur() == bc("\\"):
            return True
        return self.src[self.p] == 0xCE and self.p + 1 < len(self.src) and self.src[self.p + 1] == 0xBB

    def eat_lambda(mut self):
        if self.cur() == bc("\\"):
            self.p += 1
        else:
            self.p += 2

    def expect(mut self, c: UInt8):
        self.ws()
        if self.cur() != c:
            self.perr("expected char")
        self.p += 1

    def rdname(mut self) -> String:
        self.ws()
        var out = List[UInt8]()
        while is_word_byte(self.cur()):
            out.append(self.cur())
            self.p += 1
        if len(out) == 0:
            self.perr("expected name")
        return String(StringSlice(unsafe_from_utf8=Span(out)))

    def rduint(mut self) -> UInt32:
        self.ws()
        var v: UInt32 = 0
        while self.cur() >= bc("0") and self.cur() <= bc("9"):
            v = v * 10 + UInt32(self.cur() - bc("0"))
            self.p += 1
        return v

    # Iterative recursive-descent: an instruction stack drives parsing, a value stack
    # collects sub-results. No host recursion, so input of arbitrary nesting depth
    # parses without overflowing the stack. Scope bindings are pushed/popped by
    # OP_LAM / OP_DUPVAL+OP_DUPBODY at exactly the points recursion would.
    def parse_term(mut self) -> UInt64:
        var op = List[UInt32]()
        var ix = List[UInt32]()
        var iy = List[UInt32]()
        var vstk = List[UInt64]()
        op.append(OP_PARSE)
        ix.append(0)
        iy.append(0)
        while len(op) > 0:
            var o = op.pop()
            var x = ix.pop()
            var y = iy.pop()
            if o == OP_PARSE:
                self.ws()
                if self.is_lambda():
                    self.eat_lambda()
                    var nm = self.rdname()
                    self.expect(bc("."))
                    var L = self.alloc_n(1)
                    self.scope_nm.append(nm)
                    self.scope_t.append(MK(T_VAR, 0, L))
                    op.append(OP_LAM); ix.append(L); iy.append(0)       # heap[L]=body
                    op.append(OP_PARSE); ix.append(0); iy.append(0)     # parse body
                    continue
                var c = self.cur()
                if c == bc("*"):
                    self.p += 1
                    vstk.append(MK(T_ERA, 0, 0))
                    continue
                if c == bc("("):
                    self.p += 1
                    op.append(OP_APP); ix.append(0); iy.append(0)       # eat ')', build APP
                    op.append(OP_PARSE); ix.append(0); iy.append(0)     # parse arg
                    op.append(OP_PARSE); ix.append(0); iy.append(0)     # parse fun (first)
                    continue
                if c == bc("&") or c == bc("{"):
                    var lab: UInt32 = 0
                    if c == bc("&"):
                        self.p += 1
                        lab = self.rduint()
                        self.expect(bc("{"))
                    else:
                        self.p += 1
                    op.append(OP_SUP); ix.append(lab); iy.append(0)     # eat '}', build SUP
                    op.append(OP_PARSE); ix.append(0); iy.append(0)     # parse right
                    op.append(OP_EXPECT); ix.append(UInt32(bc(","))); iy.append(0)
                    op.append(OP_PARSE); ix.append(0); iy.append(0)     # parse left (first)
                    continue
                if c == bc("!"):
                    self.p += 1
                    var lab2: UInt32 = 0
                    self.ws()
                    if self.cur() == bc("&"):
                        self.p += 1
                        lab2 = self.rduint()
                    self.expect(bc("{"))
                    var na = self.rdname()
                    self.expect(bc(","))
                    var nb = self.rdname()
                    self.expect(bc("}"))
                    self.expect(bc("="))
                    var D = self.alloc_n(1)
                    self.dup_a.append(na)
                    self.dup_b.append(nb)
                    op.append(OP_DUPBODY); ix.append(0); iy.append(0)   # pop projections
                    op.append(OP_PARSE); ix.append(0); iy.append(0)     # parse body
                    op.append(OP_DUPVAL); ix.append(D); iy.append(lab2) # heap[D]=val, eat ';'
                    op.append(OP_PARSE); ix.append(0); iy.append(0)     # parse val (first)
                    continue
                var nm2 = self.rdname()                                  # variable
                var found = False
                var i = len(self.scope_nm)
                while i > 0:
                    i -= 1
                    if self.scope_nm[i] == nm2:
                        vstk.append(self.scope_t[i])
                        found = True
                        break
                if not found:
                    vstk.append(MK(T_VAR, 0, self.free_intern(nm2)))
            elif o == OP_APP:
                var a = vstk.pop()
                var f = vstk.pop()
                self.expect(bc(")"))
                var A = self.alloc_n(2)
                self.hset(A, f)
                self.hset(A + 1, a)
                vstk.append(MK(T_APP, 0, A))
            elif o == OP_SUP:
                var r = vstk.pop()
                var l = vstk.pop()
                self.expect(bc("}"))
                var S = self.alloc_n(2)
                self.hset(S, l)
                self.hset(S + 1, r)
                vstk.append(MK(T_SUP, x, S))
            elif o == OP_LAM:
                var bod = vstk.pop()
                self.hset(x, bod)
                _ = self.scope_nm.pop()          # pop the lambda's binding
                _ = self.scope_t.pop()
                vstk.append(MK(T_LAM, 0, x))
            elif o == OP_DUPVAL:
                var val = vstk.pop()
                self.hset(x, val)
                self.expect(bc(";"))
                var db = self.dup_b.pop()
                var da = self.dup_a.pop()
                self.scope_nm.append(da)
                self.scope_t.append(MK(T_DP0, y, x))
                self.scope_nm.append(db)
                self.scope_t.append(MK(T_DP1, y, x))
                # the dup floats; the body becomes the form's value
            elif o == OP_DUPBODY:
                _ = self.scope_nm.pop()          # pop the two projection bindings
                _ = self.scope_t.pop()
                _ = self.scope_nm.pop()
                _ = self.scope_t.pop()
            elif o == OP_EXPECT:
                self.expect(UInt8(x))
        return vstk[0]

    # ---------------------------------------------------------------- stringify
    def sb_puts(mut self, s: String):
        var b = s.as_bytes()
        for i in range(len(b)):
            self.sb.append(b[i])

    def sb_putc(mut self, c: UInt8):
        self.sb.append(c)

    # iterative readback -- no recursion, so arbitrarily deep normal forms read back
    # safely. Work items are (kind, term): kind 0 renders a term, kind 1 emits one of
    # the four structural literals.
    def show_iter(mut self, t: UInt64):
        self.sb = List[UInt8]()
        var kind = List[UInt64]()
        var term = List[UInt64]()
        kind.append(0)
        term.append(t)
        while len(kind) > 0:
            var k = kind.pop()
            var x = term.pop()
            if k == 1:
                if x == LIT_RPAREN:
                    self.sb_putc(bc(")"))
                elif x == LIT_SPACE:
                    self.sb_putc(bc(" "))
                elif x == LIT_COMMA:
                    self.sb_putc(bc(","))
                else:
                    self.sb_putc(bc("}"))
                continue
            var tag = TAG(x)
            if tag == T_VAR:
                var L = ADDR(x)
                var f = self.free_lookup(L)
                if f != "":
                    self.sb_puts(f)
                else:
                    self.sb_puts(self.bnd_name(L))
            elif tag == T_ERA:
                self.sb_putc(bc("*"))
            elif tag == T_LAM:
                var L2 = ADDR(x)
                self.sb_putc(0xCE)
                self.sb_putc(0xBB)
                self.sb_puts(self.bnd_name(L2))
                self.sb_putc(bc("."))
                kind.append(0); term.append(self.hget(L2))      # body renders next
            elif tag == T_APP:
                var A = ADDR(x)
                self.sb_putc(bc("("))                          # push reversed
                kind.append(1); term.append(LIT_RPAREN)
                kind.append(0); term.append(self.hget(A + 1))
                kind.append(1); term.append(LIT_SPACE)
                kind.append(0); term.append(self.hget(A))
            elif tag == T_SUP:
                var S = ADDR(x)
                self.sb_puts(String("&") + String(LAB(x)) + "{")
                kind.append(1); term.append(LIT_RBRACE)
                kind.append(0); term.append(self.hget(S + 1))
                kind.append(1); term.append(LIT_COMMA)
                kind.append(0); term.append(self.hget(S))
            elif tag == T_DP0:
                self.sb_puts("DP0")
            elif tag == T_DP1:
                self.sb_puts("DP1")
            else:
                self.sb_putc(bc("?"))

    def sb_str(self) -> String:
        return String(StringSlice(unsafe_from_utf8=Span(self.sb)))

    # ---------------------------------------------------------------- driver
    def reset_state(mut self):
        self.hp = 1
        self.interactions = 0
        self.free_loc = List[UInt32]()
        self.free_nm = List[String]()
        self.bnd_loc = List[UInt32]()
        self.bnd_nm = List[String]()
        self.name_ctr = 0
        self.scope_nm = List[String]()
        self.scope_t = List[UInt64]()
        self.dup_a = List[String]()
        self.dup_b = List[String]()
        self.free1 = List[UInt32]()
        self.free2 = List[UInt32]()
        self.live = 0
        self.peak_live = 0

    def set_source(mut self, s: String):
        self.src = List[UInt8]()
        var b = s.as_bytes()
        for i in range(len(b)):
            self.src.append(b[i])
        self.src.append(0)               # NUL sentinel keeps `cur()` total
        self.p = 0

    def run_source(mut self, s: String) -> String:
        self.set_source(s)
        var t = self.parse_term()
        self.ws()
        var nf = self.normal(t)
        self.show_iter(nf)
        return self.sb_str()


def one_test(mut vm: VM, inp: String, want: String) -> Int:
    vm.reset_state()
    var got = vm.run_source(inp)
    var ok = got == want
    emit(String("  [") + ("PASS" if ok else "FAIL") + "] " + inp + "\n")
    if not ok:
        emit(String("         got '") + got + "' want '" + want + "'\n")
    return 1 if ok else 0


# linear church numeral with an explicit duplicator label (the encoding a compiler emits)
def clin_str(n: Int, lab: Int) -> String:
    var s = String("\\f.\\x.")
    if n <= 1:
        return s + "(f x)"
    var curname = String("f")
    for i in range(n - 1):
        if i < n - 2:
            s += String("!&") + String(lab) + "{a" + String(i) + ",t" + String(i) + "}=" + curname + ";"
            curname = String("t") + String(i)
        else:
            s += String("!&") + String(lab) + "{a" + String(i) + ",a" + String(i + 1) + "}=" + curname + ";"
    for i in range(n):
        s += String("(a") + String(i) + " "
    s += "x"
    for _ in range(n):
        s += ")"
    return s


def count_sub(hay: String, needle: String) -> Int:
    var h = hay.as_bytes()
    var nd = needle.as_bytes()
    if len(nd) == 0 or len(h) < len(nd):
        return 0
    var c = 0
    for i in range(len(h) - len(nd) + 1):
        var hit = True
        for j in range(len(nd)):
            if h[i + j] != nd[j]:
                hit = False
                break
        if hit:
            c += 1
    return c


def run_tests(mut vm: VM) -> Int:
    emit("ic32.mojo self-test battery\n")
    var ins = List[String]()
    var outs = List[String]()
    ins.append("(\\x.x a)");                          outs.append("a")
    ins.append("((\\x.\\y.x a) b)");                  outs.append("a")
    ins.append("!&0{a,b}=*;\\q.q");                   outs.append("λa.a")
    ins.append("((\\f.\\x.(f (f x)) \\y.y) z)");      outs.append("z")
    ins.append("&3{a,b}");                            outs.append("&3{a,b}")
    ins.append("!&0{a,b}=\\x.x;(a b)");               outs.append("λa.a")
    ins.append("((\\f.\\x.(f (f x)) g) z)");          outs.append("(g (g z))")
    ins.append("((\\f.\\x.!&0{a,b}=f;(a (b x)) g) z)"); outs.append("(g (g z))")
    var tot = 0
    var pas = 0
    for i in range(len(ins)):
        tot += 1
        pas += one_test(vm, ins[i], outs[i])

    # Church arithmetic with the proper IC encoding (explicit dups + DISTINCT
    # duplicator labels -- what a compiler emits). Naive single-label numerals reduce
    # incorrectly by design; that is an input-encoding property of interaction nets,
    # not a runtime defect, which is why the conformance vectors are restricted to the
    # labeling discipline too.
    emit("  --- church arithmetic (explicit dups, distinct labels) ---\n")
    var ax = List[Int](); var ay = List[Int](); var aexp = List[Bool]()
    var awant = List[Int](); var alab = List[String]()
    ax.append(7); ay.append(3); aexp.append(False); awant.append(21); alab.append("mult 7*3")
    ax.append(3); ay.append(2); aexp.append(True);  awant.append(8);  alab.append("exp 2^3")
    ax.append(2); ay.append(5); aexp.append(True);  awant.append(25); alab.append("exp 5^2")
    for i in range(len(ax)):
        var sa = clin_str(ax[i], 1)
        var sb2 = clin_str(ay[i], 0)
        var term: String
        if aexp[i]:
            term = String("(((") + sa + " " + sb2 + ") s) z)"
        else:
            term = String("((") + sa + " (" + sb2 + " s)) z)"
        vm.reset_state()
        var got = count_sub(vm.run_source(term), "(s ")
        var ok = got == awant[i]
        tot += 1
        if ok:
            pas += 1
        emit(String("  [") + ("PASS" if ok else "FAIL") + "] " + alab[i] + ": s^" + String(got)
             + " (expected s^" + String(awant[i]) + ")\n")

    # deep stress: iterative PARSER + normaliser + readback, end-to-end. A recursive
    # descent parser overflows the host stack around ~4k nesting; this parses 200k-deep
    # input, normalizes it, and reads it back.
    emit("  --- deep stress: iterative parser + normal + readback ---\n")
    vm.reset_state()
    var KP = 200000
    var big = List[UInt8]()
    for _ in range(KP):
        big.append(bc("("))
        big.append(bc("f"))
        big.append(bc(" "))
    big.append(bc("x"))
    for _ in range(KP):
        big.append(bc(")"))
    vm.src = big^
    vm.src.append(0)
    vm.p = 0
    var t = vm.parse_term()
    vm.ws()
    vm.show_iter(vm.normal(t))
    var papps = count_sub(vm.sb_str(), "(f ")
    var deep_ok = papps == KP
    tot += 1
    if deep_ok:
        pas += 1
    emit(String("  [") + ("PASS" if deep_ok else "FAIL") + "] (f^" + String(KP)
         + " x): parsed + normalized + read back, " + String(papps) + " applications\n")

    # deep stress 2: build the spine IN THE HEAP rather than through the parser, so the
    # depth is not bounded by what an input buffer can hold. Exercises the iterative
    # normaliser and readback alone at half a million deep.
    emit("  --- deep stress: iterative normal + readback at half a million deep ---\n")
    vm.reset_state()
    var K = 500000
    var deep = vm.build_deep(K)
    vm.show_iter(vm.normal(deep))
    var gc = count_sub(vm.sb_str(), "(g ")
    var deep2_ok = gc == K
    tot += 1
    if deep2_ok:
        pas += 1
    emit(String("  [") + ("PASS" if deep2_ok else "FAIL") + "] g^" + String(K)
         + " z: normalized + read back, " + String(gc) + " applications\n")

    emit(String("  --- summary: ") + String(pas) + "/" + String(tot) + " passed ---\n")
    return 0 if pas == tot else 1


def main() raises:
    var args = argv()
    var arg1 = String("")
    if len(args) > 1:
        arg1 = String(args[1])

    var vm = VM()

    if arg1 == "--test":
        exit(run_tests(vm))

    # read the term from stdin
    var fd = FileDescriptor(0)
    var buf = List[UInt8](length=1 << 16, fill=0)
    var data = List[UInt8]()
    while True:
        var n = fd.read_bytes(Span(buf))
        if n == 0:
            break
        for i in range(n):
            data.append(buf[i])
    # strip trailing whitespace/newline
    while len(data) > 0:
        var c = data[len(data) - 1]
        if c == bc("\n") or c == bc("\r") or c == bc(" ") or c == bc("\t"):
            _ = data.pop()
        else:
            break
    vm.src = data^
    vm.src.append(0)                    # NUL sentinel keeps `cur()` total
    vm.p = 0

    var quiet = arg1 == "-q"
    var verbose = quiet or arg1 == "-v"

    var t = vm.parse_term()
    vm.ws()
    var nf = vm.normal(t)

    if not quiet:
        vm.show_iter(nf)
        emit(vm.sb_str() + "\n")
    if verbose:
        emit(String("interactions=") + String(vm.interactions) + " heap=" + String(vm.hp) + "\n")
