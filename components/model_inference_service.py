from fileinput import filename
import os
import numpy as np
import matplotlib.pyplot as plt
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import RBF, WhiteKernel
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from models.domain import AirQualityMeasurement
from config.constants import PUGLIA_BOUNDS, OUTPUT_DATAMAPS
from typing import List
from datetime import datetime
from utils.trees_utils import generate_tree_gaussians

def get_out_dir(output_dir=OUTPUT_DATAMAPS, region = "Puglia", overwrite=False):
    timestamp = datetime.now().isoformat()[:13].replace(":", "-") #* 16 for hrs
    return f'{output_dir}{region}/{timestamp}/' if not overwrite else f'{output_dir}{region}/' 


def extract_measurements_coords_and_values(
    measurements: List[AirQualityMeasurement], pollutant: str
):
    coords = []
    values = []
    for m in measurements:
        if m.pollutants is None:
            print("m.pollutants is none")
            continue
        value = getattr(m.pollutants, f"{pollutant}_value", None)
        if value is not None:
            coords.append([m.longitude, m.latitude])
            values.append(value)
        else:
            print(
                f"Valore per '{pollutant}' non trovato in {m.denomination} ({m.municipality})"
            )
    return np.array(coords), np.array(values)


def create_grid(bounds, resolution=50):
    """Crea griglia per interpolazione"""
    lon_range = np.linspace(bounds["west"], bounds["east"], resolution)
    lat_range = np.linspace(bounds["south"], bounds["north"], resolution)
    lon_grid, lat_grid = np.meshgrid(lon_range, lat_range)

    grid_coords = np.column_stack([lon_grid.ravel(), lat_grid.ravel()])

    return lon_grid, lat_grid, grid_coords


def run_kriging_on_measurements(
    coords,
    values,
    resolution=50,
    scale=0.6,
    lower_scale_bound=0.1,
    upper_scale_bound=0.4,
    noise=0.2,
    bounds=PUGLIA_BOUNDS,
    simulation_datas=None,
    pollutant = None
):
    bounds = bounds or PUGLIA_BOUNDS

    lon_grid, lat_grid, grid_coords = create_grid(bounds, resolution=resolution)

    kernel = RBF(length_scale=scale, length_scale_bounds=(lower_scale_bound, upper_scale_bound)) + WhiteKernel(noise_level=noise)
    gp = GaussianProcessRegressor(kernel=kernel, alpha=1e-6, normalize_y=True)
    gp.fit(coords, values)

    predictions, std = gp.predict(grid_coords, return_std=True)
    pred_grid = predictions.reshape(lon_grid.shape)
    std_grid = std.reshape(lon_grid.shape)

    if simulation_datas is not None:
        sim_coords, sim_values = simulation_datas

        oscillation = np.random.normal(loc=0, scale=0.01, size=len(sim_coords))
        sim_values = sim_values + oscillation

        kernel_sim = RBF(length_scale=0.008, length_scale_bounds=(0.005, 0.02)) + WhiteKernel(noise_level=0.005)
        gp_sim = GaussianProcessRegressor(kernel=kernel_sim, alpha=1e-6, normalize_y=True)
        gp_sim.fit(sim_coords, sim_values)
        sim_pred_grid, _ = gp_sim.predict(grid_coords, return_std=True)
        sim_pred_grid = sim_pred_grid.reshape(lon_grid.shape)

        # Min e Max originali
        min_val = np.min(sim_pred_grid)
        max_val = np.max(sim_pred_grid)

        # Stretch con min a 0 e max invariato
        sim_pred_grid = (sim_pred_grid - min_val) / (max_val - min_val) * max_val


        print("Genero Immagine ==============================================")
        generate_kriging_map_image(
            lon_grid, lat_grid, sim_pred_grid, 
            sim_coords, sim_values, pollutant=pollutant, 
            bounds=bounds, region="TreesModel", 
            extra_info=True
        )

        pred_grid = np.maximum(pred_grid - sim_pred_grid, 0)




    return lon_grid, lat_grid, pred_grid, std_grid, grid_coords



def generate_kriging_map_image(
    lon_grid, lat_grid, pred_grid, coords, values, pollutant, bounds = PUGLIA_BOUNDS, region = None, 
    extra_info = False, sim_coords = None, zip_archive = False
):
    region = region or "Puglia"
    bounds = bounds or PUGLIA_BOUNDS
    os.makedirs(get_out_dir(region=region), exist_ok=True)

    plt.figure(figsize=(12, 10))
    ax = plt.axes(projection=ccrs.PlateCarree())

    ax.set_extent(
        [
            bounds["west"],
            bounds["east"],
            bounds["south"],
            bounds["north"],
        ]
    )

    ax.add_feature(cfeature.COASTLINE, linewidth=0.5)
    
    if extra_info:
        ax.add_feature(cfeature.BORDERS, linewidth=0.5)
        ax.add_feature(cfeature.LAND, alpha=0.2, color="lightgray")
        ax.add_feature(cfeature.OCEAN, alpha=0.2, color="lightblue")

    contour = ax.contourf(
        lon_grid,
        lat_grid,
        pred_grid,
        levels=20,
        cmap="viridis",
        alpha=1,
        transform=ccrs.PlateCarree(),
    )

    if extra_info:

        ax.scatter(
            coords[:, 0], coords[:, 1], c=values,
            cmap="viridis", s=50, edgecolors="black",
            transform=ccrs.PlateCarree(), zorder=5
        )
        
        # Punti simulati
        if sim_coords is not None and len(sim_coords) > 0:
            ax.scatter(
                sim_coords[:, 0], sim_coords[:, 1], c="red",
                marker="^", s=60, edgecolors="black",
                transform=ccrs.PlateCarree(), zorder=6, label="Alberi"
            )
            ax.legend()

        ax.scatter(
            coords[:, 0],
            coords[:, 1],
            c=values,
            cmap="viridis",
            s=50,
            edgecolors="black",
            transform=ccrs.PlateCarree(),
            zorder=5,
        )

        cbar = plt.colorbar(contour, ax=ax, shrink=0.7, pad=0.03)
        cbar.set_label(f"{pollutant.upper()} (μg/m³)", rotation=270, labelpad=15)

        ax.gridlines(draw_labels=True)

    filename = os.path.abspath(
        os.path.join(get_out_dir(region=region, overwrite=zip_archive), f"kriging_map_{pollutant.lower()}.png")
    ) 

    plt.axis("off")
    plt.savefig(filename, dpi=300, bbox_inches="tight", pad_inches=0, transparent= not extra_info)
    plt.close()
    return filename
