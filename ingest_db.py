import os

from uuid import uuid4
from langchain_community.vectorstores import Chroma
from langchain_community.document_loaders import PyPDFDirectoryLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings.openai import OpenAIEmbeddings
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
DATA_PATH = r"data"
CHROMA_PATH = r"chroma_db"

# Initiate the embeddings model
openai_api_key = os.getenv("openai_api_key")
if not openai_api_key:
    raise ValueError("OPENAI_API_KEY is not set in the environment variables.")
embeddings_model = OpenAIEmbeddings(openai_api_key=openai_api_key, model="text-embedding-3-large")

# Initiate the vector store
vector_store = Chroma(
    collection_name="example_collection",
    embedding_function=embeddings_model,
    persist_directory=CHROMA_PATH,
)

# Load the PDF documents
# https://python.langchain.com/docs/tutorials/retrievers/
loader = PyPDFDirectoryLoader(DATA_PATH)
raw_documents = loader.load()

# Split the documents
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200,
    length_function=len,
)

# Create the chunks
chunks = text_splitter.split_documents(raw_documents)

# Create unique IDs
uuids = [str(uuid4()) for _ in range(len(chunks))]

# Add chunks to the vector store
vector_store.add_documents(documents=chunks, ids=uuids)

print(f"Generated UUIDs: {uuids}")
print(f"Number of chunks: {len(chunks)}")