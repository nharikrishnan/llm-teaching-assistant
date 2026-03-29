"""Streamlit app: upload PDF, learn by topic, Q&A after each topic."""

from __future__ import annotations

import tempfile
from pathlib import Path

import streamlit as st

from chunker import Topic, extract_topics
from doc_loader import load_pdf_as_text
from teacher import QuizItem, answer_question, generate_qa, teach_topic


def _normalize(s: str) -> str:
    return (s or "").strip().lower()


def _init_state():
    if "topics" not in st.session_state:
        st.session_state.topics = []
    if "current_topic_index" not in st.session_state:
        st.session_state.current_topic_index = 0
    if "topic_teachings" not in st.session_state:
        st.session_state.topic_teachings = {}
    if "topic_qa" not in st.session_state:
        st.session_state.topic_qa = {}
    if "user_answers" not in st.session_state:
        st.session_state.user_answers = {}
    if "doc_processed" not in st.session_state:
        st.session_state.doc_processed = False
    if "upload_key" not in st.session_state:
        st.session_state.upload_key = 0
    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = {}  # topic_idx -> list of {"role": "user"|"assistant", "content": "..."}


def main():
    st.set_page_config(page_title="Teaching Assistant", layout="wide")
    _init_state()

    st.title("LLM-Powered Teaching Assistant")
    st.caption("Upload a PDF to learn topic by topic with Q&A after each section.")

    # Check LLM config once
    try:
        from llm_config import get_llm
        get_llm()
    except ValueError as e:
        st.error(str(e))
        st.info("Copy `.env.example` to `.env` and set your API key for your chosen provider (OpenAI or Anthropic).")
        return

    # Upload and process
    uploaded = st.file_uploader("Upload a PDF", type=["pdf"], key=f"uploader_{st.session_state.upload_key}")
    if uploaded is not None and not st.session_state.doc_processed:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(uploaded.read())
            tmp_path = tmp.name
        try:
            with st.spinner("Loading and analyzing document…"):
                full_text = load_pdf_as_text(tmp_path)
                st.session_state.topics = extract_topics(full_text)
                st.session_state.doc_processed = True
                st.session_state.current_topic_index = 0
            st.success(f"Document split into {len(st.session_state.topics)} topics.")
        except Exception as e:
            st.error(f"Error processing PDF: {e}")
            return
        finally:
            Path(tmp_path).unlink(missing_ok=True)

    topics: list[Topic] = st.session_state.topics
    if not topics:
        st.info("Upload a PDF to get started.")
        return

    # Sidebar: outline and topic selection
    with st.sidebar:
        st.subheader("Outline")
        for i, t in enumerate(topics):
            label = f"{i + 1}. {t.title}"
            if st.button(label, key=f"topic_{i}", use_container_width=True):
                st.session_state.current_topic_index = i
                st.rerun()
        st.divider()
        if st.button("Start over (clear document)"):
            st.session_state.doc_processed = False
            st.session_state.topics = []
            st.session_state.topic_teachings.clear()
            st.session_state.topic_qa.clear()
            st.session_state.user_answers.clear()
            st.session_state.chat_messages.clear()
            st.session_state.upload_key = (st.session_state.get("upload_key", 0) + 1) % 10000
            st.rerun()

    idx = st.session_state.current_topic_index
    current = topics[idx]

    # Main: current topic
    st.subheader(current.title)

    # Teaching block (cached per topic)
    if idx not in st.session_state.topic_teachings:
        if st.button("Explain this topic", key="teach_btn"):
            with st.spinner("Generating explanation…"):
                teaching = teach_topic(current.title, current.content)
                st.session_state.topic_teachings[idx] = teaching
                st.rerun()
        else:
            st.write("Click **Explain this topic** to get a structured explanation.")
    else:
        st.markdown(st.session_state.topic_teachings[idx])
        if st.button("Regenerate explanation", key="reteach_btn"):
            with st.spinner("Regenerating…"):
                st.session_state.topic_teachings[idx] = teach_topic(current.title, current.content)
                st.rerun()

    st.divider()
    st.subheader("Quiz")

    # Q&A generation and display
    if idx not in st.session_state.topic_qa:
        if st.button("Generate Q&A for this topic", key="qa_btn"):
            with st.spinner("Generating questions…"):
                qa_list = generate_qa(current.title, current.content)
                st.session_state.topic_qa[idx] = qa_list
                st.session_state.user_answers[idx] = [""] * len(qa_list)
                st.rerun()
        else:
            st.write("Click **Generate Q&A for this topic** to create quiz questions.")
    else:
        qa_list: list[QuizItem] = st.session_state.topic_qa[idx]
        if idx not in st.session_state.user_answers:
            st.session_state.user_answers[idx] = [""] * len(qa_list)
        user_answers = st.session_state.user_answers[idx]

        for i, item in enumerate(qa_list):
            st.markdown(f"**Q{i + 1}. {item.question}**")
            user_answers[i] = st.text_input(
                "Your answer",
                value=user_answers[i],
                key=f"ans_{idx}_{i}",
                label_visibility="collapsed",
            )
            st.session_state.user_answers[idx] = user_answers

        if st.button("Check answers", key="check_btn"):
            for i, item in enumerate(qa_list):
                u = _normalize(user_answers[i] if i < len(user_answers) else "")
                a = _normalize(item.answer)
                # Simple match: exact or answer contained in user / user contained in answer
                ok = u == a or (a in u) or (u in a and u)
                icon = "✅" if ok else "❌"
                st.markdown(f"{icon} **Q{i + 1}** — Correct: **{item.answer}**")
        st.divider()
        if st.button("Regenerate Q&A", key="regen_qa_btn"):
            with st.spinner("Regenerating…"):
                st.session_state.topic_qa[idx] = generate_qa(current.title, current.content)
                qa_list = st.session_state.topic_qa[idx]
                st.session_state.user_answers[idx] = [""] * len(qa_list)
                st.rerun()

    st.divider()
    st.subheader("Ask the teacher")
    st.caption("Ask questions or clear doubts about this topic. The teacher answers based on the document.")

    # Chat with teacher (per-topic)
    if idx not in st.session_state.chat_messages:
        st.session_state.chat_messages[idx] = []

    chat_list = st.session_state.chat_messages[idx]
    for msg in chat_list:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if prompt := st.chat_input("Ask a question or express a doubt…"):
        chat_list.append({"role": "user", "content": prompt})
        with st.chat_message("assistant"):
            with st.spinner("Thinking…"):
                history = chat_list[:-1]
                reply = answer_question(
                    current.title,
                    current.content,
                    user_question=prompt,
                    conversation_history=history if history else None,
                )
            st.markdown(reply)
        chat_list.append({"role": "assistant", "content": reply})
        st.session_state.chat_messages[idx] = chat_list
        st.rerun()

    if chat_list and st.button("Clear chat for this topic", key="clear_chat_btn"):
        st.session_state.chat_messages[idx] = []
        st.rerun()

    # Navigation
    col1, col2, col3 = st.columns([1, 2, 1])
    with col1:
        if st.button("← Previous topic") and idx > 0:
            st.session_state.current_topic_index = idx - 1
            st.rerun()
    with col3:
        if st.button("Next topic →") and idx < len(topics) - 1:
            st.session_state.current_topic_index = idx + 1
            st.rerun()


if __name__ == "__main__":
    main()
