import os
from dotenv import load_dotenv
import torch
from transformers import BertTokenizer, BertForSequenceClassification
from langchain.vectorstores import Chroma
import gradio as gr
from pipeline import ingest

# Load environment variables from .env file
load_dotenv()

# Global configuration
DATA_PATH = r"data"
CHROMA_PATH = r"chroma_db"

# Define a function to check if it's running in Hugging Face Spaces
def is_running_in_spaces() -> bool:
    """
    Check if the application is running in Hugging Face Spaces.
    """
    return "SPACE_ID" in os.environ

# Load LegalBERT model
def load_legalbert_model():
    """
    Function to load LegalBERT (BERT model fine-tuned for legal documents).
    """
    model_name = "nlpaueb/legal-bert-base-uncased"  # Updated model name
    tokenizer = BertTokenizer.from_pretrained(model_name)
    model = BertForSequenceClassification.from_pretrained(model_name)
    return model, tokenizer

# Create a vector store using Chroma
def connect_chroma_db() -> Chroma:
    """
    Function to connect to the Chroma database.
    """
    vector_store = ingest.create_chroma_db()
    return vector_store

# Create the vector store for retriever
def create_vector_store_for_retriever() -> Chroma:
    """
    Function to create the vector store for the retriever.
    """
    num_results = 5
    retriever = connect_chroma_db().as_retriever(search_kwargs={"k": num_results})
    return retriever


def process_with_legalbert(message, history, retriever):
    """
    Function to process a response using LegalBERT model.
    """
    # Retrieve relevant documents using the retriever
    docs = retriever.get_relevant_documents(message)  # Correct method to retrieve documents
    
    # Combine the documents into a knowledge base
    knowledge = ""
    for doc in docs:
        knowledge += doc.page_content + "\n\n"

    # Prepare input for LegalBERT
    input_text = f"Question: {message}\nContext: {knowledge}"

    # Tokenize the input and make prediction
    tokenizer = BertTokenizer.from_pretrained("nlpaueb/legal-bert-base-uncased")  # Updated model name
    model = BertForSequenceClassification.from_pretrained("nlpaueb/legal-bert-base-uncased")  # Updated model name

    inputs = tokenizer(input_text, return_tensors="pt", truncation=True, padding=True)
    with torch.no_grad():
        outputs = model(**inputs)
    prediction = outputs.logits.argmax(dim=-1).item()  # Prediction could be used for classification tasks

    return f"Prediction (Legal Result): {prediction}"

# Function to stream the response from the retriever
def stream_response_from_retriever(message, history):
    """
    Function to stream the response from the LegalBERT retriever.
    """
    # Retrieve the relevant chunks based on the question
    retriever = create_vector_store_for_retriever()
    
    # Process the answer using LegalBERT
    response = process_with_legalbert(message, history, retriever)  # Pass the history
    # Add the response to the history
    history.append(response)

    # Stream the response
    yield response

def run_chatbot():
    """
    Function to run the chatbot and deploy to hugging face "lumi" space.
    """
    # deploy to gradio app
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
    ).launch(share=True, debug=True, pwa=True)

if __name__ == "__main__":
    run_chatbot()
