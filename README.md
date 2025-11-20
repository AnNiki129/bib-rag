"#bib-rag" 

## Bibliotheks-Chatbot der Hochschule - RAG-basiertes Frage-Antwort-System
----------------------------------------------------------------------------------------
  Dieses Projekt implementiert einen Chatbot für die Hochschulbibliothek.
  Der Chatbot verwendet ein "Retrieval-Augmented Generation(RAG)"-System, um zuverlässige faktenbasierte Antworten zu     liefern- basierend auf offiziellen Dokumenten.
  Die Studdierenden und Mitarbeiter sollen typische Fragen stellen können - etwa zu:
  - Ausleihe und Leihfristen
  - Verlängerungen von Medien
  - Öffnungszeiten der Standorte
  - Gebühren und Bankverbindungen
  - Online-Katalog/Recherche
  - allgemeine Bibliotheksnutzung
 Der Chatbot soll später in die Hochschulwebseite eingebunden werden, um die Bibliothek für Studierende moderner und      zugänglicher zu machen.
  Zeitraum: 6 Wochen
  Technologien: Python 3.12.6, Streamlit, RAG(Retrieval-Augmented Generation),ChromaDB,Ollama,PDF-Parsing,Git
  
----------------------------------------------------------------------------------------
## Features

  - beantwortet bibliotheksbezogene Fragen ( Öffnungszeiten, Ausleihe, Gebühren usw.)
  - testaufbau vom RAG-System mit Chroma als Vektordatenbank
  - Automatischer Import von PDF-Dokumenten
  - Chnunking der Texte und Embedding durch "Sentence-transformers"
  - Anbindung eines LLMs für die Vollversion (Llama 3.1 Sauerkraut) für den Prototypen genutztes LLM(Ollama)
-----------------------------------------------------------------------------------------
## Systemarchitektur

Alle relevanten Bibliotheksinformationen wurden gesammelt und in PDF-Form bereitgestellt unter ```bib-rag/data ```
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
```
/chroma_bib
    → Collection "bib"
```
Jeder Chunk ist gespeichert mit:
- Text
- PDF-Quelle
- Dateiname
- Embedding
-----------------------------------------------------------------------------------------
## Kontextsuche

Bei jeder Nutzerfrage passiert:
1. Frage wird analysiert -> Thema erkannt(Ausleihe, Öffnungzeiten, ...)
2. Chroma liefert die relevantesten Chunks
3. Bei bedarf werden die Chunks gefiltert
4. Nur relevente Textstellen gehen an das LLM

-----------------------------------------------------------------------------------------
## LLM-Beantwortung
im folgenden Beispiel wird noch für den Prototypen Ollama als LLM benutz. Später sollte es 
durch ```Llama 3.1 SauerkrautLM 70B Instruct``` abgelöst werden.

Ollama läuft standardmäßig unter : 
```http://localhost:11434/api/chat```

Das Modell bekommt einen präzisen System-Promt um zu vermeiden dass,
- halluzieniert wird
- oder antworten unstrukturiert erzeugt werden
Bei englischen/deutschen Fragen antwortet es der Sprache entsprechend.

-----------------------------------------------------------------------------------------


  












