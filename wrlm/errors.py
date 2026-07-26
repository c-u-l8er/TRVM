"""The shared typed-rejection base for the WRLM layer.

Mirrors the forge spine's `WrlUnsupported` / `WrlValidationError` arrangement: one
base class so a caller can write `except WrlmError` and catch every typed
rejection this layer raises, while the per-module subclasses stay meaningful.

Every rejection carries a STABLE machine code and, when the validator can name
the offending place, a dotted path. The path is an AST/record locator -- WRLM
has no surface syntax, so there are no spans or filenames to report.
"""


class WrlmError(Exception):
    def __init__(self, code, message, path=None):
        super().__init__("[%s] %s%s" % (code, message,
                                        "" if path is None else " at %s" % path))
        self.code = code
        self.message = message
        self.path = path


def fail(code, message, path=None):
    raise WrlmError(code, message, path)
