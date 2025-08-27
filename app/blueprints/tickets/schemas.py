from app.extensions import ma
from app.models import ServiceTickets
from app.blueprints.mechanics.schemas import MechanicSchema

class ServiceTicketSchema(ma.SQLAlchemyAutoSchema):
    mechanics = ma.Nested(MechanicSchema, many=True)
    class Meta:
        model = ServiceTickets
        include_fk = True

service_ticket_schema = ServiceTicketSchema()
service_tickets_schema = ServiceTicketSchema(many=True)