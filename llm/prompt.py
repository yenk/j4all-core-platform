import os
import sys

from dotenv import load_dotenv

from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain.vectorstores import Chroma

import gradio as gr

from pipeline import ingest

# Add the src directory to the system path
# This allows us to import modules from the src directory
# without needing to specify the full path
# src_path = os.path.abspath('src')
# sys.path.insert(0, src_path)

load_dotenv()

# global configuration
DATA_PATH = r"data"
CHROMA_PATH = r"chroma_db"


def create_llm() -> ChatOpenAI:
    """
    Function to initiate the model.
    """
    # Check if the OpenAI API key is set
    openai_api_key = os.getenv("OPENAI_API_KEY")

    if not openai_api_key:
        raise ValueError("OPENAI_API_KEY is not set in the environment variables.")

    # Initialize and return the model
    model = ChatOpenAI(temperature=0.5, model="gpt-4o-mini")
    return model


def connect_chroma_db() -> Chroma:
    """
    Function to connect to the chroma database.
    """
    vector_store = ingest.create_chroma_db()
    # vector_store = Chroma(
    #     collection_name="contract_disputes_collection",
    #     embedding_function=OpenAIEmbeddings(model="text-embedding-3-large"),
    #     persist_directory=CHROMA_PATH,
    # )
    return vector_store


def create_vector_store_for_retriever() -> Chroma:
    """
    Function to create the vector store for the retriever.
    """
    num_results = 5
    retriever = connect_chroma_db().as_retriever(search_kwargs={"k": num_results})
    return retriever


def stream_response_from_retriever(message, history):
    """
    Function to stream the response from the LLM RAG. This function is called by the Gradio app.
    """
    # print(f"Input: {message}. History: {history}\n")

    # retrieve the relevant chunks based on the question asked
    retriever = create_vector_store_for_retriever()
    docs = retriever.get_relevant_documents(message)

    # add all the chunks to 'knowledge'
    knowledge = ""
    for doc in docs:
        knowledge += doc.page_content + "\n\n"

    # invoke the LLM call including prompt
    if message is not None:
        partial_message = ""
        # create the prompt for the LLM
        rag_prompt = f"""
        You are an assistant that provides answers based solely on the information provided to you, 
        without relying on internal knowledge or external sources.
        
        The question: {message}
        Conversation history: {history}
        The knowledge: {knowledge}
        """
        print(rag_prompt)

        # stream the response to the Gradio App
        llm = create_llm()
        for response in llm.stream(rag_prompt):
            partial_message += response.content
            yield partial_message


def run_chatbot():
    """
    Function to run the chatbot.
    """
    # create the Gradio app
    gr.ChatInterface(fn=stream_response_from_retriever, textbox=gr.Textbox(placeholder="Send to the LLM...",
    container=False,
    autoscroll=True,
    scale=7,
    label="Ask me anything about contract disputes"),
    title="Welcome to Justice for All - Your AI Assistant, a contract dispute resolution prototype. Note: My responses should not be considered legal advice.",
    ).launch(share=True, debug=True, pwa=True)


if __name__ == "__main__":
    run_chatbot()
