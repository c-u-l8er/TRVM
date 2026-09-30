import Base
import ./law23_code.bend as C

# Law 23: a key is complete when the input can be read back from it, i.e. the
# key has a left inverse, so equal keys mean equal inputs.
law law23_complete_key:
  for d: C.Dims
  {C.unkey(C.key(d)) == d : C.Dims}

# Corollary in the form the failure was felt: equal complete keys, equal inputs.
law law23_key_injective:
  for a: C.Dims
  for b: C.Dims
  for e: {C.key(a) == C.key(b) : C.Key}
  {a == b : C.Dims}

# The incomplete key aliases two different inputs: a witness, not a bound.
law law23_key2_aliases:
  {C.key2(C.Dims{1n, 1n, 0n, True{}}) == C.key2(C.Dims{1n, 1n, 1n, False{}}) : C.Key2}
