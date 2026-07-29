// ic32.zig -- a packed-word Interaction Calculus runtime, Zig edition.
//
// A second native implementation of the IC32 typed-node, floating-dup model that
// `runtime/c/ic32.c` implements and `runtime/python/ic_float.py` pins down. It
// exists to be a CONFORMANT BACKEND under `spec/conformance/README.md`: it reads
// one term on stdin and prints its normal form on stdout, and it must reproduce
// every `nf` in `spec/conformance/vectors/normalize.json`.
//
// It is deliberately a PORT, not a redesign. The word layout, the rule set, the
// firing order, the free-list size classes and the canonical readback naming are
// the C runtime's, because the point of a second implementation is to catch a
// spec ambiguity -- and two implementations that made different structural
// choices would disagree for reasons that tell you nothing about the spec.
//
// What is NOT claimed: the interaction COUNT is not normative across runtimes
// (conformance README §1), and this file makes no attempt to match `ref_interactions`.
// Only the normal form is normative. In practice this port does match the C
// count, because it is the same reduction strategy -- but that is an observation,
// not a contract, and the conformance runner must not assert it.
//
// Word layout (SPEC.md §2.1, spare top label bit = the IC32 substitution flag):
//
//     bits [63..32] addr (32)   heap index of the target node
//     bit  [31]     sub  (1)    set when this slot holds a substitution
//     bits [30..4]  label (27)  DUP/SUP color
//     bits [3..0]   tag  (4)    VAR LAM APP ERA SUP DP0 DP1
//
//   build: zig build-exe -OReleaseFast runtime/zig/ic32.zig -femit-bin=runtime/zig/ic32z
//   use:   echo 'TERM' | ./runtime/zig/ic32z
const std = @import("std");

const Term = u64;

const T_VAR: u64 = 0;
const T_LAM: u64 = 1;
const T_APP: u64 = 2;
const T_ERA: u64 = 3;
const T_SUP: u64 = 4;
const T_DP0: u64 = 5;
const T_DP1: u64 = 6;

const SUBF: u64 = 1 << 31;

inline fn TAG(t: Term) u64 {
    return t & 0xF;
}
inline fn LAB(t: Term) u32 {
    return @truncate((t >> 4) & 0x7FFFFFF);
}
inline fn ADDR(t: Term) u32 {
    return @truncate(t >> 32);
}
inline fn ISSUB(t: Term) bool {
    return (t & SUBF) != 0;
}
inline fn SETSUB(t: Term) Term {
    return t | SUBF;
}
inline fn CLRSUB(t: Term) Term {
    return t & ~SUBF;
}
inline fn MK(tag: u64, lab: u32, addr: u32) Term {
    return (tag & 0xF) | (@as(u64, lab & 0x7FFFFFF) << 4) | (@as(u64, addr) << 32);
}

const gpa = std.heap.page_allocator;

fn fatal(comptime msg: []const u8, code: u8) noreturn {
    errWrite("FATAL: " ++ msg ++ "\n");
    std.process.exit(code);
}

// ---------------------------------------------------------------- tiny growable vector
// Hand-rolled rather than `std.ArrayList` on purpose: ArrayList's managed/unmanaged
// split moved between Zig releases, and a conformance backend that stops building on
// a toolchain bump is not a backend. This uses only `Allocator.alloc/realloc`, which
// has been stable across every version that can compile the rest of this file.
fn Vec(comptime T: type) type {
    return struct {
        items: []T = &[_]T{},
        len: usize = 0,

        const Self = @This();

        fn ensure(self: *Self, need: usize) void {
            if (need <= self.items.len) return;
            var c: usize = if (self.items.len != 0) self.items.len * 2 else 1024;
            while (c < need) c *= 2;
            if (self.items.len == 0) {
                self.items = gpa.alloc(T, c) catch fatal("out of memory", 2);
            } else {
                self.items = gpa.realloc(self.items, c) catch fatal("out of memory", 2);
            }
        }
        fn push(self: *Self, v: T) void {
            self.ensure(self.len + 1);
            self.items[self.len] = v;
            self.len += 1;
        }
        fn pop(self: *Self) T {
            self.len -= 1;
            return self.items[self.len];
        }
        fn slice(self: *Self) []T {
            return self.items[0..self.len];
        }
    };
}

// ---------------------------------------------------------------- io
fn writeAll(fd: std.posix.fd_t, bytes: []const u8) void {
    var i: usize = 0;
    while (i < bytes.len) {
        const n = std.posix.write(fd, bytes[i..]) catch return;
        if (n == 0) return;
        i += n;
    }
}
fn outWrite(bytes: []const u8) void {
    writeAll(1, bytes);
}
fn errWrite(bytes: []const u8) void {
    writeAll(2, bytes);
}

// `src` is expected to include its own NUL, so anything handed to the parser
// has to be copied with one appended; the returned slice INCLUDES the NUL.
fn zdup(s: []const u8) []u8 {
    const b = gpa.alloc(u8, s.len + 1) catch fatal("out of memory", 2);
    @memcpy(b[0..s.len], s);
    b[s.len] = 0;
    return b[0 .. s.len + 1];
}

fn readWholeFile(path: []const u8) []u8 {
    const f = std.fs.cwd().openFile(path, .{}) catch fatal("cannot open file", 3);
    defer f.close();
    const sz = f.getEndPos() catch fatal("cannot stat file", 3);
    const b = gpa.alloc(u8, @intCast(sz)) catch fatal("out of memory", 2);
    const n = f.readAll(b) catch fatal("short read", 3);
    return b[0..n];
}

// ---------------------------------------------------------------- heap
var heap: []Term = undefined;
var hp: u32 = 1; // 0 == null; also the high-water mark (only grows)
const HEAPCAP: u32 = 1 << 24; // 16M slots
var interactions: i64 = 0;
const STEPCAP: i64 = 50_000_000;

// Free lists for slot recycling, exactly the C runtime's two size classes: 1-word
// cells and 2-word nodes. Interaction-net reduction is confluent and local, so a
// consumed redex node is dead the instant its rule fires -- no tracing, no pauses.
var free1 = Vec(u32){};
var free2 = Vec(u32){};
var live: i64 = 0;
var peak_live: i64 = 0;
var allocs: i64 = 0;
var gc_on: bool = true;

inline fn FREE1(a: u32) void {
    free1.push(a);
    live -= 1;
}
inline fn FREE2(a: u32) void {
    free2.push(a);
    live -= 2;
}

fn alloc_n(n: u32) u32 {
    allocs += n;
    live += n;
    if (live > peak_live) peak_live = live;
    if (gc_on and n == 1 and free1.len > 0) return free1.pop();
    if (gc_on and n == 2 and free2.len > 0) return free2.pop();
    const a = hp;
    hp += n;
    if (hp >= HEAPCAP) fatal("heap overflow", 2);
    return a;
}

fn check_steps() void {
    if (interactions > STEPCAP) {
        outWrite("DIVERGES(step-cap)\n");
        std.process.exit(3);
    }
}

// ---------------------------------------------------------------- reduction

// fire a floating DUP node at slot D, color L, demanded from side k (0|1)
fn fire(D: u32, L: u32, k: u32) Term {
    interactions += 1;
    check_steps();
    const v = whnf(heap[D]);
    const vt = TAG(v);
    var h0: Term = 0;
    var h1: Term = 0;
    if (vt == T_SUP) {
        const S = ADDR(v);
        const vl = LAB(v);
        const a = heap[S];
        const b = heap[S + 1];
        if (vl == L) { // DUP-SUP equal: annihilate
            h0 = a;
            h1 = b;
        } else { // DUP-SUP different: commute
            const Da = alloc_n(1);
            heap[Da] = a;
            const Db = alloc_n(1);
            heap[Db] = b;
            const S0 = alloc_n(2);
            heap[S0] = MK(T_DP0, L, Da);
            heap[S0 + 1] = MK(T_DP0, L, Db);
            const S1 = alloc_n(2);
            heap[S1] = MK(T_DP1, L, Da);
            heap[S1 + 1] = MK(T_DP1, L, Db);
            h0 = MK(T_SUP, vl, S0);
            h1 = MK(T_SUP, vl, S1);
        }
        FREE2(S); // the consumed superposition node is dead
    } else if (vt == T_LAM) { // DUP-LAM
        const Lv = ADDR(v);
        const Lx0 = alloc_n(1);
        const Lx1 = alloc_n(1);
        const Df = alloc_n(1);
        heap[Df] = heap[Lv]; // salvage body, dup it
        heap[Lx0] = MK(T_DP0, L, Df);
        heap[Lx1] = MK(T_DP1, L, Df);
        const Ss = alloc_n(2);
        heap[Ss] = MK(T_VAR, 0, Lx0);
        heap[Ss + 1] = MK(T_VAR, 0, Lx1);
        heap[Lv] = SETSUB(MK(T_SUP, L, Ss)); // the lambda's var becomes a superposition
        h0 = MK(T_LAM, 0, Lx0);
        h1 = MK(T_LAM, 0, Lx1);
    } else if (vt == T_ERA) { // DUP-ERA
        h0 = MK(T_ERA, 0, 0);
        h1 = MK(T_ERA, 0, 0);
    } else if (vt == T_APP) { // DUP-APP (collapse): copy structure
        const A = ADDR(v);
        const f = heap[A];
        const a = heap[A + 1];
        const Df = alloc_n(1);
        heap[Df] = f;
        const Dx = alloc_n(1);
        heap[Dx] = a;
        const A0 = alloc_n(2);
        heap[A0] = MK(T_DP0, L, Df);
        heap[A0 + 1] = MK(T_DP0, L, Dx);
        const A1 = alloc_n(2);
        heap[A1] = MK(T_DP1, L, Df);
        heap[A1 + 1] = MK(T_DP1, L, Dx);
        h0 = MK(T_APP, 0, A0);
        h1 = MK(T_APP, 0, A1);
        FREE2(A); // the consumed application node is dead
    } else { // VAR free/stuck: DUP-VAR copy
        h0 = v;
        h1 = v;
    }
    if (k == 0) {
        heap[D] = SETSUB(h1);
        return h0;
    } else {
        heap[D] = SETSUB(h0);
        return h1;
    }
}

// (&L{a,b} c) -> !&L{c0,c1}=c; &L{(a c0),(b c1)}
fn app_sup(sup: Term, arg: Term) Term {
    interactions += 1;
    check_steps();
    const S = ADDR(sup);
    const L = LAB(sup);
    const a = heap[S];
    const b = heap[S + 1];
    const Dc = alloc_n(1);
    heap[Dc] = arg;
    const Aa = alloc_n(2);
    heap[Aa] = a;
    heap[Aa + 1] = MK(T_DP0, L, Dc);
    const Ab = alloc_n(2);
    heap[Ab] = b;
    heap[Ab + 1] = MK(T_DP1, L, Dc);
    const Sn = alloc_n(2);
    heap[Sn] = MK(T_APP, 0, Aa);
    heap[Sn + 1] = MK(T_APP, 0, Ab);
    FREE2(S); // the consumed superposition node is dead
    return MK(T_SUP, L, Sn);
}

// Eraser propagation: free the uniquely-owned sub-net rooted at t (the argument
// discarded by APP-ERA). Safe because IC sharing happens ONLY through DUP nodes, so
// this frees the APP/SUP/LAM spine above any dup and STOPS at DUP/VAR/ERA. Iterative,
// matching the C runtime's deep-robustness. The same honest limit applies: under lazy
// normalization a discarded argument is frequently an unevaluated VAR rather than
// built structure, so this reclaims only the already-built spine.
var cstk = Vec(Term){};
var erase_on: bool = true;

fn collect(root: Term) void {
    if (!erase_on) return;
    cstk.len = 0;
    cstk.push(root);
    while (cstk.len > 0) {
        const t = cstk.pop();
        const tag = TAG(t);
        if (tag == T_APP) {
            const A = ADDR(t);
            cstk.push(heap[A]);
            cstk.push(heap[A + 1]);
            FREE2(A);
        } else if (tag == T_SUP) {
            const S = ADDR(t);
            cstk.push(heap[S]);
            cstk.push(heap[S + 1]);
            FREE2(S);
        } else if (tag == T_LAM) {
            const Lv = ADDR(t);
            cstk.push(heap[Lv]);
            FREE1(Lv);
        }
        // T_VAR, T_DP0, T_DP1, T_ERA: stop (target may be shared or bound elsewhere).
    }
}

fn whnf(t0: Term) Term {
    var t = t0;
    while (true) {
        const tag = TAG(t);
        if (tag == T_VAR) {
            const w = heap[ADDR(t)];
            if (ISSUB(w)) {
                t = CLRSUB(w);
                continue;
            }
            return t; // free / unsubstituted
        }
        if (tag == T_DP0 or tag == T_DP1) {
            const D = ADDR(t);
            const w = heap[D];
            if (ISSUB(w)) { // sibling already fired
                t = CLRSUB(w);
                continue;
            }
            t = fire(D, LAB(t), if (tag == T_DP0) 0 else 1);
            continue;
        }
        if (tag == T_APP) {
            const A = ADDR(t);
            const f = whnf(heap[A]);
            const ft = TAG(f);
            if (ft == T_LAM) { // APP-LAM
                interactions += 1;
                check_steps();
                const Lv = ADDR(f);
                const arg = heap[A + 1];
                const bod = heap[Lv];
                heap[Lv] = SETSUB(arg);
                FREE2(A); // the consumed application node is dead
                t = bod;
                continue;
            }
            if (ft == T_SUP) {
                t = app_sup(f, heap[A + 1]);
                FREE2(A);
                continue;
            }
            if (ft == T_ERA) {
                interactions += 1;
                check_steps();
                collect(heap[A + 1]);
                FREE2(A);
                t = MK(T_ERA, 0, 0);
                continue;
            }
            heap[A] = f; // stuck: memoize reduced fun
            return MK(T_APP, 0, A);
        }
        return t; // LAM, SUP, ERA
    }
}

// Iterative full normaliser: an explicit stack of heap SLOT INDICES. The C runtime
// stores raw `Term*` pointers here; indices are used instead because `heap` is a Zig
// slice and an index is checked, while the guarantee that makes the C pointers safe
// (the heap is fixed-size and never reallocated) is preserved either way. The root is
// a file-level var for the same reason C used `static`: it needs a stable address.
var nstk = Vec(u32){};
var norm_root: Term = 0;
const ROOT_SLOT: u32 = 0xFFFF_FFFF; // sentinel: "the root, not a heap slot"

inline fn slotGet(i: u32) Term {
    return if (i == ROOT_SLOT) norm_root else heap[i];
}
inline fn slotSet(i: u32, v: Term) void {
    if (i == ROOT_SLOT) norm_root = v else heap[i] = v;
}

fn normal(t: Term) Term {
    norm_root = t;
    nstk.len = 0;
    nstk.push(ROOT_SLOT);
    while (nstk.len > 0) {
        const slot = nstk.pop();
        const v = whnf(slotGet(slot));
        slotSet(slot, v);
        const tag = TAG(v);
        if (tag == T_LAM) {
            nstk.push(ADDR(v));
        } else if (tag == T_APP) {
            const A = ADDR(v);
            nstk.push(A);
            nstk.push(A + 1);
        } else if (tag == T_SUP) {
            const S = ADDR(v);
            nstk.push(S);
            nstk.push(S + 1);
        }
    }
    return norm_root;
}

// ---------------------------------------------------------------- naming
const Name = struct { buf: [40]u8 = undefined, len: usize = 0 };

fn nameSet(n: *Name, s: []const u8) void {
    const k = @min(s.len, 39);
    @memcpy(n.buf[0..k], s[0..k]);
    n.len = k;
}
fn nameSlice(n: *const Name) []const u8 {
    return n.buf[0..n.len];
}

// free-var slots and their names (set at parse time)
var free_loc = Vec(u32){};
var free_nm = Vec(Name){};
// binder-name assignment during stringify
var bnd_loc = Vec(u32){};
var bnd_nm = Vec(Name){};
var name_ctr: u32 = 0;

fn free_lookup(loc: u32) ?[]const u8 {
    var i: usize = 0;
    while (i < free_loc.len) : (i += 1) {
        if (free_loc.items[i] == loc) return nameSlice(&free_nm.items[i]);
    }
    return null;
}

fn free_intern(nm: []const u8) u32 {
    var i: usize = 0;
    while (i < free_loc.len) : (i += 1) {
        if (std.mem.eql(u8, nameSlice(&free_nm.items[i]), nm)) return free_loc.items[i];
    }
    const L = alloc_n(1);
    heap[L] = MK(T_ERA, 0, 0); // sentinel (sub-clear => free)
    var n = Name{};
    nameSet(&n, nm);
    free_loc.push(L);
    free_nm.push(n);
    return L;
}

fn bnd_name(loc: u32) []const u8 {
    var i: usize = 0;
    while (i < bnd_loc.len) : (i += 1) {
        if (bnd_loc.items[i] == loc) return nameSlice(&bnd_nm.items[i]);
    }
    var n = Name{};
    const idx = name_ctr;
    name_ctr += 1;
    if (idx < 26) {
        n.buf[0] = @intCast('a' + idx);
        n.len = 1;
    } else {
        const s = std.fmt.bufPrint(n.buf[0..], "v{d}", .{idx}) catch unreachable;
        n.len = s.len;
    }
    bnd_loc.push(loc);
    bnd_nm.push(n);
    return nameSlice(&bnd_nm.items[bnd_nm.len - 1]);
}

// ---------------------------------------------------------------- parser
const Bind = struct { nm: Name = .{}, t: Term = 0 };
var scope = Vec(Bind){};

const DupNames = struct { a: Name = .{}, b: Name = .{} };
var dnstk = Vec(DupNames){};

const OP_PARSE: u32 = 0;
const OP_APP: u32 = 1;
const OP_SUP: u32 = 2;
const OP_LAM: u32 = 3;
const OP_DUPVAL: u32 = 4;
const OP_DUPBODY: u32 = 5;
const OP_EXPECT: u32 = 6;

const Ins = struct { op: u32, x: u32, y: u32 };

// parse cursor: `src` is NUL-terminated, so `cur()` is total and the C `*P` idiom
// ports directly without a bounds test at every read site.
var src: []const u8 = "";
var P: usize = 0;

inline fn cur() u8 {
    return src[P];
}

fn perr(comptime m: []const u8) noreturn {
    errWrite("parse error: " ++ m ++ "\n");
    std.process.exit(4);
}

fn ws() void {
    while (cur() == ' ' or cur() == '\t' or cur() == '\n' or cur() == '\r') P += 1;
}
fn is_lambda() bool {
    return cur() == '\\' or (src[P] == 0xCE and P + 1 < src.len and src[P + 1] == 0xBB);
}
fn eat_lambda() void {
    if (cur() == '\\') P += 1 else P += 2;
}
fn expect(c: u8) void {
    ws();
    if (cur() != c) perr("expected char");
    P += 1;
}
fn rdname(out: *Name) void {
    ws();
    var i: usize = 0;
    while ((cur() >= 'a' and cur() <= 'z') or (cur() >= 'A' and cur() <= 'Z') or
        (cur() >= '0' and cur() <= '9') or cur() == '_')
    {
        if (i < 39) {
            out.buf[i] = cur();
            i += 1;
        }
        P += 1;
    }
    out.len = i;
    if (i == 0) perr("expected name");
}
fn rduint() u32 {
    ws();
    var v: u32 = 0;
    while (cur() >= '0' and cur() <= '9') {
        v = v * 10 + (cur() - '0');
        P += 1;
    }
    return v;
}

// Iterative recursive-descent: an instruction stack drives parsing, a value stack
// collects sub-results. No host recursion, so input of arbitrary nesting depth parses
// without overflowing the stack. Scope bindings are pushed/popped by OP_LAM /
// OP_DUPVAL+OP_DUPBODY at exactly the points the recursive formulation would.
var istk = Vec(Ins){};
var vstk = Vec(Term){};

fn parse_term() Term {
    istk.len = 0;
    vstk.len = 0;
    istk.push(.{ .op = OP_PARSE, .x = 0, .y = 0 });
    while (istk.len > 0) {
        const in = istk.pop();
        switch (in.op) {
            OP_PARSE => {
                ws();
                if (is_lambda()) {
                    eat_lambda();
                    var nm = Name{};
                    rdname(&nm);
                    expect('.');
                    const L = alloc_n(1);
                    scope.push(.{ .nm = nm, .t = MK(T_VAR, 0, L) });
                    istk.push(.{ .op = OP_LAM, .x = L, .y = 0 }); // finish: heap[L]=body
                    istk.push(.{ .op = OP_PARSE, .x = 0, .y = 0 }); // parse body
                    continue;
                }
                const c = cur();
                if (c == '*') {
                    P += 1;
                    vstk.push(MK(T_ERA, 0, 0));
                    continue;
                }
                if (c == '(') {
                    P += 1;
                    istk.push(.{ .op = OP_APP, .x = 0, .y = 0 }); // finish: eat ')', build APP
                    istk.push(.{ .op = OP_PARSE, .x = 0, .y = 0 }); // parse arg
                    istk.push(.{ .op = OP_PARSE, .x = 0, .y = 0 }); // parse fun (runs first)
                    continue;
                }
                if (c == '&' or c == '{') {
                    var lab: u32 = 0;
                    if (c == '&') {
                        P += 1;
                        lab = rduint();
                        expect('{');
                    } else {
                        P += 1;
                    }
                    istk.push(.{ .op = OP_SUP, .x = lab, .y = 0 }); // finish: eat '}', build SUP
                    istk.push(.{ .op = OP_PARSE, .x = 0, .y = 0 }); // parse right
                    istk.push(.{ .op = OP_EXPECT, .x = ',', .y = 0 }); // eat ','
                    istk.push(.{ .op = OP_PARSE, .x = 0, .y = 0 }); // parse left (runs first)
                    continue;
                }
                if (c == '!') {
                    P += 1;
                    var lab: u32 = 0;
                    ws();
                    if (cur() == '&') {
                        P += 1;
                        lab = rduint();
                    }
                    expect('{');
                    var a = Name{};
                    var b = Name{};
                    rdname(&a);
                    expect(',');
                    rdname(&b);
                    expect('}');
                    expect('=');
                    const D = alloc_n(1);
                    dnstk.push(.{ .a = a, .b = b });
                    istk.push(.{ .op = OP_DUPBODY, .x = 0, .y = 0 }); // pop the projections
                    istk.push(.{ .op = OP_PARSE, .x = 0, .y = 0 }); // parse body
                    istk.push(.{ .op = OP_DUPVAL, .x = D, .y = lab }); // heap[D]=val, eat ';'
                    istk.push(.{ .op = OP_PARSE, .x = 0, .y = 0 }); // parse val (runs first)
                    continue;
                }
                var nm = Name{}; // variable
                rdname(&nm);
                var found = false;
                var i: usize = scope.len;
                while (i > 0) {
                    i -= 1;
                    if (std.mem.eql(u8, nameSlice(&scope.items[i].nm), nameSlice(&nm))) {
                        vstk.push(scope.items[i].t);
                        found = true;
                        break;
                    }
                }
                if (!found) vstk.push(MK(T_VAR, 0, free_intern(nameSlice(&nm))));
            },
            OP_APP => {
                const a = vstk.pop();
                const f = vstk.pop();
                expect(')');
                const A = alloc_n(2);
                heap[A] = f;
                heap[A + 1] = a;
                vstk.push(MK(T_APP, 0, A));
            },
            OP_SUP => {
                const r = vstk.pop();
                const l = vstk.pop();
                expect('}');
                const S = alloc_n(2);
                heap[S] = l;
                heap[S + 1] = r;
                vstk.push(MK(T_SUP, in.x, S));
            },
            OP_LAM => {
                const bod = vstk.pop();
                heap[in.x] = bod;
                scope.len -= 1; // pop the lambda's binding
                vstk.push(MK(T_LAM, 0, in.x));
            },
            OP_DUPVAL => {
                const val = vstk.pop();
                heap[in.x] = val;
                expect(';');
                const dn = dnstk.pop();
                scope.push(.{ .nm = dn.a, .t = MK(T_DP0, in.y, in.x) });
                scope.push(.{ .nm = dn.b, .t = MK(T_DP1, in.y, in.x) });
                // the dup floats; the body becomes the form's value
            },
            OP_DUPBODY => {
                scope.len -= 2; // pop the two projection bindings
            },
            OP_EXPECT => {
                expect(@intCast(in.x));
            },
            else => unreachable,
        }
    }
    return vstk.items[0];
}

// ---------------------------------------------------------------- stringify (iterative)
var sb = Vec(u8){};

fn sb_reset() void {
    sb.len = 0;
}
fn sb_putc(c: u8) void {
    sb.push(c);
}
fn sb_puts(s: []const u8) void {
    for (s) |c| sb.push(c);
}

// work item: render a Term (kind 0) or emit a literal (kind 1)
const WI = struct { kind: u32, t: Term, lit: []const u8 };
var wstk = Vec(WI){};

// iterative readback -- no recursion, so arbitrarily deep normal forms read back safely
fn show_iter(t: Term) void {
    sb_reset();
    wstk.len = 0;
    wstk.push(.{ .kind = 0, .t = t, .lit = "" });
    while (wstk.len > 0) {
        const w = wstk.pop();
        if (w.kind == 1) {
            sb_puts(w.lit);
            continue;
        }
        const x = w.t;
        const tag = TAG(x);
        if (tag == T_VAR) {
            const L = ADDR(x);
            if (free_lookup(L)) |f| sb_puts(f) else sb_puts(bnd_name(L));
        } else if (tag == T_ERA) {
            sb_putc('*');
        } else if (tag == T_LAM) {
            const L = ADDR(x);
            sb_putc(0xce);
            sb_putc(0xbb);
            sb_puts(bnd_name(L));
            sb_putc('.');
            wstk.push(.{ .kind = 0, .t = heap[L], .lit = "" }); // body renders next
        } else if (tag == T_APP) {
            const A = ADDR(x);
            sb_putc('('); // push reversed: f, " ", a, ")"
            wstk.push(.{ .kind = 1, .t = 0, .lit = ")" });
            wstk.push(.{ .kind = 0, .t = heap[A + 1], .lit = "" });
            wstk.push(.{ .kind = 1, .t = 0, .lit = " " });
            wstk.push(.{ .kind = 0, .t = heap[A], .lit = "" });
        } else if (tag == T_SUP) {
            const S = ADDR(x);
            var tmp: [24]u8 = undefined;
            const s = std.fmt.bufPrint(tmp[0..], "&{d}{{", .{LAB(x)}) catch unreachable;
            sb_puts(s);
            wstk.push(.{ .kind = 1, .t = 0, .lit = "}" });
            wstk.push(.{ .kind = 0, .t = heap[S + 1], .lit = "" });
            wstk.push(.{ .kind = 1, .t = 0, .lit = "," });
            wstk.push(.{ .kind = 0, .t = heap[S], .lit = "" });
        } else if (tag == T_DP0) {
            sb_puts("DP0");
        } else if (tag == T_DP1) {
            sb_puts("DP1");
        } else {
            sb_putc('?');
        }
    }
}

// ---------------------------------------------------------------- state reset
// Two groups, and the distinction is load-bearing for the fold mode below.
// This mirrors `runtime/c/ic32.c` exactly, for the same reason the rest of this
// file does: two implementations that split the state differently would
// disagree for reasons that tell you nothing about the model.
//
// TRANSIENT state is scratch that one parse or one stringify builds and
// consumes within the same call. Zeroing it is always correct.
//
// PERSISTENT state is built by the parser and read back later by the
// stringifier. The free-name intern table is the whole of it: free_intern()
// allocates a heap slot per free name AND records the slot<->name association
// in a side table that does not live in the heap. A restore that copies the
// heap back but clears that table leaves the slot with no name, so show_iter()
// falls through to bnd_name() and invents a binder name for a free variable --
// and two distinct free variables can then print as one identifier.
//
// bnd_loc/bnd_nm/name_ctr look like they belong to the persistent group and do
// not: bnd_name() is called only from the stringifier, so they are display
// state assigned during readback and MUST be cleared.
fn resetTransient() void {
    interactions = 0;
    bnd_loc.len = 0;
    bnd_nm.len = 0;
    name_ctr = 0;
    scope.len = 0;
    dnstk.len = 0;
    free1.len = 0;
    free2.len = 0;
    allocs = 0;
}
fn reset_state() void {
    resetTransient();
    free_loc.len = 0; // persistent group
    free_nm.len = 0;
    hp = 1;
    live = 0;
    peak_live = 0;
}

// ---------------------------------------------------------------- SnapshotV1
// Path A: parse a fixed term once, keep the heap slots it occupies, and restore
// them per epoch instead of re-parsing. The image alone is not the snapshot --
// see the note on the persistent group above.
const SNAPSHOT_SCHEMA: u32 = 1;

const SnapshotV1 = struct {
    schema: u32 = 0, // 0 => an unpopulated snapshot is REFUSED, not read
    step_hash: u64 = 0,
    hp: u32 = 1,
    live: i64 = 0,
    img: []Term = &[_]Term{},
    free_loc: []u32 = &[_]u32{},
    free_nm: []Name = &[_]Name{},
};

fn snapshotHash(s: []const u8) u64 {
    var h: u64 = 1469598103934665603; // FNV-1a 64
    for (s) |c| {
        h ^= c;
        h *%= 1099511628211;
    }
    return h;
}

// Must be called immediately after parsing the step term and BEFORE any
// reduction. Taking it there is what makes clearing the allocator free lists
// correct rather than accidentally correct: every push onto free1/free2 happens
// inside a reduction rule and none in the parser, so at this point the lists
// are provably empty.
fn snapshotCapture(step_src: []const u8) SnapshotV1 {
    var s = SnapshotV1{};
    s.schema = SNAPSHOT_SCHEMA;
    s.step_hash = snapshotHash(step_src);
    s.hp = hp;
    s.live = live;
    s.img = gpa.alloc(Term, hp) catch fatal("out of memory", 2);
    @memcpy(s.img, heap[0..hp]);
    const nf = free_loc.len;
    s.free_loc = gpa.alloc(u32, nf + 1) catch fatal("out of memory", 2);
    s.free_nm = gpa.alloc(Name, nf + 1) catch fatal("out of memory", 2);
    s.free_loc = s.free_loc[0..nf];
    s.free_nm = s.free_nm[0..nf];
    @memcpy(s.free_loc, free_loc.items[0..nf]);
    @memcpy(s.free_nm, free_nm.items[0..nf]);
    return s;
}

// Returns 0 on success, nonzero on refusal. The caller passes the hash of the
// term it believes the snapshot describes; it is a precomputed integer rather
// than the source bytes because re-hashing a multi-megabyte term every epoch
// would cost more than the parse this mode exists to avoid.
fn snapshotRestore(s: *const SnapshotV1, step_hash: u64) u8 {
    if (s.schema != SNAPSHOT_SCHEMA) return 1;
    if (s.step_hash != step_hash) return 2;
    @memcpy(heap[0..s.hp], s.img);
    hp = s.hp;
    live = s.live;
    peak_live = s.live;
    resetTransient();
    free_loc.len = 0;
    free_nm.len = 0;
    for (s.free_loc) |v| free_loc.push(v);
    for (s.free_nm) |v| free_nm.push(v);
    return 0;
}

// ---------------------------------------------------------------- self-test

fn one_test(in: [:0]const u8, want: []const u8) bool {
    reset_state();
    src = in[0 .. in.len + 1];
    P = 0;
    const t = parse_term();
    ws();
    const nf = normal(t);
    show_iter(nf);
    const okv = std.mem.eql(u8, sb.slice(), want);
    var line: [256]u8 = undefined;
    const s = std.fmt.bufPrint(line[0..], "  [{s}] {s}\n", .{ if (okv) "PASS" else "FAIL", in }) catch "  [??]\n";
    outWrite(s);
    if (!okv) {
        const s2 = std.fmt.bufPrint(line[0..], "         got '{s}' want '{s}'\n", .{ sb.slice(), want }) catch "\n";
        outWrite(s2);
    }
    return okv;
}

// linear church numeral with an explicit duplicator label (the encoding a compiler emits)
fn clin_str(n: i32, lab: i32, out: []u8) []u8 {
    var w: usize = 0;
    w += (std.fmt.bufPrint(out[w..], "\\f.\\x.", .{}) catch unreachable).len;
    if (n <= 1) {
        w += (std.fmt.bufPrint(out[w..], "(f x)", .{}) catch unreachable).len;
        return out[0..w];
    }
    var cur_buf: [24]u8 = undefined;
    var curname: []const u8 = "f";
    var i: i32 = 0;
    while (i < n - 1) : (i += 1) {
        if (i < n - 2) {
            w += (std.fmt.bufPrint(out[w..], "!&{d}{{a{d},t{d}}}={s};", .{ lab, i, i, curname }) catch unreachable).len;
            curname = std.fmt.bufPrint(cur_buf[0..], "t{d}", .{i}) catch unreachable;
        } else {
            w += (std.fmt.bufPrint(out[w..], "!&{d}{{a{d},a{d}}}={s};", .{ lab, i, i + 1, curname }) catch unreachable).len;
        }
    }
    i = 0;
    while (i < n) : (i += 1) {
        w += (std.fmt.bufPrint(out[w..], "(a{d} ", .{i}) catch unreachable).len;
    }
    out[w] = 'x';
    w += 1;
    i = 0;
    while (i < n) : (i += 1) {
        out[w] = ')';
        w += 1;
    }
    return out[0..w];
}

/// `(g (g ... (g z)))` built directly in the heap, k applications deep. Bypassing the
/// parser is the point: the input buffer, not the normaliser, is what caps the depth a
/// parsed term can reach, so this reaches past it.
fn build_deep(k: usize) Term {
    const g = free_intern("g");
    const z = free_intern("z");
    var acc = MK(T_VAR, 0, z);
    var i: usize = 0;
    while (i < k) : (i += 1) {
        const A = alloc_n(2);
        heap[A] = MK(T_VAR, 0, g);
        heap[A + 1] = acc;
        acc = MK(T_APP, 0, A);
    }
    return acc;
}

fn count_sub(hay: []const u8, needle: []const u8) usize {
    if (needle.len == 0 or hay.len < needle.len) return 0;
    var c: usize = 0;
    var i: usize = 0;
    while (i + needle.len <= hay.len) : (i += 1) {
        if (std.mem.eql(u8, hay[i .. i + needle.len], needle)) c += 1;
    }
    return c;
}

fn run_tests() u8 {
    outWrite("ic32.zig self-test battery\n");
    const Case = struct { in: [:0]const u8, out: []const u8 };
    const cases = [_]Case{
        .{ .in = "(\\x.x a)", .out = "a" }, // beta / app-lam
        .{ .in = "((\\x.\\y.x a) b)", .out = "a" }, // nested app-lam
        .{ .in = "!&0{a,b}=*;\\q.q", .out = "\xce\xbba.a" }, // DUP-ERA
        .{ .in = "((\\f.\\x.(f (f x)) \\y.y) z)", .out = "z" }, // church2 of identity
        .{ .in = "&3{a,b}", .out = "&3{a,b}" }, // sup is normal
        .{ .in = "!&0{a,b}=\\x.x;(a b)", .out = "\xce\xbba.a" }, // dup a lambda, then apply
        .{ .in = "((\\f.\\x.(f (f x)) g) z)", .out = "(g (g z))" }, // church2 on a free var
        .{ .in = "((\\f.\\x.!&0{a,b}=f;(a (b x)) g) z)", .out = "(g (g z))" }, // explicit dup
    };
    var tot: u32 = 0;
    var pass: u32 = 0;
    for (cases) |c| {
        tot += 1;
        if (one_test(c.in, c.out)) pass += 1;
    }

    // Church arithmetic with the proper IC encoding (explicit dups + DISTINCT duplicator
    // labels -- what a compiler emits). Naive single-label numerals reduce incorrectly by
    // design; that is an input-encoding property of interaction nets, not a runtime defect,
    // which is why the conformance vectors are also restricted to the labeling discipline.
    outWrite("  --- church arithmetic (explicit dups, distinct labels) ---\n");
    {
        const a = gpa.alloc(u8, 4096) catch fatal("out of memory", 2);
        const b = gpa.alloc(u8, 4096) catch fatal("out of memory", 2);
        const term = gpa.alloc(u8, 16384) catch fatal("out of memory", 2);
        const AC = struct { x: i32, y: i32, exp: bool, want: usize, label: []const u8 };
        const arith = [_]AC{
            .{ .x = 7, .y = 3, .exp = false, .want = 21, .label = "mult 7*3" },
            .{ .x = 3, .y = 2, .exp = true, .want = 8, .label = "exp 2^3" },
            .{ .x = 2, .y = 5, .exp = true, .want = 25, .label = "exp 5^2" },
        };
        for (arith) |c| {
            const sa = clin_str(c.x, 1, a);
            const sb2 = clin_str(c.y, 0, b);
            const s = if (c.exp)
                std.fmt.bufPrint(term, "((({s} {s}) s) z)\x00", .{ sa, sb2 }) catch unreachable
            else
                std.fmt.bufPrint(term, "(({s} ({s} s)) z)\x00", .{ sa, sb2 }) catch unreachable;
            reset_state();
            src = s;
            P = 0;
            const t0 = parse_term();
            ws();
            show_iter(normal(t0));
            const got = count_sub(sb.slice(), "(s ");
            const okv = (got == c.want);
            tot += 1;
            if (okv) pass += 1;
            var ln: [160]u8 = undefined;
            outWrite(std.fmt.bufPrint(ln[0..], "  [{s}] {s}: s^{d} (expected s^{d})\n", .{ if (okv) "PASS" else "FAIL", c.label, got, c.want }) catch "\n");
        }
    }

    // deep stress: iterative PARSER + normaliser + readback, end-to-end. A recursive
    // descent parser overflows the host stack around ~4k nesting; this parses 200k-deep
    // input, normalizes it, and reads it back.
    outWrite("  --- deep stress: iterative parser + normal + readback ---\n");
    reset_state();
    const KP: usize = 200000;
    const big = gpa.alloc(u8, KP * 4 + 16) catch fatal("out of memory", 2);
    var bp: usize = 0;
    var i: usize = 0;
    while (i < KP) : (i += 1) {
        big[bp] = '(';
        big[bp + 1] = 'f';
        big[bp + 2] = ' ';
        bp += 3;
    }
    big[bp] = 'x';
    bp += 1;
    i = 0;
    while (i < KP) : (i += 1) {
        big[bp] = ')';
        bp += 1;
    }
    big[bp] = 0;
    src = big[0 .. bp + 1];
    P = 0;
    const pt = parse_term();
    ws();
    const pnf = normal(pt);
    show_iter(pnf);
    const papps = count_sub(sb.slice(), "(f ");
    const deep_ok = (papps == KP);
    tot += 1;
    if (deep_ok) pass += 1;
    var line: [256]u8 = undefined;
    outWrite(std.fmt.bufPrint(line[0..], "  [{s}] (f^{d} x): parsed + normalized + read back {d} bytes, {d} applications\n", .{ if (deep_ok) "PASS" else "FAIL", KP, sb.len, papps }) catch "\n");

    // deep stress 2: build the spine IN THE HEAP rather than through the parser, so the
    // depth is not bounded by what an input buffer can hold. Exercises the iterative
    // normaliser and readback alone at half a million deep.
    outWrite("  --- deep stress: iterative normal + readback at half a million deep ---\n");
    reset_state();
    const K: usize = 500000;
    const deep = build_deep(K);
    const dnf = normal(deep);
    show_iter(dnf);
    const gc = count_sub(sb.slice(), "(g ");
    const deep2_ok = (gc == K);
    tot += 1;
    if (deep2_ok) pass += 1;
    outWrite(std.fmt.bufPrint(line[0..], "  [{s}] g^{d} z: normalized + read back {d} bytes, {d} applications\n", .{ if (deep2_ok) "PASS" else "FAIL", K, sb.len, gc }) catch "\n");

    outWrite(std.fmt.bufPrint(line[0..], "  --- summary: {d}/{d} passed ---\n", .{ pass, tot }) catch "\n");
    return if (pass == tot) 0 else 1;
}

// ---------------------------------------------------------------- main
pub fn main() void {
    heap = gpa.alloc(Term, HEAPCAP) catch fatal("heap alloc", 2);
    @memset(heap, 0);

    const argv = std.process.argsAlloc(gpa) catch fatal("args", 2);
    const arg1: []const u8 = if (argv.len > 1) argv[1] else "";

    if (std.mem.eql(u8, arg1, "--test")) std.process.exit(run_tests());

    // ------------------------------------------------------------- fold mode
    // An EXPLICIT mode, requested by name. The one-shot stdin path below is
    // unchanged and still parses directly, so the conformance contract this
    // file exists to satisfy is untouched.
    //
    //   ic32z -fold    stepfile argsfile    parse the step once, restore per epoch
    //   ic32z -reparse stepfile argsfile    re-parse the whole term per epoch
    //
    // -reparse is not a benchmark comparand. It is the behaviour -fold proposes
    // to replace, so it is the only thing -fold can be REQUIRED to preserve,
    // and the two are differentially tested against each other.
    //
    // argsfile: epoch count on the first line, then CONFIG and STATE on
    // alternating lines. Epoch i reduces ((STEP CONFIG_i) STATE_i).
    if (std.mem.eql(u8, arg1, "-fold") or std.mem.eql(u8, arg1, "-reparse")) {
        if (argv.len < 4) fatal("usage: ic32z -fold|-reparse stepfile argsfile", 3);
        const reparse = std.mem.eql(u8, arg1, "-reparse");

        var step = readWholeFile(argv[2]);
        while (step.len > 0 and (step[step.len - 1] == '\n' or step[step.len - 1] == '\r'))
            step = step[0 .. step.len - 1];
        const args_txt = readWholeFile(argv[3]);

        var lines = Vec([]const u8){};
        var it = std.mem.splitScalar(u8, args_txt, '\n');
        while (it.next()) |ln| lines.push(ln);
        if (lines.len == 0) fatal("empty args file", 3);
        const nep = std.fmt.parseInt(usize, std.mem.trim(u8, lines.items[0], " \r\t"), 10) catch
            fatal("bad epoch count in args file", 3);
        if (nep == 0 or lines.len < 1 + 2 * nep) fatal("truncated args file", 3);

        // NUL-terminate every epoch's argument text UP FRONT, so the timed
        // region measures parsing and not allocation.
        var cfg = Vec([]u8){};
        var stt = Vec([]u8){};
        var whole = Vec([]u8){};
        var i: usize = 0;
        while (i < nep) : (i += 1) {
            const c = lines.items[1 + 2 * i];
            const t = lines.items[2 + 2 * i];
            cfg.push(zdup(c));
            stt.push(zdup(t));
            if (reparse) {
                var b = Vec(u8){};
                b.push('(');
                b.push('(');
                for (step) |ch| b.push(ch);
                b.push(' ');
                for (c) |ch| b.push(ch);
                b.push(')');
                b.push(' ');
                for (t) |ch| b.push(ch);
                b.push(')');
                b.push(0);
                whole.push(b.items[0..b.len]);
            }
        }

        var parse_ns: i128 = 0;
        var reduce_ns: i128 = 0;
        var restore_ns: i128 = 0;
        var tot_itrs: i64 = 0;

        // parse the step term once
        reset_state();
        var t0 = std.time.nanoTimestamp();
        src = zdup(step);
        P = 0;
        const S = parse_term();
        ws();
        const step_parse_ns = std.time.nanoTimestamp() - t0;

        var snap = SnapshotV1{};
        var step_hash: u64 = 0;
        if (!reparse) {
            snap = snapshotCapture(step);
            step_hash = snap.step_hash;
        }

        i = 0;
        while (i < nep) : (i += 1) {
            var root: Term = undefined;
            if (reparse) {
                reset_state();
                t0 = std.time.nanoTimestamp();
                src = whole.items[i];
                P = 0;
                root = parse_term();
                ws();
                parse_ns += std.time.nanoTimestamp() - t0;
            } else {
                t0 = std.time.nanoTimestamp();
                const rc = snapshotRestore(&snap, step_hash);
                restore_ns += std.time.nanoTimestamp() - t0;
                if (rc != 0) {
                    var l: [96]u8 = undefined;
                    errWrite(std.fmt.bufPrint(l[0..], "snapshot restore refused rc={d}\n", .{rc}) catch "\n");
                    std.process.exit(5);
                }

                t0 = std.time.nanoTimestamp();
                src = cfg.items[i];
                P = 0;
                const C = parse_term();
                ws();
                src = stt.items[i];
                P = 0;
                const T = parse_term();
                ws();
                const a1 = alloc_n(2);
                heap[a1] = S;
                heap[a1 + 1] = C;
                const a2 = alloc_n(2);
                heap[a2] = MK(T_APP, 0, a1);
                heap[a2 + 1] = T;
                root = MK(T_APP, 0, a2);
                parse_ns += std.time.nanoTimestamp() - t0;
            }

            t0 = std.time.nanoTimestamp();
            const nf = normal(root);
            reduce_ns += std.time.nanoTimestamp() - t0;
            tot_itrs += interactions;

            // stdout carries normal forms, stderr the timing record, so a
            // divergence between the modes is compared against normal forms
            // only and cannot be masked or manufactured by timing text.
            sb.len = 0;
            show_iter(nf);
            sb.push('\n');
            outWrite(sb.slice());
        }

        var line: [320]u8 = undefined;
        errWrite(std.fmt.bufPrint(line[0..], "mode={s} schema={d} epochs={d} step_parse_once_ms={d:.3} " ++
            "restore_ms={d:.3} parse_ms={d:.3} reduce_ms={d:.3} itrs_per_epoch={d}\n", .{
            if (reparse) "reparse" else "fold",
            SNAPSHOT_SCHEMA,
            nep,
            if (reparse) 0.0 else @as(f64, @floatFromInt(step_parse_ns)) / 1e6,
            @as(f64, @floatFromInt(restore_ns)) / 1e6,
            @as(f64, @floatFromInt(parse_ns)) / 1e6,
            @as(f64, @floatFromInt(reduce_ns)) / 1e6,
            @divTrunc(tot_itrs, @as(i64, @intCast(nep))),
        }) catch "\n");
        std.process.exit(0);
    }

    // read the term from stdin
    var input = Vec(u8){};
    var tmp: [1 << 16]u8 = undefined;
    while (true) {
        const n = std.posix.read(0, tmp[0..]) catch break;
        if (n == 0) break;
        var k: usize = 0;
        while (k < n) : (k += 1) input.push(tmp[k]);
    }
    // strip trailing whitespace/newline, then NUL-terminate
    while (input.len > 0) {
        const c = input.items[input.len - 1];
        if (c == '\n' or c == '\r' or c == ' ' or c == '\t') input.len -= 1 else break;
    }
    input.push(0);
    src = input.items[0..input.len];
    P = 0;

    const quiet = std.mem.eql(u8, arg1, "-q");
    const verbose = quiet or std.mem.eql(u8, arg1, "-v");

    const t = parse_term();
    ws();
    const nf = normal(t);

    if (!quiet) {
        show_iter(nf);
        sb.push('\n');
        outWrite(sb.slice());
    }
    if (verbose) {
        var line: [160]u8 = undefined;
        errWrite(std.fmt.bufPrint(line[0..], "interactions={d} heap={d}\n", .{ interactions, hp }) catch "\n");
    }
}
