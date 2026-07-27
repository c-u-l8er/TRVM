"""The two task families, and the rule that a cell is DERIVED, never declared.

Step 2 ships exactly two families:

    target_transform     reach the world with this `sem-`
    goal_satisfaction    make this GoalSpecV1 true

Repair is not here. `WorldRecordV1` admits only sealed valid worlds, so a task
whose base is broken WRL cannot be honestly expressed as a `TaskBundleV1` at all;
it gets its own object when its turn comes rather than a borrowed `sem-` now.

The rule this module exists to enforce
--------------------------------------

A generator that *labels* its output has marked its own homework. So every
coordinate of the primary cell -- tier included -- is **derived from the produced
task and its base world, then compared with the cell that was requested**. A
candidate whose derived cell disagrees is rejected, not relabelled. It is the
same discipline as the identity ladder: `sem-`, `goal-`, `task-`, `case-` are all
recomputed rather than trusted, and a coverage coordinate is no different. A
cell that could be asserted would be a cell that could be faked, and a faked cell
is a silently mis-shaped training distribution.

Witnesses
---------

A witness is a list of pure operations mirroring the engine's edit algebra::

    {"op": "AddObject",       "object": {...},           "touches": [id]}
    {"op": "RemoveObject",    "target": id,              "touches": [id]}
    {"op": "AddEdge",         "edge": {src, dst, kind},  "touches": [src, dst]}
    {"op": "RemoveEdge",      "edge": {src, dst, kind},  "touches": [src, dst]}
    {"op": "SetObjectConfig", "target": id, "static_config": {...},
                                                         "touches": [id]}

They are simulated over a `WorldViewV1` with no engine present. That is possible
because the *view* -- objects and edges -- is trivially computable, while the
thing that genuinely needs an engine is deciding whether the result is legal WRL
and what its `sem-` would be. The generator never needs to answer that: for
`target_transform` the target is another already-captured record and therefore
already sealed, and for `goal_satisfaction` the goal is evaluated on the view.

This is why generation stays offline. The engine is needed to fill the pool,
once. It is never needed to build a task out of one.

`witness_edit_budget` is the length of this constructive witness. It is not
minimal, is not claimed to be, and is not named as if it were.
"""

import copy
import itertools

from . import coverage as C
from . import goalspec as G
from .errors import WrlmError, fail

FAMILY_TARGET_TRANSFORM = "target_transform"
FAMILY_GOAL_SATISFACTION = "goal_satisfaction"
FAMILIES = (FAMILY_TARGET_TRANSFORM, FAMILY_GOAL_SATISFACTION)

WRLM_BAD_FAMILY = "WRLM_BAD_FAMILY"          # unknown family / invalid cell domain
WRLM_BAD_WITNESS = "WRLM_BAD_WITNESS"        # witness does not do what it claims
WRLM_CELL_MISMATCH = "WRLM_CELL_MISMATCH"    # derived cell != requested cell
# The step was legal on its own terms and still produced a world no engine would
# seal. It has its own code because it is the gate where this simulator is
# deliberately STRICTER than the engine, and a battery that cannot tell which of
# the two gates fired is not testing the split between them.
WRLM_WITNESS_NOT_CLOSED = "WRLM_WITNESS_NOT_CLOSED"

# Each family publishes its own objective-shape vocabulary. Crossing them --
# `target_transform` + `atomic_count` -- is not a sparse cell, it is a
# meaningless one, and the cell domain has to say so rather than let the ledger
# spend forever failing to fill it.
OBJECTIVE_SHAPES = {
    FAMILY_TARGET_TRANSFORM: ("local", "multi_local", "structural",
                              "preservation"),
    FAMILY_GOAL_SATISFACTION: ("atomic_count", "conjunction", "alternative",
                               "negated_constraint"),
}

# The longest witness the coverage domain can even bucket. Owned by the bucket
# table rather than restated as a literal: two numbers that must agree are two
# numbers that can disagree, and this one drifting upward would silently create
# witnesses whose budget bucket cannot be computed.
MAX_WITNESS = C.WITNESS_BUDGET_BUCKETS[-1][2]


# ------------------------------------------------------------------ witnesses
def _touches(op):
    if op["op"] in ("AddObject",):
        return [op["object"]["object_id"]]
    if op["op"] in ("RemoveObject", "SetObjectConfig"):
        return [op["target"]]
    return [op["edge"]["src"], op["edge"]["dst"]]


def op_add_object(object_id, role, static_config=None):
    o = {"object_id": object_id, "role": role,
         "static_config": dict(static_config or {})}
    return {"op": "AddObject", "object": o, "touches": [object_id]}


def op_remove_object(object_id):
    return {"op": "RemoveObject", "target": object_id, "touches": [object_id]}


def op_add_edge(src, dst, kind):
    return {"op": "AddEdge", "edge": {"src": src, "dst": dst, "kind": kind},
            "touches": [src, dst]}


def op_remove_edge(src, dst, kind):
    return {"op": "RemoveEdge", "edge": {"src": src, "dst": dst, "kind": kind},
            "touches": [src, dst]}


def op_set_config(object_id, static_config):
    return {"op": "SetObjectConfig", "target": object_id,
            "static_config": dict(static_config), "touches": [object_id]}


def _canon_view(objects, edges):
    return {"objects": [objects[k] for k in sorted(objects)],
            "edges": sorted(edges, key=lambda e: (e["src"], e["dst"],
                                                  e["kind"]))}


def check_view_closed(view, path="world"):
    """Every edge names an object that exists.

    Applied to the BASE as well as to each step, so that an unclosed starting
    world is named as such instead of being reported as the first edit's fault.
    A sealed `WorldRecordV1` always passes; the check is here because "always"
    is a claim, and an unchecked claim is how the crossed-source hole got in.
    """
    have = {o.get("object_id") for o in view.get("objects") or []}
    dangling = sorted({x for e in view.get("edges") or []
                       for x in (e.get("src"), e.get("dst")) if x not in have})
    if dangling:
        fail(WRLM_WITNESS_NOT_CLOSED,
             "%s names no object; the engine's seal refuses such a world with "
             "WRL_UNKNOWN_ENDPOINT" % ", ".join(map(repr, dangling)), path)
    return view


def apply_witness_step(view, op, path="witness"):
    """One edit, applied to a view. Pure; no engine, no identity.

    TWO gates, in this order.

    **1. The operation's own precondition.** Exactly what the engine's
    `wrl_draft._apply_operation` enforces, operation for operation, no more and
    no less::

        AddObject         the id must not already be an object
        RemoveObject      the target must be an object
        SetObjectConfig   the target must be an object
        AddEdge           the edge must not already be present
        RemoveEdge        the edge must be present

    That parity is the point of this list. If this simulator refused something
    the engine allows, the generator would leave reachable tasks unbuilt and
    report it as a pool shortage; if it allowed something the engine refuses, it
    would mint tasks whose stated solution is not a world.

    **2. Referential closure of the world the step produces.** Every edge must
    name objects that exist.

    Gate 2 is where this deliberately DIVERGES from the engine, and the
    divergence is worth stating rather than burying. Forge's `RemoveObject` is
    *non-cascading* and its `AddEdge` does not look at endpoints -- both let a
    draft hold a dangling edge, and it is the SEAL, later, that refuses the
    finished world with `WRL_UNKNOWN_ENDPOINT`. WRLM has no seal offline. So the
    choice is between simulating a permissive engine and being unable to tell
    which results it would go on to reject, or being stricter here in the
    direction that can only cost coverage. Strictly-stricter is the safe side,
    and it is named as such: this refuses some witnesses Forge's *draft* layer
    would apply, and it never proposes one Forge's *seal* would refuse.

    Checking closure after EVERY step rather than only at the end is the second
    deliberate choice, and it is the load-bearing one. If only the endpoint were
    judged, a witness would be a SET rather than a sequence, every permutation of
    it would be equally good, and `ordering_required` would be true of almost
    nothing -- which would quietly hollow out tier 3 while every test still
    passed.

    What this does NOT check: role registries, port signatures, controller
    conflicts, clock ranges. Those are seal rules that need the engine's
    vocabulary, and encoding a copy of them here would be a second statement of
    the world contract, free to drift from the first. A witness that satisfies
    both gates here can still be refused by the seal for one of those reasons;
    what it cannot do is be refused for a reason this layer could have seen.
    """
    objects = {o["object_id"]: copy.deepcopy(o)
               for o in view.get("objects") or []}
    edges = [dict(e) for e in view.get("edges") or []]
    kind = (op or {}).get("op")

    if kind == "AddObject":
        oid = op["object"]["object_id"]
        if oid in objects:
            fail(WRLM_BAD_WITNESS, "AddObject %r already exists" % oid, path)
        objects[oid] = copy.deepcopy(op["object"])
    elif kind == "RemoveObject":
        if op["target"] not in objects:
            fail(WRLM_BAD_WITNESS, "RemoveObject %r does not exist"
                 % op["target"], path)
        del objects[op["target"]]
    elif kind == "SetObjectConfig":
        if op["target"] not in objects:
            fail(WRLM_BAD_WITNESS, "SetObjectConfig on missing %r"
                 % op["target"], path)
        objects[op["target"]]["static_config"] = dict(op["static_config"])
    elif kind == "AddEdge":
        e = dict(op["edge"])
        if e in edges:
            fail(WRLM_BAD_WITNESS, "AddEdge duplicates an existing edge", path)
        edges.append(e)
    elif kind == "RemoveEdge":
        e = dict(op["edge"])
        if e not in edges:
            fail(WRLM_BAD_WITNESS, "RemoveEdge names no existing edge", path)
        edges.remove(e)
    else:
        fail(WRLM_BAD_WITNESS, "unknown operation %r" % (kind,), path)

    return check_view_closed(_canon_view(objects, edges), path)


def apply_witness(view, witness):
    """Fold a whole witness over a view, step by step.

    The result deliberately carries NO `semantic_id`. Inventing one would mean
    guessing what the engine's canonicalisation produces, and a guessed `sem-` is
    precisely the counterfeit the whole ladder is built to make impossible. The
    simulated world is a structure, and it is only ever compared as one.
    """
    out = check_view_closed(
        _canon_view({o["object_id"]: copy.deepcopy(o)
                     for o in view.get("objects") or []},
                    [dict(e) for e in view.get("edges") or []]), "base_world")
    for i, op in enumerate(witness or []):
        out = apply_witness_step(out, op, "witness.%d" % i)
    return out


def _norm(view):
    return {"objects": sorted([{"object_id": o.get("object_id"),
                                "role": o.get("role"),
                                "static_config": o.get("static_config") or {}}
                               for o in view.get("objects") or []],
                              key=lambda o: o["object_id"]),
            "edges": sorted([{"src": e.get("src"), "dst": e.get("dst"),
                              "kind": e.get("kind")}
                             for e in view.get("edges") or []],
                            key=lambda e: (e["src"], e["dst"], e["kind"]))}


def diff_witness(base_view, target_view):
    """A constructive witness taking `base_view` to `target_view`.

    Removals before additions, so that an id can be retyped by remove-then-add
    without the two colliding. Edges out before objects out, and objects in
    before edges in, so that the sequence is executable rather than merely
    describing an endpoint.

    An edge is taken out if the target does not want it **or if either of its
    endpoints is being removed** -- including an endpoint that is immediately put
    back with a different role. Those edges are then put back at the end, because
    the additions are computed against the edges that actually SURVIVED rather
    than against the base. Retyping a wired object is the case that forces this:
    the edge is in both worlds, so a plain set difference leaves it alone, and
    `RemoveObject` then strands it. That produced a witness which described the
    right endpoint and could not be executed -- readable as a diff, refused as a
    sequence.

    Not minimal. Never called minimal.
    """
    b, t = _norm(base_view), _norm(target_view)
    bo = {o["object_id"]: o for o in b["objects"]}
    to = {o["object_id"]: o for o in t["objects"]}
    be = [tuple(sorted(e.items())) for e in b["edges"]]
    te = [tuple(sorted(e.items())) for e in t["edges"]]

    drop_obj = [k for k in sorted(bo) if k not in to
                or bo[k]["role"] != to[k]["role"]]
    add_obj = [k for k in sorted(to) if k not in bo
               or bo[k]["role"] != to[k]["role"]]
    cfg_obj = [k for k in sorted(to)
               if k in bo and bo[k]["role"] == to[k]["role"]
               and bo[k]["static_config"] != to[k]["static_config"]]

    uprooted = set(drop_obj) | set(add_obj)

    def _incident(e):
        d = dict(e)
        return d["src"] in uprooted or d["dst"] in uprooted

    edges_out = sorted([e for e in be if e not in te or _incident(e)])
    surviving = set(be) - set(edges_out)
    edges_in = sorted(set(te) - surviving)

    ops = []
    for e in edges_out:
        d = dict(e)
        ops.append(op_remove_edge(d["src"], d["dst"], d["kind"]))
    for k in drop_obj:
        ops.append(op_remove_object(k))
    for k in add_obj:
        ops.append(op_add_object(k, to[k]["role"], to[k]["static_config"]))
    for k in cfg_obj:
        ops.append(op_set_config(k, to[k]["static_config"]))
    for e in edges_in:
        d = dict(e)
        ops.append(op_add_edge(d["src"], d["dst"], d["kind"]))
    return ops


def verify_witness(base_view, witness, target_view):
    """Does this witness actually land on that world? Checked, not assumed."""
    got = _norm(apply_witness(base_view, witness))
    want = _norm(target_view)
    if got != want:
        fail(WRLM_BAD_WITNESS,
             "the witness does not reach the target world; a task whose "
             "reachability was never checked is a task nobody knows is solvable",
             "witness")
    return witness


# ----------------------------------------------------------- derived tier
def derive_tier(goal, witness, preservation=False):
    """The tier CONTRACT, computed from the task rather than asserted about it.

      tier 1  one requirement, one edit is enough
      tier 2  several requirements or several edits, order does not matter
      tier 3  ordering matters, or something must be PRESERVED while changing

    Tier 3 is the one that carries real content, so it is defined by the two
    things that actually make a transformation hard to reason about -- a step
    that cannot be taken until another has been, and a property that must survive
    the change -- rather than by size.
    """
    n = len(witness or [])
    conj = 1
    if isinstance(goal, dict) and goal.get("kind") in ("all", "any"):
        conj = len(goal.get("args") or [])
    if preservation or C.ordering_required(witness):
        return 3
    if n >= 2 or conj >= 2:
        return 2
    return 1


def derive_objective_shape(family, goal, witness, preservation=False):
    if family == FAMILY_TARGET_TRANSFORM:
        if preservation:
            return "preservation"
        if C.ordering_required(witness):
            return "structural"
        return "multi_local" if len(witness or []) >= 2 else "local"
    if family == FAMILY_GOAL_SATISFACTION:
        root = (goal or {}).get("kind")
        if root == "not":
            return "negated_constraint"
        if root == "any":
            return "alternative"
        if root == "all":
            args = goal.get("args") or []
            if any(a.get("kind") == "not" for a in args):
                return "negated_constraint"
            return "conjunction"
        # a bare `count`; `n == 0` is a prohibition, which is a different thing
        # to ask than a requirement even though the AST node is the same
        if root == "count" and goal.get("cmp") == "eq" and goal.get("n") == 0:
            return "negated_constraint"
        return "atomic_count"
    fail(WRLM_BAD_FAMILY, "unknown family %r" % (family,), "family")


def presentation_form_of(task, record):
    """Which text was actually presented -- read off the TASK and the RECORD.

    Derived rather than remembered. The generator knows which string it chose,
    but a generator's memory of its own intent is exactly the kind of claim this
    module refuses to accept: the task carries the bytes, so the bytes decide.
    """
    src = task["base_world"]["source"]
    fmt = record.get("formatted_source")
    if fmt and src == fmt and src != record["source"]:
        return "formatted"
    return "source"


def derive_cell(family, base_view, task, witness, record, preservation=False):
    """The whole primary cell, derived. Nothing here reads a declared label."""
    goal = task["objective"]["goal"]
    n_obj = len(base_view.get("objects") or [])
    return C.make_cell(
        family=family,
        tier=derive_tier(goal, witness, preservation),
        base_size_bucket=C.size_bucket(n_obj),
        objective_shape=derive_objective_shape(family, goal, witness,
                                               preservation),
        witness_edit_budget=C.witness_budget_bucket(len(witness or [])),
        presentation_form=presentation_form_of(task, record))


def check_cell(requested, derived):
    if C.cell_key(requested) != C.cell_key(derived):
        fail(WRLM_CELL_MISMATCH,
             "this candidate is a %s, not the %s that was requested; a cell "
             "that could be asserted would be a cell that could be faked"
             % (C.cell_key(derived), C.cell_key(requested)), "cell")
    return derived


# ------------------------------------------- the domain, derived and not listed
#
# Publishing a cell nothing can inhabit is the defect the ruling already named
# about cross-family shapes -- "not a sparse cell, a meaningless one" -- one level
# further down. `local` MEANS one edit with nothing preserved and nothing ordered,
# and `derive_tier` calls exactly that combination tier 1. So `local x tier 3` is
# not a hard cell, it is a contradiction; a ledger that publishes it spends its
# whole attempt budget failing to fill it and then reports the result as
# under-coverage, which points at the pool for a fault that is in the domain.
#
# The reachable set is therefore COMPUTED, by running the two derivation
# functions over each family's own (goal, preservation) domain against real
# witnesses -- not written down as a table. A table would be a second statement
# of the tier contract, free to drift from the first. This one cannot drift,
# because it is not a second statement: it is the first one, called.


def _probe_witness(n, ordering):
    """A witness of length `n` whose `ordering_required` really is `ordering`.

    Realised, never asserted. `ordering_required` reads the ops, so the only
    honest way to enumerate its True branch is to build a witness that has an
    edge op naming an object another op brings into existence. `None` means the
    request is not a witness at all: one edit cannot depend on another.
    """
    if n < 1 or (ordering and n < 2):
        return None
    if not ordering:
        return [op_set_config("probe%d" % i, {"probe": i}) for i in range(n)]
    ops = [op_add_object("probe_new", "Door", {}),
           op_add_edge("probe_src", "probe_new", "SignalWire")]
    return ops + [op_set_config("probe%d" % i, {"probe": i})
                  for i in range(n - 2)]


def _goal_domain(family):
    """Every (goal, preservation) shape this family's contract admits.

    `target_transform` asks for a WORLD, so it carries no goal at all -- unless a
    preservation clause pins something that has to survive the move, and that
    clause is a single count. It never carries a conjunction. Sweeping every goal
    against every family therefore over-reports reachability: it would call
    `target_transform x tier 2 x local` live on the strength of a two-armed goal
    that family never emits.
    """
    one = G.exactly("objects", G.role("Door"), 1)
    if family == FAMILY_TARGET_TRANSFORM:
        return [(None, False), (one, True)]
    if family == FAMILY_GOAL_SATISFACTION:
        nope = {"kind": "not", "arg": one}
        return [(one, False),
                (G.none("objects", G.role("Door")), False),
                (nope, False),
                ({"kind": "all", "args": [one, one]}, False),
                ({"kind": "all", "args": [one, nope]}, False),
                ({"kind": "any", "args": [one, one]}, False),
                (G.wired("SignalWire", G.role("Pulser"),
                         {"kind": "id_is", "object_id": "d0"}), False)]
    fail(WRLM_BAD_FAMILY, "unknown family %r" % (family,), "family")


_FEASIBLE = {}


def feasible_triples(family):
    """The `(tier, objective_shape, witness_edit_budget)` triples with a preimage.

    Pure and memoised: the derivation functions read nothing outside their
    arguments, so this enumeration is a fact about the code rather than a sample
    of it.
    """
    if family not in _FEASIBLE:
        out = set()
        for goal, pres in _goal_domain(family):
            for n in range(1, C.WITNESS_BUDGET_BUCKETS[-1][2] + 1):
                for ordering in (False, True):
                    w = _probe_witness(n, ordering)
                    if w is None:
                        continue
                    if C.ordering_required(w) != ordering:
                        # A probe that does not have the property it was built
                        # to have would silently shrink the published domain,
                        # and a domain that quietly loses cells is worse than
                        # one that loudly refuses to be computed.
                        fail(WRLM_BAD_WITNESS,
                             "probe witness of %d ops does not realise "
                             "ordering=%r" % (n, ordering), "witness")
                    out.add((derive_tier(goal, w, pres),
                             derive_objective_shape(family, goal, w, pres),
                             C.witness_budget_bucket(n)))
        _FEASIBLE[family] = frozenset(out)
    return _FEASIBLE[family]


def cell_in_domain(cell):
    """Can any task at all land in this cell?"""
    if cell["objective_shape"] not in OBJECTIVE_SHAPES.get(cell["family"], ()):
        return False
    return (cell["tier"], cell["objective_shape"],
            cell["witness_edit_budget"]) in feasible_triples(cell["family"])


def check_cell_in_domain(cell):
    if not cell_in_domain(cell):
        fail(C.WRLM_CELL_UNKNOWN,
             "no task can inhabit %s: tier, objective shape and witness budget "
             "are jointly underivable, so an empty count here would measure the "
             "domain rather than the corpus" % C.cell_key(cell), "cell")
    return cell


def valid_cells(spec_families=FAMILIES):
    """The valid cell domain: family x tier x size x SHAPE-OF-THAT-FAMILY x
    budget x presentation, restricted to the combinations something can produce.

    Cross-family shapes never appear, and neither do the contradictory ones.
    """
    out = []
    for fam in spec_families:
        for tier in C.TIERS:
            for size, _lo, _hi in C.SIZE_BUCKETS:
                for shape in OBJECTIVE_SHAPES[fam]:
                    for budget, _b1, _b2 in C.WITNESS_BUDGET_BUCKETS:
                        for pres in C.PRESENTATION_FORMS:
                            cell = C.make_cell(fam, tier, size, shape,
                                               budget, pres)
                            if cell_in_domain(cell):
                                out.append(cell)
    return out


# ------------------------------------------------------------ goal proposals
def _cfg_variant(cfg):
    """A different-but-plausible config for the same role."""
    out = dict(cfg or {})
    clock = out.get("clock")
    if isinstance(clock, list) and clock and clock[0] == "periodic":
        out["clock"] = ["periodic", int(clock[1]) + 1, clock[2]
                        if len(clock) > 2 else 0]
    return out


def _fresh_ids(view, n, tag="gx"):
    """`n` object ids this world does not already use.

    Derived from the world rather than counted off its size: `"gx%d" % (len+1)`
    collides the moment a world happens to contain a `gx` id, and an `AddObject`
    that collides is refused by the precondition gate -- which would show up as a
    generator that mysteriously cannot fill a cell rather than as a name clash.
    """
    have = {o["object_id"] for o in view.get("objects") or []}
    out, i = [], 0
    while len(out) < n:
        cid = "%s%d" % (tag, i)
        i += 1
        if cid not in have:
            out.append(cid)
    return out


def _subsequences(seq):
    """Every proper subsequence, order preserved, longest first."""
    n = len(seq)
    for size in range(n - 1, -1, -1):
        for idx in itertools.combinations(range(n), size):
            yield [seq[i] for i in idx]


def witness_is_minimal(view, goal, witness):
    """Does every edit in this witness earn its place?

    True when NO proper subsequence of the witness already satisfies the goal.

    This is the executable form of "widen the repertoire without padding
    witnesses". The cheap way to reach a `5-8` budget cell is to append edits a
    goal does not need; the cell then fills, the ledger reports depth, and the
    task is a one-edit problem wearing a six-edit costume. Stating in a docstring
    that the proposer does not do that is worth nothing -- the proposer is the
    thing under suspicion. So the claim is CHECKED, against the same evaluator
    the generator scores with, over the same edit algebra the engine uses.

    Subsequences rather than subsets: a witness is a sequence, and the ordered
    ones only apply in their own order. A subsequence that cannot be applied at
    all is not a cheaper solution, so it is simply skipped -- the closure gate
    refusing it IS the reason the dropped edit was necessary.

    Bounded by `MAX_WITNESS`, so this is at most 2**8 evaluations per witness.
    """
    if not witness:
        return False
    for sub in _subsequences(witness):
        try:
            reached = apply_witness(view, sub)
        except WrlmError:
            continue
        if G.evaluate_goal(goal, reached):
            return False
    return True


def propose_goals(view, rng):
    """Candidate goals for `goal_satisfaction`, paired with a witness.

    Each proposal is a `(goal, witness)` pair, because a goal without a
    constructive witness is only a wish: nobody has shown the world can be moved
    to satisfy it. Unsatisfiable goals are the quietest possible way to poison a
    reward signal -- every attempt fails, the model is trained against its own
    correct behaviour -- so a goal with no witness never becomes a task.

    THE REPERTOIRE IS THE LIMIT, AND IT WAS MEASURED.

    The first version of this function emitted six rules and reached 8 of the 29
    `(tier, objective_shape, witness_edit_budget)` triples the family's own
    domain admits. That is why `goal_satisfaction` saturated at every pool size:
    the missing cells were not scarce, they were UNREACHABLE from this list, and
    a bigger pool of worlds cannot supply a goal shape nobody wrote down. The
    scaling curve said "repertoire-limited" and this is the repertoire.

    Each rule below therefore exists to reach a named region, and the regions
    were chosen from the gap, not from taste:

      A  k more of a role                atomic_count, unordered, budgets 1..8
      B  k fewer of a role               atomic_count / negated_constraint;
                                         ORDERED whenever a victim is wired
      C  two counts at once              conjunction, unordered, budgets 1..8
      D  new objects, each wired         conjunction, ORDERED, budgets 2..8
      E  more edges of a kind            atomic_count, ORDERED, budgets 2..8
      F  the cheap arm costs k           alternative, unordered, budgets 1..8
      G  the cheap arm is a wiring       alternative, ORDERED, budgets 2..8
      H  a prohibition plus a count      negated_constraint, unordered, 1..8

    The ORDERED rules all get their ordering the same honest way: an edge cannot
    name an object that does not exist yet (rules D, E, G), and an object cannot
    be removed while an edge still names it (rule B). Neither is a trick played
    on `ordering_required` -- both are refusals the engine's own seal would
    make, and `apply_witness_step` enforces them, so a witness that claims tier 3
    has to survive execution in that order to be proposed at all.

    What none of them do is reach a budget by adding edits the goal does not
    need. `witness_is_minimal` checks that, by execution, and the battery runs it
    over every proposal this function emits.
    """
    objects = list(view.get("objects") or [])
    edges = list(view.get("edges") or [])
    roles = sorted({o["role"] for o in objects})
    counts = {r: sum(1 for o in objects if o["role"] == r) for r in roles}
    absent = [r for r in G.ROLE_IDS if r not in counts]
    out = []
    if not objects:
        return out

    # The four widths that hit all four budget buckets: 1 -> "1", 2 -> "2",
    # 3 -> "3-4", 5 -> "5-8". Written as the widths rather than as the bucket
    # names because the proposer builds EDITS; the bucket is derived from how
    # many there turned out to be, and that direction is the whole discipline.
    WIDTHS = (1, 2, 3, 5)

    # -- A. k more of some role. The plainest count goal there is; k AddObjects
    #       of distinct ids write disjoint state, so this is never ordered.
    for r in roles:
        for k in WIDTHS:
            ids = _fresh_ids(view, k)
            out.append((G.exactly("objects", G.role(r), counts[r] + k),
                        [op_add_object(i, r, {}) for i in ids]))

    # -- B. k fewer of some role. The demolition direction, and the one that
    #       forces reading the whole world instead of pattern-matching a name:
    #       every edge touching a victim has to come out first, so the witness
    #       is ordered exactly when the victims were wired. When k takes the
    #       role to zero the goal is `count == 0`, which is a prohibition and
    #       derives as `negated_constraint` -- a different question to ask than
    #       "how many", even though it is the same AST node.
    for r in roles:
        victims_all = [o["object_id"] for o in objects if o["role"] == r]
        for k in (1, 2, 3):
            if k > len(victims_all):
                break
            victims = victims_all[:k]
            wit = [op_remove_edge(e["src"], e["dst"], e["kind"]) for e in edges
                   if e["src"] in victims or e["dst"] in victims]
            wit += [op_remove_object(v) for v in victims]
            if not (1 <= len(wit) <= MAX_WITNESS):
                continue
            out.append((G.exactly("objects", G.role(r), counts[r] - k), wit))

    # -- C. two counts at once. `(1, 0)` is the case worth naming: one arm has
    #       to MOVE and the other has to HOLD, so the goal has two requirements
    #       and the witness has one edit. That combination -- a conjunction at
    #       budget 1 -- was unreachable before, and it is the cheapest possible
    #       statement of "change this without breaking that".
    if len(roles) >= 2:
        a, b = roles[0], roles[1]
        for ka, kb in ((1, 0), (1, 1), (2, 1), (2, 2), (3, 2)):
            ids = _fresh_ids(view, ka + kb)
            out.append(({"kind": "all", "args": [
                G.exactly("objects", G.role(a), counts[a] + ka),
                G.exactly("objects", G.role(b), counts[b] + kb)]},
                [op_add_object(i, a, {}) for i in ids[:ka]]
                + [op_add_object(i, b, {}) for i in ids[ka:]]))

    # -- D. new objects that must each be wired. Ordered by construction, and
    #       not by contrivance: `AddEdge` reads both endpoints, so the door has
    #       to exist before the wire can name it.
    pulsers = [o["object_id"] for o in objects if o["role"] == "Pulser"]
    n_wire = sum(1 for e in edges if e["kind"] == "SignalWire")
    edge_is_wire = {"kind": "edge_kind_is", "edge_kind": "SignalWire"}
    if pulsers:
        p = pulsers[0]
        for k in (1, 2, 3):
            ids = _fresh_ids(view, k)
            wit = []
            for i in ids:
                wit += [op_add_object(i, "Door", {}),
                        op_add_edge(p, i, "SignalWire")]
            args = [G.exactly("objects", G.role("Door"),
                              counts.get("Door", 0) + k)]
            args += [G.wired("SignalWire", G.role("Pulser"),
                             {"kind": "id_is", "object_id": i}) for i in ids]
            out.append(({"kind": "all", "args": args}, wit))

        # -- E. the same move asked as one count over the EDGE sort. Same
        #       ordering, different question: this one never mentions an object
        #       id, so it cannot be solved by matching names in the goal text.
        for k in (1, 2, 3):
            ids = _fresh_ids(view, k)
            wit = []
            for i in ids:
                wit += [op_add_object(i, "Door", {}),
                        op_add_edge(p, i, "SignalWire")]
            out.append((G.exactly("edges", edge_is_wire, n_wire + k), wit))

    # -- F. two ways to be right, with the cheap one costed. An `any` is only
    #       an alternative if both arms are live, and it only reaches a budget
    #       if the CHEAPER arm costs that much -- so the second arm is placed
    #       deliberately out of reach rather than made symmetric.
    if len(roles) >= 2:
        a, b = roles[0], roles[-1]
        for k in WIDTHS:
            ids = _fresh_ids(view, k)
            out.append(({"kind": "any", "args": [
                G.exactly("objects", G.role(a), counts[a] + k),
                G.exactly("objects", G.role(b), counts[b] + k + 4)]},
                [op_add_object(i, a, {}) for i in ids]))

    # -- G. an alternative whose cheap arm is a wiring, so choosing it commits
    #       to an ordered sequence. Reaches tier 3 without a preservation
    #       clause, which the `any` root cannot otherwise do.
    if pulsers and roles:
        p, far = pulsers[0], roles[0]
        for k in (1, 2, 3):
            ids = _fresh_ids(view, k)
            wit = []
            for i in ids:
                wit += [op_add_object(i, "Door", {}),
                        op_add_edge(p, i, "SignalWire")]
            arms = [G.wired("SignalWire", G.role("Pulser"),
                            {"kind": "id_is", "object_id": i}) for i in ids]
            cheap = arms[0] if k == 1 else {"kind": "all", "args": arms}
            out.append(({"kind": "any", "args": [
                cheap,
                G.exactly("objects", G.role(far), counts[far] + 20)]}, wit))

    # -- H. a prohibition carried alongside a requirement. The `not` arm costs
    #       nothing to satisfy and that is the point: it is the arm a solver can
    #       VIOLATE, and a goal that can only be failed by overreach is a
    #       different test from one that can only be failed by underreach.
    if absent and roles:
        z, a = absent[0], roles[0]
        for k in WIDTHS:
            ids = _fresh_ids(view, k)
            out.append(({"kind": "all", "args": [
                {"kind": "not", "arg": G.exists("objects", G.role(z))},
                G.exactly("objects", G.role(a), counts[a] + k)]},
                [op_add_object(i, a, {}) for i in ids]))

    rng.shuffle(out)
    return out
