from app.models import db
from app import create_app
import os
from app import create_app
from config import DevelopmentConfig

app = create_app(DevelopmentConfig)

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)