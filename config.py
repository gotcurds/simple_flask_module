import os

basedir = os.path.abspath(os.path.dirname(__file__))

class DevelopmentConfig:
    """Configuration for local development."""
    SQLALCHEMY_DATABASE_URI = "sqlite:///app.db"
    DEBUG = True

class Config:
    """Base configuration for the application."""
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
                              'sqlite:///' + os.path.join(basedir, 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

class TestConfig(Config):
    """Configuration for running tests."""
    TESTING = True
    # Use an in-memory SQLite database for testing to ensure isolation.
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'

class ProductionConfig:
    """Configuration for production environment."""
    pass
