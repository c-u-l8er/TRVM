import Base

# Two representations of one counter: the unary meaning n, and the "doubled"
# encoding 2n. Law 5 (TRVM/LAWS.md): a numeric threshold may change
# representation, never meaning. Here: decode(encode(n)) is n, for every n.

def encode(n: Nat) -> Nat:
  Nat.double(n)

def decode(n: Nat) -> Nat:
  match n:
    case 0n:
      0n
    case 1n:
      0n
    case 2n+p:
      1n+decode(p)

# The mutant: a decoder that saturates at 33 (the period-33 shape: a one-shot
# where a count was meant). Above the saturation point the meaning is lost.
def decode_sat(n: Nat) -> Nat:
  Nat.min(decode(n), 33n)
