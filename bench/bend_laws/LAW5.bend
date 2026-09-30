import Base
import ./law5_code.bend as C

law law5_roundtrip:
  for n: Nat
  {C.decode(C.encode(n)) == n : Nat}
