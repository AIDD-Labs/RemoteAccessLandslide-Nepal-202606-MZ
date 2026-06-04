import numpy as np
import rasterio


def Func_Access_Diff(normal_access_path, landslide_access_path, output_path, diff_type="absolute"):
    """
    Compute the difference between normal and landslide access-time rasters.

    Uses the normal access raster as the base grid (shape, transform, and study mask).

    Parameters:
        normal_access_path (str): Path to the normal access raster (GeoTIFF).
        landslide_access_path (str): Path to the landslide access raster (GeoTIFF).
        output_path (str): Path to save the resulting difference raster (GeoTIFF).
        diff_type (str): "absolute" or "percentage". Default is "absolute".

    Returns:
        None: Saves the difference raster to the specified path.
    """
    # Open both access rasters
    with rasterio.open(normal_access_path) as src_normal, rasterio.open(landslide_access_path) as src_landslide:
        if src_normal.shape != src_landslide.shape or src_normal.transform != src_landslide.transform:
            raise ValueError("Access rasters must have the same shape and transform.")

        normal_access = src_normal.read(1).astype(np.float32)
        landslide_access = src_landslide.read(1).astype(np.float32)
        meta = src_normal.meta.copy()

    # Study-area mask from the normal access raster (NaN = outside study)
    outside_study = np.isnan(normal_access)
    output_raster = np.full_like(normal_access, np.nan, dtype=np.float32)

    # Absolute difference: landslide access time minus normal (hours)
    if diff_type == "absolute":
        # Treat NaN as 0 only for arithmetic inside the study area
        normal_work = np.where(outside_study, 0, normal_access)
        landslide_work = np.where(np.isnan(landslide_access), 0, landslide_access)
        output_raster = landslide_work - normal_work
        output_raster[outside_study] = np.nan

    # Percentage change: (landslide - normal) / normal
    elif diff_type == "percentage":
        diff = landslide_access - normal_access
        with np.errstate(divide="ignore", invalid="ignore"):
            pct = np.where(normal_access != 0, diff / normal_access, np.nan)
        pct[outside_study] = np.nan
        pct[np.isnan(landslide_access) & ~outside_study] = np.nan
        pct[np.isinf(normal_access) & ~outside_study] = 0       # was unreachable before
        pct[(normal_access == 0) & ~outside_study] = np.inf    # zero baseline -> undefined ratio
        output_raster = pct.astype(np.float32)

    else:
        raise ValueError("Invalid diff_type. Use 'absolute' or 'percentage'.")

    # Save the output raster
    meta.update(dtype="float32", compress="lzw")
    with rasterio.open(output_path, "w", **meta) as out_raster:
        out_raster.write(output_raster, 1)
