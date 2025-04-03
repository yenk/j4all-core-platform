import os

from uuid import uuid4
from langchain_community.vectorstores import Chroma
from langchain_community.document_loaders import PyPDFDirectoryLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import OpenAIEmbeddings
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
DATA_PATH = r"data"
CHROMA_PATH = r"chroma_db"


def create_chroma_db() -> Chroma:
    """
    Function to create a Chroma database from PDF files in the specified directory.

    https://python.langchain.com/docs/modules/indexes/vectorstores/integrations/chroma
    """
    # Check if the data path exists
    if not os.path.exists(DATA_PATH):
        raise FileNotFoundError(f"The specified data path does not exist: {DATA_PATH}")

    # Check if the chroma path exists
    if not os.path.exists(CHROMA_PATH):
        os.makedirs(CHROMA_PATH)

    # Check if the OpenAI API key is set
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        raise ValueError("OPENAI_API_KEY is not set in the environment variables.")

    # Create the Chroma database for vector store
    vector_store = Chroma(
        collection_name="contract_disputes_collection",
        embedding_function=OpenAIEmbeddings(model="text-embedding-3-large"),
        persist_directory=CHROMA_PATH,
    )
    return vector_store


def load_and_split_documents() -> list:
    """
    Function to load and split pdf documents from the specified directory.
    https://python.langchain.com/docs/tutorials/retrievers/
    """
    loader = PyPDFDirectoryLoader(DATA_PATH)
    raw_documents = loader.load()
    # Check if the raw documents are empty
    if not raw_documents:
        raise ValueError("No documents found in the specified directory.")
    # Check if the raw documents are a list
    if not isinstance(raw_documents, list):
        raise TypeError("The loaded documents are not in the expected format.")

    # Split the documents
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    chunks = splitter.split_documents(raw_documents)
    return chunks if chunks else []


def create_chunks(text_splitter, raw_documents) -> list:
    """
    Function to create chunks from the loaded documents.
    """
    # Check if the text splitter is initialized
    if text_splitter is None:
        raise ValueError("Text splitter is not initialized.")
    # Check if the raw documents are loaded
    if raw_documents is None:
        raise ValueError("Raw documents are not loaded.")
    # Create the chunks
    return text_splitter.split_documents(raw_documents)


def add_chunks_to_vector_store(vector_store, chunks, uuids):
    """
    Function to add chunks to the vector store.
    """
    # Check if the vector store is initialized
    if vector_store is None:
        raise ValueError("Vector store is not initialized.")
    # Check if the chunks are loaded
    if chunks is None:
        raise ValueError("Chunks are not loaded.")
    # Check if the UUIDs are loaded
    if uuids is None:
        raise ValueError("UUIDs are not loaded.")
    vector_store.add_documents(documents=chunks, ids=uuids)


# Main function to run the script
if __name__ == "__main__":
    # Load and split documents
    raw_documents = load_and_split_documents()
    if not raw_documents:
        raise ValueError("No documents were loaded.")

    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    document_chunks = create_chunks(
        text_splitter, raw_documents
    )  # Renamed from 'chunks'
    if not document_chunks:
        raise ValueError("Failed to create chunks from the documents.")

    # Create unique IDs for the chunks
    uuids = [str(uuid4()) for _ in range(len(document_chunks))]

    # Initialize the vector store
    try:
        vector_store = create_chroma_db()
    except Exception as e:
        raise RuntimeError(f"Failed to initialize the vector store: {e}")

    # Add chunks to the vector store
    add_chunks_to_vector_store(vector_store, document_chunks, uuids)

    # Print the results
    print(f"Loaded {len(raw_documents)} documents.")
    print(f"Created {len(document_chunks)} chunks.")
    print(f"Created {len(uuids)} unique IDs.")
    print(f"Vector store created: {vector_store}")
