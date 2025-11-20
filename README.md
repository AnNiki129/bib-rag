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
Außerdem eine erstellte Anleitung für das Bibliothekspersonal um den Prototypen anzulernen und selbst verwalten.
  Zeitraum: 6 Wochen
  Technologien: Python 3.12.6, Streamlit, RAG(Retrieval-Augmented Generation),ChromaDB,Ollama,PDF-Parsing,Git
  
-----------------------------------------------------------------------------------------
## Systemarchitektur

Alle relevanten Bibliotheksinformationen wurden gesammelt und in PDF-Form bereitgestellt unter ```bib-rag/data ```
- Bibliotheksordnung
- Gebührenverzeichnis
- Ausleihregeln
- Bankverbindung
- Standordinformationen

 # Extraktion & Chunking
Mit Python und pydf wird aus jeder PDF der Text extrahiert.
Der Chunking-Algorithmus zerlegt die Abschnitte in sinnvolle kleine, semantische Abschnitte die 
- ca 1000-1.200 Zeichen pro Chunk groß sind und
- 200 Zeichen überlappung (Overlaps)
damit ist sichergestellt, dass keine Sätze abgeschnitten werden und der Zusammenhang versntanden wird.


# Speicherung in ChromaDB

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

 # Kontextsuche

Bei jeder Nutzerfrage passiert:
1. Frage wird analysiert -> Thema erkannt(Ausleihe, Öffnungzeiten, ...)
2. Chroma liefert die relevantesten Chunks
3. Bei bedarf werden die Chunks gefiltert
4. Nur relevente Textstellen gehen an das LLM


# LLM-Beantwortung
im folgenden Beispiel wird noch für den Prototypen Ollama als LLM benutz. Später sollte es 
durch ```Llama 3.1 SauerkrautLM 70B Instruct``` abgelöst werden.

Ollama läuft standardmäßig unter : 
```http://localhost:11434/api/chat```

Das Modell bekommt einen präzisen System-Promt um zu vermeiden dass,
- halluzieniert wird
- oder antworten unstrukturiert erzeugt werden
Bei englischen/deutschen Fragen antwortet es der Sprache entsprechend.

# Web-GUI mit Streamlit(für Prototypen)

Streamlit bietet eine einfache Weboberfläche:
- Eingabefeld für die Fragen
- Ausgabe aus dem LLM
- RAG-Kontext und Quellen(intern)
- läuft über den Aufruf  ```streamlit run app.py ```

-----------------------------------------------------------------------------------------
## Funktionen des Chatbots

  # Antwortgenerierung(LLM +RAG)
   Der bot beantwortet Fragen auf Grundlagen der offiziellen PDF-Dokumente

  # Automatische Spracherkennung
   - wenn Frage in Englisch gestellt -> Englische Ausgabe, ansosnten auf Deutsch

  # Antwortformat
   -  Kurzantwort:
        - 1–2 Stichpunkte mit der wichtigsten Information.

        Details:
        - 2–4 kurze Sätze mit den wichtigsten Details aus dem Kontext.
        - Keine erfundenen Informationen.
          
   - offizielle Links
   - Quellenagaben
     
  # Sichere vermeidung von Halluinationen 
   - durch Regeln
   - durch Filter
     
  # lokale Datenhaltung(keine DSGVO nötig da auch keine Nutzerdaten gespeichert werden) 

 -----------------------------------------------------------------------------------------

 ## Projektstruktur
```bib-rag/
│
├── app.py                # Streamlit-Weboberfläche
├── chat.py               # LLM + Prompt + Language Detection + RAG Integration
├── chat_finder.py        # ChromaDB Loader und Kontextsuche
├── chatOpenAI.py         # gleiche Struktur wie chat.py nur mit OpenAI-KEY Anforderung
├── index.py              # PDF-Importer + Chunker + Embedding-Generator
├── test_rag.py           # Testtool zum Prüfen der RAG-Ergebnisse
│
├── data/                 # Alle Bibliotheks-PDFs
│   ├── ausleihregeln_de_en.pdf
│   ├── LESE_BibliotheksO.pdf
│   ├── LESE_Gebuehrenverzeichnis.pdf
│   ├── standortbibliothek_zweibruecken.pdf
│   ├── bankverbindung.pdf
│   ├── … (weitere)
│
├── chroma_bib/           # ChromaDB Index (wird automatisch erstellt)
│
├── .venv/                # Python-Virtual-Environment
├── requirements.txt      # Abhängigkeiten
└── README.md             # Projektdokumentation
```
 -----------------------------------------------------------------------------------------


## Installation & Setup

# 1. Python installieren
   
  - Python 3.10 oder 3.11 von https://www.python.org/downloads/ herunterladen.
  - „Add Python to PATH“ aktivieren.
  - Installation prüfen:
    ```python --version```
  - pip aktualisieren:
    ```python -m pip install --upgrade pip ```
    
# 2. Projekt herunterladen
   
- ```bash
     git clone https://github.com/AnNiki129/bib-rag.git
- ``` bash
     cd bib-rag
- ``` bash
     git pull```

# 3. Virtuelle Umgebung (.venv)
   
 - ```python -m venv .venv```
 - ```.\.venv\Scripts\activate```
 
  Falls Scripts gesperrt:
  
 - ```Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass```
  
# 4. Abhängigkeiten installieren
   
 - ```pip install -r requirements.txt```
 
# 5. Daten vorbereiten

 - ```/data Ordner enthält alle Bibliotheks-PDFs.```
 
# 6. RAG-Index bauen
    
 - ```python index.py```
 
# 7. Ollama installieren
    
 - ```https://ollama.com/download```
 
# 8. LLM-Modell laden
    
 - ```ollama pull llama3.1:70b```
 - ```ollama list```
 
# 9. Backend testen
    
 - ```python test_rag.py```
 - ```python chat.py```
 
# 10. Streamlit starten
    
 - ```streamlit run app.py```
 - ```http://localhost:```
 
# Troubleshooting
   Fehler " Cannot be loaded because running scripts is disabled"
    - ```Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass```
      
   Fehler: Modul „chromadb“ fehlt
    - ``` pip install chromadb ```
      
   Fehler bei pyarrow
    - ``` andere python version installieren```
  
   Index wird nicht aktualisiert
    -> Ordner löschen
      - ```chroma_bib/```
    -> Dann:
      - ```python index.py```





