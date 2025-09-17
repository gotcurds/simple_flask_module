from flask import request, jsonify
from marshmallow import ValidationError
from app.models import InventoryPartDescription, Part, db
from app.util.auth import token_required
from . import parts_bp
from .schemas import inventory_part_description_schema, part_schema, parts_schema, inventory_part_descriptions_schema


# Swag Defs
# Create/Update Payload for Part Descriptions
PartDescriptionPayload = {
    "PartDescriptionPayload": {
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "price": {"type": "number"},
            "supplier_id": {"type": "integer"},
            "inventory_count": {"type": "integer"}
        },
        "required": ["name", "price", "supplier_id", "inventory_count"]
    }
}

# Payload for adding a physical part
PhysicalPartPayload = {
    "PhysicalPartPayload": {
        "type": "object",
        "properties": {
            "desc_id": {"type": "integer"}
        },
        "required": ["desc_id"]
    }
}

# Response for a single Part Description
PartDescriptionResponse = {
    "PartDescriptionResponse": {
        "type": "object",
        "properties": {
            "id": {"type": "integer"},
            "name": {"type": "string"},
            "price": {"type": "number"},
            "supplier_id": {"type": "integer"},
            "inventory_count": {"type": "integer"}
        }
    }
}

# Response for a single physical Part
PartResponse = {
    "PartResponse": {
        "type": "object",
        "properties": {
            "id": {"type": "integer"},
            "desc_id": {"type": "integer"}
        }
    }
}

@parts_bp.route("/", methods=["POST"])
@token_required
def create_inventory_part_description():
    """
    Create a new inventory part description
    ---
    tags:
      - parts
    summary: Creates a new part description in the inventory.
    description: This route allows a manager to add a new part type to the inventory, including its name, price, and supplier. Requires a manager role.
    security:
      - token: []
    consumes:
      - application/json
    parameters:
      - in: body
        name: body
        schema:
          id: PartDescriptionPayload
          $ref: '#/definitions/PartDescriptionPayload'
    responses:
      201:
        description: Part description successfully created.
        schema:
          $ref: '#/definitions/PartDescriptionResponse'
      400:
        description: Invalid data provided.
      403:
        description: Unauthorized to create a new part.
    """
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


@parts_bp.route("/add-physical-part", methods=["POST"])
@token_required
def add_physical_part():
    """
    Add a new physical part to inventory
    ---
    tags:
      - parts
    summary: Adds a new physical part instance to the inventory.
    description: This route creates a physical part that corresponds to an existing part description. It increases the count of a part. Requires a manager role.
    security:
      - token: []
    consumes:
      - application/json
    parameters:
      - in: body
        name: body
        schema:
          id: PhysicalPartPayload
          $ref: '#/definitions/PhysicalPartPayload'
    responses:
      201:
        description: Physical part successfully created.
        examples:
          application/json:
            message: "Successfully created physical part with ID 1."
      400:
        description: Missing required data (desc_id).
      403:
        description: Unauthorized to add a new physical part.
      404:
        description: Inventory description not found.
      500:
        description: An error occurred.
    """
    if request.role != "manager":
        return jsonify({"message": "Unauthorized to add a new physical part."}), 403

    try:
        data = request.json
        desc_id = data.get("desc_id")
        if not desc_id:
            return jsonify({"message": "desc_id is required."}), 400

        inventory_desc = db.session.get(InventoryPartDescription, desc_id)
        if not inventory_desc:
            return jsonify({"message": "Inventory description not found."}), 404

        new_physical_part = Part(desc_id=desc_id)
        db.session.add(new_physical_part)
        db.session.commit()
        return jsonify({"message": f"Successfully created physical part with ID {new_physical_part.id}."}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "An error occurred.", "error": str(e)}), 500


@parts_bp.route("/", methods=["GET"])
def read_all_parts():
    """
    Get all physical parts
    ---
    tags:
      - parts
    summary: Retrieves a list of all physical parts in the inventory.
    description: This route returns a list of all part instances. It does not require authentication.
    responses:
      200:
        description: A list of all physical parts.
        schema:
          type: array
          items:
            $ref: '#/definitions/PartResponse'
    """
    parts = db.session.query(Part).all()
    return parts_schema.jsonify(parts), 200


@parts_bp.route("/<int:part_id>", methods=["GET"])
def read_single_part(part_id):
    """
    Get a single physical part by ID
    ---
    tags:
      - parts
    summary: Retrieves a single physical part by its ID.
    description: This route returns details for a specific physical part using its unique ID.
    parameters:
      - name: part_id
        in: path
        type: integer
        required: true
        description: The ID of the part to retrieve.
    responses:
      200:
        description: Part found.
        schema:
          $ref: '#/definitions/PartResponse'
      404:
        description: Part not found.
    """
    part = db.session.get(Part, part_id)
    if not part:
        return jsonify({"message": "Part not found."}), 404
    return part_schema.jsonify(part), 200


@parts_bp.route("/<int:part_id>", methods=["PUT"])
@token_required
def update_part(part_id):
    """
    Update a physical part's description
    ---
    tags:
      - parts
    summary: Updates the part description associated with a physical part.
    description: This route allows a manager to change the type of a physical part, such as reclassifying it. Requires a manager role.
    security:
      - token: []
    parameters:
      - name: part_id
        in: path
        type: integer
        required: true
        description: The ID of the part to update.
      - in: body
        name: body
        schema:
          id: PhysicalPartPayload
          $ref: '#/definitions/PhysicalPartPayload'
    responses:
      200:
        description: Part updated successfully.
        schema:
          $ref: '#/definitions/PartResponse'
      400:
        description: Invalid data provided.
      403:
        description: Unauthorized to update this part.
      404:
        description: Part or Inventory description not found.
      500:
        description: An error occurred.
    """
    if request.role != "manager":
        return jsonify({"message": "Unauthorized to update this part."}), 403

    part_to_update = db.session.get(Part, part_id)
    if not part_to_update:
        return jsonify({"message": "Part not found."}), 404

    try:
        data = request.json
        desc_id = data.get("desc_id")
        if not desc_id:
            return jsonify({"message": "desc_id is required to update a part."}), 400

        inventory_desc = db.session.get(InventoryPartDescription, desc_id)
        if not inventory_desc:
            return jsonify({"message": "Inventory description for update not found."}), 404

        part_to_update.desc_id = desc_id
        db.session.commit()
        return part_schema.jsonify(part_to_update), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "An error occurred.", "error": str(e)}), 500


@parts_bp.route("/<int:part_id>", methods=["DELETE"])
@token_required
def delete_part(part_id):
    """
    Delete a physical part
    ---
    tags:
      - parts
    summary: Deletes a physical part from the inventory.
    description: This route removes a single physical part by its ID. Requires a manager role.
    security:
      - token: []
    parameters:
      - name: part_id
        in: path
        type: integer
        required: true
        description: The ID of the part to delete.
    responses:
      200:
        description: Part successfully deleted.
        examples:
          application/json:
            message: "Successfully deleted part 1."
      403:
        description: Unauthorized to delete this part.
      404:
        description: Part not found.
    """
    if request.role != "manager":
        return jsonify({"message": "Unauthorized to delete this part."}), 403

    part_to_delete = db.session.get(Part, part_id)
    if not part_to_delete:
        return jsonify({"message": "Part not found."}), 404

    db.session.delete(part_to_delete)
    db.session.commit()
    return jsonify({"message": f"Successfully deleted part {part_id}."}), 200

