from app.blueprints.mechanics import mechanics_bp
from .schemas import mechanic_schema, mechanics_schema, login_schema
from flask import request, jsonify
from marshmallow import ValidationError
from app.models import Mechanics, db, ServiceTickets
from werkzeug.security import generate_password_hash, check_password_hash
from app.util.auth import encode_token, token_required
from app.blueprints.tickets.schemas import service_tickets_schema


@mechanics_bp.route("/", methods=['POST'])
def create_mechanic():
    try:
        data = mechanic_schema.load(request.json)
    except ValidationError as e:
        return jsonify(e.messages), 400

    new_mechanic = Mechanics(**data)
    db.session.add(new_mechanic)
    db.session.commit()
    return mechanic_schema.jsonify(new_mechanic), 201

@mechanics_bp.route("/", methods=['GET'])
def read_mechanics():
    mechanics = db.session.query(Mechanics).all()
    return mechanics_schema.jsonify(mechanics), 200

@mechanics_bp.route("/<int:mechanic_id>", methods=['PUT'])
def update_mechanic(mechanic_id):
    mechanic_id = request.mechanic_id
    mechanic = db.session.get(Mechanics, mechanic_id)

    if not mechanic:
        return jsonify({"message": "user not found"}), 404
    
    try:
        mechanic_data = mechanic_schema.load(request.json)
    except ValidationError as e:
        return jsonify({"message" : e.messages}), 400
    
    # mechanic_data['password'] = generate_password_hash(mechanic_data['password'])

    for key, value in mechanic_data.items():
        setattr(mechanic, key, value)

    db.session.commit()
    return mechanic_schema.jsonify(mechanic), 200


@mechanics_bp.route("/<int:mechanic_id>", methods=['DELETE'])
def delete_mechanics(mechanic_id):
    mechanic = db.session.get(Mechanics, mechanic_id)
    db.session.delete(mechanic)
    db.session.commit()
    return jsonify({"message": f"Successfully deleted user {mechanic_id}"}), 200
    

@mechanics_bp.route("/login", methods=["POST"])
def login():
    try:
        data = login_schema.load(request.json)
    except ValidationError as e:
        return jsonify(e.messages), 400
    
    mechanic = db.session.query(Mechanics).where(Mechanics.email==data['email']).first()

    if mechanic and check_password_hash(mechanic.password, data["password"]):
        token = encode_token(mechanic.id, role=mechanic.role)
        return jsonify({
            "message": f'Welcome {mechanic.username}',
            "token": token
        }), 200
    
    return jsonify("Invlaid username or password!"), 403



@mechanics_bp.route("/my-tickets", methods=['GET'])
@token_required
def get_tickets():

    service_tickets = db.session.query(ServiceTickets).filter(ServiceTickets.mechanic_id == request.mechanic_id).all()

    if not service_tickets:
        return jsonify({"message": "No service tickets found for this mechanic."}), 404
    
    return service_tickets_schema.jsonify(service_tickets), 200