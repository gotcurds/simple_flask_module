import sys
import os
import unittest
from flask import json
from werkzeug.security import generate_password_hash
from config import TestConfig
from app import create_app
from app.models import db, Mechanics
from app.util.auth import encode_token

# This is a critical line that makes sure Python can find the 'app' module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

class TestMechanicsRoutes(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.app_context = self.app.app_context()
        self.app_context.push()
        self.client = self.app.test_client()
        with self.app.app_context():
            db.create_all()

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()
        self.app_context.pop()

    def test_get_all_mechanics(self):
        response = self.client.get("/mechanics/")
        self.assertEqual(response.status_code, 200)

    def test_login(self):
        # Create a test mechanic to log in
        test_mechanic = Mechanics(
            email="test@example.com",
            password=generate_password_hash("password"),  # Hashed password
            first_name="Test",
            last_name="User",
            role="manager"
        )
        with self.app.app_context():
            db.session.add(test_mechanic)
            db.session.commit()
        
        # Test the login route with valid credentials
        response = self.client.post("/mechanics/login", json={"email": "test@example.com", "password": "password"})
        data = json.loads(response.data)
        self.assertEqual(response.status_code, 200)
        self.assertIn("token", data)
    
    def test_create_mechanic(self):
        # Manager token is needed to create a mechanic
        with self.app.app_context():
            test_manager = Mechanics(email="manager@example.com", password=generate_password_hash("password"), first_name="Manager", last_name="User", role="manager")
            db.session.add(test_manager)
            db.session.commit()
            token = encode_token(test_manager.id, "manager")
        
        headers = {"Authorization": f"Bearer {token}"}
        
        response = self.client.post("/mechanics/", headers=headers, json={
            "first_name": "New",
            "last_name": "Mechanic",
            "email": "new.mechanic@example.com",
            "password": "newpassword",
            "role": "mechanic"
        })
        self.assertEqual(response.status_code, 201)


if __name__ == "__main__":
    unittest.main()