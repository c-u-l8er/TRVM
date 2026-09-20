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
 */
#include <stdint.h>
#include <string.h>

#define TRVM_PRINT_ABI 1

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

typedef struct {
    char   *buf;
    int64_t cap;
    int64_t len;     /* bytes needed so far, written or not */
    int64_t names;   /* binders emitted so far == the next name index */
} W;

static const char LAM[2] = { (char)0xCE, (char)0xBB };   /* U+03BB, two bytes */

static inline void put(W *w, const char *s, int64_t n)
{
    if (w->len + n <= w->cap) memcpy(w->buf + w->len, s, (size_t)n);
    w->len += n;
}

static inline void put1(W *w, char c)
{
    if (w->len + 1 <= w->cap) w->buf[w->len] = c;
    w->len += 1;
}

/* a..z for the first 26 binders, then v26, v27, ... -- ic_ref.show's rule */
static inline void put_name(W *w, int64_t i)
{
    char tmp[24];
    int k = 0;
    if (i < 26) { put1(w, (char)('a' + i)); return; }
    while (i > 0) { tmp[k++] = (char)('0' + (int)(i % 10)); i /= 10; }
    put1(w, 'v');
    while (k > 0) put1(w, tmp[--k]);
}

static inline int64_t lam(W *w)              /* bind one fresh name, return its index */
{
    int64_t n = w->names++;
    put(w, LAM, 2);
    put_name(w, n);
    put1(w, '.');
    return n;
}

static void emit_bool(W *w, int b)
{
    int64_t n0 = lam(w), n1 = lam(w);
    put_name(w, b ? n0 : n1);
}

static int emit_enum(W *w, int64_t size, int64_t idx)
{
    int64_t base, k;
    if (idx < 0 || idx >= size) return E_INDEX;
    base = w->names;
    for (k = 0; k < size; k++) (void)lam(w);
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

/* TUP of `width` bits of `v`, LSB first */
static void emit_bits(W *w, int64_t v, int64_t width)
{
    uint64_t u = (uint64_t)v;
    int64_t i;
    tup_open(w, width);
    for (i = 0; i < width; i++) {
        put1(w, ' ');
        emit_bool(w, (int)((u >> i) & 1u));
        put1(w, ')');
    }
}

/* TUP of the four lanes, each a TUP of `width` bits */
static void emit_lanes(W *w, const int64_t *st, int64_t width)
{
    int64_t l;
    tup_open(w, 4);
    for (l = 0; l < 4; l++) {
        put1(w, ' ');
        emit_bits(w, st[l], width);
        put1(w, ')');
    }
}

int64_t trvm_print_abi(void) { return TRVM_PRINT_ABI; }

/* desc: `nfields` triples (kind, arg, slot offset), in state_layout order. */
int64_t trvm_print_state(const int64_t *desc, int64_t nfields,
                         const int64_t *st, char *out, int64_t cap)
{
    W w;
    int64_t i, rc;
    w.buf = out; w.cap = cap < 0 ? 0 : cap; w.len = 0; w.names = 0;
    tup_open(&w, nfields);
    for (i = 0; i < nfields; i++) {
        int64_t kind = desc[3 * i], arg = desc[3 * i + 1], off = desc[3 * i + 2];
        const int64_t *f = st + off;
        put1(&w, ' ');
        switch (kind) {
        case K_ONEHOT:
            if (arg < 1) return E_WIDTH;
            rc = emit_enum(&w, arg, f[0]);
            if (rc) return rc;
            break;
        case K_BINP:
            if (arg < 1 || arg > 63) return E_WIDTH;
            emit_bits(&w, f[0], arg);
            break;
        case K_ONCE:
            if (arg < 1 || arg > 63) return E_WIDTH;
            {
                int64_t b;
                tup_open(&w, arg + 1);
                put1(&w, ' '); emit_bool(&w, f[0] != 0); put1(&w, ')');
                for (b = 0; b < arg; b++) {
                    put1(&w, ' ');
                    emit_bool(&w, (int)(((uint64_t)f[1] >> b) & 1u));
                    put1(&w, ')');
                }
            }
            break;
        case K_PAIR:
            tup_open(&w, 2);
            put1(&w, ' '); emit_bool(&w, f[0] != 0); put1(&w, ')');
            put1(&w, ' '); emit_bool(&w, f[1] != 0); put1(&w, ')');
            break;
        case K_POSE:
        case K_ROTOR:
            if (arg < 1 || arg > 63) return E_WIDTH;
            emit_lanes(&w, f, arg);
            break;
        case K_FAULT:
            emit_bool(&w, f[0] != 0);
            break;
        default:
            return E_KIND;
        }
        put1(&w, ')');
    }
    return w.len;
}
