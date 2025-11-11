# NetCDF Validation Guide

## Overview

The `validate_netcdf.py` script validates the output NetCDF files produced by the Bruker .d to NetCDF converter. It checks both file structure and data quality to ensure correct processing.

## Installation

The validation script uses the same dependencies as the main converter. Ensure you have installed the requirements:

```bash
pip install -r requirements.txt
```

## Usage

### Validate a Single File

```bash
python src/validate_netcdf.py path/to/file_timedomain.nc
```

### Validate All Files in a Directory

```bash
python src/validate_netcdf.py path/to/output_directory --batch
```

### Validate Paired Files

Check consistency between time-domain and Fourier-domain file pairs:

```bash
python src/validate_netcdf.py path/to/output_directory --batch --check-pairs
```

### Verbose Output

Get detailed information about each file:

```bash
python src/validate_netcdf.py file.nc --verbose
```

### JSON Output

Generate machine-readable JSON output (useful for CI/CD):

```bash
python src/validate_netcdf.py file.nc --json
```

## Validation Checks

### Structure Validation

#### Time-Domain Files (`*_timedomain.nc`)
- **Dimensions**: Must have `swim_id` and `mass_charge`
- **Data Variable**: Must have `intensity` with integer dtype
- **Coordinates**:
  - `swim_id`: Should be sequential integers starting from 1
  - `mass_charge`: Should be m/z values in reasonable range (1-10000)

#### Fourier-Domain Files (`*_fourierdomain.nc`)
- **Dimensions**: Must have `frequency` and `mass_charge`
- **Data Variable**: Must have `amplitude` with float32 dtype
- **Coordinates**:
  - `frequency`: Should start at 0, all non-negative (rfft output)
  - `mass_charge`: Should match paired time-domain file

### Data Quality Checks

Both file types are checked for:

1. **Invalid Values**
   - No NaN (Not a Number) values
   - No infinite values
   - No negative intensities/amplitudes (physically impossible)

2. **Data Completeness**
   - Not all zeros (indicates extraction failure)
   - Warnings for all-zero rows (may indicate issues with specific SWIM pulses)
   - Warnings for all-zero columns (may indicate issues with specific m/z values)

3. **Statistics**
   - Min, max, mean values
   - Count of non-zero values
   - Data range validation

### Paired File Validation

When `--check-pairs` is used, the script validates:

1. **Coordinate Consistency**: `mass_charge` coordinates must match exactly between paired files
2. **Dimension Relationships**: Frequency dimension size should equal `swim_id_count // 2 + 1` (rfft output)

## Exit Codes

- **0**: All validations passed
- **1**: Validation failures detected
- **2**: Error opening or reading files

## Example Output

### Standard Output

```
✓ PASSED: /path/to/sample_timedomain.nc
  Information:
    file_type: time_domain
    swim_id_length: 2048
    mass_charge_length: 125000
    intensity_dtype: int32
    mass_charge_range: 100.05 - 1999.95
    intensity_min: 0
    intensity_max: 65535
    intensity_mean: 123.45
    intensity_nonzero_count: 234567890
    intensity_total_count: 256000000

✗ FAILED: /path/to/corrupted_fourierdomain.nc
  Errors (2):
    - Found 150 NaN values in amplitude
    - Found 5 negative values in amplitude (physically invalid)
  Warnings (1):
    - Found 10 all-zero rows (may indicate extraction issues)

============================================================
Summary: 1/2 files passed validation
============================================================
```

### JSON Output

```json
{
  "individual_files": [
    {
      "file_path": "/path/to/sample_timedomain.nc",
      "passed": true,
      "errors": [],
      "warnings": [],
      "info": {
        "file_type": "time_domain",
        "swim_id_length": 2048,
        "mass_charge_length": 125000,
        "intensity_dtype": "int32"
      }
    }
  ],
  "paired_files": [],
  "summary": {
    "total_files": 1,
    "passed": 1,
    "failed": 0,
    "total_pairs": 0,
    "pairs_passed": 0,
    "pairs_failed": 0
  }
}
```

## Integration with Processing Pipeline

### Manual Validation After Processing

```bash
# Process .d directory
python src/extract.py /path/to/data.d /path/to/output

# Validate output
python src/validate_netcdf.py /path/to/output --batch --check-pairs --verbose
```

### Batch Processing with Validation

```bash
# Process multiple files
python src/extract.py /path/to/directory_with_d_files /path/to/output --batch

# Validate all outputs
python src/validate_netcdf.py /path/to/output --batch --check-pairs --json > validation_report.json
```

### CI/CD Integration

```bash
#!/bin/bash
# Example CI/CD script

# Run processing
python src/extract.py input.d output/

# Validate with JSON output
if python src/validate_netcdf.py output/ --batch --check-pairs --json > validation_report.json; then
    echo "Validation passed"
    exit 0
else
    echo "Validation failed"
    cat validation_report.json
    exit 1
fi
```

## Troubleshooting

### Common Issues

1. **"ModuleNotFoundError: No module named 'xarray'"**
   - Solution: Install requirements with `pip install -r requirements.txt`

2. **"Error: Path does not exist"**
   - Solution: Check the file path is correct and the file exists

3. **"Unrecognized file structure"**
   - Solution: File may be corrupted or not a valid output from the converter

4. **"mass_charge coordinates don't match between time and Fourier domain files"**
   - Solution: Files may be from different processing runs or corrupted. Re-run the extraction.

5. **"Found NaN values" or "Found negative values"**
   - Solution: Input .d file may be corrupted or extraction encountered errors. Check the extraction logs.

## Technical Details

### Expected File Structure

The validator expects NetCDF files following the xarray convention with:

- **Dimensions**: Named axes for the data array
- **Coordinates**: Index values along each dimension
- **Data Variables**: The actual data arrays with associated metadata
- **Attributes**: Optional metadata about the file/processing

### Validation Logic

The script:
1. Opens the file using xarray
2. Auto-detects file type based on dimensions
3. Validates structure (dimensions, coordinates, data types)
4. Validates data quality (no invalid values, reasonable ranges)
5. Optionally validates paired files for consistency
6. Reports results with clear pass/fail status

### Performance

- Single file validation: < 1 second for typical files
- Batch validation: Scales linearly with number of files
- Memory efficient: Uses xarray's lazy loading (doesn't load entire arrays unless needed for validation)

## Contact

For issues or questions about validation, please refer to the main project README or open an issue in the repository.
