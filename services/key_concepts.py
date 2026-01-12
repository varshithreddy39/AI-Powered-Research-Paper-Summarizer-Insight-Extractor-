import os
import json
from groq import Groq
from config import Config

def extract_key_concepts(text_path, output_path):
    """
    Extracts 10 key technical concepts from the research paper.
    
    Why we used this:
    - Discoverability: Helps users find papers by topic tags.
    - Quick Scanning: Users can instantly see if the paper is relevant to their field 
      (e.g., "Deep Learning" vs "Statistical Analysis") without reading the abstract.
    """
    try:
        if not os.path.exists(text_path):
            raise FileNotFoundError(f"Text file not found: {text_path}")
            
        with open(text_path, 'r', encoding='utf-8') as f:
            text = f.read()
            
        truncated_text = text[:15000] 
        
        client = Groq(api_key=Config.GROQ_API_KEY)
        
        prompt = f"""
        Extract the top 10 key technical concepts or keywords from the following research paper text.
        Return ONLY a JSON array of strings. Do not include any other text or explanation.
        
        Text:
        {truncated_text}
        
        Key Concepts (JSON):
        """
        
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            model=Config.GROQ_MODEL,
        )
        
        response_content = chat_completion.choices[0].message.content.strip()
        
        # Simple cleanup to ensure JSON
        if "```json" in response_content:
            response_content = response_content.split("```json")[1].split("```")[0].strip()
        elif "```" in response_content:
            response_content = response_content.split("```")[1].split("```")[0].strip()
            
        concepts = json.loads(response_content)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(concepts, f, indent=4)
            
        return concepts
    except Exception as e:
        print(f"Error extracting key concepts: {e}")
        return None
