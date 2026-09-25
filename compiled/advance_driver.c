/* advance_driver.c -- B6's native driver: advance ONE world N dependent steps under a control script.
 *
 *     TRVM_ST="<state words>" TRVM_SCRIPT=script.txt TRVM_MODE=0|1|2 advance_driver STEP.so
 *
 * The SAME protocol as the Bend driver (`advance.py` BEND_TAIL), so both processes do the same job on the same
 * bytes: the initial state as space-separated decimal words in an environment variable, the control script as a
 * text file of one line per epoch (space-separated words; a line "0" when the world takes no control), and the
 * result as decimal words on stdout. Modes: 0 prints the final state, 1 prints every state (one line each),
 * 2 only decodes the script and prints a checksum of every word (sum mod 1000000007), so decoding can be
 * reported apart from stepping. Both drivers compute the same checksum.
 *
 * The step is the ADMITTED object, loaded as built (`dlopen` of the content-addressed `.so` the emitter
 * produced; this file never compiles a step of its own). Each step's input is the state the previous step
 * wrote -- `st' = step(st, ctl[k])` and nothing else -- so step k cannot start before step k-1 has finished.
 *
 * stderr gets one JSON line: this process's own monotonic timings of its phases, in nanoseconds. It is reported
 * beside the caller's rusage, never instead of it: a phase timer says where the wall time went, not what the
 * process cost the machine. */
#define _GNU_SOURCE
#include <dlfcn.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

typedef int64_t i64;
typedef void (*step_fn)(const i64 *, const i64 *, i64 *);
typedef i64 (*width_fn)(void);

static i64 now_ns(void) {
  struct timespec t;
  clock_gettime(CLOCK_MONOTONIC, &t);
  return (i64)t.tv_sec * 1000000000LL + t.tv_nsec;
}

static void die(const char *m) {
  fprintf(stderr, "advance_driver: %s\n", m);
  exit(2);
}

static char *slurp(const char *path, size_t *len) {
  FILE *f = fopen(path, "rb");
  if (!f) die("cannot open the script");
  fseek(f, 0, SEEK_END);
  long n = ftell(f);
  fseek(f, 0, SEEK_SET);
  char *b = malloc((size_t)n + 1);
  if (!b || fread(b, 1, (size_t)n, f) != (size_t)n) die("cannot read the script");
  b[n] = 0;
  fclose(f);
  *len = (size_t)n;
  return b;
}

static void print_state(const i64 *st, i64 sw, FILE *o) {
  for (i64 i = 0; i < sw; i++) fprintf(o, i ? " %lld" : "%lld", (long long)st[i]);
  fputc('\n', o);
}

int main(int argc, char **argv) {
  if (argc != 2) die("usage: TRVM_ST=.. TRVM_SCRIPT=.. TRVM_MODE=0|1|2 advance_driver STEP.so");
  const char *st_txt = getenv("TRVM_ST"), *path = getenv("TRVM_SCRIPT"), *mode_s = getenv("TRVM_MODE");
  if (!st_txt || !path || !mode_s) die("TRVM_ST, TRVM_SCRIPT and TRVM_MODE are required");
  int mode = atoi(mode_s);
  i64 t0 = now_ns();
  void *h = dlopen(argv[1], RTLD_NOW | RTLD_LOCAL);
  if (!h) die(dlerror());
  step_fn step = (step_fn)dlsym(h, "step_v6");
  width_fn sw_of = (width_fn)dlsym(h, "state_width");
  width_fn cw_of = (width_fn)dlsym(h, "control_width");
  if (!step || !sw_of || !cw_of) die("the object does not export step_v6/state_width/control_width");
  i64 sw = sw_of(), cw = cw_of();
  i64 *st = calloc((size_t)(sw ? sw : 1), sizeof(i64)), *nx = calloc((size_t)(sw ? sw : 1), sizeof(i64));
  const char *p = st_txt;
  for (i64 i = 0; i < sw; i++) {
    char *e;
    st[i] = strtoll(p, &e, 10);
    if (e == p) die("the state has fewer words than the object's state_width");
    p = e;
  }
  i64 t1 = now_ns();
  size_t len;
  char *txt = slurp(path, &len);
  i64 n = 1;
  for (size_t i = 0; i < len; i++) n += txt[i] == '\n';
  i64 per = cw ? cw : 1;                          /* a world without control carries the placeholder word "0" */
  i64 *ctl = malloc(sizeof(i64) * (size_t)(n * per));
  if (!ctl) die("out of memory");
  const char *q = txt;
  uint64_t sum = 0;
  for (i64 k = 0; k < n; k++) {
    for (i64 j = 0; j < per; j++) {
      char *e;
      i64 v = strtoll(q, &e, 10);
      if (e == q) die("a script line has fewer words than the control width");
      ctl[k * per + j] = v;
      sum = (sum + (uint64_t)v) % 1000000007ULL;
      q = e;
    }
  }
  i64 t2 = now_ns();
  if (mode == 2) {
    printf("%llu\n", (unsigned long long)sum);
  } else {
    char *obuf = malloc(1 << 20);
    setvbuf(stdout, obuf, _IOFBF, 1 << 20);
    for (i64 k = 0; k < n; k++) {
      step(st, ctl + k * per, nx);
      i64 *tmp = st; st = nx; nx = tmp;          /* the next step reads only what this one wrote */
      if (mode == 1) print_state(st, sw, stdout);
    }
    if (mode == 0) print_state(st, sw, stdout);
  }
  i64 t3 = now_ns();
  fflush(stdout);
  fprintf(stderr, "{\"load_ns\": %lld, \"decode_ns\": %lld, \"steps_ns\": %lld, \"n\": %lld, \"sw\": %lld, \"cw\": %lld}\n",
          (long long)(t1 - t0), (long long)(t2 - t1), (long long)(t3 - t2), (long long)n, (long long)sw,
          (long long)cw);
  return 0;
}
