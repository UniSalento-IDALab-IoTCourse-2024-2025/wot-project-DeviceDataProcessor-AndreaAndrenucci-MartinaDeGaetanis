from flask import Blueprint, jsonify, request
from repositories.pollution_measurement_repository import PollutionMeasurementsRepository
from statistics import median
from collections import defaultdict

reports_bp = Blueprint("reports", __name__)

measurementRepository = PollutionMeasurementsRepository()


from flask import jsonify

@reports_bp.route("/reports/<pollutant>/<start_date>/<finish_date>", methods=["GET"])
def get_measurement_report(pollutant, start_date, finish_date):
    try:
        measurements = measurementRepository.find_between_dates(start_date, finish_date)

        if not measurements:
            return jsonify({
                "status": "error",
                "message": "Nessuna misurazione trovata",
                "data": {}
            }), 404

        field_name = f"{pollutant}_value"

        grouped = defaultdict(list)

        for m in measurements:
            dt_key = m.misuration_date.isoformat()
            value = getattr(m.pollutants, field_name, None)
            if value is not None:
                grouped[dt_key].append(value)

        dates = []
        values = []

        for dt_key in sorted(grouped.keys()):
            dates.append(dt_key)
            values.append(median(grouped[dt_key]))

        return jsonify({
            "status": "success",
            "data": {
                "dates": dates,
                "values": values
            }
        })

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e),
            "data": {}
        }), 500
