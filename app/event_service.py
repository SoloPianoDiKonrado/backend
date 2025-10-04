import json
import random
from pathlib import Path
from typing import Optional, List, Dict, Any
from app.schemas import GameInterface, EventResponse, GameEvent, EventType

class EventService:

    def __init__(self):
        self.EVENTS_FILE = Path(__file__).parent / "events/event.json"
        with open(self.EVENTS_FILE, "r") as f:
            self.EVENTS = json.load(f)
        self.triggered_events = set()

    def _check_conditions(self, event: Dict[str, Any], game_state: GameInterface) -> bool:
        """Sprawdza czy warunki wydarzenia są spełnione"""
        conditions = event.get("conditions", {})
        for stat, limits in conditions.items():
            value = getattr(game_state, stat, 0)
            if "max" in limits and value > limits["max"]:
                return False
            if "min" in limits and value < limits["min"]:
                return False
        return True

    def _apply_effects(self, game_state: GameInterface, effects: Dict[str, int]) -> GameInterface:
        """Aplikuje efekty wydarzenia do stanu gry"""
        updated_state = game_state.model_copy()
        
        for stat_name, change in effects.items():
            if hasattr(updated_state, stat_name):
                current_value = getattr(updated_state, stat_name)
                new_value = max(0, min(100, current_value + change))  # Ograniczenie 0-100
                setattr(updated_state, stat_name, new_value)
                
        return updated_state

    def choose_event(self, game_state: GameInterface) -> EventResponse:
        """Główna metoda wybierająca i sprawdzająca wydarzenie"""
        possible_events = []
        
        for event in self.EVENTS:
            if event["name"] in self.triggered_events:
                continue  # Skip already triggered events

            # Check conditions
            if self._check_conditions(event, game_state):
                # Check probability
                if random.random() < event.get("chance", 0):
                    possible_events.append(event)

        if not possible_events:
            return EventResponse(
                event_occurred=False,
                message="Brak dostępnych wydarzeń lub żadne nie wystąpiło"
            )

        # Wybierz losowe wydarzenie
        selected_event = random.choice(possible_events)
        self.triggered_events.add(selected_event["name"])  # Mark as triggered
        
        # Aplikuj efekty
        updated_game_state = self._apply_effects(game_state, selected_event["effects"])
        
        return EventResponse(
            event_occurred=True,
            event=GameEvent(
                name=selected_event["name"],
                type=EventType(selected_event["type"]),
                description=selected_event["description"],
                conditions=selected_event["conditions"],
                effects=selected_event["effects"],
                chance=selected_event["chance"]
            ),
            updated_game_state=updated_game_state,
            message=f"Wydarzenie: {selected_event['name']} - {selected_event['description']}"
        )

    def get_available_events(self, game_state: GameInterface) -> List[Dict[str, Any]]:
        """Zwraca listę dostępnych wydarzeń dla aktualnego stanu gry"""
        available_events = []
        
        for event in self.EVENTS:
            if event["name"] not in self.triggered_events and self._check_conditions(event, game_state):
                available_events.append({
                    "name": event["name"],
                    "type": event["type"],
                    "description": event["description"],
                    "chance": event["chance"],
                    "effects": event["effects"]
                })
        
        return available_events

    def reset_triggered_events(self):
        """Resetuje listę wyzwolonych wydarzeń"""
        self.triggered_events.clear()

    def simulate_multiple_events(self, game_state: GameInterface, num_events: int = 5) -> List[EventResponse]:
        """Symuluje wiele wydarzeń dla testowania"""
        results = []
        current_state = game_state
        
        for _ in range(num_events):
            result = self.choose_event(current_state)
            results.append(result)
            
            if result.event_occurred and result.updated_game_state:
                current_state = result.updated_game_state
        
        return results