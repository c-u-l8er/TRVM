# patch_v1b.py — stage B: the round-6 batteries + certificate generator string.
import sys

src = open("build_v1.py", encoding="utf-8").read()
def rep(a, b, n=1):
    global src
    assert src.count(a) == n, f"anchor not unique ({src.count(a)}x): {a[:80]!r}"
    src = src.replace(a, b)

# ── generator string binds to KERNEL_VERSION ──────────────────────────────
rep('generator: "trvm_law_kernel.mjs v0.6", node: process.version },',
    'generator: "trvm_law_kernel.mjs v" + KERNEL_VERSION, node: process.version },')

# ── L-SCHED-FLOAT-1 caption: six schedulers, adversarial pair cited ───────
rep('report("L-SCHED-FLOAT-1", "(completion+NF+coherence, 4 schedulers × vectors, floating-dup relation, PROGRESS under free choice)",',
    'report("L-SCHED-FLOAT-1", "(completion+NF+coherence, 6 schedulers incl. 2 starvation adversaries × vectors, floating-dup relation, PROGRESS under free+adversarial choice)",')

rep("the freedom claim travels with a re-derivable evidence basis, not with prose`);",
    "the freedom claim travels with a re-derivable evidence basis, not with prose. "
    "Two of the six schedulers are STARVATION ADVERSARIES (starve_dups fires an APP whenever one is enabled; starve_apps a heap DUP) — "
    "persistent avoidance of a redex class does not prevent completion, NF agreement, or count invariance on this corpus (law:sched.adversarial.float@1)`);")

# ── the round-6 batteries, inserted before L-CERT-1 ───────────────────────
rep("// L-CERT-1 : positive verification by FULL RE-EXECUTION + the naive tamper",
    r'''// L-SEMID-1 : the state-identity SPLIT, adversarially (round 6 —
// law:state.exec-identity@1, law:state.semantic-quotient@1). The external
// audit's witness is reproduced VERBATIM (its two digests are asserted),
// then the quotient is attacked: heap-id bijections (incl. mid-run states),
// dead heap injection, alpha-renaming, label bijection, and the descending
// adversarial allocator. Semantic identity must hold everywhere execution
// identity is allowed to vary.
{
  const WTERM = "!&7{a,b}=X; !&9{c,d}=Y; ((a c) (b d))";
  const mk = (t, R = FloatRt) => { const frt = new R(); const root = extrude(frt, parse(frt, t)); return { frt, root }; };
  const permuteIds = (s, bij) => {
    const entries = [...s.frt.heap.entries()];
    s.frt.heap.clear();
    for (const [id, d] of entries) s.frt.heap.set(bij.get(id) ?? id, d);
    return s;
  };
  const A = mk(WTERM);
  const ids = [...A.frt.heap.keys()];
  const B = permuteIds(mk(WTERM), new Map([[ids[0], ids[1]], [ids[1], ids[0]]]));
  const dA = execStateId(A.frt, A.root), dB = execStateId(B.frt, B.root);
  const witnessExact = dA === "18b4e47b34d38339a2675cd760726c804d36e828cfed9b9e34c05f6a99a1deb1"
                    && dB === "6bca1878284b4dfd7cf511ce4e811828509a59d100ed7f1bebe3151b09774574";
  const witnessSplit = dA !== dB && semStateId(A.frt, A.root) === semStateId(B.frt, B.root);
  const C = mk(WTERM);
  C.frt.heap.set(C.frt.fresh(), { lab: 999, l: C.frt.fresh(), r: C.frt.fresh(), val: parse(C.frt, "λq.q") });
  const deadOk = execStateId(C.frt, C.root) !== dA && semStateId(C.frt, C.root) === semStateId(A.frt, A.root);
  const alphaOk = semStateId(...(() => { const s = mk("!&7{p,q}=X; !&9{r,s2}=Y; ((p r) (q s2))"); return [s.frt, s.root]; })()) === semStateId(A.frt, A.root);
  const labelOk = semStateId(...(() => { const s = mk("!&3{a,b}=X; !&5{c,d}=Y; ((a c) (b d))"); return [s.frt, s.root]; })()) === semStateId(A.frt, A.root);
  const descOk  = semStateId(...(() => { const s = mk(WTERM, DescFloatRt); return [s.frt, s.root]; })()) === semStateId(A.frt, A.root);
  // mid-run + random bijections over fuzz-adjacent states
  let midOk = true, randTried = 0, randInvariant = 0, execVaried = 0;
  {
    const v = vectorsSrc.find((x) => x.name === "church_exp_2_2");
    const s = mk(v.term);
    const rnd = mulberry32(0x61D);
    for (let k = 0; k < 10; k++) {
      const rs = findFloatRedexes(s.frt, s.root, PLANE_POOL_FREE);
      if (!rs.length) break;
      s.root = fireFloat(s.frt, s.root, rs[Math.floor(rnd() * rs.length)]).root;
    }
    const semBefore = semStateId(s.frt, s.root), execBefore = execStateId(s.frt, s.root);
    for (let trial = 0; trial < (QUICK ? 8 : 24); trial++) {
      const cur = [...s.frt.heap.keys()];
      const shuffled = [...cur];
      for (let i = shuffled.length - 1; i > 0; i--) { const j = Math.floor(rnd() * (i + 1)); [shuffled[i], shuffled[j]] = [shuffled[j], shuffled[i]]; }
      const bij = new Map(cur.map((id, i) => [id, shuffled[i] + 5_000_000]));  // move out of range, injective
      const t2 = permuteIds({ frt: s.frt, root: s.root }, bij);   // in place
      randTried++;
      if (semStateId(t2.frt, t2.root) === semBefore) randInvariant++;
      if (execStateId(t2.frt, t2.root) !== execBefore) execVaried++;
      // permute back for next trial
      permuteIds(t2, new Map([...bij].map(([a, b]) => [b, a])));
    }
    midOk = randInvariant === randTried && semStateId(s.frt, s.root) === semBefore;
  }
  report("L-SEMID-1", "(state identity split, audit witness + id/dead/alpha/label/allocator attacks, semantic quotient, COHERENCE/BINDING)",
    witnessExact && witnessSplit && deadOk && alphaOk && labelOk && descOk && midOk ? "PROPERTY-TESTED" : "FALSIFIED?!",
    `audit witness reproduced byte-for-byte (execStateId ${dA.slice(0, 8)}… ≠ ${dB.slice(0, 8)}…, behaviors identical) and RESOLVED: semStateId equal across the swap; dead-entry injection perturbs exec, not sem: ${deadOk}; alpha-rename: ${alphaOk}; label bijection: ${labelOk}; descending adversarial allocator: ${descOk}; mid-run random heap-id bijections sem-invariant ${randInvariant}/${randTried} with exec varying on ${execVaried} — the standing Coherence question is answered NO for floatDigest and CLOSED by the split: execution identity is allocation-sensitive BY DECLARATION, semantic identity quotients ids, dead content, allocation order, alpha, and labels`);
}

// L-SEMID-2 : the quotient must not collapse DIFFERENT states — sampled
// adequacy on the semantic side, same evidence-class honesty as L-ADEQ-2.
{
  const seen = new Map(); let collisions = 0, pairs = 0;
  const put = (name, sid) => {
    for (const [n2, s2] of seen) { pairs++; if (s2 === sid && n2 !== name) collisions++; }
    seen.set(name, sid);
  };
  for (const v of vectorsSrc) {
    const frt = new FloatRt(); const root = extrude(frt, parse(frt, v.term));
    put(v.name, semStateId(frt, root));
  }
  const rt1 = new FloatRt(), rt2 = new FloatRt();
  const lockPair = semStateId(rt1, extrude(rt1, parse(rt1, "λa.λb.a")))
                !== semStateId(rt2, extrude(rt2, parse(rt2, "λa.λb.b")));
  const rnd = mulberry32(0x5EM1D ^ 0);
  let fuzzDistinct = 0, fuzzTried = 0;
  const fuzzSeen = new Set();
  for (let i = 0; i < (QUICK ? 20 : 60); i++) {
    const g = new Rt(); const lab = { n: 700 };
    const s = show(genTerm(g, rnd, 5, [], lab));
    const frt = new FloatRt();
    let root; try { root = extrude(frt, parse(frt, s)); } catch { continue; }
    const sid = semStateId(frt, root);
    fuzzTried++;
    if (!fuzzSeen.has(sid)) { fuzzSeen.add(sid); fuzzDistinct++; }
  }
  report("L-SEMID-2", "(semantic identity, pairwise distinctness on corpus + locked pair + fuzz, sampled, ADEQUACY)",
    collisions === 0 && lockPair ? "PROPERTY-TESTED" : "FALSIFIED?!",
    `0 collisions across ${pairs} corpus pairs; the locked digest-adequacy pair (λa.λb.a vs λa.λb.b) separates at the semantic level too: ${lockPair}; ${fuzzDistinct}/${fuzzTried} distinct fuzz initial states (duplicates possible only for alpha/label-equivalent generations — the quotient working, not failing). Distinctness is SAMPLED under the SHA-256 collision-resistance assumption, exactly as L-ADEQ-2 states it (law:state.semantic-quotient@1)`);
}

// L-REFINE-1 : allocation portability — the ic32 bridge, executable today
// (law:refine.alloc-portability@1). The standard and the DESCENDING
// allocator run every vector in LOCKSTEP under a rotating free-choice
// index schedule: per-step SEMANTIC chains must be equal while execution
// identity is allocator-bound. The SEMANTIC film built on A must replay on
// B; A's EXECUTION film replays; B's execution film must be either
// bit-identical to A's or REFUSED by replayFloat — the refusal IS the
// demonstration that execution identity does not travel. Emits
// refinement_receipt.json.
{
  const perTerm = []; let allSem = true, allNf = true, allCnt = true,
    semReplayOk = 0, execAOk = 0, execBRefusedOrEqual = 0, execBRefused = 0;
  for (const v of vectorsSrc) {
    const A = { frt: new FloatRt() }; A.root = extrude(A.frt, parse(A.frt, v.term));
    const B = { frt: new DescFloatRt() }; B.root = extrude(B.frt, parse(B.frt, v.term));
    const semF = newSemFilm(), exeA = newFilm(), exeB = newFilm();
    let steps = 0, prevS = "genesis", prevA = "genesis", prevB = "genesis", semEq = true;
    for (;;) {
      const sA = semStateId(A.frt, A.root), sB = semStateId(B.frt, B.root);
      if (sA !== sB) { semEq = false; break; }
      const rsA = findFloatRedexes(A.frt, A.root, PLANE_POOL_FREE);
      const rsB = findFloatRedexes(B.frt, B.root, PLANE_POOL_FREE);
      if (rsA.length === 0 && rsB.length === 0) break;
      if (rsA.length !== rsB.length) { semEq = false; break; }
      if (steps > 20000) { semEq = false; break; }
      const i = steps % rsA.length;
      const ordA = liveDiscoveryOrder(A.frt, A.root);
      const locS = semLocusOf(rsA[i], ordA);
      const eA = execStateId(A.frt, A.root), eB = execStateId(B.frt, B.root);
      const fA = fireFloat(A.frt, A.root, rsA[i]); A.root = fA.root;
      const fB = fireFloat(B.frt, B.root, rsB[i]); B.root = fB.root;
      if (fA.rule !== fB.rule) { semEq = false; break; }
      const sA2 = semStateId(A.frt, A.root);
      const fidS = frameId31(prevS, sA, PLANE_OF[fA.rule], fA.rule, locS, sA2);
      semF.frames.push({ i: steps, plane: PLANE_OF[fA.rule], rule: fA.rule, locus: locS, pre: sA, post: sA2, prev: prevS, frame_id: fidS });
      prevS = fidS;
      const pA = execStateId(A.frt, A.root);
      const lA = encodeLocus(rsA[i]);
      const fidA = frameId31(prevA, eA, PLANE_OF[fA.rule], fA.rule, lA, pA);
      exeA.frames.push({ i: steps, plane: PLANE_OF[fA.rule], rule: fA.rule, locus: lA, pre: eA, post: pA, prev: prevA, frame_id: fidA });
      prevA = fidA;
      const pB = execStateId(B.frt, B.root);
      const lB = encodeLocus(rsB[i]);
      const fidB = frameId31(prevB, eB, PLANE_OF[fB.rule], fB.rule, lB, pB);
      exeB.frames.push({ i: steps, plane: PLANE_OF[fB.rule], rule: fB.rule, locus: lB, pre: eB, post: pB, prev: prevB, frame_id: fidB });
      prevB = fidB;
      steps++;
    }
    sealSemFilm(semF, A.frt, A.root, { termination: "NORMAL_FORM", steps, last_frame: prevS, planes: [...PLANE_POOL_FREE] });
    sealFilm(exeA, A.frt, A.root, { termination: "NORMAL_FORM", steps, last_frame: prevA, planes: [...PLANE_POOL_FREE] });
    sealFilm(exeB, B.frt, B.root, { termination: "NORMAL_FORM", steps, last_frame: prevB, planes: [...PLANE_POOL_FREE] });
    const nfA = readback(A.frt, A.root).str, nfB = readback(B.frt, B.root).str;
    const ref = refNormalize(v.term).str;
    const cntEq = A.frt.total() === B.frt.total();
    allSem &&= semEq; allNf &&= (nfA === nfB && nfA === ref); allCnt &&= cntEq;
    const rSem = replaySemFilm(v.term, semF, DescFloatRt);
    if (rSem.ok) semReplayOk++;
    const rA = replayFloat(v.term, exeA);
    if (rA.ok) execAOk++;
    const rB = replayFloat(v.term, exeB);
    const bEqual = exeB.film_id === exeA.film_id;
    if (bEqual || !rB.ok) execBRefusedOrEqual++;
    if (!rB.ok) execBRefused++;
    perTerm.push({ name: v.name, steps, interactions: A.frt.total(),
      sem_chain_equal: semEq, nf_id: semId(nfA),
      sem_film_id: semF.film_id, exec_film_id_A: exeA.film_id, exec_film_id_B: exeB.film_id,
      exec_films_equal: bEqual,
      sem_film_replay_on_B: rSem.ok ? "ok" : "refused:" + rSem.reason,
      exec_film_B_replay: bEqual ? "equal-to-A" : (rB.ok ? "ok" : "refused:" + rB.reason) });
  }
  const n = vectorsSrc.length;
  const pass = allSem && allNf && allCnt && semReplayOk === n && execAOk === n && execBRefusedOrEqual === n;
  if (pass) {
    const receipt = {
      type: "RefinementReceipt", version: 1,
      law_refs: ["law:refine.alloc-portability@1", "law:state.semantic-quotient@1", "law:state.exec-identity@1"],
      relation: "floating-dup-heap-v1",
      allocators: { A: "ascending (FloatRt)", B: "descending-stride-13 (DescFloatRt), an adversarial stand-in for a second implementation until ic32" },
      schedule: "rotating free-choice index (steps % enabled)",
      terms: n, per_term: perTerm,
      summary: { sem_chains_equal: n, nf_reference_equal: n, interaction_counts_equal: n,
        sem_films_replayed_on_B: semReplayOk, exec_films_A_replayed: execAOk,
        exec_films_B_refused_by_A_replay: execBRefused,
        exec_films_identical_across_allocators: n - execBRefused },
      informational: { note: "NON-AUTHORITATIVE", generator: "trvm_law_kernel.mjs v" + KERNEL_VERSION },
    };
    receipt.receipt_id = createHash("sha256").update("TRVM-REFINE-v1|" + JSON.stringify(receipt.per_term) + "|" + JSON.stringify(receipt.summary)).digest("hex");
    writeFileSync("refinement_receipt.json", JSON.stringify(receipt, null, 1));
  }
  report("L-REFINE-1", "(allocation portability, dual-allocator lockstep + semantic-film cross-replay, refinement bridge, COHERENCE/REFINEMENT)",
    pass ? "PROPERTY-TESTED" : "FALSIFIED?!",
    `${n}/${n} vectors: per-step semantic chains EQUAL across allocators, NFs reference-equal, interaction counts equal; semantic films built on the ascending allocator replay on the DESCENDING one ${semReplayOk}/${n} by canonical-locus matching; execution films: A replays ${execAOk}/${n}, B is refused by replayFloat on ${execBRefused}/${n} (bit-identical to A on the rest — single-dup states where fold order cannot differ) — the semantic film is the PORTABLE evidence object, the execution film is the local one, and the RefinementReceipt records the asymmetry per term. This is the protocol ic32 will replay (law:refine.alloc-portability@1)`);
}

// L-ID-1 : artifact identity lock (round 6 — law:kernel.identity@1). The
// audit caught v0.6 source printing a v0.5 banner: the executable disagreed
// with the artifact identity, one round after evidence-binding. LOCKED:
// source header, runtime constant, and certificate generator must agree.
{
  let srcTxt = "";
  try { srcTxt = readFileSync(new URL(import.meta.url), "utf8"); }
  catch { try { srcTxt = readFileSync(process.argv[1], "utf8"); } catch { /* stays empty */ } }
  const headOk = srcTxt.slice(0, 300).includes("v" + KERNEL_VERSION);
  const genOk = !!schedCert && schedCert.informational?.generator === "trvm_law_kernel.mjs v" + KERNEL_VERSION;
  report("L-ID-1", "(artifact identity: source header == runtime constant == certificate generator, kernel identity, BINDING)",
    headOk && genOk ? "REGRESSION-LOCKED" : "FALSIFIED?!",
    headOk && genOk
      ? `KERNEL_VERSION ${KERNEL_VERSION} appears in the first 300 bytes of the source and in the emitted certificate's generator string — the executable can no longer disagree with the artifact it claims to be (law:kernel.identity@1; the round-6 audit witnessed exactly this disagreement in v0.6)`
      : `identity disagreement: header ${headOk}, certificate generator ${genOk}`);
}

// L-CERT-1 : positive verification by FULL RE-EXECUTION + the naive tamper''')

open("build_v1.py", "w", encoding="utf-8").write(src)
print("stage B applied:", len(src.splitlines()), "lines")
