"""forge_api.py -- the stable public boundary of the Forge/TRVM engine.

Consumers (the `trvs` / TRAAVIIS terminal, and any future tool) import THIS
module, not `spinner_bench` internals. It presents a small, VERSIONED surface:

    lower_source(source)              -> lowering + identity payload
    run_source(source)                -> deterministic ic_ref fold + per-epoch films
    verify_source(source, oracle=...) -> reference / native / oracle agreement
    engine_info()                     -> capabilities + versions (for `trvs doctor`)

`ENGINE_API_VERSION` lets a consumer refuse an incompatible engine cleanly rather
than importing something unexpected.

Internally this currently DELEGATES to the proven `spinner_bench` pipeline (the
same functions the shipping bench + web server use), so the identity spine and
the ic_ref==ic32==oracle fold are byte-for-byte the ones already covered by the
binding-run batteries. The eventual direction is to invert the dependency so
`spinner_bench` consumes this module; until then, this is the single place that
knows the bench's private surface, so a bench refactor only touches this file.
"""
import os

import spinner_bench as _bench
import forge_runtime as _rt

# Bump when the payload shape or function contract changes incompatibly.
ENGINE_API_VERSION = "1"

# The frozen shape of a lower_source() payload. A LowerResultV1 ALWAYS carries the
# five contract keys {result_version, ok, semantic_artifact_id, diagnostics, error}
# plus `engine_version`; a success additionally carries the presentation keys
# (graph/formatted/rotor_init/provenance) the world CLI reads. Consumers that only
# need identity read the contract keys; the presentation keys are a superset a
# terminal may render. Frozen so a downstream identity adapter can depend on the
# shape without importing bench internals.
LOWER_RESULT_VERSION = "forge.lower-result.v1"


def _oracle_available():
    """The independent Fixture oracle is available iff its module imports."""
    try:
        import fixture  # noqa: F401
        return True
    except Exception:
        return False


def engine_info():
    """Capabilities + versions of the loaded engine. A pure read; folds nothing."""
    return {
        "api_version": ENGINE_API_VERSION,
        "engine_dir": os.path.dirname(os.path.abspath(__file__)),
        "bench_version": _bench.BENCH_VERSION,
        "ic_ref": True,  # forge_runtime imports ic_ref at load; reaching here == ok
        "ic32_path": _rt.IC32,
        "native_available": _rt.native_available(),
        "skip_native": _rt.SKIP_NATIVE,
        "oracle_available": _oracle_available(),
        "demo_semantic_id": _bench.DEMO_WORLD_SEMANTIC_ID,
    }


def lower_source(source):
    """Lower WRL source to a LowerResultV1 payload. ALWAYS returns the frozen
    contract keys {result_version, ok, semantic_artifact_id, diagnostics, error,
    engine_version}; a success additionally carries {graph, formatted, rotor_init,
    provenance} (the presentation superset the world CLI reads). Ordinary invalid
    WRL is a data outcome ({ok:False, error:<message>, ...}), NOT an exception --
    exceptions are reserved for engine/import failures the bench pipeline itself
    could not present."""
    payload = _bench._lower_payload(source)
    payload["result_version"] = LOWER_RESULT_VERSION
    payload["engine_version"] = _bench.BENCH_VERSION
    # Normalize the five contract keys so a consumer never has to branch on shape:
    # a success has no `error`, an error has neither `semantic_artifact_id` nor
    # `diagnostics`. Fill the absent side with its neutral value.
    payload.setdefault("semantic_artifact_id", None)
    payload.setdefault("diagnostics", [])
    payload.setdefault("error", None)
    return payload


def run_source(source, scenario=None):
    """Deterministically fold the world through the ic_ref reducer: returns
    {ok, semantic_artifact_id, scenario_digest, reducer, epochs:[rows]} or error."""
    return _bench._run_payload(source, scenario=scenario)


def verify_source(source, oracle=True, scenario=None):
    """Re-fold through the native ic32 reducer and (when oracle=True) the
    independent Fixture oracle, asserting world+film parity with ic_ref: returns
    {ok, native, parity, oracle:{...}, epochs:[...], semantic_artifact_id, ...}."""
    return _bench._verify_payload(source, oracle=oracle, scenario=scenario)
