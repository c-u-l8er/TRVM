/* advance_launch.c -- run ONE command and report what it cost the machine: wall, user, system, max RSS.
 *
 *     advance_launch REPORT.json CMD ARGS...
 *
 * It exists for the max RSS. Linux keeps a process's RSS high-water mark across exec, so a child forked from the
 * ~30 MB Python harness reports at least ~30 MB whatever it went on to do (measured: every backend read 31.5 MB).
 * A child forked from this ~1 MB launcher reports its own peak. Wall is CLOCK_MONOTONIC from just before fork to
 * just after wait4, so the Python side's spawn cost is not in it either. */
#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <sys/resource.h>
#include <sys/wait.h>
#include <time.h>
#include <unistd.h>

static double now_s(void) {
  struct timespec t;
  clock_gettime(CLOCK_MONOTONIC, &t);
  return (double)t.tv_sec + (double)t.tv_nsec * 1e-9;
}

int main(int argc, char **argv) {
  if (argc < 3) {
    fprintf(stderr, "usage: advance_launch REPORT.json CMD ARGS...\n");
    return 2;
  }
  double t0 = now_s();
  pid_t pid = fork();
  if (pid < 0) return 2;
  if (pid == 0) {
    execvp(argv[2], argv + 2);
    _exit(127);
  }
  int status = 0;
  struct rusage ru;
  if (wait4(pid, &status, 0, &ru) != pid) return 2;
  double t1 = now_s();
  FILE *f = fopen(argv[1], "w");
  if (!f) return 2;
  fprintf(f, "{\"wall_s\": %.9f, \"cpu_user_s\": %.6f, \"cpu_sys_s\": %.6f, \"maxrss_kb\": %ld, "
             "\"exit\": %d, \"signal\": %d, \"minflt\": %ld, \"majflt\": %ld, \"nvcsw\": %ld, \"nivcsw\": %ld}\n",
          t1 - t0, ru.ru_utime.tv_sec + ru.ru_utime.tv_usec * 1e-6, ru.ru_stime.tv_sec + ru.ru_stime.tv_usec * 1e-6,
          ru.ru_maxrss, WIFEXITED(status) ? WEXITSTATUS(status) : -1, WIFSIGNALED(status) ? WTERMSIG(status) : 0,
          ru.ru_minflt, ru.ru_majflt, ru.ru_nvcsw, ru.ru_nivcsw);
  fclose(f);
  return WIFEXITED(status) ? WEXITSTATUS(status) : 1;
}
