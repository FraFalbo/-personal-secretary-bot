"""Personal Secretary Bot - Main Entry Point
FastAPI + pyTelegramBotAPI per Telegram Bot
Deploy: Render.com (Free Tier)
LLM: Nemotron 3.5 Lightning via NVIDIA API
"""

import os
import logging
import asyncio
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv(Path(__file__).parent / ".env")

# Configuration
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY")

if not TELEGRAM_BOT_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN non trovato nelle variabili d'ambiente!")

# Import pyTelegramBotAPI (simple, stable Telegram library)
import telebot
from fastapi import FastAPI, Request
import uvicorn

# Initialize Bot
bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN, parse_mode="HTML")

# FastAPI app
app = FastAPI(title="Segretaria Personale Bot", description="Bot Telegram multi-agente per automazione personale")

# --- NVIDIA Nemotron LLM Client ---
class NemotronClient:
    """Wrapper minimale per Nemotron 3.5 Lightning API"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.nvidia.com/v1"
    
    async def chat(self, message: str, system_prompt: str = "") -> str:
        """Invia un messaggio a Nemotron e restituisce la risposta"""
        import httpx
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        
        payload = {
            "model": "nemotron-3.5-lightning",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": message},
            ],
            "temperature": 0.7,
            "max_tokens": 1000,
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=payload,
                    timeout=30.0,
                )
                response.raise_for_status()
                data = response.json()
                return data["choices"][0]["message"]["content"]
            except Exception as e:
                logging.error(f"Errore Nemotron API: {e}")
                return "Mi dispiace, c'è stato un errore nella comunicazione con il cervello AI. Per favore riprova tra un momento."

# Create LLM client instance
llm_client: NemotronClient | None = None

if NVIDIA_API_KEY:
    llm_client = NemotronClient(NVIDIA_API_KEY)
    logging.info("✅ Client Nemotron inizializzato")
else:
    logging.warning("⚠️ NVIDIA_API_KEY non trovato - LLM disabilitato")

# --- Google Services Placeholder ---
# Da implementare dopo OAuth setup

# --- Base Agent Interface ---
from abc import ABC, abstractmethod

class BaseAgent(ABC):
    """Interfaccia base per tutti gli agenti del sistema"""
    
    @abstractmethod
    async def handle_message(self, message: "types.Message", text: str) -> str | None:
        pass
    
    def get_triggers(self) -> list[dict]:
        return []

# Import types module
import types as types_module
types = types_module

# --- Agent Registry ---
class AgentRegistry:
    def __init__(self):
        self.agents: dict[str, BaseAgent] = {}
    
    def register(self, name: str, agent: BaseAgent):
        self.agents[name] = agent
        logging.info(f"Agente registrato: {name}")
    
    def get_agent(self, name: str) -> BaseAgent | None:
        return self.agents.get(name)
    
    def get_all_agents(self) -> dict[str, BaseAgent]:
        return self.agents.copy()

agent_registry = AgentRegistry()

# --- NLP Router ---
async def route_message(text: str) -> str | None:
    """Routea il messaggio all'agente appropriato usando LLM"""
    if not llm_client:
        return None
    
    system_prompt = """Sei un router NLP per un bot segretaria personale.
Analizza l'input dell'utente e determina quale agente dovrebbe gestirlo.
Possibili agenti: "calendar", "email", "general".
Restituisci SOLO il nome dell'agente (es. "calendar") o "general" se nessuno corrisponde.
Se l'input è ambiguo, restituisci "general"."""
    
    response = await llm_client.chat(
        message=f"Input utente: {text}\n\nDetermina l'agente corretto:",
        system_prompt=system_prompt
    )
    
    agent_name = response.strip().lower()
    return agent_name if agent_name in ["calendar", "email", "general"] else "general"

# --- Telegram Handlers ---

@bot.message_handler(commands=["start"])
def cmd_start(message):
    """Messaggio di benvenuto"""
    bot.send_message(
        message.chat.id,
        "👋 Ciao! Sono la tua Segretaria Personale.\n\n"
        "Sono attivi questi servizi:\n"
        "• 📅 Gestione calendario\n"
        "• 📧 Gestione email\n"
        "• 🤖 Risposte AI generiche\n\n"
        "Puoi scrivermi in italiano o inglese!\n"
        "Esempi:\n"
        "• 'Aggiungi riunione con Marco domani 15:00'\n"
        "• 'Riassumi le mie email importanti'\n"
        "• 'Che ho in programma oggi?'",
        parse_mode="HTML"
    )

@bot.message_handler(commands=["help"])
def cmd_help(message):
    bot.send_message(
        message.chat.id,
        "🤖 Comandi disponibili:\n\n"
        "/start - Benvenuto\n"
        "/help - Questo messaggio\n"
        "/calendar - Apri menu calendario\n"
        "/email - Apri menu email\n\n"
        "Puoi anche scrivermi naturalmente:\n"
        "• 'Aggiungi appuntamento lunedì alle 10'\n"
        "• 'Quali email ho oggi?'\n"
        "• 'Riassumi le comunicazioni urgenti'",
        parse_mode="HTML"
    )

@bot.message_handler(commands=["calendar"])
def cmd_calendar(message):
    """Menu gestione calendario"""
    agent = agent_registry.get_agent("calendar")
    if agent:
        bot.send_message(message.chat.id, "📅 Modalità calendario attivata! Cosa vuoi fare?")
    else:
        bot.send_message(message.chat.id, "⚠️ Agente calendario non ancora caricato.")

@bot.message_handler(commands=["email"])
def cmd_email(message):
    """Menu gestione email"""
    agent = agent_registry.get_agent("email")
    if agent:
        bot.send_message(message.chat.id, "📧 Modalità email attivata! Cosa vuoi fare?")
    else:
        bot.send_message(message.chat.id, "⚠️ Agente email non ancora caricato.")

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    """Handler principale per tutti gli altri messaggi"""
    text = message.text or ""
    
    # Route tramite LLM (in esecuzione sincrona per semplicità)
    agent_name = asyncio.get_event_loop().run_until_complete(route_message(text))
    agent = agent_registry.get_agent(agent_name)
    
    # Se un agente specifico gestisce, usalo
    if agent:
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If we're already in an async context, schedule it
                asyncio.ensure_future(agent.handle_message(message, text))
            else:
                response = asyncio.get_event_loop().run_until_complete(agent.handle_message(message, text))
                if response:
                    bot.send_message(message.chat.id, response, parse_mode="HTML")
        except Exception as e:
            logging.error(f"Errore nell'esecuzione agente: {e}")
    else:
        # Altrimenti, risposta generica via Nemotron
        if llm_client:
            system_prompt = """Sei la Segretaria Personale, un assistente AI amichevole ed efficiente.
Rispondi all'utente in italiano (o inglese se richiesto). Mantieni le risposte concise e utili.
L'utente potrebbe chiedere cose relative al calendario, email, o domande generali."""
            
            try:
                response = asyncio.get_event_loop().run_until_complete(
                    llm_client.chat(message=text, system_prompt=system_prompt)
                )
                bot.send_message(message.chat.id, response, parse_mode="HTML")
            except Exception as e:
                logging.error(f"Errore LLM: {e}")
                bot.send_message(message.chat.id, "⚠️ Mi dispiace, c'è stato un errore. Per favore riprova.")
        else:
            bot.send_message(
                message.chat.id,
                "🤖 Non sono stato ancora configurato il cervello AI. "
                "Usa /help per vedere cosa posso fare.",
                parse_mode="HTML"
            )

# --- Scheduler Tasks ---
async def scheduled_notifications():
    """Task periodico per controllare calendario e inviare notifiche"""
    logging.info("🔔 Task schedulato: controllo notifiche...")
    # TODO: Implementare controllo calendario e notifiche push

# --- FastAPI Webhook Endpoints ---

@app.post("/telegram")
async def telegram_webhook(request: Request):
    """Endpoint per ricevere update da Telegram"""
    json_str = await request.body()
    update = telebot.types.Update.de_json(json_str.decode('utf-8'))
    bot.process_new_updates([update])
    return {"ok": True}

@app.get("/")
def root():
    return {"status": "ok", "message": "Segretaria Personale Bot è online"}

@app.get("/health")
def health():
    return {"status": "healthy"}

# --- Lifespan ---
import asyncio

@app.on_event("startup")
def startup_event():
    logging.info("🚀 Avvio Segretaria Personale Bot...")
    
    # Inizializza agenti di base
    from agents.calendar_agent import CalendarAgent
    from agents.email_agent import EmailAgent
    
    calendar_agent = CalendarAgent()
    email_agent = EmailAgent()
    
    agent_registry.register("calendar", calendar_agent)
    agent_registry.register("email", email_agent)
    
    logging.info("✅ Agenti registrati")
    
    # Imposta webhook per Render
    webhook_url = os.getenv("GOOGLE_REDIRECT_URI")
    if webhook_url:
        # Rimuovi webhook vecchio
        try:
            bot.remove_webhook()
        except:
            pass
        # Imposta nuovo webhook
        webhook_url_full = f"{webhook_url}/telegram"
        try:
            bot.set_webhook(webhook_url=webhook_url_full)
            logging.info(f"🔗 Webhook Telegram impostato su: {webhook_url_full}")
        except Exception as e:
            logging.error(f"Errore impostazione webhook: {e}")
    
    logging.info("✅ Avvenimento di startup completato")

@app.on_event("shutdown")
def shutdown_event():
    logging.info("🛑 Spegnimento bot...")
    try:
        bot.remove_webhook()
    except:
        pass
    logging.info("✅ Bot spento")

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)