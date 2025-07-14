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
    return Path(__file__).parent / 'libbaf2sql_c.so'

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
    rows = query.fetchall()

    time_domain = xr.DataArray(
        dims=["swim_id", "mass_charge"],
        coords={"swim_id": range(1, unique_swim_ids + 1), "mass_charge": profile_mz},
        name="intensity",
    ).fillna(0)

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

    return time_domain.astype("int")


def compute_fft(time_domain, unique_swim_ids, profile_mz, instrument_frequency):
    """Compute FFT on the time-domain data."""
    time_domain_np = time_domain.to_numpy()

    in_array = pyfftw.empty_aligned(
        (unique_swim_ids, len(profile_mz)), dtype=np.float32
    )
    out_array = pyfftw.empty_aligned(
        (unique_swim_ids // 2 + 1, len(profile_mz)), dtype=np.complex64
    )

    in_array[:, :] = time_domain_np - time_domain_np.mean(axis=0, keepdims=True)
    swim_fft = pyfftw.FFTW(in_array, out_array, axes=(0,))
    fft_result = swim_fft()

    fourier_domain = xr.DataArray(
        data=np.absolute(fft_result) ** 2,
        dims=["frequency", "mass_charge"],
        coords={
            "frequency": np.fft.rfftfreq(unique_swim_ids, instrument_frequency),
            "mass_charge": profile_mz,
        },
        name="amplitude",
    )

    return fourier_domain


def save_to_netcdf(data_array, file_name):
    """Save xarray DataArray to a NetCDF file."""
    data_array.to_netcdf(file_name)



def extract(d_directory, save_location):
    config_file = Path(d_directory) / 'current_config.ini'
    return extract_data(config_file, d_directory, save_location)





def extract_data(config_file, d_directory, save_location):
    """Main function to extract data and save time-domain and Fourier-domain results."""
    # Initialise Baf2Sql

    # dll_path = get_resource_path("data_handling/baf2sql_lib") / dll_file
    dll_path = get_library_path()

    baf2sql = Baf2Sql(dll_path)

    # Load configuration
    unique_swim_ids, instrument_frequency = load_config(config_file)

    # Setup SQLite connection
    conn, baf_filename = setup_sqlite_connection(d_directory, baf2sql)

    # Load BinaryStorage and profile mz
    bs = BinaryStorage(baf2sql, baf_filename)
    profile_mz = bs.read_array_double(
        conn.execute("SELECT ProfileMzId FROM Spectra").fetchone()[0]
    )

    # Extract time-domain data
    time_domain = extract_time_domain_data(conn, unique_swim_ids, profile_mz, bs)

    # Save time-domain data
    file_name = os.path.join(save_location, f"{Path(d_directory).stem}_timedomain.nc")
    save_to_netcdf(time_domain, file_name)

    # Compute and save Fourier-domain data
    fourier_domain = compute_fft(
        time_domain, unique_swim_ids, profile_mz, instrument_frequency
    )
    save_to_netcdf(fourier_domain, file_name.replace("_timedomain", "_fourierdomain"))

    return file_name


