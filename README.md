# FastAPI + PostgreSQL Boilerplate 🚀

Pełny boilerplate z FastAPI, PostgreSQL, SQLAlchemy ORM i Docker Compose z hot-reload.

## Stack Technologiczny

- **FastAPI** - nowoczesny framework webowy
- **PostgreSQL** - baza danych
- **SQLAlchemy** - ORM
- **Alembic** - migracje bazy danych
- **Docker & Docker Compose** - konteneryzacja z hot-reload
- **Pydantic** - walidacja danych

## Struktura Projektu

```
.
├── app/
│   ├── __init__.py
│   ├── main.py          # Główna aplikacja FastAPI
│   ├── config.py        # Konfiguracja
│   ├── database.py      # Setup bazy danych
│   ├── models.py        # Modele SQLAlchemy
│   ├── schemas.py       # Schematy Pydantic
│   └── crud.py          # Operacje CRUD
├── alembic/             # Migracje bazy danych
├── docker-compose.yml   # Konfiguracja Docker Compose
├── Dockerfile           # Dockerfile aplikacji
├── requirements.txt     # Zależności Python
└── .env.example         # Przykładowa konfiguracja
```

## Szybki Start

### 1. Sklonuj i przygotuj środowisko

```bash
# Skopiuj przykładową konfigurację
cp .env.example .env

# Opcjonalnie: edytuj .env jeśli chcesz zmienić domyślne wartości
```

### 2. Uruchom aplikację z Docker Compose

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

# Zatrzymaj i usuń volumes (UWAGA: skasuje dane w bazie!)
docker-compose down -v
```

## Hot Reload

Aplikacja ma włączony **hot-reload** - każda zmiana w kodzie automatycznie przeładuje serwer. Nie musisz restartować kontenerów!

## Endpointy API

### Health Check
```bash
GET /health
```

### Users CRUD

**Utwórz użytkownika**
```bash
POST /users/
Content-Type: application/json

{
  "email": "user@example.com",
  "username": "johndoe",
  "password": "secret123"
}
```

**Pobierz wszystkich użytkowników**
```bash
GET /users/
```

**Pobierz użytkownika po ID**
```bash
GET /users/{user_id}
```

**Zaktualizuj użytkownika**
```bash
PUT /users/{user_id}
Content-Type: application/json

{
  "email": "newemail@example.com",
  "username": "newusername",
  "is_active": true
}
```

**Usuń użytkownika**
```bash
DELETE /users/{user_id}
```

## Przykładowe Requesty (curl)

```bash
# Utwórz użytkownika
curl -X POST http://localhost:3000/users/ \
  -H "Content-Type: application/json" \
  -d '{"email":"test@test.com","username":"testuser","password":"pass123"}'

# Pobierz użytkowników
curl http://localhost:3000/users/

# Pobierz użytkownika po ID
curl http://localhost:3000/users/1

# Zaktualizuj użytkownika
curl -X PUT http://localhost:3000/users/1 \
  -H "Content-Type: application/json" \
  -d '{"username":"updateduser"}'

# Usuń użytkownika
curl -X DELETE http://localhost:3000/users/1
```

## Migracje Bazy Danych (Alembic)

### Utwórz nową migrację

```bash
# Wejdź do kontenera aplikacji
docker-compose exec app bash

# Utwórz migrację automatycznie na podstawie modeli
alembic revision --autogenerate -m "Initial migration"

# Zastosuj migracje
alembic upgrade head

# Cofnij ostatnią migrację
alembic downgrade -1
```

## Rozwój Lokalny (bez Dockera)

Jeśli chcesz uruchomić aplikację lokalnie:

```bash
# Utwórz virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# lub
venv\Scripts\activate  # Windows

# Zainstaluj zależności
pip install -r requirements.txt

# Uruchom PostgreSQL lokalnie lub zmień DATABASE_URL w .env

# Uruchom aplikację
uvicorn app.main:app --reload --port 3000
```

## Baza Danych

PostgreSQL działa w kontenerze Docker i jest dostępna na:
- **Host**: localhost
- **Port**: 5432
- **User**: postgres
- **Password**: postgres
- **Database**: app_db

Możesz połączyć się z bazą używając dowolnego klienta PostgreSQL (pgAdmin, DBeaver, psql, etc.)

```bash
# Połącz się przez psql
docker-compose exec db psql -U postgres -d app_db
```

## Logi

```bash
# Zobacz logi wszystkich serwisów
docker-compose logs

# Zobacz logi tylko aplikacji
docker-compose logs app

# Zobacz logi z follow
docker-compose logs -f app
```

## TODO / Dalszy Rozwój

- [ ] Dodać hashowanie haseł (bcrypt/passlib)
- [ ] Dodać autentykację JWT
- [ ] Dodać testy (pytest)
- [ ] Dodać CORS middleware
- [ ] Dodać rate limiting
- [ ] Dodać więcej modeli i relacji
- [ ] Dodać paginację
- [ ] Dodać filtering i sorting

## Troubleshooting

### Port już zajęty
Jeśli port 3000 lub 5432 jest zajęty, zmień porty w `docker-compose.yml`:
```yaml
ports:
  - "TWOJ_PORT:3000"  # dla aplikacji
  - "TWOJ_PORT:5432"  # dla PostgreSQL
```

### Problemy z bazą danych
```bash
# Usuń volumes i uruchom od nowa
docker-compose down -v
docker-compose up --build
```

### Rebuild kontenera
```bash
docker-compose up --build --force-recreate
```

## Licencja

MIT - rób co chcesz wariacik! 🔥
