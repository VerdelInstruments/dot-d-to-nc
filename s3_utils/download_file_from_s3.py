import boto3
import time


def download_from_s3(new_file_path, bucket_name, object_key):
    """
    Downloads a file from S3 to a local path after checking if the file is ready.
    :param new_file_path: the local path where the file will be saved
    :param bucket_name: the name of the S3 bucket from which to download the file
    :param object_key: the name (key) of the file under which the target file is stored on S3
    :return:
    """
    s3 = boto3.client('s3')

    if s3_file_ready(bucket_name, object_key, timeout=100):
        s3.download_file(bucket_name, object_key, new_file_path)
        print('Downloaded file from S3 to', new_file_path)
    else:
        raise TimeoutError("File not ready in S3 after waiting for the specified timeout.")


def s3_file_ready(bucket_name, object_key, timeout=100):
    """
    Polls S3 bucket to see if the object has been created and is ready for download.
    :param bucket_name: the bucket in which the target object will be placed when it is created
    :param object_key: the name (key) of the target object
    :param timeout: the maximum time to wait for the file to be ready, in seconds
    :return:
    """
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
