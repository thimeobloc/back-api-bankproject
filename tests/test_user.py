import unittest
from fastapi.testclient import TestClient
from sqlmodel import SQLModel, Session
from app.main import app
from app.db.database import engine
from app.db import models
from app.core.security import hash_password
from datetime import datetime


client = TestClient(app)


class TestUsers(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """Réinitialise la base de données avant tous les tests"""
        SQLModel.metadata.drop_all(engine)
        SQLModel.metadata.create_all(engine)
        print("\n✅ Base de données réinitialisée\n")

    def setUp(self):
        """Exécuté avant chaque test"""
        # Nettoyer la base à chaque test
        SQLModel.metadata.drop_all(engine)
        SQLModel.metadata.create_all(engine)

    def create_user(self, name="John Doe", email="john@example.com", password="secret123"):
        """Helper pour créer un utilisateur via l'API"""
        response = client.post("/users/", json={
            "name": name,
            "email": email,
            "password": password
        })
        return response

    def test_create_user_success(self):
        """Création d’un utilisateur valide"""
        response = self.create_user()
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["name"], "John Doe")
        self.assertEqual(data["email"], "john@example.com")
        self.assertIn("id", data)

    def test_create_user_duplicate_email(self):
        """Création avec email déjà utilisé"""
        self.create_user()
        response = self.create_user()
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["detail"], "Email already registered")

    def test_create_user_missing_fields(self):
        """Création d’utilisateur avec champs manquants"""
        response = client.post("/users/", json={"name": "NoEmail"})
        self.assertEqual(response.status_code, 422)


    def test_get_all_users(self):
        """Récupération de tous les utilisateurs"""
        self.create_user()
        response = client.get("/users/")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIsInstance(data, list)
        self.assertGreaterEqual(len(data), 1)
        self.assertIn("email", data[0])

    def test_get_user_by_id(self):
        """Récupération d’un utilisateur par ID"""
        response = self.create_user()
        user_id = response.json()["id"]
        response_get = client.get(f"/users/{user_id}")
        self.assertEqual(response_get.status_code, 200)
        data = response_get.json()
        self.assertEqual(data["id"], user_id)
        self.assertEqual(data["email"], "john@example.com")

    def test_get_user_not_found(self):
        """Récupération d’un utilisateur inexistant"""
        response = client.get("/users/9999")
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["detail"], "User not found")


    def test_main_account_created_with_user(self):
        """Vérifie que le compte principal est créé automatiquement"""
        response = self.create_user(name="Alice", email="alice@example.com", password="test123")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        user_id = data["id"]

        # Vérifie qu'un compte a été créé pour ce user
        with Session(engine) as session:
            accounts = session.query(models.Account).filter(models.Account.user_id == user_id).all()
            self.assertEqual(len(accounts), 1)
            account = accounts[0]
            self.assertTrue(account.main)
            self.assertEqual(account.balance, 100.0)
            self.assertFalse(account.closed)
            self.assertFalse(account.status)
            self.assertTrue(account.rib.startswith("FR"))


if __name__ == "__main__":
    unittest.main()
