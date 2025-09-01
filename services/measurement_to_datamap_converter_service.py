from flask import jsonify
import time
from config.constants import POLLUTANTS
from components.model_inference_service import extract_measurements_coords_and_values, run_kriging_on_measurements, generate_kriging_map_image
from models.domain import AirQualityMeasurement, DataMap
from repositories.pollution_measurement_repository import PollutionMeasurementsRepository
import sys


def periodic_task():
    while True:
        print("Esecuzione della funzione di servizio")
        #TODO check with os if mongo datamap exists non la creo
        #TODO gestione directory con le date
        repo = PollutionMeasurementsRepository()
        latest = repo.find_latest_measurement()
        print("Latest mes: ", latest)
        pass

        if not latest:
            print("Nessuna misura trovata")
            return jsonify({
                "status": "error",
                "message": "Nessuna misura trovata",
                "data": []
            }), 404

        measurements = repo.find_by_exact_date(latest.misuration_date)
        
        for pollutant in POLLUTANTS:
            pollutant = pollutant.lower()
            print(pollutant)

            if (pollutant == "pm2.5"):
                pollutant = "pm2dot5"

            # Estrai coordinate e valori
            coords, values = extract_measurements_coords_and_values(measurements, pollutant)

            # Esegui kriging
            lon_grid, lat_grid, pred_grid, std_grid, _ = run_kriging_on_measurements(coords, values, measurements, pollutant)

            image_path = generate_kriging_map_image(lon_grid, lat_grid, pred_grid, coords, values, pollutant)
            print(f"Immagine salvata in: {image_path}")

        time.sleep(1000)