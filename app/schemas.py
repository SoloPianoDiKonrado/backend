from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from enum import Enum
from app.main import GameInterface


class EventType(str, Enum):
    POSITIVE = "positive"
    NEGATIVE = "negative"


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
