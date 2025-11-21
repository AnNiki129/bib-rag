import chromadb
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction

CHROMA_DIR = "chroma_bib"
COLLECTION_NAME = "bib"

def main():
    print("🔄 Lade Chroma-Index ...")

    embed_fn = SentenceTransformerEmbeddingFunction(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )

    client = chromadb.PersistentClient(path=CHROMA_DIR)
    collection = client.get_collection(
        name=COLLECTION_NAME, 
        embedding_function=embed_fn
    )

    print("✅ Index geladen.\n")

    while True:
        frage = input("❓ Deine Frage (oder 'exit'): ")
        if frage.lower().strip() == "exit":
            break

        result = collection.query(
            query_texts=[frage],
            n_results=8,
        )

        docs = result["documents"][0]
        metas = result["metadatas"][0]

        print("\n🔎 Beste gefundene Textstellen:\n")
        for doc, meta in zip(docs, metas):
            print(f"📄 Quelle: {meta.get('title')} ({meta.get('source')})")
            print(doc[:400], "...\n---\n")

if __name__ == "__main__":
    main()
