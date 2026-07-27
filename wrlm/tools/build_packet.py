"""Rebuild the step-2 review packet, deterministically.

Two builds of the same tree must be byte-identical, so timestamps are pinned and
entries are written in a fixed order rather than whatever the filesystem hands
back. A packet whose bytes move on every build cannot be quoted by hash, and a
review that cannot quote a hash is reviewing something it hopes is the same.
"""

import hashlib
import os
import sys
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
WRLM = os.path.dirname(HERE)
TRVM = os.path.dirname(WRLM)

ENTRIES = [
    "wrlm/__init__.py", "wrlm/errors.py", "wrlm/worldview.py",
    "wrlm/goalspec.py", "wrlm/taskbundle.py", "wrlm/envelope.py",
    "wrlm/worldrecord.py", "wrlm/coverage.py", "wrlm/families.py",
    "wrlm/generator.py", "wrlm/tools/build_pool.py",
    "wrlm/tools/build_packet.py",
    "wrlm/test_goalspec.py", "wrlm/test_taskbundle.py",
    "wrlm/test_worldrecord.py", "wrlm/test_generator.py",
    "wrlm/fixtures/demo_world.artifact.json",
    "wrlm/fixtures/demo_lower_result.json",
    "wrlm/fixtures/pool.json", "wrlm/fixtures/pool_records.json",
    "WRLM_RESEARCH_BRIEF.md",
]

OUT = os.path.join(TRVM, "WRLM_STEP2_COVERAGE_GENERATOR_PACKET.zip")
STAMP = (1980, 1, 1, 0, 0, 0)


def main():
    lines = []
    for rel in ENTRIES:
        with open(os.path.join(TRVM, rel), "rb") as fh:
            lines.append("%s  %s" % (hashlib.sha256(fh.read()).hexdigest(), rel))
    manifest = "\n".join(lines) + "\n"

    with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED) as z:
        for rel in ENTRIES:
            info = zipfile.ZipInfo(rel, date_time=STAMP)
            info.external_attr = 0o644 << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            with open(os.path.join(TRVM, rel), "rb") as fh:
                z.writestr(info, fh.read())
        info = zipfile.ZipInfo("MANIFEST.sha256", date_time=STAMP)
        info.external_attr = 0o644 << 16
        info.compress_type = zipfile.ZIP_DEFLATED
        z.writestr(info, manifest.encode())

    with open(OUT, "rb") as fh:
        digest = hashlib.sha256(fh.read()).hexdigest()
    print("wrote %s" % OUT)
    print("  %d entries + MANIFEST.sha256" % len(ENTRIES))
    print("  sha256 %s" % digest)
    return 0


if __name__ == "__main__":
    sys.exit(main())
