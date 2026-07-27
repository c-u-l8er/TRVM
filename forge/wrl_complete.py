"""wrl_complete.py v0.1 -- Phase 3B-5: completion metadata for WRL Core.

The completion half of 3B-5. It exposes the frozen WRL Core vocabulary as
structured METADATA an editor can drive completions from, plus a cursor-aware
`completions_at(src, offset)`.

The 3B discipline applied to completion: every candidate is a PURE PROJECTION of
the frozen registries (`wrl_canonical.ROLE_IDS`/`PORTS`/`EDGE_PORTS`, `wrl_ir`'s
role/edge tables, and the 3B-4 frozen named-rotor + concise-clock sugar) --
NEVER a hand-authored constant that could drift, and never an invented token. So
a completion can only ever offer something the parser already accepts, and the
metadata provably cannot contradict the frozen surface (binding_run12: every
candidate list is a subset of its registry; every applied completion parses).

Completion is entirely read-only: it never builds or touches a semantic graph,
so it cannot perturb any identity.
"""
import os
import re
import sys
from collections import namedtuple

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import wrl_canonical as WC
import wrl_ir as W
import wrl_sugar as SG

COMPLETE_VERSION = "wrlcomplete.v1"

# reverse of wrl_ir's parse tables -> the surface lexemes (frozen projection)
_ROLE_TOKEN_OF = {rid: tok for tok, rid in W._ROLE_TOKEN.items()}
_EDGE_TAG_OF = {kind: tag for tag, kind in W._EDGE_TAG.items()}

# completion contexts
ROLE = "role"
PORT = "port"
EDGE_TAG = "edge_tag"
ROTOR_VALUE = "rotor_value"
CLOCK_FORM = "clock_form"
CONFIG_KEY = "config_key"
NONE = "none"


class Completion(namedtuple("Completion", "context prefix candidates")):
    """A completion result at a cursor: the classified `context`, the `prefix`
    already typed, and the frozen `candidates` (already prefix-filtered)."""
    __slots__ = ()


# --------------------------------------------------- frozen candidate reads
def role_completions():
    """The frozen role surface tokens an author can actually TYPE
    (pulser/relay/door/spinner/orb).

    Sourced from the WRL Core surface table, NOT from `WC.ROLE_IDS`. Those two
    are not equal: a role can be in the registry with no text spelling (see
    `wrl_ir.unwritable_role_ids`). Reading the registry and subscripting the
    surface table with it made this function raise a bare KeyError the moment
    that gap opened -- and a completion API that crashes on a legal registry is
    worse than one that omits a candidate.

    Offering an unwritable role would also be wrong on its own terms: a
    completion is a promise that the text is acceptable if accepted, and
    `[mailbox:m0]` is not."""
    return tuple(sorted(W._ROLE_TOKEN))


def edge_tag_completions():
    """The 2 frozen edge surface tags (sig/socket)."""
    return tuple(sorted(_EDGE_TAG_OF[k] for k in WC.EDGE_KINDS))


def port_completions(role):
    """The frozen port projection for a role (accepts a role id or surface
    token). Ports come straight from the registry, never invented."""
    rid = W._ROLE_TOKEN.get(role, role)
    return tuple(sorted(WC.port_projection(rid)))


def config_key_completions(role):
    """The frozen surface config keys for a role, read straight from the
    authoritative `wrl_canonical.ROLE_CONFIG_SCHEMA` (Phase 3B.5.1) -- completion
    reads the grammar, it does not mirror it."""
    rid = W._ROLE_TOKEN.get(role, role)
    schema = WC.ROLE_CONFIG_SCHEMA.get(rid)
    return tuple(schema["surface_keys"]) if schema else ()


def named_rotor_completions():
    """The full accepted named-rotor vocabulary, read from the authoritative
    `wrl_sugar.ALL_ROTOR_NAMES` (the frozen EXACT table + the policy-governed
    names like `quarter_turn_z` under `forge_named_rotor_rne_sym_v1`) -- so a
    name the desugarer accepts is always offered, and vice versa."""
    return tuple(sorted(SG.ALL_ROTOR_NAMES))


def clock_form_completions():
    """The frozen concise-clock surface forms, read from the authoritative
    `wrl_sugar.CLOCK_SUGAR_FORMS`."""
    return tuple(SG.CLOCK_SUGAR_FORMS)


# ------------------------------------------------------- metadata manifest
def surface_metadata():
    """The whole frozen WRL Core vocabulary as a structured manifest -- a PURE
    projection of the SURFACE table, so it can never drift from what the parser
    accepts. Suitable as the static backing data for an editor's completions.

    `roles` is keyed by surface lexeme and therefore covers exactly the roles
    that can be written down. It previously walked `WC.ROLE_IDS` instead, which
    made the "can never drift" claim false in both directions at once: it raised
    KeyError on a registry role with no lexeme, and it would silently have
    advertised such a role to an editor if it had not.

    The gap itself is not hidden -- it is reported under `unwritable_roles`, so
    a tool can SEE that the surface is a strict subset of the registry instead
    of having to infer it from an absence."""
    roles = {}
    for tok in sorted(W._ROLE_TOKEN):
        rid = W._ROLE_TOKEN[tok]
        roles[tok] = {
            "role_id": rid,
            "ports": list(port_completions(rid)),
            "config_keys": list(config_key_completions(rid)),
        }
    edges = {}
    for kind in WC.EDGE_KINDS:
        src_port, dst_port = WC.EDGE_PORTS[kind]
        edges[_EDGE_TAG_OF[kind]] = {
            "kind": kind, "src_port": src_port, "dst_port": dst_port,
        }
    return {
        "version": COMPLETE_VERSION,
        "roles": roles,
        # registry roles with no surface lexeme. Normally `[]`. Reported rather
        # than omitted so the surface/registry gap is VISIBLE to tooling.
        "unwritable_roles": list(W.unwritable_role_ids()),
        "edge_tags": edges,
        "named_rotors": list(named_rotor_completions()),
        "clock_forms": list(clock_form_completions()),
    }


# --------------------------------------------------- cursor classification
def _line_bounds(src, offset):
    start = src.rfind("\n", 0, offset) + 1
    end = src.find("\n", offset)
    if end == -1:
        end = len(src)
    return start, end


def _innermost_open(before):
    """The (char, index) of the last still-open bracket in `before`, or
    (None, -1). Handles [], (), {} with a simple stack."""
    stack = []
    pairs = {")": "(", "]": "[", "}": "{"}
    for i, ch in enumerate(before):
        if ch in "([{":
            stack.append((ch, i))
        elif ch in ")]}":
            if stack and stack[-1][0] == pairs[ch]:
                stack.pop()
    return stack[-1] if stack else (None, -1)


def _enclosing_role_token(before, open_idx):
    """The role surface token of the `[role:...` that most recently opened
    before `open_idx` (for port/config/rotor context). None if not found."""
    m = None
    for mm in re.finditer(r"\[(\w+):", before[:open_idx + 1]):
        m = mm
    return m.group(1) if m else None


def _filter(prefix, candidates):
    return tuple(c for c in candidates if c.startswith(prefix))


def completions_at(src, offset):
    """Classify the cursor at `offset` and return the frozen `Completion`.
    Context rules (all candidates are frozen-registry reads):

      * inside `{ ... }`          -> the enclosing role's ports
      * right after `[` (no `:`)  -> role tokens
      * inside `( ... )` after `rotor=<alpha>` -> named rotors
      * inside a Pulser `( ... )` bare word     -> clock forms
      * inside `( ... )` otherwise -> the role's config keys
      * after `-- <word>` (no `-->` yet)        -> edge tags
      * otherwise                  -> NONE
    """
    lo, _hi = _line_bounds(src, offset)
    before = src[lo:offset]
    ch, idx = _innermost_open(before)

    if ch == "{":
        role = _enclosing_role_token(before, idx)
        seg = before[idx + 1:]
        prefix = re.split(r"[,\s]", seg)[-1].strip()
        cands = port_completions(role) if role else ()
        return Completion(PORT, prefix, _filter(prefix, cands))

    if ch == "[":
        seg = before[idx + 1:]
        if ":" not in seg:
            return Completion(ROLE, seg.strip(), _filter(seg.strip(),
                                                         role_completions()))
        return Completion(NONE, "", ())

    if ch == "(":
        role = _enclosing_role_token(before, idx)
        seg = before[idx + 1:]
        mrot = re.search(r"rotor=([A-Za-z_]\w*)$", seg)
        if mrot:
            pfx = mrot.group(1)
            return Completion(ROTOR_VALUE, pfx,
                              _filter(pfx, named_rotor_completions()))
        # a pulser paren with NO `=` yet is the concise-clock sugar slot;
        # once a `k=v` appears it is the verbose form -> config keys.
        if role == "pulser" and "=" not in seg:
            token = seg.strip()
            return Completion(CLOCK_FORM, token,
                              _filter(token, clock_form_completions()))
        token = re.split(r",", seg)[-1]
        key = re.split(r"=", token)[0].strip()
        key = re.split(r"\s+", key)[-1] if key else ""
        return Completion(CONFIG_KEY, key,
                          _filter(key, config_key_completions(role)))

    m = re.search(r"--(\w*)$", before)
    if m and "-->" not in before[m.start():]:
        pfx = m.group(1)
        return Completion(EDGE_TAG, pfx, _filter(pfx, edge_tag_completions()))

    return Completion(NONE, "", ())
