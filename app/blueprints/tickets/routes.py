from app.blueprints.tickets import service_tickets_bp
from .schemas import service_ticket_schema, service_tickets_schema
from flask import request, jsonify
from marshmallow import ValidationError
from app.models import ServiceTickets, Mechanics, db, Part
from app.util.auth import encode_token, token_required

@service_tickets_bp.route("/", methods=['POST'])
@token_required
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
@token_required
def assign_mechanic(ticket_id, mechanic_id):
    ticket = db.session.get(ServiceTickets, ticket_id)
    if request.role != "manager":
        return jsonify({"message": "You are not a manager."}), 403 
    if ticket is None:
        return jsonify({"message": "Service Ticket not found."}), 404
    mechanic = db.session.get(Mechanics, mechanic_id)
    if mechanic is None:
        return jsonify({"message": "Mechanic not found."}), 404
    ticket.mechanic.append(mechanic)
    db.session.commit()
    return jsonify({"message": f"Mechanic ID {mechanic_id} assigned to Service Ticket ID {ticket_id} successfully."}), 200

@service_tickets_bp.route('/<int:ticket_id>/remove-mechanic/<int:mechanic_id>', methods=['PUT'])
@token_required
def remove_mechanic(ticket_id, mechanic_id):
    ticket = db.session.get(ServiceTickets, ticket_id)
    if request.role != "manager":
        return jsonify({"message": "You are not a manager."}), 403
    if ticket is None:
        return jsonify({"message": "Service Ticket not found."}), 404
    mechanic = db.session.get(Mechanics, mechanic_id)
    if mechanic is None:
        return jsonify({"message": "Mechanic not found."}), 404
    ticket.mechanic.remove(mechanic)
    db.session.commit()
    return jsonify({"message": f"Mechanic ID {mechanic_id} removed from Service Ticket ID {ticket_id} successfully."}), 200


@service_tickets_bp.route("/", methods=['GET'])
@token_required
def read_service_tickets():
    service_tickets = db.session.query(ServiceTickets).all()
    return service_tickets_schema.jsonify(service_tickets), 200

@service_tickets_bp.route("/<int:ticket_id>", methods=['GET'])
@token_required
def read_single_service_ticket(ticket_id):
    ticket = db.session.get(ServiceTickets, ticket_id)
    if not ticket:
        return jsonify({"message": "Service ticket not found"}), 404
    return service_ticket_schema.jsonify(ticket), 200

@service_tickets_bp.route("/<int:ticket_id>/add-part/<int:part_id>", methods=['PUT'])
@token_required
def add_part_to_ticket(ticket_id, part_id):
    if request.role != "manager":
        return jsonify({"message": "Unauthorized to add a part to this ticket."}), 403
    
    ticket = db.session.get(ServiceTickets, ticket_id)
    if not ticket:
        return jsonify({"message": "Service Ticket not found."}), 404
    
    part = db.session.get(Part, part_id)
    if not part:
        return jsonify({"message": "Part not found."}), 404
        
    ticket.parts.append(part)
    db.session.commit()
    return jsonify({"message": f"Successfully added part {part_id} to service ticket {ticket_id}."}), 200

@service_tickets_bp.route("/<int:ticket_id>/parts", methods=['GET'])
@token_required
def read_ticket_parts(ticket_id):
    ticket = db.session.get(ServiceTickets, ticket_id)
    if not ticket:
        return jsonify({"message": "Service ticket not found."}), 404

    parts_list = [
        {"part_id": part.id, "description": part.inventory_description.name}
        for part in ticket.parts
    ]
    
    return jsonify(parts_list), 200

