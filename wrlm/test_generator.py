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
import itertools
import json
import os
import random
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
    # The published domain is the FEASIBLE subset of the Cartesian product, so
    # the expected size is counted per family from its own reachable triples.
    expect = sum(len(F.feasible_triples(fam)) for fam in F.FAMILIES) \
        * len(C.SIZE_BUCKETS) * len(C.PRESENTATION_FORMS)
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
    # Counted from OUTCOMES rather than written down: this label said "eight"
    # and "350" for three more outcomes than that, and a number in a passing
    # test's prose is a number nobody re-reads.
    n_out = len(C.OUTCOMES)
    check("R11) only accepted_unique satisfies a quota, but all %d outcomes "
          "are retained -- %d recorded failures move no deficit and are still "
          "visible" % (n_out, 50 * (n_out - 1)),
          unmoved and moved and counted and ok_unknown,
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

    # ------------------------------------------------------------------ R20
    # A published cell that nothing can inhabit is not a hard cell, it is a
    # contradiction, and counting it as empty measures the domain instead of the
    # corpus. So every published cell must have a PREIMAGE -- exhibited here
    # constructively, with witnesses built differently from the ones
    # `families._probe_witness` uses (ordering arrives via a removal another op
    # references, not an addition), so the two constructions cannot agree by
    # sharing a mistake.
    def wit(n, ordering):
        if n < 1 or (ordering and n < 2):
            return None
        pad = [F.op_add_object("t%d" % i, "Orb", {}) for i in range(n - 2 * bool(
            ordering))]
        if not ordering:
            return pad
        return [F.op_remove_edge("a0", "b0", "SignalWire"),
                F.op_remove_object("b0")] + pad

    one = G.exactly("objects", G.role("Orb"), 2)
    neg = {"kind": "not", "arg": one}
    tt_goals = [(None, False), (one, True)]
    gs_goals = [(one, False), (G.none("objects", G.role("Orb")), False),
                (neg, False), ({"kind": "all", "args": [one, one]}, False),
                ({"kind": "all", "args": [one, neg]}, False),
                ({"kind": "any", "args": [one, one]}, False)]
    preimage = {}
    for fam, goals in ((F.FAMILY_TARGET_TRANSFORM, tt_goals),
                       (F.FAMILY_GOAL_SATISFACTION, gs_goals)):
        for goal, pres in goals:
            for n in range(1, F.MAX_WITNESS + 1):
                for ordering in (False, True):
                    w = wit(n, ordering)
                    if w is None or C.ordering_required(w) != ordering:
                        continue
                    preimage.setdefault(fam, set()).add(
                        (F.derive_tier(goal, w, pres),
                         F.derive_objective_shape(fam, goal, w, pres),
                         C.witness_budget_bucket(n)))
    dead_published = [c for c in cells
                      if (c["tier"], c["objective_shape"],
                          c["witness_edit_budget"]) not in preimage[c["family"]]]
    # ...and narrowing must not have deleted a whole coordinate VALUE, which is
    # the way an over-tight domain would hide instead of announce itself.
    kept = {f: {c[f] for c in cells} for f in C.CELL_FIELDS}
    complete = (kept["tier"] == set(C.TIERS)
                and kept["base_size_bucket"] == {b[0] for b in C.SIZE_BUCKETS}
                and kept["witness_edit_budget"] == {b[0] for b
                                                    in C.WITNESS_BUDGET_BUCKETS}
                and kept["presentation_form"] == set(C.PRESENTATION_FORMS)
                and kept["family"] == set(F.FAMILIES)
                and all({c["objective_shape"] for c in cells
                         if c["family"] == f} == set(F.OBJECTIVE_SHAPES[f])
                        for f in F.FAMILIES))
    check("R20) every one of the %d published cells has a preimage under an "
          "independently built witness, and narrowing deleted no coordinate "
          "value" % len(cells),
          not dead_published and complete,
          "dead=%d complete=%s" % (len(dead_published), complete))

    # ------------------------------------------------------------------ R21
    # The excluded cells are excluded for a REASON that can be stated and
    # refused, not merely omitted from a list.
    full = []
    for fam in F.FAMILIES:
        for tier in C.TIERS:
            for size, _a, _b in C.SIZE_BUCKETS:
                for shape in F.OBJECTIVE_SHAPES[fam]:
                    for bud, _c, _d in C.WITNESS_BUDGET_BUCKETS:
                        for pres in C.PRESENTATION_FORMS:
                            full.append(C.make_cell(fam, tier, size, shape,
                                                    bud, pres))
    excluded = [c for c in full if not F.cell_in_domain(c)]
    refused = 0
    for c in (C.make_cell(F.FAMILY_TARGET_TRANSFORM, 3, "tiny", "local", "1",
                          "source"),
              C.make_cell(F.FAMILY_TARGET_TRANSFORM, 1, "tiny", "structural",
                          "2", "source"),
              C.make_cell(F.FAMILY_GOAL_SATISFACTION, 1, "tiny", "conjunction",
                          "1", "source")):
        try:
            F.check_cell_in_domain(c)
        except WrlmError as exc:
            if exc.code == C.WRLM_CELL_UNKNOWN:
                refused += 1
    off_domain = [i for i in corpus if not F.cell_in_domain(i["cell"])]
    check("R21) the %d unreachable cells are refused by name (%s), not merely "
          "left out, and the generator never emits one"
          % (len(excluded), C.WRLM_CELL_UNKNOWN),
          len(excluded) == len(full) - len(cells) and refused == 3
          and not off_domain,
          "excluded=%d refused=%d off=%d" % (len(excluded), refused,
                                             len(off_domain)))

    # ------------------------------------------------------------------ R22
    # The reconciliation that makes the narrowing safe to believe. Both runs are
    # saturated -- neither reaches its acceptance limit -- so what separates them
    # is the domain and nothing else.
    #
    # THE LOAD-BEARING HALF is that no cell the narrowing removed was ever
    # inhabited by either run. That is the whole justification for deleting 448
    # cells from the published denominator, and it is a claim about the corpus
    # rather than about the generator's mood.
    #
    # The second half USED to assert set equality, and that assertion was true
    # only while the corpus sat well inside the reuse caps. It is not a law, and
    # widening `propose_goals` is what showed it: with 226 cells now reachable
    # instead of 104, the caps bind, and the caps are a FINITE budget per
    # (family, tier) that the greedy selector spends in whatever order marginal
    # deficits suggest. Padding the domain with 448 dead cells changes those
    # marginal deficits, so the same budget gets spent on a different set -- and
    # here the wide run reaches one fewer LIVE cell than the tight one.
    #
    # That is worth stating plainly, because it is stronger than the claim it
    # replaces: a dead cell is not inert. It is not merely diluting a ratio, it
    # is displacing real coverage. So the check keeps the inclusion --
    # narrowing never COSTS a cell -- and reports the displacement instead of
    # asserting it away.
    wide, _lw = GEN.generate_corpus(RECORDS, C.CoverageSpecV1("recon"),
                                    limit=900, cells=full)
    tight, _lt = GEN.generate_corpus(RECORDS, C.CoverageSpecV1("recon"),
                                     limit=900, cells=cells)
    in_wide = {C.cell_key(i["cell"]) for i in wide}
    in_tight = {C.cell_key(i["cell"]) for i in tight}
    dead_keys = {C.cell_key(c) for c in excluded}
    saturated = len(wide) < 900 and len(tight) < 900
    displaced = len(in_tight - in_wide)
    check("R22) both runs saturate, no cell removed by the narrowing was ever "
          "inhabited by either (%d dead cells), and narrowing costs nothing: "
          "publishing the dead cells DISPLACES %d live cell(s) out of %d, "
          "because the reuse caps are a finite budget the selector spends in "
          "domain order" % (len(dead_keys), displaced, len(in_tight)),
          saturated and not ((in_wide | in_tight) & dead_keys)
          and not (in_wide - in_tight),
          "wide=%d tight=%d lost_by_narrowing=%d overlap_with_dead=%d "
          "saturated=%s" % (len(in_wide), len(in_tight),
                            len(in_wide - in_tight),
                            len((in_wide | in_tight) & dead_keys), saturated))

    # ------------------------------------------------------------------ R23
    # The witness simulator against the engine's real edit algebra. Each case
    # names WHICH gate must fire, because the two gates mean different things:
    # `WRLM_BAD_WITNESS` is the operation's own precondition and is in exact
    # parity with `wrl_draft._apply_operation`, while `WRLM_WITNESS_NOT_CLOSED`
    # is the referential closure the engine defers to its seal and this layer
    # enforces early. A battery that only asked "does it fail" would let the two
    # collapse into each other and could not notice the parity breaking.
    base = {"objects": [{"object_id": "a", "role": "Pulser",
                         "static_config": {}},
                        {"object_id": "b", "role": "Door",
                         "static_config": {}}],
            "edges": [{"src": "a", "dst": "b", "kind": "SignalWire"}]}

    def gate(witness):
        try:
            F.apply_witness(base, witness)
        except WrlmError as exc:
            return exc.code
        return "ok"

    algebra = [
        # ------------------------------------------------- precondition gate
        ("AddObject onto a live id", [F.op_add_object("a", "Door", {})],
         F.WRLM_BAD_WITNESS),
        ("RemoveObject of nothing", [F.op_remove_object("zz")],
         F.WRLM_BAD_WITNESS),
        ("SetObjectConfig on nothing", [F.op_set_config("zz", {"k": 1})],
         F.WRLM_BAD_WITNESS),
        ("duplicate edge", [F.op_add_edge("a", "b", "SignalWire")],
         F.WRLM_BAD_WITNESS),
        ("RemoveEdge of no edge", [F.op_remove_edge("b", "a", "SignalWire")],
         F.WRLM_BAD_WITNESS),
        # ------------------------------------------------------ closure gate
        ("edge to a missing endpoint", [F.op_add_edge("a", "zz", "SignalWire")],
         F.WRLM_WITNESS_NOT_CLOSED),
        ("removal with an incident edge", [F.op_remove_object("b")],
         F.WRLM_WITNESS_NOT_CLOSED),
        # ------------------------------------------------- legal, and ORDERED
        ("remove the edge THEN the object",
         [F.op_remove_edge("a", "b", "SignalWire"), F.op_remove_object("b")],
         "ok"),
        ("add THEN configure",
         [F.op_add_object("c", "Door", {}), F.op_set_config("c", {"k": 1})],
         "ok"),
        ("add THEN wire",
         [F.op_add_object("c", "Door", {}),
          F.op_add_edge("a", "c", "SignalWire")], "ok"),
        ("configure twice",
         [F.op_set_config("a", {"k": 1}), F.op_set_config("a", {"k": 2})],
         "ok"),
        ("remove then re-add the same edge",
         [F.op_remove_edge("a", "b", "SignalWire"),
          F.op_add_edge("a", "b", "SignalWire")], "ok"),
        ("remove then re-add the same identity",
         [F.op_remove_edge("a", "b", "SignalWire"), F.op_remove_object("b"),
          F.op_add_object("b", "Relay", {}),
          F.op_add_edge("a", "b", "SignalWire")], "ok"),
    ]
    wrong = ["%s -> %s (wanted %s)" % (lab, gate(w), want)
             for lab, w, want in algebra if gate(w) != want]
    # ...and the SAME legal sequences reversed must fail or land elsewhere, or
    # "order matters" is a word rather than a fact. A case that already fails
    # forwards proves nothing when reversed, so only the legal ones are turned
    # round. `configure twice` reverses to a DIFFERENT world rather than to a
    # failure, which is why the oracle in R24 compares results and not just
    # legality.
    ordered = [(lab, w) for lab, w, want in algebra
               if want == "ok" and len(w) > 1]

    def same_forward_and_back(w):
        try:
            a = json.dumps(F._norm(F.apply_witness(base, w)), sort_keys=True)
            b = json.dumps(F._norm(F.apply_witness(base, list(reversed(w)))),
                           sort_keys=True)
        except WrlmError:
            return False
        return a == b

    reversible = [lab for lab, w in ordered if same_forward_and_back(w)]
    check("R23) all %d edit-algebra cases land on the gate they should, and "
          "every one of the %d ordered witnesses breaks or moves when reversed"
          % (len(algebra), len(ordered)),
          not wrong and not reversible,
          "wrong=%s reversible=%s" % (wrong, reversible))

    # ------------------------------------------------------------------ R24
    # The ordering predicate against a SEMANTIC oracle. `ordering_required` is
    # syntactic -- it reads the operations and never touches a world. The oracle
    # is the definition itself, brute-forced: permute the witness, and if any
    # permutation fails or lands somewhere else, order mattered.
    #
    # The direction that must hold is completeness: the predicate may never say
    # `independent` where the oracle says order matters. That is the failure the
    # old predicate had, and it is silent -- the corpus simply contains fewer
    # tier-3 tasks than the ledger claims, and the ledger is the thing that was
    # supposed to notice. Over-reporting is permitted and MEASURED rather than
    # waved through.
    def order_matters(view, witness):
        try:
            want = json.dumps(F._norm(F.apply_witness(view, witness)),
                              sort_keys=True)
        except WrlmError:
            return True
        for perm in itertools.permutations(range(len(witness))):
            try:
                got = F.apply_witness(view, [witness[i] for i in perm])
            except WrlmError:
                return True
            if json.dumps(F._norm(got), sort_keys=True) != want:
                return True
        return False

    # Drawn from the SATURATED corpus, not the small one built at the top of
    # this file: `corpus` stops at its limit long before the ordering-heavy
    # cells are reached, so sampling it would test the predicate mostly on the
    # short independent witnesses it already handled.
    probes = [(VIEWS[i["task"]["base_world"]["semantic_id"]], i["witness"])
              for i in tight if 2 <= len(i["witness"]) <= 5]
    probes += [(base, w) for _lab, w in ordered]
    unsound, over = [], 0
    for view, wit in probes:
        said = C.ordering_required(wit)
        truth = order_matters(view, wit)
        if truth and not said:
            unsound.append([o["op"] for o in wit])
        elif said and not truth:
            over += 1
    check("R24) over %d real witnesses the ordering predicate is never wrong in "
          "the direction that hides difficulty; it over-reports %d"
          % (len(probes), over), not unsound, "unsound=%s" % (unsound[:3],))

    # ------------------------------------------------------------------ R25
    # The three dependency classes the previous predicate missed, named one by
    # one. This is the regression test for the actual defect rather than for the
    # rewrite in general: each of these was reported INDEPENDENT, so each scored
    # a tier below its own content.
    missed = {
        "add then configure the same object":
            [F.op_add_object("c", "Door", {}), F.op_set_config("c", {"k": 1})],
        "two config writes to one object":
            [F.op_set_config("a", {"k": 1}), F.op_set_config("a", {"k": 2})],
        "remove then re-add the same edge":
            [F.op_remove_edge("a", "b", "SignalWire"),
             F.op_add_edge("a", "b", "SignalWire")],
    }
    still_missed = [k for k, w in missed.items() if not C.ordering_required(w)]
    # ...and the commuting case the fix must NOT sweep up with them. Two edges
    # onto one node change its incidence twice and still commute; calling those
    # ordered would put nearly the whole corpus in tier 3, which loses exactly
    # as much information as the bug being fixed, arriving from the other side.
    commuting = [F.op_add_edge("a", "c", "SignalWire"),
                 F.op_add_edge("a", "d", "SignalWire")]
    check("R25) each of the %d dependency classes the old predicate called "
          "independent is now caught, and two edges onto one node still commute"
          % len(missed),
          not still_missed and not C.ordering_required(commuting),
          "still_missed=%s swept_up=%s" % (still_missed,
                                           C.ordering_required(commuting)))

    # ------------------------------------------------------------------ R26
    # Every proposal ends somewhere with a name. The gap this closes was not
    # small: `off_cell` alone accounts for most of the run, and until it had a
    # name that whole mass was the unexplained difference between `proposed` and
    # the outcomes -- arithmetically indistinguishable from a counting bug.
    gross, named = ledger.accounted()
    tot = ledger.report(cells)["totals"]
    check("R26) all %d proposals are accounted for by name, and the largest "
          "category is the one that used to be invisible: off_cell=%d"
          % (gross, tot["off_cell"]),
          gross == named and gross > 0 and tot["off_cell"] > 0
          and ledger.check_accounting(),
          "gross=%d named=%d" % (gross, named))

    # ------------------------------------------------------------------ R27
    # The binding gate. `proved` means this layer re-lowered the world itself;
    # `asserted` means it took the publisher's word. A benchmark built on the
    # second is measuring the publisher, so the default admits only the first.
    spec_default = C.CoverageSpecV1("bind")
    faked = copy.deepcopy(RECORDS)
    for rec in faked:
        rec["binding"]["kind"] = "asserted"
    check("R27) the default spec admits only %s, and a pool of %d worlds that "
          "are merely asserted is refused rather than benchmarked"
          % (list(spec_default.allowed_binding_kinds), len(faked)),
          spec_default.allowed_binding_kinds == ("proved",)
          and raises(GEN.WRLM_GENERATOR_EXHAUSTED,
                     lambda: GEN.generate_corpus(faked, spec_default,
                                                 limit=5, cells=cells)),
          "allowed=%s" % (spec_default.allowed_binding_kinds,))

    # ------------------------------------------------------------------ R28
    # The repertoire gap, measured rather than described. `propose_goals` is the
    # only source of `goal_satisfaction` tasks, so the set of
    # (tier, shape, budget) triples it can EMIT is a hard ceiling on that
    # family's coverage -- no pool of worlds, however large, supplies a goal
    # shape nobody wrote down. Before the widening this reached 8 of the 29
    # triples the family's own domain admits, which is exactly why the scaling
    # curve read "saturated" at every pool size.
    #
    # Every proposal is also required to be WELL FORMED, SATISFIED by its own
    # witness, and MINIMAL. The last one is the load-bearing one: the cheap way
    # to fill a `5-8` budget cell is to append edits the goal does not need, and
    # a proposer that did that would report depth it has not got. `n_min` is a
    # count of proposals whose witness has a proper subsequence that already
    # satisfies the goal -- checked by executing every subsequence, not by
    # trusting the rule that built it.
    reach, n_prop, n_bad, n_min = set(), 0, 0, 0
    for rec in RECORDS:
        bview = VIEWS[rec["semantic_id"]]
        for goal, wit in F.propose_goals(bview, random.Random(0)):
            n_prop += 1
            try:
                G.validate_goal_v1(goal)
                reached = F.apply_witness(bview, wit)
                ok = (0 < len(wit) <= F.MAX_WITNESS
                      and G.evaluate_goal(goal, reached))
            except WrlmError:
                ok = False
            if not ok:
                n_bad += 1
                continue
            if not F.witness_is_minimal(bview, goal, wit):
                n_min += 1
            reach.add((F.derive_tier(goal, wit),
                       F.derive_objective_shape(F.FAMILY_GOAL_SATISFACTION,
                                                goal, wit),
                       C.witness_budget_bucket(len(wit))))
    want = F.feasible_triples(F.FAMILY_GOAL_SATISFACTION)
    check("R28) the widened proposer reaches %d of the %d (tier, shape, budget) "
          "triples its family admits -- up from 8 -- and across %d proposals "
          "none is malformed, unsatisfied by its own witness, or padded"
          % (len(reach & want), len(want), n_prop),
          reach == want and n_bad == 0 and n_min == 0,
          "reached=%d missing=%s bad=%d padded=%d out_of_domain=%s"
          % (len(reach & want), sorted(want - reach), n_bad, n_min,
             sorted(reach - want)))

    # ------------------------------------------------------------------ R29
    # And the check that keeps R28 honest in the other direction: minimality is
    # a real predicate, not one that returns True for everything. A witness with
    # one deliberately useless edit appended must be caught, and the same
    # witness without it must pass.
    pview = VIEWS[RECORDS[0]["semantic_id"]]
    proles = sorted({o["role"] for o in pview["objects"]})
    phave = sum(1 for o in pview["objects"] if o["role"] == proles[0])
    pgoal = G.exactly("objects", G.role(proles[0]), phave + 1)
    lean = [F.op_add_object("mz0", proles[0], {})]
    padded = lean + [F.op_add_object("mz1", proles[-1], {})]
    check("R29) minimality is a predicate and not a constant: the lean witness "
          "passes and the same witness with one goal-irrelevant edit appended "
          "is refused",
          F.witness_is_minimal(pview, pgoal, lean)
          and not F.witness_is_minimal(pview, pgoal, padded)
          and G.evaluate_goal(pgoal, F.apply_witness(pview, padded)),
          "lean=%s padded=%s"
          % (F.witness_is_minimal(pview, pgoal, lean),
             F.witness_is_minimal(pview, pgoal, padded)))

    rep = ledger.report(cells)
    print()
    print("  domain %d cells of %d in the full product; %d inhabited, "
          "%d at quota" % (len(cells), len(full), len(in_tight),
                           sum(1 for c in cells
                               if _lt.accepted(c) >= _lt.spec.quota(c))))
    print("  corpus %d over %d cells touched, %d inhabited, %d at quota "
          "(quota mass %.3f); marginals %d, pairs %d"
          % (len(corpus), rep["cells_touched"], rep["cells_inhabited"],
             rep["cells_at_quota"], rep["quota_mass"],
             rep["marginal_values_seen"], rep["pairs_seen"]))
    print("  totals %s" % json.dumps(rep["totals"], sort_keys=True))
    print()
    if FAILED:
        print("FAILED: %s" % ", ".join(FAILED))
        return 1
    print("PASS_GENERATOR_V1 -- the cell is derived, the witness is checked, "
          "the corpus is reproducible.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
