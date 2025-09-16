from app.extensions import ma
from app.models import Mechanics

class MechanicSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Mechanics
        load_instance = False

mechanic_schema = MechanicSchema()
mechanics_schema = MechanicSchema(many=True)

class MechanicLoginSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Mechanics
        only = ("email", "password")

login_schema = MechanicLoginSchema()