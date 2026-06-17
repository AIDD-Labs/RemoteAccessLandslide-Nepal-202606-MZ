#!/usr/bin/env python3
"""
Modeling code for the Nepal landslide accessibility project
([Paper title — add citation here]).

Authored by Yue Major Zeng, University of Michigan.

Before running:
  1. Edit the USER INPUT section below (input paths and parameters).
  2. Install dependencies: pip install -r requirements.txt
  3. Run: python run_modeling.py

See README.md and DATA_DESCRIPTION.md for folder layout and input data specs.
"""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from funcs.destination_nodes_from_raster import destination_raster_to_pickle
from funcs.drivespeed_by_roadslope import Func_DriveSpeed_by_Road_Slope
from funcs.speed_combine_footvehicle import Func_Combine_Speed_FootVehicle_Reduced
from funcs.speed_combine_landslide import Func_Combine_Speed_Landslide
from funcs.speed_modify_byzigzag import Func_Modify_Speed_by_Zigzag
from funcs.travelnetwork_construct import Func_Construct_Travel_Network
from funcs.travelnetwork_shortest_path import Func_Shortest_Path_To_Target
from funcs.walkspeed_bylandcover import Func_WalkSpeed_by_LandCover
from funcs.walkspeed_modify_byelevation import Func_Modify_WalkSpeed_by_Elevation
from funcs.walkspeed_modify_byroad import Func_Modify_WalkSpeed_by_Roads
from funcs.walkspeed_modify_byslope import Func_Modify_WalkSpeed_by_Slope
from funcs.walkspeed_modify_bywater import Func_Modify_WalkSpeed_by_Water
from funcs.travelnetwork_access_diff import Func_Access_Diff
from funcs.population_access import Func_Access_Time_Cdf_Pre_Post
from funcs.plot_tiff_access_time import (
    Func_Plot_Access_Diff_wHazard_Crop,
    Func_Plot_Access_Time_wHazard_Crop,
)


# =============================================================================
# USER INPUT — set paths and parameters here before running
# =============================================================================

# --- Input rasters (must share the same base grid) ---
landcover_raster = ROOT / "data/input/landcover.tif"
water_raster = ROOT / "data/input/water_merged.tif"
roads_raster = ROOT / "data/input/roads.tif"
slope_raster = ROOT / "data/input/slope.tif"
elevation_raster = ROOT / "data/input/elevation.tif"
landslide_raster = ROOT / "data/input/landslide.tif"
destination_raster = ROOT / "data/input/destination_osm.tif"
population_raster = ROOT / "data/input/population.tif"
boundary_geojson = ROOT / "data/input/boundary.geojson"

# --- Speed combination parameters ---
foot_reduction_factor = 1.0
vehicle_reduction_factor = 0.32

# --- Output folders ---
process_dir = ROOT / "data/process"
result_dir = ROOT / "data/result"


# =============================================================================
# PIPELINE — do not edit unless you know what you are changing
# =============================================================================


def run_modeling(
    landcover_raster,
    water_raster,
    roads_raster,
    slope_raster,
    elevation_raster,
    landslide_raster,
    destination_raster,
    population_raster,
    boundary_geojson,
    process_dir,
    result_dir,
    foot_reduction_factor=1.0,
    vehicle_reduction_factor=0.32,
):
    process_dir = Path(process_dir)
    result_dir = Path(result_dir)
    process_dir.mkdir(parents=True, exist_ok=True)
    result_dir.mkdir(parents=True, exist_ok=True)

    # --- Walk speed pipeline ---
    ws0 = process_dir / "walkspeed_0_landcover.tif"
    ws1 = process_dir / "walkspeed_1_water.tif"
    ws2 = process_dir / "walkspeed_2_footpath.tif"
    ws3 = process_dir / "walkspeed_3_slope.tif"
    ws4 = process_dir / "walkspeed_4_elevation.tif"
    ws5 = process_dir / "walkspeed_5_zigzag.tif"

    # Land cover -> base walk speed (km/h)
    Func_WalkSpeed_by_LandCover(landcover_raster, ws0)
    print(f"Base walk speed raster determined by land cover saved to {ws0}")

    # Set water cells to impassable
    Func_Modify_WalkSpeed_by_Water(ws0, water_raster, ws1)
    print(f"Walk speed modified by water saved to {ws1}")

    # Add walking on road speeds
    Func_Modify_WalkSpeed_by_Roads(ws1, roads_raster, ws2, footpath_speed=5)
    print(f"Walk speed modified by roads saved to {ws2}")
    
    # Reduce walk speed by slope
    Func_Modify_WalkSpeed_by_Slope(ws2, slope_raster, ws3)
    print(f"Walk speed modified by slope saved to {ws3}")

    # Reduce walk speed by elevation
    Func_Modify_WalkSpeed_by_Elevation(ws3, elevation_raster, ws4)
    print(f"Walk speed modified by elevation saved to {ws4}")

    # Zigzag path-length correction on foot speeds
    Func_Modify_Speed_by_Zigzag(ws4, slope_raster, ws5)
    print(f"Walk speed modified by zigzag saved to {ws5}")

    # --- Vehicle speed pipeline ---
    ds0 = process_dir / "drivespeed_0_road_slope.tif"
    ds1 = process_dir / "drivespeed_1_zigzag.tif"

    # Road class raster + slope -> drive speed (km/h)
    Func_DriveSpeed_by_Road_Slope(roads_raster, slope_raster, ds0)
    print(f"Drive speed determined based on road type and slope saved to {ds0}")

    # Zigzag correction on drive speeds
    Func_Modify_Speed_by_Zigzag(ds0, slope_raster, ds1)
    print(f"Drive speed modified by zigzag saved to {ds1}")

    # --- Combine speeds ---
    speed_normal = result_dir / "speedmap_normal.tif"
    speed_landslide = result_dir / "speedmap_landslide.tif"

    # Combine foot and vehicle speeds (max of reduced values per cell)
    Func_Combine_Speed_FootVehicle_Reduced(ws5, ds1, speed_normal, foot_reduction_factor, vehicle_reduction_factor)
    print(f"Normal condition speed raster by combining foot and vehicle speeds saved to {speed_normal}")

    # Block landslide cells in the disrupted scenario speed map
    Func_Combine_Speed_Landslide(speed_normal, landslide_raster, speed_landslide)
    print(f"Landslide condition speed raster by blocking landslide cells saved to {speed_landslide}")

    # --- Build travel networks ---
    net_normal = process_dir / "travel_network_normal.pkl"
    net_landslide = process_dir / "travel_network_landslide.pkl"

    # Build travel network from baseline speed map
    Func_Construct_Travel_Network(speed_normal, net_normal)
    print(f"Travel network from baseline speed map saved to {net_normal}")

    # Build travel network from landslide speed map
    Func_Construct_Travel_Network(speed_landslide, net_landslide)
    print(f"Travel network from landslide speed map saved to {net_landslide}")

    # Destination raster -> pickle {(row, col): id} on the base grid
    destination_nodes_pkl = process_dir / "destination_nodes.pkl"
    destination_raster_to_pickle(destination_raster, destination_nodes_pkl)
    print(f"Destination nodes pickle saved to {destination_nodes_pkl}")

    # --- Calculate access time ---
    out_access_normal = result_dir / "access_normal.tif"
    out_access_landslide = result_dir / "access_landslide.tif"
    out_access_landslide_plot = result_dir / "access_landslide_map.png"
   
    # Shortest travel time to nearest destination (baseline network)
    Func_Shortest_Path_To_Target( net_normal, destination_nodes_pkl, speed_normal, out_access_normal)
    print(f"Shortest travel time to nearest destination (baseline network) saved to {out_access_normal}")

    # Shortest travel time to nearest destination (landslide network)
    Func_Shortest_Path_To_Target(net_landslide, destination_nodes_pkl, speed_landslide, out_access_landslide)
    print(f"Shortest travel time to nearest destination (landslide network) saved to {out_access_landslide}")

    # Plot post-landslide shortest travel time to nearest destination
    Func_Plot_Access_Time_wHazard_Crop(
        tiff_path=out_access_landslide,
        hazard_tiff_path=landslide_raster,
        water_tiff_path=water_raster,
        destination_tiff_path=destination_raster,
        study_boundary=boundary_geojson,
        colorbar_label="Access time [h]",
        title=None,
        save_path=out_access_landslide_plot,
        crop_lonlat=None,
    )

    # --- Calculate access time difference ---
    out_access_diff = result_dir / "access_diff.tif"
    out_access_diff_plot = result_dir / "access_diff_map.png"

    # Calculate access time difference
    Func_Access_Diff(out_access_normal, out_access_landslide, out_access_diff)
    print(f"Access time difference saved to {out_access_diff}")

    # Plot access time difference
    Func_Plot_Access_Diff_wHazard_Crop(
        access_diff_tiff_path=out_access_diff,
        hazard_tiff_path=landslide_raster,
        study_boundary=boundary_geojson,
        destination_tiff_path=destination_raster,
        colorbar_label="Access Time Increase [h]",
        title=None,
        save_path=out_access_diff_plot,
        crop_lonlat=None,
    )

    # --- Calculate cumulative distribution function of access time for the population ---
    out_access_cdf = result_dir / "access_cdf.jpg"

    Func_Access_Time_Cdf_Pre_Post(
        population_tiff_path=population_raster,
        access_pre_tiff_path=out_access_normal,
        access_post_tiff_path=out_access_landslide,
        title=None,
        save_plot_path=out_access_cdf,
        xlim=None,
        ylim=None,
    )
    print(f"Access time cumulative distribution function plot saved to {out_access_cdf}")

if __name__ == "__main__":
    run_modeling(
        landcover_raster=landcover_raster,
        water_raster=water_raster,
        roads_raster=roads_raster,
        slope_raster=slope_raster,
        elevation_raster=elevation_raster,
        landslide_raster=landslide_raster,
        destination_raster=destination_raster,
        population_raster=population_raster,
        boundary_geojson=boundary_geojson,
        process_dir=process_dir,
        result_dir=result_dir,
        foot_reduction_factor=foot_reduction_factor,
        vehicle_reduction_factor=vehicle_reduction_factor,
    )
