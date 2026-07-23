"""wrl_templates.py v0.1 -- the Immutable Template Catalog (Forge v0.7-3,
GPT-5.6's template ruling).

A TEMPLATE is a release-owned, read-only, schema-validated authoring starting
point -- NOT a hidden project in the user's store. Exactly three ship with the
release (Golden ADMIT Demo, ADMIT Acceptance Bench, Blank Spinner World); their
JSON manifests live under an allowlisted `templates/` directory and are covered
by the release MANIFEST.sha256.

A `TemplateManifestV1` carries:
  * catalog / product metadata (template_id, name, short_description, purpose,
    difficulty) -- the `template_id` is a PRODUCT identifier, NEVER a Forge
    semantic identity, and by the immutable-content rule a template id may never
    silently change meaning: changing the sealed content requires a NEW version
    (e.g. `.v2`), never overwriting `.v1`. (Layout/wording/guide copy MAY change
    between app releases without a new template version.)
  * the authoring seed: `canonical_world_source` (+ its expected
    `world_semantic_id`), a `canvas_layout` (CanvasLayoutV1 presentation), and a
    set of `scenarios` (project-style {name, scenario_digest, scenario} entries)
    with a `default_scenario_document_id`.
  * the FROZEN expected identities: `expected_scenario_digests` and
    `expected_replay_bundle_ids` (keyed by scenario document name).
  * guide copy: `suggested_first_edit`, `expected_edit_effect`, `guide_steps`.

`verify_template_identity` RE-DERIVES every identity from the sealed source and
scenarios and fails closed with `FORGE_TEMPLATE_IDENTITY` if any expected value
drifts -- a corrupted or tampered template is never displayed or instantiated.
The catalog verifies all templates at startup.

This module introduces NO new semantic or runtime construct and NO new Forge
identity: a template merely BINDS an existing world source to existing scenario
documents and records the identities they already produce.
"""
import copy
import json
import os

import wrl_ir as W
import wrl_sugar as SG
import wrl_scenario as SC
import wrl_canvas as CV
import wrl_canonical as WC

TEMPLATE_VERSION = "forge.template.v1"
CATALOG_VERSION = "forge.template.catalog.v1"

# stable, versioned catalog identifiers (product ids -- NOT Forge identities)
GOLDEN_ADMIT_ID = "forge.template.golden-admit.v1"
ACCEPTANCE_BENCH_ID = "forge.template.acceptance-bench.v1"
BLANK_SPINNER_ID = "forge.template.blank-spinner.v1"

# stable error codes
WRL_BAD_TEMPLATE = "WRL_BAD_TEMPLATE"                # schema / shape violation
WRL_BAD_CATALOG = "WRL_BAD_CATALOG"                  # catalog index violation
FORGE_TEMPLATE_IDENTITY = "FORGE_TEMPLATE_IDENTITY"  # a re-derived id drifted

_TOP_KEYS = (
    "template_version", "template_id", "name", "short_description", "purpose",
    "difficulty", "canonical_world_source", "world_semantic_id", "canvas_layout",
    "scenarios", "default_scenario_document_id", "expected_scenario_digests",
    "expected_replay_bundle_ids", "suggested_first_edit", "expected_edit_effect",
    "guide_steps",
)
_SCENARIO_DOC_KEYS = ("name", "scenario_digest", "scenario")
_DIFFICULTIES = ("intro", "core", "advanced")


# --------------------------------------------------------------- validation
def _bad(msg, field=None):
    WC._fail(WRL_BAD_TEMPLATE, msg, field_path=field)


def _str(v, name):
    if not (isinstance(v, str) and v):
        _bad("%s must be a non-empty string, got %r" % (name, v), name)


def validate_template_manifest_v1(manifest):
    """Structural gate for a TemplateManifestV1. Raises WrlValidationError
    (WRL_BAD_TEMPLATE) on any violation; returns the manifest on success. This is
    a PURE SHAPE check -- identity re-derivation is `verify_template_identity`."""
    if not isinstance(manifest, dict):
        _bad("template manifest must be an object")
    if manifest.get("template_version") != TEMPLATE_VERSION:
        _bad("unknown template_version %r (only %s)"
             % (manifest.get("template_version"), TEMPLATE_VERSION),
             "template_version")
    missing = [k for k in _TOP_KEYS if k not in manifest]
    if missing:
        _bad("template missing field(s) %s" % missing)
    extra = [k for k in manifest if k not in _TOP_KEYS]
    if extra:
        _bad("template has unknown field(s) %s" % sorted(extra))

    _str(manifest["template_id"], "template_id")
    _str(manifest["name"], "name")
    _str(manifest["short_description"], "short_description")
    _str(manifest["purpose"], "purpose")
    if manifest["difficulty"] not in _DIFFICULTIES:
        _bad("difficulty must be one of %s, got %r"
             % (list(_DIFFICULTIES), manifest["difficulty"]), "difficulty")
    _str(manifest["canonical_world_source"], "canonical_world_source")
    if not WC._SEM_ID_RE.match(manifest["world_semantic_id"] or ""):
        _bad("bad world_semantic_id %r" % (manifest["world_semantic_id"],),
             "world_semantic_id")

    CV.validate_layout_v1(manifest["canvas_layout"])

    scenarios = manifest["scenarios"]
    if not (isinstance(scenarios, list) and scenarios):
        _bad("scenarios must be a non-empty list", "scenarios")
    names = []
    for i, doc in enumerate(scenarios):
        loc = "scenarios[%d]" % i
        if not isinstance(doc, dict):
            _bad("%s must be an object" % loc, loc)
        d_missing = [k for k in _SCENARIO_DOC_KEYS if k not in doc]
        if d_missing:
            _bad("%s missing field(s) %s" % (loc, d_missing), loc)
        d_extra = [k for k in doc if k not in _SCENARIO_DOC_KEYS]
        if d_extra:
            _bad("%s has unknown field(s) %s" % (loc, sorted(d_extra)), loc)
        _str(doc["name"], "%s.name" % loc)
        SC.validate_scenario_v1(doc["scenario"])
        names.append(doc["name"])
    if len(set(names)) != len(names):
        _bad("scenario document names must be unique, got %r" % names,
             "scenarios")

    default_id = manifest["default_scenario_document_id"]
    if default_id not in names:
        _bad("default_scenario_document_id %r is not a scenario document name %r"
             % (default_id, names), "default_scenario_document_id")

    for field in ("expected_scenario_digests", "expected_replay_bundle_ids"):
        m = manifest[field]
        if not isinstance(m, dict):
            _bad("%s must be an object" % field, field)
        if sorted(m.keys()) != sorted(names):
            _bad("%s keys %s must match scenario names %s"
                 % (field, sorted(m.keys()), sorted(names)), field)

    _str(manifest["suggested_first_edit"], "suggested_first_edit")
    _str(manifest["expected_edit_effect"], "expected_edit_effect")
    steps = manifest["guide_steps"]
    if not (isinstance(steps, list) and steps
            and all(isinstance(s, str) and s for s in steps)):
        _bad("guide_steps must be a non-empty list of strings", "guide_steps")
    return manifest


# ---------------------------------------------------------- identity re-derive
def _fail_identity(msg, field=None):
    WC._fail(FORGE_TEMPLATE_IDENTITY, msg, field_path=field)


def _lower_source(source):
    """Re-lower a template's canonical world source. ANY parse/validation fault
    is a corrupted template -> fail closed with FORGE_TEMPLATE_IDENTITY (a
    tampered source must never be displayed or instantiated)."""
    try:
        return W.lower_program(SG.desugar_core(source), W.parse_wrl_core)
    except WC.WrlUnsupported as ex:
        _fail_identity("template world source no longer lowers: %s" % ex,
                       "canonical_world_source")


def verify_template_identity(manifest):
    """RE-DERIVE every Forge identity from the sealed content and confirm it
    matches the frozen expected values. Assumes the manifest already passed
    `validate_template_manifest_v1`. Raises WrlValidationError
    (FORGE_TEMPLATE_IDENTITY) on ANY drift; returns the manifest on success."""
    world_id = manifest["world_semantic_id"]
    prog = _lower_source(manifest["canonical_world_source"])
    if prog.semantic_artifact_id != world_id:
        _fail_identity(
            "world source re-lowers to %s but the manifest expects %s"
            % (prog.semantic_artifact_id, world_id), "world_semantic_id")

    exp_dig = manifest["expected_scenario_digests"]
    exp_rep = manifest["expected_replay_bundle_ids"]
    for doc in manifest["scenarios"]:
        name = doc["name"]
        scenario = doc["scenario"]
        if scenario.get("world_semantic_id") != world_id:
            _fail_identity(
                "scenario %r is bound to world %r but the template world is %r"
                % (name, scenario.get("world_semantic_id"), world_id),
                "scenarios")
        digest = SC.scenario_digest(scenario)
        if digest != doc["scenario_digest"]:
            _fail_identity(
                "scenario %r re-digests to %s but the entry records %s"
                % (name, digest, doc["scenario_digest"]), "scenarios")
        if digest != exp_dig[name]:
            _fail_identity(
                "scenario %r re-digests to %s but expected_scenario_digests "
                "records %s" % (name, digest, exp_dig[name]),
                "expected_scenario_digests")
        ir = SC.canonicalize_scenario_v1(scenario)["initial_runtime"]
        replay = SC.replay_bundle_id(world_id, digest, ir)
        if replay != exp_rep[name]:
            _fail_identity(
                "scenario %r re-computes replay id %s but "
                "expected_replay_bundle_ids records %s"
                % (name, replay, exp_rep[name]), "expected_replay_bundle_ids")
    return manifest


def load_template_manifest(manifest):
    """Validate the schema AND re-derive identities (the full acceptance gate for
    one template). Returns the manifest on success; raises on either failure."""
    validate_template_manifest_v1(manifest)
    verify_template_identity(manifest)
    return manifest


# -------------------------------------------------------- build (generator side)
def build_template_manifest(template_id, name, short_description, purpose,
                            difficulty, world_source, layout, named_scenarios,
                            default_scenario_document_id, suggested_first_edit,
                            expected_edit_effect, guide_steps):
    """Construct a fully-derived, self-verifying TemplateManifestV1 from a world
    source + ordered `named_scenarios` [(name, ScenarioV1), ...]. The scenario
    documents, world_semantic_id, expected_scenario_digests and
    expected_replay_bundle_ids are DERIVED here (never hand-copied), then the
    result is run through `load_template_manifest` so a build cannot emit a
    manifest whose recorded identities disagree with its content."""
    prog = W.lower_program(SG.desugar_core(world_source), W.parse_wrl_core)
    world_id = prog.semantic_artifact_id
    scenarios, exp_dig, exp_rep = [], {}, {}
    for sname, scenario in named_scenarios:
        canon = SC.canonicalize_scenario_v1(scenario)
        digest = SC.scenario_digest(scenario)
        ir = canon["initial_runtime"]
        scenarios.append({"name": sname, "scenario_digest": digest,
                          "scenario": canon})
        exp_dig[sname] = digest
        exp_rep[sname] = SC.replay_bundle_id(world_id, digest, ir)
    manifest = {
        "template_version": TEMPLATE_VERSION,
        "template_id": template_id,
        "name": name,
        "short_description": short_description,
        "purpose": purpose,
        "difficulty": difficulty,
        "canonical_world_source": world_source,
        "world_semantic_id": world_id,
        "canvas_layout": CV.validate_layout_v1(copy.deepcopy(layout)),
        "scenarios": scenarios,
        "default_scenario_document_id": default_scenario_document_id,
        "expected_scenario_digests": exp_dig,
        "expected_replay_bundle_ids": exp_rep,
        "suggested_first_edit": suggested_first_edit,
        "expected_edit_effect": expected_edit_effect,
        "guide_steps": list(guide_steps),
    }
    return load_template_manifest(manifest)


def template_summary(manifest):
    """The browser-safe card projection (no world source, no layout)."""
    return {
        "template_id": manifest["template_id"],
        "name": manifest["name"],
        "short_description": manifest["short_description"],
        "purpose": manifest["purpose"],
        "difficulty": manifest["difficulty"],
        "world_semantic_id": manifest["world_semantic_id"],
        "default_scenario_document_id": manifest["default_scenario_document_id"],
        "scenario_names": [d["name"] for d in manifest["scenarios"]],
        "suggested_first_edit": manifest["suggested_first_edit"],
        "expected_edit_effect": manifest["expected_edit_effect"],
    }


# ------------------------------------------------------------------- catalog
class TemplateCatalog(object):
    """The loaded, schema-validated, identity-verified template catalog. Built
    from an allowlisted release directory holding `catalog.json` (an ordered
    index of {template_id, file}) plus one manifest JSON per template. A load
    FAILS CLOSED on any schema/index violation or identity drift -- a corrupted
    template is never surfaced."""

    def __init__(self, templates):
        self._templates = list(templates)          # ordered manifests
        self._by_id = {t["template_id"]: t for t in self._templates}

    # -- accessors --------------------------------------------------------
    @property
    def count(self):
        return len(self._templates)

    def ids(self):
        return [t["template_id"] for t in self._templates]

    def manifests(self):
        return [copy.deepcopy(t) for t in self._templates]

    def summaries(self):
        return [template_summary(t) for t in self._templates]

    def get(self, template_id):
        t = self._by_id.get(template_id)
        return copy.deepcopy(t) if t is not None else None

    def has(self, template_id):
        return template_id in self._by_id

    # -- loading ----------------------------------------------------------
    @classmethod
    def load_dir(cls, directory):
        """Load + fully verify the catalog under `directory`. Reads
        `catalog.json` for the ordered index, then loads/validates/verifies each
        referenced manifest. Raises WrlValidationError on any failure."""
        index_path = os.path.join(directory, "catalog.json")
        if not os.path.isfile(index_path):
            WC._fail(WRL_BAD_CATALOG, "missing catalog index %s" % index_path)
        with open(index_path, "r") as f:
            index = json.load(f)
        if not isinstance(index, dict) \
                or index.get("catalog_version") != CATALOG_VERSION:
            WC._fail(WRL_BAD_CATALOG,
                     "bad catalog_version %r (only %s)"
                     % (index.get("catalog_version") if isinstance(index, dict)
                        else index, CATALOG_VERSION))
        entries = index.get("templates")
        if not (isinstance(entries, list) and entries):
            WC._fail(WRL_BAD_CATALOG, "catalog templates must be a non-empty list")
        templates, seen = [], set()
        for i, entry in enumerate(entries):
            if not isinstance(entry, dict) \
                    or "template_id" not in entry or "file" not in entry:
                WC._fail(WRL_BAD_CATALOG,
                         "catalog entry %d must be {template_id, file}" % i)
            tid, fname = entry["template_id"], entry["file"]
            if tid in seen:
                WC._fail(WRL_BAD_CATALOG,
                         "duplicate template_id %r in catalog" % tid)
            seen.add(tid)
            fpath = os.path.join(directory, os.path.basename(fname))
            if not os.path.isfile(fpath):
                WC._fail(WRL_BAD_CATALOG,
                         "catalog references missing file %s" % fname)
            with open(fpath, "r") as f:
                manifest = json.load(f)
            load_template_manifest(manifest)
            if manifest["template_id"] != tid:
                WC._fail(WRL_BAD_CATALOG,
                         "catalog entry id %r != manifest id %r"
                         % (tid, manifest["template_id"]))
            templates.append(manifest)
        return cls(templates)
