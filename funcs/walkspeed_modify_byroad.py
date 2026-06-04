import geopandas as gpd
import numpy as np
import rasterio
from rasterio.features import rasterize
from shapely.geometry import box


def Func_Modify_WalkSpeed_by_Roads(input_raster, roads_geojson, output_raster, footpath_speed=5):
    """
    Updates a walk speed raster by adding footpath cells from all geometries in a GeoJSON.

    :param input_raster: Path to the input walk speed GeoTIFF
    :param roads_geojson: Path to the GeoJSON containing road geometries
    :param output_raster: Path to save the updated walk speed GeoTIFF
    :param footpath_speed: Walk speed for footpath cells (default: 5 km/h)
    """
    # Load the roads GeoJSON
    gdf = gpd.read_file(roads_geojson)

    # Load the input raster
    with rasterio.open(input_raster) as ref_raster:
        ref_meta = ref_raster.meta.copy()
        ref_transform = ref_raster.transform
        ref_crs = ref_meta['crs']
        ref_array = ref_raster.read(1)  # Read the first band
        ref_bounds = ref_raster.bounds

    # Reproject the GeoDataFrame to the raster's CRS
    if gdf.crs != ref_crs:
        gdf = gdf.to_crs(ref_crs)

    # Filter geometries that intersect the reference raster bounds
    gdf = gdf[gdf.intersects(box(*ref_bounds))]
    if gdf.empty:
        raise ValueError("No geometries intersect the reference raster bounds.")

    # Buffer the geometries by a small size (e.g., 1/10th of a raster cell size)
    buffer_size = ref_transform[0] * 0.4  # Assuming square cells
    gdf['geometry'] = gdf['geometry'].buffer(buffer_size)

    # Remove invalid or empty geometries after buffering
    gdf = gdf[gdf.is_valid & ~gdf.is_empty]
    if gdf.empty:
        raise ValueError("No valid geometries found after buffering.")

    # Rasterize the buffered geometries
    def rasterize_footpaths(gdf, ref_array, transform):
        # Rasterize the buffered geometries
        raster = rasterize(
            [(geom, 1) for geom in gdf.geometry],
            out_shape=ref_array.shape,
            transform=transform,
            fill=0,
            all_touched=True  # Ensure 4-point connectivity
        ).astype(np.float32)

        # Handle NaN cells in the reference raster
        raster[np.isnan(ref_array)] = np.nan
        return raster

    footpath_raster = rasterize_footpaths(gdf, ref_array, ref_transform)

    # Update the base raster with the new footpath cells
    updated_raster = np.copy(ref_array)
    updated_raster[footpath_raster == 1] = footpath_speed

    # Save the updated raster
    ref_meta.update(dtype='float32', count=1, compress='lzw')
    with rasterio.open(output_raster, 'w', **ref_meta) as out_raster:
        out_raster.write(updated_raster, 1)
