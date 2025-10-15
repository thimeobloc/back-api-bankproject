import requests

BASE_URL = "http://127.0.0.1:8000/users/"

def print_response(desc, response):
    print(f"\n--- {desc} ---")
    try:
        print(response.json())
    except Exception:
        print("Erreur de décodage JSON :", response.text)


user1 = {"name": "Alice", "email": "alice@example.com", "password": "pass123"}
user2 = {"name": "Bob", "email": "bob@example.com", "password": "pass456"}
user3 = {"name": "Charlie", "email": "charlie@example.com", "password": "pass789"}

print_response("Create Alice", requests.post(BASE_URL, json=user1))
print_response("Create Bob", requests.post(BASE_URL, json=user2))
print_response("Create Charlie", requests.post(BASE_URL, json=user3))

print_response("List all users", requests.get(BASE_URL))

print_response("Get user 1 details", requests.get(BASE_URL + "1"))
print_response("Get user 2 details", requests.get(BASE_URL + "2"))
print_response("Get user 999 (inexistant)", requests.get(BASE_URL + "999"))
