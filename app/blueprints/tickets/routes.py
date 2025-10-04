from app.blueprints.tickets import service_tickets_bp
from .schemas import service_ticket_schema, service_tickets_schema
from flask import request, jsonify
from marshmallow import ValidationError
# Assuming these model names based on the file provided
from app.models import ServiceTickets, Mechanics, db, Part 
from app.util.auth import encode_token, token_required

# --- Constants ---
FLAT_LABOR_CHARGE = 150.00
ALLOWED_STATUSES = ["Pending", "Assigned", "In Progress", "Awaiting Parts", "Complete", "Cancelled"]

# The blueprint documentation includes the definitions the Swagger UI requires.
service_tickets_bp.config = {
    "specs": [
        {
            "endpoint": 'ticketspec',
            "route": '/ticketspec.json',
            "rule_filter": lambda rule: rule.endpoint.startswith(service_tickets_bp.name),
            "model_filter": lambda tag: True,
        }
    ],
    "definitions": {
        "ServiceTicketPayload": {
            "type": "object",
            "properties": {
                "customer_id": {"type": "integer"},
                "issue_description": {"type": "string"},
                "status": {"type": "string", "enum": ALLOWED_STATUSES}
            },
            "required": ["customer_id", "issue_description", "status"]
        },
        "ServiceTicketResponse": {
            "type": "object",
            "properties": {
                "id": {"type": "integer"},
                "customer_id": {"type": "integer"},
                "issue_description": {"type": "string"},
                "status": {"type": "string"},
                "price": {"type": "number", "format": "float", "description": "Final calculated price of the service."}
            }
        },
        "TicketStatusUpdatePayload": {
            "type": "object",
            "properties": {
                "status": {"type": "string", "enum": ["In Progress", "Awaiting Parts", "Complete", "Cancelled"], "description": "New status for the ticket."},
            },
            "required": ["status"]
        },
        "TicketPartResponse": {
            "type": "object",
            "properties": {
                "part_id": {"type": "integer"},
                "description": {"type": "string"}
            }
        }
    }
}

# --- Route Implementations (Rest of the file remains the same) ---

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
    Assign a mechanic to a service ticket (Manager Only)
    ---
    tags:
      - service_tickets
    summary: Assigns a mechanic to a service ticket.
    description: A manager can use this route to assign a specific mechanic and set the ticket status to 'Assigned'.
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
    
    # Core business logic: Assign and update status
    ticket.mechanic.append(mechanic)
    ticket.status = "Assigned"
    
    db.session.commit()
    return jsonify({"message": f"Mechanic ID {mechanic_id} assigned to Service Ticket ID {ticket_id} successfully. Status set to 'Assigned'."}), 200

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
    
    # Ensure mechanic is in the list before trying to remove to prevent ValueError
    if mechanic in ticket.mechanic:
        ticket.mechanic.remove(mechanic)
        db.session.commit()
        return jsonify({"message": f"Mechanic ID {mechanic_id} removed from Service Ticket ID {ticket_id} successfully."}), 200
    else:
        # Return 404 if the mechanic was not assigned
        return jsonify({"message": f"Mechanic ID {mechanic_id} was not assigned to Service Ticket ID {ticket_id}."}), 404


@service_tickets_bp.route("/<int:ticket_id>/status", methods=["PUT"])
@token_required
def update_ticket_status(ticket_id):
    """
    Update Service Ticket Status (Mechanic/Manager)
    ---
    tags:
      - service_tickets
    summary: Updates the status of a service ticket.
    description: Accessible by mechanics and managers. If the status is set to 'Complete', the final price (Parts Cost + Labor) is calculated and stored.
    security:
      - token: []
    parameters:
      - name: ticket_id
        in: path
        type: integer
        required: true
        description: The ID of the service ticket to update.
      - in: body
        name: body
        schema:
          $ref: '#/definitions/TicketStatusUpdatePayload'
    responses:
      200:
        description: Ticket status successfully updated.
        schema:
          $ref: '#/definitions/ServiceTicketResponse'
      400:
        description: Invalid status value provided.
      403:
        description: User is not authorized (Not a Mechanic or Manager).
      404:
        description: Service ticket not found.
    """
    # Check authorization (Mechanic or Manager)
    if request.role not in ["mechanic", "manager"]:
        return jsonify({"message": "Unauthorized. Must be a mechanic or manager to update ticket status."}), 403

    ticket = db.session.get(ServiceTickets, ticket_id)
    if not ticket:
        return jsonify({"message": "Service ticket not found."}), 404

    try:
        data = request.json
        new_status = data.get("status")
        
        # Validate status
        if not new_status or new_status not in ALLOWED_STATUSES:
            return jsonify({"message": f"Invalid or missing status. Allowed values are: {', '.join(ALLOWED_STATUSES)}"}), 400

        # --- FINAL PRICE CALCULATION LOGIC ---
        if new_status == "Complete" and ticket.status != "Complete":
            # 1. Calculate total cost of parts attached to the ticket
            # Assuming 'Part' model has a 'price' attribute
            total_parts_cost = sum(part.price for part in ticket.parts)
            
            # 2. Calculate final price
            final_price = total_parts_cost + FLAT_LABOR_CHARGE

            # 3. Update the ticket price
            ticket.price = final_price
            
        # Update the status
        ticket.status = new_status
        db.session.commit()

        return service_ticket_schema.jsonify(ticket), 200

    except Exception as e:
        # A specific error could be raised if 'part.price' is None or not a number, 
        # but catching the general exception protects the transaction.
        print(f"Error during status update/price calculation: {e}")
        db.session.rollback()
        return jsonify({"message": "An error occurred during status update."}), 500


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
    Add a part to a service ticket (Manager Only)
    ---
    tags:
      - service_tickets
    summary: Adds a physical part to a service ticket and decrements inventory.
    description: A manager uses this route to associate a part with a ticket. The part's inventory count is decremented automatically.
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
        description: Part added successfully and inventory updated.
      400:
        description: Part is out of stock.
      403:
        description: Unauthorized to add a part.
      404:
        description: Service Ticket or Part not found.
    """
    if request.role != "manager":
        return jsonify({"message": "Unauthorized to add a part to this ticket. Must be a manager."}), 403
    
    ticket = db.session.get(ServiceTickets, ticket_id)
    if not ticket:
        return jsonify({"message": "Service Ticket not found."}), 404
    
    part = db.session.get(Part, part_id)
    if not part:
        return jsonify({"message": "Part not found."}), 404
    
    # Check inventory before adding
    # Assuming the Part model has an 'inventory_count' attribute
    if part.inventory_count <= 0: 
        return jsonify({"message": f"Part ID {part_id} is out of stock."}), 400
        
    ticket.parts.append(part)
    part.inventory_count -= 1 # Crucial inventory decrement
    
    db.session.commit()
    return jsonify({"message": f"Successfully added part {part_id} to service ticket {ticket_id}. Inventory count decremented."}), 200

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

    # FIX: Added a check for part.inventory_description existence to prevent an AttributeError
    # (a common "pointer error" when a relationship isn't properly loaded or is NULL).
    parts_list = [
        {
            "part_id": part.id, 
            "description": part.inventory_description.name if part.inventory_description else "Description N/A"
        }
        for part in ticket.parts
    ]
    
    return jsonify(parts_list), 200

