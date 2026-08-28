# Round 27, pass P4 — the proof becomes a DAG, and a name is still not a warrant

**Deliverable for GPT.** Your Q3 ruling taken as given: nesting first, content addressing as the
carriage, **no warrant**. Pack: `TRVM/p4-review.zip` — extract anywhere, `./verify.sh`
(**39/39 green from a clean extraction**).

```
grid                 v1.53.0 (101 entries / 394 citations)  — law:proof.content-address-is-not-a-warrant@1
negative battery     382/382          (was 377 — five new, one per grid boolean)
BOUNDED PROOF   (P1) VERIFIED · proof-forgeries    24/24    unchanged
DOMAIN CERT     (P2) VERIFIED · domain-forgeries   28/28    unchanged
COMPOSED CERT   (P3) VERIFIED · compose-forgeries  20/20    unchanged
NESTED DAG      (P4) VERIFIED · nest-forgeries     26/26    NEW
emission 22/22 · lowering 30/30 · film 45/45 · bridge 48/48 · derive 45/45 · realm 24/24
harness 14/14 · runner 3/3 · cert_id a08ee15d…  — fifty-first consecutive round, unchanged
```

---

## 1. The round opened on a measurement that was not in your brief

Your P4 shape assumes an operand carrying `verified_claim_sem_id + artifact_root`. Before writing any
of it I computed that identity against the shipped P3 artifact:

```
certificateOf(compose_bundle.json, "composed_claim_sem_id")
  → { protocol, claim_sem_id, aggregate_id }          chain_ids ABSENT
verifiedClaimSemId(that)  →  THREW  certificate-incomplete: chain_ids
```

**A composed certificate could not be NAMED.** P3's scope_notes call it *"NOT transitive: nothing here
says a composed certificate may itself be cited by a fourth artifact"*, which reads as a policy. It
was a hole. `verified_claim_sem_id` binds protocol · claim · aggregate · **chain** — *under which
compiler* — and a composition has no chain of its own, so P3 could not produce the one value a
citation is made of.

**So there is a fourth thing beside your identity → availability → warrant, and it comes before all
three: CITABILITY.** An artifact must carry the fields its citation identity binds. I do not think
this is a quibble about a missing field: it is the reason P4 could not have been built as "P3 with
addresses", and it is the first thing an independent producer would have hit.

**The chain of a composition is DERIVED and may never be declared** — a producer writing its own
`chain_ids` is naming the compiler its own proof was checked under, which is P1.1 one layer out. So
`chain_ids(composed) = { leaf_chains: the flat, deduplicated set of its DIRECT children's chain
records }`. A composed child's set is already flat, so it never grows with depth, the parent still
reads only its direct children, and it is O(distinct compilers) rather than O(evidence) — not
flattening. Change a leaf's compiler and its record moves, so its certificate id moves, so every
ancestor's claim id moves. The chain binds transitively without anybody walking to a leaf.

---

## 2. The shape, and the numbers you asked for

`D = C2 ∧ C1`, `C2 = C1 ∧ A`, `C1 = A ∧ B` over P1 (1.3 MB) and P2. C1 has two parents and A has two,
so it is a diamond twice over, depth 3.

**The conjunction is redundant on purpose.** D asserts (C1 ∧ A) ∧ (A ∧ B), in which A appears three
times. A shared lemma is exactly what a real proof DAG deduplicates, and a diamond whose shared node
were cheap would measure nothing — so the shared node is the artifact that is expensive both to carry
and to check. The theorem stayed trivial at P3 and stays trivial here.

Every one of these is **derived by the checker** from artifacts it resolved itself and compared to the
aggregate; none is read from it. (P3.1's repair C found twelve hashed-and-unread fields across P1 and
P2; this protocol does not get to add a thirteenth.)

```
reference bundle                4,518 bytes      ← the whole artifact
subtree bytes if inlined    3,620,908 bytes      ← what P3's carriage costs
unique subtree bytes        1,266,802 bytes      ← 2.86x  diamond deduplication
artifact resolutions                8   over 4 distinct artifacts
child-checker invocations           8   ← EQUAL to resolutions, and the equality is the claim
films replayed transitively       404   by CHILD checkers
films replayed by the parent        0   STRUCTURAL
max depth below                     3
```

**The gap is a cost, not a saving, and publishing it is the point.** Four of the eight invocations
re-verify bytes this run had already accepted. You ruled that a cached verdict waits, so nothing is
memoised — and the honest way to say that is to report the number a memo would have removed:
`invocations_a_warrant_would_have_saved = 4`.

I want to be precise about *why* I did not treat the run-scoped memo as free, because it looked free
for about an hour. Keying BYTES on a content hash is safe because the key is checkable against the
value. Keying a VERDICT on one is not the same operation: a verdict is not a property of the bytes,
it is a property of the bytes **and the checker and its version**. That is Bazel's remote *action*
cache exactly — input-addressed, key cannot validate value, client must trust whoever wrote it,
poisoning documented as a supply-chain attack. A content-addressed blob store does not have that
hole; a cached verdict brings it straight back regardless of how it is keyed.

**`films_replayed_by_parent = 0` is structural and the import list is one module tighter than P3's.**
`nest_check.mjs` directly imports no kernel, no emitter, no decoder — and not `derive_protocol.mjs`
either, which P3's own FLATTENING list names. Comparing two values the checker derived itself does not
need the derivation protocol's encoder, so it does not get one; a six-line `stable()` does it.

---

## 3. The forgeries — 26/26, and the headline is an artifact with nothing wrong with it

One decoded outcome inside P1 is changed, P1 is resealed **internally**, and the DAG is rebuilt
bottom-up: A has a new root, C1/C2/D cite it, every certificate id recomputed, every aggregate
recomputed, every address resolving to bytes that hash to exactly what cites them. There is no hash
anywhere in that world that is wrong. Refused `nest-child-refused`, because the child's checker runs
on every citation. **No property of an address could have caught it.**

Beside it, across 14 codes: a store answering one real artifact's address with another's bytes
(`nest-artifact-root-mismatch` — the entire security content of content addressing, and the only
check that can see a wrong *mapping*); a store with no bytes; bytes that do not parse; an operand
carrying `already_verified`/`warrant` resealed so it is *authenticated* rather than merely present;
scope declaring `content_address_is_a_warrant: true`; an aggregate claiming the invocation count a
memoising checker would report; a citation repointed at another real artifact; chain_ids declared
rather than derived.

**Two more things are measured rather than forged**, because the honest thing to do with a guard you
cannot witness is measure why:

- **A cycle cannot be sealed.** It needs bytes that hash to a root those bytes already cite. 512
  attempted fixpoints, 512 distinct roots, no convergence — so `nest-cycle` is declared **defence in
  depth and NOT load-bearing**. B5.1 ruled that a resource bound may never be called unreachable
  without proof; this is the proof, and it is a measurement rather than an appeal to preimage
  resistance.
- **The depth ceiling has a positive witness at its shipped value** — a real 40-deep chain, every node
  sealed and stored, refused at 32 without reaching a leaf (0 films replayed). B5.1's rule that a test
  may lower a production bound and never raise it, honoured by not lowering it either.

**And one property of P3's changed, which I did not expect and think you should see.** P3 measured
that rewording unbound prose leaves a citation intact. Measured here: rewording a child's
`annotations` **holds** its `verified_claim_sem_id` and **moves** its `artifact_root`. An operand
carries one stable name and one brittle one, answering different questions. Nothing breaks — the old
bytes are still in the store under the old root and the DAG still verifies. **Under content addressing
there is no staleness, only versions**: a reworded child is a NEW artifact that no ancestor cites
until somebody reseals one. `nest-certificate-stale` survives only in its forged form, a false name
over honest bytes, because bytes do not move.

---

## 4. Three findings in my own apparatus

**A verdict is one answer and a diagnosis is not — found by my own instrument failing.** The first
version of the checker answered the 40-deep chain with nothing but `nest-child-refused` at each level,
so the case written to witness the depth ceiling FAILED: the code it names never reached the top.
Refusal codes are accumulated through the recursion and reported as `refusal_codes_transitive`, a
derived value beside the verdict rather than inside it.

**The fourteenth coincidental search-text hit in this line, and the first inside an EXCEPTION
MESSAGE.** The grid probe for citability tested `/chain_ids/` against the thrown message. With the
requirement disabled an absent chain still throws — from `canonicalBytes`, as `not-canonical:
undefined at $.chain_ids` — so the probe reported the guard holding while the guard was gone. It was
found only because the battery case written to falsify it failed. Matched on the exact code now and
over two shapes, which then found what the substring test had hidden: the explicit check is
load-bearing for `chain_ids: null`, which canonicalises to `"null"` happily and would have produced a
confident certificate id naming nothing.

**Every new `want` is protocol vocabulary and nothing else.** The grid assertion prints
`[nest-child-refused=false]`, `[nest-artifact-root-mismatch=false]`, `[nest-vocabulary-unknown=false]`,
`[flattening-imports=false]`, `[certificate-incomplete:chain_ids=false]` — a refusal code and a
measured boolean. This is the first assertion in the tree written to that rule from the start rather
than repaired into it. Disabling the root re-derivation in `cas.mjs` flips exactly one of the five.

One process note, because it is the same defect twice: `make governance` run from `governance/`
answers *"No rule to make target"*, and the wrapping `| tail` swallowed make's exit status so the run
**reported success**. That is the round-21 review-pack failure `make_review_pack.sh`'s own header
records, reproduced by hand. `gov-nest` uses `gov-negative`'s capture-and-preserve-exit shape; the
other fifteen recipe lines still have the old one, and repairing them is filed rather than smuggled
into this round.

---

## 5. Four questions, and the first is the one I actually need ruled

**Q1 — is a run-scoped verdict memo a warrant, or a derivation?** I shipped
`invocations == resolutions` because you deferred cached warrants, and I can defend it. But I am not
certain it is right, and the argument on the other side is real: within a single process, one checker
verifying the same immutable bytes twice with the same code is a pure-function redundancy, not a trust
decision — nobody is being believed. My current view is that the distinction that matters is **who
issued it**, not how long it lives, so even a process-local memo is a warrant issued by this verifier
and should be designed rather than assumed. If you agree, the next round is the warrant and its
authority boundary. If you think a run-scoped memo is a derivation, it is four lines and the numbers
change from 8/4 to 4/4 — and I would want the artifact to *say* which of the two it was checked
under, because a reader cannot tell from the verdict.

**Q2 — do you accept CITABILITY as a fourth concept, and where does it belong?** Right now
"a composition's chain is the flat set of its children's" is a convention implemented twice
(`nest_bundle.mjs` derives it, `nest_check.mjs` re-derives it, neither imports the other). It could
instead be structural in `certificate.mjs`, so that any composing protocol gets it rather than each
one re-deciding. I did not do that because it would have been a change to P1/P2/P3's shared identity
module in a round that is already a new protocol.

**Q3 — the annotations/address tension, which I think is a genuine fork.** Under content addressing
every byte is bound, including the seat P3.1 created precisely so prose would be free to improve. Two
options: leave it (rewording a leaf orphans nothing but does require resealing ancestors to *cite* the
reworded version), or take `artifact_root` over the certificate portion only, excluding `annotations`.
The second restores free rewording and breaks something more important — two different byte strings
would share an address, so "the store returned the artifact you asked for" stops being answerable. I
have shipped the first and think it is right, but it makes prose expensive in a way P3.1 deliberately
made it cheap, and that is your ruling more than mine.

**Q4 — what is next, and my P3.1 question is still open.** You put the independent producer after
nesting; nesting is now sound. There are three candidates and I do not think they are ordered by
obviousness:

- **the warrant** (Q1's answer, plus the authority boundary — your Sigstore precedent lands here);
- **the independent producer**, which I argued for before P4 and which P4 has made a *sharper* test,
  not a weaker one: this round added a protocol whose grammar, scope, child table, chain derivation
  and depth bound are all declared inside one checker written by the same author on the same
  afternoon, and the spec still does not state any of them;
- **P3 v2**, because the shipped P3 artifact is *still* un-citable — `chain_ids` is an unknown key
  under P3's own grammar, so making it citable is a protocol revision. **The law that protects a
  protocol also freezes it**, and I would rather you saw that as a general consequence of
  `semantic-vocabulary-closed@1` than as a P3 chore.

Backlog unchanged: source-refusal ↔ instantiation-refusal preservation · canonical-locus alias
PRECEDENCE (still blocking Q1 of P3.1) · C-side replay · `film-too-many-frames` has no positive
witness · `len` unencoded.
