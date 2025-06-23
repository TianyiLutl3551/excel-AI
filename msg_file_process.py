import extract_msg
import os
import pytesseract
from PIL import Image
import io
import base64
import toml
from openai import OpenAI
import pandas as pd
from datetime import datetime
import json

# --- Load secrets and initialize OpenAI client ---
config = toml.load("secrets.toml")
api_key = config["openai"]["api_key"]
client = OpenAI(api_key=api_key)

msg_path = r"/Users/lutianyi/Desktop/excel AI/input/FW_ Daily Hedging P&L Summary for DBIB 2025_06_13.msg"
msg = extract_msg.Message(msg_path)

print("--- Email Analysis ---")
print(f"Subject: {msg.subject}\n")

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
        
        # 1. Encode the image data in base64
        base64_image = base64.b64encode(target_image_data).decode('utf-8')

        # 2. Create the prompt for the Vision API
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
        
        print("Image encoded and prompt created.")
        print("Next step: Call the OpenAI Vision API with this data.")

        try:
            # 3. Send the image to the Vision API
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
            
            # Parse JSON response and save to Excel
            try:
                # Try to extract JSON from the response (in case there's extra text)
                json_start = response_content.find('{')
                json_end = response_content.rfind('}') + 1
                if json_start != -1 and json_end != 0:
                    json_str = response_content[json_start:json_end]
                    data = json.loads(json_str)
                    
                    # Generate output filename
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    output_excel_path = os.path.join("output", f"financial_report_{timestamp}.xlsx")
                    
                    # Save table to Excel
                    with pd.ExcelWriter(output_excel_path, engine='openpyxl') as writer:
                        # Handle single table format
                        if 'table' in data:
                            table = data['table']
                            sheet_name = "P&L_Table"
                            df = pd.DataFrame(table['rows'], columns=table['headers'])
                            df.to_excel(writer, sheet_name=sheet_name, index=False)
                            print(f"Saved {table['title']} to sheet {sheet_name}")
                        # Handle legacy tables array format
                        elif 'tables' in data:
                            for i, table in enumerate(data.get('tables', [])):
                                sheet_name = f"Table_{i+1}"
                                df = pd.DataFrame(table['rows'], columns=table['headers'])
                                df.to_excel(writer, sheet_name=sheet_name, index=False)
                                print(f"Saved {table['name']} to sheet {sheet_name}")
                        
                        # Save summary data to a separate sheet if it exists
                        if 'summary' in data:
                            summary_df = pd.DataFrame(list(data['summary'].items()), 
                                                    columns=['Field', 'Value'])
                            summary_df.to_excel(writer, sheet_name='Summary', index=False)
                            print("Saved summary data to sheet Summary")
                    
                    print(f"\n[+] Successfully saved structured data to: {output_excel_path}")
                    
                else:
                    print("Could not find JSON in response. Saving raw text...")
                    # Fallback: save raw response to text file
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    output_text_path = os.path.join("output", f"raw_response_{timestamp}.txt")
                    with open(output_text_path, 'w') as f:
                        f.write(response_content)
                    print(f"Saved raw response to: {output_text_path}")
                    
            except json.JSONDecodeError as e:
                print(f"JSON parsing error: {e}")
                print("Saving raw response to text file...")
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_text_path = os.path.join("output", f"raw_response_{timestamp}.txt")
                with open(output_text_path, 'w') as f:
                    f.write(response_content)
                print(f"Saved raw response to: {output_text_path}")
            
        except Exception as e:
            print(f"\n--- Error calling OpenAI API ---")
            print(e)
    else:
        print("\nCould not find the target image in the email attachments.")