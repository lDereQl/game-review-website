import pytesseract
from PIL import Image
import re
import requests
from django.core.files.storage import default_storage
from django.utils import timezone

# Manually specify the path to Tesseract OCR
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"


def upload_to_storage(file):
    """
    Uploads a file to the default storage backend and returns its path.
    """
    try:
        # Save the file to the storage backend
        file_path = default_storage.save(file.name, file)
        return default_storage.path(file_path)
    except Exception as e:
        raise ValueError(f"Failed to upload file: {e}")


def upload_image_to_storage(file):
    """
    Uploads an image file to the storage backend and returns its absolute path.
    """
    try:
        # Save the file to the storage backend
        file_path = default_storage.save(f"uploaded_images/{timezone.now().strftime('%Y%m%d%H%M%S')}_{file.name}", file)
        absolute_path = default_storage.path(file_path)  # Return the full file path
        print("DEBUG: File uploaded to:", absolute_path)  # Debug line to confirm file path
        return absolute_path
    except Exception as e:
        raise ValueError(f"Failed to upload image: {e}")

def verify_id_image(image_path):
    """
    Verifies an uploaded image using Tesseract OCR to detect keywords and ID patterns.
    """
    try:
        # Extract text from the image
        text = pytesseract.image_to_string(Image.open(image_path))
        print("DEBUG: Extracted OCR Text:\n", text)  # Debugging log
        
        # Normalize the extracted text (lowercase, remove extra spaces)
        clean_text = " ".join(text.lower().split())

        # Define required keywords and patterns
        required_keywords = ['press', 'journalist', 'photographer']
        id_pattern = r'id[-\s]?\w{4,}'  # Flexible ID pattern: ID, ID-CARD, etc.

        # Verify keywords and ID pattern
        keyword_verified = any(keyword in clean_text for keyword in required_keywords)
        id_verified = re.search(id_pattern, clean_text)

        confidence = 0.9 if keyword_verified and id_verified else 0.5
        return {'verified': keyword_verified and id_verified, 'confidence': confidence, 'text': text}

    except Exception as e:
        print("Error during OCR verification:", e)
        return {'verified': False, 'confidence': 0.0, 'text': ''}

    



def get_game_info(app_id):
    """
    Fetches game details from SteamSpy API, including review counts and overall score.
    """
    steamspy_url = f"https://steamspy.com/api.php?request=appdetails&appid={app_id}"
    steamspy_response = requests.get(steamspy_url)

    if steamspy_response.status_code != 200:
        print("Failed to retrieve review data from SteamSpy.")
        return {
            "positive_reviews": "Unavailable",
            "negative_reviews": "Unavailable",
            "total_reviews": "Unavailable",
            "overall_score": "Unavailable"
        }

    review_data = steamspy_response.json()

    positive_reviews = review_data.get("positive", 0)
    negative_reviews = review_data.get("negative", 0)
    total_reviews = positive_reviews + negative_reviews
    overall_score = (positive_reviews / total_reviews) * 100 if total_reviews > 0 else 0

    return {
        "positive_reviews": positive_reviews,
        "negative_reviews": negative_reviews,
        "total_reviews": total_reviews,
        "overall_score": f"{overall_score:.2f}%"
    }
