from flask import Flask
from .models import db 
from .extensions import ma, limiter
from .blueprints.customers import customers_bp
from .blueprints.mechanics import mechanics_bp
from .blueprints.tickets import service_tickets_bp
from .blueprints.parts import parts_bp
from flasgger import Swagger
from config import DevelopmentConfig, TestConfig, ProductionConfig 
import os # Ensure os is imported if it wasn't already

def create_app(config_class=DevelopmentConfig):
    app = Flask(__name__)
    
    # Handle configuration class based on type
    if isinstance(config_class, str):
        if config_class == 'test_config':
            app.config.from_object(TestConfig)
        elif config_class == 'production':
            app.config.from_object(ProductionConfig)
        else:
            app.config.from_object(DevelopmentConfig)
    else:
        # If it's a class object, use it directly (e.g., DevelopmentConfig by default)
        app.config.from_object(config_class)


    db.init_app(app)
    ma.init_app(app)
    limiter.init_app(app)
    
    # Initialize Swagger with the template defining security and ALL global definitions.
    Swagger(app, template={
        "swagger": "2.0",
        "info": {
            "title": "Auto Shop Management API",
            "description": "API documentation for the Inventory, Customers, and Mechanics Management System.",
            "version": "1.0.0"
        },
        "securityDefinitions": {
            "token": {
                "type": "apiKey",
                "name": "Authorization",
                "in": "header",
                "description": "Bearer token is required for all protected routes."
            }
        },
        # --- START SWAGGER DEPLOYMENT CONFIG CHANGES ---
        "host": "YOUR_LIVE_RENDER_HOST_URL", # IMPORTANT: Replace this placeholder with your live Render URL (e.g., my-flask-app.onrender.com)
        "schemes": [
            "https" # Assignment requires changing schemes from http/https to https only
        ],
        # --- END SWAGGER DEPLOYMENT CONFIG CHANGES ---
        
        # ALL global definitions are placed here to resolve all cross-blueprint references.
        "definitions": {
            
            # --- Generic/Auth Definitions ---
            "LoginPayload": {
                "type": "object",
                "properties": {
                    "email": {"type": "string"},
                    "password": {"type": "string"}
                },
                "required": ["email", "password"],
                "description": "Payload for customer or generic user login."
            },
            
            # --- Customer Definitions ---
            "CustomerPayload": {
                "type": "object",
                "properties": {
                    "first_name": {"type": "string"},
                    "last_name": {"type": "string"},
                    "email": {"type": "string"},
                    "phone": {"type": "string"},
                    "address": {"type": "string"},
                    "username": {"type": "string"},
                    "password": {"type": "string"}
                },
                "required": ["first_name", "last_name", "email", "password"],
                "description": "Payload for creating or updating a customer."
            },
            "CustomerResponse": {
                "type": "object",
                "properties": {
                    "id": {"type": "integer"},
                    "first_name": {"type": "string"},
                    "last_name": {"type": "string"},
                    "email": {"type": "string"},
                    "phone": {"type": "string"},
                    "address": {"type": "string"},
                    "username": {"type": "string"}
                }
            },
            "TopSpenderResponse": {
                "type": "object",
                "properties": {
                    "customer_id": {"type": "integer"},
                    "first_name": {"type": "string"},
                    "last_name": {"type": "string"},
                    "total_spent": {"type": "number", "format": "float", "description": "Total money spent by the customer across all completed tickets."}
                }
            },
            
            # --- Part Definitions ---
            "PartDescriptionPayload": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "price": {"type": "number"}
                },
                "required": ["name", "price"]
            },
            "PartDescriptionResponse": {
                "type": "object",
                "properties": {
                    "id": {"type": "integer"},
                    "name": {"type": "string"},
                    "price": {"type": "number"}
                }
            },
            "PhysicalPartPayload": {
                "type": "object",
                "properties": {
                    "desc_id": {"type": "integer"}
                },
                "required": ["desc_id"]
            },
            "PartResponse": {
                "type": "object",
                "properties": {
                    "id": {"type": "integer"},
                    "desc_id": {"type": "integer", "description": "Foreign key to InventoryPartDescription."},
                    "inventory_description": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "integer"},
                            "name": {"type": "string"},
                            "price": {"type": "number"}
                        }
                    },
                    "ticket_id": {"type": "integer", "description": "ID of the service ticket this part is assigned to, if any."}
                }
            },
            
            # --- Mechanic Definitions ---
            "MechCreatePayload": {
                "type": "object",
                "properties": {
                    "first_name": {"type": "string"},
                    "last_name": {"type": "string"},
                    "email": {"type": "string"},
                    "salary": {"type": "number"},
                    "address": {"type": "string"},
                    "password": {"type": "string"}
                },
                "required": ["first_name", "last_name", "email", "salary", "address", "password"]
            },
            "MechUpdatePayload": {
                "type": "object",
                "properties": {
                    "first_name": {"type": "string"},
                    "last_name": {"type": "string"},
                    "email": {"type": "string"},
                    "salary": {"type": "number"},
                    "address": {"type": "string"},
                    "password": {"type": "string"}
                }
            },
            "MechLoginPayload": {
                "type": "object",
                "properties": {
                    "email": {"type": "string"},
                    "password": {"type": "string"}
                },
                "required": ["email", "password"],
                "description": "Payload for mechanic login."
            },
            "MechResponse": {
                "type": "object",
                "properties": {
                    "address": {"type": "string"},
                    "email": {"type": "string"},
                    "first_name": {"type": "string"},
                    "id": {"type": "integer"},
                    "last_name": {"type": "string"},
                    "role": {"type": "string"},
                    "salary": {"type": "number"}
                }
            },

            # --- Service Ticket Definitions (NEW) ---
            "ServiceTicketPayload": {
                "type": "object",
                "properties": {
                    "customer_id": {"type": "integer", "description": "ID of the customer requesting the service."},
                    "mechanic_id": {"type": "integer", "description": "ID of the mechanic assigned to the ticket (optional)."},
                    "vehicle_details": {"type": "string", "description": "Make, model, year, and VIN."},
                    "issue_description": {"type": "string", "description": "Detailed description of the issue."}
                },
                "required": ["customer_id", "vehicle_details", "issue_description"]
            },
            "ServiceTicketResponse": {
                "type": "object",
                "properties": {
                    "id": {"type": "integer"},
                    "status": {"type": "string", "enum": ["pending", "in_progress", "completed", "cancelled"]},
                    "final_cost": {"type": "number", "format": "float", "description": "The total cost of the service and parts."},
                    "created_at": {"type": "string", "format": "date-time"},
                    "updated_at": {"type": "string", "format": "date-time"},
                    "vehicle_details": {"type": "string"},
                    "issue_description": {"type": "string"},
                    "customer": {"$ref": "#/definitions/CustomerResponse", "description": "The customer associated with this ticket."},
                    "mechanic": {"$ref": "#/definitions/MechResponse", "description": "The mechanic assigned to this ticket."}
                }
            },
            "TicketStatusUpdatePayload": {
                "type": "object",
                "properties": {
                    "status": {"type": "string", "enum": ["pending", "in_progress", "completed", "cancelled"]}
                },
                "required": ["status"],
                "description": "Payload for updating a service ticket's status."
            },
            "TicketPartResponse": {
                "type": "object",
                "properties": {
                    "id": {"type": "integer", "description": "The ID of the physical part instance."},
                    "ticket_id": {"type": "integer", "description": "The ID of the service ticket this part is attached to."},
                    "part_name": {"type": "string", "description": "Name of the part (e.g., Oil Filter)."},
                    "part_price": {"type": "number", "format": "float", "description": "Unit price of the part."},
                    "desc_id": {"type": "integer", "description": "Foreign key to the InventoryPartDescription."}
                },
                "description": "Details of a part associated with a service ticket."
            }
        }
    })


    app.register_blueprint(customers_bp, url_prefix='/customers')
    app.register_blueprint(mechanics_bp, url_prefix='/mechanics')
    app.register_blueprint(service_tickets_bp, url_prefix='/service-tickets')
    app.register_blueprint(parts_bp, url_prefix='/parts')
    
    return app

if __name__ == '__main__':
    # This block is used for running the application directly during development
    app = create_app()
    app.run(debug=True)