import easyocr
import cv2
import numpy as np
import pytesseract
from PIL import Image
import re

# Initialize readers once
easyocr_reader = easyocr.Reader(['en'], gpu=False)

def preprocess_image(image_path):
    """Advanced image preprocessing for maximum OCR accuracy"""
    img = cv2.imread(image_path)
    
    # Convert to grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Apply adaptive thresholding for better text extraction
    thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                   cv2.THRESH_BINARY, 11, 2)
    
    # Denoise
    denoised = cv2.medianBlur(thresh, 3)
    
    # Sharpen
    kernel = np.array([[-1,-1,-1], [-1,9,-1], [-1,-1,-1]])
    sharpened = cv2.filter2D(denoised, -1, kernel)
    
    return sharpened

def extract_text_easyocr(image_path):
    """Extract text using EasyOCR with preprocessing"""
    try:
        processed_img = preprocess_image(image_path)
        results = easyocr_reader.readtext(processed_img)
        
        extracted_text = []
        for (bbox, text, prob) in results:
            if prob > 0.5:  # Higher confidence threshold
                # Clean common OCR errors
                text = clean_ocr_text(text)
                extracted_text.append(text)
        
        return "\n".join(extracted_text)
    except Exception as e:
        print(f"EasyOCR error: {e}")
        return ""

def extract_text_tesseract(image_path):
    """Extract text using Tesseract OCR with preprocessing"""
    try:
        processed_img = preprocess_image(image_path)
        
        # Configure Tesseract for best results
        custom_config = r'--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ@.-_+&()[]{}:;/\,#?!%$\'" '
        text = pytesseract.image_to_string(processed_img, config=custom_config)
        
        # Clean and format
        lines = [clean_ocr_text(line.strip()) for line in text.split('\n') if line.strip()]
        return "\n".join(lines)
    except Exception as e:
        print(f"Tesseract error: {e}")
        return ""

def clean_ocr_text(text):
    """Clean common OCR mistakes"""
    # Common substitutions
    replacements = {
        'gmai1': 'gmail',
        'corn': 'com',
        'co rn': 'com',
        'c0m': 'com',
        '@gmai1': '@gmail',
        'gm ail': 'gmail',
        'outl00k': 'outlook',
        'yah00': 'yahoo',
        '1': 'l',  # In some contexts
        '0': 'o',  # In some contexts
        '|': 'l',
        '[]': 'O',
        '()': 'O'
    }
    
    for old, new in replacements.items():
        text = text.replace(old, new)
    
    # Remove extra spaces and special characters
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'[^\w\s@.-]', '', text)
    
    return text.strip()

def extract_text(image_path):
    """Extract text using multiple OCR engines for maximum accuracy"""
    
    # Get results from both engines
    easyocr_text = extract_text_easyocr(image_path)
    tesseract_text = extract_text_tesseract(image_path)
    
    # Combine results intelligently
    easyocr_lines = [line.strip() for line in easyocr_text.split('\n') if line.strip()]
    tesseract_lines = [line.strip() for line in tesseract_text.split('\n') if line.strip()]
    
    # Merge and deduplicate
    all_lines = list(set(easyocr_lines + tesseract_lines))
    
    # Sort by length and quality (longer lines often more complete)
    all_lines.sort(key=len, reverse=True)
    
    return "\n".join(all_lines)