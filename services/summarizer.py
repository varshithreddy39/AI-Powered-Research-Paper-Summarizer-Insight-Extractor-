import os
from groq import Groq
from config import Config

def generate_summary(text_path, output_path, max_chars=80000):
    """
    Generates a structured research summary using the Groq API.
    
    Why we used a "Recursive Retry" strategy:
    - Context Window Limits: Large papers often exceed the 8k/32k token limits of models.
    - Resilience: Instead of crashing, the function automatically tries to reduce the input size
      (80k -> 40k -> 20k chars) until it fits, ensuring a user always gets a summary 
      rather than an error.
    """
    try:
        if not os.path.exists(text_path):
            return "Error: Text file not found."
            
        with open(text_path, 'r', encoding='utf-8') as f:
            text = f.read()
            
        # Recursive fallback strategy
        current_chars = max_chars
        min_chars = 10000 # Minimum useful context
        
        while current_chars >= min_chars:
            try:
                print(f"Attempting summary with {current_chars} chars...")
                truncated_text = text[:current_chars]
                
                client = Groq(api_key=Config.GROQ_API_KEY)
                
                prompt = f"""
                You are an expert academic researcher. Provide a comprehensive, high-quality structured summary of the following research paper.
                
                Structure your response exactly as follows (use Markdown):
                ### Executive Summary
                (A concise high-level overview.)
                ### Objectives
                (Research questions or hypotheses.)
                ### Methodology
                (Methods, materials, data sources.)
                ### Key Findings
                (Important quantitative and qualitative results.)
                ### Conclusion
                (Implications and future work.)

                Text:
                {truncated_text}
                
                Summary:
                """
                
                chat_completion = client.chat.completions.create(
                    messages=[{"role": "user", "content": prompt}],
                    model=Config.GROQ_MODEL,
                    temperature=0.5, # Lower temperature for stability
                    max_tokens=6000, # Ensure enough output space
                )
                
                summary = chat_completion.choices[0].message.content
                
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(summary)
                    
                return summary
                
            except Exception as e:
                print(f"Failed with {current_chars} chars: {e}")
                current_chars = int(current_chars / 2) # Halve the context
                if current_chars < min_chars:
                     return f"Failed to generate summary: {str(e)}"
        
        return "Failed: Text too complex or API limits reached."

    except Exception as e:
        print(f"Critical error in summarizer: {e}")
        return f"Critical error: {str(e)}"
