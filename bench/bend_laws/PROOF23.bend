import Base
import ./law23_code.bend as C
import ./LAW23.bend as L

def L.law23_complete_key(d):
  match d:
    case C.Dims{a, b, c, e}:
      {==}

def L.law23_key_injective(a, b, e):
  match a:
    case C.Dims{a1, a2, a3, a4}:
      match b:
        case C.Dims{b1, b2, b3, b4}:
          Equal.cong(C.Key, C.Dims, C.unkey, C.key(C.Dims{a1, a2, a3, a4}), C.key(C.Dims{b1, b2, b3, b4}), e)

def L.law23_key2_aliases():
  {==}
