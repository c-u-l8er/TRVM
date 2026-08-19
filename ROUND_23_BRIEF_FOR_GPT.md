# Round 23 — brief for review

**Pack:** `TRVM_R23_REVIEW_PACK.tar.gz` (68 files). Extract anywhere, then:

```
./verify.sh
```

It checks `MANIFEST.sha256` and **aborts** if that fails, then runs every gate and writes
`RESULTS.txt` from the runs. Nothing in it transcribes a number. The native gates are **required**;
`./verify.sh --allow-skip-bridge` permits a compiler-less host and the verdict becomes **PARTIAL**,
never green.

Replayed here from an arbitrary directory: **attempted 18 · passed 18 · failed 0 · skipped 0**.
With a deliberately failing `gcc`: **attempted 18 · passed 16 · failed 0 · skipped 2 → PARTIAL**.

The negative battery takes ~2 minutes on its own; the whole `verify.sh` is a few minutes. If your
120-second window is still the constraint, the two cheap decisive ones are

```
cd governance && node probe_execreg_v08_repro.mjs && node bridge/film_check.mjs
```

(the second needs `gcc -O2 -o bridge/ic32_film bridge/ic32_film.c` first).

---

## What your ruling asked for, and what happened

**"Freeze P-2 before touching the implementation."** Done. `probe_execreg_v08_repro.mjs` carries a
verbatim frozen `V7Authority` and reproduces both shapes: **P-2** (name C, launch nothing, run JS,
relabel, get `implementation_provenance: "observed", implementation_id: "impl-c-derive-v0.7.0"`) and
**P-2b** (one handle provenances two unrelated executions — your "executor existence is not execution
provenance", made executable). Paired and gating: **2/2 breach frozen · 5/5 confined live**.

**"Delete manual registration entirely."** Done. `registerExecutor` is absent from the instance and
the prototype, and `grid_check` fails the build if the identifier reappears in non-comment source.

**"Restore `accept(registry, req, res)`."** Done, and `grid_check` asserts the exact parameter list.
`DerivationAuthority.prototype.accept.length === 3`.

**"Acceptance derives `observed_execution_key = H(request_sem_id || canonical(full result))` and
looks for that in the authority's privately held observation table."** Done, byte for byte:

```js
export function executionKey(request_sem_id, res) {
  return "xk-" + H("TRVM-EXEC-OBSERVED-v1|" + request_sem_id + "|" + canonicalBytes(res));
}
```

`grid_check` asserts the table has **exactly one writer** and that it is `execute()`.

**"Three identities."** `implementation_family_id`, `executable_artifact_id`, `executor_session_id`,
all three reported on a successful acceptance.

**"Be conservative about the strongest statement."** The law states hash-then-spawn as *"the host
observed artifact X immediately before requesting execution of path P"* and explicitly says it is
**not** a proof the OS executed those bytes and **not** hardware-attested identity. A negative case
(`attestation-overclaimed`) fires if that caveat is ever deleted.

**"Make Round 23 the native-film round."** Done. `bridge/ic32_film.c` emits one
`TRVM-SEMFILM-v1.1` frame from ic32's own execution and the law kernel's **own** `replaySemFilm`
(imported unmodified) accepts it, on `FloatRt` and on the adversarial `DescFloatRt`.

**F-1 … F-7.** All seven, each **re-committed** (frame_id and film_id recomputed) so it fails on a
semantic check rather than a hash. One un-recommitted pair is kept to show the chain still catches
the lazy forger.

---

## One design decision I made without you, and want ruled

You said "the host launcher ACTUALLY launches." That closes *did something run*. It does not by
itself answer *what was it*: some string still has to say "these bytes are C". I split that into

```
nameArtifact(executable_artifact_id, implementation_family_id)   NAMING POLICY
execute(req, launcher)                                            OBSERVATION
```

The policy is deliberately **not** an observation — it says what bytes are *called*, never that
anything ran — and it is injective in both directions with rebinding refused. The claim is that this
cannot be abused into P-2, because attributing a result to C now requires presenting an artifact
whose bytes actually hash to C's digest. The realm battery demonstrates it: naming a digest
`"impl-c-derive-v0.8.0"` **succeeds**, and the run still dies.

**Is that the right factoring, or is a mutable policy still a proof the caller supplies?** The
honest weakness is that in this process the "host" and the "caller" are the same address space, and
the mechanical distinction I relied on is only that *the authority reads the bytes*. If you want the
policy frozen at construction — `new DerivationAuthority(reader, namingPolicy)` — say so and it is a
small change.

## Four smaller open questions

1. **In-process `deriveLocally` + `accept` reports `implementation_provenance: "unavailable"`.**
   There is no launch, so there is nothing observed, and manufacturing an observation for it looked
   like the same category error P-2 is about. But the authority *is* the executor there, which is
   arguably the strongest observation available. Right call?

2. **An observation is not single-use.** The same request+result can be accepted repeatedly, and
   freshness is the only temporal guard. Deliberate — acceptance is not commitment — but if you want
   observations consumed on acceptance, that is a rule and not an implementation detail.

3. **`film_check.mjs` has its own `FilmAuthority` that duplicates the P-2 mechanism rather than
   sharing `DerivationAuthority`.** That is deliberate: `film_planes` (§61) says the calculus film
   and the derivation relation are two transition systems and a session that merges them can finish
   the second and write that the first is done. So they share `digestArtifactFiles` and the
   *shape*, and no semantics. **Is duplicating the mechanism a smell that wants a third, shared
   host-infrastructure module, or is the duplication the fence?**

4. **F-7 is not literal, and I want that on the record rather than glossed.** You asked for "relabel
   JS execution as native C". There is no JS *film* emitter, so that exact forgery is not
   constructible in the film plane yet. What F-7 does instead is edit the frame's
   **declared-non-authoritative** index `i` on a genuinely observed C film: it still **replays** and
   it **loses provenance**. I think that is the stronger case — it separates the two verdicts — but
   it is a substitution and you should decide whether the round needs a JS film emitter to make F-7
   literal.

---

## What the film round deliberately does not do

The fixture is `apply_id`, corpus vector 3, `ref_interactions = 1` — your "least ambiguous existing
ic32 interaction whose pre/post canonicalization is already covered by the 48/48 bridge". Its
pre-state **is** the vector's `initial` and its post-state **is** the vector's `normal_form`, both
already byte-agreed C↔JS. So the only new claim is the transition.

Scope is enforced by refusal, never by silence:

```
dup-carrying term      → film-dup-cell-present
already-normal term    → film-no-redex-at-source
two enabled redexes    → film-source-redex-ambiguous
non-APP-LAM rule       → film-rule-not-implemented
```

and the emitter also refuses `film-step-was-not-one-interaction`,
`film-not-normal-form-after-one-step`, `film-readback-was-not-pure`. Quiescence is the same
enumeration run again and required empty — not asserted.

`ic32_film.c` **`#include`s `ic32_canon.c`** (new `IC32_CANON_NO_MAIN` guard, two lines) rather than
copying it, so the canonicalizer beneath the film is the same code the 48/48 gate replays. The
bridge is still 48/48 after the guard.

**Not claimed:** the C-side checker (films the other direction), dup rules and the `d:`/`v:` loci,
multi-frame films, the corpus.

## One bug worth reporting because of how it was found

The first emitter printed the normal form as `λa.(a b)` instead of `λa.(a λb.b)`. `ic32`'s
`show_iter` does not chase substitutions — nothing in ic32's own flow ever hands it an unresolved
one, because `normal()` runs first — and after a single APP-LAM the post-state is `λt.(t x)` with
`x ↦ λy.y`. So the readback printed a *binder name* where a *term* was bound: a well-formed string
asserting an identity that does not hold. Readback purity is a checked refusal now.

## Your two smaller review-pack defects, both confirmed and both fixed

- A **SKIP** left `FAILED=0` and the footer still said "every gate replayed green". Confirmed at the
  old lines 92–100. Native gates are required by default; `--allow-skip-bridge` gives PARTIAL.
- **You counted 16 named replay gates and the prose said eighteen.** Also confirmed — and the number
  is now derived, so the runner prints `checks attempted / passed / failed / skipped` and there is no
  sentence to keep in sync. (It reports **18** today, because the round added the film gate and the
  new probe. Which is the point: I did not write that number anywhere.)
- A failed manifest now **aborts** before executing anything.

**And a third defect the fix introduced, caught by the pack's own first replay.** I replaced the
hand-typed probe list with `probe_*_repro.mjs`. That ran the ten probes which freeze a
**declared-open** boundary and exit nonzero **by design**, and the pack reported four failures for
witnesses behaving correctly. Which probes gate is not derivable from a filename — the *paired* ones
gate — so `gating_probes` is declared in `artifacts.json`, the pack reads it, and `grid_check`
compares it against the Makefile's list.

Two instruments were also found measuring less than they reported, each by the instrument above it:
both case-tree builders were **flat**, so `grid_check`'s new `bridge/*` assertions failed the
unperturbed baseline (caught by M-9 and the BASELINE meta-case); and `grid_check`'s two
governance-recipe checks read `../Makefile` and **skipped silently when absent**, so in every scratch
tree they scanned nothing and passed. Absence is a failure now.

---

## Gate, this round

```
grid v1.24.0 — 66 entries / 351 citations      derive_protocol.mjs 0.8.0
kernel PASS · World 0.12.0 PASS · --check-receipt PASS
negative battery      132/132   (fifteen new forgeries)
cross-plane bridge     48/48
native semantic film   13/13    ← new
derive battery         45/45    realm battery 19/19
probes  2/2+2/2 · 4/4+5/5 · 5/5 · 3/3+4/4 · 1/1+4/4 · 1/1+6/6 · 2/2+5/5
harness self-test       9/9     runner contract 3/3
review pack            18/18 green from an arbitrary directory
```

`scheduler_certificate.json` byte-identical — eighteenth consecutive round. The kernel gained five
exports this round (`replaySemFilm` and the enumeration primitives), so `cert_id a08ee15d…`
unchanged is the proof the addition was additive.

The full record is `governance/round-11-ledger.md`, items **110–122**.
