import os

os.environ["HF_HUB_DOWNLOAD_TIMEOUT"] = "1000"
from transformers import pipeline

doc_qa = pipeline("question-answering", model="distilbert-base-cased-distilled-squad")
general_qa = pipeline("text2text-generation", model="google/flan-t5-large")


def ask_about_document(question, context):
    if not question or not context:
        return "Provide both question and document text."

    try:
        result = doc_qa(question=question, context=context)
        return result["answer"]
    except Exception as e:
        return f"Document QA failed: {str(e)}"


def ask_general_question(question):
    if not question.strip():
        return "Question cannot be empty."

    try:
        result = general_qa(question, max_length=256)
        return result[0]["generated_text"]
    except Exception as e:
        return f"General QA failed: {str(e)}"
