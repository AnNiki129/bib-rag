import os
import textwrap
import requests

import chromadb
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction

import re

def _tokens(text: str) -> set[str]:
    text = text.lower()
    text = re.sub(r"[^a-z0-9äöüß]+", " ", text)
    toks = [t for t in text.split() if len(t) >= 3]
    return set(toks)

def lexical_overlap_score(question: str, doc: str) -> float:
    q = _tokens(question)
    d = _tokens(doc)
    if not q or not d:
        return 0.0
    return len(q & d) / len(q)


def detect_language(text: str) -> str:
    """
    Sehr einfache Spracherkennung:
    - gibt 'en' zurück, wenn der Text eher nach Englisch aussieht
    - sonst 'de'
    """
    t = text.lower()

    de_keywords = ["wie", "wann", "wo", "wieviel", "wieviele", "bücher", "ausleihe", "ausleihen", "leihfrist", "gebühr", "bibliothek"]
    en_keywords = ["how", "when", "where", "what", "books", "loan", "library", "fee", "online", "search"]

    score_de = sum(kw in t for kw in de_keywords)
    score_en = sum(kw in t for kw in en_keywords)

    # Wenn mehr englische Schlüsselwörter: Englisch
    if score_en > score_de:
        return "en"
    # Sonst Standard: Deutsch
    return "de"


CHROMA_DIR = "chroma_bib"
COLLECTION_NAME = "bib"


# 🔁 Werte an Provider anpassen
API_URL = "http://localhost:11434/api/chat"  # Beispiel-Endpunkt
MODEL_NAME = "llama3"  # z.B. SauerkrautLM / Llama-3.1-SauerkrautLM-70b-Instruct /llama3


def load_collection():
    embed_fn = SentenceTransformerEmbeddingFunction(
        model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    )
    client = chromadb.PersistentClient(path=CHROMA_DIR)
    collection = client.get_collection(
        name=COLLECTION_NAME,
        embedding_function=embed_fn,
    )
    return collection


def expand_query(question: str) -> str:
    q = question.lower()
    # DE/EN: "how long can I borrow" / "wie lange darf ich ausleihen"
    if ("wie lange" in q and ("ausleihen" in q or "leihfrist" in q or "bücher" in q)) or \
       ("how long" in q and ("borrow" in q or "loan" in q or "books" in q)):
        return question + " § 10 Ortsleihe Leihfrist drei Wochen"
    return question


def retrieve_context(
    collection,
    question: str,
    k: int = 12,
    max_distance: float = 0.85,
    final_k: int = 5,
):
    result = collection.query(
        query_texts=[question],
        n_results=k,
        include=["documents", "metadatas", "distances"],
    )

    docs = result["documents"][0]
    metas = result["metadatas"][0]
    dists = result.get("distances", [[]])[0]

    candidates = []
    for doc, meta, dist in zip(docs, metas, dists):
        if dist is not None and dist > max_distance:
            continue

        sem = 1.0 - float(dist) if dist is not None else 0.0
        lex = lexical_overlap_score(question, doc)

        # Semantik ist wichtiger, Lexical ist nur der "Rerank-Feinschliff"
        score = 0.75 * sem + 0.25 * lex
        candidates.append((score, doc, meta, dist, sem, lex))

    if not candidates:
        return "", []

    candidates.sort(key=lambda x: x[0], reverse=True)
    selected = candidates[:final_k]
    # Debug-Ausgabe der Top-Kandidaten
    print("Top selected:")
    for s in selected[:3]:
        score, _, meta, dist, sem, lex = s
        print("score", score, "dist", dist, "sem", sem, "lex", lex, "section", meta.get("section"), "page", meta.get("page"))


    blocks = []
    kept = []
    for i, (score, doc, meta, dist, sem, lex) in enumerate(selected, start=1):
        title = meta.get("title", "Quelle")
        source = meta.get("source", "")
        page = meta.get("page")
        section = meta.get("section")

        extra = []
        if page is not None:
            extra.append(f"Seite {page}")
        if section:
            extra.append(section)

        extra_str = ("; " + ", ".join(extra)) if extra else ""
        blocks.append(f"[{i}] {title} ({source}{extra_str})\n{doc.strip()}")

        kept.append((doc, meta, dist, score, sem, lex))

    return "\n\n---\n\n".join(blocks), kept




def call_llm(question: str, context: str) -> str:

    lang = detect_language(question) # "de" oder "en"
    if lang == "de":
        language_header = "Antworte ausschließlich auf Deutsch."
    else: 
        language_header = "Answer exclusively in English."


    system_prompt = textwrap.dedent("""
        You are a precise university library assistant.

        RULES:
        - Use ONLY the information from the provided context.
        - Do NOT invent facts, numbers, or rules.
        - Every important factual statement MUST include a source tag like [1], [2], ...
        - Answer in the SAME language as the user's question (German or English).
        - The context may be in German. If the question is English, translate the supported facts into English.
        - If the answer is not clearly supported by the context, say so clearly in the user's language.
    """)

    user_prompt = f"""
    {language_header}

    KONTEXT/CONTEXT:
    {context}

    FRAGE/QUESTION:
    {question}

    AUSGABE/OUTPUT:
    - First: short direct answer (1–2 sentences).
    - Then: 1–3 short details if helpful.
    - End with: Sources: [1], [2]
    """

    headers = {"Content-Type": "application/json"}
    body = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "system", "content": system_prompt.strip()},
            {"role": "user", "content": user_prompt.strip()},
        ],
        "stream": False,
    }

    resp = requests.post(API_URL, headers=headers, json=body, timeout=120)
    resp.raise_for_status()
    return resp.json()["message"]["content"]







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
