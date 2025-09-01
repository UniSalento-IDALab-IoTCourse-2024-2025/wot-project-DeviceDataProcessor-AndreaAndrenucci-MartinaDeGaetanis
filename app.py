from flask import Flask
from controllers.data_processor_rest_controller import measurements_bp
from tests.connection_test import test_bp
from controllers.images_rest_controller import images_bp
from controllers.simulation_rest_controller import simulations_bp
from controllers.simulation_health_rest_controller import health_simulation_bp
from controllers.reports_rest_controller import reports_bp
from repositories.pollution_measurement_repository import PollutionMeasurementsRepository
import os

app = Flask(__name__)

PollutionMeasurementsRepository()

if __name__ == "__main__":
    app.register_blueprint(measurements_bp)
    app.register_blueprint(test_bp)
    app.register_blueprint(simulations_bp)
    app.register_blueprint(images_bp)
    app.register_blueprint(health_simulation_bp)
    app.register_blueprint(reports_bp)
    app.run(host="0.0.0.0",port=8080, debug=True)

