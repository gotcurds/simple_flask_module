from flask import Flask
from .models import db
from .extensions import ma
from .blueprints.customers import customers_bp
from .blueprints.mechanics import mechanics_bp
from .blueprints.tickets import service_tickets_bp



def create_app(config_name):

    app = Flask(__name__)
    app.config.from_object(f"config.{config_name}")

    db.init_app(app)
    ma.init_app(app)

    app.register_blueprint(customers_bp, url_prefix='/customers')
    app.register_blueprint(mechanics_bp, url_prefix='/mechanics')
    app.register_blueprint(service_tickets_bp, url_prefix='/service-tickets')

    return app