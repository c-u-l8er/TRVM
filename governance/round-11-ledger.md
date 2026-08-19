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

`law:derivation.canonical-lowering@1` (one source program under one lowering semantics determines one canonical target term), `law:derivation.target-decoding@1` (one canonical normal form under one decoder determines one structural outcome, or a structural decode refusal), and `law:derivation.lowering-refinement@1`, which composes them and is the theorem actually wanted. The first two exist to make the third **diagnosable**.

**And the lowering does NOT get a film.** A film is evidence for a *transition system*; lowering is a relation `DeriveProgram → TargetTerm`. Filming it would invent a sequence of internal compiler steps and make implementation strategy semantic — the same mistake the read-order ruling refused in round 12. The instrument is **re-lowering and comparing canonical target bytes**. A film becomes appropriate only if the lowering engine itself ever becomes a governed transition system whose intermediate steps matter.

`lowering_id` also splits in two before it is written, because one id must not silently answer two questions: `lowering_sem_id` identifies the lowering *semantics* (source core id, target encoding id, canonical specification, conformance-vector identity), and a `LoweringReceipt {program_sem_id, lowering_sem_id, target_term_sem_id}` records what happened when *this* program was lowered.

**One identity decision deferred on purpose, and named so it is not discovered.** `add(const 2, const 3)` has `inputs = {}`, so the first witness does not decide **parameterized** lowering (`program_sem_id → target term with input ports`, inputs arriving at execution, `target_term_sem_id` a function of the program alone) versus **instantiated** lowering (`program_sem_id + canonical_inputs → closed target term`, where the identity must say so). Both are coherent; they are different systems. That decision comes **before** the `input` op, not during it — an unstated variable inside `target_term_sem_id` is precisely the hidden-identity bug class round 16 exists to prevent.
