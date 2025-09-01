from celery import Celery
from components.model_inference_service import (
    extract_measurements_coords_and_values,
    run_kriging_on_measurements,
    generate_kriging_map_image
)

from components.model_inference_health_service import run_health_impact_map_kriging
from utils.filters import filter_by_municipality
from repositories.pollution_measurement_repository import PollutionMeasurementsRepository
from repositories.datamap_repository import DatamapRepository
from models.domain import DataMap
from models.dto import AirQualityMeasurementDTO
from config.constants import POLLUTANTS, SUPPORTED_SUBREGIONS
import json
from datetime import datetime, timedelta

NEW_MEASUREMENT_QUEUE = "new-measurement-queue"

celery_app = Celery(
    "myapp",
    broker="amqp://guest:guest@rabbitmq:5672//",
)

celery_app.conf.task_queues = {
    NEW_MEASUREMENT_QUEUE: {
        "exchange": NEW_MEASUREMENT_QUEUE,
        "routing_key": NEW_MEASUREMENT_QUEUE,
    }
}

celery_app.conf.task_default_queue = NEW_MEASUREMENT_QUEUE
celery_app.conf.task_default_exchange = NEW_MEASUREMENT_QUEUE
celery_app.conf.task_default_routing_key = NEW_MEASUREMENT_QUEUE

pollutionMeasurementsRepository = PollutionMeasurementsRepository()    
datamapRepository = DatamapRepository()

@celery_app.task(name="process_message")
def process_message(body):
    '''
    Dato un array di misure, generare l'immagine, 
    splittare tutte le misure e salvarle singolarmente
    '''
    dto_array = [AirQualityMeasurementDTO.from_dict(obj) for obj in json.loads(body)]
    measurements = [dto.to_domain() for dto in dto_array]
    
    now = datetime.now()
    rounded_now = (now.replace(minute=0, second=0, microsecond=0) 
                + timedelta(hours=1) if now.minute > 0 else now.replace(minute=0, second=0, microsecond=0))

    for dto in dto_array:
        dto.misuration_date = rounded_now.isoformat()

    pollutionMeasurementsRepository.save_all(measurements)
    
    try:
        '''
            Le predizioni vanno generate prima per tutta la regione, poi per le singole città
        '''
        generate_predictions(measurements)
        generate_health_prediction(measurements)

        '''
            Filtro per municipality e genero le misurazioni
        '''

        for subregion in SUPPORTED_SUBREGIONS:
            filtered_measurements = filter_by_municipality(measurements, subregion.get("region"))
            generate_predictions(filtered_measurements, subregion=subregion)

    except Exception as e:
        print(f"[process_message] Errore: {e}")


def generate_predictions(measurements, subregion = None):

    if subregion and subregion.get("puglia-scale")==True:
        subregion["region"] = "Lecce-Scaled" 


    try:
        for pollutant in POLLUTANTS:
            pollutant = pollutant.lower()
            if pollutant == "pm2.5":
                pollutant = "pm2dot5"

            bounds = subregion.get("bounds") if subregion else None

            coords, values = extract_measurements_coords_and_values(measurements, pollutant)

            lon_grid, lat_grid, pred_grid, std_grid, _ = run_kriging_on_measurements(
                coords=coords,
                values=values,
                bounds=bounds,
                resolution= 100 if subregion else 50,
                scale= 0.15 if subregion else 0.6,
                lower_scale_bound=0.01 if subregion else 0.1,
                upper_scale_bound=0.02 if subregion else 0.4,
                noise= 0.06 if subregion else 0.2,
            )

            image_path = generate_kriging_map_image(
                lon_grid, lat_grid, pred_grid, coords, values, pollutant, bounds, subregion.get("region") if subregion else None, extra_info=False
            )

            print(f"[generate_predictions] Immagine salvata in: {image_path}")

            datamapRepository.save(
                DataMap(
                    date=datetime.now(),  # <--- OGGETTO datetime, NON .isoformat()
                    pollutant=pollutant,
                    url=image_path,
                    region= subregion.get("region") if subregion else "Puglia"
                )
            )
    except Exception as e:
        print(f"[generate_predictions] Errore: {e}")


def generate_health_prediction(measurements):
    try:
        health_image_path = run_health_impact_map_kriging(
            measurements,
            resolution=50,
            target_date=None,
            extra_info=False
        )

        print(f"[generate_health_predictions] Immagine salvata in: {health_image_path}")

        datamapRepository.save(
            DataMap(
                date=datetime.now(),
                pollutant="health_index",
                url=health_image_path,
                region="Puglia"
            )
        )

    except Exception as e:
        print(f"[generate_health_prediction] Errore: {e}")
