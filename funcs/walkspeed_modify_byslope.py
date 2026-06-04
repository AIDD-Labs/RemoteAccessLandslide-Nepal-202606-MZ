import numpy as np
import rasterio

def Func_Modify_WalkSpeed_by_Slope(walk_speed_raster_path, slope_raster_path, output_raster_path):
    """
    Modify a walking speed raster based on a slope raster using a specific modification factor.
    
    Parameters:
        walk_speed_raster_path (str): Path to the walking speed raster (input).
        slope_raster_path (str): Path to the slope raster in degrees (input).
        output_raster_path (str): Path to save the modified walking speed raster (output).

    Note:
        Nepal landslide case study — edit the cap, formula, and slope units below for
        your own local parameters.

        - Slope values are capped at 30 degrees to avoid unrealistic speed reductions.
        - Slope raster is in degrees; convert to radians before applying the formula.
        - modification_factor = exp(-3.5 * abs(tan(slope_radians) + 0.05))
        - Multiply walk speed by the modification factor for each cell.
    
    """
    # Open the walking speed raster
    with rasterio.open(walk_speed_raster_path) as walk_speed_src:
        walk_speed = walk_speed_src.read(1)
        meta = walk_speed_src.meta

    # Open the slope raster
    with rasterio.open(slope_raster_path) as slope_src:
        slope = slope_src.read(1)
        
        # Ensure dimensions match
        if walk_speed.shape != slope.shape:
            raise ValueError("The dimensions of the walking speed and slope rasters must match.")
    
    # --- Nepal case study: slope cap and walk-speed factor (edit for your area) ---
    slope_capped = np.minimum(slope, 30)
    
    slope_radians = np.radians(slope_capped)
    modification_factor = np.exp(-3.5 * np.abs(np.tan(slope_radians) + 0.05))
    
    # Apply modification factor to walking speed
    modified_walk_speed = walk_speed * modification_factor
    
    # Retain NaN values
    nan_mask = np.isnan(walk_speed) | np.isnan(slope)
    modified_walk_speed[nan_mask] = np.nan

    # Update metadata for the output raster
    meta.update(dtype="float32")
    
    # Save the modified raster to the specified output path
    with rasterio.open(output_raster_path, 'w', **meta) as dst:
        dst.write(modified_walk_speed.astype(np.float32), 1)
    
    print(f"Modified walking speed raster saved to: {output_raster_path}")
