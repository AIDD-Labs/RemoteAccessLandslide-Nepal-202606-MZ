import rasterio
import numpy as np

def Func_Modify_WalkSpeed_by_Roads(walking_speed_raster, roads_raster, output_raster, footpath_speed=5):
    """
    Processes two rasters (walking speed and roads) based on the following rules:
    - Both rasters should have the same cell system (dimensions, transform, etc.).
    - Both rasters should have NaN at the same cells; if not, raise an error.
    - For non-NaN cells:
        - If the roads raster has a value >= 1 (road present), set the output cell to
          footpath_speed (default 5 km/h).
        - If the roads raster has a value of 0, retain the walking speed value from the input.

    Parameters:
        walking_speed_raster (str): Path to the input walking speed raster.
        roads_raster (str): Path to the input road-class raster (0 = no road, 1-4 = road class).
        output_raster (str): Path to save the processed raster.
        footpath_speed (float): Walk speed on road cells in km/h. Default 5.

    Returns:
        None: Saves the processed raster to the specified path.
    """
    # Open the two rasters
    with rasterio.open(walking_speed_raster) as speed_src, rasterio.open(roads_raster) as roads_src:
        # Ensure both rasters have the same dimensions and transform
        if speed_src.shape != roads_src.shape or speed_src.transform != roads_src.transform:
            raise ValueError("Input rasters must have the same shape and transform.")

        # Read the first bands of both rasters
        walking_speed = speed_src.read(1)
        roads = roads_src.read(1)

        # Ensure NaN values are consistent between the two rasters
        nan_speed = np.isnan(walking_speed)
        nan_roads = np.isnan(roads)
        if not np.array_equal(nan_speed, nan_roads):
            raise ValueError("Input rasters have mismatched NaN values.")

        # Create the output raster
        output = np.copy(walking_speed)

        # Process non-NaN cells
        road_cells = (roads >= 1)
        non_road_cells = (roads == 0)

        # Apply rules
        output[road_cells] = footpath_speed                        # Roads set to footpath speed
        output[non_road_cells] = walking_speed[non_road_cells]    # Retain walking speed elsewhere

        # Save the processed raster
        out_meta = speed_src.meta.copy()
        out_meta.update(dtype='float32', count=1, compress='lzw')

        with rasterio.open(output_raster, 'w', **out_meta) as dst:
            dst.write(output, 1)
