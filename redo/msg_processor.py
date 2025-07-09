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

pytesseract.pytesseract.tesseract_cmd = "/opt/homebrew/bin/tesseract"

# Azure Document Intelligence config (fill with your actual values or load from secrets)
AZURE_ENDPOINT = "https://awuodnaiow.cognitiveservices.azure.com/"
AZURE_KEY = "uQV0tGnvfL7t6tzDHcSn1nu6hGDXPJsfjuCCcO3KBxzV6wGbA61MJQQJ99BGACYeBjFXJ3w3AAALACOGWMO3"
AZURE_MODEL = "prebuilt-layout"

class MsgProcessor:
    def __init__(self, llm_vision_func):
        self.llm_vision_func = llm_vision_func  # Function to call LLM vision model
        self.azure_client = DocumentIntelligenceClient(
            endpoint=AZURE_ENDPOINT, credential=AzureKeyCredential(AZURE_KEY)
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
            AZURE_MODEL, image_data, content_type="image/png"
        )
        result = poller.result()
        # Extract first table as DataFrame
        if hasattr(result, 'tables') and result.tables:
            table = result.tables[0]
            table_data = [[None for _ in range(table.column_count)] for _ in range(table.row_count)]
            for cell in table.cells:
                table_data[cell.row_index][cell.column_index] = cell.content
            df = pd.DataFrame(table_data)
            return df.to_string(index=False)
        else:
            return ""

    def process_msg(self, msg_path):
        attachments = self.parse_msg_attachments(msg_path)
        for att_path in attachments:
            try:
                ocr_text = self.run_tesseract_ocr(att_path)
                if self.is_target_image(ocr_text):
                    # Classify with LLM vision model
                    table_type = self.llm_vision_func(att_path)
                    # Extract table with Azure OCR
                    table_text = self.azure_ocr_func(att_path)
                    return {
                        "image_path": att_path,
                        "table_type": table_type,  # 'blue' or 'red'
                        "table_text": table_text
                    }
            except Exception as e:
                print(f"Error processing attachment {att_path}: {e}")
        return None 