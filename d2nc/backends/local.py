"""Local backend: call the existing in-process converter.

Wraps ``src/extract.py::extract_data``. Imports inside ``src/`` are bare
(``from extractor_class import ...``), so ``src/`` must be on ``sys.path`` —
located relative to this package, not the cwd.
"""

import sys
from pathlib import Path

from ..errors import InputError, LocalJobError
from ..naming import domain_filenames

SRC_DIR = Path(__file__).resolve().parents[2] / "src"


def _load_extract_data():
    if str(SRC_DIR) not in sys.path:
        sys.path.insert(0, str(SRC_DIR))
    try:
        from extract import extract_data  # noqa: E402 (bare import inside src/)
    except Exception as e:
        raise LocalJobError(
            f"could not import the local converter from {SRC_DIR}: {e}"
        ) from e
    return extract_data


def convert(d_path, out_dir, unique_swim_ids, instrument_frequency,
            include_timedomain=False):
    d_path = Path(d_path)
    out_dir = Path(out_dir)

    if not d_path.is_dir():
        raise InputError(f"{d_path} is not a directory (expected a Bruker .d folder)")
    if not (d_path / "analysis.baf").exists():
        raise InputError(
            f"{d_path} has no analysis.baf — not a valid Bruker .d directory")
    out_dir.mkdir(parents=True, exist_ok=True)

    extract_data = _load_extract_data()
    try:
        extract_data(str(d_path), str(out_dir), unique_swim_ids, instrument_frequency)
    except Exception as e:
        raise LocalJobError(f"local conversion failed: {e}") from e

    names = domain_filenames(d_path)
    fourier = out_dir / names["fourierdomain"]
    timedomain = out_dir / names["timedomain"]

    if not fourier.exists():
        raise LocalJobError(f"expected output {fourier} was not produced")

    results = []
    if include_timedomain and timedomain.exists():
        results.append(timedomain)
    elif timedomain.exists():
        # fourierdomain-only default: generate-then-discard (matches cloud).
        timedomain.unlink()
    results.append(fourier)
    return results
