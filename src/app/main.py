from flask import Flask
from src.app.routes import api
from src.app.metrics import metrics_endpoint
from src.app.config import Config
from src.app.logging_config import setup_logging
import logging


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    setup_logging(Config.LOG_LEVEL)

    app.register_blueprint(api, url_prefix="/api/v1")
    app.add_url_rule("/metrics", "metrics", metrics_endpoint)

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=5000)
