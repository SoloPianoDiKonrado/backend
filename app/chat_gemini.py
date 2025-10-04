import os
import google.generativeai as genai
from dotenv import load_dotenv

class GeminiChat:
    def __init__(self, model_name="gemini-2.5-flash-lite"):
        # Load environment variables from .env file
        load_dotenv()
        self.api_key = os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("API key not found. Please set GEMINI_API_KEY in your .env file.")
        
        # Configure the Gemini client
        genai.configure(api_key=self.api_key)
        
        # Initialize the generative model
        self.model = genai.GenerativeModel(model_name)
        self.chat_session = None

    def start_chat(self, history=None):
        """Starts a new chat session."""
        self.chat_session = self.model.start_chat(history=history or [])
        print("Chat session started.")

    def message(self, user_input: str) -> str:
        """Sends a message to Gemini and returns the response."""
        if not self.chat_session:
            raise ValueError("Chat session not started. Call start_chat() first.")
        
        response = self.chat_session.send_message(user_input)
        return response.text

    def clear_chat(self):
        """Clears the chat session."""
        self.chat_session = None
        print("Chat session cleared.")

# Example usage
if __name__ == "__main__":
    chat = GeminiChat()
    chat.start_chat()
    print(f"User: Hello, Gemini!")
    response_text = chat.message("Hello, Gemini!")
    print(f"Gemini: {response_text}")
    chat.clear_chat()
