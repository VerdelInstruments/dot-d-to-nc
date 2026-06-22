"""Job-prefix and output-key helpers.

A run is isolated under a unique ``d2nc/<stamp>-<uuid>`` prefix so concurrent
runs never collide and cleanup can be scoped to exactly that prefix.

The S3 output key naming mirrors how ``extract_s3.py`` derives its upload keys:
given ``--output-key {job}/{stem}.nc`` it writes
``{job}/{stem}_timedomain.nc`` and ``{job}/{stem}_fourierdomain.nc``.
"""

import uuid
from datetime import datetime, timezone
from pathlib import Path

JOB_ROOT = "d2nc"


def make_job_prefix():
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    return f"{JOB_ROOT}/{stamp}-{uuid.uuid4().hex[:8]}"


def input_prefix(job, d_path):
    """Keep the ``.d`` folder name so extract_s3's .d detection fires."""
    return f"{job}/{Path(d_path).name}/"


def output_key(job, d_path):
    return f"{job}/{Path(d_path).stem}.nc"


def domain_keys(job, d_path):
    """Full S3 keys of the two outputs (matches extract_s3's replace logic)."""
    base = f"{job}/{Path(d_path).stem}"
    return {
        "timedomain": f"{base}_timedomain.nc",
        "fourierdomain": f"{base}_fourierdomain.nc",
    }


def domain_filenames(d_path):
    """Local output basenames as written by extractor_class.extract_and_save."""
    stem = Path(d_path).stem
    return {
        "timedomain": f"{stem}_timedomain.nc",
        "fourierdomain": f"{stem}_fourierdomain.nc",
    }
