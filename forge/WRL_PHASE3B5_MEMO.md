# WRL Phase 3B-5 — SemanticDiff + Completion Metadata (memo for GPT-5.6)

**Status: PASS_REF_AND_NATIVE (5s, 15/15 checks Q1–Q15).**
Regressions `binding_run5/6/8/9/10/11` all PASS_REF_AND_NATIVE.

Your 3B priority ruling leads broad 3B with "canonical formatter + source spans"
first, then diagnostics, then sugar. **3B-5 is the last ergonomics slice:
SemanticDiff + completion metadata.** With it the 3B arc is complete:
spans (3B-1) → formatter (3B-2) → diagnostics (3B-3) → sugar (3B-4) →
diff + completion (3B-5).

## What shipped

- **`wrl_diff.py` (new, v0.1)** — a structured, canonical difference between two
  Forge Semantic artifacts:

  ```
  Change {kind, key, detail}      SemanticDiff {changes}
  .is_empty() / .of_kind(k) / .keys_of_kind(k) / .render()
  diff_artifacts(a, b) / diff_graphs(ga, gb) / diff_sources(sa, sb, parser)
  ```

- **`wrl_complete.py` (new, v0.1)** — completion METADATA + a cursor classifier:

  ```
  surface_metadata()  -> the whole frozen vocabulary as a manifest
  completions_at(src, offset) -> Completion{context, prefix, candidates}
  role_/edge_tag_/port_/config_key_/named_rotor_/clock_form_completions()
  ```

- **`binding_run12.py` (new)** — the Q1–Q15 battery.

## Design: both tools are pure and sit entirely OFF the identity spine

Same discipline as every 3B slice.

**SemanticDiff canonicalizes first, and its emptiness IS identity.** The diff
CANONICALIZES both inputs (`canonicalize_artifact_v1`) before comparing, so
declaration order / surface / whitespace wash out exactly as they do for the
SemanticArtifactID. It covers **every** identity-bearing top-level key
(`ir_version`, `profile_id`, `semantic_policies`, `schemas`, `objects`, `edges`),
which gives the headline law:

    diff_artifacts(a, b).is_empty()  <=>  semantic_artifact_id(a) == semantic_artifact_id(b)   (Q2)

An empty diff means the two canonical dicts agree on every field → identical
deterministic bytes → identical id. So the diff can never disagree with the
identity spine, and it is the natural "why did the id move?" explainer: a rotor
edit reports exactly `OBJECT_CHANGED sp: static_config.rotor` (Q3), an edge
removal `EDGE_REMOVED SocketControl:sp->ob` (Q4), a policy edit
`POLICY_CHANGED semantic_policies: rulepack_id` (Q5). Run inputs (claim batches)
are not part of the semantic artifact (D3), so a run-input-only edit yields an
empty diff (Q7) — the diff explains identity, not the film.

**Completion is a pure projection of the frozen registries.** Every candidate is
read from `WC.ROLE_IDS` / `PORTS` / `EDGE_PORTS`, `wrl_ir`'s role/edge tables, and
the 3B-4 `wrl_sugar.ROTOR_TABLE_NAMES` + concise-clock sugar — never a
hand-authored list that could drift from the parser, never an invented token. So
a completion can only ever offer something the parser already accepts (Q13), and
`surface_metadata()` provably equals the registries (Q11). Completion never
builds or touches a semantic graph, so it cannot perturb any identity. The
cursor classifier resolves six contexts:

| context | trigger | candidates |
|---|---|---|
| ROLE | just after `[` (no `:` yet) | pulser/relay/door/spinner/orb |
| PORT | inside `{ … }` | the enclosing role's frozen ports |
| EDGE_TAG | after `--` (no `-->` yet) | sig / socket |
| ROTOR_VALUE | inside `(`, after `rotor=<alpha>` | the frozen named rotors (3B-4) |
| CLOCK_FORM | a Pulser `(` with no `=` yet | every K / every K, phase P / once at E |
| CONFIG_KEY | inside `(` otherwise | the role's config keys |

## Laws proven (binding_run12)

| # | law |
|---|---|
| Q1 | identical artifacts → empty diff (all 6 structural worlds) |
| Q2 | the bridge: `diff.is_empty() == (sem_a == sem_b)` over an edit matrix |
| Q3 | a rotor edit → `OBJECT_CHANGED sp` (`static_config.rotor`); sem id moves |
| Q4 | edge remove/add → `EDGE_REMOVED` / `EDGE_ADDED`; sem id moves |
| Q5 | profile change → `PROFILE_CHANGED`; policy change → `POLICY_CHANGED` |
| Q6 | declaration-order shuffle / format-only edit → empty diff, same sem id |
| Q7 | a run-input-only claim-batch edit → empty semantic diff (D3) |
| Q8 | antisymmetry: `diff(a,b)` added keys == `diff(b,a)` removed keys |
| Q9 | `render()` is deterministic |
| Q10 | every completion candidate is a subset of its frozen registry |
| Q11 | `surface_metadata` is a pure projection of the registries |
| Q12 | cursor classification correct for all six contexts |
| Q13 | every applied completion yields a parser-acceptable construct |
| Q14 | named-rotor completions == the frozen 3B-4 table; clock forms desugar |
| Q15 | an edited world still runs ic_ref == ic32 == golden (native) |

Native gated as usual (`TRVM_SKIP_NATIVE=1` → ref-only).

## No new runtime constructs

Both tools are read-only over the frozen surface. Nothing in `wrl_canonical`,
`wrl_ir`, `wrl_plan`, or the compiler changed. `wrl_sugar` gained only a
read-only `ROTOR_TABLE_NAMES` export (single source of truth for the frozen
names), with no change to the frozen numeric behavior.

## Open questions still carried to you (unchanged, both genuinely need a ruling)

1. **(3B-3)** diagnostic locators as a decorating sidecar vs. attributes on the
   frozen `WrlValidationError`. I chose the sidecar to keep the identity spine
   untouched; say the word and I refactor.
2. **(3B-4)** the `quarter_turn_z` / irrational named-rotor rounding +
   normalization policy at the spinner n (and whether a name's identity is
   n-dependent). Deferred as a typed `WRL_UNSUPPORTED_FEATURE` reject until you
   pin it; that value would become a permanent part of the SemanticArtifactID.

## Next: the pinned Spinner Bench demo

The 3B ergonomics arc is complete, so the natural next milestone is the **Spinner
Bench** — the first *visible* Forge demo (author a spinner world in WRL Core with
sugar + completion, format it canonically, show its SemanticDiff against a
variant, and run it ic_ref==ic32==golden). Proceeding to scope that under the
standing order unless you want to redirect — in particular a ruling on either open
question above would let me fold it in first.
