def Func_Combine_Speed_FootVehicle_Reduced(foot_speed_raster, vehicle_speed_raster, output_speed_raster,
                                           foot_reduction_factor, vehicle_reduction_factor):
    """
    Combines two speed rasters (foot and vehicle) by applying respective reduction factors,
    then taking the maximum speed for each cell. Raises an error if exactly one raster has NaN
    in any cell while the other has a valid value.

    :param foot_speed_raster: Path to the foot travel speed raster (GeoTIFF)
    :param vehicle_speed_raster: Path to the vehicle travel speed raster (GeoTIFF)
    :param output_speed_raster: Path to save the combined speed raster (GeoTIFF)
    :param foot_reduction_factor: Float, reduction factor to apply to foot speed
    :param vehicle_reduction_factor: Float, reduction factor to apply to vehicle speed
    """
    import numpy as np
    import rasterio

    with rasterio.open(foot_speed_raster) as foot_src, rasterio.open(vehicle_speed_raster) as vehicle_src:
        foot_speed = foot_src.read(1)
        vehicle_speed = vehicle_src.read(1)

        # Compare metadata
        foot_meta = foot_src.meta.copy()
        vehicle_meta = vehicle_src.meta.copy()
        foot_meta_filtered = {k: v for k, v in foot_meta.items() if k not in ("dtype", "nodata")}
        vehicle_meta_filtered = {k: v for k, v in vehicle_meta.items() if k not in ("dtype", "nodata")}

        if foot_meta_filtered != vehicle_meta_filtered:
            differences = {key: (foot_meta_filtered.get(key), vehicle_meta_filtered.get(key))
                           for key in foot_meta_filtered.keys()
                           if foot_meta_filtered.get(key) != vehicle_meta_filtered.get(key)}
            raise ValueError(f"Metadata mismatch (excluding 'dtype' and 'nodata'): {differences}")

        # NaN masks
        foot_nan = np.isnan(foot_speed)
        vehicle_nan = np.isnan(vehicle_speed)
        mismatch_mask = foot_nan ^ vehicle_nan
        if np.any(mismatch_mask):
            i, j = np.argwhere(mismatch_mask)[0]
            raise ValueError(f"Cell at ({i}, {j}) has one NaN and one valid value: "
                             f"foot={foot_speed[i, j]}, vehicle={vehicle_speed[i, j]}")

        both_valid = ~(foot_nan | vehicle_nan)
        combined_speed = np.full(foot_speed.shape, np.nan, dtype=np.float32)
        combined_speed[both_valid] = np.maximum(
            foot_speed[both_valid] * foot_reduction_factor,
            vehicle_speed[both_valid] * vehicle_reduction_factor
        )

        foot_meta.update(dtype="float32")
        with rasterio.open(output_speed_raster, "w", **foot_meta) as output_raster:
            output_raster.write(combined_speed, 1)

    print(f"Combined speed raster saved to {output_speed_raster}")