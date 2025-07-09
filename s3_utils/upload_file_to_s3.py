import boto3


def upload_file_to_s3(file_path: str, bucket_name: str, object_key: str):
    """
    Uploads a file to an S3 bucket.
    :param file_path: the local path of the file to upload
    :param bucket_name: the name of the bucket on S3 to upload the file into
    :param object_key: the key (path) under which the file will be stored in the bucket
    :return:
    """
    s3 = boto3.client('s3')
    s3.upload_file(file_path, bucket_name, object_key)
    print(f"Uploaded {file_path} to s3://{bucket_name}/{object_key}")
