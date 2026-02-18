from pathlib import Path
import re
import fitz
from bs4 import BeautifulSoup
import chromadb
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction

DATA_DIR = Path("data")
CHROMA_DIR = "chroma_bib"
COLLECTION_NAME = "bib"

SECTION_RE = re.compile(r"(^|\n)\s*(§\s*\d+\s+[^\n]+)", re.MULTILINE)

def load_text(path: Path) -> str:
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

    return ""  # PDFs behandeln wir separat (seitenweise)

def split_by_sections(text: str):
    """
    Splitte Text nach Paragraphen-Überschriften wie '§ 10 Ortsleihe'.
    Gibt Liste von (section_title, section_text) zurück.
    """
    text = text.strip()
    if not text:
        return []

    matches = list(SECTION_RE.finditer(text))
    if not matches:
        return [("","",)]  # fallback

    sections = []
    for i, m in enumerate(matches):
        start = m.start(2)
        end = matches[i+1].start(2) if i+1 < len(matches) else len(text)
        title = m.group(2).strip()
        body = text[start:end].strip()
        sections.append((title, body))
    return sections

def chunk_text(text: str, max_chars: int = 1200, overlap: int = 200):
    text = text.strip()
    if not text:
        return []

    length = len(text)
    overlap = min(overlap, max_chars // 2, max(0, length - 1))

    chunks = []
    start = 0
    while start < length:
        end = min(start + max_chars, length)
        chunk = text[start:end]

        if end == length:
            if len(chunk.strip()) > 50:
                chunks.append(chunk.strip())
            break

        split_pos = chunk.rfind(" ")
        if split_pos > 0:
            chunk = chunk[:split_pos]
            end = start + split_pos

        if len(chunk.strip()) > 50:
            chunks.append(chunk.strip())

        start = end - overlap
        if start <= 0 and end >= length:
            break

    return chunks

def iter_pdf_page_texts(path: Path):
    doc = fitz.open(path)
    for page_idx, page in enumerate(doc, start=1):
        t = page.get_text().strip()
        if t:
            yield page_idx, t

def main():
    docs = []
    metas = []

    for file in DATA_DIR.glob("*"):
        suffix = file.suffix.lower()
        if suffix not in [".pdf", ".txt", ".md", ".html", ".htm"]:
            print(f"⚠️ Ignoriere {file.name} (unbekannter Typ)")
            continue

        if suffix == ".pdf":
            # ✅ PDF: seitenweise + §-weise
            total_chunks = 0
            for page_num, page_text in iter_pdf_page_texts(file):
                sections = split_by_sections(page_text)
                if sections and sections != [("","",)]:
                    for section_title, section_text in sections:
                        for c in chunk_text(section_text, max_chars=1200, overlap=150):
                            docs.append(c)
                            metas.append({
                                "source": str(file),
                                "title": file.stem,
                                "page": page_num,
                                "section": section_title,
                            })
                            total_chunks += 1
                else:
                    
                    # fallback: wenn Seite kurz ist → als ein Chunk speichern
                    page_text_clean = page_text.strip()

                    if len(page_text_clean) < 3500:
                        docs.append(page_text_clean)
                        metas.append({
                            "source": str(file),
                            "title": file.stem,
                            "page": page_num,
                        })
                        total_chunks += 1
                    else:
                        for c in chunk_text(page_text_clean, max_chars=1200, overlap=150):
                            docs.append(c)
                            metas.append({
                                "source": str(file),
                                "title": file.stem,
                                "page": page_num,
                            })
                            total_chunks += 1


            print(f"📄 Verarbeite {file.name}, erzeugte Chunks: {total_chunks}")
            continue

        # ✅ Nicht-PDF: wie gehabt
        text = load_text(file)
        if not text.strip():
            print(f"⚠️ Keine verwertbaren Inhalte in: {file.name}, überspringe.")
            continue

        chunks = chunk_text(text, max_chars=1200, overlap=200)
        print(f"📄 Verarbeite {file.name}, erzeugte Chunks: {len(chunks)}")
        for c in chunks:
            docs.append(c)
            metas.append({"source": str(file), "title": file.stem})

    if not docs:
        print("❌ Keine Dokumente/Chunks gefunden. Bitte PDFs in 'data/' legen.")
        return

    embed_fn = SentenceTransformerEmbeddingFunction(
        model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    )
    client = chromadb.PersistentClient(path=CHROMA_DIR)
    try:
        client.delete_collection(COLLECTION_NAME)
    except Exception:
        pass

    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        embedding_function=embed_fn,
    )

    ids = [f"doc_{i}" for i in range(len(docs))]
    collection.add(ids=ids, documents=docs, metadatas=metas)

    print(f"✅ Index aufgebaut: '{CHROMA_DIR}' / Collection '{COLLECTION_NAME}'.")

if __name__ == "__main__":
    main()

