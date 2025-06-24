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
from prompt import get_llm_prompt

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

def extract_highlights_sections(html):
    soup = BeautifulSoup(html, 'html.parser')
    text = soup.get_text(separator='\n')
    lines = text.splitlines()
    daily = []
    qtd = []
    generic = []
    i = 0
    while i < len(lines):
        if re.search(r'daily highlights', lines[i], re.IGNORECASE):
            section = [lines[i].strip()]
            i += 1
            while i < len(lines):
                if (re.match(r'^[A-Z][A-Za-z0-9 &/:-]{2,}$', lines[i].strip()) and not re.search(r'highlights', lines[i], re.IGNORECASE)) or lines[i].strip() == '':
                    break
                section.append(lines[i].strip())
                i += 1
            daily.append('\n'.join(section))
        elif re.search(r'qtd highlights', lines[i], re.IGNORECASE):
            section = [lines[i].strip()]
            i += 1
            while i < len(lines):
                if (re.match(r'^[A-Z][A-Za-z0-9 &/:-]{2,}$', lines[i].strip()) and not re.search(r'highlights', lines[i], re.IGNORECASE)) or lines[i].strip() == '':
                    break
                section.append(lines[i].strip())
                i += 1
            qtd.append('\n'.join(section))
        elif re.search(r'highlights', lines[i], re.IGNORECASE):
            section = [lines[i].strip()]
            i += 1
            while i < len(lines):
                if (re.match(r'^[A-Z][A-Za-z0-9 &/:-]{2,}$', lines[i].strip()) and not re.search(r'highlights', lines[i], re.IGNORECASE)) or lines[i].strip() == '':
                    break
                section.append(lines[i].strip())
                i += 1
            generic.append('\n'.join(section))
        else:
            i += 1
    # If no specific daily/qtd, use generic for daily
    if not daily and not qtd and generic:
        daily = generic
    return daily, qtd

class EmailProcessor:
    def __init__(self, msg_path):
        self.msg = extract_msg.Message(msg_path)
        self.subject = self.msg.subject
        self.sender = self.msg.sender
        self.to = self.msg.to
        self.date = self.msg.date
        self.body = self._get_body()
        self.date_str = self._extract_date_from_subject() or datetime.now().strftime('%Y%m%d')

    def _get_body(self):
        if self.msg.body:
            return self.msg.body
        elif hasattr(self.msg, 'htmlBody') and self.msg.htmlBody:
            return self.msg.htmlBody
        elif hasattr(self.msg, 'rtfBody') and self.msg.rtfBody:
            return self.msg.rtfBody
        else:
            return None

    def _extract_date_from_subject(self):
        match = re.search(r'(\d{4})[/-](\d{2})[/-](\d{2})', self.subject)
        if match:
            return ''.join(match.groups())
        return None

    def extract_highlights(self):
        if not self.body or not hasattr(self.msg, 'htmlBody') or not self.msg.htmlBody:
            return pd.DataFrame({'Daily Highlights': [''], 'QTD Highlights': ['']})
        soup = BeautifulSoup(self.msg.htmlBody, 'html.parser')
        text = soup.get_text(separator='\n')
        lines = text.splitlines()
        daily, qtd, generic = [], [], []
        i = 0
        while i < len(lines):
            if re.search(r'daily highlights', lines[i], re.IGNORECASE):
                section = [lines[i].strip()]
                i += 1
                while i < len(lines):
                    if (re.match(r'^[A-Z][A-Za-z0-9 &/:-]{2,}$', lines[i].strip()) and not re.search(r'highlights', lines[i], re.IGNORECASE)) or lines[i].strip() == '':
                        break
                    section.append(lines[i].strip())
                    i += 1
                daily.append('\n'.join(section))
            elif re.search(r'qtd highlights', lines[i], re.IGNORECASE):
                section = [lines[i].strip()]
                i += 1
                while i < len(lines):
                    if (re.match(r'^[A-Z][A-Za-z0-9 &/:-]{2,}$', lines[i].strip()) and not re.search(r'highlights', lines[i], re.IGNORECASE)) or lines[i].strip() == '':
                        break
                    section.append(lines[i].strip())
                    i += 1
                qtd.append('\n'.join(section))
            elif re.search(r'highlights', lines[i], re.IGNORECASE):
                section = [lines[i].strip()]
                i += 1
                while i < len(lines):
                    if (re.match(r'^[A-Z][A-Za-z0-9 &/:-]{2,}$', lines[i].strip()) and not re.search(r'highlights', lines[i], re.IGNORECASE)) or lines[i].strip() == '':
                        break
                    section.append(lines[i].strip())
                    i += 1
                generic.append('\n'.join(section))
            else:
                i += 1
        if not daily and not qtd and generic:
            daily = generic
        return pd.DataFrame({
            'Daily Highlights': daily if daily else [''],
            'QTD Highlights': qtd if qtd else ['']
        })

class AttachmentProcessor:
    def __init__(self, msg, output_dir='output'):
        self.msg = msg
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        config = toml.load("secrets.toml")
        self.client = OpenAI(api_key=config["openai"]["api_key"])

    def preprocess_image(self, image_data):
        img = Image.open(io.BytesIO(image_data))
        gray = img.convert('L')
        threshold = 180
        binary = gray.point(lambda x: 0 if x < threshold else 255, '1')
        width, height = binary.size
        resized = binary.resize((width * 2, height * 2), Image.Resampling.LANCZOS)
        resized_gray = resized.convert('L')
        buffer = io.BytesIO()
        resized_gray.save(buffer, format='PNG')
        return buffer.getvalue()

    def find_target_image(self):
        for attachment in self.msg.attachments:
            filename = (attachment.longFilename or attachment.shortFilename).rstrip('\x00')
            if filename.lower().endswith('.png'):
                try:
                    image_bytes = io.BytesIO(attachment.data)
                    image = Image.open(image_bytes)
                    extracted_text = pytesseract.image_to_string(image)
                    if "Total Dynamic Hedge P&L as of" in extracted_text:
                        return attachment.data, filename, extracted_text
                except Exception as e:
                    print(f"Could not perform OCR on {filename}. Error: {e}")
        return None, None, None

    def call_vision_api(self, image_data, extracted_text, date_str):
        preprocessed_image_data = self.preprocess_image(image_data)
        base64_image = base64.b64encode(preprocessed_image_data).decode('utf-8')
        
        # Step 1: Extract raw table data from image using Vision API
        vision_prompt_text = (
            "Extract the main Dynamic Hedge P&L table from this image. "
            "Return ONLY the table data in a simple format that can be easily processed. "
            "Include the title and all rows with their values. "
            "Format as plain text with clear column separators."
        )
        
        print("\n--- Step 1: Extracting raw table data from image ---")
        try:
            response = self.client.chat.completions.create(
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
            raw_table_data = response.choices[0].message.content
            print("Raw table data extracted from image:")
            print(raw_table_data)
            
            # Step 2: Apply the prompt.py logic to transform the data
            print("\n--- Step 2: Applying structured data transformation ---")
            from prompt import get_llm_prompt
            
            # Get the prompt from prompt.py
            llm_prompt = get_llm_prompt(raw_table_data)
            
            # Call LLM to transform the data
            response2 = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "user", "content": llm_prompt}
                ],
                max_tokens=4000
            )
            
            structured_data = response2.choices[0].message.content
            print("Structured data response:")
            print(structured_data)
            
            # Parse the structured JSON data
            try:
                # Extract JSON from the response
                json_start = structured_data.find('[')
                json_end = structured_data.rfind(']') + 1
                if json_start != -1 and json_end != 0:
                    json_str = structured_data[json_start:json_end]
                    data = json.loads(json_str)
                else:
                    print("Could not find JSON array in structured response.")
                    return None
                
                print("--- Parsed Structured Data ---")
                print(json.dumps(data, indent=2))
                
                # Save structured data to Excel
                TableSaver.save_table(data, date_str, self.output_dir)
                
            except Exception as e:
                print(f"Error parsing structured data: {e}")
                
        except Exception as e:
            print(f"--- Error calling OpenAI API ---\n{e}")

class TableSaver:
    @staticmethod
    def save_highlights(df, date_str, output_dir='output'):
        filename = os.path.join(output_dir, f"highlight_{date_str}.xlsx")
        df.to_excel(filename, index=False)
        print(f"Highlights saved to {filename}")

    @staticmethod
    def save_table(data, date_str, output_dir='output'):
        try:
            if isinstance(data, dict) and 'table' in data and 'rows' in data['table'] and 'headers' in data['table']:
                df = pd.DataFrame(data['table']['rows'], columns=data['table']['headers'])
            elif isinstance(data, list) and len(data) > 0 and isinstance(data[0], dict):
                df = pd.DataFrame(data)
            else:
                print("Data is not in a recognized table format for saving as Excel.")
                return
            filename = os.path.join(output_dir, f"table_{date_str}.xlsx")
            df.to_excel(filename, index=False)
            print(f"Table saved to {filename}")
        except Exception as e:
            print(f"Error saving table to Excel: {e}")

def main():
    msg_path = r"/Users/lutianyi/Desktop/excel AI/input/FW_ Daily Hedging P&L Summary for DBIB 2025_06_13.msg"
    output_dir = 'output'
    os.makedirs(output_dir, exist_ok=True)

    email_proc = EmailProcessor(msg_path)
    print("--- Email Analysis ---")
    print(f"Subject: {email_proc.subject}")
    print(f"From: {email_proc.sender}")
    print(f"To: {email_proc.to}")
    print(f"Date: {email_proc.date}")
    print("\n--- Message Body ---")
    print(email_proc.body if email_proc.body else "No message body found.")

    # Extract and save highlights
    highlights_df = email_proc.extract_highlights()
    print("\n--- Extracted Highlights DataFrame ---\n")
    print(highlights_df)
    TableSaver.save_highlights(highlights_df, email_proc.date_str, output_dir)

    # Process attachments
    if not email_proc.msg.attachments:
        print("No attachments found.")
        return

    print("--- Locating Target Image Attachment ---")
    attach_proc = AttachmentProcessor(email_proc.msg, output_dir)
    image_data, filename, extracted_text = attach_proc.find_target_image()
    if image_data:
        print(f"\n--- Sending {filename} to Vision API ---")
        attach_proc.call_vision_api(image_data, extracted_text, email_proc.date_str)
    else:
        print("Could not find the target image in the email attachments.")

if __name__ == "__main__":
    main()