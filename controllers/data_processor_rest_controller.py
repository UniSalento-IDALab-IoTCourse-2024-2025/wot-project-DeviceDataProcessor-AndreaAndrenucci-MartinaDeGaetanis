from flask import Blueprint, request, jsonify, make_response
from models.dto import AirQualityMeasurementDTO, MeasurementResponseDTO, DataMapResponseDTO, DataMapDTO
from repositories.pollution_measurement_repository import PollutionMeasurementsRepository
from repositories.datamap_repository import DatamapRepository
from utils.token_utils import get_auth_params


measurements_bp = Blueprint("measurements", __name__)
measurement_repository = PollutionMeasurementsRepository()


@measurements_bp.route("/measurements/datamap/latest/<pollutant>", methods=["GET"])
def get_last_datamap(pollutant): 

    token = get_auth_params(request)
    if not (token.get("role") == "ADMIN" or token.get("role") == "REGULAR" or token.get("role") == "RESEARCHER" ) :
        return jsonify({"msg":"Token non valido"}), 403
    
    '''
    Recupera la datamap più recente
    '''
    
    try:
        if pollutant.lower() == "pm2.5":
            pollutant = "pm2dot5"
        repo = DatamapRepository()
        latest = repo.find_latest_measurement(pollutant=pollutant.lower())
        

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



@measurements_bp.route("/measurements", methods=["POST"])
def add_measurement():
    try:
        data = request.get_json()
        dto = AirQualityMeasurementDTO.from_dict(data)
        domain_model = dto.to_domain()
        measurement_repository.save(domain_model) 
        return jsonify(MeasurementResponseDTO(response=0, message="Salvataggio effettuato correttamente").to_dict()), 201
    except Exception as e:
        return jsonify(MeasurementResponseDTO(response=1, message=f"Errore nel salvataggio: {e}").to_dict()), 500
