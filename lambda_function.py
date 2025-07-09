import boto3
import os

def lambda_handler(event, context):
    s3 = boto3.client('s3')

    print("Event received:", event)

    record = event['Records'][0]
    bucket = record['s3']['bucket']['name']  # verdel-nc
    key = record['s3']['object']['key']  # input/test.txt

    tmp_path = f"/tmp/{os.path.basename(key)}"
    s3.download_file(bucket, key, tmp_path)

    with open(tmp_path, 'r') as file:
        content = file.read()

    result = content.upper()

    output_key = key.replace('input/', 'output/').replace('.txt', '_output.txt')
    s3.put_object(Bucket=bucket, Key=output_key, Body=result)

    return {
        'statusCode': 200,
        'body': f"Processed {key} and saved result to {output_key}"
    }