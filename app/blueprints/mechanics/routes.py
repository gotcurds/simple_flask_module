from app.blueprints.mechanics import mechanics_bp
from .schemas import mechanic_schema, mechanics_schema, login_schema
from flask import request, jsonify
from marshmallow import ValidationError
from app.models import Mechanics, db, ServiceTickets
from app.util.auth import token_required, encode_token
from werkzeug.security import check_password_hash, generate_password_hash
from sqlalchemy import func
from app.blueprints.tickets.schemas import service_tickets_schema

# NOTE: Swagger definitions (like MechResponse) have been moved to app/app_factory.py
# to resolve "Could not resolve reference" errors by making them globally available.

# Login Route for Mechanics
@mechanics_bp.route("/login", methods=["POST"])
def login():
    """
    Login a mechanic
    ---
    tags:
      - mechanics
    summary: Authenticates a mechanic and returns a JWT token.
    description: Verifies a mechanic's credentials and, if valid, generates a JSON Web Token (JWT) for authentication.
    consumes:
      - application/json
    parameters:
      - in: body
        name: body
        schema:
          $ref: '#/definitions/MechLoginPayload'
    responses:
      200:
        description: Successful login. Returns a welcome message and a JWT token.
        examples:
          application/json:
            message: "Welcome John"
            token: "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
      400:
        description: Invalid request.
      403:
        description: Invalid email or password.
    """
    try:
        data = login_schema.load(request.json)
    except ValidationError as e:
        return jsonify(e.messages), 400
    
    mechanic = db.session.query(Mechanics).where(Mechanics.email == data['email']).first()

    if mechanic and check_password_hash(mechanic.password, data['password']):
        token = encode_token(mechanic.id, role=mechanic.role)
        return jsonify({
            "message": f"Welcome {mechanic.first_name}",
            "token": token
        }), 200

    return jsonify("Invalid email or password!"), 403

# Create Mechanic Route
@mechanics_bp.route("/", methods=["POST"])
@token_required
def create_mechanic():
    """
    Create a new mechanic
    ---
    tags:
      - mechanics
    summary: Creates a new mechanic account.
    description: Only a manager can create a new mechanic account. Requires a JWT with 'manager' role.
    security:
      - token: []
    consumes:
      - application/json
    parameters:
      - in: body
        name: body
        schema:
          $ref: '#/definitions/MechCreatePayload'
    responses:
      201:
        description: Mechanic successfully created.
        schema:
          $ref: '#/definitions/MechResponse'
      400:
        description: Invalid data provided.
      403:
        description: Unauthorized to create a mechanic.
    """
    if request.role != "manager":
        return jsonify({"message": "Unauthorized to create a mechanic."}), 403

    try:
        data = mechanic_schema.load(request.json)
    except ValidationError as e:
        return jsonify(e.messages), 400

    hashed_password = generate_password_hash(data['password'])
    data['password'] = hashed_password
    
    new_mechanic = Mechanics(**data)
    
    db.session.add(new_mechanic)
    db.session.commit()
    return mechanic_schema.jsonify(new_mechanic), 201

# Get All Mechanics Route with Caching
@mechanics_bp.route("/", methods=["GET"])
def get_all_mechanics():
    """
    Get all mechanics
    ---
    tags:
      - mechanics
    summary: Retrieves a list of all mechanics.
    description: This route provides a list of all mechanics stored in the database. No authentication is required for this route.
    responses:
      200:
        description: A list of mechanics.
        schema:
          type: array
          items:
            $ref: '#/definitions/MechResponse'
    """
    mechanics = db.session.query(Mechanics).all()
    return mechanics_schema.jsonify(mechanics), 200

# Get Mechanic by ID Route
@mechanics_bp.route("/<int:mechanic_id>", methods=["GET"])
@token_required
def read_single_mechanic(mechanic_id):
    """
    Get a single mechanic
    ---
    tags:
      - mechanics
    summary: Retrieves a single mechanic by ID.
    description: This route returns detailed information for a specific mechanic using their ID.
    security:
      - token: []
    parameters:
      - name: mechanic_id
        in: path
        type: integer
        required: true
        description: The ID of the mechanic to retrieve.
    responses:
      200:
        description: Mechanic found.
        schema:
          $ref: '#/definitions/MechResponse'
      404:
        description: Mechanic not found.
    """
    mechanic = db.session.get(Mechanics, mechanic_id)
    if not mechanic:
        return jsonify({"message": "Mechanic not found."}), 404
    return mechanic_schema.jsonify(mechanic), 200

# Update Mechanic Route (Manager role required)
@mechanics_bp.route("/<int:mechanic_id>", methods=["PUT"])
@token_required
def update_mechanic(mechanic_id):
    """
    Update a mechanic
    ---
    tags:
      - mechanics
    summary: Updates an existing mechanic's details.
    description: Only a manager can update a mechanic's information. Requires a JWT with 'manager' role.
    security:
      - token: []
    parameters:
      - name: mechanic_id
        in: path
        type: integer
        required: true
        description: The ID of the mechanic to update.
      - in: body
        name: body
        schema:
          $ref: '#/definitions/MechUpdatePayload'
    responses:
      200:
        description: Mechanic updated successfully.
        schema:
          $ref: '#/definitions/MechResponse'
      400:
        description: Invalid data provided.
      403:
        description: Unauthorized to update this mechanic.
      404:
        description: Mechanic not found.
    """
    if request.role != "manager":
        return jsonify({"message": "Unauthorized to update this mechanic."}), 403
    
    mechanic = db.session.get(Mechanics, mechanic_id)
    if not mechanic:
        return jsonify({"message": "Mechanic not found."}), 404
    
    try:
        data = mechanic_schema.load(request.json, partial=True)
    except ValidationError as e:
        return jsonify(e.messages), 400
    
    if 'password' in data:
        data['password'] = generate_password_hash(data['password'])
        
    for key, value in data.items():
        setattr(mechanic, key, value)
    
    db.session.commit()
    return mechanic_schema.jsonify(mechanic), 200

# Delete Mechanic Route (Manager role required)
@mechanics_bp.route("/<int:mechanic_id>", methods=["DELETE"])
@token_required
def delete_mechanic(mechanic_id):
    """
    Delete a mechanic
    ---
    tags:
      - mechanics
    summary: Deletes a mechanic account by ID.
    description: This route allows a manager to permanently delete a mechanic's account. Requires a JWT with 'manager' role.
    security:
      - token: []
    parameters:
      - name: mechanic_id
        in: path
        type: integer
        required: true
        description: The ID of the mechanic to delete.
    responses:
      200:
        description: Mechanic successfully deleted.
        examples:
          application/json:
            message: "Successfully deleted mechanic 1."
      403:
        description: Unauthorized to delete this mechanic.
      404:
        description: Mechanic not found.
    """
    if request.role != "manager":
        return jsonify({"message": "Unauthorized to delete this mechanic."}), 403
        
    mechanic = db.session.get(Mechanics, mechanic_id)
    if not mechanic:
        return jsonify({"message": "Mechanic not found."}), 404
    
    db.session.delete(mechanic)
    db.session.commit()
    return jsonify({"message": f"Successfully deleted mechanic {mechanic_id}."}), 200

# Get Mechanic's Service Tickets
@mechanics_bp.route("/my-tickets", methods=["GET"])
@token_required
def get_my_tickets():
    """
    Get a mechanic's service tickets
    ---
    tags:
      - mechanics
    summary: Retrieves all service tickets assigned to the logged-in mechanic.
    description: This route uses the authenticated user's ID to fetch and return a list of their assigned service tickets.
    security:
      - token: []
    responses:
      200:
        description: A list of service tickets for the authenticated mechanic.
      404:
        description: No tickets found for this mechanic.
    """
    mechanic = db.session.query(Mechanics).where(Mechanics.id == request.user_id).first()
    tickets = db.session.query(ServiceTickets).join(
        ServiceTickets.mechanic
    ).where(
        Mechanics.id == mechanic.id
    ).all()
    return service_tickets_schema.jsonify(tickets), 200

# Advanced Query: Get mechanics by number of tickets worked on
@mechanics_bp.route("/top-mechanics", methods=["GET"])
def get_top_mechanics():
    """
    Get top mechanics by tickets worked
    ---
    tags:
      - mechanics
    summary: Ranks mechanics by the number of service tickets they have worked on.
    description: This route uses an advanced query to retrieve and rank all mechanics based on the count of service tickets they've been assigned.
    responses:
      200:
        description: A list of mechanics ranked by ticket count.
        examples:
          application/json:
            - id: 1
              first_name: "John"
              last_name: "Doe"
              ticket_count: 5
            - id: 2
              first_name: "Jane"
              last_name: "Smith"
              ticket_count: 3
    """
    top_mechanics = db.session.query(
        Mechanics, func.count(ServiceTickets.id).label("ticket_count")
    ).join(
        ServiceTickets.mechanic
    ).group_by(
        Mechanics.id
    ).order_by(
        func.count(ServiceTickets.id).desc()
    ).all()

    results = [
        {
            "id": mechanic.id,
            "first_name": mechanic.first_name,
            "last_name": mechanic.last_name,
            "ticket_count": row.ticket_count
        }
        for mechanic, row in top_mechanics
    ]

    return jsonify(results), 200