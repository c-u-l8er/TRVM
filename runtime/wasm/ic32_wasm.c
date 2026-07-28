// ic32_wasm.c -- freestanding wasm32 build of the IC32 interaction-calculus runtime.
//
// Same reduction core as ic32.c (validated against ic_float.py / ic_ref.py), but
// with no libc: a static heap in linear memory, tiny string helpers, and a small
// exported ABI so a JS host (Node here, browser later) can drive it.
//
// ABI (all exported):
//   input_ptr()  -> offset of the input byte buffer (write the UTF-8 term there)
//   output_ptr() -> offset of the output byte buffer (read the result from there)
//   run(in_len)  -> parses+normalizes+stringifies; returns output length in bytes
//   last_interactions() -> interaction count of the last run
//
// build (see build note at bottom):
//   clang --target=wasm32 -O2 -nostdlib -ffreestanding -Wl,--no-entry \
//     -Wl,--export-dynamic -Wl,-z,stack-size=16777216 \
//     -Wl,--initial-memory=268435456 -o ic32.wasm ic32_wasm.c

typedef unsigned long long u64;   // 64-bit on wasm32
typedef unsigned int       u32;
typedef unsigned char      u8;

#define EXPORT(n) __attribute__((export_name(n)))

#define TAG(t)   ((int)((t) & 0xF))
#define SUBF     (1ULL<<31)
#define LAB(t)   ((u32)(((t) >> 4) & 0x7FFFFFF))
#define ADDR(t)  ((u32)((t) >> 32))
#define ISSUB(t) ((t) & SUBF)
#define SETSUB(t) ((t) | SUBF)
#define CLRSUB(t) ((t) & ~SUBF)
#define MK(tag,lab,addr) ( ((u64)((tag)&0xF)) | (((u64)((lab)&0x7FFFFFF))<<4) | (((u64)(addr))<<32) )

enum { T_VAR=0, T_LAM=1, T_APP=2, T_ERA=3, T_SUP=4, T_DP0=5, T_DP1=6 };

// ----------------------------------------------------------- static memory
#define HEAPCAP (1u<<24)          // 16M slots * 8B = 128MB (matches ic32.c)
static u64 heap[HEAPCAP];
static u32 hp = 1;
static long interactions = 0;
static long STEPCAP = 50000000;
static int  aborted = 0;

static u8 in_buf[1u<<20];         // 1MB input
static u8 out_buf[1u<<24];        // 16MB output (deep readback at 2^21 depth ~ 8MB)
static u32 opos = 0;

// Explicit work stack shared by normal() and show() (never concurrent).
// normal() reinterprets as u32[WSTKCAP*2]; show() uses as u64[WSTKCAP].
#define WSTKCAP (1u<<22)           // 4M u64 entries = 32MB
static u64 wstk[WSTKCAP];

static u32 alloc_n(int n){
    u32 a = hp; hp += n;
    if (hp >= HEAPCAP){ aborted = 1; return 1; }
    return a;
}
static inline void step(void){ if (++interactions > STEPCAP) aborted = 1; }

// ----------------------------------------------------------- reduction
static u64 whnf(u64 t);

static u64 fire(u32 D, u32 L, int k){
    step(); if (aborted) return MK(T_ERA,0,0);
    u64 v = whnf(heap[D]);
    int vt = TAG(v);
    u64 h0, h1;
    if (vt == T_SUP){
        u32 S = ADDR(v); u32 vl = LAB(v);
        u64 a = heap[S], b = heap[S+1];
        if (vl == L){ h0 = a; h1 = b; }
        else {
            u32 Da = alloc_n(1); heap[Da] = a;
            u32 Db = alloc_n(1); heap[Db] = b;
            u32 S0 = alloc_n(2); heap[S0] = MK(T_DP0,L,Da); heap[S0+1] = MK(T_DP0,L,Db);
            u32 S1 = alloc_n(2); heap[S1] = MK(T_DP1,L,Da); heap[S1+1] = MK(T_DP1,L,Db);
            h0 = MK(T_SUP,vl,S0); h1 = MK(T_SUP,vl,S1);
        }
    } else if (vt == T_LAM){
        u32 Lv = ADDR(v);
        u32 Lx0 = alloc_n(1), Lx1 = alloc_n(1);
        u32 Df  = alloc_n(1); heap[Df] = heap[Lv];
        heap[Lx0] = MK(T_DP0,L,Df);
        heap[Lx1] = MK(T_DP1,L,Df);
        u32 Ss = alloc_n(2);
        heap[Ss] = MK(T_VAR,0,Lx0); heap[Ss+1] = MK(T_VAR,0,Lx1);
        heap[Lv] = SETSUB(MK(T_SUP,L,Ss));
        h0 = MK(T_LAM,0,Lx0); h1 = MK(T_LAM,0,Lx1);
    } else if (vt == T_ERA){
        h0 = MK(T_ERA,0,0); h1 = MK(T_ERA,0,0);
    } else if (vt == T_APP){
        u32 A = ADDR(v); u64 f = heap[A], a = heap[A+1];
        u32 Df = alloc_n(1); heap[Df] = f;
        u32 Dx = alloc_n(1); heap[Dx] = a;
        u32 A0 = alloc_n(2); heap[A0] = MK(T_DP0,L,Df); heap[A0+1] = MK(T_DP0,L,Dx);
        u32 A1 = alloc_n(2); heap[A1] = MK(T_DP1,L,Df); heap[A1+1] = MK(T_DP1,L,Dx);
        h0 = MK(T_APP,0,A0); h1 = MK(T_APP,0,A1);
    } else {
        h0 = v; h1 = v;
    }
    if (k == 0){ heap[D] = SETSUB(h1); return h0; }
    else       { heap[D] = SETSUB(h0); return h1; }
}

static u64 app_sup(u64 sup, u64 arg){
    step(); if (aborted) return MK(T_ERA,0,0);
    u32 S = ADDR(sup); u32 L = LAB(sup);
    u64 a = heap[S], b = heap[S+1];
    u32 Dc = alloc_n(1); heap[Dc] = arg;
    u32 Aa = alloc_n(2); heap[Aa] = a; heap[Aa+1] = MK(T_DP0,L,Dc);
    u32 Ab = alloc_n(2); heap[Ab] = b; heap[Ab+1] = MK(T_DP1,L,Dc);
    u32 Sn = alloc_n(2); heap[Sn] = MK(T_APP,0,Aa); heap[Sn+1] = MK(T_APP,0,Ab);
    return MK(T_SUP,L,Sn);
}

static u64 whnf(u64 t){
    for (;;){
        if (aborted) return MK(T_ERA,0,0);
        int tag = TAG(t);
        if (tag == T_VAR){
            u64 w = heap[ADDR(t)];
            if (ISSUB(w)){ t = CLRSUB(w); continue; }
            return t;
        }
        if (tag == T_DP0 || tag == T_DP1){
            u32 D = ADDR(t);
            u64 w = heap[D];
            if (ISSUB(w)){ t = CLRSUB(w); continue; }
            t = fire(D, LAB(t), tag == T_DP0 ? 0 : 1);
            continue;
        }
        if (tag == T_APP){
            u32 A = ADDR(t);
            u64 f = whnf(heap[A]);
            int ft = TAG(f);
            if (ft == T_LAM){
                step(); if (aborted) return MK(T_ERA,0,0);
                u32 Lv = ADDR(f);
                u64 arg = heap[A+1];
                u64 bod = heap[Lv];
                heap[Lv] = SETSUB(arg);
                t = bod; continue;
            }
            if (ft == T_SUP){ t = app_sup(f, heap[A+1]); continue; }
            if (ft == T_ERA){ step(); t = MK(T_ERA,0,0); continue; }
            heap[A] = f;
            return MK(T_APP,0,A);
        }
        return t;
    }
}

// iterative full normaliser: explicit work stack of heap-slot indices.
// Handles arbitrarily deep results without growing the WASM call stack.
static u64 normal(u64 t){
    if (aborted) return t;
    t = whnf(t);
    u32 *stk = (u32*)wstk;            // reinterpret as u32[], capacity WSTKCAP*2
    u32 ssp = 0;
    int tag = TAG(t);
    if (tag == T_LAM){ stk[ssp++] = ADDR(t); }
    else if (tag == T_APP){ u32 A = ADDR(t); stk[ssp++] = A+1; stk[ssp++] = A; }
    else if (tag == T_SUP){ u32 S = ADDR(t); stk[ssp++] = S+1; stk[ssp++] = S; }
    while (ssp > 0){
        if (aborted) break;
        u32 idx = stk[--ssp];
        u64 v = whnf(heap[idx]); heap[idx] = v;
        int vt = TAG(v);
        if (vt == T_LAM){ stk[ssp++] = ADDR(v); }
        else if (vt == T_APP){ u32 A = ADDR(v); stk[ssp++] = A+1; stk[ssp++] = A; }
        else if (vt == T_SUP){ u32 S = ADDR(v); stk[ssp++] = S+1; stk[ssp++] = S; }
    }
    return t;
}

// ----------------------------------------------------------- tiny libc bits
static int seq(const char* a, const char* b){
    while (*a && *b){ if (*a != *b) return 0; a++; b++; }
    return *a == *b;
}
static void scpy(char* d, const char* s, int n){
    int i = 0; for (; i < n-1 && s[i]; i++) d[i] = s[i]; d[i] = 0;
}

// ----------------------------------------------------------- naming
#define MAXNAMES 8192
static u32  free_loc[MAXNAMES]; static char free_nm[MAXNAMES][40]; static int n_free=0;
static u32  bnd_loc[MAXNAMES];  static char bnd_nm[MAXNAMES][8];   static int n_bnd=0;
static int  name_ctr=0;

static const char* free_lookup(u32 loc){
    for (int i=0;i<n_free;i++) if (free_loc[i]==loc) return free_nm[i];
    return 0;
}
static u32 free_intern(const char* nm){
    for (int i=0;i<n_free;i++) if (seq(free_nm[i],nm)) return free_loc[i];
    u32 L = alloc_n(1); heap[L] = MK(T_ERA,0,0);
    free_loc[n_free]=L; scpy(free_nm[n_free],nm,40); n_free++;
    return L;
}
static const char* bnd_name(u32 loc){
    for (int i=0;i<n_bnd;i++) if (bnd_loc[i]==loc) return bnd_nm[i];
    char* s = bnd_nm[n_bnd]; int i=name_ctr++;
    if (i<26){ s[0]='a'+i; s[1]=0; }
    else { s[0]='v'; int v=i, p=1; char tmp[6]; int tp=0; if(!v)tmp[tp++]='0'; while(v){tmp[tp++]='0'+v%10; v/=10;} while(tp&&p<7) s[p++]=tmp[--tp]; s[p]=0; }
    bnd_loc[n_bnd]=loc; n_bnd++;
    return s;
}

// ----------------------------------------------------------- parser
typedef struct { char nm[40]; u64 t; } Bind;
static Bind scope[4096]; static int sp=0;
static const char* P;

static void ws(void){ while (*P==' '||*P=='\t'||*P=='\n'||*P=='\r') P++; }
static int  is_lambda(void){ return (*P=='\\') || ((u8)P[0]==0xCE && (u8)P[1]==0xBB); }
static void eat_lambda(void){ if (*P=='\\') P++; else P+=2; }
static void expect(char c){ ws(); if (*P==c) P++; else aborted=1; }
static void rdname(char* out){
    ws(); int i=0;
    while ((*P>='a'&&*P<='z')||(*P>='A'&&*P<='Z')||(*P>='0'&&*P<='9')||*P=='_'){ if(i<39) out[i++]=*P; P++; }
    out[i]=0; if (i==0) aborted=1;
}
static u32 rduint(void){ ws(); u32 v=0; while(*P>='0'&&*P<='9'){v=v*10+(*P-'0');P++;} return v; }

static u64 parse_term(void){
    if (aborted) return MK(T_ERA,0,0);
    ws();
    if (is_lambda()){
        eat_lambda(); char nm[40]; rdname(nm); expect('.');
        u32 L = alloc_n(1);
        scpy(scope[sp].nm,nm,40); scope[sp].t = MK(T_VAR,0,L); sp++;
        u64 bod = parse_term(); sp--;
        heap[L] = bod;
        return MK(T_LAM,0,L);
    }
    char c = *P;
    if (c=='*'){ P++; return MK(T_ERA,0,0); }
    if (c=='('){
        P++; u64 f = parse_term(); u64 a = parse_term(); expect(')');
        u32 A = alloc_n(2); heap[A]=f; heap[A+1]=a;
        return MK(T_APP,0,A);
    }
    if (c=='&'){
        P++; u32 lab = rduint(); expect('{');
        u64 l = parse_term(); expect(','); u64 r = parse_term(); expect('}');
        u32 S = alloc_n(2); heap[S]=l; heap[S+1]=r;
        return MK(T_SUP,lab,S);
    }
    if (c=='{'){
        P++; u64 l = parse_term(); expect(','); u64 r = parse_term(); expect('}');
        u32 S = alloc_n(2); heap[S]=l; heap[S+1]=r;
        return MK(T_SUP,0,S);
    }
    if (c=='!'){
        P++; u32 lab=0; ws();
        if (*P=='&'){ P++; lab=rduint(); }
        expect('{'); char a[40],b[40]; rdname(a); expect(','); rdname(b); expect('}'); expect('=');
        u32 D = alloc_n(1);
        u64 val = parse_term();
        heap[D] = val;
        expect(';');
        scpy(scope[sp].nm,a,40); scope[sp].t = MK(T_DP0,lab,D); sp++;
        scpy(scope[sp].nm,b,40); scope[sp].t = MK(T_DP1,lab,D); sp++;
        u64 bod = parse_term(); sp-=2;
        return bod;
    }
    char nm[40]; rdname(nm);
    for (int i=sp-1;i>=0;i--) if (seq(scope[i].nm,nm)) return scope[i].t;
    return MK(T_VAR,0,free_intern(nm));
}

// ----------------------------------------------------------- stringify -> out_buf
static void emit(u8 c){ if (opos < sizeof(out_buf)-1) out_buf[opos++] = c; }
static void emits(const char* s){ while (*s) emit((u8)*s++); }
static void emit_lambda(void){ emit(0xCE); emit(0xBB); }
static void emit_uint(u32 v){ char t[12]; int n=0; if(!v){emit('0');return;} while(v){t[n++]='0'+v%10; v/=10;} while(n) emit(t[--n]); }

// iterative readback: explicit work stack so arbitrarily deep normal forms
// read back without growing the WASM call stack. Uses wstk[] as u64[].
// Encoding: bit 63 clear = term to render; bit 63 set = emit byte in low 8 bits.
#define SHOWLIT(c) (0x8000000000000000ULL | (u64)(u8)(c))
#define ISLIT(x)   ((x) & 0x8000000000000000ULL)

static void show(u64 root){
    u32 ssp = 0;
    wstk[ssp++] = root;
    while (ssp > 0){
        u64 item = wstk[--ssp];
        if (ISLIT(item)){ emit((u8)(item & 0xFF)); continue; }
        int tag = TAG(item);
        if (tag == T_VAR){
            u32 L = ADDR(item); const char* f = free_lookup(L);
            if (f) emits(f); else emits(bnd_name(L));
        } else if (tag == T_ERA){
            emit('*');
        } else if (tag == T_LAM){
            u32 L = ADDR(item);
            emit_lambda(); emits(bnd_name(L)); emit('.');
            wstk[ssp++] = heap[L];
        } else if (tag == T_APP){
            u32 A = ADDR(item);
            emit('(');
            wstk[ssp++] = SHOWLIT(')');
            wstk[ssp++] = heap[A+1];
            wstk[ssp++] = SHOWLIT(' ');
            wstk[ssp++] = heap[A];
        } else if (tag == T_SUP){
            u32 S = ADDR(item);
            emit('&'); emit_uint(LAB(item)); emit('{');
            wstk[ssp++] = SHOWLIT('}');
            wstk[ssp++] = heap[S+1];
            wstk[ssp++] = SHOWLIT(',');
            wstk[ssp++] = heap[S];
        } else {
            emit('?');
        }
    }
}

// ----------------------------------------------------------- exported ABI
EXPORT("input_ptr")  u8*  input_ptr(void){ return in_buf; }
EXPORT("output_ptr") u8*  output_ptr(void){ return out_buf; }
EXPORT("last_interactions") long last_interactions(void){ return interactions; }

EXPORT("run") int run(int in_len){
    hp = 1; interactions = 0; aborted = 0; opos = 0;
    sp = 0; n_free = 0; n_bnd = 0; name_ctr = 0;
    if (in_len < 0 || in_len >= (int)sizeof(in_buf)) return -1;
    in_buf[in_len] = 0;
    P = (const char*)in_buf;
    u64 t = parse_term();
    u64 nf = normal(t);
    if (aborted){ opos = 0; emits("ABORTED"); return opos; }
    show(nf);
    return (int)opos;
}
