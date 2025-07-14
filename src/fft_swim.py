import pyfftw
import xarray as xr
import numpy as np


def compute_fft_efficient(time_domain, unique_swim_ids, profile_mz, instrument_frequency):
    """
    Compute FFT on the time-domain data.

    Parameters:
    - time_domain: xarray DataArray containing time-domain data.
    - unique_swim_ids: Number of unique SWIM IDs.
    - profile_mz: Array of m/z values.
    - instrument_frequency: Frequency of the instrument.

    Returns:
    - xarray DataArray containing the Fourier domain representation.
    """

    n_freqs = unique_swim_ids // 2 + 1
    n_mz = len(profile_mz)

    freq_axis = np.fft.rfftfreq(unique_swim_ids, instrument_frequency)
    result = np.empty((n_freqs, n_mz), dtype=np.float32)

    fft_input = pyfftw.empty_aligned(unique_swim_ids, dtype=np.float32)
    fft_output = pyfftw.empty_aligned(n_freqs, dtype=np.complex64)
    fft = pyfftw.FFTW(fft_input, fft_output, axes=(0,))

    for i, mz in enumerate(profile_mz):
        signal = time_domain.isel({"mass_charge": i}).values.astype(np.float64)
        signal -= signal.mean()  # Remove DC component

        fft_input[:] = signal

        # runs the fft and stores it in fft_output
        fft()

        result[:, i] = np.abs(fft_output) ** 2

    return xr.DataArray(
        data=result,
        dims=["frequency", "mass_charge"],
        coords={
            "frequency": freq_axis,
            "mass_charge": profile_mz
        },
        name="amplitude"
    )


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



if __name__ == '__main__':
    # Example usage
    size = 200000
    unique_swim_ids = 2048
    time_domain = xr.DataArray(np.random.rand(unique_swim_ids, size), dims=["swim_id", "mass_charge"])
    profile_mz = np.linspace(100, 200, size)
    instrument_frequency = 1.0
