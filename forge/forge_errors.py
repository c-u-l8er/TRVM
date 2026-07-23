#!/usr/bin/env python3
"""forge_errors.py -- ErrorPresentationV1, the browser-safe typed-error sidecar
(v0.7-2 "Error and Progress UX").

Every API failure the Spinner Bench server returns is presented through ONE frozen
shape so the browser never sees a raw Python string (`KeyError: ...`,
`WrlValidationError: ...`, a `Traceback`). Full exceptions may remain in the
developer log under a generated `error_id`; only the sanitized presentation crosses
to the browser.

    ErrorPresentationV1 {
        error_presentation_version   # "forge.error.v1"
        code            # a STABLE machine code (the validation contract)
        title           # a short human title
        message         # a human message (domain text, never a Python repr)
        severity        # "error" | "warning" | "info"
        retryable       # bool -- can the same request succeed after a fix?
        action_label    # the single suggested next action (or null)
        category        # source_draft | project_recovery | runtime_native | bundle | ...
        field_path?     # dotted canonical path (static_config.rotor, ...)
        source_span?    # {file_id,start_line,start_column,end_line,end_column}
        object_id?      # canonical object/edge key to highlight on the canvas
        details?        # extra structured context (cache path, parity report, ...)
        error_id?       # correlation id for the developer log (unknown errors)
    }

This module carries NO WRL parsing: it maps a code (or an exception that carries a
`.code`) to a presentation. Source-span / canvas-locator enrichment is added by the
caller (which already holds the source + diagnostics)."""
import uuid

ERROR_PRESENTATION_VERSION = "forge.error.v1"

# ---- error categories (the four ruled families + request/internal) ----------
CAT_SOURCE = "source_draft"
CAT_PROJECT = "project_recovery"
CAT_RUNTIME = "runtime_native"
CAT_BUNDLE = "bundle"
CAT_REQUEST = "request"
CAT_INTERNAL = "internal"

# severities
ERROR, WARNING, INFO = "error", "warning", "info"

# ---- runtime/native + job synthetic codes (not raised as WrlValidationError) --
NATIVE_UNAVAILABLE = "NATIVE_UNAVAILABLE"
NATIVE_BUILD_FAILED = "NATIVE_BUILD_FAILED"
REFERENCE_FOLD_FAILED = "REFERENCE_FOLD_FAILED"
PARITY_MISMATCH = "PARITY_MISMATCH"
JOB_CANCELLED = "JOB_CANCELLED"
JOB_FAILED = "JOB_FAILED"
FORGE_BAD_REQUEST = "WRL_BAD_REQUEST"
FORGE_INTERNAL = "FORGE_INTERNAL"

# code -> (title, severity, retryable, action_label, category)
_REGISTRY = {
    # ---- source / draft -----------------------------------------------------
    "WRL_PARSE": ("Could not parse the world source", ERROR, True,
                  "Fix the source", CAT_SOURCE),
    "WRL_SUGAR_MALFORMED": ("Malformed WRL sugar", ERROR, True,
                            "Fix the source", CAT_SOURCE),
    "WRL_WORLD_SOURCE_HAS_SCENARIO": (
        "Run inputs do not belong in the world source", ERROR, True,
        "Move claims to a scenario", CAT_SOURCE),
    "WRL_DUPLICATE_ID": ("Duplicate object id", ERROR, True,
                         "Rename the duplicate", CAT_SOURCE),
    "WRL_UNKNOWN_ENDPOINT": ("Edge names an unknown object", ERROR, True,
                             "Fix the endpoint", CAT_SOURCE),
    "WRL_ILLEGAL_PORT_PAIR": ("Illegal port connection", ERROR, True,
                              "Rewire the edge", CAT_SOURCE),
    "WRL_CONTROLLER_CONFLICT": ("Two controllers drive one target", ERROR, True,
                                "Remove one controller", CAT_SOURCE),
    "WRL_CLOCK_RANGE": ("Clock value out of range", ERROR, True,
                        "Fix the clock", CAT_SOURCE),
    "WRL_NUMERIC_RANGE": ("Numeric value out of range", ERROR, True,
                          "Fix the value", CAT_SOURCE),
    "WRL_EPOCH_RANGE": ("Epoch out of range", ERROR, True,
                        "Fix the epoch", CAT_SOURCE),
    "WRL_UNSUPPORTED_FEATURE": ("Unsupported world feature", ERROR, True,
                                "Remove the feature", CAT_SOURCE),
    "WRL_PORT_SIGNATURE": ("Port signature mismatch", ERROR, True,
                           "Fix the ports", CAT_SOURCE),
    "WRL_INVALID_CANDIDATE": ("The draft is not a runnable world", WARNING, True,
                              "Repair the draft", CAT_SOURCE),
    "WRL_COMMIT_MISMATCH": ("The candidate changed before commit", WARNING, True,
                            "Re-apply and commit", CAT_SOURCE),
    "WRL_STALE_DRAFT": ("The draft is based on an old revision", WARNING, True,
                        "Reload latest revision", CAT_SOURCE),
    "WRL_BAD_EDIT": ("Malformed edit request", ERROR, False, None, CAT_SOURCE),
    "WRL_BAD_GESTURE": ("Malformed canvas gesture", ERROR, False, None,
                        CAT_SOURCE),
    "WRL_BAD_DRAFT": ("Malformed draft state", ERROR, False, None, CAT_SOURCE),
    "WRL_BAD_SESSION": ("Malformed session state", ERROR, False, None,
                        CAT_SOURCE),
    "WRL_UNSEALED_POLICY": ("Unsealed policy", ERROR, False, None, CAT_SOURCE),
    "WRL_MALFORMED_ARTIFACT": ("Malformed artifact", ERROR, False, None,
                               CAT_SOURCE),
    "WRL_BAD_LOWERING_PROFILE": ("Bad lowering profile", ERROR, False, None,
                                 CAT_SOURCE),
    "WRL_SEALED_IMMUTABLE": ("Attempted write to a sealed object", ERROR, False,
                             None, CAT_SOURCE),
    "WRL_UNKNOWN_ARTIFACT_FIELD": ("Unknown artifact field", ERROR, True,
                                   "Remove the field", CAT_SOURCE),
    # ---- project / recovery -------------------------------------------------
    "WRL_PROJECT_EXISTS": ("That project id is already taken", WARNING, True,
                           "Choose another id", CAT_PROJECT),
    "WRL_PROJECT_MISSING": ("No such project", ERROR, False, None, CAT_PROJECT),
    "WRL_PROJECT_NOT_FOUND": ("No such project", ERROR, False, None, CAT_PROJECT),
    "WRL_PROJECT_STALE": ("The project changed on disk", WARNING, True,
                          "Reload latest revision", CAT_PROJECT),
    "WRL_BAD_PROJECT": ("This project cannot be saved as-is", WARNING, True,
                        "Migrate project", CAT_PROJECT),
    "WRL_PROJECT_MIGRATION": ("Project migration failed", ERROR, True,
                              "Retry migration", CAT_PROJECT),
    "WRL_BAD_TRASH": ("Malformed trash entry", ERROR, False, None, CAT_PROJECT),
    "WRL_TRASH_MISSING": ("No such trashed project", ERROR, False, None,
                          CAT_PROJECT),
    "WRL_BAD_SESSION_POINTER": ("Malformed last-session pointer", ERROR, False,
                               None, CAT_PROJECT),
    "WRL_BAD_RECOVERY": ("Malformed recovery journal", ERROR, False, None,
                         CAT_PROJECT),
    "WRL_RECOVERY_MISSING": ("No recovery journal", INFO, False, None,
                             CAT_PROJECT),
    "WRL_RECOVERY_STALE": ("Recovery is from an older revision", WARNING, True,
                           "Open as copy", CAT_PROJECT),
    # ---- runtime / native verification --------------------------------------
    NATIVE_UNAVAILABLE: ("The native reducer is unavailable", INFO, False,
                         "Run reference-only", CAT_RUNTIME),
    NATIVE_BUILD_FAILED: ("The native reducer failed to build", WARNING, True,
                          "Retry native build", CAT_RUNTIME),
    REFERENCE_FOLD_FAILED: ("The reference fold failed", ERROR, True,
                            "View details", CAT_RUNTIME),
    PARITY_MISMATCH: ("Native parity mismatch", ERROR, False,
                      "View verification details", CAT_RUNTIME),
    JOB_CANCELLED: ("The job was cancelled", INFO, True, None, CAT_RUNTIME),
    JOB_FAILED: ("The job failed", ERROR, True, "Retry", CAT_RUNTIME),
    # ---- bundle -------------------------------------------------------------
    "WRL_BAD_BUNDLE": ("Unsupported or malformed bundle", ERROR, False, None,
                       CAT_BUNDLE),
    "WRL_BUNDLE_CORRUPT": ("The bundle is corrupt", ERROR, False, None,
                           CAT_BUNDLE),
    "WRL_BUNDLE_UNRESOLVED": ("The bundle is missing referenced objects", WARNING,
                              False, None, CAT_BUNDLE),
    "WRL_BUNDLE_IDENTITY": ("The bundle's world does not match its identity", ERROR,
                            False, None, CAT_BUNDLE),
    # ---- object store (surfaced as bundle/internal) -------------------------
    "WRL_STORE_MISSING": ("A referenced object is missing", ERROR, False, None,
                          CAT_BUNDLE),
    "WRL_STORE_CORRUPT": ("A stored object is corrupt", ERROR, False, None,
                          CAT_BUNDLE),
    "WRL_STORE_ID_MISMATCH": ("A stored object id mismatch", ERROR, False, None,
                              CAT_BUNDLE),
    "WRL_STORE_BAD_REF": ("A malformed object reference", ERROR, False, None,
                          CAT_BUNDLE),
    # ---- request / internal -------------------------------------------------
    FORGE_BAD_REQUEST: ("Malformed request", ERROR, False, None, CAT_REQUEST),
    FORGE_INTERNAL: ("An unexpected internal error occurred", ERROR, False, None,
                     CAT_INTERNAL),
}

_DEFAULT = ("An error occurred", ERROR, False, None, CAT_INTERNAL)


def category_of(code):
    return _REGISTRY.get(code, _DEFAULT)[4]


def present(code, message, *, field_path=None, source_span=None,
            object_id=None, details=None, error_id=None):
    """Build one ErrorPresentationV1 dict. `message` MUST already be domain text
    (never a raw Python exception repr); the optional locators/details are added
    verbatim. Unknown codes fall back to a generic internal presentation."""
    title, severity, retryable, action, category = _REGISTRY.get(code, _DEFAULT)
    out = {
        "error_presentation_version": ERROR_PRESENTATION_VERSION,
        "code": code,
        "title": title,
        "message": message,
        "severity": severity,
        "retryable": bool(retryable),
        "action_label": action,
        "category": category,
    }
    if field_path is not None:
        out["field_path"] = field_path
    if source_span is not None:
        out["source_span"] = source_span
    if object_id is not None:
        out["object_id"] = object_id
    if details is not None:
        out["details"] = details
    if error_id is not None:
        out["error_id"] = error_id
    return out


def from_exception(exc, *, logger=None, field_path=None, source_span=None,
                   object_id=None, details=None):
    """Present a caught exception. A typed WrlValidationError (anything carrying a
    stable `.code`) is presented with its own domain message. An UNKNOWN exception
    is NEVER leaked: it gets a generic internal presentation with a correlation
    `error_id`; the full exception is handed to `logger(error_id, exc)` for the
    developer log only."""
    code = getattr(exc, "code", None)
    if code:
        msg = getattr(exc, "message", None) or str(exc)
        return present(code, msg,
                       field_path=field_path
                       or getattr(exc, "field_path", None),
                       source_span=source_span, object_id=object_id,
                       details=details)
    error_id = uuid.uuid4().hex[:12]
    if logger is not None:
        try:
            logger(error_id, exc)
        except Exception:
            pass
    return present(FORGE_INTERNAL,
                   "An unexpected internal error occurred (ref %s)." % error_id,
                   details=details, error_id=error_id)


def native(code, message, *, details=None):
    """Present a runtime/native code (native unavailable / build failed / parity
    mismatch / job failed|cancelled)."""
    return present(code, message, details=details)


def bad_request(message="The request could not be understood."):
    return present(FORGE_BAD_REQUEST, message)
