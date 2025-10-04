from __future__ import annotations

from enum import Enum
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field
from typing import Optional, Any, Dict
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

class GenerateYear(BaseModel):
    flavour_text: str
    options: list[GameOption]


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


# Event System Endpoints
from app.event_service import EventService
from app.schemas import GameInterface, EventResponse, GameEvent

# Global event service instance
event_service = EventService()

@app.post("/events/trigger", response_model=EventResponse)
def trigger_event(game_state: GameInterface):
    """
    Wyzwala losowe wydarzenie na podstawie aktualnego stanu gry.
    """
    return event_service.choose_event(game_state)

@app.post("/events/available")
def get_available_events(game_state: GameInterface):
    """
    Zwraca listę dostępnych wydarzeń dla aktualnego stanu gry.
    """
    available_events = event_service.get_available_events(game_state)
    return {
        "available_events": available_events,
        "count": len(available_events)
    }

@app.post("/events/simulate")
def simulate_events(game_state: GameInterface, num_events: int = 5):
    """
    Symuluje wiele wydarzeń dla testowania.
    """
    results = event_service.simulate_multiple_events(game_state, num_events)
    return {
        "simulation_results": results,
        "total_events": len(results),
        "events_occurred": sum(1 for r in results if r.event_occurred)
    }

@app.post("/events/reset")
def reset_events():
    """
    Resetuje listę wyzwolonych wydarzeń.
    """
    event_service.reset_triggered_events()
    return {"message": "Lista wyzwolonych wydarzeń została zresetowana"}

@app.get("/events/info")
def get_events_info():
    """
    Zwraca informacje o systemie wydarzeń.
    """
    return {
        "total_events": len(event_service.EVENTS),
        "triggered_events": list(event_service.triggered_events),
        "available_events_file": str(event_service.EVENTS_FILE)
    }


# AI Event Generation Endpoints
from app.ai_event_generator import AIEventGenerator

# Global AI event generator instance
ai_generator = AIEventGenerator()

@app.post("/events/ai/describe")
def generate_ai_description(event: GameEvent, game_state: GameInterface):
    """
    Generuje opis wydarzenia używając AI.
    """
    description = ai_generator.generate_event_description(event, game_state)
    return {
        "original_description": event.description,
        "ai_description": description,
        "event_name": event.name
    }

@app.post("/events/ai/variation")
def generate_event_variation(base_event: Dict[str, Any], game_state: GameInterface):
    """
    Generuje wariację wydarzenia używając AI.
    """
    variation = ai_generator.generate_event_variation(base_event, game_state)
    return {
        "original_event": base_event,
        "ai_variation": variation
    }

@app.post("/events/ai/generate")
def generate_random_event(game_state: GameInterface, event_type: str = "random"):
    """
    Generuje całkowicie nowe wydarzenie używając AI.
    """
    new_event = ai_generator.generate_random_event(game_state, event_type)
    return {
        "ai_generated_event": new_event,
        "game_state": game_state.dict()
    }

@app.post("/events/ai/trigger_with_description")
def trigger_event_with_ai_description(game_state: GameInterface):
    """
    Wyzwala wydarzenie i generuje AI opis.
    """
    # Najpierw wyzwól wydarzenie
    event_result = event_service.choose_event(game_state)
    
    if event_result.event_occurred and event_result.event:
        # Generuj AI opis
        ai_description = ai_generator.generate_event_description(event_result.event, game_state)
        
        return {
            "event_occurred": True,
            "event": event_result.event,
            "updated_game_state": event_result.updated_game_state,
            "original_description": event_result.event.description,
            "ai_description": ai_description,
            "message": f"Wydarzenie: {event_result.event.name} - {ai_description}"
        }
    
    return event_result
