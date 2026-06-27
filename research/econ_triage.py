"""
econ_triage.py -- which economic invariants can be coordination-free currencies?

frontier.py found delta (proportional demurrage) breaks free merge: proportional decay does
not commute with deposits. This generalizes the test. A currency is coordination-free when:
  (1) its state has an order-independent CRDT merge (commutative, associative, idempotent), and
  (2) for a TRANSACTED balance, its update commutes with the substrate's transactions
      (deposits) -- else order matters and coordination is needed.
Sort the currency-update FORMS by both, then map the named invariants to forms.

The seven v0.5 economic invariants render client-side and didn't come through; mergeability is
determined by FORM, which is what this sorts. Placing each of the seven precisely needs its
exact update rule.

Run: python3 econ_triage.py
"""
import random
rng = random.Random(0)

def crdt_ok(merge, gen, idempotent, n=400):
    for _ in range(n):
        a, b, c = gen(), gen(), gen()
        if merge(a, b) != merge(b, a): return False                       # commutative
        if merge(merge(a, b), c) != merge(a, merge(b, c)): return False   # associative
        if idempotent and merge(a, a) != a: return False                  # idempotent
    return True

# correct CRDT merges per form -------------------------------------------------------
def vec(): return tuple(rng.randint(0, 9) for _ in range(3))             # per-replica state
gcounter = (lambda a, b: tuple(max(x, y) for x, y in zip(a, b)), vec, True)   # additive -> G-Counter
maxreg   = (lambda a, b: max(a, b), lambda: rng.randint(0, 99), True)         # max-register
minreg   = (lambda a, b: min(a, b), lambda: rng.randint(0, 99), True)         # min-register
gset     = (lambda a, b: a | b, lambda: frozenset(rng.sample(range(9), 3)), True)  # G-Set
def fset(): return frozenset(rng.sample(range(9), 3))
# proportional: pure scalar value, "merge" by averaging/combining is NOT order-independent
prop_merge = lambda a, b: a * b            # composing two decays multiplies (commutes), but merging
                                           # two independently-decayed balances this way is unsound
proportional = (prop_merge, lambda: rng.uniform(0.1, 2.0), True)         # idempotent? a*a != a -> fails

FORMS = {
    "additive accumulation (G-Counter)": gcounter,
    "max-register":                      maxreg,
    "min-register":                      minreg,
    "grow-only set (G-Set)":             gset,
    "proportional / decay (scalar *)":   proportional,
}

# does the update commute with an additive transaction (deposit)? (matters for a shared balance)
def commutes_with_deposit(update):
    for _ in range(200):
        x = rng.uniform(-50, 50); k = rng.uniform(0.3, 3.0); d = rng.uniform(1, 40)
        if abs(update(x + d, k) - (update(x, k) + d)) > 1e-7: return False
    return True
UPDATES = {
    "additive accumulation (G-Counter)": lambda x, k: x + k,
    "max-register":                      lambda x, k: max(x, k),
    "min-register":                      lambda x, k: min(x, k),
    "grow-only set (G-Set)":             None,                       # not a numeric balance
    "proportional / decay (scalar *)":   lambda x, r: x * r,
}

print("Economic-layer mergeability triage: which forms are coordination-free currencies?")
print("=" * 78)
print(f"\n  {'currency-update form':<36}{'CRDT-merge?':<13}{'commutes w/ deposit?'}")
print("  " + "-" * 74)
for name, (merge, gen, idem) in FORMS.items():
    crdt = crdt_ok(merge, gen, idem)
    upd = UPDATES[name]
    comm = "n/a (not a balance)" if upd is None else str(commutes_with_deposit(upd))
    print(f"  {name:<36}{str(crdt):<13}{comm}")

print("\n  reading it:")
print("   * additive / max / min / set all have a CRDT merge -> mergeable, coordination-free")
print("     as standalone currencies. proportional has NO order-independent value merge")
print("     (a*a != a; merging two independently-decayed balances needs a shared clock).")
print("   * for a TRANSACTED balance (deposits on the same value), only ADDITIVE commutes with")
print("     deposits; max/min/proportional do not -> they can't share a balance coordination-free.")

print("\n  mapping the named invariants (form determines mergeability):")
print("  " + "-" * 74)
M = [("beta (persistence)",       "additive accumulation",  "coordination-FREE (G-Counter; tiers.py)"),
     ("delta (demurrage)",        "proportional decay",     "coordination-HARD (no value merge; breaks deposits)"),
     ("C = A + Phi (Ulanowicz)",  "additive identity",      "identity is tier-1; window CONSTRAINT is tier-2"),
     ("kappa (routing)",          "structure measure",      "not a currency (tier-2 graph measure)"),
     ("sigma (resolution)",       "H^1 obstruction",        "not a currency (the merge IS the resolution)")]
for inv, form, verd in M:
    print(f"   {inv:<24} {form:<22} -> {verd}")

print("\n" + "=" * 78)
print("DESIGN RULE for the v0.5 economic layer:")
print(" * Additive / counter / register / set currencies are coordination-free. Proportional")
print("   (multiplicative) currencies are NOT -- no order-independent merge, and they break")
print("   transacted balances. This is precisely why beta is free and delta is hard.")
print(" * A holding cost must therefore be ADDITIVE / per-capita (a fixed per-epoch drain, keyed")
print("   idempotently per epoch = a PN-counter), not PROPORTIONAL, to stay a coordination-free")
print("   currency beside the others. The multi-currency design is sound; the FORM of each")
print("   currency is the constraint -- multiplicative money fights coordination-freedom.")
print(" * (Exact placement of all seven v0.5 invariants needs their update rules; the form test")
print("   above is the tool that sorts each once defined.)")
