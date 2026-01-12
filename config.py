import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads')
    DATA_FOLDER = os.path.join(BASE_DIR, 'data')
    DOCUMENTS_METADATA = os.path.join(DATA_FOLDER, 'documents')
    EXTRACTED_TEXT_FOLDER = os.path.join(DATA_FOLDER, 'extracted_text')
    SUMMARIES_FOLDER = os.path.join(DATA_FOLDER, 'summaries')
    CONCEPTS_FOLDER = os.path.join(DATA_FOLDER, 'concepts')
    INSIGHTS_FOLDER = os.path.join(DATA_FOLDER, 'insights')
    EMBEDDINGS_FOLDER = os.path.join(DATA_FOLDER, 'embeddings')
    
    GROQ_API_KEY = os.getenv('GROQ_API_KEY')
    GROQ_MODEL = 'llama-3.1-8b-instant'
    # GROQ_MODEL = 'llama-3.1-70b-versatile' # Optional upgrade
    
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024 # 16 MB max upload
    
    # Create directories if they don't exist
    for path in [UPLOAD_FOLDER, DOCUMENTS_METADATA, EXTRACTED_TEXT_FOLDER, 
                 SUMMARIES_FOLDER, CONCEPTS_FOLDER, INSIGHTS_FOLDER, EMBEDDINGS_FOLDER]:
        os.makedirs(path, exist_ok=True)
