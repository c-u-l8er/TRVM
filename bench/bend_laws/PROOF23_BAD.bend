import Base
import ./law23_code.bend as C

# The incomplete key, claimed complete. This file must FAIL to check: no
# function can read profile and policy back out of a key2.
law law23_key2_complete:
  for d: C.Dims
  {C.unkey2(C.key2(d)) == d : C.Dims}

def law23_key2_complete(d):
  match d:
    case C.Dims{a, b, c, e}:
      {==}
