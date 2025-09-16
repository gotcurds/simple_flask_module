from app.extensions import ma
from app.models import Customers

class UserSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Customers

user_schema = UserSchema()
users_schema = UserSchema(many=True)


class UserLoginSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Customers
        only = ("email", "password")

login_schema = UserLoginSchema()