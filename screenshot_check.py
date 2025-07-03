import pyautogui
import pytesseract
import time

# --- Configuration ---
# For Windows users: Uncomment the line below and set the path to your
# Tesseract installation if it's not in your system's PATH.
# Find the tesseract.exe file and replace the path here.
# pytesseract.pytesseract.tesseract_cmd = (
#     r"C:\Program Files\Tesseract-OCR\tesseract.exe"
# )


def check_for_admin_message():
    """
    Takes a screenshot of a specific region and checks for a target message.
    """
    try:
        # 1. Define the screen region to capture
        # The format is (left, top, width, height)
        x1, y1 = 445, 905
        x2, y2 = 1469, 955
        width = x2 - x1
        height = y2 - y1
        region_to_capture = (x1, y1, width, height)

        # The exact message we are looking for
        target_message = "Only admins can send messages"

        # 2. Take a screenshot of the specified region
        print(f"Capturing screen region: {region_to_capture}...")
        screenshot = pyautogui.screenshot(region=region_to_capture)

        # Optional: Save the screenshot to a file for debugging
        # screenshot.save("debug_screenshot.png")
        # print("Debug screenshot saved as 'debug_screenshot.png'")

        # 3. Use pytesseract to perform OCR and extract text
        extracted_text = pytesseract.image_to_string(screenshot)

        # Clean up the extracted text by removing leading/trailing whitespace
        cleaned_text = extracted_text.strip()
        print(f"Detected Text: '{cleaned_text}'")

        # 4. Check if the target message is in the extracted text
        # Using 'in' is more robust than '==' in case OCR picks up
        # extra characters or artifacts.
        if target_message in cleaned_text:
            print(f"\n[SUCCESS] Found the message: '{target_message}'")
            return True
        else:
            print(f"\n[INFO] The target message was not found.")
            return False

    except FileNotFoundError:
        print(
            "[ERROR] Tesseract not found. Please ensure it's installed and "
            "the path is configured correctly in the script."
        )
        return False
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return False


if __name__ == "__main__":
    # Give yourself a few seconds to switch to the correct window
    # before the script takes the screenshot.
    print("The script will run in 5 seconds. Please prepare your screen.")
    time.sleep(5)
    check_for_admin_message()