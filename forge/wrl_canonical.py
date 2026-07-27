"""wrl_canonical.py -- WRL Slice 2 identity spine (Phase 3A).

The single source of truth for the FROZEN Forge Semantic IR v1 registries and
for the canonical-identity discipline GPT-5.6 named for WRL Slice 2:

    validate_graph      typed structural validation (stable error codes)
    canonicalize_graph  order-independent canonical WRL graph
    serialize_artifact  deterministic canonical bytes of the STATIC artifact
    semantic_artifact_id  Hash(canonical Forge IR + semantic policy refs)
    backend_artifact_id   Hash(SemanticArtifactID + lowering profile)

Identity split (D4): the SemanticArtifactID is a pure function of the frozen
semantic graph (objects with static_config, structural edges, semantic policy
ids) and NOTHING of the backend encoding, the run plan, or the claim batches.
The BackendArtifactID additionally folds in the lowering profile (encoding,
compiler hash, backend representation) -- so one-hot<->binary and Q-format
backend swaps move the BackendArtifactID while leaving the SemanticArtifactID
fixed, and a different numeric/admit policy or a different initial rotor moves
BOTH (the semantic id first).

This module deliberately does NOT import wrl_ir at load time (wrl_ir imports
these registries and helpers). canonicalize_graph rebuilds a graph via the
passed instance's own type, so no back-import is needed.
"""
import hashlib
import json
import re
from collections import namedtuple

# the OPERATIVE counter-encoding domain (Phase 3D.1-A): `auto` applies the
# profile's pinned `onehot_max`; `one_hot`/`binary` force the representation.
COUNTER_ENCODINGS = ("auto", "one_hot", "binary")
_SEM_ID_RE = re.compile(r"^sem-[0-9a-f]{64}$")

# ------------------------------------------------------------ frozen registry
IR_VERSION = "1.0"
PROFILE_ID = "forge.world.core.v1"          # deterministic-circuit-world
RULEPACK_ID = "forge.world.core.rules.v1"   # the transition law (Slice 2.1)
ADMIT_POLICY_ID = "admit_candidate_min_firstreceipt_v1"
FILM_SCHEMA_ID = "film.v0.7"
NUMERIC_POLICY_IDS = ("POLICY_FORGE",)
LOWERING_PROFILE_VERSION = "1.0"

# IR v1.1 / Mailbox Slice A, RULING Q2: `Mailbox` is the SIXTH sanctioned
# role. The addition is strictly ADDITIVE -- a world that declares no Mailbox
# canonicalizes to byte-identical bytes and therefore keeps its exact prior
# SemanticArtifactID (the frozen demo still seals `sem-8ae91fe9...fe4a`).
# Per D8 there is NO new edge kind: a mailbox is addressed by id, never wired.
ROLE_IDS = ("Pulser", "Relay", "Door", "Spinner", "Orb", "Mailbox")
MAILBOX_ROLE = "Mailbox"
EDGE_KINDS = ("SignalWire", "SocketControl")

# frozen schema block (the only accepted artifact schemas)
SCHEMA_IDS = {
    "runtime_state_schema": "RuntimeStateV1",
    "epoch_input_schema": "EpochInputV1",
    "observable_schema": "EpochResultV1",
}
# D6: a mailbox-bearing world carries `mailbox_states` / `mailbox_capacity_fault`
# as NEW SIBLING runtime fields, so it declares a DIFFERENT runtime state
# schema. The two blocks are MUTUALLY EXCLUSIVE and `schemas_for_roles` decides
# which one an artifact must carry: a mailbox-free world may not claim v1_1 and
# a mailbox-bearing world may not hide behind v1. That is what makes the extra
# runtime surface visible in the SemanticArtifactID instead of implicit.
SCHEMA_IDS_V1_1 = dict(SCHEMA_IDS, runtime_state_schema="RuntimeStateV1_1")
STATE_SCHEMA_REFS = {"state.%s.v1" % r.lower() for r in ROLE_IDS}

# --------------------------------------------- IR v1.1 mailbox semantic surface
# A mailbox-bearing world does not merely declare an extra role: it selects a
# DIFFERENT ADMIT policy, a DIFFERENT runtime state schema, a DIFFERENT film
# schema, and a DIFFERENT IR revision. All four move together or not at all.
#
# They are therefore derived by ONE function from the role set, because four
# independent selectors are four opportunities to drift -- and a drifted
# selector is the worst possible failure here: an artifact whose id claims one
# semantics while the runner executes another.
IR_VERSION_V1_1 = "1.1"
MAILBOX_ADMIT_POLICY_ID = "admit_mailbox_deliver_all_v1"
# Frozen Film v0.7 never reserved `MailboxEnqueue` / `MailboxDeliver` /
# `MailboxReject`, the gated `admit_mailbox:` projection, or a mailbox state
# projection. A second implementation reading `film.v0.7` is therefore entitled
# to implement the pre-mailbox meaning of that identifier, so a mailbox world
# MUST NOT claim it. The mailbox film schema is a distinct id.
FILM_SCHEMA_ID_MAILBOX = "film.v0.7.mailbox.v1"
# The canonical validator must not admit an artifact its own sanctioned oracle
# rejects, so the upper bound is stated here and the agreement with the Fixture
# is CHECKED (binding_run43 r10.18) rather than shared.
#
# It is checked and not shared on purpose. The Fixture is an INDEPENDENT oracle:
# if it imported this constant, a wrong bound would be agreed on by both sides
# and the cross-check would confirm nothing. A checked agreement catches drift
# while keeping the second opinion second. (An earlier comment here claimed
# "both sides read it", which was simply false -- `fixture.py` spells `0 < w_ <=
# 32` itself. Claiming a shared definition that does not exist is worse than an
# honest fork, because it tells the next reader there is nothing to check.)
MAILBOX_WIDTH_MAX = 32

# ------------------------------------------- IR v1.1 async route surface (B)
# Slice B: an AsyncRouteDecl is a STATIC, world-generated, ONE-SHOT `Send`. It
# is not an edge (D8 still holds: a mailbox is never wired) and it is not a
# scenario claim; it is world structure, so it belongs to the
# SemanticArtifactID exactly as a rotor does.
#
# The three constants below are DERIVED from ADMIT's frozen identity bounds and
# are deliberately NOT imported from `admit`. `wrl_canonical` is the identity
# spine; every module in the system reads it, and it currently imports nothing
# but the standard library. Making it import the runtime reducer to learn a
# number would invert the layering for the sake of one integer.
#
# So the derivation is stated here and PINNED by a battery row against
# `admit`'s own values (binding_run47 P1). That is the same discipline as
# MAILBOX_WIDTH_MAX above: an unavoidable second spelling is acceptable only
# when something fails the moment the two disagree.

# Each route mints exactly one ClaimFact, and ADMIT's claim log holds
# `admit.MAX_FACTS` of them. A seventh route could never be represented, so it
# is refused at seal rather than silently dropped at runtime.
MAX_ASYNC_ROUTES = 6

# `admit.WK == 4`, so writer ids run 0..15 and 15 is the LAST addressable
# writer. Reserving the top of the namespace (rather than, say, 0) means the
# reservation cannot collide with the low ids scenarios actually use, and it
# is derivable -- `(1 << WK) - 1` -- rather than arbitrary.
ROUTE_WRITER_ID = 15

# Every route hung on the SAME firing epoch arrives in ONE observation batch,
# and `admit.admit_step` opens with a hard `assert len(batch) <= MAX_BATCH`.
# That assert is not a typed rejection -- it is an AssertionError, raised by the
# reducer, about a world that sealed perfectly. Slice B routes are all `once`,
# so co-firing is not an exotic case: it is what happens the moment an author
# hangs a second route on a pulser. Measured before the law was written, worlds
# with 5 and 6 routes on one `once(1)` pulser both sealed (sem-a95c45c6..,
# sem-b209f845..) and would have crashed the reducer on epoch 1.
#
# This bound is TIGHTER than MAX_ASYNC_ROUTES and it is a different bound for a
# different reason: MAX_ASYNC_ROUTES bounds the CUMULATIVE claim log over a run,
# this bounds ONE epoch's observation. Six routes are representable; six routes
# at once are not.
MAX_ROUTE_COFIRE = 4

# A `Send` payload body is four lanes (`admit.payload_key`: b0..b3), each
# bounded by the TARGET MAILBOX's declared width -- `admit._op_outcome`
# rejects `body_out_of_range` otherwise. A route whose body is out of range
# would seal, compile, and then provably fail to deliver: a world that is dead
# by construction. The validator therefore applies the same bound at seal time.
ROUTE_BODY_LANES = 4


def route_body_in_range(width, body):
    """The frozen body-lane domain for a mailbox of the given width.

    A SECOND SPELLING of `admit._op_outcome`'s `0 <= v < (1 << w_)` test, for
    the layering reason given above.

    COMMIT 4 PROMISED TO REMOVE THIS FORK AND DID NOT. The promise assumed the
    unification was free once `admit` was being edited anyway; working it
    through showed it is not, and the reason is worth recording rather than
    re-discovering:

      * `admit` importing this module would make the FROZEN L-0 reducer depend
        on the module Slice B edits every commit. A language-track mistake would
        then take the whole ratified tier red, which is the precise failure the
        sweep's frozen/live split exists to prevent.
      * this module importing `admit` is the inversion the header refuses, and
        it is refused for a load-bearing reason: the spine has a verified
        BROWSER PORT, and a spine that reaches for the reducer cannot be ported.
      * extracting the law into a third shared module ends the fork but adds a
        file to BOTH dependency graphs, including the ported one.

    So the fork stays, and it stays under the discipline every other derived
    constant here is under: an unavoidable second spelling is acceptable only
    when something fails the moment the two disagree. That is `binding_run47`
    P0c, which folds the SAME bodies through both spellings across the whole
    boundary neighbourhood -- a body at the boundary must be Applied and a body
    one over must be Rejected `body_out_of_range`.

    Flagged to GPT-5.6 in the commit 4 memo: this is a judgement call about
    which coupling is worse, not a fact, and it is reversible either way.

    `width` is checked, not assumed. Callers read it off the TARGET mailbox's
    static config, so a caller that reached here with a target that is not a
    mailbox would arrive with `None` and `1 << None` would raise TypeError --
    an untyped crash where a typed rejection belongs. Mutation testing found
    this: switching the target-role rule off turned a named row failure into a
    bare crash that aborted the whole section, so the battery could no longer
    say WHICH law had been broken."""
    return (isinstance(width, int) and not isinstance(width, bool)
            and width > 0
            and isinstance(body, (tuple, list))
            and len(body) == ROUTE_BODY_LANES
            and all(isinstance(v, int) and not isinstance(v, bool)
                    and 0 <= v < (1 << width) for v in body))


def once_epoch(clock):
    """The epoch a `once` clock fires, or None if the clock is not `once`.

    One spelling, because commit 4 gave this question a SECOND asker. The seal
    derives a route's firing epoch to enforce the co-firing bound; the runtime
    fold derives it again to decide which observation batch the route's claim
    joins. Two hand-rolled `clock[1]`s that must agree forever is the forked
    vocabulary this slice keeps finding, so it is written once and read twice.

    Tolerant of the JSON round-trip (a deserialized artifact carries lists)."""
    c = tuple(clock or ())
    return c[1] if len(c) == 2 and c[0] == "once" else None


def semantic_surface_for_roles(roles):
    """The FOUR role-derived semantic identity fields, decided together.

    This is the single source of truth for "what semantics does a world
    carrying these roles have?". `Mailbox` present selects the entire v1.1
    mailbox surface; absent, every field is exactly its frozen v1 value, so a
    mailbox-free world is byte-identical and keeps its prior
    SemanticArtifactID."""
    has_mailbox = MAILBOX_ROLE in set(roles)
    return {
        "ir_version": IR_VERSION_V1_1 if has_mailbox else IR_VERSION,
        "runtime_state_schema": ("RuntimeStateV1_1" if has_mailbox
                                 else "RuntimeStateV1"),
        "admit_policy_id": (MAILBOX_ADMIT_POLICY_ID if has_mailbox
                            else ADMIT_POLICY_ID),
        "film_schema_id": (FILM_SCHEMA_ID_MAILBOX if has_mailbox
                           else FILM_SCHEMA_ID),
    }


def schemas_for_roles(roles):
    """The schema block an artifact carrying these roles MUST declare.

    Derived from `semantic_surface_for_roles` rather than chosen separately, so
    the runtime state schema can never disagree with the admit policy."""
    return dict(SCHEMA_IDS,
                runtime_state_schema=
                semantic_surface_for_roles(roles)["runtime_state_schema"])


def roles_of_artifact(artifact):
    """The role ids an artifact declares, in artifact order."""
    return tuple(o.get("role") for o in (artifact.get("objects") or ()))


def mailbox_decls_of_artifact(artifact):
    """`{mailbox_id: (width, capacity)}` read off a canonical artifact.

    The SEMANTIC source of truth for the mailbox set. ADMIT must read the
    mailbox declarations from the artifact that was hashed into the
    SemanticArtifactID -- never from the backend compile plan, which per D8
    carries nothing about mailboxes because a mailbox is not physical."""
    out = {}
    for o in (artifact.get("objects") or ()):
        if o.get("role") == MAILBOX_ROLE:
            cfg = o.get("static_config") or {}
            out[o.get("object_id")] = (cfg.get("w"), cfg.get("cap"))
    return out


def routes_of_artifact(artifact):
    """The AsyncRouteDecl list read off a canonical artifact -- `[]` for a
    route-free world.

    The artifact CANONICALLY OMITS `async_routes` when empty, so every consumer
    that wants to ask "does this world emit routes?" would otherwise have to
    spell `artifact.get("async_routes") or ()` and get the omission rule right.
    That is the shape of question the L-0 round found being answered four
    different ways, so it is answered ONCE here.

    `routes_of` is the same question asked of a GRAPH. Two accessors rather than
    one because they read two different representations; they are kept adjacent
    to their subjects rather than merged into a shape-sniffing helper that would
    quietly return `[]` for a typo'd argument."""
    return list(artifact.get("async_routes") or ())

# the required non-null single-valued semantic policy ids
REQUIRED_POLICY_IDS = ("rulepack_id", "admit_policy_id", "film_schema_id")
# the required keys of a backend lowering profile (Phase 3D.1-A: `encoding` ->
# operative `counter_encoding` + a pinned `onehot_max`).
REQUIRED_LOWERING_KEYS = ("counter_encoding", "onehot_max", "numeric_backend",
                          "compiler_hash", "target", "lowering_profile_version")

# per-role port signatures (frozen)
PORTS = {
    "Pulser":  {"out": ("sig_out",), "in": ()},
    "Relay":   {"out": ("sig_out",), "in": ("sig_in",)},
    "Door":    {"out": (),           "in": ("sig_in",)},
    "Spinner": {"out": ("socket",),  "in": ("sig_in",)},
    "Orb":     {"out": (),           "in": ("pose",)},
    # D8: a Mailbox has NO structural port. It is addressed by id exactly as
    # `SetRotor` names a spinner. Because edge validation is entirely
    # port-driven, this single empty entry is what makes every attempt to wire
    # a mailbox fail WRL_ILLEGAL_PORT_PAIR -- D8 is enforced structurally,
    # not by a special case.
    "Mailbox": {"out": (),           "in": ()},
}
# the required (src_out_port, dst_in_port) for each structural edge kind
EDGE_PORTS = {
    "SignalWire":    ("sig_out", "sig_in"),
    "SocketControl": ("socket", "pose"),
}

# ----------------------------------------- authoritative per-role config schema
# (Phase 3B.5.1) The single source of truth for a role's config keys, consumed
# by BOTH the artifact validator (`static_config_keys` -> the exact key set a
# sealed static_config may reveal) AND the surface tooling (`surface_keys` -> the
# k=v lexemes a WRL Core `(...)` group accepts, which wrl_complete offers). A
# Pulser's verbose surface (`mode/period/phase/epoch`) is folded to a single
# positional `clock` field in the artifact, so the two projections differ for it.
ROLE_CONFIG_SCHEMA = {
    "Pulser":  {"surface_keys": ("mode", "period", "phase", "epoch"),
                "static_config_keys": ("clock",)},
    "Relay":   {"surface_keys": (), "static_config_keys": ()},
    "Door":    {"surface_keys": (), "static_config_keys": ()},
    "Spinner": {"surface_keys": ("w", "n", "rotor", "configurable"),
                "static_config_keys": ("w", "n", "rotor", "configurable")},
    "Orb":     {"surface_keys": (), "static_config_keys": ()},
    # MailboxDecl (D7): `w` is the message body width, `cap` the per-period
    # capacity governing `mailbox_capacity_fault`. Both are STATIC world
    # structure, so both belong to the SemanticArtifactID -- widening a
    # mailbox is a different world, exactly as re-rotoring a spinner is.
    "Mailbox": {"surface_keys": ("w", "cap"),
                "static_config_keys": ("w", "cap")},
}

# frozen exact key sets for the sealed artifact records (Phase 3B.5.1). A sealed
# artifact must reveal EXACTLY these fields -- an unknown field is a typed
# rejection, never silently dropped, so no meaning-bearing data can smuggle past
# the identity spine unnoticed.
#
# `async_routes` is OPTIONAL and canonically OMITTED when empty (ruling Q, Slice
# B commit 2): there is exactly ONE encoding of "this world has no routes", the
# absence of the key. Admitting both an absent key and an empty list would give
# the same world two canonical spellings and therefore two SemanticArtifactIDs
# -- which is precisely the failure the identity spine exists to prevent -- and
# it is what keeps every pre-Slice-B world byte-identical.
ARTIFACT_FIELDS = ("ir_version", "profile_id", "semantic_policies",
                   "schemas", "objects", "edges", "async_routes")
POLICY_FIELDS = ("rulepack_id", "numeric_policy_ids",
                 "admit_policy_id", "film_schema_id")
OBJECT_FIELDS = ("object_id", "role", "static_config",
                 "state_schema_ref", "ports")
EDGE_FIELDS = ("kind", "src", "dst")
# AsyncRouteDecl. `body` is NOT part of the RouteKey (see `route_key`) but IS
# part of the record, so two routes that differ only in body are the SAME route
# declared twice -- a duplicate -- while a single route whose body changes is a
# DIFFERENT world.
ROUTE_FIELDS = ("source_id", "route_tag", "mailbox_id", "body")

_IDENT_OK = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_")


# ----------------------------------------------- canonical semantic locators
# (Phase 3B.5.1) An identity-spine locator names an offending element by its
# CANONICAL key -- NOT by a source span or filename (those stay in the 3B-1
# sidecar). wrl_diagnostics maps these through a WrlSourceMap to spans/canvas.
class ObjectKey(namedtuple("ObjectKey", "object_id")):
    __slots__ = ()

    def render(self):
        return "object %s" % (self.object_id,)


class EdgeKey(namedtuple("EdgeKey", "kind src dst")):
    __slots__ = ()

    def render(self):
        return "edge %s:%s->%s" % (self.kind, self.src, self.dst)


class RouteKey(namedtuple("RouteKey", "source_id route_tag mailbox_id")):
    """The canonical identity of an AsyncRouteDecl (Slice B, ruling Q2).

    A SEPARATE locator, not an overloaded `ObjectKey`. A route is not an
    object: it has no ports, no state schema, and no entry in `object_order`,
    and naming it with an object's locator would tell every diagnostics
    consumer to go looking for a node that does not exist.

    `body` is deliberately EXCLUDED. Identity is "which source, under which
    tag, addresses which mailbox" -- so re-sending a different value under an
    existing route is an EDIT of that route, and declaring the same route twice
    with two different bodies is a contradiction (WRL_DUPLICATE_ROUTE) rather
    than two routes that will both fire. Lexicographic tuple order is the
    canonical order, and per Q4 a route's zero-based ordinal in that order IS
    its ADMIT `sequence`."""
    __slots__ = ()

    def render(self):
        return "route %s ~~%s~~> %s" % (self.source_id, self.route_tag,
                                        self.mailbox_id)


# ------------------------------------------------------------------ exceptions
class WrlUnsupported(Exception):
    """A construct outside the frozen IR v1 scope (never a speculative
    lowering). Base class so `except WrlUnsupported` also catches the typed
    structural rejections below."""


class WrlValidationError(WrlUnsupported):
    """A typed structural rejection carrying a STABLE machine code AND, when the
    validator can name the offending element, CANONICAL semantic locators
    (Phase 3B.5.1): `primary_locator`/`related_locator` are ObjectKey/EdgeKey (or
    None) and `field_path` is a dotted canonical path like `static_config.rotor`
    (or None). These stay on the identity spine -- no source spans or filenames
    -- so the validator never depends on the 3B-1 sidecar; wrl_diagnostics maps
    the locators through a WrlSourceMap to spans/canvas."""
    def __init__(self, code, message, primary_locator=None,
                 related_locator=None, field_path=None):
        super().__init__("[%s] %s" % (code, message))
        self.code = code
        self.message = message
        self.primary_locator = primary_locator
        self.related_locator = related_locator
        self.field_path = field_path


# stable error codes (the validation contract)
WRL_DUPLICATE_ID = "WRL_DUPLICATE_ID"
WRL_UNKNOWN_ENDPOINT = "WRL_UNKNOWN_ENDPOINT"
WRL_ILLEGAL_PORT_PAIR = "WRL_ILLEGAL_PORT_PAIR"
WRL_CONTROLLER_CONFLICT = "WRL_CONTROLLER_CONFLICT"
WRL_CLOCK_RANGE = "WRL_CLOCK_RANGE"
WRL_NUMERIC_RANGE = "WRL_NUMERIC_RANGE"
WRL_EPOCH_RANGE = "WRL_EPOCH_RANGE"
WRL_UNSUPPORTED_FEATURE = "WRL_UNSUPPORTED_FEATURE"
# Slice 2.1 sealing / lexical errata codes
WRL_UNSEALED_POLICY = "WRL_UNSEALED_POLICY"          # null/empty policy id
WRL_MALFORMED_ARTIFACT = "WRL_MALFORMED_ARTIFACT"    # bad shape / version / schema
WRL_PORT_SIGNATURE = "WRL_PORT_SIGNATURE"            # {ports} != role signature
WRL_BAD_LOWERING_PROFILE = "WRL_BAD_LOWERING_PROFILE"  # half-specified backend
# Phase 3D.1.1 sealed-object integrity code
WRL_SEALED_IMMUTABLE = "WRL_SEALED_IMMUTABLE"        # attempted write to a seal
# Phase 3B.5.1 exact-key-set code
WRL_UNKNOWN_ARTIFACT_FIELD = "WRL_UNKNOWN_ARTIFACT_FIELD"  # extra sealed field
# Slice B async-route codes. An undeclared route endpoint reuses
# WRL_UNKNOWN_ENDPOINT and an out-of-range body reuses WRL_NUMERIC_RANGE: those
# rejections mean exactly what they already meant, and a new code for a rule
# that has not changed is a fork of the diagnostic vocabulary.
WRL_DUPLICATE_ROUTE = "WRL_DUPLICATE_ROUTE"      # two routes, one RouteKey
WRL_ROUTE_BUDGET = "WRL_ROUTE_BUDGET"            # more than MAX_ASYNC_ROUTES
# Slice B commit 4. DISTINCT from WRL_ROUTE_BUDGET on purpose: the budget says
# "declare fewer routes", this says "declare them on different epochs". Folding
# the two under one code would give the author one message for two opposite
# repairs -- the run47 lesson that many laws sharing one error code is a
# reporting defect, applied before it can happen.
WRL_ROUTE_BATCH_OVERFLOW = "WRL_ROUTE_BATCH_OVERFLOW"
# Slice B commit 4, the PAIRING half of the same bound. A world whose routes fit
# and a scenario whose per-epoch claims fit can still, TOGETHER, overrun one
# observation batch. Neither document is at fault, so this gets its own code for
# the reason WRL_ROUTE_WRITER_RESERVED does: a pairing rejection must not read as
# a verdict on either document, or the author edits the wrong file.
WRL_EPOCH_BATCH_OVERFLOW = "WRL_EPOCH_BATCH_OVERFLOW"
# One code for BOTH ends, mirroring WRL_ILLEGAL_PORT_PAIR: the author's fix is
# the same shape at either end ("this end may not be that role").
WRL_ILLEGAL_ROUTE_ENDPOINT = "WRL_ILLEGAL_ROUTE_ENDPOINT"
# Slice B commit 3. A route-bearing world MINTS claims under ROUTE_WRITER_ID, so
# a scenario run against THAT world may not also write under it. This is a
# COMPATIBILITY rejection, not a narrowing of ScenarioV1: writer 15 stays legal
# in every route-free world, and the ruling is explicit that the document
# validator must NOT learn about it -- a scenario is authored before it is bound
# to a world, and a scenario is deliberately reusable across worlds.
WRL_ROUTE_WRITER_RESERVED = "WRL_ROUTE_WRITER_RESERVED"
# Slice B commit 5d (Core 0.2.1 §8c consequence 2). A ReplayBundle records the
# acceptance policy its frames ran under (§8b `policy_ids`); the initial
# artifact seals the policy the world declares. If those two disagree the
# bundle is INTERNALLY INCONSISTENT and is refused rather than reconciled.
#
# Refused rather than reconciled is the whole content of the code. Preferring
# either source silently would reintroduce the 0.1.x defect from the other end:
# there a film named a policy that could not reproduce its own frames and
# nothing looked, so the mismatch was invisible. Making the record load-bearing
# (§8b) without making it CHECKED would leave it equally invisible -- it would
# just be a different field nobody compared.
WRL_REPLAY_POLICY_MISMATCH = "WRL_REPLAY_POLICY_MISMATCH"


def _fail(code, message, primary_locator=None, related_locator=None,
          field_path=None):
    raise WrlValidationError(code, message, primary_locator,
                             related_locator, field_path)


def _reject_unknown(present, allowed, where, primary_locator=None,
                    path_prefix=None):
    """Reject any field NOT in the frozen `allowed` set. `where` names the record
    for the message; `primary_locator`/`path_prefix` carry the canonical locator
    onto the raised error so wrl_diagnostics can point at the extra field."""
    extra = sorted(set(present) - set(allowed))
    if extra:
        fp = extra[0] if path_prefix is None else "%s.%s" % (path_prefix,
                                                             extra[0])
        _fail(WRL_UNKNOWN_ARTIFACT_FIELD,
              "%s has unknown field(s) %s (frozen set: %s)"
              % (where, extra, sorted(allowed)),
              primary_locator=primary_locator, field_path=fp)


# --------------------------------------------------------------- port helpers
def object_ports(role):
    """The frozen non-empty port groups of a role (adapter/artifact form)."""
    return {k: list(v) for k, v in PORTS[role].items() if v}


def port_projection(role):
    """The full frozen port SET of a role -- the checked projection that a WRL
    `{...}` brace group must reveal exactly (Slice 2.1)."""
    return set(PORTS[role]["in"]) | set(PORTS[role]["out"])


def validate_port_projection(role, tokens, object_id=None):
    """A WRL `{ports}` brace group is a CHECKED projection of the role's frozen
    ports: it must reveal the role signature exactly. A bogus token is rejected
    -- visible source is never silently ignored (Slice 2.1).

    `{}` is rejected for every role whose signature is NON-empty, which was
    every role when this was written. It is now ACCEPTED for `Mailbox`, whose
    frozen signature is genuinely empty (D8) -- and it is accepted by the same
    `got != want` comparison, with no mailbox case. That is the point: the rule
    was always "reveal the signature exactly", and "reject `{}`" was only ever
    a consequence of the table's contents. A hand-written "`{}` is invalid"
    check would have had to be found and edited here; there was nothing to edit.

    `object_id` names the offending object and is folded into a canonical
    `ObjectKey` locator (Slice B pre-freeze obligation, WRL Core 0.1.3 §16.3).
    Before this, `WRL_PORT_SIGNATURE` was the one identity-spine rejection that
    arrived with `primary_locator=None`, so a diagnostics consumer wanting to
    point at the bad node had to re-derive WHICH node from the message text --
    a second spelling of what the validator already knew, which is the
    forked-vocabulary defect in its diagnostic form. It stays OPTIONAL because
    the projection is also checked in contexts that have no object yet; an
    unlocated rejection is worse than a located one but better than a crash."""
    want = port_projection(role)
    got = set(tokens)
    if got != want:
        _fail(WRL_PORT_SIGNATURE,
              "%s ports %s do not match the frozen signature %s"
              % (role, sorted(got), sorted(want)),
              primary_locator=ObjectKey(object_id) if object_id else None,
              field_path="ports")


# ------------------------------------------------------------ payload helpers
def _rotor4(tok):
    """Coerce a rotor spec to a length-4 int tuple, or raise NUMERIC_RANGE."""
    if not (isinstance(tok, (tuple, list)) and len(tok) == 4):
        _fail(WRL_NUMERIC_RANGE, "rotor must have 4 lanes, got %r" % (tok,))
    try:
        return tuple(int(v) for v in tok)
    except (TypeError, ValueError):
        _fail(WRL_NUMERIC_RANGE, "rotor lanes must be integers: %r" % (tok,))


def route_key(route):
    """The canonical RouteKey of an AsyncRouteDecl record (body excluded)."""
    return RouteKey(route["source_id"], route["route_tag"],
                    route["mailbox_id"])


def routes_of(g):
    """The async routes of a graph-shaped object, tolerating older shapes.

    Every pre-Slice-B graph builder (`wrl_canvas`, `wrl_draft`, `wrl_legacy`,
    the `_ArtifactGraph` scratch view) constructs a graph and never sets
    `routes`. Reading through one accessor means those callers keep working and
    -- more importantly -- means there is ONE answer to "what are this graph's
    routes", so a caller cannot accidentally read a missing attribute as
    something other than 'none'."""
    return list(getattr(g, "routes", None) or ())


def route_claim_identity(routes):
    """`{RouteKey: (writer_id, sequence)}` -- the ADMIT identity each route
    mints (ruling Q4). `writer_id` is the reserved `ROUTE_WRITER_ID` and
    `sequence` is the route's ZERO-BASED ordinal in canonical RouteKey order.

    A pure function of the canonical route set, defined here rather than in the
    runtime because it is the thing that must not drift: the world's identity
    and the claim identities it mints have to be derived from the same ordering
    or a re-canonicalized world would mint different facts."""
    return {route_key(r): (ROUTE_WRITER_ID, i)
            for i, r in enumerate(sorted(routes, key=route_key))}


def _canon_payload_key(payload):
    """A deterministic sort key for a claim payload (surface-independent)."""
    kind = payload[0]
    if kind == "SetRotor":
        return (0, payload[1], tuple(int(v) for v in payload[2]))
    if kind == "ResetFault":
        return (1, payload[1], ())
    return (9, str(payload), ())


# --------------------------------------------------------------- validation
def validate_graph(g):
    """Typed structural validation of a canonical WRL graph against the
    frozen IR v1 registries. Raises WrlValidationError with a stable code.
    The IR validator -- not the Fixture constructor -- owns these errors."""
    if g.profile != PROFILE_ID:
        _fail(WRL_UNSUPPORTED_FEATURE,
              "unknown profile %r; this compiler only serves %s"
              % (g.profile, PROFILE_ID))

    # ---- objects: closed roles, unique ids, well-formed identifiers
    role_of = {}
    cfg_of = {}
    first_decl = {}
    for role, name, cfg in g.nodes:
        if role not in ROLE_IDS:
            _fail(WRL_UNSUPPORTED_FEATURE,
                  "role %r not in the frozen v1 registry %s" % (role, ROLE_IDS),
                  primary_locator=ObjectKey(name), field_path="role")
        if name in role_of:
            _fail(WRL_DUPLICATE_ID, "duplicate object id %r" % (name,),
                  primary_locator=ObjectKey(name),
                  related_locator=first_decl.get(name))
        if not name or set(name) - _IDENT_OK or "__" in name:
            _fail(WRL_UNSUPPORTED_FEATURE,
                  "bad object id %r (alnum/_ only, no '__')" % (name,),
                  primary_locator=ObjectKey(name), field_path="object_id")
        role_of[name] = role
        cfg_of[name] = cfg
        first_decl[name] = ObjectKey(name)
        _validate_config(role, name, cfg)

    # ---- edges: closed kinds, declared endpoints, legal port pairs
    sig_in_count, socket_in_count = {}, {}
    first_ctrl = {}
    for edge in g.edges:
        kind, s, d = edge
        ekey = EdgeKey(kind, s, d)
        if kind not in EDGE_KINDS:
            _fail(WRL_UNSUPPORTED_FEATURE,
                  "edge kind %r not in frozen v1 edges %s" % (kind, EDGE_KINDS),
                  primary_locator=ekey, field_path="kind")
        if s not in role_of:
            _fail(WRL_UNKNOWN_ENDPOINT, "edge source %r not declared" % (s,),
                  primary_locator=ekey, field_path="src")
        if d not in role_of:
            _fail(WRL_UNKNOWN_ENDPOINT,
                  "edge destination %r not declared" % (d,),
                  primary_locator=ekey, field_path="dst")
        out_port, in_port = EDGE_PORTS[kind]
        if out_port not in PORTS[role_of[s]]["out"]:
            _fail(WRL_ILLEGAL_PORT_PAIR,
                  "%s (%s) has no out-port %s for a %s"
                  % (s, role_of[s], out_port, kind),
                  primary_locator=ekey, related_locator=ObjectKey(s))
        if in_port not in PORTS[role_of[d]]["in"]:
            _fail(WRL_ILLEGAL_PORT_PAIR,
                  "%s (%s) has no in-port %s for a %s"
                  % (d, role_of[d], in_port, kind),
                  primary_locator=ekey, related_locator=ObjectKey(d))
        if kind == "SignalWire":
            sig_in_count[d] = sig_in_count.get(d, 0) + 1
        else:
            socket_in_count[d] = socket_in_count.get(d, 0) + 1
        first_ctrl.setdefault((kind, d), ekey)

    for d, c in sig_in_count.items():
        if c > 1:
            _fail(WRL_CONTROLLER_CONFLICT,
                  "%s has %d signal-wire inputs (a spinner admits one)"
                  % (d, c),
                  primary_locator=ObjectKey(d),
                  related_locator=first_ctrl.get(("SignalWire", d)))
    for d, c in socket_in_count.items():
        if c > 1:
            _fail(WRL_CONTROLLER_CONFLICT,
                  "%s has %d controllers (an orb admits one)" % (d, c),
                  primary_locator=ObjectKey(d),
                  related_locator=first_ctrl.get(("SocketControl", d)))

    _validate_routes(routes_of(g), role_of, cfg_of)

    # ---- run plan / epoch inputs (range only; targets are runtime-checked)
    if not isinstance(g.periods, int) or g.periods < 0:
        _fail(WRL_EPOCH_RANGE, "periods must be a non-negative integer")
    for e, batch in enumerate(g.batches):
        epoch = e + 1
        if not (1 <= epoch <= g.periods):
            _fail(WRL_EPOCH_RANGE,
                  "epoch %d out of range [1, %d]" % (epoch, g.periods))
    return g


def _validate_routes(routes, role_of, cfg_of):
    """Typed structural validation of the AsyncRouteDecl set (Slice B).

    Every rejection here describes a world that would seal, compile, and then
    provably fail to do the one thing it declared. A route to an undeclared
    mailbox is `unknown_mailbox` at runtime; an out-of-range body is
    `body_out_of_range`; a route from a `once(0)` pulser fires on an epoch that
    does not exist. All three are silent at every layer except the film, and
    the film is the last place you want to learn that a world was dead when it
    was written."""
    seen = {}
    by_epoch = {}
    for r in routes:
        if not isinstance(r, dict):
            _fail(WRL_MALFORMED_ARTIFACT, "route must be an object")
        _reject_unknown(r, ROUTE_FIELDS, "async route")
        missing = [k for k in ROUTE_FIELDS if k not in r]
        if missing:
            _fail(WRL_MALFORMED_ARTIFACT,
                  "async route missing field(s) %s" % missing)
        key = route_key(r)
        src, tag, mb = key

        for label, ident in (("source_id", src), ("route_tag", tag),
                             ("mailbox_id", mb)):
            if not isinstance(ident, str) or not ident \
                    or set(ident) - _IDENT_OK or "__" in ident:
                _fail(WRL_UNSUPPORTED_FEATURE,
                      "bad route %s %r (alnum/_ only, no '__')"
                      % (label, ident),
                      primary_locator=key, field_path=label)

        # DUPLICATES BEFORE THE BUDGET. Seven routes of which two are the same
        # route almost certainly meant six; reporting "too many routes" would
        # send the author to delete one they meant to keep.
        if key in seen:
            _fail(WRL_DUPLICATE_ROUTE,
                  "duplicate route %s (bodies %r and %r) -- the RouteKey "
                  "excludes the body, so this is one route declared twice, "
                  "not two routes" % (key.render(), seen[key], r.get("body")),
                  primary_locator=key, related_locator=key)
        seen[key] = r.get("body")

        # ---- source: a declared `once` Pulser that can actually fire (Q5)
        if src not in role_of:
            _fail(WRL_UNKNOWN_ENDPOINT, "route source %r not declared" % (src,),
                  primary_locator=key, field_path="source_id")
        if role_of[src] != "Pulser":
            _fail(WRL_ILLEGAL_ROUTE_ENDPOINT,
                  "route source %s is a %s; only a Pulser may emit a route"
                  % (src, role_of[src]),
                  primary_locator=key, related_locator=ObjectKey(src),
                  field_path="source_id")
        clock = tuple(cfg_of[src].get("clock") or ())
        fires_at = once_epoch(clock)
        if fires_at is None:
            _fail(WRL_ILLEGAL_ROUTE_ENDPOINT,
                  "route source %s has clock %r; Slice B routes are ONE-SHOT, "
                  "so the source must be `once` (a recurring route is deferred "
                  "to forge.world.async.v1)" % (src, clock or None),
                  primary_locator=key, related_locator=ObjectKey(src),
                  field_path="source_id")
        # `once(0)` is legal for a bare Pulser (epoch 0 is simply before the
        # run) but a route hung on one can never fire, so the world silently
        # does nothing. Refusing it is the difference between "declared and
        # provably ignored" and "declared and quietly dropped".
        if fires_at < 1:
            _fail(WRL_EPOCH_RANGE,
                  "route source %s fires at once(%d); epochs start at 1, so "
                  "this route could never fire" % (src, fires_at),
                  primary_locator=key, related_locator=ObjectKey(src),
                  field_path="source_id")
        # The firing epoch comes from the SAME accessor the runtime fold uses,
        # so the co-firing tally below cannot drift from the epoch the claim
        # will actually be observed at.
        by_epoch.setdefault(fires_at, []).append(key)

        # ---- target: a declared Mailbox (D8 -- addressed by id, never wired)
        if mb not in role_of:
            _fail(WRL_UNKNOWN_ENDPOINT,
                  "route mailbox %r not declared" % (mb,),
                  primary_locator=key, field_path="mailbox_id")
        if role_of[mb] != MAILBOX_ROLE:
            _fail(WRL_ILLEGAL_ROUTE_ENDPOINT,
                  "route target %s is a %s; a route addresses a %s"
                  % (mb, role_of[mb], MAILBOX_ROLE),
                  primary_locator=key, related_locator=ObjectKey(mb),
                  field_path="mailbox_id")

        # ---- body: the target mailbox's own declared lane width
        width = cfg_of[mb].get("w")
        if not route_body_in_range(width, r.get("body")):
            _fail(WRL_NUMERIC_RANGE,
                  "route %s body %r must be %d lanes in [0, 2^%s)"
                  % (key.render(), r.get("body"), ROUTE_BODY_LANES, width),
                  primary_locator=key, related_locator=ObjectKey(mb),
                  field_path="body")

    if len(routes) > MAX_ASYNC_ROUTES:
        _fail(WRL_ROUTE_BUDGET,
              "%d async routes declared; the bound is %d, because each route "
              "mints exactly one ClaimFact and the claim log holds %d"
              % (len(routes), MAX_ASYNC_ROUTES, MAX_ASYNC_ROUTES),
              primary_locator=route_key(sorted(routes, key=route_key)[-1]))

    # ---- co-firing: one epoch's worth of routes must fit ONE observation
    # batch (commit 4). AFTER the budget, because seven co-firing routes are
    # over both bounds and "declare fewer routes" is the coarser repair; a
    # world that is only over THIS bound gets the message about epochs.
    #
    # Keyed by EPOCH, not by source: two `once(1)` pulsers with three routes
    # each also deliver six claims in one batch, and a per-source tally would
    # wave that through.
    for ep in sorted(by_epoch):
        keys = by_epoch[ep]
        if len(keys) > MAX_ROUTE_COFIRE:
            _fail(WRL_ROUTE_BATCH_OVERFLOW,
                  "%d routes fire at epoch %d; one epoch's observation batch "
                  "holds %d, so this world crashes the reducer on the epoch it "
                  "was written to act on -- spread them across epochs"
                  % (len(keys), ep, MAX_ROUTE_COFIRE),
                  primary_locator=sorted(keys)[-1])


def _validate_config(role, name, cfg):
    loc = ObjectKey(name)
    if role == "Pulser":
        clock = cfg.get("clock")
        # a JSON round-trip (deserialize_artifact) yields lists, not tuples
        if not (isinstance(clock, (tuple, list)) and clock):
            _fail(WRL_CLOCK_RANGE, "pulser %s: missing clock" % (name,),
                  primary_locator=loc, field_path="static_config.clock")
        if clock[0] == "periodic":
            _, p, ph = clock
            if not (isinstance(p, int) and p >= 1):
                _fail(WRL_CLOCK_RANGE, "pulser %s: period >= 1" % (name,),
                      primary_locator=loc, field_path="static_config.clock")
            if not (isinstance(ph, int) and 0 <= ph < p):
                _fail(WRL_CLOCK_RANGE,
                      "pulser %s: phase in [0, period)" % (name,),
                      primary_locator=loc, field_path="static_config.clock")
        elif clock[0] == "once":
            _, e = clock
            if not (isinstance(e, int) and e >= 0):
                _fail(WRL_CLOCK_RANGE, "pulser %s: once epoch >= 0" % (name,),
                      primary_locator=loc, field_path="static_config.clock")
        else:
            _fail(WRL_UNSUPPORTED_FEATURE,
                  "pulser %s: clock mode %r (only periodic|once)"
                  % (name, clock[0]),
                  primary_locator=loc, field_path="static_config.clock")
    elif role == "Spinner":
        for key in ("w", "n", "rotor"):
            if cfg.get(key) is None:
                _fail(WRL_UNSUPPORTED_FEATURE,
                      "spinner %s: missing %r" % (name, key),
                      primary_locator=loc, field_path="static_config.%s" % key)
        w_, n_ = cfg["w"], cfg["n"]
        if not (isinstance(w_, int) and w_ > 0 and
                isinstance(n_, int) and 0 <= n_ <= w_):
            _fail(WRL_NUMERIC_RANGE, "spinner %s: bad lane geometry" % (name,),
                  primary_locator=loc, field_path="static_config.n")
        rot = _rotor4(cfg["rotor"])
        if not all(0 <= v < (1 << w_) for v in rot):
            _fail(WRL_NUMERIC_RANGE,
                  "spinner %s: rotor lanes out of [0, 2^%d)" % (name, w_),
                  primary_locator=loc, field_path="static_config.rotor")
    elif role == MAILBOX_ROLE:
        # MailboxDecl (D7). `w` bounds a message body lane, `cap` bounds how
        # many messages may be enqueued for one period. `cap` must be >= 1:
        # a zero-capacity mailbox could never accept a send, so it would be a
        # world that silently rejects everything -- exactly the class of
        # quiet failure Slice A's guards exist to prevent.
        for key in ("w", "cap"):
            if cfg.get(key) is None:
                _fail(WRL_UNSUPPORTED_FEATURE,
                      "mailbox %s: missing %r" % (name, key),
                      primary_locator=loc, field_path="static_config.%s" % key)
        w_, cap_ = cfg["w"], cfg["cap"]
        # Bound stated ONCE (MAILBOX_WIDTH_MAX) and shared with the Fixture
        # oracle. Previously the canonical validator accepted any w > 0 while
        # the oracle required w <= 32, so an artifact could seal successfully
        # and then be rejected by its own sanctioned oracle.
        if not (isinstance(w_, int) and 1 <= w_ <= MAILBOX_WIDTH_MAX):
            _fail(WRL_NUMERIC_RANGE,
                  "mailbox %s: body width must be in 1..%d"
                  % (name, MAILBOX_WIDTH_MAX),
                  primary_locator=loc, field_path="static_config.w")
        if not (isinstance(cap_, int) and cap_ >= 1):
            _fail(WRL_NUMERIC_RANGE,
                  "mailbox %s: capacity must be >= 1" % (name,),
                  primary_locator=loc, field_path="static_config.cap")


# --------------------------------------------------------------- canonicalize
def canonicalize_graph(g):
    """Return a NEW graph with an order-independent canonical form: objects
    sorted IDENTITY-FIRST by (object_id, role), edges sorted by (kind, src,
    dst), rotor lanes normalized to int tuples, and each epoch's claim batch
    sorted by a surface-independent payload key. Declaration order and surface
    syntax no longer affect the bytes. Identity-first ordering is stable even
    if the role registry expands (Slice 2.1)."""
    cg = type(g)()
    cg.profile = g.profile
    cg.periods = g.periods
    cg.nodes = sorted(((role, name, _canon_config(role, cfg))
                       for role, name, cfg in g.nodes),
                      key=lambda t: (t[1], t[0]))
    cg.edges = sorted((kind, s, d) for (kind, s, d) in g.edges)
    # Routes sort by RouteKey, so declaration order carries no meaning -- and
    # because Q4 makes a route's ADMIT `sequence` its ordinal in THIS order,
    # sorting here is what makes the minted claim identities a function of the
    # world rather than of how the author happened to type it.
    cg.routes = sorted((_canon_route(r) for r in routes_of(g)), key=route_key)
    cg.batches = []
    for batch in g.batches:
        cg.batches.append(sorted(
            ({"writer_id": c["writer_id"], "sequence": c["sequence"],
              "payload": _canon_payload(c["payload"])} for c in batch),
            key=lambda c: (_canon_payload_key(c["payload"]),
                           -1 if c["writer_id"] is None else c["writer_id"],
                           -1 if c["sequence"] is None else c["sequence"])))
    return cg


def _canon_config(role, cfg):
    out = dict(cfg)
    if role == "Spinner" and cfg.get("rotor") is not None:
        out["rotor"] = _rotor4(cfg["rotor"])
        out["configurable"] = bool(cfg.get("configurable", False))
    return out


def _canon_route(route):
    """Normalize one AsyncRouteDecl. The body is POSITIONAL (b0..b3) and is
    never reordered; it is only coerced from a JSON round-trip's list form back
    to an int tuple, exactly as a rotor is."""
    if not isinstance(route, dict):
        _fail(WRL_MALFORMED_ARTIFACT, "route must be an object")
    # The shape gate has to be HERE and not only in `_validate_routes`, because
    # canonicalization runs FIRST on the graph path (`lower_graph`) and sorts by
    # RouteKey. A record missing `source_id` would sort a None against a str and
    # die in `sorted()` with a bare TypeError -- an untyped crash standing in
    # for what is simply a malformed record.
    _reject_unknown(route, ROUTE_FIELDS, "async route")
    for k in ROUTE_FIELDS:
        if k not in route:
            _fail(WRL_MALFORMED_ARTIFACT,
                  "async route missing field %r" % (k,))
    for k in ("source_id", "route_tag", "mailbox_id"):
        if not isinstance(route[k], str):
            _fail(WRL_MALFORMED_ARTIFACT,
                  "async route %s must be a string, got %r" % (k, route[k]))
    body = route.get("body")
    if isinstance(body, (tuple, list)):
        try:
            body = tuple(int(v) for v in body)
        except (TypeError, ValueError):
            _fail(WRL_NUMERIC_RANGE,
                  "route body lanes must be integers: %r" % (body,))
    return {"source_id": route.get("source_id"),
            "route_tag": route.get("route_tag"),
            "mailbox_id": route.get("mailbox_id"),
            "body": body}


def _canon_payload(payload):
    if payload[0] == "SetRotor":
        return ("SetRotor", payload[1], _rotor4(payload[2]))
    if payload[0] == "ResetFault":
        return ("ResetFault", payload[1])
    return payload


# ------------------------------------------------- serialization / identity
def _plain(obj):
    """Recursively convert tuples to lists so the JSON form is stable and
    round-trips (json.loads yields lists; re-serialization must match)."""
    if isinstance(obj, (tuple, list)):
        return [_plain(x) for x in obj]
    if isinstance(obj, dict):
        return {k: _plain(v) for k, v in obj.items()}
    return obj


def serialize_artifact(artifact):
    """Deterministic canonical bytes of the STATIC semantic artifact. Keys
    sorted; tuples flattened to arrays; compact separators. The object and
    edge LISTS are pre-sorted by graph_to_ir; sort_keys covers dict order."""
    return json.dumps(_plain(artifact), sort_keys=True,
                      separators=(",", ":")).encode()


def deserialize_artifact(blob):
    return json.loads(blob.decode())


def _sha(blob):
    return hashlib.sha256(blob).hexdigest()


# ---------------------------------------------------- sealing / validation
def _nonempty_str(v):
    return isinstance(v, str) and v != ""


def validate_artifact_v1(artifact):
    """Full structural validation of a STATIC semantic artifact before it may
    be given an identity (Slice 2.1). Rejects null/empty policy ids, unknown
    schema ids, unsupported ir/profile versions, and malformed object/edge
    records. `deserialize_artifact` yields arbitrary JSON, so the hash path
    MUST run this first -- an unsealed policy can never be hashed into an
    official-looking SemanticArtifactID."""
    if not isinstance(artifact, dict):
        _fail(WRL_MALFORMED_ARTIFACT, "artifact must be an object")
    _reject_unknown(artifact, ARTIFACT_FIELDS, "artifact")
    # ir_version is now ROLE-DERIVED (v1.1 mailbox surface), so the exact
    # value is checked below once the roles are known. Here we only reject
    # revisions this compiler does not serve at all.
    if artifact.get("ir_version") not in (IR_VERSION, IR_VERSION_V1_1):
        _fail(WRL_MALFORMED_ARTIFACT,
              "unsupported ir_version %r (only %s / %s)"
              % (artifact.get("ir_version"), IR_VERSION, IR_VERSION_V1_1))
    if artifact.get("profile_id") != PROFILE_ID:
        _fail(WRL_UNSUPPORTED_FEATURE,
              "unknown profile %r; this compiler only serves %s"
              % (artifact.get("profile_id"), PROFILE_ID))

    pol = artifact.get("semantic_policies")
    if not isinstance(pol, dict):
        _fail(WRL_MALFORMED_ARTIFACT, "missing semantic_policies block")
    _reject_unknown(pol, POLICY_FIELDS, "semantic_policies",
                    path_prefix="semantic_policies")
    for key in REQUIRED_POLICY_IDS:
        if not _nonempty_str(pol.get(key)):
            _fail(WRL_UNSEALED_POLICY,
                  "semantic policy %r is null/empty; a sealed artifact must "
                  "name the law that gives it meaning" % (key,))
    npi = pol.get("numeric_policy_ids")
    if not (isinstance(npi, list) and npi and all(_nonempty_str(x)
                                                  for x in npi)):
        _fail(WRL_UNSEALED_POLICY,
              "numeric_policy_ids must be a non-empty list of ids")

    objects = artifact.get("objects")
    edges = artifact.get("edges")
    if not isinstance(objects, list) or not isinstance(edges, list):
        _fail(WRL_MALFORMED_ARTIFACT, "objects/edges must be lists")

    # D6/Q2: the schema block is DETERMINED BY THE ROLES PRESENT, so it cannot
    # be chosen independently of the world. A mailbox-free world must declare
    # RuntimeStateV1 and a mailbox-bearing world must declare RuntimeStateV1_1;
    # either mismatch is a typed rejection rather than a silent acceptance.
    try:
        _roles = [o["role"] for o in objects]
    except (KeyError, TypeError) as ex:
        _fail(WRL_MALFORMED_ARTIFACT, "malformed object record: %r" % (ex,))
    _surface = semantic_surface_for_roles(_roles)
    _want_schemas = schemas_for_roles(_roles)
    if artifact.get("schemas") != _want_schemas:
        _fail(WRL_MALFORMED_ARTIFACT,
              "schema block %r does not match the roles present (expected %s)"
              % (artifact.get("schemas"), _want_schemas))

    # The SAME derivation governs the other three semantic identity fields, so
    # a mailbox-bearing artifact CANNOT name the mailbox-free ADMIT policy, the
    # frozen film schema, or IR v1.0 -- and a mailbox-free artifact cannot
    # borrow the mailbox surface. Without this an artifact's identity could
    # claim one semantics while the runner executed another.
    if artifact.get("ir_version") != _surface["ir_version"]:
        _fail(WRL_MALFORMED_ARTIFACT,
              "ir_version %r does not match the roles present (expected %r)"
              % (artifact.get("ir_version"), _surface["ir_version"]))
    for _key in ("admit_policy_id", "film_schema_id"):
        if pol.get(_key) != _surface[_key]:
            _fail(WRL_UNSEALED_POLICY,
                  "semantic_policies.%s is %r but the roles present require "
                  "%r -- the artifact must name the semantics it executes"
                  % (_key, pol.get(_key), _surface[_key]))

    try:
        for o in objects:
            role = o["role"]
            oid = o.get("object_id")
            _reject_unknown(o, OBJECT_FIELDS, "object %r" % (oid,),
                            primary_locator=ObjectKey(oid))
            if role in ROLE_CONFIG_SCHEMA:
                sc = o.get("static_config") or {}
                _reject_unknown(
                    sc, ROLE_CONFIG_SCHEMA[role]["static_config_keys"],
                    "object %r static_config" % (oid,),
                    primary_locator=ObjectKey(oid),
                    path_prefix="static_config")
            if o["state_schema_ref"] != "state.%s.v1" % str(role).lower():
                _fail(WRL_MALFORMED_ARTIFACT,
                      "object %r: state_schema_ref %r != role %r"
                      % (oid, o.get("state_schema_ref"), role),
                      primary_locator=ObjectKey(oid),
                      field_path="state_schema_ref")
            if role in ROLE_IDS and o.get("ports") != object_ports(role):
                _fail(WRL_MALFORMED_ARTIFACT,
                      "object %r: ports %r != frozen %r"
                      % (oid, o.get("ports"), object_ports(role)),
                      primary_locator=ObjectKey(oid), field_path="ports")
        for e in edges:
            _reject_unknown(e, EDGE_FIELDS, "edge record")
        gnodes = [(o["role"], o["object_id"], o["static_config"])
                  for o in objects]
        gedges = [(e["kind"], e["src"], e["dst"]) for e in edges]
    except (KeyError, TypeError) as ex:
        _fail(WRL_MALFORMED_ARTIFACT, "malformed object/edge record: %r" % (ex,))

    # `async_routes` is optional, but an EMPTY one is not a legal canonical
    # encoding -- the canonicalizer omits the key entirely (see
    # ARTIFACT_FIELDS). Accepting `[]` here would let a hand-built artifact
    # carry a second spelling of "no routes" past the identity spine, and
    # `_seal` re-validates the CANONICAL form, so a tolerated `[]` would only
    # ever be visible on the raw side of the boundary -- which is exactly where
    # a second spelling does its damage.
    if "async_routes" in artifact:
        routes = artifact["async_routes"]
        if not isinstance(routes, list):
            _fail(WRL_MALFORMED_ARTIFACT, "async_routes must be a list")
        if not routes:
            _fail(WRL_MALFORMED_ARTIFACT,
                  "async_routes is present but empty; a route-free world omits "
                  "the field entirely (there is exactly one encoding of 'no "
                  "routes')")
    else:
        routes = []

    # reuse the graph structural validator (roles, ports, controller conflict,
    # AND the route laws -- one validator, so an artifact that arrived by
    # deserialization is held to the same route rules as parsed text)
    scratch = _ArtifactGraph(artifact.get("profile_id"), gnodes, gedges,
                             routes)
    validate_graph(scratch)
    return artifact


class _ArtifactGraph:
    """A minimal graph view over an artifact for reuse of validate_graph
    (no run inputs live in the static artifact)."""
    def __init__(self, profile, nodes, edges, routes=()):
        self.profile = profile
        self.nodes = nodes
        self.edges = edges
        self.routes = list(routes)
        self.periods = 0
        self.batches = []


def canonicalize_artifact_v1(artifact):
    """Normalize a valid-shaped artifact to its CANONICAL form so that any two
    reorder-equivalent artifacts serialize to identical bytes (Phase 3C-0).
    Normalizes: objects by (object_id, role), edges by (kind, src, dst),
    numeric_policy_ids (ordering carries no meaning), each port array, and the
    tuple/list/dict representation via the plain-form conversion. Rotor lanes
    and clock fields are POSITIONAL and are never reordered. Tolerant of shape
    (the returned value is re-validated by the caller)."""
    if not isinstance(artifact, dict):
        _fail(WRL_MALFORMED_ARTIFACT, "artifact must be an object")
    try:
        pol = artifact["semantic_policies"]
        cobjs = sorted(
            ({"object_id": o["object_id"], "role": o["role"],
              "static_config": _plain(o["static_config"]),
              "state_schema_ref": o["state_schema_ref"],
              "ports": {k: sorted(v) for k, v in o["ports"].items()}}
             for o in artifact["objects"]),
            key=lambda o: (o["object_id"], o["role"]))
        cedges = sorted(
            ({"kind": e["kind"], "src": e["src"], "dst": e["dst"]}
             for e in artifact["edges"]),
            key=lambda e: (e["kind"], e["src"], e["dst"]))
        cpol = {
            "rulepack_id": pol["rulepack_id"],
            "numeric_policy_ids": sorted(pol["numeric_policy_ids"]),
            "admit_policy_id": pol["admit_policy_id"],
            "film_schema_id": pol["film_schema_id"],
        }
        cart = {
            "ir_version": artifact["ir_version"],
            "profile_id": artifact["profile_id"],
            "semantic_policies": cpol,
            "schemas": _plain(artifact["schemas"]),
            "objects": cobjs,
            "edges": cedges,
        }
        # CANONICAL OMISSION. The key appears iff the world declares a route,
        # so a route-free world's canonical bytes are BYTE-IDENTICAL to what
        # they were before Slice B existed -- which is what keeps the frozen
        # demo sealing to sem-8ae91fe9...fe4a and every prior id untouched.
        # An `async_routes: []` on the way in canonicalizes to no key at all,
        # so "absent" and "empty" are one world with one identity.
        croutes = sorted((_canon_route(r)
                          for r in (artifact.get("async_routes") or ())),
                         key=route_key)
        if croutes:
            cart["async_routes"] = croutes
    except (KeyError, TypeError, AttributeError) as ex:
        _fail(WRL_MALFORMED_ARTIFACT, "malformed artifact: %r" % (ex,))
    return _plain(cart)


def _seal(artifact):
    """The public identity path: validate shape -> canonicalize -> validate
    canonical -> serialize. Returns (canonical_isolated_artifact, bytes). The
    canonical value is a fresh, isolated structure (plain-form deep copy), so
    later caller mutation cannot change an issued identity."""
    validate_artifact_v1(artifact)
    canon = canonicalize_artifact_v1(artifact)
    validate_artifact_v1(canon)
    return canon, serialize_artifact(canon)


def validate_lowering_profile_v1(profile):
    """A backend lowering profile must be fully specified AND in-domain before
    it may earn a BackendArtifactID (Phase 3D.1-A). The profile is now
    OPERATIVE: `counter_encoding` (auto|one_hot|binary) + a positive int
    `onehot_max` actually select the counter representation the compiler emits.
    `lowering_profile_version` must be the supported version; the remaining
    fields stay open strings until the compiler/target registries freeze. A
    half-specified or out-of-domain backend must not receive an official-looking
    identity."""
    if not isinstance(profile, dict):
        _fail(WRL_BAD_LOWERING_PROFILE, "lowering profile must be an object")
    for key in REQUIRED_LOWERING_KEYS:
        if key == "onehot_max":
            continue
        if not _nonempty_str(profile.get(key)):
            _fail(WRL_BAD_LOWERING_PROFILE,
                  "lowering profile missing/empty %r" % (key,))
    if profile["counter_encoding"] not in COUNTER_ENCODINGS:
        _fail(WRL_BAD_LOWERING_PROFILE,
              "unknown counter_encoding %r (only %s)"
              % (profile["counter_encoding"], COUNTER_ENCODINGS))
    om = profile.get("onehot_max")
    if not (isinstance(om, int) and not isinstance(om, bool) and om >= 1):
        _fail(WRL_BAD_LOWERING_PROFILE,
              "onehot_max must be a positive integer, got %r" % (om,))
    if profile["lowering_profile_version"] != LOWERING_PROFILE_VERSION:
        _fail(WRL_BAD_LOWERING_PROFILE,
              "unsupported lowering_profile_version %r (only %s)"
              % (profile["lowering_profile_version"], LOWERING_PROFILE_VERSION))
    return profile


def validate_semantic_id(semantic_id):
    """A BackendArtifactID must fold in a WELL-FORMED SemanticArtifactID:
    `sem-` followed by exactly 64 lowercase hex digits (Phase 3C-0)."""
    if not (isinstance(semantic_id, str) and _SEM_ID_RE.match(semantic_id)):
        _fail(WRL_BAD_LOWERING_PROFILE,
              "malformed semantic id %r (expect sem-<64 lowercase hex>)"
              % (semantic_id,))
    return semantic_id


class SealedArtifact:
    """A validated + CANONICAL static artifact carrying its SemanticArtifactID.
    Constructing one is the sealing gate -- it fails on any unsealed policy or
    malformed record, and normalizes reorder-equivalent inputs to one identity.

    Phase 3D.1.1 -- SEALED OBJECT INTEGRITY. The seal stores the CANONICAL BYTES,
    not a mutable dictionary. `.artifact` deserializes a FRESH copy on every read
    (mutating it can never touch the seal); `.semantic_id` is DERIVED from the
    bytes inside the constructor and is not a caller-writable field. The object
    is immutable: any attribute assignment or deletion raises WRL_SEALED_IMMUTABLE
    (D30). Mutating the original input after sealing has no effect because the
    bytes were already frozen (D28)."""
    __slots__ = ("_canonical_bytes", "_semantic_id")

    def __init__(self, artifact):
        _, blob = _seal(artifact)
        object.__setattr__(self, "_canonical_bytes", blob)
        object.__setattr__(self, "_semantic_id", "sem-" + _sha(blob))

    def __setattr__(self, name, value):
        _fail(WRL_SEALED_IMMUTABLE,
              "SealedArtifact is immutable; cannot assign %r" % (name,))

    def __delattr__(self, name):
        _fail(WRL_SEALED_IMMUTABLE,
              "SealedArtifact is immutable; cannot delete %r" % (name,))

    @property
    def canonical_bytes(self):
        """The frozen canonical serialization the SemanticArtifactID is over."""
        return self._canonical_bytes

    @property
    def artifact(self):
        """A FRESH isolated copy of the canonical artifact on every read."""
        return deserialize_artifact(self._canonical_bytes)

    @property
    def semantic_id(self):
        return self._semantic_id


def seal_artifact(artifact):
    """Validate, canonicalize, then seal a static artifact. Rejects null/empty
    policy ids, unknown schemas, unsupported versions, and malformed records;
    reorder-equivalent artifacts seal to identical bytes and identity."""
    return SealedArtifact(artifact)


def semantic_artifact_id(artifact):
    """SemanticArtifactID = Hash(CANONICAL Forge IR + semantic policy refs). A
    pure function of the frozen semantic graph -- independent of backend
    encoding, run plan, claim batches, AND object/edge/policy ORDER. The
    artifact is validated and canonicalized before it is hashed (Phase 3C-0):
    an unsealed policy can never earn an identity, and two reorder-equivalent
    artifacts get the same id. Accepts a raw artifact dict or a SealedArtifact.

    Phase 3D.1.1: for a SealedArtifact the id is recomputed straight from the
    seal's CANONICAL BYTES rather than trusting a stored field, so the returned
    id always agrees with the sealed bytes (D35)."""
    if isinstance(artifact, SealedArtifact):
        return "sem-" + _sha(artifact.canonical_bytes)
    _, blob = _seal(artifact)
    return "sem-" + _sha(blob)


def backend_artifact_id(semantic_id, lowering_profile):
    """BackendArtifactID = Hash(SemanticArtifactID + lowering profile). Both the
    SemanticArtifactID (well-formed `sem-<64 hex>`) and the lowering profile
    (encoding/version domain) are VALIDATED before hashing (Phase 3C-0). Two
    profiles that differ ONLY in a backend representation share the
    SemanticArtifactID but not this one; a semantic change already moved the
    SemanticArtifactID."""
    validate_semantic_id(semantic_id)
    validate_lowering_profile_v1(lowering_profile)
    body = {"semantic": semantic_id,
            "lowering": _plain(lowering_profile)}
    return "bknd-" + _sha(json.dumps(body, sort_keys=True,
                                     separators=(",", ":")).encode())
