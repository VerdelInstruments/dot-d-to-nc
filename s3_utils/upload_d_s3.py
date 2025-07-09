from pathlib import Path


def upload_dot_d_to_s3(file_path: str):
    # Ensure the file exists
    if not Path(file_path).is_dir():
        raise FileNotFoundError(f"The direcotry {file_path} does not exist.")

    # zip the .d directory into temporary local file
    zipped_file = zip_dot_d_file(file_path)

    # Upload the file to S3
    try:
        s3.upload_file(file_path, bucket_name, f'input/{Path(file_path).name}')
        print(f"Uploaded {file_path} to s3://{bucket_name}/input/{Path(file_path).name}")
    except Exception as e:
        print(f"Failed to upload {file_path} to S3: {e}")
        raise e