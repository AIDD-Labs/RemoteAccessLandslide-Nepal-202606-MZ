"""Build a destination-node pickle from a destination raster (aligned to the base grid)."""

import pickle
from pathlib import Path

import numpy as np
import rasterio


def destination_raster_to_pickle(
    destination_raster_path,
    output_pickle_path,
    reference_raster_path=None,
):
    """
    Convert a destination GeoTIFF to a node-collection pickle for shortest-path routing.

    Each cell with a finite value **> 0** becomes one target node ``(row, col)``.
    The cell value is used as the node id when it is a whole number; otherwise a
    running index is assigned.

    Parameters
    ----------
    destination_raster_path : str or Path
        GeoTIFF band 1: destination markers (e.g. count or flag per cell).
    output_pickle_path : str or Path
        Where to write the pickle dict ``{(row, col): id_str, ...}``.
    reference_raster_path : str or Path, optional
        If given, destination raster must match this raster's shape, transform, and CRS.

    Returns
    -------
    dict
        The node collection written to the pickle file.
    """
    destination_raster_path = Path(destination_raster_path)
    output_pickle_path = Path(output_pickle_path)

    with rasterio.open(destination_raster_path) as src:
        data = np.asarray(src.read(1), dtype=np.float64)
        dest_meta = src.meta.copy()

    if reference_raster_path is not None:
        with rasterio.open(reference_raster_path) as ref:
            ref_meta = ref.meta.copy()
        ref_filtered = {k: v for k, v in ref_meta.items() if k not in ("dtype", "nodata")}
        dest_filtered = {k: v for k, v in dest_meta.items() if k not in ("dtype", "nodata")}
        if ref_filtered != dest_filtered:
            raise ValueError(
                "Destination raster grid must match the reference raster "
                "(shape, transform, CRS)."
            )

    nodes_collection = {}
    fallback_id = 0
    rows, cols = data.shape

    for row in range(rows):
        for col in range(cols):
            value = data[row, col]
            if not np.isfinite(value) or value <= 0:
                continue
            if value == np.floor(value):
                node_id = str(int(value))
            else:
                node_id = str(fallback_id)
                fallback_id += 1
            nodes_collection[(int(row), int(col))] = node_id

    if not nodes_collection:
        raise ValueError(
            f"No destination cells (value > 0) found in {destination_raster_path}."
        )

    output_pickle_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_pickle_path, "wb") as f:
        pickle.dump(nodes_collection, f)

    print(
        f"Destination nodes: {len(nodes_collection)} cells -> {output_pickle_path}"
    )
    return nodes_collection
