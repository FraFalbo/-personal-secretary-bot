"""Agente Email - Analisi, Filtraggio e Bozze

Gestisce:
- Analisi mail in arrivo
- Filtraggio spam/inofficiali
- Riassunto comunicazioni urgenti
- Preparazione bozze di risposta
"""

from agents.base_agent import BaseAgent
from telebot import types
import re


class EmailAgent(BaseAgent):
    """Agente per la gestione della posta Gmail.
    
    Features:
    - Lettura e analisi mail in arrivo
    - Filtraggio spam e promozioni
    - Riassunto comunicazioni urgenti
    - Bozze di risposta automatiche
    """
    
    def __init__(self):
        self.gmail_service = None  # Inizializzerà dopo OAuth setup
        self.service_initialized = False
    
    async def handle_message(self, message: types.Message, text: str) -> str | None:
        """Gestisci messaggi relativi alla email.
        
        Pattern riconosciuti:
        - "Riassumi le mie email urgenti"
        - "Ci sono email importanti oggi?"
        - "Crea bozza di risposta a [email]"
        - "Cancella spam"
        """
        text_lower = text.lower().strip()
        
        # Pattern: "riassumi email urgenti"
        if "riassumi" in text_lower and "email" in text_lower:
            return (
                "📧 Analisi email in corso...\n\n"
                "⚠️ Integrazione Gmail in corso. "
                "Per ora puoi:\n"
                "• Scrivimi 'riassumi email' per vedere stato\n"
                "• Usa i comandi del bot per gestire la posta"
            )
        
        # Pattern: "ci sono email importanti"
        if "importante" in text_lower and "email" in text_lower:
            return (
                "📧 Controllo stato email...\n\n"
                "⚠️ Servizio Gmail attualmente disponibile in fase di setup. "
                "Puoi scrivermi 'riassumi email urgenti' quando sarà pronto."
            )
        
        # Pattern: "crea bozza di risposta"
        create_patterns = [
            r"crea\s+bozza\s+(?:di\s+)?risposta?\s*(?:a\s+)?(\S+@\S+)?",
            r"bozza\s+risposta\s+(?:a\s+)?(\S+@\S+)?",
        ]
        
        for pattern in create_patterns:
            match = re.search(pattern, text_lower)
            if match:
                email = match.group(1) if match.group(1) else "l'utente"
                return (
                    f"📝 Sto creando bozza di risposta per: {email}\n"
                    "⚠️ Integrazione Gmail in corso. "
                    "La bozza sarà pronta per tua approvazione appena il sistema è configurato."
                )
        
        # Non gestito
        return None
    
    def get_triggers(self) -> list[dict]:
        """Trigger APScheduler per controllo email periodico.
        
        Returns:
            Lista di trigger per controllare la posta ogni ora
        """
        return [
            {
                "id": "hourly_email_check",
                "trigger": "cron",
                "minute": 0,
            }
        ]
    
    async def _hourly_email_check(self):
        """Task orario: controlla nuove email in arrivo.
        
        Verrà collegato ad APScheduler.
        """
        logging.info("📧 Check orario email - in esecuzione")
        # TODO: Query Gmail API per nuove mail
        # Filtra spam, riassumi urgenti, crea bozze
    
    def get_help_text(self) -> str:
        return (
            "📧 Agente Email:\n"
            "• 'Riassumi le mie email urgenti'\n"
            "• 'Ci sono email importanti?'\n"
            "• 'Crea bozza risposta a indirizzo@email'"
        )