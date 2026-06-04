"""Build a destination-node pickle from a destination raster (aligned to the base grid)."""

import pickle

import numpy as np
import rasterio


def destination_raster_to_pickle(destination_raster_path, output_pickle_path):
    """
    Convert a destination GeoTIFF to a pickle list of target cells for shortest-path routing.

    Each cell with a finite value **> 0** becomes one destination ``(row, col)`` on the
    destination raster grid. The cell value itself is not used — only the location matters.

    Parameters
    ----------
    destination_raster_path : str or Path
        GeoTIFF band 1: destination markers on the modeling base grid (value > 0).
    output_pickle_path : str or Path
        Where to write the pickle list ``[(row, col), ...]``.

    Returns
    -------
    list[tuple[int, int]]
        Destination grid cells written to the pickle file.
    """
    # Read destination raster (cells with value > 0 mark a target location)
    with rasterio.open(destination_raster_path) as src:
        data = np.asarray(src.read(1), dtype=np.float64)

    # Collect (row, col) for every destination cell
    destination_nodes = []
    rows, cols = data.shape

    for row in range(rows):
        for col in range(cols):
            value = data[row, col]
            if not np.isfinite(value) or value <= 0:
                continue
            destination_nodes.append((int(row), int(col)))

    if not destination_nodes:
        raise ValueError(
            f"No destination cells (value > 0) found in {destination_raster_path}."
        )

    # Write destination cell list for shortest-path routing
    with open(output_pickle_path, "wb") as f:
        pickle.dump(destination_nodes, f)

    return destination_nodes
