// well-formedness (CLOSURE): grammar respected after every step
function wellFormed(rt, root) {
  const seen = new Set(); const st = [root];
  while (st.length) {
    const r = chase(rt, st.pop());
    if (seen.has(r)) continue; seen.add(r);
    switch (r.t) {
      case "Var": if (!(isFree(r.nam) || Number.isInteger(r.nam))) return false; break;
      case "Era": break;
      case "Lam": if (!Number.isInteger(r.nam)) return false; st.push(r.bod); break;
      case "App": st.push(r.fun, r.arg); break;
      case "Sup": if (!Number.isInteger(r.lab)) return false; st.push(r.lft, r.rgt); break;
      case "Dup": if (!(Number.isInteger(r.lft) && Number.isInteger(r.rgt))) return false; st.push(r.val, r.bod); break;
      default: return false;
    }
  }
  return true;
}

// ── embedded conformance vectors (docs/spec/conformance/vectors) ──────────
const EMBEDDED_VECTORS = [{"name": "identity", "term": "\u03bbx.x", "nf": "\u03bba.a", "ref_interactions": 0}, {"name": "K_true", "term": "\u03bba.\u03bbb.a", "nf": "\u03bba.\u03bbb.a", "ref_interactions": 0}, {"name": "K_false", "term": "\u03bba.\u03bbb.b", "nf": "\u03bba.\u03bbb.b", "ref_interactions": 0}, {"name": "apply_id", "term": "(\u03bbx.\u03bbt.(t x) \u03bby.y)", "nf": "\u03bba.(a \u03bbb.b)", "ref_interactions": 1}, {"name": "not_true", "term": "(\u03bbb.\u03bbt.\u03bbf.((b f) t) \u03bbT.\u03bbF.T)", "nf": "\u03bba.\u03bbb.b", "ref_interactions": 3}, {"name": "dup_pair", "term": "!{a,b} = {\u03bbx.x,\u03bby.y}; (a b)", "nf": "\u03bba.a", "ref_interactions": 2}, {"name": "sup_app", "term": "({\u03bbx.x,\u03bby.y} \u03bbz.z)", "nf": "&0{\u03bba.a,\u03bbb.b}", "ref_interactions": 5}, {"name": "church_not_2", "term": "((\u03bbf.\u03bbx.!{f0,f1}=f;(f0 (f1 x)) \u03bbB.\u03bbT.\u03bbF.((B F) T)) \u03bba.\u03bbb.a)", "nf": "\u03bba.\u03bbb.a", "ref_interactions": 16}, {"name": "church_apply_0", "term": "((\u03bbf.\u03bbx.x S) Z)", "nf": "Z", "ref_interactions": 2}, {"name": "church_apply_1", "term": "((\u03bbf.\u03bbx.(f x) S) Z)", "nf": "(S Z)", "ref_interactions": 2}, {"name": "church_apply_2", "term": "((\u03bbf.\u03bbx.!&1001{c0,c1}=f;(c0 (c1 x)) S) Z)", "nf": "(S (S Z))", "ref_interactions": 3}, {"name": "church_apply_3", "term": "((\u03bbf.\u03bbx.!&1002{c0,t0}=f;!&1003{c1,c2}=t0;(c0 (c1 (c2 x))) S) Z)", "nf": "(S (S (S Z)))", "ref_interactions": 4}, {"name": "church_apply_4", "term": "((\u03bbf.\u03bbx.!&1004{c0,t0}=f;!&1005{c1,t1}=t0;!&1006{c2,c3}=t1;(c0 (c1 (c2 (c3 x)))) S) Z)", "nf": "(S (S (S (S Z))))", "ref_interactions": 5}, {"name": "church_apply_5", "term": "((\u03bbf.\u03bbx.!&1007{c0,t0}=f;!&1008{c1,t1}=t0;!&1009{c2,t2}=t1;!&1010{c3,c4}=t2;(c0 (c1 (c2 (c3 (c4 x))))) S) Z)", "nf": "(S (S (S (S (S Z)))))", "ref_interactions": 6}, {"name": "church_apply_6", "term": "((\u03bbf.\u03bbx.!&1011{c0,t0}=f;!&1012{c1,t1}=t0;!&1013{c2,t2}=t1;!&1014{c3,t3}=t2;!&1015{c4,c5}=t3;(c0 (c1 (c2 (c3 (c4 (c5 x)))))) S) Z)", "nf": "(S (S (S (S (S (S Z))))))", "ref_interactions": 7}, {"name": "church_exp_2_2", "term": "((\u03bbf.\u03bbx.!&1001{c0,c1}=f;(c0 (c1 x)) \u03bbf.\u03bbx.!&1002{c0,c1}=f;(c0 (c1 x))) S)", "nf": "\u03bba.(S (S (S (S a))))", "ref_interactions": 21}, {"name": "church_exp_3_2", "term": "((\u03bbf.\u03bbx.!&1001{c0,t0}=f;!&1002{c1,c2}=t0;(c0 (c1 (c2 x))) \u03bbf.\u03bbx.!&1003{c0,c1}=f;(c0 (c1 x))) S)", "nf": "\u03bba.(S (S (S (S (S (S (S (S a))))))))", "ref_interactions": 42}, {"name": "church_exp_2_3", "term": "((\u03bbf.\u03bbx.!&1001{c0,c1}=f;(c0 (c1 x)) \u03bbf.\u03bbx.!&1002{c0,t0}=f;!&1003{c1,c2}=t0;(c0 (c1 (c2 x)))) S)", "nf": "\u03bba.(S (S (S (S (S (S (S (S (S a)))))))))", "ref_interactions": 36}, {"name": "church_exp_3_3", "term": "((\u03bbf.\u03bbx.!&1001{c0,t0}=f;!&1002{c1,c2}=t0;(c0 (c1 (c2 x))) \u03bbf.\u03bbx.!&1003{c0,t0}=f;!&1004{c1,c2}=t0;(c0 (c1 (c2 x)))) S)", "nf": "\u03bba.(S (S (S (S (S (S (S (S (S (S (S (S (S (S (S (S (S (S (S (S (S (S (S (S (S (S (S a)))))))))))))))))))))))))))", "ref_interactions": 91}, {"name": "church_exp_4_2", "term": "((\u03bbf.\u03bbx.!&1001{c0,t0}=f;!&1002{c1,t1}=t0;!&1003{c2,c3}=t1;(c0 (c1 (c2 (c3 x)))) \u03bbf.\u03bbx.!&1004{c0,c1}=f;(c0 (c1 x))) S)", "nf": "\u03bba.(S (S (S (S (S (S (S (S (S (S (S (S (S (S (S (S a))))))))))))))))", "ref_interactions": 71}, {"name": "church_exp_2_4", "term": "((\u03bbf.\u03bbx.!&1001{c0,c1}=f;(c0 (c1 x)) \u03bbf.\u03bbx.!&1002{c0,t0}=f;!&1003{c1,t1}=t0;!&1004{c2,c3}=t1;(c0 (c1 (c2 (c3 x))))) S)", "nf": "\u03bba.(S (S (S (S (S (S (S (S (S (S (S (S (S (S (S (S a))))))))))))))))", "ref_interactions": 55}, {"name": "church_not_parity_2", "term": "(((\u03bbf.\u03bbx.!&1001{c0,c1}=f;(c0 (c1 x)) \u03bbp.\u03bbt.\u03bbf.((p f) t)) \u03bba.\u03bbb.a) X)", "nf": "\u03bba.X", "ref_interactions": 17}, {"name": "church_not_parity_3", "term": "(((\u03bbf.\u03bbx.!&1001{c0,t0}=f;!&1002{c1,c2}=t0;(c0 (c1 (c2 x))) \u03bbp.\u03bbt.\u03bbf.((p f) t)) \u03bba.\u03bbb.a) X)", "nf": "\u03bba.a", "ref_interactions": 28}, {"name": "church_not_parity_4", "term": "(((\u03bbf.\u03bbx.!&1001{c0,t0}=f;!&1002{c1,t1}=t0;!&1003{c2,c3}=t1;(c0 (c1 (c2 (c3 x)))) \u03bbp.\u03bbt.\u03bbf.((p f) t)) \u03bba.\u03bbb.a) X)", "nf": "\u03bba.X", "ref_interactions": 39}];

// ── random closed-ish term generator (termination-biased) ─────────────────
function genTerm(rt, rnd, depth, bound, labCounter, used = new Set()) {
  const r = rnd();
  if (depth <= 0 || r < 0.22) {
    const avail = bound.filter((n) => !used.has(n));       // AFFINE: each binder used at most once
    if (avail.length && rnd() < 0.7) {
      const pick = avail[Math.floor(rnd() * avail.length)];
      used.add(pick); return Var(pick);
    }
    return Var("free:" + "SZX"[Math.floor(rnd() * 3)]);
  }
  if (r < 0.44) {                                   // Lam
    const u = rt.fresh();
    return Lam(u, genTerm(rt, rnd, depth - 1, bound.concat(u), labCounter, used));
  }
  if (r < 0.70) {                                   // App
    return App(genTerm(rt, rnd, depth - 1, bound, labCounter, used),
               genTerm(rt, rnd, depth - 1, bound, labCounter, used));
  }
  if (r < 0.85) {                                   // Sup
    return Sup(labCounter.n++,
      genTerm(rt, rnd, depth - 1, bound, labCounter, used),
      genTerm(rt, rnd, depth - 1, bound, labCounter, used));
  }
  const a = rt.fresh(), b = rt.fresh();             // Dup
  return Dup(labCounter.n++, a, b,
    genTerm(rt, rnd, depth - 1, bound, labCounter, used),
    genTerm(rt, rnd, depth - 2, bound.concat(a, b), labCounter, used));
}
