import sys
import os
import argparse
import boto3
import tempfile
import shutil
from pathlib import Path

from extractor_class import SwimDataExtractor

def download_from_s3(bucket_name, key, local_path):
    """Download a file/directory from S3 to local path"""
    s3 = boto3.client('s3')
    
    # List all objects with the prefix
    response = s3.list_objects_v2(Bucket=bucket_name, Prefix=key)
    
    if 'Contents' not in response:
        raise FileNotFoundError(f"No objects found with prefix {key} in bucket {bucket_name}")
    
    # Create local directory structure
    os.makedirs(local_path, exist_ok=True)
    
    # Download all files
    for obj in response['Contents']:
        # Get the relative path within the .d directory
        rel_path = obj['Key'][len(key):].lstrip('/')
        if rel_path:  # Skip the directory itself
            local_file_path = os.path.join(local_path, rel_path)
            
            # Create subdirectories if needed
            os.makedirs(os.path.dirname(local_file_path), exist_ok=True)
            
            print(f"Downloading {obj['Key']} to {local_file_path}")
            s3.download_file(bucket_name, obj['Key'], local_file_path)

def upload_to_s3(local_file, bucket_name, key):
    """Upload a file to S3"""
    s3 = boto3.client('s3')
    print(f"Uploading {local_file} to s3://{bucket_name}/{key}")
    s3.upload_file(local_file, bucket_name, key)

def extract_data(d_directory, save_location, unique_swim_ids=2048, instrument_frequency=1):
    extractor = SwimDataExtractor(d_directory)
    out = extractor.extract_and_save(save_location, unique_swim_ids, instrument_frequency)
    print("Data extracted and saved to:", out)
    return out

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Extract and convert .d files to .nc format")
    parser.add_argument('--input-bucket', required=True, help="S3 bucket containing input .d files")
    parser.add_argument('--output-bucket', required=True, help="S3 bucket for output files")
    parser.add_argument('--input-key', required=True, help="S3 key (path) to the .d directory")
    parser.add_argument('--output-key', help="S3 key for output file (optional, will auto-generate)")

    args = parser.parse_args()
    
    # Debug: Print parsed arguments
    print(f"DEBUG - Parsed arguments:")
    print(f"  input_bucket: '{args.input_bucket}'")
    print(f"  output_bucket: '{args.output_bucket}'")
    print(f"  input_key: '{args.input_key}'")
    print(f"  output_key: '{args.output_key}'")

    # Create temporary directories
    with tempfile.TemporaryDirectory() as temp_dir:
        input_dir = os.path.join(temp_dir, 'input')
        output_dir = os.path.join(temp_dir, 'output')
        os.makedirs(output_dir, exist_ok=True)
        
        print(f"Created temporary directories: {input_dir}, {output_dir}")
        
        try:
            # Download input data from S3
            print(f"Downloading from s3://{args.input_bucket}/{args.input_key}")
            download_from_s3(args.input_bucket, args.input_key, input_dir)
            
            # Process the data
            print(f"Processing data from {input_dir} to {output_dir}/converted_data.nc")
            output_file = extract_data(input_dir, output_dir)
            
            # Generate output key if not provided
            if not args.output_key:
                input_name = Path(args.input_key).stem
                args.output_key = f"{input_name}_converted.nc"
            
            # Upload result to S3
            if os.path.exists(output_file):
                upload_to_s3(output_file, args.output_bucket, args.output_key)
                print(f"Successfully uploaded result to s3://{args.output_bucket}/{args.output_key}")
            else:
                print(f"Error: Output file {output_file} was not created")
                sys.exit(1)
                
        except Exception as e:
            print(f"Error during processing: {str(e)}")
            sys.exit(1)
