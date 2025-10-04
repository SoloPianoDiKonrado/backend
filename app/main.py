from __future__ import annotations

from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel
from typing import Optional, Any
import os
from dotenv import load_dotenv

# Załaduj zmienne środowiskowe
load_dotenv()
from .chat_gemini import GeminiChat

# Globalna instancja chatu (dla pojedynczego użytkownika)
chat_instance: Optional[GeminiChat] = None

# Modele Pydantic dla request/response
class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    response: str
    status: str
    model: str
    error: Optional[str] = None

app = FastAPI(
    title="Chat with Gemini API",
    description="API do czatu z Google Gemini",
    version="1.1.0"
)

@app.on_event("startup")
def startup_event():
    print(os.getenv("GEMINI_API_KEY"))
    """Inicjalizuje instancję chatu podczas startu aplikacji."""
    initialize_chat()

@app.get("/")
def read_root():
    return {
        "message": "Witaj wariacik! API działa jak należy 🚀",
        "docs": "/docs",
        "redoc": "/redoc",
        "chat_endpoints": {
            "chat": "/chat - wysyłanie wiadomości",
            "clear": "/clear - czyszczenie historii rozmowy",
        }
    }

@app.get("/health")
def health_check():
    return {"status": "healthy"}

# Funkcja pomocnicza do inicjalizacji chatu
def initialize_chat():
    """Inicjalizuje instancję chatu jeśli jeszcze nie istnieje."""
    global chat_instance
    if chat_instance is None:
        try:
            chat_instance = GeminiChat()
            chat_instance.start_chat()
        except ValueError as e:
            # Jeśli klucz API nie jest dostępny, aplikacja nie będzie mogła w pełni działać
            # Logujemy błąd, ale nie przerywamy startu serwera
            print(f"Błąd inicjalizacji chatu: {str(e)}")

# Funkcja pomocnicza do pobrania instancji chatu
def get_chat_instance() -> GeminiChat:
    """Pobiera instancję chatu, zgłaszając błąd jeśli nie jest dostępna."""
    if chat_instance is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Chat service is not available. Check API key."
        )
    return chat_instance

@app.post("/chat", response_model=ChatResponse)
def chat(message: ChatRequest) -> ChatResponse:
    """
    Endpoint do wysyłania wiadomości do modelu Gemini.
    """
    chat = get_chat_instance()
    try:
        response_text = chat.message(message.message)
        return ChatResponse(
            response=response_text,
            status="success",
            model=chat.model.model_name
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@app.delete("/clear")
def clear_history():
    """
    Endpoint do czyszczenia historii rozmowy.
    """
    chat = get_chat_instance()
    chat.clear_chat()
    # Po wyczyszczeniu, musimy ponownie zainicjować sesję czatu
    chat.start_chat()

    return {
        "message": "Historia rozmowy została wyczyszczona",
        "status": "success"
    }
