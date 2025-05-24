# Extract text from PDFs
import os
import PyPDF2

def extract_text_from_pdf(pdf_path):
    """Extract text from PDF file"""
    try:
        if not os.path.exists(pdf_path):
            print(f"File not found: {pdf_path}")
            return None
            
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            text = ""
            for page_num in range(len(reader.pages)):
                page = reader.pages[page_num]
                text += page.extract_text() or ""
            return text
    except Exception as e:
        print(f"Error extracting: {e}")
        return None

if __name__ == '__main__':
    test_path = "../data/CV_Bryan.pdf"
    text = extract_text_from_pdf(test_path)
    if text:
        print(f"Extracted {len(text)} characters")
    else:
        print("Extraction failed")