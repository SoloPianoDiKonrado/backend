from __future__ import annotations

from enum import Enum
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field
from typing import Optional, Any
import json
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

class GameInterface(BaseModel):
    money: int
    health: int #0-200
    relations: int
    satisfaction: int
    passive_income: int

    age: int
    job: str
    education: str

class GenerateYearRequest(BaseModel):
    game_state: GameInterface

class Currency(str, Enum):
    MONEY = "money"
    HEALTH = "health"
    RELATIONS = "relations"
    SATISFACTION = "satisfaction"


class CurrencyChange(BaseModel):
    currency: Currency
    amount: int


class GameOption(BaseModel):
    name: str  # short name
    price: int
    currency: Currency
    results: list[CurrencyChange]

class GenerateYearResponse(BaseModel):
    flavour_text: str
    options: list[GameOption]

class GameHistory(BaseModel):
    options: list[GameOption]

class GenerateYearRequest(BaseModel):
    game_interface: GameInterface
    options_amount: int
    history: list[GameHistory]

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


@app.post("/generate_year", response_model=GenerateYearResponse)
def generate_year(request: GenerateYearRequest) -> GenerateYearResponse:
    """
    Generates a new year in the game based on the current game state.
    """
    chat = get_chat_instance()

    # The system prompt is intentionally left empty as per the user's request.
    # It can be filled in later with instructions for the model.
    system_prompt = ""

    user_prompt = f"""
    Jesteś Mistrzem Gry w symulatorze "Bieg przez życie". Twoim celem jest tworzenie klarownych, lat życia. Zawsze odpowiadaj WYŁĄCZNIE w formacie JSON.
    **Zasady generowania:**
    1.  **Format odpowiedzi:** Zawsze zwracaj poprawny JSON.
    Stan gry:
    {request.game_state.json()}

    Proszę podać odpowiedź w prawidłowym formacie JSON, zgodnie ze strukturą modelu GenerateYearResponse.
    Odpowiedź powinna być obiektem JSON z dwoma kluczami: 'flavour_text' (ciąg znaków) i 'options' (lista obiektów).
    Każdy obiekt opcji musi mieć następujące klucze: 'name' (ciąg znaków), 'price' (liczba całkowita), 'currency' (jedno z: 'money', 'health', 'relations', 'satisfaction') i 'results' (lista obiektów zmian waluty).
    Każdy obiekt zmiany waluty musi mieć klucze 'currency' i 'amount'.
    """


    try:
        response_text = chat.message(user_prompt)
        # Assuming the model returns a JSON string, we parse it.
        response_json = json.loads(response_text)
        return GenerateYearResponse(**response_json)
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to decode JSON from model response."
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred: {str(e)}"
        )


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
