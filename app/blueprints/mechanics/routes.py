from app.blueprints.mechanics import mechanics_bp
from .schemas import mechanic_schema, mechanics_schema, login_schema
from flask import request, jsonify
from marshmallow import ValidationError
from app.models import Mechanics, db, ServiceTickets
from app.util.auth import token_required, encode_token
from werkzeug.security import check_password_hash
from sqlalchemy import func
from app.blueprints.tickets.schemas import service_tickets_schema

# Login Route for Mechanics
@mechanics_bp.route("/login", methods=["POST"])
def login():
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
def create_mechanic():
    try:
        data = mechanic_schema.load(request.json)
    except ValidationError as e:
        return jsonify(e.messages), 400

    new_mechanic = Mechanics(**data)
    db.session.add(new_mechanic)
    db.session.commit()
    return mechanic_schema.jsonify(new_mechanic), 201

# Get All Mechanics Route with Caching
@mechanics_bp.route("/", methods=["GET"])
def get_all_mechanics():
    mechanics = db.session.query(Mechanics).all()
    return mechanics_schema.jsonify(mechanics), 200

# Get Mechanic by ID Route
@mechanics_bp.route("/<int:mechanic_id>", methods=["GET"])
def get_mechanic(mechanic_id):
    mechanic = db.session.get(Mechanics, mechanic_id)
    return mechanic_schema.jsonify(mechanic), 200

# Update Mechanic Route (Manager role required)
@mechanics_bp.route("/<int:mechanic_id>", methods=["PUT"])
@token_required
def update_mechanic(mechanic_id):
    if request.role != "manager":
        return jsonify({"message": "You are not a manager."}), 403

    mechanic = db.session.get(Mechanics, mechanic_id)
    if not mechanic:
        return jsonify({"message": "Mechanic not found"}), 404

    try:
        mechanic_data = mechanic_schema.load(request.json, partial=True)
    except ValidationError as e:
        return jsonify(e.messages), 400

    for key, value in mechanic_data.items():
        setattr(mechanic, key, value)

    db.session.commit()
    return mechanic_schema.jsonify(mechanic), 200

# Delete Mechanic Route (Manager role required)
@mechanics_bp.route("/<int:mechanic_id>", methods=["DELETE"])
@token_required
def delete_mechanic(mechanic_id):
    if request.role != "manager":
        return jsonify({"message": "You are not a manager."}), 403
    
    mechanic = db.session.get(Mechanics, mechanic_id)
    if not mechanic:
        return jsonify({"message": "Mechanic not found"}), 404
    db.session.delete(mechanic)
    db.session.commit()
    return jsonify({"message": f"Mechanic {mechanic_id} successfully deleted"}), 200

# Get Mechanic's Service Tickets
@mechanics_bp.route("/my-tickets", methods=["GET"])
@token_required
def get_my_tickets():
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