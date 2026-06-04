import rasterio
import numpy as np

def Func_WalkSpeed_by_LandCover(input_tiff, output_tiff):
    """
    Convert a land cover classification raster to a travel speed raster.

    Parameters:
        input_tiff (str): Path to the input land cover classification raster.
        output_tiff (str): Path to save the output travel speed raster.

    Returns:
        None
    """
    # --- Nepal case study: land-cover class -> foot travel speed (km/h) ---
    # Matches class codes 1-8 in DATA_DESCRIPTION.md. 
    # Edit for your own land-cover legend and local walk-speed parameters.
    travel_speed_map = {
        1: 3.24,  # Forest
        2: 3.6,   # Shrubland
        3: 4.86,  # Grassland
        4: 3.24,  # Agriculture Area
        5: 3.0,   # Barren Area
        6: 0,     # Water Body
        7: 1.62,  # Snow/Glacier
        8: 5.0    # Built-up Area
    }

    # Open the input raster
    with rasterio.open(input_tiff) as src:
        input_data = src.read(1)  # Read the first band
        meta = src.meta.copy()   # Copy the metadata

    # Create an output array with the same shape as the input raster
    output_data = np.full_like(input_data, np.nan, dtype=np.float32)

    # Map the input classification values to travel speed
    for land_cover, speed in travel_speed_map.items():
        output_data[input_data == land_cover] = speed

    # Preserve NaN values from the input raster
    output_data[np.isnan(input_data)] = np.nan

    # Update metadata for the output raster
    meta.update({
        'dtype': 'float32',  # Use float32 to support NaN
        'nodata': np.nan     # Define the NoData value as NaN
    })

    # Write the output raster to a new file
    with rasterio.open(output_tiff, 'w', **meta) as dst:
        dst.write(output_data, 1)
