import os
import zipfile

import boto3

from pathlib import Path

from src.lambda_handler import _extract

key = os.environ["INPUT_KEY"]
bucket = os.environ.get("OUTPUT_BUCKET", "nc_files")

print(f"Processing: {key} → {bucket}")


# download from S3
# process .d to .nc
# upload result back to S3

s3 = boto3.client("s3")

local_zip_path = f"/tmp/{Path(key).name}"
s3.download_file(bucket, key, local_zip_path)


# Unzip to /tmp
with zipfile.ZipFile(local_zip_path, 'r') as zip_ref:
    extracted_path = f"/tmp/{Path(key).stem}"
    zip_ref.extractall(extracted_path)

    print(extracted_path)

print(f"HANDLER: path available: {Path(extracted_path).exists()}")
print("HANDLER: Unzipped file to", extracted_path)

print(os.listdir(extracted_path))

# Create output path
output_path = f"/tmp/{Path(key).stem}_output"
os.makedirs(output_path, exist_ok=True)

print("HANDLER: Created output directory at", output_path)


# Call your extract function
result_file = _extract(extracted_path, output_path)

print("HANDLER: Extraction complete, result file is", result_file)

# Upload result to S3
result_key = f"nc_files/{Path(result_file).name}"
print("RESULT KEY:", result_key)
s3.upload_file(result_file, bucket, result_key)

print("HANDLER: Uploaded result file to S3 at", result_key)

# return {
#     "statusCode": 200,
#     "body": f"Output file uploaded to s3://{bucket}/{result_key}"
# }



# def handler(event, context):
#     # Extract bucket name and object key from the S3 event
#     record = event['Records'][0]
#     bucket = record['s3']['bucket']['name']
#     key = record['s3']['object']['key']
#
#     print("EVENT RECEIVED: ", event)
#
#     local_zip_path = f"/tmp/{Path(key).name}"
#
#     # Download the zipped .d directory from S3
#     # s3.download_file(bucket, key, local_zip_path)
#
#     # print("HANDLER: Downloaded file from S3 to", local_zip_path)
#     #
#     # # Unzip to /tmp
#     # with zipfile.ZipFile(local_zip_path, 'r') as zip_ref:
#     #     extracted_path = f"/tmp/{Path(key).stem}"
#     #     zip_ref.extractall(extracted_path)
#     #
#     # extracted_path = "/Users/joseph/Downloads/250702_davaoH2O_021.d"
#     extracted_path = "/input_data"
#
#     print(f"HANDLER: path available: {Path(extracted_path).exists()}")
#     print("HANDLER: Unzipped file to", extracted_path)
#
#     print(os.listdir(extracted_path))
#
#     # Create output path
#     output_path = f"/tmp/{Path(key).stem}_output"
#     os.makedirs(output_path, exist_ok=True)
#
#     print("HANDLER: Created output directory at", output_path)
#
#
#     # Call your extract function
#     result_file = _extract(extracted_path, output_path)
#
#     print("HANDLER: Extraction complete, result file is", result_file)
#
#     # Upload result to S3
#     result_key = f"nc_files/{Path(result_file).name}"
#     print("RESULT KEY:", result_key)
#     s3.upload_file(result_file, bucket, result_key)
#
#     print("HANDLER: Uploaded result file to S3 at", result_key)
#
#     return {
#         "statusCode": 200,
#         "body": f"Output file uploaded to s3://{bucket}/{result_key}"
#     }
