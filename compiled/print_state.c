/* print_state.c -- the canonical printer for the compiled WRL backend.
 *
 * One pass from the compiled step's int64 state vector to the exact bytes
 * `ic_ref.show(ic_ref.parse(compiler.enc_state_v6(view, state)))` produces,
 * with no term text and no AST in between.
 *
 * WHY THIS IS A SEPARATE OBJECT and not code inside the emitted step: the
 * emitted step's source sha256 IS the admitted artifact's identity
 * (`cbknd-`/`cbknd2-`), and the battery admits a step by film- and
 * state-equality against the calculus.  A printer changes no film and no
 * state, so putting it in the step would move every C identity -- and would
 * do it again on every printer change -- to buy nothing the battery checks.
 * It is also world-independent by construction (the grammar below is fixed;
 * only the field descriptor varies) and backend-independent (emit_c's slot
 * vector and emit_c2's unpacked vector are the same vector), so one object
 * serves every world and both C emitters.  See README.md section 2j.
 *
 * WHAT IT MUST REPRODUCE.  `enc_state_v6` emits a closed normal form built
 * from four shapes only -- no Era, no Sup, no Dup, no free variable -- and
 * `show` renames every binder in FIRST-ENCOUNTER order over the whole term:
 * a..z, then v26, v27, ...  `show` names a Lam's binder before walking its
 * body and an App's function before its argument, so for these shapes the
 * name index of a binder is exactly the number of binders emitted before it
 * in the output text.  That is the whole of the correspondence, and it is why
 * this can be a single forward pass with one counter.
 *
 *   TUP(p0..pk-1)  ->  "lam" f "." "("*k f (" " pi ")")*k        (k==0: "lam" f "." f)
 *   BOOL(b)        ->  "lam" n0 "." "lam" n1 "." (b ? n0 : n1)
 *   ENUM(size,i)   ->  "lam" n0 "." ... "lam" n(size-1) "." n(i)
 *   PAIR(x,y)      ==  TUP(x,y), byte for byte
 *
 * and the fields of `compiler.state_layout` render as
 *
 *   counter onehot(period,phase)      ENUM(period, slot)
 *   counter binp(period,phase,width)  TUP(width bits of slot, LSB first)
 *   counter once(epoch,width)         TUP(BOOL(done), width bits of k)
 *   wire | door | relay               TUP(BOOL(a), BOOL(b))
 *   pose | rotor (lane width w)       TUP(4 x TUP(w bits of the lane, LSB first))
 *   fault                             BOOL(flag)
 *
 * The bit of a negative lane value is its two's-complement bit, which is what
 * Python's `(v >> i) & 1` yields for i < 64; `(uint64_t)v >> i` is the same
 * bit without relying on a signed right shift.
 *
 * Buffer contract, snprintf's: the return value is the number of bytes the
 * rendering NEEDS.  Bytes are written only while they fit, so a return value
 * greater than `cap` means nothing usable was written and the caller should
 * call again with a bigger buffer.  Negative means refused.
 *
 * THE READER IS THE SAME WALK RUN BACKWARDS (2026-09-20).  `trvm_read_state`
 * turns those canonical bytes back into the state vector, and it is not a
 * second traversal: it is `trvm_print_state`'s traversal with `w->mode` set
 * to READ, so every place the printer writes a token the reader matches it,
 * and every place the printer writes a NAME chosen by a value the reader
 * reads that name back and recovers the value.  Two traversals of one grammar
 * would be two spellings of one rule, and this lane has already paid for that
 * once (README section 2k).  One walk cannot disagree with itself.
 *
 * What that buys beyond speed is TIGHTNESS: the reader accepts a string if and
 * only if the printer could have produced it for this descriptor.  It is not a
 * lambda-calculus parser that then checks the shape -- it never builds a term
 * at all -- so a state that is well-formed but not of this world's layout is
 * refused at the byte where it first differs, which is also what makes its
 * refusals cheap.
 *
 * Lane values come back UNSIGNED, the low `w` bits as written, because that is
 * what `binlib.dec_bits` produces and therefore what `compiler.dec_state_v6`
 * hands `CompiledStep.encode` today.  The reader's job is to agree with the
 * Python path it replaces, not to improve on its representation.
 */
#include <stdint.h>
#include <string.h>

#define TRVM_PRINT_ABI 3   /* 2: reads state. 3: reads and writes the epoch CONTROL too. */

/* field kinds, in `compiler.state_layout` terms */
enum {
    K_ONEHOT = 0,   /* arg = period (enum size),   1 slot: the index     */
    K_BINP   = 1,   /* arg = bit width,            1 slot: the count     */
    K_ONCE   = 2,   /* arg = bit width,            2 slots: done, k      */
    K_PAIR   = 3,   /* arg unused,                 2 slots: a, b         */
    K_POSE   = 4,   /* arg = lane width,           4 slots: the lanes    */
    K_FAULT  = 5,   /* arg unused,                 1 slot: the flag      */
    K_ROTOR  = 6    /* arg = lane width,           4 slots: the lanes    */
};

#define E_KIND   (-1)   /* a field kind this printer does not know       */
#define E_WIDTH  (-2)   /* a width outside 1..63                         */
#define E_INDEX  (-3)   /* an enum index outside its size                */

enum { M_PRINT = 0, M_READ = 1 };

#define E_SYNTAX (-4)   /* the input is not what the printer would have written */
#define E_TRAIL  (-5)   /* it matched, and then there was more                  */

typedef struct {
    /* print side */
    char   *buf;
    int64_t cap;
    int64_t len;     /* bytes needed so far, written or not */
    /* read side */
    const char *in;
    int64_t in_len;
    int64_t pos;
    int64_t *slots;
    /* both */
    int64_t names;   /* binders walked so far == the next name index */
    int     mode;
    int     err;
} W;

static const char LAM[2] = { (char)0xCE, (char)0xBB };   /* U+03BB, two bytes */

/* One token: written in PRINT mode, matched in READ mode. Every byte of the
 * grammar goes through here, which is what keeps the two directions in step. */
static inline void put(W *w, const char *s, int64_t n)
{
    if (w->err) return;
    if (w->mode == M_READ) {
        if (w->pos + n > w->in_len || memcmp(w->in + w->pos, s, (size_t)n) != 0) { w->err = E_SYNTAX; return; }
        w->pos += n;
        return;
    }
    if (w->len + n <= w->cap) memcpy(w->buf + w->len, s, (size_t)n);
    w->len += n;
}

static inline void put1(W *w, char c)
{
    if (w->err) return;
    if (w->mode == M_READ) {
        if (w->pos >= w->in_len || w->in[w->pos] != c) { w->err = E_SYNTAX; return; }
        w->pos += 1;
        return;
    }
    if (w->len + 1 <= w->cap) w->buf[w->len] = c;
    w->len += 1;
}

/* a..z for the first 26 binders, then v26, v27, ... -- ic_ref.show's rule.
 * In READ mode this MATCHES the name index i, which is the whole reason the
 * reader needs no symbol table: at every fixed position the name is a function
 * of how many binders have been walked, so it is known before it is read. */
static inline void put_name(W *w, int64_t i)
{
    char tmp[24];
    int k = 0;
    if (i < 26) { put1(w, (char)('a' + i)); return; }
    while (i > 0) { tmp[k++] = (char)('0' + (int)(i % 10)); i /= 10; }
    put1(w, 'v');
    while (k > 0) put1(w, tmp[--k]);
}

/* READ mode only: the name at `pos` as an index, or -1. `a`..`z` are 0..25 and
 * `vN` is N; the two cannot be confused, because a bare `v` is index 21 and is
 * never followed by a digit in canonical output (a name is always followed by
 * `.`, ` `, `)`, or the end). */
static int64_t read_name(W *w)
{
    int64_t i;
    char c;
    if (w->err) return -1;
    if (w->pos >= w->in_len) { w->err = E_SYNTAX; return -1; }
    c = w->in[w->pos];
    if (c == 'v' && w->pos + 1 < w->in_len && w->in[w->pos + 1] >= '0' && w->in[w->pos + 1] <= '9') {
        w->pos += 1;
        i = 0;
        while (w->pos < w->in_len && w->in[w->pos] >= '0' && w->in[w->pos] <= '9') {
            if (i > (int64_t)1 << 40) { w->err = E_SYNTAX; return -1; }
            i = i * 10 + (w->in[w->pos] - '0');
            w->pos += 1;
        }
        if (i < 26) { w->err = E_SYNTAX; return -1; }        /* `v3` is not a name show would write */
        return i;
    }
    if (c >= 'a' && c <= 'z') { w->pos += 1; return c - 'a'; }
    w->err = E_SYNTAX;
    return -1;
}

static inline int64_t lam(W *w)              /* bind one fresh name, return its index */
{
    int64_t n = w->names++;
    put(w, LAM, 2);
    put_name(w, n);
    put1(w, '.');
    return n;
}

/* PRINT: write BOOL(b). READ: recover b from which of the two binders the body
 * names. Returns the bit in READ mode, `b` in PRINT mode. */
static int emit_bool(W *w, int b)
{
    int64_t n0 = lam(w), n1 = lam(w);
    if (w->mode == M_READ) {
        int64_t got = read_name(w);
        if (w->err) return 0;
        if (got == n0) return 1;
        if (got == n1) return 0;
        w->err = E_SYNTAX;
        return 0;
    }
    put_name(w, b ? n0 : n1);
    return b;
}

/* PRINT: write ENUM(size, idx). READ: recover idx, refusing a name outside the
 * enum's own binders -- which is how a state for a DIFFERENT world's layout is
 * caught here rather than several fields later. */
static int emit_enum(W *w, int64_t size, int64_t idx, int64_t *out)
{
    int64_t base, k;
    if (w->mode == M_PRINT && (idx < 0 || idx >= size)) return E_INDEX;
    base = w->names;
    for (k = 0; k < size; k++) (void)lam(w);
    if (w->mode == M_READ) {
        int64_t got = read_name(w);
        if (w->err) return 0;
        if (got < base || got >= base + size) { w->err = E_SYNTAX; return 0; }
        *out = got - base;
        return 0;
    }
    put_name(w, base + idx);
    return 0;
}

/* TUP's head: the binder, the k open parens and the spine variable.
 * Each item is then " " <item> ")". */
static inline void tup_open(W *w, int64_t k)
{
    int64_t f = lam(w), i;
    for (i = 0; i < k; i++) put1(w, '(');
    put_name(w, f);
}

/* TUP of `width` bits of `v`, LSB first. READ returns the value, unsigned. */
static int64_t emit_bits(W *w, int64_t v, int64_t width)
{
    uint64_t u = (uint64_t)v, acc = 0;
    int64_t i;
    tup_open(w, width);
    for (i = 0; i < width; i++) {
        int bit;
        put1(w, ' ');
        bit = emit_bool(w, (int)((u >> i) & 1u));
        put1(w, ')');
        if (w->mode == M_READ && bit) acc |= (uint64_t)1 << i;
    }
    return (int64_t)acc;
}

/* TUP of the four lanes, each a TUP of `width` bits. READ writes them to `out`. */
static void emit_lanes(W *w, const int64_t *st, int64_t width, int64_t *out)
{
    int64_t l;
    tup_open(w, 4);
    for (l = 0; l < 4; l++) {
        int64_t v;
        put1(w, ' ');
        v = emit_bits(w, st ? st[l] : 0, width);      /* READ mode has no state vector to read FROM */
        put1(w, ')');
        if (w->mode == M_READ) out[l] = v;
    }
}

int64_t trvm_print_abi(void) { return TRVM_PRINT_ABI; }

/* ------------------------------------------------------------- names that are not canonical (CONTROL only)
 * The STATE text is always a previous PAYLOAD, so its binders are `show`'s and a name is known from the count of
 * binders walked so far -- no table. The CONTROL text is not: it is `compiler.enc_config_bundle`'s raw output and
 * carries Forge's own generated names (`lam tf3.((tf3 lam tf1.(tf1 lam cnc.lam csr.cnc)) ...)`). So the control
 * walk binds names into a small table and matches uses against it. Two disciplines in one file, each because of
 * what its input actually is.
 *
 * THE BOUND, derived and then measured rather than picked. A control's binders are
 *   2 (the two TUPs) + per controlling spinner 2 (the Scott sum) + per SET rotor 4*(2w+1)+1 + per orb 2,
 * so the term that matters is the SET rotors: at w=63 one of them is ~511 binders and everything else is noise.
 * 2048 therefore admits about FOUR simultaneously-set 63-bit rotors, and that is the honest way to state it.
 * Measured over every pair `battery.pairs(False)` folds -- 1,120 (pair, epoch) controls, demo, fuzz, gentle and
 * extremes -- the worst is `spinner-w63-n31` at 516 binders / 3,438 bytes (one set rotor at w=63), so the tree's
 * widest world sits at 4.0x headroom and nothing falls back. A world with five or more controlled 63-lane
 * spinners all set in one epoch would exceed it, be REFUSED here, and fall back to the Python decoder -- correct,
 * slower, and visible in the candidate's `reader` field, which is what that fallback is for. */
#define CTRL_BINDERS 2048
#define E_BINDERS (-6)

typedef struct { int32_t off; int32_t len; } Span;

/* READ: the name at `pos`, as a span. Forge names are [A-Za-z][A-Za-z0-9]*. */
static Span scan_name(W *w)
{
    Span sp;
    sp.off = (int32_t)w->pos; sp.len = 0;
    if (w->err) return sp;
    if (w->pos >= w->in_len) { w->err = E_SYNTAX; return sp; }
    {
        char c = w->in[w->pos];
        if (!((c >= 'a' && c <= 'z') || (c >= 'A' && c <= 'Z'))) { w->err = E_SYNTAX; return sp; }
    }
    while (w->pos < w->in_len) {
        char c = w->in[w->pos];
        if ((c >= 'a' && c <= 'z') || (c >= 'A' && c <= 'Z') || (c >= '0' && c <= '9')) w->pos += 1;
        else break;
    }
    sp.len = (int32_t)(w->pos - sp.off);
    return sp;
}

/* PRINT: write `lam <canonical name>.`. READ: match a lambda, bind whatever name is there into `tab[slot]`. */
static void lam_bind(W *w, Span *tab, int64_t slot)
{
    if (w->err) return;
    if (slot >= CTRL_BINDERS) { w->err = E_BINDERS; return; }
    put(w, LAM, 2);
    if (w->mode == M_READ) {
        tab[slot] = scan_name(w);
        put1(w, '.');
        w->names++;
        return;
    }
    put_name(w, w->names++);
    put1(w, '.');
}

/* PRINT: write the canonical name of binder `idx`. READ: the name here must be the one bound at `slot`. */
static void use_bound(W *w, Span *tab, int64_t slot, int64_t idx)
{
    if (w->err) return;
    if (w->mode == M_READ) {
        Span got = scan_name(w);
        if (w->err) return;
        if (got.len != tab[slot].len || memcmp(w->in + got.off, w->in + tab[slot].off, (size_t)got.len) != 0)
            w->err = E_SYNTAX;
        return;
    }
    put_name(w, idx);
}

/* TUP whose binder is bound into the table rather than assumed canonical. */
static int64_t tup_open_bound(W *w, Span *tab, int64_t slot, int64_t k)
{
    int64_t idx = w->names, i;
    lam_bind(w, tab, slot);
    for (i = 0; i < k; i++) put1(w, '(');
    use_bound(w, tab, slot, idx);
    return idx;
}

/* BOOL whose two binders are bound rather than assumed canonical. */
static int bool_bound(W *w, Span *tab, int64_t slot, int b)
{
    int64_t i0 = w->names;
    lam_bind(w, tab, slot);
    {
        int64_t i1 = w->names;
        lam_bind(w, tab, slot + 1);
        if (w->mode == M_READ) {
            Span got = scan_name(w);
            if (w->err) return 0;
            if (got.len == tab[slot].len && memcmp(w->in + got.off, w->in + tab[slot].off, (size_t)got.len) == 0) return 1;
            if (got.len == tab[slot + 1].len && memcmp(w->in + got.off, w->in + tab[slot + 1].off, (size_t)got.len) == 0) return 0;
            w->err = E_SYNTAX;
            return 0;
        }
        put_name(w, b ? i0 : i1);
    }
    return b;
}

/* TUP of `width` bits, with bound binders. READ returns the value, unsigned. */
static int64_t bits_bound(W *w, Span *tab, int64_t *slot, int64_t v, int64_t width)
{
    uint64_t u = (uint64_t)v, acc = 0;
    int64_t i;
    tup_open_bound(w, tab, (*slot)++, width);
    for (i = 0; i < width; i++) {
        int bit;
        put1(w, ' ');
        bit = bool_bound(w, tab, *slot, (int)((u >> i) & 1u));
        *slot += 2;
        put1(w, ')');
        if (w->mode == M_READ && bit) acc |= (uint64_t)1 << i;
    }
    return (int64_t)acc;
}

static void lanes_bound(W *w, Span *tab, int64_t *slot, const int64_t *src, int64_t width, int64_t *out)
{
    int64_t l;
    tup_open_bound(w, tab, (*slot)++, 4);
    for (l = 0; l < 4; l++) {
        int64_t v;
        put1(w, ' ');
        v = bits_bound(w, tab, slot, src ? src[l] : 0, width);
        put1(w, ')');
        if (out) out[l] = v;
    }
}

/* ------------------------------------------------------------------ the epoch CONTROL, both directions
 * `compiler.enc_config_bundle` is TUP(rotor_bundle, fault_bundle): per controlling spinner in ORB order a Scott
 * sum -- NoChange = `lam a.lam b.a`, SetRotor(r) = `lam a.lam b.(b <pose>)` -- and per orb a BOOL. Three of the
 * four shapes are already here; the sum is the fourth, and it is the only place the READ direction has to look
 * ahead (one byte: a `(` means SetRotor, a name means NoChange).
 *
 * The vector is `emit_c.CompiledStep.control`'s: 5 slots per controlling spinner (set flag, then 4 lanes), then
 * one slot per orb. So reading it produces the control vector the step takes DIRECTLY -- `dec_config_bundle` and
 * `CompiledStep.control` both drop out, which on the spinner worlds was 259-724 us a job. */
static void walk_control(W *w, const int64_t *widths, int64_t nctrl, int64_t norbs,
                         const int64_t *ctl, int64_t *out)
{
    Span tab[CTRL_BINDERS];
    int64_t slot = 0, i;
    tup_open_bound(w, tab, slot++, 2);
    /* the rotor bundle */
    put1(w, ' ');
    tup_open_bound(w, tab, slot++, nctrl);
    for (i = 0; i < nctrl && !w->err; i++) {
        int64_t base = 5 * i, n0slot, n1idx;
        put1(w, ' ');
        n0slot = slot;
        (void)0;
        {
            int64_t i0 = w->names;
            lam_bind(w, tab, slot);
            n1idx = w->names;
            lam_bind(w, tab, slot + 1);
            slot += 2;
            (void)i0;
        }
        if (widths[i] < 1 || widths[i] > 63) { w->err = E_WIDTH; return; }
        if (w->mode == M_READ) {
            if (w->pos < w->in_len && w->in[w->pos] == '(') {
                put1(w, '(');
                use_bound(w, tab, n0slot + 1, n1idx);
                put1(w, ' ');
                lanes_bound(w, tab, &slot, 0, widths[i], out ? out + base + 1 : 0);
                put1(w, ')');
                if (out) out[base] = 1;
            } else {
                use_bound(w, tab, n0slot, 0);
                if (out) { int64_t l; out[base] = 0; for (l = 0; l < 4; l++) out[base + 1 + l] = 0; }
            }
        } else if (ctl && ctl[base] != 0) {
            put1(w, '(');
            use_bound(w, tab, n0slot + 1, n1idx);
            put1(w, ' ');
            lanes_bound(w, tab, &slot, ctl + base + 1, widths[i], 0);
            put1(w, ')');
        } else {
            use_bound(w, tab, n0slot, n1idx - 1);
        }
        put1(w, ')');
    }
    put1(w, ')');
    /* the fault bundle */
    put1(w, ' ');
    tup_open_bound(w, tab, slot++, norbs);
    for (i = 0; i < norbs && !w->err; i++) {
        int b;
        put1(w, ' ');
        b = bool_bound(w, tab, slot, ctl ? (ctl[5 * nctrl + i] != 0) : 0);
        slot += 2;
        put1(w, ')');
        if (out) out[5 * nctrl + i] = b;
    }
    put1(w, ')');
}

int64_t trvm_print_control(const int64_t *widths, int64_t nctrl, int64_t norbs,
                           const int64_t *ctl, char *out, int64_t cap)
{
    W w;
    w.buf = out; w.cap = cap < 0 ? 0 : cap; w.len = 0;
    w.in = 0; w.in_len = 0; w.pos = 0; w.slots = 0;
    w.names = 0; w.mode = M_PRINT; w.err = 0;
    walk_control(&w, widths, nctrl, norbs, ctl, 0);
    return w.err ? (int64_t)w.err : w.len;
}

int64_t trvm_read_control(const int64_t *widths, int64_t nctrl, int64_t norbs,
                          const char *in, int64_t in_len, int64_t *ctl, int64_t width)
{
    W w;
    int64_t i;
    if (width < 5 * nctrl + norbs) return E_WIDTH;
    for (i = 0; i < width; i++) ctl[i] = 0;
    w.buf = 0; w.cap = 0; w.len = 0;
    w.in = in; w.in_len = in_len < 0 ? 0 : in_len; w.pos = 0; w.slots = ctl;
    w.names = 0; w.mode = M_READ; w.err = 0;
    walk_control(&w, widths, nctrl, norbs, 0, ctl);
    if (w.err) return (int64_t)w.err;
    if (w.pos != w.in_len) return E_TRAIL;
    return 0;
}


/* THE WALK. One traversal of one grammar, in whichever direction `w->mode` says.
 * desc: `nfields` triples (kind, arg, slot offset), in state_layout order. */
static void walk(W *w, const int64_t *desc, int64_t nfields, const int64_t *st, int64_t *out)
{
    int64_t i, rc;
    tup_open(w, nfields);
    for (i = 0; i < nfields && !w->err; i++) {
        int64_t kind = desc[3 * i], arg = desc[3 * i + 1], off = desc[3 * i + 2];
        const int64_t *f = st ? st + off : 0;
        int64_t *o = out ? out + off : 0;
        put1(w, ' ');
        switch (kind) {
        case K_ONEHOT:
            if (arg < 1) { w->err = E_WIDTH; return; }
            rc = emit_enum(w, arg, f ? f[0] : 0, o);
            if (rc) { w->err = (int)rc; return; }
            break;
        case K_BINP:
            if (arg < 1 || arg > 63) { w->err = E_WIDTH; return; }
            {
                int64_t v = emit_bits(w, f ? f[0] : 0, arg);
                if (o) o[0] = v;
            }
            break;
        case K_ONCE:
            if (arg < 1 || arg > 63) { w->err = E_WIDTH; return; }
            {
                int64_t b, done, acc = 0;
                tup_open(w, arg + 1);
                put1(w, ' '); done = emit_bool(w, f ? (f[0] != 0) : 0); put1(w, ')');
                for (b = 0; b < arg; b++) {
                    int bit;
                    put1(w, ' ');
                    bit = emit_bool(w, f ? (int)(((uint64_t)f[1] >> b) & 1u) : 0);
                    put1(w, ')');
                    if (bit) acc |= (int64_t)1 << b;
                }
                if (o) { o[0] = done; o[1] = acc; }
            }
            break;
        case K_PAIR:
            {
                int a0, a1;
                tup_open(w, 2);
                put1(w, ' '); a0 = emit_bool(w, f ? (f[0] != 0) : 0); put1(w, ')');
                put1(w, ' '); a1 = emit_bool(w, f ? (f[1] != 0) : 0); put1(w, ')');
                if (o) { o[0] = a0; o[1] = a1; }
            }
            break;
        case K_POSE:
        case K_ROTOR:
            if (arg < 1 || arg > 63) { w->err = E_WIDTH; return; }
            emit_lanes(w, f, arg, o);
            break;
        case K_FAULT:
            {
                int b = emit_bool(w, f ? (f[0] != 0) : 0);
                if (o) o[0] = b;
            }
            break;
        default:
            w->err = E_KIND;
            return;
        }
        put1(w, ')');
    }
}

/* desc: `nfields` triples (kind, arg, slot offset), in state_layout order. */
int64_t trvm_print_state(const int64_t *desc, int64_t nfields,
                         const int64_t *st, char *out, int64_t cap)
{
    W w;
    w.buf = out; w.cap = cap < 0 ? 0 : cap; w.len = 0;
    w.in = 0; w.in_len = 0; w.pos = 0; w.slots = 0;
    w.names = 0; w.mode = M_PRINT; w.err = 0;
    walk(&w, desc, nfields, st, 0);
    return w.err ? (int64_t)w.err : w.len;
}

/* The inverse: canonical bytes -> the state vector. 0 on success, negative on
 * refusal. `st` must have room for the descriptor's whole width; it is written
 * only on success, because a half-decoded state is worse than none. */
int64_t trvm_read_state(const int64_t *desc, int64_t nfields,
                        const char *in, int64_t in_len, int64_t *st, int64_t width)
{
    W w;
    int64_t i, need = 0;
    /* the descriptor's own width, so a short `st` is caught here and not by the caller's allocator */
    for (i = 0; i < nfields; i++) {
        int64_t kind = desc[3 * i], off = desc[3 * i + 2];
        int64_t n = (kind == K_POSE || kind == K_ROTOR) ? 4 : (kind == K_ONCE || kind == K_PAIR) ? 2 : 1;
        if (off + n > need) need = off + n;
    }
    if (width < need) return E_WIDTH;
    for (i = 0; i < width; i++) st[i] = 0;
    w.buf = 0; w.cap = 0; w.len = 0;
    w.in = in; w.in_len = in_len < 0 ? 0 : in_len; w.pos = 0; w.slots = st;
    w.names = 0; w.mode = M_READ; w.err = 0;
    walk(&w, desc, nfields, 0, st);
    if (w.err) return (int64_t)w.err;
    if (w.pos != w.in_len) return E_TRAIL;      /* it matched, and then there was more */
    return 0;
}
