import Base

# Law 23 (TRVM/LAWS.md): a memoization key must include every dimension over
# which the memoized generator ranges. The generator ranges over four.
type Dims is Data:
  Dims{depth: Nat, size: Nat, profile: Nat, policy: Bool}

# The complete key carries all four.
type Key is Data:
  Key{depth: Nat, size: Nat, profile: Nat, policy: Bool}

def key(d: Dims) -> Key:
  match d:
    case Dims{a, b, c, e}:
      Key{a, b, c, e}

# The incomplete key (the async-memokey bug's shape): profile and policy dropped.
type Key2 is Data:
  Key2{depth: Nat, size: Nat}

def key2(d: Dims) -> Key2:
  match d:
    case Dims{a, b, c, e}:
      Key2{a, b}

def Key.depth(k: Key) -> Nat:
  match k:
    case Key{a, b, c, e}:
      a

def Key.size(k: Key) -> Nat:
  match k:
    case Key{a, b, c, e}:
      b

def Key.profile(k: Key) -> Nat:
  match k:
    case Key{a, b, c, e}:
      c

def Key.policy(k: Key) -> Bool:
  match k:
    case Key{a, b, c, e}:
      e

# A key is complete exactly when the input can be read back from it.
def unkey(k: Key) -> Dims:
  match k:
    case Key{a, b, c, e}:
      Dims{a, b, c, e}

# The best possible "inverse" of the incomplete key: it must invent two fields.
def unkey2(k: Key2) -> Dims:
  match k:
    case Key2{a, b}:
      Dims{a, b, 0n, True{}}
