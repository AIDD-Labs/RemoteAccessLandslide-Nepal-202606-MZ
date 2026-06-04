import geopandas as gpd
import rasterio
from shapely.geometry import box
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap

def Func_Road_Classification(shapefile_path, raster_path, output_geojson):
    """
    Selects objects from a shapefile that touch a raster area, categorizes them based on fclass,
    saves the updated GeoDataFrame as GeoJSON, and plots all classes on the same map with distinct colors.

    :param shapefile_path: Path to the input shapefile
    :param raster_path: Path to the reference raster
    :param output_geojson: Path to save the updated GeoJSON file
    """
    # Load the shapefile
    gdf = gpd.read_file(shapefile_path)

    # Check if 'fclass' column exists
    if 'fclass' not in gdf.columns:
        raise ValueError("The shapefile must contain an 'fclass' column.")

    # Open the raster and get its bounding box
    with rasterio.open(raster_path) as raster:
        raster_bounds = raster.bounds
        raster_bbox = box(*raster_bounds)  # Create a shapely box from raster bounds

    # Create a GeoDataFrame for the raster bounding box
    raster_gdf = gpd.GeoDataFrame({"geometry": [raster_bbox]}, crs=raster.crs)

    # Ensure both GeoDataFrames use the same CRS
    gdf = gdf.to_crs(raster_gdf.crs)

    # Select objects that touch the raster area
    selected_objects = gdf[gdf.geometry.intersects(raster_bbox)]

    # Define the categorization rules for fclass
    class_mapping = {
        1: ['trunk', 'trunk_link'],
        2: ['primary','primary_link', 'secondary','secondary_link'],
        3: ['tertiary', 'tertiary_link','residential', 'service', 'unclassified', 
            'track_grade1', 'track_grade2', 'track_grade3'],
        4: ['track', 'track_grade4', 'track_grade5', 'path', 'footway', 'steps', 
            'bridleway', 'cycleway', 'living_street', 'pedestrian', 'unknown']
    }

    # Add a 'class' column based on the mapping
    def determine_class(fclass):
        for class_num, fclasses in class_mapping.items():
            if fclass in fclasses:
                return class_num
        # If fclass is not defined, raise an error
        raise ValueError(f"Undefined fclass encountered: {fclass}")

    selected_objects['class'] = selected_objects['fclass'].apply(determine_class)

    # Save the updated GeoDataFrame as GeoJSON
    selected_objects.to_file(output_geojson, driver="GeoJSON")
    
import geopandas as gpd
import rasterio
from rasterio.features import rasterize
import numpy as np

def Func_Rasterize_Roads(road_shapefile, reference_tiff_path, output_tiff_path):
    """
    Rasterizes road classes from a shapefile into a raster based on a reference TIFF file.
    Each class is rasterized separately and merged by selecting the smallest class number.
    Saves the final raster to the specified output path.

    :param road_shapefile: Path to the road shapefile
    :param reference_tiff_path: Path to the reference GeoTIFF file
    :param output_tiff_path: Path to save the rasterized road GeoTIFF file
    """
    # Load the road shapefile
    gdf = gpd.read_file(road_shapefile)

    # Load the reference TIFF
    with rasterio.open(reference_tiff_path) as ref_src:
        ref_meta = ref_src.meta.copy()
        ref_transform = ref_src.transform
        ref_array = ref_src.read(1)  # Read the first band
        ref_crs = ref_src.crs

    # Check CRS compatibility
    if gdf.crs != ref_crs:
        raise ValueError("CRS of shapefile and reference TIFF do not match.")

    # Ensure the class column is numeric
    if not np.issubdtype(gdf["class"].dtype, np.number):
        gdf["class"] = gdf["class"].astype(int)

    # Buffer all geometries slightly (e.g., 1/10th of a raster cell size)
    buffer_size = ref_transform[0] * 0.4
    gdf["geometry"] = gdf["geometry"].buffer(buffer_size)

    # Drop invalid, None, or empty geometries
    initial_count = len(gdf)
    gdf = gdf[gdf.is_valid & ~gdf.is_empty]
    dropped_count = initial_count - len(gdf)
    if dropped_count > 0:
        print(f"Warning: {dropped_count} invalid or empty geometries were dropped.")

    # Rasterize each class separately
    class_rasters = []
    for road_class in [4, 3, 2, 1]:
        class_geoms = gdf[gdf["class"] == road_class]
        if not class_geoms.empty:
            shapes = [(geom, road_class) for geom in class_geoms.geometry]

            # Rasterize for the current class
            class_raster = rasterize(
                shapes,
                out_shape=ref_array.shape,
                transform=ref_transform,
                fill=np.nan,  # NaN for cells not touched by the current class
                all_touched=True,
                dtype=np.float32,
            )

            # Replace 0 (no road) with NaN
            class_raster = np.where(class_raster == 0, np.nan, class_raster)
            class_rasters.append(class_raster)
        else:
            class_rasters.append(np.full(ref_array.shape, np.nan, dtype=np.float32))

    # Stack the class rasters into a 3D array
    stacked_rasters = np.stack(class_rasters, axis=-1)  # Shape: (rows, cols, 4)

    # Collapse the 3D array to 2D by selecting the lowest non-NaN value
    merged_raster = np.nanmin(stacked_rasters, axis=-1)

    # Set areas without a class to 0
    merged_raster[np.isnan(merged_raster)] = 0

    # Apply NaN mask from the reference raster
    merged_raster[np.isnan(ref_array)] = np.nan

    # Update metadata for the output raster
    ref_meta.update(dtype="float32", count=1, compress="lzw")

    # Save the output raster
    with rasterio.open(output_tiff_path, "w", **ref_meta) as out_tiff:
        out_tiff.write(merged_raster, 1)

    print(f"Rasterized road file saved to {output_tiff_path}")
