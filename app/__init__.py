from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS
from .config import config

db = SQLAlchemy()


def create_app(config_name="default"):
    app = Flask(__name__)

    # Load default configuration
    app.config.from_object(config[config_name])

    db.init_app(app)
    migrate = Migrate(app, db)

    from .routes import bp

    app.register_blueprint(bp)

    CORS(app)

    return app
