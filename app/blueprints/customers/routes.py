from app.blueprints.customers import customers_bp
from .schemas import user_schema, users_schema, login_schema
from flask import request, jsonify
from marshmallow import ValidationError
from app.models import Customers, db, ServiceTickets
from app.extensions import limiter
from werkzeug.security import generate_password_hash, check_password_hash
from app.util.auth import encode_token, token_required
from sqlalchemy import func

# Swag Defs
LoginPayload = {
    "LoginPayload": {
        "type": "object",
        "properties": {
            "email": {"type": "string"},
            "password": {"type": "string"}
        },
        "required": ["email", "password"]
    }
}

CustomerPayload = {
    "CustomerPayload": {
        "type": "object",
        "properties": {
            "first_name": {"type": "string"},
            "last_name": {"type": "string"},
            "email": {"type": "string"},
            "password": {"type": "string"}
        },
        "required": ["first_name", "last_name", "email", "password"]
    }
}

CustomerResponse = {
    "CustomerResponse": {
        "type": "object",
        "properties": {
            "id": {"type": "integer"},
            "first_name": {"type": "string"},
            "last_name": {"type": "string"},
            "email": {"type": "string"}
        }
    }
}

TopSpenderResponse = {
    "TopSpenderResponse": {
        "type": "object",
        "properties": {
            "first_name": {"type": "string"},
            "last_name": {"type": "string"},
            "total_spent": {"type": "number"}
        }
    }
}


@customers_bp.route("/login", methods=["POST"])
def login():
    """
    Log in a customer
    ---
    tags:
      - customers
    summary: Authenticates a customer and returns an access token.
    description: This route validates a customer's email and password, and if they are correct, issues a JWT for future authenticated requests.
    consumes:
      - application/json
    parameters:
      - in: body
        name: body
        schema:
          id: LoginPayload
          $ref: '#/definitions/LoginPayload'
    responses:
      200:
        description: Login successful. Returns a welcome message and a JWT token.
        examples:
          application/json:
            message: "Welcome Jane"
            token: "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
      400:
        description: Invalid data provided.
      403:
        description: Invalid username or password.
    """
    try:
        data = login_schema.load(request.json)
    except ValidationError as e:
        return jsonify(e.messages), 400
    
    customer = db.session.query(Customers).where(Customers.email==data['email']).first()

    if customer and check_password_hash(customer.password, data["password"]):
        token = encode_token(customer.id, role="customer")
        return jsonify({
            "message": f'Welcome {customer.first_name}',
            "token": token
        }), 200
    
    return jsonify("Invalid username or password!"), 403


@customers_bp.route("/", methods=['POST'])
def create_customer():
    """
    Create a new customer
    ---
    tags:
      - customers
    summary: Registers a new customer account.
    description: This route allows a new customer to create an account by providing their personal information and a password.
    consumes:
      - application/json
    parameters:
      - in: body
        name: body
        schema:
          id: CustomerPayload
          $ref: '#/definitions/CustomerPayload'
    responses:
      201:
        description: Customer successfully created.
        schema:
          $ref: '#/definitions/CustomerResponse'
      400:
        description: Invalid data provided.
    """
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
    """
    Get all customers
    ---
    tags:
      - customers
    summary: Retrieves a paginated list of all customers.
    description: This route returns a list of all customer accounts, with optional pagination to handle large datasets.
    parameters:
      - name: page
        in: query
        type: integer
        default: 1
        description: The page number to retrieve.
      - name: per_page
        in: query
        type: integer
        default: 20
        description: The number of customers per page.
    responses:
      200:
        description: A paginated list of customers.
        schema:
          type: array
          items:
            $ref: '#/definitions/CustomerResponse'
    """
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 20))

    customers = db.session.query(Customers).paginate(page,per_page)
    return users_schema.jsonify(customers.items), 200
    

@customers_bp.route('/<int:customer_id>', methods=['GET'])
def read_customer(customer_id):
    """
    Get a single customer by ID
    ---
    tags:
      - customers
    summary: Retrieves a single customer by their unique ID.
    description: This route returns detailed information for a specific customer.
    parameters:
      - name: customer_id
        in: path
        type: integer
        required: true
        description: The ID of the customer to retrieve.
    responses:
      200:
        description: Customer found.
        schema:
          $ref: '#/definitions/CustomerResponse'
      404:
        description: Customer not found.
    """
    customer = db.session.get(Customers, customer_id)
    if not customer:
        return jsonify({"message": "customer not found"}), 404
    return user_schema.jsonify(customer), 200


@customers_bp.route("/my-profile", methods=['PUT'])
@token_required
def update_user():
    """
    Update the authenticated customer's profile
    ---
    tags:
      - customers
    summary: Updates the currently logged-in customer's profile.
    description: This route allows a customer to update their own account information, including name, email, and password.
    security:
      - token: []
    consumes:
      - application/json
    parameters:
      - in: body
        name: body
        schema:
          $ref: '#/definitions/CustomerPayload'
    responses:
      200:
        description: Customer profile successfully updated.
        schema:
          $ref: '#/definitions/CustomerResponse'
      400:
        description: Invalid data provided.
      404:
        description: Customer not found.
    """
    
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
@token_required
def delete_customer(customer_id):
    """
    Delete a customer account
    ---
    tags:
      - customers
    summary: Deletes a customer account by ID.
    description: This route allows a customer to delete their own account. It is protected by a rate limit of 3 deletions per day per IP.
    security:
      - token: []
    parameters:
      - name: customer_id
        in: path
        type: integer
        required: true
        description: The ID of the customer account to delete.
    responses:
      200:
        description: Customer successfully deleted.
        examples:
          application/json:
            message: "Successfully deleted user 101"
      403:
        description: Unauthorized to delete this account.
      404:
        description: Customer not found.
    """
    customer = db.session.get(Customers, customer_id)
    if not customer:
        return jsonify({"message": "that customer is not in the database"}), 404
    
    if customer_id != int(request.user_id):
        return jsonify({"message": "we're sorry it seems as if you don't have access to that account."}), 403
    else:
        db.session.delete(customer)
        db.session.commit()
        return jsonify({"message": f"Successfully deleted user {customer_id}"}), 200


@customers_bp.route("/big-spenders", methods=["GET"])
def get_top_customers():
    """
    Get top spending customers
    ---
    tags:
      - customers
    summary: Retrieves a list of the top customers by total spending.
    description: This route queries the database to find the customers with the highest total value of service tickets, providing a "big spenders" report.
    responses:
      200:
        description: A list of the top spending customers.
        schema:
          type: array
          items:
            $ref: '#/definitions/TopSpenderResponse'
    """
    # group by customer, sum the prices, and order by the total sum.
    customer_data = db.session.query(
        Customers.first_name,
        Customers.last_name,
        func.sum(ServiceTickets.price).label("total_spent")).join(ServiceTickets).group_by(Customers.id).order_by(func.sum(ServiceTickets.price).desc()).all()

    results = [
        {
            "first_name": row.first_name,
            "last_name": row.last_name,
            "total_spent": float(row.total_spent)
        }
        for row in customer_data
    ]

    return jsonify(results), 200


    
