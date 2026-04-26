import fitz  # PyMuPDF
import io

class DocumentParserError(Exception):
    pass

def extract_text_from_pdf_bytes(pdf_bytes: bytes) -> str:
    """
    Extracts raw text from a PDF file provided as bytes.
    """
    try:
        # Open PDF from memory
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        text_content = []
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            text_content.append(page.get_text())
        
        doc.close()
        return "\n".join(text_content)
    except Exception as e:
        raise DocumentParserError(f"Failed to parse PDF: {str(e)}")

def extract_text_from_file(file_bytes: bytes, filename: str) -> str:
    """
    Extracts text based on the file extension.
    Falls back to trying to decode as utf-8 if not a known binary format.
    """
    if filename.lower().endswith(".pdf"):
        return extract_text_from_pdf_bytes(file_bytes)
    else:
        try:
            return file_bytes.decode("utf-8")
        except UnicodeDecodeError:
            raise DocumentParserError(f"File {filename} is not a valid UTF-8 text file or PDF.")
