"""[BINDING wrlm-generator-v1] the coverage policy, the two families, the loop.

Build-order step 2 of TRVM/WRLM_RESEARCH_BRIEF.md §10, second object. R1-R3h/R18/
R19 live in `test_worldrecord.py` and cover the captured world; R4-R17 here cover
what is built OUT of one.

Every check below mechanizes a ruling rather than a preference. The three
rejections that shaped the coverage spec -- `base_semantic_id` is not a coverage
dimension, declared `difficulty` is not a coverage dimension, and there is no one
giant Cartesian cell -- are each tested by PARSING the module that states them,
because a law about a seam that is checked by string search is a law that a
comment can satisfy.

Run:  python3 test_generator.py      (or: python3 -m wrlm.test_generator)
"""

import ast
import copy
import hashlib
import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from wrlm import coverage as C
from wrlm import families as F
from wrlm import generator as GEN
from wrlm import goalspec as G
from wrlm import taskbundle as T
from wrlm import worldrecord as R
from wrlm.errors import WrlmError

HERE = os.path.dirname(os.path.abspath(__file__))

FAILED = []


def check(label, ok, detail=""):
    print("  [%s] %s%s" % ("PASS" if ok else "FAIL", label,
                           "" if ok else "  <-- %s" % detail))
    if not ok:
        FAILED.append(label)


def raises(code, fn, *a, **kw):
    try:
        fn(*a, **kw)
    except WrlmError as e:
        if e.code == code:
            return True, ""
        return False, "raised %s, wanted %s" % (e.code, code)
    except Exception as e:                                    # noqa: BLE001
        return False, "raised untyped %s: %s" % (type(e).__name__, e)
    return False, "did not raise"


def load(name):
    with open(os.path.join(HERE, "fixtures", name)) as fh:
        return json.load(fh)


RECORDS = load("pool_records.json")
BY_SEM = {r["semantic_id"]: r for r in RECORDS}
VIEWS = {sem: R.view(rec) for sem, rec in BY_SEM.items()}

# Small enough to keep the battery honest about its own runtime, large enough
# that the corpus spans several cells, both families and every size bucket the
# pool can reach.
LIMIT = 40


def module_ast(name):
    with open(os.path.join(HERE, name)) as fh:
        return ast.parse(fh.read(), filename=name)


def literal_assign(tree, name):
    """The literal value of a module-level assignment, read from the SOURCE.

    Not `getattr(module, name)`: the point of several checks below is that the
    stated policy and the running policy are the same object, so one side has to
    be obtained without executing the other."""
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name) and t.id == name:
                    return ast.literal_eval(node.value)
    return None


def relabel(view, prefix="zz"):
    """The same world with every object renamed. Nothing structural moves."""
    ids = sorted({o["object_id"] for o in view["objects"]})
    ren = {o: "%s%d" % (prefix, i) for i, o in enumerate(ids)}
    objs = []
    for o in view["objects"]:
        n = copy.deepcopy(o)
        n["object_id"] = ren[o["object_id"]]
        objs.append(n)
    edges = [dict(e, src=ren.get(e["src"], e["src"]),
                  dst=ren.get(e["dst"], e["dst"])) for e in view["edges"]]
    return {"objects": objs, "edges": edges}


def main():
    print("[BINDING wrlm-generator-v1] coverage policy, task families, "
          "corpus loop")

    cov_ast = module_ast("coverage.py")
    fam_ast = module_ast("families.py")

    # ------------------------------------------------------------------ R4
    # `base_shape_id` exists so that a world and its own relabelling cannot be
    # treated as two different worlds. That is what makes it usable for reuse
    # caps and, more importantly, for split blocking.
    src = VIEWS[RECORDS[0]["semantic_id"]]
    inv = all(C.base_shape_id(v) == C.base_shape_id(relabel(v))
              and C.base_shape_id(v) == C.base_shape_id(relabel(v, "qq"))
              for v in VIEWS.values())
    shapes = {C.base_shape_id(v) for v in VIEWS.values()}
    # Collisions are ALLOWED (they over-merge, which is the safe direction), but
    # a fingerprint that merged everything would be useless, so it must still
    # separate the pool into more than one class.
    distinct = len(shapes) > 1
    # and it is not a rung on the identity ladder
    prefixed = C.base_shape_id(src).startswith("shape-")
    check("R4)  base_shape_id is renaming-invariant across the whole pool, "
          "still separates it, and is prefixed `shape-` not `sem-`",
          inv and distinct and prefixed,
          "inv=%s distinct=%d prefixed=%s" % (inv, len(shapes), prefixed))

    # ------------------------------------------------------------------ R5
    # Read from the source of coverage.py, then compared with the running value.
    # A cell dimension that could be added at import time would make the stated
    # policy decorative.
    stated = literal_assign(cov_ast, "CELL_FIELDS")
    factor_keys = set(C.all_factors(src, None, []))
    banned_in_cell = not ({"base_semantic_id", "difficulty", "semantic_id",
                           "sem"} & set(stated or ()))
    banned_in_factors = not ({"difficulty"} & factor_keys)
    check("R5)  neither base_semantic_id nor declared difficulty is a coverage "
          "dimension -- identity diversity is not semantic diversity, and "
          "balancing on a label the generator writes is a closed loop",
          stated is not None and tuple(stated) == tuple(C.CELL_FIELDS)
          and banned_in_cell and banned_in_factors,
          "stated=%s running=%s" % (stated, C.CELL_FIELDS))

    # ------------------------------------------------------------------ R6
    # Each family publishes its own objective-shape vocabulary. A cross-family
    # cell is not a sparse cell, it is a meaningless one, and the domain has to
    # say so rather than let the ledger spend forever failing to fill it.
    cells = F.valid_cells()
    cross = [c for c in cells
             if c["objective_shape"] not in F.OBJECTIVE_SHAPES[c["family"]]]
    all_valid = True
    try:
        for c in cells:
            C.validate_cell_v1(c)
    except WrlmError:
        all_valid = False
    expect = (len(F.FAMILIES) * len(C.TIERS) * len(C.SIZE_BUCKETS) * 4
              * len(C.WITNESS_BUDGET_BUCKETS) * len(C.PRESENTATION_FORMS))
    # and the derivation can never PRODUCE another family's shape either
    leak = False
    for fam in F.FAMILIES:
        for goal in (None, G.exactly("objects", G.role("Door"), 1),
                     G.none("objects", G.role("Door")),
                     {"kind": "any", "args": [G.exactly("objects",
                                                        G.role("Door"), 1)]},
                     {"kind": "all", "args": [G.exactly("objects",
                                                        G.role("Door"), 1)]}):
            for wit in ([], [F.op_set_config("p0", {})],
                        [F.op_add_object("n", "Door", {}),
                         F.op_add_edge("p0", "n", "SignalWire")]):
                for pres in (False, True):
                    s = F.derive_objective_shape(fam, goal, wit, pres)
                    if s not in F.OBJECTIVE_SHAPES[fam]:
                        leak = True
    check("R6)  every family publishes its own cell domain: no cross-family "
          "objective shape exists in it, and none can be derived into one",
          not cross and all_valid and not leak and len(cells) == expect,
          "cross=%d n=%d want=%d leak=%s" % (len(cross), len(cells), expect,
                                             leak))

    # ------------------------------------------------------------------ R7
    # The tier is the ruled contract, so it is DERIVED from the task and then
    # compared. A candidate whose derived cell disagrees is rejected, not
    # relabelled -- a cell that could be asserted would be a cell that could be
    # faked.
    rec = RECORDS[0]
    view = VIEWS[rec["semantic_id"]]
    anchor = sorted(o["object_id"] for o in view["objects"])[0]
    ordered = [F.op_add_object("n_new", "Door", {}),
               F.op_add_edge(anchor, "n_new", "SignalWire")]
    goal = G.exactly("objects", G.role("Door"),
                     1 + sum(1 for o in view["objects"]
                             if o["role"] == "Door"))
    lying = T.make_task(rec["semantic_id"], rec["source"], goal=goal,
                        family=F.FAMILY_GOAL_SATISFACTION, tier=1,
                        difficulty="easy")
    derived = F.derive_cell(F.FAMILY_GOAL_SATISFACTION, view, lying, ordered,
                            rec)
    requested = C.make_cell(F.FAMILY_GOAL_SATISFACTION, 1,
                            C.size_bucket(len(view["objects"])),
                            derived["objective_shape"], "2", "source")
    ok_mis, d_mis = raises(F.WRLM_CELL_MISMATCH, F.check_cell, requested,
                           derived)
    check("R7)  tier is derived from the witness, not read off the task: a "
          "bundle DECLARING tier 1 over an order-dependent witness derives "
          "tier 3, and the mismatch is a typed refusal",
          lying["stratum"]["tier"] == 1 and derived["tier"] == 3 and ok_mis,
          "derived=%s %s" % (derived["tier"], d_mis))

    # ------------------------------------------------------------------ R8
    # A goal without a constructive witness is only a wish. Unsatisfiable tasks
    # are the quietest way to poison a reward signal: every attempt fails, so
    # the model is trained against its own correct behaviour.
    pairs = 0
    ok_wit = True
    no_identity = True
    for a in RECORDS[:6]:
        for b in RECORDS[:6]:
            if a["semantic_id"] == b["semantic_id"]:
                continue
            va, vb = VIEWS[a["semantic_id"]], VIEWS[b["semantic_id"]]
            w = F.diff_witness(va, vb)
            try:
                F.verify_witness(va, w, vb)
            except WrlmError:
                ok_wit = False
                continue
            pairs += 1
            if "semantic_id" in F.apply_witness(va, w):
                no_identity = False
    # a witness that does NOT land where it claims is refused
    va = VIEWS[RECORDS[0]["semantic_id"]]
    vb = VIEWS[RECORDS[1]["semantic_id"]]
    full = F.diff_witness(va, vb)
    ok_short, d_short = raises(F.WRLM_BAD_WITNESS, F.verify_witness, va,
                               full[:-1], vb)
    check("R8)  a witness is CHECKED to reach its target, a truncated one is "
          "refused, and a simulated world never invents a `sem-`",
          ok_wit and pairs >= 20 and no_identity and ok_short,
          "pairs=%d wit=%s ident=%s %s" % (pairs, ok_wit, no_identity,
                                           d_short))

    # ------------------------------------------------------------------ R9
    # "Interacting" is defined exactly once. If the ledger and the tier contract
    # each had their own notion, they could drift into disagreeing about what
    # tier 3 means and nobody would notice until the corpus was built.
    uses_shared = False
    for node in ast.walk(fam_ast):
        if isinstance(node, ast.FunctionDef) and node.name == "derive_tier":
            for sub in ast.walk(node):
                if (isinstance(sub, ast.Attribute)
                        and sub.attr == "ordering_required"):
                    uses_shared = True
    independent = [F.op_set_config("p0", {"a": 1}),
                   F.op_set_config("r0", {"b": 2})]
    interacting = [F.op_add_object("n_new", "Door", {}),
                   F.op_add_edge("p0", "n_new", "SignalWire")]
    # overlap alone must NOT be enough: two edits touching the same node is the
    # common case, and calling it interacting would drain the tier of content
    overlap_only = [F.op_set_config("p0", {"a": 1}),
                    F.op_add_edge("p0", "r0", "SignalWire")]
    check("R9)  one shared definition of ordering: derive_tier calls "
          "coverage.ordering_required, and mere touched-object overlap does "
          "NOT make a witness interacting",
          uses_shared
          and not C.ordering_required(independent)
          and C.ordering_required(interacting)
          and not C.ordering_required(overlap_only)
          and F.derive_tier(None, interacting) == 3
          and F.derive_tier(None, independent) == 2,
          "shared=%s" % uses_shared)

    # ------------------------------------------------------------------ R10
    # A lexicographic tie-break permanently privileges whichever enum value
    # sorts first, and re-privileges it after every reset or partial
    # regeneration. Hashing against the corpus seed is just as reproducible.
    tier1 = [c for c in cells if c["family"] == F.FAMILY_GOAL_SATISFACTION
             and c["tier"] == 1]
    lex_min = min(tier1, key=C.cell_key)
    picks, differs = [], 0
    for i in range(8):
        spec = C.CoverageSpecV1("tie-seed-%d" % i)
        led = C.CoverageLedger(spec)
        pick = C.select_cell(led, tier1, (F.FAMILY_GOAL_SATISFACTION, 1))
        # deterministic across a RESET: a fresh ledger with the same spec must
        # reproduce it exactly
        led2 = C.CoverageLedger(C.CoverageSpecV1("tie-seed-%d" % i))
        again = C.select_cell(led2, tier1, (F.FAMILY_GOAL_SATISFACTION, 1))
        if C.cell_key(pick) != C.cell_key(again):
            differs = -999
        picks.append(C.cell_key(pick))
        if C.cell_key(pick) != C.cell_key(lex_min):
            differs += 1
    check("R10) tied cells are broken by HASH of (seed, spec version, cell), "
          "not lexicographically: the pick moves with the seed, is stable "
          "across a ledger reset, and is not the lexicographic first",
          len(set(picks)) > 1 and differs >= 7,
          "distinct=%d non_lex=%s" % (len(set(picks)), differs))

    # ------------------------------------------------------------------ R11
    # Ten thousand proposals and two acceptances is not a healthy cell. Keeping
    # the other seven counters is what makes an under-covered cell
    # distinguishable from a generator that cannot inhabit the cell it claims.
    spec = C.CoverageSpecV1("quota-seed")
    led = C.CoverageLedger(spec)
    cell = tier1[0]
    before = led.deficit(cell)
    for outcome in C.OUTCOMES:
        if outcome == "accepted_unique":
            continue
        for _ in range(50):
            led.record(cell, outcome)
    unmoved = led.deficit(cell) == before
    led.accept(cell, "case-a" * 8, C.all_factors(view, None, []),
               rec["semantic_id"])
    moved = led.deficit(cell) == before - 1
    ok_unknown, d_unknown = raises(C.WRLM_BAD_COVERAGE, led.record, cell,
                                   "looks_fine")
    counted = led.counts(cell)["proposed"] == 50
    check("R11) only accepted_unique satisfies a quota, but all eight outcomes "
          "are retained -- 350 recorded failures move no deficit and are still "
          "visible", unmoved and moved and counted and ok_unknown,
          "unmoved=%s moved=%s counted=%s %s" % (unmoved, moved, counted,
                                                 d_unknown))

    # ------------------------------------------------------------------ R12
    # Where `sem-` earns its keep after being thrown out of the cell: real reuse
    # of one rich world is fine, one demonstration world quietly BECOMING the
    # benchmark is not.
    spec2 = C.CoverageSpecV1("cap-seed", max_per_sem=2, max_per_shape=3)
    led2 = C.CoverageLedger(spec2)
    fac = C.all_factors(view, None, [])
    fam, tier = cell["family"], cell["tier"]
    for i in range(2):
        led2.accept(cell, "case-%02d" % i, fac, rec["semantic_id"])
    sem_bound = led2.sem_capped(rec["semantic_id"], fam, tier)
    other_sem_free = not led2.sem_capped("sem-" + "0" * 64, fam, tier)
    # the shape cap binds ACROSS distinct sem-, which is the whole point
    for i in range(2):
        led2.accept(cell, "case-x%d" % i, fac, "sem-%064d" % i)
    shape_bound = led2.shape_capped(fac["base_shape_id"], fam, tier)
    # and a cap is scoped to (family, tier), not global
    scoped = not led2.shape_capped(fac["base_shape_id"], fam, 3)
    check("R12) reuse caps bind: max_per_sem stops one world dominating, "
          "max_per_shape binds across DIFFERENT sem- that share a structure, "
          "and both are scoped to (family, tier)",
          sem_bound and other_sem_free and shape_bound and scoped,
          "sem=%s shape=%s scoped=%s" % (sem_bound, shape_bound, scoped))

    # ------------------------------------------------------------------ R13
    # A benchmark whose contents depend on when it was built cannot be compared
    # with itself across runs, and a corpus that cannot be regenerated cannot be
    # audited.
    def digest(corpus):
        return hashlib.sha256(json.dumps(
            [c["case_id"] for c in corpus], separators=(",", ":")).encode()
        ).hexdigest()[:24]

    specA = C.CoverageSpecV1("seed-A")
    corpus, ledger = GEN.generate_corpus(RECORDS, specA, limit=LIMIT)
    again, _ = GEN.generate_corpus(RECORDS, C.CoverageSpecV1("seed-A"),
                                   limit=LIMIT)
    other, _ = GEN.generate_corpus(RECORDS, C.CoverageSpecV1("seed-B"),
                                   limit=LIMIT)
    dA, dA2, dB = digest(corpus), digest(again), digest(other)
    unique = len({c["case_id"] for c in corpus}) == len(corpus)
    check("R13) the corpus is byte-reproducible from (pool, corpus_seed), "
          "moves when the seed moves, and contains no duplicate `case-`",
          dA == dA2 and dA != dB and unique and len(corpus) == LIMIT,
          "%s / %s / %s unique=%s n=%d" % (dA, dA2, dB, unique, len(corpus)))

    # ------------------------------------------------------------------ R14
    # Re-derived from the STORED task, witness and record -- nothing is read
    # back off the label the generator wrote.
    off_cell = []
    for item in corpus:
        cel = item["cell"]
        base = BY_SEM[item["task"]["base_world"]["semantic_id"]]
        bview = VIEWS[base["semantic_id"]]
        pres = cel["objective_shape"] == "preservation"
        d = F.derive_cell(cel["family"], bview, item["task"], item["witness"],
                          base, pres)
        if C.cell_key(d) != C.cell_key(cel):
            off_cell.append((C.cell_key(d), C.cell_key(cel)))
    # difficulty is derived from tier, so it cannot drift away from the contract
    drifted = [i for i in corpus
               if i["task"]["stratum"]["difficulty"]
               != GEN._DIFFICULTY_BY_TIER[i["cell"]["tier"]]]
    check("R14) every accepted item's cell RE-DERIVES from its stored task, "
          "witness and record, and its provenance difficulty is a function of "
          "the derived tier",
          not off_cell and not drifted,
          "off=%s drift=%d" % (off_cell[:1], len(drifted)))

    # ------------------------------------------------------------------ R15
    # A task solved before it starts is pure reward noise; a task nobody has
    # shown to be solvable is worse.
    degenerate, unreached = [], []
    for item in corpus:
        base = BY_SEM[item["task"]["base_world"]["semantic_id"]]
        bview = VIEWS[base["semantic_id"]]
        try:
            T.check_task_nondegenerate(item["task"], bview)
        except WrlmError:
            degenerate.append(item["case_id"])
            continue
        reached = F.apply_witness(bview, item["witness"])
        obj = item["task"]["objective"]
        if obj["goal"] is not None and not G.evaluate_goal(obj["goal"],
                                                           reached):
            unreached.append(item["case_id"])
        tgt = obj["target_semantic_id"]
        if tgt is not None:
            if F._norm(reached) != F._norm(VIEWS[tgt]):
                unreached.append(item["case_id"])
    check("R15) every accepted task is unsolved at its base AND carries a "
          "witness that reaches its objective -- the goal evaluates true, the "
          "target world is structurally reached",
          not degenerate and not unreached,
          "degen=%s unreached=%s" % (degenerate[:2], unreached[:2]))

    # ------------------------------------------------------------------ R16
    # Splitting by `case-` lets a world and its own relabelling land on opposite
    # sides: contamination with extra steps, inflating the score by exactly the
    # amount nobody can measure.
    splits = GEN.split_assignment(corpus, specA)
    where = {}
    straddling = []
    for name, items in splits.items():
        for i in items:
            s = i["factors"]["base_shape_id"]
            if where.setdefault(s, name) != name:
                straddling.append(s)
    total = sum(len(v) for v in splits.values()) == len(corpus)
    # the property that actually matters, tested directly: a relabelled world
    # is assigned to the same side as its original
    twin_ok = True
    for item in corpus:
        bview = VIEWS[item["task"]["base_world"]["semantic_id"]]
        if C.base_shape_id(relabel(bview)) != item["factors"]["base_shape_id"]:
            twin_ok = False
    check("R16) train/validation/test are blocked on base_shape_id: no shape "
          "straddles two splits, a relabelled world lands with its original, "
          "and nothing is dropped",
          not straddling and total and twin_ok,
          "straddle=%s total=%s twin=%s" % (straddling[:1], total, twin_ok))

    # ------------------------------------------------------------------ R17
    # The architectural claim of step 2, checked by PARSING rather than reading:
    # an engine is needed to CAPTURE a world, never to USE one. `tools/` is
    # deliberately outside the package and is the one place forge appears --
    # asserted here too, so the separation cannot be satisfied vacuously by
    # nobody importing forge anywhere.
    forge_importers = []
    scanned = 0
    for name in sorted(os.listdir(HERE)):
        if not name.endswith(".py"):
            continue
        scanned += 1
        for node in ast.walk(module_ast(name)):
            mods = []
            if isinstance(node, ast.Import):
                mods = [a.name for a in node.names]
            elif isinstance(node, ast.ImportFrom):
                mods = [node.module or ""]
            for m in mods:
                head = m.split(".")[0]
                if head in ("forge", "forge_api", "spinner_bench", "wrl_ir",
                            "wrl_canonical", "fixture", "compiler"):
                    forge_importers.append((name, m))
    with open(os.path.join(HERE, "tools", "build_pool.py")) as fh:
        tools_ast = ast.parse(fh.read())
    tools_imports = {a.name for n in ast.walk(tools_ast)
                     if isinstance(n, ast.Import) for a in n.names}
    tools_imports |= {n.module for n in ast.walk(tools_ast)
                      if isinstance(n, ast.ImportFrom) and n.module}
    tools_uses_forge = "forge_api" in tools_imports
    probe = ("import json,sys;"
             "from wrlm import coverage as C, generator as GEN;"
             "recs=json.load(open('wrlm/fixtures/pool_records.json'));"
             "c,l=GEN.generate_corpus(recs, C.CoverageSpecV1('seed-A'), "
             "limit=4);"
             "print(json.dumps([x['case_id'] for x in c]))")
    proc = subprocess.run([sys.executable, "-B", "-c", probe],
                          cwd=os.path.dirname(HERE), capture_output=True,
                          env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1"))
    offline = proc.returncode == 0 and len(json.loads(proc.stdout or "[]")) == 4
    check("R17) the wrlm package imports no engine at all (%d modules parsed), "
          "generation runs in a clean subprocess, and the ONE script that does "
          "touch forge sits outside the package" % scanned,
          not forge_importers and tools_uses_forge and offline,
          "%s tools=%s offline=%s %s" % (forge_importers[:2], tools_uses_forge,
                                         offline,
                                         (proc.stderr.decode() or
                                          "").strip().splitlines()[-1:]))

    print()
    print("  corpus %d over %d cells touched, %d filled; marginals %d, pairs %d"
          % (len(corpus), ledger.report()["cells_touched"],
             ledger.report()["cells_filled"],
             ledger.report()["marginal_values_seen"],
             ledger.report()["pairs_seen"]))
    print("  totals %s" % json.dumps(ledger.report()["totals"], sort_keys=True))
    print()
    if FAILED:
        print("FAILED: %s" % ", ".join(FAILED))
        return 1
    print("PASS_GENERATOR_V1 -- the cell is derived, the witness is checked, "
          "the corpus is reproducible.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
