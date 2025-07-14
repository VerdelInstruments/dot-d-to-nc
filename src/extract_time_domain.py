import xarray as xr

def extract_time_domain_data(conn, unique_swim_ids, profile_mz, binary_storage):
    """Extract time-domain data from SQLite and populate an xarray DataArray."""
    query = conn.execute("SELECT Rt, ProfileMzId, ProfileIntensityId FROM Spectra")
    rows = query.fetchall()

    # builds a DataArray with swim_id as the first dimension and mass_charge as the second. This builds the axes only,
    # and fills the whole data array with zeros.
    time_domain = xr.DataArray(
        dims=["swim_id", "mass_charge"],
        coords={"swim_id": range(1, unique_swim_ids + 1), "mass_charge": profile_mz},
        name="intensity",
    ).fillna(0)

    swim_id = 1
    for ii, row in enumerate(rows):

        # try to fill the full TOF row with the data from the binary storage.
        try:
            time_domain.loc[{"swim_id": swim_id}] = binary_storage.read_array_double(
                row[2]
            )

        # if there is an error, skip the row and print a message.
        except Exception as e:
            print(f"Skipping row {ii} due to error: {e}")
            continue

        # if we are not on the first row and the retention time difference between the current and previous row is greater than 1:
        # JDH: I think this 1 is the instrument frequency, in which case it should be a variable.
        if ii > 0 and round(rows[ii][0] - rows[ii - 1][0], 0) > 1:
            # really not clear why this is happening
            swim_id += 1
            print("Detected a large retention time gap, incrementing swim_id. Data will be missing a row. ")

        # increment the swim_id for each row processed
        swim_id += 1

    return time_domain.astype("int")