import requests
import json

BASE_URL = "http://127.0.0.1:8000"

def post(path, data):
    response = requests.post(f"{BASE_URL}{path}", json=data)
    print(response.json())

def delete(path):
    response = requests.delete(f"{BASE_URL}{path}")
    print(response.json())

def get(path):
    response = requests.get(f"{BASE_URL}{path}")
    print(response.json())

if __name__ == "__main__":
    post("/users/", {"name": "Alice", "email": "alice@example.com", "password": "pass123"})
    post("/users/", {"name": "Bob", "email": "bob@example.com", "password": "pass456"})
    post("/users/", {"name": "Charlie", "email": "charlie@example.com", "password": "pass789"})

    post("/balances/deposit", {"account_id": 1, "amount": 1000.0})
    post("/balances/deposit", {"account_id": 2, "amount": 500.0})
    post("/balances/deposit", {"account_id": 3, "amount": 200.0})

    post("/balances/withdraw", {"account_id": 1, "amount": 100.0})
    post("/balances/withdraw", {"account_id": 2, "amount": 50.0})

    post("/balances/transfer", {"from_account_id": 1, "to_account_id": 2, "amount": 150.0})
    post("/balances/transfer", {"from_account_id": 2, "to_account_id": 3, "amount": 50.0})
    post("/balances/transfer", {"from_account_id": 1, "to_account_id": 3, "amount": 200.0})
    post("/balances/transfer", {"from_account_id": 3, "to_account_id": 1, "amount": 25.0})
    post("/balances/transfer", {"from_account_id": 1, "to_account_id": 1, "amount": 50.0})
    post("/balances/transfer", {"from_account_id": 1, "to_account_id": 2, "amount": 5000.0})
    post("/balances/transfer", {"from_account_id": 999, "to_account_id": 2, "amount": 50.0})

    delete("/balances/transfer_abort/1/3")
    delete("/balances/transfer_abort/2/4")

    get("/balances/transfers/1")
    get("/balances/transfers/2")
    get("/balances/transfer/3")
    get("/balances/deposits/1")
    get("/balances/deposits/2")
    get("/balances/deposits/3")
    get("/balances/withdraws/1")
    get("/balances/withdraws/2")
    get("/balances/withdraws/3")
