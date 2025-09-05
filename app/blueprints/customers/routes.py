from app.blueprints.customers import customers_bp
from .schemas import user_schema, users_schema, login_schema
from flask import request, jsonify
from marshmallow import ValidationError
from app.models import Customers, db
from app.extensions import limiter
from werkzeug.security import generate_password_hash, check_password_hash
from app.util.auth import encode_token, token_required


@customers_bp.route("/login", methods=["POST"])
def login():
    try:
        data = login_schema.load(request.json)
    except ValidationError as e:
        return jsonify(e.messages), 400
    
    customer = db.session.query(Customers).where(Customers.email==data['email']).first()

    if customer and check_password_hash(customer.password, data["password"]):
        token = encode_token(customer.id, role=customer.role)
        return jsonify({
            "message": f'Welcome {customer.username}',
            "token": token
        }), 200
    
    return jsonify("Invlaid username or password!"), 403


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


@customers_bp.route("/my-profile", methods=['PUT'])
@token_required
def update_user():
    
    customer = db.session.get(Customers, request.customer_id)

    if not customer:
        return jsonify({"message": "user not found"}), 404
    
    try:
        customer_data = user_schema.load(request.json)
    except ValidationError as e:
        return jsonify({"message" : e.messages}), 400
    
    customer_data['password'] = generate_password_hash(customer_data['password'])

    for key, value in customer_data.items():
        setattr(customer, key, value)

    db.session.commit()
    return user_schema.jsonify(customer), 200


@customers_bp.route('/<int:customer_id>', methods=['DELETE'])
@limiter.limit("3 per day")
def delete_customer(customer_id):
    customer = db.session.get(Customers, customer_id)
    db.session.delete(customer)
    db.session.commit()
    return jsonify({"message": f"Successfully deleted user {customer_id}"}), 200
