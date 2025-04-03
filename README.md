---
title: justo
app_file: chatbot.py
sdk: gradio
sdk_version: 5.23.1
---
# Justice for All Prototyping

Developing a prototype for [Justice for All](https://j4all.org), a pioneering platform to making justice accessible to everyone bu leveraging open-source data.

## Data sources

Please see `data/` directory to view a complete list of datasets used for this platform.

## Installation

Use `pyproject.toml` file to install dependencies. You may have to install some modules separately because Poetry may not have a complete profile. Use `pip install.`

## Tech Stack

* [Chroma](https://www.trychroma.com/) -> open source vector database

* [Langchain](https://www.langchain.com/) -> RAG, embedded semantic search generation engine

* [OpenAI](https://openai.com/) for embedded text modeling

* [gradio](https://www.gradio.app/) for rag `chatbot` prompting interface

* [huggingface](https://huggingface.co/) for deploying the model live coupled with github action for a CI/CD workflow.

## Deployment

1. Install all necessary dependencies.

2. Run `ingest_db.py` once to generate chroma_db vector database for RAG and embedding. This gets invoked in chatbot prompting.

    * `chroma_db` is auto-generated when you run `ingest_db.py` once to provision the chroma_db.

3. Run `chatbot.py`. This will deploy gradio as our demo app to showcase what the chatbot can do!