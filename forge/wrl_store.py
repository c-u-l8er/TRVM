"""wrl_store.py v0.5-1 -- immutable content-addressed object stores (Forge World
Library, phase 1).

GPT-5.6's v0.5 ruling is the Forge World Library / project persistence. Phase
v0.5-1 lays the IMMUTABLE substrate: three filesystem-backed, content-addressed
object stores, each keyed by an existing identity from the frozen identity
ladder (wrl_scenario.py) -- NO new identity, NO new runtime construct:

    WorldObjectStore     keyed by SemanticArtifactID   (`sem-<64hex>`)
    ScenarioRuntimeStore keyed by ScenarioDigest        (`scen-<64hex>`)
    ReplayBundleStore    keyed by ReplayBundleID         (`replay-<64hex>`)

Every store obeys two laws:

  * CONTENT ADDRESSING -- the on-disk key IS the hash of the stored canonical
    bytes. A put recomputes the id from the bytes and REFUSES to persist a
    mislabeled object; writes are naturally idempotent (same content -> same id
    -> same file). Reorder-/label-equivalent inputs collapse to one file.

  * HASH-VERIFIED READ -- every get re-hashes the file bytes and refuses to
    return an object whose content no longer matches its key (WRL_STORE_CORRUPT).
    So bit-rot or tampering surfaces as a TYPED diagnostic, never silent bad data.

Persistence is the standard atomic-write law (GPT-5.6): validate -> serialize ->
write a temp file -> flush + fsync -> atomic rename (+ fsync the directory). A
crash mid-write can only leave a `.tmp-*` stub, never a torn object file, and the
rename is durable. The stores hold NO in-memory index -- a fresh instance over
the same root sees exactly what is on disk.

These stores are pure library objects taking an explicit filesystem root; wiring
them behind the live endpoints (ProjectStore + session cache) is v0.5-3. Nothing
here touches the runtime/backend, so this phase is REF-only by nature; the sibling
battery (binding_run24.py) still anchors ONE native check proving a world routed
THROUGH the store folds ic_ref == ic32 == the Fixture oracle (N8).
"""
import os
import re
import tempfile

import wrl_canonical as WC
import wrl_scenario as SC

# typed diagnostics (the store contract) -- never a raw OSError/KeyError crosses
WRL_STORE_MISSING = "WRL_STORE_MISSING"        # get of an absent id
WRL_STORE_CORRUPT = "WRL_STORE_CORRUPT"        # on-disk bytes != their key hash
WRL_STORE_ID_MISMATCH = "WRL_STORE_ID_MISMATCH"  # put content != the claimed id
WRL_STORE_BAD_REF = "WRL_STORE_BAD_REF"        # malformed reference in a bundle

_SCEN_ID_RE = re.compile(r"^scen-[0-9a-f]{64}$")
_REPLAY_ID_RE = re.compile(r"^replay-[0-9a-f]{64}$")


# ---------------------------------------------------------- the persistence law
def _atomic_write(path, blob):
    """validate(caller) -> serialize(caller) -> temp file -> flush+fsync ->
    atomic rename (+ dir fsync). The only durable write primitive in the store;
    a crash leaves at most a `.tmp-*` stub, never a torn object file."""
    directory = os.path.dirname(path)
    fd, tmp = tempfile.mkstemp(dir=directory, prefix=".tmp-", suffix=".part")
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(blob)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)          # atomic on POSIX
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise
    # make the rename itself durable (best-effort; some filesystems disallow it)
    try:
        dfd = os.open(directory, os.O_RDONLY)
        try:
            os.fsync(dfd)
        finally:
            os.close(dfd)
    except OSError:
        pass


# --------------------------------------------------------- content-addressed base
class _ContentStore:
    """A directory of `<id>.json` files whose name IS the hash of their bytes.
    Subclasses supply the id prefix and the hash-to-id function."""
    _PREFIX = None

    def __init__(self, root):
        self._root = root
        os.makedirs(root, exist_ok=True)

    def _id_of(self, blob):
        return self._PREFIX + WC._sha(blob)

    def _path(self, oid):
        return os.path.join(self._root, oid + ".json")

    def _put_bytes(self, oid, blob):
        """Persist canonical bytes under their own content id (idempotent).
        Refuses to write bytes whose hash != the claimed id, and refuses to
        overwrite an existing file whose bytes differ (impossible under content
        addressing, so a difference means corruption)."""
        computed = self._id_of(blob)
        if computed != oid:
            WC._fail(WRL_STORE_ID_MISMATCH,
                     "refusing to store object as %r; its content hashes to %r"
                     % (oid, computed))
        path = self._path(oid)
        if os.path.exists(path):
            with open(path, "rb") as f:
                existing = f.read()
            if existing != blob:
                WC._fail(WRL_STORE_CORRUPT,
                         "on-disk object %r differs from its content hash" % oid)
            return oid
        _atomic_write(path, blob)
        return oid

    def _get_bytes(self, oid):
        """Read + HASH-VERIFY. WRL_STORE_MISSING if absent, WRL_STORE_CORRUPT if
        the bytes no longer hash to their key."""
        path = self._path(oid)
        if not os.path.exists(path):
            WC._fail(WRL_STORE_MISSING, "no object %r in store" % oid)
        with open(path, "rb") as f:
            blob = f.read()
        computed = self._id_of(blob)
        if computed != oid:
            WC._fail(WRL_STORE_CORRUPT,
                     "object %r failed hash verification (bytes hash to %r)"
                     % (oid, computed))
        return blob

    def has(self, oid):
        return os.path.exists(self._path(oid))

    def ids(self):
        """Every stored id, sorted. Non-object files are ignored."""
        try:
            names = os.listdir(self._root)
        except OSError:
            return []
        return sorted(n[:-5] for n in names
                      if n.endswith(".json") and n.startswith(self._PREFIX))


# ------------------------------------------------------------- WorldObjectStore
class WorldObjectStore(_ContentStore):
    """Immutable store of sealed world artifacts keyed by SemanticArtifactID.
    Stores the SealedArtifact's frozen CANONICAL BYTES; on read it re-seals a
    fresh copy so the returned world is validated AND re-verified to reproduce
    its key (integrity below the raw hash, 3D.1.1 discipline)."""
    _PREFIX = "sem-"

    def put(self, artifact):
        """Seal (if needed) and persist a world; returns its SemanticArtifactID."""
        sealed = artifact if isinstance(artifact, WC.SealedArtifact) \
            else WC.seal_artifact(artifact)
        return self._put_bytes(sealed.semantic_id, sealed.canonical_bytes)

    def get(self, sem_id):
        """Return a fresh SealedArtifact for `sem_id` (hash-verified twice: raw
        bytes vs key, then re-seal must reproduce the id)."""
        blob = self._get_bytes(sem_id)
        sealed = WC.seal_artifact(WC.deserialize_artifact(blob))
        if sealed.semantic_id != sem_id:
            WC._fail(WRL_STORE_CORRUPT,
                     "world %r re-seals to %r" % (sem_id, sealed.semantic_id))
        return sealed


# --------------------------------------------------------- ScenarioRuntimeStore
class ScenarioRuntimeStore(_ContentStore):
    """Immutable store of canonical RUN INPUTS keyed by ScenarioDigest. It stores
    the digest DOMAIN only -- `{initial_runtime, epoch_batches}` -- exactly what
    the ScenarioDigest is over, so it is world-id- AND label-independent by
    construction: a label-only or world-rebind edit collapses to the same file."""
    _PREFIX = "scen-"

    def put(self, scenario):
        """Canonicalize a ScenarioV1 and persist its runtime domain; returns the
        ScenarioDigest (== wrl_scenario.scenario_digest)."""
        canon = SC.canonicalize_scenario_v1(scenario)
        blob = WC.serialize_artifact(SC._digest_domain(canon))
        return self._put_bytes(self._PREFIX + WC._sha(blob), blob)

    def get(self, scen_digest):
        """Return the stored runtime domain `{initial_runtime, epoch_batches}`."""
        return WC.deserialize_artifact(self._get_bytes(scen_digest))


# ------------------------------------------------------------- ReplayBundleStore
class ReplayBundleStore(_ContentStore):
    """Immutable store of replay bundles keyed by ReplayBundleID. A bundle binds
    one concrete run: a world (SemanticArtifactID), a scenario (ScenarioDigest)
    and its initial runtime. References are format-checked before hashing so a
    malformed bundle is a TYPED WRL_STORE_BAD_REF, not a late hash surprise."""
    _PREFIX = "replay-"

    def put(self, world_semantic_id, scen_digest, initial_runtime):
        """Persist a replay bundle; returns the ReplayBundleID
        (== wrl_scenario.replay_bundle_id)."""
        if not (isinstance(world_semantic_id, str)
                and WC._SEM_ID_RE.match(world_semantic_id)):
            WC._fail(WRL_STORE_BAD_REF,
                     "bad world_semantic_id %r" % (world_semantic_id,))
        if not (isinstance(scen_digest, str) and _SCEN_ID_RE.match(scen_digest)):
            WC._fail(WRL_STORE_BAD_REF, "bad scenario_digest %r" % (scen_digest,))
        if not (isinstance(initial_runtime, dict)
                and isinstance(initial_runtime.get("numeric_faults"), list)):
            WC._fail(WRL_STORE_BAD_REF,
                     "initial_runtime must be {numeric_faults:[...]}")
        body = [world_semantic_id, scen_digest,
                {"numeric_faults": sorted(initial_runtime["numeric_faults"])}]
        blob = WC.serialize_artifact(body)
        return self._put_bytes(self._PREFIX + WC._sha(blob), blob)

    def get(self, replay_id):
        """Return the stored bundle `[world_semantic_id, scen_digest,
        {numeric_faults}]`."""
        if not (isinstance(replay_id, str) and _REPLAY_ID_RE.match(replay_id)):
            WC._fail(WRL_STORE_BAD_REF, "bad replay id %r" % (replay_id,))
        return WC.deserialize_artifact(self._get_bytes(replay_id))
