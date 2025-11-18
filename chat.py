import os
import textwrap
import requests

import chromadb
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction

CHROMA_DIR = "chroma_bib"
COLLECTION_NAME = "bib"

# 🗝️ API-Key aus Umgebungsvariable lesen 
API_KEY = os.getenv("LLM_API_KEY")

# 🔁 Werte an Provider anpassen
API_URL = "https://api.together.xyz/v1/chat/completions"  # Beispiel-Endpunkt
MODEL_NAME = "DEIN/MODELLNAME"  # z.B. SauerkrautLM / Llama 3.1 70B Instruct


def load_collection():
    embed_fn = SentenceTransformerEmbeddingFunction(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )
    client = chromadb.PersistentClient(path=CHROMA_DIR)
    collection = client.get_collection(
        name=COLLECTION_NAME,
        embedding_function=embed_fn,
    )
    return collection


def retrieve_context(collection, question: str, k: int = 4):
    """Holt die wichtigsten Textstellen aus dem RAG-Index."""
    result = collection.query(
        query_texts=[question],
        n_results=k,
    )

    docs = result["documents"][0]
    metas = result["metadatas"][0]

    blocks = []
    for i, (doc, meta) in enumerate(zip(docs, metas), start=1):
        title = meta.get("title", "Quelle")
        source = meta.get("source", "")
        block = f"[{i}] {title} ({source})\n{doc}"
        blocks.append(block)

    context = "\n\n---\n\n".join(blocks)
    return context, list(zip(docs, metas))


def call_llm(question: str, context: str) -> str:
    """Ruft das LLM (z. B. SauerkrautLM / Llama) über eine Chat-API auf."""
    if not API_KEY:
        return "⚠️ Kein API-Key gesetzt. Bitte LLM_API_KEY als Umgebungsvariable setzen."

    system_prompt = textwrap.dedent("""
        Du bist ein Bibliotheksassistent an einer Hochschule.
        Antworte ausschließlich auf Basis der bereitgestellten Kontexte.
        Wenn eine Information nicht eindeutig im Kontext steht,
        sage ehrlich, dass du es nicht sicher weißt und verweise auf die Bibliothek.
        Antworte kurz, sachlich und auf Deutsch.
    """)

    user_prompt = f"""
    Frage eines Studierenden:
    {question}

    Relevante Auszüge aus Bibliotheksdokumenten:

    {context}

    Formuliere eine klare, gut verständliche Antwort auf Deutsch.
    Nenne am Ende in einer Zeile, aus welchen Abschnitten du geantwortet hast,
    z.B.: Quellen: [1], [3]
    """

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }

    body = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "system", "content": system_prompt.strip()},
            {"role": "user", "content": user_prompt.strip()},
        ],
        "temperature": 0.2,
        "max_tokens": 400,
    }

    resp = requests.post(API_URL, headers=headers, json=body, timeout=60)
    resp.raise_for_status()
    data = resp.json()
    return data["choices"][0]["message"]["content"]


def main():
    print("🔄 Lade RAG-Index ...")
    collection = load_collection()
    print("✅ Index geladen.\n")

    while True:
        frage = input("❓ Deine Frage (oder 'exit'): ")
        if frage.strip().lower() == "exit":
            break

        context, docs_metas = retrieve_context(collection, frage, k=4)

        print("\n📚 (intern) Kontext-Ausschnitte, die ans Modell geschickt werden:\n")
        print(context[:800] + "...\n")
        print("🤖 Antwort vom Modell:\n" + "-" * 60)

        try:
            answer = call_llm(frage, context)
        except Exception as e:
            answer = f"❌ Fehler beim Aufruf des Modells: {e}"

        print(answer)
        print("\n" + "=" * 80 + "\n")


if __name__ == "__main__":
    main()
