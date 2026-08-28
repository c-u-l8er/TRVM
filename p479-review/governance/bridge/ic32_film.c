/* ═══════════════════════════════════════════════════════════════════════════
   ic32_film.c — v0.5.1 — the execution plane originates PARTIAL execution evidence too

   v0.2.0 could emit multi-frame films but fired only APP-LAM: a term where any
   DUP-* rule became enabled was refused by name. That refusal was honest and it
   was also the whole frontier — the distinctive interaction-net dynamics, the
   ones a tree-application relation cannot model, were still evidenced only by
   JavaScript.

   v0.3.0 implements the FLOAT PLANE: enumeration over the root tree AND every
   live dup cell, canonical `t:` / `d:` / `v:` loci, and the six handlers the
   church_exp_2_2 witness actually requires —

       APP-SUP · DUP-LAM · DUP-SUP= · DUP-SUP! · DUP-VAR · DUP-APP

   ERA was deliberately not among them, because the JS measurement of
   church_exp_2_2 established that neither APP-ERA nor DUP-ERA fires on that
   fixture — two rules unexercised, not the one that was anticipated — and a
   handler with no witness is coverage by hope.

   v0.4.0 CLOSES THE POOL. Both ERA rules fire, and they arrived with the two
   purpose-built minimal fixtures that justify them rather than as a pair of
   handlers hoping for a term: `(* x)` is one APP-ERA frame, and
   `!{a,b} = *; λz.a` is one DUP-ERA frame with a single live projection.
   COVERAGE BY CONSTRUCTION, not coverage because one large program happened to
   contain everything. Every rule of the declared pool now has a positive
   native witness, and film_check derives that sentence from the films rather
   than stating it.

   v0.4.0 also adds CANONICAL LOCUS INJECTIVITY as a checked precondition. Each
   findAppRedexes call carries its own visited set, so a node reachable both
   from the root and from inside a dup value is enumerable under a `t:` AND a
   `v:` locus. The locus is committed into frame_id, so two spellings of one
   transition would be two canonical frame identities for the same pre, rule
   and post — which is not something "canonical" can mean. Nothing in the 35
   measured fixtures produces an alias; the emitter REFUSES `film-locus-alias`
   rather than blessing both spellings, because precedence between them is
   unruled and picking one silently would decide a rule nobody wrote down.

   v0.5.0 MAKES THE BUDGET EVIDENCE INSTEAD OF A REFUSAL, and the distinction it
   turns into a portable object is an epistemic one rather than a bookkeeping
   one:

       NORMAL_FORM       there is provably no work left
       BUDGET_EXHAUSTED  we stopped looking, and this much work was left

   Those are different claims about the world and a runtime that cannot tell
   them apart cannot be trusted with either. Until now C could originate only
   the first: reaching a budget produced `film-budget-exhausted`, a refusal,
   which says "no evidence" where the honest answer is "evidence of a partial
   execution". The terminal contract it seals into is UNCHANGED — TRVM-SEMFILM
   -v1.1 already declares the budget witness (steps == budget, remaining_work
   the fresh full-pool count, > 0, all of it committed inside film_id and all of
   it re-derived by replay). B5 invents no budget concept; it makes C originate
   the terminal object the kernel already knew how to judge.

   THREE THINGS THAT ARE EASY TO GET WRONG HERE, and are not:

     1. NORMAL_FORM WINS AT THE BOUNDARY. The pool is enumerated FIRST; an
        empty pool is a normal form even when the step count has just reached
        the budget. "steps == budget therefore exhausted" would misclassify a
        computation that finished exactly on its last permitted step. For
        church_exp_2_2 that is the difference between --budget 20 and 21.
     2. THE TERMINAL IS NOT A FRAME. Budget describes the state at the moment a
        further step was denied, not a state reached by a "budget event". No
        synthetic frame is appended and no transition is fired after the last
        real one; `remaining_work` is measured on the state the last real frame
        left behind.
     3. THE SEMANTIC BUDGET AND THE STORAGE CEILING STAY SEPARATE. `--budget N`
        is execution policy and can produce evidence; MAXFRAMES is this
        program's frame array and can only produce `film-too-many-frames`.
        --budget above MAXFRAMES still refuses, which is the witness that the
        two were never the same number wearing two names.

   A partial film does NOT compute a normal form. Reading one back would be
   performing exactly the work the budget denied and reporting it beside a
   terminal that says it was not done, so `normal_form` and `normal_form_id`
   are ABSENT from a budget film rather than present and unused.

   ── MEASURE BEFORE ASSERTING ───────────────────────────────────────────────
   `--measure` prints what this runtime actually does — frame rows, rule and
   locus tallies, the enabled set at every step, the terminal — and commits
   NOTHING: no film id, no chain, no expected values. It exists so the C
   relation can be compared against the JS oracle's independently measured
   relation BEFORE any conformance assertion is written. Nothing in this file
   contains a frame count, a rule sequence, or a locus for church_exp_2_2, and
   nothing may: a conformance theorem whose expected table was transcribed from
   the other implementation is a transcription theorem.

   The measurement formatter and the film formatter run over ONE reducer. Two
   separately written C transition engines would duplicate the mechanism to
   manufacture an independence that is not where independence matters: the
   independence that matters is C-under-test versus the JS semantic oracle.

   ── WHAT THE FLOAT PLANE COSTS IN ic32's REPRESENTATION ────────────────────
   The law kernel's FloatRt holds dups in a side table keyed by id, with the two
   projections as NAMES, so firing a dup is two substitutions by name and the
   occurrences never have to be found. ic32 has no such table: a dup is a heap
   cell reached through T_DP0/T_DP1 words, and `heap[D]` serves double duty —
   the cell's value before the rule fires, the OTHER side's substitution after.
   So ic32 can only fire a dup FROM A DEMANDED SIDE, and the demanded
   projection must be replaced where it stands. `find_projections` is that
   lookup, and it refuses rather than guesses if a projection is not unique.

   That is a representational obligation, not a semantic one, and it is the
   reason this file reuses ic32's own `fire()` and `app_sup()` rather than
   reimplementing the rules: the rules are the runtime's, the scheduling and
   the addressing are the film's.

   THE TWO ORDERS ARE NOT THE SAME ORDER, and conflating them is the easiest
   way to produce a locus that names the wrong redex. The kernel enumerates
   live cells with `liveHeap`, which pushes children FORWARD and therefore pops
   RIGHT-TO-LEFT; it indexes `d:`/`v:` loci with `liveDiscoveryOrder`, which
   pushes children REVERSED and therefore pops LEFT-TO-RIGHT. One order decides
   which redex is at position 0 of the enumeration, the other decides what
   number that redex's locus carries. `live_cells(root, direction)` implements
   both and the caller says which it wants.

   ── WHAT IS STILL NOT CLAIMED ──────────────────────────────────────────────
     · A canonical-locus alias is REFUSED, not resolved. If a well-formed
       fixture ever produces one, the answer is a precedence rule — probably
       earliest occurrence under the frozen global enumeration — and not
       blessing both spellings.
     · It does not replay. Films flow C → JS only.
     · THE ONE-INTERACTION GUARD IS POST-HOC AND STAYS SO. It measures what the
       runtime DID, including any future change inside fire() or whnf(), where
       a structural pre-check could only measure what we predict. Its soundness
       depends on this emitter being FAIL-STOP: a refusal exits, so a heap
       mutated before the guard fired never becomes accepted evidence. If this
       ever becomes a persistent service, that needs transactional scratch
       state. The PREDICTION behind it — that whnf is inert on every head class
       dup_rule_name admits — is measured by `--probe-whnf`, not asserted here.

   The canonicalizer is INCLUDED, not copied: ic32_canon.c is the same file the
   bridge gate replays at 48/48, which in turn includes ic32.c verbatim.

   Usage:  ic32_film "<term>"                emit a TRVM-SEMFILM-v1.1 film (JSON)
           ic32_film --budget N "<term>"     at most N transitions; a partial run
                                             seals a BUDGET_EXHAUSTED terminal
           ic32_film --measure "<term>"      non-gating measurement, plain text
           ic32_film --measure -v "<term>"   + the enabled set at every step
           ic32_film --probe-whnf "<term>"   per admitted dup head: interaction
                                             delta and canonical-state movement
           on any unmet precondition: {"ok":false,"reason":"…"} and exit 1
   ═══════════════════════════════════════════════════════════════════════════ */
#define IC32_CANON_NO_MAIN 1
#include "ic32_canon.c"
#include <errno.h>   /* B5.1: strtol's ERANGE, which the B5 parse ignored */
#include <ctype.h>   /* B5.1: the leading whitespace strtol skips in silence */

/* The declared RULE POOL, in the law kernel's own construction order
   ([...PLANES.INTERACT, ...PLANES.COLLAPSE]). It is committed inside film_id,
   so a different order is a different film and replay says so. */
#define PLANE_POOL "APP-LAM,APP-SUP,APP-ERA,DUP-LAM,DUP-SUP=,DUP-SUP!,DUP-ERA,DUP-VAR,DUP-APP"

/* law:plane.rule-partition@1 — COLLAPSE is exactly DUP-VAR and DUP-APP. */
static const char* plane_of(const char* rule){
    if (!strcmp(rule, "DUP-VAR") || !strcmp(rule, "DUP-APP")) return "COLLAPSE";
    return "INTERACT";
}

static int g_measure = 0;
static void refuse(const char* reason){
    if (g_measure) printf("REFUSED %s\n", reason);
    else           printf("{\"ok\":false,\"reason\":\"%s\"}\n", reason);
    exit(1);
}

/* ── §2-equivalent stuck-application test ─────────────────────────────────
   The kernel's isStuckApp: the head chases to a FREE variable through zero or
   more stuck applications. Only these may be DUP-APP-copied under free
   scheduling; a reducible or not-yet-bound head is a wire whose peer has not
   arrived, and copying it early ties a knot the driver can never reach. */
static int is_stuck_app(Term app){
    for (int depth = 0; depth < 10000; depth++){
        Term f = ccanon_chase(heap[ADDR(app)]);
        if (TAG(f) == T_VAR) return is_free_var(f);
        if (TAG(f) == T_APP){ app = f; continue; }
        return 0;
    }
    return 0;
}

/* ── which rule, if any, is a dup cell ready to fire? ─────────────────────
   dupRule, against the CHASED value. The label comes from the PROJECTION, not
   from the cell — ic32 carries it in the DP word — so SUP-equality needs the
   label the enumeration found the cell through. Chase, never whnf: chasing
   costs no interaction, and a value that is still a live projection of another
   cell is a WAIT rather than a redex. */
static const char* dup_rule_name(uint32_t D, uint32_t L){
    Term v = ccanon_chase(heap[D]);
    switch (TAG(v)){
        case T_LAM: return "DUP-LAM";
        case T_SUP: return LAB(v) == L ? "DUP-SUP=" : "DUP-SUP!";
        case T_ERA: return "DUP-ERA";
        case T_VAR: return is_free_var(v) ? "DUP-VAR" : NULL;
        case T_APP: return is_stuck_app(v) ? "DUP-APP" : NULL;
        default:    return NULL;      /* a projection of an unfired cell: WAIT */
    }
}

/* ── live dup cells, in EITHER of the kernel's two traversal orders ───────
   L2R (liveDiscoveryOrder) indexes the canonical `d:`/`v:` loci.
   R2L (liveHeap)          orders the redex ENUMERATION.
   A first-seen T_DP0/T_DP1 is the discovery of its cell; the cell's value is
   pushed immediately, which is what makes the walk depth-first into the dup. */
typedef struct { uint32_t D, lab; } Cell;
typedef struct { Cell* a; size_t n, cap; } CellVec;
static void cv_push(CellVec* v, uint32_t D, uint32_t lab){
    if (v->n == v->cap){ v->cap = v->cap ? v->cap*2 : 32; v->a = (Cell*)realloc(v->a, v->cap*sizeof(Cell)); }
    v->a[v->n].D = D; v->a[v->n].lab = lab; v->n++;
}
static void cv_free(CellVec* v){ free(v->a); v->a = NULL; v->n = v->cap = 0; }
static int cv_index(const CellVec* v, uint32_t D){
    for (size_t i = 0; i < v->n; i++) if (v->a[i].D == D) return (int)i;
    return -1;
}
#define ORDER_L2R 1
#define ORDER_R2L 0
static void live_cells(Term root, int l2r, CellVec* out){
    U64Map seenNode; map_init(&seenNode, 4096);
    U64Map seenCell; map_init(&seenCell, 1024);
    TVec st = {0}; tpush(&st, root);
    while (st.n){
        Term t = ccanon_chase(st.a[--st.n]);
        uint64_t nk = (uint64_t)CLRSUB(t);
        int* s = map_slot(&seenNode, nk);
        if (*s == 1) continue; *s = 1;
        switch (TAG(t)){
            case T_DP0: case T_DP1: {
                uint32_t D = ADDR(t);
                int* c = map_slot(&seenCell, (uint64_t)D);
                if (*c == 1) break; *c = 1;
                cv_push(out, D, LAB(t));
                tpush(&st, heap[D]);        /* the cell's value, depth-first */
                break;
            }
            case T_LAM: tpush(&st, heap[ADDR(t)]); break;
            case T_APP: case T_SUP:
                if (l2r){ tpush(&st, heap[ADDR(t)+1]); tpush(&st, heap[ADDR(t)]); }
                else    { tpush(&st, heap[ADDR(t)]);   tpush(&st, heap[ADDR(t)+1]); }
                break;
            default: break;
        }
    }
    free(st.a); map_free(&seenNode); map_free(&seenCell);
}

/* ── redex enumeration ────────────────────────────────────────────────────
   findAppRedexes, against ic32's representation. Three things must match the
   kernel exactly or the locus will not name the same redex:

     · the child ORDER is fun-then-arg for App, lft-then-rgt for Sup, bod for
       Lam — the kernel pushes them reversed onto a stack and pops, so the walk
       visits them forward, and this reproduces that by pushing reversed too;
     · the visited set is keyed on the CHASED node, so a shared subterm is
       enumerated once, under the FIRST path that reached it;
     · a redex is classified by the chased HEAD of an application, never by
       reducing it — reducing the head would be taking more than one step.

   The path is a dot-joined list of the kernel's own field names, which is what
   `t:<path>` means. Root is the empty path, so the locus is exactly "t:".

   Each call carries its OWN visited set, exactly as the kernel's separate
   findAppRedexes(root) / findAppRedexes(d.val) calls do — a node reachable
   both from the root and from inside a dup value is enumerated in both, and
   collapsing that into one shared set would silently drop a `v:` redex. */
/* ── THE IMPLEMENTATION RESOURCE CEILINGS (B5.1) ──────────────────────────
   Overridable at COMPILE TIME so a limits build can reach a guard that
   production terms cannot, and production values are unchanged.

   B5 reported honestly that `film-too-many-frames` had no positive witness:
   MAXPATH binds first on every term tried, so no fixture the emitter can film
   reaches the frame array. GPT's ruling is that raising a production resource
   bound to make another production resource bound easier to hit in a test is
   the wrong trade — it changes the implementation under test to improve the
   test surface. A defensive resource ceiling is not a semantic refusal and
   does not owe the same coverage.

   So: -DMAXFRAMES=4 builds an emitter whose frame array a small term fills,
   which witnesses the GUARD; the production constants are asserted separately,
   which witnesses the CONFIGURATION. Two different claims, kept apart —
   mechanism witness versus production reachability. */
#ifndef MAXPATH
#define MAXPATH 480
#endif
#ifndef MAXREDEX
#define MAXREDEX 4096
#endif
#ifndef MAXFRAMES
#define MAXFRAMES 4096
#endif
typedef struct { char path[MAXPATH]; const char* rule; } Redex;
typedef struct { Term t; char path[MAXPATH]; } WalkItem;

static int enumerate_app_redexes(Term root, Redex* out, int cap, int* overflow){
    U64Map seen; map_init(&seen, 4096);
    size_t stcap = 1024;
    WalkItem* st = (WalkItem*)malloc(sizeof(WalkItem) * stcap);
    size_t sp = 0;
    st[sp].t = root; st[sp].path[0] = 0; sp++;
    int n = 0; *overflow = 0;

    while (sp){
        WalkItem it = st[--sp];
        Term t = ccanon_chase(it.t);
        uint64_t nk = (uint64_t)CLRSUB(t);
        int* s = map_slot(&seen, nk);
        if (*s == 1) continue; *s = 1;

        if (TAG(t) == T_APP){
            Term f = ccanon_chase(heap[ADDR(t)]);
            const char* rule = NULL;
            if      (TAG(f) == T_LAM) rule = "APP-LAM";
            else if (TAG(f) == T_SUP) rule = "APP-SUP";
            else if (TAG(f) == T_ERA) rule = "APP-ERA";
            if (rule){
                if (n >= cap){ *overflow = 1; break; }
                snprintf(out[n].path, MAXPATH, "%s", it.path);
                out[n].rule = rule;
                n++;
            }
        }
        /* children, pushed in REVERSE so the pops run in the kernel's order */
        const char* kids[2] = { NULL, NULL };
        Term ct[2]; int nk2 = 0;
        switch (TAG(t)){
            case T_LAM: kids[0] = "bod"; ct[0] = heap[ADDR(t)];                       nk2 = 1; break;
            case T_APP: kids[0] = "fun"; ct[0] = heap[ADDR(t)];
                        kids[1] = "arg"; ct[1] = heap[ADDR(t)+1];                     nk2 = 2; break;
            case T_SUP: kids[0] = "lft"; ct[0] = heap[ADDR(t)];
                        kids[1] = "rgt"; ct[1] = heap[ADDR(t)+1];                     nk2 = 2; break;
            default: nk2 = 0; break;
        }
        for (int i = nk2 - 1; i >= 0; i--){
            if (sp + 1 >= stcap){ stcap *= 2; st = (WalkItem*)realloc(st, sizeof(WalkItem) * stcap); }
            st[sp].t = ct[i];
            /* A TRUNCATED PATH IS A WRONG LOCUS, and silently so: two distinct
               redexes deep in one spine would be handed the same `t:` string,
               and the emitter would be naming a redex it did not fire. Replay
               would refuse it, but as "the emitter is broken" rather than as
               "this term is deeper than the locus encoding". snprintf returns
               the length it WANTED, so the bound is checkable. */
            int need = it.path[0]
              ? snprintf(st[sp].path, MAXPATH, "%s.%s", it.path, kids[i])
              : snprintf(st[sp].path, MAXPATH, "%s", kids[i]);
            if (need < 0 || need >= MAXPATH) refuse("film-locus-path-too-deep");
            sp++;
        }
    }
    free(st); map_free(&seen);
    return n;
}

/* The FLOAT-PLANE enumeration, in findFloatRedexes' exact construction order:
   every tree app redex first, then — per live cell in liveHeap order — the
   cell's own dup rule, then the app redexes inside the cell's VALUE. The
   position of a redex in this list is what "leftmost" means; the locus it
   carries is computed from the OTHER order. */
#define K_APP    0
#define K_DUP    1
#define K_DUPVAL 2
typedef struct {
    int kind;
    uint32_t D, lab;
    char path[MAXPATH];
    const char* rule;
    char locus[MAXPATH + 32];
} FRedex;

static int enumerate_float_redexes(Term root, FRedex* out, int cap, int* overflow){
    int n = 0; *overflow = 0;
    Redex rs[MAXREDEX]; int ov = 0;

    int na = enumerate_app_redexes(root, rs, MAXREDEX, &ov);
    if (ov){ *overflow = 1; return n; }
    for (int i = 0; i < na; i++){
        if (n >= cap){ *overflow = 1; return n; }
        out[n].kind = K_APP; out[n].D = 0; out[n].lab = 0;
        snprintf(out[n].path, MAXPATH, "%s", rs[i].path);
        out[n].rule = rs[i].rule; n++;
    }

    CellVec live = {0}; live_cells(root, ORDER_R2L, &live);
    for (size_t c = 0; c < live.n; c++){
        uint32_t D = live.a[c].D, L = live.a[c].lab;
        const char* dr = dup_rule_name(D, L);
        if (dr){
            if (n >= cap){ *overflow = 1; cv_free(&live); return n; }
            out[n].kind = K_DUP; out[n].D = D; out[n].lab = L;
            out[n].path[0] = 0; out[n].rule = dr; n++;
        }
        int nb = enumerate_app_redexes(heap[D], rs, MAXREDEX, &ov);
        if (ov){ *overflow = 1; cv_free(&live); return n; }
        for (int i = 0; i < nb; i++){
            if (n >= cap){ *overflow = 1; cv_free(&live); return n; }
            out[n].kind = K_DUPVAL; out[n].D = D; out[n].lab = L;
            snprintf(out[n].path, MAXPATH, "%s", rs[i].path);
            out[n].rule = rs[i].rule; n++;
        }
    }
    cv_free(&live);
    return n;
}

/* semLocusOf: a structural path for tree apps, a DISCOVERY INDEX for heap
   dups — allocation-independent by construction, which is the whole reason a
   semantic film replays on an adversarial allocator. `?` where the kernel
   writes `?`: a cell absent from the discovery order. */
static void sem_locus_of(FRedex* r, const CellVec* order){
    if (r->kind == K_APP){ snprintf(r->locus, sizeof(r->locus), "t:%s", r->path); return; }
    int i = cv_index(order, r->D);
    char ix[16]; if (i < 0) snprintf(ix, sizeof(ix), "?"); else snprintf(ix, sizeof(ix), "%d", i);
    if (r->kind == K_DUP) snprintf(r->locus, sizeof(r->locus), "d:%s", ix);
    else                  snprintf(r->locus, sizeof(r->locus), "v:%s:%s", ix, r->path);
}

/* ── finding a cell's projections ─────────────────────────────────────────
   ic32 fires a dup from a demanded side and hands the result back to the
   demand site, so the film has to BE the demand site. This walks every slot
   reachable from the root — structural children, substitution slots, and the
   values of live cells — and collects the slots whose stored word is a
   projection of D. Substitution slots are reached explicitly (rather than
   chased past) precisely because a projection can live in one: an APP-LAM
   whose argument was a projection writes it into the binder's slot.

   Uniqueness is CHECKED, not assumed. A linear net has exactly one occurrence
   of each projection; if this ever finds two, the caller refuses rather than
   picking one and hoping. */
typedef struct { Term** a; size_t n, cap; } PVec;
static void pv_push(PVec* v, Term* s){
    if (v->n == v->cap){ v->cap = v->cap ? v->cap*2 : 64; v->a = (Term**)realloc(v->a, v->cap*sizeof(Term*)); }
    v->a[v->n++] = s;
}
static void find_projections(Term* rootslot, uint32_t D, PVec* p0, PVec* p1){
    U64Map seenSlot; map_init(&seenSlot, 4096);
    U64Map seenCell; map_init(&seenCell, 1024);
    PVec st = {0}; pv_push(&st, rootslot);
    int rootdone = 0;
    while (st.n){
        Term* s = st.a[--st.n];
        if (s == rootslot){ if (rootdone) continue; rootdone = 1; }
        else {
            int* seen = map_slot(&seenSlot, (uint64_t)(size_t)(s - heap));
            if (*seen == 1) continue; *seen = 1;
        }
        Term w = CLRSUB(*s);
        uint32_t A = ADDR(w);
        switch (TAG(w)){
            case T_VAR:
                if (ISSUB(heap[A])) pv_push(&st, &heap[A]);
                break;
            case T_DP0: case T_DP1: {
                if (ISSUB(heap[A])){ pv_push(&st, &heap[A]); break; }
                if (A == D) pv_push(TAG(w) == T_DP0 ? p0 : p1, s);
                int* c = map_slot(&seenCell, (uint64_t)A);
                if (*c != 1){ *c = 1; pv_push(&st, &heap[A]); }
                break;
            }
            case T_LAM:
                /* UNCONDITIONALLY, including a substituted binder slot. This
                   walk must be a SUPERSET of the reachability live_cells uses
                   — missing an occurrence is a wrong answer, whereas finding
                   one more is caught by the uniqueness check below. Skipping
                   ISSUB here would have made the two walks disagree about a
                   lambda whose binder was already consumed, which is exactly
                   where a projection can be hiding: APP-LAM writes its
                   argument into the binder's slot, and that argument can be a
                   dup projection. */
                pv_push(&st, &heap[A]);
                break;
            case T_APP: case T_SUP:
                pv_push(&st, &heap[A]); pv_push(&st, &heap[A+1]);
                break;
            default: break;
        }
    }
    free(st.a); map_free(&seenSlot); map_free(&seenCell);
}

/* ── fire one dup cell, using ic32's OWN rule implementation ──────────────
   `fire(D,L,k)` is the shipped runtime's dup interaction, unedited. It opens
   with whnf(heap[D]) — which costs NOTHING here, because dup_rule_name has
   already established by CHASING that the value is a Lam, Sup, Era, free Var
   or stuck App, and whnf returns each of those without an interaction. That is
   not an assumption: the caller checks that exactly one interaction happened,
   and a violated precondition shows up as a refusal rather than as a frame.

   ERA refuses. Enumerated so the terminal is honest, unfired so no rule ships
   without a witness. */
static int fire_dup(Term* rootslot, uint32_t D, uint32_t L, const char** rule_out){
    const char* rule = dup_rule_name(D, L);
    if (!rule) return 0;

    PVec p0 = {0}, p1 = {0};
    find_projections(rootslot, D, &p0, &p1);
    if (p0.n > 1 || p1.n > 1){ free(p0.a); free(p1.a); refuse("film-projection-not-unique"); }
    if (p0.n == 0 && p1.n == 0){ free(p0.a); free(p1.a); return 0; }

    int k = p0.n ? 0 : 1;
    Term* p = k == 0 ? p0.a[0] : p1.a[0];
    int wassub = ISSUB(*p) ? 1 : 0;
    free(p0.a); free(p1.a);

    /* fire() writes the OTHER side's value into heap[D] with the sub bit set,
       so the sibling projection resolves by chasing; this side is replaced
       where it stands. */
    Term h = fire(D, L, k);
    *p = wassub ? SETSUB(h) : h;
    *rule_out = rule;
    return 1;
}

/* ── fire exactly one app redex, addressed by path ────────────────────────
   ic32's heap is mutable, so "rebuild the spine with the new child" is a slot
   write rather than a persistent-tree rebuild. The walk therefore descends by
   SLOT POINTER, chasing at each level exactly as the kernel does; the
   difference is that the kernel REBUILDS the spine functionally while this
   writes the slot, which is equivalent exactly because a spine node on the way
   to a redex is uniquely referenced in a linear net. That equivalence is not
   asserted here; it is CHECKED, by the post-state the kernel recomputes when
   it replays the frame. */
static int step_at(Term* slot, const char* path, const char** rule_out){
    if (path && *path){
        Term t = ccanon_chase(*slot);
        char head[MAXPATH]; const char* dot = strchr(path, '.');
        size_t hl = dot ? (size_t)(dot - path) : strlen(path);
        if (hl >= MAXPATH) return 0;
        memcpy(head, path, hl); head[hl] = 0;
        const char* rest = dot ? dot + 1 : "";
        uint32_t A = ADDR(t);
        Term* next = NULL;
        if      (TAG(t) == T_LAM && !strcmp(head, "bod")) next = &heap[A];
        else if (TAG(t) == T_APP && !strcmp(head, "fun")) next = &heap[A];
        else if (TAG(t) == T_APP && !strcmp(head, "arg")) next = &heap[A+1];
        else if (TAG(t) == T_SUP && !strcmp(head, "lft")) next = &heap[A];
        else if (TAG(t) == T_SUP && !strcmp(head, "rgt")) next = &heap[A+1];
        if (!next) return 0;
        return step_at(next, rest, rule_out);
    }
    Term t = ccanon_chase(*slot);
    if (TAG(t) != T_APP) return 0;
    uint32_t A = ADDR(t);
    Term f = ccanon_chase(heap[A]);
    if (TAG(f) == T_LAM){
        uint32_t Lv = ADDR(f);
        Term arg = heap[A+1];
        Term bod = heap[Lv];
        heap[Lv] = SETSUB(arg);          /* APP-LAM: the binder becomes the argument */
        interactions++;
        FREE2(A);                        /* the consumed application node is dead */
        *slot = bod;
        *rule_out = "APP-LAM";
        return 1;
    }
    if (TAG(f) == T_SUP){
        /* (&L{a,b} c) -> !&L{c0,c1}=c; &L{(a c0),(b c1)} — ic32's own app_sup,
           which allocates the dup cell the kernel's applyAppAt allocates. */
        Term nt = app_sup(f, heap[A+1]);  /* interactions++ inside */
        FREE2(A);
        *slot = nt;
        *rule_out = "APP-SUP";
        return 1;
    }
    if (TAG(f) == T_ERA){
        /* (* a) -> *. ic32's whnf also runs `collect(heap[A+1])`, which frees
           the discarded argument's already-built APP/SUP/LAM spine and stops
           at DUP/VAR/ERA. That is RECLAMATION, not semantics — it moves slots
           onto a free list and changes nothing the canonical signature can
           see. It is kept rather than suppressed because the runtime under
           test must be the runtime that ships, and because suppressing it
           would make the film's memory behaviour differ from ic32's own for
           no semantic gain. Whether the free-scheduling order can reach a
           state where collect() frees a slot something live still points at
           is not argued here: it is MEASURED, by the C↔JS post-state
           agreement on the ERA fixtures. */
        interactions++;
        collect(heap[A+1]);
        FREE2(A);
        *slot = MK(T_ERA,0,0);
        *rule_out = "APP-ERA";
        return 1;
    }
    return 0;
}

/* ── the underlying redex a locus names ───────────────────────────────────
   GPT's ruling, B3 §(c): within one enabled semantic state, canonical locus
   assignment must be INJECTIVE over semantic redex identity — one redex gets
   at most one canonical locus. The representation makes an alias expressible:
   each findAppRedexes call carries its OWN visited set, so a node reachable
   both from the root and from inside a dup value is enumerated twice, once
   under `t:` and once under `v:`. Nothing in the 27 measured fixtures produces
   one, and the locus is committed into frame_id — so two spellings of one
   transition would be two canonical frame identities for the same pre, rule
   and post, which is not what "canonical" can mean.

   Identity is PHYSICAL and per-runtime: an application redex is its APP node,
   a dup redex is its cell. The two live in disjoint key spaces. C and JS
   cannot compare these to each other; each checks its own injectivity. */
static Term node_at(Term start, const char* path){
    Term t = ccanon_chase(start);
    while (path && *path){
        const char* dot = strchr(path, '.');
        size_t hl = dot ? (size_t)(dot - path) : strlen(path);
        char head[MAXPATH];
        if (hl >= MAXPATH) return 0;
        memcpy(head, path, hl); head[hl] = 0;
        uint32_t A = ADDR(t);
        Term nxt;
        if      (TAG(t) == T_LAM && !strcmp(head, "bod")) nxt = heap[A];
        else if (TAG(t) == T_APP && !strcmp(head, "fun")) nxt = heap[A];
        else if (TAG(t) == T_APP && !strcmp(head, "arg")) nxt = heap[A+1];
        else if (TAG(t) == T_SUP && !strcmp(head, "lft")) nxt = heap[A];
        else if (TAG(t) == T_SUP && !strcmp(head, "rgt")) nxt = heap[A+1];
        else return 0;
        t = ccanon_chase(nxt);
        path = dot ? dot + 1 : "";
    }
    return t;
}
static uint64_t redex_identity(Term root, FRedex* r){
    if (r->kind == K_DUP) return ((uint64_t)1 << 40) | (uint64_t)r->D;
    Term base = (r->kind == K_APP) ? root : heap[r->D];
    Term t = node_at(base, r->path);
    if (!t || TAG(t) != T_APP) return 0;
    return (uint64_t)ADDR(t);
}

/* dispatch: the three redex kinds address three different slots. A `v:` redex
   fires INSIDE a live cell's value, which in ic32 is the cell slot itself —
   the kernel's `d.val = applyAppAt(d.val, path)`, one representation over. */
static int fire_float(Term* rootslot, FRedex* r, const char** rule_out){
    if (r->kind == K_APP)    return step_at(rootslot, r->path, rule_out);
    if (r->kind == K_DUPVAL) return step_at(&heap[r->D], r->path, rule_out);
    return fire_dup(rootslot, r->D, r->lab, rule_out);
}

static void sha_of(const char* s, char out[65]){ sha256_str(s, out); }

/* ── rule / locus tallies, for the measurement only ──────────────────────── */
#define NRULES 9
static const char* RULE_NAMES[NRULES] = {
    "APP-LAM","APP-SUP","APP-ERA","DUP-LAM","DUP-SUP=","DUP-SUP!","DUP-ERA","DUP-VAR","DUP-APP" };
static int rule_index(const char* r){
    for (int i = 0; i < NRULES; i++) if (!strcmp(RULE_NAMES[i], r)) return i;
    return -1;
}

/* ── STRICT INTEGER PARSE (B5.1) ──────────────────────────────────────────
   B5 shipped `strtol(argv[++i], NULL, 10)`, which is the C idiom that reads
   AS FAR AS IT CAN and reports nothing about the rest. GPT reproduced four
   consequences, and each is the same fault wearing different clothes: the
   emitter answered a question the caller did not ask.

       --budget abc     -> 0    a zero-frame BUDGET_EXHAUSTED film, valid in
                                every field, describing a policy nobody set
       --budget 3junk   -> 3    a typo silently becomes a budget
       --budget 1.5     -> 1    truncation nobody asked for
       --budget 1e30    -> LONG_MAX, errno ERANGE ignored, so the overflow
                                became NO BUDGET and the malformed request
                                came back a COMPLETE 21-frame NORMAL_FORM film

   The last is the worst: it is not an under-claim or a refusal, it is a
   confident complete answer to a different question. B5's own principle —
   being caught downstream is not the same as being honest upstream — held for
   -1 and not for any of these, because -1 was the only one strtol reported.

   endptr AND errno, both, because they catch different things: endptr catches
   what was not consumed, errno catches what was consumed and did not fit. */
static long parse_budget(const char* s){
    if (!s || !*s) refuse("film-budget-invalid");        /* "" consumes nothing */
    /* strtol ALSO SKIPS LEADING WHITESPACE AND ACCEPTS A LEADING '+', neither
       of which endptr or errno reports, so " 3" and "+3" would come back as 3
       with nothing to show they had been reshaped on the way in. GPT's spec is
       ^[0-9]+$ and this is that, with one exception kept deliberately: a
       leading '-' is allowed THROUGH so the value can be recognised as
       negative and refused by its own name below. Rejecting it here would tell
       a caller who wrote -1 that their spelling was wrong, when their spelling
       was fine and their policy was not. */
    if (isspace((unsigned char)s[0]) || s[0] == '+') refuse("film-budget-invalid");
    errno = 0;
    char* end = NULL;
    long v = strtol(s, &end, 10);
    if (errno == ERANGE)  refuse("film-budget-invalid"); /* consumed, did not fit */
    if (end == s || *end) refuse("film-budget-invalid"); /* trailing junk, or none read */
    /* A NEGATIVE BUDGET IS NOT A MALFORMED ONE, and it gets its own name. "-1"
       is syntactically a number: the caller expressed a policy, and the policy
       is out of range. "3junk" is not a number: the caller's intent cannot be
       recovered at all. Collapsing them under one code would hand a reader a
       refusal that cannot say whether to fix a value or fix a spelling —
       exactly the distinction lower-inputs-undecided lost, one layer over.
       Left unguarded a negative would seal a film claiming budget=-1 against
       steps=0, which replay refuses on sem-budget-mismatch. Zero is legitimate
       and means exactly what it says. */
    if (v < 0) refuse("film-budget-negative");
    return v;
}

int main(int argc, char** argv){
    int verbose = 0, probe_whnf = 0; const char* term_arg = NULL;
    long budget = 4096;
    /* WHAT THIS BINARY WAS COMPILED WITH, which is not what the source says.
       Under -DMAXFRAMES=4 a grep of the #define reports 4096 and the running
       program means 4 — so the configuration claim is answered by the artifact
       rather than by its source. Diagnostic mode: commits nothing, and is not
       reachable through FilmAuthority's options schema. */
    for (int i = 1; i < argc; i++) if (!strcmp(argv[i], "--limits")){
        printf("LIMITS ic32_film 0.5.1 MAXFRAMES=%d MAXPATH=%d MAXREDEX=%d\n",
               MAXFRAMES, MAXPATH, MAXREDEX);
        return 0;
    }
    for (int i = 1; i < argc; i++){
        if      (!strcmp(argv[i], "--measure")) g_measure = 1;
        else if (!strcmp(argv[i], "--probe-whnf")) { probe_whnf = 1; g_measure = 1; }
        else if (!strcmp(argv[i], "-v") || !strcmp(argv[i], "--verbose")) verbose = 1;
        else if (!strcmp(argv[i], "--budget")){
            /* A FLAG WITH NO VALUE IS NOT A TERM. The guard used to be
               `&& i + 1 < argc`, so a trailing `--budget` fell through to the
               else and BECAME term_arg — the parser then reported
               "expected name at ...--budget", a syntax error about the
               calculus for what is an argument error about the CLI. */
            if (i + 1 >= argc) refuse("film-budget-missing-value");
            budget = parse_budget(argv[++i]);
        }
        /* AN ARGUMENT THE EMITTER DOES NOT UNDERSTAND IS NOT SILENTLY A TERM.
           Anything unrecognized used to land in term_arg, so `--typo "<term>"`
           filmed the term with the flag discarded, and two terms kept the
           last. Both are the same species as the budget defect: a
           caller-supplied argument consumed without effect. */
        else if (argv[i][0] == '-' && argv[i][1]) refuse("film-unknown-flag");
        else if (term_arg)                        refuse("film-multiple-terms");
        else term_arg = argv[i];
    }
    if (!term_arg){
        fprintf(stderr, "usage: ic32_film [--measure|--probe-whnf] [-v] [--budget N] \"<term>\"\n");
        return 2;
    }
    heap = (Term*)calloc(HEAPCAP, sizeof(Term));
    if (!heap){ fprintf(stderr, "FATAL: heap alloc\n"); return 2; }
    reset_state();

    P = term_arg;
    Term root = parse_term(); ws();

    /* ── the film loop. One frame per fired redex, chained, until the pool is
          quiescent. The strategy is the kernel's LEFTMOST over the float-plane
          enumeration: every tree app redex precedes every dup redex, so rs[0]
          is the leftmost tree app whenever one exists and the leftmost live
          dup otherwise. Stated rather than implied — a different strategy is a
          different film, and replay judges the film it was handed.
          ─────────────────────────────────────────────────────────────────── */
    struct { char pre[65], post[65], locus[MAXPATH + 32], frame_id[65]; const char* rule; int enabled; } fr[MAXFRAMES];
    int nf = 0;
    char prev[65]; snprintf(prev, sizeof(prev), "genesis");
    char first_sig[1 << 14]; first_sig[0] = 0;
    int rule_count[NRULES]; for (int i = 0; i < NRULES; i++) rule_count[i] = 0;
    long locus_t = 0, locus_d = 0, locus_v = 0;

    /* ── THE PRECONDITION WITNESS (GPT's ruling, B3 §(b)) ─────────────────
       The emitter's one-interaction guard is POST-HOC on purpose: it measures
       what the shipped runtime actually did, including any future change
       inside fire() or whnf(), where a structural pre-check could only measure
       what we predict. GPT ruled the post-hoc guard is the stronger final
       instrument and asked for the prediction to be MEASURED SEPARATELY rather
       than left as prose.

       This is that measurement. For every live dup cell the classifier
       ADMITS — every head class dup_rule_name returns a rule for — it runs
       ic32's own whnf on the cell's value and reports two things:

           interaction delta        must be 0
           canonical semantic state must be unchanged

       The second clause is the one that matters and the one a counter alone
       would miss: whnf performs representation-level memoization (it writes
       the reduced head back into a stuck application's slot) WITHOUT counting
       an interaction. That is fine precisely because the canonical state does
       not move, and "fine" is a thing to check.

       It deliberately does NOT re-classify anything: a second inline rule
       recognizer beside dup_rule_name would be two semantic recognizers that
       can drift, which is the mechanism-duplication defect this tree has paid
       for twice. It asks the ONE classifier what it admits, and measures those. */
    if (probe_whnf){
        CellVec live = {0}; live_cells(root, ORDER_L2R, &live);
        printf("PROBE-WHNF ic32_film 0.5.1\n");
        printf("TERM %s\n", term_arg);
        for (size_t i = 0; i < live.n; i++){
            uint32_t D = live.a[i].D, L = live.a[i].lab;
            const char* r = dup_rule_name(D, L);
            if (!r) { printf("SKIP d:%zu not-admitted\n", i); continue; }
            char* s0 = canonical_signature(root); char h0[65]; sha_of(s0, h0); free(s0);
            long before = interactions;
            whnf(heap[D]);
            long delta = interactions - before;
            char* s1 = canonical_signature(root); char h1[65]; sha_of(s1, h1); free(s1);
            printf("WHNF %s delta=%ld state=%s\n", r, delta, strcmp(h0, h1) ? "CHANGED" : "same");
        }
        cv_free(&live);
        return 0;
    }

    if (g_measure){
        char* s0 = canonical_signature(root);
        char h0[65]; sha_of(s0, h0);
        printf("MEASURE ic32_film 0.5.1\n");
        printf("TERM %s\n", term_arg);
        printf("INITIAL %s\n", h0);
        free(s0);
    }

    static FRedex rx[MAXREDEX];
    int budget_exhausted = 0;
    long remaining_work = 0;
    for (;;){
        int overflow = 0;
        int n = enumerate_float_redexes(root, rx, MAXREDEX, &overflow);
        if (overflow) refuse("film-redex-enumeration-overflow");
        /* POOL-QUIESCENCE IS TESTED FIRST, AND THAT ORDER IS THE WHOLE
           BOUNDARY RULE. An empty pool is a NORMAL_FORM even when nf has just
           reached the budget: the computation finished, it did not run out of
           permission. Reading "steps == budget" as exhaustion would report a
           completed execution as an abandoned one — an under-claim, but still
           a false statement about what happened, and the one a proof consumer
           would most regret. church_exp_2_2 --budget 21 is the witness. */
        if (n == 0) break;                       /* pool-quiescent */
        /* THE BUDGET IS A TERMINAL, AND WAS A REFUSAL UNTIL v0.5.0. Work
           remains and we are denied a step, which is a FACT ABOUT THIS
           EXECUTION and therefore evidence. What stays forbidden is what was
           always forbidden: falling through to NORMAL_FORM with work
           remaining, the false quiescence this very fixture falsified an
           entire scheduling relation with. `n` here IS the fresh full-pool
           enumeration at the state we are sealing, so the terminal's
           remaining_work is measured and not inferred — but it is re-measured
           below anyway, for the same reason the quiescent terminal is: "the
           loop told me" is not evidence.

           Checked BEFORE the storage bound because the two are different
           kinds of limit. With the default they coincide numerically; raise
           --budget above MAXFRAMES and the storage refusal is reachable
           again, which is what keeps them distinguishable rather than merely
           declared distinct. */
        if (nf >= budget) { budget_exhausted = 1; break; }
        if (nf >= MAXFRAMES) refuse("film-too-many-frames");

        CellVec order = {0}; live_cells(root, ORDER_L2R, &order);
        for (int i = 0; i < n; i++) sem_locus_of(&rx[i], &order);

        /* CANONICAL LOCUS INJECTIVITY, checked at every state rather than
           assumed from a corpus that happens not to produce an alias. Refusing
           is the honest answer while precedence between two spellings is
           UNRULED: blessing both would put two frame_ids on one transition,
           and picking one silently would decide a rule nobody wrote down. */
        for (int i = 0; i < n; i++){
            uint64_t idi = redex_identity(root, &rx[i]);
            if (!idi) continue;
            for (int j = i + 1; j < n; j++)
                if (redex_identity(root, &rx[j]) == idi && strcmp(rx[i].locus, rx[j].locus) != 0){
                    cv_free(&order);
                    refuse("film-locus-alias");
                }
        }

        char* pre_sig = canonical_signature(root);
        if (!nf) snprintf(first_sig, sizeof(first_sig), "%s", pre_sig);
        sha_of(pre_sig, fr[nf].pre); free(pre_sig);
        snprintf(fr[nf].locus, sizeof(fr[nf].locus), "%s", rx[0].locus);
        fr[nf].enabled = n;

        if (g_measure && verbose){
            printf("ORDER %d cells=%zu\n", nf + 1, order.n);
            for (int i = 0; i < n; i++)
                printf("ENABLED %d %s %s\n", nf + 1, rx[i].locus, rx[i].rule);
        }
        cv_free(&order);

        long before = interactions;
        const char* rule = NULL;
        if (!fire_float(&root, &rx[0], &rule)) refuse("film-rule-not-implemented");
        if (strcmp(rule, rx[0].rule) != 0)      refuse("film-fired-rule-disagrees-with-enumeration");
        if (interactions - before != 1)         refuse("film-step-was-not-one-interaction");
        fr[nf].rule = rule;
        { int ri = rule_index(rule); if (ri >= 0) rule_count[ri]++; }
        if      (fr[nf].locus[0] == 't') locus_t++;
        else if (fr[nf].locus[0] == 'd') locus_d++;
        else                             locus_v++;

        char* post_sig = canonical_signature(root);
        sha_of(post_sig, fr[nf].post); free(post_sig);

        char* chain = sfmt("%s|%s|%s|%s|%s|%s", prev, fr[nf].pre, plane_of(rule), rule,
                           fr[nf].locus, fr[nf].post);
        sha_of(chain, fr[nf].frame_id); free(chain);
        snprintf(prev, sizeof(prev), "%s", fr[nf].frame_id);

        if (g_measure)
            printf("FRAME %d %s %s %s %s %s %d\n", nf + 1, rule, plane_of(rule),
                   fr[nf].locus, fr[nf].pre, fr[nf].post, fr[nf].enabled);
        nf++;
    }
    /* A ZERO-FRAME FILM IS TWO DIFFERENT FACTS and they must not share a
       name. Nothing fired because nothing was ENABLED is a bad fixture, and
       still refuses. Nothing fired because the budget was ZERO is an honest
       partial execution of length nought — the exact shape the round-6B audit
       forged and the v1 terminal accepted without proof, now GENERATED rather
       than forged, and judged by the repaired schema. */
    if (nf == 0 && !budget_exhausted) refuse("film-no-redex-at-source");

    /* THE TERMINAL, RE-ENUMERATED RATHER THAN INHERITED FROM THE LOOP EXIT,
       in both directions. Quiescence is concluded only after a FRESH FULL-POOL
       enumeration returns empty — not from "the loop ended", and not from "the
       rules I know how to fire are exhausted". Both of those are how a false
       normal form gets written down, and this fixture is the historical witness
       for the second: church_exp_2_2 at step 15 is what falsified
       law:sched.free.ast-term@1.

       The budget terminal gets the same treatment for the same reason, and the
       count it takes is the thing REPLAY WILL RE-DERIVE — the first number C's
       enumeration has ever had to agree with the JS oracle on, as opposed to
       agreeing about a state. A budget claim over a quiescent pool is refused
       here rather than emitted and left for replay to reject: this emitter's
       job is to be honest, not to be caught. */
    {
        int ov = 0;
        static FRedex chk[MAXREDEX];
        int remaining = enumerate_float_redexes(root, chk, MAXREDEX, &ov);
        if (ov) refuse("film-redex-enumeration-overflow");
        if (budget_exhausted){
            if (remaining <= 0) refuse("film-budget-terminal-quiescent");
            remaining_work = remaining;
        } else if (remaining != 0) refuse("film-not-quiescent-at-terminal");
    }

    char* final_sig = canonical_signature(root);
    char final_id[65]; sha_of(final_sig, final_id);
    /* A ZERO-FRAME FILM HAS NO FRAME TO TAKE A PRE-SIGNATURE FROM, and the
       state it starts in is the state it ends in. Taken here rather than
       special-cased in the printer, so the two signatures are the same object
       in both directions. */
    if (!nf) snprintf(first_sig, sizeof(first_sig), "%s", final_sig);

    /* READBACK, from POOL-QUIESCENCE and not from ic32's normal form. Those
       are different states with the same readback: the film's terminal keeps
       residual dups that normal() would resolve, and the semantic-film
       contract is about the former.

       v0.1.0 also asserted that the readback fired ZERO interactions, and that
       assertion was ACCIDENTALLY TRUE: on a one-step dup-free fixture resolving
       the state costs nothing at all, so a machine counter that never moved
       looked like a verified property. It is not one. The kernel's claim is
       that readback from quiescence fires no INTERACT-PLANE rule; ic32's
       `interactions` is not plane-classified — it counts every fire(), APP-LAM
       and DUP-VAR alike — so comparing it against zero measures a different
       quantity that happens to agree on the trivial case. On the lowered
       add(const 2, const 3) it fires FOUR, resolving residual projections the
       kernel's reference readback resolves by chasing without counting. The
       states agree; the counters do not, and the counter was never the claim.
       So the checked property is the quiescence above, and the count is
       REPORTED rather than asserted. */
    /* AND A PARTIAL FILM DOES NOT READ BACK AT ALL. normal() would perform
       precisely the work the budget denied, and a `normal_form` field beside a
       terminal saying the run was cut short is a second, contradictory answer
       to "what did this execution produce?" — a caller who reads the wrong one
       gets a value the evidence does not support. So the readback is guarded,
       and the two fields it produces are ABSENT from a budget film rather than
       present-and-to-be-ignored. `sealSemFilm` in the kernel makes the same
       choice: normal_form_id is set for NORMAL_FORM only. */
    long before_readback = interactions;
    long readback_steps = 0;
    char nf_id[70]; nf_id[0] = 0;
    if (!budget_exhausted){
        Term rb = normal(root);
        readback_steps = interactions - before_readback;
        sb_reset(); show_iter(rb); sb_putc(0);
        char nf_hex[65]; sha_of(sb, nf_hex);
        snprintf(nf_id, sizeof(nf_id), "sem-%s", nf_hex);
    }
    long film_interactions = before_readback;

    if (g_measure){
        if (budget_exhausted)
            printf("TERMINAL BUDGET_EXHAUSTED %d %s %ld budget=%ld\n",
                   nf, final_id, remaining_work, budget);
        else {
            printf("TERMINAL NORMAL_FORM %d %s 0\n", nf, final_id);
            printf("NF %s\n", sb);
            printf("NFID %s\n", nf_id);
        }
        printf("SIGLEN %zu\n", strlen(final_sig));
        printf("INTERACTIONS %ld readback_steps=%ld\n", film_interactions, readback_steps);
        for (int i = 0; i < NRULES; i++)
            if (rule_count[i]) printf("FIRE %s %d\n", RULE_NAMES[i], rule_count[i]);
        for (int i = 0; i < NRULES; i++)
            if (!rule_count[i]) printf("NEVER %s\n", RULE_NAMES[i]);
        printf("LOCUS t: %ld\n", locus_t);
        printf("LOCUS d: %ld\n", locus_d);
        printf("LOCUS v: %ld\n", locus_v);
        free(final_sig);
        return 0;
    }

    /* THE COMMITMENT, in the kernel's own field order — domain, last_frame,
       termination, steps, final_sem_id, normal_form_id, budget,
       remaining_work, planes — with "-" for each field the terminal class does
       not carry. That layout is law:film.terminal-witness@1 made concrete: the
       round-6B audit found budget and remaining_work OUTSIDE the commitment
       entirely, so mutating either left film_id unchanged. They are inside it
       here, which is why a resealed forgery has to move the id and an unsealed
       one dies on it. */
    char* fcommit = budget_exhausted
        ? sfmt("TRVM-SEMFILM-v1.1|%s|BUDGET_EXHAUSTED|%d|%s|-|%ld|%ld|%s",
               prev, nf, final_id, budget, remaining_work, PLANE_POOL)
        : sfmt("TRVM-SEMFILM-v1.1|%s|NORMAL_FORM|%d|%s|%s|-|-|%s",
               prev, nf, final_id, nf_id, PLANE_POOL);
    char film_id[65]; sha_of(fcommit, film_id); free(fcommit);

    printf("{\"ok\":true,");
    printf("\"emitter\":\"ic32_film\",\"emitter_version\":\"0.5.1\",");
    printf("\"domain\":\"TRVM-SEMFILM-v1.1\",");
    printf("\"source_term\":");
    { printf("\""); for (const char* p = term_arg; *p; p++){
        if (*p == '"' || *p == '\\') { putchar('\\'); putchar(*p); }
        else putchar(*p); } printf("\","); }
    printf("\"pre_sem_signature\":\"%s\",", first_sig);
    printf("\"post_sem_signature\":\"%s\",", final_sig);
    if (!budget_exhausted){
        printf("\"normal_form\":\"");
        for (const char* p = sb; *p; p++){
            if (*p == '"' || *p == '\\') { putchar('\\'); putchar(*p); }
            else putchar(*p); }
        printf("\",");
    }
    printf("\"interactions\":%ld,\"readback_steps\":%ld,", film_interactions, readback_steps);
    printf("\"film\":{\"frames\":[");
    for (int i = 0; i < nf; i++){
        printf("%s{\"i\":%d,\"plane\":\"%s\",\"rule\":\"%s\",", i ? "," : "", i,
               plane_of(fr[i].rule), fr[i].rule);
        printf("\"locus\":\"%s\",\"pre\":\"%s\",\"post\":\"%s\",", fr[i].locus, fr[i].pre, fr[i].post);
        printf("\"prev\":\"%s\",\"frame_id\":\"%s\"}",
               i ? fr[i-1].frame_id : "genesis", fr[i].frame_id);
    }
    printf("],\"terminal\":{\"termination\":\"%s\",\"steps\":%d,",
           budget_exhausted ? "BUDGET_EXHAUSTED" : "NORMAL_FORM", nf);
    printf("\"last_frame\":\"%s\",\"final_sem_id\":\"%s\",", prev, final_id);
    /* The witness fields for THIS terminal class and no others. A budget film
       carrying a normal_form_id, or a normal-form film carrying a budget,
       would be a schema with optional truth in it. */
    if (budget_exhausted) printf("\"budget\":%ld,\"remaining_work\":%ld,", budget, remaining_work);
    else                  printf("\"normal_form_id\":\"%s\",", nf_id);
    printf("\"planes\":[");
    { const char* p = PLANE_POOL; int first = 1; char buf[32]; int bi = 0;
      for (;; p++){
        if (*p == ',' || *p == 0){ buf[bi] = 0; printf("%s\"%s\"", first ? "" : ",", buf);
          first = 0; bi = 0; if (*p == 0) break; }
        else buf[bi++] = *p;
      } }
    printf("]},\"film_id\":\"%s\"}}\n", film_id);
    free(final_sig);
    return 0;
}
