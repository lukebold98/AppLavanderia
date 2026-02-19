import os
from mindee import Client, product
from dotenv import load_dotenv

def test_standard_product():
    print("--- Testing Mindee Key with Standard Invoice Product ---")
    load_dotenv()
    api_key = os.getenv("MINDEE_API_KEY")
    if not api_key:
        print("ERROR: MINDEE_API_KEY not found in .env")
        return

    client = Client(api_key=api_key)
    
    # We don't even need an image to test the key, we can try to initialize or call a predict on a dummy
    try:
        print("Checking connection...")
        # A simple way to check if key is valid without uploading a file? 
        # Most methods require a file. Let's use a very small dummy file if possible or just try to enqueue anyway.
        # But wait, Mindee might reject dummy files.
        
        # Let's try to use the image they already have
        image_path = r"C:/Users/luc21/.gemini/antigravity/brain/22b724e4-969a-4694-a0bc-b367498ba90e/uploaded_media_1769957553566.png"
        if not os.path.exists(image_path):
             print("No image found for test.")
             return

        input_doc = client.source_from_path(image_path)
        print("Attempting to parse as Invoice (Standard Product)...")
        # This will likely fail with "not an invoice" if it's a bolla, but it should NOT return 401 if the key is valid.
        try:
            res = client.parse(product.InvoiceV4, input_doc)
            print("SUCCESS: Connection established (Key is valid).")
        except Exception as e:
            if "401" in str(e):
                print(f"FAILED: Still 401. Your API KEY is almost certainly INVALID or EXPIRED.\nError: {e}")
            else:
                print(f"INFO: Connection worked, but parsing failed as expected (not an invoice): {e}")
                print("This confirms the KEY is VALID, but the issue is with the CUSTOM MODEL config.")

    except Exception as e:
        print(f"Unexpected Error: {e}")

if __name__ == "__main__":
    test_standard_product()
