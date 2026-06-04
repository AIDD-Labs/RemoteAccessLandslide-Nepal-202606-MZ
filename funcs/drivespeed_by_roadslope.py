import numpy as np
import rasterio


def Func_DriveSpeed_by_Road_Slope(
    road_class_tiff_path,
    slope_tiff_path,
    output_speed_tiff_path
):
    """
    Calculates driving speed based on road class and slope.

    :param road_class_tiff_path: Path to the road classification raster (0, 1-4, NaN)
    :param slope_tiff_path: Path to the slope raster (% values)
    :param output_speed_tiff_path: Path to save the output speed raster
    """
    # Define speed lookup table
    speed_lookup = {
        1: {  # Strategic Road Network (SRN)
            (0, 10): 50,
            (10, 25): 40,
            (25, 60): 30,
            (60, 100): 20,
        },
        2: {  # District Road Core Network (DRCN)
            (0, 10): 40,
            (10, 25): 30,
            (25, 60): 20,
            (60, 100): 15,
        },
        3: {  # Strategic Urban Road (SUR) and unpaved roads
            (0, 10): 20,
            (10, 25): 15,
            (25, 60): 10,
            (60, 100): 7.5,
        },
        4: {  # Village Roads (VR) and Paths
            (0, 10): 5,
            (10, 25): 3.8,
            (25, 60): 2.5,
            (60, 100): 1.875,
        },
    }

    def get_speed(road_class, slope):
        """Lookup speed based on road class and slope."""
        if road_class in speed_lookup:
            for slope_range, speed in speed_lookup[road_class].items():
                if slope_range[0] <= slope < slope_range[1]:
                    return speed
        return 0  # Default speed if no match

    # Read raster data
    with rasterio.open(road_class_tiff_path) as road_src:
        road_class = road_src.read(1)  # Read the first band
        road_meta = road_src.meta.copy()

    with rasterio.open(slope_tiff_path) as slope_src:
        slope = slope_src.read(1)  # Read the first band
        slope_meta = slope_src.meta.copy()

    # Check metadata, ignoring 'dtype' and 'nodata'
    road_meta_filtered = {k: v for k, v in road_meta.items() if k not in ("dtype", "nodata")}
    slope_meta_filtered = {k: v for k, v in slope_meta.items() if k not in ("dtype", "nodata")}

    if road_meta_filtered != slope_meta_filtered:
        differences = {key: (road_meta_filtered.get(key), slope_meta_filtered.get(key))
                       for key in road_meta_filtered.keys() if road_meta_filtered.get(key) != slope_meta_filtered.get(key)}
        raise ValueError(f"Metadata mismatch (excluding 'dtype' and 'nodata'): {differences}")

    
    # Prepare output speed raster with NaN initially
    speed_raster = np.full(road_class.shape, np.nan, dtype=np.float32)

    # Calculate speed for each cell
    for i in range(road_class.shape[0]):
        for j in range(road_class.shape[1]):
            road_value = road_class[i, j]
            slope_value = slope[i, j]

            if np.isnan(road_value):  # If road class is NaN
                speed_raster[i, j] = np.nan
            elif road_value == 0:  # No road
                speed_raster[i, j] = 0
            elif not np.isnan(slope_value):  # Valid road class and slope
                speed_raster[i, j] = get_speed(int(road_value), slope_value)

    # Use metadata from road classification raster for output
    output_meta = road_meta
    output_meta.update(dtype="float32", compress="lzw")

    # Save the output raster
    with rasterio.open(output_speed_tiff_path, "w", **output_meta) as output_tiff:
        output_tiff.write(speed_raster, 1)

    print(f"Driving speed raster saved to {output_speed_tiff_path}")
