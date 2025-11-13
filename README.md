"#bib-rag" 

## Bibliotheks-Chatbot der Hochschule - RAG-basiertes Frage-Antwort-System
----------------------------------------------------------------------------------------
  Dieses Projekt implementiert einen Chatbot für die Hochschulbibliothek.
  Der Chatbot verwendet ein "Retrieval-Augmented Generation(RAG)"-System, um zuverlässige faktenbasierte Antworten zu liefern- basierend auf offiziellen Dokumenten.
  
----------------------------------------------------------------------------------------
## Features

  - beantwortet bibliotheksbezogene Fragen ( Öffnungszeiten, Ausleihe, Gebühren usw.)
  - testaufbau vom RAG-System mit Chroma als Vektordatenbank
  - Automatischer Import von PDF-Dokumenten
  - Chnunking der Texte und Embedding durch "Sentence-transformers"
  - Anbindung eines LLMs (Llama 3.1 Sauerkraut)
