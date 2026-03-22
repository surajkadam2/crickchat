import os
from dotenv import load_dotenv
from  google import genai
from config import GEMINI_MODEL

# Load environment variables from .env
load_dotenv()

# Configure Gemini API
client =genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

def ask_claude(message: str, temperature: float = 0.0) -> str:
    """
    Sends a message to Claude API and returns the response as plain text.
    
    Wrapper around the Claude API that handles request formatting and response
    extraction. The temperature parameter controls response determinism: 0.0 for
    deterministic SQL generation, higher values for more creative explanations.
    
    Args:
        message (str): The prompt or message to send to Claude.
        temperature (float, optional): Controls response randomness. 0.0 is deterministic,
            higher values (0-2) increase creativity. Defaults to 0.0.
        
    Returns:
        str: The model's response as plain text.
        
    Raises:
        Exception: If API call fails or authentication is invalid.
    """
    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=message,
        config={
            "temperature": temperature
        }
    )
    return response.text


if __name__ == "__main__":
    result = ask_claude("Say hello and tell me what you can do")
    print(result)