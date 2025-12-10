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

            # Find the .d directory (user may upload with or without .d folder)
            # Look for any .d directory first
            d_dirs = [d for d in Path(input_dir).rglob('*.d') if d.is_dir()]

            if d_dirs:
                # Use the first .d directory found
                data_dir = str(d_dirs[0])
                print(f"Found .d directory: {data_dir}")
            else:
                # No .d directory found - files may be uploaded flat
                # Check if we have BAF files directly in input_dir
                baf_files = list(Path(input_dir).glob('*.baf'))
                if baf_files:
                    data_dir = input_dir
                    print(f"No .d directory found, using flat structure: {data_dir}")
                else:
                    raise FileNotFoundError(
                        f"No .d directory or BAF files found in {input_dir}. "
                        f"Please upload either a .d folder or BAF files directly."
                    )

            # Process the data
            print(f"Processing data from {data_dir} to {output_dir}/converted_data.nc")
            timedomain_file = extract_data(data_dir, output_dir)
            fourierdomain_file = timedomain_file.replace('_timedomain', '_fourierdomain')
            
            # Generate output keys if not provided
            if not args.output_key:
                input_name = Path(args.input_key).stem
                timedomain_key = f"{input_name}_timedomain.nc"
                fourierdomain_key = f"{input_name}_fourierdomain.nc"
            else:
                timedomain_key = args.output_key.replace('.nc', '_timedomain.nc')
                fourierdomain_key = args.output_key.replace('.nc', '_fourierdomain.nc')
            
            # Upload both files to S3
            uploaded_files = []
            if os.path.exists(timedomain_file):
                upload_to_s3(timedomain_file, args.output_bucket, timedomain_key)
                print(f"Successfully uploaded timedomain to s3://{args.output_bucket}/{timedomain_key}")
                uploaded_files.append('timedomain')
            else:
                print(f"Warning: Timedomain file {timedomain_file} was not created")
            
            if os.path.exists(fourierdomain_file):
                upload_to_s3(fourierdomain_file, args.output_bucket, fourierdomain_key)
                print(f"Successfully uploaded fourierdomain to s3://{args.output_bucket}/{fourierdomain_key}")
                uploaded_files.append('fourierdomain')
            else:
                print(f"Error: Fourierdomain file {fourierdomain_file} was not created")
                sys.exit(1)
            
            if not uploaded_files:
                print(f"Error: No output files were created")
                sys.exit(1)
                
        except Exception as e:
            print(f"Error during processing: {str(e)}")
            sys.exit(1)
