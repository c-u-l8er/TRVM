/* batch_price.c -- the per-step price of what a K-step `trvm.reduce` would do inside the executor, each operation
 * timed alone over a real trajectory, in-process, no FFI, no Python (driven by batch_price.py).
 *
 *     batch_price STEP.so PRINT.so INPUT.bin REPS  ->  one JSON object on stdout
 *
 * INPUT.bin (int64 little-endian unless noted): width cw nfields ndesc nctrl norbs nsteps text_bytes,
 * desc[ndesc], widths[max(1,nctrl)], a0[width], ctls[nsteps*cw], text_off[nsteps+1], then text_bytes of the
 * per-epoch control TEXTS (the calculus rendering `trvm.reduce` carries today, printer.render_control's bytes).
 *
 * Each operation is timed as a loop over the n states of the world's own trajectory (computed first by the step),
 * REPS times; the median per-operation cost is reported in wall ns (CLOCK_MONOTONIC) and thread-CPU ns
 * (CLOCK_THREAD_CPUTIME_ID). Operations:
 *   step            st' = step_v6(st, ctl[k]), dependent, the loop B6 timed
 *   sha256_raw      sha256 of the state vector's bytes (8 * width), OpenSSL EVP one-shot, digest fetched once
 *   chain_raw       h = sha256(h || state bytes), one EVP context re-initialised per state -- a hash chain
 *   blake3_raw      BLAKE3 of the state vector's bytes (libblake3)
 *   render          trvm_print_state: the canonical normal-form text the receipt digests today
 *   render_sha256   render + sha256 of the text (the per-state cost of committing to CANONICAL intermediates)
 *   read_control    trvm_read_control: one epoch's control text -> control vector (the input decode per epoch)
 *   read_state      trvm_read_state: canonical text -> vector (the input decode, once per batch)
 *   loop_vec_chain  step + chain_raw, controls already vectors         (a batch that chains raw states)
 *   loop_txt_chain  read_control + step + chain_raw                    (the same, controls carried as text)
 *   loop_txt_canon  read_control + step + render + sha256 chain of it  (a batch committing canonical texts)
 * and a checksum of the final state, which the driver compares with the C step run from Python.
 */
#define _GNU_SOURCE
#include <blake3.h>
#include <dlfcn.h>
#include <openssl/evp.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

typedef int64_t i64;
typedef void (*step_fn)(const i64 *, const i64 *, i64 *);
typedef i64 (*print_fn)(const i64 *, i64, const i64 *, char *, i64);
typedef i64 (*read_state_fn)(const i64 *, i64, const char *, i64, i64 *, i64);
typedef i64 (*read_ctl_fn)(const i64 *, i64, i64, const char *, i64, i64 *, i64);

static void die(const char *m) { fprintf(stderr, "batch_price: %s\n", m); exit(2); }
static i64 now(clockid_t c) { struct timespec t; clock_gettime(c, &t); return (i64)t.tv_sec * 1000000000LL + t.tv_nsec; }
static int cmp(const void *a, const void *b) { i64 x = *(const i64 *)a, y = *(const i64 *)b; return x < y ? -1 : x > y; }

static i64 n, w, cw, nfields, nctrl, norbs, reps;
static i64 *desc, *widths, *a0, *ctls, *toff, *traj;
static char *texts, **rtxt;
static i64 *rlen;
static step_fn step;
static print_fn pst;
static read_state_fn rst;
static read_ctl_fn rct;
static const EVP_MD *md;
static EVP_MD_CTX *mctx;
static volatile i64 sink;
static char *buf;
static i64 cap = 1 << 16;

static void sha_raw(const void *p, size_t len, unsigned char *out) { unsigned int ol; EVP_Digest(p, len, out, &ol, md, NULL); }
static void chain(unsigned char *h, const void *p, size_t len)
{
  unsigned int ol;
  EVP_DigestInit_ex(mctx, md, NULL);
  EVP_DigestUpdate(mctx, h, 32);
  EVP_DigestUpdate(mctx, p, len);
  EVP_DigestFinal_ex(mctx, h, &ol);
}

enum { OP_STEP, OP_SHA, OP_CHAIN, OP_B3, OP_RENDER, OP_RSHA, OP_RCTL, OP_RST, OP_LVC, OP_LTC, OP_LTCANON, NOPS };
static const char *names[NOPS] = { "step", "sha256_raw", "chain_raw", "blake3_raw", "render", "render_sha256",
                                   "read_control", "read_state", "loop_vec_chain", "loop_txt_chain", "loop_txt_canon" };

static void run(int op)
{
  i64 *a = malloc(8 * (w ? w : 1)), *b = malloc(8 * (w ? w : 1)), *c = malloc(8 * (cw ? cw : 1)), *t;
  unsigned char h[32] = { 0 }, d[32];
  blake3_hasher bh;
  memcpy(a, a0, 8 * w);
  for (i64 k = 0; k < n; k++) {
    const i64 *s = traj + k * w;
    switch (op) {
    case OP_STEP: step(a, ctls + k * cw, b); t = a; a = b; b = t; break;
    case OP_SHA: sha_raw(s, 8 * w, d); sink += d[0]; break;
    case OP_CHAIN: chain(h, s, 8 * w); break;
    case OP_B3: blake3_hasher_init(&bh); blake3_hasher_update(&bh, s, 8 * w); blake3_hasher_finalize(&bh, d, 32); sink += d[0]; break;
    case OP_RENDER: sink += pst(desc, nfields, s, buf, cap); break;
    case OP_RSHA: { i64 m = pst(desc, nfields, s, buf, cap); chain(h, buf, m); } break;
    case OP_RCTL: if (rct(widths, nctrl, norbs, texts + toff[k], toff[k + 1] - toff[k], c, cw)) die("read_control refused"); sink += cw ? c[0] : 0; break;
    case OP_RST: if (rst(desc, nfields, rtxt[k], rlen[k], c == NULL ? NULL : b, w)) die("read_state refused"); sink += b[0]; break;
    case OP_LVC: step(a, ctls + k * cw, b); t = a; a = b; b = t; chain(h, a, 8 * w); break;
    case OP_LTC:
      if (rct(widths, nctrl, norbs, texts + toff[k], toff[k + 1] - toff[k], c, cw)) die("read_control refused");
      step(a, c, b); t = a; a = b; b = t; chain(h, a, 8 * w); break;
    case OP_LTCANON: {
      if (rct(widths, nctrl, norbs, texts + toff[k], toff[k + 1] - toff[k], c, cw)) die("read_control refused");
      step(a, c, b); t = a; a = b; b = t;
      i64 m = pst(desc, nfields, a, buf, cap); chain(h, buf, m); } break;
    }
  }
  sink += h[0] + a[0];
  free(a); free(b); free(c);
}

int main(int argc, char **argv)
{
  if (argc != 5) die("usage: batch_price STEP.so PRINT.so INPUT.bin REPS");
  void *so = dlopen(argv[1], RTLD_NOW), *pso = dlopen(argv[2], RTLD_NOW);
  if (!so || !pso) die(dlerror());
  step = (step_fn)dlsym(so, "step_v6");
  pst = (print_fn)dlsym(pso, "trvm_print_state");
  rst = (read_state_fn)dlsym(pso, "trvm_read_state");
  rct = (read_ctl_fn)dlsym(pso, "trvm_read_control");
  if (!step || !pst || !rst || !rct) die("missing symbol");
  reps = atoll(argv[4]);
  FILE *f = fopen(argv[3], "rb");
  if (!f) die("input");
  i64 hd[8];
  if (fread(hd, 8, 8, f) != 8) die("header");
  w = hd[0]; cw = hd[1]; nfields = hd[2]; i64 ndesc = hd[3]; nctrl = hd[4]; norbs = hd[5]; n = hd[6]; i64 tb = hd[7];
  desc = malloc(8 * ndesc); widths = malloc(8 * (nctrl ? nctrl : 1)); a0 = malloc(8 * w);
  ctls = malloc(8 * (n * cw ? n * cw : 1)); toff = malloc(8 * (n + 1)); texts = malloc(tb ? tb : 1);
  if (fread(desc, 8, ndesc, f) != (size_t)ndesc || fread(widths, 8, nctrl ? nctrl : 1, f) != (size_t)(nctrl ? nctrl : 1) ||
      fread(a0, 8, w, f) != (size_t)w || fread(ctls, 8, n * cw, f) != (size_t)(n * cw) ||
      fread(toff, 8, n + 1, f) != (size_t)(n + 1) || fread(texts, 1, tb, f) != (size_t)tb) die("body");
  fclose(f);
  md = EVP_MD_fetch(NULL, "SHA256", NULL);
  mctx = EVP_MD_CTX_new();
  buf = malloc(cap);
  /* the trajectory, by the step itself; every state kept (the per-state ops read it), and each state's text */
  traj = malloc(8 * w * n);
  rtxt = malloc(sizeof(char *) * n); rlen = malloc(8 * n);
  i64 *a = malloc(8 * w);
  memcpy(a, a0, 8 * w);
  i64 text_bytes = 0;
  for (i64 k = 0; k < n; k++) {
    step(a, ctls + k * cw, traj + k * w);
    memcpy(a, traj + k * w, 8 * w);
    i64 m = pst(desc, nfields, a, buf, cap);
    if (m < 0 || m > cap) die("render refused or too large");
    rtxt[k] = malloc(m); memcpy(rtxt[k], buf, m); rlen[k] = m; text_bytes += m;
  }
  unsigned long long cs = 1469598103934665603ULL;             /* FNV-1a over the final state's words */
  for (i64 i = 0; i < w; i++) { cs ^= (unsigned long long)a[i]; cs *= 1099511628211ULL; }
  printf("{\"n\": %lld, \"width\": %lld, \"control_width\": %lld, \"final_fnv\": \"%016llx\", "
         "\"state_bytes_raw\": %lld, \"render_bytes_mean\": %.1f, \"control_text_bytes_mean\": %.1f, \"ops\": {",
         (long long)n, (long long)w, (long long)cw, cs, (long long)(8 * w), (double)text_bytes / n, (double)toff[n] / n);
  i64 *wall = malloc(8 * reps), *cpu = malloc(8 * reps);
  for (int op = 0; op < NOPS; op++) {
    run(op);                                                         /* warm */
    for (i64 r = 0; r < reps; r++) {
      i64 w0 = now(CLOCK_MONOTONIC), c0 = now(CLOCK_THREAD_CPUTIME_ID);
      run(op);
      cpu[r] = now(CLOCK_THREAD_CPUTIME_ID) - c0; wall[r] = now(CLOCK_MONOTONIC) - w0;
    }
    qsort(wall, reps, 8, cmp); qsort(cpu, reps, 8, cmp);
    printf("%s\"%s\": {\"wall_ns\": %.2f, \"cpu_ns\": %.2f, \"wall_ns_min\": %.2f}", op ? ", " : "", names[op],
           (double)wall[reps / 2] / n, (double)cpu[reps / 2] / n, (double)wall[0] / n);
  }
  printf("}, \"sink\": %lld}\n", (long long)(sink & 1));
  return 0;
}
