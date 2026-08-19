/* ═══════════════════════════════════════════════════════════════════════════
   ic32_film.c — v0.2.0 — the execution plane ORIGINATES evidence

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

     · v0.2.0 emits MULTI-FRAME films and TOLERATES dup cells, but fires only
       APP-plane rules. A term where a DUP-* rule becomes enabled is REFUSED by
       name (film-dup-rule-enabled), not silently skipped.

       That distinction was measured rather than assumed, and it is why v0.2.0
       is a smaller change than "implement the six DUP rules". The lowered
       add(const 2, const 3) CARRIES dup cells — Church addition duplicates its
       function argument and ic32's net is linear — and under the leftmost-tree-
       app strategy NOT ONE DUP RULE EVER FIRES: six APP-LAM frames at tree
       loci, and the residual dups are dead by the end. v0.1.0 refused that
       fixture on `film-dup-cell-present`, which was the right refusal for the
       wrong reason: the blocker was never the presence of dups, it was firing
       them. So the precondition moved from PRESENCE to ENABLEDNESS, which
       still has to be computed — the emitter classifies every live dup cell to
       decide quiescence honestly.
     · It stops at POOL-QUIESCENCE, not at ic32's `normal()`. Those are
       different states with the same readback: the film's terminal keeps
       residual dups that normal() would resolve, and the semantic-film contract
       is about the former. v0.1.0 got away with conflating them because its
       one-step fixture had neither.
     · BUDGET_EXHAUSTED terminals and the whole corpus are still later work.
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

/* ── live dup cells, and whether any of them has an ENABLED rule ──────────
   ic32 has no dup table: a dup is a heap cell reached through T_DP0/T_DP1
   projections, so the live cells are the distinct addresses those projections
   name. dupRule's classification, against the CHASED value:

       Lam                       DUP-LAM
       Sup, label equal/differ   DUP-SUP= / DUP-SUP!
       Era                       DUP-ERA
       free Var                  DUP-VAR
       stuck App (head is free)  DUP-APP
       anything else             no rule — a residual dup, which is legitimate
                                 at pool-quiescence and is not work

   The emitter needs this to say NORMAL_FORM honestly. Claiming quiescence
   while a dup rule was enabled would be a terminal the kernel refuses as
   sem-false-normal-form, and finding that out from the replay rather than from
   the emitter would mean the emitter had asserted something it never checked. */
static int dup_rule_enabled(uint32_t D){
    Term v = ccanon_chase(heap[D]);
    switch (TAG(v)){
        case T_LAM: case T_SUP: case T_ERA: return 1;
        case T_VAR: return is_free_var(v);
        case T_APP: {                       /* stuck iff the head chases to a free var */
            Term f = ccanon_chase(heap[ADDR(v)]);
            return TAG(f)==T_VAR && is_free_var(f);
        }
        default: return 0;
    }
}

static int any_dup_rule_enabled(Term root){
    U64Map seen; map_init(&seen, 4096);
    U64Map cells; map_init(&cells, 1024);
    TVec st = {0}; tpush(&st, root);
    int found = 0;
    while (st.n && !found){
        Term t = ccanon_chase(st.a[--st.n]);
        uint64_t nk = (uint64_t)CLRSUB(t);
        int* s = map_slot(&seen, nk);
        if (*s == 1) continue; *s = 1;
        switch (TAG(t)){
            case T_DP0: case T_DP1: {
                uint32_t D = ADDR(t);
                int* c = map_slot(&cells, (uint64_t)D);
                if (*c == 1) break; *c = 1;
                if (dup_rule_enabled(D)) { found = 1; break; }
                tpush(&st, heap[D]);        /* the cell's value is reachable too */
                break;
            }
            case T_LAM: tpush(&st, heap[ADDR(t)]); break;
            case T_APP: tpush(&st, heap[ADDR(t)+1]); tpush(&st, heap[ADDR(t)]); break;
            case T_SUP: tpush(&st, heap[ADDR(t)+1]); tpush(&st, heap[ADDR(t)]); break;
            default: break;
        }
    }
    free(st.a); map_free(&seen); map_free(&cells);
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
        // CHASE, then descend into the chased node's own slot. v0.1.0 refused a
        // substituted variable here, which was right for a one-step fixture and
        // wrong the moment a film has more than one frame: after an APP-LAM the
        // spine holds vars pointing at the substituted values, and every path
        // below the first frame runs through one. The kernel chases at each
        // level too — the difference is that it REBUILDS the spine functionally
        // while this writes the slot, which is equivalent exactly because a
        // spine node on the way to a redex is uniquely referenced in a linear
        // net. That equivalence is not asserted here; it is CHECKED, by the
        // post-state the kernel recomputes when it replays the frame.
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

    /* ── the film loop. One frame per fired redex, chained, until the pool is
          quiescent. The strategy is the kernel's: findFloatRedexes lists every
          TREE app redex before any dup redex, so rs[0] is the leftmost tree app
          whenever one exists, and the walk order here reproduces that exactly.
          ─────────────────────────────────────────────────────────────────── */
#define MAXFRAMES 4096
    struct { char pre[65], post[65], locus[MAXPATH + 4], frame_id[65]; const char* rule; } fr[MAXFRAMES];
    int nf = 0;
    char prev[65]; snprintf(prev, sizeof(prev), "genesis");
    char first_sig[1 << 14]; first_sig[0] = 0;

    for (;;){
        if (any_dup_rule_enabled(root)) refuse("film-dup-rule-enabled");

        Redex rs[MAXREDEX]; int overflow = 0;
        int n = enumerate_app_redexes(root, rs, MAXREDEX, &overflow);
        if (overflow) refuse("film-redex-enumeration-overflow");
        if (n == 0) break;                       /* pool-quiescent */
        if (nf >= MAXFRAMES) refuse("film-too-many-frames");

        char* pre_sig = canonical_signature(root);
        if (!nf) snprintf(first_sig, sizeof(first_sig), "%s", pre_sig);
        sha_of(pre_sig, fr[nf].pre); free(pre_sig);
        snprintf(fr[nf].locus, sizeof(fr[nf].locus), "t:%s", rs[0].path);

        long before = interactions;
        const char* rule = NULL;
        if (!step_at(&root, rs[0].path, &rule)) refuse("film-rule-not-implemented");
        if (strcmp(rule, rs[0].rule) != 0)      refuse("film-fired-rule-disagrees-with-enumeration");
        if (interactions - before != 1)         refuse("film-step-was-not-one-interaction");
        fr[nf].rule = rule;

        char* post_sig = canonical_signature(root);
        sha_of(post_sig, fr[nf].post); free(post_sig);

        char* chain = sfmt("%s|%s|INTERACT|%s|%s|%s", prev, fr[nf].pre, rule, fr[nf].locus, fr[nf].post);
        sha_of(chain, fr[nf].frame_id); free(chain);
        snprintf(prev, sizeof(prev), "%s", fr[nf].frame_id);
        nf++;
    }
    if (nf == 0) refuse("film-no-redex-at-source");

    /* ── READBACK, from POOL-QUIESCENCE and not from ic32's normal form.
          Those are different states with the same readback: the film's terminal
          keeps residual dups that normal() would resolve. The kernel's
          normal_form_id is semId(readback(post).str), and its readback asserts
          PURITY — from quiescence it must fire no INTERACT-plane rule. That is
          a check here too, not a remark: if resolving the state costs an
          interaction, this was not quiescent and the terminal was a lie.

          ic32's show_iter does not chase substitutions, because nothing in
          ic32's own flow ever hands it an unresolved one. v0.1.0 printed
          "λa.(a b)" — a binder NAME where a TERM was bound — until normal() was
          run first, which is a well-formed string asserting an identity that
          does not hold. ──────────────────────────────────────────────────── */
    /* POOL-QUIESCENCE, asserted rather than inherited from the loop exit. The
       loop stops when no tree app redex remains and no dup rule is enabled,
       which is exactly sem-false-normal-form's condition, and re-checking it
       here costs one walk and makes the terminal a measurement. */
    { int ov = 0; Redex chk[MAXREDEX];
      if (enumerate_app_redexes(root, chk, MAXREDEX, &ov) != 0 || ov)
          refuse("film-not-quiescent-at-terminal");
      if (any_dup_rule_enabled(root)) refuse("film-not-quiescent-at-terminal"); }

    char* final_sig = canonical_signature(root);
    char final_id[65]; sha_of(final_sig, final_id);

    /* READBACK, from POOL-QUIESCENCE and not from ic32's normal form.
       v0.1.0 also asserted that the readback fired ZERO interactions, and that
       assertion was ACCIDENTALLY TRUE: on a one-step dup-free fixture resolving
       the state costs nothing at all, so a machine counter that never moved
       looked like a verified property. It is not one. The kernel's claim is
       that readback from quiescence fires no INTERACT-PLANE rule; ic32's
       `interactions` is not plane-classified — it counts every fire(), app_sup
       and APP-LAM alike — so comparing it against zero measures a different
       quantity that happens to agree on the trivial case.

       On the lowered add(const 2, const 3) it fires FOUR, resolving residual
       projections the kernel's reference readback resolves by chasing without
       counting. The states agree; the counters do not, and the counter was
       never the claim. So the check is the one above — the pool is quiescent —
       and the count is REPORTED rather than asserted. What a plane-classified
       counter inside ic32 would buy is real and is declared open. */
    long before_readback = interactions;
    Term rb = normal(root);
    long readback_steps = interactions - before_readback;
    sb_reset(); show_iter(rb); sb_putc(0);
    char nf_hex[65]; sha_of(sb, nf_hex);
    char nf_id[70]; snprintf(nf_id, sizeof(nf_id), "sem-%s", nf_hex);
    long film_interactions = before_readback;

    char* fcommit = sfmt("TRVM-SEMFILM-v1.1|%s|NORMAL_FORM|%d|%s|%s|-|-|%s",
                         prev, nf, final_id, nf_id, PLANE_POOL);
    char film_id[65]; sha_of(fcommit, film_id); free(fcommit);

    printf("{\"ok\":true,");
    printf("\"emitter\":\"ic32_film\",\"emitter_version\":\"0.2.0\",");
    printf("\"domain\":\"TRVM-SEMFILM-v1.1\",");
    printf("\"source_term\":");
    { printf("\""); for (const char* p = argv[1]; *p; p++){
        if (*p == '"' || *p == '\\') { putchar('\\'); putchar(*p); }
        else putchar(*p); } printf("\","); }
    printf("\"pre_sem_signature\":\"%s\",", first_sig);
    printf("\"post_sem_signature\":\"%s\",", final_sig);
    printf("\"normal_form\":\"");
    { for (const char* p = sb; *p; p++){
        if (*p == '"' || *p == '\\') { putchar('\\'); putchar(*p); }
        else putchar(*p); } printf("\","); }
    printf("\"interactions\":%ld,\"readback_steps\":%ld,", film_interactions, readback_steps);
    printf("\"film\":{\"frames\":[");
    for (int i = 0; i < nf; i++){
        printf("%s{\"i\":%d,\"plane\":\"INTERACT\",\"rule\":\"%s\",", i ? "," : "", i, fr[i].rule);
        printf("\"locus\":\"%s\",\"pre\":\"%s\",\"post\":\"%s\",", fr[i].locus, fr[i].pre, fr[i].post);
        printf("\"prev\":\"%s\",\"frame_id\":\"%s\"}",
               i ? fr[i-1].frame_id : "genesis", fr[i].frame_id);
    }
    printf("],\"terminal\":{\"termination\":\"NORMAL_FORM\",\"steps\":%d,", nf);
    printf("\"last_frame\":\"%s\",\"final_sem_id\":\"%s\",", prev, final_id);
    printf("\"normal_form_id\":\"%s\",\"planes\":[", nf_id);
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
