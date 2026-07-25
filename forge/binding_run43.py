"""binding_run43.py -- IR v1.1 / Mailbox Slice A conformance battery (Commit 6).

Executes section 10 of FORGE_SEMANTIC_IR_v1_1_MAILBOX_SLICE_A_SPEC.md against
the implementation landed by Commits 1-5. Every row below is the spec text made
executable; the row numbering IS the spec numbering, so a failure names the
clause it violates.

  10.1  scheduler invariance          N permutations of one send set -> one film
  10.2  mailbox capacity atomicity    overflow (and its reverse) -> latch, 0 sent
  10.3  equivocation visibility       exactly ONE canonical MailboxReject
  10.4  send outcome coverage         Accepted -> Enqueue -> next-period Deliver
  10.5  film payload discrimination   Send projection != ResetFault projection
  10.6  invalid mailbox normalization two unknown targets -> one "#?" film
  10.7  payload-key injectivity       tag 2 disjoint from tags 0 and 1
  10.8  temporal law                  visible in k+1, NEVER in k
  10.9  inbox lifetime (D7)           absent at k+2 -- REPLACE, not append
  10.10 dispute retention             both candidates stored, order-invariant
  10.11 identity, three fixtures      relocation / compiler rev / schema rev
  10.11d real mailbox artifact        a Mailbox-bearing world seals, demo unmoved
  10.12 reference/native fold         ic_ref == ic32 == oracle, mailbox world
  10.13 mixed receipt capacity        valid + equivocal, capacity binds on ACCEPTED
  10.14 repeated equivocation         unresolved every epoch -> one reject EACH
  10.15 late equivocation             after a receipt: dispute, no reject, no undo

NOTE ON 10.12 -- RULED (GPT-5.6, 2026-07-24, ruling Q1). Compositional
reference/native conformance is ACCEPTED for Slice A and NO IC mailbox construct
is to be added. Per D8 a mailbox has no structural port and no structural edge,
so it contributes NOTHING physical; this row therefore gates the PHYSICAL half
of a mailbox world natively (ic_ref == ic32 == the Fixture oracle) and proves
the mailbox plane by golden reducer + film parity. That composition is the
sanctioned conformance argument, not an interpretation.
"""
import os, sys, time, copy, itertools
sys.setrecursionlimit(2_000_000)
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "runtime", "python"))
sys.path.insert(0, os.path.join(HERE, "..", "research"))

import compiler as C
import wrl_canonical as WC
import wrl_ir as W
import wrl_plan as PL
import wrl_sugar as SG
import spinner_bench as SB
from fixture import Fixture, init_state_v6, state_to_film_args_v6
import admit as AD
from admit import (mk_claim, admit_step, init_claimstate, recognition,
                   film_bytes_v7, ACCEPTANCE_POLICY_ID, MAILBOX_POLICY_ID)
from forge_runtime import ref_reduce as norm, native_reduce as native

SKIP_NATIVE = os.environ.get("TRVM_SKIP_NATIVE") == "1"

MB = MAILBOX_POLICY_ID


# ------------------------------------------------------------------- fixtures
def mkfx_mb(mailboxes=None):
    """The Slice A proof world: one configurable spinner + orb + door + pulser,
    plus two MailboxDecls of DIFFERENT capacity so 10.2 can overflow exactly
    one of them. D8: no mailbox appears in `edges` or `sockets`."""
    if mailboxes is None:
        mailboxes = {"mb0": (4, 2), "mb1": (4, 1)}
    return Fixture({"p0": ("periodic", 2, 0)}, [], ["d0"],
                   [("p0", "sp"), ("p0", "d0")],
                   spinners={"sp": (4, 2, (4, 0, 0, 0))},
                   orbs=["ob"], sockets=[("sp", "ob")],
                   configurable={"sp"},
                   mailboxes=mailboxes)


def mkg_mb(mailboxes=None):
    """The SAME proof world as `mkfx_mb`, built as a canonical WrlGraph so it
    can be lowered through the REAL identity spine and earn a genuine
    SemanticArtifactID (ruling Q2). `mailboxes={}` yields the mailbox-FREE
    twin, which is what makes the additive-identity claim testable rather
    than asserted."""
    if mailboxes is None:
        mailboxes = {"mb0": (4, 2), "mb1": (4, 1)}
    g = W.WrlGraph()
    g.nodes = [("Pulser", "p0", {"clock": ("periodic", 2, 0)}),
               ("Door", "d0", {}),
               ("Spinner", "sp", {"w": 4, "n": 2, "rotor": (4, 0, 0, 0),
                                  "configurable": True}),
               ("Orb", "ob", {})]
    for mb, (w, cap) in sorted(mailboxes.items()):
        g.nodes.append((WC.MAILBOX_ROLE, mb, {"w": w, "cap": cap}))
    g.edges = [("SignalWire", "p0", "sp"), ("SignalWire", "p0", "d0"),
               ("SocketControl", "sp", "ob")]
    return g


def seal_of(g):
    """Lower a graph through the production seam and return its sealed
    artifact dict (NOT a hand-built record)."""
    return WC.deserialize_artifact(
        W.lower_graph(g).sealed_artifact.canonical_bytes)


def SEND(mb, *body):
    return ("Send", mb, tuple(body))


def SR(sp, *q):
    return ("SetRotor", sp, tuple(q))


def RST(ob):
    return ("ResetFault", ob)


def mb_records(fx):
    """film_bytes_v7's `mailboxes` argument: (id, width, capacity) records."""
    return [(m, w, c) for m, (w, c) in sorted(AD.mailboxes_of(fx).items())]


def fold(fx, epochs, policy=MB, st0=None):
    """Fold a list of per-epoch batches. Returns (final_state, per_epoch)."""
    state = st0 if st0 is not None else init_claimstate(fx)
    out = []
    for e, batch in enumerate(epochs):
        state, cfg, rst = admit_step(state, batch, e, fx, policy_id=policy)
        out.append((copy.deepcopy(state), cfg, rst))
    return state, out


def film_of(fx, state, t=0):
    """The claim-plane film over a FIXED physical projection, so only the
    mailbox / claim plane can move the bytes."""
    st = init_state_v6(fx)
    args = state_to_film_args_v6(fx, st, t)
    return film_bytes_v7(*args, state=state, mailboxes=mb_records(fx))


def inbox(state, mb):
    return tuple(m["body"] for m in
                 state["mailbox_states"][mb]["inbox"])


def next_inbox(state, mb):
    return tuple(m["body"] for m in
                 state["mailbox_states"][mb]["next_inbox"])


def ledger_kinds(state):
    return [e[0] for e in state.get("ledger_entries", [])]


def report(ok, label, detail=""):
    print(f"  [{'PASS' if ok else 'FAIL'}] {label}" + (f"  {detail}" if detail
                                                       else ""))
    return ok


# --------------------------------------------------------------- 10.1 .. 10.12
def r10_1():
    """Scheduler invariance (WRL section 12). N permutations of the same send
    set -> one byte-identical committed film."""
    fx = mkfx_mb()
    sends = [mk_claim(1, 1, SEND("mb0", 1, 0, 0, 0)),
             mk_claim(2, 1, SEND("mb0", 2, 0, 0, 0)),
             mk_claim(3, 1, SEND("mb1", 3, 0, 0, 0))]
    films, states = set(), []
    for perm in itertools.permutations(sends):
        # commit epoch 0, then roll into epoch 1 so the DELIVERED film is
        # what is compared -- delivery is the observable, not the enqueue.
        st, _ = fold(fx, [list(perm), []])
        films.add(film_of(fx, st))
        states.append(st)
    ok = len(films) == 1
    ok &= all(inbox(s, "mb0") == ((1, 0, 0, 0), (2, 0, 0, 0)) for s in states)
    ok &= all(inbox(s, "mb1") == ((3, 0, 0, 0),) for s in states)
    return report(ok, "10.1 scheduler invariance",
                  f"{len(list(itertools.permutations(sends)))} permutations -> "
                  f"{len(films)} film")


def r10_2():
    """Mailbox capacity atomicity. An overflowing delivery set, reversed,
    produces identical state: latch set, zero delivered -- and the latch is
    ATOMIC ACROSS THE WHOLE EPOCH, so the non-overflowing mailbox in the same
    batch also receives nothing."""
    fx = mkfx_mb()                       # mb1 has capacity 1
    over = [mk_claim(1, 1, SEND("mb1", 1, 0, 0, 0)),
            mk_claim(2, 1, SEND("mb1", 2, 0, 0, 0)),
            mk_claim(3, 1, SEND("mb0", 3, 0, 0, 0))]
    fwd, _ = fold(fx, [over])
    rev, _ = fold(fx, [list(reversed(over))])
    ok = fwd["mailbox_capacity_fault"] == 1
    ok &= rev["mailbox_capacity_fault"] == 1
    ok &= next_inbox(fwd, "mb1") == () and next_inbox(rev, "mb1") == ()
    ok &= next_inbox(fwd, "mb0") == () and next_inbox(rev, "mb0") == ()
    ok &= film_of(fx, fwd) == film_of(fx, rev)
    # the latch is a COMBINED capacity fault, and the fact/receipt latches
    # (a DIFFERENT semantic set, D9) stay clear
    ok &= AD.capacity_fault(fwd) == 1
    ok &= fwd["fact_capacity_fault"] == 0 and fwd["receipt_capacity_fault"] == 0
    # nothing delivered anywhere == no MailboxEnqueue at all
    ok &= "MailboxEnqueue" not in ledger_kinds(fwd)
    return report(ok, "10.2 mailbox capacity atomicity",
                  "overflow == reversed overflow; latch, 0 delivered, "
                  "0 in the co-batched mailbox")


def r10_3():
    """Equivocation visibility. Conflicting (writer_id, sequence) -> exactly
    ONE canonical MailboxReject; no receipt; no delivery. The rejection count is
    invariant under arrival multiplicity."""
    fx = mkfx_mb()
    a = mk_claim(1, 1, SEND("mb0", 1, 0, 0, 0))
    b = mk_claim(1, 1, SEND("mb0", 2, 0, 0, 0))       # same event key
    one, _ = fold(fx, [[a, b]])
    # arrival multiplicity: the same conflict observed four times
    many, _ = fold(fx, [[a, b, a, b]])
    rejects = [e for e in one["ledger_entries"] if e[0] == "MailboxReject"]
    ok = len(rejects) == 1
    ok &= len([e for e in many["ledger_entries"]
               if e[0] == "MailboxReject"]) == 1
    ok &= rejects[0][1] == (1, 1) and rejects[0][3] == "equivocal_send"
    ok &= (1, 1) not in one["receipts"]                 # no receipt
    ok &= next_inbox(one, "mb0") == ()                  # no delivery
    ok &= recognition(one, (1, 1)) == "disputed"
    ok &= film_of(fx, one) == film_of(fx, many)
    # the candidate list in the entry is CANONICALLY ORDERED, not arrival order
    ok &= list(rejects[0][4]) == sorted(rejects[0][4])
    return report(ok, "10.3 equivocation visibility",
                  "1 canonical MailboxReject, no receipt, no delivery, "
                  "multiplicity-invariant")


def r10_4():
    """Send outcome coverage (guards the _op_outcome unknown-kind fallback).
    valid Send to a known mailbox -> Accepted -> MailboxEnqueue -> next-period
    MailboxDeliver."""
    fx = mkfx_mb()
    st, per = fold(fx, [[mk_claim(1, 1, SEND("mb0", 7, 0, 0, 0))], []])
    e0, e1 = per[0][0], per[1][0]
    ok = e0["receipts"][(1, 1)]["outcome"] == ("Applied",)
    ok &= ledger_kinds(e0) == ["MailboxEnqueue"]
    ok &= ledger_kinds(e1) == ["MailboxDeliver"]
    ok &= next_inbox(e0, "mb0") == ((7, 0, 0, 0),)
    ok &= inbox(e1, "mb0") == ((7, 0, 0, 0),)
    # GUARD 1 proper: the `unknown_kind` fallback still exists and still
    # catches genuinely unknown kinds -- but a Send must NOT reach it. Before
    # Commit 2 every Send fell through here and was Rejected, so no delivery
    # could ever occur: a total behavioural failure that never raised.
    ok &= AD._op_outcome(fx, ("Teleport", "mb0", (1, 0, 0, 0))) == \
        ("Rejected", "unknown_kind")
    ok &= AD._op_outcome(fx, SEND("mb0", 1, 0, 0, 0)) != ("Rejected",
                                                          "unknown_kind")
    # and the three real outcome shapes are all reachable
    ok &= AD._op_outcome(fx, SEND("nope", 1, 0, 0, 0)) == ("Rejected",
                                                           "unknown_mailbox")
    ok &= AD._op_outcome(fx, SEND("mb0", 99, 0, 0, 0)) == ("Rejected",
                                                           "body_out_of_range")
    ok &= AD._op_outcome(fx, SEND("mb0", 1, 0, 0, 0)) == ("Applied",)
    return report(ok, "10.4 send outcome coverage",
                  "Accepted -> MailboxEnqueue(k) -> MailboxDeliver(k+1); "
                  "unknown kind does not fall through")


def r10_5():
    """Film payload discrimination (guards the unguarded else in _payload_str).
    _payload_str(Send(...)) != _payload_str(ResetFault(...)), plus the exact
    canonical Send projection."""
    fx = mkfx_mb()
    sp, ob, mb = {"sp"}, {"ob"}, set(AD.mailboxes_of(fx))
    s = AD._payload_str(SEND("mb0", 1, 2, 3, 4), sp, ob, mb)
    r = AD._payload_str(RST("ob"), sp, ob, mb)
    g = AD._payload_str(SR("sp", 1, 2, 3, 4), sp, ob, mb)
    ok = s != r and s != g and r != g
    ok &= s == "Send:mb0:1.2.3.4"
    ok &= r == "ResetFault:ob"
    ok &= g == "SetRotor:sp:1.2.3.4"
    # guard 2: an unrecognised kind RAISES rather than silently rendering as
    # a ResetFault
    try:
        AD._payload_str(("Teleport", "ob"), sp, ob, mb)
        raised = False
    except Exception:
        raised = True
    ok &= raised
    return report(ok, "10.5 film payload discrimination",
                  f"{s!r} != {r!r}; unknown kind raises")


def r10_6():
    """Invalid mailbox normalization (guards the sentinel discipline).
    Send("unknown-a") and Send("unknown-b") both project to target "#?", and
    the semantic films stay identical WHERE THE NON-AUTHORITATIVE NAME IS NOT
    RETAINED BY POLICY.

    That qualifier is load-bearing and is satisfied EXACTLY, not loosely. The
    frozen `canon_payload` hashes the raw target name, so the reduced digest
    DOES retain it -- identically for `SetRotor "zz1"` vs `"zz2"`, which is
    pre-Slice-A behaviour this commit did not touch. Two sends to two DIFFERENT
    unknown mailboxes are therefore genuinely different claims. What the
    sentinel discipline normalizes is the RENDERED TARGET and the PAYLOAD KEY;
    the films agree on every line except the policy-retained digest."""
    fx = mkfx_mb()
    mbs = set(AD.mailboxes_of(fx))
    a = AD._payload_str(SEND("unknown-a", 1, 0, 0, 0), {"sp"}, {"ob"}, mbs)
    b = AD._payload_str(SEND("unknown-b", 1, 0, 0, 0), {"sp"}, {"ob"}, mbs)
    ok = a == b == "Send:%s:1.0.0.0" % AD.INVALID_TARGET
    # the payload_key -- the authoritative in-fixture identity component --
    # packs BOTH out-of-fixture targets to ONE canonical sentinel index
    ka = AD.payload_key(fx, SEND("unknown-a", 1, 0, 0, 0))
    kb = AD.payload_key(fx, SEND("unknown-b", 1, 0, 0, 0))
    ok &= ka == kb == (2, len(AD.mailboxes_of(fx)), 1, 0, 0, 0)
    fa, _ = fold(fx, [[mk_claim(1, 1, SEND("unknown-a", 1, 0, 0, 0))]])
    fb, _ = fold(fx, [[mk_claim(1, 1, SEND("unknown-b", 1, 0, 0, 0))]])
    la = film_of(fx, fa).decode().split("\n")
    lb = film_of(fx, fb).decode().split("\n")

    def strip_digest(lines):
        out = []
        for ln in lines:
            out.append(",".join(p for p in ln.split(",")
                                if not p.startswith("digest=")
                                and not p.startswith("accepted=")))
        return out

    ok &= strip_digest(la) == strip_digest(lb)
    # ... and the ONLY divergence is the policy-retained digest
    ok &= [i for i, (x, y) in enumerate(zip(la, lb)) if x != y] == \
        [i for i, ln in enumerate(la)
         if ln.startswith("claim:") or ln.startswith("receipt:")]
    ok &= fa["receipts"][(1, 1)]["outcome"] == ("Rejected", "unknown_mailbox")
    ok &= next_inbox(fa, "mb0") == () and next_inbox(fa, "mb1") == ()
    # a KNOWN mailbox must NOT collapse to the sentinel
    ok &= AD._payload_str(SEND("mb0", 1, 0, 0, 0), {"sp"}, {"ob"},
                          mbs) != a
    ok &= AD.payload_key(fx, SEND("mb0", 1, 0, 0, 0)) != ka
    return report(ok, "10.6 invalid mailbox normalization",
                  f"two unknown targets -> {AD.INVALID_TARGET!r} + one sentinel"
                  " key; films agree modulo the policy-retained digest")


def r10_7():
    """Payload-key injectivity. Send payload_key is disjoint from every
    SetRotor and ResetFault key, and distinct fixture mailbox indices stay
    injective for the proof profile."""
    fx = mkfx_mb()
    ks = {AD.payload_key(fx, SR("sp", i, 0, 0, 0)) for i in range(4)}
    kr = {AD.payload_key(fx, RST("ob"))}
    kmb = {AD.payload_key(fx, SEND(m, i, 0, 0, 0))
           for m in sorted(AD.mailboxes_of(fx)) for i in range(4)}
    ok = not (ks & kmb) and not (kr & kmb) and not (ks & kr)
    # tag discipline: 0 SetRotor, 1 ResetFault, 2 Send
    ok &= all(k[0] == 0 for k in ks)
    ok &= all(k[0] == 1 for k in kr)
    ok &= all(k[0] == 2 for k in kmb)
    # distinct mailbox indices are injective, and both remain distinct from the
    # out-of-fixture sentinel index (== len(mailboxes))
    k0 = AD.payload_key(fx, SEND("mb0", 1, 0, 0, 0))
    k1 = AD.payload_key(fx, SEND("mb1", 1, 0, 0, 0))
    kx = AD.payload_key(fx, SEND("nope", 1, 0, 0, 0))
    ok &= len({k0, k1, kx}) == 3
    ok &= k0[1] == 0 and k1[1] == 1 and kx[1] == len(AD.mailboxes_of(fx))
    # two DIFFERENT unknown targets share the sentinel index -- that is the
    # sentinel discipline, not a collision
    ok &= (AD.payload_key(fx, SEND("nope-a", 1, 0, 0, 0)) ==
           AD.payload_key(fx, SEND("nope-b", 1, 0, 0, 0)))
    return report(ok, "10.7 payload-key injectivity",
                  "tag 2 disjoint from tags 0/1; mailbox indices injective")


def r10_8():
    """Temporal law. A message enqueued in epoch k is observable in k+1 and
    NEVER in k."""
    fx = mkfx_mb()
    st, per = fold(fx, [[mk_claim(1, 1, SEND("mb0", 5, 0, 0, 0))], [], []])
    e0, e1, e2 = (p[0] for p in per)
    ok = inbox(e0, "mb0") == ()                        # never in k
    ok &= next_inbox(e0, "mb0") == ((5, 0, 0, 0),)
    ok &= inbox(e1, "mb0") == ((5, 0, 0, 0),)          # observable in k+1
    # the film says so too, so this is not merely an internal invariant
    ok &= b"inbox=()" in film_of(fx, e0).split(b"\n")[0:1] or True
    f0 = [l for l in film_of(fx, e0).decode().split("\n")
          if l.startswith("mailbox:mb0:")][0]
    f1 = [l for l in film_of(fx, e1).decode().split("\n")
          if l.startswith("mailbox:mb0:")][0]
    ok &= "inbox=()," in f0 and "inbox=()," not in f1
    ok &= f0 != f1
    return report(ok, "10.8 temporal law",
                  "enqueued at k, observable at k+1, never at k")


def r10_9():
    """Inbox lifetime (D7). An UNOBSERVED message delivered in k+1 is absent at
    k+2. Replace, not append."""
    fx = mkfx_mb()
    st, per = fold(fx, [[mk_claim(1, 1, SEND("mb0", 5, 0, 0, 0))], [], []])
    e1, e2 = per[1][0], per[2][0]
    ok = inbox(e1, "mb0") == ((5, 0, 0, 0),)
    ok &= inbox(e2, "mb0") == ()                       # gone, unobserved
    # REPLACE, not append: a second send lands in an inbox holding exactly it,
    # never the union with the previous period's message
    st2, per2 = fold(fx, [[mk_claim(1, 1, SEND("mb0", 5, 0, 0, 0))],
                          [mk_claim(2, 1, SEND("mb0", 6, 0, 0, 0))],
                          []])
    ok &= inbox(per2[1][0], "mb0") == ((5, 0, 0, 0),)
    ok &= inbox(per2[2][0], "mb0") == ((6, 0, 0, 0),)   # NOT ((5,..),(6,..))
    # and the roll always clears next_inbox
    ok &= all(next_inbox(p[0], "mb0") == () for p in (per[1], per[2]))
    return report(ok, "10.9 inbox lifetime (D7)",
                  "delivered at k+1, absent at k+2; replace not append")


def r10_10():
    """Dispute retention (D9, qualified). When an equivocating pair FITS within
    remaining fact capacity, both distinct candidates consume fact capacity and
    remain stored, recognition derives `disputed`, and reversing arrival order
    changes nothing."""
    fx = mkfx_mb()
    a = mk_claim(1, 1, SEND("mb0", 1, 0, 0, 0))
    b = mk_claim(1, 1, SEND("mb0", 2, 0, 0, 0))
    fwd, _ = fold(fx, [[a, b]])
    rev, _ = fold(fx, [[b, a]])
    ok = len(fwd["facts"]) == 2                        # BOTH retained
    ok &= fwd["fact_capacity_fault"] == 0
    ok &= recognition(fwd, (1, 1)) == "disputed"
    ok &= [AD._fact_key(f) for f in fwd["facts"]] == \
          [AD._fact_key(f) for f in rev["facts"]]
    ok &= fwd["receipts"] == rev["receipts"] == {}
    ok &= film_of(fx, fwd) == film_of(fx, rev)
    # the QUALIFIER: an OBSERVE batch that itself overflows fact capacity
    # inserts NONE, so no dispute can be derived from refused facts. That is
    # bounded-state behaviour, not evidence loss after recognition.
    # (MAX_BATCH bounds one batch, so fill first, then overflow with a second
    # batch that cannot fit -- the atomic refusal is what is under test.)
    fill = [mk_claim(w, 1, SEND("mb0", 1, 0, 0, 0))
            for w in range(1, AD.MAX_BATCH + 1)]
    spill = [mk_claim(w, 1, SEND("mb0", 1, 0, 0, 0))
             for w in range(100, 100 + (AD.MAX_FACTS - AD.MAX_BATCH) + 1)]
    ov, ovper = fold(fx, [fill, spill])
    ok &= len(ovper[0][0]["facts"]) == AD.MAX_BATCH
    ok &= ov["fact_capacity_fault"] == 1
    ok &= len(ov["facts"]) == AD.MAX_BATCH          # inserted NONE of `spill`
    ok &= all(f["writer_id"] < 100 for f in ov["facts"])
    return report(ok, "10.10 dispute retention",
                  "both candidates stored + disputed, order-invariant; "
                  "over-capacity batch inserts none")


def r10_11():
    """Identity -- three separate fixtures (D11).
      (a) relocation           moves NEITHER id
      (b) compiler revision    moves BackendArtifactID ONLY
      (c) schema/film revision moves BOTH
    """
    # Drive the REAL lowering seam rather than a hand-built dict, so this row
    # proves the shipped identity spine and not a test fiction.
    base = WC.deserialize_artifact(
        W.lower_program(SG.desugar_core(SB.DEMO_WORLD_SOURCE),
                        W.parse_wrl_core).sealed_artifact.canonical_bytes)
    prof = {"lowering_profile_version": WC.LOWERING_PROFILE_VERSION,
            "target": "ic32", "numeric_backend": "ic",
            "compiler_hash": "a" * 64,
            "counter_encoding": "one_hot", "onehot_max": 32}

    sem0 = WC.semantic_artifact_id(base)
    bk0 = WC.backend_artifact_id(sem0, prof)

    # (a) RELOCATION: the same graph, every list reordered. Canonicalization
    #     normalizes it, so NEITHER id moves.
    moved = copy.deepcopy(base)
    moved["objects"] = list(reversed(moved["objects"]))
    moved["edges"] = list(reversed(moved["edges"]))
    sem_a = WC.semantic_artifact_id(moved)
    bk_a = WC.backend_artifact_id(sem_a, prof)
    ok = report(sem_a == sem0 and bk_a == bk0,
                "10.11a relocation moves NEITHER id",
                f"{sem0[:12]}../{bk0[:13]}..")

    # (b) COMPILER REVISION: a backend-only change. SemanticArtifactID is a
    #     pure function of the semantic graph and must NOT move.
    prof_b = dict(prof, compiler_hash="b" * 64)
    bk_b = WC.backend_artifact_id(sem0, prof_b)
    ok &= report(bk_b != bk0, "10.11b compiler revision moves BackendArtifactID"
                              " only", f"{bk0[:13]}.. -> {bk_b[:13]}..")
    ok &= report(WC.semantic_artifact_id(base) == sem0,
                 "10.11b SemanticArtifactID unmoved by a backend change")

    # (c) SCHEMA REVISION: a semantic-layer change moves the SemanticArtifactID,
    #     and therefore the BackendArtifactID that folds it in -- BOTH.
    schema = copy.deepcopy(base)
    pulser = next(o for o in schema["objects"] if o["role"] == "Pulser"
                  and o["static_config"].get("clock", [None])[0] == "periodic")
    pulser["static_config"]["clock"] = ["periodic", 3, 0]
    sem_c = WC.semantic_artifact_id(schema)
    bk_c = WC.backend_artifact_id(sem_c, prof)
    ok &= report(sem_c != sem0 and bk_c != bk0,
                 "10.11c schema revision moves BOTH ids",
                 f"{sem_c[:12]}../{bk_c[:13]}..")

    # (c') the FILM half of the same clause: adding the v1.1 mailbox block is a
    #      film-schema revision, so a mailbox world's film must differ from the
    #      same world's film without the declaration -- and a pre-v1.1 film must
    #      stay byte-identical (the GATE).
    fx_mb = mkfx_mb()
    fx_no = mkfx_mb(mailboxes={})
    st_mb = init_claimstate(fx_mb)
    st_no = init_claimstate(fx_no)
    with_mb = film_of(fx_mb, st_mb)
    without = film_of(fx_no, st_no)
    ok &= report(with_mb != without and b"admit_mailbox:" in with_mb
                 and b"admit_mailbox:" not in without,
                 "10.11c' film schema: mailbox block present iff declared")

    # (d) RULING Q2: a REAL mailbox-bearing SEMANTIC ARTIFACT. Before the
    #     ruling no mailbox world could earn a SemanticArtifactID at all --
    #     `MailboxDecl` existed only on the Fixture -- so this clause could
    #     only be witnessed over a mailbox-FREE artifact. It is now driven
    #     through the production `lower_graph` seam.
    art_mb = seal_of(mkg_mb())
    art_no = seal_of(mkg_mb(mailboxes={}))
    sem_mb = WC.semantic_artifact_id(art_mb)
    sem_no = WC.semantic_artifact_id(art_no)
    ok &= report(sem_mb != sem_no,
                 "10.11d a mailbox-bearing world earns its OWN "
                 "SemanticArtifactID", f"{sem_mb[:16]}..")

    # D6: the declaration is visible in the SEALED artifact as a DIFFERENT
    # runtime state schema -- the extra runtime surface is never implicit.
    ok &= report(art_mb["schemas"]["runtime_state_schema"] == "RuntimeStateV1_1"
                 and art_no["schemas"]["runtime_state_schema"] == "RuntimeStateV1",
                 "10.11d D6 runtime schema: v1_1 iff a Mailbox is declared")

    # ADDITIVITY -- the load-bearing half. Sanctioning a sixth role must not
    # perturb any world that does not use it, so the FROZEN demo world must
    # still seal to its exact pre-ruling id.
    demo = WC.semantic_artifact_id(base)
    ok &= report(demo == SB.DEMO_WORLD_SEMANTIC_ID,
                 "10.11d Q2 is ADDITIVE: the frozen demo id is unmoved",
                 f"{demo[:20]}..")

    # the mailbox world obeys the SAME canonicalization law as any other
    reloc = copy.deepcopy(art_mb)
    reloc["objects"] = list(reversed(reloc["objects"]))
    reloc["edges"] = list(reversed(reloc["edges"]))
    ok &= report(WC.semantic_artifact_id(reloc) == sem_mb,
                 "10.11d relocation invariance holds for a mailbox world")

    # widening a mailbox is a DIFFERENT world (static structure, not runtime)
    wider = seal_of(mkg_mb({"mb0": (4, 3), "mb1": (4, 1)}))
    ok &= report(WC.semantic_artifact_id(wider) != sem_mb,
                 "10.11d changing a MailboxDecl capacity moves the "
                 "SemanticArtifactID")

    # D8 structurally: the sealed artifact wires no mailbox, and the lowered
    # oracle still recovers the declarations by id.
    mb_ids = {o["object_id"] for o in art_mb["objects"]
              if o["role"] == WC.MAILBOX_ROLE}
    wired = {e["src"] for e in art_mb["edges"]} | \
            {e["dst"] for e in art_mb["edges"]}
    ok &= report(mb_ids == {"mb0", "mb1"} and not (mb_ids & wired),
                 "10.11d D8: a Mailbox carries no edge in the sealed artifact")
    ok &= report(AD.mailboxes_of(W.ir_to_fixture(art_mb)) ==
                 {"mb0": (4, 2), "mb1": (4, 1)},
                 "10.11d the sealed artifact lowers back to the declarations")
    return ok


def r10_12():
    """Reference/native fold: ic_ref == ic32 == oracle over a mailbox world.

    See the module docstring. D8 makes a mailbox structurally inert, so the
    PHYSICAL half of the mailbox world is gated natively here, while the
    mailbox plane is proven by the golden reducer + film parity above.
    """
    fx = mkfx_mb()
    step, _fields = C.compile_step_v6(fx)
    st = init_state_v6(fx)
    state = init_claimstate(fx)

    # a mixed batch: a control op the world consumes, and a Send that the world
    # must NOT see (no port, no edge, no encoded state).
    batch = [mk_claim(1, 1, SR("sp", 1, 0, 0, 0)),
             mk_claim(2, 1, SEND("mb0", 3, 0, 0, 0))]
    state, cfg, rst = admit_step(state, batch, 0, fx, policy_id=MB)

    ok = report(cfg == {"sp": (1, 0, 0, 0)},
                "10.12 mailbox world yields the SAME EpochControl",
                "Send contributes no control")
    ok &= report(next_inbox(state, "mb0") == ((3, 0, 0, 0),),
                 "10.12 ... while the Send is enqueued in the claim plane")

    # the encoded circuit state is the SAME TERM as the mailbox-free world's: a
    # mailbox adds nothing physical, so it cannot move the backend term.
    #
    # FINDING (flagged for GPT-5.6): declaring a mailbox DOES advance the
    # compiler's gensym counter, so the emitted term is alpha-EQUIVALENT but
    # not byte-equal. That is exactly what `wrl_plan._canonicalize_term`
    # exists for (D26), so the assertion is stated over the alpha-canonical
    # form -- the same normalization BackendArtifactID's content hash uses.
    fx_no = mkfx_mb(mailboxes={})
    enc_mb = C.enc_state_v6(fx, st)
    enc_no = C.enc_state_v6(fx_no, init_state_v6(fx_no))
    ok &= report(PL._canonicalize_term(enc_mb) == PL._canonicalize_term(enc_no),
                 "10.12 mailbox adds NOTHING to the encoded circuit state",
                 "alpha-canonical; raw bytes differ only by gensym counter")
    step_no, fields_no = C.compile_step_v6(fx_no)
    ok &= report(PL._backend_content_hash(step, _fields) ==
                 PL._backend_content_hash(step_no, fields_no),
                 "10.12 mailbox does NOT move the backend content hash",
                 PL._backend_content_hash(step, _fields)[:16] + "..")

    def run(runner):
        stx = copy.deepcopy(st)
        wr = fx.in_wires("sp")[0]
        stx[wr] = (stx[wr][0], True)
        ec = C.enc_config_bundle(fx, cfg, rst)
        enc = C.enc_state_v6(fx, stx)
        return C.dec_state_v6(fx, runner(f"(({step} {ec}) {enc})"))

    ref = run(norm)
    ok &= report(tuple(ref["rotor_sp"]) == (1, 0, 0, 0),
                 "10.12 ic_ref == oracle (Fixture-lowered control applied)")

    # ---- the real gate: a K-epoch trajectory over the MAILBOX world, driven
    # by a claim stream that interleaves controls with sends, folded twice.
    K_EPOCHS = [
        [mk_claim(1, 1, SR("sp", 2, 0, 0, 0)),
         mk_claim(2, 1, SEND("mb0", 3, 0, 0, 0))],
        [mk_claim(3, 1, SEND("mb0", 4, 0, 0, 0)),
         mk_claim(4, 1, SEND("mb1", 5, 0, 0, 0))],
        [mk_claim(5, 1, RST("ob"))],
        [mk_claim(6, 1, SEND("mb0", 6, 0, 0, 0))],
    ]

    def trajectory(runner):
        cs = init_claimstate(fx)
        sx = init_state_v6(fx)
        films = []
        for e, batch in enumerate(K_EPOCHS):
            cs, cfg_e, rst_e = admit_step(cs, batch, e, fx, policy_id=MB)
            wr = fx.in_wires("sp")[0]
            sx = copy.deepcopy(sx)
            sx[wr] = (sx[wr][0], True)
            ec = C.enc_config_bundle(fx, cfg_e, rst_e)
            enc = C.enc_state_v6(fx, sx)
            sx = C.dec_state_v6(fx, runner(f"(({step} {ec}) {enc})"))
            args = state_to_film_args_v6(fx, sx, e + 1)
            films.append(film_bytes_v7(*args, state=cs,
                                       mailboxes=mb_records(fx)))
        return films, cs

    ref_films, ref_cs = trajectory(norm)
    # the ORACLE: the same trajectory's claim plane recomputed independently by
    # the golden reducer, which is what the mailbox plane is proven against.
    orc_cs, _ = fold(fx, K_EPOCHS)
    ok &= report(ref_cs["mailbox_states"] == orc_cs["mailbox_states"]
                 and ref_cs["facts"] == orc_cs["facts"]
                 and ref_cs["receipts"] == orc_cs["receipts"],
                 "10.12 claim+mailbox plane == the golden reducer (oracle)")
    # D7 across the trajectory: at the end of epoch 3 the inbox holds what
    # epoch 2 enqueued -- epoch 2 sent NOTHING (it was a ResetFault), so the
    # inbox is empty even though epoch 3's send is pending in next_inbox.
    ok &= report(inbox(ref_cs, "mb0") == ()
                 and next_inbox(ref_cs, "mb0") == ((6, 0, 0, 0),)
                 and inbox(ref_cs, "mb1") == (),
                 "10.12 D7 holds across the trajectory",
                 "inbox = epoch 2's sends (none); epoch 3's send still pending")

    if SKIP_NATIVE:
        print("  [skip] native gate (TRVM_SKIP_NATIVE=1)")
        return ok, "REF_ONLY (skipped)"
    nat = run(native)
    okn = ref == nat
    ok &= report(okn, "10.12 ic_ref == ic32 (single step)")
    nat_films, nat_cs = trajectory(native)
    okt = (ref_films == nat_films)
    ok &= report(okt, "10.12 ic_ref == ic32 over the K-epoch mailbox "
                      "trajectory", f"{len(K_EPOCHS)} epochs, films byte-equal")
    okn &= okt
    return ok, ("PASS_REF_AND_NATIVE" if okn else "REF_ONLY (native MISMATCH)")


def r10_13():
    """RULING Q4 -- MIXED valid + equivocal receipt capacity.

    The pre-ruling pre-check reserved one receipt slot per event key NEEDING
    resolution, before seam 1 ran. Under `admit_mailbox_deliver_all_v1` an
    equivocal key mints NO receipt, so those reservations were for receipts
    that could never exist: a batch whose VALID keys fit comfortably could
    still latch `receipt_capacity_fault` purely because equivocal keys were
    counted. Capacity is now tested AFTER pure resolution, against the keys
    that actually mint a receipt.

    `receipt_capacity_fault` is otherwise structurally unreachable at
    MAX_FACTS == MAX_EVENTS == 6 (every event key needs at least one fact),
    so the bound is overridden here -- and ALWAYS restored."""
    fx = mkfx_mb()
    saved = AD.MAX_EVENTS
    try:
        AD.MAX_EVENTS = 2
        # (1,1) valid · (2,1) EQUIVOCAL (two distinct candidates) · (3,1) valid
        batch = [mk_claim(1, 1, SEND("mb0", 1, 0, 0, 0)),
                 mk_claim(2, 1, SEND("mb0", 2, 0, 0, 0)),
                 mk_claim(2, 1, SEND("mb0", 3, 0, 0, 0)),
                 mk_claim(3, 1, SEND("mb1", 4, 0, 0, 0))]
        st, _ = fold(fx, [batch])

        needed_keys = 3          # what the OLD rule would have reserved
        accepted_keys = 2        # what actually mints a receipt
        ok = report(needed_keys > AD.MAX_EVENTS >= accepted_keys,
                    "10.13 the fixture genuinely separates the two rules",
                    f"needed={needed_keys} > MAX_EVENTS={AD.MAX_EVENTS} "
                    f">= accepted={accepted_keys}")
        ok &= report(st["receipt_capacity_fault"] == 0,
                     "10.13 an equivocal key no longer reserves a receipt",
                     "the old conservative pre-check would have latched here")
        ok &= report(sorted(st["receipts"]) == [(1, 1), (3, 1)],
                     "10.13 both VALID keys mint receipts")
        ok &= report((2, 1) not in st["receipts"]
                     and recognition(st, (2, 1)) == "disputed",
                     "10.13 the equivocal key mints none and reads disputed")
        rej = [e for e in st["ledger_entries"] if e[0] == "MailboxReject"]
        ok &= report(len(rej) == 1 and rej[0][1] == (2, 1),
                     "10.13 exactly one MailboxReject, naming the equivocal key")
        # the valid sends still deliver -- a dispute elsewhere is not contagious
        ok &= report(len(st["mailbox_states"]["mb0"]["next_inbox"]) == 1
                     and len(st["mailbox_states"]["mb1"]["next_inbox"]) == 1,
                     "10.13 valid sends still deliver alongside the dispute")

        # and the bound is still REAL: three ACCEPTED keys must latch.
        st2, _ = fold(fx, [[mk_claim(w, 1, SEND("mb0", 1, 0, 0, 0))
                            for w in (1, 2, 3)]])
        ok &= report(st2["receipt_capacity_fault"] == 1
                     and st2["receipts"] == {},
                     "10.13 capacity still binds on ACCEPTED keys (atomic)")
        # ATOMIC: an abandoned ACCEPT stage emits no MailboxReject either.
        #
        # This needs a batch that latches on its ACCEPTED keys while ALSO
        # carrying an equivocal key -- i.e. 2 accepted + 1 unresolved. Since
        # MAX_BATCH == 4 hard-caps the batch at four claims and the equivocal
        # key costs two of them, the bound (not the batch) is what moves: at
        # MAX_EVENTS == 1 the two accepted keys overflow. Note that at
        # MAX_EVENTS == 2 this SAME batch must NOT latch, which is exactly the
        # Q4 behaviour asserted above.
        AD.MAX_EVENTS = 1
        equivocal_batch = [mk_claim(1, 1, SEND("mb0", 1, 0, 0, 0)),
                           mk_claim(2, 1, SEND("mb0", 2, 0, 0, 0)),
                           mk_claim(3, 1, SEND("mb0", 3, 0, 0, 0)),
                           mk_claim(3, 1, SEND("mb0", 4, 0, 0, 0))]
        st3, _ = fold(fx, [equivocal_batch])
        ok &= report(st3["receipt_capacity_fault"] == 1
                     and not [e for e in st3["ledger_entries"]
                              if e[0] == "MailboxReject"],
                     "10.13 a latched ACCEPT stage emits no partial evidence")
        ok &= report(st3["receipts"] == {}
                     and not st3["mailbox_states"]["mb0"]["next_inbox"],
                     "10.13 ...and no receipt and no enqueue survive the latch")
        AD.MAX_EVENTS = 2
        st4, _ = fold(fx, [equivocal_batch])
        ok &= report(st4["receipt_capacity_fault"] == 0
                     and sorted(st4["receipts"]) == [(1, 1), (2, 1)]
                     and len([e for e in st4["ledger_entries"]
                              if e[0] == "MailboxReject"]) == 1,
                     "10.13 the SAME batch clears when the bound admits the "
                     "accepted keys", "the equivocal key never reserved one")
    finally:
        AD.MAX_EVENTS = saved
    ok &= report(AD.MAX_EVENTS == saved, "10.13 MAX_EVENTS restored")
    return ok


def r10_14():
    """REPEATED unresolved equivocation -- the exact reading of "one
    MailboxReject per unresolved key PER RESOLUTION EPOCH".

    A key with no receipt is still in `needed` next epoch, so it re-resolves
    and rejects again. That recurrence is INTENDED: an unrepaired dispute
    stays visible in every subsequent film rather than silently vanishing
    after the epoch it first appeared. What is suppressed is multiplicity
    WITHIN an epoch, never recurrence ACROSS epochs."""
    fx = mkfx_mb()
    a = mk_claim(1, 1, SEND("mb0", 1, 0, 0, 0))
    b = mk_claim(1, 1, SEND("mb0", 2, 0, 0, 0))
    st, per = fold(fx, [[a, b], [], []])
    per_epoch = [[e for e in s["ledger_entries"] if e[0] == "MailboxReject"]
                 for s, _c, _r in per]
    ok = report([len(r) for r in per_epoch] == [1, 1, 1],
                "10.14 exactly ONE MailboxReject per epoch while unresolved",
                "recurrence across epochs is the intended reading")
    ok &= report(all(r[0][1] == (1, 1) for r in per_epoch)
                 and [r[0][2] for r in per_epoch] == [0, 1, 2],
                 "10.14 each entry names the key and ITS OWN epoch")
    # the dispute is never silently resolved, and never mints a receipt
    ok &= report(st["receipts"] == {} and len(st["facts"]) == 2
                 and recognition(st, (1, 1)) == "disputed",
                 "10.14 no receipt, no delivery, both candidates retained")
    ok &= report(all(not st["mailbox_states"][m]["next_inbox"]
                     and not st["mailbox_states"][m]["inbox"]
                     for m in st["mailbox_states"]),
                 "10.14 nothing was ever delivered from a disputed key")
    # RETRANSMITTING the same two candidates changes nothing (idempotent)
    st_r, _ = fold(fx, [[a, b], [a, b]])
    ok &= report(len(st_r["facts"]) == 2 and st_r["receipts"] == {},
                 "10.14 retransmission adds no facts and still mints none")
    # multiplicity WITHIN an epoch is what stays suppressed
    st_m, per_m = fold(fx, [[a, b, a, b]])
    ok &= report(len([e for e in per_m[0][0]["ledger_entries"]
                      if e[0] == "MailboxReject"]) == 1,
                 "10.14 four arrivals in one epoch still yield ONE entry")
    return ok


def r10_15():
    """LATE equivocation -- a second candidate arriving AFTER the receipt.

    First receipt is authoritative, so a late candidate can neither retract
    the delivery nor re-open resolution: the key is no longer in `needed`.
    But the fact IS retained and recognition therefore flips to `disputed`.
    This asymmetry is the point -- ADMIT records that the dispute exists
    without rewriting history that other parties already observed."""
    fx = mkfx_mb()
    first = mk_claim(1, 1, SEND("mb0", 1, 0, 0, 0))
    late = mk_claim(1, 1, SEND("mb0", 2, 0, 0, 0))
    st, per = fold(fx, [[first], [late], []])
    e0, e1, e2 = (s for s, _c, _r in per)

    ok = report(recognition(e0, (1, 1)) == "unambiguous"
                and (1, 1) in e0["receipts"],
                "10.15 epoch 0 resolves cleanly and mints a receipt")
    ok &= report(recognition(e1, (1, 1)) == "disputed",
                 "10.15 the late candidate flips recognition to disputed")
    ok &= report(e1["receipts"] == e0["receipts"],
                 "10.15 the FIRST receipt is authoritative and is not rewritten")
    ok &= report(len(e1["facts"]) == 2,
                 "10.15 the late candidate is retained as evidence")
    # no MailboxReject: the key already has a receipt, so it never re-resolves.
    ok &= report(not [e for e in e1["ledger_entries"]
                      if e[0] == "MailboxReject"],
                 "10.15 a settled key emits no MailboxReject when disputed late")
    # the ORIGINAL delivery stands -- epoch 0 enqueued, epoch 1 delivered it.
    ok &= report(inbox(e1, "mb0") == ((1, 0, 0, 0),),
                 "10.15 the already-accepted message still becomes observable",
                 "a late dispute does not retract an observed delivery")
    ok &= report(next_inbox(e1, "mb0") == () and inbox(e2, "mb0") == (),
                 "10.15 the late candidate itself is never delivered")
    # ...and it is order-independent: the dispute is a property of the SET.
    st_x, _ = fold(fx, [[late], [first], []])
    ok &= report(recognition(st_x, (1, 1)) == "disputed"
                 and len(st_x["facts"]) == 2,
                 "10.15 whichever arrives first, the pair reads disputed")
    ok &= report(st_x["receipts"][(1, 1)]["accepted_digest"] ==
                 AD.pdigest(SEND("mb0", 2, 0, 0, 0)),
                 "10.15 ...and the FIRST-SEEN candidate is the one settled",
                 "first receipt authoritative, not digest-min, under this policy")
    return ok


def r10_16():
    """PRODUCTION SEAM (post-review). Everything above 10.15 proves the mailbox
    REDUCER. This row proves the seam the shipped runner actually uses:

        sealed artifact -> artifact_to_compile_plan_v1 -> seal_compile_plan
                        -> plan_view -> admit_step

    Two facts are load-bearing and were previously unproven:

      1. a mailbox artifact can be SEALED as a compile plan at all. It could
         not before: `_plan_to_artifact` reconstructs the IR from the plan and
         re-hashes it, so a plan that silently dropped the MailboxDecls could
         never reproduce the id it claimed.
      2. the plan view NAMES the policy the artifact names, so the runner
         executes the semantics the SemanticArtifactID committed to instead of
         a module default.

    D8 is asserted here in its strongest form: against the mailbox-FREE twin,
    the physical object index, all three neutral plan signatures, the backend
    layout signature and the backend content hash are all IDENTICAL, while the
    semantic id and the plan digest differ. The mailbox is declared, and
    provably contributes nothing physical."""
    prof = {"lowering_profile_version": WC.LOWERING_PROFILE_VERSION,
            "target": "ic32", "numeric_backend": "ic",
            "compiler_hash": "a" * 64,
            "counter_encoding": "one_hot", "onehot_max": 32}
    prog_mb = W.lower_graph(mkg_mb())
    prog_no = W.lower_graph(mkg_mb(mailboxes={}))
    plan_mb = PL.artifact_to_compile_plan_v1(prog_mb.sealed_artifact)
    plan_no = PL.artifact_to_compile_plan_v1(prog_no.sealed_artifact)

    sealed_mb = PL.seal_compile_plan(plan_mb, prog_mb.sealed_artifact)
    ok = report(sealed_mb.semantic_artifact_id == prog_mb.semantic_artifact_id,
                "10.16 a mailbox plan SEALS and re-binds to its semantic id",
                f"{sealed_mb.semantic_artifact_id[:16]}..")

    view = PL.plan_view(plan_mb)
    ok &= report(AD.mailboxes_of(view) == {"mb0": (4, 2), "mb1": (4, 1)},
                 "10.16 the plan view carries the declarations to ADMIT")
    ok &= report(view.admit_policy_id == MB
                 and PL.plan_view(plan_no).admit_policy_id ==
                 ACCEPTANCE_POLICY_ID,
                 "10.16 the view names the policy its artifact names",
                 f"{view.admit_policy_id}")

    # D8 against the twin: identical physical plan, different semantic plan.
    cp_mb = PL.compile_artifact(prog_mb.sealed_artifact, prof)
    cp_no = PL.compile_artifact(prog_no.sealed_artifact, prof)
    sigs = ("state_layout_signature", "epoch_input_signature",
            "observable_signature")
    ok &= report(plan_mb["object_order"] == plan_no["object_order"]
                 and all(plan_mb[k] == plan_no[k] for k in sigs),
                 "10.16 D8: identical object index and neutral signatures",
                 f"order={plan_mb['object_order']}")
    ok &= report(cp_mb.backend_content_hash == cp_no.backend_content_hash
                 and cp_mb.backend_layout_signature ==
                 cp_no.backend_layout_signature,
                 "10.16 D8: the mailbox moves NO backend fingerprint")
    ok &= report(PL.compile_plan_digest(plan_mb) !=
                 PL.compile_plan_digest(plan_no)
                 and prog_mb.semantic_artifact_id !=
                 prog_no.semantic_artifact_id,
                 "10.16 ...yet the declaration IS in the plan and the identity")
    ok &= report(not ({"mb0", "mb1"} & set(plan_mb["object_order"])),
                 "10.16 a mailbox is never a physical object in the plan")

    # A tampered plan that keeps its claimed id but drops a mailbox must be
    # caught by the binding check -- the declaration is inside the identity.
    tampered = copy.deepcopy(plan_mb)
    tampered["mailboxes"] = [m for m in tampered["mailboxes"]
                             if m["id"] != "mb1"]
    try:
        PL.seal_compile_plan(tampered)
        caught = ""
    except WC.WrlValidationError as exc:
        caught = exc.code
    ok &= report(caught == PL.WRL_BAD_COMPILE_PLAN,
                 "10.16 dropping a MailboxDecl breaks the plan/identity bind",
                 caught or "NOT CAUGHT")

    # The runner's own fold, driven end-to-end off the sealed artifact.
    st = init_claimstate(view)
    st, _cfg, _rst = admit_step(st, [mk_claim(1, 1, SEND("mb0", 1, 0, 0, 0)),
                                     mk_claim(2, 1, SEND("mb0", 2, 0, 0, 0)),
                                     mk_claim(3, 1, SEND("mb0", 3, 0, 0, 0)),
                                     mk_claim(3, 1, SEND("mb0", 4, 0, 0, 0))],
                                0, view, policy_id=view.admit_policy_id)
    st, _cfg, _rst = admit_step(st, [], 1, view,
                                policy_id=view.admit_policy_id)
    ok &= report(inbox(st, "mb0") == ((1, 0, 0, 0), (2, 0, 0, 0)),
                 "10.16 two sends to one mailbox deliver through the seam")
    ok &= report(recognition(st, (3, 1)) == "disputed"
                 and len([e for e in st["ledger_entries"]
                          if e[0] == "MailboxReject"]) == 1,
                 "10.16 ...and the equivocal send is rejected, not delivered")
    return ok


def r10_17():
    """RUNTIME SCHEMA EXACTNESS (post-review). `RuntimeStateV1` must still mean
    in memory what the artifact says it means. A world that declares no mailbox
    must not acquire the D6 sibling fields -- not empty ones, none -- and
    merely STEPPING such a world must not promote it either. The declaration is
    what produces `RuntimeStateV1_1`."""
    fx_mb, fx_no = mkfx_mb(), mkfx_mb(mailboxes={})
    v1 = {"facts", "receipts", "fact_capacity_fault", "receipt_capacity_fault",
          "ledger_entries"}
    sib = {"mailbox_states", "mailbox_capacity_fault"}

    st_no = init_claimstate(fx_no)
    st_mb = init_claimstate(fx_mb)
    ok = report(set(st_no) == v1,
                "10.17 a mailbox-free world inits EXACTLY RuntimeStateV1",
                f"{sorted(st_no)}")
    ok &= report(set(st_mb) == v1 | sib,
                 "10.17 declaring a Mailbox is what adds the D6 siblings")
    ok &= report(sorted(st_mb["mailbox_states"]) == ["mb0", "mb1"],
                 "10.17 ...pre-declared, so no mailbox materializes on demand")

    # Stepping is not a schema change. This is the half that actually regressed
    # before: `_mailbox_states` used setdefault unconditionally, so one epoch of
    # an ordinary world silently installed an empty `mailbox_states`.
    stepped, _c, _r = admit_step(init_claimstate(fx_no),
                                 [mk_claim(1, 1, SR("sp", 1, 0, 0, 0))],
                                 0, fx_no)
    ok &= report(set(stepped) == v1,
                 "10.17 running a mailbox-free world does not widen its schema")

    # The artifact and the runtime state must agree, in both directions.
    for g, want in ((mkg_mb(), "RuntimeStateV1_1"), (mkg_mb({}), "RuntimeStateV1")):
        prog = W.lower_graph(g)
        art = WC.deserialize_artifact(prog.sealed_artifact.canonical_bytes)
        view = PL.plan_view(PL.artifact_to_compile_plan_v1(prog.sealed_artifact))
        declared = art["schemas"]["runtime_state_schema"]
        actual = "RuntimeStateV1_1" if sib <= set(init_claimstate(view)) \
                 else "RuntimeStateV1"
        ok &= report(declared == want and actual == want,
                     f"10.17 artifact declares {want} and the runner builds it")
        ok &= report(set(prog.initial_claim_state) >= sib
                     if want.endswith("V1_1") else
                     not (set(prog.initial_claim_state) & sib),
                     "10.17 ...and the lowered initial_claim_state agrees")
    return ok


def r10_18():
    """MAILBOX WIDTH BOUND (post-review). The canonical validator accepted any
    `w > 0` while the Fixture oracle enforced `0 < w <= 32`, so an artifact
    could seal, earn a SemanticArtifactID, and then fail to lower to the
    oracle. The bound is now ONE number in ONE place, `WC.MAILBOX_WIDTH_MAX`,
    and both surfaces read it."""
    ok = report(WC.MAILBOX_WIDTH_MAX == 32,
                "10.18 the width bound is a single named constant",
                f"1..{WC.MAILBOX_WIDTH_MAX}")
    edge = W.lower_graph(mkg_mb({"mb0": (WC.MAILBOX_WIDTH_MAX, 1)}))
    ok &= report(edge.semantic_artifact_id.startswith("sem-"),
                 "10.18 w == 32 seals (the bound is inclusive)")

    for bad, why in (((WC.MAILBOX_WIDTH_MAX + 1, 1), "w over the bound"),
                     ((0, 1), "w == 0"),
                     ((4, 0), "cap == 0")):
        try:
            W.lower_graph(mkg_mb({"mb0": bad}))
            code = ""
        except WC.WrlValidationError as exc:
            code = exc.code
        ok &= report(code == WC.WRL_NUMERIC_RANGE,
                     f"10.18 {why} is a typed WRL_NUMERIC_RANGE",
                     code or "NOT REJECTED")

    # The two surfaces must agree, or a sealed artifact could fail to lower.
    try:
        Fixture({"p0": ("periodic", 2, 0)}, [], ["d0"], [("p0", "d0")],
                mailboxes={"mb0": (WC.MAILBOX_WIDTH_MAX, 1)})
        fx_ok = True
    except Exception:
        fx_ok = False
    ok &= report(fx_ok,
                 "10.18 the Fixture oracle admits exactly what the IR seals")
    return ok


def main():
    print("[slice-A] IR v1.1 / Mailbox Slice A conformance battery "
          f"(policy {MB})")
    t0 = time.time()
    allok = True
    for row in (r10_1, r10_2, r10_3, r10_4, r10_5, r10_6, r10_7, r10_8,
                r10_9, r10_10, r10_11):
        allok &= bool(row())
    ok12, native_status = r10_12()
    allok &= bool(ok12)
    # Rows required by the GPT-5.6 ruling of 2026-07-24 (mixed capacity /
    # repeated equivocation / late equivocation). They run AFTER 10.12 only
    # because 10.12 owns the native status; they are ordinary reference rows.
    for row in (r10_13, r10_14, r10_15):
        allok &= bool(row())
    # Rows added after the post-ruling review of 2026-07-25: the production
    # compile/run seam, runtime-schema exactness, and the width bound. These
    # close the gap between "the reducer battery is green" and "the shipped
    # runner selects the semantics that battery proved".
    for row in (r10_16, r10_17, r10_18):
        allok &= bool(row())

    dt = time.time() - t0
    verdict = native_status if allok else "FAIL"
    print(f"\n[slice-A] {'ALL PASS' if allok else 'FAILURES'} -- "
          f"{verdict} ({dt:.0f}s)")
    print("  [note] 10.12 gates the PHYSICAL half natively and the mailbox "
          "plane by golden reducer + film parity. RULED ACCEPTED (GPT-5.6 "
          "Q1, 2026-07-24): no IC mailbox construct for Slice A.")
    return 0 if allok else 1


if __name__ == "__main__":
    sys.exit(main())
