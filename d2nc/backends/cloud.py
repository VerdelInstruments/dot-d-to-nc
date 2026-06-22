"""Cloud backend: direct ECS run_task on the deployed ``conversion-service``.

Standalone and 221B-free: upload the .d to scratch, run the existing converter
container with an ``extract_s3.py`` command override, poll to completion,
download the .nc, then delete all scratch (ephemeral, no-residue default).
"""

import os
import time
from pathlib import Path

from ..errors import CloudJobError, InputError
from ..naming import domain_keys, input_prefix, make_job_prefix, output_key

# Verified live infra (eu-west-2, acct 987686461587). Overridable via `infra=`.
DEFAULTS = {
    "cluster": "conversion-service",
    "task_def": "conversion-service-task",
    "container": "conversion-service",
    "input_bucket": "conversion-service-input-p3m4m5tk",
    "output_bucket": "conversion-service-output-p3m4m5tk",
    "subnets": ["subnet-01ad09a4f268f8a19", "subnet-05a566f31bafc362f"],
    "security_groups": ["sg-06247b7f954ed8c91"],
    "log_group": "/ecs/conversion-service",
}

POLL_INTERVAL = 10


def convert(session, d_path, out_dir, unique_swim_ids, instrument_frequency,
            include_timedomain=False, keep_artifacts=False, timeout=1800,
            infra=None):
    cfg = dict(DEFAULTS)
    if infra:
        cfg.update(infra)

    d_path = _validate(d_path)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    s3 = session.client("s3")
    ecs = session.client("ecs")

    job = make_job_prefix()
    in_prefix = input_prefix(job, d_path)
    out_key = output_key(job, d_path)
    keys = domain_keys(job, d_path)

    print(f"Job: {job}")
    try:
        _upload_dir(s3, d_path, cfg["input_bucket"], in_prefix)
        command = _build_command(cfg, in_prefix, out_key,
                                 unique_swim_ids, instrument_frequency)
        task_arn = _run_task(ecs, cfg, command)
        print(f"ECS task: {task_arn}")
        _wait(ecs, cfg, task_arn, timeout)
        return _download(s3, cfg["output_bucket"], keys, out_dir, include_timedomain)
    finally:
        _cleanup(s3, cfg, job, keep_artifacts)


def _validate(d_path):
    d_path = Path(d_path)
    if not d_path.is_dir():
        raise InputError(f"{d_path} is not a directory (expected a Bruker .d folder)")
    if not d_path.name.endswith(".d"):
        print(f"WARNING: {d_path.name} does not end with '.d'")
    if not (d_path / "analysis.baf").exists():
        raise InputError(
            f"{d_path} has no analysis.baf — not a valid Bruker .d directory")
    return d_path


def _upload_dir(s3, d_path, bucket, prefix):
    count, total = 0, 0
    for root, _dirs, files in os.walk(d_path):
        for fn in files:
            local = Path(root) / fn
            rel = local.relative_to(d_path)
            key = prefix + str(rel).replace(os.sep, "/")
            s3.upload_file(str(local), bucket, key)
            count += 1
            total += local.stat().st_size
    if count == 0:
        raise InputError(f"{d_path} is empty — nothing to upload")
    print(f"Uploaded {count} files ({total / 1024 / 1024:.1f} MB) "
          f"to s3://{bucket}/{prefix}")


def _build_command(cfg, in_prefix, out_key, unique_swim_ids, instrument_frequency):
    command = [
        "python3", "extract_s3.py",
        "--input-bucket", cfg["input_bucket"],
        "--output-bucket", cfg["output_bucket"],
        "--input-key", in_prefix,
        "--output-key", out_key,
    ]
    # The deployed image may predate the extract_s3.py param args, so only pass
    # them when non-default (and warn — a rebuild/push is needed for them to bite).
    if unique_swim_ids != 2048 or instrument_frequency != 1.0:
        print("WARNING: non-default swim params requested "
              f"(unique_swim_ids={unique_swim_ids}, "
              f"instrument_frequency={instrument_frequency}). These only take "
              "effect once the conversion-service image is rebuilt with the "
              "updated extract_s3.py. Passing them anyway.")
        command += ["--unique-swim-ids", str(unique_swim_ids),
                    "--instrument-frequency", str(instrument_frequency)]
    return command


def _run_task(ecs, cfg, command):
    resp = ecs.run_task(
        cluster=cfg["cluster"],
        taskDefinition=cfg["task_def"],
        launchType="FARGATE",
        networkConfiguration={"awsvpcConfiguration": {
            "subnets": cfg["subnets"],
            "securityGroups": cfg["security_groups"],
            "assignPublicIp": "ENABLED",
        }},
        overrides={"containerOverrides": [
            {"name": cfg["container"], "command": command}]},
    )
    failures = resp.get("failures") or []
    if failures:
        raise CloudJobError(f"ECS run_task failed: {failures}")
    tasks = resp.get("tasks") or []
    if not tasks:
        raise CloudJobError(f"ECS run_task returned no task: {resp}")
    return tasks[0]["taskArn"]


def _wait(ecs, cfg, task_arn, timeout):
    deadline = time.time() + timeout
    last = None
    while True:
        tasks = ecs.describe_tasks(
            cluster=cfg["cluster"], tasks=[task_arn]).get("tasks") or []
        if not tasks:
            raise CloudJobError("task disappeared from describe_tasks")
        task = tasks[0]
        status = task.get("lastStatus")
        if status != last:
            print(f"  task status: {status}")
            last = status

        if status == "STOPPED":
            containers = task.get("containers") or []
            exit_code = containers[0].get("exitCode") if containers else None
            reason = (task.get("stoppedReason")
                      or (containers[0].get("reason") if containers else None))
            if exit_code == 0:
                return
            _print_log_hint(cfg, task_arn)
            raise CloudJobError(
                f"conversion task failed (exitCode={exit_code}, reason={reason!r})")

        if time.time() > deadline:
            try:
                ecs.stop_task(cluster=cfg["cluster"], task=task_arn,
                              reason="d2nc timeout")
            except Exception:
                pass
            raise CloudJobError(f"timed out after {timeout}s waiting for conversion")
        time.sleep(POLL_INTERVAL)


def _print_log_hint(cfg, task_arn):
    task_id = task_arn.rsplit("/", 1)[-1]
    stream = f"ecs/{cfg['container']}/{task_id}"
    print(f"  logs: stream '{stream}' in '{cfg['log_group']}'")
    print(f"  tail: aws logs tail {cfg['log_group']} "
          f"--log-stream-names {stream}")


def _download(s3, bucket, keys, out_dir, include_timedomain):
    wanted = [("fourierdomain", keys["fourierdomain"])]
    if include_timedomain:
        wanted.insert(0, ("timedomain", keys["timedomain"]))

    results = []
    for label, key in wanted:
        try:
            s3.head_object(Bucket=bucket, Key=key)
        except Exception as e:
            raise CloudJobError(
                f"expected {label} output s3://{bucket}/{key} not found "
                f"after task success: {e}") from e
        dest = out_dir / Path(key).name
        s3.download_file(bucket, key, str(dest))
        print(f"Downloaded {label} -> {dest}")
        results.append(dest)
    return results


def _cleanup(s3, cfg, job, keep_artifacts):
    if keep_artifacts:
        print(f"Keeping cloud artifacts under "
              f"s3://{cfg['input_bucket']}/{job}/ and "
              f"s3://{cfg['output_bucket']}/{job}/")
        return
    deleted = (_delete_prefix(s3, cfg["input_bucket"], job + "/")
               + _delete_prefix(s3, cfg["output_bucket"], job + "/"))
    print(f"Cleaned up {deleted} scratch objects (no residue).")


def _delete_prefix(s3, bucket, prefix):
    objs = []
    paginator = s3.get_paginator("list_objects_v2")
    for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
        objs.extend({"Key": o["Key"]} for o in page.get("Contents", []))
    for i in range(0, len(objs), 1000):
        s3.delete_objects(Bucket=bucket, Delete={"Objects": objs[i:i + 1000]})
    return len(objs)
