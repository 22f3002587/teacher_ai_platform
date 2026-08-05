import fitz
from PIL import Image
import pytesseract
import io
import shutil

tesseract_path = shutil.which("tesseract") or r"C:\Program Files\Tesseract-OCR\tesseract.exe"
pytesseract.pytesseract.tesseract_cmd = tesseract_path

class DocumentParser:
    def parse(self, pdf_path: str):
        doc = fitz.open(pdf_path)
        pages = []

        for page_number, page in enumerate(doc):
            text = page.get_text("text")

            if not text.strip():
                pix = page.get_pixmap(dpi=300)
                img = Image.open(io.BytesIO(pix.tobytes("png")))
                text = pytesseract.image_to_string(img)

            pages.append({"page": page_number + 1, "text": text})

        return {"num_pages": len(doc), "pages": pages}
