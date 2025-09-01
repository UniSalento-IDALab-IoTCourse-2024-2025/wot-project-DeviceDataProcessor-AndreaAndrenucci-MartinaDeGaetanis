import numpy as np

def generate_tree_gaussians(grid_coords, sim_coords, sigma=0.01, peak=5, offset=0):
    """
    Genera una mappa con gaussiane centrate sugli alberi.
    - sigma: larghezza della gaussiana (in gradi lat/lon)
    - peak: valore massimo della gaussiana
    """
    gaussians = np.zeros(len(grid_coords))
    for tree in sim_coords:
        dist_sq = (grid_coords[:, 0] - tree[0])**2 + (grid_coords[:, 1] - tree[1])**2
        gaussians += (peak * np.exp(-dist_sq / (2 * sigma**2)))-offset 
    return gaussians
