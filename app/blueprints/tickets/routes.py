from app.blueprints.tickets import service_tickets_bp
from .schemas import service_ticket_schema, service_tickets_schema
from flask import request, jsonify
from marshmallow import ValidationError
from app.models import ServiceTickets, Mechanics, db, Part
from app.util.auth import encode_token, token_required

# Swag Defs
ServiceTicketPayload = {
    "ServiceTicketPayload": {
        "type": "object",
        "properties": {
            "customer_id": {"type": "integer"},
            "issue_description": {"type": "string"},
            "status": {"type": "string"}
        },
        "required": ["customer_id", "issue_description", "status"]
    }
}

ServiceTicketResponse = {
    "ServiceTicketResponse": {
        "type": "object",
        "properties": {
            "id": {"type": "integer"},
            "customer_id": {"type": "integer"},
            "issue_description": {"type": "string"},
            "status": {"type": "string"}
        }
    }
}

TicketPartResponse = {
    "TicketPartResponse": {
        "type": "object",
        "properties": {
            "part_id": {"type": "integer"},
            "description": {"type": "string"}
        }
    }
}

@service_tickets_bp.route("/", methods=['POST'])
@token_required
def create_service_ticket():
    """
    Create a new service ticket
    ---
    tags:
      - service_tickets
    summary: Creates a new service ticket.
    description: This route allows a customer or manager to create a new service ticket for an issue.
    security:
      - token: []
    consumes:
      - application/json
    parameters:
      - in: body
        name: body
        schema:
          id: ServiceTicketPayload
          $ref: '#/definitions/ServiceTicketPayload'
    responses:
      201:
        description: Service ticket successfully created.
        schema:
          $ref: '#/definitions/ServiceTicketResponse'
      400:
        description: Invalid data provided.
    """
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
    """
    Assign a mechanic to a service ticket
    ---
    tags:
      - service_tickets
    summary: Assigns a mechanic to a service ticket.
    description: A manager can use this route to assign a specific mechanic to work on a service ticket.
    security:
      - token: []
    parameters:
      - name: ticket_id
        in: path
        type: integer
        required: true
        description: The ID of the service ticket.
      - name: mechanic_id
        in: path
        type: integer
        required: true
        description: The ID of the mechanic to assign.
    responses:
      200:
        description: Mechanic assigned successfully.
        examples:
          application/json:
            message: "Mechanic ID 1 assigned to Service Ticket ID 101 successfully."
      403:
        description: Unauthorized to perform this action.
      404:
        description: Service Ticket or Mechanic not found.
    """
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
    """
    Remove a mechanic from a service ticket
    ---
    tags:
      - service_tickets
    summary: Removes a mechanic from a service ticket.
    description: This route allows a manager to unassign a mechanic from a service ticket.
    security:
      - token: []
    parameters:
      - name: ticket_id
        in: path
        type: integer
        required: true
        description: The ID of the service ticket.
      - name: mechanic_id
        in: path
        type: integer
        required: true
        description: The ID of the mechanic to remove.
    responses:
      200:
        description: Mechanic removed successfully.
        examples:
          application/json:
            message: "Mechanic ID 1 removed from Service Ticket ID 101 successfully."
      403:
        description: Unauthorized to perform this action.
      404:
        description: Service Ticket or Mechanic not found.
    """
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
    """
    Get all service tickets
    ---
    tags:
      - service_tickets
    summary: Retrieves a list of all service tickets.
    description: This route returns a list of all existing service tickets.
    security:
      - token: []
    responses:
      200:
        description: A list of service tickets.
        schema:
          type: array
          items:
            $ref: '#/definitions/ServiceTicketResponse'
    """
    service_tickets = db.session.query(ServiceTickets).all()
    return service_tickets_schema.jsonify(service_tickets), 200

@service_tickets_bp.route("/<int:ticket_id>", methods=['GET'])
@token_required
def read_single_service_ticket(ticket_id):
    """
    Get a single service ticket by ID
    ---
    tags:
      - service_tickets
    summary: Retrieves a single service ticket by its ID.
    description: This route returns details for a specific service ticket.
    security:
      - token: []
    parameters:
      - name: ticket_id
        in: path
        type: integer
        required: true
        description: The ID of the service ticket to retrieve.
    responses:
      200:
        description: Service ticket found.
        schema:
          $ref: '#/definitions/ServiceTicketResponse'
      404:
        description: Service ticket not found.
    """
    ticket = db.session.get(ServiceTickets, ticket_id)
    if not ticket:
        return jsonify({"message": "Service ticket not found"}), 404
    return service_ticket_schema.jsonify(ticket), 200

@service_tickets_bp.route("/<int:ticket_id>/add-part/<int:part_id>", methods=['PUT'])
@token_required
def add_part_to_ticket(ticket_id, part_id):
    """
    Add a part to a service ticket
    ---
    tags:
      - service_tickets
    summary: Adds a physical part to a service ticket.
    description: A manager can use this route to associate a physical part with a service ticket, indicating it was used for the repair.
    security:
      - token: []
    parameters:
      - name: ticket_id
        in: path
        type: integer
        required: true
        description: The ID of the service ticket.
      - name: part_id
        in: path
        type: integer
        required: true
        description: The ID of the physical part to add.
    responses:
      200:
        description: Part added successfully.
        examples:
          application/json:
            message: "Successfully added part 1 to service ticket 101."
      403:
        description: Unauthorized to add a part.
      404:
        description: Service Ticket or Part not found.
    """
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
    """
    Get parts associated with a service ticket
    ---
    tags:
      - service_tickets
    summary: Retrieves all parts associated with a service ticket.
    description: This route returns a list of all physical parts that have been added to a specific service ticket.
    security:
      - token: []
    parameters:
      - name: ticket_id
        in: path
        type: integer
        required: true
        description: The ID of the service ticket.
    responses:
      200:
        description: Parts retrieved successfully.
        schema:
          type: array
          items:
            $ref: '#/definitions/TicketPartResponse'
      404:
        description: Service ticket not found.
    """
    ticket = db.session.get(ServiceTickets, ticket_id)
    if not ticket:
        return jsonify({"message": "Service ticket not found."}), 404

    parts_list = [
        {"part_id": part.id, "description": part.inventory_description.name}
        for part in ticket.parts
    ]
    
    return jsonify(parts_list), 200

