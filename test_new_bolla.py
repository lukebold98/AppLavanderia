from Modules.BRAIN.controller import DeliveryController
import os

def test_ocr():
    # Helper to print separators
    print("-" * 50)
    print("Testing OCR on 'Files_progetto/bolla 2.jpeg'")
    
    image_path = r"C:/Users/luc21/.gemini/antigravity/brain/10ab584f-c4db-4eed-b8cb-4715c2e0a109/uploaded_media_1_1769928667345.jpg"
    
    if not os.path.exists(image_path):
        print(f"ERROR: File not found at {image_path}")
        return

    try:
        # Initialize controller (this might create a DB file if not exists, which is fine)
        controller = DeliveryController()
        
        # Process the image
        raw_text, items = controller.process_bolla(image_path)
        
        print("-" * 50)
        print("RAW TEXT EXTRACTED:")
        print(raw_text[:500] + "..." if len(raw_text) > 500 else raw_text) # Print first 500 chars
        print("-" * 50)
        
        print(f"PARSED ITEMS: {len(items)} found")
        for item in items:
            print(f" - [{item.employee_name}] {item.item_code} | {item.item_description} (Qty: {item.quantity})")
            
        if len(items) == 0:
            print("\nWARNING: No items parsed. The structure might be different from expected.")

    except Exception as e:
        print(f"EXCEPTION OCCURRED: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_ocr()
