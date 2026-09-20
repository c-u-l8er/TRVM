"""printer.py -- the compiled backend's canonical printer, in C.

    from printer import CanonicalPrinter
    pr = CanonicalPrinter(view)
    pr.render(slots) == ic_ref.show(ic_ref.parse(compiler.enc_state_v6(view, state))).encode()

`print_state.c` walks the compiled step's own int64 state vector straight to the calculus's canonical
normal-form bytes.  The Python path it replaces is three conversions -- state dict -> term text ->
AST -> canonical text -- and `results-payload.json` measured it at 49-5,686 us against a step of
15-160 us, which is where `BENCHMARK_LANE.md` section B2-perf's 297x end-to-end (1x on chain30) comes
from.

THE DESIGN DECISION, made explicitly (README section 2j): this is a SEPARATE, world-independent object
beside the step, not printer code inside the emitted step.  The emitted step's source sha256 is the
admitted artifact's identity; the battery admits a step by film- and state-equality; a printer changes
neither, so folding it in would move every `cbknd-`/`cbknd2-` identity, and again on every future
printer change, for nothing the battery checks.  `laws_gate.py --check` HOLDING across this work is the
falsifier for that claim.

The printer has its own identity, `cprn-` over its own source, and is built by `emit_c.build` at the
admitted `-O2` into the same toolchain-namespaced cache.
"""
import ctypes
import hashlib
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.dont_write_bytecode = True

import emit_c as EC                                        # noqa: E402

SOURCE_PATH = os.path.join(HERE, "print_state.c")
ABI = 1

# the field kinds of print_state.c, in `compiler.state_layout` terms
K_ONEHOT, K_BINP, K_ONCE, K_PAIR, K_POSE, K_FAULT, K_ROTOR = range(7)
_ERRORS = {-1: "unknown field kind", -2: "width outside 1..63", -3: "enum index outside its size"}


def descriptor(view):
    """The (kind, arg, slot offset) triples the C printer walks, from `emit_c.slot_map`'s own field list.

    `arg` is the one number the rendering of that kind needs: an enum's size, a counter's bit width, a
    lane width.  Read off the SAME `slot_map` the step's encoder uses, so a layout change moves both or
    neither -- the printer never re-walks the layout on its own.
    """
    fields, width = EC.slot_map(view)
    desc = []
    for kind, name, off, n, spec in fields:
        if kind == "counter":
            if spec[0] == "onehot":
                desc += [K_ONEHOT, spec[1], off]
            elif spec[0] == "binp":
                desc += [K_BINP, spec[3], off]
            elif spec[0] == "once":
                desc += [K_ONCE, spec[2], off]
            else:
                raise ValueError("printer: unhandled counter spec %r" % (spec,))
        elif kind in ("wire", "door", "relay"):
            desc += [K_PAIR, 0, off]
        elif kind == "pose":
            desc += [K_POSE, spec[1], off]              # ("pose", pose_width(view, name)) -- slot_map's own
        elif kind == "fault":
            desc += [K_FAULT, 0, off]
        elif kind == "rotor":
            desc += [K_ROTOR, spec[1], off]             # ("rotor", view.spinners[name][0]) -- slot_map's own
        else:
            raise ValueError("printer: unhandled field kind %r" % kind)
    return desc, len(fields), width


def _source():
    with open(SOURCE_PATH) as f:
        return f.read()


def printer_id(source=None):
    """`cprn-` over the printer's own source -- its own identity, deliberately NOT a `cbknd-`.

    Taken from the same read that built the object, so the id always describes the `.so` that is loaded; reading
    the file a second time would let an edit between the two give a new id to an old object, which is exactly the
    fault `FLAGS_POLICY.md` choice 5 closed for the step.
    """
    if source is None and _LIB:
        return next(iter(_LIB.values()))[4]
    src = _source() if source is None else source
    return "cprn-" + hashlib.sha256(src.encode()).hexdigest()


_LIB = {}


def _lib(cc="gcc"):
    """The printer object, built once per process at the admitted `-O2` and content-addressed like the step's."""
    if cc not in _LIB:
        src = _source()
        so, sha, built = EC.build(src, cc)
        lib = ctypes.CDLL(so)
        lib.trvm_print_abi.argtypes = []
        lib.trvm_print_abi.restype = ctypes.c_int64
        abi = lib.trvm_print_abi()
        if abi != ABI:
            raise RuntimeError("printer: object ABI %d, this module speaks %d (%s)" % (abi, ABI, so))
        lib.trvm_print_state.argtypes = [ctypes.POINTER(ctypes.c_int64), ctypes.c_int64,
                                         ctypes.POINTER(ctypes.c_int64), ctypes.c_char_p, ctypes.c_int64]
        lib.trvm_print_state.restype = ctypes.c_int64
        _LIB[cc] = (lib, so, sha, built, "cprn-" + hashlib.sha256(src.encode()).hexdigest())
    return _LIB[cc]


class CanonicalPrinter:
    """One world's canonical printer: `render(slots)` -> the calculus's normal-form bytes for that state.

    `slots` is the compiled step's int64 state vector -- `emit_c.CompiledStep._Arr`, which `emit_c2`'s
    packed step unpacks to as well, so one printer serves both C emitters.
    """

    def __init__(self, view, cc="gcc"):
        self.view = view
        desc, self.nfields, self.width = descriptor(view)
        self._desc = (ctypes.c_int64 * len(desc))(*desc)
        self._lib, self.so_path, self.source_sha256, self.built_now, self.printer_id = _lib(cc)
        self._cap = 1 << 12
        self._buf = ctypes.create_string_buffer(self._cap)

    def render(self, slots):
        n = self._lib.trvm_print_state(self._desc, self.nfields, slots, self._buf, self._cap)
        if n < 0:
            raise ValueError("printer refused: %s (code %d)" % (_ERRORS.get(n, "?"), n))
        if n > self._cap:
            # the buffer is grown once per world and then never again; a rendering's size is a property
            # of the layout, not of the state, so this is a startup cost and not a per-epoch one.
            while self._cap < n:
                self._cap *= 2
            self._buf = ctypes.create_string_buffer(self._cap)
            n = self._lib.trvm_print_state(self._desc, self.nfields, slots, self._buf, self._cap)
            if n < 0 or n > self._cap:
                raise RuntimeError("printer: re-render did not fit (%d in %d)" % (n, self._cap))
        return self._buf.raw[:n]

    def render_state(self, cs, st):
        """`render` from the state DICT, for a caller that has no slot vector -- it pays `cs.encode` first."""
        return self.render(cs.encode(st))
