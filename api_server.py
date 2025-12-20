from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from contextlib import asynccontextmanager

import chat  

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
    allow_origins=["http://localhost:8000", "http://127.0.0.1:8000"],
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
        return {"reply": "Bitte gib eine Frage ein."}

    collection = app.state.collection

    # RAG
    context, _docs = chat.retrieve_context(collection, question, k=4)

    # Ollama
    answer = chat.call_llm(question, context)

    return {"reply": answer}
