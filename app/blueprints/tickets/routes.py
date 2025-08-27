from app.blueprints.tickets import service_tickets_bp
from .schemas import service_ticket_schema, service_tickets_schema
from flask import request, jsonify
from marshmallow import ValidationError
from app.models import ServiceTickets, Mechanics, db

@service_tickets_bp.route("/", methods=['POST'])
def create_service_ticket():
    try:
        data = service_ticket_schema.load(request.json)
    except ValidationError as e:
        return jsonify(e.messages), 400

    new_service_ticket = ServiceTickets(**data)
    db.session.add(new_service_ticket)
    db.session.commit()
    return service_ticket_schema.jsonify(new_service_ticket), 201

@service_tickets_bp.route('/<int:ticket_id>/assign-mechanic/<int:mechanic_id>', methods=['PUT'])
def assign_mechanic(ticket_id, mechanic_id):
    ticket = db.session.get(ServiceTickets, ticket_id)
    if ticket is None:
        return jsonify({"message": "Service Ticket not found."}), 404
    mechanic = db.session.get(Mechanics, mechanic_id)
    if mechanic is None:
        return jsonify({"message": "Mechanic not found."}), 404
    ticket.mechanic.append(mechanic)
    db.session.commit()
    return jsonify({"message": f"Mechanic ID {mechanic_id} assigned to Service Ticket ID {ticket_id} successfully."}), 200

@service_tickets_bp.route('/<int:ticket_id>/remove-mechanic/<int:mechanic_id>', methods=['PUT'])
def remove_mechanic(ticket_id, mechanic_id):
    ticket = db.session.get(ServiceTickets, ticket_id)
    if ticket is None:
        return jsonify({"message": "Service Ticket not found."}), 404
    mechanic = db.session.get(Mechanics, mechanic_id)
    if mechanic is None:
        return jsonify({"message": "Mechanic not found."}), 404
    ticket.mechanic.remove(mechanic)
    db.session.commit()
    return jsonify({"message": f"Mechanic ID {mechanic_id} removed from Service Ticket ID {ticket_id} successfully."}), 200


@service_tickets_bp.route("/", methods=['GET'])
def read_service_tickets():
    service_tickets = db.session.query(ServiceTickets).all()
    return service_tickets_schema.jsonify(service_tickets), 200



