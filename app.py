
from datetime import datetime

import streamlit as st

from logic.chat_history import ChatHistory
from logic.qna import answer_question
from logic.summarizer import summarize_text
from logic.ui_components import (chat_message_ui, chat_options_modal,
                                sidebar_chat_history_ui, user_input_ui)
from logic.utils import extract_text_from_image, extract_text_from_pdf

# Initialize database and session state
ChatHistory.init_db()

st.set_page_config(page_title="EduMate", layout="wide", page_icon="📚")

st.markdown(
    """
    <style>
        .stChatMessage {
            padding: 12px;
        }
        .stButton button {
            min-width: 32px;
        }
    </style>
""",
    unsafe_allow_html=True,
)

# Session state initialization
if "history" not in st.session_state:
    st.session_state.history = ChatHistory.get_all_chats()
if "active_chat_id" not in st.session_state:
    st.session_state.active_chat_id = None
if "paused" not in st.session_state:
    st.session_state.paused = False
if "edit_mode" not in st.session_state:
    st.session_state.edit_mode = None
if "edit_title_for" not in st.session_state:
    st.session_state.edit_title_for = None
if "show_menu_for" not in st.session_state:
    st.session_state.show_menu_for = None

# Sidebar
with st.sidebar:
    st.title("📚 EduMate")
    sidebar_chat_history_ui(ChatHistory.get_all_chats())

# Handle chat menu actions
if st.session_state.get("show_menu_for"):
    chat_options_modal(st.session_state["show_menu_for"])
    if st.session_state.get("pin_chat"):
        ChatHistory.toggle_pin(st.session_state.pin_chat)
        st.toast(
            (
                "Pinned!"
                if ChatHistory.get_chat(st.session_state.pin_chat)["pinned"]
                else "Unpinned!"
            ),
            icon="📌",
        )
        st.session_state.pin_chat = None
        st.rerun()
    if st.session_state.get("delete_chat"):
        ChatHistory.delete_chat(st.session_state.delete_chat)
        st.toast("Chat deleted", icon="🗑️")
        if st.session_state.active_chat_id == st.session_state.delete_chat:
            st.session_state.active_chat_id = None
        st.session_state.delete_chat = None
        st.rerun()
    if st.session_state.get("edit_title_for"):
        new_title = st.text_input("New title:", key="new_title")
        if st.button("💾 Save"):
            ChatHistory.update_chat(st.session_state.edit_title_for, title=new_title)
            st.toast("Title updated", icon="✏️")
            st.session_state.edit_title_for = None
            st.rerun()

# Main UI
st.header("🤖 EduMate Assistant")

# File upload and processing
uploaded_file = st.file_uploader(
    "📎 Upload PDF/Image", type=["pdf", "jpg", "png", "jpeg"]
)
if uploaded_file:
    text = (
        extract_text_from_pdf(uploaded_file)
        if uploaded_file.type == "application/pdf"
        else extract_text_from_image(uploaded_file)
    )
    if st.button("📝 Summarize"):
        with st.spinner("🔍 Analyzing document..."):
            summary = summarize_text(text)
            chat_id = ChatHistory.create_chat(
                title="Document Summary",
                question="Summarize this document",
                answer=summary,
                pinned=False,
            )
            st.session_state.history = ChatHistory.get_all_chats()
            st.session_state.active_chat_id = chat_id
            st.toast("Summary created!", icon="✅")
            st.rerun()

# Display active chat
if st.session_state.active_chat_id:
    active_chat = ChatHistory.get_chat(st.session_state.active_chat_id)
    if active_chat:
        chat_message_ui(
            {
                "message": active_chat["question"],
                "timestamp": active_chat["created_at"],
                "id": active_chat["id"],
            },
            is_user=True,
        )
        chat_message_ui(
            {
                "message": active_chat["answer"],
                "timestamp": active_chat["updated_at"],
                "id": active_chat["id"],
            },
            is_user=False,
        )

# Chat input
if st.session_state.paused:
    if st.button("▶️ Resume Chat"):
        st.session_state.paused = False
        st.toast("Chat resumed", icon="💬")
        st.rerun()
else:
    user_input = user_input_ui()
    if user_input:
        with st.spinner("💭 Processing..."):
            response = answer_question(user_input)
            chat_id = ChatHistory.create_chat(
                title=user_input[:25] + ("..." if len(user_input) > 25 else ""),
                question=user_input,
                answer=response,
                pinned=False,
            )
            st.session_state.history = ChatHistory.get_all_chats()
            st.session_state.active_chat_id = chat_id
            st.toast("Response saved", icon="💾")
            st.rerun()
