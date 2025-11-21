import os
import textwrap
import requests

import chromadb
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction


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
MODEL_NAME = "llama3"  # z.B. SauerkrautLM / Llama 3.1 70B Instruct/llama3


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


def retrieve_context(collection, question: str, k: int = 8):
    """Holt die wichtigsten Textstellen aus dem RAG und filtert nach Themen."""

    result = collection.query(
        query_texts=[question],
        n_results=k,
    )

    docs = result["documents"][0]
    metas = result["metadatas"][0]
    docs_metas = list(zip(docs, metas))

    # THEMEN-ERKENNUNG  -------------------------------------------
    q = question.lower()

    thema_ausleihe = ["ausleihe", "ausleihen", "leihfrist", "verlängern", "verlängerung", "medien", "bücher", "buch", "fernleihe", 
    "mitarbeiter", "student", "wie viele"]
    thema_gebuehren = ["gebühr", "säumnis", "mahnung", "müssen zahlen","kosten", "wie viel"]
    thema_oeffnungszeiten = ["geöffnet", "öffnungszeiten", "wann", "zweibrücken", "kaiserslautern", "pirmasens", "standort"]
    thema_bank = ["bankverbindung", "iban", "überweisung","zu spät", "zahlen", "konto"]
    thema_online = ["search", "ebooks", "online", "journal", "zugriff", "from home"]

    if any(w in q for w in thema_ausleihe):
        keywords = ["leihfrist", "wochen", "verlängern", "ausleihe", "medien", "ausleihen", "fernleihe", "bücher", "buch",  "mitarbeiter", "student", "ich", "wie viele"]
    elif any(w in q for w in thema_gebuehren):
        keywords = ["gebühr", "säumnis", "mahnung", "zahlen", "kosten", "müssen", "wie viel"]
    elif any(w in q for w in thema_oeffnungszeiten):
        keywords = ["öffnungszeiten", "geöffnet", "bibliothek", "standort", "kaiserslautern", "zweibrücken", "pirmasens", "wann"]
    elif any(w in q for w in thema_bank):
        keywords = ["iban", "konto", "bank", "überweisung", "zahlen", "bankverbindung", "zu spät"]
    elif any(w in q for w in thema_online):
        keywords = ["online", "katalog", "zugriff", "discovery", "e-book"]
    else:
        keywords = []

    # Filter anwenden --------------------------------------------------
    if keywords:
        filtered = []
        for doc, meta in docs_metas:
            text = doc.lower()
            if any(kw in text for kw in keywords):
                filtered.append((doc, meta))

        if filtered:
            docs_metas = filtered

    # Kontext zusammenbauen -------------------------------------------
    blocks = []
    for i, (doc, meta) in enumerate(docs_metas, start=1):
        title = meta.get("title", "Quelle")
        source = meta.get("source", "")
        block = f"[{i}] {title} ({source})\n{doc}"
        blocks.append(block)

    return "\n\n---\n\n".join(blocks), docs_metas


def call_llm(question: str, context: str) -> str:
    """Ruft das LLM über Ollama auf und antwortet je nach Sprache der Frage nur DE oder nur EN."""

    lang = detect_language(question)

    if lang == "en":
        # ✅ ENGLISCHE ANTWORT
        system_prompt = textwrap.dedent("""
            You are a university library assistant.
            You answer questions about the library (loan periods, renewals, opening hours,
            fees, bank details, online catalog, etc.).

            RULES:
            - Use ONLY the information from the provided context.
            - Do NOT invent facts or links.
            - Answer ONLY in English.
            - If the answer is not clearly contained in the context, say so explicitly
              and refer the user to the library staff.
            - You may use the official catalog and library links if relevant.
        """)

        user_prompt = f"""
        Question from a person:
        {question}

        Relevant context from library documents:
        {context}

        Task:
        - Read the context carefully.
        - Answer the question ONLY using information from this context.
        - If the context does not contain a reliable answer, say that it cannot be answered
          reliably and suggest contacting the library.

        Answer format (English only):

        Short answer:
        - 1–2 bullet points with the key information.

        Details:
        - 2–4 short sentences with important details from the context.
        - Do not invent information.

        Links (if relevant):
         -  eMedien: https://www.hs-kl.de/hochschule/servicestellen/bibliothek/emedien

        -   Online-Catalog: https://hbz-hkl.primo.exlibrisgroup.com/discovery/search?vid=49HBZ_HKL:VU1

        -   interlibrary loan: https://www.hs-kl.de/hochschule/servicestellen/bibliothek/fernleihe

        -   Opening hours-Kaiserlautern: https://www.hs-kl.de/hochschule/servicestellen/bibliothek/kontakt-oeffnungszeiten-kaiserslautern

        -   Opening hours-Zweibrücken: https://www.hs-kl.de/hochschule/servicestellen/bibliothek/kontakt-oeffnungszeiten-zweibruecken

        -   Opening hours-Pirmasens: https://www.hs-kl.de/hochschule/servicestellen/bibliothek/kontakt-oeffnungszeiten-pirmasens

        Sources:
        - e.g. Sources: [1], [3]
        """ 

    else:
        # ✅ DEUTSCHE ANTWORT
        system_prompt = textwrap.dedent("""
            Du bist ein Bibliotheksassistent an einer Hochschule.
            Du beantwortest Fragen zur Bibliothek (Ausleihe, Verlängerung, Öffnungszeiten,
            Gebühren, Bankverbindung, Online-Katalog usw.).

            REGELN:
            - Nutze AUSSCHLIESSLICH die Informationen aus dem bereitgestellten Kontext.
            - Erfinde KEINE Fakten und KEINE zusätzlichen Links.
            - Antworte NUR auf Deutsch.
            - Wenn die Frage im Kontext nicht sicher beantwortet werden kann,
              sage das klar und verweise auf die Bibliothek.
            - Du darfst offizielle Links zur Bibliothek nennen, wenn sie zur Frage passen.
        """)

        user_prompt = f"""
        Frage einer Person:
        {question}

        Relevante Auszüge aus Bibliotheksdokumenten:
        {context}

        Aufgabe:
        - Lies den Kontext sorgfältig.
        - Beantworte die Frage NUR mit Informationen aus diesem Kontext.
        - Wenn keine sichere Antwort möglich ist, schreibe das ausdrücklich
          und schlage vor, sich direkt an die Bibliothek zu wenden.

        Antwortformat (nur Deutsch):

        Kurzantwort:
        - 1–2 Stichpunkte mit der wichtigsten Information.

        Details:
        - 2–4 kurze Sätze mit den wichtigsten Details aus dem Kontext.
        - Keine erfundenen Informationen.

        Links:
        -   eMedien: https://www.hs-kl.de/hochschule/servicestellen/bibliothek/emedien

        -   Online-Catalog: https://hbz-hkl.primo.exlibrisgroup.com/discovery/search?vid=49HBZ_HKL:VU1

        -   Fernleihe: https://www.hs-kl.de/hochschule/servicestellen/bibliothek/fernleihe

        -   Öffnungszeiten-Standort-Kaiserlautern: https://www.hs-kl.de/hochschule/servicestellen/bibliothek/kontakt-oeffnungszeiten-kaiserslautern

        -   Öffnungszeiten-Standort-Zweibrücken: https://www.hs-kl.de/hochschule/servicestellen/bibliothek/kontakt-oeffnungszeiten-zweibruecken

        -   Öffnungszeiten-Standort-Pirmasens: https://www.hs-kl.de/hochschule/servicestellen/bibliothek/kontakt-oeffnungszeiten-pirmasens
    



        Quellen:
        - z.B.: Quellen: [1], [3]
        """

    headers = {
        "Content-Type": "application/json",
    }

    body = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "system", "content": system_prompt.strip()},
            {"role": "user",   "content": user_prompt.strip()},
        ],
        "stream": False,
    }

    resp = requests.post(API_URL, headers=headers, json=body, timeout=120)
    resp.raise_for_status()
    data = resp.json()
    return data["message"]["content"]






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
