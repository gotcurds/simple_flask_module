import unittest
import os
import json
import sys
# Add the project's root directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from flask import Flask
from app import create_app, db
from app.models import Part, InventoryPartDescription
from app.util.auth import encode_token
from werkzeug.security import generate_password_hash
from app.blueprints.parts.routes import parts_bp
from app.blueprints.parts.schemas import part_schema, parts_schema, inventory_part_description_schema

# Define the test configuration
class TestConfig:
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = os.environ.get('SECRET_KEY', 'default-test-secret')
    WTF_CSRF_ENABLED = False


class PartsRoutesTestCase(unittest.TestCase):

    def setUp(self):
        self.app = create_app(TestConfig)
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        self.client = self.app.test_client()

        # Create test users
        self.manager_token = encode_token(1, 'manager')
        self.user_token = encode_token(2, 'user')

        # Create a part description for testing purposes
        self.part_desc_one = InventoryPartDescription(
            name="Oil Filter",
            price=15.00
        )
        self.part_desc_two = InventoryPartDescription(
            name="Spark Plug",
            price=5.00
        )

        db.session.add(self.part_desc_one)
        db.session.add(self.part_desc_two)
        db.session.commit()

        # Create parts for testing
        self.part_one = Part(desc_id=self.part_desc_one.id)
        self.part_two = Part(desc_id=self.part_desc_two.id)
        db.session.add(self.part_one)
        db.session.add(self.part_two)
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_create_inventory_part_description_success(self):
        # Test POST /parts/ with manager credentials.
        data = {
            "name": "Brake Pad",
            "price": 35.00
        }
        response = self.client.post('/parts/', json=data, headers={'Authorization': f'Bearer {self.manager_token}'})
        self.assertEqual(response.status_code, 201)
        self.assertIn("id", response.get_json())

    def test_create_part_description_unauthorized(self):
        # Test POST /parts/ with a non-manager user.
        data = {
            "name": "Brake Pad",
            "price": 35.00
        }
        response = self.client.post('/parts/', json=data, headers={'Authorization': f'Bearer {self.user_token}'})
        self.assertEqual(response.status_code, 403)
        self.assertIn("Unauthorized to create a new part.", response.get_json()['message'])
    
    def test_create_physical_part_success(self):
        # Test POST /parts/add-physical-part with manager credentials and existing part description.
        data = {"desc_id": self.part_desc_one.id}
        response = self.client.post('/parts/add-physical-part', json=data, headers={'Authorization': f'Bearer {self.manager_token}'})
        self.assertEqual(response.status_code, 201)
        self.assertIn("Successfully created physical part with ID", response.get_json()['message'])

    def test_create_physical_part_not_found(self):
        # Test POST /parts/add-physical-part with non-existent description ID.
        data = {"desc_id": 999}
        response = self.client.post('/parts/add-physical-part', json=data, headers={'Authorization': f'Bearer {self.manager_token}'})
        self.assertEqual(response.status_code, 404)
        self.assertIn("Inventory description not found.", response.get_json()['message'])

    def test_read_all_parts_success(self):
        # Test GET /parts/ route.
        response = self.client.get('/parts/')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 2)

    def test_read_single_part_success(self):
        # Test GET /parts/<int:part_id> route.
        response = self.client.get(f'/parts/{self.part_one.id}')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data['id'], self.part_one.id)
        self.assertEqual(data['desc_id'], self.part_desc_one.id)
        # Corrected assertion to look inside the nested dictionary
        self.assertIn("name", data['inventory_description'])
        self.assertEqual(data['inventory_description']['name'], self.part_desc_one.name)

    def test_read_single_part_not_found(self):
        # Test GET /parts/<int:part_id> with a non-existent ID.
        response = self.client.get('/parts/999')
        self.assertEqual(response.status_code, 404)
        self.assertIn("Part not found.", response.get_json()['message'])
    
    def test_update_part_success(self):
        # Test PUT /parts/<int:part_id> with manager credentials.
        new_desc = InventoryPartDescription(name="New Part Name", price=25.00)
        db.session.add(new_desc)
        db.session.commit()
        
        update_data = {"desc_id": new_desc.id}
        response = self.client.put(f'/parts/{self.part_one.id}', json=update_data, headers={'Authorization': f'Bearer {self.manager_token}'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()['desc_id'], new_desc.id)
    
    def test_update_part_unauthorized(self):
        # Test PUT /parts/<int:part_id> with non-manager credentials.
        update_data = {"desc_id": self.part_desc_two.id}
        response = self.client.put(f'/parts/{self.part_one.id}', json=update_data, headers={'Authorization': f'Bearer {self.user_token}'})
        self.assertEqual(response.status_code, 403)
        self.assertIn("Unauthorized to update this part.", response.get_json()['message'])

    def test_delete_part_success(self):
        # Test DELETE /parts/<int:part_id> with manager credentials.
        part_id_to_delete = self.part_one.id
        response = self.client.delete(f'/parts/{part_id_to_delete}', headers={'Authorization': f'Bearer {self.manager_token}'})
        self.assertEqual(response.status_code, 200)
        self.assertIn(f"Successfully deleted part {part_id_to_delete}.", response.get_json()['message'])
        
    def test_delete_part_unauthorized(self):
        # Test DELETE /parts/<int:part_id> with non-manager credentials.
        response = self.client.delete(f'/parts/{self.part_one.id}', headers={'Authorization': f'Bearer {self.user_token}'})
        self.assertEqual(response.status_code, 403)
        self.assertIn("Unauthorized to delete this part.", response.get_json()['message'])