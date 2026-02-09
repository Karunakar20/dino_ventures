import requests
import uuid
import time

BASE_URL = "http://localhost:8000/wallet"

def get_balance(user_id):
    resp = requests.get(f"{BASE_URL}/{user_id}/balance")
    resp.raise_for_status()
    print(f"User {user_id} Balance: {resp.json()}")
    return resp.json()['total_balance']

def top_up(user_id, amount):
    ref_id = f"topup_{uuid.uuid4()}"
    payload = {
        "user_id": user_id,
        "amount": amount,
        "reference_id": ref_id,
        "description": "Test Topup"
    }
    resp = requests.post(f"{BASE_URL}/topup", json=payload)
    print(f"TopUp: {resp.status_code} - {resp.json()}")
    resp.raise_for_status()

def bonus(user_id, amount):
    ref_id = f"bonus_{uuid.uuid4()}"
    payload = {
        "user_id": user_id,
        "amount": amount,
        "reference_id": ref_id,
        "description": "Test Bonus"
    }
    resp = requests.post(f"{BASE_URL}/bonus", json=payload)
    print(f"Bonus: {resp.status_code} - {resp.json()}")
    resp.raise_for_status()

def spend(user_id, amount):
    ref_id = f"spend_{uuid.uuid4()}"
    payload = {
        "user_id": user_id,
        "amount": amount,
        "reference_id": ref_id,
        "description": "Test Spend"
    }
    resp = requests.post(f"{BASE_URL}/spend", json=payload)
    print(f"Spend: {resp.status_code} - {resp.json()}")
    resp.raise_for_status()

def run_verification():
    # Wait for service to be up
    print("Waiting for service to be ready...")
    for i in range(10):
        try:
            requests.get("http://localhost:8000")
            break
        except requests.exceptions.ConnectionError:
            time.sleep(1)
            
    print("Checking initial balance for Alice (User ID 2)...")
    initial = get_balance(2) # Seeded as 2? Actually system=1, alice=2, bob=3 based on seed order.
                             # Wait, ID generation depends. `system_user` (1), `alice` (2), `bob` (3).
                             # Accounts match?
    
    print("Top up 100...")
    top_up(2, 100)
    
    print("Bonus 50...")
    bonus(2, 50)
    
    print("Spend 30...")
    spend(2, 30)
    
    final = get_balance(2)
    expected = initial + 100 + 50 - 30
    print(f"Final: {final}, Expected: {expected}")
    
    assert final == expected
    print("VERIFICATION PASSED!")

if __name__ == "__main__":
    run_verification()
