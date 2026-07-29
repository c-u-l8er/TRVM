#!/usr/bin/env python3
"""binding_run53.py -- Slice B, Commit 5d: FREEZE INTEGRITY (F1-F12).

Commit 5c was accepted in full. `WRL_CORE_0.2.md` as a final frozen document was
not, and the ruling named why: the implementation was grounded and the DOCUMENT
had drifted from it. This battery is the acceptance gate for the corrective cut,
and it is unlike every other battery in this tree in one respect worth stating
up front -- HALF OF ITS ROWS ASSERT ABOUT A DOCUMENT.

That is deliberate, and it is the point of the commit. 5a-5c closed the gap
between two runtimes and a declaration. 5d closes two gaps that no runtime
comparison can see:

  * a constitution whose clauses live in the file it supersedes, and
  * an API that permits what the constitution forbids, in a tree where no
    caller happens to do it.

Neither is detectable by running code against other code. A document defect is
invisible to every reducer; an unused-but-permitted parameter is invisible to
every test that exercises callers. So the rows below compare an IMPLEMENTATION
AGAINST A DECLARATION and a DECLARATION AGAINST ITSELF -- which is exactly the
sixth grounding dimension §14b grew in 5c, applied one level up.

    F1   the document is self-contained                     (documentary)
    F2   §16.1 states all four `==` grounding obligations    (documentary)
    F3   §16.2 carries the permission/instance split AND the no-principal
         constraint -- the prohibition is the load-bearing half
    F4   §17 carries the five sugar closure obligations      (documentary)
    F5   the Slice B commit count is EIGHT, consistently     (documentary)
    F6   the byte-movement claim is scoped, both halves named
    F7   ordinary world execution cannot select a policy     (API)
    F8   replay REFUSES a policy/artifact mismatch           (API)
    F9   the probe seam survives, and still reaches T7i's configuration
    F10  T7f-T7i still green through the split
    F11  no identity moved
    F12  the aggregate gates, and what this battery does NOT prove

ON PARSING RATHER THAN GREPPING. This tree has learned five times that "a law
about a seam must PARSE, not grep". A document is a seam too. Substring-searching
the whole file for "claimant" would pass if the word appeared in §8's rationale
and §16.1 were still empty -- which is very close to the actual 0.2.0 defect,
since §8 discusses the same four facts. So this file parses the Markdown into
(heading -> body) and every documentary row asserts about a NAMED SECTION'S OWN
BODY. `_sec("16.1")` returns text bounded by the next heading of any level.

Run:  python3 binding_run53.py
"""
import inspect
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "runtime", "python"))

import admit as AD
import wrl_canonical as WC
import wrl_fold as FD
import wrl_ir as W
import binding_run47 as B47
import binding_run49 as B49
import binding_run51 as B51

CORE = os.path.join(HERE, "..", "WRL_CORE_0.2.md")

_FAILED = []

# Every row id this run emitted, in order, so the battery can check its OWN
# naming. `mutate_harness.rows_failed` keys a catcher by the id it parses out
# of a `[FAIL] F7a)` line, so two rows sharing an id are, to the mutation gate,
# ONE row -- and a mutant that breaks exactly one of them is credited to both.
# The first cut of F4 emitted five distinct obligations all as `F4c)`, which is
# invisible while they pass. Set membership is not identity; F12b is the row.
_IDS = []
_ID = re.compile(r"^(F[N\d]+[a-z]?)\)")


def rep(ok, label):
    m = _ID.match(label)
    if callable(ok):
        try:
            ok = bool(ok())
        except Exception as e:                                # noqa: BLE001
            print("  [FAIL] %s -- raised %s: %s"
                  % (label, type(e).__name__, e))
            _FAILED.append(label)
            if m:
                _IDS.append(m.group(1))
            return
    print("  [%s] %s" % ("PASS" if ok else "FAIL", label))
    if not ok:
        _FAILED.append(label)
    if m:
        _IDS.append(m.group(1))


# --------------------------------------------------------------- the parser
# One walk, and every documentary row PROJECTS it -- the `state_layout` lesson
# from binding_run52 applied to prose. A second hand-rolled scan of the same
# file is a fork, and it will disagree.
_HEAD = re.compile(r"^(#{1,6})\s+(.*?)\s*$")


def _sections(text):
    """`[(level, title, body), ...]` in document order.

    A body ends at the next heading of ANY level, not the next heading of the
    same level. That matters here: §16.1's body must not silently absorb §16.2
    and §16.3, or F2 would pass on text those sections supply."""
    lines = text.split("\n")
    heads = []
    for i, ln in enumerate(lines):
        m = _HEAD.match(ln)
        if m:
            heads.append((i, len(m.group(1)), m.group(2)))
    out = []
    for k, (i, lvl, title) in enumerate(heads):
        end = heads[k + 1][0] if k + 1 < len(heads) else len(lines)
        out.append((lvl, title, "\n".join(lines[i + 1:end])))
    return out


with open(CORE, "r", encoding="utf-8") as _f:
    DOC = _f.read()
SECS = _sections(DOC)


def _sec(num):
    """The body of the section whose title begins with `num` + a delimiter.

    Matched on the NUMBER, not on the words after it, so a retitled section is
    still found and a row that depends on the words fails loudly on the body
    rather than silently on a lookup. Raises on absence and on ambiguity: two
    sections numbered 16.1 is itself a defect this battery should report, and
    the anchor-collision bug in the WRL site was exactly a set check passing
    when a name existed TWICE."""
    # `(?!\.?\d)` is load-bearing and was a real bug here: a bare `(?=[\s.-])`
    # let `_sec("17")` match BOTH `17.` and `17.1`, and the ambiguity guard
    # below turned that into a crash rather than into §17.1's body silently
    # answering for §17. The guard earned itself on its first run.
    hits = [b for _l, t, b in SECS
            if re.match(re.escape(num) + r"(?!\.?\d)(?=[\s.\u2014:-])", t)]
    if not hits:
        raise KeyError("no section %r in %s" % (num, CORE))
    if len(hits) > 1:
        raise KeyError("section %r appears %d times" % (num, len(hits)))
    return hits[0]


def _titled(prefix):
    """Body of the unique section whose TITLE starts with `prefix` (for the
    unnumbered front matter: the promotion and corrective records)."""
    hits = [b for _l, t, b in SECS if t.startswith(prefix)]
    if len(hits) != 1:
        raise KeyError("%r matched %d sections" % (prefix, len(hits)))
    return hits[0]


_QUOTED = re.compile(r"[\"\u201c\u201d][^\"\u201c\u201d\n]*[\"\u201c\u201d]")


def _unquoted(text):
    """`text` with quoted spans blanked.

    QUOTING a defect is not committing it, and this document quotes its own
    withdrawn wording repeatedly on purpose -- the corrective record's whole
    job is to say what 0.2.0 said. Every row that searches for a WITHDRAWN
    phrase must therefore search unquoted prose, and it lives here rather than
    in each row because two spellings of one rule is the fork this commit is
    about. F1a and F6a both project it."""
    return _QUOTED.sub(" ", text)


_PTR = re.compile(r"^\**[Uu]nchanged\b|^\**[Ss]ee\s+`?WRL_CORE_0\.1"
                  r"|[Uu]nchanged from (?:0\.1|`?WRL_CORE_0\.1)", re.M)


# --- the documentary PREDICATES, factored so the negative controls below can
# --- call the same code the rows call. A control that re-implements the
# --- predicate proves the control works, not the row.
def p_pointer_offenders(secs):
    """Sections whose normative content DEFERS to the superseded 0.1 file."""
    return [t for _l, t, b in secs if _PTR.search(_unquoted(b))]


def p_commit_rows(body):
    """The numbered rows of §16.3's commit table."""
    return [ln for ln in body.split("\n")
            if re.match(r"^\|\s*(?:\d+|\d+[a-z])\s*\|", ln)]


def p_scoped(body):
    """Whether the byte-movement claim is scoped and both halves named."""
    return ("Among sealed artifact trajectories" in body
            and "policy-conformance seam" in body
            and "EventLedger" in body)


def p_gate_facts(body):
    """The `==` obligations §16.1's body is missing (empty == grounded)."""
    return [w for w in ("claimant", "target", "operation family",
                        "named policy") if w not in body]


def _replace(secs, num, body):
    """`secs` with the section numbered `num` given a different body."""
    out = []
    for lvl, t, b in secs:
        if re.match(re.escape(num) + r"(?!\.?\d)(?=[\s.\u2014:-])", t):
            out.append((lvl, t, body))
        else:
            out.append((lvl, t, b))
    return out


def section(fn):
    """Run a section, CONTAINING anything that escapes it.

    An exception that leaves a section is not a section that failed -- it is a
    battery that stopped, and every row after it goes unreported while the
    process exits looking like a crash rather than a verdict. Under mutation
    that reads as SURVIVED ("crashed -- rows never ran"), which is exactly
    backwards: the mutant did something visible and the harness could not say
    what. `mutate_harness`'s fourth discipline is *crash is not a catch*, and
    the only way a battery can honour it is to turn an escape into a NAMED red
    row attributable to the section it escaped from.

    This is `binding_run51.section`'s discipline, ported. It earned itself
    here on its first run: N6 (binding_run49's dispatch collapsed to two
    cases) raised out of F9 and scored SURVIVED against a battery that in fact
    contains the row for it.
    """
    print("\n" + fn.__doc__.strip().split("\n")[0])
    try:
        fn()
    except BaseException as ex:                               # noqa: BLE001
        # SystemExit/KeyboardInterrupt are the operator talking, not the
        # code under test; swallowing them would make the battery unkillable.
        if isinstance(ex, (SystemExit, KeyboardInterrupt)):
            raise
        rep(False, "%s) raised %s: %s -- the section aborted before its "
                   "remaining rows could run"
            % (fn.__name__.split("_")[0].upper(), type(ex).__name__, ex))


# ============================================================ F1
def f1_self_contained():
    """F1  the document is self-contained."""
    # The defect was not "0.1 is mentioned". Citing the historical record for
    # PROVENANCE is fine and this file does it deliberately. The defect is a
    # section whose NORMATIVE CONTENT is a pointer -- so the row looks for the
    # pointer forms, in section bodies, and it looks for them everywhere rather
    # than only in the three known sites. A restored §16.2 with a newly
    # abbreviated §19 would be the same document with the same disease.
    # This document quotes the abbreviation four times on purpose -- the title
    # block, two rows of the corrective record, and §17.1's restoration note
    # all say `"unchanged from 0.1.x"` in order to name what was removed. The
    # first cut of this row exempted those sections BY TITLE, which is the
    # weaker check twice over: it would have gone on passing if §17.1 had been
    # re-abbreviated, and it needed extending every time another section
    # mentioned the history. The discriminator is not WHICH section speaks but
    # WHETHER it is quoting, so no section is exempt.
    bad = p_pointer_offenders(SECS)
    rep(not bad,
        "F1a) no section's normative content is a pointer into the superseded "
        "0.1 file%s" % ("" if not bad else " -- OFFENDERS: %r" % (bad,)))

    # And the positive half. A pointer can also be removed by deleting the
    # section, which would pass F1a and fail the ruling. Each restored section
    # must carry real content, so a floor on length is asserted -- crude, but
    # it is the property that actually failed: 0.2.0's §16.2 was two lines.
    sizes = {n: len(_sec(n).strip()) for n in ("16.1", "16.2", "17")}
    rep(all(v > 400 for v in sizes.values()),
        "F1b) the three restored sections carry content rather than a status "
        "line -- lengths %r" % (sizes,))

    rep("self-contained" in _titled("WRL Core 0.2.1").lower()
        if any(t.startswith("WRL Core 0.2.1") for _l, t, _b in SECS) else False,
        "F1c) the title block STATES the self-containment property, so a "
        "future editor abbreviating a section is violating something written "
        "down rather than something remembered")


# ============================================================ F2
def f2_gate():
    """F2  §16.1 states all four `==` grounding obligations."""
    b = _sec("16.1")
    missing = p_gate_facts(b)
    rep(not missing,
        "F2a) §16.1's OWN body names all four enforced facts%s"
        % ("" if not missing else " -- MISSING %r" % (missing,)))
    # The gate is a conjunction, and "ADMIT enforces some of these" is not the
    # frozen claim. The word that carries it is `all four`.
    rep("all four" in b,
        "F2b) ...and states them as a CONJUNCTION -- `all four`, not a list a "
        "reader may satisfy partially")
    # The heading, not the body -- the claim `==` is not almost free IS the
    # section's title, and a body that argued it under a retitled heading
    # would leave §16's step-3 row pointing at something else. Written out
    # because the first cut of this row ended in `or True` and therefore
    # asserted nothing: an always-green row is worse than a missing one, since
    # it reports coverage it does not have.
    titles = [t for _l, t, _b in SECS if t.startswith("16.1")]
    rep(len(titles) == 1 and "almost free" in titles[0]
        and " not " in titles[0],
        "F2c) §16.1's HEADING still carries the claim -- %r" % (titles,))
    # The empirical argument 0.2.0 added is kept, not traded against the gate.
    # This is the row that would have caught the original defect: 0.2.0 had
    # this sentence and ONLY this sentence.
    rep("eight commits" in b,
        "F2d) ...alongside the Slice B empirical argument 0.2.0 added -- the "
        "restoration ADDED the gate back, it did not swap the two")


# ============================================================ F3
def f3_permission_instance():
    """F3  §16.2 permission/instance split AND the no-principal constraint."""
    b = _sec("16.2")
    layers = ("World document", "ScenarioV1", "Receipts")
    missing = [x for x in layers if x not in b]
    rep(not missing,
        "F3a) §16.2 carries all three layers of the split%s"
        % ("" if not missing else " -- MISSING %r" % (missing,)))
    rep("verified channel" in b and "claim instances" in b,
        "F3b) ...with what each layer CARRIES, which is the content of the "
        "split -- three named layers with no carried meaning is a list")
    # The prohibition. This is the half the ruling called load-bearing, and the
    # reason is that a permission stated only in a superseded file is merely
    # unavailable, while a PROHIBITION stated only there is not in force.
    rep("worker:w1" in b and "separate question" in b,
        "F3c) ...and the no-principal constraint, verbatim enough to bind: a "
        "prohibition that lives only in the superseded document is not a "
        "prohibition")


# ============================================================ F4
def f4_sugar():
    """F4  §17 carries the five sugar closure obligations."""
    b17 = _sec("17")
    b171 = _sec("17.1")
    both = b17 + "\n" + b171
    rep("CLOSURE-PROVEN" in b17,
        "F4a) §17 states the tier's status in the section the document names "
        "as its SINGLE SOURCE")
    rows = [ln for ln in b171.split("\n")
            if re.match(r"^\|\s*[1-5]\s*\|", ln)]
    rep(len(rows) == 5,
        "F4b) §17.1 carries all five closure obligations as rows -- found %d"
        % (len(rows),))
    # One row PER obligation, each with its OWN id. The first cut emitted all
    # five as "F4c)", which reads fine when they pass and is useless when one
    # does not: `mutate_harness.rows_failed` keys on the id, so five distinct
    # laws would have reported as a single indistinguishable catcher and a
    # mutant that broke exactly one of them would be credited to all five.
    # An id that names five things names none of them.
    for tag, frag, why in (
            ("c", "remapping seam", "obligation 1, the API seam"),
            ("d", "diagnostics path", "obligation 2, a REAL consumer"),
            ("e", "column", "obligation 3, line AND column"),
            ("f", "SemanticDiff", "obligation 4, authored coordinates"),
            ("g", "negative control", "obligation 5, the evidence rule")):
        rep(frag in both,
            "F4%s) ...including %s" % (tag, why))
    rep("no sugar-specific identity" in both,
        "F4h) ...and the identity law, which is the one clause here with a "
        "consequence for the seal")


# ============================================================ F5
def f5_eight():
    """F5  the Slice B commit count is EIGHT, consistently."""
    # `_titled("Promotion record")` would be WRONG here and it is worth saying
    # why, because it is the same mistake as `_sec("17")` matching §17.1 from
    # the other direction: a body ends at the NEXT HEADING OF ANY LEVEL, so the
    # promotion record's own body is the two lines before `### What moved` and
    # contains none of the claims this section is about. The subsections are
    # named directly.
    prom = _titled("What did NOT move")
    b163 = _sec("16.3")
    b161 = _sec("16.1")
    rep("**eight** commits" in prom or "eight commits" in prom,
        "F5a) the promotion record says EIGHT")
    rep("eight" in b163,
        "F5b) §16.3 says EIGHT")
    rep("eight commits" in b161,
        "F5c) §16.1's empirical argument says EIGHT -- the third place the "
        "number appears, and the one 0.2.0 got right while the record was "
        "wrong")
    # The actual rows, counted rather than trusted. A prose "eight" over a
    # table of nine is the SAME defect in the other direction, and the count
    # is the only thing that catches it.
    rows = p_commit_rows(b163)
    rep(len(rows) == 8,
        "F5d) ...and the table has EIGHT rows, counted -- found %d. Prose "
        "agreeing with prose is two spellings; prose agreeing with the table "
        "is the check" % (len(rows),))
    # 5d itself is recorded and deliberately excluded from that count, with a
    # reason. Silence would be indistinguishable from an oversight.
    rep("5d" in b163 and "grounded a construct" in b163,
        "F5e) ...and 5d's EXCLUSION from the grounding count is stated with "
        "its reason, so the eight is a decision rather than a stale number")
    # Nothing still claims six.
    six = [t for _l, t, b in SECS if re.search(r"\bsix\b\s+commits", b)]
    rep(not six, "F5f) no section still says SIX commits%s"
        % ("" if not six else " -- %r" % (six,)))


# ============================================================ F6
def f6_byte_scope():
    """F6  the byte-movement claim is scoped, and both halves are named."""
    prom = _titled("Where declared bytes moved")
    # The unscoped sentence is gone...
    # Document-wide, not section-scoped. Asserting the withdrawn sentence is
    # absent from the section it USED to live in would pass if it had merely
    # moved, and a false claim is not repaired by relocation.
    rep("moved in exactly one place" not in _unquoted(DOC),
        "F6a) the unscoped `exactly one place` claim is gone from the whole "
        "document as an ASSERTION, not merely from the section it was written "
        "in -- the corrective record still quotes it, which is the record "
        "doing its job")
    rep(p_scoped(prom),
        "F6b) ...replaced by a claim SCOPED to sealed trajectories, with the "
        "second location NAMED -- the scope is what made the original "
        "sentence false about the codebase while true about execution")
    rep("policy-conformance seam" in prom and "EventLedger" in prom,
        "F6c) ...and that second location is the probe seam and the ledger, "
        "spelled out rather than left implicit")
    rep("no sealed world can produce it" in prom,
        "F6d) ...and marked unreachable from any seal, which is why it is a "
        "conformance correction and not a trajectory change")


# ============================================================ F7
def f7_no_policy_in_production():
    """F7  ordinary world execution cannot select an acceptance policy."""
    # This is the row the whole API half exists for, and it is an assertion
    # about a SIGNATURE. That is unusual and it is the only thing that works:
    # every call site in the tree already passed, which is precisely why the
    # defect survived 0.2.0.
    p = list(inspect.signature(AD.admit_step).parameters)
    rep(p == ["state", "batch", "epoch", "fx"],
        "F7a) `admit_step` has NO policy parameter -- %r" % (p,))
    pf = list(inspect.signature(FD.fold_world).parameters)
    rep("policy" not in " ".join(pf),
        "F7b) `fold_world` has no policy parameter either -- %r" % (pf,))

    # ...and a production reduction cannot be handed one anyway. The seam is
    # typed, so the refusal is structural rather than a value check.
    r = B47.lower(B47.world2(B51.MB_CAP4), [B47.route()])
    fx = W.ir_to_fixture(r.artifact)
    st = AD.init_claimstate(fx)

    def raw_rejected():
        try:
            FD.admit_step_sealed(st, [], 1, fx, AD.MAILBOX_POLICY_ID)
        except Exception as e:                                # noqa: BLE001
            return WC.WRL_UNSEALED_POLICY in str(e) or "RuntimeSeams" in str(e)
        return False
    rep(raw_rejected,
        "F7c) `admit_step_sealed` REFUSES a bare policy id -- the precondition "
        "is a type only `runtime_seams` builds, so substituting a policy at a "
        "call site requires first constructing a different world")

    # And the honest path works, from the seal.
    seams = FD.runtime_seams(r.artifact, fx)
    rep(isinstance(seams, FD.RuntimeSeamsV1)
        and seams.admit_policy_id == AD.MAILBOX_POLICY_ID,
        "F7d) ...while the sealed path yields the world's OWN policy (%s)"
        % (seams.admit_policy_id,))
    rep(len(seams) == 3 and tuple(seams)[0] == seams.admit_policy_id,
        "F7e) ...and `RuntimeSeamsV1` still unpacks as the 3-tuple every "
        "existing caller reads, which is how this split moved a parameter "
        "without moving a trajectory")


# ============================================================ F8
def f8_replay_refuses():
    """F8  replay REFUSES a recorded policy that disagrees with the seal."""
    r = B47.lower(B47.world2(B51.MB_CAP4), [B47.route()])
    art = r.artifact
    sealed = FD.admit_policy_of(art)
    rep(FD.verify_replay_policy(art, sealed) == sealed,
        "F8a) a bundle recording the SEALED policy verifies, and the check "
        "returns the id it verified rather than making the caller re-read the "
        "field it just validated")

    def mismatch(rec):
        try:
            FD.verify_replay_policy(art, rec)
        except Exception as e:                                # noqa: BLE001
            return WC.WRL_REPLAY_POLICY_MISMATCH in str(e)
        return False
    rep(lambda: mismatch(AD.ACCEPTANCE_POLICY_ID),
        "F8b) a bundle recording the OTHER frozen policy is REFUSED with "
        "WRL_REPLAY_POLICY_MISMATCH -- not reconciled toward either source")
    rep(lambda: mismatch(None),
        "F8c) ...and so is a bundle recording NOTHING. A missing policy is a "
        "0.1.x film, and silently accepting one would re-admit exactly the "
        "trajectories §8b was written to exclude")
    # The direction matters. §8b made the record load-bearing; F8 is what
    # makes it checked. Assert the error names the field, so a reader of the
    # failure knows which of the two sources to fix.
    # Asserted on the EXCEPTION'S FIELD, not on its rendered message. The first
    # cut of this row searched `str(e)` and failed: `field_path` is carried
    # structurally by `WrlValidationError` and is not spliced into the prose.
    # Searching the message would have been the weaker check even if it had
    # passed -- it would go green on a message that merely happened to mention
    # the words, and red on a reworded but correctly-tagged error.
    try:
        FD.verify_replay_policy(art, AD.ACCEPTANCE_POLICY_ID)
        fp = None
    except WC.WrlValidationError as e:
        fp = e.field_path
    rep(fp == "policy_ids.admit_policy_id",
        "F8d) ...and the refusal TAGS the field that disagrees (%r), so a "
        "diagnostic consumer can point at it without parsing English" % (fp,))


# ============================================================ F9
def f9_probe_survives():
    """F9  the probe seam survives and still reaches T7i's configuration."""
    # T7i's evidence lives at a MAILBOX-FREE world under the MAILBOX policy --
    # a pairing no artifact can seal. If the probe had been deleted along with
    # the raw parameter, this configuration would have become unreachable and
    # §8b consequence 2 would have lost its only witness. That is the whole
    # argument of §8c's closing note, so it is asserted rather than trusted.
    lp = B47.lower(B47.world2(""), [])          # no mailbox line, no routes
    fx = W.ir_to_fixture(lp.artifact)
    rep(FD.admit_policy_of(lp.artifact) == AD.ACCEPTANCE_POLICY_ID,
        "F9a) the witness world seals the FROZEN policy (it declares no "
        "mailbox), so the mailbox policy is not reachable from its seal")
    st = AD.init_claimstate(fx)
    out = AD.admit_policy_probe(st, [], 1, fx, AD.MAILBOX_POLICY_ID)
    rep(len(out) == 3,
        "F9b) ...and the probe still drives it under the MAILBOX policy -- the "
        "cross-product that no seal can express stays reachable")

    def none_refused():
        try:
            AD.admit_policy_probe(st, [], 1, fx, None)
        except ValueError:
            return True
        return False
    rep(none_refused,
        "F9c) ...while the probe REFUSES `None`. `None` names the frozen "
        "policy and `admit_step` is the entry that means that; letting the "
        "probe accept it would restore the ambiguity the split removed")
    # The regression this row exists for, recorded because it cost two reruns:
    # the first cut of the dispatch read "declared or probe" and routed every
    # `policy=None` caller into the probe, which refuses None by contract.
    # Three cases, not two.
    #
    # Written as a CALLABLE, not as a bare call whose result is then asserted
    # on. The regression's symptom is a raised ValueError, and an exception
    # raised at row-construction time escapes the section: every later row
    # goes unreported and the harness scores the mutant "crashed -- rows never
    # ran", i.e. SURVIVED, against a battery that does in fact hold its row.
    # `rep`'s callable form turns the raise into THIS row going red, by name.
    # `section` now contains escapes too, but a row that names itself is worth
    # more than a section-level catch-all, and the two are not redundant: this
    # one says WHICH law the mutant broke.
    rep(lambda: len(B49.gfilms(lp.artifact, fx, [[]], 1, policy=None,
                               mailboxes=FD.film_mailboxes(fx))) == 1,
        "F9d) ...and a caller asking for the FROZEN policy by passing None "
        "still folds, through `admit_step`. Three cases (sealed / frozen / "
        "named), not two -- collapsing them broke T4, R7 and R11")


# ============================================================ F10
def f10_t7_boundary():
    """F10  T7f-T7i still green through the split."""
    # Delegated to the section that owns those rows rather than restated here.
    # A second copy of T7's setup would be a fork, and 5d is a commit about
    # forks. `t7_boundary` reports through binding_run51's own `rep`, so its
    # failures land in ITS list -- which is read back below.
    # T7 reads the rigs from binding_run51's module-level `S`, which T0 fills.
    # Sections in that file are not independent, so the prerequisite is run
    # rather than the rigs rebuilt here -- a second construction would be a
    # fork of the setup, and 5d is a commit about forks. T0's own rows are
    # excluded from this row's verdict by snapshotting AFTER it.
    B51.t0_profile_and_codec()
    before = len(B51._FAILED)
    B51.t7_boundary()
    new = B51._FAILED[before:]
    rep(not new, "F10) T7 boundary rows green through the API split%s"
        % ("" if not new else " -- %r" % (new,)))


# ============================================================ F11
def f11_identity():
    """F11  no identity moved."""
    # The claim `_admit_step_with_policy`'s docstring makes in as many words:
    # this split moved a parameter between functions and moved no trajectory.
    # A signature change that moved a seal would be a far worse defect than
    # the one being fixed.
    import binding_run44 as B44
    import spinner_bench as SB
    rep(SB.DEMO_WORLD_SEMANTIC_ID == B44.DEMO_SEM,
        "F11a) the pinned demo world still seals sem-8ae91fe9...fe4a")
    r = B47.lower(B47.world2(B51.MB_CAP4), [B47.route()])
    fx = W.ir_to_fixture(r.artifact)
    seams = FD.runtime_seams(r.artifact, fx)
    st = AD.init_claimstate(fx)
    a = FD.admit_step_sealed(st, [], 1, fx, seams)
    b = AD.admit_policy_probe(st, [], 1, fx, seams.admit_policy_id)
    rep(a == b,
        "F11b) the sealed seam and the probe compute the IDENTICAL reduction "
        "for the same policy -- the split is about provenance, and provenance "
        "must not be observable in the result")


# ============================================================ FN
def fn_negative_controls():
    """FN  the documentary rows CAN fail (negative controls)."""
    # §17.1's own evidence rule, applied to this file: "an assertion never
    # observed to fail is not yet evidence". F1-F6 are string searches over a
    # document that currently satisfies them, which is the easiest kind of row
    # to write vacuously -- a typo in a pattern yields a check that passes on
    # everything forever, and nothing downstream would ever notice.
    #
    # The API rows (F7-F9) get their negative controls from `mutate53`, which
    # reverts real production edits in an isolated tree. The DOCUMENTARY rows
    # cannot: `mutate_harness` copies `forge/` and SYMLINKS its siblings, so a
    # mutation naming `../WRL_CORE_0.2.md` would write straight through the
    # symlink into the real shared document -- in a tree several sessions edit
    # concurrently. So these controls corrupt a PARSED COPY in memory and touch
    # no file at all, and they call the same predicate functions the rows call
    # rather than re-implementing them, which is the only version that proves
    # anything about the rows.
    abbreviated = _replace(SECS, "16.2", "\n**Unchanged from 0.1.2.**\n")
    rep(not p_pointer_offenders(SECS) and p_pointer_offenders(abbreviated),
        "FN1) re-abbreviating §16.2 to a pointer is DETECTED -- F1a is a live "
        "check and not a pattern that matches nothing")

    short = "\n".join("| %d | c | as ruled |" % i for i in range(6))
    rep(len(p_commit_rows(_sec("16.3"))) == 8
        and len(p_commit_rows(short)) == 6,
        "FN2) a six-row commit table is COUNTED as six -- F5d reads the table "
        "rather than trusting the prose beside it")

    unscoped = "declared bytes moved in exactly one place, the Film label."
    rep(p_scoped(_titled("Where declared bytes moved"))
        and not p_scoped(unscoped),
        "FN3) the withdrawn unscoped sentence does NOT satisfy the scoped "
        "predicate -- F6b would have gone red on 0.2.0's actual text")

    gutted = "It is tempting to read the verified route as nearly grounded."
    rep(not p_gate_facts(_sec("16.1")) and len(p_gate_facts(gutted)) == 4,
        "FN4) §16.1 stripped back to 0.2.0's surviving sentence is MISSING "
        "all four obligations -- F2a is the row that would have caught the "
        "original defect, and this is the proof it fires on it")


# ============================================================ F12
def f12_scope():
    """F12  the aggregate gates, and what this battery does NOT prove."""
    # S7's discipline: a battery that only records what it covers is a
    # brochure. These are the gates 5d rides on and does not re-run, named so
    # a reader of the packet knows the boundary of THIS file's evidence.
    gates = ("binding_run51.py", "binding_run49.py", "binding_run43.py",
             "binding_run3o.py", "mutate51.py", "mutate53.py")
    for g in gates:
        print("     %-18s -- run separately" % (g[:-3],))
    # The first cut of this row was `rep(True, ...)` beside those prints, which
    # is the `or True` defect in its politest form: it reports coverage and
    # checks nothing, so the day one of these files is renamed or deleted the
    # scope statement keeps claiming a boundary that no longer exists. A
    # statement about which gates carry the rest of the evidence is checkable,
    # so it is checked.
    absent = [g for g in gates if not os.path.exists(os.path.join(HERE, g))]
    rep(not absent,
        "F12a) this file proves the DOCUMENT and the API SEAM; the reduction, "
        "the backend term and the native fold are the gates named above, and "
        "all of them EXIST%s" % ("" if not absent else " -- MISSING %r"
                                 % (absent,)))
    # The self-check. See `_IDS`.
    dupes = sorted({i for i in _IDS if _IDS.count(i) > 1})
    rep(not dupes,
        "F12b) ...and every row id in this run is UNIQUE, so `rows_failed` "
        "attributes a caught mutant to one law and not to a family sharing a "
        "name%s" % ("" if not dupes else " -- REPEATED %r" % (dupes,)))


SECTIONS = (f1_self_contained, f2_gate, f3_permission_instance, f4_sugar,
            f5_eight, f6_byte_scope, f7_no_policy_in_production,
            f8_replay_refuses, f9_probe_survives, f10_t7_boundary,
            f11_identity, fn_negative_controls, f12_scope)


def main():
    print("binding_run53 -- Slice B commit 5d: FREEZE INTEGRITY (F1-F12)")
    print("document: %s" % (os.path.relpath(CORE, HERE),))
    print("sections parsed: %d" % (len(SECS),))
    for fn in SECTIONS:
        section(fn)
    print("")
    if _FAILED:
        print("[wrl-sliceB-5d] %d FAILED" % (len(_FAILED),))
        for f in _FAILED:
            print("   - %s" % (f,))
        return 1
    print("[wrl-sliceB-5d] ALL PASS -- freeze integrity closed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
