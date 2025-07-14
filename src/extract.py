import sys
import argparse
from pathlib import Path

from extractor_class import SwimDataExtractor


def extract_data(d_directory, save_location, unique_swim_ids=2048, instrument_frequency=1):
    extractor = SwimDataExtractor(d_directory)
    out = extractor.extract_and_save(save_location, unique_swim_ids, instrument_frequency)
    print("Data extracted and saved to:", out)
    return out

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Extract and convert .d files to .nc format")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--single', nargs=2, metavar=('INPUT_D', 'OUTPUT'), help="Process a single .d directory")
    group.add_argument('--directory', metavar='DIR', help="Process all .d directories inside DIR")


    args = parser.parse_args()

    if args.single:
        d_directory, save_location = args.single
        extract_data(d_directory, save_location)

    elif args.directory:
        input_dir = Path(args.directory)
        for d_path in input_dir.glob("*.d"):
            output_path = Path("output") / (d_path.stem + "_output.nc")
            output_path.parent.mkdir(exist_ok=True)
            print(f"Processing {d_path} → {output_path}")
            extract_data(d_path, output_path)
