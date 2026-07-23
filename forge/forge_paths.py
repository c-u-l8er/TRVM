"""forge_paths.py -- external cache locations + transactional native build.

v0.6.5.1 (Read-Only Installation Closure). GPT-5.6's ruling: a distributable
Forge release must be a READ-ONLY installation -- launching it (reference OR
native) must leave the extracted tree byte-identical. Two things used to write
back into the install dir:

  * Python bytecode:  first `import` wrote `<install>/forge/__pycache__/*.pyc`.
  * the native reducer: the launcher compiled `<install>/runtime/c/ic32`.

Both now live in an EXTERNAL, per-OS cache directory. This module owns those
locations and the transactional native build, so both the launcher and the
server agree on where the ic32 binary and the python bytecode go.

Cache layout (honoring FORGE_RUNTIME_CACHE, else the per-OS cache dir):

    <cache_root>/runtime/ic32-<source-sha256>-<os>-<arch>[.exe]
    <cache_root>/pycache/py<major><minor>/...

The native binary is keyed by (source sha256, os, arch) so multiple installed
Forge versions can share one compatible binary AND an edited `ic32.c`
auto-rebuilds under a fresh key. The build is transactional: compile a temp
binary in the cache dir, verify it is a nonzero executable, then atomically
`os.replace` it into place -- a crash never leaves a half-written binary that a
later launch would trust.
"""
import hashlib
import os
import platform
import stat
import subprocess
import sys
import tempfile


def _home():
    return os.path.expanduser("~")


def cache_root():
    """The external Forge cache root. FORGE_RUNTIME_CACHE overrides; otherwise
    the per-OS user cache directory. Never inside the install tree."""
    env = os.environ.get("FORGE_RUNTIME_CACHE")
    if env:
        return os.path.abspath(env)
    if sys.platform == "darwin":
        return os.path.join(_home(), "Library", "Caches", "TRVM Forge")
    if os.name == "nt":
        base = os.environ.get("LOCALAPPDATA") or os.path.join(
            _home(), "AppData", "Local")
        return os.path.join(base, "TRVM Forge", "cache")
    # Linux / other POSIX: XDG_CACHE_HOME or ~/.cache
    base = os.environ.get("XDG_CACHE_HOME") or os.path.join(_home(), ".cache")
    return os.path.join(base, "trvm-forge")


def runtime_cache_dir():
    """Where compiled native reducers live (external)."""
    return os.path.join(cache_root(), "runtime")


def _python_tag():
    return "py%d%d" % (sys.version_info[0], sys.version_info[1])


def pycache_prefix():
    """External PYTHONPYCACHEPREFIX target -- keeps `.pyc` out of the install
    while retaining bytecode caching perf. Per python-version so a mixed-python
    machine never collides."""
    return os.path.join(cache_root(), "pycache", _python_tag())


def _platform_tag():
    system = (platform.system() or "unknown").lower()
    machine = (platform.machine() or "unknown").lower()
    return "%s-%s" % (system, machine)


def _sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def ic32_cache_path(source_path):
    """The canonical external path of the compiled ic32 for THIS `ic32.c`
    (keyed by source sha256 + os + arch). Deterministic; does not build."""
    digest = _sha256_file(source_path)
    name = "ic32-%s-%s" % (digest, _platform_tag())
    if os.name == "nt":
        name += ".exe"
    return os.path.join(runtime_cache_dir(), name)


def _which(name):
    for d in os.environ.get("PATH", "").split(os.pathsep):
        p = os.path.join(d, name)
        if os.path.isfile(p) and os.access(p, os.X_OK):
            return p
    return None


def find_cc():
    """Locate a C compiler: $CC, then gcc/clang/cc. None if none found."""
    return os.environ.get("CC") or _which("gcc") or _which("clang") \
        or _which("cc")


def _is_runnable_binary(path):
    try:
        return os.path.isfile(path) and os.path.getsize(path) > 0 \
            and os.access(path, os.X_OK)
    except OSError:
        return False


def ensure_ic32(source_path, cc=None):
    """Return an executable ic32 path for `source_path`, building into the
    EXTERNAL cache if necessary. Never writes into the install tree.

    Precedence:
      1. TRVM_IC32_PATH, if it names a runnable binary (explicit override);
      2. the content-addressed cache path, if it already holds a runnable
         binary (reuse across installs / launches);
      3. a fresh transactional compile into the cache.

    Returns the path on success, or None if there is no compiler or the build
    fails (the launcher then degrades to reference-only)."""
    override = os.environ.get("TRVM_IC32_PATH")
    if override and _is_runnable_binary(override):
        return override

    if not os.path.isfile(source_path):
        return None

    target = ic32_cache_path(source_path)
    if _is_runnable_binary(target):
        return target

    cc = cc or find_cc()
    if not cc:
        return None

    cdir = runtime_cache_dir()
    os.makedirs(cdir, exist_ok=True)

    # transactional: compile a temp binary in the cache dir, verify, then
    # atomically rename into the content-addressed target.
    fd, tmp = tempfile.mkstemp(prefix=".ic32-build-", dir=cdir)
    os.close(fd)
    try:
        try:
            subprocess.run([cc, "-O2", "-o", tmp, source_path],
                           check=True)
        except (subprocess.CalledProcessError, OSError):
            return None
        try:
            os.chmod(tmp, os.stat(tmp).st_mode | stat.S_IXUSR | stat.S_IXGRP
                     | stat.S_IXOTH)
        except OSError:
            pass
        if not _is_runnable_binary(tmp):
            return None
        os.replace(tmp, target)  # atomic
        tmp = None
        return target if _is_runnable_binary(target) else None
    finally:
        if tmp and os.path.exists(tmp):
            try:
                os.remove(tmp)
            except OSError:
                pass
