import boto3


def upload_file_to_s3(file_path, bucket_name, object_key):
    s3 = boto3.client('s3')
    s3.upload_file(file_path, bucket_name, object_key)
    print(f"Uploaded {file_path} to s3://{bucket_name}/{object_key}")


if __name__ == "__main__":
    file_path = './test.txt'
    bucket_name = 'verdel-nc'
    object_key = 'test-out.txt'

    upload_file_to_s3(file_path, bucket_name, object_key)