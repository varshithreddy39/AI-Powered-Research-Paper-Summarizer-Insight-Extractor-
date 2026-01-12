import os
import faiss
import pickle
import numpy as np
from sentence_transformers import SentenceTransformer
from config import Config

# Initialize model once (global) to avoid reloading
# Note: In a production app, this might be handled differently
model = SentenceTransformer('all-MiniLM-L6-v2')

def create_embeddings(text_path, doc_id):
    """
    Chunks text, creates embeddings, and saves FAISS index.
    
    Args:
        text_path (str): Path to the text file.
        doc_id (str): Document ID to associate with embeddings.
        
    Returns:
        bool: True if successful, False otherwise.
    """
    try:
        if not os.path.exists(text_path):
            raise FileNotFoundError(f"Text file not found: {text_path}")
            
        with open(text_path, 'r', encoding='utf-8') as f:
            text = f.read()
            
        # Simple chunking by paragraphs or fixed size
        # Using fixed size overlap for better context
        chunk_size = 500
        overlap = 50
        words = text.split()
        chunks = []
        for i in range(0, len(words), chunk_size - overlap):
            chunk = " ".join(words[i:i + chunk_size])
            if len(chunk) > 50: # Ignore very small chunks
                chunks.append(chunk)
        
        if not chunks:
            return False

        embeddings = model.encode(chunks)
        embedding_dim = embeddings.shape[1]
        
        index = faiss.IndexFlatL2(embedding_dim)
        index.add(np.array(embeddings).astype('float32'))
        
        # Save index and chunks
        index_path = os.path.join(Config.EMBEDDINGS_FOLDER, f"{doc_id}.faiss")
        chunks_path = os.path.join(Config.EMBEDDINGS_FOLDER, f"{doc_id}_chunks.pkl")
        
        faiss.write_index(index, index_path)
        with open(chunks_path, 'wb') as f:
            pickle.dump(chunks, f)
            
        return True
    except Exception as e:
        print(f"Error creating embeddings: {e}")
        return False

def search(query, doc_id, k=5):
    """
    Performs semantic search on a specific document.
    
    Args:
        query (str): The search query.
        doc_id (str): The document ID to search within.
        k (int): Number of results to return.
        
    Returns:
        list: List of top-k matching text chunks.
    """
    try:
        index_path = os.path.join(Config.EMBEDDINGS_FOLDER, f"{doc_id}.faiss")
        chunks_path = os.path.join(Config.EMBEDDINGS_FOLDER, f"{doc_id}_chunks.pkl")
        
        if not os.path.exists(index_path) or not os.path.exists(chunks_path):
            return []
            
        index = faiss.read_index(index_path)
        with open(chunks_path, 'rb') as f:
            chunks = pickle.load(f)
            
        query_vector = model.encode([query])
        distances, indices = index.search(np.array(query_vector).astype('float32'), k)
        
        results = []
        for i in range(k):
            idx = indices[0][i]
            if idx < len(chunks):
                results.append(chunks[idx])
                
        return results
    except Exception as e:
        print(f"Error searching: {e}")
        return []
