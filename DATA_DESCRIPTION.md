# Input Data Description (Nepal Landslide Case Study)

This document describes the input data required to run the travel-speed and access-time workflow. It specifies the required input data formats expected by the model and provides example data sources from the Nepal case study.

Data preprocessing scripts are not included, as preprocessing workflows vary substantially across regions and data sources. Users should prepare their own datasets according to the input specifications described in this document.

---

## Base raster grid (required for all layers)

All GeoTIFF layers used in modeling must share the **same raster base**:

| Property | Must match across layers |
|----------|--------------------------|
| Width and height (rows × cols) | Yes |
| Affine transform (origin, pixel size, rotation) | Yes |
| CRS | Yes |

**You choose the base raster and cell size.** In this Nepal study, the base grid was defined from a **population** layer after clipping to the study boundary and aggregating cells (see §1). Another project could use a DEM, a blank template, or any reference grid—but every subsequent raster must be resampled or rasterized to that same grid.

All layers share one **rectangular** GeoTIFF grid; the study boundary itself can be **any shape**. After masking:

- Cells **inside** the boundary hold real values (`0` is fine where it means something, e.g. no road).
- Cells **outside** the boundary but still in the raster must be **`NaN`**.

---

## 1. Population (base grid for this project)

### Generally available datasets

Meta [High Resolution Population Density Maps](https://ai.meta.com/ai-for-good/docs/methodology-high-resolution-population-density-maps/) provide global gridded population estimates at ~30 m resolution.

### Data source used in the paper

| **Download** | [Nepal HRSL on HDX](https://data.humdata.org/dataset/nepal-high-resolution-population-density-maps-demographic-estimates) |
| --- | --- |
| **Original format** | GeoTIFF, band 1 = estimated population count per cell |
| **Original resolution** | ~30.9 m × 30.9 m (before 3×3 aggregation in prep) |

Clipped to the study boundary, aggregated **3×3** (~31 m → ~90 m), and used as the **base grid** for all other layers.

### Sample data provided

| **File (example)** | `data/input/population.tif` |
| --- | --- |
| **Format** | GeoTIFF, `float`, band 1 |
| **Values** | People per cell (≥ 0 inside study area) |

---

## 2. Study area boundary (optional but used in prep)

Define **your own** study extent as **one GeoJSON polygon** (single feature or one dissolved multipolygon). Use it when preparing input data to clip rasters and filter vector layers so cells outside the study are `NaN` and features outside the boundary are dropped.

### Data source used in the paper

| **Download** | [Administrative shapefiles of Nepal (MOFALD)](https://data.humdata.org/dataset/admin-shapefiles-of-nepal-mofald) |
| --- | --- |
| **Source** | District boundaries from the MOFALD shapefiles; study extent = outer boundary of the 14 districts most affected by the 2015 Gorkha earthquake (subset of the 31 HRRP earthquake-affected districts) |

### Sample data provided

| **File (example)** | `data/input/boundary.geojson` |
| --- | --- |
| **Format** | GeoJSON, one polygon (or dissolved outer ring) |
| **Content** | Study-area mask in geographic coordinates (reproject to match your base raster CRS when clipping) |

---

## 3. Land cover

### Generally available datasets

Two examples of globally available categorical land-cover rasters are [ESA WorldCover](https://esa-worldcover.org/en) ([Earth Engine](https://developers.google.com/earth-engine/datasets/catalog/ESA_WorldCover_v200)) and [MODIS Land Cover (MCD12Q1)](https://www.earthdata.nasa.gov/data/catalog/lpcloud-mcd12q1-061) ([Earth Engine](https://developers.google.com/earth-engine/datasets/catalog/MODIS_061_MCD12Q1)).

### Data source used in the paper

| **Product** | ICIMOD, *Land Cover of Nepal 2010* |
| --- | --- |
| **Download** | https://rds.icimod.org/Home/DataDetail?metadataId=9224&searchlist=True |
| **Original format** | GeoTIFF, categorical integer classes |

**Note:** The paper uses this Nepal-specific ICIMOD product rather than a generally available global land-cover dataset, for better accuracy in the study area.

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

### Sample data provided

| **File (example)** | `data/input/landcover.tif` |
| --- | --- |
| **Format** | GeoTIFF, band 1 |
| **Values** | Integer class codes **1–8** inside study area |

---

## 4. Elevation

### Generally available datasets

[USGS SRTM](https://www.usgs.gov/centers/eros/science/usgs-eros-archive-digital-elevation-shuttle-radar-topography-mission-srtm-1) (~30 m) provides global elevation and is available via [Google Earth Engine](https://developers.google.com/earth-engine/datasets/catalog/USGS_SRTMGL1_003).

### Data source used in the paper

| **Access** | Exported from Google Earth Engine |
| --- | --- |
| **Original format** | GeoTIFF, band 1 = elevation (**meters**) |
| **Original resolution** | ~30 m (SRTM) |

### Sample data provided

| **File (example)** | `data/input/elevation.tif` |
| --- | --- |
| **Format** | GeoTIFF, `float`, band 1 |
| **Values** | Elevation (m) |

---

## 5. Slope

### Data source used in the paper

Slope was **derived from the elevation layer** (§4); no separate source product was used.

### Sample data provided

| **File (example)** | `data/input/slope.tif` |
| --- | --- |
| **Format** | GeoTIFF, `float`, band 1 |
| **Values** | Terrain slope in **percent (%)**: **0** (flat) to **90** (very steep) |

---

## 6. Surface water

### Generally available datasets

Surface water polygons and waterways can be extracted from [OpenStreetMap](https://www.openstreetmap.org/about), e.g. via [Geofabrik](https://download.geofabrik.de/) regional extracts.

### Data source used in the paper

| **Download** | https://download.geofabrik.de/asia/nepal.html |
| --- | --- |
| **Original files** | `gis_osm_water_a_free_1.shp` (water polygons), `gis_osm_waterways_free_1.shp` (waterway lines) |
| **Original format** | Esri shapefile |

Water polygons and waterways were rasterized and **merged** into one layer for the study area.

### Sample data provided

| **File (example)** | `data/input/water_merged.tif` |
| --- | --- |
| **Format** | GeoTIFF, band 1 |
| **Values** | **`0`** = land, **`1`** = water (not walkable) |

---

## 7. Roads

### Generally available datasets

Road networks are commonly sourced from [OpenStreetMap](https://www.openstreetmap.org/about), with regional shapefile extracts from [Geofabrik](https://download.geofabrik.de/).

### Data source used in the paper

| **Download** | https://download.geofabrik.de/asia/nepal.html |
| --- | --- |
| **Original file** | `data/raw/nepal_osm_roads/gis_osm_roads_free_1.shp` |
| **Original format** | Esri shapefile; OSM attribute **`fclass`** (road type) |

| Class | Typical OSM types (summary) | Corresponding Nepal designation |
|-------|-----------------------------|--------------------------------|
| 1 | trunk, trunk_link | Strategic Road Network (SRN) |
| 2 | primary, primary_link, secondary, secondary_link | District Road Core Network (DRCN) |
| 3 | tertiary, residential, service, unclassified, track grades 1–3 | Strategic Urban Road (SUR) and unpaved roads |
| 4 | track, path, footway, steps, etc. | Village Roads (VR) and Paths |

**Road classes in this study:** Classes **1–4** group OSM `fclass` values to match **Nepal road designations** (SRN, DRCN, SUR, VR). Each class uses a different **road class × slope → speed** lookup in `funcs/drivespeed_by_roadslope.py` (`speed_lookup` in `Func_DriveSpeed_by_Road_Slope`). For other regions, define your own OSM groupings and edit that lookup table to match local road types and speed assumptions.

### Sample data provided

| **File (example)** | `data/input/roads.tif` |
| --- | --- |
| **Format** | GeoTIFF, band 1 |
| **Values** | Integer class codes **`0`** = no road, **`1–4`** = road class from OSM `fclass` grouping |

---

## 8. Hazard impact mask (landslides in this study)

**General:** This layer marks **hazard-affected cells** for the post-event scenario. Elsewhere it can be any hazard (flood, fire, earthquake damage, etc.). Provide a raster on your base grid where **`1`** = affected (blocked or impassable in the hazard run), **`0`** = not affected; the hazard type does not matter, only the mask.

### Data source used in the paper

| **Original source** | USGS / Roback et al., landslides from 2015 Gorkha earthquake |
| --- | --- |
| **Download** | https://www.sciencebase.gov/catalog/item/582c74fbe4b04d580bd377e8 |
| **Original file (example)** | `Full20170209/Full20170209.shp` |
| **Original format** | Esri shapefile, landslide polygons |

### Sample data provided

| **File (example)** | `data/input/landslide.tif` |
| --- | --- |
| **Format** | GeoTIFF, band 1 |
| **Values** | **`1`** = landslide-affected cell, **`0`** = not landslide |

---

## 9. Destinations (for access-time calculation)

**General:** A raster marking **where your destinations are**. Use any facility set you care about (hospitals, clinics, schools, markets, etc.) from any source—points are rasterized to cells on the base grid. **`1`** = destination cell, **`0`** = not a destination (inside study). The model treats any value **> 0** as a destination for shortest-path routing.

### Generally available datasets

Healthcare and other facility locations can be compiled from [OpenStreetMap](https://www.openstreetmap.org/about). For many countries, [Humanitarian OpenStreetMap Team (HOT)](https://www.hotosm.org/) publishes curated healthcare datasets on HDX—for Nepal, see [HOT OSM Nepal health facilities](https://data.humdata.org/dataset/hotosm_npl_health_facilities).

### Data source used in the paper

| **Destinations used** | Hospitals |
| --- | --- |
| **Original source** | NDRRMA healthcare facility list |
| **Original format** | GeoJSON points |

**Note:** Nepal-specific data obtained directly from NDRRMA; it cannot be redistributed with this repository. Prepare your own destination layer from a public source (§ Generally available datasets) or local authorities.

### Sample data provided

| **File (example)** | `data/input/destination_osm.tif` |
| --- | --- |
| **Format** | GeoTIFF, band 1, on **base grid** |
| **Values** | **`1`** at each hospital cell; **`0`** elsewhere |

**Note:** Because of data-distribution restrictions on the NDRRMA list, the sample destination file in this repository is prepared from [HOT OSM Nepal health facilities](https://data.humdata.org/dataset/hotosm_npl_health_facilities) and is **not exactly the same** as the destination set used in the paper.
