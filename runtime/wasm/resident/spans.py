#!/usr/bin/env python3
"""The executor span, four ways, per term — so the number the vertical witness measured (perform p50 67 ms, of which
~56 ms is Node starting) can be read against what a resident host leaves of it:

  floor     a Node process per job: `node ../experimental/cli.mjs < term` (the shape of reduce-file.mjs)
  oneshot   in-process, module loaded once, a Worker per job (lab/BENCH.md §11's shape)     [measure.mjs]
  resident  in-process, warm workers, a fresh instance per job                                [measure.mjs]
  socket    residentd over a Unix socket, driven from THIS Python process (no Node in the client path)

    python3 spans.py [--jobs N] [--pool P] [--out results-resident.json] [TERMFILE ...]

Development reading on a shared host unless the record says otherwise: the JSON carries load average and the
process count so the reader can see what the host was doing.
"""
import argparse, json, os, statistics as st, subprocess, sys, tempfile, time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from client import ResidentClient  # noqa: E402


def pct(xs, p):
    s = sorted(xs)
    return s[min(len(s) - 1, int(p * len(s)))]


def summarize(lat, **extra):
    return dict(n=len(lat), p50_ms=round(pct(lat, .5), 3), p99_ms=round(pct(lat, .99), 3), min_ms=round(min(lat), 3), **extra)


def floor_row(term_file, jobs):
    cli = HERE.parent / 'experimental' / 'cli.mjs'
    lat, statuses = [], {}
    with open(term_file, 'rb') as f:
        term = f.read()
    for _ in range(jobs):
        t0 = time.perf_counter()
        p = subprocess.run(['node', str(cli)], input=term, capture_output=True)
        lat.append((time.perf_counter() - t0) * 1000)
        try:
            s = json.loads(p.stdout)['status']
        except Exception:
            s = 'unparseable'
        statuses[s] = statuses.get(s, 0) + 1
    return summarize(lat, statuses=statuses)


def socket_rows(term_file, jobs, pool):
    term = Path(term_file).read_text(encoding='utf-8')
    sock = os.path.join(tempfile.mkdtemp(prefix='residentd-'), 'r.sock')
    proc = subprocess.Popen(['node', str(HERE / 'residentd.mjs'), '--socket', sock, '--pool', str(pool), '--max-queue', str(pool * 4)],
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    banner = json.loads(proc.stdout.readline())
    rows = {}
    try:
        def drive(concurrency):
            import threading
            lat, timing, lock, statuses = [], [], threading.Lock(), {}
            n = [0]

            def lane():
                c = ResidentClient(sock)
                while True:
                    with lock:
                        if n[0] >= jobs:
                            break
                        n[0] += 1
                    t0 = time.perf_counter(); r = c.reduce(term); dt = (time.perf_counter() - t0) * 1000
                    with lock:
                        lat.append(dt); statuses[r.get('status')] = statuses.get(r.get('status'), 0) + 1
                        if r.get('timing'): timing.append(r['timing'])
                c.close()
            ResidentClient(sock).reduce(term)  # warm-up
            t0 = time.perf_counter()
            ths = [threading.Thread(target=lane) for _ in range(concurrency)]
            [t.start() for t in ths]; [t.join() for t in ths]
            wall = time.perf_counter() - t0
            extra = dict(jobs_per_s=round(len(lat) / wall, 1), statuses=statuses)
            if timing:
                extra['host_timing_p50_ms'] = {k: round(st.median(t[k] for t in timing), 3) for k in ('instantiate_ms', 'run_ms', 'read_ms')}
            return summarize(lat, **extra)
        rows['socket C=1'] = drive(1)
        rows[f'socket C={pool}'] = drive(pool)
        rows['daemon'] = banner
    finally:
        proc.terminate(); proc.wait(timeout=10)
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--jobs', type=int, default=60)
    ap.add_argument('--pool', type=int, default=8)
    ap.add_argument('--out', default=str(HERE / 'results-resident.json'))
    ap.add_argument('terms', nargs='*', default=[str(HERE / 'fixtures' / 'chain30-epoch-1.ic'), str(HERE / 'fixtures' / 'corpus-exp_2p16.ic')])
    a = ap.parse_args()
    out = dict(measured=time.strftime('%Y-%m-%dT%H:%M:%S%z'), host=os.uname().nodename, node=subprocess.run(['node', '--version'], capture_output=True, text=True).stdout.strip(),
               loadavg=os.getloadavg(), ncpu=os.cpu_count(), jobs=a.jobs, pool=a.pool, terms={})
    for term_file in a.terms:
        name = Path(term_file).name
        print(f'# {name}', file=sys.stderr, flush=True)
        rows = {'floor-node-per-job': floor_row(term_file, min(a.jobs, 30))}
        m = json.loads(subprocess.run(['node', str(HERE / 'measure.mjs'), term_file, str(a.jobs), str(a.pool)], capture_output=True, text=True, check=True).stdout)
        rows.update(m['rows'])
        rows.update(socket_rows(term_file, a.jobs, a.pool))
        out['terms'][name] = dict(term_bytes=m['term_bytes'], rows=rows, resident_stats=m['resident_stats'])
        for k, v in rows.items():
            if 'p50_ms' in v:
                print(f'  {k:32s} p50 {v["p50_ms"]:8.3f} ms  p99 {v["p99_ms"]:8.3f} ms  jobs/s {v.get("jobs_per_s", "-")}', file=sys.stderr, flush=True)
    out['loadavg_after'] = os.getloadavg()
    Path(a.out).write_text(json.dumps(out, indent=1))
    print(f'wrote {a.out}', file=sys.stderr)


if __name__ == '__main__':
    main()
