from datetime import datetime, date
from flask import Blueprint, jsonify, request
from repositories.pollution_measurement_repository import PollutionMeasurementsRepository
from repositories.datamap_repository import DatamapRepository
from models.dto import AirQualityMeasurementDTO, MeasurementResponseDTO, DataMapResponseDTO, DataMapDTO
import joblib
import pandas as pd
import numpy as np
from utils.health_utils import generate_single_day_forecast, prediction_measuraments
from components.model_inference_health_service  import convert_to_aqi_unit, calculate_aqi_overall, create_grid, generate_health_impact_map
from config.constants import PUGLIA_BOUNDS, OUTPUT_DATAMAPS_HEALTH
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import RBF, WhiteKernel
from sklearn.cluster import DBSCAN
from utils.token_utils import get_auth_params

health_simulation_bp = Blueprint("health_simulation", __name__)

measurementRepository = PollutionMeasurementsRepository()

with open('models/gb_model.pkl', 'rb') as f:
    gb_model = joblib.load(f)

@health_simulation_bp.route("/health-simulation/datamap/latest", methods=["GET"])
def get_latest_datamap_health():
    token = get_auth_params(request)
    if not (token.get("role") == "ADMIN" or token.get("role") == "RESEARCHER" ) :
        return jsonify({"msg":"Token non valido"}), 403
    try:
        repo = DatamapRepository()
        latest = repo.find_latest_measurement(pollutant="health_index")

        if not latest:
            return jsonify({
                "status": "error",
                "message": "Nessuna datamap trovata",
                "data": {}
            }), 404

        
        dto = DataMapDTO.from_domain(latest)

        return jsonify(DataMapResponseDTO(
                response=0,
                message="Datamap recuperata correttamente",
                payload=[dto]
            ).to_dict()
        ), 200 
    except Exception as e:
        return jsonify(DataMapResponseDTO(response=1, message=f"{e}").to_dict()), 400


@health_simulation_bp.route("/health-simulation/datamap", methods=['POST'])
def run_prediction_health():
    
    token = get_auth_params(request)
    if not (token.get("role") == "ADMIN" or token.get("role") == "RESEARCHER" ) :
        return jsonify({"msg":"Token non valido"}), 403
    
    data = request.get_json()
    date_str = data.get('date')  # deve essere in formato YYYY-MM-DD
    
    if not date_str:
        return jsonify({
            "status": "error",
            "message": "Parametro 'date' mancante"
        }), 400
    
    oggi = date.today()
    coords = measurementRepository.find_unique_coords_closest_to_today()

    print(f"Coordinate trovate: {len(coords) if coords else 0}")
    
    if not coords:
        return jsonify({
            "status": "error", 
            "message": f"Nessuna stazione trovata per la data {oggi}"
        }), 404
    
    try:
        target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError as e:
        return jsonify({
            "status": "error",
            "message": f"Formato data non valido: {date_str}. Utilizzare YYYY-MM-DD"
        }), 400
    
    predictions = []
    feature_dicts = []
    successful_coords = []

    coords = np.array(coords)

    # Clustering
    clustering = DBSCAN(eps=0.21, min_samples=1).fit(coords)
    labels = clustering.labels_
    unique_coords = []

    # Per ogni cluster, prendi il centroide
    for label in np.unique(labels):
        cluster_points = coords[labels == label]
        centroid = cluster_points.mean(axis=0)
        unique_coords.append(centroid)

    unique_coords = np.array(unique_coords)

    for i, coord in enumerate(unique_coords):
        longitude, latitude = coord
        spatial_target = [longitude, latitude]

        print(f"Processando coordinata {i+1}/{len(unique_coords)}: {coord}")
        
        try:
            prediction = prediction_measuraments(target_date, spatial_target)
            print(prediction)

            if not prediction or not isinstance(prediction, dict):
                raise ValueError(f"Predizione non valida ricevuta: {prediction}")

            prediction_station = {
                "coordinates": {
                    "longitude": longitude,
                    "latitude": latitude
                },
                "pollutants": {
                    "pm2_5": prediction.get("PM2.5"),
                    "pm10": prediction.get("PM10"),
                    "no2": prediction.get("NO2"),
                    "o3": prediction.get("O3"),
                    "so2": prediction.get("SO2")
                }
            }


            try:
                print(f"Tentativo calcolo health index per coordinata {i+1}")
                
                input_station = prediction_health_index(latitude, longitude, target_date, prediction_station)
                
                feature_dicts.append(input_station)
                successful_coords.append(coord)
                
            except Exception as health_error:
                print(f"ERRORE nel calcolo health index per coordinata {i+1}:")
                print(f"Tipo errore: {type(health_error).__name__}")
                print(f"Messaggio: {str(health_error)}")
                import traceback
                print(f"Traceback: {traceback.format_exc()}")
            
            predictions.append(prediction_station)
                        
        except Exception as prediction_error:
            print(f"Errore nella predizione per coordinata {i+1}: {str(prediction_error)}")
            predictions.append({
                "coordinates": {
                    "longitude": longitude,
                    "latitude": latitude
                },
                "pollutants": None,
                "error": str(prediction_error)
            })

    if not feature_dicts:
        return jsonify({
            "status": "error",
            "message": "Nessuna predizione valida ottenuta per il calcolo dell'indice di salute"
        }), 500

    try:
        features_df = pd.DataFrame(feature_dicts)
        features_df = features_df[gb_model.feature_names_in_]
        health_index = gb_model.predict(features_df)

        coords_for_map = np.array(successful_coords)
        filename = generate_map(coords_for_map, health_index, target_date)

        return jsonify({
            "status": "success",
            "filename": filename,
            "data": {
                "target_date": date_str,
                "predictions": predictions
            }
        }), 200

    except Exception as model_error:
        print(f"Errore nel modello o nella generazione della mappa: {str(model_error)}")
        return jsonify({
            "status": "error",
            "message": f"Errore nella generazione del modello: {str(model_error)}"
        }), 500


def prediction_health_index(latitude, longitude, target_date, predictions):
    weather = generate_single_day_forecast(latitude, longitude, target_date)
    temperature_kelvin = weather['temperature']
    humidity = weather['humidity']
    wind_speed = weather['wind_speed']

    temperature_celsius = temperature_kelvin - 273.15
    temperature_celsius = round(temperature_celsius, 1)

    pm25 = predictions["pollutants"]["pm2_5"]
    pm10 = predictions["pollutants"]["pm10"]
    no2  = predictions["pollutants"]["no2"]
    o3   = predictions["pollutants"]["o3"]
    so2  = predictions["pollutants"]["so2"]

    pm25_ug = convert_to_aqi_unit("PM2.5", pm25, "µg/m³")
    pm10_ug = convert_to_aqi_unit("PM10", pm10, "µg/m³")
    o3_ppm = convert_to_aqi_unit("O3", o3, "µg/m³")
    so2_ppb = convert_to_aqi_unit("SO2", so2, "µg/m³")
    no2_ppb = convert_to_aqi_unit("NO2", no2, "µg/m³")


    concentrations = {
        "PM2.5": pm25_ug,  # µg/m³
        "PM10": pm10_ug,   # µg/m³
        "O3": o3_ppm,   # ppm
        "SO2": so2_ppb, # ppb
        "NO2": no2_ppb  # ppb
    }

    aqi = calculate_aqi_overall(concentrations)

    input_model = {
        "AQI": aqi,
        "PM10": pm10_ug,
        "PM2_5": pm25_ug,
        "NO2": no2_ppb,
        "SO2": so2_ppb,
        "O3": o3_ppm,
        "Temperature": temperature_celsius,
        "Humidity": humidity,
        "WindSpeed": wind_speed,
    }

    return input_model



def generate_map(coords, health_index, target_date):
    lon_grid, lat_grid, grid_coords = create_grid(PUGLIA_BOUNDS, resolution=50)

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
        bounds=PUGLIA_BOUNDS,
        target_date=target_date,
        extra_info=False
    )

    print(f"Heatmap generata: {filename}")
    return filename