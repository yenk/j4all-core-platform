import os

from uuid import uuid4

from langchain_community.vectorstores import Chroma
from langchain_community.document_loaders import PyPDFDirectoryLoader
from langchain_community.embeddings import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Global configuration
DATA_PATH = os.path.join(os.path.dirname(__file__), "../data")
CHROMA_PATH = os.path.join(os.path.dirname(__file__), "../chroma_db")


def get_openai_api_key() -> str:
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        raise ValueError("OPENAI_API_KEY is not set in the environment variables.")
    return openai_api_key


def create_chroma_db() -> Chroma:
    """
    Creates and returns a Chroma vector store using OpenAI embeddings.
    """
    if not os.path.exists(DATA_PATH):
        raise FileNotFoundError(f"The specified data path does not exist: {DATA_PATH}")
    if not os.path.exists(CHROMA_PATH):
        os.makedirs(CHROMA_PATH)

    try:
        api_key = get_openai_api_key()
        embedding_function = OpenAIEmbeddings(
            model="text-embedding-3-large", api_key=api_key
        )

        vector_store = Chroma(
            collection_name="contract_disputes_collection",
            embedding_function=embedding_function,
            persist_directory=CHROMA_PATH,
        )
        return vector_store

    except Exception as e:
        raise RuntimeError(f"Failed to initialize the vector store: {e}") from e


def load_and_split_documents() -> list:
    """
    Function to load and split PDF documents from the specified directory.
    """
    # Load documents from the data path
    loader = PyPDFDirectoryLoader(DATA_PATH)
    raw_documents = loader.load()

    if not raw_documents:
        raise ValueError("No documents were found in the specified data path.")

    # Split the documents into chunks
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=300, chunk_overlap=100)
    chunks = text_splitter.split_documents(raw_documents)

    if not chunks:
        raise ValueError("Failed to split documents into chunks.")

    return chunks


def add_chunks_to_vector_store(store: Chroma, chunks: list):
    """
    Function to add chunks to the vector store.
    """
    # Check if the vector store is initialized
    if vector_store is None:
        raise ValueError("Vector store is not initialized.")

    # Check if the chunks are loaded
    if not chunks:
        raise ValueError("Chunks are not loaded.")

    # Generate unique IDs for each chunk
    uuids = [str(uuid4()) for _ in range(len(chunks))]

    # Add chunks to the vector store
    vector_store.add_documents(documents=chunks, ids=uuids)
    print(f"Added {len(chunks)} chunks to the vector store.")


# Main function to run the script
if __name__ == "__main__":
    try:
        # Load and split documents
        document_chunks = load_and_split_documents()
        # # Initialize the vector store
        vector_store = create_chroma_db()
        # # Add chunks to the vector store
        add_chunks_to_vector_store(store=vector_store, chunks=document_chunks)
        # # Print the results
        print(
            f"Successfully processed and added {len(document_chunks)} chunks to the vector store."
        )

    except Exception as e:
        print(f"An error occurred: {e}")
