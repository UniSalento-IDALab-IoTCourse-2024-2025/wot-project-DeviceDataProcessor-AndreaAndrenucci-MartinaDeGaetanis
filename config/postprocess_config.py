INPUT_FILE = "./predictions.geojson"
OUTPUT_FILE = "./out/postprocess.geojson"
MIN_BLOCK_SIZE = 6  
TOLERANCE = 0.8    
VALUE_KEYS=[
    "PM10_predicted",
    "PM2.5_predicted",
    "NO2_predicted",
    "O3_predicted",
    "SO2_predicted",
    "CO_predicted",
    "C6H6_predicted",
    "IPA_predicted",
    "H2S_predicted"
]