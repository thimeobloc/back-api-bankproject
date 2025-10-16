import requests
from datetime import datetime

BASE_URL = "http://127.0.0.1:8000"

def post(path, data):
    response = requests.post(f"{BASE_URL}{path}", json=data)
    print(f"\nPOST {path} ->", response.status_code)
    try:
        print(response.json())
    except Exception:
        print(response.text)
    return response.json() if response.status_code == 200 else None

def get(path):
    response = requests.get(f"{BASE_URL}{path}")
    print(f"\nGET {path} ->", response.status_code)
    try:
        print(response.json())
    except Exception:
        print(response.text)
    return response.json() if response.status_code == 200 else None


if __name__ == "__main__":

    # Création des utilisateurs
    user1 = post("/users/", {"name": "Alice", "email": "alice@example.com", "password": "pass123"})
    user2 = post("/users/", {"name": "Bob", "email": "bob@example.com", "password": "pass456"})
    user3 = post("/users/", {"name": "Charlie", "email": "charlie@example.com", "password": "pass789"})

    # Création d'un compte supplémentaire pour chaque utilisateur
    account1 = post("/accounts/", {"user_id": 1, "date": datetime.now().isoformat()})
    account2 = post("/accounts/", {"user_id": 2, "date": datetime.now().isoformat()})
    account3 = post("/accounts/", {"user_id": 3, "date": datetime.now().isoformat()})

    # Vérification des utilisateurs
    get("/users/")

    # Vérification des comptes de chaque utilisateur
    get("/accounts/account/1/")
    get("/accounts/account/2/")
    get("/accounts/account/3/")

    # Récupération des RIBs pour chaque compte
    if account1:
        get(f"/accounts/beneficiary/1/{account1['id']}/RIB")
    if account2:
        get(f"/accounts/beneficiary/2/{account2['id']}/RIB")
    if account3:
        get(f"/accounts/beneficiary/3/{account3['id']}/RIB")

