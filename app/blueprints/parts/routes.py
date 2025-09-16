from app.blueprints.parts import parts_bp
from .schemas import inventory_part_description_schema, inventory_part_descriptions_schema
from flask import request, jsonify
from marshmallow import ValidationError
from app.models import InventoryPartDescription, db, Part
from app.util.auth import token_required

@parts_bp.route("/", methods=['POST'])
@token_required
def create_part():
    # Security check: Only a manager can add parts
    if request.role != "manager":
        return jsonify({"message": "Unauthorized to create a new part."}), 403
        
    try:
        data = inventory_part_description_schema.load(request.json)
    except ValidationError as e:
        return jsonify(e.messages), 400

    new_part = InventoryPartDescription(**data)
    
    db.session.add(new_part)
    db.session.commit()
    return inventory_part_description_schema.jsonify(new_part), 201

@parts_bp.route("/", methods=['GET'])
def read_parts():
    parts = db.session.query(InventoryPartDescription).all()
    return inventory_part_descriptions_schema.jsonify(parts), 200

@parts_bp.route("/<int:part_id>", methods=['GET'])
def get_part(part_id):
    part = db.session.get(InventoryPartDescription, part_id)
    if not part:
        return jsonify({"message": "Part not found"}), 404
    return inventory_part_description_schema.jsonify(part), 200

@parts_bp.route("/<int:part_id>", methods=['PUT'])
@token_required
def update_part(part_id):
    # Security check: Only a manager can update parts
    if request.role != "manager":
        return jsonify({"message": "Unauthorized to update this part."}), 403

    part = db.session.get(InventoryPartDescription, part_id)
    if not part:
        return jsonify({"message": "Part not found"}), 404
    
    try:
        part_data = inventory_part_description_schema.load(request.json, partial=True)
    except ValidationError as e:
        return jsonify({"message": e.messages}), 400

    for key, value in part_data.items():
        setattr(part, key, value)
    
    db.session.commit()
    return inventory_part_description_schema.jsonify(part), 200

@parts_bp.route("/<int:part_id>", methods=['DELETE'])
@token_required
def delete_part(part_id):
    # Security check: Only a manager can delete parts
    if request.role != "manager":
        return jsonify({"message": "Unauthorized to delete this part."}), 403
    
    part = db.session.get(InventoryPartDescription, part_id)
    if not part:
        return jsonify({"message": "Part not found"}), 404
    
    db.session.delete(part)
    db.session.commit()
    return jsonify({"message": f"Successfully deleted part {part_id}"}), 200

@parts_bp.route("/add-physical-part", methods=['POST'])
@token_required
def create_physical_part():
    if request.role != "manager":
        return jsonify({"message": "Unauthorized to add a physical part."}), 403
    
    try:
        data = request.json
        desc_id = data.get('desc_id')
    except Exception:
        return jsonify({"message": "Invalid request body."}), 400
        
    inventory_description = db.session.get(InventoryPartDescription, desc_id)
    if not inventory_description:
        return jsonify({"message": "Inventory description not found"}), 404
        
    new_part = Part(inventory_description=inventory_description)
    db.session.add(new_part)
    db.session.commit()
    return jsonify({"message": f"Successfully created physical part with ID {new_part.id}."}), 201
