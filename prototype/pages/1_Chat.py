"""
💬 Chat — ask the tutor (Streamlit page)
=======================================
Conversational, RAG-grounded tutor with AUTOMATIC topic detection. The student
just asks; the system finds the relevant Class 10 content (notes + uploaded PDFs)
and answers. No subject/chapter/concept picking.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st

import db as store
from chat_engine import TutorChat
from llm_provider import using_real_llm


@st.cache_resource
def get_chat() -> TutorChat:
    store.init_db()
    return TutorChat()


chat = get_chat()

st.set_page_config(page_title="EduSakhi Chat", page_icon="💬", layout="centered")
st.title("💬 Ask the Tutor")
st.caption("Ask anything in your own words — the tutor finds the right Class 10 "
           "topic automatically and answers from the notes + your uploaded PDFs.")

with st.sidebar:
    st.header("Chat settings")
    language = st.selectbox("Language", ["english", "telugu", "both"],
                            format_func=lambda k: {"english": "English",
                                                   "telugu": "తెలుగు",
                                                   "both": "English + Telugu"}[k])
    st.markdown(f"**LLM:** {'🟢 HuggingFace' if using_real_llm() else '⚪ offline'}")
    if st.button("🧹 Clear chat", use_container_width=True):
        st.session_state.chat_msgs = []
        st.rerun()

if "chat_msgs" not in st.session_state:
    st.session_state.chat_msgs = []

for role, content in st.session_state.chat_msgs:
    with st.chat_message(role):
        st.markdown(content)

prompt = st.chat_input("Ask a doubt… e.g. 'why does a fuse melt?'")
if prompt:
    st.session_state.chat_msgs.append(("user", prompt))
    with st.chat_message("user"):
        st.markdown(prompt)
    with st.chat_message("assistant"):
        with st.spinner("Finding the topic and answering…"):
            answer, topic, sources = chat.reply(
                prompt, language, history=st.session_state.chat_msgs[:-1],
            )
        st.caption(f"📌 Detected topic: **{topic}**")
        st.markdown(answer)
        if sources:
            with st.expander("🔎 Sources used"):
                for s in sources:
                    tag = "📄 PDF" if s.get("kind") == "pdf" else "📝 note"
                    st.caption(f"{tag} {s['concept']} (score {s['score']}) — {s['text'][:160]}")
    st.session_state.chat_msgs.append(("assistant", answer))
