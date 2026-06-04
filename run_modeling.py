#!/usr/bin/env python3
"""
End-to-end modeling pipeline: travel speed (foot + vehicle), network construction,
and access-time calculation to a user-defined destination set.

Edit the USER INPUT section below, then run this file.
"""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from funcs.destination_nodes_from_raster import destination_raster_to_pickle
from funcs.drivespeed_by_roadslope import Func_DriveSpeed_by_Road_Slope
from funcs.rasterize_road import Func_Rasterize_Roads
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


# =============================================================================
# USER INPUT — set paths and parameters here before running
# =============================================================================

# --- Input rasters / vectors (must share the same base grid) ---
landcover_map = ROOT / "data/input/landcover.tif"
water_map = ROOT / "data/input/water_merged.tif"
roads_geojson = ROOT / "data/input/roads.geojson"
slope_map = ROOT / "data/input/slope.tif"
elevation_map = ROOT / "data/input/elevation.tif"
landslide_map = ROOT / "data/input/landslide.tif"

# --- Destination raster (cells with value > 0 are targets; same base grid as other rasters) ---
destination_raster = ROOT / "data/input/destination_raster.tif"

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
    landcover_map,
    water_map,
    roads_geojson,
    slope_map,
    elevation_map,
    landslide_map,
    destination_raster,
    process_dir,
    result_dir,
    foot_reduction_factor=1.0,
    vehicle_reduction_factor=0.32,
):
    process_dir = Path(process_dir)
    result_dir = Path(result_dir)
    process_dir.mkdir(parents=True, exist_ok=True)
    result_dir.mkdir(parents=True, exist_ok=True)

    roads_raster = process_dir / "roads.tif"

    # Road vector -> class raster on the base grid (for vehicle speeds)
    Func_Rasterize_Roads(roads_geojson, landcover_map, roads_raster)

    ws0 = process_dir / "walkspeed_0_landcover.tif"
    ws1 = process_dir / "walkspeed_1_water.tif"
    ws2 = process_dir / "walkspeed_2_footpath.tif"
    ws3 = process_dir / "walkspeed_3_slope.tif"
    ws4 = process_dir / "walkspeed_4_elevation.tif"
    ws5 = process_dir / "walkspeed_5_zigzag.tif"

    # Land cover -> base walk speed (km/h)
    Func_WalkSpeed_by_LandCover(landcover_map, ws0)

    # Set water cells to impassable (speed 0)
    Func_Modify_WalkSpeed_by_Water(ws0, water_map, ws1)

    # Add footpath speeds from road linework (vector)
    Func_Modify_WalkSpeed_by_Roads(ws1, roads_geojson, ws2)

    # Reduce walk speed by slope
    Func_Modify_WalkSpeed_by_Slope(ws2, slope_map, ws3)

    # Reduce walk speed by elevation
    Func_Modify_WalkSpeed_by_Elevation(ws3, elevation_map, ws4)

    # Zigzag path-length correction on foot speeds
    Func_Modify_Speed_by_Zigzag(ws4, slope_map, ws5)

    ds0 = process_dir / "drivespeed_0_road_slope.tif"
    ds1 = process_dir / "drivespeed_1_zigzag.tif"

    # Road class raster + slope -> drive speed (km/h)
    Func_DriveSpeed_by_Road_Slope(roads_raster, slope_map, ds0)

    # Zigzag correction on drive speeds
    Func_Modify_Speed_by_Zigzag(ds0, slope_map, ds1)

    speed_normal = result_dir / "speedmap_normal.tif"
    speed_landslide = result_dir / "speedmap_landslide.tif"

    # Combine foot and vehicle speeds (max of reduced values per cell)
    Func_Combine_Speed_FootVehicle_Reduced(
        ws5,
        ds1,
        speed_normal,
        foot_reduction_factor,
        vehicle_reduction_factor,
    )

    # Block landslide cells in the disrupted scenario speed map
    Func_Combine_Speed_Landslide(speed_normal, landslide_map, speed_landslide)

    net_normal = process_dir / "travel_network_normal.pkl"
    net_landslide = process_dir / "travel_network_landslide.pkl"

    # Build travel network from baseline speed map
    Func_Construct_Travel_Network(speed_normal, net_normal)

    # Build travel network from landslide speed map
    Func_Construct_Travel_Network(speed_landslide, net_landslide)

    out_access_normal = result_dir / "access_normal.tif"
    out_access_landslide = result_dir / "access_landslide.tif"

    # Destination raster -> pickle {(row, col): id} on the base grid
    destination_nodes_pkl = process_dir / "destination_nodes.pkl"
    destination_raster_to_pickle(
        destination_raster,
        destination_nodes_pkl,
        reference_raster_path=landcover_map,
    )

    # Shortest travel time to nearest destination (baseline network)
    Func_Shortest_Path_To_Target(
        net_normal, destination_nodes_pkl, speed_normal, out_access_normal
    )

    # Shortest travel time to nearest destination (landslide network)
    Func_Shortest_Path_To_Target(
        net_landslide, destination_nodes_pkl, speed_landslide, out_access_landslide
    )


if __name__ == "__main__":
    run_modeling(
        landcover_map=landcover_map,
        water_map=water_map,
        roads_geojson=roads_geojson,
        slope_map=slope_map,
        elevation_map=elevation_map,
        landslide_map=landslide_map,
        destination_raster=destination_raster,
        process_dir=process_dir,
        result_dir=result_dir,
        foot_reduction_factor=foot_reduction_factor,
        vehicle_reduction_factor=vehicle_reduction_factor,
    )
