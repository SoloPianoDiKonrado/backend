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
        Oto historia gry: {history_json}, a oto obecny stan gry: {game_state_json}. Ogranicz sie prosze tylko do podsumowania. Message zwroc w formie. Podsumowanie: ... Nie pisz prosze zadnych powitan itp. Chce miec response w raw stringu, zadnych znakow nowej linii itp.
        Waluta to polski złoty. Podsumowanie ma miejsce pod koniec gry. Wiec obecny stan gry jest juz po jej zakonczeniu. Zwracaj sie bezposrednio do gracza, typu: podjales dobra decyzje podejmujac prace... itp. (nie pisz w 3 osobie). Pisz ogolnie, nie podawaj szczegolow, np kwot. Na koncu
        nie pisz gratulacji itp."""

        return GameSummaryResponse(summary=self.gemini.message(prompt))


