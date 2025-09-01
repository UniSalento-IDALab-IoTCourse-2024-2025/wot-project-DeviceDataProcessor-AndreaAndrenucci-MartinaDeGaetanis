from flask import Blueprint, jsonify, request
import os
import base64
from utils.token_utils import get_auth_params


images_bp = Blueprint("images", __name__)

@images_bp.route("/images/<region>/<date>/<hour>/<filename>", methods=["GET"])
def serve_image(region, date, hour, filename):
    
    token = get_auth_params(request)
    if not (token.get("role") == "ADMIN" or token.get("role") == "REGULAR" or token.get("role") == "RESEARCHER" ) :
        return jsonify({"msg":"Token non valido"}), 403
    
    try:
        file_path = f"./out/datamaps/{region}/{date}T{hour}/{filename}"
        if os.path.exists(file_path):
            with open(file_path, "rb") as image_file:
                encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
                return jsonify({"image_base64": encoded_string, "code":0})
        else:
            return jsonify({"error": "File not found", "code":1}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@images_bp.route("/images/health/<filename>", methods=["GET"])
def serve_image_health(filename):

    
    token = get_auth_params(request)
    if not (token.get("role") == "ADMIN" or token.get("role") == "REGULAR" or token.get("role") == "RESEARCHER" ) :
        return jsonify({"msg":"Token non valido"}), 403
    
    try:
        file_path = f"./out/datamaps/datamapsHealth/{filename}"
        if os.path.exists(file_path):
            with open(file_path, "rb") as image_file:
                encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
                return jsonify({"image_base64": encoded_string, "code":0})
        else:
            return jsonify({"error": "File not found", "code":1}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@images_bp.route("/images/health/delete/<filename>", methods=["DELETE"])
def delete_image_health(filename):
    try:
        file_path = f"./out/datamaps/datamapsHealth/{filename}"

        if os.path.exists(file_path):
            os.remove(file_path)
            return jsonify({"message": "File eliminato con successo", "code": 0}), 200
        else:
            return jsonify({"error": "File non trovato", "code": 1}), 404

    except Exception as e:
        return jsonify({"error": str(e), "code": 2}), 500