import os
from uuid import uuid4
import hashlib
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


def is_running_in_spaces() -> bool:
    return "SPACE_ID" in os.environ


# Only import and load dotenv locally
if not is_running_in_spaces():
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ModuleNotFoundError:
        print("Warning: python-dotenv not installed. Skipping local .env loading.")


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
    loader = PyPDFDirectoryLoader(DATA_PATH, recursive=True)
    raw_documents = loader.load()

    if not raw_documents:
        raise ValueError("No documents were found in the specified data path.")

    # Split the documents into chunks
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=300, chunk_overlap=100)
    chunks = text_splitter.split_documents(raw_documents)

    if not chunks:
        raise ValueError("Failed to split documents into chunks.")

    return chunks


def remove_duplicates(chunks: list) -> list:
    """
    Removes duplicate chunks based on content hash.
    """
    seen_hashes = set()
    unique_chunks = []

    for chunk in chunks:
        # Assuming chunk is a Document object and has a 'page_content' attribute
        chunk_content = chunk.page_content  # Access the 'page_content' attribute
        chunk_hash = hashlib.sha256(chunk_content.encode('utf-8')).hexdigest()

        if chunk_hash not in seen_hashes:
            seen_hashes.add(chunk_hash)
            unique_chunks.append(chunk)

    print(f"Removed {len(chunks) - len(unique_chunks)} duplicate chunks.")
    return unique_chunks


def add_chunks_to_vector_store(store: Chroma, chunks: list):
    """
    Function to add chunks to the vector store, removing duplicates before adding.
    """
    # Check if the vector store is initialized
    if store is None:
        raise ValueError("Vector store is not initialized.")

    # Check if the chunks are loaded
    if not chunks:
        raise ValueError("Chunks are not loaded.")

    # Remove duplicates
    unique_chunks = remove_duplicates(chunks)

    # Generate unique IDs for each chunk
    uuids = [str(uuid4()) for _ in range(len(unique_chunks))]

    # Add unique chunks to the vector store
    store.add_documents(documents=unique_chunks, ids=uuids)
    print(f"Added {len(unique_chunks)} unique chunks to the vector store.")


# Main function to run the script
if __name__ == "__main__":
    try:
        # Load and split documents
        document_chunks = load_and_split_documents()

        # Initialize the vector store
        vector_store = create_chroma_db()

        # Add chunks to the vector store
        add_chunks_to_vector_store(store=vector_store, chunks=document_chunks)

        # Print the results
        print(f"Successfully processed and added {len(document_chunks)} chunks to the vector store.")

    except Exception as e:
        print(f"An error occurred: {e}")
