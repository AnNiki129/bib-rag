import streamlit as st


from chat import load_collection, call_llm, retrieve_context 


# 1) RAG-Index einmal laden (nicht bei jeder Anfrage neu)
@st.cache_resource
def get_collection():
    return load_collection()

collection = get_collection()

st.set_page_config(page_title="Bibliotheks-Chatbot", page_icon="📚")

st.title("📚 Bibliotheks-Chatbot")
st.write("Stelle hier deine Fragen zur Bibliothek (Ausleihe, Öffnungszeiten, Gebühren, ...).")

# Einfacher Chat-Verlauf
if "messages" not in st.session_state:
    st.session_state["messages"] = []

# Bisherige Nachrichten anzeigen
for role, content in st.session_state["messages"]:
    with st.chat_message(role):
        st.markdown(content)

# Eingabefeld
frage = st.chat_input("Deine Frage...")

if frage:
    # Nutzer-Nachricht anzeigen
    st.session_state["messages"].append(("user", frage))
    with st.chat_message("user"):
        st.markdown(frage)

    # Kontext aus RAG holen
    context, docs_metas = retrieve_context(collection, frage, k=4)

    # Antwort vom LLM holen
    with st.chat_message("assistant"):
        with st.spinner("Denke nach..."):
            antwort = call_llm(frage, context)
            st.markdown(antwort)
    st.session_state["messages"].append(("assistant", antwort))
