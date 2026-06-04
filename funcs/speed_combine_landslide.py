import rasterio
import numpy as np

def Func_Combine_Speed_Landslide(base_speed_raster, landslide_raster, output_raster):
    """
    Combines a base speed raster and a landslide map to produce an output raster where:
    - Cells with value 1 in the landslide raster are set to 0 in the output raster (representing no speed).
    - For other cells (0 or NaN in the landslide raster), the cell value from the base speed map is used.

    Parameters:
        base_speed_raster (str): Path to the base speed raster file.
        landslide_raster (str): Path to the landslide raster file.
        output_raster (str): Path to save the resulting raster.

    Returns:
        None: Saves the combined raster to the specified path.
    """
    # Load the base speed raster
    with rasterio.open(base_speed_raster) as base_src:
        base_speed = base_src.read(1)  # Read the first band
        base_meta = base_src.meta  # Get metadata

    # Load the landslide raster
    with rasterio.open(landslide_raster) as landslide_src:
        landslide_data = landslide_src.read(1)  # Read the first band

        # Ensure both rasters have the same dimensions
        if base_speed.shape != landslide_data.shape:
            raise ValueError("The base speed raster and landslide raster must have the same dimensions.")

    # Create the output array
    output_data = np.copy(base_speed)

    # Set cells to 0 where landslide map has value 1
    output_data[landslide_data == 1] = 0

    # Keep base speed values for cells where landslide is 0 or NaN
    # NaN handling is implicit as it does not overwrite existing values in `output_data`

    # Save the output raster
    base_meta.update(dtype='float32', compress='lzw')  # Update metadata for output
    with rasterio.open(output_raster, 'w', **base_meta) as out_raster:
        out_raster.write(output_data, 1)

    print(f"Combined raster saved to {output_raster}")
