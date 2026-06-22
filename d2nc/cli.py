"""d2nc CLI — `python -m d2nc convert PATH.d [OUT_DIR] [params]`."""

import argparse
import sys

from . import __version__
from .awsutil import CREDENTIAL_ERROR_NAMES, make_session
from .dispatch import choose_backend
from .errors import D2ncError


def build_parser():
    p = argparse.ArgumentParser(
        prog="d2nc",
        description="Convert a Bruker .d to NetCDF (.nc) via a local or cloud backend.")
    p.add_argument("--version", action="version", version=f"d2nc {__version__}")
    sub = p.add_subparsers(dest="command", required=True)

    c = sub.add_parser("convert", help="Convert one .d directory to .nc")
    c.add_argument("d_path", help="Path to the Bruker .d directory")
    c.add_argument("out_dir", nargs="?", default=".",
                   help="Output directory (default: current dir)")
    c.add_argument("--backend", choices=["auto", "local", "cloud"], default="auto",
                   help="Backend to use (default: auto)")
    c.add_argument("--unique-swim-ids", type=int, default=2048,
                   help="Number of SWIM pulses (default: 2048)")
    c.add_argument("--instrument-frequency", type=float, default=1.0,
                   help="FFT sampling interval (default: 1.0)")
    c.add_argument("--include-timedomain", action="store_true",
                   help="Also fetch/keep the large timedomain .nc "
                        "(default: fourierdomain only)")
    c.add_argument("--keep-cloud-artifacts", action="store_true",
                   help="Do not delete cloud scratch after conversion "
                        "(the 'persist' stub)")
    c.add_argument("--min-ram-gb", type=float, default=12.0,
                   help="Min free RAM (GB) to pick local in auto mode (default: 12)")
    c.add_argument("--cloud-timeout", type=int, default=1800,
                   help="Seconds to wait for the cloud task (default: 1800)")
    c.add_argument("--region", default="eu-west-2", help="AWS region (default: eu-west-2)")
    c.add_argument("--profile", default=None, help="AWS profile (e.g. verdel)")
    return p


def cmd_convert(args):
    backend, reason = choose_backend(args.backend, min_ram_gb=args.min_ram_gb)
    print(f"Backend: {backend} ({reason})")

    if backend == "local":
        from .backends import local

        results = local.convert(
            args.d_path, args.out_dir,
            args.unique_swim_ids, args.instrument_frequency,
            include_timedomain=args.include_timedomain)
    else:
        from .backends import cloud

        session = make_session(profile=args.profile, region=args.region)
        results = cloud.convert(
            session, args.d_path, args.out_dir,
            args.unique_swim_ids, args.instrument_frequency,
            include_timedomain=args.include_timedomain,
            keep_artifacts=args.keep_cloud_artifacts,
            timeout=args.cloud_timeout)

    print("\nDone. Output:")
    for r in results:
        print(f"  {r}")
    return 0


def main(argv=None):
    args = build_parser().parse_args(argv)
    try:
        if args.command == "convert":
            return cmd_convert(args)
    except D2ncError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("Interrupted.", file=sys.stderr)
        return 130
    except Exception as e:  # noqa: BLE001 — translate common AWS creds failures
        if type(e).__name__ in CREDENTIAL_ERROR_NAMES:
            hint = f" --profile {args.profile}" if getattr(args, "profile", None) else ""
            print(f"ERROR: AWS credentials problem ({type(e).__name__}). "
                  f"Try: aws sso login{hint}", file=sys.stderr)
            return 1
        raise
    return 0
