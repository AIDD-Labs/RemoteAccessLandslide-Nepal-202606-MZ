import rasterio
import numpy as np

def Func_Modify_Speed_by_Zigzag(input_speed, input_slope, output_speed):
    """
    Modifies a speed raster based on the increased distance of a zigzag path on a slope.

    :param input_speed: Path to the input speed raster (GeoTIFF)
    :param input_slope: Path to the slope raster (GeoTIFF)
    :param output_speed: Path to save the modified speed raster (GeoTIFF)
    """
    # Open the speed raster
    with rasterio.open(input_speed) as speed_src:
        speed = speed_src.read(1)  # Read the first band
        meta = speed_src.meta.copy()

    # Open the slope raster
    with rasterio.open(input_slope) as slope_src:
        slope = slope_src.read(1)  # Read the first band
        
        # Ensure dimensions match
        if speed.shape != slope.shape:
            raise ValueError("The dimensions of the speed and slope rasters must match.")
    
    # Create an output array for modified speed
    modified_speed = np.copy(speed)

    # Convert slope to radians
    slope_radians = np.radians(slope)

    # Apply transformation rules
    cos_slope = np.cos(slope_radians)
    tan_slope = np.tan(slope_radians)
    sin_30 = np.sin(np.radians(30))

    # Where slope <= 30 degrees, new speed = old speed * cos(slope angle)
    mask_low_slope = slope <= 30
    modified_speed[mask_low_slope] = speed[mask_low_slope] * cos_slope[mask_low_slope]

    # Where slope > 30 degrees, new speed = old speed * sin(30)/tan(slope angle)
    mask_high_slope = slope > 30
    modified_speed[mask_high_slope] = (
        speed[mask_high_slope] * (sin_30 / tan_slope[mask_high_slope])
    )

    # Maintain NaN values
    modified_speed[np.isnan(speed)] = np.nan

    # Save the modified raster
    meta.update(dtype='float32')
    with rasterio.open(output_speed, 'w', **meta) as out_raster:
        out_raster.write(modified_speed, 1)
