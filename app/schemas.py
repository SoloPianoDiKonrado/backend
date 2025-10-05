from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from enum import Enum

class EventType(str, Enum):
    POSITIVE = "positive"
    NEGATIVE = "negative"

class Currency(str, Enum):
    MONEY = "money"
    HEALTH = "health"
    RELATIONS = "relations"
    SATISFACTION = "satisfaction"
    PASSIVE_INCOME = "passive_income"

class CurrencyChange(BaseModel):
    currency: Currency
    amount: int

class GameInterface(BaseModel):
    money: int
    health: int  # 0–200
    relations: int
    satisfaction: int
    passive_income: int

    age: Optional[int] = None
    job: Optional[str] = None
    education: Optional[str] = None

class GameOption(BaseModel):
    name: str  # short name
    price: int
    currency: Currency
    results: list[CurrencyChange]

class GameHistory(BaseModel):
    options: list[GameOption]

class EventCondition(BaseModel):
    max: Optional[int] = None
    min: Optional[int] = None


class EventEffects(BaseModel):
    money: int
    health: int #0-200
    relations: int
    satisfaction: int
    passive_income: int

class GameEvent(BaseModel):
    name: str
    type: EventType
    description: str
    conditions: Dict[str, EventCondition]
    effects: EventEffects
    chance: float


class EventRequest(BaseModel):
    game_state: GameInterface
    available_events: List[GameEvent]


class EventResponse(BaseModel):
    event_occurred: bool
    event: Optional[GameEvent] = None
    updated_game_state: Optional[GameInterface] = None
    message: str


class AIEventRequest(BaseModel):
    game_state: GameInterface
    events_data: List[Dict[str, Any]]

class GameSummaryRequest(BaseModel):
    history: GameHistory
    game_state: GameInterface

class GameSummaryResponse(BaseModel):
    summary: str


class GenerateYearResponse(BaseModel):
    options: list[GameOption]

class GenerateYearRequest(BaseModel):
    game_interface: GameInterface
    options_amount: int
    history: list[GameHistory]