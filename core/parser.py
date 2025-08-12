# core/parser.py
import os
from PyPDF2 import PdfReader
from docx import Document
from io import StringIO
import pytesseract
from PIL import Image
import requests
from bs4 import BeautifulSoup


def extract_text_from_pdf(file_path):
    text = ""
    try:
        reader = PdfReader(file_path)
        for page in reader.pages:
            text += page.extract_text() + "\n"
    except Exception as e:
        return f"[PDF ошибка: {e}]"
    return text


def extract_text_from_docx(file_path):
    try:
        doc = Document(file_path)
        return "\n".join([p.text for p in doc.paragraphs])
    except Exception as e:
        return f"[DOCX ошибка: {e}]"


def extract_text_from_doc(file_path):
    try:
        import subprocess
        import tempfile
        temp_docx = tempfile.mktemp(suffix=".docx")
        result = subprocess.run(
            ["unoconv", "-f", "docx", "-o", temp_docx, file_path],
            capture_output=True
        )
        if result.returncode == 0:
            return extract_text_from_docx(temp_docx)
        else:
            return "[DOC: ошибка конвертации]"
    except Exception:
        return "[DOC: установи unoconv]"


def extract_text_from_rtf(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            return f.read()
    except Exception as e:
        return f"[RTF ошибка: {e}]"


def extract_text_from_image(file_path):
    try:
        img = Image.open(file_path)
        return pytesseract.image_to_string(img, lang='rus+eng')
    except Exception as e:
        return f"[OCR ошибка: {e}]"


def extract_text(file_path):
    ext = os.path.splitext(file_path.lower())[1]

    if ext == ".pdf":
        return extract_text_from_pdf(file_path)
    elif ext == ".docx":
        return extract_text_from_docx(file_path)
    elif ext == ".doc":
        return extract_text_from_doc(file_path)
    elif ext == ".txt":
        try:
            for enc in ['utf-8', 'cp1251']:
                with open(file_path, 'r', encoding=enc) as f:
                    return f.read()
        except:
            return "[TXT: ошибка кодировки]"
    elif ext == ".rtf":
        return extract_text_from_rtf(file_path)
    elif ext in [".jpg", ".jpeg", ".png", ".bmp", ".tiff"]:
        return extract_text_from_image(file_path)
    else:
        return f"[Формат {ext} не поддерживается]"
