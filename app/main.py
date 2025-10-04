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
