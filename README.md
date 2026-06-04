# Nepal Landslide Modeling Code

Code, sample input data, and data documentation for the Nepal landslide accessibility project associated with:

**[Paper title — add citation here]**

---

## Folder structure

```text
nepal_landslide_modeling/
├── README.md                 # This file
├── DATA_DESCRIPTION.md       # Input data sources, formats, and prep notes
├── run_modeling.py           # Main script — edit USER INPUT, then run
├── requirements.txt          # Python dependencies
├── funcs/                    # Modeling functions (speed, network, access time)
└── data/
    ├── input/                # Sample prepared inputs (Nepal case study)
    ├── process/              # Intermediate outputs (created when you run)
    └── result/               # Final outputs (created when you run)
```

- **`funcs/`** — step-by-step functions used by the pipeline (land-cover walk speed, road drive speed, network build, shortest path, etc.).
- **`run_modeling.py`** — defines the full pipeline in `run_modeling()` and runs it from the `if __name__ == "__main__"` block at the bottom.
- **`data/input/`** — sample rasters and boundary for the Nepal study, ready to reproduce paper results (see [DATA_DESCRIPTION.md](DATA_DESCRIPTION.md) for how each file was built).

Sample files in `data/input/`:

`population.tif`, `boundary.geojson`, `landcover.tif`, `elevation.tif`, `slope.tif`, `water_merged.tif`, `roads.tif`, `landslide.tif`, `destination.tif`

---

## How to run

1. Open **`run_modeling.py`** and edit the **USER INPUT** section (input paths and parameters).
2. Install dependencies and run:

```bash
cd nepal_landslide_modeling
pip install -r requirements.txt
python run_modeling.py
```

All input rasters must share the same base grid (width, height, transform, CRS). Details for each layer are in **[DATA_DESCRIPTION.md](DATA_DESCRIPTION.md)**.

---

## What the pipeline does

Steps in **`run_modeling.py`** (in order):

1. **Foot travel speed** — land cover → water mask → footpaths from roads → slope → elevation → zigzag correction (`data/process/walkspeed_5_zigzag.tif`).
2. **Vehicle travel speed** — road class + slope → zigzag correction (`data/process/drivespeed_1_zigzag.tif`).
3. **Combine speeds** — max of foot and vehicle speeds → baseline speed map; then apply landslide mask for disrupted scenario (`data/result/speedmap_normal.tif`, `data/result/speedmap_landslide.tif`).
4. **Travel networks** — 8-neighbor graphs from each speed map (`data/process/travel_network_*.pkl`).
5. **Access time** — shortest travel time to nearest destination, baseline vs. landslide (`data/result/access_normal.tif`, `data/result/access_landslide.tif`).
6. **Post-processing** — maps, CDFs, population summaries, and other paper figures *(not included in this repository yet)*.

---

## Key results

After a successful run, the main outputs are in **`data/result/`**:

| File | Description |
|------|-------------|
| `speedmap_normal.tif` | Travel speed (km/h) before landslide disruption |
| `speedmap_landslide.tif` | Travel speed (km/h) with landslide-affected cells blocked |
| `access_normal.tif` | Travel time (hours) to nearest destination — baseline |
| `access_landslide.tif` | Travel time (hours) to nearest destination — landslide scenario |

## Other result visualizations

*(Post-processing and plotting code for maps, CDFs, and population summaries is not included in this repository yet.)*

---

## Contact

Questions: **majorz@umich.edu**

## Copyright

© 2026 Yue Major Zeng, University of Michigan.
