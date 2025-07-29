import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
import os
import extract_msg
from PIL import Image
import pytesseract
import tempfile
import uuid
import io
from azure.core.credentials import AzureKeyCredential
from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.ai.documentintelligence.models import AnalyzeDocumentRequest
import pandas as pd

# Tesseract OCR setup - now handled by ConfigManager

# Azure Document Intelligence config (loaded from config manager)
from src.utils.config_manager import ConfigManager

class MsgProcessor:
    def __init__(self):
        # Load configuration
        self.config_manager = ConfigManager()
        
        # Setup Tesseract
        import pytesseract
        pytesseract.pytesseract.tesseract_cmd = self.config_manager.get_tesseract_cmd()
        
        # Load Azure settings from config
        azure_config = self.config_manager.get_azure_config()
        self.azure_endpoint = azure_config.get("endpoint", "")
        self.azure_key = azure_config.get("key", "")
        self.azure_model = "prebuilt-layout"
        
        # Initialize Azure client
        self.azure_client = DocumentIntelligenceClient(
            endpoint=self.azure_endpoint, 
            credential=AzureKeyCredential(self.azure_key)
        )

    def parse_msg_attachments(self, msg_path):
        msg = extract_msg.Message(msg_path)
        attachments = []
        for att in msg.attachments:
            # Sanitize filename and handle missing/invalid names
            filename = att.longFilename or att.shortFilename or f"attachment_{uuid.uuid4().hex}"
            filename = filename.replace('\x00', '').replace('\0', '')
            if not filename.strip():
                filename = f"attachment_{uuid.uuid4().hex}"
            # Only process image files (.png, .jpg, .jpeg)
            if not filename.lower().endswith(('.png', '.jpg', '.jpeg')):
                continue
            att_path = os.path.join(tempfile.gettempdir(), filename)
            with open(att_path, 'wb') as f:
                f.write(att.data)
            attachments.append(att_path)
        return attachments

    def run_tesseract_ocr(self, image_path):
        image = Image.open(image_path)
        text = pytesseract.image_to_string(image)
        return text

    def is_target_image(self, ocr_text):
        # Use the same logic as msg_file_process.py for blue table detection
        return "Total Dynamic Hedge P&L as of" in ocr_text

    def azure_ocr_func(self, image_path):
        # Read image data
        with open(image_path, "rb") as f:
            image_data = f.read()
        poller = self.azure_client.begin_analyze_document(
            self.azure_model, image_data, content_type="image/png"
        )
        result = poller.result()
        
        # Extract full text content from the image (for highlights)
        full_text_content = ""
        if hasattr(result, 'content') and result.content:
            full_text_content = result.content
            print(f"[DEBUG] Azure OCR extracted {len(full_text_content)} characters of text")
            
            # Look for highlights in the full text
            full_text_lower = full_text_content.lower()
            if 'highlight' in full_text_lower or 'daily' in full_text_lower:
                print(f"[DEBUG] Found potential highlights in full text!")
                # Show relevant lines
                lines = full_text_content.split('\n')
                for i, line in enumerate(lines):
                    if 'highlight' in line.lower() or ('daily' in line.lower() and len(line.strip()) > 5):
                        print(f"[DEBUG] Highlights line {i}: {repr(line)}")
        
        # Smart table selection instead of always taking tables[0]
        table_text = ""
        if hasattr(result, 'tables') and result.tables:
            target_table = None
            
            print(f"[DEBUG] Azure OCR found {len(result.tables)} tables")
            
            # Strategy 1: Look for table with P&L characteristics
            for i, table in enumerate(result.tables):
                # Extract table content to analyze
                table_data = [[None for _ in range(table.column_count)] for _ in range(table.row_count)]
                for cell in table.cells:
                    table_data[cell.row_index][cell.column_index] = cell.content
                
                # Convert to string to check content
                table_content = '\n'.join(['\t'.join([str(cell) if cell else '' for cell in row]) for row in table_data])
                table_content_lower = table_content.lower()
                
                print(f"[DEBUG] Table {i}: {table.row_count}x{table.column_count}, preview: {table_content[:100]}...")
                
                # Look for P&L table indicators (in order of priority)
                score = 0
                
                # High priority indicators
                if 'liability' in table_content_lower and 'asset' in table_content_lower:
                    score += 100
                    print(f"[DEBUG] Table {i}: Found Liability+Asset columns (+100)")
                elif 'rider' in table_content_lower and 'asset' in table_content_lower:
                    score += 90
                    print(f"[DEBUG] Table {i}: Found Rider+Asset columns (+90)")
                
                # Medium priority indicators
                if 'p&l' in table_content_lower or 'p&amp;l' in table_content_lower:
                    score += 50
                    print(f"[DEBUG] Table {i}: Found P&L reference (+50)")
                
                if any(keyword in table_content_lower for keyword in ['equity', 'interest rate', 'credit']):
                    score += 30
                    print(f"[DEBUG] Table {i}: Found risk categories (+30)")
                
                # Size-based scoring (P&L tables are typically larger)
                if table.row_count >= 10:
                    score += 20
                    print(f"[DEBUG] Table {i}: Large table {table.row_count} rows (+20)")
                
                if table.column_count >= 4:
                    score += 10
                    print(f"[DEBUG] Table {i}: Wide table {table.column_count} cols (+10)")
                
                print(f"[DEBUG] Table {i} total score: {score}")
                
                # Select table with highest score
                if target_table is None or score > target_table[1]:
                    target_table = (table, score, i)
            
            # Use the best table found
            if target_table is not None:
                best_table, best_score, best_index = target_table
                print(f"[DEBUG] Selected table {best_index} with score {best_score}")
                
                # Extract the selected table
                table_data = [[None for _ in range(best_table.column_count)] for _ in range(best_table.row_count)]
                for cell in best_table.cells:
                    table_data[cell.row_index][cell.column_index] = cell.content
                df = pd.DataFrame(table_data)
                table_text = df.to_string(index=False)
            else:
                print("[DEBUG] No suitable table found, using first table as fallback")
                if result.tables:
                    table = result.tables[0]
                    table_data = [[None for _ in range(table.column_count)] for _ in range(table.row_count)]
                    for cell in table.cells:
                        table_data[cell.row_index][cell.column_index] = cell.content
                    df = pd.DataFrame(table_data)
                    table_text = df.to_string(index=False)
        
        # Return both table and full text content
        return {
            'table_text': table_text,
            'full_text': full_text_content
        }

    def process_msg(self, msg_path, llm_vision_func):
        attachments = self.parse_msg_attachments(msg_path)
        for att_path in attachments:
            try:
                ocr_text = self.run_tesseract_ocr(att_path)
                if self.is_target_image(ocr_text):
                    # Classify with LLM vision model
                    table_type = llm_vision_func(att_path)
                    # Extract table and full text with Azure OCR
                    azure_result = self.azure_ocr_func(att_path)
                    return {
                        "image_path": att_path,
                        "table_type": table_type,  # 'blue' or 'red'
                        "table_text": azure_result['table_text'],
                        "full_text": azure_result['full_text']
                    }
            except Exception as e:
                print(f"Error processing attachment {att_path}: {e}")
        return None 