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

from . import coverage as C
from . import goalspec as G
from .errors import fail

FAMILY_TARGET_TRANSFORM = "target_transform"
FAMILY_GOAL_SATISFACTION = "goal_satisfaction"
FAMILIES = (FAMILY_TARGET_TRANSFORM, FAMILY_GOAL_SATISFACTION)

WRLM_BAD_FAMILY = "WRLM_BAD_FAMILY"          # unknown family / invalid cell domain
WRLM_BAD_WITNESS = "WRLM_BAD_WITNESS"        # witness does not do what it claims
WRLM_CELL_MISMATCH = "WRLM_CELL_MISMATCH"    # derived cell != requested cell

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

MAX_WITNESS = 8


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


def apply_witness(view, witness):
    """Simulate a witness over a view. Pure; no engine, no identity.

    The result deliberately carries NO `semantic_id`. Inventing one would mean
    guessing what the engine's canonicalisation produces, and a guessed `sem-` is
    precisely the counterfeit the whole ladder is built to make impossible. The
    simulated world is a structure, and it is only ever compared as one.
    """
    objects = {o["object_id"]: copy.deepcopy(o) for o in view.get("objects") or []}
    edges = [dict(e) for e in view.get("edges") or []]
    for i, op in enumerate(witness or []):
        kind = op.get("op")
        if kind == "AddObject":
            oid = op["object"]["object_id"]
            if oid in objects:
                fail(WRLM_BAD_WITNESS, "AddObject %r already exists" % oid,
                     "witness.%d" % i)
            objects[oid] = copy.deepcopy(op["object"])
        elif kind == "RemoveObject":
            if op["target"] not in objects:
                fail(WRLM_BAD_WITNESS, "RemoveObject %r does not exist"
                     % op["target"], "witness.%d" % i)
            del objects[op["target"]]
        elif kind == "SetObjectConfig":
            if op["target"] not in objects:
                fail(WRLM_BAD_WITNESS, "SetObjectConfig on missing %r"
                     % op["target"], "witness.%d" % i)
            objects[op["target"]]["static_config"] = dict(op["static_config"])
        elif kind == "AddEdge":
            e = dict(op["edge"])
            if e in edges:
                fail(WRLM_BAD_WITNESS, "AddEdge duplicates an existing edge",
                     "witness.%d" % i)
            edges.append(e)
        elif kind == "RemoveEdge":
            e = dict(op["edge"])
            if e not in edges:
                fail(WRLM_BAD_WITNESS, "RemoveEdge names no existing edge",
                     "witness.%d" % i)
            edges.remove(e)
        else:
            fail(WRLM_BAD_WITNESS, "unknown operation %r" % (kind,),
                 "witness.%d" % i)
    return {"objects": [objects[k] for k in sorted(objects)],
            "edges": sorted(edges, key=lambda e: (e["src"], e["dst"],
                                                  e["kind"]))}


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

    ops = []
    for e in sorted(set(be) - set(te)):
        d = dict(e)
        ops.append(op_remove_edge(d["src"], d["dst"], d["kind"]))
    for k in drop_obj:
        ops.append(op_remove_object(k))
    for k in add_obj:
        ops.append(op_add_object(k, to[k]["role"], to[k]["static_config"]))
    for k in cfg_obj:
        ops.append(op_set_config(k, to[k]["static_config"]))
    for e in sorted(set(te) - set(be)):
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


def propose_goals(view, rng):
    """Candidate goals for `goal_satisfaction`, paired with a witness.

    Each proposal is a `(goal, witness)` pair, because a goal without a
    constructive witness is only a wish: nobody has shown the world can be moved
    to satisfy it. Unsatisfiable goals are the quietest possible way to poison a
    reward signal -- every attempt fails, the model is trained against its own
    correct behaviour -- so a goal with no witness never becomes a task.
    """
    objects = list(view.get("objects") or [])
    edges = list(view.get("edges") or [])
    roles = sorted({o["role"] for o in objects})
    out = []
    if not objects:
        return out

    fresh = "gx%d" % (len(objects) + 1)

    # 1. one more of some role: atomic_count, one AddObject
    for r in roles:
        have = sum(1 for o in objects if o["role"] == r)
        out.append((G.exactly("objects", G.role(r), have + 1),
                    [op_add_object(fresh, r, {})]))

    # 2. two more of some role: atomic_count, two AddObjects
    for r in roles[:2]:
        have = sum(1 for o in objects if o["role"] == r)
        out.append((G.exactly("objects", G.role(r), have + 2),
                    [op_add_object(fresh, r, {}),
                     op_add_object(fresh + "b", r, {})]))

    # 3. a conjunction over two roles
    if len(roles) >= 2:
        a, b = roles[0], roles[1]
        ha = sum(1 for o in objects if o["role"] == a)
        hb = sum(1 for o in objects if o["role"] == b)
        out.append(({"kind": "all", "args": [
            G.exactly("objects", G.role(a), ha + 1),
            G.exactly("objects", G.role(b), hb + 1)]},
            [op_add_object(fresh, a, {}), op_add_object(fresh + "b", b, {})]))

    # 4. an alternative -- either of two ways to be right
    if len(roles) >= 2:
        a, b = roles[0], roles[-1]
        ha = sum(1 for o in objects if o["role"] == a)
        hb = sum(1 for o in objects if o["role"] == b)
        out.append(({"kind": "any", "args": [
            G.exactly("objects", G.role(a), ha + 1),
            G.exactly("objects", G.role(b), hb + 1)]},
            [op_add_object(fresh, a, {})]))

    # 5. a prohibition: remove every instance of a role. This is the shape that
    #    forces reading the whole world instead of pattern-matching a name.
    for r in roles:
        victims = [o["object_id"] for o in objects if o["role"] == r]
        if not (1 <= len(victims) <= 3):
            continue
        wit = []
        for e in edges:
            if e["src"] in victims or e["dst"] in victims:
                wit.append(op_remove_edge(e["src"], e["dst"], e["kind"]))
        wit += [op_remove_object(v) for v in victims]
        out.append((G.none("objects", G.role(r)), wit))

    # 6. wire something new up: an edge-domain goal with a rewiring witness
    pulsers = [o["object_id"] for o in objects if o["role"] == "Pulser"]
    doors = [o["object_id"] for o in objects if o["role"] == "Door"]
    if pulsers and doors:
        p, d = pulsers[0], doors[-1]
        if not any(e["src"] == p and e["dst"] == d for e in edges):
            wit = [op_remove_edge(e["src"], e["dst"], e["kind"])
                   for e in edges if e["dst"] == d]
            wit.append(op_add_edge(p, d, "SignalWire"))
            out.append((G.wired("SignalWire", G.role("Pulser"),
                                {"kind": "id_is", "object_id": d}), wit))

    rng.shuffle(out)
    return out
