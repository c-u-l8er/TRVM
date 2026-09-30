import Base
import ./law5_code.bend as C

# The same law over the saturating decoder. This file must FAIL to check:
# a representation that saturates has changed the meaning.
law law5_roundtrip_sat:
  for n: Nat
  {C.decode_sat(C.encode(n)) == n : Nat}

def law5_roundtrip_sat(n):
  match n:
    case 0n:
      {==}
    case 1n+p:
      %law5_roundtrip_sat(p) : {1n+C.decode_sat(C.encode(p)) == 1n+_ : Nat}
      {==}

def main() -> {C.decode_sat(C.encode(40n)) == 40n : Nat}:
  law5_roundtrip_sat(40n)
