/* ═══════════════════════════════════════════════════════════════════════════
   ic32_canon.c — the execution plane emits canonical semantic bytes

   TRVM's two planes have until now met only at the corpus: same 24 vectors,
   same committed hash. This is the first join computed by something other than
   JavaScript. It implements SEMSTATE-CANONICAL-v1 §2–§5 over ic32's OWN
   packed-word heap — chase, live discovery order, canonical fold, the two-phase
   signature with §5 compaction, and SHA-256 — so a C runtime can say what
   semantic state it is in, in the same bytes the law kernel says it in.

   This is deliberately NOT a transliteration of the JS hasher. It is written
   from the spec against a different representation: ic32 has no Dup node at
   all (a dup is a heap cell reached through T_DP0/T_DP1 projections), no node
   objects to memoize on, and free variables live in a side intern table. If
   the bytes still agree, the canonical form is a property of the calculus
   rather than an artifact of one implementation — which is the whole claim
   the pre-hash vectors exist to make falsifiable.

   ic32.c is included verbatim, with its main renamed. Nothing in it is edited:
   the runtime under test must be the runtime that ships.

   Usage:  ic32_canon [--nf]      terms on stdin, one per line
           emits  <sem_state_id>\t<sem_signature>  per line
           --nf   normalize each term first (default: initial state)
   ═══════════════════════════════════════════════════════════════════════════ */
#define main ic32_main_renamed
#include "../../runtime/c/ic32.c"
#undef main
#include <stdarg.h>

/* ── SHA-256 (FIPS 180-4), self-contained ─────────────────────────────────── */
typedef struct { uint32_t s[8]; uint64_t n; unsigned char b[64]; size_t bl; } SHA256;
static const uint32_t K256[64] = {
0x428a2f98,0x71374491,0xb5c0fbcf,0xe9b5dba5,0x3956c25b,0x59f111f1,0x923f82a4,0xab1c5ed5,
0xd807aa98,0x12835b01,0x243185be,0x550c7dc3,0x72be5d74,0x80deb1fe,0x9bdc06a7,0xc19bf174,
0xe49b69c1,0xefbe4786,0x0fc19dc6,0x240ca1cc,0x2de92c6f,0x4a7484aa,0x5cb0a9dc,0x76f988da,
0x983e5152,0xa831c66d,0xb00327c8,0xbf597fc7,0xc6e00bf3,0xd5a79147,0x06ca6351,0x14292967,
0x27b70a85,0x2e1b2138,0x4d2c6dfc,0x53380d13,0x650a7354,0x766a0abb,0x81c2c92e,0x92722c85,
0xa2bfe8a1,0xa81a664b,0xc24b8b70,0xc76c51a3,0xd192e819,0xd6990624,0xf40e3585,0x106aa070,
0x19a4c116,0x1e376c08,0x2748774c,0x34b0bcb5,0x391c0cb3,0x4ed8aa4a,0x5b9cca4f,0x682e6ff3,
0x748f82ee,0x78a5636f,0x84c87814,0x8cc70208,0x90befffa,0xa4506ceb,0xbef9a3f7,0xc67178f2};
#define ROR(x,n) (((x)>>(n))|((x)<<(32-(n))))
static void sha256_block(SHA256* c, const unsigned char* p){
    uint32_t w[64], a,b,cc,d,e,f,g,h,t1,t2;
    for (int i=0;i<16;i++) w[i]=(p[i*4]<<24)|(p[i*4+1]<<16)|(p[i*4+2]<<8)|p[i*4+3];
    for (int i=16;i<64;i++){
        uint32_t s0=ROR(w[i-15],7)^ROR(w[i-15],18)^(w[i-15]>>3);
        uint32_t s1=ROR(w[i-2],17)^ROR(w[i-2],19)^(w[i-2]>>10);
        w[i]=w[i-16]+s0+w[i-7]+s1;
    }
    a=c->s[0];b=c->s[1];cc=c->s[2];d=c->s[3];e=c->s[4];f=c->s[5];g=c->s[6];h=c->s[7];
    for (int i=0;i<64;i++){
        uint32_t S1=ROR(e,6)^ROR(e,11)^ROR(e,25), ch=(e&f)^((~e)&g);
        t1=h+S1+ch+K256[i]+w[i];
        uint32_t S0=ROR(a,2)^ROR(a,13)^ROR(a,22), mj=(a&b)^(a&cc)^(b&cc);
        t2=S0+mj;
        h=g;g=f;f=e;e=d+t1;d=cc;cc=b;b=a;a=t1+t2;
    }
    c->s[0]+=a;c->s[1]+=b;c->s[2]+=cc;c->s[3]+=d;c->s[4]+=e;c->s[5]+=f;c->s[6]+=g;c->s[7]+=h;
}
static void sha256_init(SHA256* c){
    c->s[0]=0x6a09e667;c->s[1]=0xbb67ae85;c->s[2]=0x3c6ef372;c->s[3]=0xa54ff53a;
    c->s[4]=0x510e527f;c->s[5]=0x9b05688c;c->s[6]=0x1f83d9ab;c->s[7]=0x5be0cd19;
    c->n=0;c->bl=0;
}
static void sha256_update(SHA256* c, const void* data, size_t len){
    const unsigned char* p=(const unsigned char*)data; c->n+=len;
    while (len){
        size_t k=64-c->bl; if (k>len) k=len;
        memcpy(c->b+c->bl,p,k); c->bl+=k; p+=k; len-=k;
        if (c->bl==64){ sha256_block(c,c->b); c->bl=0; }
    }
}
static void sha256_hex(SHA256* c, char out[65]){
    uint64_t bits=c->n*8; unsigned char pad[72]; size_t i=0;
    pad[i++]=0x80; while (((c->bl+i)%64)!=56) pad[i++]=0;
    for (int j=7;j>=0;j--) pad[i++]=(unsigned char)((bits>>(j*8))&0xFF);
    sha256_update(c,pad,i); c->n=0;
    for (int j=0;j<8;j++) snprintf(out+j*8,9,"%08x",c->s[j]);
    out[64]=0;
}
static void sha256_str(const char* s, char out[65]){
    SHA256 c; sha256_init(&c); sha256_update(&c,s,strlen(s)); sha256_hex(&c,out);
}

/* ── uint64 → int maps (open addressing; ids by first occurrence) ─────────── */
typedef struct { uint64_t* k; int* v; unsigned char* used; size_t cap, n; } U64Map;
static void map_init(U64Map* m, size_t cap){
    m->cap=cap; m->n=0;
    m->k=(uint64_t*)calloc(cap,sizeof(uint64_t));
    m->v=(int*)calloc(cap,sizeof(int));
    m->used=(unsigned char*)calloc(cap,1);
}
static void map_free(U64Map* m){ free(m->k); free(m->v); free(m->used); m->k=NULL;m->v=NULL;m->used=NULL; }
static void map_grow(U64Map* m);
static int* map_slot(U64Map* m, uint64_t key){
    if (m->n*2 >= m->cap) map_grow(m);
    size_t h=(size_t)((key*0x9E3779B97F4A7C15ULL)>>32) & (m->cap-1);
    for (;;){
        if (!m->used[h]){ m->used[h]=1; m->k[h]=key; m->v[h]=-1; m->n++; return &m->v[h]; }
        if (m->k[h]==key) return &m->v[h];
        h=(h+1)&(m->cap-1);
    }
}
static void map_grow(U64Map* m){
    U64Map o=*m; map_init(m,o.cap*2);
    for (size_t i=0;i<o.cap;i++) if (o.used[i]) *map_slot(m,o.k[i])=o.v[i];
    map_free(&o);
}
/* id by FIRST OCCURRENCE — §5 phase 1 is renaming-equivariant precisely because
   the counter advances in traversal order and never on re-encounter. */
static int intern(U64Map* m, int* ctr, uint64_t key){
    int* v=map_slot(m,key);
    if (*v < 0) *v = (*ctr)++;
    return *v;
}

/* name keys live in two disjoint spaces: lambda binders are heap locations,
   dup projections are (cell, side). ic32 has no Dup NODE, so its two
   projections must be given names the spec's Dup rule can print. */
#define NK_LAM(L)      (((uint64_t)0<<40) | (uint64_t)(L))
#define NK_DUP(D,side) (((uint64_t)1<<40) | ((uint64_t)(D)*2 + (uint64_t)(side)))

/* ── §2 chase: transparent substitution resolution ───────────────────────── */
static Term ccanon_chase(Term t){
    for (int hops=0; hops<1000000; hops++){
        int tag=TAG(t);
        if (tag==T_VAR){
            Term w=heap[ADDR(t)];
            if (ISSUB(w)){ t=CLRSUB(w); continue; }
            return t;
        }
        if (tag==T_DP0||tag==T_DP1){
            Term w=heap[ADDR(t)];
            if (ISSUB(w)){ t=CLRSUB(w); continue; }   /* sibling already fired */
            return t;
        }
        return t;
    }
    return t;
}
static int is_free_var(Term t){ return TAG(t)==T_VAR && free_lookup(ADDR(t))!=NULL; }

/* ── §3 live discovery order over dup CELLS ──────────────────────────────── */
/* JS walks its heap-of-dups; ic32 has no such table, so the same order is
   recovered by treating a first-seen T_DP0/T_DP1 as the discovery of its cell
   and pushing that cell's value — which is exactly what §3 specifies. */
typedef struct { uint32_t* a; size_t n, cap; } U32Vec;
static void vec_push(U32Vec* v, uint32_t x){
    if (v->n==v->cap){ v->cap=v->cap?v->cap*2:64; v->a=(uint32_t*)realloc(v->a,v->cap*sizeof(uint32_t)); }
    v->a[v->n++]=x;
}
typedef struct { Term* a; size_t n, cap; } TVec;
static void tpush(TVec* v, Term x){
    if (v->n==v->cap){ v->cap=v->cap?v->cap*2:256; v->a=(Term*)realloc(v->a,v->cap*sizeof(Term)); }
    v->a[v->n++]=x;
}

/* ── §5 the canonical signature ──────────────────────────────────────────── */
/* A string arena so signatures can be memoized per node without a GC. */
typedef struct { char** s; size_t n, cap; } SVec;
static size_t sv_put(SVec* v, const char* s){
    if (v->n==v->cap){ v->cap=v->cap?v->cap*2:256; v->s=(char**)realloc(v->s,v->cap*sizeof(char*)); }
    v->s[v->n]=strdup(s); return v->n++;
}
static void sv_free(SVec* v){ for (size_t i=0;i<v->n;i++) free(v->s[i]); free(v->s); }

typedef struct {
    U64Map nid, lid, memo;      /* names, labels, node → signature index */
    int nn, ln;
    SVec arena;
    U32Vec order;               /* live dup cells, discovery order */
} Canon;

/* §5 compaction: any signature longer than 80 chars becomes '#'+sha256, full
   width. Applied at EVERY node, so an inner node can never undercut the outer
   commitment by being long and un-hashed. */
static char* compact(char* sig){
    if (strlen(sig) <= 80) return sig;
    char hex[65]; sha256_str(sig,hex);
    char* out=(char*)malloc(67);
    out[0]='#'; memcpy(out+1,hex,65);
    free(sig);
    return out;
}
static char* sfmt(const char* fmt, ...){
    va_list ap; va_start(ap,fmt);
    int n=vsnprintf(NULL,0,fmt,ap); va_end(ap);
    char* s=(char*)malloc((size_t)n+1);
    va_start(ap,fmt); vsnprintf(s,(size_t)n+1,fmt,ap); va_end(ap);
    return s;
}

static uint32_t dup_label(Canon* c, uint32_t D);

/* explicit-stack preorder over the folded term (§5 phase 1 push orders) */
static void canon_phase1(Canon* c, Term root){
    U64Map seen; map_init(&seen,4096);
    /* wrappers first, outermost → innermost */
    for (size_t i=0;i<c->order.n;i++){
        uint32_t D=c->order.a[i];
        intern(&c->lid,&c->ln,(uint64_t)dup_label(c,D));
        intern(&c->nid,&c->nn,NK_DUP(D,0));
        intern(&c->nid,&c->nn,NK_DUP(D,1));
        /* then val's subtree (val before bod, per CHILDREN Dup:["val","bod"]) */
        TVec st={0}; tpush(&st,heap[D]);
        while (st.n){
            Term t=ccanon_chase(st.a[--st.n]);
            uint64_t nk=(uint64_t)CLRSUB(t);
            int* s=map_slot(&seen,nk);
            if (*s==1) continue; *s=1;
            switch (TAG(t)){
                case T_VAR: if (!is_free_var(t)) intern(&c->nid,&c->nn,NK_LAM(ADDR(t))); break;
                case T_ERA: break;
                case T_LAM: intern(&c->nid,&c->nn,NK_LAM(ADDR(t))); tpush(&st,heap[ADDR(t)]); break;
                case T_APP: tpush(&st,heap[ADDR(t)+1]); tpush(&st,heap[ADDR(t)]); break;
                case T_SUP: intern(&c->lid,&c->ln,(uint64_t)LAB(t));
                            tpush(&st,heap[ADDR(t)+1]); tpush(&st,heap[ADDR(t)]); break;
                case T_DP0: case T_DP1: /* a projection is a NAME in the folded term */
                            intern(&c->nid,&c->nn,NK_DUP(ADDR(t),TAG(t)==T_DP0?0:1)); break;
            }
        }
        free(st.a);
    }
    /* finally the root subtree (the innermost body) */
    TVec st={0}; tpush(&st,root);
    while (st.n){
        Term t=ccanon_chase(st.a[--st.n]);
        uint64_t nk=(uint64_t)CLRSUB(t);
        int* s=map_slot(&seen,nk);
        if (*s==1) continue; *s=1;
        switch (TAG(t)){
            case T_VAR: if (!is_free_var(t)) intern(&c->nid,&c->nn,NK_LAM(ADDR(t))); break;
            case T_ERA: break;
            case T_LAM: intern(&c->nid,&c->nn,NK_LAM(ADDR(t))); tpush(&st,heap[ADDR(t)]); break;
            case T_APP: tpush(&st,heap[ADDR(t)+1]); tpush(&st,heap[ADDR(t)]); break;
            case T_SUP: intern(&c->lid,&c->ln,(uint64_t)LAB(t));
                        tpush(&st,heap[ADDR(t)+1]); tpush(&st,heap[ADDR(t)]); break;
            case T_DP0: case T_DP1:
                        intern(&c->nid,&c->nn,NK_DUP(ADDR(t),TAG(t)==T_DP0?0:1)); break;
        }
    }
    free(st.a); map_free(&seen);
}

/* labels are on projections, so remember one projection per cell during discovery */
static U64Map g_dupLab; static int g_dupLab_init=0;
static uint32_t dup_label(Canon* c, uint32_t D){
    (void)c;
    int* v=map_slot(&g_dupLab,(uint64_t)D);
    return (uint32_t)(*v < 0 ? 0 : *v);
}

/* Phase 2 — memoized post-order signature over the folded term. */
static char* sig_of(Canon* c, Term t);

static char* sig_node(Canon* c, Term t){
    t=ccanon_chase(t);
    switch (TAG(t)){
        case T_ERA: return sfmt("E");
        case T_VAR: {
            const char* f=free_lookup(ADDR(t));
            if (f) return sfmt("Ffree:%s", f);
            return sfmt("N%d", intern(&c->nid,&c->nn,NK_LAM(ADDR(t))));
        }
        case T_DP0: case T_DP1:
            return sfmt("N%d", intern(&c->nid,&c->nn,NK_DUP(ADDR(t),TAG(t)==T_DP0?0:1)));
        case T_LAM: {
            char* b=sig_of(c,heap[ADDR(t)]);
            char* s=sfmt("L%d(%s)", intern(&c->nid,&c->nn,NK_LAM(ADDR(t))), b);
            return compact(s);
        }
        case T_APP: {
            char* f=sig_of(c,heap[ADDR(t)]); char* a=sig_of(c,heap[ADDR(t)+1]);
            return compact(sfmt("A(%s,%s)", f, a));
        }
        case T_SUP: {
            char* l=sig_of(c,heap[ADDR(t)]); char* r=sig_of(c,heap[ADDR(t)+1]);
            return compact(sfmt("S%d(%s,%s)", intern(&c->lid,&c->ln,(uint64_t)LAB(t)), l, r));
        }
    }
    return sfmt("?");
}
/* memoize on node identity — the digest is over the DAG, not its unfolding */
static char* sig_of(Canon* c, Term t){
    t=ccanon_chase(t);
    uint64_t nk=(uint64_t)CLRSUB(t);
    int* m=map_slot(&c->memo,nk);
    if (*m >= 0) return c->arena.s[*m];
    char* s=sig_node(c,t);
    *m=(int)sv_put(&c->arena,s);
    free(s);
    return c->arena.s[*m];
}

static char* canonical_signature(Term root){
    Canon c; memset(&c,0,sizeof(c));
    map_init(&c.nid,1024); map_init(&c.lid,256); map_init(&c.memo,4096);
    if (!g_dupLab_init){ map_init(&g_dupLab,256); g_dupLab_init=1; }
    else { map_free(&g_dupLab); map_init(&g_dupLab,256); }

    /* discovery also records each cell's label from the projection that found it */
    {
        U64Map seenNode; map_init(&seenNode,1024);
        TVec st={0}; tpush(&st,root);
        while (st.n){
            Term t=ccanon_chase(st.a[--st.n]);
            uint64_t nk=(uint64_t)CLRSUB(t);
            int* seen=map_slot(&seenNode,nk);
            if (*seen==1) continue; *seen=1;
            switch (TAG(t)){
                case T_LAM: tpush(&st,heap[ADDR(t)]); break;
                case T_APP: case T_SUP:
                    tpush(&st,heap[ADDR(t)+1]); tpush(&st,heap[ADDR(t)]); break;
                case T_DP0: case T_DP1: {
                    uint32_t D=ADDR(t);
                    int* lv=map_slot(&g_dupLab,(uint64_t)D);
                    if (*lv < 0){ *lv=(int)LAB(t); vec_push(&c.order,D); tpush(&st,heap[D]); }
                    break;
                }
                default: break;
            }
        }
        free(st.a); map_free(&seenNode);
    }

    canon_phase1(&c, root);

    /* fold: innermost body is the root, wrappers applied first-discovered-outermost */
    char* acc = strdup(sig_of(&c, root));
    for (size_t i=c.order.n; i-- > 0; ){
        uint32_t D=c.order.a[i];
        char* val=sig_of(&c,heap[D]);
        char* s=sfmt("D%d[%d,%d](%s,%s)",
            intern(&c.lid,&c.ln,(uint64_t)dup_label(&c,D)),
            intern(&c.nid,&c.nn,NK_DUP(D,0)),
            intern(&c.nid,&c.nn,NK_DUP(D,1)),
            val, acc);
        free(acc);
        acc=compact(s);
    }
    char* out=strdup(acc);
    free(acc);
    map_free(&c.nid); map_free(&c.lid); map_free(&c.memo);
    free(c.order.a); sv_free(&c.arena);
    return out;
}

int main(int argc, char** argv){
    heap=(Term*)calloc(HEAPCAP,sizeof(Term));
    if (!heap){ fprintf(stderr,"FATAL: heap alloc\n"); return 2; }
    int do_nf = (argc>1 && !strcmp(argv[1],"--nf"));

    char line[65536];
    while (fgets(line,sizeof(line),stdin)){
        size_t L=strlen(line);
        while (L && (line[L-1]=='\n'||line[L-1]=='\r')) line[--L]=0;
        if (!L) continue;
        reset_state();
        P=line; Term t=parse_term(); ws();
        if (do_nf) t=normal(t);
        char* sig=canonical_signature(t);
        char hex[65]; sha256_str(sig,hex);
        printf("%s\t%s\n", hex, sig);
        free(sig);
    }
    return 0;
}
