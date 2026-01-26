import os

class Config:
    # LLM Settings
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    # Using 'gemini-2.0-flash-exp' as requested, though pricing might be 0 for preview. 
    # We will use Gemini 1.5 Flash rates as a proxy for "Estimated Cost" if it were paid.
    LLM_MODEL_NAME = "gemini-2.0-flash-lite" 
    
    # Ingestion Settings
    MAX_HIERARCHY_DEPTH = 3
    SUBTOPICS_PER_NODE = (3, 5) # (Min, Max) width
    QUESTIONS_PER_LEAF = {
        "beginner": 2,
        "intermediate": 2,
        "advanced": 1
    }

    # Pricing (USD per 1M tokens) - Based on Gemini 1.5 Flash rates as placeholder
    PRICE_PER_1M_INPUT_TOKENS = 0.10
    PRICE_PER_1M_OUTPUT_TOKENS = 0.40
    
    @staticmethod
    def get_api_key():
        if not Config.GEMINI_API_KEY:
            print("⚠️ WARNING: GEMINI_API_KEY not found in environment variables.")
        return Config.GEMINI_API_KEY
