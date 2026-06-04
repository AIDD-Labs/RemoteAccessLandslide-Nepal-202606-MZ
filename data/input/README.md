# Prepared input data

Place all required prepared files in this folder before running `run_modeling.py`.

## Required files

- `landcover.tif`
- `water_merged.tif`
- `roads.geojson` (must include numeric `class` column 1–4)
- `slope.tif`
- `elevation.tif`
- `landslide.tif`
- `destination_raster.tif`

## Grid alignment

All GeoTIFF inputs must use the **same base grid** (shape, affine transform, CRS). Outside the study area, cells should be `NaN`.

## Destination raster

`destination_raster.tif` marks destination cells on the base grid (value > 0). The pipeline writes `data/process/destination_nodes.pkl` from this raster before access-time calculation.

## Local setup in this workspace

Files here may be symlinks to prepared data elsewhere. When syncing to GitHub, copy or LFS-track the actual files.
