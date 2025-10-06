import os
from app.models import db
from app import create_app
# Import both configuration classes
from config import DevelopmentConfig, ProductionConfig 

# --- Dynamic Configuration Selection ---
# Check the environment variable FLASK_ENV. 
# Gunicorn/Render can set this to 'production' to switch configurations.
if os.environ.get("FLASK_ENV") == "production":
    app = create_app(ProductionConfig)
else:
    # Default to DevelopmentConfig for local runs
    app = create_app(DevelopmentConfig)

# --- Database Setup and Local Run ---
if __name__ == "__main__":
    # Ensure tables are created when running the file directly
    with app.app_context():
        # Only create all tables if using SQLite (in development)
        # Production (PostgreSQL) should be handled by Alembic Migrations
        if 'sqlite' in app.config['SQLALCHEMY_DATABASE_URI']:
            db.create_all()
    
    # Get the port from environment variables or default to 5000
    port = int(os.environ.get('PORT', 5000))
    
    # Run the application with debug mode enabled for local development
    app.run(host='0.0.0.0', port=port, debug=True)