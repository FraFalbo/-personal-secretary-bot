"""Personal Secretary Bot - Main Entry Point
Async approach: Telegram polling integrated with FastAPI event loop
Bot risponde SEMPRE a ogni messaggio! No threading complications.
"""

import os
import asyncio
import logging
from pathlib import Path
from dotenv import load_dotenv
import telebot
from fastapi import FastAPI
import uvicorn

# Load environment variables
load_dotenv(Path(__file__).parent / ".env")

# Configuration
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY")

if not TELEGRAM_BOT_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN non trovato nelle variabili d'ambiente!")

# Initialize Bot
bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN, parse_mode="HTML")

# FastAPI app
app = FastAPI(title="Segretaria Personale Bot", description="Bot Telegram multi-agente")

# === NVIDIA Nemotron LLM Client ===
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
                return "⚠️ Mi dispiace, c'è stato un errore nella comunicazione con l'AI."

# Create LLM client
llm_client: NemotronClient | None = None
if NVIDIA_API_KEY:
    llm_client = NemotronClient(NVIDIA_API_KEY)
    logging.info("✅ Client Nemotron inizializzato")
else:
    logging.warning("⚠️ NVIDIA_API_KEY non trovato - LLM disabilitato ma comandi base funzionano")

# === Base Agent Interface ===
from abc import ABC, abstractmethod

class BaseAgent(ABC):
    @abstractmethod
    async def handle_message(self, message: "types.Message", text: str) -> str | None:
        pass
    
    def get_triggers(self) -> list[dict]:
        return []

import types as types_module
types = types_module

# === Agent Registry ===
class AgentRegistry:
    def __init__(self):
        self.agents: dict[str, BaseAgent] = {}
    
    def register(self, name: str, agent: BaseAgent):
        self.agents[name] = agent
    
    def get_agent(self, name: str) -> BaseAgent | None:
        return self.agents.get(name)
    
    def get_all_agents(self) -> dict[str, BaseAgent]:
        return self.agents.copy()

agent_registry = AgentRegistry()

# === NLP Router ===
async def route_message(text: str) -> str | None:
    """Routea il messaggio all'agente appropriato usando LLM"""
    if not llm_client:
        return None
    system_prompt = """Sei un router NLP per un bot segretaria personale.
Analizza l'input e determina quale agente gestirlo.
Possibili: "calendar", "email", "general". Restituisci SOLO il nome."""
    response = await llm_client.chat(
        message=f"Input: {text}\n\nAgente:",
        system_prompt=system_prompt
    )
    agent_name = response.strip().lower()
    return agent_name if agent_name in ["calendar", "email", "general"] else "general"

# === Critical: Startup task for Telegram Polling ===
# Avviamo il polling Telegram come task asyncio dentro il loop di FastAPI
# Questo evita l'errore "no current event loop in thread" perché tutto gira nello stesso loop

async def start_bot_polling():
    """Funzione async che avvia il polling Telegram."""
    try:
        # none_stop=True fa sì che il polling continui indefinitamente
        # interval=2 controlla ogni 2 secondi nuovi messaggi
        # timeout=20 attende 20 secondi senza messaggi prima di riavviare
        bot.polling(none_stop=True, interval=2, timeout=20)
    except Exception as e:
        logging.error(f"Errore polling Telegram: {e}")
        # In caso di errore, riprova dopo un po'
        await asyncio.sleep(5)
        asyncio.create_task(start_bot_polling())

# === FastAPI Lifespan Events ===
@app.on_event("startup")
async def startup_event():
    logging.info("🚀 Avvio Segretaria Personale Bot...")
    # Avvia il polling Telegram in background nel loop di FastAPI
    asyncio.create_task(start_bot_polling())
    logging.info("✅ Polling Telegram avviato nel loop async")

@app.on_event("shutdown")
async def shutdown_event():
    logging.info("🛑 Spegnimento...")
    try:
        bot.stop_polling()
    except:
        pass
    logging.info("✅ Spento")

# === FastAPI Routes ===

@app.get("/")
def root():
    return {"status": "ok", "message": "Bot attivo - polling in esecuzione"}

@app.get("/health")
def health():
    return {"status": "healthy"}

# === Telegram Handlers ===

@bot.message_handler(commands=["start"])
def cmd_start(message):
    bot.send_message(
        message.chat.id,
        "👋 Ciao! Sono la tua Segretaria Personale.\n\n"
        "Servizi attivi:\n"
        "• 📅 Gestione calendario\n"
        "• 📧 Gestione email\n"
        "• 🤖 Risposte AI generative\n\n"
        "Scrivimi in italiano o inglese!\n"
        "Es: 'Aggiungi riunione con Marco domani 15:00'",
        parse_mode="HTML"
    )

@bot.message_handler(commands=["help"])
def cmd_help(message):
    bot.send_message(
        message.chat.id,
        "🤖 Comandi: /start /help /calendar /email\n"
        "Scrivimi naturalmente: 'Quali sono i miei impegni?'",
        parse_mode="HTML"
    )

@bot.message_handler(commands=["calendar"])
def cmd_calendar(message):
    agent = agent_registry.get_agent("calendar")
    if agent:
        bot.send_message(message.chat.id, "📅 Modalità calendario attiva! Scrivimi cosa vuoi fare.")
    else:
        bot.send_message(message.chat.id, "⚠️ Agente calendario in caricamento.")

@bot.message_handler(commands=["email"])
def cmd_email(message):
    agent = agent_registry.get_agent("email")
    if agent:
        bot.send_message(message.chat.id, "📧 Modalità email attiva! Scrivimi cosa vuoi fare.")
    else:
        bot.send_message(message.chat.id, "⚠️ Agente email in caricamento.")

@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    """Handler PRINCIPALE: risponde SEMPRE a ogni messaggio.
    
    Logica a 3 livelli:
    1. Agente specifico (Calendar/Email) se riconosciuto
    2. LLM Nemotron come fallback intelligente
    3. Messaggio educato se nulla altro funziona
    """
    text = message.text or ""
    
    # 1. Prima prova il routing LLM per trovare un agente
    agent_name = asyncio.get_event_loop().run_until_complete(route_message(text))
    agent = agent_registry.get_agent(agent_name)
    
    # 2. Se c'è un agente, provalo
    if agent:
        try:
            resp = await agent.handle_message(message, text)
            if resp:
                bot.send_message(message.chat.id, resp, parse_mode="HTML")
                return
        except Exception as e:
            logging.error(f"Errore agente {agent_name}: {e}")
    
    # 3. FALLBACK: LLM Nemotron se nessun agente ha risposto
    if llm_client:
        try:
            sys_prompt = f"""Sei la Segretaria Personale AI amichevole.
L'utente ha scritto: "{text}"
Rispondi in italiano in modo conciso (max 2 frasi). Se non sai qualcosa, dillo onestamente."""
            resp = await llm_client.chat(message=text, system_prompt=sys_prompt)
            if resp and resp.strip():
                bot.send_message(message.chat.id, resp, parse_mode="HTML")
                return
        except Exception as e:
            logging.error(f"Errore LLM fallback: {e}")
    
    # 4. ULTIMO RISORTO: Messaggio di default educato
    bot.send_message(
        message.chat.id,
        "🤖 Ho ricevuto il tuo messaggio! Sto elaborando...\n\n"
        "Non sono riuscito a capire esattamente cosa volevi, ma ecco le opzioni:\n"
        "• Scrivimi 'Quali sono i miei impegni?' per il calendario\n"
        "• Scrivimi 'Aggiungi riunione con Nome data ora' per nuovi eventi\n"
        "• Scrivimi 'Help' per tutti i comandi\n\n"
        "Riprova o dimmi chiaramente cosa vuoi fare! 👇",
        parse_mode="HTML"
    )

# === Root GET (alternativa al /telegram webhook) ===
@app.get("/")
def root():
    return {"status": "ok", "message": "Bot attivo"}

@app.get("/health")
def health():
    return {"status": "healthy"}

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)