/* ═══════════════════════════════════════════════════════════════════════════
   ic32_film.c — v0.1.0 — the execution plane ORIGINATES evidence

   Every semantic film in this tree so far was made by the law kernel. The C
   runtime has been able to say what semantic STATE it is in since round 12
   (ic32_canon.c, 48/48 byte-identical signatures), but a state is not a
   transition, and the evidence for every transition was still JavaScript's.

   This emits one frame of the TRVM-SEMFILM-v1.1 contract from ic32's own
   execution: the pre-state ic32 parsed, the redex ic32 found, the rule ic32
   fired, the post-state ic32 reached, and the terminal ic32 verified. The
   frame is then handed to the law kernel's OWN replaySemFilm — the same replay
   that judges JS films, on a fresh runtime, with no translation of meaning in
   between. A checker written for this occasion would be checking the occasion.

   THE THEOREM IS DELIBERATELY NARROW, and every clause of it is a checked
   precondition rather than an assumption about the fixture:

       For a frozen one-step fixture, the native C runtime independently emits
       a frame whose pre-state, enabled rule and canonical locus, post-state,
       and terminal status are accepted by the existing semantic-film contract
       without normalization or translation.

   WHAT THIS DOES NOT DO, stated here rather than discovered later:

     · It handles the DUP-FREE FRAGMENT ONLY. A term containing a dup cell is
       REFUSED by name (film-dup-cell-present), not silently skipped, because
       the `d:` and `v:` loci and the six DUP-* rules are unimplemented here.
       ic32_canon.c already canonicalizes dup-carrying terms and its 48/48
       covers them, so the film's narrower scope is visible rather than implied.
     · It emits ONE frame. Multi-frame films, BUDGET_EXHAUSTED terminals and
       the whole corpus are later work.
     · It does not replay. The C-side checker — films flowing the other
       direction — is the next step and is not claimed here.

   The canonicalizer is INCLUDED, not copied: ic32_canon.c is the same file the
   bridge gate replays at 48/48, which in turn includes ic32.c verbatim. So the
   pre and post ids this emits come from the same code that already agrees with
   the JS oracle byte-for-byte, and the only new C in the pipeline is redex
   enumeration and a single-step fire.

   Usage:  ic32_film "<term>"      one term, as an argument
           emits a TRVM-SEMFILM-v1.1 film as JSON on stdout, exit 0
           on any unmet precondition: {"ok":false,"reason":"…"} and exit 1
   ═══════════════════════════════════════════════════════════════════════════ */
#define IC32_CANON_NO_MAIN 1
#include "ic32_canon.c"

/* The declared RULE POOL, in the law kernel's own construction order
   ([...PLANES.INTERACT, ...PLANES.COLLAPSE]). It is committed inside film_id,
   so a different order is a different film and replay says so. */
#define PLANE_POOL "APP-LAM,APP-SUP,APP-ERA,DUP-LAM,DUP-SUP=,DUP-SUP!,DUP-ERA,DUP-VAR,DUP-APP"

static void refuse(const char* reason){
    printf("{\"ok\":false,\"reason\":\"%s\"}\n", reason);
    exit(1);
}

/* ── the dup-free precondition, checked over the whole reachable term ─────── */
static int reaches_dup_cell(Term root){
    U64Map seen; map_init(&seen, 1024);
    TVec st = {0}; tpush(&st, root);
    int found = 0;
    while (st.n && !found){
        Term t = ccanon_chase(st.a[--st.n]);
        uint64_t nk = (uint64_t)CLRSUB(t);
        int* s = map_slot(&seen, nk);
        if (*s == 1) continue; *s = 1;
        switch (TAG(t)){
            case T_DP0: case T_DP1: found = 1; break;
            case T_LAM: tpush(&st, heap[ADDR(t)]); break;
            case T_APP: tpush(&st, heap[ADDR(t)+1]); tpush(&st, heap[ADDR(t)]); break;
            case T_SUP: tpush(&st, heap[ADDR(t)+1]); tpush(&st, heap[ADDR(t)]); break;
            default: break;
        }
    }
    free(st.a); map_free(&seen);
    return found;
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
   `t:<path>` means. Root is the empty path, so the locus is exactly "t:". */
#define MAXPATH 480
#define MAXREDEX 4096
typedef struct { char path[MAXPATH]; const char* rule; } Redex;
typedef struct { Term t; char path[MAXPATH]; } WalkItem;

static int enumerate_app_redexes(Term root, Redex* out, int cap, int* overflow){
    U64Map seen; map_init(&seen, 4096);
    WalkItem* st = (WalkItem*)malloc(sizeof(WalkItem) * 65536);
    size_t sp = 0, stcap = 65536;
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
            if (it.path[0]) snprintf(st[sp].path, MAXPATH, "%s.%s", it.path, kids[i]);
            else            snprintf(st[sp].path, MAXPATH, "%s", kids[i]);
            sp++;
        }
    }
    free(st); map_free(&seen);
    return n;
}

/* ── fire exactly one app redex, addressed by path ────────────────────────
   ic32's heap is mutable, so "rebuild the spine with the new child" is a slot
   write rather than a persistent-tree rebuild. The walk therefore descends by
   SLOT POINTER. It refuses a path that passes through a substituted variable:
   the node behind such a slot is shared, and writing the slot would relocate
   somebody else's subterm. For the dup-free one-step fixtures this never
   arises — the redex is the root — and refusing is the honest response to a
   case this version does not implement. */
static int step_at(Term* slot, const char* path, const char** rule_out){
    if (path && *path){
        Term t = *slot;
        if (TAG(t) == T_VAR && ISSUB(heap[ADDR(t)])) return 0;   /* shared: refuse */
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
    if (TAG(f) != T_LAM){
        /* enumerated as APP-SUP or APP-ERA; firing those is not implemented in
           v0.1.0 and pretending otherwise is how a film round produces a frame
           nobody can replay */
        return 0;
    }
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

static void sha_of(const char* s, char out[65]){ sha256_str(s, out); }

int main(int argc, char** argv){
    if (argc < 2){ fprintf(stderr, "usage: ic32_film \"<term>\"\n"); return 2; }
    heap = (Term*)calloc(HEAPCAP, sizeof(Term));
    if (!heap){ fprintf(stderr, "FATAL: heap alloc\n"); return 2; }
    reset_state();

    P = argv[1];
    Term root = parse_term(); ws();

    if (reaches_dup_cell(root)) refuse("film-dup-cell-present");

    /* ── PRE ─────────────────────────────────────────────────────────────── */
    char* pre_sig = canonical_signature(root);
    char pre_id[65]; sha_of(pre_sig, pre_id);

    /* ── the redex ic32 found ────────────────────────────────────────────── */
    Redex rs[MAXREDEX]; int overflow = 0;
    int n = enumerate_app_redexes(root, rs, MAXREDEX, &overflow);
    if (overflow) refuse("film-redex-enumeration-overflow");
    if (n == 0)   refuse("film-no-redex-at-source");
    if (n != 1)   refuse("film-source-redex-ambiguous");

    char locus[MAXPATH + 4];
    snprintf(locus, sizeof(locus), "t:%s", rs[0].path);

    /* ── the step ic32 fired ─────────────────────────────────────────────── */
    long before = interactions;
    const char* rule = NULL;
    if (!step_at(&root, rs[0].path, &rule)) refuse("film-rule-not-implemented");
    if (strcmp(rule, rs[0].rule) != 0)      refuse("film-fired-rule-disagrees-with-enumeration");
    if (interactions - before != 1)         refuse("film-step-was-not-one-interaction");

    /* ── POST ────────────────────────────────────────────────────────────── */
    char* post_sig = canonical_signature(root);
    char post_id[65]; sha_of(post_sig, post_id);

    /* ── the terminal ic32 verified. NORMAL_FORM is not asserted, it is the
          same enumeration run again and required to be empty. ─────────────── */
    int overflow2 = 0;
    int rest = enumerate_app_redexes(root, rs, MAXREDEX, &overflow2);
    if (overflow2) refuse("film-redex-enumeration-overflow");
    if (rest != 0) refuse("film-not-normal-form-after-one-step");
    if (reaches_dup_cell(root)) refuse("film-dup-cell-present");   /* a step may make one */

    /* READBACK. The kernel's normal_form_id is semId(readback(post).str), and
       its readback RESOLVES the state before printing — so this must too.
       ic32's show_iter does not chase substitutions (nothing in ic32's own flow
       ever hands it an unresolved one, because normal() runs first), and the
       first version of this file printed "λa.(a b)": the binder NAME of a
       variable that had been substituted to λy.y. A readback that prints a
       binder where a term is bound is a well-formed string asserting an
       identity that does not hold, which is the same class of fault ic32's own
       reset_state comment warns about for free names.

       The kernel also asserts readback PURITY — from quiescence it must fire no
       INTERACT-plane rule — so the interaction count is required not to move.
       That is a check, not a comment: if resolving the state costs an
       interaction, this was not a normal form and the terminal was a lie. */
    long film_interactions = interactions;
    root = normal(root);
    if (interactions != film_interactions) refuse("film-readback-was-not-pure");
    sb_reset(); show_iter(root);
    sb_putc(0);
    char nf_hex[65]; sha_of(sb, nf_hex);
    char nf_id[70]; snprintf(nf_id, sizeof(nf_id), "sem-%s", nf_hex);

    /* ── the commitments ─────────────────────────────────────────────────── */
    char* chain = sfmt("genesis|%s|INTERACT|%s|%s|%s", pre_id, rule, locus, post_id);
    char frame_id[65]; sha_of(chain, frame_id);
    char* fcommit = sfmt("TRVM-SEMFILM-v1.1|%s|NORMAL_FORM|1|%s|%s|-|-|%s",
                         frame_id, post_id, nf_id, PLANE_POOL);
    char film_id[65]; sha_of(fcommit, film_id);

    printf("{\"ok\":true,");
    printf("\"emitter\":\"ic32_film\",\"emitter_version\":\"0.1.0\",");
    printf("\"domain\":\"TRVM-SEMFILM-v1.1\",");
    printf("\"source_term\":");
    { printf("\""); for (const char* p = argv[1]; *p; p++){
        if (*p == '"' || *p == '\\') { putchar('\\'); putchar(*p); }
        else putchar(*p); } printf("\","); }
    printf("\"pre_sem_signature\":\"%s\",", pre_sig);
    printf("\"post_sem_signature\":\"%s\",", post_sig);
    printf("\"normal_form\":\"");
    { for (const char* p = sb; *p; p++){
        if (*p == '"' || *p == '\\') { putchar('\\'); putchar(*p); }
        else putchar(*p); } printf("\","); }
    printf("\"interactions\":%ld,", film_interactions);
    printf("\"film\":{\"frames\":[{\"i\":0,\"plane\":\"INTERACT\",\"rule\":\"%s\",", rule);
    printf("\"locus\":\"%s\",\"pre\":\"%s\",\"post\":\"%s\",", locus, pre_id, post_id);
    printf("\"prev\":\"genesis\",\"frame_id\":\"%s\"}],", frame_id);
    printf("\"terminal\":{\"termination\":\"NORMAL_FORM\",\"steps\":1,");
    printf("\"last_frame\":\"%s\",\"final_sem_id\":\"%s\",", frame_id, post_id);
    printf("\"normal_form_id\":\"%s\",\"planes\":[", nf_id);
    { const char* p = PLANE_POOL; int first = 1; char buf[32]; int bi = 0;
      for (;; p++){
        if (*p == ',' || *p == 0){ buf[bi] = 0; printf("%s\"%s\"", first ? "" : ",", buf);
          first = 0; bi = 0; if (*p == 0) break; }
        else buf[bi++] = *p;
      } }
    printf("]},\"film_id\":\"%s\"}}\n", film_id);
    free(pre_sig); free(post_sig); free(chain); free(fcommit);
    return 0;
}
