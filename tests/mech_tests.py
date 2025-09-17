import unittest
import os
import json
import sys
# A more direct way to add the project's root to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from flask import Flask
from app import create_app, db
from app.models import Mechanics
from app.util.auth import encode_token
from werkzeug.security import generate_password_hash

class MechanicsRoutesTestCase(unittest.TestCase):

    def setUp(self):
        """Set up the test application and database before each test."""
        # The key change is here: pass the string 'test_config'
        self.app = create_app('test_config')
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        self.client = self.app.test_client()

        # Create a manager and mechanic for testing
        manager_password = generate_password_hash("manager123")
        mechanic_password = generate_password_hash("mechanic123")

        self.manager = Mechanics(
            first_name="Admin",
            last_name="Manager",
            email="manager@test.com",
            salary=80000.0,
            address="123 Manager St",
            password=manager_password,
            role="manager"
        )
        self.mechanic_one = Mechanics(
            first_name="John",
            last_name="Doe",
            email="john@test.com",
            salary=50000.0,
            address="123 Oak Ave",
            password=mechanic_password,
            role="mechanic"
        )

        db.session.add(self.manager)
        db.session.add(self.mechanic_one)
        db.session.commit()

        # Get tokens for testing
        self.manager_token = encode_token(self.manager.id, self.manager.role)
        self.mechanic_token = encode_token(self.mechanic_one.id, self.mechanic_one.role)


    def tearDown(self):
        """Clean up the database and application context after each test."""
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    # Test cases for the Mechanics Blueprint routes
    def test_create_mechanic_success(self):
        """Test POST /mechanics/ route with manager credentials."""
        new_mechanic_data = {
            "first_name": "Jane",
            "last_name": "Smith",
            "email": "jane@test.com",
            "salary": 55000.0,
            "address": "456 Pine Ave",
            "password": "jane123"
        }
        response = self.client.post('/mechanics/',
                                    data=json.dumps(new_mechanic_data),
                                    content_type='application/json',
                                    headers={'Authorization': f'Bearer {self.manager_token}'})
        
        self.assertEqual(response.status_code, 201)
        data = response.get_json()
        self.assertEqual(data['first_name'], 'Jane')
        self.assertEqual(data['email'], 'jane@test.com')

    def test_create_mechanic_unauthorized(self):
        """Test POST /mechanics/ route with unauthorized (non-manager) credentials."""
        new_mechanic_data = {
            "first_name": "Jane",
            "last_name": "Smith",
            "email": "jane@test.com",
            "salary": 55000.0,
            "address": "456 Pine Ave",
            "password": "jane123"
        }
        response = self.client.post('/mechanics/',
                                    data=json.dumps(new_mechanic_data),
                                    content_type='application/json',
                                    headers={'Authorization': f'Bearer {self.mechanic_token}'})
        
        self.assertEqual(response.status_code, 403)
        self.assertIn("Unauthorized to create a mechanic.", response.get_json()['message'])
    
    def test_read_all_mechanics_success(self):
        """Test GET /mechanics/ route to retrieve all mechanics."""
        response = self.client.get('/mechanics/', headers={'Authorization': f'Bearer {self.mechanic_token}'})
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(len(data), 2)  # Should contain the manager and the mechanic

    def test_read_single_mechanic_success(self):
        """Test GET /mechanics/<int:mechanic_id> route."""
        response = self.client.get(f'/mechanics/{self.mechanic_one.id}', headers={'Authorization': f'Bearer {self.mechanic_token}'})
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data['id'], self.mechanic_one.id)
        self.assertEqual(data['first_name'], self.mechanic_one.first_name)

    def test_read_single_mechanic_not_found(self):
        """Test GET /mechanics/<int:mechanic_id> with a non-existent ID."""
        non_existent_id = 999
        response = self.client.get(f'/mechanics/{non_existent_id}', headers={'Authorization': f'Bearer {self.mechanic_token}'})
        self.assertEqual(response.status_code, 404)
        self.assertIn("Mechanic not found.", response.get_json()['message'])

    def test_update_mechanic_success(self):
        """Test PUT /mechanics/<int:mechanic_id> route with manager credentials."""
        update_data = {
            "salary": 60000.0
        }
        response = self.client.put(f'/mechanics/{self.mechanic_one.id}',
                                   data=json.dumps(update_data),
                                   content_type='application/json',
                                   headers={'Authorization': f'Bearer {self.manager_token}'})
        
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data['salary'], 60000.0)
        
    def test_update_mechanic_unauthorized(self):
        """Test PUT /mechanics/<int:mechanic_id> route with unauthorized credentials."""
        update_data = {
            "salary": 60000.0
        }
        response = self.client.put(f'/mechanics/{self.mechanic_one.id}',
                                   data=json.dumps(update_data),
                                   content_type='application/json',
                                   headers={'Authorization': f'Bearer {self.mechanic_token}'})
        
        self.assertEqual(response.status_code, 403)
        self.assertIn("Unauthorized to update this mechanic.", response.get_json()['message'])
    
    def test_delete_mechanic_success(self):
        """Test DELETE /mechanics/<int:mechanic_id> route with manager credentials."""
        mechanic_to_delete_id = self.mechanic_one.id
        response = self.client.delete(f'/mechanics/{mechanic_to_delete_id}', headers={'Authorization': f'Bearer {self.manager_token}'})
        
        self.assertEqual(response.status_code, 200)
        self.assertIn(f"Successfully deleted mechanic {mechanic_to_delete_id}.", response.get_json()['message'])

        # Verify the mechanic is actually deleted
        check_response = self.client.get(f'/mechanics/{mechanic_to_delete_id}', headers={'Authorization': f'Bearer {self.manager_token}'})
        self.assertEqual(check_response.status_code, 404)

    def test_delete_mechanic_unauthorized(self):
        """Test DELETE /mechanics/<int:mechanic_id> route with unauthorized credentials."""
        response = self.client.delete(f'/mechanics/{self.mechanic_one.id}', headers={'Authorization': f'Bearer {self.mechanic_token}'})
        self.assertEqual(response.status_code, 403)
        self.assertIn("Unauthorized to delete this mechanic.", response.get_json()['message'])

    def test_delete_mechanic_not_found(self):
        """Test DELETE /mechanics/<int:mechanic_id> with a non-existent ID."""
        non_existent_id = 999
        response = self.client.delete(f'/mechanics/{non_existent_id}', headers={'Authorization': f'Bearer {self.manager_token}'})
        self.assertEqual(response.status_code, 404)
        self.assertIn("Mechanic not found.", response.get_json()['message'])

if __name__ == '__main__':
    unittest.main()