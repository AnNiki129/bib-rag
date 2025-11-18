from pathlib import Path
import re

import fitz  # aus pymupdf
from bs4 import BeautifulSoup

import chromadb
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction


DATA_DIR = Path("data")
CHROMA_DIR = "chroma_bib"
COLLECTION_NAME = "bib"


def load_text(path: Path) -> str:
    """Liest Text aus PDF/HTML/TXT/MD und gibt reinen Text zurück."""
    suffix = path.suffix.lower()

    if suffix in [".txt", ".md"]:
        return path.read_text(encoding="utf-8", errors="ignore")

    if suffix in [".html", ".htm"]:
        html = path.read_text(encoding="utf-8", errors="ignore")
        soup = BeautifulSoup(html, "lxml")
        for tag in soup(["script", "style", "nav", "footer"]):
            tag.decompose()
        text = soup.get_text("\n")
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()

    if suffix == ".pdf":
        doc = fitz.open(path)
        pages = [page.get_text() for page in doc]
        return "\n".join(pages)

    return ""


def chunk_text(text: str, max_chars: int = 1000, overlap: int = 200):
    """Zerlegt langen Text in überlappende Chunks"""
    text = text.strip()
    length = len(text)
    if length == 0:
        return []

    # overlap darf nicht größer sein als die Chunkgröße oder Textlänge
    overlap = min(overlap, max_chars // 2, max(0, length - 1))

    chunks = []
    start = 0

    while start < length:
        end = min(start + max_chars, length)
        chunk = text[start:end]

        # Letzter Chunk: danach abbrechen
        if end == length:
            if len(chunk.strip()) > 50:
                chunks.append(chunk.strip())
            break

        # Möglichst am Wortende trennen
        split_pos = chunk.rfind(" ")
        if split_pos > 0:
            chunk = chunk[:split_pos]
            end = start + split_pos

        if len(chunk.strip()) > 50:
            chunks.append(chunk.strip())

        # Nächster Start – immer vorwärts gehen, nicht wieder bei 0 landen
        start = end - overlap
        if start <= 0 and end >= length:
            break

    return chunks



def main():
    # 1) PDFs & andere Dateien einlesen
    docs = []
    metas = []

    for file in DATA_DIR.glob("*"):
        if file.suffix.lower() not in [".pdf", ".txt", ".md", ".html", ".htm"]:
            print(f"⚠️  Ignoriere {file.name} (unbekannter Typ)")
            continue

        text = load_text(file)
        if not text.strip():
            print(f"⚠️  Keine verwertbaren Inhalte in: {file.name}, überspringe.")
            continue

        chunks = chunk_text(text, max_chars=1200, overlap=200)
        print(f"📄 Verarbeite {file.name}, erzeugte Chunks: {len(chunks)}")
        if not chunks:
            print(f"⚠️  Keine Chunks erzeugt für: {file.name}, überspringe.")
            continue

        for c in chunks:
            docs.append(c)
            metas.append({"source": str(file), "title": file.stem})

    if not docs:
        print("❌ Keine Dokumente/Chunks gefunden. Bitte PDFs in den Ordner 'data/' legen.")
        return

    print(f"📄 Dokumente/Chunks gesamt: {len(docs)}")

    # 2) Chroma-Client + Embedding-Funktion
    embed_fn = SentenceTransformerEmbeddingFunction(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )

    client = chromadb.PersistentClient(path=CHROMA_DIR)

    # existierende Collection ggf. löschen (Neuaufbau)
    try:
        client.delete_collection(COLLECTION_NAME)
    except Exception:
        pass

    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        embedding_function=embed_fn,
    )

    # 3) Daten hinzufügen
    ids = [f"doc_{i}" for i in range(len(docs))]

    collection.add(
        ids=ids,
        documents=docs,
        metadatas=metas,
    )

    print(f"✅ Index aufgebaut. Chunks gespeichert in '{CHROMA_DIR}' / Collection '{COLLECTION_NAME}'.")


if __name__ == "__main__":
    main()
