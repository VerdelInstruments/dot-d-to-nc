import json, os, requests, zipfile
from pathlib import Path

job_file = next(Path("jobs").glob("job_*.json"))
with open(job_file) as f:
    job = json.load(f)

input_url = job["input_url"]
output_file = job["output_filename"]

print("Downloading input from", input_url)
r = requests.get(input_url)
with open("job.zip", "wb") as f:
    f.write(r.content)

with zipfile.ZipFile("job.zip", "r") as zf:
    zf.extractall("job")

print("Running processing job...")
os.chdir("job")
os.system(f"python runner.py > ../{output_file}")
os.chdir("..")

print("Uploading result to transfer.sh...")
with open(output_file, "rb") as f:
    r = requests.put(f"https://transfer.sh/{output_file}", data=f)
print("Output available at:", r.text.strip())