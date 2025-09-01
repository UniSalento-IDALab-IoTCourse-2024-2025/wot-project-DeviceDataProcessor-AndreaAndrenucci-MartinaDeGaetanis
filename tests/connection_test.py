from flask import Blueprint, request, jsonify, make_response


test_bp = Blueprint("test", __name__)


@test_bp.route("/test/connection/", methods=["GET"])
def test_connection():
    return jsonify({"status": "success", "message": "Connessione riuscita"}), 200

@test_bp.route("/test/connection/<parameter>", methods=["GET"])
def pass_parameters(parameter):
    return jsonify({"status": "success", "message": f"Parametro passato: {parameter}"}), 200
    