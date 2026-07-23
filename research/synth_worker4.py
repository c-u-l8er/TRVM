"""Child worker for synth_bool4 [MP]: owns a hash slice of each level's
candidate stream; receives ONLY serialized base deltas on stdin; replies with
serialized semilattice deltas on stdout. No shared memory with orchestrator."""
import sys, os, json, itertools
sys.setrecursionlimit(100000)
from synth_bool4 import (Base, Worker, store_from_json, store_to_json,
                         gen_level, reps_from, pid_of, ref_size, sig_of)

def main():
    k, K = int(sys.argv[1]), int(sys.argv[2])
    base = Base()
    for line in sys.stdin:
        req = json.loads(line)
        if req["op"] == "quit": return
        d = store_from_json(json.dumps(req["base_delta"], sort_keys=True),
                            env=base)
        base.fold_from(d.prog, d.beh, d.ev, d.ctx)
        nvars, size, task = req["nvars"], req["size"], req["task"]
        lib = req["lib"] or None
        target = tuple(c == "1" for c in req["tgt"])
        cands = ([("V", i) for i in range(nvars)] if size == 1 else
                 gen_level(reps_from(base, nvars), size, lib))
        w = Worker(k, base, task)
        w._grammar = "raw+AP" if lib else "raw"
        w._lib = frozenset(lib or []); w._max = req["max_size"]
        sols, seen = [], set()
        for ast in sorted(cands, key=lambda a: pid_of(a, nvars)):
            p = pid_of(ast, nvars)
            if p in seen or int(p[:16], 16) % K != k: continue
            seen.add(p)
            _, sig, _ = w.classify(ast, nvars, size)
            if sig == target:
                sols.append((ref_size(ast), ref_size(w.resolve_raw(ast)), p))
        delta = Base()
        delta.fold_from(w.prog, w.beh, w.ev, w.ctx)
        print(json.dumps(dict(delta=json.loads(store_to_json(delta)),
                              sols=sols, paid=w.paid, novel=w.novel,
                              ospid=os.getpid(), k=k)), flush=True)

if __name__ == "__main__":
    main()
