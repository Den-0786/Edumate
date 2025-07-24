from datetime import datetime
import streamlit as st
import torch
from transformers import pipeline
from logic.chat_history import ChatHistory
from logic.ui_components import (
    chat_message_ui, chat_options_modal,
    sidebar_chat_history_ui, user_input_ui
)
from logic.utils import extract_text_from_image, extract_text_from_pdf

# --- Init ---
ChatHistory.init_db()
st.set_page_config(page_title="EduMate", layout="wide", page_icon="📚")

# --- Load Models Once ---
def load_models():
    if "models_loaded" not in st.session_state:
        with st.spinner("Loading AI models..."):
            device = "cuda" if torch.cuda.is_available() else "cpu"
            st.session_state.qa_pipeline = pipeline(
                "question-answering",
                model="deepset/tinyroberta-squad2",
                device=device
            )
            st.session_state.summarizer = pipeline(
                "summarization",
                model="sshleifer/distilbart-cnn-12-6",
                device=device
            )
        st.session_state.models_loaded = True

# --- Prompt Logic ---
def get_context_prompt(level):
    return {
        "Basic": "Explain simply like to a 10-year-old: ",
        "SHS": "Explain for high school level: ",
        "Tertiary": "Provide detailed academic explanation: "
    }.get(level, "")

# --- Answer ---
def answer_question(question, context="", level="Basic"):
    prompt = get_context_prompt(level) + question
    result = st.session_state.qa_pipeline(
        question=prompt,
        context=context or prompt,
        max_length=512
    )
    return result["answer"]

# --- Summarize ---
def summarize_text(text, level="Basic"):
    prompt = f"Summarize this for {level} level: {text}"
    summary = st.session_state.summarizer(
        prompt,
        max_length=130 if level == "Basic" else 200,
        min_length=30
    )
    return summary[0]["summary_text"]


def cleanup_models():
    st.session_state.pop("qa_pipeline", None)
    st.session_state.pop("summarizer", None)
    torch.cuda.empty_cache()


# sourcery skip: use-named-expression
for key, val in {
    "history": ChatHistory.get_all_chats(),
    "active_chat_id": None,
    "education_level": "Basic",
    "search_query": "",
    "dark_mode": False,
    "paused": False,
    "smart_context": ""
}.items():
    st.session_state.setdefault(key, val)

load_models()


st.markdown("""
    <style>
    .stChatMessage { padding: 12px; }
    .stButton button {
        transition: all 0.2s ease-in-out;
        border-radius: 6px;
    }
    .stButton button:hover {
        background-color: #ffeb3b20;
        transform: scale(1.05);
    }
    @media only screen and (max-width: 768px) {
        section[data-testid="stSidebar"] { display: none; }
        .mobile-sidebar-toggle { display: block; margin-bottom: 10px; }
    }
    @media only screen and (min-width: 769px) {
        .mobile-sidebar-toggle { display: none; }
    }
    </style>
""", unsafe_allow_html=True)

# --- Dark Mode ---
if st.session_state.dark_mode:
    st.markdown("""
        <style>
        body { background-color: #121212; color: white; }
        .stTextInput input, .stSelectbox div { background-color: #222; color: white; }
        </style>
    """, unsafe_allow_html=True)

# --- Mobile Sidebar Toggle ---
if st.button("📂 Show Sidebar", key="toggle_sidebar", help="Only shows on mobile"):
    st.markdown("""
        <script>
        const sidebar = window.parent.document.querySelector('section[data-testid="stSidebar"]');
        sidebar.style.display = sidebar.style.display === "none" ? "block" : "none";
        </script>
    """, unsafe_allow_html=True)

# --- Sidebar ---
with st.sidebar:
    st.title("📚 EduMate")
    st.text_input("🔍 Search chats...", key="search_query")
    
    filtered_history = [
        c for c in st.session_state.history
        if st.session_state.search_query.lower() in c["title"].lower()
    ]
    sidebar_chat_history_ui(filtered_history)

    st.markdown("---")
    st.session_state.education_level = st.selectbox(
        "🎓 Education Level", ["Basic", "SHS", "Tertiary"]
    )
    st.toggle("🌙 Dark Mode", key="dark_mode")
    if st.button("🧹 Free Up Memory"):
        cleanup_models()
        st.success("Memory freed!")


st.header("🤖 EduMate Assistant")

# --- Upload & Summarize ---
uploaded_file = st.file_uploader("📎 Upload PDF/Image", type=["pdf", "jpg", "png", "jpeg"])
if uploaded_file:
    text = extract_text_from_pdf(uploaded_file) if uploaded_file.type == "application/pdf" else extract_text_from_image(uploaded_file)
    st.session_state.smart_context = text  

    if st.button("📝 Summarize"):
        with st.spinner("🔍 Analyzing document..."):
            summary = summarize_text(text, st.session_state.education_level)
            chat_id = ChatHistory.create_chat(
                title=f"Summary ({st.session_state.education_level})",
                question=f"Summarize this document ({st.session_state.education_level})",
                answer=summary
            )
            st.session_state.history = ChatHistory.get_all_chats()
            st.session_state.active_chat_id = chat_id
            st.toast("Summary generated!", icon="✅")
            st.rerun()

# --- Smart Suggestions ---
if st.session_state.smart_context and not st.session_state.get("active_chat_id"):
    st.subheader("🪄 Smart Suggestions from Upload")
    suggestions = [
        "What is the main idea of the text?",
        "Summarize in 3 key points",
        "What is the tone or mood?",
        "Who is the audience?"
    ]
    for s in suggestions:
        if st.button(s, key=f"suggestion-{s}"):
            with st.spinner("💡 Thinking..."):
                response = answer_question(
                    s,
                    context=st.session_state.smart_context,
                    level=st.session_state.education_level
                )
                chat_id = ChatHistory.create_chat(title=s, question=s, answer=response)
                st.session_state.history = ChatHistory.get_all_chats()
                st.session_state.active_chat_id = chat_id
                st.toast("Suggestion answered!", icon="💡")
                st.rerun()

# --- Chat Display ---
if st.session_state.active_chat_id:
    chat = ChatHistory.get_chat(st.session_state.active_chat_id)
    if chat:
        chat_message_ui({"id": chat["id"], "message": chat["question"], "timestamp": chat["created_at"]}, is_user=True)
        chat_message_ui({"id": chat["id"], "message": chat["answer"], "timestamp": chat["updated_at"]}, is_user=False)

# --- Chat Input ---
user_input = user_input_ui()
if user_input:
    with st.spinner("💭 Processing..."):
        response = answer_question(user_input, level=st.session_state.education_level)
        chat_id = ChatHistory.create_chat(
            title=f"{st.session_state.education_level} - {user_input[:25]}{'...' if len(user_input) > 25 else ''}",
            question=user_input,
            answer=response
        )
        st.session_state.history = ChatHistory.get_all_chats()
        st.session_state.active_chat_id = chat_id
        st.toast("Response saved!", icon="💾")
        st.rerun()
