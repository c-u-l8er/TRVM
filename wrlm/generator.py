"""The corpus generator: deterministic, offline, and unable to grade itself.

Everything here runs with no engine present. A `WorldRecordV1` was verified once,
at capture, by something that had a Forge; from then on the world is just data
that reopens and revalidates. That is the whole reason `worldrecord.py` was built
before this file existed.

Determinism
-----------

There is no ambient RNG. No `random.random()`, no clock, no `id()`, no set
iteration order leaking into output. Every random choice comes from a
`random.Random` seeded by hashing::

    corpus_seed | coverage_spec_version | generator_version | cell | attempt

so the same corpus specification produces the same corpus, on any machine, in any
order, forever. A benchmark whose contents depend on when it was built cannot be
compared with itself across runs, and a corpus that cannot be regenerated cannot
be audited.

The loop
--------

  1. choose the `(family, tier)` partition furthest from quota **by ratio**, so
     an easy family with a large valid domain cannot swallow the corpus;
  2. choose the cell in it with the largest deficit;
  3. break cell ties by hashing the cell against the corpus seed -- never
     lexicographically, which would permanently favour whichever enum value
     sorts first and would re-favour it after every reset;
  4. generate a bounded batch of candidates for that cell;
  5. keep the survivor that adds the most new marginal and pairwise coverage,
     ties broken by lowest `case-`.

Step 5 is the only place a `case-` tie-break belongs, and the reason is simply
that before step 4 no case exists to break a tie with.

What gets rejected, and why it is counted
-----------------------------------------

invalid, already-solved at base, duplicate `case-`, outside the requested cell,
no constructive witness, over budget. Every rejection is recorded under its own
outcome. A cell with ten thousand proposals and two acceptances is not an
under-covered cell, it is a generator that cannot inhabit the cell it claims, and
those two situations call for opposite responses. Counting only successes makes
them look identical.
"""

import hashlib
import random

from . import coverage as C
from . import families as F
from . import goalspec as G
from . import taskbundle as T
from . import worldrecord as R
from .errors import WrlmError, fail

GENERATOR_ID = "wrlm.generator.v1"
# Bumped with `wrlm.coverage.v1.2`. The version is hashed into every per-cell
# RNG, so it is not decoration: leaving it at "1" while the witness algebra and
# the ordering predicate changed underneath would mean two different corpora
# answering to one seed, which is the one thing a reproducible benchmark cannot
# allow.
GENERATOR_VERSION = "2"

WRLM_GENERATOR_EXHAUSTED = "WRLM_GENERATOR_EXHAUSTED"

BATCH = 8
MAX_ATTEMPTS_PER_CELL = 3

# `difficulty` is a DESCRIPTIVE label kept for provenance. It is derived from the
# tier so it cannot drift, and it drives no allocation whatsoever -- balancing on
# a label the generator itself writes would be a closed loop that reports success
# for a relabelling.
_DIFFICULTY_BY_TIER = {1: "easy", 2: "moderate", 3: "hard"}


def _rng(spec, cell, attempt, salt=""):
    material = "|".join([spec.corpus_seed, spec.version, GENERATOR_VERSION,
                         C.cell_key(cell), str(attempt), salt])
    return random.Random(int(hashlib.sha256(material.encode()).hexdigest()[:16],
                             16))


def _presented(record, form):
    if form == "formatted" and record.get("formatted_source"):
        return record["formatted_source"]
    return record["source"]


class Candidate(object):
    __slots__ = ("task", "witness", "factors", "case", "cell", "record")

    def __init__(self, task, witness, factors, case, cell, record):
        self.task, self.witness, self.factors = task, witness, factors
        self.case, self.cell, self.record = case, cell, record


# ------------------------------------------------------------------ families
def _build_goal_satisfaction(record, view, cell, rng):
    """Propose `(goal, witness)` pairs, keep the ones that inhabit this cell."""
    for goal, witness in F.propose_goals(view, rng):
        if not witness or len(witness) > F.MAX_WITNESS:
            continue
        yield goal, witness, None, False


def _build_target_transform(record, view, cell, pool, rng, views, outcomes):
    """Pair this base with another captured world it can actually reach.

    The target is never invented. It is a world some engine already sealed, so
    its `sem-` is real and the task is scored against something that exists. A
    generator that synthesised its own target would be asserting a `sem-` it had
    no standing to assert -- the counterfeit the whole ladder forbids.
    """
    others = [r for r in pool if r["semantic_id"] != record["semantic_id"]]
    rng.shuffle(others)
    for target in others:
        tview = views[target["semantic_id"]]
        witness = F.diff_witness(view, tview)
        if not witness or len(witness) > F.MAX_WITNESS:
            continue
        try:
            F.verify_witness(view, witness, tview)
        except WrlmError:
            # A diff that describes the right endpoint but cannot be EXECUTED --
            # a step that strands an edge, say. Counted rather than skipped
            # silently: this is the number that would go up first if the witness
            # algebra and the engine's edit algebra drifted apart, and a silent
            # `continue` would spend that signal on nothing.
            outcomes["proposed"] += 1
            outcomes["unsatisfiable_or_no_witness"] += 1
            continue
        # A preservation task additionally pins something that is ALREADY true
        # of the base and must survive: a second, harder question about the same
        # move. Only offered when it is genuinely non-trivial to keep.
        preserved = None
        if cell["objective_shape"] == "preservation":
            preserved = _preservable(view, tview)
            if preserved is None:
                continue
        yield target, witness, preserved, preserved is not None


def _preservable(base_view, target_view):
    """A property true in BOTH worlds, so it constrains without contradicting.

    A preservation clause that fails at the target would make the task
    unsatisfiable, and an unsatisfiable task is the worst thing a generator can
    emit: every attempt is scored wrong, so the reward signal actively teaches
    against correct behaviour."""
    roles = sorted({o["role"] for o in base_view.get("objects") or []})
    for r in roles:
        a = sum(1 for o in base_view.get("objects") or [] if o["role"] == r)
        b = sum(1 for o in target_view.get("objects") or [] if o["role"] == r)
        if a == b and a > 0:
            return G.exactly("objects", G.role(r), a)
    return None


# ------------------------------------------------------------------- one cell
def _views(pool):
    """Memoised projections. A view is a pure function of the record, so an
    evicted or recomputed entry is byte-identical -- this caps work without
    moving anything."""
    return {r["semantic_id"]: R.view(r) for r in pool}


def generate_batch(ledger, cell, pool, attempt=0, views=None):
    """A bounded batch of candidates for one cell. Rejections are counted here.

    Returns `(survivors, outcomes)`; `outcomes` is the per-reason tally the
    ledger needs in order to tell a hard cell from a broken generator.
    """
    spec = ledger.spec
    rng = _rng(spec, cell, attempt)
    outcomes = dict.fromkeys(C.OUTCOMES, 0)
    survivors = []
    views = views if views is not None else _views(pool)

    bases = [r for r in pool
             if C.size_bucket(len(views[r["semantic_id"]]["objects"]))
             == cell["base_size_bucket"]]
    rng.shuffle(bases)

    for record in bases:
        if len(survivors) >= BATCH:
            break
        view = views[record["semantic_id"]]
        shape = C.base_shape_id(view)
        # Caps are checked BEFORE generating, not after: a capped world should
        # not consume the attempt budget of a cell it is no longer allowed in.
        if ledger.sem_capped(record["semantic_id"], cell["family"],
                             cell["tier"]):
            continue
        if ledger.shape_capped(shape, cell["family"], cell["tier"]):
            continue

        if cell["family"] == F.FAMILY_GOAL_SATISFACTION:
            proposals = _build_goal_satisfaction(record, view, cell, rng)
        else:
            proposals = _build_target_transform(record, view, cell, pool, rng,
                                                views, outcomes)

        for item in proposals:
            if len(survivors) >= BATCH:
                break
            outcomes["proposed"] += 1
            cand = _try_candidate(ledger, cell, record, view, item, outcomes)
            if cand is not None:
                survivors.append(cand)
    return survivors, outcomes


def _try_candidate(ledger, cell, record, view, item, outcomes):
    form = cell["presentation_form"]
    presented = _presented(record, form)
    if form == "formatted" and presented == record["source"]:
        # Not a failed proposal: the CELL is unreachable from this record, because
        # the record has no formatted twin distinct from its source. Named, so
        # that "half the presentation axis is empty" reads as a property of the
        # pool rather than as a generator that keeps missing.
        outcomes["presentation_unavailable"] += 1
        return None

    if cell["family"] == F.FAMILY_GOAL_SATISFACTION:
        goal, witness, _t, preservation = item
        target_sem = None
    else:
        target, witness, goal, preservation = item
        target_sem = target["semantic_id"]

    tier_guess = F.derive_tier(goal, witness, preservation)

    # Cheap coordinates first. These are derived from (goal, witness, view)
    # alone, so an off-cell proposal is discarded before a task is minted and a
    # `goal-`/`task-`/`case-` chain is hashed for nothing. The law is unchanged
    # -- the cell is still DERIVED and still compared, and the full comparison
    # against the finished task still runs below. Only the order moved.
    if (tier_guess != cell["tier"]
            or len(witness) > C.WITNESS_BUDGET_BUCKETS[-1][2]
            or C.witness_budget_bucket(len(witness)) != cell["witness_edit_budget"]
            or F.derive_objective_shape(cell["family"], goal, witness,
                                        preservation) != cell["objective_shape"]):
        outcomes["off_cell"] += 1
        return None

    try:
        task = T.make_task(
            record["semantic_id"], presented, goal=goal,
            target_semantic_id=target_sem,
            family=cell["family"], tier=tier_guess,
            difficulty=_DIFFICULTY_BY_TIER[tier_guess],
            generator_id=GENERATOR_ID, generator_version=GENERATOR_VERSION,
            seed=0)
    except WrlmError:
        outcomes["invalid_generated_world"] += 1
        return None

    # Already solved? Then there is nothing for an attempt to do, and a task that
    # scores 1.0 for doing nothing is pure reward noise.
    try:
        T.check_task_nondegenerate(task, view)
    except WrlmError as exc:
        outcomes["degenerate_at_base" if exc.code == T.WRLM_TASK_DEGENERATE
                 else "invalid_generated_world"] += 1
        return None

    # The witness must actually land somewhere that satisfies the objective.
    try:
        reached = F.apply_witness(view, witness)
    except WrlmError:
        outcomes["unsatisfiable_or_no_witness"] += 1
        return None
    if goal is not None and not G.evaluate_goal(goal, reached):
        outcomes["unsatisfiable_or_no_witness"] += 1
        return None

    # The cell is DERIVED and must match what was asked for.
    derived = F.derive_cell(cell["family"], view, task, witness, record,
                            preservation)
    if C.cell_key(derived) != C.cell_key(cell):
        # Not a fault and not a rejection: the proposal was simply for a
        # different cell. It used to be left as the unnamed gap between
        # `proposed` and the named outcomes -- which made an exploration miss
        # arithmetically indistinguishable from a counting bug.
        outcomes["off_cell"] += 1
        return None

    case = T.case_id(task)
    if case in ledger.cases:
        outcomes["duplicate_case"] += 1
        return None

    factors = C.all_factors(view, goal, witness)
    return Candidate(task, witness, factors, case, cell, record)


# --------------------------------------------------------------- the corpus
def generate_corpus(pool, spec, limit=200, cells=None):
    """Run the loop until every cell is at quota or the attempt budget is spent.

    `pool` is a list of `WorldRecordV1`. `limit` bounds total acceptances so a
    misconfigured spec cannot run forever.
    """
    for rec in pool:
        R.validate_record_v1(rec)
    # The binding gate. A record whose `sem-` was inherited from a publisher
    # rather than re-lowered here is `asserted`, and a benchmark built on those
    # is measuring the publisher. Excluded records are COUNTED, not quietly
    # dropped: a pool that halved on the way in and a pool that was always small
    # produce the same corpus and call for opposite responses.
    admitted = [r for r in pool
                if r["binding"]["kind"] in spec.allowed_binding_kinds]
    if not admitted:
        fail(WRLM_GENERATOR_EXHAUSTED,
             "no record in a pool of %d carries a binding in %s; every world "
             "here is trusted rather than proved"
             % (len(pool), list(spec.allowed_binding_kinds)), "pool")
    excluded = len(pool) - len(admitted)
    pool = admitted

    cells = cells or F.valid_cells()
    ledger = C.CoverageLedger(spec)
    ledger.pool_admitted = len(admitted)
    ledger.pool_excluded = excluded
    views = _views(pool)
    corpus, stalled = [], set()

    while len(corpus) < limit:
        live = [c for c in cells
                if ledger.deficit(c) > 0 and C.cell_key(c) not in stalled]
        if not live:
            break
        part = C.select_partition(ledger, live)
        cell = C.select_cell(ledger, live, part)
        if cell is None:
            break

        chosen = None
        for attempt in range(MAX_ATTEMPTS_PER_CELL):
            survivors, outcomes = generate_batch(ledger, cell, pool, attempt,
                                                 views)
            # A batch keeps up to BATCH survivors and exactly one is accepted.
            # The rest passed every gate and simply lost, which is neither an
            # acceptance nor a rejection -- and leaving it as neither is what
            # broke `proposed == sum(outcomes)`. `accepted_unique` is booked by
            # `ledger.accept` below, so only the losers are booked here.
            outcomes["candidate_not_selected"] += max(len(survivors) - 1, 0)
            for name, n in outcomes.items():
                for _ in range(n):
                    ledger.record(cell, name)
            if survivors:
                # Phase 5: the survivor that ILLUMINATES the most -- new marginal
                # values plus new pairs -- rather than merely the first that fit.
                # Which properties are chosen to describe diversity is what
                # decides which regions of the space get built at all.
                chosen = max(survivors,
                             key=lambda c: (ledger.coverage_gain(c.factors),
                                            [-ord(x) for x in c.case]))
                break
        if chosen is None:
            ledger.record(cell, "attempt_bound_exhausted")
            stalled.add(C.cell_key(cell))
            continue

        ledger.accept(cell, chosen.case, chosen.factors,
                      chosen.task["base_world"]["semantic_id"])
        corpus.append({"task": chosen.task, "case_id": chosen.case,
                       "task_id": T.task_bundle_id(chosen.task),
                       "cell": chosen.cell, "witness": chosen.witness,
                       "factors": chosen.factors})
    # Every proposal ended somewhere with a name, or this raises. Checked at the
    # end of the run rather than trusted, for the same reason the cell is derived
    # rather than declared.
    ledger.check_accounting()
    return corpus, ledger


def split_assignment(corpus, spec, ratios=(0.7, 0.15, 0.15)):
    """train / validation / test, assigned on `base_shape_id`.

    NOT on `case-`, and not on `sem-`. Splitting by case lets a world and its own
    relabelling land on opposite sides, which is contamination with extra steps:
    the test item is structurally identical to something already trained on, and
    the score it produces is inflated by exactly the amount nobody can measure.
    Shape blocking closes that, and because the fingerprint over-merges rather
    than under-merges, its errors cost coverage instead of leaking answers.
    """
    shapes = sorted({c["factors"]["base_shape_id"] for c in corpus})
    order = sorted(shapes, key=lambda s: hashlib.sha256(
        (spec.corpus_seed + "|split|" + s).encode()).hexdigest())
    n = len(order)
    n_tr = int(n * ratios[0])
    n_va = int(n * (ratios[0] + ratios[1]))
    where = {}
    for i, s in enumerate(order):
        where[s] = "train" if i < n_tr else ("validation" if i < n_va else "test")
    out = {"train": [], "validation": [], "test": []}
    for item in corpus:
        out[where[item["factors"]["base_shape_id"]]].append(item)
    return out
