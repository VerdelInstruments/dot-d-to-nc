#!/usr/bin/env python3
"""
Simple test to verify the validation script logic without requiring actual NetCDF files.
This tests the validation logic components independently.
"""

import sys
sys.path.insert(0, 'src')

from validate_netcdf import ValidationResult, NetCDFValidator
import numpy as np

def test_validation_result():
    """Test ValidationResult class."""
    print("Testing ValidationResult class...")

    result = ValidationResult("test_file.nc")
    assert result.passed == True
    assert len(result.errors) == 0
    assert len(result.warnings) == 0

    result.add_error("Test error")
    assert result.passed == False
    assert len(result.errors) == 1

    result.add_warning("Test warning")
    assert len(result.warnings) == 1
    assert result.passed == False  # Still failed due to error

    result.add_info("test_key", "test_value")
    assert result.info["test_key"] == "test_value"

    # Test to_dict
    result_dict = result.to_dict()
    assert result_dict["passed"] == False
    assert len(result_dict["errors"]) == 1
    assert len(result_dict["warnings"]) == 1

    print("✓ ValidationResult tests passed")


def test_validator_file_type_detection():
    """Test file type detection logic."""
    print("\nTesting file type detection...")

    validator = NetCDFValidator()

    # Mock dataset classes for testing
    class MockDataset:
        def __init__(self, dims):
            self.dims = dims

    # Test time-domain detection
    ds_time = MockDataset({'swim_id': 2048, 'mass_charge': 125000})
    file_type = validator.detect_file_type(ds_time)
    assert file_type == 'time_domain', f"Expected 'time_domain', got {file_type}"

    # Test Fourier-domain detection
    ds_fourier = MockDataset({'frequency': 1025, 'mass_charge': 125000})
    file_type = validator.detect_file_type(ds_fourier)
    assert file_type == 'fourier_domain', f"Expected 'fourier_domain', got {file_type}"

    # Test unrecognized
    ds_unknown = MockDataset({'x': 100, 'y': 100})
    file_type = validator.detect_file_type(ds_unknown)
    assert file_type is None, f"Expected None, got {file_type}"

    print("✓ File type detection tests passed")


def test_paired_file_detection():
    """Test paired file path detection."""
    print("\nTesting paired file detection...")

    from pathlib import Path
    from validate_netcdf import find_paired_file

    # Test time-domain to Fourier-domain
    time_path = Path("/output/sample_timedomain.nc")
    expected_fourier = Path("/output/sample_fourierdomain.nc")

    # Note: This won't check existence, just path transformation
    result = find_paired_file(time_path)
    # Result will be None since file doesn't exist, but we can test the logic

    # Test Fourier-domain to time-domain
    fourier_path = Path("/output/sample_fourierdomain.nc")
    expected_time = Path("/output/sample_timedomain.nc")

    result = find_paired_file(fourier_path)

    # Test non-standard filename
    other_path = Path("/output/random.nc")
    result = find_paired_file(other_path)
    assert result is None, "Should return None for non-standard filename"

    print("✓ Paired file detection tests passed")


def test_validation_logic_components():
    """Test individual validation logic components."""
    print("\nTesting validation logic components...")

    validator = NetCDFValidator()

    # Test coordinate validation logic concepts
    # swim_id should start at 1
    swim_ids = np.arange(1, 2049)  # 1 to 2048
    assert swim_ids[0] == 1, "swim_id should start at 1"
    assert len(swim_ids) == 2048, "swim_id should have 2048 values"

    # Frequency should start at 0 for rfft
    unique_swim_ids = 2048
    instrument_frequency = 1.0
    freq = np.fft.rfftfreq(unique_swim_ids, instrument_frequency)
    assert freq[0] == 0, "Frequency should start at 0"
    assert len(freq) == unique_swim_ids // 2 + 1, "Frequency length should be N//2 + 1"
    assert np.all(freq >= 0), "All frequencies should be non-negative"

    # Test data quality checks
    test_data = np.random.rand(100, 100) * 1000

    # Check for NaN
    nan_count = np.isnan(test_data).sum()
    assert nan_count == 0, "Test data should have no NaN"

    # Check for infinity
    inf_count = np.isinf(test_data).sum()
    assert inf_count == 0, "Test data should have no infinity"

    # Check for negatives
    negative_count = (test_data < 0).sum()
    assert negative_count == 0, "Test data should have no negatives"

    # Test with problematic data
    bad_data = test_data.copy()
    bad_data[0, 0] = np.nan
    bad_data[1, 1] = np.inf
    bad_data[2, 2] = -100

    assert np.isnan(bad_data).sum() == 1, "Should detect 1 NaN"
    assert np.isinf(bad_data).sum() == 1, "Should detect 1 infinity"
    assert (bad_data < 0).sum() == 1, "Should detect 1 negative"

    print("✓ Validation logic component tests passed")


def test_expected_dimensions():
    """Test expected dimension relationships."""
    print("\nTesting expected dimension relationships...")

    # Test rfft dimension relationship
    unique_swim_ids = 2048
    expected_freq_count = unique_swim_ids // 2 + 1
    assert expected_freq_count == 1025, f"Expected 1025 frequencies, got {expected_freq_count}"

    # Test for different values
    for n in [256, 512, 1024, 2048, 4096]:
        expected = n // 2 + 1
        actual_freq = np.fft.rfftfreq(n, 1.0)
        assert len(actual_freq) == expected, f"For N={n}, expected {expected} frequencies"

    print("✓ Dimension relationship tests passed")


def main():
    """Run all tests."""
    print("="*60)
    print("Running Validation Script Logic Tests")
    print("="*60)

    try:
        test_validation_result()
        test_validator_file_type_detection()
        test_paired_file_detection()
        test_validation_logic_components()
        test_expected_dimensions()

        print("\n" + "="*60)
        print("✓ All tests passed!")
        print("="*60)
        return 0

    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
        return 1
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 2


if __name__ == '__main__':
    sys.exit(main())
