"""Base Agent Interface - Modello per tutti gli agenti del sistema."""

from abc import ABC, abstractmethod
from telebot import types


class BaseAgent(ABC):
    """Interfaccia base per tutti gli agenti del sistema multi-agente.
    
    Ogni agente deve implementare:
    - handle_message: per gestire i messaggi degli utenti
    - get_triggers: per task periodici APScheduler (opzionale)
    """
    
    @abstractmethod
    async def handle_message(self, message: types.Message, text: str) -> str | None:
        """Gestisisce un messaggio in arrivo.
        
        Args:
            message: Messaggio Telegram original (telebot.types.Message)
            text: Testo del messaggio
            
        Returns:
            Risposta testuale se l'agente gestisce il messaggio, None altrimenti
        """
        pass
    
    def get_triggers(self) -> list[dict]:
        """Restituisce trigger APScheduler per task periodici.
        
        Returns:
            Lista di dizioni con trigger scheduler (es. {"id": "check_calendar", "trigger": "cron", "hour": 9, "minute": 0})
            Restituisce lista vuota se l'agente non ha task periodici.
        """
        return []
    
    def get_help_text(self) -> str:
        """Testo di aiuto per questo agente (mostrato nei menu).
        
        Returns:
            Descrizione dei comandi di questo agente
        """
        return "Nessuna descrizione disponibile"