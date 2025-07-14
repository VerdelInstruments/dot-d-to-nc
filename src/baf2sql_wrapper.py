from ctypes import (
    cdll,
    c_int,
    c_uint64,
    c_uint32,
    c_char_p,
    c_double,
    POINTER,
    create_string_buffer
)


class Baf2Sql:

    def __init__(self, path_to_dll: str):
        """
        Initialise the Baf2Sql wrapper with the path to the Baf2Sql DLL/SO.
        :param path_to_dll: Path to the Baf2Sql DLL or shared object file.
        """

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

    @classmethod
    def from_filename(cls, dll_path):
        """Create a Baf2Sql instance from a dll filename."""
        return cls(dll_path)
