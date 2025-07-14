import sqlite3
from pathlib import Path
import os
import platform

from baf2sql_wrapper import Baf2Sql
from binary_storage import BinaryStorage
from extract_time_domain import extract_time_domain_data
from fft_swim import compute_fft, compute_fft_efficient


def get_dll_filename():
    system = platform.system()

    if system == 'Linux':
        return 'libbaf2sql_c.so'
    elif system == 'Windows':
        return 'baf2sql_c.dll'
    elif system == 'Darwin':
        raise RuntimeError('macOS is not supported for this operation. Use the Docker image to build a system that will work on your PC.')
    else:
        raise RuntimeError(f'Unsupported OS: {system}')


class SwimDataExtractor:

    def __init__(self, d_directory, dll_path=None, baf_filename='analysis.baf'):
        self.d_directory = Path(d_directory)
        self.baf_filename = self.d_directory / baf_filename

        self.dll_path = Path(dll_path or __file__).parent / get_dll_filename()

        if not Path(self.d_directory).exists():
            raise NotADirectoryError(f"Directory does not exist: {self.d_directory}")

        if not self.baf_filename.exists():
            raise FileNotFoundError(f"BAF file not found: {self.baf_filename}")

        if not self.dll_path.exists():
            raise FileNotFoundError(f"DLL file not found: {self.dll_path}")

        self.baf2sql = Baf2Sql.from_filename(self.dll_path)
        self.sqlite_path = self.baf2sql.get_sqlite_cache_filename(str(self.baf_filename))
        self.conn = sqlite3.connect(self.sqlite_path)
        self.bs = BinaryStorage(self.baf2sql, str(self.baf_filename))

    def get_profile_mz(self):
        """
        Gets the m/z index values by querying those from the first SWIM pulse. These stay the same
        across SWIM pulses as they are set by the TOF time resolution, so this is valid.

        :return: An array of m/z values.
        """
        return self.bs.read_array_double(
            self.conn.execute("SELECT ProfileMzId FROM Spectra").fetchone()[0]
        )

    def extract_time_domain(self, unique_swim_ids, profile_mz):
        return extract_time_domain_data(self.conn, unique_swim_ids, profile_mz, self.bs)

    def extract_and_save(self, save_location, unique_swim_ids, instrument_frequency):

        save_path = Path(save_location) / f"{self.d_directory.stem}_timedomain.nc"
        fourier_save_path = str(save_path).replace('_timedomain', '_fourierdomain')

        profile_mz = self.get_profile_mz()

        time_domain = self.extract_time_domain(unique_swim_ids, profile_mz)
        time_domain.to_netcdf(save_path)

        fourier = compute_fft_efficient(time_domain, unique_swim_ids, profile_mz, instrument_frequency)
        fourier.to_netcdf(fourier_save_path)

        return str(save_path)


