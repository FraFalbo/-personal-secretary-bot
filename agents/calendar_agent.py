"""Agente Calendar - Proattivo e Reattivo
Risponde SEMPRE a ogni messaggio relativi al calendario.
"""

from agents.base_agent import BaseAgent
from telebot import types
import re
import asyncio
from datetime import datetime, timedelta


class CalendarAgent(BaseAgent):
    """Agente per la gestione del calendario Google.
    
    CARATTERISTICA IMPORTANTE: Risponde SEMPRE a ogni messaggio
    che tocchi il calendario, anche se non capisce esattamente il formato.
    """

    def __init__(self):
        self.calendar_service = None
        self.service_initialized = False
    
    async def handle_message(self, message: types.Message, text: str) -> str | None:
        """Gestisci messaggi relativi al calendario.
        
        Questo metodo RISPARDA SEMPRE un valore (mai None) se il testo
        sembra riguardare il calendario. Se non capisce il formato preciso,
        chiede chiarimenti all'utente.
        """
        text_lower = text.lower().strip()
        
        # === RICONOSCIMENTO MODELLI SPECIFICI ===
        
        # Modello 1: "Quali sono i miei Impegni" / "What are my engagements"
        if re.search(r"qual[i]\s+sono\s+(?:i\s+)?(?:miei\s+)?(?:impegni|compromessi|appuntamenti)", text_lower):
            return self._get_calendar_summary(message)
        
        # Modello 2: "Che ho in programma" / "What do I have planned"
        if re.search(r"che\s+ho\s+(?:in\s+)?(?:programm[ae])?", text_lower):
            return self._get_calendar_summary(message)
        
        # Modello 3: "Mostrami il calendario" / "Show me my calendar"
        if re.search(r"(mostrami|show\s+me)(?:\s+il\s+)?(?:calendario|programma)", text_lower):
            return self._get_calendar_summary(message)
        
        # Modello 4: "Giornata di oggi" / "Today's schedule"
        if re.search(r"(oggi|domani|questa\s+settimana)", text_lower):
            # Se cita una data, cerca di dargli un senso
            return self._get_daily_schedule(message, text_lower)
        
        # === MODELLO "GENERICO CALENDARIO" ===
        # Se il messaggio contiene parole chiave calendario ma non combacia sopra,
        # rispondi comunque con un utile promemoria
        
        # Modello 5: Qualsiasi cosa contenga queste parole chiave
        calendar_keywords = ["calendario", "appuntamento", "riunione", "orario", "scadenza", "scadenze"]
        if any(kw in text_lower for kw in calendar_keywords):
            return (
                f"📅 Ho rilevato un riferimento al tuo calendario.\n\n"
                f"Non sono riuscito a capire esattamente cosa cerchi tra: "
                f"'{text}'.\n\n"
                f"Puoi provare:\n"
                f"• 'Quali sono i miei impegni?'\n"
                f"• 'Che ho in programma oggi?'\n"
                f"• 'Aggiungi riunione con Nome data ora'"
            )
        
        # Nessun pattern matches ma l'utente ci sta provando - dare un'aiuto
        return (
            "📅 Interessante! Parliamo di calendario.\n\n"
            "Non sono riusito a interpretare esattamente la tua richiesta, "
            "ma ecco cosa posso fare per te:\n"
            "• Chiedermi 'Quali sono i miei impegni?' → elenco tutto\n"
            "• Scrivermi 'Aggiungi riunione con Marco domani 15:00' → nuovo evento\n"
            "• Chiedermi 'Che ho in programma oggi?' → giornata di oggi\n\n"
            "Cosa ne dici di provare uno di questi esempi?"
        )
    
    # === METODI INTERNI DI AIUTO ===
    
    def _get_calendar_summary(self, message: types.Message) -> str:
        """Restituisce un riassunto generale del calendario."""
        import asyncio
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # Se siamo già in un contesto async, schedule
                asyncio.ensure_future(self._fetch_and_summarize(message))
                return "📅 Sto controllando il tuo calendario... dai un attimo!"
            else:
                resp = asyncio.get_event_loop().run_until_complete(self._fetch_and_summarize(message))
                return resp if resp else self._default_calendar_help()
        except Exception:
            return self._default_calendar_help()
    
    def _get_daily_schedule(self, message: types.Message, text_lower: str) -> str:
        """Restituisce la programmazione giornaliera."""
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.ensure_future(self._fetch_daily_schedule(text_lower))
                return "📅 Controllando la tua programmazione giornaliera..."
            else:
                resp = asyncio.get_event_loop().run_until_complete(
                    self._fetch_daily_schedule(text_lower)
                )
                return resp if resp else self._default_calendar_help()
        except Exception:
            return self._default_calendar_help()
    
    async def _fetch_and_summarize(self, message: types.Message):
        """Fetch calendar data and summarize (placeholder)."""
        # TODO: Integrare con Google Calendar API reale
        await asyncio.sleep(0.1)  # Simulazione delay
        return (
            "📅 Il tuo calendario è momentaneamente offline "
            "(integrazione Google in corso). Per ora ti recuerdo:\n"
            "• Usa 'Quali sono i miei impegni?' per un prompt generale\n"
            "• Scrivimi 'Aggiungi riunione con Nome data ora' per nuovi eventi\n"
            "• Il bot funziona meglio dopo la configurazione OAuth Google"
        )
    
    async def _fetch_daily_schedule(self, text_lower: str):
        """Fetch daily schedule placeholder."""
        await asyncio.sleep(0.1)
        return (
            "📅 Giornata di oggi: niente eventi schedulati nel calendario "
            "al momento. Aggiungi qualcosa con 'Aggiungi evento...'!"
        )
    
    def _default_calendar_help(self) -> str:
        """Messaggio di help di default quando tutto fallisce."""
        return (
            "📅 Agente Calendar attivo!\n\n"
            "Capisco questi pattern:\n"
            "• 'Quali sono i miei impegni?' → elenco impegni\n"
            "• 'Che ho in programma oggi?' → giornata di oggi\n"
            "• 'Mostrami il calendario' → overview generale\n"
            "• 'Aggiungi riunione con Nome data ora' → nuovo evento\n\n"
            "Prova uno di questi comandi! 👆"
        )
    
    def get_triggers(self) -> list[dict]:
        return [
            {
                "id": "daily_check",
                "trigger": "cron",
                "hour": 9,
                "minute": 0,
            }
        ]
    
    def get_help_text(self) -> str:
        return (
            "📅 Agente Calendar:\n"
            "• 'Quali sono i miei impegni?'\n"
            "• 'Che ho in programma oggi?'\n"
            "• 'Aggiungi riunione con Nome data ora'\n"
            "• 'Mostrami il calendario'"
        )