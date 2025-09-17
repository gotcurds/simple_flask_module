from flask import Flask
from .models import db
from .extensions import ma, limiter
from .blueprints.customers import customers_bp
from .blueprints.mechanics import mechanics_bp
from .blueprints.tickets import service_tickets_bp
from .blueprints.parts import parts_bp
from flasgger import Swagger
from config import Config, TestConfig

def create_app(config_class=Config):
    app = Flask(__name__)
    
    # Check if the config_class is a string and map it to the correct class
    if isinstance(config_class, str):
        if config_class == 'test_config':
            app.config.from_object(TestConfig)
        else:
            # Handle other string-based configurations if needed
            app.config.from_object(config_class)
    else:
        # If it's a class object, use it directly
        app.config.from_object(config_class)

    db.init_app(app)
    ma.init_app(app)
    limiter.init_app(app)
    Swagger(app)

    app.register_blueprint(customers_bp, url_prefix='/customers')
    app.register_blueprint(mechanics_bp, url_prefix='/mechanics')
    app.register_blueprint(service_tickets_bp, url_prefix='/service-tickets')
    app.register_blueprint(parts_bp, url_prefix='/parts')
    
    return app