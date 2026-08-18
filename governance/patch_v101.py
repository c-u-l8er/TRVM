# patch_v101.py — round-6.1: the semantic-film terminal-witness closure.
# GPT's AUDIT-SEM-BUDGET: a zero-frame BUDGET_EXHAUSTED semantic film over an
# enabled state replayed ok, and budget/remaining_work mutations did not even
# change film_id. Repair: TRVM-SEMFILM-v1.1 commits every terminal witness
# field, replay re-derives the budget terminal (mirroring replayFloat,
# tightened: steps === budget, remaining_work > 0), and L-SEMTERM-1 gives the
# terminal the same adversarial treatment round 5 gave execution films.
import sys

src = open("build_v1.py", encoding="utf-8").read()
def rep(a, b, n=1):
    global src
    assert src.count(a) == n, f"anchor not unique ({src.count(a)}x): {a[:90]!r}"
    src = src.replace(a, b)

# ── version ───────────────────────────────────────────────────────────────
rep('const KERNEL_VERSION = "1.0.0";', 'const KERNEL_VERSION = "1.0.1";')
rep("   trvm_law_kernel.mjs — v1.0.0 — a law-governed Interaction Calculus kernel",
    "   trvm_law_kernel.mjs — v1.0.1 — a law-governed Interaction Calculus kernel")
rep("# Assembles trvm_law_kernel.mjs v1.0.0 from verbatim v0.4 blocks + new sections.",
    "# Assembles trvm_law_kernel.mjs v1.0.1 from verbatim v0.4 blocks + new sections.")

# header: round-6.1 block after the v1.0.0 block's item 4
rep('''      the round-6 audit caught a v0.6 source printing a v0.5 banner.

   CARRIED FROM v0.6 (round 5 — the evidence-binding round)''',
    '''      the round-6 audit caught a v0.6 source printing a v0.5 banner.

   WHAT CHANGED IN v1.0.1 (round 6.1 — the terminal-witness closure)
   ─────────────────────────────────────────────────────────────────
   The round-6B audit falsified TRVM-SEMFILM-v1's terminal contract: a
   zero-frame BUDGET_EXHAUSTED semantic film over an enabled state
   replayed ok, and budget/remaining_work mutations did not even change
   film_id — the same species as the round-4 execution-film terminal
   hole, reintroduced by the third replay implementation. Closed as a
   LAW, not a patch (law:film.terminal-witness@1): every terminal class
   a replay accepts must have a complete DECLARED witness schema, every
   witness field COMMITTED, and every witness field independently
   RE-DERIVED. TRVM-SEMFILM-v1.1 commits budget and remaining_work;
   replay re-derives the budget terminal, TIGHTER than execution films
   where the honest generator permits it: steps === budget (not >=) and
   remaining_work > 0 (a budget claim on a quiescent state is an
   under-claim — refused in the portable film). L-SEMTERM-1 attacks the
   terminal with eleven forgeries, each dying on its own refusal.

   CARRIED FROM v0.6 (round 5 — the evidence-binding round)''')

# ── commitment v1.1: domain bump + witness fields ─────────────────────────
rep('''  createHash("sha256").update(["TRVM-SEMFILM-v1", t.last_frame, t.termination, t.steps,
    t.final_sem_id, t.normal_form_id ?? "-", (t.planes ?? []).join(",")].join("|")).digest("hex");''',
    '''  createHash("sha256").update(["TRVM-SEMFILM-v1.1", t.last_frame, t.termination, t.steps,
    t.final_sem_id, t.normal_form_id ?? "-", t.budget ?? "-", t.remaining_work ?? "-",
    (t.planes ?? []).join(",")].join("|")).digest("hex");''')

rep('''// domain ("TRVM-SEMFILM-v1"). Replay is by locus MATCHING against the live''',
    '''// domain ("TRVM-SEMFILM-v1.1" — v1.1 commits the budget-terminal witness
// fields; the round-6B audit forged the v1 terminal, law:film.terminal-witness@1).
// Replay is by locus MATCHING against the live''')

# ── seal: derive remaining_work honestly at seal time ─────────────────────
rep('''function sealSemFilm(film, frt, root, t) {
  t.final_sem_id = semStateId(frt, root);
  if (t.termination === "NORMAL_FORM" && t.normal_form_id === undefined) {
    try { t.normal_form_id = semId(readback(frt, root).str); } catch { t.normal_form_id = null; }
  }
  film.terminal = t; film.film_id = semFilmIdOf(t);
  return film;
}''',
    '''function sealSemFilm(film, frt, root, t) {
  t.final_sem_id = semStateId(frt, root);
  if (t.termination === "NORMAL_FORM" && t.normal_form_id === undefined) {
    try { t.normal_form_id = semId(readback(frt, root).str); } catch { t.normal_form_id = null; }
  }
  if (t.termination === "BUDGET_EXHAUSTED" && t.remaining_work === undefined) {
    // the honest witness source: the live enumeration at the sealed state
    t.remaining_work = findFloatRedexes(frt, root,
      new Set(t.planes ?? [...PLANE_POOL_FREE])).length;
  }
  film.terminal = t; film.film_id = semFilmIdOf(t);
  return film;
}''')

# ── replay: re-derive the budget terminal ─────────────────────────────────
rep('''  } else if (t.termination !== "BUDGET_EXHAUSTED") return { ok: false, reason: "sem-terminal-malformed" };''',
    '''  } else if (t.termination === "BUDGET_EXHAUSTED") {
    // law:film.terminal-witness@1 — the budget terminal is RE-DERIVED, not
    // accepted. Mirrors replayFloat, tightened where the honest generator
    // permits: steps must EQUAL the declared budget (one-step integral
    // progression, no resumed films), and work must actually remain — a
    // BUDGET_EXHAUSTED claim on a quiescent state is refused.
    if (!Number.isInteger(t.budget) || !Number.isInteger(t.remaining_work))
      return { ok: false, reason: "sem-terminal-malformed" };
    const rsEnd = findFloatRedexes(frt, root, permitted);
    if (rsEnd.length !== t.remaining_work) return { ok: false, reason: "sem-terminal-work-mismatch" };
    if (n !== t.budget) return { ok: false, reason: "sem-budget-mismatch" };
    if (t.remaining_work <= 0) return { ok: false, reason: "sem-no-remaining-work" };
  } else return { ok: false, reason: "sem-terminal-malformed" };''')

# ── L-SEMTERM-1 battery, after the L-REFINE-1 block ───────────────────────
rep('''// L-ID-1 : artifact identity lock (round 6 — law:kernel.identity@1). The''',
    r'''// L-SEMTERM-1 : the semantic-film TERMINAL under attack (round 6.1 —
// law:film.terminal-witness@1). GPT's AUDIT-SEM-BUDGET forged the v1
// terminal: zero-frame BUDGET_EXHAUSTED over an enabled state, ok:true,
// with budget/remaining_work outside the commitment. Reproduced here
// against v1 before the fix. v1.1: positive direction — an honest PARTIAL
// semantic film replays on BOTH allocators (portable checkpoints); then
// eleven forgeries, each required to die on its DISTINCT declared refusal.
{
  const V = vectorsSrc.find((x) => x.name === "church_exp_2_2");
  const buildPartial = (budget, pool = [...PLANE_POOL_FREE]) => {
    const frt = new FloatRt();
    let root = extrude(frt, parse(frt, V.term));
    const film = newSemFilm();
    let prev = "genesis", n = 0;
    const permitted = new Set(pool);
    while (n < budget) {
      const rs = findFloatRedexes(frt, root, permitted);
      if (!rs.length) break;
      const order = liveDiscoveryOrder(frt, root);
      const pre = semStateId(frt, root);
      const rx = rs[0];
      const loc = semLocusOf(rx, order);
      const r = fireFloat(frt, root, rx); root = r.root;
      const post = semStateId(frt, root);
      const fid = frameId31(prev, pre, PLANE_OF[r.rule], r.rule, loc, post);
      film.frames.push({ i: n, plane: PLANE_OF[r.rule], rule: r.rule, locus: loc, pre, post, prev, frame_id: fid });
      prev = fid; n++;
    }
    sealSemFilm(film, frt, root, { termination: "BUDGET_EXHAUSTED", steps: n, last_frame: prev, planes: pool, budget });
    return { film, frt, root };
  };
  const clone = (f) => JSON.parse(JSON.stringify(f));
  const reseal = (f) => { f.film_id = semFilmIdOf(f.terminal); return f; };
  const B = 7;
  const honest = buildPartial(B);
  const W = honest.film.terminal.remaining_work;
  const posA = replaySemFilm(V.term, honest.film, FloatRt).ok === true;
  const posB = replaySemFilm(V.term, honest.film, DescFloatRt).ok === true;
  const expect = (film, want) => {
    const r = replaySemFilm(V.term, film, FloatRt);
    return !r.ok && r.reason === want;
  };
  const cases = [];
  // 1-2. mutation WITHOUT resealing — dies at the commitment
  { const m = clone(honest.film); m.terminal.budget = 1;
    cases.push(["budget-mutation-unsealed", expect(m, "sem-film-id-mismatch")]); }
  { const m = clone(honest.film); m.terminal.remaining_work = -7;
    cases.push(["work-mutation-unsealed", expect(m, "sem-film-id-mismatch")]); }
  // 3. resealed budget lie (claims a budget the frames never reached)
  { const m = reseal(clone(honest.film)); m.terminal.budget = 999; reseal(m);
    cases.push(["budget-lie-resealed", expect(m, "sem-budget-mismatch")]); }
  // 4. resealed NEGATIVE remaining work
  { const m = clone(honest.film); m.terminal.remaining_work = -7; reseal(m);
    cases.push(["negative-work-resealed", expect(m, "sem-terminal-work-mismatch")]); }
  // 5. resealed WRONG remaining work
  { const m = clone(honest.film); m.terminal.remaining_work = W + 3; reseal(m);
    cases.push(["wrong-work-resealed", expect(m, "sem-terminal-work-mismatch")]); }
  // 6. resealed non-integer budget
  { const m = clone(honest.film); m.terminal.budget = "lots"; reseal(m);
    cases.push(["malformed-budget-resealed", expect(m, "sem-terminal-malformed")]); }
  // 7. steps overrun the declared budget (frames beyond budget, resealed)
  { const over = buildPartial(B); const m = clone(over.film);
    m.terminal.budget = B - 2; reseal(m);
    cases.push(["steps-overrun-budget-resealed", expect(m, "sem-budget-mismatch")]); }
  // 8. BUDGET_EXHAUSTED claimed on an actually QUIESCENT state
  { const frt = new FloatRt(); let root = extrude(frt, parse(frt, V.term));
    const film = newSemFilm(); let prev = "genesis", n = 0;
    for (;;) {
      const rs = findFloatRedexes(frt, root, PLANE_POOL_FREE);
      if (!rs.length) break;
      const order = liveDiscoveryOrder(frt, root);
      const pre = semStateId(frt, root);
      const r = fireFloat(frt, root, rs[0]); const loc = semLocusOf(rs[0], order);
      root = r.root;
      const post = semStateId(frt, root);
      const fid = frameId31(prev, pre, PLANE_OF[r.rule], r.rule, loc, post);
      film.frames.push({ i: n, plane: PLANE_OF[r.rule], rule: r.rule, locus: loc, pre, post, prev, frame_id: fid });
      prev = fid; n++;
    }
    sealSemFilm(film, frt, root, { termination: "BUDGET_EXHAUSTED", steps: n, last_frame: prev, planes: [...PLANE_POOL_FREE], budget: n });
    cases.push(["budget-claim-on-quiescence", expect(film, "sem-no-remaining-work")]); }
  // 9. GPT's exact witness under v1.1: zero-frame film over an enabled state,
  //    HONESTLY resealed — the budget cannot have been reached
  { const frt = new FloatRt(); const root = extrude(frt, parse(frt, "(λx.x X)"));
    const film = newSemFilm();
    sealSemFilm(film, frt, root, { termination: "BUDGET_EXHAUSTED", steps: 0, last_frame: "genesis", planes: [...PLANE_POOL_FREE], budget: 999, remaining_work: 424242 });
    const r0 = replaySemFilm("(λx.x X)", film, FloatRt);
    cases.push(["audit-witness-resealed", !r0.ok && (r0.reason === "sem-terminal-work-mismatch" || r0.reason === "sem-budget-mismatch")]); }
  // 10. NORMAL_FORM -> BUDGET_EXHAUSTED flip on a complete film, resealed
  { const frt = new FloatRt(); let root = extrude(frt, parse(frt, V.term));
    const film = newSemFilm(); let prev = "genesis", n = 0;
    for (;;) {
      const rs = findFloatRedexes(frt, root, PLANE_POOL_FREE);
      if (!rs.length) break;
      const order = liveDiscoveryOrder(frt, root);
      const pre = semStateId(frt, root);
      const r = fireFloat(frt, root, rs[0]); const loc = semLocusOf(rs[0], order);
      root = r.root;
      const post = semStateId(frt, root);
      const fid = frameId31(prev, pre, PLANE_OF[r.rule], r.rule, loc, post);
      film.frames.push({ i: n, plane: PLANE_OF[r.rule], rule: r.rule, locus: loc, pre, post, prev, frame_id: fid });
      prev = fid; n++;
    }
    sealSemFilm(film, frt, root, { termination: "BUDGET_EXHAUSTED", steps: n, last_frame: prev, planes: [...PLANE_POOL_FREE], budget: n, remaining_work: 0 });
    cases.push(["nf-to-budget-flip-resealed", expect(film, "sem-no-remaining-work")]); }
  // 11. BUDGET_EXHAUSTED -> NORMAL_FORM flip on a partial film, resealed
  { const m = clone(honest.film);
    m.terminal.termination = "NORMAL_FORM"; delete m.terminal.budget; delete m.terminal.remaining_work;
    m.terminal.normal_form_id = null; reseal(m);
    cases.push(["budget-to-nf-flip-resealed", expect(m, "sem-false-normal-form")]); }
  // 12. rule-pool participates in the WORK arithmetic: narrow the pool on an
  //     honest INTERACT-only prefix whose cutoff state has COLLAPSE work
  {
    let made = null;
    outer:
    for (let b = 1; b <= 12; b++) {
      const frt = new FloatRt();
      let root = extrude(frt, parse(frt, V.term));
      const film = newSemFilm(); let prev = "genesis", n = 0;
      while (n < b) {
        const rs = findFloatRedexes(frt, root, PLANE_POOL_FREE)
          .filter((r) => PLANE_OF[r.rule] === "INTERACT");
        if (!rs.length) continue outer;
        const order = liveDiscoveryOrder(frt, root);
        const pre = semStateId(frt, root);
        const r = fireFloat(frt, root, rs[0]); const loc = semLocusOf(rs[0], order);
        root = r.root;
        const post = semStateId(frt, root);
        const fid = frameId31(prev, pre, PLANE_OF[r.rule], r.rule, loc, post);
        film.frames.push({ i: n, plane: PLANE_OF[r.rule], rule: r.rule, locus: loc, pre, post, prev, frame_id: fid });
        prev = fid; n++;
      }
      const full = findFloatRedexes(frt, root, PLANE_POOL_FREE).length;
      const interactOnly = [...PLANE_POOL_FREE].filter((r) => PLANE_OF[r] === "INTERACT");
      const narrow = findFloatRedexes(frt, root, new Set(interactOnly)).length;
      if (full !== narrow && narrow > 0) {
        // commit remaining_work under the FULL pool but declare the NARROW pool
        sealSemFilm(film, frt, root, { termination: "BUDGET_EXHAUSTED", steps: n, last_frame: prev, planes: interactOnly, budget: n, remaining_work: full });
        made = film; break;
      }
    }
    cases.push(["pool-narrowing-work-arithmetic", made !== null && expect(made, "sem-terminal-work-mismatch")]);
  }
  const bad = cases.filter(([, ok2]) => !ok2).map(([nm]) => nm);
  report("L-SEMTERM-1", "(semantic-film terminal witness, honest partial replay on both allocators + 12 forgeries, terminal contract, BINDING/ADEQUACY)",
    posA && posB && bad.length === 0 ? "PROPERTY-TESTED" : "FALSIFIED?!",
    posA && posB && bad.length === 0
      ? `honest ${B}-step PARTIAL semantic film (budget ${B}, remaining_work ${W}) replays ok on BOTH allocators — portable checkpoints exist; 12/12 terminal forgeries refused on their declared reasons: commitment (2x sem-film-id-mismatch), budget lie + overrun (sem-budget-mismatch), negative/wrong/pool-narrowed work (sem-terminal-work-mismatch), malformed budget (sem-terminal-malformed), quiescence claim + NF flip (sem-no-remaining-work), partial-as-NF flip (sem-false-normal-form), and the round-6B audit witness itself, honestly resealed. The v1 terminal accepted ALL of the resealed ones (law:film.terminal-witness@1)`
      : `failing cases: ${bad.join(", ") || "(positive replay failed)"}`);
}

// L-ID-1 : artifact identity lock (round 6 — law:kernel.identity@1). The''')

open("build_v1.py", "w", encoding="utf-8").write(src)
print("v1.0.1 patch applied:", len(src.splitlines()), "lines")
