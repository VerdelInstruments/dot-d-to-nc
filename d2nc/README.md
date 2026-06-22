# d2nc — spike CLI

Convert one Bruker `.d` to NetCDF (`.nc`) from the outside, picking a backend
automatically. Thin front door over the existing converter:

- **local** — in-process `src/extract.py::extract_data` (Windows/Linux, needs the
  bundled `baf2sql` lib + RAM).
- **cloud** — direct ECS `run_task` on the deployed `conversion-service`
  (standalone, 221B-free; works from macOS). Uploads to scratch, runs, downloads
  the `.nc`, then deletes scratch (ephemeral by default).

Run from the `dot-d-to-nc/` repo root (no install needed):

```bash
# auto backend (macOS -> cloud, Win/Linux -> local)
python -m d2nc convert /path/to/sample.d ./out

# force cloud, with the verdel profile
python -m d2nc convert /path/to/sample.d ./out --backend cloud --profile verdel

# keep both files and leave cloud scratch in place
python -m d2nc convert /path/to/sample.d ./out --include-timedomain --keep-cloud-artifacts
```

By default only the `*_fourierdomain.nc` is kept (the file 2Discover loads);
`--include-timedomain` also keeps the large raw intermediate.

## Cloud prerequisites

- `aws sso login --profile verdel` (the session must be valid).
- IAM: ECS `run_task`/`describe_tasks` on `conversion-service`, S3 RW on
  `conversion-service-input/output-p3m4m5tk`, CloudWatch read for failure logs.

## Notes / deferred (spike scope)

- Non-default `--unique-swim-ids` / `--instrument-frequency` only take effect once
  the `conversion-service` image is rebuilt with the updated `extract_s3.py`
  (the CLI warns and passes them anyway). Default runs work against today's image.
- `--keep-cloud-artifacts` is a stub for a future real `persist`-to-221B.
- Deferred: `binned`/`peaks` output levels, f0/f1 frequency-axis metadata,
  server-side suppression of the timedomain file, batch mode.

Validate output with the existing tool:
`python src/validate_netcdf.py ./out/sample_fourierdomain.nc --verbose`
