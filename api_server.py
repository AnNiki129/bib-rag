from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from contextlib import asynccontextmanager

import json
from pathlib import Path

import chat

# ---------- Link-Katalog laden ----------
BASE_DIR = Path(__file__).resolve().parent
LINKS_PATH = BASE_DIR / "data" / "links.json"

if LINKS_PATH.exists():
    LINK_CATALOG = json.loads(LINKS_PATH.read_text(encoding="utf-8"))
else:
    LINK_CATALOG = []

def match_links(question: str, lang: str, max_links: int = 5):
    q = (question or "").lower()
    hits = []

    for item in LINK_CATALOG:
        keywords = item.get("keywords", [])
        if any(k.lower() in q for k in keywords):
            hits.append({
                "title": item["title_de"] if lang == "de" else item["title_en"],
                "url": item["url"],
            })

    # Duplikate raus
    unique = []
    seen = set()
    for h in hits:
        if h["url"] not in seen:
            unique.append(h)
            seen.add(h["url"])

    return unique[:max_links]

def links_reply_text(lang: str):
    return (
        "Hier sind passende Links zu deiner Frage:"
        if lang == "de"
        else
        "Here are relevant links for your question:"
    )

@asynccontextmanager
async def lifespan(app: FastAPI):
    # STARTUP
    print("🔄 Lade RAG-Index ...")
    app.state.collection = chat.load_collection()
    print("✅ RAG-Index geladen.")
    yield
    # SHUTDOWN (optional)
    print("🛑 Server wird beendet.")


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    # später: hier die echte Bibliotheks-Domain eintragen
    allow_origins=["http://localhost:8000", "http://127.0.0.1:8000", "http://localhost:8501"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatReq(BaseModel):
    message: str


@app.post("/api/llm")
def api_llm(req: ChatReq):
    question = (req.message or "").strip()
    if not question:
        return {"reply": "Bitte gib eine Frage ein.", "links": []}

    lang = chat.detect_language(question)

    # 1) Links immer matchen
    links = match_links(question, lang)

    # 2) Wenn Links-only gewünscht: KEIN RAG/LLM
    if any(l.get("mode") == "only" for l in links):
        # mode aus response entfernen, UI braucht es nicht
        links_out = [{"title": l["title"], "url": l["url"]} for l in links]
        return {"reply": links_reply_text(lang), "links": links_out}

    # 3) Sonst normales RAG/LLM + Links anhängen
    collection = app.state.collection
    context, _kept = chat.retrieve_context(collection, question, k=12)
    answer = chat.call_llm(question, context)

    links_out = [{"title": l["title"], "url": l["url"]} for l in links]
    return {"reply": answer, "links": links_out}