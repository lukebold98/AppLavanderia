from Modules.EYES.ocr_engine import MindeeOcrEngine
import os

def test_mindee():
    print("-" * 50)
    print("Testing Mindee OCR Integration")
    
    # Use one of the uploaded images
    image_path = r"C:/Users/luc21/.gemini/antigravity/brain/22b724e4-969a-4694-a0bc-b367498ba90e/uploaded_media_1_1769957431293.png"
    
    if not os.path.exists(image_path):
        # Fallback to the other one if needed
        image_path = r"C:/Users/luc21/.gemini/antigravity/brain/22b724e4-969a-4694-a0bc-b367498ba90e/uploaded_media_0_1769957431293.png"
    
    if not os.path.exists(image_path):
        print(f"ERROR: Image not found at {image_path}")
        return

    try:
        engine = MindeeOcrEngine()
        print(f"Initialized Mindee Engine V2.")
        print(f"Model ID: {engine.model_id}")
        print("Sending request... (this might take a few seconds)")
        
        # This returns empty list for now but PRINTS the fields to console
        items = engine.process_image(image_path)
        
        print("-" * 50)
        print("Done.")

    except Exception as e:
        print(f"EXCEPTION: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_mindee()
