import boto3

from pathlib import Path
import os
import zipfile

# from lambda_runner import extract, extract_data

s3 = boto3.client('s3')


def _extract(d_directory, save_location):
    # config_file = Path(__file__).parent / 'current_config.ini'
    config_file = None

    data = extract_data(config_file, d_directory, save_location)
    print('extracted data:', data)
    return data


def handler(event, context):
    # Extract bucket name and object key from the S3 event
    record = event['Records'][0]
    bucket = record['s3']['bucket']['name']
    key = record['s3']['object']['key']

    print("EVENT RECEIVED: ", event)

    local_zip_path = f"/tmp/{Path(key).name}"

    # Download the zipped .d directory from S3
    # s3.download_file(bucket, key, local_zip_path)

    # print("HANDLER: Downloaded file from S3 to", local_zip_path)
    #
    # # Unzip to /tmp
    # with zipfile.ZipFile(local_zip_path, 'r') as zip_ref:
    #     extracted_path = f"/tmp/{Path(key).stem}"
    #     zip_ref.extractall(extracted_path)
    #
    # extracted_path = "/Users/joseph/Downloads/250702_davaoH2O_021.d"
    extracted_path = "/input_data"

    print(f"HANDLER: path available: {Path(extracted_path).exists()}")
    print("HANDLER: Unzipped file to", extracted_path)

    print(os.listdir(extracted_path))

    # Create output path
    output_path = f"/tmp/{Path(key).stem}_output"
    os.makedirs(output_path, exist_ok=True)

    print("HANDLER: Created output directory at", output_path)


    # Call your extract function
    result_file = _extract(extracted_path, output_path)

    print("HANDLER: Extraction complete, result file is", result_file)

    # Upload result to S3
    result_key = f"nc_files/{Path(result_file).name}"
    print("RESULT KEY:", result_key)
    s3.upload_file(result_file, bucket, result_key)

    print("HANDLER: Uploaded result file to S3 at", result_key)

    return {
        "statusCode": 200,
        "body": f"Output file uploaded to s3://{bucket}/{result_key}"
    }

import configparser
import sqlite3
import os
import zipfile
from pathlib import Path
from ctypes import *

import numpy as np
import xarray as xr
import pyfftw

def get_library_path():
    file =  Path(__file__).parent / 'libbaf2sql_c.so'
    print(f'finding file at {file}')
    if not file.exists():
        raise FileNotFoundError(f"Library file not found at {file}")
    return file



class Baf2Sql:

    def __init__(self, path_to_dll):
        self.dll = cdll.LoadLibrary(str(path_to_dll))
        self._setup_function_signatures()

    def _setup_function_signatures(self):

        self.dll.baf2sql_get_sqlite_cache_filename_v2.argtypes = [
            c_char_p,
            c_uint32,
            c_char_p,
            c_int,
        ]
        self.dll.baf2sql_get_sqlite_cache_filename_v2.restype = c_uint32
        self.dll.baf2sql_array_open_storage.argtypes = [c_int, c_char_p]
        self.dll.baf2sql_array_open_storage.restype = c_uint64
        self.dll.baf2sql_array_close_storage.argtypes = [c_uint64]
        self.dll.baf2sql_array_close_storage.restype = None
        self.dll.baf2sql_get_last_error_string.argtypes = [c_char_p, c_uint32]
        self.dll.baf2sql_get_last_error_string.restype = c_uint32
        self.dll.baf2sql_array_get_num_elements.argtypes = [
            c_uint64,
            c_uint64,
            POINTER(c_uint64),
        ]
        self.dll.baf2sql_array_get_num_elements.restype = c_int
        self.dll.baf2sql_array_read_double.argtypes = [
            c_uint64,
            c_uint64,
            POINTER(c_double),
        ]
        self.dll.baf2sql_array_read_double.restype = c_int

    def throw_last_error(self):
        """Throw last Baf2Sql error string as an exception."""

        len = self.dll.baf2sql_get_last_error_string(None, 0)
        buf = create_string_buffer(len)
        self.dll.baf2sql_get_last_error_string(buf, len)
        raise RuntimeError(buf.value)

        # The Baf2Sql DLL expects all strings in UTF-8 encoding.

    @staticmethod
    def to_utf8(string):
        """Convert a string to UTF-8 encoding."""
        if not isinstance(string, str):
            raise ValueError("Input must be a string.")
        return string.encode("utf-8")

    def get_sqlite_cache_filename(self, baf_filename, all_variables=False):
        """Find out the file name of the SQLite cache corresponding to the specified BAF file.
        (If the SQLite cache doesn't exist yet, it will be created.
        """

        u8path = self.to_utf8(baf_filename)
        len = self.dll.baf2sql_get_sqlite_cache_filename_v2(
            None, 0, u8path, all_variables
        )

        if len == 0:
            self.throw_last_error()

        buffer = create_string_buffer(len)
        self.dll.baf2sql_get_sqlite_cache_filename_v2(
            buffer, len, u8path, all_variables
        )
        return buffer.value


class BinaryStorage:

    def __init__(self, baf2sql, baf_filename, raw_calibration=False):

        # Copy reference to DLL object so this instance works properly
        # even if the module is reloaded in an interactive session.
        self.baf2sql = baf2sql
        self.dll = self.baf2sql.dll

        self.handle = self.dll.baf2sql_array_open_storage(
            1 if raw_calibration else 0, self.baf2sql.to_utf8(baf_filename)
        )

        if self.handle == 0:
            self.baf2sql.throw_last_error()

    def __del__(self):
        self.dll.baf2sql_array_close_storage(self.handle)

    def get_array_num_elements(self, id):
        """Returns number of elements in array with specified ID."""
        n = c_uint64(0)
        if not self.dll.baf2sql_array_get_num_elements(self.handle, id, n):
            self.baf2sql.throw_last_error()
        return n.value

    def read_array_double(self, id):
        """Returns the requested array as a double np.array."""
        buffer = np.empty(shape=self.get_array_num_elements(id), dtype=np.float64)

        if not self.dll.baf2sql_array_read_double(
            self.handle, id, buffer.ctypes.data_as(POINTER(c_double))
        ):
            self.baf2sql.throw_last_error()

        return buffer


def load_config(config_file):
    """Load and parse the configuration file."""
    config = configparser.ConfigParser()
    config.read(config_file)

    # Print out all sections and keys
    print("Sections:", config.sections())
    for section in config.sections():
        print(f"[{section}]")
        for key, value in config[section].items():
            print(f"{key} = {value}")
    unique_swim_ids = int(config["SWIM.settings"]["unique_swim_ids"])
    instrument_frequency = float(config["instrument.settings"]["instrument_frequency"])
    return unique_swim_ids, instrument_frequency


def setup_sqlite_connection(d_directory, baf2sql):
    """Setup SQLite connection using Baf2Sql."""
    baf_filename = os.path.join(d_directory, "analysis.baf")
    sqlite_filename = baf2sql.get_sqlite_cache_filename(baf_filename)
    conn = sqlite3.connect(sqlite_filename)
    return conn, baf_filename


def extract_time_domain_data(conn, unique_swim_ids, profile_mz, binary_storage):
    """Extract time-domain data from SQLite and populate an xarray DataArray."""
    query = conn.execute("SELECT Rt, ProfileMzId, ProfileIntensityId FROM Spectra")
    print(query)
    rows = query.fetchall()

    print("Number of rows fetched:", len(rows))
    #
    # time_domain = xr.DataArray(
    #     dims=["swim_id", "mass_charge"],
    #     coords={"swim_id": range(1, unique_swim_ids + 1), "mass_charge": profile_mz},
    #     name="intensity",
    # ).fillna(0)

    time_domain = xr.DataArray(
        data=np.zeros((unique_swim_ids, len(profile_mz))),  # or np.full(...) if you want NaNs
        dims=["swim_id", "mass_charge"],
        coords={"swim_id": range(1, unique_swim_ids + 1), "mass_charge": profile_mz},
        name="intensity",
    )

    print("Initialized time_domain DataArray with shape:", time_domain.shape)

    swim_id = 1
    for ii, row in enumerate(rows):
        try:
            time_domain.loc[{"swim_id": swim_id}] = binary_storage.read_array_double(
                row[2]
            )
        except Exception as e:
            print(f"Skipping row {ii} due to error: {e}")
            continue
        if ii > 0 and round(rows[ii][0] - rows[ii - 1][0], 0) > 1:
            swim_id += 1
        swim_id += 1

    print("Final shape of time_domain DataArray:", time_domain.shape)
    return time_domain#.astype("int")


def compute_fft(time_domain, unique_swim_ids, profile_mz, instrument_frequency):
    """Compute FFT on the time-domain data."""
    # time_domain_np = time_domain.to_numpy()
    print('got time domain numpy array with shape:', time_domain.shape)

    in_array = pyfftw.empty_aligned(
        (unique_swim_ids, len(profile_mz)), dtype=np.float32
    )

    print('created input array with shape:', in_array.shape)


    out_array = pyfftw.empty_aligned(
        (unique_swim_ids // 2 + 1, len(profile_mz)), dtype=np.complex64
    )

    print('created output array with shape:', out_array.shape)

    # mean = time_domain_np.mean(axis=0, keepdims=True)_

    # in_array[:, :] = time_domain_np - time_domain_np.mean(axis=0, keepdims=True)
    # np.subtract(
    #     time_domain_np,
    #     time_domain_np.mean(axis=0, keepdims=True),
    #     out=in_array
    # )

    print(type(time_domain))
    mean = time_domain.values.mean(axis=0, keepdims=True)
    print(mean.shape, mean.dtype)

    print(time_domain.shape, time_domain.dtype)
    # in_array = time_domain - mean
    np.subtract(time_domain, mean, out=in_array)
    # batch the mean subtraction to avoid memory issues
    # chunk_size = 10000
    # for i in range(0, time_domain.shape[1], chunk_size):
    #     print(i)
    #     sl = slice(i, i + chunk_size)
    #     np.subtract(time_domain.values[:, sl], mean[:, sl], out=in_array[:, sl])

    print('input array mean subtracted, now performing FFT')
    swim_fft = pyfftw.FFTW(in_array, out_array, axes=(0,))

    print('FFT setup complete, executing FFT')
    fft_result = swim_fft()

    print('FFT execution complete, result shape:', fft_result.shape)

    fourier_domain = xr.DataArray(
        data=np.absolute(fft_result) ** 2,
        dims=["frequency", "mass_charge"],
        coords={
            "frequency": np.fft.rfftfreq(unique_swim_ids, instrument_frequency),
            "mass_charge": profile_mz,
        },
        name="amplitude",
    )

    print('Created Fourier domain DataArray with shape:', fourier_domain.shape)

    return fourier_domain


def save_to_netcdf(data_array, file_name):
    """Save xarray DataArray to a NetCDF file."""
    data_array.to_netcdf(file_name)


def extract_data(config_file, d_directory, save_location):
    """Main function to extract data and save time-domain and Fourier-domain results."""
    # Initialise Baf2Sql

    # dll_path = get_resource_path("data_handling/baf2sql_lib") / dll_file
    dll_path = get_library_path()

    print('got library path:', dll_path)

    baf2sql = Baf2Sql(dll_path)

    # Load configuration
    # unique_swim_ids, instrument_frequency = load_config(config_file)
    unique_swim_ids, instrument_frequency = 2048, 1

    print('got swim ids')

    # Setup SQLite connection
    conn, baf_filename = setup_sqlite_connection(d_directory, baf2sql)

    print("connection set up: ", conn)

    # Load BinaryStorage and profile mz
    bs = BinaryStorage(baf2sql, baf_filename)
    profile_mz = bs.read_array_double(
        conn.execute("SELECT ProfileMzId FROM Spectra").fetchone()[0]
    )

    print("Profile m/z loaded:", profile_mz)

    # Extract time-domain data
    time_domain = extract_time_domain_data(conn, unique_swim_ids, profile_mz, bs)


    print("Time-domain data extracted with shape:", time_domain.shape)

    # Save time-domain data
    file_name = os.path.join(save_location, f"{Path(d_directory).stem}_timedomain.nc")

    print("Saving time-domain data to:", file_name)
    save_to_netcdf(time_domain, file_name)
    print('saved time-domain data')

    # Compute and save Fourier-domain data
    fourier_domain = compute_fft(
        time_domain, unique_swim_ids, profile_mz, instrument_frequency
    )

    print("Fourier-domain data computed with shape:", fourier_domain.shape)



    save_to_netcdf(fourier_domain, file_name.replace("_timedomain", "_fourierdomain"))

    print('saved fourier-domain data')

    return file_name




if __name__ == "__main__":
    # Simulate Lambda event
    result = handler({
  "Records": [
    {
      "s3": {
        "bucket": {
          "name": "verdel-nc"
        },
        "object": {
          "key": "zipped/250702_davaoH2O_021.d.zip"
        }
      }
    }
  ]
}, {})  # mock event/context
    print(result)