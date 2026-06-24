# Seeing Beyond the Road: Modeling Post-Disaster Access in Rural and Complex Settings

**Yue Zeng**, **Seth Guikema**, and **Sabine Loos**  
Department of Civil and Environmental Engineering, University of Michigan — Ann Arbor

This repository contains the modeling code and sample data used to estimate **combined on-road and off-road travel speeds** on a raster grid, build **travel networks**, and compute **shortest travel times to destinations** under baseline and **hazard-disrupted** conditions. It accompanies the paper above and is intended for public release so others can reproduce and adapt the workflow.

For input formats, sources, and preparation notes, see **[DATA_DESCRIPTION.md](DATA_DESCRIPTION.md)**.

---

## Folder structure

```text
nepal_landslide_modeling/
├── README.md                 # This file
├── DATA_DESCRIPTION.md       # Input data sources, formats, and prep notes
├── run_modeling.py           # Main pipeline script — edit USER INPUT, then run
├── run_modeling.slurm        # Example Slurm batch script (HPC)
├── requirements.txt          # Python dependencies
├── funcs/                    # Modeling and plotting functions
└── data/
    ├── input/                # Sample prepared inputs (Nepal case study)
    ├── process/              # Intermediate outputs (created when you run)
    └── result/               # Final outputs (created when you run)
```

---

## Requirements

- Python 3.10+ recommended  
- Dependencies in `requirements.txt`: `numpy`, `rasterio`, `geopandas`, `matplotlib`, `networkx`, `tqdm`, `shapely`, `seaborn`

```bash
cd nepal_landslide_modeling
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

On HPC systems (e.g. Great Lakes), load a Python module before creating the virtual environment. An example batch script is provided in `run_modeling.slurm`.

---

## How to run

1. Open **`run_modeling.py`** and edit the **USER INPUT** section if your paths or calibration parameters differ from the defaults.
2. Ensure all input GeoTIFFs share the same width, height, transform, and CRS (see [DATA_DESCRIPTION.md](DATA_DESCRIPTION.md)).
3. Run:

```bash
python run_modeling.py
```

Or submit on a cluster:

```bash
sbatch run_modeling.slurm
```

---

## What the pipeline does

Steps in **`run_modeling.py`** (in order):

### 1. Foot travel speed

Estimates off-road walking speed from land cover, then adjusts for water (impassable), roads, slope, elevation, and zigzag path length.

### 2. Vehicle travel speed

Estimates on-road driving speed from road class and slope, then applies a zigzag path-length correction.

### 3. Combine speeds (baseline and disrupted)

Combines foot and vehicle speeds per cell (effective speed = max of reduced foot and vehicle values) to build baseline and hazard-disrupted speed maps. Hazard-affected cells are blocked in the hazard-disrupted speed maps. 

Calibration parameters `foot_reduction_factor` and `vehicle_reduction_factor` are set in the USER INPUT section of `run_modeling.py`.

**Outputs:** `data/result/speedmap_normal.tif`, `data/result/speedmap_landslide.tif`

### 4. Travel networks

Builds 8-neighbor travel networks from each speed map and registers destination cells as path targets.

### 5. Access time

Computes shortest travel time (hours) from every cell to the nearest destination for baseline and disrupted conditions.

**Outputs:** `data/result/access_normal.tif`, `data/result/access_landslide.tif`, `data/result/access_landslide_map.png`, 

### 6. Post-processing

Derives access-time change and access-time CDF comparing baseline and disrupted conditions.

**Outputs:** `data/result/access_diff.tif`, `data/result/access_diff_map.png`, `data/result/access_cdf.jpg`

---

## Key results

After a successful run, main outputs in **`data/result/`**:

| File | Description |
|------|-------------|
| `speedmap_normal.tif` | Travel speed (km/h) — baseline |
| `speedmap_landslide.tif` | Travel speed (km/h) — landslide cells blocked |
| `access_normal.tif` | Travel time (h) to nearest destination — baseline |
| `access_landslide.tif` | Travel time (h) to nearest destination — post-disaster |
| `access_diff.tif` | Increase in travel time (h), landslide minus baseline |
| `access_landslide_map.png` | Map of post-disaster access time |
| `access_diff_map.png` | Map of access-time increase |
| `access_cdf.jpg` | Population-weighted access-time CDF (pre vs post) |

---

## Citation

This software is archived and published through DesignSafe.

Published Software DOI: https://doi.org/10.17603/ds2-z6jb-0f97

If you use this software, please cite:

**Zeng, Y., Guikema, S., & Loos, S. (2026). Modeling Disaster Impacts on Access to Essential Services in Rural Mountainous Regions (Version 1.1) [Computer software]. DesignSafe. https://doi.org/10.17603/ds2-z6jb-0f97**
---

## Contact

Questions: **majorz@umich.edu** (Yue "Major" Zeng)

---

## Copyright

© 2026 Yue Zeng, Seth Guikema, and Sabine Loos, University of Michigan.
