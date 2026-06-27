// ic32.c -- a packed-word Interaction Calculus runtime.
//
// Implements the IC32 typed-node, floating-dup model (the representation
// ic_float.py pins down, and HVM3 uses) over SPEC.md's 64-bit tagged word.
//
// Word layout (SPEC.md §2.1, with the spare top label bit used as the IC32
// substitution flag):
//
//     bits [63..32] addr (32)   heap index of the target node
//     bit  [31]     sub  (1)    set when this slot holds a substitution
//     bits [30..4]  label (27)  DUP/SUP color
//     bits [3..0]   tag  (4)    VAR LAM APP ERA SUP DP0 DP1
//
// Substitution is in-place at the binder's heap slot (the IC32 trick): a VAR or
// DPk term's addr points at its binder node's slot; when the binder is consumed
// the substituted term is written there with the sub bit set, and reading the
// variable retrieves it. DUP nodes are bodyless and float on the heap, reached
// only through DP0/DP1 variables and fired lazily.
//
// Validated against ic_float.py / ic_ref.py on the same term battery (driver
// pipes terms on stdin; this prints the normal form on stdout).
//
//   build: gcc -O2 -o ic32 ic32.c
//   use:   echo 'TERM' | ./ic32

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <time.h>

typedef uint64_t Term;

#define TAG(t)   ((int)((t) & 0xF))
#define SUBF     (1ULL<<31)
#define LAB(t)   ((uint32_t)(((t) >> 4) & 0x7FFFFFF))
#define ADDR(t)  ((uint32_t)((t) >> 32))
#define ISSUB(t) ((t) & SUBF)
#define SETSUB(t) ((t) | SUBF)
#define CLRSUB(t) ((t) & ~SUBF)
#define MK(tag,lab,addr) ( ((Term)((tag)&0xF)) | (((Term)((lab)&0x7FFFFFF))<<4) | (((Term)(addr))<<32) )

enum { T_VAR=0, T_LAM=1, T_APP=2, T_ERA=3, T_SUP=4, T_DP0=5, T_DP1=6 };

// ---------------------------------------------------------------- heap
static Term    *heap;
static uint32_t hp = 1;                 // 0 == null; also the high-water mark (only grows)
static uint32_t HEAPCAP = 1u<<24;       // 16M slots
static long     interactions = 0;
static long     STEPCAP = 50000000;

// Free lists for slot recycling (HVM-style: interactions free their consumed redex nodes, and
// allocation reuses freed slots before bumping hp). Two size classes: 1-word cells and 2-word
// nodes. This is the whole "GC": interaction-net reduction is confluent and local, so a consumed
// node is dead the instant its rule fires -- no tracing, no pauses, O(1) per free.
static uint32_t *free1=NULL, *free2=NULL;
static int free1_n=0, free2_n=0, free1_cap=0, free2_cap=0;
static long     allocs=0;               // total slots handed out (counts requests, not bumps)
static long     live=0, peak_live=0;    // slots currently in use, and peak (true memory occupancy)
static int      gc_on=1;                 // toggle slot recycling (for measurement)
static void push_free(uint32_t **lst, int *n, int *cap, uint32_t a){
    if (*n >= *cap){ *cap = *cap ? *cap*2 : 1024; *lst = (uint32_t*)realloc(*lst, (size_t)(*cap)*sizeof(uint32_t)); }
    (*lst)[(*n)++] = a;
}
#define FREE1(a) do{ push_free(&free1,&free1_n,&free1_cap,(a)); live -= 1; }while(0)
#define FREE2(a) do{ push_free(&free2,&free2_n,&free2_cap,(a)); live -= 2; }while(0)

static uint32_t alloc_n(int n){
    allocs += n; live += n; if (live > peak_live) peak_live = live;
    if (gc_on && n == 1 && free1_n > 0) return free1[--free1_n];   // recycle a 1-word cell
    if (gc_on && n == 2 && free2_n > 0) return free2[--free2_n];   // recycle a 2-word node
    uint32_t a = hp; hp += n;
    if (hp >= HEAPCAP){ fprintf(stderr,"FATAL: heap overflow\n"); exit(2); }
    return a;
}
static void check_steps(void){
    if (interactions > STEPCAP){ printf("DIVERGES(step-cap)\n"); fflush(stdout); exit(3); }
}

// ---------------------------------------------------------------- reduction
static Term whnf(Term t);

// fire a floating DUP node at slot D, color L, demanded from side k (0|1)
static Term fire(uint32_t D, uint32_t L, int k){
    interactions++; check_steps();
    Term v = whnf(heap[D]);
    int vt = TAG(v);
    Term h0, h1;
    if (vt == T_SUP){
        uint32_t S = ADDR(v); uint32_t vl = LAB(v);
        Term a = heap[S], b = heap[S+1];
        if (vl == L){                         // DUP-SUP equal: annihilate
            h0 = a; h1 = b;
        } else {                              // DUP-SUP different: commute
            uint32_t Da = alloc_n(1); heap[Da] = a;
            uint32_t Db = alloc_n(1); heap[Db] = b;
            uint32_t S0 = alloc_n(2); heap[S0] = MK(T_DP0,L,Da); heap[S0+1] = MK(T_DP0,L,Db);
            uint32_t S1 = alloc_n(2); heap[S1] = MK(T_DP1,L,Da); heap[S1+1] = MK(T_DP1,L,Db);
            h0 = MK(T_SUP,vl,S0); h1 = MK(T_SUP,vl,S1);
        }
        FREE2(S);                             // the consumed superposition node is dead
    } else if (vt == T_LAM){                  // DUP-LAM
        uint32_t Lv = ADDR(v);
        uint32_t Lx0 = alloc_n(1), Lx1 = alloc_n(1);
        uint32_t Df  = alloc_n(1); heap[Df] = heap[Lv];   // salvage body, dup it
        heap[Lx0] = MK(T_DP0,L,Df);
        heap[Lx1] = MK(T_DP1,L,Df);
        uint32_t Ss = alloc_n(2);
        heap[Ss] = MK(T_VAR,0,Lx0); heap[Ss+1] = MK(T_VAR,0,Lx1);
        heap[Lv] = SETSUB(MK(T_SUP,L,Ss));    // the lambda's var becomes a superposition
        h0 = MK(T_LAM,0,Lx0); h1 = MK(T_LAM,0,Lx1);
    } else if (vt == T_ERA){                  // DUP-ERA
        h0 = MK(T_ERA,0,0); h1 = MK(T_ERA,0,0);
    } else if (vt == T_APP){                  // DUP-APP (collapse): copy structure
        uint32_t A = ADDR(v); Term f = heap[A], a = heap[A+1];
        uint32_t Df = alloc_n(1); heap[Df] = f;
        uint32_t Dx = alloc_n(1); heap[Dx] = a;
        uint32_t A0 = alloc_n(2); heap[A0] = MK(T_DP0,L,Df); heap[A0+1] = MK(T_DP0,L,Dx);
        uint32_t A1 = alloc_n(2); heap[A1] = MK(T_DP1,L,Df); heap[A1+1] = MK(T_DP1,L,Dx);
        h0 = MK(T_APP,0,A0); h1 = MK(T_APP,0,A1);
        FREE2(A);                             // the consumed application node is dead
    } else {                                  // VAR free/stuck: DUP-VAR copy
        h0 = v; h1 = v;
    }
    if (k == 0){ heap[D] = SETSUB(h1); return h0; }
    else       { heap[D] = SETSUB(h0); return h1; }
}

// (&L{a,b} c) -> !&L{c0,c1}=c; &L{(a c0),(b c1)}
static Term app_sup(Term sup, Term arg){
    interactions++; check_steps();
    uint32_t S = ADDR(sup); uint32_t L = LAB(sup);
    Term a = heap[S], b = heap[S+1];
    uint32_t Dc = alloc_n(1); heap[Dc] = arg;
    uint32_t Aa = alloc_n(2); heap[Aa] = a; heap[Aa+1] = MK(T_DP0,L,Dc);
    uint32_t Ab = alloc_n(2); heap[Ab] = b; heap[Ab+1] = MK(T_DP1,L,Dc);
    uint32_t Sn = alloc_n(2); heap[Sn] = MK(T_APP,0,Aa); heap[Sn+1] = MK(T_APP,0,Ab);
    FREE2(S);                                 // the consumed superposition node is dead
    return MK(T_SUP,L,Sn);
}

// Eraser propagation (Phase-2 reclamation): free the uniquely-owned sub-net rooted at t, i.e.
// the argument discarded by APP-ERA. Safe because IC sharing happens ONLY through DUP nodes:
// we free the APP/SUP/LAM spine that lies above any dup, and STOP at DUP/VAR/ERA (whose targets
// may be shared with live structure or bound elsewhere). Iterative, so deep structures don't grow
// the C stack -- matching the rest of ic32's deep-robustness. NOTE the honest limit: under lazy
// normalization a discarded argument is frequently an unevaluated VAR (a substitution binding)
// rather than built structure, so this reclaims only the already-built spine; the dup-projection
// case (ERA-DUP) and affine unused-binder case are left to the encoding / Phase 3.
static Term* cstk=NULL; static long ccap=0;
static int   erase_on=1;
static void collect(Term root){
    if (!erase_on) return;
    if (!cstk){ ccap = 1<<12; cstk = (Term*)malloc(ccap*sizeof(Term)); }
    long csp = 0; cstk[csp++] = root;
    while (csp > 0){
        Term t = cstk[--csp];
        int tag = TAG(t);
        if (csp + 2 >= ccap){ ccap *= 2; cstk = (Term*)realloc(cstk, ccap*sizeof(Term)); }
        if (tag == T_APP){ uint32_t A = ADDR(t); cstk[csp++] = heap[A]; cstk[csp++] = heap[A+1]; FREE2(A); }
        else if (tag == T_SUP){ uint32_t S = ADDR(t); cstk[csp++] = heap[S]; cstk[csp++] = heap[S+1]; FREE2(S); }
        else if (tag == T_LAM){ uint32_t Lv = ADDR(t); cstk[csp++] = heap[Lv]; FREE1(Lv); }
        // T_VAR, T_DP0, T_DP1, T_ERA: stop (target may be shared or bound elsewhere) -- safe.
    }
}

static Term whnf(Term t){
    for (;;){
        int tag = TAG(t);
        if (tag == T_VAR){
            Term w = heap[ADDR(t)];
            if (ISSUB(w)){ t = CLRSUB(w); continue; }
            return t;                          // free / unsubstituted
        }
        if (tag == T_DP0 || tag == T_DP1){
            uint32_t D = ADDR(t);
            Term w = heap[D];
            if (ISSUB(w)){ t = CLRSUB(w); continue; }   // sibling already fired
            t = fire(D, LAB(t), tag == T_DP0 ? 0 : 1);
            continue;
        }
        if (tag == T_APP){
            uint32_t A = ADDR(t);
            Term f = whnf(heap[A]);
            int ft = TAG(f);
            if (ft == T_LAM){                  // APP-LAM
                interactions++; check_steps();
                uint32_t Lv = ADDR(f);
                Term arg = heap[A+1];
                Term bod = heap[Lv];
                heap[Lv] = SETSUB(arg);
                FREE2(A);                      // the consumed application node is dead
                t = bod; continue;
            }
            if (ft == T_SUP){ t = app_sup(f, heap[A+1]); FREE2(A); continue; }
            if (ft == T_ERA){ interactions++; check_steps(); collect(heap[A+1]); FREE2(A); t = MK(T_ERA,0,0); continue; }
            heap[A] = f;                       // stuck: memoize reduced fun
            return MK(T_APP,0,A);
        }
        return t;                              // LAM, SUP, ERA
    }
}

// iterative full normaliser: explicit stack of slot pointers (heap is fixed-size, so
// &heap[i] pointers stay valid across whnf's allocations). Handles arbitrarily deep results
// without growing the C stack.
static Term** nstk = NULL; static long ncap = 0;
static Term normal(Term t){
    if (!nstk){ ncap = 1<<16; nstk = (Term**)malloc(ncap*sizeof(Term*)); }
    static Term root; root = t;
    long sp = 0; nstk[sp++] = &root;
    while (sp){
        if (sp + 2 >= ncap){ ncap *= 2; nstk = (Term**)realloc(nstk, ncap*sizeof(Term*)); }
        Term* slot = nstk[--sp];
        Term v = whnf(*slot); *slot = v;
        int tag = TAG(v);
        if (tag == T_LAM){ uint32_t L = ADDR(v); nstk[sp++] = &heap[L]; }
        else if (tag == T_APP){ uint32_t A = ADDR(v); nstk[sp++] = &heap[A]; nstk[sp++] = &heap[A+1]; }
        else if (tag == T_SUP){ uint32_t S = ADDR(v); nstk[sp++] = &heap[S]; nstk[sp++] = &heap[S+1]; }
    }
    return root;
}

// ---------------------------------------------------------------- naming
// free-var slots and their names (set at parse time)
#define MAXNAMES 8192
// ---------------------------------------------------------------- naming
// free-var slots and their names (set at parse time); growable so deep terms cannot overflow
static uint32_t* free_loc = NULL; static char (*free_nm)[40] = NULL; static int n_free=0, free_cap=0;
// binder-name assignment during stringify
static uint32_t* bnd_loc = NULL;  static char (*bnd_nm)[12] = NULL;  static int n_bnd=0, bnd_cap=0;
static int name_ctr=0;
static void free_ensure(int need){
    if (need <= free_cap) return;
    int c = free_cap ? free_cap*2 : 8192; while (c < need) c *= 2;
    free_loc = (uint32_t*)realloc(free_loc, (size_t)c*sizeof(uint32_t));
    free_nm  = (char(*)[40])realloc(free_nm, (size_t)c*40); free_cap = c;
}
static void bnd_ensure(int need){
    if (need <= bnd_cap) return;
    int c = bnd_cap ? bnd_cap*2 : 8192; while (c < need) c *= 2;
    bnd_loc = (uint32_t*)realloc(bnd_loc, (size_t)c*sizeof(uint32_t));
    bnd_nm  = (char(*)[12])realloc(bnd_nm, (size_t)c*12); bnd_cap = c;
}

static const char* free_lookup(uint32_t loc){
    for (int i=0;i<n_free;i++) if (free_loc[i]==loc) return free_nm[i];
    return NULL;
}
static uint32_t free_intern(const char* nm){
    for (int i=0;i<n_free;i++) if (!strcmp(free_nm[i],nm)) return free_loc[i];
    uint32_t L = alloc_n(1); heap[L] = MK(T_ERA,0,0);   // sentinel (sub-clear => free)
    free_ensure(n_free+1);
    free_loc[n_free]=L; strncpy(free_nm[n_free],nm,39); free_nm[n_free][39]=0; n_free++;
    return L;
}
static const char* bnd_name(uint32_t loc){
    for (int i=0;i<n_bnd;i++) if (bnd_loc[i]==loc) return bnd_nm[i];
    bnd_ensure(n_bnd+1);
    char* s = bnd_nm[n_bnd]; int i=name_ctr++;
    if (i<26){ s[0]='a'+i; s[1]=0; } else { snprintf(s,12,"v%d",i); }
    bnd_loc[n_bnd]=loc; n_bnd++;
    return s;
}

// ---------------------------------------------------------------- parser
typedef struct { char nm[40]; Term t; } Bind;
static Bind* scope = NULL; static int sp = 0; static int scope_cap = 0;
static void scope_ensure(int need){
    if (need <= scope_cap) return;
    int nc = scope_cap ? scope_cap : 4096;
    while (nc < need) nc *= 2;
    scope = (Bind*)realloc(scope, (size_t)nc*sizeof(Bind)); scope_cap = nc;
}
// dup binder names pending while the iterative parser is still parsing the dup's value
typedef struct { char a[40], b[40]; } DupNames;
static DupNames* dnstk = NULL; static int dnsp = 0, dncap = 0;
// iterative-parser work item: an instruction over an explicit stack (replaces C recursion)
enum { OP_PARSE, OP_APP, OP_SUP, OP_LAM, OP_DUPVAL, OP_DUPBODY, OP_EXPECT };
typedef struct { int op; uint32_t x, y; } Ins;        // x,y: heap addr / label / expected char
static const char* P;     // parse cursor

static void perr(const char* m){ fprintf(stderr,"parse error: %s at ...%.20s\n", m, P); exit(4); }
static void ws(void){ while (*P==' '||*P=='\t'||*P=='\n'||*P=='\r') P++; }
static int  is_lambda(void){ return (*P=='\\') || ((unsigned char)P[0]==0xCE && (unsigned char)P[1]==0xBB); }
static void eat_lambda(void){ if (*P=='\\') P++; else P+=2; }
static char peek(void){ ws(); return *P; }
static void expect(char c){ ws(); if (*P!=c) perr("expected char"); P++; }
static void rdname(char* out){
    ws(); int i=0;
    while ((*P>='a'&&*P<='z')||(*P>='A'&&*P<='Z')||(*P>='0'&&*P<='9')||*P=='_'){ if(i<39) out[i++]=*P; P++; }
    out[i]=0; if (i==0) perr("expected name");
}
static uint32_t rduint(void){ ws(); uint32_t v=0; int any=0; while(*P>='0'&&*P<='9'){v=v*10+(*P-'0');P++;any=1;} return any?v:0; }

static Term parse_term(void);

// Iterative recursive-descent: an instruction stack drives parsing, a value stack collects
// sub-results. No C recursion, so input of arbitrary nesting depth parses without overflowing
// the stack. Scope bindings are pushed/popped by OP_LAM / OP_DUPVAL+OP_DUPBODY exactly where
// the recursive version did.
static Term parse_term(void){
    static Ins*  istk = NULL; static long icap = 0;
    static Term* vstk = NULL; static long vcap = 0;
    if (!istk){ icap = 1<<16; istk = (Ins*)malloc(icap*sizeof(Ins)); }
    if (!vstk){ vcap = 1<<16; vstk = (Term*)malloc(vcap*sizeof(Term)); }
    if (!dnstk){ dncap = 1<<12; dnstk = (DupNames*)malloc(dncap*sizeof(DupNames)); }
    long isp = 0, vsp = 0;
    #define IPUSH(O,X,Y) do{ if(isp>=icap){icap*=2; istk=(Ins*)realloc(istk,icap*sizeof(Ins));} \
                             istk[isp].op=(O); istk[isp].x=(X); istk[isp].y=(Y); isp++; }while(0)
    #define VPUSH(T)     do{ if(vsp>=vcap){vcap*=2; vstk=(Term*)realloc(vstk,vcap*sizeof(Term));} \
                             vstk[vsp++]=(T); }while(0)
    IPUSH(OP_PARSE,0,0);
    while (isp > 0){
        Ins in = istk[--isp];
        switch (in.op){
        case OP_PARSE: {
            ws();
            if (is_lambda()){
                eat_lambda(); char nm[40]; rdname(nm); expect('.');
                uint32_t L = alloc_n(1);
                scope_ensure(sp+1);
                strncpy(scope[sp].nm,nm,39); scope[sp].nm[39]=0; scope[sp].t = MK(T_VAR,0,L); sp++;
                IPUSH(OP_LAM, L, 0);                  // finish: heap[L]=body, pop scope, build LAM
                IPUSH(OP_PARSE, 0, 0);                // parse body
                break;
            }
            char c = *P;
            if (c=='*'){ P++; VPUSH(MK(T_ERA,0,0)); break; }
            if (c=='('){
                P++;
                IPUSH(OP_APP, 0, 0);                  // finish: eat ')', build APP
                IPUSH(OP_PARSE, 0, 0);                // parse arg
                IPUSH(OP_PARSE, 0, 0);                // parse fun (runs first)
                break;
            }
            if (c=='&' || c=='{'){
                uint32_t lab = 0;
                if (c=='&'){ P++; lab = rduint(); expect('{'); } else { P++; }
                IPUSH(OP_SUP, lab, 0);                // finish: eat '}', build SUP
                IPUSH(OP_PARSE, 0, 0);                // parse right
                IPUSH(OP_EXPECT, (uint32_t)',', 0);   // eat ','
                IPUSH(OP_PARSE, 0, 0);                // parse left (runs first)
                break;
            }
            if (c=='!'){
                P++; uint32_t lab=0; ws();
                if (*P=='&'){ P++; lab=rduint(); }
                expect('{'); char a[40],b[40]; rdname(a); expect(','); rdname(b); expect('}'); expect('=');
                uint32_t D = alloc_n(1);
                if (dnsp>=dncap){ dncap*=2; dnstk=(DupNames*)realloc(dnstk,dncap*sizeof(DupNames)); }
                strncpy(dnstk[dnsp].a,a,39); dnstk[dnsp].a[39]=0;
                strncpy(dnstk[dnsp].b,b,39); dnstk[dnsp].b[39]=0; dnsp++;
                IPUSH(OP_DUPBODY, 0, 0);              // finish: pop the two projection bindings
                IPUSH(OP_PARSE, 0, 0);                // parse body
                IPUSH(OP_DUPVAL, D, lab);             // after val: heap[D]=val, eat ';', push bindings
                IPUSH(OP_PARSE, 0, 0);                // parse val (outer scope; runs first)
                break;
            }
            char nm[40]; rdname(nm);                  // variable
            int found = 0;
            for (int i=sp-1;i>=0;i--) if (!strcmp(scope[i].nm,nm)){ VPUSH(scope[i].t); found=1; break; }
            if (!found) VPUSH(MK(T_VAR,0,free_intern(nm)));
            break;
        }
        case OP_APP: {
            Term a = vstk[--vsp], f = vstk[--vsp];
            expect(')');
            uint32_t A = alloc_n(2); heap[A]=f; heap[A+1]=a;
            VPUSH(MK(T_APP,0,A));
            break;
        }
        case OP_SUP: {
            Term r = vstk[--vsp], l = vstk[--vsp];
            expect('}');
            uint32_t S = alloc_n(2); heap[S]=l; heap[S+1]=r;
            VPUSH(MK(T_SUP, in.x, S));
            break;
        }
        case OP_LAM: {
            Term bod = vstk[--vsp];
            heap[in.x] = bod; sp--;                   // pop the lambda's binding
            VPUSH(MK(T_LAM,0,in.x));
            break;
        }
        case OP_DUPVAL: {
            Term val = vstk[--vsp];
            heap[in.x] = val;
            expect(';');
            dnsp--;
            scope_ensure(sp+2);
            strncpy(scope[sp].nm, dnstk[dnsp].a, 39); scope[sp].nm[39]=0; scope[sp].t = MK(T_DP0,in.y,in.x); sp++;
            strncpy(scope[sp].nm, dnstk[dnsp].b, 39); scope[sp].nm[39]=0; scope[sp].t = MK(T_DP1,in.y,in.x); sp++;
            break;                                    // dup floats; body becomes the form's value
        }
        case OP_DUPBODY: { sp -= 2; break; }          // pop the two projection bindings
        case OP_EXPECT:  { expect((char)in.x); break; }
        }
    }
    return vstk[0];
    #undef IPUSH
    #undef VPUSH
}

// ---------------------------------------------------------------- stringify (iterative)
static char *sb = NULL; static long sb_len = 0, sb_cap = 0;
static void sb_reset(void){ if (!sb){ sb_cap = 1<<16; sb = (char*)malloc(sb_cap); } sb_len = 0; }
static void sb_putc(char c){ if (sb_len+1 >= sb_cap){ sb_cap *= 2; sb = (char*)realloc(sb, sb_cap); } sb[sb_len++] = c; }
static void sb_puts(const char* s){ while (*s) sb_putc(*s++); }

// work item: render a Term (kind 0) or emit a literal (kind 1, static-storage pointer)
typedef struct { int kind; Term t; const char* lit; } WI;
static WI* wstk = NULL; static long wcap = 0;
// iterative readback -- no recursion, so arbitrarily deep normal forms read back safely
static void show_iter(Term t){
    if (!wstk){ wcap = 1<<16; wstk = (WI*)malloc(wcap*sizeof(WI)); }
    sb_reset();
    long sp = 0; wstk[sp++] = (WI){0, t, NULL};
    while (sp){
        if (sp + 6 >= wcap){ wcap *= 2; wstk = (WI*)realloc(wstk, wcap*sizeof(WI)); }
        WI w = wstk[--sp];
        if (w.kind == 1){ sb_puts(w.lit); continue; }
        Term x = w.t; int tag = TAG(x);
        if (tag == T_VAR){ uint32_t L = ADDR(x); const char* f = free_lookup(L); sb_puts(f ? f : bnd_name(L)); }
        else if (tag == T_ERA){ sb_putc('*'); }
        else if (tag == T_LAM){
            uint32_t L = ADDR(x);
            sb_putc((char)0xce); sb_putc((char)0xbb); sb_puts(bnd_name(L)); sb_putc('.');
            wstk[sp++] = (WI){0, heap[L], NULL};               // body renders next
        }
        else if (tag == T_APP){
            uint32_t A = ADDR(x);
            sb_putc('(');                                      // push reversed: f, " ", a, ")"
            wstk[sp++] = (WI){1, 0, ")"};
            wstk[sp++] = (WI){0, heap[A+1], NULL};
            wstk[sp++] = (WI){1, 0, " "};
            wstk[sp++] = (WI){0, heap[A], NULL};
        }
        else if (tag == T_SUP){
            uint32_t S = ADDR(x);
            char tmp[24]; snprintf(tmp, 24, "&%u{", LAB(x)); sb_puts(tmp);
            wstk[sp++] = (WI){1, 0, "}"};
            wstk[sp++] = (WI){0, heap[S+1], NULL};
            wstk[sp++] = (WI){1, 0, ","};
            wstk[sp++] = (WI){0, heap[S], NULL};
        }
        else if (tag == T_DP0){ sb_puts("DP0"); }
        else if (tag == T_DP1){ sb_puts("DP1"); }
        else sb_putc('?');
    }
    sb_putc(0);                                                 // NUL-terminate
}

// ---------------------------------------------------------------- self-test
static void reset_state(void){
    hp = 1; interactions = 0; n_free = 0; n_bnd = 0; name_ctr = 0; sp = 0; dnsp = 0;
    free1_n = 0; free2_n = 0; allocs = 0; live = 0; peak_live = 0;
}
static int one_test(const char* in, const char* expect){
    reset_state();
    P = in; Term t = parse_term(); ws();
    Term nf = normal(t); show_iter(nf);
    int ok = !strcmp(sb, expect);
    printf("  [%s] %-46s", ok?"PASS":"FAIL", in);
    if (!ok) printf("  got '%s' expected '%s'", sb, expect);
    putchar('\n');
    return ok;
}
// build (g (g (g ... (g z)))) with k applications DIRECTLY in the heap (no parser),
// so the deep-result test isolates the iterative normaliser + readback rather than the
// still-recursive parser.
static Term build_deep(int k){
    uint32_t g = free_intern("g"), z = free_intern("z");
    Term acc = MK(T_VAR,0,z);
    for (int i=0;i<k;i++){
        uint32_t A = alloc_n(2);
        heap[A]   = MK(T_VAR,0,g);
        heap[A+1] = acc;
        acc = MK(T_APP,0,A);
    }
    return acc;
}
// linear church numeral with an explicit duplicator label (the encoding a compiler emits).
static void clin_str(int n, int lab, char* buf){
    char* p = buf; p += sprintf(p, "\\f.\\x.");
    if (n <= 1){ sprintf(p, "(f x)"); return; }
    char cur[24]; strcpy(cur, "f");
    for (int i=0;i<n-1;i++){
        if (i<n-2){ p += sprintf(p,"!&%d{a%d,t%d}=%s;", lab,i,i,cur); sprintf(cur,"t%d",i); }
        else      { p += sprintf(p,"!&%d{a%d,a%d}=%s;", lab,i,i+1,cur); }
    }
    for (int i=0;i<n;i++) p += sprintf(p,"(a%d ",i);
    *p++='x'; for (int i=0;i<n;i++) *p++=')'; *p=0;
}
// count "(s " occurrences in the readback -> the church numeral read off (s (s ... z))
static long count_s(void){ long c=0; for (long i=0;i+2<sb_len;i++) if (sb[i]=='('&&sb[i+1]=='s'&&sb[i+2]==' ') c++; return c; }
static int church_arith(const char* term, long expect, const char* label){
    reset_state(); P = term; Term t = parse_term(); ws();
    Term nf = normal(t); show_iter(nf);
    long got = count_s(); int ok = (got == expect);
    printf("  [%s] %-28s s^%-4ld (expected s^%ld)\n", ok?"PASS":"FAIL", label, got, expect);
    return ok;
}
static int run_tests(void){
    printf("ic32 self-test battery\n");
    struct { const char* in; const char* out; } C[] = {
        {"(\\x.x a)",                       "a"},                       // beta / app-lam
        {"((\\x.\\y.x a) b)",               "a"},                       // nested app-lam
        {"!&0{a,b}=*;\\q.q",                "\xce\xbb""a.a"},           // DUP-ERA
        {"((\\f.\\x.(f (f x)) \\y.y) z)",   "z"},                       // church2 of identity
        {"&3{a,b}",                         "&3{a,b}"},                 // sup is normal
        {"!&0{a,b}=\\x.x;(a b)",            "\xce\xbb""a.a"},           // dup a lambda, then apply
        {"((\\f.\\x.(f (f x)) g) z)",       "(g (g z))"},               // church2 on a free var
        {"((\\f.\\x.!&0{a,b}=f;(a (b x)) g) z)", "(g (g z))"},          // same, explicit dup
    };
    int tot = (int)(sizeof(C)/sizeof(C[0])), pass = 0;
    for (int i=0;i<tot;i++) pass += one_test(C[i].in, C[i].out);

    // church arithmetic with proper IC encoding (explicit dups + distinct duplicator labels --
    // what a compiler emits). multiplication and exponentiation reduce correctly; the failures
    // seen with naive single-label / non-linear numerals are an input-encoding issue, not a
    // runtime defect.
    printf("  --- church arithmetic (explicit dups, distinct labels) ---\n");
    {
        static char a[2048], b[2048], term[5000];
        // mult(7,3) = (clin(7,lab1) (clin(3,lab0) s)) z = s^21
        clin_str(7,1,a); clin_str(3,0,b);
        snprintf(term,sizeof(term),"((%s (%s s)) z)", a, b);
        pass += church_arith(term, 21, "mult 7*3"); tot++;
        // exp: clin(3,lab1) clin(2,lab0) = 2^3 = s^8
        clin_str(3,1,a); clin_str(2,0,b);
        snprintf(term,sizeof(term),"(((%s %s) s) z)", a, b);
        pass += church_arith(term, 8, "exp 2^3"); tot++;
        // exp: clin(2,lab1) clin(5,lab0) = 5^2 = s^25
        clin_str(2,1,a); clin_str(5,0,b);
        snprintf(term,sizeof(term),"(((%s %s) s) z)", a, b);
        pass += church_arith(term, 25, "exp 5^2"); tot++;
    }

    // deep stress 1: full pipeline end-to-end -- iterative PARSER + normaliser + readback.
    // a recursive-descent parser overflows the C stack around ~4k nesting; this parses 200k-deep
    // input, normalizes, and reads it back.
    printf("  --- deep stress: iterative parser + normal + readback, end-to-end ---\n");
    reset_state();
    int KP = 200000;                               // (f (f (f ... (f x))))  with KP applications
    long cap = (long)KP*4 + 16; char* big = (char*)malloc(cap);
    char* bp = big;
    for (int i=0;i<KP;i++){ *bp++='('; *bp++='f'; *bp++=' '; }
    *bp++='x'; for (int i=0;i<KP;i++) *bp++=')'; *bp=0;
    P = big;
    Term pt = parse_term(); ws();
    Term pnf = normal(pt); show_iter(pnf);
    long papps = 0; for (long i=0;i+2 < sb_len;i++) if (sb[i]=='('&&sb[i+1]=='f'&&sb[i+2]==' ') papps++;
    int parse_ok = (papps == KP);
    printf("  [%s] (f^%d x): parsed + normalized + read back %ld bytes, %ld applications (expected %d)\n",
           parse_ok?"PASS":"FAIL", KP, sb_len-1, papps, KP);
    free(big);
    pass += parse_ok; tot++;

    // deep stress 2: in-heap build past the input-buffer limit -- normaliser + readback at 500k.
    printf("  --- deep stress: iterative normal + readback at half a million deep ---\n");
    reset_state();
    int K = 500000;
    Term deep = build_deep(K);
    Term dnf = normal(deep);
    show_iter(dnf);
    long gc = 0;
    for (long i=0;i+2 < sb_len;i++) if (sb[i]=='(' && sb[i+1]=='g' && sb[i+2]==' ') gc++;
    int deep_ok = (gc == K);
    printf("  [%s] g^%d z: normalized + read back %ld bytes, %ld applications (expected %d)\n",
           deep_ok?"PASS":"FAIL", K, sb_len-1, gc, K);
    pass += deep_ok; tot++;

    printf("  --- summary: %d/%d passed ---\n", pass, tot);
    return (pass==tot) ? 0 : 1;
}

// ---------------------------------------------------------------- main
int main(int argc, char** argv){
    heap = (Term*)calloc(HEAPCAP, sizeof(Term));
    if (!heap){ fprintf(stderr,"FATAL: heap alloc\n"); return 2; }

    if (argc>1 && !strcmp(argv[1],"--test")) return run_tests();

    if (argc>1 && !strcmp(argv[1],"--gcstats")){
        static char a[8192], b[8192], term[20000];
        struct { const char* name; int kind, x, y; } cs[] = {
            {"mult 12*12 = s^144", 0, 12, 12},
            {"mult 20*20 = s^400", 0, 20, 20},
            {"exp 2^8 = s^256",    1,  8, 2},
            {"exp 3^4 = s^81",     1,  4, 3},
        };
        printf("ic32 slot recycling -- heap high-water mark, recycling OFF vs ON\n");
        printf("(reduction is local + confluent, so a consumed redex node is dead immediately;\n");
        printf(" freeing it to a size-classed free list is the whole GC -- no tracing, no pauses)\n\n");
        printf("%-22s %12s %12s %12s %9s\n", "term", "hp_OFF", "hp_ON", "slots_req", "shrink");
        for (int i=0;i<4;i++){
            clin_str(cs[i].x,1,a); clin_str(cs[i].y,0,b);
            if (cs[i].kind==0) snprintf(term,sizeof(term),"((%s (%s s)) z)", a, b);
            else               snprintf(term,sizeof(term),"(((%s %s) s) z)", a, b);
            gc_on=0; reset_state(); P=term; { Term t0=parse_term(); ws(); normal(t0); }
            uint32_t hp_off=hp;
            gc_on=1; reset_state(); P=term; { Term t1=parse_term(); ws(); normal(t1); }
            uint32_t hp_on=hp; long slots=allocs;
            printf("%-22s %12u %12u %12ld %8.1f%%\n", cs[i].name, hp_off, hp_on, slots,
                   100.0*(double)(hp_off-hp_on)/(double)hp_off);
        }
        printf("\nhp_OFF is the old behavior (every alloc bumps; ~ total slots requested).\n");
        printf("hp_ON is the live high-water mark: peak simultaneous slots, bounded by recycling.\n");
        gc_on=1;
        return 0;
    }

    if (argc>1 && !strcmp(argv[1],"--erasestats")){
        int N=2000;
        static char spine[1<<16], term[1<<17];
        char* p=spine; for(int i=0;i<N;i++) p+=sprintf(p,"(g ");
        *p++='z'; for(int i=0;i<N;i++) *p++=')'; *p=0;
        struct { const char* name; const char* fmt; } cs[]={
            {"direct        (* spine)",                "(* %s)"},
            {"var-indirect  ((f x) with f=*)",         "((\\f.\\x.(f x) *) %s)"},
            {"affine-unused ((\\a.\\b.b spine) w)",     "((\\a.\\b.b %s) w)"},
        };
        printf("eraser propagation -- live slots remaining after reduction (spine depth %d)\n", N);
        printf("collect frees the discarded sub-net at APP-ERA; this shows WHERE it can reach.\n\n");
        printf("%-36s %10s %12s %12s\n","case","peak_live","live_OFF","live_ON");
        for (int i=0;i<3;i++){
            snprintf(term,sizeof(term),cs[i].fmt,spine);
            erase_on=0; reset_state(); P=term; { Term t=parse_term(); ws(); normal(t); }
            long loff=live, pk=peak_live;
            erase_on=1; reset_state(); P=term; { Term t=parse_term(); ws(); normal(t); }
            long lon=live;
            printf("%-36s %10ld %12ld %12ld\n", cs[i].name, pk, loff, lon);
        }
        printf("\ndirect erasure is reclaimed; the var-indirect and affine-unused cases are NOT --\n");
        printf("under lazy reduction the discarded thing is usually a var binding, not built\n");
        printf("structure, so it sits in a binder slot. those leaks need substitution-aware\n");
        printf("collection / compiler-inserted erasers, not a bigger collector.\n");
        erase_on=1;
        return 0;
    }

    static char buf[1<<24];
    size_t n = fread(buf,1,sizeof(buf)-1,stdin);
    buf[n]=0;
    // strip trailing whitespace/newline
    while (n>0 && (buf[n-1]=='\n'||buf[n-1]=='\r'||buf[n-1]==' '||buf[n-1]=='\t')) buf[--n]=0;

    int quiet = (argc>1 && !strcmp(argv[1],"-q"));   // skip stringify (for timing)
    int verbose = (argc>1 && (!strcmp(argv[1],"-v") || quiet));

    P = buf;
    Term t = parse_term();
    ws();

    struct timespec t0,t1;
    clock_gettime(CLOCK_MONOTONIC,&t0);
    Term nf = normal(t);
    clock_gettime(CLOCK_MONOTONIC,&t1);
    double red_ms = (t1.tv_sec-t0.tv_sec)*1e3 + (t1.tv_nsec-t0.tv_nsec)/1e6;

    if (!quiet){ show_iter(nf); fputs(sb,stdout); putchar('\n'); }
    if (verbose)
        fprintf(stderr,"interactions=%ld heap=%u reduce_ms=%.3f Minter_per_s=%.2f\n",
                interactions, hp, red_ms, interactions/(red_ms/1e3)/1e6);
    return 0;
}
