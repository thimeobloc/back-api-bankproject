import requests

BASE_URL = "http://127.0.0.1:8000"

def post(path, data=None):
    response = requests.post(f"{BASE_URL}{path}", json=data)
    print(f"\nPOST {path} ->", response.status_code)
    print(response.json())
    return response.json()

def delete(path):
    response = requests.delete(f"{BASE_URL}{path}")
    print(f"\nDELETE {path} ->", response.status_code)
    print(response.json())
    return response.json()

def get(path):
    response = requests.get(f"{BASE_URL}{path}")
    print(f"\nGET {path} ->", response.status_code)
    print(response.json())
    return response.json()


if __name__ == "__main__":

    # Création des utilisateurs
    res_dave = post("/users/", {"name": "Dave", "email": "dave@example.com", "password": "pass111"})
    res_eve  = post("/users/", {"name": "Eve", "email": "eve@example.com", "password": "pass222"})

    account_id_dave = res_dave["id"]
    account_id_eve  = res_eve["id"]

    # Dépôts
    post("/balances/deposit", {"account_id": account_id_dave, "amount": 800.0})
    post("/balances/deposit", {"account_id": account_id_eve, "amount": 300.0})

    # Retraits
    post("/balances/withdraw", {"account_id": account_id_dave, "amount": 200.0})

    # Transferts normaux
    post("/balances/transfer", {"from_account_id": account_id_dave, "to_account_id": account_id_eve, "amount": 100.0})

    # Transferts avec erreurs
    post("/balances/transfer", {"from_account_id": account_id_dave, "to_account_id": account_id_dave, "amount": 50.0})  # Même compte
    post("/balances/transfer", {"from_account_id": account_id_dave, "to_account_id": account_id_eve, "amount": 10000.0}) # Solde insuffisant

    # Création d’un compte secondaire pour Eve pour tester la clôture
    res_secondary = post("/accounts/", {"user_id": account_id_eve})
    account_id_secondary = res_secondary["id"]

    # Fermer le compte secondaire
    post(f"/accounts/closed/{account_id_secondary}/{account_id_eve}")

    # Tentatives sur le compte fermé (devraient échouer)
    post("/balances/withdraw", {"account_id": account_id_secondary, "amount": 50.0})
    post("/balances/transfer", {"from_account_id": account_id_dave, "to_account_id": account_id_secondary, "amount": 50.0})

    # Consultations
    get(f"/balances/deposits/{account_id_dave}")
    get(f"/balances/withdraws/{account_id_dave}")
    get(f"/balances/transfers/{account_id_dave}")
    get(f"/balances/deposits/{account_id_eve}")
    get(f"/balances/withdraws/{account_id_eve}")
    get(f"/balances/transfers/{account_id_eve}")
    get(f"/balances/deposits/{account_id_secondary}")
    get(f"/balances/withdraws/{account_id_secondary}")
    get(f"/balances/transfers/{account_id_secondary}")
