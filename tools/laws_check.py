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

It also checks the reverse direction, which is the one that used to be unguarded:

  * BROKEN WITNESS    -- LAWS.md cites `path:line` evidence that does not
                         resolve (file missing, or shorter than the cited line) (ERROR)
  * UNRESOLVED REF    -- a path-only reference naming a file found nowhere      (WARN)

The reverse direction matters because the forward scan matches the *string*
"Law N". Move a witness file and the forward scan stays green -- it finds the law
mentioned at the new path and reports OK -- while every `path:line` in LAWS.md
pointing into that file silently rots. So the witness spans are PARSED (paths,
line lists, ranges, and bare `:NNN` continuations that inherit the preceding
path), not pattern-matched around.

Exit status: non-zero if any ORPHAN CITATION, RESERVED-LAW citation, or BROKEN
WITNESS is found, or if any UNRATIFIED AUTHORITY is found under --strict.

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


# --- witness citations -----------------------------------------------------------
# LAWS.md backs each law with evidence written as inline code spans:
#
#     `forge/binding_run3.py:177`          path + one line
#     `forge/fixture.py:5-6`               path + a line RANGE
#     `forge/MANIFEST.md:69,70`            path + several lines
#     `:1548`                              a BARE continuation of the previous path
#     `LAW_RATIFICATION_2026-07-22.md`     a path with no line at all
#     `cost_report`                        prose, not a citation
#
# Until now nothing checked these. That mattered more than it looks: the scan above
# finds a law by the *string* "Law 6", so moving a witness file leaves the scan green
# while every `path:line` pointing into it silently rots. A checker whose whole purpose
# is verified citation has to READ the citations, not pattern-match around them.
SPAN_RE = re.compile(r"`([^`]+)`")
# A precise citation: a path with an extension, then one or more line numbers/ranges.
PRECISE_RE = re.compile(r"^(?P<path>[A-Za-z0-9_][A-Za-z0-9_./+-]*\.[A-Za-z0-9]+)"
                        r":(?P<lines>\d+(?:-\d+)?(?:,\s*\d+(?:-\d+)?)*)$")
# A bare continuation -- ":1548" -- inherits the previous path in the same law block.
CONT_RE = re.compile(r"^:(?P<lines>\d+(?:-\d+)?(?:,\s*\d+(?:-\d+)?)*)$")
# A path-only reference, no line claim.
PATHONLY_RE = re.compile(r"^(?P<path>[A-Za-z0-9_][A-Za-z0-9_./+-]*\.[A-Za-z0-9]+)$")

_LINECOUNT_CACHE = {}


def _line_count(abspath):
    if abspath not in _LINECOUNT_CACHE:
        try:
            with open(abspath, encoding="utf-8", errors="replace") as f:
                _LINECOUNT_CACHE[abspath] = sum(1 for _ in f)
        except OSError:
            _LINECOUNT_CACHE[abspath] = -1
    return _LINECOUNT_CACHE[abspath]


def _max_line(lines_field):
    hi = 0
    for part in lines_field.split(","):
        for n in part.split("-"):
            n = n.strip()
            if n.isdigit():
                hi = max(hi, int(n))
    return hi


def check_witnesses():
    """Parse LAWS.md's evidence spans and verify each one resolves.

    Returns (broken, unresolved, checked) where `broken` are PRECISE citations
    (`path:line`) whose file is missing or too short -- a hard error, because the
    citation makes a claim about a specific line -- and `unresolved` are path-only
    references naming a file that exists nowhere, which is only a warning since prose
    may name a file loosely (`synth_async.py` for `research/synth_async.py`).
    """
    broken, unresolved, checked = [], [], 0
    basenames = {}
    for path in _iter_files():
        basenames.setdefault(os.path.basename(path), []).append(path)

    law_id, last_path, lineno = None, None, 0
    with open(LAWS_MD, encoding="utf-8") as f:
        for lineno, line in enumerate(f, 1):
            m = DEF_RE.match(line)
            if m:
                nums = [int(n) for n in re.findall(r"\d+", m.group(1))]
                law_id = nums[0] if nums else None
                last_path = None          # a new law block starts a new path scope
                continue
            for span in SPAN_RE.findall(line):
                span = span.strip()
                pm = PRECISE_RE.match(span)
                cm = CONT_RE.match(span) if not pm else None
                if pm:
                    rel, lines_field = pm.group("path"), pm.group("lines")
                    last_path = rel
                elif cm:
                    if last_path is None:
                        broken.append((law_id, lineno, span,
                                       "bare line continuation with no preceding path"))
                        continue
                    rel, lines_field = last_path, cm.group("lines")
                else:
                    om = PATHONLY_RE.match(span)
                    if om:
                        rel = om.group("path")
                        abspath = os.path.join(TRVM_ROOT, rel)
                        if os.path.exists(abspath):
                            last_path = rel
                        elif os.path.basename(rel) not in basenames:
                            unresolved.append((law_id, lineno, span))
                    continue

                checked += 1
                abspath = os.path.join(TRVM_ROOT, rel)
                if not os.path.exists(abspath):
                    broken.append((law_id, lineno, span, "file does not exist"))
                    continue
                have = _line_count(abspath)
                want = _max_line(lines_field)
                if have >= 0 and want > have:
                    broken.append((law_id, lineno, span,
                                   f"cites line {want} but file has {have}"))
    return broken, unresolved, checked


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
    broken_witnesses, unresolved_witnesses, n_witnesses = check_witnesses()

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
    print(f"witness path:line spans : {n_witnesses} parsed from LAWS.md")
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

    if broken_witnesses:
        print("ERROR -- BROKEN WITNESS (LAWS.md cites a path:line that does not resolve)")
        print("-" * 52)
        for law_id, ln, span, why in broken_witnesses:
            law = f"Law {law_id}" if law_id is not None else "(preamble)"
            print(f"  {law} at LAWS.md:{ln} -- `{span}`: {why}")
        print()

    if unresolved_witnesses:
        print("WARN -- UNRESOLVED REFERENCE (named file found nowhere in the tree)")
        print("-" * 52)
        for law_id, ln, span in unresolved_witnesses:
            law = f"Law {law_id}" if law_id is not None else "(preamble)"
            print(f"  {law} at LAWS.md:{ln} -- `{span}`")
        print()

    if uncited:
        print("INFO -- laws defined but not cited anywhere in the live tree")
        print("-" * 52)
        print("  " + ", ".join(f"Law {n}" for n in uncited))
        print()

    fail = (bool(orphans) or bool(reserved_cited) or bool(broken_witnesses)
            or (strict and bool(unratified)))
    print("RESULT:", "FAIL" if fail else "OK")
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main())
