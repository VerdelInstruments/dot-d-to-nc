from pathlib import Path

import boto3

import tempfile
import zipfile
import os

from helpers.load_yaml import load_yaml
from project_root import PROJECT_ROOT

CONFIG_PATH = PROJECT_ROOT / 'config.yaml'


def upload_dot_d_to_s3(dot_d_path: str):
    """
    Creates a temporary zip file from a .d directory and upload this to s3
    :param dot_d_path: Path to the .d directory to be zipped.
    :return: Path to the created zip file.
    """
    if not os.path.isdir(dot_d_path) or not dot_d_path.endswith('.d'):
        raise ValueError(f"{dot_d_path} is not a valid .d directory.")

    filename = os.path.basename(dot_d_path.rstrip('/')) + '.zip'

    s3 = boto3.client('s3')
    config = load_yaml(CONFIG_PATH)

    bucket = config['s3']['bucket']
    storage_directory = config['s3']['zipped_file_directory']

    # create a temporary local zipped file for uploading to s3
    with tempfile.TemporaryDirectory() as tmp_dir:
        zip_path = os.path.join(tmp_dir, filename)
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(dot_d_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, dot_d_path)
                    zipf.write(file_path, arcname)

        # upload it
        s3.upload_file(zip_path, bucket, f"{storage_directory}/{filename}")
        print(f'uploaded to s3 at  {bucket}/{storage_directory}/{filename}')

    return zip_path



if __name__ == '__main__':
    upload_dot_d_to_s3('/Users/joseph/Documents/verdel/240927_TrailCID_SWIM_01.d')
