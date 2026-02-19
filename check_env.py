import os
from dotenv import load_dotenv

def check_env():
    print("--- ENV Check ---")
    load_dotenv()
    key = os.getenv("MINDEE_API_KEY")
    if key:
        print(f"Key found! Length: {len(key)}")
        print(f"Starts with: {key[:5]}...")
        print(f"Ends with: ...{key[-5:]}")
        if key.strip() != key:
            print("WARNING: Key has leading/trailing whitespace!")
    else:
        print("Key NOT found in environment.")

if __name__ == "__main__":
    check_env()
