import requests
import time
import json

BASE_URL = "http://localhost:8000"

def test_endpoint(name, url):
    print(f"\n--- Testing {name} ({url}) ---")
    start = time.time()
    try:
        res = requests.get(url, timeout=10)
        dur = time.time() - start
        print(f"Status: {res.status_code}")
        print(f"Time: {dur:.4f}s")
        if res.status_code == 200:
            data = res.json()
            if isinstance(data, list):
                print(f"Response: List with {len(data)} items")
                if len(data) > 0:
                    print(f"Sample: {data[0]}")
            else:
                print("Response keys:", data.keys())
        else:
            print("Error:", res.text)
    except Exception as e:
        print(f"FAILED: {e}")

if __name__ == "__main__":
    test_endpoint("Weekly Forecast", f"{BASE_URL}/api/v1/prediction/forecast")
    test_endpoint("Medications", f"{BASE_URL}/api/v1/medications")
    test_endpoint("Entries", f"{BASE_URL}/api/v1/entries")
