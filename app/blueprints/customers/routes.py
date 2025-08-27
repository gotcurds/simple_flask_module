from app.blueprints.customers import customers_bp
from .schemas import user_schema, users_schema
from flask import request, jsonify
from marshmallow import ValidationError
from app.models import Customers, db

@customers_bp.route("/", methods=['POST'])
def create_customer():
    try:
        data = user_schema.load(request.json)
    except ValidationError as e:
        return jsonify(e.messages), 400

    new_customer = Customers(**data)
    db.session.add(new_customer)
    db.session.commit()
    return user_schema.jsonify(new_customer), 201

@customers_bp.route("/", methods=['GET'])
def read_customers():
    customers = db.session.query(Customers).all()
    return users_schema.jsonify(customers), 200
    


@customers_bp.route('/<int:customer_id>', methods=['GET'])
def read_customer(customer_id):
    customer = db.session.get(Customers, customer_id)
    return user_schema.jsonify(customer), 200


@customers_bp.route('/<int:customer_id>', methods=['DELETE'])
def delete_customer(customer_id):
    customer = db.session.get(Customers, customer_id)
    db.session.delete(customer)
    db.session.commit()
    return jsonify({"message": f"Successfully deleted user {customer_id}"}), 200
