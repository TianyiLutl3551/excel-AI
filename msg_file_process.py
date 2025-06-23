import extract_msg
import os
import pytesseract
from PIL import Image, ImageEnhance, ImageFilter
import io
import base64
import toml
from openai import OpenAI
import pandas as pd
from datetime import datetime
import json
from bs4 import BeautifulSoup
import re

# --- Load secrets and initialize OpenAI client ---
config = toml.load("secrets.toml")
api_key = config["openai"]["api_key"]
client = OpenAI(api_key=api_key)

def preprocess_image_for_vision_api(image_data):
    """
    Preprocess image using PIL for better Vision API results:
    1. Grayscale conversion
    2. Binarization (threshold)
    3. Resize (scale up for small text)
    """
    # Open the image from bytes
    img = Image.open(io.BytesIO(image_data))
    
    # 1. Grayscale conversion
    gray = img.convert('L')
    
    # 2. Binarization (threshold)
    threshold = 180
    binary = gray.point(lambda x: 0 if x < threshold else 255, '1')
    
    # 3. Resize (scale up for small text)
    width, height = binary.size
    resized = binary.resize((width * 2, height * 2), Image.Resampling.LANCZOS)
    
    # 4. Convert back to grayscale for encoding
    resized_gray = resized.convert('L')
    
    # 5. Encode the processed image to PNG in memory
    buffer = io.BytesIO()
    resized_gray.save(buffer, format='PNG')
    image_bytes = buffer.getvalue()
    
    return image_bytes

def extract_highlights_from_html(html):
    soup = BeautifulSoup(html, 'html.parser')
    text = soup.get_text(separator='\n')
    # Find all lines containing 'highlights' (case-insensitive)
    lines = text.splitlines()
    highlights_sections = []
    i = 0
    while i < len(lines):
        if re.search(r'highlights', lines[i], re.IGNORECASE):
            section = [lines[i].strip()]
            i += 1
            # Collect lines until next heading or empty line or end
            while i < len(lines):
                if (re.match(r'^[A-Z][A-Za-z0-9 &/:-]{2,}$', lines[i].strip()) and not re.search(r'highlights', lines[i], re.IGNORECASE)) or lines[i].strip() == '':
                    break
                section.append(lines[i].strip())
                i += 1
            highlights_sections.append('\n'.join(section))
        else:
            i += 1
    return highlights_sections

msg_path = r"/Users/lutianyi/Desktop/excel AI/input/FW_ Please review_ Daily Hedging P&L Summary for WB 2024_05_01.msg"
msg = extract_msg.Message(msg_path)

print("--- Email Analysis ---")
print(f"Subject: {msg.subject}")
print(f"From: {msg.sender}")
print(f"To: {msg.to}")
print(f"Date: {msg.date}")
print("\n--- Message Body ---")
if msg.body:
    print(msg.body)
elif hasattr(msg, 'htmlBody') and msg.htmlBody:
    print("[HTML Body]")
    highlights = extract_highlights_from_html(msg.htmlBody)
    if highlights:
        print("\n--- Extracted Highlights Section(s) ---\n")
        for section in highlights:
            print(section)
            print("\n" + "-"*40 + "\n")
    else:
        print("No highlights section found.")
    # Optionally, print the whole HTML as text for debug:
    # print(BeautifulSoup(msg.htmlBody, 'html.parser').get_text())
elif hasattr(msg, 'rtfBody') and msg.rtfBody:
    print("[RTF Body]")
    print(msg.rtfBody)
else:
    print("No message body found.")
print("\n" + "="*50 + "\n")

if not msg.attachments:
    print("No attachments found.")
else:
    print("--- Locating Target Image Attachment ---")
    target_image_data = None
    target_image_filename = None
    
    for attachment in msg.attachments:
        filename = (attachment.longFilename or attachment.shortFilename).rstrip('\x00')
        
        if filename.lower().endswith('.png'):
            print(f"[*] Checking image: {filename}...")
            try:
                # Use OCR to check the content of the image
                image_bytes = io.BytesIO(attachment.data)
                image = Image.open(image_bytes)
                extracted_text = pytesseract.image_to_string(image)
                
                # Check if the target phrase is in the extracted text
                if "Total Dynamic Hedge P&L as of" in extracted_text:
                    print(f"[+] Found target image: {filename}")
                    target_image_data = attachment.data
                    target_image_filename = filename
                    break # Stop after finding the first match
                else:
                    print(f"[-] Image does not contain the target phrase.")
            
            except Exception as e:
                print(f"Could not perform OCR on {filename}. Error: {e}")
        else:
            print(f"[-] Skipping non-image file: {filename}")

    # --- Process the located image with Vision API ---
    if target_image_data:
        print(f"\n--- Sending {target_image_filename} to Vision API ---")
        
        # 1. Preprocess the image
        preprocessed_image_data = preprocess_image_for_vision_api(target_image_data)

        # 2. Encode the preprocessed image in base64
        base64_image = base64.b64encode(preprocessed_image_data).decode('utf-8')

        # 3. Create the prompt for the Vision API
        vision_prompt_text = """
        You are a precise financial table extraction specialist. Extract ONLY the main P&L table from this image.

        CRITICAL RULES:
        1. Look for the table with title pattern: "[COMPANY] Total Dynamic Hedge P&L as of [DATE]"
        2. Extract exactly 5 columns: "VA Rider [COMPANY]", "Rider", "Asset", "Daily Net", "QTD Net"
        3. If you see fewer than 5 columns in the image, do NOT add missing columns
        4. Preserve the hierarchical structure (main categories with indented subcategories)
        5. Use exact values from image - no guessing or filling in
        6. If a cell is empty or unclear, use "N/A"
        7. Keep negative numbers in parentheses format: "(15.7)"
        8. The date in your output must match the date in the image title exactly

        JSON Format:
        {
          "table": {
            "title": "Exact title from image",
            "headers": ["VA Rider [COMPANY]", "Rider", "Asset", "Daily Net", "QTD Net"],
            "rows": [
              ["Total Equity", "(15.7)", "16.1", "0.4", "(26.2)"],
              ["  Equity Delta", "(15.7)", "16.1", "0.4", "(2.3)"],
              ["  Equity Gamma & Residual", "-", "-", "-0.0", "(23.8)"]
            ]
          }
        }

        DO NOT extract other tables or add columns that don't exist.
        """
        
        print("Image preprocessed and encoded.")
        print("Next step: Call the OpenAI Vision API with this data.")

        try:
            # 4. Send the preprocessed image to the Vision API
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": vision_prompt_text},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=4000
            )
            
            print("--- LLM Vision API Response ---")
            response_content = response.choices[0].message.content
            print("Raw response:")
            print(response_content)
            
            # Parse JSON response and display data
            try:
                # Try to extract JSON from the response (in case there's extra text)
                json_start = response_content.find('{')
                json_end = response_content.rfind('}') + 1
                if json_start != -1 and json_end != 0:
                    json_str = response_content[json_start:json_end]
                    data = json.loads(json_str)
                    
                    # Just print the parsed data
                    print("--- Parsed JSON Data ---")
                    print(json.dumps(data, indent=2))
                    
                else:
                    print("Could not find JSON in response.")
                    print("Raw response:")
                    print(response_content)
                    
            except json.JSONDecodeError as e:
                print(f"JSON parsing error: {e}")
                print("Raw response:")
                print(response_content)
            
        except Exception as e:
            print(f"\n--- Error calling OpenAI API ---")
            print(e)
    else:
        print("\nCould not find the target image in the email attachments.")