import sys

from extractor_class import SwimDataExtractor


def extract_data(d_directory, save_location, unique_swim_ids=2048, instrument_frequency=1):
    extractor = SwimDataExtractor(d_directory)
    out =  extractor.extract_and_save(save_location, unique_swim_ids, instrument_frequency)
    print("Data extracted and saved to:", out)
    return out

if __name__ == '__main__':
    d_directory = sys.argv[1]
    save_location = sys.argv[2]

    extract_data(d_directory, save_location)