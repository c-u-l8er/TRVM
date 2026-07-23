"""lowering_policy.py -- the shared counter-representation policy (Phase 3D.1-D).

GPT-5.6's Phase 3D.1 correction: the one-hot / binary counter representation is a
BACKEND policy, not a Fixture fact and not a CompilePlanV1 fact. This module is
the single home for that policy so that BOTH the Fixture (the independent test
oracle) and the production `_PlanView` shim consult the SAME rule -- and so that
the production compile path no longer imports `fixture.ONEHOT_MAX`.

A periodic clock of period `p` lowers to:
  * a one-hot enum      when the profile forces `one_hot`, or when `auto` and
                        `p <= onehot_max`;
  * a binary counter    when the profile forces `binary`, or when `auto` and
                        `p >  onehot_max`.
A `once` clock keeps its Once-specific encoding regardless of the profile (there
is no alternative representation for it in this profile).

The choice changes only the ENCODED STATE LAYOUT (the BackendArtifactID and the
backend content), never the semantic film: both representations count 0..p-1 and
fire at the same phase. `counter_spec_for` returns the compiler's `counter_spec`
shape unchanged, so no compiler code moves.
"""

DEFAULT_ONEHOT_MAX = 32          # the `auto` threshold when a profile pins it
COUNTER_ENCODINGS = ("auto", "one_hot", "binary")


def counter_spec_for(clock, counter_encoding="auto",
                     onehot_max=DEFAULT_ONEHOT_MAX):
    """(clock, counter_encoding, onehot_max) -> the compiler counter_spec:
        ('onehot', period, phase)
      | ('binp',   period, phase, width)
      | ('once',   epoch, width)
    `clock` is the semantic clock tuple: ('periodic', p, ph) | ('once', e)."""
    if clock[0] == "once":
        e = clock[1]
        return ("once", e, max(1, (e + 1).bit_length()))
    _, p, ph = clock
    if counter_encoding == "one_hot":
        use_onehot = True
    elif counter_encoding == "binary":
        use_onehot = False
    else:                                   # "auto"
        use_onehot = p <= onehot_max
    if use_onehot:
        return ("onehot", p, ph)
    return ("binp", p, ph, p.bit_length())
