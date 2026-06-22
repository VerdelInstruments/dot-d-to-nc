"""Auto-backend selection policy.

auto:  macOS -> cloud (no native converter);
       Windows/Linux -> local iff the bundled baf2sql lib is present AND there is
       enough free RAM; otherwise cloud.
"""

import os
import platform
from pathlib import Path

from .errors import DispatchError

# The native baf2sql lib ships in dot-d-to-nc/src (one level up from this package).
SRC_DIR = Path(__file__).resolve().parents[1] / "src"
LIB_BY_OS = {"Windows": "baf2sql_c.dll", "Linux": "libbaf2sql_c.so"}


def available_ram_gb():
    """Best-effort free RAM in GB, or None if it can't be determined."""
    try:
        import psutil

        return psutil.virtual_memory().available / (1024 ** 3)
    except Exception:
        pass
    try:
        return (os.sysconf("SC_PAGE_SIZE") * os.sysconf("SC_AVAIL_PHYS_PAGES")) / (1024 ** 3)
    except (ValueError, OSError, AttributeError):
        return None


def native_lib_present():
    name = LIB_BY_OS.get(platform.system())
    return bool(name) and (SRC_DIR / name).exists()


def choose_backend(requested, min_ram_gb=12.0):
    """Return ``(backend, reason)`` where backend is 'local' or 'cloud'.

    Raises DispatchError only for an impossible *explicit* choice
    (``--backend local`` on macOS).
    """
    system = platform.system()

    if requested == "local":
        if system == "Darwin":
            raise DispatchError(
                "local backend is unsupported on macOS (native baf2sql lib is "
                "Windows/Linux only). Use --backend cloud, or run the local path "
                "via the repo Docker image."
            )
        return "local", f"forced local on {system}"

    if requested == "cloud":
        return "cloud", "forced cloud"

    # auto
    if system == "Darwin":
        return "cloud", "macOS has no native converter"
    if system in ("Windows", "Linux"):
        if not native_lib_present():
            return "cloud", f"native baf2sql lib not found in {SRC_DIR}"
        ram = available_ram_gb()
        if ram is None:
            return "local", f"{system}, lib present, RAM unknown (assuming sufficient)"
        if ram >= min_ram_gb:
            return "local", f"{system}, lib present, {ram:.1f} GB free >= {min_ram_gb:.0f} GB"
        return "cloud", f"only {ram:.1f} GB free < {min_ram_gb:.0f} GB"
    return "cloud", f"unknown platform {system!r}"
