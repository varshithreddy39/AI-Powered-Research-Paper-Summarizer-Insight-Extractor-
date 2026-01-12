# AI Research Paper Summarizer & Insight Extraction Platform

A research intelligence platform that allows users to upload academic PDFs and automatically generate summaries, key concepts, research insights, and perform semantic search.

## Features

- **PDF Upload**: Upload academic PDFs for analysis.
- **Raw Text Extraction**: Extracts and displays raw text from the PDF.
- **Summarization**: Generates an executive summary using LLaMA-3 (via Groq API).
- **Key Concepts**: Extracts top technical keywords/concepts.
- **Research Insights**: Generates findings, contributions, and implications.
- **Semantic Search**: Search through the document using semantic embeddings.
- **Document History**: View previously uploaded documents.

## Tech Stack

- **Backend**: Flask (Python 3.9+)
- **LLM**: Groq API (llama-3.1-8b-instant)
- **Vector Search**: Sentence Transformers (all-MiniLM-L6-v2) + FAISS
- **Frontend**: HTML5, CSS3, JavaScript (Vanilla)

## Setup

1. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Environment Variables:**
   Create a `.env` file in the root directory:
   ```env
   GROQ_API_KEY=your_groq_api_key_here
   ```

3. **Run the Application:**
   ```bash
   python app.py
   ```

4. **Access:**
   Open [http://localhost:5001](http://localhost:5001) in your browser.

## File Structure

- `app.py`: Main Flask application.
- `services/`: Specific logic for each feature (parsing, AI, search).
- `templates/`: HTML files.
- `static/`: CSS, JS, and uploads.
- `data/`: JSON metadata, text files, and embeddings.
