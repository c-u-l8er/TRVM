"""CoverageSpecV1 -- what "a diverse corpus" is allowed to mean.

A generator that maximises a coverage ledger will produce exactly the corpus the
ledger describes and nothing else. So the ledger is not bookkeeping; it is the
specification of the training distribution, written down where it can be argued
with. This module is that argument.

Three things it deliberately refuses to do
------------------------------------------

**`base_semantic_id` is not a coverage dimension.** One cell per world defines
identity diversity, not semantic diversity: two trivial renamings of the same
six-node topology land in different cells and look like progress, while one rich
world that could support twenty genuinely different tasks looks "full" after one.
`sem-` is still used here -- for reuse caps, for split blocking, for provenance --
but it never gets to say what diverse means.

**Declared `difficulty` is not a coverage dimension.** The generator owns that
label, so balancing on it is circular: relabel the tasks, watch the ledger go
green, change nothing about the actual population. `difficulty` stays on the task
as generator provenance. `tier` carries the ruled contract instead, because a
tier is *derived and checked*, not asserted.

**There is no one giant Cartesian cell.** Two families x three tiers x four sizes
x four objective shapes x four edit budgets x two presentations is already 768
cells before topology, roles, density or cycles are considered, and nearly all of
them would sit empty forever. Instead the policy is hierarchical: a small primary
cell the generator can deliberately aim at, plus a wide set of secondary factors
measured by *marginal and pairwise* coverage. That split is the standard
combinatorial-testing move -- low-order factor interactions as a tractable stand-in
for an unreachable full state space -- and it is what keeps "diverse" measurable
instead of aspirational.

Of those 768, **448 cannot be inhabited by anything**: `local` means one edit with
nothing preserved and nothing ordered, which `derive_tier` calls tier 1, so
`local x tier 3` is a contradiction rather than a hard cell. `families.valid_cells`
publishes only the 320 combinations that have a preimage, and it computes that set
by calling the derivation functions rather than by carrying a table of them. The
first version of this module published all 768 and then reported the 448 as
under-coverage -- which pointed at the pool for a fault that was in the domain.
Marginal coverage could not have caught it: every coordinate VALUE was reachable,
and only the COMBINATIONS were dead.

The primary cell
----------------

    (family, tier, base_size_bucket, objective_shape,
     witness_edit_budget, presentation_form)

Every coordinate is **derived from the produced task and its base world, then
compared against the cell that was requested**. A candidate whose derived cell
disagrees with the requested one is rejected, not relabelled. This is the same
rule the identity ladder runs on: nothing is believed because it was claimed.

On `witness_edit_budget`: it is the length of the generator's *constructive*
witness. It is not called `minimal_edit_distance`, because minimality has not
been proved and naming it as if it had would be the same species of overclaim
that put the crossed-source hole in `capture()`.

On `base_shape_id`
------------------

A renaming-invariant structural fingerprint, used for reuse caps and for
train/validation/test blocking so that a world and its own relabelling cannot end
up on opposite sides of a split.

It is computed by 1-WL colour refinement, and the guarantee that matters is
one-sided: **isomorphic worlds always agree; non-isomorphic worlds may also
agree.** Collisions therefore over-merge -- they force distinct worlds to share a
cap and share a split. Both are the safe direction. Under-merging would leak a
world's twin across a split boundary, and that is the failure this exists to
prevent.

It is emphatically **not** a rung on the identity ladder. It is prefixed
`shape-`, it derives no other id, and nothing is ever addressed by it.
"""

import hashlib
import json

from .errors import fail

# v1.1 narrowed the published cell domain from 768 to the combinations that have
# a preimage. The cell FIELDS are unchanged, so this is not a v2 -- but it is a
# version bump, because the version is what promises that a seed reproduces a
# corpus, and a corpus is drawn from a domain. Two different domains answering to
# one version string would make that promise quietly false.
#
# v1.2 rebuilt `ordering_required` on precondition/effect semantics and made the
# witness simulator refuse worlds the engine's seal would refuse. Neither change
# adds or removes a cell FIELD either, and the published domain came back the
# same size -- but the map from tasks INTO that domain moved, which is the same
# promise again. A seed that reproduced one corpus under v1.1 reproduces a
# different one here, and the version is what says so out loud.
COVERAGE_SPEC_VERSION = "wrlm.coverage.v1.2"

WRLM_BAD_COVERAGE = "WRLM_BAD_COVERAGE"    # malformed spec / cell / factor
WRLM_CELL_UNKNOWN = "WRLM_CELL_UNKNOWN"    # cell outside the family's domain

CELL_FIELDS = ("family", "tier", "base_size_bucket", "objective_shape",
               "witness_edit_budget", "presentation_form")

# ------------------------------------------------------------------- buckets
# Boundaries are policy, versioned with the spec. Size is in the primary cell
# because it moves both the prompt the model reads and the search space it has
# to reason over -- it is not a cosmetic property of the world.
SIZE_BUCKETS = (("tiny", 2, 4), ("small", 5, 8),
                ("medium", 9, 16), ("large", 17, 32))
WITNESS_BUDGET_BUCKETS = (("1", 1, 1), ("2", 2, 2),
                          ("3-4", 3, 4), ("5-8", 5, 8))
PRESENTATION_FORMS = ("source", "formatted")
TIERS = (1, 2, 3)


def _bucket(n, table, path):
    for name, lo, hi in table:
        if lo <= n <= hi:
            return name
    fail(WRLM_BAD_COVERAGE, "%s out of covered range: %r" % (path, n), path)


def size_bucket(n_objects):
    return _bucket(n_objects, SIZE_BUCKETS, "base_size_bucket")


def witness_budget_bucket(n_edits):
    return _bucket(n_edits, WITNESS_BUDGET_BUCKETS, "witness_edit_budget")


# ------------------------------------------------------------------- the cell
def make_cell(family, tier, base_size_bucket, objective_shape,
              witness_edit_budget, presentation_form):
    return {"family": family, "tier": tier,
            "base_size_bucket": base_size_bucket,
            "objective_shape": objective_shape,
            "witness_edit_budget": witness_edit_budget,
            "presentation_form": presentation_form}


def validate_cell_v1(cell):
    if not isinstance(cell, dict):
        fail(WRLM_BAD_COVERAGE, "cell must be an object, got %s"
             % type(cell).__name__, "cell")
    have, want = set(cell), set(CELL_FIELDS)
    if have != want:
        fail(WRLM_BAD_COVERAGE, "cell keys wrong: %s"
             % ", ".join(["+%s" % k for k in sorted(have - want)]
                         + ["-%s" % k for k in sorted(want - have)]), "cell")
    if cell["tier"] not in TIERS:
        fail(WRLM_BAD_COVERAGE, "tier must be one of %s, got %r"
             % (list(TIERS), cell["tier"]), "cell.tier")
    if cell["base_size_bucket"] not in [b[0] for b in SIZE_BUCKETS]:
        fail(WRLM_BAD_COVERAGE, "unknown size bucket %r"
             % (cell["base_size_bucket"],), "cell.base_size_bucket")
    if cell["witness_edit_budget"] not in [b[0] for b in WITNESS_BUDGET_BUCKETS]:
        fail(WRLM_BAD_COVERAGE, "unknown witness budget bucket %r"
             % (cell["witness_edit_budget"],), "cell.witness_edit_budget")
    if cell["presentation_form"] not in PRESENTATION_FORMS:
        fail(WRLM_BAD_COVERAGE, "unknown presentation form %r"
             % (cell["presentation_form"],), "cell.presentation_form")
    return cell


def cell_bytes(cell):
    return json.dumps(validate_cell_v1(cell), sort_keys=True,
                      separators=(",", ":")).encode()


def cell_key(cell):
    """A hashable key. Deliberately the canonical bytes rather than a tuple, so
    that adding a cell dimension later cannot silently alias old ledger keys
    onto new ones."""
    return cell_bytes(cell).decode()


# ------------------------------------------------------------- base_shape_id
def _init_colour(obj):
    """A node's starting colour: role plus the SHAPE of its configuration.

    Config *keys* participate; config *values* do not. A pulser firing every 2
    and a pulser firing every 3 are the same structure presented with different
    numbers, and treating them as different shapes would make the fingerprint
    finer -- which weakens exactly the property it exists for. Coarse merges
    over-block; fine splits leak."""
    cfg = obj.get("static_config") or {}
    keys = sorted(cfg) if isinstance(cfg, dict) else ["<malformed>"]
    return "%s|%s" % (obj.get("role"), ",".join(map(str, keys)))


def _h(s):
    return hashlib.sha256(s.encode("utf-8")).hexdigest()[:16]


def base_shape_id(view):
    """`shape-<hex>`: a 1-WL fingerprint that ignores object names.

    NOT an identity rung, NOT an isomorphism certificate. See the module
    docstring for the one-sided guarantee and why that direction is the safe one.
    """
    objects = view.get("objects") or []
    edges = view.get("edges") or []
    colour = {}
    for o in objects:
        colour[o.get("object_id")] = _init_colour(o)

    # Colour refinement stabilises within |V| rounds, so |V| rounds is enough
    # and there is no reason to iterate to a fixed point separately.
    for _ in range(len(objects)):
        nxt = {}
        for oid, c in colour.items():
            nbr = []
            for e in edges:
                if e.get("src") == oid:
                    nbr.append("o|%s|%s" % (e.get("kind"),
                                            colour.get(e.get("dst"), "?")))
                if e.get("dst") == oid:
                    nbr.append("i|%s|%s" % (e.get("kind"),
                                            colour.get(e.get("src"), "?")))
            nxt[oid] = _h(c + "#" + "&".join(sorted(nbr)))
        if nxt == colour:
            break
        colour = nxt

    body = json.dumps({"n": len(objects), "m": len(edges),
                       "colours": sorted(colour.values())},
                      sort_keys=True, separators=(",", ":"))
    return "shape-" + hashlib.sha256(body.encode()).hexdigest()[:32]


# ------------------------------------------------------- secondary factors
def _b(n, cuts, names):
    for c, name in zip(cuts, names):
        if n <= c:
            return name
    return names[-1]


def world_factors(view):
    """Structural properties of the base world, measured not declared."""
    objects = view.get("objects") or []
    edges = view.get("edges") or []
    n = max(len(objects), 1)
    roles = sorted({o.get("role") for o in objects})
    kinds = sorted({e.get("kind") for e in edges})

    deg = {}
    for e in edges:
        deg[e.get("src")] = deg.get(e.get("src"), 0) + 1
        deg[e.get("dst")] = deg.get(e.get("dst"), 0) + 1

    # undirected connectivity: components as a plain union-find over the ids
    parent = {o.get("object_id"): o.get("object_id") for o in objects}

    def find(x):
        while parent.get(x, x) != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for e in edges:
        a, b = find(e.get("src")), find(e.get("dst"))
        if a in parent and b in parent and a != b:
            parent[a] = b
    comps = len({find(o.get("object_id")) for o in objects}) if objects else 0

    if not kinds:
        mix = "none"
    elif kinds == ["SignalWire"]:
        mix = "signal_only"
    elif kinds == ["SocketControl"]:
        mix = "control_only"
    else:
        mix = "mixed"

    return {
        "edge_density_bucket": _b(len(edges) / float(n), (0.5, 1.0, 1.5),
                                  ("sparse", "even", "dense", "very_dense")),
        "connected_components_bucket": ("1" if comps == 1 else
                                        "2" if comps == 2 else "3+"),
        "cyclic": "cyclic" if _has_cycle(objects, edges) else "acyclic",
        "role_diversity_bucket": _b(len(roles), (1, 2, 3),
                                    ("one", "two", "three", "four_plus")),
        "edge_kind_mix": mix,
        "maximum_degree_bucket": _b(max(deg.values()) if deg else 0, (1, 2, 3),
                                    ("0_1", "2", "3", "4_plus")),
        "base_shape_id": base_shape_id(view),
    }


def _has_cycle(objects, edges):
    """Directed cycle detection. A world with feedback is a different reasoning
    problem from a pipeline, so it is worth a factor of its own."""
    adj = {}
    for e in edges:
        adj.setdefault(e.get("src"), []).append(e.get("dst"))
    WHITE, GREY, BLACK = 0, 1, 2
    state = {o.get("object_id"): WHITE for o in objects}
    for start in list(state):
        if state[start] != WHITE:
            continue
        stack = [(start, iter(adj.get(start, [])))]
        state[start] = GREY
        while stack:
            node, it = stack[-1]
            nxt = next(it, None)
            if nxt is None:
                state[node] = BLACK
                stack.pop()
                continue
            if state.get(nxt, BLACK) == GREY:
                return True
            if state.get(nxt, BLACK) == WHITE:
                state[nxt] = GREY
                stack.append((nxt, iter(adj.get(nxt, []))))
    return False


def _walk(node, out):
    if not isinstance(node, dict):
        return
    out.append(node)
    for k in ("args",):
        for a in node.get(k) or []:
            _walk(a, out)
    for k in ("arg", "where"):
        if isinstance(node.get(k), dict):
            _walk(node[k], out)


def _depth(node):
    if not isinstance(node, dict):
        return 0
    kids = list(node.get("args") or [])
    for k in ("arg", "where"):
        if isinstance(node.get(k), dict):
            kids.append(node[k])
    return 1 + max([_depth(k) for k in kids] or [0])


def goal_factors(goal):
    """Properties of what is being ASKED, independent of the world asked about.

    `mentions_explicit_object_id` is the one to watch. A corpus dominated by
    `id_is("p0")` goals teaches name-directed patching -- find the string, edit
    near it -- rather than structural reasoning about the world. That is a
    plausible way to score well on this benchmark while learning nothing it was
    built to teach, so it is measured from day one rather than discovered later.
    """
    if goal is None:
        return {"goal_root_kind": "none", "goal_ast_depth_bucket": "0",
                "goal_ast_node_count_bucket": "0",
                "mentions_explicit_object_id": "no",
                "local_vs_global": "none", "number_of_conjuncts": "0"}
    nodes = []
    _walk(goal, nodes)
    kinds = [n.get("kind") for n in nodes]
    root = goal.get("kind")
    conj = len(goal.get("args") or []) if root in ("all", "any") else 1
    has_id = "id_is" in kinds
    return {
        "goal_root_kind": root,
        "goal_ast_depth_bucket": _b(_depth(goal), (1, 2, 3),
                                    ("1", "2", "3", "4_plus")),
        "goal_ast_node_count_bucket": _b(len(nodes), (3, 8, 16),
                                         ("1_3", "4_8", "9_16", "17_plus")),
        "mentions_explicit_object_id": "yes" if has_id else "no",
        # A goal anchored to a named object is answerable locally; a bare count
        # over a domain is a statement about the whole world.
        "local_vs_global": "local" if has_id else "global",
        "number_of_conjuncts": str(min(conj, 4)),
    }


ADD_OPS = ("AddObject", "AddEdge")
REMOVE_OPS = ("RemoveObject", "RemoveEdge")


# ------------------------------------------------- the dependency of two edits
#
# The first version of `ordering_required` asked one question: does an edge
# operation name an object that another operation creates or destroys? That is a
# real dependency, and it is not all of them. It missed at least three whole
# classes:
#
#     AddObject(x) then SetObjectConfig(x)   -- configuring what was just made
#     SetObjectConfig(x) twice               -- last writer wins
#     AddEdge(e) and RemoveEdge(e)           -- same edge, opposite directions
#
# Every one of those was reported as INDEPENDENT, so every witness built from
# them was scored a tier below its real content. A false negative here does not
# announce itself: the corpus simply contains fewer hard tasks than its own
# ledger says, and the ledger is the thing that was supposed to notice.
#
# So the predicate is rebuilt on what each edit READS and what it CHANGES, and
# two edits are dependent exactly when one touches state the other depends on.
# That is the standard Bernstein condition, with one refinement the plain form
# gets wrong here -- see `op_resources`.

WITNESS_OPERATIONS = ("AddObject", "RemoveObject", "AddEdge", "RemoveEdge",
                      "SetObjectConfig")


def op_resources(op):
    """`(reads, writes, bumps)` -- the state one edit depends on and changes.

        reads    state this edit's legality or result depends on
        writes   state it ASSIGNS; two assignments to one resource never commute
        bumps    state it ACCUMULATES into; two bumps DO commute

    The three-way split is the refinement, and it exists to stop the predicate
    over-reporting. Adding two different edges to the same node changes that
    node's incidence twice. Under a plain read/write model those two edits share
    a written resource and are called order-dependent -- which is false. They
    commute, and the world cannot tell which arrived first. Incidence only
    becomes observable when something READS it, and exactly one operation does:
    `RemoveObject`, which needs it empty.

    Getting that wrong in the other direction matters just as much as the false
    negatives this replaces. A predicate that calls everything interacting puts
    the whole corpus in tier 3, which is the same loss of information as calling
    nothing interacting, arriving from the opposite side.
    """
    kind = (op or {}).get("op")
    if kind == "AddObject":
        oid = (op.get("object") or {}).get("object_id")
        # Writes existence AND config: `AddObject` carries a `static_config`, so
        # a later `SetObjectConfig` on the same id is overwriting a value this
        # op already assigned.
        return (set(), {"obj:%s" % oid, "cfg:%s" % oid}, set())
    if kind == "RemoveObject":
        t = op.get("target")
        # Reads incidence because it may not run while an edge still names the
        # target -- the closure gate in `families.apply_witness_step`.
        return ({"inc:%s" % t}, {"obj:%s" % t, "cfg:%s" % t}, set())
    if kind == "SetObjectConfig":
        t = op.get("target")
        return ({"obj:%s" % t}, {"cfg:%s" % t}, set())
    if kind in ("AddEdge", "RemoveEdge"):
        e = op.get("edge") or {}
        src, dst = e.get("src"), e.get("dst")
        # `AddEdge` needs both endpoints to exist; `RemoveEdge` needs only the
        # edge, whose presence already implies them in any closed world.
        reads = ({"obj:%s" % src, "obj:%s" % dst} if kind == "AddEdge"
                 else set())
        return (reads,
                {"edge:%s|%s|%s" % (e.get("kind"), src, dst)},
                {"inc:%s" % src, "inc:%s" % dst})
    fail(WRLM_BAD_COVERAGE,
         "cannot decide the ordering dependencies of %r: an unknown operation "
         "with no resources would be silently independent of everything, which "
         "is the exact false negative this model replaces"
         % (kind,), "witness.op")


def ops_depend(a, b):
    """Do these two edits fail to commute?

    A write conflicts with anything -- another write, a read, an accumulation.
    An accumulation conflicts only with a read. Symmetric, because "does order
    matter" is a question about a pair and not about which one was written first.
    """
    ra, wa, ba = op_resources(a)
    rb, wb, bb = op_resources(b)
    if wa & (rb | wb | bb) or wb & (ra | wa | ba):
        return True
    return bool((ra & bb) or (rb & ba))


def ordering_required(witness):
    """Does any edit depend on another edit having happened first?

    THE definition of "interacting", stated once and used by both the coverage
    ledger and the tier contract, so those two can never drift into disagreeing
    about what tier 3 means.

    Mere overlap of touched objects is too weak a test in one direction -- almost
    every rewiring touches some node twice, so overlap would classify nearly
    everything as interacting and the tier would carry no information. Naming
    only object lifecycle was too weak in the other. What is asked instead is the
    thing the phrase actually means: is there a pair of edits whose order changes
    either what is legal or what results?

    This is a SYNTACTIC decision, taken from the operations alone with no world
    in hand, and it is checked against a semantic oracle -- brute-force over
    every permutation of a real witness on a real world -- in the battery. The
    syntactic answer is required never to say "independent" where the oracle
    says order matters. It is permitted to be conservative the other way, and
    where it is, the battery says by how much rather than letting it pass.
    """
    ops = list(witness or [])
    for i in range(len(ops)):
        for j in range(i + 1, len(ops)):
            if ops_depend(ops[i], ops[j]):
                return True
    return False


def witness_factors(witness):
    """Properties of the constructive transformation the generator knows about."""
    ops = list(witness or [])
    kinds = sorted({o.get("op") for o in ops})
    touched = []
    for o in ops:
        touched.extend(o.get("touches") or [])
    distinct = len(set(touched))
    adds = any(k in ADD_OPS for k in kinds)
    rems = any(k in REMOVE_OPS for k in kinds)
    return {
        "operation_kind_set": "+".join(kinds) if kinds else "none",
        "affected_objects_bucket": _b(distinct, (1, 2, 4),
                                      ("1", "2", "3_4", "5_plus")),
        "independent_vs_interacting": ("interacting" if ordering_required(ops)
                                       else "independent"),
        "adds_vs_removes": ("mixed" if adds and rems else
                            "adds" if adds else
                            "removes" if rems else "config_only"),
    }


def all_factors(view, goal, witness):
    f = {}
    f.update(world_factors(view))
    f.update(goal_factors(goal))
    f.update(witness_factors(witness))
    return f


# ------------------------------------------------------------------ the spec
class CoverageSpecV1(object):
    """The versioned policy. Every number in here is a decision, not a default.

    `max_per_sem` / `max_per_shape` are where `base_semantic_id` earns its keep
    after being thrown out of the cell: they permit real reuse of one rich world
    while stopping a single demonstration world from quietly becoming the
    benchmark."""

    # A world enters the pool `asserted` and is upgraded to `proved` only when a
    # real `LowerResultV1` was injected at capture. Benchmark-grade means
    # `proved` and nothing else: an `asserted` binding is a world whose `sem-`
    # was taken on the word of whoever handed it over, and a benchmark built on
    # those is measuring the supplier. It is a LIST rather than a flag because
    # loosening it should have to name what it is admitting.
    BENCHMARK_GRADE_BINDINGS = ("proved",)

    def __init__(self, corpus_seed, cell_quota=2, max_per_sem=4,
                 max_per_shape=12, allowed_binding_kinds=None):
        if not isinstance(corpus_seed, str) or not corpus_seed.strip():
            fail(WRLM_BAD_COVERAGE, "corpus_seed must be a non-empty string",
                 "corpus_seed")
        self.version = COVERAGE_SPEC_VERSION
        self.corpus_seed = corpus_seed
        self.cell_quota = int(cell_quota)
        self.max_per_sem = int(max_per_sem)
        self.max_per_shape = int(max_per_shape)
        self.allowed_binding_kinds = tuple(
            allowed_binding_kinds if allowed_binding_kinds is not None
            else self.BENCHMARK_GRADE_BINDINGS)

    def quota(self, cell):
        return self.cell_quota

    def describe(self):
        return {"coverage_spec_version": self.version,
                "corpus_seed": self.corpus_seed,
                "cell_quota": self.cell_quota,
                "max_per_sem": self.max_per_sem,
                "max_per_shape": self.max_per_shape,
                "allowed_binding_kinds": list(self.allowed_binding_kinds)}


# ---------------------------------------------------------------- the ledger
#
# Every proposal ends in exactly one of these. The list used to be shorter and
# the shortfall was the problem: a proposal that turned out to be for a DIFFERENT
# cell, or that wanted a formatted presentation the record does not have, was
# dropped without a name. Those two were the largest gap between `proposed` and
# everything accounted for, and an unnamed gap is indistinguishable from a
# counting bug -- which means nobody can tell whether a cell is hard, mis-aimed,
# or simply unreachable in the presentation it was asked for.
CANDIDATE_OUTCOMES = (
    "accepted_unique",              # accepted, unique `case-`, quota-satisfying
    "candidate_not_selected",       # survived every gate, lost the batch
    "off_cell",                     # derived cell != requested cell
    "presentation_unavailable",     # no distinct formatted twin to present
    "duplicate_case",
    "degenerate_at_base",
    "unsatisfiable_or_no_witness",
    "invalid_generated_world",
    "host_fault",
)

# Not a candidate outcome: nothing was proposed, the CELL ran out of attempts.
# Folding it in with the rest would break the identity below and, worse, would
# make an exhausted cell look like a rejected proposal.
CELL_OUTCOMES = ("attempt_bound_exhausted",)

OUTCOMES = ("proposed",) + CANDIDATE_OUTCOMES + CELL_OUTCOMES


class CoverageLedger(object):
    """Counts, caps, and the selection rule.

    Only `accepted_unique` satisfies a quota -- accepted, non-degenerate, unique
    `case-`. Every other outcome is still counted, because the difference between
    *an under-covered cell* and *a generator that cannot inhabit the cell it
    claims* is invisible if you only record successes. Ten thousand proposals and
    two acceptances is not a healthy cell; without the other counters it looks
    like a busy one.
    """

    def __init__(self, spec):
        self.spec = spec
        self.cells = {}            # cell_key -> {outcome: n}
        self.cell_of = {}          # cell_key -> cell
        self.marginal = {}         # (factor, value) -> n
        self.pairwise = {}         # ((f1,v1),(f2,v2)) -> n
        self.per_sem = {}          # (sem, family, tier) -> n
        self.per_shape = {}        # (shape, family, tier) -> n
        self.cases = set()         # case- ids already accepted

    # -- recording ---------------------------------------------------------
    def _cell_row(self, cell):
        k = cell_key(cell)
        if k not in self.cells:
            self.cells[k] = dict.fromkeys(OUTCOMES, 0)
            self.cell_of[k] = dict(cell)
        return self.cells[k]

    def record(self, cell, outcome):
        if outcome not in OUTCOMES:
            fail(WRLM_BAD_COVERAGE, "unknown outcome %r" % (outcome,), "outcome")
        self._cell_row(cell)[outcome] += 1

    def accept(self, cell, case, factors, semantic_id):
        """Register an accepted case and everything it contributes."""
        row = self._cell_row(cell)
        row["accepted_unique"] += 1
        self.cases.add(case)
        for fv in sorted(factors.items()):
            self.marginal[fv] = self.marginal.get(fv, 0) + 1
        items = sorted(factors.items())
        for i in range(len(items)):
            for j in range(i + 1, len(items)):
                self.pairwise[(items[i], items[j])] = \
                    self.pairwise.get((items[i], items[j]), 0) + 1
        pk = (semantic_id, cell["family"], cell["tier"])
        self.per_sem[pk] = self.per_sem.get(pk, 0) + 1
        sk = (factors["base_shape_id"], cell["family"], cell["tier"])
        self.per_shape[sk] = self.per_shape.get(sk, 0) + 1

    # -- caps --------------------------------------------------------------
    def sem_capped(self, semantic_id, family, tier):
        return (self.per_sem.get((semantic_id, family, tier), 0)
                >= self.spec.max_per_sem)

    def shape_capped(self, shape_id, family, tier):
        return (self.per_shape.get((shape_id, family, tier), 0)
                >= self.spec.max_per_shape)

    # -- reading -----------------------------------------------------------
    def accepted(self, cell):
        return self.cells.get(cell_key(cell), {}).get("accepted_unique", 0)

    def deficit(self, cell):
        return self.spec.quota(cell) - self.accepted(cell)

    def counts(self, cell):
        return dict(self.cells.get(cell_key(cell),
                                   dict.fromkeys(OUTCOMES, 0)))

    def coverage_gain(self, factors):
        """How much NEW low-order coverage would this candidate contribute?

        Unseen marginal values plus unseen pairs. Pairwise, not exhaustive: full
        interaction coverage over this many factors is unreachable, and pairwise
        is the established tractable substitute that still exposes obvious holes.
        """
        items = sorted(factors.items())
        gain = sum(1 for fv in items if fv not in self.marginal)
        for i in range(len(items)):
            for j in range(i + 1, len(items)):
                if (items[i], items[j]) not in self.pairwise:
                    gain += 1
        return gain

    def accounted(self):
        """`(proposed, sum of candidate outcomes)`. These must be equal.

        The check is the point. Two totals that are supposed to agree and are
        never compared are two totals that will quietly stop agreeing, and the
        symptom -- a cell that looks under-covered -- is the same symptom as a
        real shortage. See `check_accounting`.
        """
        gross = sum(c["proposed"] for c in self.cells.values())
        named = sum(c[o] for c in self.cells.values()
                    for o in CANDIDATE_OUTCOMES)
        return gross, named

    def check_accounting(self):
        gross, named = self.accounted()
        if gross != named:
            fail(WRLM_BAD_COVERAGE,
                 "%d proposals but %d named outcomes: %d proposal%s ended "
                 "somewhere with no name, and an unnamed rejection reads as "
                 "under-coverage of the cell that made it"
                 % (gross, named, abs(gross - named),
                    "" if abs(gross - named) == 1 else "s"), "ledger")
        return True

    def report(self, cells=None):
        """Spread first, then depth, then the accounting.

        `cells_touched` counts cells the generator AIMED at; `cells_inhabited`
        counts cells it landed in. The two used to share the name `cells_filled`
        between them and a cell that was tried a hundred times and never filled
        read as progress. `quota_mass` is the depth number: how much of the
        published quota is actually paid for, which spread alone cannot say.
        """
        acc = {k: self.cells[k]["accepted_unique"] for k in self.cells}
        at_quota = sum(1 for k in self.cells
                       if acc[k] >= self.spec.cell_quota)
        domain = cells if cells is not None else list(self.cell_of.values())
        want = sum(self.spec.quota(c) for c in domain) or 1
        have = sum(min(self.accepted(c), self.spec.quota(c)) for c in domain)
        gross, named = self.accounted()
        return {"cells_touched": len(self.cells),
                "cells_inhabited": sum(1 for k in acc if acc[k] > 0),
                "cells_at_quota": at_quota,
                "cells_published": len(domain),
                "quota_mass": round(have / float(want), 4),
                "accepted": sum(acc.values()),
                "proposed": gross,
                "outcomes_named": named,
                "marginal_values_seen": len(self.marginal),
                "pairs_seen": len(self.pairwise),
                "totals": {o: sum(c[o] for c in self.cells.values())
                           for o in OUTCOMES}}


# ------------------------------------------------------------- selection
def partition_of(cell):
    return (cell["family"], cell["tier"])


def select_partition(ledger, cells):
    """Phase 1: the (family, tier) partition furthest from its quota, by RATIO.

    Ratio rather than raw count, so one family with an enormous valid domain
    cannot swallow the corpus simply by having more cells to fill."""
    parts = {}
    for c in cells:
        p = partition_of(c)
        acc, quota = parts.get(p, (0, 0))
        parts[p] = (acc + ledger.accepted(c), quota + ledger.spec.quota(c))
    if not parts:
        return None
    ranked = sorted(parts.items(),
                    key=lambda kv: (kv[1][0] / float(kv[1][1] or 1), kv[0]))
    return ranked[0][0]


def select_cell(ledger, cells, partition):
    """Phases 2 and 3: largest deficit, ties broken by a HASH of the cell.

    Not lexicographic. A lexicographic tie-break permanently privileges whichever
    enum value happens to sort first, and that bias reasserts itself after every
    reset or partial regeneration -- the corpus would quietly over-represent
    `tiny`, `source`, and whatever family got named first. Hashing against the
    corpus seed is just as reproducible and has no such preference.

    Note the tie-break is over CELLS, before generation. Breaking ties on `case-`
    is impossible here: no case exists yet."""
    live = [c for c in cells if partition_of(c) == partition
            and ledger.deficit(c) > 0]
    if not live:
        live = [c for c in cells if partition_of(c) == partition]
    if not live:
        return None
    best = max(ledger.deficit(c) for c in live)
    tied = [c for c in live if ledger.deficit(c) == best]
    return min(tied, key=lambda c: hashlib.sha256(
        (ledger.spec.corpus_seed + "|" + ledger.spec.version + "|").encode()
        + cell_bytes(c)).hexdigest())
