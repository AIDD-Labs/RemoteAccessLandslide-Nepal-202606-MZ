# Input Data Description (Nepal Landslide Case Study)

This document describes **what data to prepare** before running the travel-speed and access-time workflow (`2_1`–`3_2`). It lists **original sources**, **original formats**, and **final prepared products**. It does not include processing code—only where the data came from and what each file should contain.

Prepared data for this project are described in notebooks **`1_0`** through **`1_4`**.

---

## Base raster grid (required for all layers)

All GeoTIFF layers used in modeling must share the **same raster base**:

| Property | Must match across layers |
|----------|-------------------------|
| Width and height (rows × cols) | Yes |
| Affine transform (origin, pixel size, rotation) | Yes |
| CRS | Yes |

**You choose the base raster and cell size.** In this Nepal study, the base grid was defined from a **population** layer after clipping to the study boundary and aggregating cells (see §1). Another project could use a DEM, a blank template, or any reference grid—but every subsequent raster must be resampled or rasterized to that same grid.

Outside the study area, cells should be **`NaN`** (not zero), unless a layer explicitly uses zero with a documented meaning (e.g. “no road”).

---

## 1. Population (typical base grid for this project)

| Item | Detail |
|------|--------|
| **Notebook** | `1_1_Data_Prep_Population.ipynb` |
| **Original source** | Meta High Resolution Population Density Maps for Nepal |
| **Source link** | https://dataforgood.facebook.com/dfg/docs/methodology-high-resolution-population-density-maps |
| **Original file (example)** | `data/raw/population_npl_2018-10-01.tif` |
| **Original format** | GeoTIFF, band 1 = population count (or density per cell, depending on Meta product version) |
| **Original resolution (this study)** | ~30.9 m × 30.9 m (noted in notebook before aggregation) |

**Final prepared product**

| File (example) | `data/input/MFD_population.tif` |
|----------------|----------------------------------|
| Format | GeoTIFF, `float`, band 1 |
| Values | People per cell (≥ 0 inside study area) |
| Outside study | `NaN` |
| Grid role | **Base grid** for this project: clipped to study boundary, cells aggregated **3×3** (~90 m) in the Nepal workflow |

**Notes for other users:** Pick your own cell size when building the base (e.g. 30 m, 90 m, 100 m). All other rasters must be aligned to whatever base you define.

---

## 2. Study area boundary (optional but used in prep)

| Item | Detail |
|------|--------|
| **Notebook** | `1_0_Data_Prep_StudyArea.ipynb` |
| **Original source** | Nepal district boundaries (31 earthquake-affected districts), MoFALD / HRRP |
| **Original file (example)** | `data/raw/District/districts_31A/31Adist_polbnda_adm3_MoFALD_HRRP_wgs84.shp` |
| **Original format** | Esri shapefile; district name field `HRRP_DNAME` |

**Final prepared products**

| File | Format | Content |
|------|--------|---------|
| `data/input/MFD_districts.geojson` | GeoJSON polygons | 14 most-affected districts (subset of the 31) |
| `data/input/MFD_boundary.geojson` | GeoJSON polygon | Single dissolved outer boundary of those districts |

Used to clip rasters and filter vector data. Not required inside the speed/network math itself, but defines the Nepal study extent.

---

## 3. Land cover

| Item | Detail |
|------|--------|
| **Notebook** | `1_2_Data_Prep_Ground_Maps.ipynb` |
| **Original source** | ICIMOD, *Land Cover of Nepal 2010* |
| **Source link** | https://rds.icimod.org/Home/DataDetail?metadataId=9224&searchlist=True |
| **Original file (example)** | `data/raw/Land cover of Nepal 2010/data/np_lc_2010_v2f.tif` |
| **Original format** | GeoTIFF, categorical integer classes |

**Final prepared product**

| File (example) | `data/input/MFD_landcover.tif` |
|----------------|--------------------------------|
| Format | GeoTIFF, band 1, resampled to the **base grid** |
| Class codes | Integer **1–8** (used by foot-speed lookup in modeling): |

| Code | Class |
|------|--------|
| 1 | Forest |
| 2 | Shrubland |
| 3 | Grassland |
| 4 | Agriculture |
| 5 | Barren |
| 6 | Water body |
| 7 | Snow / glacier |
| 8 | Built-up |

| Outside study | `NaN` |

---

## 4. Elevation

| Item | Detail |
|------|--------|
| **Notebook** | `1_2_Data_Prep_Ground_Maps.ipynb` |
| **Original source** | USGS SRTM (via Earth Engine export in notebook) |
| **Source links** | https://www.usgs.gov/centers/eros/science/usgs-eros-archive-digital-elevation-shuttle-radar-topography-mission-srtm-1 |
| | https://developers.google.com/earth-engine/datasets/catalog/USGS_SRTMGL1_003 |
| **Original file (example)** | `data/raw/Nepal_Elevation.tif` |
| **Original format** | GeoTIFF, elevation in **meters** |

**Final prepared product**

| File (example) | `data/input/MFD_Elevation.tif` |
|----------------|-------------------------------|
| Format | GeoTIFF, `float`, band 1, resampled to **base grid** |
| Values | Elevation (m) |
| Outside study | `NaN` |

---

## 5. Slope

| Item | Detail |
|------|--------|
| **Notebook** | `1_2_Data_Prep_Ground_Maps.ipynb` |
| **Original source** | Derived from elevation (SRTM-based raster in project) |
| **Original file (example)** | `data/raw/Nepal_Slope.tif` |
| **Original format** | GeoTIFF |

**Final prepared product**

| File (example) | `data/input/MFD_Slope.tif` |
|----------------|---------------------------|
| Format | GeoTIFF, `float`, band 1, resampled to **base grid** |
| Values | Slope in **percent (%)** — used for walk speed, drive speed, and zigzag correction |
| Outside study | `NaN` |

---

## 6. Surface water

| Item | Detail |
|------|--------|
| **Notebook** | `1_2_Data_Prep_Ground_Maps.ipynb` |
| **Original source** | OpenStreetMap Nepal extract (Geofabrik) |
| **Source link** | https://download.geofabrik.de/asia/nepal.html |
| **Original files (example)** | `data/raw/nepal_osm_water/gis_osm_water_a_free_1.shp` (polygons) |
| | `data/raw/nepal_osm_water/gis_osm_waterways_free_1.shp` (lines) |
| **Original format** | Esri shapefile, line/polygon geometries |

**Final prepared product**

| File (example) | `data/process/MFD_water_merged.tif` |
|----------------|-----------------------------------|
| Format | GeoTIFF, band 1, on **base grid** |
| Values | **`0`** = land, **`1`** = water (not walkable), **`NaN`** = outside study |

Intermediate prep files (`MFD_waterbody.tif`, `MFD_waterways.tif`) are optional; modeling uses the **merged** mask.

---

## 7. Roads (vector + raster)

| Item | Detail |
|------|--------|
| **Notebook** | `1_2_Data_Prep_Ground_Maps.ipynb` |
| **Original source** | OpenStreetMap Nepal roads (Geofabrik) |
| **Source link** | https://download.geofabrik.de/asia/nepal.html |
| **Original file (example)** | `data/raw/nepal_osm_roads/gis_osm_roads_free_1.shp` |
| **Original format** | Esri shapefile; OSM attribute **`fclass`** (road type) |

**Final prepared products**

| File (example) | Format | Content |
|----------------|--------|---------|
| `data/input/MFD_roads.geojson` | GeoJSON lines | Roads intersecting study area; numeric **`class`** **1–4** from OSM `fclass` grouping (see notebook / `Funcs_Road_Classification`) |

| Class | Typical OSM types (summary) |
|-------|-----------------------------|
| 1 | trunk, trunk_link |
| 2 | primary, primary_link, secondary, secondary_link |
| 3 | tertiary, residential, service, unclassified, track grades 1–3 |
| 4 | track, path, footway, steps, etc. |

| File (example) | `data/process/MFD_roads.tif` |
|----------------|------------------------------|
| Format | GeoTIFF on **base grid** |
| Values | **`0`** = no road, **`1–4`** = road class, **`NaN`** = outside study |

Modeling uses **vector** roads for footpath speeds and **raster** roads for vehicle speeds (raster can be built from the same GeoJSON on your base grid).

---

## 8. Landslide impact mask

| Item | Detail |
|------|--------|
| **Notebook** | `1_4_Data_Prep_Landslides.ipynb` |
| **Original source** | USGS / Roback et al., landslides from 2015 Gorkha earthquake |
| **Source link** | https://www.sciencebase.gov/catalog/item/582c74fbe4b04d580bd377e8 |
| **Original file (example)** | `data/raw/Roback_Nepal_final_files/Full20170209/Full20170209.shp` |
| **Original format** | Esri shapefile, landslide polygons |
| **Notebook note** | Earth Engine script link also recorded for alternate extraction |

**Final prepared product**

| File (example) | `data/input/MFD_landslide.tif` |
|----------------|-------------------------------|
| Format | GeoTIFF, band 1, rasterized to **base grid** |
| Values | **`1`** = landslide-affected cell (blocked in post scenario), **`0`** = not landslide, **`NaN`** = outside study |

---

## 9. Destinations (for access-time calculation)

| Item | Detail |
|------|--------|
| **Notebook** | `1_3_Data_Prep_Destination.ipynb` |
| **Original source (example: hospitals)** | NDRRMA healthcare facility locations |
| **Original file (example)** | `data/raw/NDRRMA_health.geojson` |
| **Original format** | GeoJSON points; fields include `id`, `type`, etc. |

**Final prepared products (examples from this study)**

| File | Format | Content |
|------|--------|---------|
| `data/input/MFD_healthcare.geojson` | GeoJSON points | Facilities clipped to boundary; added field **`class`**: `Hospital` or `Clinic` |
| `data/process/MFD_healthcare_hospital_nodes_collection.tif` | GeoTIFF on **base grid** | One or more hospital cells with value **> 0** (often `1`) per occupied cell |

For access-time modeling you need a **destination raster** on the base grid:

| Requirement | Detail |
|-------------|--------|
| Band 1 | **`> 0`** marks a destination cell; **`NaN`** outside study |
| Meaning | Each positive cell is a target for shortest-path routing (nearest-destination travel time) |

You may use any destination set (hospitals, markets, schools, etc.) as long as it is expressed as this raster on your chosen base grid. The Nepal hospital example above is one prepared instance.

---

## 10. Other vectors from study-area prep (optional)

Documented in `1_0_Data_Prep_StudyArea.ipynb` for reference or auxiliary analysis—not all are used in the core `2_1`–`3_2` speed pipeline:

| Source (example) | Original | Final (example) |
|------------------|----------|-----------------|
| IER household survey locations | `data/raw/IER-HH-Locations.xlsx` (columns `LAT`, `LON`) | `data/input/AF_survey_locations.geojson` |
| District headquarters | `data/raw/District/district_headquarters/disthq_GCSWGS1984.shp` | `data/input/AF_district_headquarters.geojson` |

---

## Summary checklist for modeling (`2_1` → `3_2`)

Prepare these aligned to **your** base grid:

| Layer | Prepared file (Nepal examples) | Key value rules |
|-------|-------------------------------|-----------------|
| Base / mask | User-defined (here: `MFD_population.tif`) | Defines extent and cell size |
| Land cover | `MFD_landcover.tif` | Integers 1–8 |
| Water | `MFD_water_merged.tif` | 0 / 1 / NaN |
| Roads (vector) | `MFD_roads.geojson` | `class` 1–4 |
| Roads (raster) | `MFD_roads.tif` | 0, 1–4, NaN |
| Slope | `MFD_Slope.tif` | Percent |
| Elevation | `MFD_Elevation.tif` | Meters |
| Landslide | `MFD_landslide.tif` | 0 / 1 / NaN |
| Destinations | e.g. `*_nodes_collection.tif` | > 0 at target cells |

---

## References (as cited in project notebooks)

- Meta population maps: https://dataforgood.facebook.com/dfg/docs/methodology-high-resolution-population-density-maps  
- ICIMOD land cover 2010: https://rds.icimod.org/Home/DataDetail?metadataId=9224&searchlist=True  
- USGS SRTM: https://developers.google.com/earth-engine/datasets/catalog/USGS_SRTMGL1_003  
- Geofabrik OSM Nepal: https://download.geofabrik.de/asia/nepal.html  
- USGS 2015 Nepal landslides: https://www.sciencebase.gov/catalog/item/582c74fbe4b04d580bd377e8  
