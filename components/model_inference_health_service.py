from fileinput import filename
import os
import numpy as np
import matplotlib.pyplot as plt
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import RBF, WhiteKernel
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from models.domain import AirQualityMeasurement
from config.constants import PUGLIA_BOUNDS, OUTPUT_DATAMAPS_HEALTH
from typing import List
from datetime import datetime
import pandas as pd
from utils.health_utils import generate_single_day_forecast
import joblib

with open('models/gb_model.pkl', 'rb') as f:
    gb_model = joblib.load(f)


# conversioni alle unità AQI
def convert_to_aqi_unit(pollutant, value, unit):
    if pollutant == "O3":
        return value / 2140 if unit != "ppm" else value
    elif pollutant == "SO2":
        return value / 2.62 if unit != "ppb" else value
    elif pollutant == "NO2":
        return value / 1.88 if unit != "ppb" else value
    else:
        return value
    

def calculate_aqi(concentration, breakpoints):
    """
    Calcola l'AQI per una concentrazione usando i breakpoints EPA.
    """
    for (Clow, Chigh, Ilow, Ihigh) in breakpoints:
        if Clow <= concentration <= Chigh:
            return ((Ihigh - Ilow) / (Chigh - Clow)) * (concentration - Clow) + Ilow
    return None


def calculate_aqi_overall(concentrations):
    """
    Calcola l'AQI complessivo dato un dizionario di concentrazioni.
    """
    AQI_BREAKPOINTS = {
        "PM2.5": [
            (0.0, 12.0, 0, 50),
            (12.1, 35.4, 51, 100),
            (35.5, 55.4, 101, 150),
            (55.5, 150.4, 151, 200),
            (150.5, 250.4, 201, 300),
            (250.5, 500.0, 301, 500)
        ],
        "PM10": [
            (0, 54, 0, 50),
            (55, 154, 51, 100),
            (155, 254, 101, 150),
            (255, 354, 151, 200),
            (355, 424, 201, 300),
            (425, 604, 301, 500)
        ],
        "O3": [
            (0.000, 0.054, 0, 50),
            (0.055, 0.070, 51, 100),
            (0.071, 0.085, 101, 150),
            (0.086, 0.105, 151, 200),
            (0.106, 0.200, 201, 300)
        ],
        "SO2": [
            (0, 35, 0, 50),
            (36, 75, 51, 100),
            (76, 185, 101, 150),
            (186, 304, 151, 200),
            (305, 604, 201, 300),
            (605, 1004, 301, 500)
        ],
        "NO2": [
            (0, 53, 0, 50),
            (54, 100, 51, 100),
            (101, 360, 101, 150),
            (361, 649, 151, 200),
            (650, 1249, 201, 300),
            (1250, 2049, 301, 500)
        ]
    }


    max_aqi = 0

    for pollutant, conc in concentrations.items():
        if pollutant in AQI_BREAKPOINTS:
            aqi = calculate_aqi(conc, AQI_BREAKPOINTS[pollutant])
            if aqi:
                if aqi > max_aqi:
                    max_aqi = aqi
    return round(max_aqi)



def create_grid(bounds, resolution=50):
    lon_range = np.linspace(bounds["west"], bounds["east"], resolution)
    lat_range = np.linspace(bounds["south"], bounds["north"], resolution)
    lon_grid, lat_grid = np.meshgrid(lon_range, lat_range)

    grid_coords = np.column_stack([lon_grid.ravel(), lat_grid.ravel()])

    return lon_grid, lat_grid, grid_coords



def run_health_impact_map_kriging (
    measurements: List[AirQualityMeasurement],
    bounds=PUGLIA_BOUNDS,
    resolution=50,
    model = gb_model,
    target_date=None,
    extra_info=False
):
    if target_date is None:
        target_date = datetime.today()
    else:
        target_date = pd.to_datetime(target_date)


    coords = []
    feature_dicts = []
    for m in measurements:
        if m.pollutants is None:
            continue
        coords.append([m.longitude, m.latitude])
        pm25 = getattr(m.pollutants, "pm2_5_value", 0)
        pm25_unit = getattr(m.pollutants, "pm2dot5_unit", "µg/m³")

        pm10 = getattr(m.pollutants, "pm10_value", 0)
        pm10_unit = getattr(m.pollutants, "pm10_unit", "µg/m³")

        no2 = getattr(m.pollutants, "no2_value", 0)
        no2_unit = getattr(m.pollutants, "no2_unit", "µg/m³")

        o3 = getattr(m.pollutants, "o3_value", 0)
        o3_unit = getattr(m.pollutants, "o3_unit", "µg/m³")

        so2 = getattr(m.pollutants, "so2_value", 0)
        so2_unit = getattr(m.pollutants, "so2_unit", "µg/m³")

        pm25_ug = convert_to_aqi_unit("PM2.5", pm25, pm25_unit)
        pm10_ug = convert_to_aqi_unit("PM10", pm10, pm10_unit)
        o3_ppm = convert_to_aqi_unit("O3", o3, o3_unit)
        so2_ppb = convert_to_aqi_unit("SO2", so2, so2_unit)
        no2_ppb = convert_to_aqi_unit("NO2", no2, no2_unit)


        concentrations = {
            "PM2.5": pm25_ug,  # µg/m³
            "PM10": pm10_ug,   # µg/m³
            "O3": o3_ppm,   # ppm
            "SO2": so2_ppb, # ppb
            "NO2": no2_ppb  # ppb
        }

        aqi = calculate_aqi_overall(concentrations)

        weather = generate_single_day_forecast(m.latitude, m.longitude, target_date)
        temperature_kelvin = weather['temperature']
        humidity = weather['humidity']
        wind_speed = weather['wind_speed']

        temperature_celsius = temperature_kelvin - 273.15

        temperature_celsius = round(temperature_celsius, 1)

        feature_dicts.append({
            "AQI": aqi,
            "PM10": pm10_ug,
            "PM2_5": pm25_ug,
            "NO2": no2_ppb,
            "SO2": so2_ppb,
            "O3": o3_ppm,
            "Temperature": temperature_celsius,
            "Humidity": humidity,
            "WindSpeed": wind_speed,
        })

    features_df = pd.DataFrame(feature_dicts)
    features_df = features_df[model.feature_names_in_]

    health_index = model.predict(features_df)
    
    coords = np.array(coords)


    lon_grid, lat_grid, grid_coords = create_grid(bounds, resolution=resolution)

    kernel = RBF(length_scale=0.6, length_scale_bounds=(0.1, 0.4)) + WhiteKernel(noise_level=0.2)
    gp = GaussianProcessRegressor(kernel=kernel, alpha=1e-6, normalize_y=True)
    gp.fit(coords, health_index)

    pred_values, std_values = gp.predict(grid_coords, return_std=True)
    pred_grid = pred_values.reshape(lon_grid.shape)
    std_grid = std_values.reshape(lon_grid.shape)

    filename = generate_health_impact_map(
        lon_grid,
        lat_grid,
        pred_grid,
        coords,
        health_index,
        bounds=bounds,
        target_date=target_date,
        extra_info=extra_info
    )

    print(f"Heatmap generata: {filename}")
    return filename


def generate_health_impact_map(
    lon_grid, lat_grid, pred_grid, coords, values, 
    bounds=PUGLIA_BOUNDS, target_date=None, extra_info=False
):
    os.makedirs(OUTPUT_DATAMAPS_HEALTH, exist_ok=True)

    plt.figure(figsize=(12, 10))
    ax = plt.axes(projection=ccrs.PlateCarree())

    ax.set_extent([bounds["west"], bounds["east"], bounds["south"], bounds["north"]])

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
        cmap="YlOrRd",
        alpha=1,
        transform=ccrs.PlateCarree()
    )

    if extra_info:
        ax.scatter(
            coords[:, 0], coords[:, 1], c=values,
            cmap="viridis", s=50, edgecolors="black",
            transform=ccrs.PlateCarree(), zorder=5,
        )

        cbar = plt.colorbar(contour, ax=ax, shrink=0.7, pad=0.03)
        cbar.set_label("Indice impatto salute", rotation=270, labelpad=15)

        ax.gridlines(draw_labels=True)

    if target_date is None:
        filename = os.path.abspath(
        os.path.join(OUTPUT_DATAMAPS_HEALTH, "health_impact_map.png")
        )
    else:
        date_str = pd.to_datetime(target_date).strftime("%Y-%m-%d")
        filename = os.path.abspath(
            os.path.join(OUTPUT_DATAMAPS_HEALTH, f"health_impact_map_{date_str}.png")
        )

    plt.axis("off")
    plt.savefig(filename, dpi=300, bbox_inches="tight", pad_inches=0, transparent=not extra_info)
    plt.close()
    return filename