import os
import json
import uuid
import datetime
from flask import Flask, render_template, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename

from config import Config
from services import pdf_parser, summarizer, key_concepts, research_insights, semantic_search

# Initialize the Flask application
# Why: Flask is used as the lightweight web framework to serve the UI and handle API requests.
app = Flask(__name__)
app.config.from_object(Config)

# Helper: Save document metadata
def save_document_metadata(doc_id, filename, original_filename):
    """
    Saves initial metadata for an uploaded document.
    
    Why: specific metadata (ID, original name, upload date) is needed to track files 
    since we are not using a traditional database. This creates a persistent record 
    mapped to the file on disk.
    """
    metadata = {
        'doc_id': doc_id,
        'filename': filename,
        'original_filename': original_filename,
        'upload_date': datetime.datetime.now().isoformat(),
        'status': 'uploaded' 
    }
    path = os.path.join(Config.DOCUMENTS_METADATA, f"{doc_id}.json")
    with open(path, 'w') as f:
        json.dump(metadata, f, indent=4)
    return metadata

# Helper: Update document status
def update_document_status(doc_id, status_key, value=True):
    """
    Updates specific status flags in the document's metadata file.
    
    Why: To track progress of async or multi-step operations (e.g., 'text_extracted': True) 
    so the UI knows which features are ready to be displayed.
    """
    try:
        path = os.path.join(Config.DOCUMENTS_METADATA, f"{doc_id}.json")
        if os.path.exists(path):
            with open(path, 'r') as f:
                metadata = json.load(f)
            metadata[status_key] = value
            with open(path, 'w') as f:
                json.dump(metadata, f, indent=4)
    except Exception as e:
        print(f"Error updating metadata: {e}")

@app.route('/')
def home():
    """
    Renders the Landing Page.
    Why: The entry point for users to understand the tool's value proposition.
    """
    return render_template('index.html')

@app.route('/dashboard.html')
def dashboard():
    """
    Renders the Main Dashboard.
    Why: The central hub where users can see stats and access their recent documents.
    """
    return render_template('dashboard.html')

@app.route('/upload.html')
def upload_page():
    """
    Renders the Upload Page.
    Why: Dedicated interface for drag-and-drop PDF ingestion.
    """
    return render_template('upload.html')

@app.route('/documents.html')
def documents_page():
    """
    Renders the Document History Page.
    
    Why: Users need a way to browse previous uploads.
    Implementation: Reads all JSON metadata files from disk and sorts them by date
    to display a chronological list.
    """
    # Load all documents for history
    docs = []
    if os.path.exists(Config.DOCUMENTS_METADATA):
        for filename in os.listdir(Config.DOCUMENTS_METADATA):
            if filename.endswith('.json'):
                try:
                    with open(os.path.join(Config.DOCUMENTS_METADATA, filename), 'r') as f:
                        docs.append(json.load(f))
                except:
                    pass
    
    # Sort by date descending
    docs.sort(key=lambda x: x.get('upload_date', ''), reverse=True)
    return render_template('documents.html', documents=docs)

@app.route('/documents', methods=['GET'])
def get_documents():
    """
    API Enpoint: Get all documents.
    Why: Provides a JSON list of documents for dynamic frontend consumption (e.g. dashboard widgets).
    """
    docs = []
    if os.path.exists(Config.DOCUMENTS_METADATA):
        for filename in os.listdir(Config.DOCUMENTS_METADATA):
            if filename.endswith('.json'):
                try:
                    with open(os.path.join(Config.DOCUMENTS_METADATA, filename), 'r') as f:
                        docs.append(json.load(f))
                except:
                    pass
    docs.sort(key=lambda x: x.get('upload_date', ''), reverse=True)
    return jsonify(docs)

@app.route('/upload', methods=['POST'])
def upload_file():
    """
    API Endpoint: Handle File Upload.
    
    Why: Receives the binary PDF file, saves it securely to the `uploads/` directory,
    and generates a unique ID to track it throughout the pipeline.
    """
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    if file:
        filename = secure_filename(file.filename)
        doc_id = str(uuid.uuid4())
        save_name = f"{doc_id}_{filename}"
        file_path = os.path.join(Config.UPLOAD_FOLDER, save_name)
        file.save(file_path)
        
        save_document_metadata(doc_id, save_name, filename)
        
        return jsonify({'message': 'File uploaded successfully', 'doc_id': doc_id, 'filename': filename}), 200

@app.route('/extract-text', methods=['POST'])
def extract_text():
    """
    API Endpoint: Extract Text & Metadata.
    
    Why: Converts the raw PDF binary into machine-readable text using `pdf_parser`.
    Also triggers the initial metadata extraction (Title, Authors, Source) to populate the UI.
    """
    data = request.json
    doc_id = data.get('doc_id')
    if not doc_id:
        return jsonify({'error': 'doc_id is required'}), 400
    
    # Find file path from metadata
    meta_path = os.path.join(Config.DOCUMENTS_METADATA, f"{doc_id}.json")
    if not os.path.exists(meta_path):
        return jsonify({'error': 'Document not found'}), 404
        
    with open(meta_path, 'r') as f:
        metadata = json.load(f)
        
    pdf_path = os.path.join(Config.UPLOAD_FOLDER, metadata['filename'])
    output_path = os.path.join(Config.EXTRACTED_TEXT_FOLDER, f"{doc_id}.txt")
    
    # Extract text if not already extracted
    text = None
    if os.path.exists(output_path):
        with open(output_path, 'r', encoding='utf-8') as f:
            text = f.read()
    else:
        text = pdf_parser.extract_text_from_pdf(pdf_path, output_path)
        
    if text:
        update_document_status(doc_id, 'text_extracted')
        
        # Extract metadata
        metadata_info = pdf_parser.extract_metadata(text)
        
        # Update stored metadata (optional, merge with existing)
        try:
             with open(meta_path, 'r') as f:
                current_meta = json.load(f)
             current_meta.update(metadata_info)
             with open(meta_path, 'w') as f:
                json.dump(current_meta, f, indent=4)
        except Exception as e:
            print(f"Error saving metadata info: {e}")
            
        semantic_search.create_embeddings(output_path, doc_id)
        
        return jsonify({
            'text': text,
            'metadata': metadata_info
        }), 200
    else:
        return jsonify({'error': 'Failed to extract text'}), 500

@app.route('/summarize', methods=['POST'])
def summarize():
    """
    API Endpoint: Generate Summary.
    
    Why: Uses the LLM to create a structured summary (Objectives, Methods, Findings). 
    This is the core value proposition of the tool.
    """
    data = request.json
    doc_id = data.get('doc_id')
    if not doc_id:
        return jsonify({'error': 'doc_id is required'}), 400
        
    text_path = os.path.join(Config.EXTRACTED_TEXT_FOLDER, f"{doc_id}.txt")
    output_path = os.path.join(Config.SUMMARIES_FOLDER, f"{doc_id}.txt")
    
    summary = None
    if os.path.exists(output_path):
        with open(output_path, 'r', encoding='utf-8') as f:
            summary = f.read()
    else:
        summary = summarizer.generate_summary(text_path, output_path)
        
    if summary and not summary.startswith("Failed") and not summary.startswith("Error") and not summary.startswith("Critical"):
        update_document_status(doc_id, 'summary_generated')
        return jsonify({'summary': summary}), 200
    else:
        # Pass the specific error message to the frontend
        error_msg = summary if summary else "Unknown generation error"
        return jsonify({'error': error_msg}), 500

@app.route('/key-concepts', methods=['POST'])
def get_key_concepts():
    """
    API Endpoint: Extract Key Technical Concepts.
    
    Why: Returns a list of keywords/tags that help the user quickly skim 
    the paper's main topics without reading the full text.
    """
    data = request.json
    doc_id = data.get('doc_id')
    if not doc_id:
        return jsonify({'error': 'doc_id is required'}), 400
        
    text_path = os.path.join(Config.EXTRACTED_TEXT_FOLDER, f"{doc_id}.txt")
    output_path = os.path.join(Config.CONCEPTS_FOLDER, f"{doc_id}.json")
    
    concepts = None
    if os.path.exists(output_path):
        with open(output_path, 'r', encoding='utf-8') as f:
            concepts = json.load(f)
    else:
        concepts = key_concepts.extract_key_concepts(text_path, output_path)
        
    if concepts:
        update_document_status(doc_id, 'concepts_extracted')
        return jsonify({'concepts': concepts}), 200
    else:
        return jsonify({'error': 'Failed to extract concepts'}), 500

@app.route('/insights', methods=['POST'])
def get_insights():
    """
    API Endpoint: Generate Research Insights.
    
    Why: Moves beyond simple summarization to provide critical analysis, 
    implications, and future research directions suitable for PhDs/scientists.
    """
    data = request.json
    doc_id = data.get('doc_id')
    if not doc_id:
        return jsonify({'error': 'doc_id is required'}), 400
        
    # Insights depend on summary, so check if summary exists, else generate it
    summary_path = os.path.join(Config.SUMMARIES_FOLDER, f"{doc_id}.txt")
    if not os.path.exists(summary_path):
       
        text_path = os.path.join(Config.EXTRACTED_TEXT_FOLDER, f"{doc_id}.txt")
        if not summarizer.generate_summary(text_path, summary_path):
             return jsonify({'error': 'Summary required for insights and failed to generate'}), 500

    output_path = os.path.join(Config.INSIGHTS_FOLDER, f"{doc_id}.txt")
    
    insights = None
    if os.path.exists(output_path):
        with open(output_path, 'r', encoding='utf-8') as f:
            insights = f.read()
    else:
        insights = research_insights.generate_insights(summary_path, output_path)
        
    if insights:
        update_document_status(doc_id, 'insights_generated')
        return jsonify({'insights': insights}), 200
    else:
        return jsonify({'error': 'Failed to generate insights'}), 500

@app.route('/semantic-search', methods=['POST'])
def perform_semantic_search():
    """
    API Endpoint: Verify Semantic Search.
    
    Why: Allows users to query the document using natural language (e.g. "What was the accuracy?")
    and find relevant sections based on meaning, not just keywords.
    """
    data = request.json
    doc_id = data.get('doc_id')
    query = data.get('query')
    if not doc_id or not query:
        return jsonify({'error': 'doc_id and query are required'}), 400
        
    results = semantic_search.search(query, doc_id)
    return jsonify({'results': results}), 200

@app.route('/api/dashboard', methods=['GET'])
def get_dashboard_data():
    """
    API Endpoint: Dashboard Analytics.
    
    Why: Aggregates simple metrics (total files, summaries) and lists recent activity 
    to populate the main dashboard charts and widgets.
    """
    files_uploaded = len([f for f in os.listdir(Config.UPLOAD_FOLDER) if f != '.gitignore']) if os.path.exists(Config.UPLOAD_FOLDER) else 0
    summaries_generated = len([f for f in os.listdir(Config.SUMMARIES_FOLDER) if f != '.gitignore']) if os.path.exists(Config.SUMMARIES_FOLDER) else 0
    insights_generated = len([f for f in os.listdir(Config.INSIGHTS_FOLDER) if f != '.gitignore']) if os.path.exists(Config.INSIGHTS_FOLDER) else 0
    
    # Get recent docs (limit 5)
    recent_docs = []
    if os.path.exists(Config.DOCUMENTS_METADATA):
        for filename in os.listdir(Config.DOCUMENTS_METADATA):
            if filename.endswith('.json'):
                try:
                    with open(os.path.join(Config.DOCUMENTS_METADATA, filename), 'r') as f:
                        recent_docs.append(json.load(f))
                except:
                    pass
    recent_docs.sort(key=lambda x: x.get('upload_date', ''), reverse=True)
    recent_docs = recent_docs[:5]
    
    return jsonify({
        'stats': {
            'uploaded': files_uploaded,
            'summaries': summaries_generated,
            'insights': insights_generated,
            'queue': 0 
        },
        'recent_documents': recent_docs
    })

if __name__ == '__main__':
    app.run(debug=True, port=5001)
