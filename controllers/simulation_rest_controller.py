from flask import Blueprint, jsonify, request, send_file
import math
from repositories.pollution_measurement_repository import PollutionMeasurementsRepository
from utils.filters import filter_by_municipality
from components.model_inference_service import (
    extract_measurements_coords_and_values,
    run_kriging_on_measurements,
    generate_kriging_map_image,
    get_out_dir
)
from models.domain import Pollutants, AirQualityMeasurement
from config.constants import POLLUTANTS, SUPPORTED_SUBREGIONS, TREE_ABSORPTION
from datetime import datetime, timezone
import zipfile
import os
from utils.token_utils import get_auth_params


simulations_bp = Blueprint("simulations", __name__)

measurementRepository = PollutionMeasurementsRepository()

@simulations_bp.route("/simulations", methods=["POST"])
def print_bounds():
    # token = get_auth_params(request)
    # if not (token.get("role") == "ADMIN" or token.get("role") == "RESEARCHER" ) :
    #     return jsonify({"msg":"Token non valido"}), 403
    
    data = request.get_json()

    lat_min = data.get("lat_min")
    lon_min = data.get("lon_min")
    lat_max = data.get("lat_max")
    lon_max = data.get("lon_max")
    n_points = data.get("n_points")
    
    date = data.get("date")

    measurements = []

    measurements = measurementRepository.find_by_exact_date(date)
    try:
        if not measurements or len(measurements) == 0: 
            return jsonify({"Error":"Nessuna misura trovata per la data"})
    except Exception as e:
        return jsonify({
            "Error":"Errore nel recupero delle misure",
            "Msg":f"{e}",
            "Date":f"{date}"
        })

    measurements = filter_by_municipality(measurements, "Lecce")

    
    n_rows, n_cols, height, width = get_grid_from_coords(
        lat_max=lat_max,
        lat_min=lat_min,
        lon_max=lon_max,
        lon_min=lon_min,
        n_points=n_points
    )

    points = []
    for i in range(n_rows):
        for j in range(n_cols):
            lat = lat_min + (i + 0.5) * (height / n_rows)
            lon = lon_min + (j + 0.5) * (width / n_cols)
            points.append({"lat": lat, "lon": lon})
    

    zip_files = run_predictions(measurements, points)
    return send_file(
            zip_files,
            mimetype="application/zip",
            as_attachment=True,
            download_name="simulation_results.zip"
        )



def get_grid_from_coords(lat_min, lat_max, lon_min, lon_max, n_points):
    
    if None in [lat_min, lon_min, lat_max, lon_max, n_points]:
        return jsonify({"error": "Missing parameters"}), 400
    
    
    width = lon_max - lon_min
    height = lat_max - lat_min
    aspect_ratio = width / height if height != 0 else 1
    
    
    n_cols = round(math.sqrt(n_points * aspect_ratio))
    n_rows = round(n_points / n_cols) if n_cols != 0 else n_points
    
    if n_cols == 0: n_cols = 1
    if n_rows == 0: n_rows = 1

    return n_rows, n_cols, height, width


def run_predictions(measurements, points, zip_output=True):
    simulation_datas = []
    generated_files = []

    for point in points:
        lat = point["lat"]
        lon = point["lon"]
        sim_measurement = AirQualityMeasurement(
            misuration_date=datetime.now(timezone.utc),
            denomination="Simulated Tree Absorption",
            municipality=None,
            province=None,
            latitude=lat,
            longitude=lon,
            quality_index=None,         
            quality_class=None,         
            area_type=None,              
            pollutants=Pollutants(
                c6h6_value=TREE_ABSORPTION["c6h6_value"],
                co_value=TREE_ABSORPTION["co_value"],
                h2s_value=TREE_ABSORPTION["h2s_value"],
                ipa_value=TREE_ABSORPTION["ipa_value"],
                no2_value=TREE_ABSORPTION["no2_value"],
                o3_value=TREE_ABSORPTION["o3_value"],
                pm10_value=TREE_ABSORPTION["pm10_value"],
                pm2dot5_value=TREE_ABSORPTION["pm2dot5_value"],
                so2_value=TREE_ABSORPTION["so2_value"],
            )
        )
        simulation_datas.append(sim_measurement)

    for pollutant in POLLUTANTS:
        pollutant = pollutant.lower()
        if pollutant == "pm2.5":
            pollutant = "pm2dot5"

        subregion = SUPPORTED_SUBREGIONS[1]
        bounds = subregion.get("bounds") 

        coords, values = extract_measurements_coords_and_values(measurements, pollutant)
        sim_coords, sim_values = extract_measurements_coords_and_values(simulation_datas, pollutant)

        lon_grid, lat_grid, pred_grid, std_grid, _ = run_kriging_on_measurements(
            coords=coords,
            values=values,
            bounds=bounds,
            resolution=100,
            scale=0.15,
            lower_scale_bound=0.01,
            upper_scale_bound=0.02,
            noise=0.06,
            simulation_datas=(sim_coords, sim_values),
            pollutant=pollutant
        )

        image_path = generate_kriging_map_image(
            lon_grid, lat_grid, pred_grid, coords, values, pollutant, bounds,
            "Simulation", True, sim_coords=sim_coords
        )

        generated_files.append(image_path)


    if zip_output and generated_files:
        out_dir = get_out_dir(region="simulations_dir", overwrite=True)
        os.makedirs(out_dir, exist_ok=True)

        zip_path = os.path.join(out_dir, "simulation_results.zip")
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
            for file_path in generated_files:
                arcname = os.path.basename(file_path)
                zipf.write(file_path, arcname=arcname)
        return zip_path

    
    return generated_files
