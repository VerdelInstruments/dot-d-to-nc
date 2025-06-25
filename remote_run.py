import os, sys, json, time, subprocess, zipfile, tempfile, requests
from pathlib import Path

def zip_dir(src_dir, dest_zip):
    with zipfile.ZipFile(dest_zip, 'w') as zf:
        for root, _, files in os.walk(src_dir):
            for f in files:
                full = os.path.join(root, f)
                rel = os.path.relpath(full, src_dir)
                zf.write(full, rel)

def upload_to_transfersh(file_path):
    print("Uploading input to transfer.sh...")
    with open(file_path, 'rb') as f:
        r = requests.put(f"https://transfer.sh/{Path(file_path).name}", data=f)
    return r.text.strip()

def push_job_descriptor(gist_url, input_url, tag):
    job = {
        "input_url": input_url,
        "output_filename": f"{tag}_output.dat"
    }
    fname = f"job_{tag}.json"
    with open(fname, "w") as f:
        json.dump(job, f)
    subprocess.run(["gh", "api", f"/repos/YOUR_USERNAME/YOUR_REPO/contents/jobs/{fname}",
                    "--method", "PUT",
                    "-f", f"message=job {tag}",
                    "-f", f"content={Path(fname).read_text().encode('utf-8').decode('utf-8')}",
                    "-f", "branch=main"])
    return fname

def poll_actions_and_get_output(tag, timeout=600):
    print("Polling GitHub Actions for job...")
    headers = {"Accept": "application/vnd.github+json"}
    for _ in range(timeout // 10):
        runs = requests.get("https://api.github.com/repos/YOUR_USERNAME/YOUR_REPO/actions/runs").json()
        for run in runs.get("workflow_runs", []):
            if tag in run["head_commit"]["message"]:
                if run["status"] == "completed":
                    logs_url = run["logs_url"]
                    logs = requests.get(logs_url).content
                    with open("logs.zip", "wb") as f:
                        f.write(logs)
                    subprocess.run(["unzip", "-o", "logs.zip", "-d", "logs"])
                    for logfile in Path("logs").rglob("*"):
                        if logfile.suffix == ".txt":
                            with open(logfile) as lf:
                                for line in lf:
                                    if "https://transfer.sh" in line:
                                        return line.strip()
        time.sleep(10)
    raise TimeoutError("GitHub Action did not finish in time")

if __name__ == "__main__":
    d_path = sys.argv[1]
    tag = Path(d_path).stem + "_" + str(int(time.time()))
    with tempfile.TemporaryDirectory() as tmp:
        zip_path = os.path.join(tmp, f"{tag}.zip")
        zip_dir(d_path, zip_path)
        input_url = upload_to_transfersh(zip_path)
        push_job_descriptor("https://github.com/josephhickie/windows-binary-runner", input_url, tag)
        result_url = poll_actions_and_get_output(tag)
        print("Downloading result from:", result_url)
        r = requests.get(result_url)
        with open(f"{tag}_output.dat", "wb") as f:
            f.write(r.content)
        print("✅ Done.")