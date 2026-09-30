import Base
import ./law5_code.bend as C
import ./LAW5.bend as L

def L.law5_roundtrip(n):
  match n:
    case 0n:
      {==}
    case 1n+p:
      %L.law5_roundtrip(p) : {1n+C.decode(C.encode(p)) == 1n+_ : Nat}
      {==}
