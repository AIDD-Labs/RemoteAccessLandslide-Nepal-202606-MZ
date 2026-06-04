# Nepal Landslide Modeling Package

Self-contained package for the **travel-speed → network → access-time** workflow. Data preparation is assumed complete; place prepared inputs in `data/input/` and run one script.

## Folder structure

```text
nepal_landslide_modeling/
├── README.md
├── run_modeling.py
├── requirements.txt
├── funcs/
└── data/
    ├── input/       # Prepared inputs
    ├── process/     # Intermediate rasters and network pickles
    └── result/      # Final speed maps and access-time rasters
```

## Quick start

1. Open `run_modeling.py` and edit the **USER INPUT** section (paths, destination pickle, parameters).
2. Run:

```bash
cd nepal_landslide_modeling
pip install -r requirements.txt
python run_modeling.py
```

Example USER INPUT block:

```python
landcover_map = ROOT / "data/input/landcover.tif"
water_map = ROOT / "data/input/water_merged.tif"
roads_geojson = ROOT / "data/input/roads.geojson"
slope_map = ROOT / "data/input/slope.tif"
elevation_map = ROOT / "data/input/elevation.tif"
landslide_map = ROOT / "data/input/landslide.tif"
destination_raster = ROOT / "data/input/destination_raster.tif"
foot_reduction_factor = 1.0
vehicle_reduction_factor = 0.32
```

## Pipeline overview

| Stage | What it does | Main output |
|-------|----------------|-------------|
| Foot speed | Land cover, water, road vector footpaths, slope, elevation, zigzag | `data/process/walkspeed_5_zigzag.tif` |
| Vehicle speed | Road class, slope, zigzag | `data/process/drivespeed_1_zigzag.tif` |
| Combine | Max of foot/vehicle speeds; then landslide mask | `data/result/speedmap_normal.tif`, `speedmap_landslide.tif` |
| Network | 8-neighbor graph with travel-time edge weights | `data/process/travel_network_*.pkl` |
| Access time | Shortest path to nearest destination node | `data/result/access_normal.tif`, `access_landslide.tif` |

## Required prepared inputs (`data/input/`)

**All rasters must share the same base grid** (identical width, height, transform, and CRS). Vector layers must be reprojectable to that grid.

### Raster inputs

| File | Band 1 content | Notes |
|------|----------------|-------|
| `landcover.tif` | Integer classes `1–8` | Land-cover codes for walk-speed lookup |
| `water_merged.tif` | `0` land, `1` water, `NaN` outside | Water mask |
| `roads.geojson` | `geometry` (lines), `class` (`1–4`) | Road vector; rasterized inside the pipeline to `data/process/roads.tif` for vehicle speeds and used directly for footpath speeds |
| `slope.tif` | Slope in **percent** (`%`) | Foot, vehicle, and zigzag steps |
| `elevation.tif` | Elevation in **meters** | Foot-speed adjustment |
| `landslide.tif` | `0` / `1` / `NaN` | `1` = blocked cell in landslide scenario |

### Destination raster

| File | Format | Notes |
|------|--------|-------|
| `destination_raster.tif` | GeoTIFF band 1 | Cells with value **> 0** are destinations (same base grid as other rasters). Converted to a node pickle inside `run_modeling.py`. |

Example from this project: `data/process/MFD_healthcare_hospital_nodes_collection.tif` (one cell per destination, values often `1`).

Optional: `boundary.geojson` for map context only (not used in computation).

## Sync with GitHub

This folder is meant to be its **own Git repository** (not the parent `Nepal_Landslide_JupyterCode_Clean` project). On GitHub, the repo root should show `README.md`, `run_modeling.py`, `funcs/`, etc.—the same layout as this directory.

### One-time setup

1. **Open this folder in Cursor/VS Code**  
   `File → Open Folder…` → choose `nepal_landslide_modeling` (so Source Control only tracks this package).

2. **Initialize Git** (if not done yet):
   ```bash
   cd "/Users/majorz/Documents/Michigan Records/Research/Nepal Landslide/Nepal_Landslide_JupyterCode_Clean/nepal_landslide_modeling"
   git init
   git add .
   git commit -m "Initial commit: Nepal landslide modeling package"
   ```

3. **Create an empty repo on GitHub**  
   https://github.com/new → name it (e.g. `nepal-landslide-modeling`) → **do not** add a README, `.gitignore`, or license (this folder already has them).

4. **Connect and push** (replace `YOUR_USER` and `YOUR_REPO`):
   ```bash
   git branch -M main
   git remote add origin https://github.com/YOUR_USER/YOUR_REPO.git
   git push -u origin main
   ```

### Day-to-day sync

| Action | Command |
|--------|---------|
| Send local changes to GitHub | `git add -A && git commit -m "Describe change" && git push` |
| Get changes from GitHub (another machine) | `git pull` |

In Cursor: **Source Control** panel → stage → commit message → **Commit** → **Sync/Push**.

### Data files and symlinks

Large rasters are **not** committed (see `.gitignore`). After cloning on a new machine, copy prepared inputs into `data/input/` using **[DATA_DESCRIPTION.md](DATA_DESCRIPTION.md)**. Local symlinks to files outside this folder are fine for your machine but are not pushed to GitHub.

## Dependencies

See `requirements.txt`: `numpy`, `rasterio`, `geopandas`, `networkx`, `tqdm`, `shapely`.
