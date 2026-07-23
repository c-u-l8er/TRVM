#!/usr/bin/env python3
"""laws_check.py -- constitution consistency checker for TRVM/LAWS.md.

Additive, read-only. Touches no frozen artifact. It cross-references the law
citations scattered through the live source tree against the canonical index in
LAWS.md, and reports the drift the LAWS.md was created to eliminate:

  * ORPHAN CITATION   -- code cites "Law N" that LAWS.md does not define  (ERROR)
  * RESERVED LAW CITED -- code cites a RESERVED id (no statement/authority) (ERROR)
  * UNRATIFIED AUTHORITY -- a .py battery cites a Tier-B (RECONSTRUCTED/
                          referenced) law as if it were binding             (WARN)
  * UNCITED LAW       -- LAWS.md defines a law nothing in code references    (INFO)

Exit status: non-zero if any ORPHAN CITATION or RESERVED-LAW citation is found,
or if any UNRATIFIED AUTHORITY is found under --strict.

Usage:
    python3 tools/laws_check.py            # report, fail only on orphans
    python3 tools/laws_check.py --strict   # also fail on unratified authority
"""
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TRVM_ROOT = os.path.dirname(HERE)
LAWS_MD = os.path.join(TRVM_ROOT, "LAWS.md")

# Directories that are snapshots, build output, or caches -- not the live tree.
SKIP_DIRS = {
    "TRVM_july_21_research", "dist", "__pycache__", ".git", ".forge_projects",
    ".recovery", ".objects", ".trash", "node_modules", "old_scrap",
}
SCAN_EXTS = (".py", ".md")

# A citation is "Law 5" or "Binding Law 5" (case-insensitive on the word).
CITE_RE = re.compile(r"\b(?:binding\s+law|law)\s+(\d+)\b", re.IGNORECASE)

# A LAWS.md heading: "### Law 5 — CANONICAL" or "### Laws 20, 21 — RECONSTRUCTED..."
DEF_RE = re.compile(r"^###\s+Laws?\s+([\d,\s]+?)\s+[—-]\s+(.+?)\s*$")


def _iter_files():
    for dirpath, dirnames, filenames in os.walk(TRVM_ROOT):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for fn in filenames:
            if fn.endswith(SCAN_EXTS):
                yield os.path.join(dirpath, fn)


def parse_laws_md():
    """Return {law_id: tier} where tier is 'CANONICAL', 'RESERVED', or 'TIER-B'."""
    defined = {}
    with open(LAWS_MD, encoding="utf-8") as f:
        for line in f:
            m = DEF_RE.match(line)
            if not m:
                continue
            nums = [int(n) for n in re.findall(r"\d+", m.group(1))]
            tier_phrase = m.group(2).upper()
            # A RESERVED law holds its ID but has no statement and no authority;
            # it may not be cited (checked as an error below).
            if tier_phrase.startswith("RESERVED"):
                tier = "RESERVED"
            else:
                # CANONICAL wins only if the heading leads with it and is not a
                # partial/referenced placeholder.
                canonical = (tier_phrase.startswith("CANONICAL")
                             and "PARTIAL" not in tier_phrase)
                tier = "CANONICAL" if canonical else "TIER-B"
            for n in nums:
                defined[n] = tier
    return defined


def collect_citations():
    """Return {law_id: [(relpath, lineno, is_python)]}."""
    cites = {}
    self_path = os.path.abspath(__file__)
    for path in _iter_files():
        rel = os.path.relpath(path, TRVM_ROOT)
        if rel == "LAWS.md":
            continue  # the definition source is not a citation source
        if os.path.abspath(path) == self_path:
            continue  # the checker's own docstring/examples are not citations
        is_py = path.endswith(".py")
        try:
            with open(path, encoding="utf-8", errors="replace") as f:
                for i, line in enumerate(f, 1):
                    for m in CITE_RE.finditer(line):
                        cites.setdefault(int(m.group(1)), []).append((rel, i, is_py))
        except OSError:
            continue
    return cites


def main():
    strict = "--strict" in sys.argv[1:]
    defined = parse_laws_md()
    cites = collect_citations()

    orphans = []          # (law_id, [locations]) cited but undefined
    reserved_cited = []   # (law_id, [locations]) RESERVED law cited anywhere
    unratified = []       # (law_id, [py locations]) Tier-B cited in .py
    for law_id in sorted(cites):
        locs = cites[law_id]
        if law_id not in defined:
            orphans.append((law_id, locs))
            continue
        if defined[law_id] == "RESERVED":
            reserved_cited.append((law_id, locs))
            continue
        if defined[law_id] == "TIER-B":
            py = [(r, ln) for (r, ln, is_py) in locs if is_py]
            if py:
                unratified.append((law_id, py))

    cited_ids = set(cites)
    uncited = sorted(law_id for law_id, tier in defined.items() if law_id not in cited_ids)

    print("TRVM constitution check  (LAWS.md vs live tree)")
    print("=" * 52)
    print(f"laws defined in LAWS.md : {len(defined)}  "
          f"({sum(1 for t in defined.values() if t == 'CANONICAL')} canonical, "
          f"{sum(1 for t in defined.values() if t == 'TIER-B')} tier-B, "
          f"{sum(1 for t in defined.values() if t == 'RESERVED')} reserved)")
    print(f"distinct laws cited     : {len(cited_ids)}")
    print()

    print("Citations")
    print("-" * 52)
    for law_id in sorted(cited_ids):
        tier = defined.get(law_id, "UNDEFINED")
        n = len(cites[law_id])
        print(f"  Law {law_id:<3} [{tier:<9}] {n} citation(s)")
        for rel, ln, _ in cites[law_id]:
            print(f"      {rel}:{ln}")
    print()

    if orphans:
        print("ERROR -- ORPHAN CITATIONS (cited law not defined in LAWS.md)")
        print("-" * 52)
        for law_id, locs in orphans:
            print(f"  Law {law_id}:")
            for rel, ln, _ in locs:
                print(f"      {rel}:{ln}")
        print()

    if reserved_cited:
        print("ERROR -- RESERVED LAW CITED (a RESERVED id has no authority "
              "and may not be cited)")
        print("-" * 52)
        for law_id, locs in reserved_cited:
            print(f"  Law {law_id} is RESERVED but is cited:")
            for rel, ln, _ in locs:
                print(f"      {rel}:{ln}")
        print()

    if unratified:
        print("WARN -- UNRATIFIED AUTHORITY (Tier-B law cited in .py code)")
        print("-" * 52)
        for law_id, py in unratified:
            print(f"  Law {law_id} is not yet CANONICAL but is cited as authority:")
            for rel, ln in py:
                print(f"      {rel}:{ln}")
        print()

    if uncited:
        print("INFO -- laws defined but not cited anywhere in the live tree")
        print("-" * 52)
        print("  " + ", ".join(f"Law {n}" for n in uncited))
        print()

    fail = bool(orphans) or bool(reserved_cited) or (strict and bool(unratified))
    print("RESULT:", "FAIL" if fail else "OK")
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main())
