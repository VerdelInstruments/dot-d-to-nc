from ctypes import c_uint64, c_double, POINTER
import numpy as np

from baf2sql_wrapper import Baf2Sql


class BinaryStorage:

    def __init__(self, baf2sql: Baf2Sql, baf_filename: str, raw_calibration: bool = False):
        """
        A class for reading binary arrays from a BAF file.
        :param baf2sql: Instance of Baf2Sql class for accessing the BAF file.
        :param baf_filename: The filename of the BAF file.
        :param raw_calibration: If True, the raw calibration data will be used.
        """

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