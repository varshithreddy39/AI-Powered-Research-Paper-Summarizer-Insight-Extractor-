import fitz  # PyMuPDF
import os

def extract_text_from_pdf(pdf_path, output_path):
    """
    Extracts raw text from a PDF file using PyMuPDF (fitz).
    
    Why we used PyMuPDF (fitz):
    1. Speed: It is significantly faster than PyPDF2 or PDFMiner.
    2. Accuracy: It handles layout and whitespace preservation better, which is crucial 
       for maintaining the structure of academic papers before finding the summarizer.
    3. Reliability: Supports a wide range of PDF versions and corrupted files.
    """
    try:
        doc = fitz.open(pdf_path)
        text = ""
        for page in doc:
            text += page.get_text() + "\n"
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(text)
            
        return text
    except Exception as e:
        print(f"Error extracting text from PDF: {e}")
        return None

def extract_metadata(text_chunk):
    """
    Extracts structured metadata (Title, Authors, Year, Source) from the first page text.
    
    Why we used an LLM (Groq) here:
    - Traditional regex is brittle for academic papers which have vastly different layouts.
    - The LLM can "read" the context (e.g., distinguishing between an author and an affiliation).
    - We targeted the first 5000 characters as the header info is almost always on the first page.
    """
    try:
        from groq import Groq
        from config import Config
        import json
        
        client = Groq(api_key=Config.GROQ_API_KEY)
        
        prompt = f"""
        Extract the following metadata from the research paper text below.
        
        Guidelines for 'source':
        - Look for Journal names (e.g., "IEEE Access", "Nature"), Conference names (e.g., "ICML 2024"), or Publisher lines (e.g., "Elsevier", "Springer").
        - Check headers and footers.
        - If you see "Member, IEEE", the source might be an IEEE transaction/journal.
        
        Return ONLY a JSON object with these keys: 
        - "title" (string)
        - "authors" (string, comma separated)
        - "year" (string, e.g. "2024")
        - "source" (string, e.g. journal name or conference. Infer from context if not explicit. Return "Unknown" only if absolutely unsure.)

        Text:
        {text_chunk[:5000]}
        
        JSON:
        """
        
        completion = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model=Config.GROQ_MODEL,
            response_format={"type": "json_object"}
        )
        
        return json.loads(completion.choices[0].message.content)
    except Exception as e:
        print(f"Error extracting metadata: {e}")
        return {
            "title": "Unknown Title",
            "authors": "Unknown Authors",
            "year": "Unknown Year",
            "source": "Unknown Source"
        }
