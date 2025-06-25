import sys
from pathlib import Path

from functions import extract_data

input_file = sys.argv[1]
output_location = sys.argv[2]

config_file = Path(__file__).parent / 'current_config.ini'

filename = extract_data(config_file, input_file, output_location)