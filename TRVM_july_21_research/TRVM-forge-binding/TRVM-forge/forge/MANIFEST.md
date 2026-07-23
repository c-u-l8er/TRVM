# TRVM Forge — E2 Bundle (2026-07-18)

| File | Version | Role |
|---|---|---|
| TRVM_FORGE_stage1_canvas_spec.md | v0.3 (frozen) | Stage-one Canvas spec. Architecture freeze in effect; v0.4 errata batch queued in E2_RESULTS (idempotent event identity w/ equivocation disputes, capability release, typed links w/ src ports, total order key, writer-complete instance ids, full-width ids, global ceiling, lineage in state, Relay promotion, exporter-derived tariff features, 160B header). |
| e2_model.py | v2.3 | Semantic model interpreter / golden oracle. Claim-set recognition (arrival-order independent) + log-relative acceptance policy; phased ADMIT→COMMIT→REACT with dual-phase exactly-once ledgers; content-addressed rulepack; EV_CONFIG; auto-complete canonical state hashing. |
| e2_run.py | v2.3 | Falsification battery: 18 critical-pair cases x 300 randomized schedules, equivocation convergence matrix, 15-mutation oracle sensitivity, 9/9 fault-injection negatives, exhaustive DFS windows (2,592 and 24 complete per-epoch film enumerations; >=60,000 gate-merge), E2a 40x2,000 cross-seed + 100,000 asserted epochs. |
| film.py | v0.1 | Portable canonical film encoding: role-named canonical bytes + SHA-256 per epoch; fixture manifest (edges, configs, rulepack hash, oid<->role binding). |
| lower_e2a.py | v0.1 | The lowering compiler: reduced-E2a clocked subsystem -> closed IC terms (Scott bools, one-hot enums, fresh-label dups); K-epoch composition; structural decoders. |
| binding_run.py | v0.1 | Parity harness: model vs ic_ref vs ic32 per-epoch films; composed single-term check; closed-form asserts both sides; mutation negatives (NEG mode, 4/4). |
| FORGE_BINDING_RESULTS.md | v0.8 | Binding ledger. Current: 3b.4 quaternion proxy PASS_REF_AND_NATIVE -- oracle per-product policy extracted+matched, drift -2.015289e-05 replicated exactly (K=20,000), live policy separator, rotation costs Q8.8 ~287k const/~306k dyn. Registry completed; dyn_mac4 promoted. Native Once LANDED+REFROZEN (proc-e2.3, 28/28); Law 6 GLOBAL. v0.9: 3b.5a Spinner+pose PASS_REF_AND_NATIVE, film v0.5. |
| fixture.py | v0.2 | Typed fixtures with EXPLICIT clock modes (periodic/once), schema validation (role uniqueness, no '__', phase<period), generator over all modes. |
| compiler.py | v0.3 | Graph-driven lowering incl. BINARY clock counters (ripple-carry inc, const-eq, mod-reset, once-latch); one-hot kept as representation for p<=32 (Law 5). |
| binding_run2.py | v0.2 | Slice-2 battery: regression + 3 hand topologies w/ closed forms + 30-fixture random sweep (6,000 epochs) + description-mutation negatives. |
| random_order.py | v0.2 | Conservative-schedule-class normalizer (scope narrowed; DUP-VAR boundary pinned executable) + reproducible composed-cost strategy report. |
| binding_run3.py | v0.1 | Slice-3a battery: t=33 horizon regression, long-horizon binary parity (thru 700 epochs), mixed-mode sweep, 5 schema negatives, cost notes. |
| binlib.py | v0.6 | Fixed-width ALU circuits (policies specified first): add/sub/ltu/eq/widen/trunc, neg/slt/saturating add-sub; counters' representation generalized. |
| binding_run3b.py | v0.3 | 3b battery: 4-bit exhaustive all ops, self-timed 8-bit, 16-bit boundaries, signed edges, ic32 spots, cost-by-input-class. |
| binding_run3c.py | v0.2 | 3b.3a/b battery: schema negatives, per-stage oracles, dynamic stages+composed qmul, wide+dynamic MAC w/ ULP separator, HARD native gate taxonomy, class/size/scheduler measurements. |
| binding_run3d.py | v0.1 | 3b.4 battery: policy extraction, model-certified drift replication, live separator, proxy trajectories const+dyn, hard native gate, transitivity verdict. |
| binding_run3e.py | v0.1 | 3b.5a battery: spinner latency/parity both widths, init teeth, multi-rotation, exclusivity+release, EV_CONFIG rotor, determinism, hard native gate. |
| E2_RESULTS.md | v2.2 | Findings ledger and status. Current: 27/27 pass. |

Run: `python3 e2_run.py` (stdlib only, ~2–3 min). Expected: `TOTAL: 27 checks, 27 pass, 0 FAIL`.

Open items: graph-driven compiler for arbitrary fixtures (slice 2); Motor8 fixed-point arithmetic on-reducer; ADMIT/claims on-reducer; cost bridge (charged steps <-> interactions); CPU/CUDA parity; stage-three settlement policy. The binding is UNBLOCKED: see FORGE_BINDING_RESULTS.md (Option A slice 1 PASS -- portable film encoding + clocked-subsystem lowering, hash-for-hash parity model vs ic_ref vs ic32).
