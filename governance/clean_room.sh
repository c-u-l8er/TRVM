#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════════════════
#  clean_room.sh — v0.1.0 — THE PRIVATE VIEW IS BUILT BEFORE IT IS VERIFIED
#  law:proof.mount-is-a-private-object@1
#
#  P4.7.8 promised this sequence:
#
#      emit → verify → bind read-only → start the model
#
#  and GPT proved it insufficient at P4.7.9. Two things are wrong with it. The
#  read-only bind is applied to a tree that already existed, so any other name
#  for those inodes — a hard link, a second bind, an open descriptor — still
#  writes to them; and the verification happens BEFORE the final topology
#  exists, so what was verified is not what the model reads.
#
#  So the order is inverted and the filesystem is new:
#
#      unshare a mount namespace
#          ↓
#      mount a fresh tmpfs at the mount point
#          ↓
#      emit the package into it FROM THE MANIFEST      new inodes · nlink 1
#          ↓                                           exactly the pinned bpkg
#      remount it READ-ONLY
#          ↓
#      verify THE FINAL VIEW, in the process that will serve it
#          ↓
#      exec the broker — the namespace is never touched again
#
#  WHY A tmpfs INSIDE A NAMESPACE AND NOT A BIND MOUNT. A bind is a second name
#  for an existing filesystem, which is the very thing being defended against; a
#  tmpfs created here has no contents until we write them, no name outside this
#  namespace, and no descriptor older than itself. `ls` from any other process on
#  this machine shows an empty directory. There is no alias to create, so there
#  is nothing to check for — which is a stronger statement than any check.
#
#  WHY `exec`. The broker REPLACES this shell. Nothing else ever runs in the
#  namespace, so no later step can re-mount, re-point or re-populate the view
#  between the verification and the first model request. That window is the one
#  P4.7.8's `--verify-mount` was invented to close and could not.
#
#  AND THE VERIFICATION IS NOT A SEPARATE STEP. `clean_room.mjs` verifies as its
#  first act and serves from the bytes it verified. This script does not verify
#  and hand over a pathname: verifying one name and later resolving another is
#  exactly the defect, one layer up.
#
#  THREAT CEILING, UNCHANGED AND STATED: root on the host can falsify any of
#  this deliberately. We are removing ordinary aliasing and TOCTOU, not solving
#  a hostile kernel.
# ═══════════════════════════════════════════════════════════════════════════
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BLIND="${CLEAN_ROOM_MOUNT:-${TMPDIR:-/tmp}/trvm-blind-$$}"
WORK="${CLEAN_ROOM_WORKSPACE:-$HERE/clean-room/workspace-$$}"

if [ "${1:-}" = "--help" ]; then
  # DERIVED, NOT COUNTED. This was `sed -n '2,52p'` and the header had since
  # grown past 52, so --help printed `set -euo pipefail` as if it were prose. A
  # hand-typed line number drifting away from the thing it points at is the same
  # species as a hand-typed law count, in the file whose subject is that a
  # default or a constant which happens to be right is not a guarantee.
  awk 'NR==1 { next } /^# \xe2\x95\x90/ { c++ } { sub(/^# ?/, ""); print } c == 2 { exit }' \
    "${BASH_SOURCE[0]}"
  echo
  echo "usage: clean_room.sh [--selftest] [--model ID] [--max-turns N] [--seed N]"
  echo "  CLEAN_ROOM_MOUNT      mount point for the private tmpfs (default: a fresh \$TMPDIR path)"
  echo "  CLEAN_ROOM_WORKSPACE  the candidate's writable tree (default: governance/clean-room/…)"
  echo "  OPENROUTER_API_KEY    required unless --selftest"
  exit 0
fi

command -v unshare >/dev/null || { echo "CLEAN-ROOM: unshare(1) is not available"; exit 2; }

mkdir -p "$BLIND"
[ -z "$(ls -A "$BLIND")" ] || { echo "CLEAN-ROOM: $BLIND is not empty"; exit 1; }

#  EVERYTHING FROM HERE RUNS IN ONE PROCESS TREE INSIDE ONE NAMESPACE.
#  `--map-root-user` is what makes an unprivileged mount possible; `--mount`
#  is what makes the result invisible to every other process on the machine.
#  `--propagation private` IS STATED RATHER THAN INHERITED. It is unshare(1)'s
#  default, and the host's /tmp and / are both `shared` here, so a mount created
#  under `unchanged` propagation would be pushed BACK into the parent namespace —
#  where it would have a name outside, which is the whole property this script
#  exists to establish. A default that happens to be right is not a guarantee,
#  and the one thing this script must not do is inherit its central claim.
exec unshare --mount --map-root-user --propagation private -- /usr/bin/env bash -euo pipefail -c '
  BLIND="$1"; WORK="$2"; HERE="$3"; shift 3

  mount -t tmpfs -o "size=64m,mode=0755" tmpfs "$BLIND"

  #  THE PACKAGE IS EMITTED, NOT COPIED. `--emit` writes file by file from the
  #  manifest and refuses a package the run never pinned, so the private view is
  #  the pinned bpkg by construction. `cp -a` would have preserved hard links
  #  within the source tree, which is the defect wearing a hat.
  node "$HERE/blind_package.mjs" --emit "$BLIND" >/dev/null

  #  READ-ONLY, AND THE STRONG SENSE OF IT. THIS IS WHERE THE OBVIOUS FIX WOULD
  #  HAVE REPRODUCED THE DEFECT IT IS FIXING. The natural spelling here is
  #
  #      mount -o remount,bind,ro "$BLIND"
  #
  #  and it is the WRONG ONE. It sets MS_RDONLY on this MOUNT POINT and leaves
  #  the SUPERBLOCK read-write — measured: mountinfo still reads `rw`, a second
  #  bind of it can be remounted `rw`, and writes through that name succeed. That
  #  is precisely the distinction GPT cited from mount(8) when reporting the hard
  #  link, so taking it here would have put a read-only name over a writable
  #  filesystem inside the repair for a read-only name over a writable file.
  #
  #  `--options-source=disable` is what makes the real superblock remount
  #  possible: libmount otherwise re-applies the options it recorded in its own
  #  userspace table, which name the OUTER uid (1000) — unmapped in this
  #  namespace, so the remount fails with `Invalid uid` and a `set -e` script
  #  dies at the one step it must not skip.
  mount --options-source=disable -o remount,ro "$BLIND"
  mount -o remount,bind,ro "$BLIND"           # and the mount-point flag as well

  #  AND THE RESULT IS ASSERTED, NOT ASSUMED. A command that exits 0 has reported
  #  on itself. These ask the kernel, through the one file that answers.
  #
  #  mountinfo: `id parent maj:min root MOUNTPOINT opts [optional...] - fs src`.
  #  The optional fields carry `shared:N` if and only if the mount is in a peer
  #  group — that is, if and only if it propagates. Its ABSENCE is the property
  #  "this filesystem has no name outside this namespace", checked at its cause
  #  and at the moment it matters, rather than inferred afterwards from a
  #  mountpoint that would be empty either way.
  LINE=$(awk -v m="$BLIND" '"'"'$5 == m { last = $0 } END { print last }'"'"' /proc/self/mountinfo)
  [ -n "$LINE" ] || { echo "CLEAN-ROOM: REFUSED — no mount at $BLIND"; exit 1; }
  case "${LINE%% - *}" in
    *shared:*) echo "CLEAN-ROOM: REFUSED — $BLIND is in a mount peer group and PROPAGATES, so the" \
                    "clean room has a name outside this namespace: ${LINE%% - *}"; exit 1 ;;
  esac
  case "${LINE%% - *}" in
    *" ro,"*|*" ro "*|*,ro,*|*,ro" "*) : ;;
    *) echo "CLEAN-ROOM: REFUSED — $BLIND did not come back read-only: ${LINE%% - *}"; exit 1 ;;
  esac
  if ( : > "$BLIND/.write-probe" ) 2>/dev/null; then
    echo "CLEAN-ROOM: REFUSED — $BLIND accepted a write after being remounted read-only"; exit 1
  fi
  echo "CLEAN-ROOM: PRIVATE — $BLIND is a tmpfs with no peer group (it cannot propagate to any" \
       "other namespace) and a read-only superblock (a second bind of it cannot be made writable)."

  exec node "$HERE/clean_room.mjs" --mount "$BLIND" --workspace "$WORK" "$@"
' _ "$BLIND" "$WORK" "$HERE" "$@"
