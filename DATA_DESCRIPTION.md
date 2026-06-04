# Input Data Description (Nepal Landslide Case Study)

This document describes the input data required to run the travel-speed and access-time workflow. It specifies the required input data formats expected by the model and provides example data sources from the Nepal case study.

Data preprocessing scripts are not included, as preprocessing workflows vary substantially across regions and data sources. Users should prepare their own datasets according to the input specifications described in this document.

---

## Base raster grid (required for all layers)

All GeoTIFF layers used in modeling must share the **same raster base**:

| Property | Must match across layers |
|----------|-------------------------|
| Width and height (rows × cols) | Yes |
| Affine transform (origin, pixel size, rotation) | Yes |
| CRS | Yes |

**You choose the base raster and cell size.** In this Nepal study, the base grid was defined from a **population** layer after clipping to the study boundary and aggregating cells (see §1). Another project could use a DEM, a blank template, or any reference grid—but every subsequent raster must be resampled or rasterized to that same grid.

All layers share one **rectangular** GeoTIFF grid; the study boundary itself can be **any shape** (in Nepal, 14 irregular districts inside a rectangular bounding box). After masking, cells **inside** the boundary hold real values (`0` is fine where it means something, e.g. no road); cells **outside** the boundary but still in the raster must be **`NaN`**.

---

## 1. Population (base grid for this project)

**General dataset**

| Item | Detail |
|------|--------|
| **Product** | Meta [High Resolution Population Density Maps](https://ai.meta.com/ai-for-good/docs/methodology-high-resolution-population-density-maps/) 

**Nepal data**

| Item | Detail |
|------|--------|
| **Download** | [Nepal HRSL on HDX](https://data.humdata.org/dataset/nepal-high-resolution-population-density-maps-demographic-estimates) |
| **Original format** | GeoTIFF, band 1 = estimated population count per cell |
| **Original resolution** | ~30.9 m × 30.9 m (before 3×3 aggregation in prep) |

**Processed input data**

| File (example) | `data/input/population.tif` |
|----------------|----------------------------------|
| Format | GeoTIFF, `float`, band 1 |
| Values | People per cell (≥ 0 inside study area) |

**Nepal case study:** Clipped to the study boundary, aggregated **3×3** (~31 m → ~90 m), and used as the **base grid** for all other layers.


---

## 2. Study area boundary (optional but used in prep)

Define **your own** study extent as **one GeoJSON polygon** (single feature or one dissolved multipolygon). Use it when preparing input data to clip rasters and filter vector layers so cells outside the study are `NaN` and features outside the boundary are dropped.

**Processed input data**

| File (example) | `data/input/boundary.geojson` |
|----------------|----------------------------------|
| Format | GeoJSON, one polygon (or dissolved outer ring) |
| Content | Study-area mask in geographic coordinates (reproject to match your base raster CRS when clipping) |

**Nepal case study:** `boundary.geojson` is the outer boundary of the **14 districts most affected by the 2015 Gorkha earthquake** (subset of the 31 HRRP earthquake-affected districts).

---

## 3. Land cover

**General dataset**

You need a **categorical land-cover raster** (integer class per cell) on your base grid. The Nepal study uses a country-specific product; other regions can use any suitable land-cover map (national or global).

| Item | Detail | Data Dowloads |
|------|--------|--------|
| **ESA WorldCover** | https://esa-worldcover.org/en?utm_source=chatgpt.com | https://developers.google.com/earth-engine/datasets/catalog/ESA_WorldCover_v200?utm_source=chatgpt.com | 
| **MODIS Land Cover** | https://www.earthdata.nasa.gov/data/catalog/lpcloud-mcd12q1-061?utm_source=chatgpt.com | https://developers.google.com/earth-engine/datasets/catalog/MODIS_061_MCD12Q1?utm_source=chatgpt.com |

**Nepal data**

| Item | Detail |
|------|--------|
| **Product** | ICIMOD, *Land Cover of Nepal 2010* |
| **Download** | https://rds.icimod.org/Home/DataDetail?metadataId=9224&searchlist=True |
| **Original format** | GeoTIFF, categorical integer classes |

**Processed input data**

| File (example) | `data/input/landcover.tif` |
|----------------|-----------------------------------------------------------|
| Format | GeoTIFF, band 1 |
| Values | Integer class codes **1–8** inside study area |

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

**Using a different land-cover source:** Reclassify your source labels to match codes **1–8** above, *or* edit the class → foot-speed table in `funcs/walkspeed_bylandcover.py` (`travel_speed_map` in `Func_WalkSpeed_by_LandCover`) so each input class maps to the correct travel speed (km/h) for your legend.

---

## 4. Elevation

**General dataset**

| Item | Detail | Data Dowloads |
|------|--------|---------------|
| **USGS SRTM** (~30 m) | https://www.usgs.gov/centers/eros/science/usgs-eros-archive-digital-elevation-shuttle-radar-topography-mission-srtm-1 | https://developers.google.com/earth-engine/datasets/catalog/USGS_SRTMGL1_003 |

**Nepal data (this case study)**

| Item | Detail |
|------|--------|
| **Access** | Exported from Google Earth Engine|
| **Original format** | GeoTIFF, band 1 = elevation (**meters**) |
| **Original resolution** | ~30 m (SRTM) |

**Processed input data**

| File (example) | `data/input/elevation.tif`  |
|----------------|----------------------------------------------------------|
| Format | GeoTIFF, `float`, band 1|
| Values | Elevation (m) |


---

## 5. Slope

**Note:** In the Nepal case study, the slope layer is derived from the elevation layer (§4) as ready-made slope raster is not commonly distributed. If you have a slope product in your study area, you may use it directly.

**Processed input data**

| File (example) | `data/input/slope.tif` |
|----------------|---------------------------|
| Format | GeoTIFF, `float`, band 1|
| Values | Terrain slope in **percent (%)**: **0** (flat) to **90** (very steep) |

---

## 6. Surface water

**General dataset**

| Item | Detail | Avaliable Through |
|------|--------|---------------|
| **OpenStreetMap** | https://www.openstreetmap.org/about | Geofabrik OSM extracts https://download.geofabrik.de/ |

**Nepal data (this case study)**

| Item | Detail |
|------|--------|
| **Download** | https://download.geofabrik.de/asia/nepal.html |
| **Original files** | `gis_osm_water_a_free_1.shp` (water polygons), `gis_osm_waterways_free_1.shp` (waterway lines) |
| **Original format** | Esri shapefile |

**Nepal case study:** The water-polygon and waterway layers were rasterized and **merged** into one layer for the study area.

**Processed input data**

| File (example) | `data/input/water_merged.tif` |
|----------------|-----------------------------------|
| Format | GeoTIFF, band 1 |
| Values | **`0`** = land, **`1`** = water (not walkable) |

---

## 7. Roads

**General dataset**

| Item | Detail | Avaliable Through |
|------|--------|---------------|
| **OpenStreetMap** | https://www.openstreetmap.org/about | Geofabrik OSM extracts https://download.geofabrik.de/ |

**Nepal data (this case study)**

| Item | Detail |
|------|--------|
| **Download** | https://download.geofabrik.de/asia/nepal.html |
| **Original file** | `data/raw/nepal_osm_roads/gis_osm_roads_free_1.shp` |
| **Original format** | Esri shapefile; OSM attribute **`fclass`** (road type) |


**Processed input data**

| File (example) | `data/input/roads.tif` |
|----------------|-----------------------------------|
| Format | GeoTIFF, band 1 |
| Values | Integer class codes **`0`** = no road, **`1–4`** = road class from OSM `fclass` grouping|

| Class | Typical OSM types (summary) | Corespodint nepal dsignation|
|-------|-----------------------------| -----------------------------|
| 1 | trunk, trunk_link |Strategic Road Network (SRN) |
| 2 | primary, primary_link, secondary, secondary_link |District Road Core Network (DRCN) | 
| 3 | tertiary, residential, service, unclassified, track grades 1–3 | Strategic Urban Road (SUR) and unpaved roads|
| 4 | track, path, footway, steps, etc. | Village Roads (VR) and Paths |

**Road classes in this study:** Classes **1–4** group OSM `fclass` values to match **Nepal road designations** (SRN, DRCN, SUR, VR). Each class uses a different **road class × slope → speed** lookup in `funcs/drivespeed_by_roadslope.py` (`speed_lookup` in `Func_DriveSpeed_by_Road_Slope`). For other regions, define your own OSM groupings and edit that lookup table to match local road types and speed assumptions.


---

## 8. Hazard impact mask (landslides in this study)

**General:** This layer marks **hazard-affected cells** for the post-event scenario. In Nepal it is the **2015 Gorkha landslide** footprint; elsewhere it can be any hazard (flood, fire, earthquake damage, etc.). Provide a raster on your base grid where **`1`** = affected (blocked or impassable in the hazard run), **`0`** = not affected, the hazard type does not matter, only the mask.

**Nepal data (this case study)**

| Item | Detail |
|------|--------|
| **Original source** | USGS / Roback et al., landslides from 2015 Gorkha earthquake |
| **Download** | https://www.sciencebase.gov/catalog/item/582c74fbe4b04d580bd377e8 |
| **Original file (example)** | `Full20170209/Full20170209.shp` |
| **Original format** | Esri shapefile, landslide polygons |

**Processed input data**

| File (example) | `data/input/landslide.tif` |
|----------------|-------------------------------|
| Format | GeoTIFF, band 1 |
| Values | **`1`** = landslide-affected cell, **`0`** = not landslide |

---

## 9. Destinations (for access-time calculation)

**General:** A raster marking **where your destinations are**. Use any facility set you care about (hospitals, clinics, schools, markets, etc.) from any source—points are rasterized to cells on the base grid. **`1`** = destination cell, **`0`** = not a destination (inside study). The model treats any value **> 0** as a destination for shortest-path routing.

**Nepal data (this case study)**

| Item | Detail |
|------|--------|
| **Destinations used** | Hospitals |
| **Original source** | NDRRMA healthcare facility list |
| **Original format** | GeoJSON points |

**Processed input data**

| File (example) | `data/input/destination.tif` |
|----------------|------------------------------|
| Format | GeoTIFF, band 1, on **base grid** |
| Values | **`1`** at each hospital cell; **`0`** elsewhere|

---
