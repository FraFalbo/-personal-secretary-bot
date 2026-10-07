"""Agente Calendar - Proattivo e Reattivo

Gestisce:
- Reattivo: Aggiungere eventi calendario ("Aggiungi riunione con Marco domani 15:00")
- Proattivo: Notifiche push per appuntamenti imminenti (task APScheduler)
"""

from agents.base_agent import BaseAgent
from telebot import types
import re
import asyncio
from datetime import datetime, timedelta


class CalendarAgent(BaseAgent):
    """Agente per la gestione del calendario Google.
    
    Features:
    - Reattivo: Creare eventi da messaggi testuali/vozze
    - Proattivo: Notifiche per appuntamenti imminenti
    """
    
    def __init__(self):
        self.calendar_service = None  # Inizializzerà dopo OAuth setup
        self.service_initialized = False
    
    async def handle_message(self, message: types.Message, text: str) -> str | None:
        """Gestisci messaggi relativi al calendario.
        
        Pattern riconosciuti:
        - "Aggiungi riunione con [nome] [data] [ora]"
        - "Che ho in programma [oggi/domani/questa settimana]"
        - "Rimuovi [evento]"
        """
        text_lower = text.lower().strip()
        
        # Pattern: "Aggiungi riunione con X domani alle Y" / "Add meeting with X tomorrow at Y"
        
        # Try to parse "aggiungi meeting" patterns
        add_patterns = [
            r"aggiungi\s+meeting\s+con\s+(\w+)\s+(?:domani|tomorrow)?\s*(?:alle|at\s+)?(\d{1,2}:?\d{0,2})?",
            r"create\s+event\s+for\s+(\w+)",
            r"schedule\s+(\w+)",
        ]
        
        # Try to parse "che ho in programma" patterns
        check_patterns = [
            r"che\s+ho\s+in\s+programma\s+(?:oggi|tomorrow|questa\s+settimana)?",
            r"cosa\s+ho\s+(?:in\s+)?programma",
        ]
        
        # Check "aggiungi" patterns
        for pattern in add_patterns:
            match = re.search(pattern, text_lower)
            if match:
                # Estrai dettagli
                person = match.group(1) if match.lastindex >= 1 else None
                time_str = match.group(2) if match.lastindex >= 2 else None
                
                # Prova a capire data/ora
                result = self._parse_datetime(text_lower, time_str)
                
                if result:
                    event_title = f"Incontro con {person}" if person else "Nuovo evento"
                    # TODO: Chiamare Google Calendar API per creare evento
                    return (
                        f"✅ Sto organizzando l'evento: '{event_title}'\n"
                        f"📅 Data/Ora: {result['date']} ore {result['time']}\n"
                        f"⚠️ Nota: Integrazione Google Calendar in corso. "
                        f"Usa /help per vedere le opzioni attuali."
                    )
                else:
                    return "❌ Non sono riuscito a capire la data/ora. Puoi specificare meglio? Es: 'Aggiungi riunione con Marco domani alle 15'"
        
        # Check "che ho in programma" patterns
        for pattern in check_patterns:
            if re.search(pattern, text_lower):
                # TODO: Query Google Calendar API
                return (
                    "📅 Il tuo calendario è momentaneamente offline "
                    "(integrazione in corso). Per ora puoi:\n"
                    "• Scrivermi 'aggiungi riunione con Nome data ora'\n"
                    "• Usare i comandi del bot per gestire eventi"
                )
        
        # Non gestito da questo agente
        return None
    
    def _parse_datetime(self, text: str, time_str: str | None) -> dict | None:
        """Parteggia data e ora dal testo dell'utente.
        
        Args:
            text: Testo originale dell'utente
            time_str: Ora opzionale estratta
            
        Returns:
            Dizionario con 'date' e 'time' chiavi, o None
        """
        now = datetime.now()
        
        # Se c'è un'ora esplicita
        if time_str:
            # Normalizza l'ora
            time_parts = re.findall(r"\d+", time_str.replace(":", ""))
            if len(time_parts) >= 2:
                hour = int(time_parts[0])
                minute = int(time_parts[1]) if len(time_parts) > 1 else 0
                
                # Gestisci formato 12h vs 24h
                if hour > 12:
                    hour -= 12
                
                return {
                    "date": now.strftime("%Y-%m-%d"),
                    "time": f"{hour:02d}:{minute:02d}",
                }
        
        # Se sono state menzionate date relative
        if "domani" in text or "tomorrow" in text:
            tomorrow = now + timedelta(days=1)
            return {
                "date": tomorrow.strftime("%Y-%m-%d"),
                "time": "15:00",  # Default time
            }
        
        if "oggi" in text:
            return {
                "date": now.strftime("%Y-%m-%d"),
                "time": "15:00",
            }
        
        return None
    
    def get_triggers(self) -> list[dict]:
        """Restituisce trigger APScheduler per notifiche proattive.
        
        Returns:
            Lista di trigger per APScheduler che controllano il calendario
            alle 9:00 ogni mattina
        """
        return [
            {
                "id": "daily_calendar_check",
                "trigger": "cron",
                "hour": 9,
                "minute": 0,
            }
        ]
    
    async def _daily_check(self):
        """Task giornaliero: controlla calendario e prepara notifiche.
        
        Questo verrà collegato ad APScheduler
        """
        logging.info("🔔 Check giornaliero calendario - in esecuzione")
        # TODO: Query Google Calendar per eventi di oggi/domani
        # Invia notifiche via Telegram agli utenti
    
    def get_help_text(self) -> str:
        return (
            "📅 Agente Calendar:\n"
            "• 'Aggiungi riunione con Nome data ora'\n"
            "• 'Che ho in programma oggi?'\n"
            "• 'Rimuovi l'incontro delle 14'"
        )