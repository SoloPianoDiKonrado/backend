import os
from dotenv import load_dotenv
from google import genai
from google.genai.types import GenerateContentConfig, HttpOptions

class GeminiChat:
    def __init__(self, model_name="gemini-2.5-flash-lite"):
        # Load environment variables
        load_dotenv()
        self.api_key = os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("API key not found. Please set GEMINI_API_KEY in your .env file.")
        
        # Initialize the Gemini client
        self.client = genai.Client(api_key=self.api_key)
        self.model_name = model_name

    def message(self, user_input: str, system_prompt: str = None) -> str:
        """Sends a message to Gemini and returns the response."""
        response = self.client.models.generate_content(
            model=self.model_name,
            contents=user_input,
            config=GenerateContentConfig(system_instruction=system_prompt),
        )
        # print(response.text)
        return response.text
