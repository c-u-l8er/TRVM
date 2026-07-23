# E2 Results v2.3 — Native Once Refreeze (28/28)

*(Retitled per round 12: the canonical current result is 28/28 under proc-e2.3. The v2.2 body below is preserved as the historical record; the errata section at the end is the authoritative delta.)*

# E2 Results v2.2 — Equivocation Convergence Pass

**27/27 checks pass. The round-six defect — recognition without convergence — is resolved by separating the two layers the review identified: a claim-set recognition layer that is provably arrival-order independent, and a named acceptance policy that is log-relative by design. Option A remains viable; the reducer binding remains the sole open frontier.**

Supersedes v2.1. Round six executed the artifact and found the deepest defect of the series: equivocation was detected, but which payload won, which dispute evidence survived, and the reject-log growth all depended on arrival order. As the review put it, the experiment had reached the actual TRVM thesis — how does recognition remain convergent when one identity carries contradictory claims?

## The law, as now implemented and tested (Q1/Q2)

**Recognition layer (converges).** The base object is `claims[event_id][payload_digest] = (status, receipt)` — a monotone, mergeable set of observed claims. Recognition (unknown / unambiguous / disputed) is *derived* from the set, never stored. Every conflicting digest is retained. Retransmitting **any** previously observed claim — accepted or conflicting — is idempotent: zero core-state change, verified. The permanent *equivocation convergence matrix* runs Block and Door payloads under one identity through all four arrival patterns plus retransmissions and asserts: identical observed-digest sets across all patterns, disputed recognition in all patterns, and retransmission inertness.

**Acceptance layer (log-relative, by declared policy).** First claim in canonical log order takes effect; within one admission batch the order key is (seq, writer, payload_digest), so simultaneous conflicting claims resolve by digest — the matrix verifies both same-batch host orders produce byte-identical worlds. Later conflicting claims contest the receipt (derivable from |claims| > 1) but never undo the effect. Cross-batch orders are different logs and legitimately accept different payloads — deterministic per log, which is Stage One's guarantee. Distributed settlement (defer-until-settled / authority+digest selection / compensating rollback / sequencer) is Stage Three's protocol menu, deferred explicitly.

**An instructive test failure.** The first draft of the matrix asserted status-carrying claim sets identical across *all* patterns and failed — correctly, because it was checking acceptance where the law demands recognition. The corrected assertion is the sharper statement: recognition converges everywhere; acceptance converges per log. The failure clarified the law before any reducer ever runs it.

## The rest of the round-six list

**Q3 — Dual-phase exactly-once.** REACT now has its own ledgers: participant delivery counted against the registry, and every generated SIG/SIGW token carries a serial that must be consumed exactly once. The fault battery attacks both phases and the generated tokens: **9/9 injected faults detected** (commit dup/omit/stale, react dup/omit/stale, sig dup/omit, unregistered live participant). The review's concrete harm — a duplicated hot-wire delivery causing two noncommutative spinner rotations — is now structurally impossible to miss.

**Q4 — Content-addressed rulepack.** `rulepack_hash` is computed over the declarative semantic tables (prefab schemas, port types, legal pairs, merge policies, configurables, tariffs, numeric policy) plus a procedural-rules version commitment; artifact ids derive from it, and the test verifies stability under identity and movement under any table edit. Full content-addressing of procedural rule bodies arrives with the portable encoding — stated, not glossed. `H()` now serializes arguments with structural framing (no concatenation ambiguity), and events are schema-validated with malformed submissions deterministically rejected.

**Q5 — EV_CONFIG.** Tunable objects (Pulser period/phase, Spinner rotor) have authoritative event semantics with typed validation; the config battery covers accept and three reject shapes. Every fixture is now built entirely through events — the E2a relay ring is primed by an in-model one-shot seed pulser instead of a direct field write. Zero out-of-step authoritative mutation anywhere in the harness; the model now obeys its own harness contract.

**Q7 — Honest metering.** The ceiling meters *charged semantic steps* (events, grafts, erasures, removed wires, phase deliveries, reactions); membership scans and endpoint validation are declared uncharged bookkeeping. Adjacency-indexed full accounting belongs to the reducer, where the ranking function is native.

## Battery totals

Eighteen critical-pair cases at 300 randomized schedules each (all laws asserted every schedule, budget invariant every epoch), the equivocation matrix, oracle sensitivity 15/15 with automatic coverage, 9/9 fault negatives, ceiling and rulepack tests, three exhaustive windows (2,592 and 24 complete per-epoch film enumerations; ≥60,000 for the gate merge), E2a 40×2,000 cross-seed unanimity, and 100,000 epochs of closed-form assertion (relay period-4 seed-primed from t=5, door period-3, spinner rotation epochs, charged-steps bound 30) with zero violations. Quaternion-proxy drift unchanged at −2.015×10⁻⁵, observational, E1's problem.

## Open, honestly

Procedural rule bodies enter rulepack identity via version commitment until the portable canonical encoding exists (first task of the binding). Stage-three settlement policy selection is deferred protocol work. Eighteen-rule active-pair lowering, real-reducer conformance, and CPU/CUDA parity are open and blocked on the repository. The claim-set model is precisely the structure that should merge across replicas via boundary ports — the recognition layer was designed mergeable on purpose, so stage three inherits it rather than reinventing it.


## Errata: proc-e2.3 — native Once (round 11, narrow unfreeze, REFROZEN)

The period-10**9 Once sentinel is gone. Clocks carry authoritative
`mode`/`epoch`/`done`; a once clock fires iff the commit epoch equals
its target, `done` latches at the first commit at-or-after the target
(so late configuration latches WITHOUT firing), and no second firing
exists at any t — asserted at t=10**9, the inverted round-8 falsifier.
Acceptance (now check 28): Once(40) fires exactly once; Once(1) primes
during construction; Once(0)-late never fires with done latched;
silence at 10**9. Model-side films read `done` from state, not from a
horizon predicate. RULEPACK_HASH moved with the CONFIGURABLE edit, as
the content-addressing requires. Battery: **28/28**. The model is
REFROZEN at v2.3; binding Law 6 is now global.
