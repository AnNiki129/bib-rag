import streamlit as st
from chat import load_collection, retrieve_context, call_llm

st.set_page_config(page_title="Bibliotheks-Chatbot", page_icon="📚")


@st.cache_resource
def get_collection():
    return load_collection()


def main():
    st.title("📚 Bibliotheks-Chatbot")
    st.write("Stelle hier deine Fragen zur Bibliothek (Ausleihe, Öffnungszeiten, Gebühren, ...).")

    # Chat-Verlauf initialisieren
    if "messages" not in st.session_state:
        st.session_state["messages"] = []

    # Bisherige Nachrichten anzeigen
    for role, content in st.session_state["messages"]:
        with st.chat_message(role):
            st.markdown(content)

    frage = st.chat_input("Deine Frage...")

    if frage:
        # Nutzerfrage anzeigen
        st.session_state["messages"].append(("user", frage))
        with st.chat_message("user"):
            st.markdown(frage)

        # RAG-Index erst jetzt laden, NICHT vor UI
        try:
            with st.spinner("Lade Suchindex der Bibliothek..."):
                collection = get_collection()
        except Exception as e:
            with st.chat_message("assistant"):
                st.error(f"Fehler beim Laden des RAG-Index: {e}")
            return

        # Kontext aus RAG holen
        with st.spinner("Suche relevante Infos..."):
            context, docs_metas = retrieve_context(collection, frage, k=4)

        # Antwort erzeugen 
        with st.chat_message("assistant"):
            with st.spinner("Formuliere Antwort..."):
                antwort = call_llm(frage, context)
                st.markdown(antwort)

        st.session_state["messages"].append(("assistant", antwort))


if __name__ == "__main__":
    main()
