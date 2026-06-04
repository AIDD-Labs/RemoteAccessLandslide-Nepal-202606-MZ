def Func_Combine_Speed_FootVehicle_Reduced(foot_speed_raster, vehicle_speed_raster, output_speed_raster,
                                           foot_reduction_factor, vehicle_reduction_factor):
    """
    Combine foot and vehicle speed rasters into one effective travel-speed map.

    Parameters:
        foot_speed_raster (str): Foot travel speed raster (GeoTIFF, km/h).
        vehicle_speed_raster (str): Vehicle travel speed raster (GeoTIFF, km/h).
        output_speed_raster (str): Output combined speed raster (GeoTIFF, km/h).
        foot_reduction_factor (float): Multiplier applied to foot speed before combining.
        vehicle_reduction_factor (float): Multiplier applied to vehicle speed before combining.

    Note:
        Both input rasters must share the same grid and NaN mask. For each valid cell,
        output speed = max(foot_speed × foot_reduction_factor,
        vehicle_speed × vehicle_reduction_factor).

        Reduction factors are user-set calibration parameters — adjust them in
        run_modeling.py to match local travel conditions. Nepal case study defaults:
        foot_reduction_factor = 1.0, vehicle_reduction_factor = 0.32.
    """
    import numpy as np
    import rasterio

    # Open the two speed rasters
    with rasterio.open(foot_speed_raster) as foot_src, rasterio.open(vehicle_speed_raster) as vehicle_src:
        # Read the first band of each raster
        foot_speed = foot_src.read(1)
        vehicle_speed = vehicle_src.read(1)

        # Ensure both rasters share the same grid (shape, transform, CRS, etc.)
        foot_meta = foot_src.meta.copy()
        vehicle_meta = vehicle_src.meta.copy()
        foot_meta_filtered = {k: v for k, v in foot_meta.items() if k not in ("dtype", "nodata")}
        vehicle_meta_filtered = {k: v for k, v in vehicle_meta.items() if k not in ("dtype", "nodata")}

        if foot_meta_filtered != vehicle_meta_filtered:
            differences = {key: (foot_meta_filtered.get(key), vehicle_meta_filtered.get(key))
                           for key in foot_meta_filtered.keys()
                           if foot_meta_filtered.get(key) != vehicle_meta_filtered.get(key)}
            raise ValueError(f"Metadata mismatch (excluding 'dtype' and 'nodata'): {differences}")

        # Ensure NaN values mark the same cells in both rasters (outside study area)
        foot_nan = np.isnan(foot_speed)
        vehicle_nan = np.isnan(vehicle_speed)
        mismatch_mask = foot_nan ^ vehicle_nan
        if np.any(mismatch_mask):
            i, j = np.argwhere(mismatch_mask)[0]
            raise ValueError(f"Cell at ({i}, {j}) has one NaN and one valid value: "
                             f"foot={foot_speed[i, j]}, vehicle={vehicle_speed[i, j]}")

        # For valid cells, take the faster of reduced foot vs. reduced vehicle speed
        both_valid = ~(foot_nan | vehicle_nan)
        combined_speed = np.full(foot_speed.shape, np.nan, dtype=np.float32)
        combined_speed[both_valid] = np.maximum(
            foot_speed[both_valid] * foot_reduction_factor,
            vehicle_speed[both_valid] * vehicle_reduction_factor
        )

        # Save the combined speed raster
        foot_meta.update(dtype="float32")
        with rasterio.open(output_speed_raster, "w", **foot_meta) as output_raster:
            output_raster.write(combined_speed, 1)