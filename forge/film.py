"""film.py -- portable canonical film encoding (binding slice v0.1).

The film is the shared observable: a canonical byte serialization of the
dynamic projection of the world at an epoch boundary, hashed per epoch.
Both sides -- the semantic model (e2_model.World) and the interaction-
calculus lowering -- must produce these bytes independently; parity is
byte parity, compared as SHA-256 per epoch.

Names are canonical ROLE names ("p3", "seed", "door", "r1", "r2",
"w_pd", "w_sr", "w_12", "w_21"), not model instance ids: the portable
encoding defines the shared namespace, and the fixture manifest records
the model-oid <-> role binding plus the rulepack hash, so the film is
runtime-independent by construction.
"""
import hashlib


def film_bytes(t, pulsers, doors, relays, wires, spinners=None, orbs=None):
    """v0.3 (review round 7): the clock line carries MODE and the DONE
    latch, so the film fully describes the state that determines future
    firing -- two worlds with different latches can no longer share a
    film. pulsers: [(role, mode, period_or_epoch, phase, armed, done)]
    with mode in {periodic, once}. v0.4 (review round 8): the line also
    carries NF = next_fire_in, the representation-independent clock
    POSITION -- on the model side derived from (t, config); on the
    compiler side derived from the DECODED COUNTER -- so a counter
    inconsistent with t (same film, different future under v0.3) now
    diverges the film immediately. done: authoritative latch compiler-
    side, horizon-scoped predicate model-side; nf = -1 once done."""
    lines = ["FILM v0.5", f"t={t}"]
    # v0.5 (round 12): the film carries authoritative pose state --
    # numeric policy id, lane geometry, pose/rotor lanes as fixed-width
    # big-endian two's-complement hex, controller/socket relationship,
    # and the numeric-fault latch. Present (possibly empty) in every
    # film; the version line bumps every hash so both sides move
    # together.
    for (r, pol, w, n, lanes, sock) in sorted(kw.get("spinners", []) if False else (spinners or [])):
        lb = ",".join(f"{v & ((1 << w) - 1):0{(w + 3) // 4}x}"
                      for v in lanes)
        lines.append(f"spinner:{r}:policy={pol},quat4,w={w},n={n},"
                     f"rotor={lb},socket={sock}")
    for (r, pol, w, n, lanes, ctl, fault) in sorted(orbs or []):
        lb = ",".join(f"{v & ((1 << w) - 1):0{(w + 3) // 4}x}"
                      for v in lanes)
        lines.append(f"orb:{r}:policy={pol},quat4,w={w},n={n},"
                     f"pose={lb},controller={ctl},fault={int(fault)}")
    for (r, mode, p, ph, a, dn, nf) in sorted(pulsers):
        lines.append(f"pulser:{r}:mode={mode},p={p},phase={ph},"
                     f"armed={int(a)},done={int(dn)},nf={nf}")
    for (r, o, n) in sorted(doors):
        lines.append(f"door:{r}:open={int(o)},next_open={int(n)}")
    for (r, c, n) in sorted(relays):
        lines.append(f"relay:{r}:cur_out={int(c)},next_out={int(n)}")
    for (r, c, n) in sorted(wires):
        lines.append(f"wire:{r}:cur={int(c)},nxt={int(n)}")
    return ("\n".join(lines) + "\n").encode()


def film_hash(*args, **kw):
    return hashlib.sha256(film_bytes(*args, **kw)).hexdigest()


def film_bytes_v6(t, pulsers, doors, relays, wires, spinners=None,
                  orbs=None):
    """FILM v0.6 (slice 3b.5d-2): the rotor is read from circuit STATE,
    not from a fixture constant; the spinner record additionally carries
    its config PERMISSION (fixed|configurable) -- a permission distinction
    only, the state layout is uniform. The numeric-fault latch on the orb
    record is authoritative STICKY state. Every v0.6 world uses this; v0.5
    is retained for historical replay only.
    spinners: [(role, policy, w, n, rotor_lanes, socket, perm)];
    orbs: [(role, policy, w, n, pose_lanes, controller, fault)]."""
    lines = ["FILM v0.6", f"t={t}"]
    for (r, pol, w, n, lanes, sock, perm) in sorted(spinners or []):
        lb = ",".join(f"{v & ((1 << w) - 1):0{(w + 3) // 4}x}"
                      for v in lanes)
        lines.append(f"spinner:{r}:policy={pol},quat4,w={w},n={n},"
                     f"rotor={lb},socket={sock},config={perm}")
    for (r, pol, w, n, lanes, ctl, fault) in sorted(orbs or []):
        lb = ",".join(f"{v & ((1 << w) - 1):0{(w + 3) // 4}x}"
                      for v in lanes)
        lines.append(f"orb:{r}:policy={pol},quat4,w={w},n={n},"
                     f"pose={lb},controller={ctl},fault={int(fault)}")
    for (r, mode, p, ph, a, dn, nf) in sorted(pulsers):
        lines.append(f"pulser:{r}:mode={mode},p={p},phase={ph},"
                     f"armed={int(a)},done={int(dn)},nf={nf}")
    for (r, o, n) in sorted(doors):
        lines.append(f"door:{r}:open={int(o)},next_open={int(n)}")
    for (r, c, n) in sorted(relays):
        lines.append(f"relay:{r}:cur_out={int(c)},next_out={int(n)}")
    for (r, c, n) in sorted(wires):
        lines.append(f"wire:{r}:cur={int(c)},nxt={int(n)}")
    return ("\n".join(lines) + "\n").encode()


def film_hash_v6(*args, **kw):
    return hashlib.sha256(film_bytes_v6(*args, **kw)).hexdigest()


def fixture_manifest(edges, configs, rulepack_hash, oid_binding=None):
    """v0.2, per review: the IDENTITY hash covers only shared canonical
    facts -- sorted typed edges, sorted configs, the rulepack hash. The
    model-oid <-> role map is model-derived (the IC term has no object
    ids), so it is DIAGNOSTIC metadata returned separately and excluded
    from the identity."""
    lines = ["FIXTURE v0.2"]
    for e in sorted(edges):
        lines.append("edge:" + ",".join(map(str, e)))
    for c in sorted(configs):
        lines.append("config:" + ",".join(map(str, c)))
    lines.append(f"rulepack:{rulepack_hash}")
    b = ("\n".join(lines) + "\n").encode()
    diag = "".join(f"bind:{r}={o}\n" for r, o in
                   sorted((oid_binding or {}).items()))
    return b, hashlib.sha256(b).hexdigest(), diag
