# Round 11 Ledger — the two planes were one machine
### The evidence plane joins the runtime it had been proving things about, as a refinement-preserving transformation: same corpus hash, same `cert_id`, same 144 receipts, same pre-hash vectors — and the join is proved at the corpus, not asserted by directory adjacency
*2026-08-18 · no new theory. updates: the tree moves to `TRVM/governance/`, trvm_law_kernel.mjs (corpus projection + CONF-2), Makefile (`governance` target wired into `make test`)*

## The verification ledger, round 11

**1. They were never two versions.** The tree carried as `TRVM2` was read as a successor to `TRVM` and is not one: no file overlaps, and `TRVM`'s record never mentions it. `TRVM` is the **execution plane** — `ic32` in C, Zig, Mojo and WebAssembly, a coordination-free swarm, a distribution thesis. This tree is the **evidence plane** — identity, laws, warrants, films, certificates, receipted maintenance. The name asserted replacement of the half that actually runs, and there is no version of this record in which that was true.

**2. The join is the corpus, and it was already exact.** `TRVM/docs/spec/conformance/vectors/normalize.json` and the kernel's `EMBEDDED_VECTORS` are the same 24 vectors — identical on `(name, term, nf, ref_interactions)`, differing only by a fifth field the canonical file carries. Two projects had been proving things about one corpus without either knowing the other held it.

**3. Repointing at the canonical source would have silently resealed every certificate — the projection is why it did not.** The scheduler certificate commits `sha256(JSON.stringify(vectors))`, so the extra `ic_ref_agrees` field would have entered the commitment and moved `cert_id`, and the checker would have accepted the new value as self-consistent: a corpus commitment that depends on **provenance annotation** rather than on the corpus. `CORPUS_FIELDS` now declares what a vector's corpus identity *is* — four fields, in order — and the projection is applied at load. With it, the kernel run against TRVM's canonical file produces a certificate with **zero differing fields** from the embedded run: same `corpus.sha256 c2775f7b…`, same `cert_id a08ee15d…`, same `run_manifest_hash`, all 144 receipts byte-identical, and `golden_prehash_vectors.json` byte-identical. That is the whole content of this round's claim, and it is arithmetic.

**4. The second copy is not deleted; it is proved unable to drift.** The obvious reading of "one authoritative source" is to delete `EMBEDDED_VECTORS`, and it is wrong here: the ic32 handoff packs distribute the kernel as a **lone oracle file** with no repository around it, and a kernel that cannot normalize without a sibling corpus is not an oracle. So the embedded set stays and **CONF-2** binds it: whenever the canonical corpus is reachable, both must commit to the same hash under the same projection. Unreachable is reported `NOT_APPLICABLE` with the reason — *"UNCHECKED against it this run, which is not the same as agreeing with it"* — because a skipped check that prints like a passing one is the exact failure this record has been prosecuting since round 9's harness repairs.

**5. `make test` becomes the constitutional boundary.** Until now the tree had two independent definitions of green: TRVM's `native zig mojo conformance …selftest wasm-smoke swarm research`, and this tree's five gates, neither aware of the other. `make test` now additionally runs `governance` — law kernel, invariant grid, World plus `--check-receipt`, and the negative battery — with the kernel sourcing the canonical corpus by relative path. A runtime optimisation can no longer move semantics while the evidence plane keeps certifying the old ones, and the evidence plane can no longer redefine semantics while four fast implementations execute something else.

**6. What this move deliberately did *not* do.** The structured layout (`governance/{kernel,world,grid,evidence,probes,audit}/`) is the right destination and is **not** this commit. Thirteen artifact reads use bare filenames against the working directory, `grid_check` discovers ledgers via `readdirSync(".")`, and the negative battery copies a flat file list into each scratch case — so subdividing is a path refactor across every consumer, and a path refactor in the same commit as a move is a change whose "nothing moved" proof is worth much less. The tree lands flat, proved identical; the subdivision is its own round with its own proof.

**7. Gate.** Every gate re-run from the new location: kernel PASS against the canonical corpus (CONF-1 24/24, CONF-2 REGRESSION-LOCKED); grid v1.8.0 — 46 entries / 320 citations / 15 artifacts; World PASS; `--check-receipt` PASS; negative battery **49/49**; `golden_prehash_vectors.json` byte-identical from either corpus source. Kernel v1.1.0, untouched calculus, seventh consecutive round without the calculus moving.

## Theory movement this round

**A repository merge can be held to the same standard as a state transition, and this one was.** The project's own discipline — old state plus committed steps must reconstruct the new state — applies to moving code as readily as to a maintenance pass. The move's receipt is the certificate: if the calculus had shifted by one interaction, `cert_id` would say so, and no amount of directory tidiness would hide it.

**The right join is canonical bytes, not adjacency.** Two planes sharing a parent directory share nothing. These two share a corpus commitment and, since round 10, a canonical pre-hash representation — so `execution → canonical bytes → semStateId → evidence` is a chain with an arithmetic link at every arrow. That is the seam the planes are welded at, and it is the reason the merge is more than filing.

**A correction the merge forces on the ic32 handoff.** The pack briefs Lane B to build an independent `ic32` — parser, floating-dup heap, INTERACT, readback — and **`ic32` already exists in four languages one directory away**, self-validating at 13/13 and normalizing half-million-deep terms. None of the four carries an identity layer. The pack's milestones are therefore mis-scoped: milestones 1–4 and 6–8 are substantially built, and the outstanding work is milestones 5, 9, 10 and 11 — canonical serialization, films, cross-replay, refinement receipts — against an evaluator that already runs. Separately, milestone #7 asks for "24-vector count parity" while TRVM's own conformance spec says normatively that `ref_interactions` "is normative only for runtimes that claim to implement the same reduction strategy as `ic_float`" and others "are bound only by normal-form agreement". The kernel matches on 18/24 and says so. The spec already ruled this; the pack contradicts a document that predates it.

**Next:** re-cut the ic32 handoff around evidence-enabling the existing `ic32` rather than rebuilding it, starting with C — `normalize → canonical bytes → semStateId`, checked against the golden signature strings; then Zig/Mojo/WASM; then cross-implementation films, which is where the evidence model stops being able to hide a JavaScript artifact. The structured `governance/` subdivision, and CP5–CP7, follow.

---

## Round 12 — the join is computed by a C program

**8. The bridge is green at the byte level, 48/48.** `bridge/ic32_canon.c` includes `runtime/c/ic32.c` verbatim with its `main` renamed — the runtime under test is the runtime that ships, unedited — and implements SEMSTATE-CANONICAL-v1 §2–§5 over ic32's packed words: chase through substituted slots, live discovery order over dup *cells*, the canonical fold, the two-phase signature with §5 compaction, and its own SHA-256. Every one of the 24 vectors, in both its initial and its normal-form state, produces a canonical signature **string identical character for character** to the JS oracle's, and a `sem_state_id` identical to its digest. `λx.x` signs `L0(N0)` in C exactly as the spec hand-derived it in §5.1(a).

**9. The representations have almost nothing in common, which is the entire point.** The JS kernel walks node objects and memoizes on object identity, with a heap of `Dup` records the semantic fold wraps around the root. ic32 has **no Dup node at all** — a dup is a heap cell reached only through `T_DP0`/`T_DP1` projection terms, tags and labels are bit-packed into a `uint64_t`, free variables live in a side intern table the heap knows nothing about, and there are no objects to memoize on (the packed word is the node identity). Two implementations sharing no data structure reached the same bytes. A digest-level agreement would have been consistent with a C canonical form that is wrong in some way SHA-256 absorbs; **string** agreement is not, and that is the rung the round-10 vectors were built to make reachable.

**10. What this retires.** Until now every claim the evidence plane made was, strictly speaking, a claim about a JavaScript program — the canonical form could have been an artifact of one implementation's traversal habits and nothing would have shown it. It is now a property two independent implementations exhibit over incompatible representations. `make test` runs `gov-bridge`, so a change to either plane that moves a byte fails the build rather than being discovered by a later session.

**11. The handoff is re-cut at v3, and it corrects the brief rather than extending it.** Packs v1 and v2 told Lane B to build an independent ic32; ic32 exists in four languages one directory away, self-validating at 13/13. v3 re-scopes to evidence-enabling those runtimes, ships the C bridge as the worked example, and lists Zig → Mojo → WASM → films → cross-replay → refinement receipts as the milestones. It also strikes milestone #7 ("24-vector count parity") and cites the spec that already ruled it: `docs/spec/conformance/README.md` §10.1 makes `ref_interactions` normative *only* within a declared reduction strategy, so an interaction count is not semantic identity and a faster evaluator must not be failed for being faster. All three packs remain frozen and verify against their own manifests.

**12. Gate.** `make governance` = kernel PASS (CONF-1 24/24, CONF-2 REGRESSION-LOCKED) · grid v1.8.0, 46 entries / 320 citations · World PASS · `--check-receipt` PASS · negative battery 49/49 · **BRIDGE-CHECK 48/48 byte-identical across implementations**. The calculus has not moved for an eighth consecutive round.

---

## Round 13 — the object holding the lock was never confined

**13. Three of the audit's four 9D witnesses reproduced against World 0.7.1.** Round 9.3 shipped explicitly provisional because the external 9D document had arrived empty; the findings were re-supplied and run. `probe_maintainer_9d_repro.mjs` (frozen at v0.7.1) reports **1/4 confined**. Rounds 9.1–9.3 hardened the *World* — locked writes, crypto-random unreachable key, private fields, frozen prototype and instances, receipted apply tears — and every one of those fixes was about the object being locked, never about the object *holding the lock*. The Maintainer was an ordinary class with public `world`/`defs`/`state` and patchable prototype methods.

**14. What each breach actually was.** **9D-1**: `addGround` mutates `defs` *before* the world write, so a derivation calling it mid-pass had its publication correctly refused by the lock and still left a `GHOST` def behind — after which `snapshot()` put a name in the receipt's after-map that the world had never published, with no covering step. **9D-2 is worse than a leak and worse than the audit's framing**: assigning `this.world` mid-pass made `finally { this.world.unlock(lockKey) }` release the *wrong* world, so the unlock threw `world-lock-capability-refused`, **no receipt was sealed at all**, and the authoritative world was left **permanently locked** — in an append-only world with no external lock-breaker, that is unrecoverable. Not corruption; bricking. **9D-3**: `sealReceipt` was replaceable on the instance, so an otherwise honest pass returned a receipt claiming `no_op: true`, zero steps, and a chosen `pass_id`. **9D-4 did not reproduce** — coordinator `state` poisoning never reached the receipt, and the record says so rather than counting it.

**15. Closed structurally where the attack is structural, temporally where it is temporal.** World 0.8.0: the Maintainer instance and `Maintainer.prototype` are frozen (root identity and methods non-reassignable, `setPrototypeOf` refused) and a **private** `#inPass` flag refuses `addGround`/`addComposite`/`register`/`pass` re-entry for the duration of a pass. `defs`/`state` stay **mutable by design**, and the grid says why: poisoning them from outside a pass is the external-ingest position `register()` already models and several batteries depend on it. The attack was never that a Map can be written — it was that it could be written *from inside a transaction*, which is exactly what the flag refuses.

**16. The battery caught this round's own fix as incomplete, which is the third time this session.** L-COORD-1's first run reported 3/4: the instance freeze was in place but `Maintainer.prototype` was still writable, and the patched prototype duly returned a forged receipt. Writing the falsifier before believing the fix is the only reason it was found here instead of by the next audit — the same pattern as round 9's `|| true` clause, round 10's harness repairs, and this round's own `$SCRATCH`.

**17. Two corrections adopted from the audit, and one overclaim retracted.** The bridge's rationale was written as "a canonical form wrong in a way SHA-256 absorbs"; the correct statement is that digest equality establishes agreement only *under* the collision-resistance assumption, while byte equality discharges that assumption entirely and localizes disagreement to the character. And **CONF-2 was overclaimed**: it does not make divergence "impossible", because when the canonical corpus is unreachable the equality is *unknown*, not agreed. Standalone oracle use may leave it unknown; emission may not. `TRVM_STRICT_CORPUS=1` turns an unreachable corpus into a falsification, and `make gov-strict` is the release/pack-cut gate — deliberately outside `make test`, which is a development gate.

**18. Gate.** kernel PASS (CONF-1 24/24 · CONF-2 REGRESSION-LOCKED, and FALSIFIED under strict mode with the corpus absent, verified both directions) · grid **v1.9.0**, 47 entries / 323 citations · World **0.8.0** PASS with L-COORD-1 4/4 · `--check-receipt` PASS · negative battery **54/54** · bridge 48/48. The calculus has not moved for a ninth consecutive round.

**Open, and named rather than implied.** This closes *object-authority* confinement. A derivation sharing the process still holds ambient host authority — filesystem, network, CPU — that no object discipline can withdraw, and Node's `worker_threads` would close the first of those and not the second: each worker gets its own V8 isolate and heap, which is real JS object isolation, but it is explicitly not a security sandbox. Two distinct future laws, not one: `derivation-object-confinement` (a worker isolate can plausibly close it) and `derivation-host-confinement` (needs an OS-level sandbox or capability environment).

---

## Round 9D.1 — the coordinator was sealed; its reachable authority graph was not

**19. The previous round's closure was premature, and one of its findings is retracted.** The audit reproduced three bypasses against the patched World 0.8.0 and all three verified here: **0/3 confined**. `#inPass` mediates *methods* — `addGround` — not the raw `Map` behind a frozen property; and `Object.freeze` on a property says nothing about the object it points at. Worse, **9D-4 was not confined in round 13**: that result was an artifact of *which node* the test poisoned. Poisoning the node being re-derived is overwritten by staged apply; poisoning a *different* node reached the receipt intact. The capability was live the whole time and the record said otherwise. Retracted.

**20. The third witness needed no map access at all, and is the deepest of the three.** `addGround` stored the **caller's `spec` object by reference**. A derivation that retained the outer object and reassigned `specB.measureFn` mid-pass had its replacement executed and **committed** — no `defs` access, no `state` access, no World escape, no reflection, no prototype patch, no lock theft. Ambient authority through registration aliasing. It would have survived making the maps private, which is exactly why "make it private" was the wrong shape of answer.

**21. The receipt was assembling one authoritative-looking fact out of two sources.** `snapshot()` read `pub_version` from the World and `warrant_id` from coordinator state, so a poisoned coordinator entry produced `{pub_version: 4 (honest), warrant_id: "f0rged"}` — a hybrid fact with no single authority behind it. Both fields now come from the publication itself; coordinator state is *compared* against it and any disagreement sets `coordinator_diverged` rather than being silently preferred or silently dropped. This matters past this bug: receipts are evidence objects, and an evidence object may not join fields from disagreeing authorities.

**22. Closed at the capability, with the test seam intact.** World 0.9.0: `defs`/`state` are `GuardedStore`s whose `set`/`delete`/`clear` consult the in-flight flag, with a module-private `RAW` table as the only unguarded write path so the pass can still commit its own results; values are **owned and frozen on ingest** (`ownDef`/`ownSpec`/`ownWarrant`), which is what severs registration aliasing; and the pass captures a **definition view at entry** and computes against it, so a mutation slipping any future guard still cannot change what that pass did. Guard and snapshot are belt and braces on purpose — 0.8.0 had only the guard, and the guard had a gap. Poisoning from *outside* a pass still works, because that is the external-ingest position `register()` already models and L-MAINT-3/L-MAINT-5 depend on it.

**23. A mislabelled instrument, caught in review rather than by the next audit.** The 9D.1 probe's last line printed *"`spec.measureFn` is directly assignable"* while actually testing `typeof … === "function"` — true of every version, measuring nothing. It now attempts the assignment. Four rounds running, the instrument has been the thing that was wrong.

**24. Gate.** grid **v1.10.0** — 48 entries / 326 citations · World **0.9.0** with L-COORD-1 4/4 and **L-COORD-2 4/4** · kernel PASS · `--check-receipt` PASS · negative battery **58/58** · bridge 48/48. The three witnesses stay red against 0.8.0 in `probe_coordinator_alias_9d1_repro.mjs`.

**The rhyme, five layers deep.** 9B: the fork was not a boundary. 9C: the hidden key was not hidden. 9D: the coordinator was not sealed. **9D.1: the coordinator was sealed, but its reachable authority graph was not.** Each round the boundary held exactly where it was drawn and the authority walked around the edge — and the next edge is the process itself, which no object discipline reaches.

---

## Round 9D.2 — ownership that was shallow, ownership that projected, and the realm underneath both

**25. Two more defects in the 0.9.0 repair, one of them a regression the repair itself introduced.** `ownWarrant` froze the warrant *object* and left `value` and `witness` as the caller's nested objects, so `m.state.get("B").value.x = 999` was an in-pass write that `GuardedStore` never saw — **no `.set()` occurred, so `#inPass` was never consulted**. And `ownSpec` kept `{measure, predicate, measureFn}` while silently dropping `inputs`, `law_refs` and `naive`, all of which the derivers consume and the first of which participates in `derivation_id`: the alias-severing repair was **also an undeclared semantic projection**. It was invisible to the corpus only because no shipped spec uses those fields — a coverage hole, not a correctness argument. Both reproduced against 0.9.0 and are frozen there; both are CONFINED at 0.10.0. Ownership is now transitive through `canonicalBytes` — the boundary the World already trusts, rather than a second clone algorithm — and schema-complete, with unknown spec fields **refused** rather than discarded.

**26. Identity-only divergence detection could not see a corrupted record.** A coordinator entry mutated without resealing keeps a `warrant_id` that still matches the publication, so the 0.9.0 check reported agreement about a record whose value had been changed. The published *value* is now compared too, and the flag names which field diverged rather than saying `true`.

**27. The realm witness, frozen and deliberately NOT closed.** Replacing `Map.prototype.get` and performing an ordinary, permitted `world.read("flag")` hands the private `#res` Map to the caller as `this`. Writing through the captured reference produced a resource at **version 777 against a vclock of 1, with no append-only log entry** — the World's central invariant broken with no lock key, no reflection, no public field, and no Map ever handed to the derivation. So the standing phrase that `#private` makes internals unreachable "by prototype tricks" was too broad, and the record now states the narrow truth: **private fields resist reflection and prototype manipulation *of the object*; they do not protect the objects *stored in* them from monkey-patching of the shared primordials used to operate on them.** Capturing pristine primordials at load would be defence in depth, not a boundary — it commits to auditing `Map`, `Array`, `Object`, `JSON`, iterators and sorting in perpetuity, which is the hardened-JavaScript problem and not a property of this design. The witness stays red as the motivation for realm separation.

**28. `law:evidence.instrument-nonvacuity@1`, and it is mechanised rather than exhorted.** Every negative case now digests its scratch tree before and after the perturbation and is **refused as VACUOUS** if the forgery changed nothing. Verified by making a case forge nothing on purpose: the battery reported `FAIL … (VACUOUS)` and `57/58`, then restored. Six apparatus failures across four rounds would each have been caught mechanically by this rule — the unset `$SCRATCH` (never executed), the hand-typed `44/44` (count not derived), the hard-coded `"1.0.2"` replacement (a version bump would have made it a no-op), the untested prototype half of the authority graph, the false "9D-4 confined" (wrong node, so the semantic path was never entered), and a probe line printing "directly assignable" while testing `typeof === "function"`. **The engine has been right more often than the apparatus measuring it**, and that is now a law rather than a recurring note.

**29. Gate.** grid **v1.11.0** — 50 entries · World **0.10.0**, all 26 batteries green with L-COORD-1 4/4 and L-COORD-2 4/4 · kernel PASS · `--check-receipt` PASS · negative battery **58/58** *with non-vacuity enforced* · bridge 48/48.

**The ladder, six deep.** 9B: the fork was not a boundary. 9C: the hidden key was not hidden. 9D: the coordinator was not sealed. 9D.1: the coordinator was sealed, its reachable aliases were not. 9D.2: the aliases were severed, the *nested* values were not — and beneath all of it the shared realm was never a boundary at all. Each round the seal held exactly where it was drawn. The next edge is the process, and no object discipline reaches it.

---

## Round 9D.3 — ownership that failed open, and an instrument that claimed more than it did

**30. `ownValue` ended in `catch { return v; }`.** An object neither `canonicalBytes` nor `structuredClone` could handle was returned to the caller **with the authority the layer existed to take**. Three variants, 0/3 confined against 0.10.0: a witness carrying a method defeated both paths; `spec.inputs` carrying a method took the entire registration-alias species back, with B re-deriving on a caller-mutated input mid-pass; and the `Map` case is the one that matters beyond aliasing.

**31. The Map witness proved the two domains disagreed about what a value is.** `structuredClone` *succeeds* on a `Map`, and `Object.freeze` freezes the wrapper's ordinary properties while leaving the Map's **entries** writable — so `.set()` still worked on a "frozen" witness. And because warrant identity serializes with `JSON.stringify`, for which `new Map([["e",1]])` is `{}`, `Map([["e",1]])` and `Map([["e",999]])` were **indistinguishable to `warrant_id`**. The ownership domain (structuredClone) and the identity domain (JSON) had different opinions about what a value is, and evidence built on top of that disagreement is not evidence. One domain now, and it is the one the World already refuses on: **a witness may be semantically opaque without being representationally arbitrary.**

**32. Closed by refusing, not by getting cleverer.** World 0.11.0 owns through `canonicalBytes` alone and throws `<field>-not-canonical` for `spec.inputs`, `warrant.value` and `warrant.witness` alike. The fail-open path is gone and grid_check asserts its absence by source scan, so it cannot return by accident. If tagged encodings for `Map`/`Set`/`Date` are ever needed, one encoding must serve ownership, equality, `warrant_id` and replay together — never `structuredClone` on one side and `JSON.stringify` on the other.

**33. The instrumentation law stated a stronger property than the harness implemented.** `run_case_engine` had **no** non-vacuity check at all — one round after the law was registered claiming every case had one. That is precisely the defect the law describes, committed by the law's own introduction. Both runners now check, the digest is **per-file** rather than whole-tree so the evidence names the artifact perturbed, and clauses 4–6 of the law — that the intended execution *path* ran and that the reported predicate is the one measured — are now **declared open** in the registry instead of implied. A common falsifier protocol with occurrence counts, target-specific pre/post values and observed verdicts belongs with the artifact-roots round.

**34. And the detector's own first defect was a vacuity blind spot.** The first draft diffed one-sidedly, so a case that **deletes** an artifact — `refine-receipt-missing` — was reported VACUOUS. Found by running it, fixed to a symmetric difference, and recorded in the harness rather than quietly corrected, because a law about instruments that hides its own instrument's failure would be self-refuting.

**35. Prose drift, repaired.** The world header said the calculus kernel was frozen at v1.0.1 while the shipped `KERNEL_VERSION` is 1.1.0 — exactly the class of drift this machinery exists to make boring to catch, sitting in the file the machinery lives in.

**36. Film identity, decided before the film round rather than during it.** `program_sem_id` (the semantic derivation identity, **equal across conforming implementations**) is split from `implementation_id` (executable provenance — a hash of `ic32.c`, the JS module, the wasm binary). A portable film commits the first; committing an executable hash would give the JS, C and WASM implementations of the same program different identities and make cross-runtime films implementation-specific **by construction**, defeating the exercise. Declared in the grid and checked, so the film round inherits the decision instead of improvising it.

**37. Gate.** grid **v1.12.0** — 51 entries · World **0.11.0** · kernel PASS · `--check-receipt` PASS · negative battery **61/61**, both runners non-vacuous and each case naming its target · bridge 48/48.

**The ladder, seven deep.** 9B the fork · 9C the key · 9D the coordinator · 9D.1 its reachable aliases · 9D.2 its nested values · **9D.3 the boundary that gave up and handed the object back** — and beneath all of them the shared realm, still open by decision. Every round the seal held exactly where it was drawn.

---

## Round 9D.4 — the decision rule fired, and the answer is to stop

**38. The fourth variant needs no object at all.** A `let bias = 0` shared by two closures. A runs first, sets it to 1000, and B — `support_changed`, therefore re-derived — commits **1005 where an honest B is 5**, in the coordinator and in the World, with the pass not aborted. Against World 0.11.0, which had just closed three ownership rounds. `Object.freeze`, `deepFreeze`, `structuredClone`, `canonicalBytes`, `#private`, `GuardedStore` and the pass-entry snapshot are all **inapplicable**: JavaScript gives the coordinator no mechanism to enumerate, copy, canonicalize or freeze a captured lexical environment, and freezing `measureFn` itself does not help. **Capturing an arbitrary callable does not capture its semantics.**

**39. A second theorem fails alongside it, and it is the one that matters for films.** `derivation_id` is computed from `measure`/`predicate`/`inputs` — so the witness holds it **constant** while behaviour changes from `fb` to `fb + 1000`. `derivation_id` does not identify a derivation's *semantics*. That is a tolerable limit of a closure API and an **intolerable** one the moment a semantic film asserts that an identified program performed a particular transition. The `program_sem_id`/`implementation_id` split declared last round now has an executable falsifier behind it rather than a design argument.

**40. This one is frozen and NOT repaired, by decision, and the decision was made in advance.** The previous round's record stated the criterion before the evidence: *"if your next pass finds a fourth ownership variant I would take that as evidence the object-discipline approach has more surface than I can enumerate, and move realm separation ahead of films."* It did, so that is what happens. `law:derivation.environment-confinement@1` is registered **FALSIFIED by design and canonical** — the statement is what must hold, the current API does not hold it, and closure comes from **replacing** the API rather than hardening it. Three negative cases keep it that way: greenwashing the status, deleting the law, and dropping the roadmap each die on their own diagnostic. The probe exits 0 on purpose: it documents a boundary, it does not gate the build.

**41. 0.11.0 is not a failure — it is what running out of the class looks like.** Four rounds of ownership pushed ordinary object discipline far enough that the remaining counterexample stopped being a forgotten `freeze` on a nested field and became a lexical cell. **An arbitrary closure is an unbounded capability container.** That is an architectural boundary, and the right response to an architectural boundary is not another patch.

**42. What replaces it, declared before it is built.** The realm boundary accepts **only TRVM's canonical value domain** — never "structuredClone succeeded", a phrase the 9D.3 Map witness already disqualified by proving `structuredClone` and `JSON.stringify` disagree about what a value is. `Function`, `Map`, `Set`, `Date`, `SharedArrayBuffer`, `MessagePort`, class instances and transferable handles are refused: those are capabilities, not data. `program_sem_id` may **not** be a caller-selected label, or `measureFn = evilClosure` simply becomes `{"program_sem_id": "honest-program"}` while arbitrary code runs — it must be an immutable binding whose rebinding is itself authority-bearing. And three scopes stay separate rather than collapsing into "sandboxed": **object** confinement (a worker isolate closes it), **determinism** (a persistent worker holding `let counter = 0` leaks no parent authority and still fails to make `program_sem_id = P` denote a stable function), and **host** confinement (needs an OS-level sandbox).

**43. Realm separation and transition portability are one round, not two.** A derivation that must *name a program* instead of shipping a closure is already most of what a film needs to identify a step. So the first target is one tiny deterministic program with a JS and a C implementation, and the acceptance condition is **JS-film → C-checker accepts and C-film → JS-checker accepts** — not endpoint equality. That single round closes closure authority, program-semantic identity, cross-realm execution, cross-implementation transition semantics, and the film gap together. Artifact roots still go first: four rounds established that the measurement apparatus is part of the theorem, and that infrastructure gets finished before it is built on.

**44. Gate.** grid **v1.13.0** — 52 entries, one of them FALSIFIED by design · World 0.11.0 · kernel PASS · `--check-receipt` PASS · negative battery **64/64** · bridge 48/48.

**The ladder, and where it stops.** 9B the fork · 9C the key · 9D the coordinator · 9D.1 its reachable aliases · 9D.2 its nested values · 9D.3 the boundary that handed the object back · **9D.4 the authority that was never an object.** Six rounds of drawing the seal one layer further out, and the seventh says the layer is the wrong shape. The next boundary is a realm, and no amount of `Object.freeze` reaches it.

---

## Round 14 — the apparatus becomes explicit, and the replacement API crosses a realm

**45. Artifact roots first, because four rounds established that the apparatus is part of the theorem.** Ambient CWD discovery is replaced by roots anchored at `import.meta.url` across `grid_check` (v2.20), `trvm_world` (0.12.0), the extractor and the bridge checker, each overridable by `TRVM_GOV_ROOT`, with grid_check **reporting its resolved root in the verdict line**. Output proved identical apart from that note. This is not tidiness: in an evidence system "which file did I read?" is provenance, and a checker whose answer is "whatever was beside the process" cannot state it.

**46. The artifact set is declared once, and the coverage rule runs in the direction that fails silently.** `artifacts.json` holds the case input set; both negative runners read it instead of two hand-maintained `cp` lists **that had already diverged** — `run_case_engine` omitted `maintenance_receipt.json` for no stated reason. grid_check now refuses any governance artifact **present but undeclared**, and requires every probe to declare what it witnesses. A missing declared file already failed loudly; an undeclared present file is never copied into a scratch case and therefore never tested, and the roster keeps counting.

**47. Instrument-nonvacuity clause 1, mechanised.** The intended target is **derived from the perturbation script** — files opened for writing, files removed — and must equal the set that actually changed, so a case editing the wrong artifact, or an extra one, fails as loudly as one editing nothing. Verified to fire by making a case touch an undeclared artifact (`TARGET MISMATCH`, 63/64) and restoring it. **Clause 4 stays declared open**: independent evidence that the intended execution *path* ran. The diagnostic match is a weak proxy, and the false "9D-4 confined" came from a witness that never entered the path it was written for. Closing it needs the verifier to report which rules it *evaluated*, not only which one failed.

**48. The replacement for the falsified closure API exists, and it is falsified in both positions.** `derive_protocol.mjs`: a program is a canonical AST, `program_sem_id` is `H(canonical program)`, and the registry's key **is** the program's hash — so a caller cannot select an id and rebinding is not an operation the API offers. That is exactly what the 9D.4 witness demanded of any replacement, since `measureFn = evilClosure` would otherwise have become `{"program_sem_id": "honest-program"}`. Ten in-process falsifiers, five more across a real `worker_threads` crossing.

**49. One architectural decision was forced and is worth stating plainly: the derivation realm cannot read, and does not need to.** A worker that holds no world reference cannot perform a tracked read — so reads became an **authority** operation performed on the authoritative side and passed as explicit grants, while computation stays in the realm that owns nothing. An ungranted read is refused by name on the far side. This is a real change to where the read footprint comes from and it is flagged rather than buried: the footprint is now the authority's record of what it read on the derivation's behalf, not the derivation's own claim about what it touched.

**50. The decisive result is empirical and one line long.** `postMessage` of a request carrying a closure throws **`DataCloneError: () => 1 could not be cloned`**. The attack that defeated `Object.freeze`, `deepFreeze`, `structuredClone`, `canonicalBytes`, `#private` fields, `GuardedStore` and the pass-entry snapshot **cannot be expressed at the boundary at all**. The confinement is performed by the transport rather than by object discipline — which is why replacing the API was the correct response to a falsified law rather than a sixth round of hardening.

**51. Scope, stated rather than implied.** `law:derivation.serialized-boundary@1` — superseded by `@2` in round 15, which §55–§57 record and which leaves this paragraph's scope statement standing while retracting §49's — closes **object** confinement only. A worker holding `let counter = 0` leaks no parent authority and still fails to make `program_sem_id` denote a stable function; `Date.now`, `Math.random`, the filesystem and the network remain reachable. Determinism and host confinement are separate scopes, named separately, and grid_check refuses an `artifacts.json` whose `derivation_boundary` drops its `not_claimed` note — the scope limit cannot quietly fall off the record.

**52. Gate.** grid **v1.15.0** — 53 entries · World **0.12.0** · kernel PASS · `--check-receipt` PASS · negative battery **67/67** with target-matching · bridge 48/48 · **derive 10/10 in-process and 5/5 across a realm**.

**Where this stops.** The protocol is proven; **no existing derivation has been ported to it**. The program language is deliberately tiny — `const/read/scope/cite/add/sub/mul/len/input` — and the real measures, `componentMeasure`'s graph reachability among them, cannot be expressed in it yet. That is the next decision, and it is a scoping decision rather than an engineering one.

---

## Round 15 — the record said the footprint was the grant, and the mechanism said neither

**53. Two sentences of round 14 were not supported by the code, and both witnesses reproduced verbatim before anything was changed.** Review supplied them; they are frozen in `probe_derivegrant_v02_repro.mjs`. **W-1**: the worker sourced its read table from `req.canonical_inputs.__reads`, and the language has `{op:"input", name:…}`, which retrieves *any* canonical input — so the one-node program `{op:"input", name:"__reads"}` returned the entire authority-supplied read table with `witness.reads = 0`, `support = []` and `read_footprint = {exact:[],predicates:[]}`. A derivation consumed authority data and produced no dependency record. **W-2**: a request asserting `implementation_id: "impl-c-pretend-v9"` was executed by the JavaScript evaluator and returned success, and `DeriveResult` carried no `implementation_id` at all. Neither defect needed more than one line of the worker, and both read as harmless: a convenient place to put the read table, and a field passed through from the request.

**54. The repair is not to redefine the footprint as the grant — they are two evidence objects and collapsing them loses both.** The **grant** (`read_grants`, named by `grant_id = H(canonical read_grants)`) is a *capability* record: what the authority made available. It is allowed to be broader than what is read, and under data-dependent traversal it must be — `read adj:a → discover b → read edge:a|b` cannot be pre-resolved to its exact subset. The **footprint** is the *dependency* record: what the program consumed through a tracked read. Freshness, invalidation, replay and support analysis key on the footprint alone, so defining it as the grant would invalidate every derivation whenever any granted-but-unread resource moved — which under snapshot granting is every derivation. The battery states it as arithmetic: a 3-resource grant against a 1-entry footprint, with the two unused resources named. `input` now addresses `canonical_inputs` only; `read`/`scope` address `read_grants` only; and the authority validates the returned footprint as a **subset of the grant it issued**, at the granted versions and scope digests, *on its own evidence and before any re-derivation* — `footprint-ungranted-read: secret:key` fires against an otherwise honest result whose value would have re-derived equal.

**55. `law:derivation.serialized-boundary@1` is superseded by `@2` rather than edited.** Revision 1 is kept as the honest record of an overclaim, with a `revision_note` naming both unsupported sentences. Two new laws carry what @1 was reaching for: `law:derivation.grant-footprint-separation@1` and `law:derivation.implementation-provenance@1`. The **granting model is now a decision rather than a default** — snapshot (A) over read-RPC (B), because it is deterministic, films cleanly and does not turn every primitive evaluation into a cross-realm round trip. Its cost is stated where it will be needed: the grant may reveal more than the program reads, so confidentiality against the derivation realm is the trigger to revisit, not a property this design already has.

**56. `implementation_id` becomes load-bearing in one direction, and the other is declared open rather than implied.** The executor **asserts** it; the caller may only state `expected_implementation_id`, which an executor that cannot satisfy it refuses by name — so impersonation has no path, and the JS worker refuses a request demanding a C executor across a real boundary. It is excluded from the **semantic projection** that cross-implementation validation compares, which is the operative half of the `program_sem_id`/`implementation_id` split: a result stamped `impl-c-derive-v0.2.0` validates against a JS re-derivation and its provenance is *recorded* rather than compared away. Comparing whole results would have made cross-implementation validation fail by construction. **Still open, and stated in the law's own text:** `implementation_id` is a declared constant, not a digest of executable bytes, so a *modified* JS worker still emits `impl-js-derive-v0.2.0`. Impersonation is closed; provenance is not.

**57. §49 is retracted.** It read: *"the footprint is now the authority's record of what it read on the derivation's behalf, not the derivation's claim about what it touched."* That was wrong twice over — it described a collapse that would break freshness, and the mechanism did not implement even the collapse it described. What is true at v0.2.0 is the sentence §49 should have contained: the authority decides and records what data crosses into the derivation realm; the derivation records what it consumed; and the authority validates the second against the first. §51's *scope* statement stands unchanged.

**58. A third defect, found while repairing the first two, in the module built to remove exactly this.** `evaluate(ast, reader, inputs)` took the reader as a **callable parameter**, and `deriveLocally` passed the caller's. That is the closure-authority shape in miniature — not a boundary hole, since the worker built its own reader from data and no function survives `postMessage`, but the same species living in the authority's own path in the file whose header describes why closures are unbounded capability containers. The evaluator now builds its reader from canonical grant data and nothing else, and a pair of reader callables in the grant position is refused *as data*: `grants-schema: [read,scope]`. Related, and found by the battery rather than by reading: `evaluate` was not total over its input domain — a malformed grant produced a raw `TypeError` instead of a named refusal. Fixed in the code, not in the assertion that caught it.

**59. The probe is PAIRED, and it is the first probe in this tree that gates.** Its siblings freeze a boundary that is *declared* open, so they report a breach and that is the record. These two defects are repaired, so a one-directional probe would pass just as happily if the frozen copy were quietly replaced with the repaired one. It therefore runs each witness twice: against the embedded v0.1.0 copy, where it **must still reproduce** — a witness that stops reproducing against the version it was written for has stopped measuring — and against the live modules, where it must be confined. `law:evidence.instrument-nonvacuity@1` applied to a repro. The frozen copy runs in a real `worker_threads` realm from a `data:` URL, because W-1 was a defect in the worker's *wiring* rather than in the shared evaluator, and nothing is written to the artifact tree.

**60. The language is ruled before the expressiveness round, not during it.** **Small total core plus named semantic primitives.** The nine-op core stays; complex behaviour arrives as `{op:"prim", primitive_sem_id, args}` and never as `if`/`while`/`function`/`closure`/`recursion`/`eval`. A general programming language at the derivation boundary re-admits the unbounded capability container that `law:derivation.environment-confinement@1` was falsified by, in a form that serializes. `primitive_sem_id` must be **content-bound** — H(primitive language/version + canonical input/output contract + semantic specification identity + conformance-vector identity) — because `"componentReachability"` as a bare string is exactly the caller-selected label `program_sem_id` refuses. Component reachability is the first primitive, chosen because it is materially harder than arithmetic: traversal, data-dependent reads, support, adjacency footprints and the phantom-scope case all appear in it at once, and it still has a total semantic definition over a finite grant snapshot. Declared; not built.

**61. Two transition systems had started to be discussed in the same words, and the failure mode is specific.** `film_planes` separates them. The **TRVM calculus film** is `semantic pre-state → (rule + canonical locus) → semantic post-state` over the ic32 interaction-net relation, contracted by conformance §10/§10.5 — canonical bytes agree C↔JS at 48/48 and **no native runtime emits films yet**. The **derivation evidence** relation is `DeriveRequest → evaluate → DeriveResult`, and it has one implementation. Porting `add`/`read`/`input` to C would prove the second and would **not** close the first. Without that distinction a session could finish cross-replay on the tiny derivation AST and write *"cross-implementation semantic films complete"* while pack-v3's milestones 5, 9, 10 and 11 stand untouched. So the roadmap is re-ordered: **native ic32 film emission is not gated on the derivation language** and proceeds on the existing conformance contract. The convergence that would make them one system — `DeriveProgram AST → canonical lowering → interaction-net term → ic32 → semantic film`, one execution substrate rather than a derivation interpreter beside a rewrite runtime — is recorded as reachable and **not adopted**, which is the reason not to build so much dedicated interpreter machinery that the option closes.

**62. Gate.** grid **v1.16.0** — 56 entries / 339 citations · `derive_protocol.mjs` **0.2.0** joins `artifact_versions` · kernel PASS (CONF-1 24/24 · CONF-2 REGRESSION-LOCKED) · World 0.12.0 PASS · `--check-receipt` PASS · negative battery **76/76** with nine new forgeries, each caught by its own diagnostic · bridge 48/48 · derive **21/21 in-process, 9/9 across a realm, 2/2 + 2/2 paired**. `scheduler_certificate.json` reproduced byte-identically — `cert_id` unmoved, the calculus untouched for a tenth consecutive round.

**63. And the artifact-root round had two reads it said it had closed.** Round 14 recorded that ambient CWD discovery was *"replaced by explicit roots anchored at `import.meta.url`"* across `grid_check`. The root was introduced and `A()` applied to most reads — but the **citation scan**, the primary evidence loop of the whole checker, still resolved every artifact against the working directory, and so did the **banned-phrase tripwire**. Found by running the checker from one directory up, which is not a clever test. The two failure modes differ, and the second is the one that matters: the citation scan reported `artifact missing` for all sixteen artifacts and failed loudly, while the banned-phrase loop was written `existsSync(f) ? readFileSync(f) : ""` — an absent file scanned the **empty string** and every banned-phrase check passed vacuously. From any directory but `governance/` the tripwire reported clean while measuring nothing. Both anchored at `ROOT` at v2.21, absence is now a failure rather than an empty scan, and the checker produces identical output from `governance/`, from `TRVM/`, and from `/` under `TRVM_GOV_ROOT`. The round-14 claim was not false about its intent and was false about its extent, which is the difference the record cares about: **five rounds running, the instrument has been the thing that was wrong.**

**Where this leaves the ladder.** Rounds 9B–9D.4 walked a seal outward until the authority stopped being an object. Round 14 replaced the API and proved the transport does the confining. **Round 15 is the first round in that sequence where the defect was in the record rather than in the boundary** — the mechanism was sound about what crossed and wrong about what it was recording, and a footprint that can be produced without a read is not a weaker dependency record, it is not one. The next boundary is still the process. The next *evidence* is a native film.

---

## Round 16 — the identity bound a spelling

**64. `program_sem_id` committed syntax while the record claimed it committed semantics, and those cannot both be true.** Review put the contradiction in one line: `programSemId` computed `H("TRVM-PROGRAM-v1|" + canonicalBytes(ast))` while `derivation_language` said the core was deliberately *not* frozen. If two conforming implementations may assign different meaning to `add`, to evaluation order, to numeric behaviour or to refusal semantics and still agree on the id, the id names a spelling. Four gaps sat behind it, all reproduced before anything was changed and frozen as C-1…C-4 in `probe_coresem_v03_repro.mjs`:

| | |
|---|---|
| **C-1** | `add` was JavaScript `+` — `"2"+"3"` is `"23"`, `[]+{}` is `"[object Object]"`, `1e308+1e308` is `Infinity` |
| **C-2** | `bind()` validated nothing — `{op:"exec", cmd:"rm -rf /"}` was issued a `program_sem_id` |
| **C-3** | arity and field sets unconstrained — `{op:"const"}` with no value, `add` with no `b`, and `add` with an extra field all received ids |
| **C-4** | the footprint was an ordered **sequence** inside the semantic projection, so a right-to-left implementation returned different canonical bytes — `foreign-result-divergence` — for a program it computed identically |

**65. The core is frozen, and its identity is content-bound rather than a label.** `TRVM-DERIVE-CORE-v1` (`law:derivation.core-semantics@1`) declares the grammar, the value domain, arithmetic — IEEE-754 binary64, **no coercion**, operands must be numbers and results must be finite with overflow refused *at* the operation — evaluation order, the footprint's shape, totality, and the exact refusal vocabulary. `core_sem_id = H(canonical CORE_SPEC)`, **not** the string `"TRVM-DERIVE-CORE-v1"`, because a bare name is precisely the caller-selected identity the primitive ruling already refuses for `"componentReachability"` — the record would have committed the same defect one layer up while forbidding it one layer down. `program_sem_id = H("TRVM-PROGRAM-v2" | core_sem_id | canonical AST)`, and the grammar is validated **before** the hash, so no identity exists for a program outside the language.

**66. C-4's obvious repair was the wrong one, and the ruling matters more than the fix.** Declaring evaluation order semantic in the core closes the divergence and buys it at a price the record should not pay: two *correct* implementations, differing only in the order they visited dependencies, would disagree about identity over a field neither of them considers semantic. Depending on `{a,b}` is one dependency set however it was reached. So `read_footprint` became a **canonical dependency set** — sorted, deduplicated — and access order with repeats moved to `read_trace`, which is kept because the film plane wants it and **excluded from the semantic projection** because semantics do not. The core still *fixes* evaluation order, so refusals and traces reproduce everywhere; it simply no longer makes that order an identity. This is the same principle that keeps `ref_interactions` out of conformance identity, and the record has now applied it twice.

**67. Two arithmetic surfaces that were frozen without being witnessed, and one that was decided by accident.** `sub` and `mul` shared `add`'s refusal string and had no falsifier of their own; all three now carry overflow and coercion witnesses (`-1e308 - 1e308`, `1e308 * 2`, and a non-number operand each). And **signed zero was being ruled by `JSON.stringify`**: the core said "IEEE-754 binary64" while `canonicalBytes` collapses `-0` to `"0"`. The canonical numeric quotient **identifies -0 with +0**, that is now stated in `CORE_SPEC.signed_zero`, and `mul(-1, 0)` is the witness. It was already true of the entire canonical domain and unstated, which is exactly how a C implementation would have decided it for us.

**68. Every v0.2.0 program id is retired, deliberately, and the timing is the whole argument.** `psem-f154679c…` became `psem-fa4ca55b…` for the same AST. This is cheap exactly once — while no second implementation exists to be broken by it — and expensive forever after. The alternative on the table was to mark the domain separator explicitly draft; freezing was preferred because `add`, `read`, `input`, evaluation order, canonical values and the refusal vocabulary do not need `componentReachability` to exist before their meaning can be settled. The primitive *catalog* stays unfrozen, and a `prim` extension bumps the core version and every program id with it.

**69. The non-vacuity detector caught a round-15 falsifier that had gone dead in this round's own edits.** `derive-semantic-projection-widened` targeted the literal `RESULT_FIELDS.filter((f) => f !== "implementation_id")`, which this round replaced with a two-element exclusion list — so the forgery changed nothing and the battery reported `VACUOUS`, 83/84. Repointed at the new shape. This is the fourth time a falsifier has been silently invalidated by a change to the thing it was watching, and the first time the harness said so before a human noticed.

**70. Gate.** grid **v1.17.0** — 58 entries / 340 citations · `derive_protocol.mjs` **0.4.0** · kernel PASS (CONF-1 24/24 · CONF-2 REGRESSION-LOCKED) · World 0.12.0 PASS · `--check-receipt` PASS · negative battery **84/84** with eight new forgeries · bridge 48/48 · derive **31/31 in-process, 9/9 across a realm** · probes **2/2+2/2** and **4/4+5/5**. `scheduler_certificate.json` byte-identical — `cert_id` unmoved, the calculus untouched for an eleventh consecutive round.

**What this round is not.** It is the core's semantics and nothing else. The derivation *authority* — issuance binding, live-footprint freshness, the composition that may call a result committable — is a separate theorem and is deliberately not in this commit; the manifest's `not_claimed` says so in the present tense rather than promising it. One theorem per round, which the previous draft of this work did not observe.

---

## Round 17 — issuance authenticated the grant, and acceptance took both proofs from its caller

**71. The authority layer was drafted and reviewed before it was committed, and review found a live authority bug in it.** Round 16 deliberately shipped the core alone and left this as a separate theorem. That was the right split for a second reason nobody intended: the authority draft had three defects, all reproduced verbatim, all frozen in `probe_issuebind_v05_repro.mjs`.

**72. Issuance answered a question about the wrong object.** The draft derived `request_id = H(intent_id | grant_id)` and recorded `request_id → grant_id`. Neither binds the program, the inputs or the implementation requirement — so *"was this issued?"* was answered about a **grant**, while the thing being accepted was a **request**. **I-1**: take an honest request with `canonical_inputs.bias = 0`, change only `bias` to `1000`, keep `request_id` and `grant_id` untouched. `wasIssued` → **true**, the derivation returns **1005** where an honest one returns 5, acceptance returns **committable**. The authority accepted request content it never issued. Issuance now records `request_id → request_sem_id = H(canonical request)`, recomputed at acceptance, so any change to any field is a *different request* rather than the same request with different content.

**73. The options bag let a caller write authority content.** **I-2**: `authorize(intent, over)` spread `...over` **after** every field the authority had just decided, so `authorize(intent, {canonical_inputs: {bias: 1000}})` produced an **authority-issued** request evaluating to 1005 — the authority's own stamp on the caller's substitution. The bag is gone. Exactly one thing may be requested, `expected_implementation_id`, and it is a requirement on the *executor* rather than authority content.

**74. Acceptance was a pure function whose caller supplied both of its proofs.** **I-3**: `acceptForeignResult(registry, req, res, liveReader, issuer = null)` — the issuer **defaulted to absent**, so omitting it turned issuance checking off entirely and a wholly self-made request with a self-made `grant_id` was accepted. And `liveReader` was a parameter, so after the World moved `fb@1 → fb@2` a fake reader that simply replayed the granted version turned a `stale-read` refusal back into an acceptance. Acceptance is now a **method on the authority**: the issuance table and the live World reader are closed over, and there is no argument a caller can pass to switch either off. `GrantIssuer` became `DerivationAuthority`, because the name was describing one of its jobs.

**75. Freshness, and why it is not the same question as containment.** `footprintWithinGrant` is historical — was every claimed read inside the snapshot this derivation received? `validateFootprintFresh` is temporal — are those dependencies still current *now*? Both can be satisfied about a World that has moved, which `probe_stalegrant_v03_repro.mjs` witnesses directly: grant cut at `fb@1=5`, derive, World moves to `fb@2=9`, then `checkResult` **PASS** · `footprintWithinGrant` **PASS** · `validateForeignResult` **PASS** — all three *correct* — and the value 5 is now wrong. Re-derivation against the snapshot can never notice, because executor and authority are agreeing about the same stale bytes. Freshness keys on the **footprint, never a global vclock**; the negative half is witnessed (`other@1→2` moves and acceptance still passes) and `grid_check` refuses a law text that drops the phrase. The scope half reaches further than expected: a node joining a query with no exact read moving is `stale-scope: kind:node` — the World's phantom-scope case arriving at the derivation boundary.

**76. `committable` was a claim one function call cannot make, and the draft made it.** Acceptance returns `{validated, fresh_at_check}` and nothing else. The World can move between acceptance returning and the caller applying, so a boolean saying "you may commit this" is a TOCTOU window with a reassuring name. The composition that actually commits belongs to the World — acquire the authoritative lock, accept, deterministic prepared apply with no hostile callback in between, seal the receipt, release — and **no lock capability is exported to reach it**, because rounds 9B–9C are the record of what happens when transaction authority is passed around. The caller's obligation is stated in the source and in the law; it is not enforced, and the manifest says so rather than implying otherwise.

**77. And the negative battery had been running against a checker that was already red.** *(Annotated in round 20: those results were not false-green — each case did find its requested diagnostic — but they were not isolated-cause evidence either, because the verifier was already failing. The contamination stays in the record as evidence about the development process; `law:evidence.clean-baseline@1` is the general rule promoted out of it.)* Adding a case whose expected pattern did not match meant reading the rest of the output for the first time in a while — and an **unperturbed** scratch case did not pass `grid_check`. `artifacts.json` declares `tools` as well as `case_inputs`, the checker requires every *declared* artifact to exist, and the case tree only ever copied `case_inputs` — so four unrelated failures (`negative_battery.sh`, `extract_prehash.mjs`, and both derive batteries "declared, which is absent") have preceded every forgery **since round 14**. Every case still found its own diagnostic, so nothing was falsely green; but the baseline was not clean, and a checker that is already failing is not measuring what a negative case thinks it is. The case tree now carries everything the manifest declares, and a clean case passes.

**78. Two of this round's own falsifiers were wrong in the two documented ways.** `committability-claim-restored` expected a phrase that appears in the *law text* rather than in the *diagnostic*, and `authorize-options-reopened` expected `authorize() must whitelist its options` — where `grep -E` reads `()` as an empty group, so the pattern could never match its own message. Both are the "wrong diagnostic" species the harness self-test enumerates, found by the battery refusing to call them caught.

**79. Gate.** grid **v1.18.0** — 60 entries / 341 citations · `derive_protocol.mjs` **0.5.0** · kernel PASS · World 0.12.0 PASS · `--check-receipt` PASS · negative battery **92/92** with eight new forgeries, against a clean baseline for the first time since round 14 · bridge 48/48 · derive **40/40 in-process, 10/10 across a realm** · probes **2/2+2/2**, **4/4+5/5**, **5/5**, **3/3+4/4**. `scheduler_certificate.json` byte-identical — twelfth consecutive round.

**Still not claimed.** The World's lock composition around acceptance is specified and **not built**. `implementation_id` is still a declared constant, so impersonation is closed and provenance is not. No derivation has been ported. The apparatus self-test is the next round.

---

## Round 18 — the apparatus is measured too

**80. Six consecutive rounds found the defect in the instrument rather than the engine, and that stopped being a run of bad luck several rounds ago.** The unset `$SCRATCH` so a case could never execute · the hand-typed `44/44` · the version forgery that replaced a literal a bump would have made a no-op · a probe line printing *"directly assignable"* while testing `typeof` · the false *"9D-4 confined"* from a witness that never entered its own path · a non-vacuity law registered one round before its harness implemented it · a one-sided diff that called a deleting case vacuous · round 15's two CWD-relative reads, one of which scanned the **empty string** and reported success · and round 17's contaminated baseline. That is a recurring threat to the validity of every number this tree prints, so the **known failure species get a gate**: `law:evidence.harness-selftest@1` and `harness_selftest.sh`, **9/9**.

**81. Eight of the nine require the harness to say something. The ninth requires it to say nothing.** M-1 working-directory dependence · M-2 an absent declared artifact · M-3 a present undeclared one · M-4 a perturbation that changes nothing · M-5 a case that **deletes** rather than modifies · M-6 a case that moves an artifact it did not declare · M-7 a case whose expected diagnostic is not the one produced · M-8 a paired probe whose frozen side has been silently repaired · and **M-9, an unperturbed case tree that must simply pass**. M-9 is the shape a battery of forgeries structurally cannot see: every case in it is *supposed* to make the checker fail, so a checker that was already failing looks exactly like a checker doing its job. Round 17 found it by accident, and only by reading output there had been no reason to read.

**82. Bounded, and the boundary is the point.** This is not a general test-of-tests and does not recurse. It encodes nine shapes that have actually gone wrong in this tree and stops. The temptation to keep going — a test of the self-test, a test of that — is the same temptation the record refused when it declined to keep hardening object ownership after the fourth variant: past a certain depth the effort stops buying evidence and starts buying reassurance.

**83. It caught three defects in its own first draft, which is the only evidence that it works.** The scratch-battery builder split the real runner at the first line beginning `run_case ` — which is the function **definition**, `run_case () {` — producing a meta-battery whose runner was undefined, so every meta-case failed for a reason unrelated to what it measured. M-8's silent repair emptied the frozen `reads` table and **W-1 kept reproducing**, because W-1 never performs a read: it reaches the grant table through the `input` op, since v0.1.0 carried that table inside `canonical_inputs`. And M-1 first asserted that all three directories produced a *passing* verdict rather than an *identical* one, so it failed on an unrelated version-lockstep error — a meta-case failing outside its own subject, which is itself one of the nine.

**84. Gate.** grid **v1.19.0** — 61 entries / 342 citations · kernel PASS · World 0.12.0 PASS · `--check-receipt` PASS · negative battery **95/95** with three new forgeries · bridge 48/48 · derive **40/40 · 10/10** · probes **2/2+2/2**, **4/4+5/5**, **5/5**, **3/3+4/4** · harness self-test **9/9**. `scheduler_certificate.json` byte-identical — thirteenth consecutive round without the calculus moving.

**Where the three rounds leave it.** 16 froze what a program *means*; 17 fixed what an authority *authenticates* and what acceptance may *claim*; 18 measures the thing that measures all of it. None of the three touched the calculus. The next work is the lowering spike — the pure fragment only, with `program_sem_id`, `lowering_id` and `target_term_sem_id` kept as three identities so the result is a refinement statement rather than a renaming — and then native ic32 films, which remain **not gated** on the derivation language.

---

## Round 19 — outside the semantic projection had become unchecked

**85. Round 16's ruling was right and left a hole nobody had named.** Access order is execution strategy and must not be semantic identity — that stands. What round 16 did not say, and what v0.5.0 therefore did not do, is that a field excluded from the *comparison* still needs a rule of its own. **T-1**, frozen in `probe_traceforge_v06_repro.mjs`: a program reading `a` then `b` traces `[["a",1],["b",1]]`; reverse **only** the trace, leave the canonical footprint and the value untouched, and against v0.5.0 —

```
validateForeignResult  → { ok: true }
authority.accept       → { ok: true, validated: true, fresh_at_check: true }
```

`checkResult` compared the footprint to the *set* of the trace, which a reversal does not change, and `validateForeignResult` compared only the semantic projection, from which the trace was excluded. So the one field carrying execution evidence was the one field nothing looked at.

**86. The flat shape was part of the defect.** `read_trace` sat as a sibling of `value`, `support` and `read_footprint`. A field inside `DeriveResult` reads as authenticated by the same machinery as its neighbours, and this one was not — the exclusion was a comment, and comments do not hold. The envelopes are now explicit, and the trust status of each field is visible in the shape:

```
semantic_result      value · witness · support · read_footprint
                     determines portable meaning; this is what
                     cross-implementation validation compares

execution_evidence   implementation_id · read_trace
                     conformance and provenance; excluded from the
                     comparison and NOT excluded from checking
```

**87. NON-SEMANTIC DOES NOT MEAN UNVERIFIED.** That sentence is the whole round, and it is now the opening clause of `law:derivation.execution-evidence@1`. The core *fixes* evaluation order precisely so that refusals and traces reproduce, so a returned trace disagreeing with the authority's own re-derivation is a **conformance failure of the implementation**, not a disagreement about the program — refused as `trace-nonconforming`. And the two verdicts are reported **separately**: `semantic_agreement: true, trace_conforms: false`. *"Same meaning, different strategy"* and *"wrong answer"* are different diagnoses, and v0.5.0 could make neither because it never looked.

**88. The non-vacuity detector caught two more falsifiers this round's own edits had killed.** `derive-trace-made-semantic` and `derive-semantic-projection-widened` both targeted the literal `NON_SEMANTIC_RESULT_FIELDS`, which the envelope split removed, and `acceptance-claims-committable` targeted a return statement this round rewrote. All three changed nothing and were reported `VACUOUS` rather than passing. That is the third, fourth and fifth time this session — and every one was found by the mechanism rather than by a reader.

**89. Gate.** grid **v1.20.0** — 62 entries / 343 citations · `derive_protocol.mjs` **0.6.0** · kernel PASS · World 0.12.0 PASS · `--check-receipt` PASS · negative battery **100/100** with five new forgeries · bridge 48/48 · derive **41/41 in-process, 10/10 across a realm** · probes **2/2+2/2**, **4/4+5/5**, **5/5**, **3/3+4/4**, **1/1+4/4** · harness **9/9**. `scheduler_certificate.json` byte-identical — fourteenth consecutive round.

**The shape of the last four rounds.** 16 froze what a program *means*. 17 fixed what an authority *authenticates* and what acceptance may *claim*. 18 measured the measurer. 19 is the one that says the quiet part: this system now has enough distinct evidence classes — semantic, execution, transaction — that each needs its own explicit trust boundary, and a field is not safe merely because it has been excluded from someone else's.


---

## Round 20 — a perturbation result needs a declared clean baseline

**90. M-9 generalises, and the wrong generalisation was the obvious one.** "Every gate must report nothing when nothing is wrong" fails immediately: the kernel, the World and the bridge all legitimately print their results, and they are not perturbation experiments — they ARE baseline observations. The invariant belongs to a narrower and much more common claim: *"I changed X, and therefore X caused this failure."* Only a falsifier asserts that, and only a falsifier can be wrong about it in the way round 17 found.

**91. `law:evidence.clean-baseline@1`, and the word is DECLARED rather than silent.** A perturbation-based result is admissible only if the identical verifier, fixture, environment and artifact set satisfy their **declared** baseline before the perturbation is applied — and each falsifier family names its own:

| family | declared baseline |
|---|---|
| `negative_battery.sh` | `grid_check` exits 0 on the unperturbed fixture — **implemented** |
| paired probes | the live half is confined; both directions required — **implemented by construction** |
| one-directional 9D probes | the honest fixture holds the invariants under attack — **declared open** |
| bridge / kernel / World | positive gates; themselves baseline observations — nothing added |

Five phases, in order: `establish_baseline` · `perturb` · `assert_perturbation` · `run_subject` · `assert_specific_diagnostic`.

**92. The baseline is established once and each case proves it inherited it.** Every case builds its fixture by the same recipe from the same source, so one baseline run covers them all — but that is exactly the sort of "obviously true" step this record keeps finding to be false. So it is verified rather than assumed: each case compares its own pre-perturbation digest against the baselined tree and fails **FIXTURE DRIFT** if they differ. A failed baseline aborts the whole run and says why, in the words that matter: *no case below is isolated-cause evidence.*

**93. The self-test stays bounded at nine, deliberately.** Promoting M-9 into a law applied as a **precondition** of every falsifier family is not the same as adding six more meta-cases for the kernel, the World and the bridge. The second is the infinite regress the self-test was written to avoid, and the bounded suite is worth more than a larger one precisely because its boundary is defensible.

**94. And this round's own edit inflated a counter by one.** The phase insertion matched in both runners — `run_case` and `run_case_engine` — so the engine case incremented `CASES` twice and the printed total read **101** where the case set was 100. Caught because the number moved when nothing about the case set had, which is the only reason a derived total is worth having: the round-10 repair that made these counters derived rather than hand-typed is what made this visible at all.

**95. Gate.** grid **v1.21.0** — 63 entries / 344 citations · kernel PASS · World 0.12.0 PASS · `--check-receipt` PASS · negative battery **103/103**, with a declared baseline established and every fixture proved to inherit it · bridge 48/48 · derive **41/41 · 10/10** · probes **2/2+2/2**, **4/4+5/5**, **5/5**, **3/3+4/4**, **1/1+4/4** · harness **9/9**. `scheduler_certificate.json` byte-identical — fifteenth consecutive round without the calculus moving.


---

## Round 21 — the gate could not fail

**96. The derive battery ran BROKEN for a full round and `make governance` stayed green.** The round-19 envelope split moved `read_footprint` inside `semantic_result`, and one call site in `derive_battery.mjs` was missed. The battery crashed on it — `TypeError: Cannot read properties of undefined (reading 'exact')` — and the gate reported success for round 19 and round 20, because every governance recipe was written

```make
@cd $(GOV) && $(NODE) derive_battery.mjs | tail -1
```

and **`cmd | tail -1` takes the exit status of `tail`**. A crashing subject printed a stack trace's last line where its verdict should have been, and the pipeline exited 0. Found while assembling a review bundle — by reading a line of output, not by the gate.

**97. A gate that cannot fail is a display.** All thirteen governance recipe lines now capture the subject's output *and* status before printing (`out=$(cmd) && printf …`), so the recipe fails on the subject's own status. Verified in both directions rather than asserted: an **unresolvable import** (a crash) and a **false assertion** (exit 1) each fail the target, and the restored file passes. `law:evidence.clean-baseline@1` gains this as its runner half — the baseline clause is about the *fixture*, and this is the same disease in the *runner*.

**98. And the first crash test written for it was vacuous.** Appending `throw new Error("deliberate crash")` to the end of the battery proved nothing: the file ends in `process.exit(fail ? 1 : 0)`, so the throw is unreachable. The test reported the gate as passing a crash it never experienced. That is the ninth species — a falsifier that does not perturb what it claims to — committed while building the fix for a tenth, and it is recorded rather than quietly corrected because the alternative is a record that only contains the mistakes I noticed in time.

**99. A section of the grid was lost in the round-16 split, and a review brief asserted it was there.** The combined round-16 draft carried `lowering_spike` — `TRVM-TERM-CANON-v1`, the three properties, the decision rule. Splitting that draft into rounds 16/17/18 rebuilt the grid from the round-15 base, and the section was never re-added. The review brief for 16/17/18 then stated that `TRVM-TERM-CANON-v1` was *"recorded in `lowering_spike`"*, while the machine-readable extract shipped in the same bundle contained `"lowering_spike": null`. **The prose was wrong and the extract was right**, which is the only reason it is knowable at all — and it was found by an unrelated edit failing with `KeyError: 'lowering_spike'`, not by anyone reading either. Restored in this round with the fourth identity the review supplied, locked by `grid_check`, and given its own forgery. The lesson is not "check the prose": it is that the machine-readable half of a claim is worth shipping precisely because it can contradict the sentence beside it.

**100. Gate.** grid **v1.22.0** — 63 entries / 346 citations · negative battery **105/105** · derive **40/40 · 10/10** · probes **2/2+2/2**, **4/4+5/5**, **5/5**, **3/3+4/4**, **1/1+4/4** · harness **9/9** · bridge 48/48 · kernel PASS · World 0.12.0 PASS. `scheduler_certificate.json` byte-identical — sixteenth consecutive round.

**The uncomfortable summary of rounds 15 through 21.** Seven consecutive rounds, and in six of them the defect was in the evidence apparatus rather than in the thing it measures: a footprint that could be produced without a read, an identity that bound a spelling, an issuance that authenticated the wrong object, a trace excluded from comparison and therefore from checking, a fixture that was already red, and a gate that could not fail. The calculus has not moved in sixteen rounds. What keeps moving is the machinery that claims to be watching it.


---

## Round 22 — an execution claim is not provenance

**101. The law said impersonation was closed. JavaScript could impersonate C all the way through acceptance, and had been able to for seven rounds.** `law:derivation.implementation-provenance@1` — superseded by `@2` in this round, and kept on the record as the history of a false claim rather than quietly revised — stated *"a caller therefore cannot cause a result to claim an implementation that did not produce it"*, and named its open half as "not yet a digest of executable bytes". **P-1**, frozen in `probe_execclaim_v07_repro.mjs`: `deriveLocally(registry, req, implementationId)` took the identity as a **parameter**, so —

```
authorize(intent, {expected_implementation_id: "impl-c-derive-v0.6.0"})
deriveLocally(reg, req, "impl-c-derive-v0.6.0")     ← the JS evaluator runs
authority.accept(reg, req, res)

  → { ok: true, validated: true, fresh_at_check: true,
      trace_conforms: true, implementation_id: "impl-c-derive-v0.6.0" }
```

Every byte honest JS output; only the label C. Acceptance compared the caller's **expectation** against the caller's own **label** — a claim against a claim — and agreed with itself. Worse, `trace_conforms: true` made the forgery read as *better attested* than an unforged result.

**102. Hashing the executable would not have closed it, which is why the declared-open item was mis-scoped.** A digest carried inside the same untrusted result is self-asserted: a forger writes the digest too. The missing object was never a stronger label. **It is independent observation of which executor actually ran** — and the host has that, because the host is what spawned the worker.

**103. Round 19's two envelopes were one short.**

```
semantic_result        portable MEANING
execution_evidence     the execution CLAIM — what the result says happened
host observation       the only OBSERVATION — what the host launched
```

`deriveLocally` takes no implementation parameter; an implementation's identity comes from the implementation. `validateForeignResult` establishes semantic agreement and trace conformance and **explicitly not provenance**, reporting `implementation_claimed` rather than certifying it. `registerExecutor` records what the host launched and returns a handle carrying a private `Symbol`, so a caller cannot fabricate one. Acceptance compares the requirement against the **observation**, refuses `implementation-claim-contradicts-observation` when the label disagrees with it, and answers **`implementation-provenance-unavailable`** — never "verified" — where no observation exists. What a native executable should register (a trusted launcher hashing the binary it execs) stays declared open; **whether** an observation exists is no longer optional.

**104. `trace_conforms` leaves the acceptance success shape.** It is not wrong the way `committable` was — it is a stable verdict about this result against this frozen core, not a claim that decays — but on success it is redundant, because acceptance cannot reach success without it, and a boolean per check invites a reader to weigh them. It stays in the validator and in the failure diagnostics, where `semantic_agreement: true, trace_conforms: false` is exactly the distinction worth having. `fresh_at_check` stays, because its temporal limitation is meaningful.

**105. The forgery was sitting in the realm battery as a passing test.** `cross-implementation-shape` took an honest JS result, relabelled it `impl-c-derive-…`, and asserted that validation succeeded and "the authority records WHO ran it". That *is* P-1, written as a green case, since round 15. It now asserts what it always measured: a result **claiming** a foreign executor agrees on meaning and conforms on its trace, and the validator reports the claim rather than certifying it.

**106. The runner half of `clean-baseline@1` becomes executable, and stays out of the bounded nine.** `runner_contract.sh`, **3/3**: it extracts the *actual* governance recipe form from the Makefile, builds a throwaway target from it, and requires success on exit 0, failure on exit 1, and failure on a crash that prints nothing. If it cannot find the recipe form it fails rather than passing vacuously. The nine harness species are about falsifier non-vacuity; process-status propagation is a different layer, and separating them is principled rather than a way to keep the count at nine.

**107. And the outcome identity is ruled before it is built.** `outcome_sem_id` must **not** hash a human-readable reason. Rendering `"program-type: add of non-number"` is diagnostics; hashing it would recreate round 16's *"the identity bound a spelling"* one layer up, where two conforming implementations could differ by a comma. `TRVM-DERIVE-OUTCOME-v1` encodes structurally: `{status:"value", value}` or `{status:"refused", code, locus}`, `code` drawn from the frozen core's refusal vocabulary.

**108. Gate.** grid **v1.23.0** — 64 entries / 347 citations · `derive_protocol.mjs` **0.7.0** · kernel PASS · World 0.12.0 PASS · `--check-receipt` PASS · negative battery **112/112** with seven new forgeries · bridge 48/48 · derive **45/45 in-process, 10/10 across a realm** · probes **2/2+2/2**, **4/4+5/5**, **5/5**, **3/3+4/4**, **1/1+4/4**, **1/1+6/6** · harness **9/9** · runner contract **3/3**. `scheduler_certificate.json` byte-identical — seventeenth consecutive round.

**109. The review pack that carried round 21 was itself broken, and said so in the file the manifest authenticated.** The bundle's `gate/make-governance.txt` contained `make: *** No rule to make target 'governance'` and its captured negative battery contained `cd: governance: No such file or directory` — because the capture ran from the wrong directory — while the README asserted 105/105 from them. There was even a drift witness in the same bundle: the captured harness said 347 citations where the README said 346. The manifest verified perfectly, because a manifest authenticates *bytes*, not *meaning*. Round 21's thesis, reproduced by round 21's own review pack: **a displayed gate is not an executable gate.** The repair is the same one: the pack must be executable, its counts generated by replaying it, never transcribed.

**The seam list, seven rounds long.** grant vs footprint · syntax vs semantics · grant identity vs issuance · semantics vs execution trace · perturbation vs baseline · subject status vs runner status · and now **execution claim vs observed executor**. Every one of them a place where two things that felt like one thing were not. The calculus has not moved in seventeen rounds; what keeps moving is the boundary between kinds of evidence.

## Round 23 — executor existence is not execution provenance, and the C runtime originates a frame

**110. Registration was an assertion wearing an observation's clothes, and the P-1 attack had simply moved.** Round 22's architecture sentence was *"the host observes what it launched"*. Its mechanism, `registerExecutor(implementation_id)`, launched nothing: it took a string, put it in a private Map, and returned a handle carrying a private `Symbol`. **P-2**, frozen in `probe_execreg_v08_repro.mjs` against a verbatim copy of v0.7.0 —

```
actual executor:  impl-js-derive-v0.7.0

auth.registerExecutor("impl-c-derive-v0.7.0")   ← nothing C-shaped is launched,
                                                  or present, anywhere
the JS evaluator produces the result
the result is relabelled C
authority.accept(reg, req, res, thatHandle)

  → { ok: true, validated: true, fresh_at_check: true,
      implementation_provenance: "observed",
      implementation_id: "impl-c-derive-v0.7.0" }
```

The Symbol proved *this authority minted this handle*. It did not prove *this authority observed this implementation execute this request and produce this result*, and only the second sentence is provenance. So:

```
v0.6   the caller chooses the identity at deriveLocally()
v0.7   the caller chooses the identity at registerExecutor()
```

**111. And the round-17 shape came back one level up.** Round 17's lesson was that acceptance must take no proofs from its caller — issuance and the live reader became closed-over authority state rather than arguments. Then v0.7.0 wrote `accept(registry, req, res, executor = null)`, and the handle was a proof supplied at acceptance time. **P-2b** reproduces the consequence directly: one handle provenances two unrelated executions, because a handle binds neither a request nor a set of bytes. Even a registration that really launched C could have had its handle paired with a result produced anywhere else. The law:

> **Executor existence is not execution provenance. An observation must bind the executor, the request and the returned bytes as ONE execution event.**

which is the issuance lesson, one layer higher:

```
request provenance     don't authenticate the grant;
                       authenticate the WHOLE REQUEST.
execution provenance   don't authenticate the executor handle;
                       authenticate the WHOLE EXECUTION EVENT.
```

**112. Manual registration is deleted rather than improved, and the authority becomes the thing that runs an executor.** `execute(req, launcher)`: the authority reads the artifact's files **itself** and hashes them, resolves the family name from its **own** digest→name policy, spawns, sends *this* request, takes *these* bytes, and only then records an observation keyed by `H(request_sem_id | canonical(the whole result))`. `accept(registry, req, res)` takes no provenance argument and consults that privately held table. Change any byte of the result — including `implementation_id` — and the key **misses**; there is no "was this relabelled?" comparison, because the question cannot be asked of a table the bytes are not in.

A launcher supplies **mechanism and no identity**: `artifact_files` (where) and `spawn` (how). It gets no field in which to state what it is. A launcher that spawns the real worker while declaring someone else's files is identified as those files.

**113. Three identities, because one string was answering three questions.**

```
implementation_family_id   what protocol implementation this is
executable_artifact_id     H(the bytes the authority read)
executor_session_id        this particular authority-driven launch
```

The digest→name direction (`nameArtifact`) is a **naming policy and not an observation** — it says what bytes are *called*, never that anything ran — so naming a digest `"impl-c-derive-v0.8.0"` succeeds and buys nothing. It is injective in both directions and refuses rebinding, because a policy a caller can rewrite mid-run is a policy a caller chooses.

**114. And the strongest statement is deliberately weaker than it could be made to sound.** Hash-then-spawn supports *"the host observed artifact X immediately before requesting execution of path P"*. It is **not** a proof that the OS executed those exact bytes under every filesystem race, and it is **not** hardware-attested executable identity. Uncovered and named: the node binary and standard library for a JS executor, every shared object the loader binds for a native one. `law:derivation.implementation-provenance@2` is superseded by `@3` and kept on the record; a negative case fires if the attestation caveat is ever deleted from the statement.

**115. The execution plane originates evidence.** For twenty-two rounds every semantic film in this tree was **made by the law kernel**. The C runtime could say what semantic *state* it was in — 48/48 byte-identical signatures since round 12 — and could not say that it had *moved*, so every transition's evidence was JavaScript's and a C runtime appeared in the record only as a thing the record described. `bridge/ic32_film.c` emits one frame of `TRVM-SEMFILM-v1.1` from ic32's own execution, and the law kernel's **own** `replaySemFilm` — imported unmodified, on a fresh runtime — accepts it.

```
canonical pre-state → host LAUNCHES ic32_film (hashed first) → ONE native C rewrite
                    → rule · canonical locus · post-state · terminal
                    → replaySemFilm on a FRESH runtime → ACCEPT
```

The fixture is `apply_id`, corpus vector 3, `ref_interactions = 1`: its whole reduction *is* one rewrite, so its pre-state is the vector's `initial` and its post-state is the vector's `normal_form` — two states the bridge gate had already shown C and JS agree on byte for byte. **The only new claim is the transition between them.** Nothing is smuggled in through the endpoints.

**116. Every clause of the theorem is a checked precondition, and the scope is a refusal rather than a silence.** The emitter enumerates redexes and requires exactly one; fires exactly it and requires the interaction count to move by exactly one; recomputes the post-state; re-runs the same enumeration and requires it empty before saying `NORMAL_FORM`; and requires the readback to be **pure** — resolving the state must cost no interaction. A dup-carrying term is `film-dup-cell-present`, an already-normal term is `film-no-redex-at-source`, a two-redex term is `film-source-redex-ambiguous`. `ic32_film.c` **`#include`s `ic32_canon.c`** under a new `IC32_CANON_NO_MAIN` guard, so the canonicalizer beneath the film is the same code the 48/48 bridge replays rather than a copy written for the occasion — and the bridge is still 48/48 after the guard.

**117. The first version of the emitter printed a binder name where a term was bound.** `ic32`'s `show_iter` does not chase substitutions, because nothing in ic32's own flow ever hands it an unresolved one — `normal()` runs first. After a single APP-LAM the post-state is `λt.(t x)` with `x ↦ λy.y`, and the readback came out `λa.(a b)`: a well-formed string asserting an identity that does not hold, which is the same class of fault ic32's own `reset_state` comment warns about for free names. The repair is the kernel's own rule — `readback` resolves before printing — and readback **purity** is now a checked refusal rather than a remark.

**118. Seven forgeries, each re-committed so it dies on the calculus rather than on bookkeeping.** F-1 wrong pre-state → `sem-revision-mismatch`; F-2 wrong post-state → `sem-post-mismatch`; F-3 a real rule at a wrong locus → `sem-locus-not-enabled`; F-4 a real redex misdescribed as a dup rule → `sem-rule-mismatch`; F-5 the honest film replayed against another source term → `sem-revision-mismatch`; **F-6** a genuine C observation that cannot be re-pointed at another film; **F-7** an edit to the frame's *declared-non-authoritative* index `i`, which still **replays** and still **loses provenance**. F-7 is the one worth keeping: replay and provenance are different verdicts, and the second is over the bytes as they were observed. F-6 and F-7 are P-2's closure in the film plane, which is why the two halves of this round are one piece of architecture and not two.

**The two transition systems stay separate.** The TRVM calculus film is `pre-state → (rule + locus) → post-state` over the ic32 interaction-net relation; the derivation evidence relation is `DeriveRequest → evaluate → DeriveResult`. What they share is **host infrastructure** — hash the artifact, launch it, key the observation over the whole event — and no semantics. `film_planes` (§61) exists because a session could otherwise finish the second and write that the first was done.

**119. Three defects in the review pack, all the same fault in miniature.** A **SKIPPED** gate left `FAILED=0` and the footer still said *"every gate replayed green"* — so a CI that lost its compiler read as a full replay. The native gates are required by default now; `--allow-skip-bridge` downgrades the verdict to **PARTIAL**, and a run with two skips prints `attempted 18 / passed 16 / failed 0 / skipped 2 — this is NOT a green replay`. The prose said *"all eighteen gates"* while the script ran sixteen: the runner **counts** now, and there is no sentence left to keep in sync. And a failed manifest carried on executing the very files whose integrity had just failed — it **aborts**.

**120. Replacing a hand-typed list with a glob was the wrong repair, and the pack caught it on its first replay.** Globbing `probe_*_repro.mjs` ran the ten probes that freeze a **declared-open** boundary and exit nonzero **by design**, and the pack reported four failures for witnesses behaving correctly. Which probes gate is not derivable from a filename: the **paired** ones gate. So `gating_probes` is declared in `artifacts.json`, the pack reads it, and `grid_check` compares it against the Makefile's list — two hand-maintained copies of one list is how a probe gets added in one place and gates in neither.

**121. Two instruments were measuring less than their reports implied, and both were found by the instruments above them.** The negative battery and the harness self-test each built a **flat** case tree, so the moment `grid_check` began asserting invariants on `bridge/*` the unperturbed baseline failed on four absent files — caught by M-9 and by the BASELINE meta-case, which is what they are for. `subdir_case_inputs` and `gating_probes` are declared and copied with structure. Separately, `grid_check`'s two governance-recipe checks read `../Makefile` and **skipped silently when it was absent**, so in every scratch tree they scanned nothing and passed: absence is a failure now, and the case trees carry a copy. The new `gate-list-drifts-from-registry` forgery is what exposed it, by passing when it should not have.

**122. Gate.** grid **v1.24.0** — 66 entries / 351 citations (this line is a transcription in a record of a moment; the gate derives it, and writing this section moved it from 350) · `derive_protocol.mjs` **0.8.0** · kernel PASS · World 0.12.0 PASS · `--check-receipt` PASS · negative battery **132/132** with fifteen new forgeries · bridge **48/48** · **native semantic film 13/13** · derive **45/45 in-process, 19/19 across a realm** · probes 2/2+2/2, 4/4+5/5, 5/5, 3/3+4/4, 1/1+4/4, 1/1+6/6, **2/2+5/5** · harness **9/9** · runner contract **3/3** · review pack replays **18/18 green from an arbitrary directory**. `scheduler_certificate.json` byte-identical — eighteenth consecutive round, and the kernel gained five exports this round, so `cert_id a08ee15d…` is the proof that the addition was additive.

**The seam list, eight rounds long.** grant vs footprint · syntax vs semantics · grant identity vs issuance · semantics vs execution trace · perturbation vs baseline · subject status vs runner status · execution claim vs observed executor · and now **executor existence vs execution event**. Every one a place where two things that felt like one thing were not.

**What changed about the shape of the work.** Rounds 15–22 were all governance: the calculus stood still while the boundary between kinds of evidence moved. This round the boundary moved *and* the execution plane crossed it — the C runtime is now a producer of evidence in the governed language rather than a subject the governance plane writes about. That is a threshold, and it is one frame wide. **Next**, in order: the C-side checker, so a JS film is accepted by C and the direction reverses; then the dup rules and the `d:`/`v:` loci, which is where the canonical locus stops being a tree path; then multi-frame films and the corpus. `film-dup-cell-present` is the marker for exactly how far this got.

## Round 24 — a launch descriptor may not carry both the evidence and an action

**123. The authority hashed one thing and executed another, and the round-23 gate could not see it.** v0.8.0's repair was real as far as it went: the authority read the artifact's bytes itself instead of believing a name. Then it called a function the same caller had supplied beside the declaration.

```
{
  artifact_files: X,   ← the EVIDENCE, which the authority hashes
  spawn: Y             ← an INDEPENDENT caller-controlled ACTION
}
```

Two fields of one object, mechanically unrelated. **P-3**, frozen in `probe_execlaunch_v09_repro.mjs`: declare the genuine `derive_worker.mjs` + `derive_protocol.mjs` closure, name that digest `impl-c-derive-v0.8.0`, and hand `execute()` a `spawn()` that evaluates the request in-process and changes only the returned label —

```
→ { ok: true, validated: true, fresh_at_check: true,
    implementation_provenance: "observed",
    implementation_id: "impl-c-derive-v0.8.0",
    executable_artifact_id: <digest of the REAL JS closure> }
```

with no C anywhere and no worker either. The hash was honest and answered a question nobody had asked. So

```
authority read bytes X  →  authority launched X      DID NOT FOLLOW
authority read bytes X  →  authority invoked callback Y      is what held
```

**124. And it existed in the film plane too, where it says something sharper.** **P-3F** supplies the *real* `ic32_film` binary as `artifact_files` — so the digest is genuinely C's and the family name is genuinely C's — and a `run()` returning a film C produced earlier. No C process executes during the observation and `film_provenance` is still `"observed"`. The probe runs this rather than describing it. It separates two truths that this project has spent nine rounds learning to keep apart: **the film is semantically valid — `replaySemFilm` proves it — and the claimed execution provenance is false.**

**125. The pattern across four revisions is the point, and it is why the repair is structural.**

```
@1  the caller picks the LABEL                       deriveLocally(…, id)
@2  the caller picks the NAME registration reports   registerExecutor(name)
@3  the caller picks the ACTION beside the evidence  {artifact_files, spawn}
```

Each revision closed one supplier and left the next. Any field a caller controls on the launch path becomes the provenance. So the caller supplies **nothing** on that path:

> **Artifact observation does not establish execution provenance unless the mechanism invoked is mechanically DERIVED FROM the artifact observed. A launch descriptor may not carry both the evidence and an independent executable action.**

`law:derivation.implementation-provenance@3` is superseded by `@4`, and `@3` stays on the record — it was right about the half it named.

**126. `ObservedExecutionHost`, and the fence moves rather than the wall.** Constructed with an **immutable executor catalog**: family → `{kind, entrypoint, artifact_closure}`, deep-frozen, injective, refusing an entrypoint that is **not inside the closure it hashes** (that is P-3 with the descriptor moved indoors) and refusing **any** entry field beyond those three (which is where a `spawn()` would have to reappear). The transport per `kind` is written in the host. `execute(registry, req)` names a family and nothing else; the invocation is **data**, canonicalised, and `canonicalBytes` refuses a function outright — so the mechanical reason an action cannot ride along is the same rule the message domain has enforced since v0.1.0. `nameArtifact` is gone with the rest: the catalog *is* the naming policy and it is fixed before the authority exists.

Round 23 built this mechanism **twice** — once in `DerivationAuthority`, once in `film_check`'s `FilmAuthority` — and reproduced P-3 in both. Duplicating the **semantic** boundary was right and stays (`film_planes`: the calculus film and the derivation relation are different transition systems, and merging them lets a session finish the second and write that the first is done). Duplicating the **mechanism** was the defect. So both authorities now share the host, which holds catalog, hashing, launching, transport, sessions and the one observation table — and **no TRVM semantics at all**. It cannot re-derive a result, replay a film, or say what either means.

**127. Two smaller corrections that came with it.** The far side's program image is now `registry.image()` — the authority's own registry — where v0.8.0 let the caller choose which programs the worker would hold by passing them to the launcher it also built. And acceptance reports `executor_sessionS`, **plural**: the key is over BYTES, so two launches producing byte-identical output share it, and v0.8.0 both overwrote the earlier record *and* reported one id as though it named the launch that produced the copy in hand. It never did. What is true is "these recorded sessions are known to have produced these request/result bytes".

**128. F-7 is renamed rather than made literal.** It was never "JS relabelled as C" — there is no JS film emitter, and manufacturing an implementation solely to manufacture an adversary would be building the wrong thing. It is **F-7a, replay-preserving mutation**: editing the frame's declared-**non-authoritative** index `i` on a genuinely observed film, which still **replays** and still **loses provenance**. The theorem it proves is worth having on its own — provenance is over the observed bytes including the fields replay deliberately ignores — and it is now stated as that rather than as a substitute for something else. Film provenance is also keyed over the **whole emission** now, not the film alone: provenance is over everything the executor emitted, never over a subset a caller chose to present.

**129. Three answered questions, recorded because the answers are rulings and not defaults.** In-process `deriveLocally` keeps `implementation_provenance: "unavailable"` — the authority and the reference evaluator sharing a process is a topology, not independent execution provenance, and manufacturing an observation there would dissolve the distinction the last three rounds were spent establishing. Observations stay **reusable**: consuming them would conflate evidence validation with commit authorization, which is the `committable` category error again; if one-shot effects need anti-replay later, that rule belongs in the transaction layer. And the naming policy's **factoring** was right — taxonomy and observation are different operations — while its **mutability** was not, so it is frozen at construction, and freezing it was never the P-3 repair.

**130. A third hand-maintained file list, found the same way as the first two.** M-8 built its tree from three hand-typed filenames, so the moment `derive_protocol.mjs` imported the new host module the meta-case broke on a missing file. It uses the declared case-input tree now. That is three rounds running in which a list kept in two places drifted: the probe gating set (round 23), the subdir artifacts (round 23), and this.

**131. Gate.** grid **v1.25.0** — 67 entries / 353 citations (transcribed at a moment; the gate derives it, and writing this section moved it from 352 — the same drift round 23 recorded, and the reason nothing executable carries a typed count) · `derive_protocol.mjs` **0.9.0** · `observed_execution_host.mjs` **0.1.0** · kernel PASS · World 0.12.0 PASS · `--check-receipt` PASS · negative battery **143/143** with eleven new forgeries · bridge **48/48** · native semantic film **14/14** · derive **45/45 in-process, 20/20 across a realm** · probes 2/2+2/2, 4/4+5/5, 5/5, 3/3+4/4, 1/1+4/4, 1/1+6/6, 2/2+5/5, **2/2+5/5** · harness **9/9** · runner contract **3/3**. `scheduler_certificate.json` byte-identical — nineteenth consecutive round.

**The seam list, nine rounds long.** grant vs footprint · syntax vs semantics · grant identity vs issuance · semantics vs execution trace · perturbation vs baseline · subject status vs runner status · execution claim vs observed executor · executor existence vs execution event · and now **the artifact observed vs the mechanism invoked**.

**Where this leaves the two theorems.** Round 23's **native semantic-film theorem stands** — it was never what P-3 touched, and the frame still replays. Round 23's **execution-provenance theorem was falsified** by P-3/P-3F and is re-established here on a mechanism with no caller-supplied surface left. Reporting them separately is the honest classification and is more informative than a verdict on "the round".

**Next**, and it is a phase change rather than another hardening loop: the **lowering spike**, whose chain the grid has had declared since round 18 —

```
program_sem_id  →(lowering)→  target_term_sem_id  →(native ic32)→  target_nf_sem_id  →(decode)→  outcome_sem_id
```

with source/target outcome equality as the refinement obligation. The missing middle is no longer missing: native ic32 can originate a semantic film the independent kernel replays. Lower `add(const 2, const 3)` through the real governed runtime.

## Round 25 — acceptance took its semantic oracle from the claimant

**132. The last supplier was the one nobody had looked at, because it was the first parameter.** By v0.9.0 the authority owned issuance, the World reader, execution observations, the execution host and freshness. It did not own the thing that says what a `program_sem_id` **means**.

```
accept(registry, req, res)
       ^^^^^^^^
       supplied by the caller, every time
```

**P-4**, frozen in `probe_semoracle_v10_repro.mjs`: issue an ordinary request for `{op:"const", value:5}`, then hand acceptance

```js
{ verify: () => ({ ok: true }),           // blesses the ISSUED id
  get:    () => ({ op:"const", value:999 }) }
```

and 999 is accepted under the issued id — `{ ok: true, validated: true, fresh_at_check: true }` — while the identical result against the real registry is `foreign-result-divergence`. **Re-derivation was working perfectly.** It re-derived against the program the *claimant* nominated, agreed with itself, and reported agreement. The entire difference between the two lines is who supplied the oracle.

Provenance being `"unavailable"` does not save it: a request stating no `expected_implementation_id` is *allowed* to accept a semantically validated result with no observed execution. That is the in-process path and it is correct on its own terms.

**133. Four rungs, one shape.**

```
@1  the caller supplied the implementation LABEL     deriveLocally(…, id)
@2  the caller supplied the registration NAME        registerExecutor(name)
@3  the caller supplied the ACTION beside the        {artifact_files, spawn}
    artifact evidence
@4  the caller supplied the SEMANTIC ORACLE          accept(registry, …)
    used at acceptance
```

Round 24's generalisation was *any field a caller controls on the launch path becomes the provenance*. P-4 is its exact twin on the semantic side: **an authority cannot validate a semantic claim using a program resolver supplied by the claimant.** Acceptance takes no proof from its caller, **including the mapping from semantic identity to semantic program**.

**134. `instanceof` would not have closed it, and a law that read as "check the type" would have invited the wrong repair.** **P-4b** is the case that says so: the oracle is a *genuine* `ProgramRegistry` instance, holding a different program. No Proxy, no hostile object, and the type check passes. The question was never the type. It is **ownership** — and the registry is now BUILT at the authority's construction from canonical program **data**, severed through `canonicalBytes` by `ProgramRegistry.bind`, which the authority calls itself. Accepting a ready-made registry would have satisfied any check and left the ownership exactly where P-4 found it.

**135. `bindProgram` stays, and needs no second rule.** Teaching a long-lived authority a new program is an explicit authority operation, and it is safe for the reason the id exists at all: the id **is** the program's hash, so `const(999)` gets its own and cannot become `const(5)`'s. Growing the registry cannot repoint an issued id. That is round 16's ruling paying a dividend nine rounds later.

**136. Which leaves the object with a boundary rather than a parameter list.**

```
DerivationAuthority
├── issued requests
├── semantic program registry          ← P-4
├── authoritative World reader         ← round 17
└── ObservedExecutionHost              ← P-3, with its immutable catalog
```

and a caller supplies exactly two things: **an INTENT, and a RESULT TO VALIDATE.** Every oracle the authority consults is constructor-time. The live case that matters is not any one of them but the set: `the-supplier-ladder-is-empty` asserts all four at once, because a ladder is only closed if the list is finite and someone has written the list down.

**137. Gate.** grid **v1.26.0** — **71** entries / 361 citations (68 enforced plus the three lowering laws registered OPEN and unbuilt; transcribed at a moment, and the gate derives it) · `derive_protocol.mjs` **0.10.0** · kernel PASS · World 0.12.0 PASS · `--check-receipt` PASS · negative battery **150/150** with seven new forgeries · bridge **48/48** · native semantic film **14/14** · derive **45/45 in-process, 20/20 across a realm** · probes 2/2+2/2, 4/4+5/5, 5/5, 3/3+4/4, 1/1+4/4, 1/1+6/6, 2/2+5/5, 2/2+5/5, **2/2+5/5** · harness **9/9** · runner contract **3/3**. `scheduler_certificate.json` byte-identical — twentieth consecutive round, across four rounds that rebuilt the authority's entire parameter surface without touching the calculus once.

**The seam list, ten rounds long.** grant vs footprint · syntax vs semantics · grant identity vs issuance · semantics vs execution trace · perturbation vs baseline · subject status vs runner status · execution claim vs observed executor · executor existence vs execution event · the artifact observed vs the mechanism invoked · and now **re-derivation vs the oracle it re-derives against**.

**Next: the lowering spike, and its shape is ruled before it is built.** Three logically independent relations, which can each fail while the others hold, so they get three obligations and three identities rather than one:

```
program_sem_id  ──lowering_sem_id──▶  target_term_sem_id
                                            │
                                     native semantic film
                                            ▼
                                      target_nf_sem_id
                                            │
                                      decode_sem_id
                                            ▼
                                   target_outcome_sem_id
source evaluator ─────────────────▶ source_outcome_sem_id

REFINEMENT:  source_outcome_sem_id == target_outcome_sem_id
```

`law:derivation.canonical-lowering@1` (one source program under one lowering semantics determines one canonical target term), `law:derivation.target-decoding@1` (one canonical normal form under one decoder determines one structural outcome, or a structural decode refusal), and `law:derivation.lowering-refinement@1`, which composes them and is the theorem actually wanted. The first two exist to make the third **diagnosable**. *(Both `@1`s were **superseded** at B1.2.1 — canonical-lowering by `@2`, lowering-refinement by `@2`; this line is history and stands as written.)*

**And the lowering does NOT get a film.** A film is evidence for a *transition system*; lowering is a relation `DeriveProgram → TargetTerm`. Filming it would invent a sequence of internal compiler steps and make implementation strategy semantic — the same mistake the read-order ruling refused in round 12. The instrument is **re-lowering and comparing canonical target bytes**. A film becomes appropriate only if the lowering engine itself ever becomes a governed transition system whose intermediate steps matter.

`lowering_id` also splits in two before it is written, because one id must not silently answer two questions: `lowering_sem_id` identifies the lowering *semantics* (source core id, target encoding id, canonical specification, conformance-vector identity), and a `LoweringReceipt {program_sem_id, lowering_sem_id, target_term_sem_id}` records what happened when *this* program was lowered.

**One identity decision deferred on purpose, and named so it is not discovered.** `add(const 2, const 3)` has `inputs = {}`, so the first witness does not decide **parameterized** lowering (`program_sem_id → target term with input ports`, inputs arriving at execution, `target_term_sem_id` a function of the program alone) versus **instantiated** lowering (`program_sem_id + canonical_inputs → closed target term`, where the identity must say so). Both are coherent; they are different systems. That decision comes **before** the `input` op, not during it — an unstated variable inside `target_term_sem_id` is precisely the hidden-identity bug class round 16 exists to prevent.

## Round 25b — the source language reaches the governed runtime

**138. The refinement is witnessed, and the chain that carries it does not collapse anywhere.**

```
add(const 2, const 3)        inputs = {}
       │  lowering_sem_id            ← re-lowered independently and compared
       ▼
one canonical ic32 term  ──▶ target_term_sem_id     (kernel AND ic32_canon agree)
       │  NATIVE ic32, launched by ObservedExecutionHost from a catalog entry
       ▼
L0(L1(A(N0,A(N0,A(N0,A(N0,A(N0,N1)))))))  ──▶ target_nf_sem_id
       │  decode_sem_id
       ▼
{status:"value", value:5}  ──▶ target_outcome_sem_id
source evaluator ─────────▶ {status:"value", value:5} ──▶ source_outcome_sem_id

                            EQUAL
```

`lowering_check.mjs` **9/9**. Six identities, six distinct values, asserted so — collapsing any pair turns a refinement statement into a **renaming**, which is the failure the chain exists to avoid.

**139. Three relations, three obligations, because they fail independently.** A lowering can be perfect while the decoder misreads the normal form; a decoder can be perfect while lowering emitted the wrong term; and the runtime can execute a correct term incorrectly. `law:derivation.canonical-lowering@1` and `law:derivation.target-decoding@1` exist to make `law:derivation.lowering-refinement@1` **diagnosable** — a bare equality failure cannot say which of three broke. All three were registered **OPEN and unbuilt** in the previous section before any of them was written, which is the `film_identity_forward_declaration` discipline: a decision made in advance is inherited rather than improvised. *(Both `@1`s were **superseded** at B1.2.1 — canonical-lowering by `@2`, lowering-refinement by `@2`; this line is history and stands as written.)*

**140. The lowering gets no film, and that is a ruling.** A film is evidence for a **transition system**; lowering is a relation `DeriveProgram → TargetTerm`. Filming it would invent a sequence of internal compiler steps and make implementation strategy semantic — the mistake the read-order ruling refused when it kept access order out of the footprint. The instrument is **re-lowering**: lower again, independently, compare `target_term_sem_id`. `add(3,2)` reaches a different one, so the check is not vacuous.

`lowering_id` also split in two before either was written: `lowering_sem_id` identifies the **relation**, and a `LoweringReceipt {program_sem_id, lowering_sem_id, target_term_sem_id}` records the **application**. One id must not silently answer both "which lowering semantics is this?" and "what did lowering do here?".

**141. The decoder reads the canonical SIGNATURE, not a readback.** So it reads the same bytes the 48/48 bridge has agreed on since round 12, and cannot be misled by a binder name — which is exactly how round 23's first film emitter went wrong. §5 compaction is irreversible, so a compacted signature is **refused** rather than guessed at: `decode-signature-compacted`. That bounds the decodable numerals, and the bound is stated rather than discovered.

**142. THE GAP, and it is measured at the fixture the refinement runs on.** The native execution leg is evidenced by **observation** — the host hashed a catalogued binary and ran it — and **not by a film**. Every lowered addition carries a dup cell by construction, because Church addition uses its function argument twice and ic32's net is linear, and `ic32_film` v0.1.0 is the dup-free one-step fragment. `native-film-absent-by-refusal` asserts the emitter's own `film-dup-cell-present` on this exact term rather than describing the gap in prose. So the law states **two grades of evidence for the execution leg** and claims only the first:

```
OBSERVED         the host hashed a catalogued binary and then ran it
FILM-EVIDENCED   the kernel independently replayed the transition sequence
```

An execution the host observed and an execution the kernel replayed are different claims, and this round is the first place where saying so out loud costs something. Closing it is DUP-LAM · DUP-SUP= · DUP-SUP! · DUP-ERA · DUP-VAR · DUP-APP, the `d:` and `v:` loci, and multi-frame films — **concretely scoped now**, rather than named in the abstract.

**143. And the inputs model stays undecided, on purpose, with `input` refused by name.** `target_term_sem_id` is a function of the program **alone** under parameterized lowering and of the program **and its inputs** under instantiated lowering. Both are coherent; they are different systems. `lower({op:"input"})` returns `lower-inputs-undecided`, `INPUTS_MODEL.decided` is `false` and the grid checks it, because deciding this while implementing `input` is precisely how an unstated variable gets inside an identity — the bug class round 16 exists to prevent. Five out-of-fragment refusals are named and checked: `lower-inputs-undecided`, `lower-reads-undecided`, `lower-unsupported-op`, `lower-non-integer-constant`, `lower-negative`.

**144. Gate.** grid **v1.27.0** — 71 entries / 363 citations (transcribed at a moment; the gate derives it) · `derive_protocol.mjs` 0.10.0 · `lowering.mjs` **0.1.0** · negative battery **159/159** with nine new forgeries · bridge 48/48 · native semantic film 14/14 · **lowering refinement 9/9** · derive 45/45 · realm 20/20 · nine paired probes · harness 9/9 · runner 3/3. `scheduler_certificate.json` byte-identical — **twenty-first consecutive round**, and this is the one where that number finally means something beyond hygiene: a source program was compiled, executed on a different runtime in a different language, decoded, and found to agree — and the calculus underneath did not move by a byte.

**What the ladder looks like from here.** Rounds 15–25 were the supplier ladder: label, name, action, oracle. Rounds 12–24 were the evidence ladder: canonical bytes, then a transition, then who ran it. This round is the first that is neither — it is the two ladders meeting, and the thing they were both for. **Next**, in the order the gap now dictates: the six DUP-* rules and the `d:`/`v:` loci in `ic32_film`, then multi-frame films, which upgrades this same witness from observed to film-evidenced without changing the fixture; then the parameterized-vs-instantiated ruling; then `input`.

## Round 26 — an instanceof guard is satisfied by a subclass, and the film gap was mis-stated

**145. P-5, and it is the P-4 lesson one object later.** v0.10.0 built its own semantic registry from data and, one constructor argument on, still **accepted** a ready-made `ObservedExecutionHost` behind `host instanceof ObservedExecutionHost`. A two-method subclass passes it:

```js
class EvilHost extends ObservedExecutionHost {
  async run() { throw new Error("must not execute"); }
  observationOf() { return { implementation_family_id: "impl-c-fake-v1", … }; }
}
```

Acceptance returned `ok / validated / fresh_at_check` with `implementation_provenance: "observed"`, `implementation_id: "impl-c-fake-v1"`, `executable_artifact_id: "fake-artifact"`. **Nothing executed** — `run` throws if it is called. The catalog, the digest, hash-then-launch and the observation table were all still correct and all still unconsulted, because **the object that was asked was not the object that holds them.**

```
@1 the implementation LABEL          @4 the SEMANTIC ORACLE at acceptance
@2 the registration NAME             @5 the EXECUTION-AUTHORITY OBJECT itself
@3 the ACTION beside the evidence
```

**146. And the repair is not a tighter predicate.** **P-5b**: `Object.getPrototypeOf(host) === ObservedExecutionHost.prototype` *would* exclude the subclass — and admits a Proxy over a genuine host that answers `observationOf` however it likes. `instanceof` asks what a thing is **descended from**; the question is **who built it**. Both authorities take an executor **catalog**, which is data, and construct the host themselves against their module's own class binding. `DerivationAuthority.length` is 1: reader is the only required argument, and the other two are the DATA the oracles are built from.

**147. The grid contradicted itself in one file and the checker did not notice.** `lowering_spike.status` still read `"DECLARED, not built."` while three lowering laws above it in the same registry were `PROPERTY-TESTED`. That is the round-21 prose-versus-record class surviving the round that built the thing, and `grid_check` refuses it now — including the requirement that `execution_grade` and `film_grade` be carried **separately**.

**148. Then the film gap turned out to be mis-stated, and measuring it was the whole round.** Round 25 recorded the native execution leg as **OBSERVED, not FILM-EVIDENCED**, on the strength of `ic32_film` refusing the lowered term with `film-dup-cell-present`. Before writing the six DUP rules, the kernel's **own** film for that exact term was measured:

```
6 frames, every one APP-LAM, all at TREE loci
t:fun · t: · t:bod.bod.fun · t:bod.bod · t:bod.bod.arg.arg.fun · t:bod.bod.arg.arg
```

**Not one dup rule ever fires.** The lowered term is full of `!&L{…}` dups — Church addition duplicates its function argument and ic32's net is linear — and under the leftmost-tree-app strategy the residual dups are simply **dead** by the end. So v0.1.0's refusal was the right refusal for the wrong reason: **the blocker was never their presence, it was firing them.** The precondition moved from PRESENCE to ENABLEDNESS, which still has to be computed — the emitter classifies every live dup cell against `dupRule`'s own table to decide quiescence honestly — and `film-dup-rule-enabled` names where it actually stops.

`ic32_film` **0.2.0** emits multi-frame films. The C side reproduces the kernel's six loci exactly, reaches the same `final_sem_id 37800fc6…`, and `replaySemFilm` accepts the whole chain on `FloatRt` **and** `DescFloatRt`. `law:derivation.lowering-refinement@1` goes **OBSERVED → FILM-EVIDENCED** for the first witness, without changing the fixture. *(`lowering-refinement@1` was **superseded** at B1.2.1 by `@2`, which corrects a six-versus-seven identity enumeration and not this grade; history, unchanged.)*

**149. And one check was deleted for being accidentally true.** v0.1.0 asserted the readback fired **zero** interactions. On a one-step dup-free fixture, resolving the state costs nothing at all — so a machine counter that never moved looked like a verified property. It is not one: ic32's `interactions` is **not plane-classified**, it counts every `fire()`, `app_sup` and APP-LAM alike, while the kernel's claim is about **INTERACT-plane** rules. On the lowered term it fires **four**, resolving residual projections the kernel's reference readback resolves by chasing without counting — and the states agree perfectly. The counter was never the claim. Pool-quiescence is what is asserted now, re-checked at the terminal rather than inherited from the loop exit, and the count is **reported**.

This is the sixth time an instrument has been found measuring something adjacent to what it claimed, and the first time the instrument was one this record wrote three sections earlier.

**150. Two other stale predicates, same day.** The v0.1.0 checks `film-dup-cell-present` and `film-not-normal-form-after-one-step` were both scoped to a fixture rather than to a property. `step_at` also refused any path through a substituted variable — correct for one frame, and wrong from the second onward, because after an APP-LAM every path below runs through one. It chases at each level now; the equivalence between the kernel's functional spine rebuild and this in-place slot write is **not asserted**, it is checked by the post-state the kernel recomputes on replay.

**151. Gate.** grid **v1.28.0** — 72 entries / 365 citations (transcribed; the gate derives it) · `derive_protocol.mjs` **0.11.0** · `ic32_film.c` **0.2.0** · negative battery **168/168** with fifteen new forgeries · bridge 48/48 · native semantic film **16/16** · lowering refinement **9/9, film-evidenced** · derive 45/45 · realm 20/20 · **ten** paired probes · harness 9/9 · runner 3/3. `scheduler_certificate.json` byte-identical — twenty-second consecutive round.

**The seam list, eleven long.** …the artifact observed vs the mechanism invoked · re-derivation vs the oracle it re-derives against · and now **an object's lineage vs its provenance**.

**What the measurement changed about the plan.** The next round was scoped as "six DUP rules, the `d:`/`v:` loci, multi-frame films" — three items, of which only the third was needed for the theorem in hand. Measuring first cost one afternoon and saved a round. **Next**: the parameterized-versus-instantiated inputs ruling, which must be settled before the `input` op; then a fixture where a DUP rule genuinely fires, which is what the six rules and the `d:`/`v:` loci are actually for; then `sub`/`mul` and the first named primitive.

## Round 27, pass A — sever before validating, not after

**152. P-6, and it is the first rung that is not an object at all.** Round 26 finished turning every authority-bearing OBJECT into constructor DATA. It then validated that data **while the caller still owned it**, and copied it afterwards. A getter is read as many times as it is written, and the reads need not agree.

```js
const entry = {
  kind: "node-worker",
  get entrypoint() { reads++; return reads <= 3 ? honestWorker : maliciousWorker; },
  artifact_closure: [honestWorker, protocol, host],
};
```

The old constructor read `entrypoint` **four** times — `typeof`, `isAbsolute`, the entrypoint-inside-closure check, and then the frozen internal entry. The first three see the honest worker, so every validation passes *including the one round 24 added precisely to stop an entrypoint escaping its own hashed closure*. The fourth read is what gets stored:

```
internal entrypoint   /tmp/…_evil_worker.mjs      ← not in the closure
artifact_closure      derive_worker.mjs · derive_protocol.mjs · observed_execution_host.mjs
```

The un-hashed worker really runs, and acceptance reports `implementation_provenance: "observed"` against the digest of the **honest** closure. So P-3 came back wearing data:

```
P-3   validate artifact X          execute caller action Y
P-6   validate data describing X   copy "the same" data later   execute Y
```

**153. P-6b is the same disease on the other authority surface, and its milder outcome is not a defence.** `bind` computed `programSemId(ast)` and then `canonicalBytes(ast)` — two reads of caller-owned state — so the registry ended up **keyed by `const(5)`'s identity and holding `const(999)`**. It fails closed: `verify()` recomputes the id from what was stored and refuses with `program-id-mismatch`. But `bind()` reached the state its own comment calls impossible, `authorize()` will issue a request against that id in the meantime, and **a second mechanism catching the first is not the first working.** Frozen for that reason.

**154. The rule, and it is meant to end the ladder rather than extend it.**

> **Every untrusted structure that becomes authority state is canonicalised into an OWNED SNAPSHOT exactly once; validation, identity computation and storage then operate only on that snapshot. No unowned mutable object is consulted twice across a trust decision.**

Not getter detection, not banning Proxies, not another predicate. Snapshot once, then do everything against the snapshot. Both surfaces now read their getter **exactly once**, asserted as a count. The executor catalog is canonical **plain data** and a `Map` is refused — this is a boundary whose whole thesis is that capabilities are not data, and admitting richer JS object forms at it buys nothing. A catalog entry carrying a function is now refused by `canonicalBytes` *before any field is examined*, which is earlier than the schema check that used to catch it.

**155. Six rungs, and what the sixth one says about the other five.**

```
@1 the implementation LABEL          @4 the SEMANTIC ORACLE at acceptance
@2 the registration NAME             @5 the AUTHORITY-BEARING OBJECT
@3 the ACTION beside the evidence    @6 MUTABLE DATA READ TWICE
```

`canonicalBytes` has refused a capability since v0.1.0. What was never said is that **reading through it twice reintroduces one** — the second read *is* the capability. Every earlier rung was a thing a caller handed over; this one is a thing a caller kept.

**156. Gate.** grid **v1.29.0** — 73 entries / 366 citations · `derive_protocol.mjs` **0.12.0** · `observed_execution_host.mjs` **0.2.0** · negative battery **174/174** with six new forgeries · bridge 48/48 · native semantic film 16/16 · lowering refinement 9/9 film-evidenced · derive 45/45 · realm 20/20 · **eleven** paired probes · harness 9/9 · runner 3/3. `scheduler_certificate.json` byte-identical — twenty-third consecutive round.

**The seam list, twelve long.** …an object's lineage vs its provenance · and now **a value read once vs a value read twice**.

**Pass B is deliberately not in this round.** The inputs decision record and the `church_exp_2_2` film are the next work and they are separate fronts; mixing an authority-boundary closure with a language-architecture ruling is how a round stops being falsifiable as one thing.

## Round 27, pass A.1 — authenticated as one value, used as another

**157. P-7, found by GPT against the round-27A pack, and reproduced here before anything was built against it.** Round 27A's law is correct and its reach was the constructor. Every place where untrusted structure *became* authority state took one snapshot; method **arguments** kept the older shape — authenticate the caller's object, then go on reading the caller's object.

```
execute(req)
  wasIssued(req)                     → hashes ONE read of every field → PASSES
  req.expected_implementation_id     → read again
  { message: req }                   → read again by the host's canonicalBytes,
                                       and again by the worker's structured clone
```

Three reads after the one that authenticated. So a request whose `program_sem_id` answers `const(5)` to the first read and `const(999)` to every read after it is **issued as one program and executed as another**:

```
authority issued    request R → const(5)     psem-82eee05e…
authority executed             const(999)    psem-3b198d80…
native worker returned         999
```

Both programs are genuinely in the authority's own registry, so nothing is malformed, no identity is forged, nothing fails closed. Then acceptance, handed a *fresh* time-varying copy of the same request:

```
wasIssued      sees the issued const(5) bytes       → PASS
re-derivation  now sees const(999), re-derives 999  → AGREES
provenance     the execution really was authority-driven → observed
freshness                                            → PASS

{ ok: true, validated: true, fresh_at_check: true,
  implementation_provenance: "observed", implementation_id: "impl-js-derive-…" }
```

**The same 999 result paired with the FROZEN issued request is refused as `result-program-mismatch`.** That is what makes this a forgery rather than fail-closed hygiene that happens to hold: the entire difference is the caller's retained ownership. Frozen as P-7 in `probe_reread_v13_repro.mjs`, paired and gating.

**158. The repair is not a fresher hash, and the issuance table was the tell.** Hashing again would authenticate a *second* read and leave a third. `#issued` stored `request_id → request_sem_id`, which can answer *"were these bytes issued?"* and cannot answer *"what did I issue?"* — so every method that needed the second question had **no choice** but to re-read the caller. It now stores the request itself, `wasIssued` returns it, and `execute`/`accept` read that.

GPT preferred the stronger form: `execute(request_id)` / `accept(request_id, result)`, operating only on the authority's copy. Taken the weaker-looking option deliberately, and not for ergonomics — **an id is a strictly weaker credential than the bytes.** Knowing the whole request implies knowing its id; the converse is false. Keeping `(req, res)` keeps full-bytes authentication *and* gets owned exercise; `execute(request_id)` would make the request_id a bearer token. One to argue if GPT sees it differently. **[Ruled in 27A.2, item 168: the API is right and this justification is not. Possession of the request is a stronger CONTENT WITNESS, not stronger authorization.]**

**159. The result side was closed in the same round, one argument to the right.** `res` was live caller-owned input consulted by six checks in sequence — schema, footprint containment, re-derivation, trace conformance, the provenance lookup, freshness. No witness was written for it first. Seven rungs have each been found in the parameter beside the one just repaired, and waiting for the eighth to be demonstrated would be pretending not to know where it is. `authorize`'s `intent` and `options` were snapshotted at entry for the same reason.

**160. The law, stated so that it covers arguments and not only constructor data.**

> **Every authority operation consumes either an authority-owned object or one canonical snapshot made at entry. No trust decision authenticates one read of external state and exercises authority using another.**

`law:derivation.entry-snapshot@1`. Mechanically: one exported `ownCanonical()` called at the top of `authorize`, `wasIssued`, `execute`, `accept`, `observationOf` and `ProgramRegistry.bind`. It is a *function* rather than a discipline because v0.12.0 proved the discipline's failure mode — the rule was written down and applied exactly where it had been written down.

**161. And the enforcement is an enumeration, not three more witnesses.** `derive_realm_battery.mjs` now hands every entrypoint a structurally identical argument whose every field counts its own reads, and fails if any count exceeds the one-read-per-field floor:

```
authorize/intent 7/7 · authorize/options 1/1 · wasIssued/req 11/11 · execute/req 11/11
accept/req 11/11 · accept/res 18/18 · observationOf/req 11/11 · observationOf/res 18/18
bindProgram/ast 2/2
```

Reintroducing the defect in `execute` alone moves that to **`execute/req 33/11`** and the case names the offender. A method added later with a live argument fails here without anyone remembering to come back. *The first version of this check scored `accept/res 0/0` — the fixture under-granted, `run.result` was `undefined`, and the res-side probes passed by measuring nothing. It now throws if the fixture does not execute and accept.*

**162. Two instruments were reporting without measuring, and this round found both.**

- **`derive_battery.mjs`'s `issuance-binds-the-whole-request` had been calling the deleted three-argument `accept(reg, req, res)` since v0.10.0.** `reg` landed in the `req` slot, `reg.request_id` was `undefined`, and the issuance table's miss on `undefined` produced the expected string `grant-not-issued-by-this-authority` **by accident**. It asserted that string for eighteen rounds and never once exercised the sentence it printed. Snapshot-at-entry is what surfaced it: a `ProgramRegistry` is not canonical data, so the argument now fails loudly instead of quietly agreeing. Fixed, and it still passes — the *behaviour* was always right; only the instrument was wrong.
- **`derive_realm_battery.mjs` was printing a hand-typed "Four rungs" against a six-rung mechanism.** Two rounds stale. There is now one machine-readable `SUPPLIER_LADDER` and every live surface derives its count and wording from it. The frozen probes keep their own era's wording **on purpose** — each records the ladder as it stood when its witness was cut, and rewriting that would be falsifying a dated record.

**163. And one that was invisible rather than wrong.** `observed_execution_host.mjs` separated artifact-closure paths with a **raw NUL byte in the source**. `file(1)` classified the module as `data`; ugrep, and every other text tool, skipped it in silence. *A grep over that file returned nothing and read like an answer.* Now the six-character `\u0000` escape — identical string, visible module. Same species as the two above: an instrument that reports without measuring, except here the instrument was `grep`.

**163b. P-7c — the same defect in the host, found here rather than reported.** GPT's list stopped at the authority. `ObservedExecutionHost.run()` canonicalised `invocation` for the observation key and then handed the **same live object** to the transport:

```
inputCanonical = canonicalBytes(invocation)   ← read 1: the KEY
runNodeWorker(entry, invocation)              ← read 2: what RUNS
```

An invocation honest on read 1 and hostile on read 2 is therefore keyed under one request and executed as another, and the table ends up holding:

```
observation under the HONEST request bytes    PRESENT
observation under the bytes that actually ran ABSENT
```

That is **worse than a forged observation being unfindable**: it is a true-looking observation for an execution that did not happen, in the table round 23 built so that relabelling would *move* the key. Unreachable through `DerivationAuthority.execute`, whose invocation is assembled from owned parts — but the host is exported, `FilmAuthority` and `lowering_check` drive it directly, and it is the only writer of the observation table. **The obligation belongs to the entrypoint, not to its politest caller.** `run()` now launches the snapshot it keyed. Host 0.2.0 → **0.3.0**.

**164. Seven rungs, and @6 and @7 are one rule at two moments.**

```
@1 the implementation LABEL          @5 the AUTHORITY-BEARING OBJECT
@2 the registration NAME             @6 MUTABLE DATA READ TWICE
@3 the ACTION beside the evidence    @7 MUTABLE DATA AUTHENTICATED ONCE
@4 the SEMANTIC ORACLE at acceptance
```

```
@6   validate external X     → read X again → store X'
@7   authenticate external X → exercise authority using X'
```

The round-27A law *predicted* @7. It had simply not been applied to every authority entrypoint.

**165. Gate.** grid **v1.30.0** — 74 entries / 367 citations · `derive_protocol.mjs` **0.13.0** · `observed_execution_host.mjs` **0.3.0** · negative battery **182/182** with eight new forgeries and three repointed off dead source text · bridge 48/48 · native semantic film 16/16 · lowering refinement 9/9 film-evidenced · derive **45/45** · realm **22/22** · **twelve** paired probes (the newest is 3/3 frozen, 6/6 live) · harness 9/9 · runner 3/3. `scheduler_certificate.json` byte-identical — **twenty-fourth** consecutive round.

**166. The posture changes after this, and that is GPT's call taken as given.** Stop asking *"what is P-next?"* as the main activity; let actual counterexamples reopen the line. The bulk of the work becomes what TRVM needs — more causal computation, native film coverage, inputs, primitives, WRL/Forge integration, real programs.

**167. Pass B, ruled and not to be re-litigated.**

- **`instantiation_sem_id` gets its own identity and its own law.** Lowering and instantiation compose but answer different questions, and merging them makes a target failure ambiguous between *translated wrong* and *inputs wired wrong*. The chain: `program_sem_id →(lowering_sem_id)→ target_template_sem_id →(instantiation_sem_id + inputs_sem_id)→ target_term_sem_id →(native film)→ target_nf_sem_id →(decode_sem_id)→ target_outcome_sem_id`, with `source_outcome_sem_id == target_outcome_sem_id`.
- **`instantiation_sem_id` identifies the RELATION, not the invocation.** It commits port namespace/version, the source-name→port rule, missing/extra-input semantics, canonical input embedding, substitution semantics, refusal vocabulary, conformance vectors. It does **not** contain `x=5` — that is `inputs_sem_id`. An `InstantiationReceipt {target_template_sem_id, instantiation_sem_id, inputs_sem_id, target_term_sem_id}` verified by independent re-instantiation. **No film**: instantiation is a deterministic relation, not a transition system.
- **I-4 is the inverse of round 16.** Round 16: identity depended on a spelling that should not matter. I-4's danger: identity accidentally depends on an *allocation* that should not matter, while losing the *source name* that does. The quotient — internal target variable names are non-semantic/alpha-equivalent; source input keys are semantic. The port is `input-port("x")` at the canonical target-AST layer, before textual/ic32 variable allocation, so `_impl17` and `q93` reach the same `target_template_sem_id`. **Do not Unicode-normalize source input strings** — if the frozen core distinguishes two code-point sequences, the port identity must preserve that exact distinction; normalizing is itself a language-semantic change.
- **Three falsifiers, not one:** different internal allocations + same source name → **same** `target_template_sem_id`; same allocation + different source names → **different**; x/y port binding swapped at instantiation → the term/outcome changes or refuses, and **must never validate under the correct instantiation receipt**.
- **Fixture A = `church_exp_2_2`** (21 frames: DUP-LAM, both SUP cases, DUP-VAR, DUP-APP, APP-SUP, APP-LAM, all `t:`/`d:`/`v:` locus families). **Fixture B = a purpose-built DUP-ERA witness**, because `church_exp_2_2` does not exercise it and six rules claimed from one large term that happened to terminate is coverage by hope.

## Round 27, pass A.2 — four cleanups GPT asked for, one of which was a real bug

None of these is a forgery. GPT reviewed 27A.1, could not produce another P-style false verdict
against v0.13, and ruled four changes before Pass B. All four are done; the round is deliberately
small.

**168. The credential claim in item 158 was wrong, and the correction is worth more than the claim.**
I argued that keeping `execute(req)` was right because "an id is a strictly weaker credential than
the bytes". GPT's ruling: **not necessarily.** Unless TRVM explicitly promises the request is secret,
possession of the request is not authentication of the caller either — a request that is logged,
transmitted or cached is bearer data too. The three things were being run together:

```
request_id            locator / identity
whole request bytes   CONTENT WITNESS
execution capability  AUTHORIZATION
```

The full request *is* a strictly stronger **content witness** — it lets the authority establish "you
are talking about exactly the request I issued" rather than merely naming one. Neither should quietly
become the security capability. **If TRVM ever needs *only party X may cause this issued request to
execute*, that must be an explicit capability/delegation rule and not an emergent consequence of who
happens to know a `request_id`.** The API is unchanged and correct; the justification for it is now
the accurate one.

**169. `bindProgram` erased the provenance of an earlier genuine execution.** GPT's find, reproduced
here:

```
execute(A) · accept                     → implementation_provenance "observed"
bindProgram(B)                            an unrelated program
accept(same request, same result)       → implementation-provenance-unavailable
observationOf(same request, same result)→ null
```

Acceptance asked the observation table about a past execution by **rebuilding** the invocation out of
`this.#registry.image()` — that is, out of state as it stands *now*. `bindProgram()` is an explicit,
legitimate authority operation and it grows that image, so the rebuilt invocation stopped matching
the one the host had keyed. It fails closed and forges nothing. It is still wrong:

> **Historical fact is not a function of current configuration.**

`execute()` now records the canonical invocation bytes **the host itself keyed** (`run()` returns
`input_canonical`), and acceptance looks those up. A **list** rather than one entry, because the same
request run before and after a bind is two genuinely different invocations and both happened — and
observations across them are **merged, not first-hit**, for the round-24 reason: reporting one launch
as though it were the only one overclaims exactly the way `executor_session_id` singular did.

**170. The exported validators were a boundary hazard, and the measurement is the argument.** GPT
instrumented `checkRequest` with a Proxy around an otherwise valid request. One call:

```
ownKeys 2 · getOwnPropertyDescriptor 10 · getPrototypeOf 1 · get 13 · has 1
```

Reproduced exactly. So "a pure function over data the caller already owns" is the second half of a
sentence whose first half was a **precondition nothing enforced**. No v0.14 forgery follows, because
`DerivationAuthority` passes only `issued`/`ownRes`/`ownIntent` — but a second authority built on
these exports would recreate P-7 without writing a line of new trust logic. So the implementations
are `checkRequestOwned` / `checkIntentOwned` / `checkResultOwned` / `deriveLocallyOwned` /
`validateForeignResultOwned`, where the suffix is a precondition; the exported names snapshot once
and delegate; the authority keeps calling the `Owned` forms, because paying for a second
canonicalisation of something it just canonicalised is ceremony rather than safety. Public
`checkRequest` now touches the same surface as one `ownCanonical` traversal. **GPT explicitly
declined to number this as P-8**, and that is right: it is a hazard the now-correct law predicts, not
a false verdict.

**171. The read-count enumeration is a regression detector and NOT a terminating proof.** Item 161
oversold it. It counts `get`, and

```js
const x = { get a() { reads++; return 1; } };
Object.keys(x); Object.keys(x);      // reads === 0, and the object was touched twice
```

A Proxy can put code behind `ownKeys`, `getOwnPropertyDescriptor`, `getPrototypeOf`, `has` and `get`;
a field-read counter sees only the last. So case 20 stays, described accurately, and case 20b measures
the rest: twelve entrypoints — including the reusable exports — each handed a **recursively**
Proxy-wrapped argument, each required to touch the external object **exactly as much as one
`ownCanonical()` traversal and never again** (e.g. `wasIssued/req gOPD:11 get:11 getPrototypeOf:6
ownKeys:6`). The invariant being defended is architectural, not numeric: *after `ownCanonical()`
returns, no code below it holds a reference to the external value.* The traps are the detector.

**172. And the sharper statement about what canonicalisation does and does not prevent.** This module
says in several places that `canonicalBytes` refuses a capability. True of a capability as a **value**
— `{evil: () => …}` dies. Not true that canonicalisation never runs caller code: reading
`{get x(){…}}` executes a function, and a Proxy runs traps while being serialised. The accurate claim:

> `ownCanonical` prevents caller-owned **behaviour from surviving** the canonicalisation boundary.

not

> canonicalisation never invokes caller behaviour.

**DECLARED OPEN.** No such behaviour participates in any authority decision, because every decision
happens on the captured value afterwards — that is the invariant, and 20b detects regressions in it.
But *no hostile same-realm code executes at ingestion* is a **stronger property no API whose boundary
is an arbitrary JavaScript object can have.** Reaching it needs

```
canonical serialized text → parser owned by the authority → canonical data
```

because a primitive string has no getters and no traps. That is the future serialized-wire boundary,
it is not built, and it is named here rather than discovered during Pass B.

**173. One review-pack nit.** `lowering_check.mjs`'s skip text said `make gov-film builds both`. It
does not — `gov-film` builds the film binary and `gov-lower` builds both, which is why GPT's first
rebuild left `lowering_check` correctly refusing. Fixed.

**174. Gate.** grid **v1.31.0** — 74 entries / 368 citations · `derive_protocol.mjs` **0.14.0** ·
`observed_execution_host.mjs` **0.4.0** · negative battery **188/188** with six new forgeries and two
repointed onto the `Owned` names · bridge 48/48 · native film 16/16 · lowering refinement 9/9
film-evidenced · derive 45/45 · realm **23/23** · twelve paired probes · harness 9/9 · runner 3/3.
`scheduler_certificate.json` byte-identical — **twenty-fifth** consecutive round.

**175. The supplier-ladder line stops being the main development activity here.** GPT's judgment, and
it is taken. The mechanism now reads:

```
external intent
      │  ownCanonical
      ▼
owned snapshot
      │
      ▼
authority-issued owned request
      │
      ├── authority-owned registry
      ├── authority-owned execution host
      ├── authority-owned World reader
      └── authority-owned observation history   ← recorded, not reconstructed
```

with results snapshotted at acceptance. No proactive P-8 hunt. **Pass B is go**, and the next
question is what interesting programs this authority can compile, execute and causally prove.

## Round 27, pass A.3 — multiplicity must preserve correlation

One repair, and it closes pass A. GPT found it against 27A.2 and declined to number it P-8, which is
the right call and worth keeping in the record: nothing false was accepted.

**176. Two sessions, two artifacts, one artifact id.** Reproduced exactly as reported:

```
run the same issued request                      S1 → artifact 0e34c127… → 5
append one comment to derive_worker.mjs
run it again                                     S2 → artifact d07dc1d9… → 5

accept →  implementation_id      impl-js-derive-…
          executable_artifact_id 0e34c127…
          executor_sessions      [S1, S2]
```

Both executions genuinely happened, both genuinely produced those request/result bytes, and the
authority drove both. Nothing is invented. What is wrong is the **shape**: it reads as *these
recorded sessions ran artifact 0e34c127…* when the evidence says *S1 ran A and S2 ran B*. The two
artifact versions could differ arbitrarily and coincide only on this request's result.

**177. And it is older than the round that surfaced it.** GPT attributed it to A.2's new merge. It is
not: both runs share ONE host key — same invocation bytes, same output — so the host's own list holds
two observations, and `observationOfCanonical` was already doing

```js
executable_artifact_id: list[0].executable_artifact_id,
executor_sessions:     list.map(…)
```

That is **round 24's own fix, half-applied.** Round 24 discovered that the key is over bytes, made
`executor_sessions` plural for exactly this reason, and left the artifact id singular over the same
plural list. A.2's authority-level merge then rewrote the identical mistake one level up — which is
its own small lesson: *two copies of a rule is how the mechanism gets duplicated and the semantics
drift*, the same finding round 24 recorded about building the launch machinery twice.

**178. The law.**

> **Multiplicity must preserve correlation. Evidence fields that vary together may not be
> independently collapsed into singular summaries.**

`law:derivation.observation-multiplicity@1`. GPT's framing is the clearest statement of it: this is
the database error of taking one column from the first row and another column from every row, then
presenting the pair as a record. Provenance is **relational** — family ↔ artifact ↔ session — not
three unrelated sets.

**179. The tuple is the unit, and there is one summariser.** `summariseObservations()` lives in the
host and is used by the host *and* by the authority merging across invocations. Observations are
grouped by the `(implementation_family_id, executable_artifact_id)` that actually co-occurred,
carrying the sessions that ran it; every singular field is **derived**, emitted only when genuinely
unique and `null` otherwise — which is what the family id has done since round 24 and what the
artifact id should have been doing beside it.

```
execution_observations: [
  { family, artifact: A, executor_sessions: [S1] },
  { family, artifact: B, executor_sessions: [S2] },
]
executable_artifact_id: null          ← not unique
executable_artifact_ids: [A, B]
executor_sessions: [S1, S2]           ← summaries, derived from the tuples
```

**180. Not a forgery, and the law says so in those words.** A `grid_check` assertion requires the
statement to keep the sentence *"not a forgery but a PROVENANCE SHAPE defect"*, and a forgery in the
negative battery rewrites it to *"a forgery of execution provenance"* and must be caught. Filing this
as a P-rung would misdescribe the severity **in the flattering direction** — it would let a shape
defect borrow the seriousness of an accepted false verdict, and this tree has spent twenty-seven
rounds making severity claims mean something.

**181. Gate.** grid **v1.32.0** — 75 entries / 369 citations · `derive_protocol.mjs` **0.15.0** ·
`observed_execution_host.mjs` **0.5.0** · negative battery **194/194** with six new forgeries · bridge
48/48 · native film 16/16 · lowering refinement 9/9 film-evidenced · derive 45/45 · realm **24/24** ·
twelve paired probes · harness 9/9 · runner 3/3. `scheduler_certificate.json` byte-identical —
**twenty-sixth** consecutive round. The multiplicity witness mutates `derive_worker.mjs` and restores
it in a `finally`, so the artifact tree is unchanged whether the case passes or throws.

**182. PASS A IS CLOSED.** GPT's judgment, taken: the assurance plane is not finished forever, but its
job is now to *support* causal language growth rather than to *be* the project. Rounds 17–27 asked
whether the machinery can truthfully say what program, what authority, what executor, what bytes,
what dependencies, what execution and what evidence are being talked about. Pass B asks what useful
language can be run through it. **No proactive P-8 hunt.** Future boundary work is driven by concrete
counterexamples.

## Round 27, pass A.4 — severity is a field, and the NUL came back

Two small corrections from GPT's A.3 review. No new mechanism.

**183. The severity invariant was checking English, and that is over-engineering of the wrong kind.**
Item 180 made `grid_check` require the exact sentence *"not a forgery but a PROVENANCE SHAPE defect"*
in the law statement. GPT's ruling: **the distinction is worth mechanising and the sentence is not the
mechanism.** Requiring a phrase makes editorial wording load-bearing — the prose cannot be improved
without the checker reading it as a change of meaning, which is the record-staleness trap approached
from the other side. Entries now carry structured metadata against a declared
`defect_class_vocabulary`:

```json
{ "defect_class": "provenance-shape",
  "accepted_false_verdict": false,
  "underlying_observations_genuine": true }
```

and the contrast is expressed in **data** rather than in one law's prose: `derivation.entry-snapshot@1`
and `derivation.owned-snapshot@1` are `authority-forgery` with `accepted_false_verdict: true`. Any
entry declaring a `defect_class` must declare a known one and must answer **both** severity questions
— a class name alone re-creates the prose problem with fewer characters.

**184. And the literal NUL came back, in the file that documents why it must not.** A.1 found a raw
`0x00` separator in `observed_execution_host.mjs`, fixed it, and wrote a comment explaining that
`file(1)` reclassifies the module as `data` and every text tool skips it in silence. **A.3's new
grouping key reintroduced the same byte in the same file, four commits later** — this session's own
error, not an inherited one. So it is checked rather than remembered: `grid_check` scans every
governance `.mjs/.js/.sh/.json/.md/.c/.h/.py` file, in the root and in `bridge/`, and fails on any
literal NUL, naming the file, offset and line.

The check caught its author on its first run. `grid_check.mjs` itself contained a NUL — in the comment
explaining the hazard, where the escape had been pasted as the byte it describes. Three occurrences in
one round, across three files, every one of them invisible to `grep`. That is the argument for the
check, made by the check.

**185. Gate.** grid **v1.33.0** — 75 entries / 370 citations · `observed_execution_host.mjs`
**0.5.1** · negative battery **198/198**, with the prose forgery replaced by four structured-severity
forgeries and one that rewrites the escape back into a raw byte · realm 24/24 · derive 45/45 · bridge
48/48 · film 16/16 · lowering 9/9 · twelve paired probes · harness 9/9 · runner 3/3.
`scheduler_certificate.json` byte-identical — **twenty-seventh** consecutive round.

**186. Pass A stays closed. B1 begins.**

## Round 27, pass B1 — the inputs model, decided and not built

The first Pass-B round. It decides an architecture and implements none of it, which is the whole
point: an unstated variable inside `target_term_sem_id` is the round-16 hidden-identity bug class,
and deciding this *while* writing `input` is how it gets in.

**187. "Parameterized versus instantiated" was a FALSE CHOICE.** The template is parameterized **and**
the executed term is necessarily closed. They are two relations, they compose, and they get two
identities:

```
program_sem_id
      │  lowering_sem_id
      ▼
target_template_sem_id        reusable, independent of invocation data
      │  instantiation_sem_id + inputs_sem_id
      ▼
target_term_sem_id            the closed executable term
      │  native semantic film
      ▼
target_nf_sem_id  ──decode_sem_id──▶  target_outcome_sem_id  ==  source_outcome_sem_id
```

**188. Why they may not be merged, which is the whole of the ruling.** A template can be *perfectly
lowered* while instantiation binds `"x"` to the port for `"y"`. Merge the relations and a target
failure becomes ambiguous between **the program was translated incorrectly** and **correctly
translated code had its inputs miswired**. Twenty-seven rounds have gone into removing exactly that
species of ambiguity; this one is cheap to keep out and expensive to retrofit.

**189. `instantiation_sem_id` identifies the RELATION, not the invocation.** It commits to the port
namespace and version, the source-name→port rule, missing- and extra-input semantics, the canonical
embedding of an input value, substitution semantics, the refusal vocabulary and the conformance
vectors. It does **not** contain `x=5` — that is `inputs_sem_id`. The moment the invocation data is
inside the relation id, every invocation is a different relation and the receipt can say nothing
general.

**190. The port is bound to the SOURCE NAME, and this is the inverse of round 16.** Port identity is
`H(namespace | canonicalBytes(source_input_name))`, taken at the canonical target-AST layer as
`{op:"input-port", source_name:N}` **before** any textual or ic32 variable allocation — so two
implementations that internally allocate `_impl17` and `q93` reach the same
`target_template_sem_id`. The quotient, stated exactly:

```
internal target variable names   NON-SEMANTIC, alpha-equivalent
source input keys               SEMANTIC
```

Round 16's bug was identity depending on **a spelling that should not matter**. The danger here is
identity depending on **an allocation that should not matter, while losing the source name that
must.** Same axis, opposite direction.

**And source input names are NOT Unicode-normalized.** If the frozen core distinguishes two code-point
sequences as different names, port identity preserves that distinction exactly. Normalizing at the
encoding layer would be a language-semantic change made where the source cannot see it — a quotient
introduced by the compiler on the language's behalf.

**191. No film for instantiation.** It is a deterministic relation, not a transition system, so its
instrument is independent **re-instantiation** against an `InstantiationReceipt {target_template_sem_id,
instantiation_sem_id, inputs_sem_id, target_term_sem_id}` — the same argument that gave lowering
re-lowering rather than a film. A film here would be evidence about the target runtime's steps, which
is a different claim about a different object.

**192. DECIDED, NOT BUILT — and the refusal can now say which.** `input` still does not lower.
`instantiate()` throws `instantiate-not-implemented`. The lowering refusal was renamed
`lower-inputs-undecided` → **`lower-input-not-implemented`**, because *"we have not ruled"* and *"we
have ruled and not written it"* are different states, and a refusal that conflates them is a stale
instrument with a delay fuse. The three port falsifiers are **declared as data** —
`INSTANTIATION_FALSIFIERS`, I-4a allocation-invariance, I-4b source-name-sensitivity, I-4c
binding-has-force — with `status: "DECLARED"` and none written. B2 writes them. Declared as data and
not prose because a hand-maintained list drifts from its suite, which this tree has now watched happen
to a law count, a case count and a rung count.

**193. `LOWERING_SEM_ID` moved, and that is the point.** `LOWERING_SPEC` carries `inputs_model`, so
deciding the model changes the lowering relation and therefore its identity. An id that survived this
ruling unchanged would be claiming the decision was not part of the relation. The refinement receipt
is re-cut rather than re-pointed, and the 9/9 witness is unchanged and still FILM-EVIDENCED.

**194. Two records were about to contradict the code, and one already did.**
`lowering_spike.status` still read *"inputs model UNDECIDED"* — the same prose-versus-record drift its
own `record_correction` field is about, in the same file. `grid_check` now binds
`lowering_spike.inputs_model.decided` to `INPUTS_MODEL.decided` in the source **in both directions**,
and refuses a status string that says UNDECIDED while the code says otherwise.

And a negative-battery case was **deleted rather than repointed**: `inputs-silently-lowered` flipped
`decided: false → true` and asserted *"must record the inputs model as UNDECIDED"*. B1 made its
perturbation the live state, so it went VACUOUS — changed no artifact, tested nothing. Its premise is
what the round reversed, so `inputs-model-reverted` guards the new state in the new direction and the
old case is gone with a comment saying why. **A falsifier outliving its premise is a falsifier that
has stopped measuring**, which is the species this battery exists to catch.

**195. Gate.** grid **v1.34.0** — 76 entries / 371 citations · `lowering.mjs` **0.2.0** · negative
battery **207/207** with ten new B1 forgeries and one deleted · lowering refinement **9/9, still
FILM-EVIDENCED** · derive 45/45 · realm 24/24 · bridge 48/48 · film 16/16 · twelve paired probes ·
harness 9/9 · runner 3/3. `scheduler_certificate.json` byte-identical — **twenty-eighth** consecutive
round.

**196. `law:derivation.instantiation-identity@1` — SUPERSEDED at B1.1 by @2, kept as history —
is PROPERTY-TESTED FOR THE DECISION and claims nothing about behaviour.** *(@1 shipped an
overbound identity projection and an extra-input rule that contradicted the source; see item 198.)* Its evidence says so, and a `grid_check` assertion requires it to keep
saying so. This is the one place a frozen architecture can quietly start reading as a working
feature.

**197. Next: B2, the three port witnesses.** Then `church_exp_2_2` and the dedicated DUP-ERA fixture.

## Round 27, pass B1.1 — the preflight GPT asked for, and B1 was wrong twice

GPT approved B1's architecture and refused to let B2 start on it. Two findings, both real, both in
work this session shipped one commit earlier.

**198. THE SEMANTIC IDS WERE OVERBOUND TO LIFECYCLE, which is round 16 inside the compiler
specification.** `LOWERING_SEM_ID` hashed the whole `LOWERING_SPEC`, lifecycle fields included.
Measured, and GPT's number reproduced to the digit:

```
implemented: false → true     lsem-5673108765b4…  →  lsem-63f98923ed13…
decided_at reworded           lsem-5673108765b4…  →  lsem-1e69c64c5c4a…
conformance-status reworded   isem-c6b793933e30…  →  isem-60b7eb6d2d0a…
```

Not one rule changed in any of those. **B2 becoming BUILT would have re-identified a relation B1
froze.** The split:

```
SEMANTICS   what the relation DOES — changing it changes emitted terms
            or accepted inputs.                             HASHED
STATUS      rounds, evidence grades, whether code exists.   NOT HASHED
```

under new `TRVM-*-SEM-v2` tags. And the dual property is asserted, because an id that stopped tracking
semantics would be the same defect facing the other way: dropping `add` from `lowered_ops` moves the
**lowering** id; changing extra-input semantics or making the source name non-semantic moves the
**instantiation** id and *not* lowering's. That is the two-relation ruling **measured** rather than
asserted.

**DECLARED OPEN, because the split is real and not total.** The semantic records are still English:
rewording normative prose like `dup_label_policy` or `substitution` still moves an id. That is
correct-but-brittle rather than solved, and closing it needs a formal target-AST grammar that is not
written. What has been removed is the class GPT measured — lifecycle and evidence status can no longer
re-identify a relation.

The B1 ids are kept as `OVERBOUND_TRANSITIONAL_SEM_IDS`, and `derivation.instantiation-identity@1`
stays on the record as non-canonical history with a `revision_note` saying what it got wrong. A record
that quietly replaced them would be doing the thing this correction is about.

**199. THE EXTRA-INPUT RULE CONTRADICTED THE SOURCE LANGUAGE, and the argument for it was false.**
B1 froze extras as `instantiate-extra-input`, justified by: accepting them would let `inputs_sem_id`
vary while `target_term_sem_id` did not, *"so the receipt would stop being a function."*

**That is simply wrong about functions.** A function may be many-to-one; `(template, {x:2})` and
`(template, {x:2, unused:999})` mapping to one term *is* a function. And the rule contradicted the
source, which was checkable in one line and was not checked:

```
evaluate({op:"input", name:"x"}, {}, {x:2, y:999})   →   2
```

The source **ignores** unused inputs. Refusing them at the target would have broken refinement **by
construction** on the first program carrying a spare input — a compiler and a language disagreeing
because the compiler invented a rule. Extras are ignored now. `inputs_sem_id` still hashes the whole
canonical record, so invocations stay distinguishable as requests; *different `inputs_sem_id` → same
`target_term_sem_id`* is not an identity defect but the correct statement that **executable semantics
do not depend on unused data**. Narrowing the source's input discipline is a source-language change
needing a new `CORE_SEM_ID`, and the instantiator may not impose it unilaterally.

**200. The refinement claim is scoped BEFORE anything is built.** `REFINEMENT_SCOPE` says it holds
over canonical, **fully bound** input environments in which instantiation succeeds. Missing inputs are
refused on both sides but at different layers under different codes — `program-input-missing` during
source *evaluation*, `instantiate-missing-input` *before a target term exists* — so refusal
preservation is a separate theorem and is **DECLARED OPEN**. Claiming it on the strength of the
positive witness would be the two-grades-of-evidence mistake round 26 made about films.

**201. I-4c now MANDATES an asymmetric fixture.** The obvious witness cannot fail:

```
add(input x, input y)   x=2 y=3   →  5      swapped  →  5     ← proves nothing
add(input x, add(input x, input y))         →  7      swapped  →  8     ← mandated
```

Both verified against the real source evaluator. `2+3 == 3+2`, so a symmetric witness is green whether
or not the binding was honoured — a test whose output cannot reveal the defect it is named for. The
fixture is recorded in the falsifier so B2 cannot quietly write the easy one.

**202. And the check I wrote to defend all this was reading its own comment.** The grid assertion for
`implemented: false` matched the *explanatory comments* about the overbinding bug — so every real
field could flip to `true` and the check still passed. Fixed with a comment-stripped `lowNoc`, the
same device `derive_protocol`'s assertions have used since v1.18. **A check reading the prose that
documents a defect, instead of the field the defect is in, is the species this file exists to catch**
— found here by the negative battery, which is what it is for.

**203. The stale headline.** `LOWERING-CHECK`'s summary still printed *"The inputs model stays
UNDECIDED and `input` is refused until it is ruled"* — green cases, green headline, and the headline
describing the world before the round that produced it. Derived from `INPUTS_MODEL` now, alongside the
refinement scope and its open item.

**204. Gate.** grid **v1.35.0** — 77 entries / 372 citations · `lowering.mjs` **0.3.0** · negative
battery **215/215** with eight new B1.1 forgeries and one repointed at the history entry · lowering
**11/11**, refinement unchanged and still FILM-EVIDENCED · derive 45/45 · realm 24/24 · bridge 48/48 ·
film 16/16 · twelve paired probes · harness 9/9 · runner 3/3. `scheduler_certificate.json`
byte-identical — **twenty-ninth** consecutive round.

**205. B2 is unblocked.** Templates for every program including input-free ones, `input-port("x")`
before allocation, `instantiate()`, the `InstantiationReceipt` verified by re-instantiation, and the
three falsifiers with I-4c asymmetric. Then `church_exp_2_2` and the DUP-ERA fixture.

## Round 27, pass B1.2 — the layer B1 presumed and did not have

GPT approved B1.1 and stopped B2 again, for a better reason than the last one.

**206. B1 froze an architecture the compiler could not express.** The ruling says a port lives at
`{op:"input-port", source_name:"x"}` *"at the canonical target-AST layer, BEFORE any textual or ic32
variable allocation."* There was no such layer. `lower()` built an ic32 **string**:

```js
return { ok: true, target_term: go(ast) };
```

So a port would have had to be a placeholder like `$input_x` — **spelling as semantics, the exact
defect the ruling forbids, reintroduced by the absence of the representation it presumes.** GPT saw
that before a line of B2 was written; it is the kind of thing that only shows up when someone asks
*where would this actually live.*

**207. `TRVM-TARGET-TEMPLATE-v1`**, minimal on purpose — exactly today's fragment:

```
Template := church(n) | add(Template, Template) | port(source_name)
```

with its own content-bound encoding identity. Lowering's codomain is now the template; `emit()` is a
separate deterministic serialization to ic32.

**208. And the reason I-4a holds is now STRUCTURAL rather than promised.** A template contains **no
binder names and no dup labels.** `emit()` invents both from the template's shape by the declared
depth-first policy. Two implementations that allocate `_impl17` and `q93` cannot differ in the
template, because *there is no field an allocation could occupy.* That is a much better answer than
asking an emitter to be well-behaved. `emit()` refuses a template still holding a port
(`emit-unbound-port`), because a template with a free port is not an executable term.

**209. THE REGRESSION THEOREM, which is why this was safe to do before B2.**

```
pre-B1.2  lower(add(2,3)).target_term   129 characters
post-B1.2 emit(template)                129 characters      BYTE-IDENTICAL
```

Introducing the compiler phase changed **neither the executable term nor its outcome** — same six-frame
film, same normal form, same value 5, refinement still FILM-EVIDENCED. Verified against the previous
commit's `lower()`, and on a nested fixture too.

**210. `LoweringReceipt` ends at the template now.** It bound `{program_sem_id, lowering_sem_id,
target_term_sem_id}` — the **pre-B1 relation**, still asserting that lowering produces the executable
term, which the two-level ruling denies. It ends at `target_template_sem_id`; the closed term's
identity belongs to the `InstantiationReceipt`.

**211. And the hashed semantics were still incomplete, which is B1.1's own defect surviving one round.**
`LOWERED_OPS` was `["const","add"]`, so **B2 adding `input` would have moved `LOWERING_SEM_ID`** —
implementing a frozen rule re-identifying the relation, precisely what B1.1 set out to make
impossible. The whole fragment including `input` is in the semantics now, with its rule frozen:

```
{op:"input", name:N}  →  {t:"port", source_name:N}     N carried through UNCHANGED
```

and `lower-input-not-implemented` moved to `LOWERING_STATUS` as an operational refusal. **Measured:
implementing the rule *and* flipping both lifecycle flags moves neither semantic id.** The B1.1
promise is finally true rather than nearly true.

**212. `consumed_inputs` is named so it cannot be erased.** Instantiation substitutes only the ports
the template declares; the inputs **supplied** and the inputs **consumed** are different sets. That is
**grant-versus-footprint from round 15, one layer down** — GPT's observation, and it is the right
frame. No `input_footprint` is emitted yet and that is named rather than implied.

**213. The file header had been contradicting its own body for a round.** It still drew
`program_sem_id → target_term_sem_id` and still said the inputs model was undecided, while the
sections below said the opposite. Fixed — a file contradicting itself is the record-staleness class
this tree does not tolerate anywhere else.

**214. Gate.** grid **v1.36.0** — 77 entries / 372 citations · `lowering.mjs` **0.4.0** · negative
battery **221/221** with six new B1.2 forgeries · lowering **12/12**, refinement unchanged and still
FILM-EVIDENCED · derive 45/45 · realm 24/24 · bridge 48/48 · film 16/16 · twelve paired probes ·
harness 9/9 · runner 3/3. `scheduler_certificate.json` byte-identical — **thirtieth** consecutive
round.

**215. B2 is now genuinely unblocked**, and it is small: delete one refusal line so `input` lowers to
`T.port(name)`, write `instantiate()` over the template, and write I-4a/I-4b/I-4c with the mandated
asymmetric fixture. The identities will not move when it lands, and that is checkable rather than
hoped for.

---

## Round 27, pass B1.2.1 — `emit()` was a hidden semantic relation

**GPT's find against the B1.2 pack, reproduced here before anything was built against it, and it
brought three more of the same species out with it.** GPT approved the target-template layer and the
minimal AST and stopped B2 for the fourth time, for the best reason yet: the round is no longer about
whether an untrusted caller can forge an execution. It is about *where compiler semantics live and
which relation identity must move when an encoding changes*.

**216. The contradiction, reproduced.** Change `TARGET_ENCODING.add` and nothing else. The executable
term's bytes change. `INSTANTIATION_SEM_ID` (`isem-bf9434fc…`), `target_template_sem_id`
(`tmpl-ebab76bb…`) and `TARGET_TEMPLATE_ENCODING_SEM_ID` (`tenc-2adf4d28…`) **all stand still** — so
the identity of the relation that *produces* those bytes did not move. `LOWERING_SEM_ID` moved instead
(`lsem-d95ee1cb…` → `lsem-39ec194a…` under my mutation; GPT reached `6e445936…` under a different
mutation of the same field, which is why the finding is the SHAPE and not the hex). B1.2 introduced
the template and left both encoding commitments pointing where they had pointed when there was no
template.

**217. Both halves were wrong, and they are one mistake facing opposite ways.**

- **UNDER-BOUND.** `INSTANTIATION_SEMANTICS` named its domain by **id** and its codomain in **prose** —
  `"TRVM-TERM-CANON-v1 / ic32 executable text, via emit()"`. The whole executable encoding reached the
  relation's identity as **eight characters inside an English sentence**. A name anyone may claim is
  not a commitment; that is the objection the primitive ruling already raised against a bare
  `componentReachability`, arriving inside the compiler.
- **OVER-BOUND, and this half is mine.** `LOWERING_SEMANTICS` still carried the entire
  `TARGET_ENCODING` — a **pre-template leftover**. Before B1.2, `lower()` produced ic32 text and the
  executable encoding genuinely *was* lowering's codomain. B1.2 moved the codomain onto the template,
  fixed the `LoweringReceipt` **one declaration below**, and left this line pointing two layers
  downstream. So an emitter change **re-identified every `LoweringReceipt` ever issued**, for a
  relation lowering does not perform.

**THE RULE, now in the law:** *a relation's identity must commit, BY CONTENT AND NOT BY NAME, to
exactly the encodings of its own domain and codomain — no more and no fewer.* Under-binding hides a
semantic dependency behind a symbol name; over-binding re-identifies a relation when something it does
not perform changes. They are the same defect and they were both present.

**218. `TARGET_EXECUTABLE_ENCODING_SEM_ID`, and emission is ruled INTO the instantiation relation.**
`xenc-` over `canonicalBytes(TARGET_ENCODING)`, named as `INSTANTIATION_SEMANTICS.codomain_encoding_sem_id`.
GPT's larger point is taken and **written down rather than left implicit**: a third relation with its
own `emission_sem_id` is the more faithful decomposition — *a correct port substitution can coexist
with an incorrect emitter* — and it is **not taken while `emit()` is neither independently reused nor
independently theorem-bearing**. The trigger for revisiting it is in the hashed record, so the boundary
stays a decision rather than an accident. That is the whole complaint of this round, one layer up.

**219. THE THREE-WAY SEPARATION, MEASURED — `emit-is-not-a-hidden-relation`.** The two-relation ruling
is worth nothing if the ids do not sort changes *between* the relations:

| mutation | `lsem` | `isem` | `tenc` |
|---|---|---|---|
| `TARGET_ENCODING.add` / `.dup_label_policy` / `.numbers` | same | **MOVED** | same |
| `op_lowering_rules.const` / `.add` | **MOVED** | same | same |
| `TARGET_TEMPLATE_ENCODING.grammar` (the shared boundary) | **MOVED** | **MOVED** | **MOVED** |

**220. Removing the leftover binding exposed a second gap: the lowering map had never been written
down.** `lowered_ops` says *which* ops lower and the template encoding says what the codomain's nodes
*are*, but **nothing in the hashed semantics said that a `const` becomes a `church` node**, or that
`add` preserves operand order. B1.1 froze the `input` rule under GPT's pressure and `const` and `add`
were left implicit — so `const(n) → church(n+1)` would have **contradicted no sentence**. New
`op_lowering_rules`. *An identity that cannot move when its map changes is the same defect as one that
moves when its map has not.*

**221. The two refusal vocabularies were CROSSED.** `TARGET_ENCODING.refusals` held four `lower-*`
**source-fragment** refusals that cannot arise while emitting; `LOWERING_SEMANTICS.refusal_semantics`
held `emit-unbound-port` and `template-malformed`, **neither reachable from `lower()`** — which emits
only zero-port templates it built itself. Once the encoding's bytes carry an identity, renaming
`lower-negative` would have moved the *executable encoding's* id without touching the encoding. Each
list now belongs to the record that owns it, and the witness **drives every name lowering claims to an
actual refusal**.

**222. `LOWERED_OPS` → `IMPLEMENTED_LOWERED_OPS`**, GPT's naming point taken. It read as the fragment
itself while sitting four lines from `LOWERING_SEMANTICS.lowered_ops` holding a **different and larger**
list, and distinguishing *specified* from *implemented* is the entire conceptual content of B1.2. The
comment above it still said `input` was absent "because the inputs model is undecided" — untrue since
B1 and doubly untrue since B1.2 froze the rule.

**223. The receipt prose GPT flagged is not repaired, it is DERIVED.** Case 1 printed
`{program_sem_id, lowering_sem_id, target_term_sem_id}` for a round after B1.2 moved the receipt's
domain — the code correct, its own report describing the previous architecture. It now reads the field
list off `Object.keys(receipt)`, which is the only version of the line that cannot say something the
receipt does not.

**224. THE COUNT IS GONE, not corrected — and the law had it too.** `six-identities-stay-distinct`
went on proving a six-way claim about a seven-node chain for the whole of B1.2, **and
`law:derivation.lowering-refinement@1` enumerated the same six** — now **superseded** by `@2`. So the
registry and the witness were
stale together, which is how a hand-typed count survives a reading. `REFINEMENT_CHAIN` is now
machine-readable with an `exercised` flag and a `why_not` per unexercised node; the case
(`chain-identities-stay-distinct`) **derives** its set, **fails** if a declared node is not wired into
the witness, and **names** the unexercised ones. The headline derives too. *A node silently absent and
a node declared absent are the difference between a stale instrument and a scoped one.* GPT's advice —
"don't get obsessed with the count; cover every semantic node it claims the refinement distinguishes"
— is implemented as *there is no count to get wrong*.

**225. `law:derivation.canonical-lowering@1` — since **superseded** by `@2` — was describing the
pre-B1.2 world, AND grid_check was
holding it there.** My find, not GPT's, and the worse of the two stale records. The statement printed
the `LoweringReceipt` as `{program_sem_id, lowering_sem_id, target_term_sem_id}` — the domain B1.2
explicitly moved — and called parameterized-versus-instantiated **DEFERRED**, three passes after B1
decided it and B1.1 ruled the framing a false choice. The grid assertion defending it read *"must keep
the inputs model DEFERRED AND NAMED"* and required only that the words `PARAMETERIZED` and
`INSTANTIATED` appear. **A check that requires a stale record to stay stale is a ratchet, not an
instrument.** Revised to `@2`, which now requires the DECISION and *refuses* the deferring sentence.

**226. And the lookup was reading whichever revision came first.** `entries.find((x) => x.id ===
"derivation.canonical-lowering")` carried no revision filter, and the sibling loop pinned
`revision === 1`. So every assertion below them read whatever sat earliest in the array — which is how
a check keeps testing a superseded statement without ever saying so. All three lookups now resolve the
**canonical** revision. Three laws revised, all three predecessors **kept** as non-canonical history
with `defect_class: record-staleness`, `accepted_false_verdict: false`,
`underlying_observations_genuine: true` — every witness they cite ran and passed; what was stale was
the record of what the mechanism does.

**227. `artifact_versions` had THREE entries no check read, and I found it by tripping over my own
half-applied bump.** The `declared` list in grid_check named `trvm_law_kernel.mjs`, `trvm_world.mjs`
and `derive_protocol.mjs`; the map also carried `lowering.mjs`, `observed_execution_host.mjs` and
`bridge/ic32_film.c`. **Half the map was a hand-maintained number with no instrument behind it** — it
had been carrying `lowering.mjs` through 0.2.0, 0.3.0 and 0.4.0 by hand, unverified. Bumping to 0.5.0
and watching grid_check say **PASS** with the grid still declaring 0.4.0 is what surfaced it. And the
same commit had moved the file's *header* to `v0.5.0` while leaving `LOWERING_VERSION` at `"0.4.0"` —
the identical defect inside one file. All six entries are now read, the map is required to be **fully
covered** by the reader, and `ic32_film.c` is matched on the `emitter_version` string it actually emits
to consumers.

**228. A falsifier outlived its premise again, and was deleted rather than repointed.**
`inputs-model-decided-by-accident` required the law to KEEP the deferred wording. B1.2.1 removed that
assertion, so the case had no subject: it perturbed a sentence nothing checks. Deleted on the **B1
precedent** — `inputs-silently-lowered` went the same way for the same reason. Its live replacement,
`inputs-model-deferred-again`, perturbs the DECISION the law now makes. Two more cases were repointed
after the non-vacuity detector caught them reporting misses against anchors this round had moved; that
detector earned its keep three times in one round.

**229. NOTHING BEHAVIOURAL CHANGED, and that is checkable.** `instantiate()` still throws; `input`
still refuses as `lower-input-not-implemented`; the three port falsifiers are still `DECLARED` and
unwritten. The `add(2,3)` witness still reaches the **same 129 characters** of ic32, the same six-frame
film, the same normal form and the same value 5. `emit(template)` is still byte-identical to what the
pre-template `lower()` produced. Both relation ids moved — `lsem-84c93447…`, `isem-6ac0ea7b…` — and
that is the point: **both relations' commitments changed and neither relation's behaviour did.**

**230. One debt is NAMED rather than paid.** Once emission belongs to instantiation, `lower()` calling
`emit()` means **lowering performs part of instantiation**, and the whole 13-case refinement witness
runs off `low.target_term` — so it reaches native execution **without passing through the relation this
round just made load-bearing**. Nothing identity-bearing flows from the field: the receipt ends at the
template and the term's id is minted by the kernel. But it is recorded as `LOWERING_STATUS.emission_debt`
with a named closer, which makes **B2's restatement of `add(2,3)` through `instantiate({})` mandatory
rather than tidy**.

**231. Gate.** grid **v1.37.0** — 80 entries / 372 citations · `lowering.mjs` **0.5.0** · negative
battery **241/241** (21 new; 1 deleted for a dead premise, 3 repointed) · lowering **13/13**, refinement
unchanged and still FILM-EVIDENCED · derive 45/45 · realm 24/24 · bridge 48/48 · film 16/16 · twelve
paired probes · harness 9/9 · runner 3/3. `scheduler_certificate.json` byte-identical —
**thirty-first** consecutive round.

**232. B2 is one ruling away**, and its shape is unchanged from B1.2 except that item 6 is now
mandatory: (1) delete one refusal line so `input` lowers to `T.port(name)`; (2) `instantiate()` +
`InstantiationReceipt`, verified by **independent re-instantiation** against an independently minted
`target_term_sem_id` — `instantiate()` must **not** self-assert it, on the same rule that keeps the
term's identity the kernel's; (3) I-4a; (4) I-4b; (5) I-4c on `x + (x + y)` all the way through —
correct → 7, swapped → 8, and the correct receipt accepts only the 7-producing term; (6) **restate
`add(2,3)` through `instantiate({})`**, which closes item 230 and is the backwards-compatibility
theorem. Then `church_exp_2_2` and the dedicated DUP-ERA film.

---

## Round 27, pass B2 — inputs become executable

**GPT ruled B2 GO with a ten-step progression and two API constraints, and both constraints changed
the shape of the code rather than decorating it.** The architectural preflight is over: three passes
decided the inputs model, fixed an overbound projection, built the target-template layer and bound the
executable encoding, and this is the round where the thing runs.

**233. `input` lowers, `instantiate()` closes, and I-4c reaches the runtime.** `x + (x + y)` with
x=2, y=3 runs **natively to 7** and the x/y swap to **8** — different terms, different normal forms,
different outcome identities, and the SOURCE evaluator independently gives 7 and 8. The swapped term
does **not** verify against the correct `InstantiationReceipt`. That is the falsifier the mandated
asymmetric fixture exists for: `add(x, y)` with the same values gives 5 either way, so the obvious
witness could not have revealed the defect it is named for.

**234. THE MAP IS STRUCTURAL AND `lower()` INTERPRETS IT.** B1.2.1 wrote `op_lowering_rules` in
English and GPT ruled that insufficient for the same reason the codomain-in-prose was: *a normative
sentence beside a hand-coded implementation is two artifacts that can disagree, and only one of them is
hashed.* The table is now what runs — `LOWERING_SEMANTICS.op_lowering_rules[node.op]` — so a rule
cannot be edited without changing behaviour and behaviour cannot change without moving
`LOWERING_SEM_ID`. `transform: "identity"` on the port's source name is the no-normalization ruling
**made structural**: a name reaches the port unchanged because there is no other transform the table
can name. This closes most of B1.1's declared-open prose brittleness; `substitution` and
`dup_label_policy` are still English elsewhere and that is unchanged.

**235. `lower()` NO LONGER RETURNS AN EXECUTABLE TERM.** GPT was emphatic and the reasoning is the one
this tree keeps re-learning: keeping the convenience field leaves an **official path** (`lower →
instantiate → term`) beside a **shortcut** (`lower → term`), and every future reader has to remember
which one carries the semantics. *That is how a hidden second mechanism comes back.* Removed.
`instantiate()` is the only route to a term, including at the empty environment.

**236. The migration theorem, kept as a theorem rather than an API.** `instantiate(template, {})`
reproduces the **exact 129 characters** the removed field used to return, and the six-frame film, the
normal form and the value 5 are all reached through it. So the zero-input path did not change meaning
when it changed owner — which is what makes removing the shortcut safe rather than merely tidy.

**237. `instantiate()` MAY NOT MINT THE IDENTITY OF ITS OWN OUTPUT.** GPT's second constraint, and it
is load-bearing: an instantiator that emitted bytes **and** certified their semantic id would produce
the artifact and the certificate from one source, so a wrong emission would carry a matching id and
verify against itself. It returns `{ok, target_term, closed_template, inputs_sem_id, consumed_inputs}`
and **no** `target_term_sem_id`; the kernel canonicalises the bytes; `instantiationReceipt()` is built
around that id and refuses an incomplete one by name. Verification **re-instantiates and
re-canonicalises independently** rather than asking the instantiator to agree with itself. Same
discipline the `LoweringReceipt` already followed.

**238. I-4a is witnessed against a SECOND EMITTER, because asserting it about one proves nothing.**
A deliberately hostile allocator — `_impl17`/`q93` binders, labels from 100 — emits **189 characters**
where the real one emits 129, from the *same template*, which keeps the same
`target_template_sem_id` because there is no field an allocation could occupy. **And the allocation
turns out to be non-semantic all the way down**: both terms reach the *identical* canonical normal-form
signature. That was measured, not assumed, and it is a stronger result than the falsifier asked for.

**239. I-4b keeps the source key, Unicode included.** `input("x")` and `input("y")` reach different
template ids, and NFC-composed `é` differs from decomposed `e`+◌́ — normalizing would be a
**language**-semantic change made at the encoding layer, where the source cannot see it.

**240. GPT's item 9: the positive witness carries an unused input.** `{x:2, y:3, unused:999}` and
`{x:2, y:3}` have **different `inputs_sem_id` and reach the SAME term**, so "extras are ignored" is
exercised rather than merely written down — and `consumed_inputs` is `[x, y]`, keeping supplied and
consumed distinct.

**241. THE EMISSION SPLIT TRIGGER MOVED TO STATUS, and B1.2.1 had re-committed B1.1's own finding.**
I had put the trigger inside `INSTANTIATION_SEMANTICS` — governance prose inside a relation identity,
so rewording a note about what the project should do next would re-identify the relation. It is in
`INSTANTIATION_STATUS` now, with GPT's two additional conditions: split emission when it becomes
independently **reused**, independently **theorem-bearing**, independently **versioned or replaceable**,
or when the closed-template intermediate becomes an **independently identified or externally observed**
artifact. GPT's framing of the underlying rule is the durable one: *keep A∘B one relation while nobody
needs to name, vary, verify, reuse or observe A independently of B.* The last two conditions fire
first.

**242. BUILDING IT MOVED NEITHER SEMANTIC ID, and the measurement is an EQUATION rather than a
simulation.** My first version of this case spread the STATUS fields over the SEMANTICS record and
hashed the result — which measures nothing, because status keys are not *in* the hashed object and
adding them naturally changes the hash. The real check: **put back only `op_lowering_rules` and only
`emission`, and the B1.2.1 identities return exactly** (`lsem-84c93447…`, `isem-6ac0ea7b…`). So those
two fields are the only hashed bytes the round touched, and everything B2 actually *built* — `input`
lowering, `instantiate()`, the removal of `target_term`, three falsifiers going DECLARED → WITNESSED,
every lifecycle flag flipping — **moved no identity at all.** That is what B1.1 split the records to
make possible, and B2 is the first round able to exercise it.

**243. Two assertions had become ratchets, and one instrument was answering with the wrong field.**
- The grid required the inputs model to be `implemented: false` and `lower-input-not-implemented` to be
  present — correct for three passes, and **guaranteed to fail on the round that fixed it**. Same
  species as `canonical-lowering@1`'s "keep it DEFERRED", one file over.
- The `REFINEMENT_CHAIN` assertion required `exercised: false` and a `why_not:` to *exist* — true only
  while nodes were unexercised. It now requires the **mechanism**: an `exercised` flag on every node,
  and a `why_not` on every node that lacks one. That holds in both states.
- **`consumed_inputs` was being answered by the implementation.** The assertion guards a *semantic*
  commitment, and once `instantiate()` returned a field of the same name, renaming the semantics field
  left grid_check passing. Found by the battery going `exit=0`; the assertion is scoped to
  `INSTANTIATION_SEMANTICS` now.

**244. And a check I wrote this round would have refused the correct architecture.** The
"lower() must not return a target_term" assertion tested the *whole file* for `target_term: emit(`
and matched **`instantiate()`'s own emission** — it would have failed against the very shape GPT
ruled. Scoped to `lower()`'s body. Six battery cases also failed with `exit=1` against a *correct*
refusal because their expected patterns contained `lower()` and `instantiate()`: **parentheses are an
empty group in a regex**, so each pattern silently matched a string that was never printed.

**245. Three law forgeries had been retargeted at history by a revision bump.** They keyed on
`e['revision'] == 2`, so revising the law pointed them at a superseded entry — a forgery that perturbs
history and leaves the live statement alone. They key on `canonical` now, which is the same correction
grid_check's own lookup needed at B1.2.1.

**246. Gate.** grid **v1.38.0** — 83 entries / 374 citations · `lowering.mjs` **0.6.0** · negative
battery **260/260** (20 new; 2 deleted for dead premises, 10 repointed) · lowering **19/19**, every
chain node now exercised · derive 45/45 · realm 24/24 · bridge 48/48 · film 16/16 · twelve paired
probes · harness 9/9 · runner 3/3. `scheduler_certificate.json` byte-identical — **thirty-second**
consecutive round.

**247. What is next, and what is still open.** `church_exp_2_2` (DUP-LAM, both SUP cases, DUP-VAR,
DUP-APP, APP-SUP, APP-LAM across `t:`/`d:`/`v:`) and then the purpose-built **DUP-ERA** witness, which
`exp_2_2` does not exercise. Still declared open and unchanged: **source-refusal ↔
instantiation-refusal preservation** — the source refuses a missing input as `program-input-missing`
during evaluation, instantiation as `instantiate-missing-input` before a term exists, and refinement
over refusals is a separate theorem nobody has attempted. Also unchanged: the six DUP-* rules, the
`d:`/`v:` loci and BUDGET_EXHAUSTED terminals are refused by name rather than approximated.

---

## Round 27, pass B2.1 — the emission split fires, and two defects behind it

**GPT's review of B2 found a real compiler-layer defect, a hidden vocabulary, and ruled that B2 had
tripped every condition of the split trigger B1.2.1 wrote down.** The trigger firing is the good news
in the round: it was declared before it was needed and it told us when the composition had become too
interesting to stay one relation.

**248. THE INSTANTIATOR READ ITS INPUTS TWICE — reproduced before repair.** `instantiate()` read the
caller's object once to **bind** values into the term and again to compute `inputs_sem_id`. A getter
answering 2 and then 999 gives:

```
reads: 2 · term: Church 2 · inputs_sem_id: inputsSemId({x:999})
```

An application record asserting *"these inputs were {x:999}"* above *"this term represents x=2"*.
**Nothing about the runtime was wrong — the RELATION misbound its own input identity.** That is
`derivation.entry-snapshot@1` arriving in the compiler layer, and the repair is the same mechanism the
authority layer already had: **one canonical `ownCanonical` snapshot of BOTH arguments at entry**,
everything downstream reading the snapshot. The template is snapshot too, because `instantiate()` is
exported and walks it three times. **The invariant: the bytes `inputs_sem_id` identifies are exactly
the bytes every substituted value was derived from.** Not a supplier rung — a compiler-relation TOCTOU,
and GPT was right to decline to number it.

**249. A CLOSED VOCABULARY OF BARE NAMES STILL HIDES SEMANTICS.** B2 gave rules a closed set of
predicate and transform **names** bound to JavaScript functions and called it structural. GPT changed
`integer` from `Number.isInteger` to `() => true`: `const(1.5)` **lowered successfully instead of
refusing**, with `LOWERING_SEM_ID` **unchanged**. `identity` was worse — it could have been made to
NFC-normalize a source input name, silently undoing the port ruling three passes after it was made.
The vocabulary stays **closed** and its *definitions* are now data in the hashed record. **Where the
trust boundary sits is stated rather than implied:** the kind interpreter is trusted code like
`canonicalBytes`; what has been removed is the rule **language's** ability to hide meaning.

**250. THE SPLIT TRIGGER FIRED — all four conditions, at once, without my noticing.** B1.2.1 wrote
them down and B2 tripped every one: `emit()` is exported and independently reused · **I-4a is a
theorem about emission alone**, comparing two emitters over one template · the executable encoding
carries its own content identity and an alternate emitter was deliberately run against it ·
`instantiate()` **returned** the closed template to its caller. *The second settles it:* once two
emitters are compared over one closed template, an emitter upgrade re-cutting the semantic identity of
**port substitution** is plainly wrong, and that is exactly what a merged relation does.

**251. Three relations now, and the closed template gets its OWN identity domain.**

```
program → template → CLOSED TEMPLATE → term → nf → outcome
  lowering   instantiation   emission     film   decode
```

`ctmpl-` against `tmpl-` **even where the bytes are equal**. For `add(2,3)` with `{}` the two
structures are byte-identical and they are **not the same thing**: one is what the *compiler* produced,
the other is what an *invocation* closed. Sharing an id would make "this was instantiated" and "this
needed no instantiation" indistinguishable — the collapse the whole chain exists to prevent.

**252. The split made the verifiers cleaner, which is an argument FOR it rather than a consequence.**
Verifying instantiation now needs **no runtime canonicaliser at all**, because the relation ends at a
structure this module owns. Only emission needs one — and it **takes it as a parameter**, because the
module that defines a relation must not also choose the oracle that judges it. Both are exported
production functions: at B2 the only implementation of *"does this receipt hold?"* lived in the test
suite, and **a relation whose verification procedure exists only in its own tests is a relation nobody
else can check.**

**253. I-4c is FILM-EVIDENCED, and it cost nothing.** GPT passed the B2 `x + (x + y)` term to the
existing `ic32_film` and it already succeeded: **12 frames, all APP-LAM, terminal NORMAL_FORM**.
Reproduced here and wired in, so the **input** refinement witness now carries the grade the no-input
one has had since round 26 — without one line of new runtime semantics. **It does NOT advance the
frontier and is not a substitute for `church_exp_2_2`:** every frame is APP-LAM at tree loci, and the
six DUP-* rules, the `d:`/`v:` loci and BUDGET_EXHAUSTED remain exactly as unexercised as before.

**254. A falsifier was RETIRED rather than repaired, for the third time in this pass.**
`implementing-moved-neither-id` reverted the two fields B2 changed and required the B1.2.1 identities
to return exactly — true and worth measuring at B2. B2.1 ended its premise: the delta is no longer two
fields, and keeping it would have meant **growing an embedded copy of the module inside its own test**,
at which point it stops being an independent check. The live property it protected is still measured by
`semantic-ids-track-semantics-only`. The B2 ids are kept in `SUPERSEDED_B2_SEM_IDS`.

**255. And two of my own instruments were answering with the wrong thing.** The grid assertion for the
closed-template domain tested for the **string** `"ctmpl-"`, which also appears in
`INSTANTIATION_SEMANTICS.codomain_identity_domain` — so renaming the actual constructor's prefix left
it green. Found by the battery going `exit=0`. Bound to the constructor now. *This is the third round
running in which an assertion was satisfied by a coincidental second occurrence of the text it was
looking for* — after `consumed_inputs` answered by the implementation field and the `implemented:
false` assertion answered by a comment.

**256. Gate.** grid **v1.39.0** — 86 entries / 374 citations · `lowering.mjs` **0.7.0** · negative
battery **275/275** (16 new; 1 deleted for a dead premise, 3 repointed) · lowering **21/21**, **eleven**
chain nodes all exercised, I-4c film-evidenced · derive 45/45 · realm 24/24 · bridge 48/48 · film 16/16
· harness 9/9 · runner 3/3. `scheduler_certificate.json` byte-identical — **thirty-third** consecutive
round.

**257. NEXT IS `church_exp_2_2`, and that is where the real frontier is.** Not I-4c — it only ever
exercised APP-LAM. `exp_2_2` reaches DUP-LAM, both SUP cases, DUP-VAR, DUP-APP, APP-SUP and the `d:`
and `v:` loci; then the purpose-built **DUP-ERA** witness, because `exp_2_2` does not exercise it and
six rules from one large term that happened to terminate is coverage by hope. Still declared open and
unchanged: source-refusal ↔ instantiation-refusal preservation.

---

## Round 27, pass B2.1.1 — the verifier closure

**GPT's find against B2.1, and it is the defect B2.1 itself closed, one layer up.** B2.1 established
that *the relation may not bind one snapshot and identify another*, and then shipped verifiers that
**verified one snapshot and authenticated another**.

**258. Both false positives, reproduced before repair.** `verifyInstantiationReceipt` called
`instantiate()` — which snapshots the template internally — and then
`targetTemplateSemId(ownCanonical(template))`, a **second traversal of the caller's object**. So a
template whose `source_name` answers `"x"` then `"y"` satisfied a receipt asserting:

```
target_template_sem_id = port("y")   inputs_sem_id = {x:2}   closed_template_sem_id = church(2)
```

**Three claims, each true of a different immutable template and true of no single one** — `port("x")`
with `{x:2}` gives `church(2)`, and `port("y")` with `{x:2}` refuses outright as
`instantiate-missing-input`. The verifier returned `ok: true` because the first traversal supplied the
instantiation half and the second supplied the source-identity half. `verifyEmissionReceipt` had it
across its two `ownCanonical` calls: a closed template answering `church(2)` then `church(3)` satisfied
a receipt pairing the identity of 3 with the emitted term of 2.

**259. The repair is round 27A.2's convention, and the RECEIPT is untrusted too.** Each verifier owns
every untrusted argument once at entry — template, inputs or closed template, **and the receipt, which
arrives from whoever is asking to be believed** — and delegates to an `*Owned` helper whose suffix is a
**precondition** and which never reaches back to a caller object. The canonicaliser stays a
**capability the caller grants** rather than data to snapshot, because the module defining a relation
must not choose the oracle that judges it.

**260. And the honest claim about the receipt is narrower than the other two, so it is stated that
way.** No verifier reads a receipt field twice today, so snapshotting it closes **no live exploit** —
it is defence in depth, and the witness measures what it actually buys: the receipt is **pinned** to
one read, so a future verifier that does read a field twice cannot be split. My first draft of that
case asserted a hostile receipt would be *refused*; it is not, and correctly so — the snapshot collapses
it into whatever it said on the single read. **Claiming a defect there would have been an overclaim in
the flattering direction**, and the case now measures pinning instead.

**261. THE ASSERTION-STRENGTH HIERARCHY, GPT's ruling on the three-round pattern.**

> **RUNTIME DATA > BEHAVIOURAL API > PARSED AST > RAW TEXT**, and raw-text matching may not stand in
> for structure.

`grid_check` now **imports** `lowering.mjs`. **Fourteen assertions** moved off regex: record contents
are read as data, API shape by **calling** the functions. Text is reserved for properties that are
genuinely textual — a version constant, a forbidden phrase, a NUL byte — or for code-shape obligations
that would need a JS parser this tree does not have, and those are marked **TEXT-TIER** in place so a
reader can see which rung they are on. GPT explicitly declined the larger option of parsing
`lowering.mjs` into data, as too big for the problem; that judgment is taken.

This kills the class for the converted assertions: `"ctmpl-"` was matched by
`codomain_identity_domain` while the real constructor's prefix had been renamed, and **calling
`closedTemplateSemId()` cannot be fooled that way**.

**262. THE CONVERSION LOST TWO PROPERTIES, AND THE BATTERY CAUGHT BOTH IN ONE RUN.** `typeof f ===
"function"` **cannot see a deleted parameter**: removing `canonicaliseTarget` from
`verifyEmissionReceipt` leaves every behavioural probe passing, because `undefined` is not a function
either way. The same for `emissionReceipt` losing its second parameter. Both now assert **arity on the
function object**. *A stronger representation is not automatically a stronger assertion* — moving up
the hierarchy has its own failure mode, and it is the one where the new form is silently weaker than
the regex it replaced.

**263. A stale comment, one relation behind.** The block above `instantiationReceipt` still drew
instantiation producing "closed term BYTES" and needing the runtime canonicaliser — the pre-split
world. The implementation was correct and its own explanation described the previous architecture.
Third time for this file.

**264. Gate.** grid **v1.40.0** — 87 entries / 374 citations · `lowering.mjs` **0.7.1** · negative
battery **281/281** (6 new) · lowering **22/22** · derive 45/45 · realm 24/24 · bridge 48/48 · film
16/16 · harness 9/9 · runner 3/3. `scheduler_certificate.json` byte-identical — **thirty-fourth**
consecutive round. `derivation.instantiation-identity` is the **first** superseded revision in this
line carrying `accepted_false_verdict: true` — the verifier genuinely returned `ok:true` for a receipt
that does not hold, and the record says so rather than filing it as staleness.

**265. Compiler governance stops here.** GPT's instruction, and it is the right call: the next work is
`church_exp_2_2` — DUP-LAM, both SUP cases, DUP-VAR, DUP-APP, APP-SUP and the `d:`/`v:` loci — then the
dedicated **DUP-ERA** witness. **Not** an `input_footprint_sem_id`: `consumed_inputs` is
`templatePorts(target_template)` and therefore **statically derivable** from an id already committed,
so a footprint identity today would be a second name for information the template already carries. It
earns one when consumption becomes **execution-dependent** — a conditional or lazy read where two runs
of one template consume different subsets — and at that point round 15's grant/footprint/trace
distinction becomes exact rather than analogous. **And not** a relabelling of the 24 runtime vectors as
emission vectors: they test a *runtime* and emission produces the *input* to one. A small
`EMISSION_CONFORMANCE-v1` corpus over `{closed_template → target_term_sem_id}` composes with the
existing runtime oracle downstream; I-4a is already evidence of the second, weaker emission property —
different bytes, same normal form.
