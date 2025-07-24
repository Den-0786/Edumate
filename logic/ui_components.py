import uuid
from datetime import datetime
import streamlit as st

def chat_message_ui(chat, is_user=True):
    with st.chat_message("user" if is_user else "assistant"):
        st.markdown(
            f"{'👤' if is_user else '🤖'} {chat['message']}", unsafe_allow_html=True
        )
        st.markdown(f"<small>{chat['timestamp']}</small>", unsafe_allow_html=True)

        cols = st.columns([0.1, 0.1, 0.1])
        with cols[0]:
            if st.button("✏️", key=f"edit-{chat['id']}"):
                st.session_state["edit_mode"] = chat["id"]
                st.toast("", icon="✏️")
        with cols[1]:
            if st.button("📋", key=f"copy-{chat['id']}"):
                st.code(chat["message"], language="markdown")
                st.toast("", icon="📋")
        with cols[2]:
            if st.button("📌", key=f"pin-{chat['id']}"):
                st.session_state["pin_chat"] = chat["id"]
                st.toast("", icon="📌")


def sidebar_chat_history_ui(chat_list):  # sourcery skip: use-named-expression
    st.sidebar.subheader("📚 Chat History")

    # 🔍 Search bar
    search_query = st.sidebar.text_input("Search chats...", key="search_chats")
    filtered_chats = [
        c for c in chat_list if search_query.lower() in c["title"].lower()
    ] if search_query else chat_list

    pinned_chats = [c for c in filtered_chats if c.get("pinned")]
    if pinned_chats:
        st.sidebar.subheader("📌 Pinned")
        for chat in pinned_chats:
            render_chat_item(chat)

    recent_chats = [c for c in filtered_chats if not c.get("pinned")]
    if recent_chats:
        st.sidebar.subheader("⏱️ Recent")
        for chat in recent_chats:
            render_chat_item(chat)

    st.sidebar.markdown("---")

    # 🌙 Dark mode toggle
    dark_mode = st.sidebar.toggle("🌙 Dark Mode", key="dark_mode")
    if dark_mode:
        st.markdown(
            """
            <style>
                body { background-color: #0e1117; color: #ffffff; }
                .stButton>button, .stTextInput>div>input {
                    background-color: #333333; color: white;
                }
                .stChatMessage { background-color: #1e1e1e; }
            </style>
            """, unsafe_allow_html=True
        )


def render_chat_item(chat):
    cols = st.sidebar.columns([0.7, 0.15, 0.15])
    with cols[0]:
        if st.button(f"💬 {chat['title']}", key=f"load-{chat['id']}"):
            st.session_state["active_chat_id"] = chat["id"]
            st.toast("", icon="📂")
    with cols[1]:
        if st.button("📌", key=f"sidebar-pin-{chat['id']}"):
            st.session_state["pin_chat"] = chat["id"]
    with cols[2]:
        if st.button("⋮", key=f"menu-{chat['id']}"):
            st.session_state["show_menu_for"] = chat["id"]


def chat_options_modal(chat_id):
    with st.modal("Chat Options", key=f"modal-{chat_id}"):
        st.write("What would you like to do?")
        if st.button("✏️ Edit Chat Title"):
            st.session_state["edit_title_for"] = chat_id
            st.toast("", icon="✏️")
        if st.button("🗑️ Delete Chat"):
            st.session_state["delete_chat"] = chat_id
            st.toast("", icon="🗑️")
        if st.button("📌 Pin/Unpin"):
            st.session_state["pin_chat"] = chat_id
            st.toast("", icon="📌")
        if st.button("✕ Close"):
            st.session_state.pop("show_menu_for", None)


def user_input_ui(pause_key="pause"):
    col1, col2, col3 = st.columns([0.7, 0.15, 0.15])
    with col1:
        user_input = st.text_input(
            "Ask or type...", key="user_input", label_visibility="collapsed"
        )
    with col2:
        if st.button("📎", key="attach"):
            st.session_state["attach_mode"] = True
    with col3:
        if st.button("⏸️", key=pause_key):
            st.session_state["paused"] = not st.session_state.get("paused", False)
            st.toast("", icon="⏸️")
    return user_input
