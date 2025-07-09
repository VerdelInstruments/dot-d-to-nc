import boto3

from pathlib import Path
import os
import zipfile

from lambda_runner import extract


s3 = boto3.client('s3')


def handler(event, context):
    # Extract bucket name and object key from the S3 event
    record = event['Records'][0]
    bucket = record['s3']['bucket']['name']
    key = record['s3']['object']['key']

    print("EVENT RECEIVED: ", event)

    local_zip_path = f"/tmp/{Path(key).name}"

    # Download the zipped .d directory from S3
    s3.download_file(bucket, key, local_zip_path)

    print("HANDLER: Downloaded file from S3 to", local_zip_path)

    # Unzip to /tmp
    with zipfile.ZipFile(local_zip_path, 'r') as zip_ref:
        extracted_path = f"/tmp/{Path(key).stem}"
        zip_ref.extractall(extracted_path)

    # Create output path
    output_path = f"/tmp/{Path(key).stem}_output"
    os.makedirs(output_path, exist_ok=True)

    # Call your extract function
    result_file = extract(extracted_path, output_path)

    # Upload result to S3
    result_key = f"nc_files/{Path(result_file).name}"
    s3.upload_file(result_file, bucket, result_key)

    return {
        "statusCode": 200,
        "body": f"Output file uploaded to s3://{bucket}/{result_key}"
    }
