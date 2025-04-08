import os
from dotenv import load_dotenv

from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain.vectorstores import Chroma
from langchain.prompts import PromptTemplate
from langchain.chains import RetrievalQA

import gradio as gr
from pipeline import ingest

# Load environment variables
load_dotenv()

# Constants
DATA_PATH = "data"
CHROMA_PATH = "chroma_db"

LEGAL_PROMPT_TEMPLATE = """
You are a legal assistant specialized in contract law and appellate matters. Use the context provided below, which may include excerpts from contracts, case law, or legal analysis, to answer the legal question. Be precise and grounded in the facts presented. Do not make up information. If the answer is not in the context, say:

"I cannot provide a legal answer based on the provided context."

---

Context:
{context}

---

Legal Question:
{question}

Legal Answer:
"""

# Reusable prompt object
prompt = PromptTemplate(
    input_variables=["context", "question"],
    template=LEGAL_PROMPT_TEMPLATE,
)


def create_llm() -> ChatOpenAI:
    """
    Initialize the OpenAI model (gpt-4o-mini).
    """
    openai_api_key = ingest.get_openai_api_key()
    if not openai_api_key:
        raise ValueError("OPENAI_API_KEY is not set.")
    return ChatOpenAI(temperature=0.0, model="gpt-4o-mini", api_key=openai_api_key)


def create_retriever(k: int = 5):
    """
    Create the retriever from Chroma vector store.
    """
    vector_store = ingest.create_chroma_db()
    return vector_store.as_retriever(search_kwargs={"k": k})


def stream_response_from_retriever(message, history):
    """
    Stream a response using LLM and retrieved legal context.
    """
    retriever = create_retriever()
    docs = retriever.get_relevant_documents(message)
    knowledge = "\n\n".join(doc.page_content for doc in docs)

    if not message:
        return

    llm = create_llm()
    partial_message = ""

    # Create full RAG-style input prompt
    rag_prompt = f"""
    You are a legal assistant specialized in contract law and appellate matters.
    Use the context provided below, which may include excerpts from contracts, case law, or legal analysis,
    to answer the legal question. Be precise and grounded in the facts presented.

    Question: {message}
    Context: {knowledge}
    """

    # Stream output token by token
    for response in llm.stream(rag_prompt):
        partial_message += response.content
        yield partial_message


def run_chatbot():
    """
    Run the LumiLens chatbot with Gradio UI.
    """
    gr.ChatInterface(
        fn=stream_response_from_retriever,
        textbox=gr.Textbox(
            placeholder="Send to the LLM...",
            container=False,
            autoscroll=True,
            scale=7,
            show_label=False,
        ),
        title="Hi, I'm LumiLens! I'm an AI-powered tool designed to assist with Justice for All inquiries. I'm a prototype, and my owner is working to bring me to life!",
        theme="default",
    ).launch(share=True, debug=True, pwa=True)


if __name__ == "__main__":
    run_chatbot()
    