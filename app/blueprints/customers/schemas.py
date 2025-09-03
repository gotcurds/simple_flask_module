from app.extensions import ma
from app.models import Customers

class UserSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Customers

user_schema = UserSchema()
users_schema = UserSchema(many=True)
login_schema = UserSchema(exclude=['first_name', 'last_name', 'phone', 'address', 'username'])