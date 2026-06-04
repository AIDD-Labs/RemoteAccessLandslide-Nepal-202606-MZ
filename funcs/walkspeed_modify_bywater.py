import rasterio
import numpy as np

def Func_Modify_WalkSpeed_by_Water(walking_speed_raster, water_area_raster, output_raster):
    """
    Processes two rasters (walking speed and water area) based on the following rules:
    - Both rasters should have the same cell system (dimensions, transform, etc.).
    - Both rasters should have NaN at the same cells; if not, raise an error.
    - For non-NaN cells:
        - If the water raster has a value of 1 (water area), set the output cell to 0 (not walkable).
        - If the water raster has a value of 0, retain the walking speed value from the input.

    Parameters:
        walking_speed_raster (str): Path to the input walking speed raster.
        water_area_raster (str): Path to the input water area raster.
        output_raster (str): Path to save the processed raster.

    """
    # Open the two rasters
    with rasterio.open(walking_speed_raster) as speed_src, rasterio.open(water_area_raster) as water_src:
        # Ensure both rasters have the same dimensions and transform
        if speed_src.shape != water_src.shape or speed_src.transform != water_src.transform:
            raise ValueError("Input rasters must have the same shape and transform.")

        # Read the first bands of both rasters
        walking_speed = speed_src.read(1)
        water_area = water_src.read(1)

        # Ensure NaN values are consistent between the two rasters
        nan_speed = np.isnan(walking_speed)
        nan_water = np.isnan(water_area)
        if not np.array_equal(nan_speed, nan_water):
            raise ValueError("Input rasters have mismatched NaN values.")

        # Create the output raster
        output = np.copy(walking_speed)

        # Process non-NaN cells
        water_cells = (water_area == 1)
        land_cells = (water_area == 0)

        # Apply rules
        output[water_cells] = 0          # Water areas set to 0
        output[land_cells] = walking_speed[land_cells]  # Retain walking speed for land cells

        # Save the processed raster
        out_meta = speed_src.meta.copy()
        out_meta.update(dtype='float32', count=1, compress='lzw')

        with rasterio.open(output_raster, 'w', **out_meta) as dst:
            dst.write(output, 1)
