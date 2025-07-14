from extractor_class import SwimDataExtractor


def extract_data(d_directory, save_location, unique_swim_ids=2048, instrument_frequency=1):
    extractor = SwimDataExtractor(d_directory)
    return extractor.extract_and_save(save_location, unique_swim_ids, instrument_frequency)