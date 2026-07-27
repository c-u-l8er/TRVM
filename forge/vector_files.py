"""The committed vector files, and a check that these are actually them.

The vectors live in the WRL repository. The Forge probes run from a COPY of
`forge/`, so they read copies -- and a copy is the one part of this arrangement
that can rot without anything noticing. A stale `_vectors.json` does not make a
probe fail; it makes the Python side agree with a record the JS side stopped
sending, which is worse than a red, because the whole point of a shared corpus
is that the two implementations are held to THE SAME BYTES. Two implementations
agreeing about different bytes is the exact failure this corpus exists to rule
out, and it would present as a clean run.

So the digests are pinned here. Updating a vector file means updating a hash in
this file, deliberately, in the same commit -- the same golden-file discipline
the wire vectors themselves use, applied one level up to the transport.

Source of truth:  WRL/test/projection-vectors.json
                  WRL/test/projection-negative-vectors.json
"""
import hashlib
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))

# sha256 of the file as committed in WRL/test/.
DIGESTS = {
    "_vectors.json":
        "31aa192db11cb6500f3a96b7b9d9cf9d9d39711bc728bc46f4d16f42e59b6314",
    "_negative_vectors.json":
        "81ee1a37f4b9d0c35dc06f7cf10e49e1d69067b3813e7aeaf7c3afd4c5cb167e",
}


class StaleVectorFile(Exception):
    """A vector copy is not the file it claims to be."""


def load(basename):
    """Return the parsed vector document, or raise if the copy is not current.

    Raising rather than warning is deliberate: a probe that continued against
    an unknown corpus would still print a row of `ok`s, and those would mean
    nothing at all.
    """
    path = os.path.join(HERE, basename)
    if not os.path.exists(path):
        raise StaleVectorFile(
            "%s is missing -- copy it from WRL/test/" % basename)
    raw = open(path, "rb").read()
    got = hashlib.sha256(raw).hexdigest()
    want = DIGESTS[basename]
    if got != want:
        raise StaleVectorFile(
            "%s is not the committed file.\n    want %s\n    got  %s\n"
            "    Either the copy is stale, or the vectors moved and this "
            "digest was not updated with them." % (basename, want, got))
    return json.loads(raw.decode("utf-8"))
