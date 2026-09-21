"""A minimal client written ONLY from residentd.mjs's documented wire -- 4-byte big-endian
length + UTF-8 JSON -- with nothing imported from TRVM/compiled/. It is pointed at the
COMPILED daemon (residentd.py). If the interop claim in BENCHMARK_LANE §7.8(a) is true,
this answers real jobs."""
import base64, json, socket, struct, sys, time, statistics as st

MAX_FRAME = 1048576 + 4096

def send(sock, obj):
    out = json.dumps(obj).encode("utf-8")
    sock.sendall(struct.pack(">I", len(out)) + out)

def recv(sock):
    head = b""
    while len(head) < 4:
        c = sock.recv(4 - len(head))
        if not c: raise EOFError("closed")
        head += c
    n = struct.unpack(">I", head)[0]
    if n > MAX_FRAME: raise ValueError("oversized frame %d" % n)
    body = b""
    while len(body) < n:
        c = sock.recv(n - len(body))
        if not c: raise EOFError("closed mid-frame")
        body += c
    return json.loads(body.decode("utf-8"))

path, bundle_path, n_jobs = sys.argv[1], sys.argv[2], int(sys.argv[3])
b64 = base64.b64encode(open(bundle_path, "rb").read()).decode("ascii")
meta = json.load(open(sys.argv[4]))

lat, digests, barriers = [], set(), set()
for i in range(1, n_jobs + 1):
    s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM); s.connect(path)   # one connection per job, as Super does
    t0 = time.perf_counter(); send(s, {"id": i, "bundle_b64": b64}); r = recv(s)
    lat.append((time.perf_counter() - t0) * 1000.0); s.close()
    if r.get("status") != "candidate":
        print("REFUSED/ERROR:", json.dumps(r)[:400]); sys.exit(3)
    out = base64.b64decode(r["output_b64"]) if "output_b64" in r else r["output"].encode()
    import hashlib; digests.add(hashlib.sha256(out).hexdigest())
    barriers.add(tuple(sorted(k for k in ("jobRetired","workerExited","childReaped") if r.get(k) is True)))

s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM); s.connect(path)
send(s, {"op": "stats"}); stats = recv(s); s.close()

lat.sort()
print(json.dumps({
    "jobs": n_jobs,
    "nf_sha256_returned": sorted(digests),
    "nf_sha256_expected": meta["nf_sha256"],
    "digest_matches": digests == {meta["nf_sha256"]},
    "barrier_reported": sorted(barriers),
    "p50_ms": round(st.median(lat), 3), "min_ms": round(lat[0], 3), "max_ms": round(lat[-1], 3),
    "cold_first_job_ms": round(lat[0], 3) if n_jobs == 1 else None,
    "served": stats.get("served"), "pool": stats.get("pool"),
}, indent=1))
