import os
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain.vectorstores import Chroma
import gradio as gr

# from langchain_community.embeddings import OpenAIEmbeddings
# from langchain.chat_models import ChatOpenAI
# from langchain.embeddings.openai import OpenAIEmbeddings


from dotenv import load_dotenv

load_dotenv()

# configuration
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
    embeddings_model = OpenAIEmbeddings(model="text-embedding-3-large")
    llm = ChatOpenAI(temperature=0.5, model="gpt-4o-mini")
    return llm


def connect_chroma_db() -> Chroma:
    """
    Function to connect to the chroma database.
    """
    # Check if the data path exists
    if not os.path.exists(DATA_PATH):
        raise FileNotFoundError(f"The specified data path does not exist: {DATA_PATH}")

    # Check if the chroma path exists
    if not os.path.exists(CHROMA_PATH):
        os.makedirs(CHROMA_PATH)

    vector_store = Chroma(
        collection_name="contract_disputes_collection",
        embedding_function=OpenAIEmbeddings(model="text-embedding-3-large"),
        persist_directory=CHROMA_PATH,
    )
    return vector_store


def create_vector_store_for_retriever() -> Chroma:
    """
    Function to create the vector store for the retriever.
    """
    vector_store = connect_chroma_db()
    num_results = 5
    retriever = vector_store.as_retriever(search_kwargs={"k": num_results})
    return retriever


def stream_response_from_retriever(message, history):
    """
    Function to stream the response from the LLM. This function is called by the Gradio app.
    """
    print(f"Input: {message}. History: {history}\n")

    # retrieve the relevant chunks based on the question asked
    retriever = create_vector_store_for_retriever()
    docs = retriever.get_relevant_documents(message)

    # add all the chunks to 'knowledge'
    knowledge = ""
    for document in docs:
        knowledge += document.page_content + "\n\n"

    # invoke the LLM call including prompt
    if message is not None:
        partial_message = ""
        # create the prompt for the LLM
        rag_prompt = f"""
        You are an assistant which answers questions based on knowledge which is provided to you.
        When responding, you don't use your internal knowledge.
        Only use the information in the "The knowledge" section.
        You don't inform the user about the provided knowledge.
        
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
    gr.Interface(
        fn=stream_response_from_retriever,
        inputs=gr.Textbox(
            placeholder="Send to the LLM...", container=False, autoscroll=True, scale=7
        ),
        outputs=gr.Textbox(label="Response"),
        title="Welcome to Justice for All Chatbot, a contract dispute resolution prototype. I'm your AI assistant, trained based on the U.S.Civilian Board of Contract Appeals dataset, providing guidance on complex contractual issues. Note: I'm a prototype, and my responses should not be considered legal advice. What's your contract dispute about? Share details, and I'll offer helpful insights.",
        description="A J4All prototypic chatbot that answers questions based on the provided knowledge.",
        theme="default",
        flagging_mode="never",  # Updated to use a valid flagging_mode value
        live=True,
    ).launch(share=True, debug=True, pwa=True)


if __name__ == "__main__":
    run_chatbot()
