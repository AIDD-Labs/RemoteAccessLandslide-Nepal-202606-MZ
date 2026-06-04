import numpy as np
import rasterio

def Func_Modify_WalkSpeed_by_Elevation(walk_speed_raster_path, elevation_raster_path, output_raster_path):
    """
    Modify walking speed based on elevation modification factors.

    Parameters:
        walk_speed_raster_path (str): Path to the walking speed raster.
        elevation_raster_path (str): Path to the elevation raster.
        output_raster_path (str): Path to save the modified walking speed raster.

    Behavior:
        - The walking speed and elevation rasters must have the same dimensions and NaN cells.
        - For non-NaN cells, apply an elevation modification factor:
          - Elevation 0-3000: factor 1
          - Elevation 3000-4000: factor 0.8
          - Elevation 4000-5000: factor 0.6
          - Elevation 5000-6000: factor 0.4
          - Elevation >= 6000: factor 0.2
        - Multiply the factor with the walking speed for each cell.
        - Save the modified walking speed raster to the specified output path.
    """
    # Open the walking speed raster
    with rasterio.open(walk_speed_raster_path) as walk_speed_src:
        walk_speed = walk_speed_src.read(1)  # Read the first band
        walk_speed_meta = walk_speed_src.meta  # Metadata for output raster

    # Open the elevation raster
    with rasterio.open(elevation_raster_path) as elevation_src:
        elevation = elevation_src.read(1)  # Read the first band

        # Ensure dimensions match
        if walk_speed.shape != elevation.shape:
            raise ValueError("The walking speed and elevation rasters must have the same dimensions.")

    # Handle NaN cells
    nan_mask = np.isnan(walk_speed) | np.isnan(elevation)

    # Initialize the modification factor array
    modification_factor = np.ones_like(elevation)

    # Apply elevation modification factors
    modification_factor[(elevation > 3000) & (elevation <= 4000)] = 0.8
    modification_factor[(elevation > 4000) & (elevation <= 5000)] = 0.6
    modification_factor[(elevation > 5000) & (elevation <= 6000)] = 0.4
    modification_factor[elevation > 6000] = 0.2

    # Apply the modification factor to the walking speed
    modified_walk_speed = walk_speed * modification_factor

    # Retain NaN cells in the output
    modified_walk_speed[nan_mask] = np.nan

    # Update metadata for the output raster
    walk_speed_meta.update(dtype="float32")

    # Save the modified raster to the output path
    with rasterio.open(output_raster_path, 'w', **walk_speed_meta) as dst:
        dst.write(modified_walk_speed.astype(np.float32), 1)

    print(f"Modified walking speed raster saved to: {output_raster_path}")
