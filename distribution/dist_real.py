"""
dist_real.py -- the boundary-port distributed reducer (dist_ic) taken OFF the
simulation and onto REAL OS processes with REAL inter-process messaging.

dist_ic.py proved the protocol is coordination-free in a faithful single-process
simulation (480 runs, all schedule/partition-independent). This file runs the
SAME protocol with each node as a genuinely isolated OS process: a worker owns a
heap shard in its own process memory, and every cross-shard reference is resolved
by a real message over a multiprocessing channel.

How it stays deadlock-free
--------------------------
Cross-shard beta/dup interactions create mutual data dependencies between shards
(an App on shard A applies a Lam on shard B, whose body references the argument
back on A). If every worker both reduced AND served requests while blocked, that
mutual dependency would deadlock without re-entrant workers. We avoid that here by
the simplest sound split: the workers are PASSIVE shard servers (READ / WRITE /
ALLOC only -- never blocking on each other), and a single coordinator runs the
reduction, touching remote shards purely through messages. No worker ever waits on
another worker, so there is no deadlock. The heaps are genuinely distributed and
every boundary crossing is a real message; what is centralized is the control flow,
not the state.

This is the honest next rung: the boundary-port protocol over real IPC. Pushing the
REDUCTION itself into the workers (distributed control flow) needs re-entrant
workers (threads + fine-grained locks) or a CPS scheduler -- that's the frontier
after this, and it's where parallel speedup would come from.

Reuses dist_ic's reducer (whnf/fire/app_sup/normal), parser, scatter, and show
UNCHANGED -- they are parameterized over a "net" object; we just give them one
whose read/write/alloc are IPC calls instead of dict access.
"""

import multiprocessing as mp
import time
import dist_ic
from dist_ic import T, ERA, is_sub, sub_val, parse, scatter, show, remap_term, Net

# ----------------------------------------------------------------- worker (passive shard server)
def worker_main(wid, in_q, out_q, shard, base_next):
    heap = shard            # this process's OWN heap shard (isolated memory)
    nxt  = base_next
    while True:
        op, args = in_q.get()
        if op == "READ":
            out_q.put(heap[args[0]])
        elif op == "WRITE":
            heap[args[0]] = args[1]; out_q.put(True)
        elif op == "ALLOC":
            b = nxt; nxt += args[0]; out_q.put(b)
        elif op == "DUMP":
            out_q.put((dict(heap), nxt))     # for debugging
        elif op == "STOP":
            out_q.put(True); return

# ----------------------------------------------------------------- IPC-backed net
class RemoteNet:
    """Same interface dist_ic's reducer expects, but read/write/alloc are real
       messages to the worker process that owns the shard."""
    def __init__(self, W, in_qs, out_qs):
        self.W = W
        self.in_qs = in_qs; self.out_qs = out_qs
        self.inter = 0          # interactions (counted by the reused reducer)
        self.remote = 0         # cross-shard interactions (counted by the reused reducer)
        self.msgs = 0           # REAL IPC round-trips
        self.child_order = "lr"
    def _rpc(self, w, op, *args):
        self.msgs += 1
        self.in_qs[w].put((op, args)); return self.out_qs[w].get()
    def read(self, ref):  return self._rpc(ref[0], "READ", ref[1])
    def write(self, ref, val): self._rpc(ref[0], "WRITE", ref[1], val)
    def alloc(self, node, n=1): return (node, self._rpc(node, "ALLOC", n))
    def off(self, ref, k): return (ref[0], ref[1] + k)

# ----------------------------------------------------------------- run on real processes
def run_real(txt, W, assign, child_order="lr"):
    # 1. parse + scatter locally to compute the per-worker shards
    local = Net(W)
    root, freenm = parse(local, txt)
    rm = scatter(local, assign)
    root = T(root.tag, root.lab, rm(root.ref)) if root.ref else root
    freenm2 = {rm(ref): nm for ref, nm in freenm.items()}

    # 2. launch real worker processes, hand each its shard
    ctx = mp.get_context("fork")
    in_qs  = [ctx.Queue() for _ in range(W)]
    out_qs = [ctx.Queue() for _ in range(W)]
    procs  = []
    for w in range(W):
        p = ctx.Process(target=worker_main,
                        args=(w, in_qs[w], out_qs[w], local.heaps[w], local.next[w]))
        p.start(); procs.append(p)

    # 3. drive the reduction from the coordinator over real IPC
    net = RemoteNet(W, in_qs, out_qs); net.child_order = child_order
    t0 = time.time()
    nf = dist_ic.normal(net, root)
    out = show(net, nf, freenm2)
    dt = time.time() - t0

    # 4. shut down workers
    for w in range(W):
        in_qs[w].put(("STOP", ())); out_qs[w].get()
    for p in procs: p.join()

    return out, net.inter, net.remote, net.msgs, dt

# ----------------------------------------------------------------- self-test
if __name__ == "__main__":
    import ic_float, random

    LAB = [1000]
    def ch(n):
        if n == 0: return "λf.λx.x"
        if n == 1: return "λf.λx.(f x)"
        cs = [f"c{i}" for i in range(n)]; src = []; cur = "f"
        for i in range(n-1):
            LAB[0]+=1; L=LAB[0]; nxt = f"t{i}" if i<n-2 else cs[-1]
            src.append(f"!&{L}{{{cs[i]},{nxt}}}={cur};"); cur=nxt
        body="x"
        for c in reversed(cs): body=f"({c} {body})"
        return "λf.λx."+"".join(src)+body
    NOT="λp.λt.λf.((p f) t)"; TRUE="λa.λb.a"; FALSE="λa.λb.b"
    C2="λf.λx.!&1001{f0,f1}=f;(f0 (f1 x))"
    pair2=f"λs.((s ((na {NOT}) {FALSE})) ((nb {NOT}) {TRUE}))"

    cases = [
        ("Ex5", "((λf.λx.!{f0,f1}=f;(f0 (f1 x)) λB.λT.λF.((B F) T)) λa.λb.a)"),
        ("ch4",  f"(({ch(4)} S) Z)"),
        ("exp(2,2)=4", f"(({ch(2)} {ch(2)}) S)"),
        ("exp(3,2)=8", f"(({ch(3)} {ch(2)}) S)"),
        ("(C3 NOT)T",  f"((({ch(3)} {NOT}) {TRUE}) X)"),
        ("div: dup C2->NOT", f"!&8{{na,nb}}={C2}; ((((na {NOT}) {FALSE}) A) B)"),
        ("div2: both copies", f"!&8{{na,nb}}={C2}; ({pair2} λp.λq.p)"),
    ]

    print("Boundary-port protocol on REAL OS processes (each worker = isolated heap shard,")
    print("every cross-shard reference = a real inter-process message).")
    print("="*78)
    print(f"{'term':20} {'oracle':>12} | W | {'IPC msgs':>9} {'x-shard int':>11} {'ms':>7} | verdict")
    allok = True
    for name, t in cases:
        oracle,_,_ = ic_float.run(t)
        results = set()
        for W in (2, 3):
            # a couple of partitions
            l = Net(1); _r,_ = parse(l, t); nu = len(l.units[0])
            for aname, af in [("round-robin", lambda i: i),
                              ("random", lambda i, nu=nu, W=W: random.Random(5*W).randrange(W))]:
                out, inter, remote, msgs, dt = run_real(t, W, af)
                results.add(out)
                if aname == "round-robin":
                    flag = "OK" if out == oracle else "MISMATCH"
                    if out != oracle: allok = False
                    print(f"{name:20} {oracle[:12]:>12} | {W} | {msgs:9} {remote:11} {dt*1000:7.1f} | {flag}")
        if len(results) != 1 or oracle not in results:
            allok = False; print(f"   !! {name}: partition-dependent or wrong: {results}")
    print()
    print("RESULT:", "all real-process runs == single-node oracle (partition-independent)"
          if allok else "DISCREPANCY")
