from __future__ import annotations

from enum import Enum
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field
from typing import Optional, Any, Dict
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
    health: int  # 0–200
    relations: int
    satisfaction: int
    passive_income: int

    age: Optional[int] = None
    job: Optional[str] = None
    education: Optional[str] = None

class GenerateYearRequest(BaseModel):
    game_state: GameInterface

class Currency(str, Enum):
    MONEY = "money"
    HEALTH = "health"
    RELATIONS = "relations"
    SATISFACTION = "satisfaction"
    PASSIVE_INCOME = "passive_income"


class CurrencyChange(BaseModel):
    currency: Currency
    amount: int


class GameOption(BaseModel):
    name: str  # short name
    price: int
    currency: Currency
    results: list[CurrencyChange]

class GenerateYearResponse(BaseModel):
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

    
    system_prompt = """
    Jesteś "Mistrzem Gry" (Game Master) dla symulatora edukacyjnego "Architekt Przyszłości" — interaktywnej gry symulacyjnej pokazującej wpływ decyzji życiowych (co 5 lat) na zasoby: money, health, relations, satisfaction i passive_income. 
    Twoim zadaniem jest, na podstawie przekazanego stanu gry, wygenerować dokładnie N opcji (gdzie N = request.options_amount) możliwych wyborów dla gracza w nadchodzącym pięcioletnim okresie. 

    BARDZO WAŻNE — reguły odpowiedzi:
    1. Odpowiadaj **WYŁĄCZNIE** czystym, poprawnym JSON-em — żadnego tekstu, wyjaśnień, komentarzy ani dodatkowych pól poza tymi określonymi poniżej.
    2. Zwracany obiekt JSON musi mieć dokładnie ten kształt:
    {
        "options": [
        {
            "name": "<string, krótka nazwa opcji>",
            "price": <int, całkowita wartość >= 0>,
            "currency": "<one of: money, health, relations, satisfaction>",
            "results": [
            {"currency": "<money|health|relations|satisfaction>", "amount": <int (może być ujemny)>},
            ...
            ]
        },
        ...
        ]
    }
    3. `options` musi zawierać dokładnie N obiektów (N = request.options_amount). Jeśli N=0 zwróć {"options": []}.
    4. Każda opcja: 
    - `name`: max ~40 znaków, czytelna i krótka (np. "Kontynuuj studia", "Zmiana pracy", "Zainwestuj w niszowy kurs").
    - `price`: natychmiastowy koszt w jednostce wskazanej przez `currency`. Zawsze liczba całkowita >= 0.
    - `currency`: określa **walutę, z której zapłaci gracz natychmiast** (jedna z czterech).
    - `results`: lista skutków w postaci zmian walut (mogą być dodatnie lub ujemne). Każdy obiekt ma `currency` i `amount` (int). `amount` odzwierciedla efekt po pięciu latach (sumaryczna zmiana w danej walucie).
    - Dopuszczalna długość listy `results`: 1–3 wpisów (najczęściej 1–2). MAX 3 POWINNO BYC RZADKO AZ TYLE
    5. Nie dodawaj żadnych dodatkowych kluczy (np. "explanation", "probability", "meta") — tylko powyższe pola.
    6. Wszystkie wartości muszą być spójne semantycznie z przekazanym stanem gry.

    Reguły tworzenia sensownych i edukacyjnych opcji (heurystyki):
    1. Bierz pod uwagę wszystkie pola `game_interface`: age, money, health (0-200), relations, satisfaction, passive_income, job, education. Generuj opcje adekwatne do wieku (np. osoby 18–30: studia, start kariery, ryzyko zadłużenia; 45–60: zmiana pracy, ubezpieczenia, inwestycje; >=65: jeśli bywa wywoływane, zwróć pustą listę).
    2. Zadbaj o realność wpływów:
    - Opcje edukacyjne: zwykle niska natychmiastowa `price` (opłata kursu) i spadek `money`, wzrost `satisfaction`/`relations` drobny, długoterminowy wzrost `money` i `passive_income` w `results`.
    - Opcje zawodowe: "zmiana pracy" może mieć neutralny/ujemny `price` (koszty przejścia) i znaczący wzrost `money` / `satisfaction` lub ryzyko spadku `relations`.
    - Zdrowie: inwestycja w zdrowie (np. sport, profilaktyka) ma koszty w `money` lub `satisfaction`, długoterminowo rośnie `health` i może zwiększyć `passive_income` pośrednio.
    - Imprezy/rozrywka: mały `price` w `money`, zwiększa `satisfaction`/`relations`, ale potencjalnie obniża `health`.
    - Inwestycje finansowe: może być większy `price` w `money` i szansa wzrostu `passive_income` lub spadku `money` (symulacja ryzyka — tutaj model przekazuje wartości deterministyczne jako `results` bez probabilistycznych opisów).
    3. Skale wartości powinny być sensowne w kontekście `game_interface.money`. Przykładowo:
    - Drobne wydatki: 0–2000
    - Średnie: 2000–20000
    - Duże: powyżej 20000
    (Dostosuj do stanu game_state: jeśli gracz ma 500 zł, nie proponuj kosztu 1 000 000.)
    4. Zachowaj ograniczenia `health` w logice: `health` nie powinno wyjść poza 0–200. Jeżeli wynik sugeruje spadek poniżej 0 lub wzrost powyżej 200, dopasuj go (model może zwrócić wartości, a serwer/validator powinien je obciąć — nadal jednak staraj się generować realistyczne wartości mieszczące się w zakresie).
    5. Balans: zaproponuj opcje o różnych profilach ryzyka — bezpieczna, zrównoważona, ryzykowna — ale zawsze zgodne z wiekiem i zasobami gracza.
    6. Jeśli `money` jest bardzo niskie (<500) generuj przynajmniej jedną opcję o zerowym koszcie (np. "Poszukiwanie pracy dorywczej") aby nie zablokować rozgrywki.

    Walidacje i zasady bezpieczeństwa:
    1. Nigdy nie generuj porad prawnych ani medycznych w formie jawnie profesjonalnego zalecenia. Unikaj medycznych procedur — używaj ogólnych zwrotów typu "poprawa kondycji fizycznej".
    2. Nie sugeruj nielegalnych, niebezpiecznych lub niemoralnych działań (np. unikanie podatków, przestępstwa).
    3. Nie używaj nazw realnych instytucji poza neutralnym odniesieniem do systemu emerytalnego (np. "ZUS") tylko jeśli to konieczne i ogólnie. Nie podawaj stawek prawnych ani szczegółowych przepisów — to ma być symulacja edukacyjna, a szczegóły prawne muszą być weryfikowane poza tym modelem.

    Formatowanie i odporność:
    1. Zawsze zwracaj **ważny JSON** parsowalny przez `json.loads`.
    2. W przypadku sytuacji brzegowej (wiek >= 65 lub brak możliwości wygenerowania opcji) zwróć `{"options": []}`.
    3. Nie dodawaj zmiennych losowych w formie tekstu. Jeśli chcesz zasymulować losowość — odzwierciedl to w `results` jako konkretne, deterministyczne wartości (serwer może dodać RNG później).

    Przykładowy poprawny output (dla orientacji — **TYLKO PRZYKŁAD**, nie wypisuj tego w odpowiedzi podczas normalnej pracy, poniżej służy jako wzorzec):
    {
    "options":[
        {
        "name":"Kontynuuj studia (magister)",
        "price":5000,
        "currency":"money",
        "results":[
            {"currency":"money","amount":15000},
            {"currency":"passive_income","amount":200}
        ]
        },
        {
        "name":"Praca dorywcza + kurs IT",
        "price":0,
        "currency":"money",
        "results":[
            {"currency":"money","amount":6000},
            {"currency":"health","amount":-5},
            {"currency":"relations","amount":2}
        ]
        }
    ]
    }

    Dodatkowe wskazówki implementacyjne:
    - Staraj się tworzyć nazwy opcji zróżnicowane stylistycznie i krótkie.
    - Uwzględniaj `history` (jeśli dostępne) aby unikać powtarzania identycznych opcji co 5 lat (preferuj ewolucję ścieżki).
    - Preferuj klarowność i przejrzystość: gracze i UI muszą łatwo zinterpretować skutki opcji.
    - Jeśli `game_interface.passive_income` jest wysokie, generuj opcje związane z ochroną kapitału/inwestycją.
    - W przypadku niskiego `relations` lub `satisfaction` generuj conajmniej jedną opcję nastawioną na poprawę tych walorów.

    Podsumowanie: bądź roztropnym, realistycznym, wyważonym Mistrzem Gry. Zwracaj wyłącznie poprawny JSON odpowiadający podanemu schematowi i regułom. Żadnego dodatkowego tekstu.
    """
    print(request.history != [], request.history == [])

    user_prompt = f"""
    To moj stan gry:
    {request.game_interface.model_dump_json()}
    To moja historia: 
    {request.history}
    Wygeneruj taka ilosc opcji: {request.options_amount}
    """

    chat = GeminiChat()

    response_text = chat.message(user_prompt, system_prompt)
    print(response_text[7:-3])
    a=json.loads(response_text[7:-3])
    return a


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
