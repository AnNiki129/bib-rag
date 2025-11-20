"#bib-rag" 

## Bibliotheks-Chatbot der Hochschule - RAG-basiertes Frage-Antwort-System
----------------------------------------------------------------------------------------
  Dieses Projekt implementiert einen Chatbot für die Hochschulbibliothek.
  Der Chatbot verwendet ein "Retrieval-Augmented Generation(RAG)"-System, um zuverlässige faktenbasierte Antworten zu liefern-    basierend auf offiziellen Dokumenten.
  Die Studdierenden und Mitarbeiter sollen typische Fragen stellen können - etwa zu:
  - Ausleihe und Leihfristen
  - Verlängerungen von Medien
  - Öffnungszeiten der Standorte
  - Gebühren und Bankverbindungen
  - Online-Katalog/Recherche
  - allgemeine Bibliotheksnutzung
 Der Chatbot soll später in die Hochschulwebseite eingebunden werden, um die Bibliothek für Studierende moderner und      zugänglicher zu machen.
  Zeitraum: 6 Wochen
  Technologien: Python, Streamlit, RAG(Retrieval-Augmented Generation),ChromaDB,Ollama,PDF-Parsing,Git
  
----------------------------------------------------------------------------------------
## Features

  - beantwortet bibliotheksbezogene Fragen ( Öffnungszeiten, Ausleihe, Gebühren usw.)
  - testaufbau vom RAG-System mit Chroma als Vektordatenbank
  - Automatischer Import von PDF-Dokumenten
  - Chnunking der Texte und Embedding durch "Sentence-transformers"
  - Anbindung eines LLMs für die Vollversion (Llama 3.1 Sauerkraut) für den Prototypen genutztes LLM(Ollama)
-----------------------------------------------------------------------------------------
## Systemarchitektur

Alle relevanten Bibliotheksinformationen wurden gesammelt und in PDF-Form bereitgestellt unter ´´´bash bib-rag/data ´´´
- Bibliotheksordnung
- Gebührenverzeichnis
- Ausleihregeln
- Bankverbindung
- Standordinformationen
-----------------------------------------------------------------------------------------
## Extraktion & Chunking
Mit Python und pydf wird aus jeder PDF der Text extrahiert.
Der Chunking-Algorithmus zerlegt die Abschnitte in sinnvolle kleine, semantische Abschnitte die 
- ca 1000-1.200 Zeichen pro Chunk groß sind und
- 200 Zeichen überlappung (Overlaps)
damit ist sichergestellt, dass keine Sätze abgeschnitten werden und der Zusammenhang versntanden wird.

-----------------------------------------------------------------------------------------
## Speicherung in ChromaDB

Die textlichen Chunks werden in einer lokalen ChromaDB gespeichert
'''bash
/chroma_bib
    → Collection "bib"
'''

  












