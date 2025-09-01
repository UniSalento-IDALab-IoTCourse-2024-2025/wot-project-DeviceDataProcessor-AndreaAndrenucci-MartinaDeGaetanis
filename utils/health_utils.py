import numpy as np
import pandas as pd
import pickle
import os
from datetime import timedelta, date
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"
import tensorflow as tf
LoadModel = tf.keras.models.load_model


def calculate_and_save_daily_stats(historical_data, filename='daily_stats.pkl'):

    daily_stats = historical_data.groupby(['month', 'day']).agg({
        'temperature': ['mean', 'std'],
        'humidity': ['mean', 'std'],
        'wind_speed': ['mean', 'std']
    })

    daily_stats.columns = ['_'.join(col) for col in daily_stats.columns]
    daily_stats = daily_stats.reset_index()

    with open(filename, 'wb') as f:
        pickle.dump(daily_stats, f)

    print(f"Daily stats calcolate e salvate in {filename}")
    return


def generate_single_day_forecast(latitude, longitude, target_date, daily_stats_file='./models/daily_stats.pkl', random_seed=42):
    np.random.seed(random_seed)
    
    with open(daily_stats_file, 'rb') as f:
        daily_stats = pickle.load(f)
    
    if isinstance(target_date, str):
        target_date = pd.to_datetime(target_date)
    
    stats = daily_stats[
        (daily_stats['Latitude'] == latitude) &
        (daily_stats['Longitude'] == longitude) &
        (daily_stats['month'] == target_date.month) & 
        (daily_stats['day'] == target_date.day)
    ]
    
    if len(stats) > 0:
        temp = np.random.normal(stats.iloc[0]['temperature_mean'], stats.iloc[0]['temperature_std'])
        hum = np.random.normal(stats.iloc[0]['humidity_mean'], stats.iloc[0]['humidity_std'])
        wind = np.random.normal(stats.iloc[0]['wind_speed_mean'], stats.iloc[0]['wind_speed_std'])
    else:
        temp = np.random.normal(daily_stats['temperature_mean'].mean(), daily_stats['temperature_std'].mean())
        hum = np.random.normal(daily_stats['humidity_mean'].mean(), daily_stats['humidity_std'].mean())
        wind = np.random.normal(daily_stats['wind_speed_mean'].mean(), daily_stats['wind_speed_std'].mean())
    
    hum = np.clip(hum, 0, 100)
    wind = max(0, wind)
    
    return {
        'date': target_date.strftime('%d-%m-%Y'),
        'temperature': round(temp, 2),
        'humidity': round(hum, 2),
        'wind_speed': round(wind, 2)
    }


def haversine_distance(lon1, lat1, lon2, lat2):

    from math import radians, cos, sin, asin, sqrt
    
    # Converti in radianti
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    
    # Formula haversine
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    r = 6371  # Raggio della Terra in km
    
    return c * r

def find_nearest_coordinates(longitude, latitude):
    """
    Utilizzo della formula haversine per distanze più accurate
    """
    try:
        coords_df = pd.read_csv('./models/training_coordinates.csv')
    except FileNotFoundError:
        raise FileNotFoundError("File training_coordinates.csv non trovato.")
    
    # Calcola distanze usando haversine (più accurato per coordinate geografiche)
    coords_df['distance_km'] = coords_df.apply(
        lambda row: haversine_distance(longitude, latitude, row['Longitude'], row['Latitude']), 
        axis=1
    )
    
    closest = coords_df.loc[coords_df['distance_km'].idxmin()]
    
    return {
        'longitude': closest['Longitude'],
        'latitude': closest['Latitude'], 
        'distance_km': closest['distance_km'],
        'coord_key': f"{closest['Latitude']}_{closest['Longitude']}"
    }



def prediction_measuraments(target_date, spatial_target):

    pollutant_columns = ['PM2.5','PM10','NO2','O3','SO2']

    model = LoadModel("./models/best_model.keras")

    with open("./models/last_sequences_updated.pkl", "rb") as f:
        last_sequences = pickle.load(f)
    
    # print(list(last_sequences.keys()))

    with open("./models/meteo_scaler.pkl", "rb") as f:
        meteo_scaler = pickle.load(f)

    with open("./models/pollutant_scaler.pkl", "rb") as f:
        pollutant_scaler = pickle.load(f)

    with open("./models/year_scaler.pkl", "rb") as f:
        year_scaler = pickle.load(f)

    with open("./models/coord_scaler.pkl", "rb") as f:
        coord_scaler = pickle.load(f)


    lon, lat = spatial_target

    # Trova le coordinate più vicine presenti nel dataset
    nearest = find_nearest_coordinates(lon, lat)
    station_id = nearest['coord_key']

    if station_id not in last_sequences:
        raise ValueError(f"Nessuna sequenza disponibile per la stazione più vicina {station_id}")

    # Recupera l'ultima sequenza salvata
    X_seq = last_sequences[station_id]["X_seq"]

    # Assicurati che target_date sia un datetime
    if isinstance(target_date, str):
        target_date = pd.to_datetime(target_date)
    current_date = date(2025, 8, 25)

    def get_scaled_meteo(latitudine, longitudine, date):
        meteo_dict = generate_single_day_forecast(latitudine, longitudine, date)
        meteo_array = pd.DataFrame(
            [[meteo_dict['temperature'], meteo_dict['humidity'], meteo_dict['wind_speed']]],
            columns=['temperature','humidity','wind_speed']
        )
        return meteo_scaler.transform(meteo_array)


    while current_date <= target_date:
        # Feature temporali cicliche
        year_df = pd.DataFrame([[current_date.year]], columns=['year'])
        year = year_scaler.transform(year_df)[0][0]        
        month = current_date.month
        day = current_date.day
        month_sin = np.sin(2 * np.pi * month / 12)
        month_cos = np.cos(2 * np.pi * month / 12)
        day_sin = np.sin(2 * np.pi * day / 31)
        day_cos = np.cos(2 * np.pi * day / 31)
        X_temp = np.expand_dims([year, month_sin, month_cos, day_sin, day_cos], axis=0)

        # Feature meteo scalate
        X_meteo = get_scaled_meteo(nearest['latitude'], nearest['longitude'], current_date)

        # Feature spaziali
        coords_df = pd.DataFrame(
            [[nearest['latitude'], nearest['longitude']]],
            columns=['Latitude', 'Longitude']
        )
        X_spatial = coord_scaler.transform(coords_df)

        # Predizione
        pred_scaled = model.predict([X_seq[np.newaxis, :, :], X_meteo, X_temp, X_spatial], verbose=0)

        # Aggiorna sequenza autoregressiva
        X_seq = np.vstack([X_seq[1:], pred_scaled])

        current_date += timedelta(days=1)

    # Descalare e arrotondare
    pred_scaled_df = pd.DataFrame(pred_scaled, columns=pollutant_columns)
    y_pred_rescaled = pollutant_scaler.inverse_transform(pred_scaled_df)
    rounded_predictions = np.round(y_pred_rescaled).astype(int)

    # Creazione dizionario finale
    prediction_dict = {pollutant: int(rounded_predictions[0, i]) 
                       for i, pollutant in enumerate(pollutant_columns)}

    return prediction_dict