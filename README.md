# Chat with Gemini API 🚀

API do czatu z Google Gemini przy użyciu LangChain i FastAPI. Pozwala na prowadzenie rozmowy z modelem językowym Google Gemini, przechowywanie historii rozmowy w pamięci oraz jej czyszczenie.

## Stack Technologiczny

- **FastAPI** - nowoczesny framework webowy
- **LangChain** - framework do pracy z dużymi modelami językowymi
- **Google Gemini** - model językowy od Google
- **Docker & Docker Compose** - konteneryzacja
- **Pydantic** - walidacja danych

## Struktura Projektu

```
.
├── app/
│   ├── __init__.py
│   ├── main.py          # Główna aplikacja FastAPI z endpointami
│   └── chat_gemini.py   # Klasa ChatWithGemini do obsługi czatu
├── docker-compose.yml   # Konfiguracja Docker Compose
├── Dockerfile           # Dockerfile aplikacji
├── requirements.txt     # Zależności Python
├── .env.example         # Przykładowa konfiguracja
└── README.md           # Ten plik
```

## Szybki Start

### 1. Przygotuj środowisko

```bash
# Skopiuj przykładową konfigurację
cp .env.example .env

# Edytuj .env i dodaj swój klucz API Google Gemini
# GOOGLE_API_KEY=your_actual_google_api_key_here
```

### 2. Uruchom aplikację

```bash
# Zbuduj i uruchom kontenery
docker-compose up --build

# Lub w trybie detached (w tle)
docker-compose up -d --build
```

Aplikacja będzie dostępna pod adresem:
- **API**: http://localhost:3000
- **Dokumentacja Swagger**: http://localhost:3000/docs
- **ReDoc**: http://localhost:3000/redoc

### 3. Zatrzymaj aplikację

```bash
docker-compose down
```

## Endpointy API

### Główna strona
```bash
GET /
```
Zwraca informacje o dostępnych endpointach.

### Health Check
```bash
GET /health
```
Sprawdza czy API działa.

### Chat z Gemini
```bash
POST /chat
Content-Type: application/json

{
  "message": "Twoja wiadomość do modelu"
}
```

Odpowiedź:
```json
{
  "response": "Odpowiedź od modelu Gemini",
  "status": "success",
  "model": "gemini-pro"
}
```

### Historia rozmowy
```bash
GET /history
```

Odpowiedź:
```json
{
  "history": [
    {
      "type": "human",
      "content": "Pierwsza wiadomość użytkownika"
    },
    {
      "type": "ai",
      "content": "Odpowiedź modelu"
    }
  ],
  "total_messages": 2
}
```

### Statystyki rozmowy
```bash
GET /stats
```

Odpowiedź:
```json
{
  "total_messages": 10,
  "human_messages": 5,
  "ai_messages": 5,
  "model": "gemini-pro",
  "temperature": 0.7
}
```

### Czyszczenie historii
```bash
DELETE /clear
```

Odpowiedź:
```json
{
  "message": "Historia rozmowy została wyczyszczona",
  "status": "success"
}
```

## Przykładowe Requesty (curl)

```bash
# Wyślij wiadomość do modelu
curl -X POST http://localhost:3000/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"Cześć, jak się masz?"}'

# Pobierz historię rozmowy
curl http://localhost:3000/history

# Pobierz statystyki
curl http://localhost:3000/stats

# Wyczyść historię rozmowy
curl -X DELETE http://localhost:3000/clear
```

## Konfiguracja

### Zmienne środowiskowe

Utwórz plik `.env` na podstawie `.env.example`:

```env
GOOGLE_API_KEY=your_google_api_key_here
```

Aby uzyskać klucz API Google Gemini:
1. Wejdź na [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Zaloguj się na swoje konto Google
3. Utwórz nowy klucz API
4. Skopiuj klucz do pliku `.env`

### Opcjonalne parametry ChatWithGemini

Możesz skonfigurować klasę `ChatWithGemini` w `app/chat_gemini.py`:

```python
chat_instance = ChatWithGemini(
    api_key="your_api_key",           # Klucz API (opcjonalny)
    model_name="gemini-pro",         # Nazwa modelu (domyślnie: gemini-pro)
    temperature=0.7                  # Kreatywność modelu (0.0-1.0)
)
```

## Hot Reload

Aplikacja ma włączony **hot-reload** - każda zmiana w kodzie automatycznie przeładuje serwer. Nie musisz restartować kontenerów!

## Rozwój Lokalny (bez Dockera)

Jeśli chcesz uruchomić aplikację lokalnie:

```bash
# Utwórz virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac

# Zainstaluj zależności
pip install -r requirements.txt

# Skonfiguruj GOOGLE_API_KEY w .env

# Uruchom aplikację
uvicorn app.main:app --reload --port 3000
```

## Troubleshooting

### Brak klucza API
Jeśli nie skonfigurujesz `GOOGLE_API_KEY`, aplikacja zwróci błąd 500 przy pierwszym użyciu czatu.

### Problemy z kontenerami
```bash
# Rebuild kontenera
docker-compose up --build --force-recreate

# Zobacz logi
docker-compose logs app
```

## Licencja

MIT - rób co chcesz wariacik! 🔥
