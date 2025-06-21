---
title: LumiLens
app_file: prompt.py
sdk: gradio
sdk_version: 5.23.1
---

# LumiLens - Justice for All AI Assistant

LumiLens is an AI-powered legal assistant prototype for [Justice for All](https://j4all.org), designed to make justice accessible to everyone by leveraging open-source legal data and advanced natural language processing.

**🚧 Important Update**: We are transitioning from Gradio to **Streamlit** as our core prototype framework for the MVP. This change will provide better performance, more customization options, and improved user experience for our legal assistant application.

## 🚀 Features

- **Legal Document Analysis**: Processes and analyzes legal documents including contracts, case law, and appellate matters
- **RAG-Powered Q&A**: Retrieval-Augmented Generation for accurate legal question answering
- **Interactive Chat Interface**: User-friendly Streamlit-based chat interface (transitioning from Gradio)
- **Vector Database**: Efficient document storage and retrieval using ChromaDB
- **OpenAI Integration**: Leverages GPT-4o-mini for intelligent legal assistance

## 🛠️ Tech Stack

### Core Technologies
- **[ChromaDB](https://www.trychroma.com/)** - Open-source vector database for document storage and similarity search
- **[LangChain](https://www.langchain.com/)** - Framework for building LLM-powered applications with RAG capabilities
- **[OpenAI GPT-4o-mini](https://openai.com/)** - Large language model for text generation and understanding
- **[OpenAI Text Embeddings](https://openai.com/)** - Text embedding model for semantic search

### Web Interface & Deployment
- **[Streamlit](https://streamlit.io/)** - Modern web framework for data applications (replacing Gradio)
- **[GitHub Actions](https://github.com/features/actions)** - CI/CD pipeline for automated deployment
- **[Streamlit Cloud](https://streamlit.io/cloud)** - Hosting platform for Streamlit applications

### Data Processing
- **[PyPDF](https://pypdf.readthedocs.io/)** - PDF document processing and text extraction
- **[BeautifulSoup4](https://www.crummy.com/software/BeautifulSoup/)** - HTML/XML parsing
- **[TikToken](https://github.com/openai/tiktoken)** - Token counting for OpenAI models

## 📋 Prerequisites

- Python 3.12+
- OpenAI API key
- Git

## 🚀 Quick Start

### 1. Clone the Repository
```bash
git clone <repository-url>
cd j4all-core-platform
```

### 2. Install Dependencies

**Option A: Using Poetry (Recommended)**
```bash
# Install Poetry if you haven't already
curl -sSL https://install.python-poetry.org | python3 -

# Install dependencies
poetry install
```

**Option B: Using pip**
```bash
pip install -r requirements.txt
```

### 3. Environment Setup

Create a `.env` file in the root directory:
```bash
cp .env.example .env  # if .env.example exists
```

Add your OpenAI API key:
```env
OPENAI_API_KEY=your_openai_api_key_here
```

### 4. Data Ingestion

Run the ingestion script to process legal documents and create the vector database:
```bash
# Using Poetry
poetry run python pipeline/ingest.py

# Using pip
python pipeline/ingest.py
```

This will:
- Load PDF documents from the `data/` directory
- Split documents into chunks
- Generate embeddings using OpenAI
- Store vectors in ChromaDB

### 5. Launch the Application

**Current (Gradio):**
```bash
# Using Poetry
poetry run python prompt.py

# Using pip
python prompt.py
```

**Upcoming (Streamlit):**
```bash
# Using Poetry
poetry run streamlit run app.py

# Using pip
streamlit run app.py
```

The application will be available at `http://localhost:8501` (Streamlit) or `http://localhost:7860` (current Gradio).

## 📁 Project Structure

```
j4all-core-platform/
├── data/                   # Legal documents (PDFs) organized by year
│   ├── 2021/
│   ├── 2022/
│   ├── 2023/
│   ├── 2024/
│   └── 2025/
├── pipeline/              # Data processing pipeline
│   ├── __init__.py
│   ├── ingest.py         # Document ingestion and vectorization
│   └── load.py           # Data loading utilities
├── chroma_db/            # Vector database (auto-generated)
├── prompt.py             # Current Gradio application
├── app.py                # Upcoming Streamlit application
├── pyproject.toml        # Poetry dependencies
├── requirements.txt      # pip dependencies
└── README.md
```

## 🔧 Development

### Local Development Setup

1. **Fork and clone** the repository
2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. **Install development dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
4. **Set up environment variables** (see Quick Start section)
5. **Run the ingestion pipeline** to populate the vector database
6. **Start the development server**:
   ```bash
   # Current Gradio version
   python prompt.py
   
   # Upcoming Streamlit version
   streamlit run app.py
   ```

### Code Style

- Follow PEP 8 guidelines
- Use type hints where appropriate
- Add docstrings to functions and classes
- Keep functions focused and single-purpose

### Testing

```bash
# Run tests (when implemented)
python -m pytest

# Run linting
flake8 .
```

## 🤝 Contributing

We welcome contributions! Here's how you can help:

### 1. Fork the Repository
Create your own fork of the project on GitHub.

### 2. Create a Feature Branch
```bash
git checkout -b feature/your-feature-name
```

### 3. Make Your Changes
- Add new features or fix bugs
- Update documentation as needed
- Ensure code follows project standards

### 4. Test Your Changes
- Run the ingestion pipeline with your changes
- Test the application locally
- Ensure all functionality works as expected

### 5. Submit a Pull Request
- Provide a clear description of your changes
- Include any relevant issue numbers
- Request review from maintainers

### Areas for Contribution
- **Streamlit Migration**: Help transition from Gradio to Streamlit
- **Document Processing**: Improve PDF parsing and text extraction
- **RAG Pipeline**: Enhance retrieval and generation capabilities
- **UI/UX**: Improve the Streamlit interface and user experience
- **Performance**: Optimize vector search and response times
- **Documentation**: Expand guides and examples

## 🚀 Deployment

### Streamlit Cloud Deployment

The project will be deployed using Streamlit Cloud for the MVP.

1. **Fork the repository** to your GitHub account
2. **Set up Streamlit Cloud**:
   - Go to [Streamlit Cloud](https://streamlit.io/cloud)
   - Connect your GitHub account
   - Deploy the repository
3. **Configure environment variables** in Streamlit Cloud dashboard
4. **Deploy** - Streamlit Cloud will automatically deploy from your main branch

### Local Deployment

```bash
# Install Streamlit
pip install streamlit

# Run locally
streamlit run app.py
```

## 📊 Data Sources

The platform uses legal documents from the `data/` directory, organized by year. Each document is processed and indexed for semantic search capabilities.

**Document Types:**
- Contract disputes
- Appellate decisions
- Legal orders and dismissals
- Case law documents

## 🔒 Security & Privacy

- **API Keys**: Never commit API keys to version control
- **Data Privacy**: Ensure compliance with data protection regulations
- **Access Control**: Implement appropriate access controls for sensitive legal data

## 📝 License

[Add your license information here]

## 🆘 Support

- **Issues**: Report bugs and feature requests via GitHub Issues
- **Discussions**: Join community discussions in GitHub Discussions
- **Documentation**: Check the project wiki for detailed guides

## 🙏 Acknowledgments

- Justice for All organization for the vision and mission
- OpenAI for providing the language models
- The open-source community for the tools and frameworks used

---

**Note**: This is a prototype system transitioning to Streamlit for the MVP. For production use, ensure proper security measures, data validation, and compliance with legal requirements.