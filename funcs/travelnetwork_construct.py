import math
import pickle

import numpy as np
import networkx as nx
import rasterio
from rasterio.transform import xy
from tqdm import tqdm


def Func_Construct_Travel_Network(raster_path, output_pickle_path):
    """
    Creates a NetworkX weighted graph from a raster of travel speeds and saves it as a pickle.
    Links are created only if both cells have a speed > 0, with weight based on distance and average speed.

    Prints a list of all isolated cells at the end.

    Parameters:
        raster_path (str): Path to the travel speed raster file (GeoTIFF).
        output_pickle_path (str): Path to save the resulting NetworkX graph (pickle).
    """
    # Load the raster
    with rasterio.open(raster_path) as src:
        raster_data = src.read(1)
        transform = src.transform
        res = src.res
        rows, cols = raster_data.shape

        # Initialize the graph
        G = nx.Graph()

        # List to store isolated cells
        isolated_cells = []

        # Iterate through all cells
        for row in tqdm(range(rows), desc="Processing", disable=False):
            for col in range(cols):
                current_speed = raster_data[row, col]
                if current_speed > 0:  # Only process cells with non-zero speed
                    # Find the centroid of the current cell
                    current_lon, current_lat = xy(transform, col, row, offset="center")

                    # Define neighboring positions and directions
                    neighbors = [
                        (row - 1, col),  # Up
                        (row + 1, col),  # Down
                        (row, col - 1),  # Left
                        (row, col + 1),  # Right
                        (row - 1, col - 1),  # Up-left
                        (row + 1, col - 1),  # Down-left
                        (row - 1, col + 1),  # Up-right
                        (row + 1, col + 1),  # Down-right
                    ]

                    # Check if the cell has any valid neighbors
                    has_neighbors = False

                    for nbr_row, nbr_col in neighbors:
                        # Check bounds for neighbors
                        if 0 <= nbr_row < rows and 0 <= nbr_col < cols:
                            neighbor_speed = raster_data[nbr_row, nbr_col]
                            if neighbor_speed > 0:  # Only create a link if neighbor speed > 0
                                has_neighbors = True
                                # Find the centroid of the neighbor cell
                                nbr_lon, nbr_lat = xy(transform, nbr_col, nbr_row, offset="center")

                                # Calculate distance between the two centroids in km
                                lat_dis = (nbr_lat - current_lat) * 111.32
                                lon_dis = (nbr_lon - current_lon) * 111.32 * math.cos(math.radians((nbr_lat + current_lat) / 2))
                                distance = math.sqrt(lat_dis**2 + lon_dis**2)

                                # Calculate travel time (weight) based on average speed
                                average_speed = (current_speed + neighbor_speed) / 2  # km/h
                                weight = distance / average_speed  # Travel time in hours

                                # Add the edge with calculated weight
                                G.add_edge((row, col), (nbr_row, nbr_col), weight=weight)

                    # If no neighbors were found, add this cell to the isolated list
                    if not has_neighbors:
                        isolated_cells.append((row, col))

        # Save the graph as a pickle
        with open(output_pickle_path, "wb") as f:
            pickle.dump(G, f)

    # Print all isolated cells at the end
    if isolated_cells:
        # Report isolation stats
        total_valid_cells = np.sum(raster_data > 0)
        num_isolated = len(isolated_cells)
        print(f"{num_isolated} / {total_valid_cells} cells are isolated")
    else:
        print("No isolated cells found.")

    print(f"Graph saved to {output_pickle_path}")
