from models.domain.air_quality_measurement import AirQualityMeasurement
from components.model_inference_service import run_kriging_on_measurements, generate_kriging_map_image, extract_measurements_coords_and_values
from config.constants import POLLUTANTS

if __name__ == "__main__":
    from models.domain.pollutants import Pollutants
    import random

    # Genera dati fittizi
    measurements = []
    for _ in range(20 ):
        m = AirQualityMeasurement(
            misuration_date="2025-06-19",
            denomination="Stazione X",
            municipality="Bari",
            province="BA",
            latitude=41.1 + random.uniform(-0.5, 0.5),
            longitude=16.8 + random.uniform(-1, 1),
            quality_index=3,
            quality_class="buona",
            area_type="urbana",
            pollutants=Pollutants(
                pm10_value=random.uniform(10, 60),
                no2_value=random.uniform(5, 30),
                c6h6_value=random.uniform(5, 30),
                co_value=random.uniform(5, 30),
                h2s_value=random.uniform(5, 30),
                ipa_value=random.uniform(5, 30),
                o3_value=random.uniform(5, 30),
                pm2dot5_value=random.uniform(5, 30),
                so2_value=random.uniform(5, 30),
            )
        )
        measurements.append(m)

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
