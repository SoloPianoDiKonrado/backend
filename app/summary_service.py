from app.chat_gemini import GeminiChat
from app.schemas import GameSummaryRequest, GameSummaryResponse
import json

class SummaryService:

    def __init__(self):
        self.gemini = GeminiChat()

    def getGameSummary(self, game_state: GameSummaryRequest) -> GameSummaryResponse:
        history_json = game_state.history.model_dump_json()
        game_state_json = game_state.game_state.model_dump_json()

        prompt = f""" Jesteś "Mistrzem Gry" (Game Master) dla symulatora edukacyjnego "Architekt Przyszłości" — interaktywnej gry symulacyjnej pokazującej wpływ decyzji życiowych (co 5 lat) na zasoby: money, health, relations, satisfaction i passive_income. 
        Twoim zadaniem jest na podstawie historii oraz obecnego stanu gry wygenerować podsumowanie gry. Opisz proszę jakie decyzje zostały podjęte, czy były one dobre czy złe, jakie skutki miały.
        Oto historia gry: {history_json}, a oto obecny stan gry: {game_state_json}"""

        return GameSummaryResponse(summary=self.gemini.message(prompt))


