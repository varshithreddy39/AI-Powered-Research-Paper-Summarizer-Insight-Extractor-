import os
from groq import Groq
from config import Config

def generate_insights(summary_path, output_path):
    """
    Generates high-level critical insights from the paper's summary.
    
    Why: 
    - A standard summary parses *what* the paper says.
    - Insights analyze *why it matters*: finding implications, limitations, and future work.
    - This creates a "Research Assistant" experience rather than just a "Reader".
    """
    try:
        if not os.path.exists(summary_path):
            raise FileNotFoundError(f"Summary file not found: {summary_path}")
            
        with open(summary_path, 'r', encoding='utf-8') as f:
            summary_text = f.read()
            
        client = Groq(api_key=Config.GROQ_API_KEY)
        
        prompt = f"""
        Based on the following summary of a research paper, generate research insights.
        Include:
        1. Key Findings
        2. Core Contributions
        3. Implications of the work
        
        Summary:
        {summary_text}
        
        Insights:
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
        
        insights = chat_completion.choices[0].message.content
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(insights)
            
        return insights
    except Exception as e:
        print(f"Error generating insights: {e}")
        return None
