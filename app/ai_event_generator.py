import json
from app.chat_gemini import GeminiChat
from app.schemas import GameInterface, GameEvent, EventType
from typing import Dict, Any

class AIEventGenerator:
    def __init__(self):
        self.gemini = GeminiChat()
        self.gemini.start_chat()

    def generate_event_description(self, event: GameEvent, game_state: GameInterface) -> str:
        """
        Generuje opis wydarzenia używając AI na podstawie wydarzenia i stanu gry.
        """
        prompt = f"""
        Jesteś narratorem gry symulującej życie. 
        
        Wydarzenie: {event.name}
        Typ: {event.type}
        Opis bazowy: {event.description}
        Efekty: {event.effects}
        
        Aktualny stan gry:
        - Zdrowie: {game_state.health}
        - Finanse: {game_state.finances}
        - Relacje: {game_state.relationships}
        - Dochód pasywny: {game_state.passive_income}
        - Satysfakcja: {game_state.satisfaction}
        
        Wygeneruj krótki, angażujący opis tego wydarzenia (2-3 zdania) w stylu narracyjnym.
        Opis powinien być realistyczny i pasować do aktualnego stanu gry.
        """
        
        try:
            description = self.gemini.message(prompt)
            return description.strip()
        except Exception as e:
            # Fallback do oryginalnego opisu w przypadku błędu AI
            return event.description

    def generate_event_variation(self, base_event: Dict[str, Any], game_state: GameInterface) -> Dict[str, Any]:
        """
        Generuje wariację wydarzenia używając AI.
        """
        prompt = f"""
        Na podstawie wydarzenia bazowego: {base_event['name']}
        Opis: {base_event['description']}
        Efekty: {base_event['effects']}
        
        Stan gry: {game_state.dict()}
        
        Wygeneruj wariację tego wydarzenia - nową nazwę i opis, ale z podobnymi efektami.
        Odpowiedz w formacie JSON:
        {{
            "name": "Nowa nazwa wydarzenia",
            "description": "Nowy opis wydarzenia",
            "type": "{base_event['type']}",
            "effects": {base_event['effects']},
            "chance": {base_event['chance']}
        }}
        """
        
        try:
            response = self.gemini.message(prompt)
            # Spróbuj wyciągnąć JSON z odpowiedzi
            if "{" in response and "}" in response:
                json_start = response.find("{")
                json_end = response.rfind("}") + 1
                json_str = response[json_start:json_end]
                return json.loads(json_str)
        except Exception as e:
            print(f"Error generating AI variation: {e}")
        
        # Fallback do oryginalnego wydarzenia
        return base_event

    def generate_random_event(self, game_state: GameInterface, event_type: str = "random") -> Dict[str, Any]:
        """
        Generuje całkowicie nowe wydarzenie używając AI.
        """
        prompt = f"""
        Jesteś twórcą wydarzeń dla gry symulującej życie.
        
        Aktualny stan gry:
        - Zdrowie: {game_state.health}
        - Finanse: {game_state.finances}
        - Relacje: {game_state.relationships}
        - Dochód pasywny: {game_state.passive_income}
        - Satysfakcja: {game_state.satisfaction}
        
        Wygeneruj nowe wydarzenie (pozytywne lub negatywne) pasujące do tego stanu.
        Odpowiedz w formacie JSON:
        {{
            "name": "Nazwa wydarzenia",
            "description": "Opis wydarzenia",
            "type": "positive" lub "negative",
            "conditions": {{}},
            "effects": {{
                "health": 0,
                "finances": 0,
                "relationships": 0,
                "passive_income": 0,
                "satisfaction": 0
            }},
            "chance": 0.1
        }}
        """
        
        try:
            response = self.gemini.message(prompt)
            if "{" in response and "}" in response:
                json_start = response.find("{")
                json_end = response.rfind("}") + 1
                json_str = response[json_start:json_end]
                return json.loads(json_str)
        except Exception as e:
            print(f"Error generating random event: {e}")
        
        # Fallback do prostego wydarzenia
        return {
            "name": "AI Generated Event",
            "description": "An AI-generated event",
            "type": "positive",
            "conditions": {},
            "effects": {"health": 0, "finances": 0, "relationships": 0, "passive_income": 0, "satisfaction": 0},
            "chance": 0.1
        }

    def close(self):
        """Zamyka sesję AI"""
        self.gemini.clear_chat()
