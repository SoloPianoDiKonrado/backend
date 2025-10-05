from __future__ import annotations

from enum import Enum
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field
from typing import Optional, Any, Dict
import json
import os
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware
from app.summary_service import SummaryService
from app.schemas import GameSummaryRequest, GameSummaryResponse, GenerateYearResponse, GameInterface, GenerateYearRequest

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

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # zezwól na wszystkie domeny
    allow_credentials=True,
    allow_methods=["POST", "GET", "OPTIONS"],
    allow_headers=["Content-Type", "Accept"],
)

# Import additional modules for IP logging
from fastapi import Request
import logging
import datetime

# Configure logging for IP tracking
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ip_logger")

# IP Logger Middleware
@app.middleware("http")
async def log_ip_middleware(request: Request, call_next):
    """
    Middleware to log IP addresses of incoming requests.
    """
    # Get client IP address
    client_ip = request.client.host if request.client else "unknown"

    # Get additional request info
    method = request.method
    url_path = request.url.path
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Log the request
    logger.info(f"[{timestamp}] IP: {client_ip} - Method: {method} - Path: {url_path}")

    # Continue processing the request
    response = await call_next(request)
    return response

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
# System Prompt: Mistrz Gry - "Architekt Przyszłości"

## OPTYMALIZACJA WYDAJNOŚCI
⚠️ KRYTYCZNE: Generuj odpowiedzi SZYBKO. Flash-lite wykonuje to w 2s - utrzymuj tę prędkość. Żadnego rozwlekania, tylko konkretny JSON.

---

## TWOJA ROLA
Jesteś "Mistrzem Gry" dla edukacyjnego symulatora życiowego. Generujesz N opcji decyzyjnych (N = request.options_amount) dla kolejnego 5-letniego okresu, wpływających na: money, health, relations, satisfaction, passive_income.

---

## FORMAT ODPOWIEDZI (BEZWZGLĘDNIE OBOWIĄZUJĄCY)

Zwracaj TYLKO ten JSON (zero tekstu poza nim):
{
  "options": [
    {
      "name": "string max 40 znaków",
      "price": 0,
      "currency": "money|health|relations|satisfaction",
      "is_work_related": false,
      "job_name": "string (tylko gdy is_work_related=true)", bardzo ważne!
      "results": [
        {"currency": "money|health|relations|satisfaction|passive_income", "amount": -1000}
      ]
    }
  ]
}
Wymagania strukturalne:
- Dokładnie N opcji w tablicy (N z requestu)
- price: int >= 0 (koszt natychmiastowy)
- currency: waluta kosztu (jedna z czterech, BEZ passive_income)
- is_work_related: true = nowa praca/awans/firma; false = edukacja/hobby/inwestycje
- job_name: wymagane gdy is_work_related=true
- results: 1-3 efekty (rzadko 3!), amount może być ujemny
- degree: stopien naukowy - w przypadku jesli akcja jest studiami np. name: Studia magisterskie - degree: magister 
---

## MECHANIZM ANTY-POWTÓRZEŃ (KLUCZOWE!)

Zasada unikania duplikatów:
1. Śledź kontekst historii: Jeśli gracz właśnie skończył studia - NIE proponuj ponownie studiów
2. Rotacja tematów: W każdym wywołaniu mieszaj kategorie:
   - Kariera (30-40%)
   - Finanse/inwestycje (20-30%)
   - Zdrowie/lifestyle (15-25%)
   - Relacje/rozwój osobisty (15-25%)

3. Warianty w obrębie kategorii:
   ZŁE: "Kurs programowania" → "Kurs programowania Python" → "Bootcamp programowania"
   DOBRE: "Kurs programowania" → "Specjalizacja DevOps" → "Freelancing IT"

4. Różnicuj skalę i ryzyko:
   - Opcja bezpieczna (małe zmiany, pewne efekty)
   - Opcja zrównoważona (średnie nakłady, proporcjonalne efekty)
   - Opcja ryzykowna/ambitna (duże nakłady LUB niepewny wynik)

5. Progresja kariery - ograniczenia:
   - MAX 1 awans na 10 lat (2 cykle)
   - Założenie firmy: wymaga doświadczenia (>=10 lat pracy LUB passive_income >5000)
   - Brak teleportacji: Junior → Mid → Senior → Lead (nie przeskakuj!)

---

## KONTEKSTOWA GENERACJA OPCJI

Analiza stanu gracza (game_interface):
Przed generowaniem sprawdź:
wiek = game_interface.age
majątek = game_interface.money
dochód_pasywny = game_interface.passive_income
stan_zdrowia = game_interface.health
wykształcenie = game_interface.education
praca = game_interface.job
stan_cywilny = game_interface.married

Matryce decyzyjne wg wieku:

18-25 lat (Start)
- Edukacja (40%): studia, kursy zawodowe, certyfikaty
- Pierwsza praca (30%): staże, juniorskie stanowiska
- Relacje (20%): budowanie sieci kontaktów, hobby
- Lifestyle (10%): sport, podróże niskobudżetowe

26-35 lat (Budowa)
- Rozwój kariery (35%): specjalizacja, awans, zmiana branży
- Inwestycje (25%): mieszkanie, akcje, oszczędności
- Rodzina (20%): ślub (jeśli married=false), planowanie
- Edukacja (20%): MBA, kursy zaawansowane

36-50 lat (Stabilizacja)
- Optymalizacja finansowa (40%): nieruchomości, portfel, emerytury
- Zdrowie (25%): profilaktyka, sport, ubezpieczenia
- Kariera senior (20%): ekspertyza, mentoring, konsulting
- Work-life balance (15%): hobby, rodzina, redukcja stresu

51-64 lat (Przygotowanie)
- Zabezpieczenie emerytury (45%): inwestycje pasywne, wyprzedaż aktywów
- Zdrowie profilaktyczne (30%): badania, leczenie
- Praca part-time (15%): konsulting, przekazanie wiedzy
- Pasje (10%): podróże, realizacja marzeń

>=65 lat
{"options": []}

---

## REALISTYCZNE WYCENY (Polska 2024+)

Skale kosztów:
Mikroinwestycje (500-2000): Kurs online, siłownia roczna
Małe wydatki (2000-10000): Certyfikat branżowy, weekend za granicą
Średnie inwestycje (10000-50000): Studia podyplomowe, sprzęt do biznesu
Duże decyzje (50000-200000): MBA, wkład własny na mieszkanie
Wielkie ruchy (>200000): Zakup nieruchomości, firma

Praca - zarobki roczne (results.money):
Praktykant: 30000-45000
Junior: 45000-65000
Mid: 65000-100000
Senior: 100000-150000
Lead/Manager: 150000-250000
Własna firma: 80000-300000 (duża rozpiętość)

REGUŁA: Jeśli price > 0 w currency="money", NIE DAWAJ ujemnego money w results!

---

## EFEKTY DŁUGOTERMINOWE (results)

Przykładowe konwersje (5 lat):

Studia MBA:
price: 50000 money
results: [
  {money: 120000},      // Wzrost zarobków
  {passive_income: 500}, // Lepsze inwestycje
  {satisfaction: 15}     // Realizacja
]

Zmiana pracy (ryzyko):
price: 0
results: [
  {money: -20000},     // Trudny start
  {satisfaction: 25},  // Nowe wyzwania
  {health: -10}        // Stres adaptacji
]

Sport regularny:
price: 3000 money
results: [
  {health: 25},        // Główny efekt
  {satisfaction: 10}   // Samopoczucie
]

Limity:
- health: zawsze 0-100 (nigdy nie przekraczaj!)
- passive_income: wzrost max 1000/5lat (chyba że sprzedaż biznesu)
- relations: zmiany -20 do +30
- satisfaction: zmiany -30 do +40

---

## MECHANIZMY ANTY-EXPLOIT

Zabezpieczenia przed absurdami:
1. Zakaz spirali bogactwa:
   - Jeśli passive_income > 10000 → brak opcji "+50000 passive_income"
   - Progresja liniowa, nie wykładnicza

2. Cooldown na wielkie decyzje:
   - Ślub: tylko raz (married=false)
   - Założenie firmy: max raz na 15 lat
   - Zakup mieszkania: max raz na 10 lat

3. Bariery wejścia:
   Jeśli opcja == "Własna firma":
       wymagaj: doświadczenie >=10 lat LUB passive_income > 5000
   
   Jeśli opcja == "Manager":
       wymagaj: poprzednia_rola == "Senior" i staż >=5 lat

4. Blokada biedy:
   - Jeśli money < 1000 → zawsze 1 opcja z price=0 (praca dorywcza)

---

## RÓŻNORODNOŚĆ NARRACYJNA

Zmienne nazw (używaj rotacyjnie):
Zamiast ciągle "Kurs X":
"Specjalizacja w Y"
"Certyfikat Z" 
"Bootcamp A"
"Warsztaty B"
"Program rozwojowy C"

Konkretne, unikalne opisy:
ZŁE: "Inwestycja w nieruchomości"
DOBRE: "Zakup kawalerki pod wynajem w małym mieście"

ZŁE: "Poprawa zdrowia"
DOBRE: "Roczny karnet CrossFit + dietetyk"

ZŁE: "Zmiana pracy"
DOBRE: "Skok do konkurencji z 30% podwyżką"

---

## WALIDACJE I BEZPIECZEŃSTWO

Zakazy treściowe:
- Nielegalne działania (unikanie podatków, przestępstwa)
- Konkretne porady medyczne/prawne
- Nazwy realnych firm (poza "ZUS" ogólnie)
- Hazard, substancje, niebezpieczne hobby

Edukacyjny ton:
- "Wzrost świadomości finansowej"
- "Poprawa kondycji fizycznej"
- "Budowanie stabilności zawodowej"

---

## PRZYKŁAD DOBREJ ODPOWIEDZI

Sytuacja: Wiek 28, money=45000, Mid Developer, education="Inżynier IT", married=false

{
  "options": [
    {
      "name": "Awans na Senior Developer",
      "price": 8000,
      "currency": "satisfaction",
      "is_work_related": true,
      "job_name": "Senior Developer",
      "results": [
        {"currency": "money", "amount": 85000},
        {"currency": "passive_income", "amount": 300},
        {"currency": "health", "amount": -8}
      ]
    },
    {
      "name": "Zakup małego mieszkania na kredyt",
      "price": 45000,
      "currency": "money",
      "is_work_related": false,
      "results": [
        {"currency": "passive_income", "amount": -400},
        {"currency": "satisfaction", "amount": 20}
      ]
    },
    {
      "name": "Freelancing weekendowy + sport",
      "price": 2500,
      "currency": "money",
      "is_work_related": false,
      "results": [
        {"currency": "money", "amount": 35000},
        {"currency": "health", "amount": 15},
        {"currency": "relations", "amount": -5}
      ]
    },
    {
      "name": "Ślub i stabilizacja życia",
      "price": 15000,
      "currency": "money",
      "is_work_related": false,
      "results": [
        {"currency": "satisfaction", "amount": 30},
        {"currency": "relations", "amount": 25},
        {"currency": "money", "amount": -10000}
      ]
    }
  ]
}

---

## CHECKLIST PRZED WYSŁANIEM

- JSON jest poprawny (parsuje się bez błędów)
- Dokładnie N opcji
- Wszystkie price >= 0
- results mają 1-3 elementy
- Nazwy są unikalne i konkretne (nie generyczne)
- Progresja kariery ma sens (bez skoków)
- Wartości finansowe realistyczne dla Polski
- Żaden exploit (spirala bogactwa, duplikaty)
- Health w zakresie 0-100
- Jeśli price w money > 0, brak ujemnego money w results

---

OSTATNIE PRZYPOMNIENIE: Nie generuj tego samego contentu 2 razy z rzędu. Każde wywołanie = świeże, kontekstowe, zróżnicowane opcje. SZYBKO I NA TEMAT.
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
summary_service = SummaryService()

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

@app.post("/summary")
def get_summary(game_state: GameSummaryRequest) -> GameSummaryResponse:
    """
    Zwraca podsumowanie gry.
    """
    return summary_service.getGameSummary(game_state)
