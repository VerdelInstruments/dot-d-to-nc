import boto3


def upload_file_to_s3(file_path, bucket_name, object_key):
    s3 = boto3.client('s3')
    s3.upload_file(file_path, bucket_name, object_key)
    print(f"Uploaded {file_path} to s3://{bucket_name}/{object_key}")

def download_from_s3(new_file_path, bucket_name, object_key):
    s3 = boto3.client('s3')

    if s3_file_ready(bucket_name, object_key, timeout=100):
        s3.download_file(bucket_name, object_key, new_file_path)
        print('Downloaded file from S3 to', new_file_path)
    else:
        raise TimeoutError("File not ready in S3 after waiting for the specified timeout.")



def s3_file_ready(bucket_name, object_key, timeout=100):
    s3 = boto3.client('s3')
    start_time = time.time()

    while time.time() - start_time < timeout:
        try:
            s3.head_object(Bucket=bucket_name, Key=object_key)
            print(f"File {object_key} is ready in bucket {bucket_name}.")
            return True
        except Exception as e:
            print(f"Waiting for {object_key} to be ready... {e}")
            time.sleep(5)


if __name__ == "__main__":

    import time

    file_path = './lambda_function_new.zip'
    bucket_name = 'lambda-deployments-jdh'
    object_key = 'nc_conversion.zip'

    upload_file_to_s3(file_path, bucket_name, object_key)