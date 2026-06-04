import numpy as np
import rasterio
import warnings
import networkx as nx
import pickle
from tqdm import tqdm

def Func_Shortest_Path_To_Target(graph_pickle_path, target_pickle_path, reference_raster_path, output_raster_path):
    """
    Computes the shortest cost distances from all nodes in a graph to multiple target nodes
    and outputs a combined raster with the minimum distance values.

    For each cell:
    - Output NaN if the reference raster cell is NaN.
    - Output inf if the reference raster has a value but the cell is not part of the graph.
    - Output inf for nodes in the graph that are unreachable.
    - Output the cost distance for nodes in the graph that are reachable.
    - Output 0 for the target node.

    Parameters:
        graph_pickle_path (str): Path to the saved NetworkX graph in pickle form.
        target_pickle_path (str): Path to the saved target node list in pickle form.
        reference_raster_path (str): Path to the reference raster (GeoTIFF).
        output_raster_path (str): Path to save the final output raster (GeoTIFF).

    Returns:
        None: Saves the final output raster to the specified path.
    """
    # Load the graph from pickle
    with open(graph_pickle_path, 'rb') as f:
        graph = pickle.load(f)

    # Load the target node list from pickle
    with open(target_pickle_path, 'rb') as f:
        target_node_list = pickle.load(f)

    # Load the reference raster
    with rasterio.open(reference_raster_path) as ref_src:
        ref_data = ref_src.read(1)  # Read the first band
        ref_meta = ref_src.meta.copy()

    # Initialize a list to store target-specific rasters
    all_target_rasters = []

    # Process each target node with a progress bar
    for target_node in tqdm(target_node_list, desc="Processing target nodes", disable=False):
        if target_node not in graph:
            warnings.warn(f"Target node {target_node} is not in the graph. Skipping...")
            continue

        # Compute shortest path lengths using Dijkstra's algorithm
        shortest_path_lengths = nx.single_source_dijkstra_path_length(graph, target_node, weight='weight')

        # Identify reachable and unreachable nodes
        all_nodes = set(graph.nodes)
        reachable_nodes = set(shortest_path_lengths.keys())
        unreachable_nodes = all_nodes - reachable_nodes

        # Create an output raster for this target
        target_raster = np.full_like(ref_data, np.nan, dtype=np.float32)

        # Populate the target raster
        for row in range(ref_data.shape[0]):
            for col in range(ref_data.shape[1]):
                cell = (row, col)

                if np.isnan(ref_data[row, col]):
                    # Reference raster cell is NaN
                    target_raster[row, col] = np.nan
                elif cell not in graph:
                    # Cell has a value in reference raster but is not part of the graph
                    target_raster[row, col] = np.inf
                elif cell in reachable_nodes:
                    # Cell is part of the graph and reachable
                    target_raster[row, col] = shortest_path_lengths[cell]
                elif cell in unreachable_nodes:
                    # Cell is part of the graph but unreachable
                    target_raster[row, col] = np.inf
                elif cell == target_node:
                    # Target cell
                    target_raster[row, col] = 0

        # Append the target raster to the list
        all_target_rasters.append(target_raster)

    if not all_target_rasters:
        raise ValueError("No valid target nodes were processed. Output raster cannot be generated.")

    # Combine all target rasters into a final raster using NumPy's min operation
    all_target_rasters_stack = np.stack(all_target_rasters, axis=0)
    final_raster = np.nanmin(all_target_rasters_stack, axis=0)

    # Save the final output raster
    ref_meta.update(dtype='float32', compress='lzw')
    with rasterio.open(output_raster_path, 'w', **ref_meta) as out_raster:
        out_raster.write(final_raster, 1)

    print(f"Combined shortest path raster saved to {output_raster_path}")
