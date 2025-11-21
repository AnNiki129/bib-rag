import textwrap
import chromadb
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction

CHROMA_DIR = "chroma_bib"
COLLECTION_NAME = "bib"


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


def build_answer(question: str, docs_metas):
    lines = []
    lines.append(f"Frage: {question}")
    lines.append("")
    lines.append("Mögliche Antwort (basierend auf gefundenen Textstellen):")
    lines.append("")

    for i, (doc, meta) in enumerate(docs_metas, start=1):
        title = meta.get("title", "Quelle")
        source = meta.get("source", "")
        snippet = doc.replace("\n", " ")
        if len(snippet) > 400:
            snippet = snippet[:400] + "..."
        lines.append(f"[{i}] {title} ({source})")
        lines.append(textwrap.fill(snippet, width=90))
        lines.append("")

    lines.append("⚠️ Dies ist eine reine RAG-Antwort ohne KI-Formulierung.")
    return "\n".join(lines)


def main():
    print("🔄 Lade RAG-Index ...")
    collection = load_collection()
    print("✅ Index geladen.\n")

    while True:
        frage = input("❓ Deine Frage (oder 'exit'): ")
        if frage.strip().lower() == "exit":
            break

        result = collection.query(
            query_texts=[frage],
            n_results=8,
        )

        docs = result["documents"][0]
        metas = result["metadatas"][0]

        docs_metas = list(zip(docs, metas))
        answer = build_answer(frage, docs_metas)

        print("\n" + "=" * 80)
        print(answer)
        print("=" * 80 + "\n")


if __name__ == "__main__":
    main()
