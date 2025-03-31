# Justice for All Prototyping

Building a prototype to democratize Justice for All - j4all.org.

## Installation

Use `pyproject.toml` file to install dependencies. You may have to install some modules separately because Poetry may not have a complete profile. Use `pip install.`

## Tech Stack

`chromadb` -> open source vector database we are using to store our data here.
Read more [here](https://www.trychroma.com/).

## Deployment

1. Install all necessary dependencies.

2. Run `ingest_db.py` once to generate chroma_db vector database for RAG and embedding. This gets invoked in chatbot prompting.

`chroma_db` is auto-generated when you run `ingest_db.py` once to provision the chroma_db.

3. Run `chatboy.py`. This will deploy gradio as our demo app to showcase what the chatbot can do!