import os
from datetime import timedelta

# Define the base directory for path construction
basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    """Base configuration for the application."""
    # Use environment variable for database URL, fallback to SQLite for local use
    # CRITICAL: Render will set the DATABASE_URL environment variable.
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
                              'sqlite:///' + os.path.join(basedir, 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Security: SECRET_KEY is used for sessions and JWT.
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'default-dev-secret-key-12345'
    
    # Flask-Caching configuration
    CACHE_TYPE = "SimpleCache"  # Use a simple in-memory cache for dev
    CACHE_DEFAULT_TIMEOUT = 300 # Cache for 5 minutes
    
    # JWT Configuration
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'super-secret-jwt-key'
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
    
    # Swagger/Flask-RESTX configuration
    SWAGGER_UI_DOC_EXPANSION = 'list'
    RESTX_MASK_SWAGGER = False

class DevelopmentConfig(Config):
    """Development environment specific configuration."""
    DEBUG = True
    FLASK_ENV = 'development'
    # Override database URI to ensure we use the dev database when running locally
    SQLALCHEMY_DATABASE_URI = "sqlite:///app.db" 

class TestConfig(Config):
    """Configuration for running tests."""
    TESTING = True
    # Use an in-memory SQLite database for testing to ensure isolation.
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'

class ProductionConfig(Config):
    """Configuration for production environment."""
    # Production inherits from Config, so it automatically gets SQLALCHEMY_DATABASE_URI
    # and SECRET_KEY from environment variables (DATABASE_URL and SECRET_KEY).
    DEBUG = False
    FLASK_ENV = 'production'
    # For production, we explicitly disable the simple cache, favoring null or an external service.
    CACHE_TYPE = "null" 