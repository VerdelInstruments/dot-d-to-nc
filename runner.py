import os
import subprocess
import time
import requests
import sys



# REPO_DIR = "/path/to/your/repo"
INPUT_FILE = sys.argv[0]
REPO_INPUT_PATH = os.path.join(REPO_DIR, "input.dat")
GITHUB_API_URL = "https://api.github.com/repos/josephhickie/windows-binary-runner/actions/runs"

# Step 1: Copy file and push
os.system(f"cp {INPUT_FILE} {REPO_INPUT_PATH}")
os.chdir(REPO_DIR)
subprocess.run(["git", "add", f"{INPUT_FILE}"])
subprocess.run(["git", "commit", "-m", "Trigger run"])
subprocess.run(["git", "push"])

# Step 2: Wait for job to complete
print("Waiting for GitHub Actions to complete...")
run_id = None
while True:
    r = requests.get(GITHUB_API_URL)
    runs = r.json().get("workflow_runs", [])
    if not runs:
        time.sleep(5)
        continue
    latest = runs[0]
    if run_id is None:
        run_id = latest["id"]
    if latest["status"] == "completed":
        break
    time.sleep(10)

# Step 3: Get logs and find transfer.sh URL
print("Getting logs...")
log_url = latest["logs_url"]
r = requests.get(log_url, headers=HEADERS)
with open("logs.zip", "wb") as f:
    f.write(r.content)

# Unzip and grep for URL
os.system("unzip -o logs.zip -d logs")
with open("logs/step_log.txt", "r") as f:
    for line in f:
        if "https://transfer.sh/" in line:
            url = line.strip()
            break

# Step 4: Download the result
print("Downloading output from", url)
r = requests.get(url)
with open("output.dat", "wb") as f:
    f.write(r.content)
print("Done!")