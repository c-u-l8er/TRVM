function redexRule(rt, node) {
  if (node.t === "App") {
    const f = chase(rt, node.fun);
    if (f.t === "Lam") return "APP-LAM";
    if (f.t === "Sup") return "APP-SUP";
    if (f.t === "Era") return "APP-ERA";
    return null;
  }
  if (node.t === "Dup") {
    const v = chase(rt, node.val);
    if (v.t === "Lam") return "DUP-LAM";
    if (v.t === "Sup") return v.lab === node.lab ? "DUP-SUP=" : "DUP-SUP!";
    if (v.t === "Era") return "DUP-ERA";
    // SCHEDULER-SAFETY GATE — independently rediscovered here, then found
    // already enforced in forge/random_order.py, and matching upstream IC,
    // where DUP-VAR/DUP-APP live under the separate Collapsing extension.
    // Reading: INTERACT and COLLAPSE are different semantic planes with
    // different readiness conditions. Normative gate:
    // collapse rules may fire under free scheduling only on GENUINELY stuck
    // values. A bound-but-unsubbed Var is a wire whose peer hasn't arrived;
    // copying it early can tie sub[x]=Var(a), sub[a]=Var(x) — a black hole
    // the normal-order driver can never reach. Same for reducible Apps.
    if (v.t === "Var") return isFree(v.nam) ? "DUP-VAR" : null;
    if (v.t === "App") return isStuckApp(rt, v) ? "DUP-APP" : null;
    return null;
  }
  return null;
}

function findRedexes(rt, root, cap = Infinity) {
  const out = []; const seen = new Set();
  const st = [{ n: root, path: [] }];
  while (st.length && out.length < cap) {
    const { n, path } = st.pop();
    const r = chase(rt, n);
    if (seen.has(r)) continue; seen.add(r);
    const rule = redexRule(rt, r);
    if (rule) out.push({ path, rule });
    const keys = CHILDREN[r.t];
    for (let i = keys.length - 1; i >= 0; i--) st.push({ n: r[keys[i]], path: path.concat(keys[i]) });
  }
  return out;
}
// rebuild along path with the node at `path` replaced by fire(resolved-node)
function applyAt(rt, root, path) {
  function rec(t, i) {
    const r = chase(rt, t);                 // splice through Var indirection
    if (i === path.length) {
      const rule = redexRule(rt, r);
      if (!rule) return { refused: true };
      let out;
      if (r.t === "App") {
        const f = chase(rt, r.fun);
        out = rule === "APP-LAM" ? app_lam(rt, r, f)
            : rule === "APP-SUP" ? app_sup(rt, r, f)
            : app_era(rt);
      } else {
        const v = chase(rt, r.val);
        out = rule === "DUP-LAM" ? dup_lam(rt, r, v)
            : rule.startsWith("DUP-SUP") ? dup_sup(rt, r, v)
            : rule === "DUP-ERA" ? dup_era(rt, r)
            : rule === "DUP-VAR" ? dup_var(rt, r, v)
            : dup_app(rt, r, v);
      }
      return { node: out, rule };
    }
    const k = path[i];
    if (!CHILDREN[r.t].includes(k)) return { refused: true };
    const sub = rec(r[k], i + 1);
    if (sub.refused) return sub;
    const copy = { ...r }; copy[k] = sub.node;
    return { node: copy, rule: sub.rule };
  }
  const res = rec(root, 0);
  return res.refused ? { refused: true, root } : { refused: false, root: res.node, rule: res.rule };
}
