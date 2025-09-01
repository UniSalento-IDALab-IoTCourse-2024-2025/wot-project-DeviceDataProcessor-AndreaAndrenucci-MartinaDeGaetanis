DATASET_PATH = './Dataset/Dataset.csv'

OUTPUT_DIR_MODEL = '../out/output_model/'
OUTPUT_DATAMAPS="./out/datamaps/"
OUTPUT_DATAMAPS_HEALTH="./out/datamaps/datamapsHealth"
OUTPUT_DIR_RF = '../out/output_rf/'

PUGLIA_BOUNDS = {"north": 42.1, "south": 39.7, "west": 14.7, "east": 18.8}
LECCE_BOUNDS = {"north": 40.401261, "south": 40.313983, "west": 18.075689, "east": 18.254114}

SUPPORTED_SUBREGIONS = [
    {
        "region":"Lecce",
        "puglia-scale":True,
        "bounds":PUGLIA_BOUNDS
    },
    {
        "region":"Lecce",
        "puglia-scale":False,
        "bounds":LECCE_BOUNDS
    }
]

TREE_ABSORPTION = {
    "c6h6_value": 1.1,
    "co_value": 0.7,
    "h2s_value": 0.003,
    "ipa_value": 0.018,
    "no2_value": 28.0,
    "o3_value": 62.0,
    "pm10_value": 26.0,
    "pm2dot5_value": 15.0,
    "so2_value": 1.6
}


NUM_ROWS = 68 # 80 170

CELLS_X = 40
CELLS_Y = 30

POLLUTANTS = {
    "PM10": "PM10_valore_inquinante_misurato",
    "PM2.5": "PM2.5_valore_inquinante_misurato",
    "NO2": "NO2_valore_inquinante_misurato",
    "O3": "O3_valore_inquinante_misurato",
    "SO2": "SO2_valore_inquinante_misurato",
    "CO": "CO_valore_inquinante_misurato",
    "C6H6": "C6H6_valore_inquinante_misurato",
    "IPA": "IPA_valore_inquinante_misurato",
    "H2S": "H2S_valore_inquinante_misurato"
}