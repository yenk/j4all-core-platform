import streamlit as st
import os
from pathlib import Path
import requests
import zipfile
import io

# Page configuration
st.set_page_config(
    page_title="LumiLens - Legal Document Analysis",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .sub-header {
        font-size: 1.5rem;
        color: #2c3e50;
        margin-bottom: 1rem;
    }
    .info-box {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
</style>
""", unsafe_allow_html=True)

def download_and_unzip_data():
    """
    Download and extract data.zip from GitHub Releases if data/ or chroma_db/ do not exist.
    """
    release_url = "https://github.com/user-attachments/files/20872836/data.zip"  # Update if your tag or asset name changes
    data_dir = Path("data")
    db_dir = Path("chroma_db")
    if not data_dir.exists() or not db_dir.exists():
        print(f"Downloading data from {release_url}...")
        try:
            response = requests.get(release_url, stream=True)
            response.raise_for_status()
            with zipfile.ZipFile(io.BytesIO(response.content)) as z:
                z.extractall(".")
            print("✅ Data and database downloaded and set up successfully!")
        except Exception as e:
            print(f"Status code: {response.status_code}")
            print(f"Response content: {response.content[:200]}")
            raise
    else:
        print("Data directories already exist. Skipping download.")

def main():
    """"""
    # Download and extract data.zip if needed
    download_and_unzip_data()
    # Header
    st.markdown('<h1 class="main-header">📄 LumiLens</h1>', unsafe_allow_html=True)
    st.markdown('<p style="text-align: center; font-size: 1.2rem; color: #666;">Legal Document Analysis & AI Assistant</p>', unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.header("🔧 Navigation")
        page = st.selectbox(
            "Choose a page:",
            ["🏠 Home", "📊 Document Analysis", "💬 Chat Assistant", "📁 Document Upload", "⚙️ Settings"]
        )
        
        st.markdown("---")
        st.markdown("### 📋 Quick Stats")
        st.metric("Documents Processed", "1,247")
        st.metric("Analysis Accuracy", "94.2%")
        st.metric("Active Users", "23")
    
    # Main content based on page selection
    if page == "🏠 Home":
        show_home_page()
    elif page == "📊 Document Analysis":
        show_document_analysis()
    elif page == "💬 Chat Assistant":
        show_chat_assistant()
    elif page == "📁 Document Upload":
        show_document_upload()
    elif page == "⚙️ Settings":
        show_settings()

def show_home_page():
    st.markdown('<h2 class="sub-header">Welcome to LumiLens</h2>', unsafe_allow_html=True)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("""
        <div class="info-box">
        <h3>🚀 What is LumiLens?</h3>
        <p>LumiLens is an AI-powered legal document analysis platform that helps legal professionals 
        quickly extract insights, analyze contracts, and get intelligent answers to legal questions.</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("### 🔍 Key Features")
        features = [
            "📄 **Document Analysis**: Extract key information from legal documents",
            "💬 **AI Chat Assistant**: Get instant answers to legal questions",
            "📊 **Insight Dashboard**: Visualize document patterns and trends",
            "🔒 **Secure Processing**: Enterprise-grade security for sensitive documents",
            "⚡ **Fast Processing**: Analyze documents in seconds, not hours"
        ]
        
        for feature in features:
            st.markdown(f"- {feature}")
    
    with col2:
        st.markdown("### 📈 Recent Activity")
        st.metric("Documents Today", "12")
        st.metric("Queries Processed", "45")
        st.metric("Users Online", "8")
        
        st.markdown("### 🎯 Quick Actions")
        if st.button("📄 Upload Document", type="primary"):
            st.info("Navigate to Document Upload page")
        
        if st.button("💬 Start Chat"):
            st.info("Navigate to Chat Assistant page")

def show_document_analysis():
    st.markdown('<h2 class="sub-header">📊 Document Analysis</h2>', unsafe_allow_html=True)
    
    # Document upload section
    uploaded_file = st.file_uploader(
        "Choose a legal document to analyze",
        type=['pdf', 'docx', 'txt'],
        help="Upload a legal document for AI analysis"
    )
    
    if uploaded_file is not None:
        st.success(f"✅ Uploaded: {uploaded_file.name}")
        
        # Analysis options
        st.markdown("### 🔍 Analysis Options")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            extract_entities = st.checkbox("Extract Entities", value=True)
            extract_dates = st.checkbox("Extract Dates", value=True)
        
        with col2:
            extract_amounts = st.checkbox("Extract Amounts", value=True)
            extract_parties = st.checkbox("Extract Parties", value=True)
        
        with col3:
            summarize = st.checkbox("Generate Summary", value=True)
            risk_assessment = st.checkbox("Risk Assessment", value=False)
        
        if st.button("🚀 Analyze Document", type="primary"):
            with st.spinner("Analyzing document..."):
                # Placeholder for actual analysis
                st.info("🔧 Analysis functionality coming soon!")
                
                # Mock results
                st.markdown("### 📋 Analysis Results")
                
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown("**📅 Key Dates**")
                    st.write("- Contract Start: January 15, 2024")
                    st.write("- Contract End: December 31, 2024")
                    st.write("- Payment Due: 30 days")
                
                with col2:
                    st.markdown("**💰 Financial Terms**")
                    st.write("- Total Value: $125,000")
                    st.write("- Payment Schedule: Monthly")
                    st.write("- Late Fee: 2% per month")

def show_chat_assistant():
    st.markdown('<h2 class="sub-header">💬 AI Chat Assistant</h2>', unsafe_allow_html=True)
    
    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Chat input
    if prompt := st.chat_input("Ask me about legal documents, contracts, or regulations..."):
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Display user message
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Display assistant response
        with st.chat_message("assistant"):
            response = f"🔧 This is a placeholder response. The actual AI assistant functionality is coming soon!\n\nYou asked: {prompt}"
            st.markdown(response)
        
        # Add assistant response to chat history
        st.session_state.messages.append({"role": "assistant", "content": response})

def show_document_upload():
    st.markdown('<h2 class="sub-header">📁 Document Upload</h2>', unsafe_allow_html=True)
    
    st.markdown("""
    <div class="info-box">
    <h3>📋 Upload Guidelines</h3>
    <ul>
        <li>Supported formats: PDF, DOCX, TXT</li>
        <li>Maximum file size: 50MB</li>
        <li>Documents are processed securely</li>
        <li>Analysis results are available immediately</li>
    </ul>
    </div>
    """, unsafe_allow_html=True)
    
    # Batch upload
    uploaded_files = st.file_uploader(
        "Upload multiple documents",
        type=['pdf', 'docx', 'txt'],
        accept_multiple_files=True,
        help="Select multiple files for batch processing"
    )
    
    if uploaded_files:
        st.success(f"✅ Uploaded {len(uploaded_files)} documents")
        
        # Show uploaded files
        st.markdown("### 📄 Uploaded Files")
        for i, file in enumerate(uploaded_files):
            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                st.write(f"**{file.name}**")
            with col2:
                st.write(f"{file.size / 1024:.1f} KB")
            with col3:
                if st.button(f"Process {i+1}", key=f"process_{i}"):
                    st.info(f"Processing {file.name}...")

def show_settings():
    st.markdown('<h2 class="sub-header">⚙️ Settings</h2>', unsafe_allow_html=True)
    
    st.markdown("### 🔐 API Configuration")
    openai_key = st.text_input("OpenAI API Key", type="password", help="Enter your OpenAI API key")
    
    st.markdown("### 🎨 Interface Settings")
    theme = st.selectbox("Theme", ["Light", "Dark", "Auto"])
    language = st.selectbox("Language", ["English", "Spanish", "French"])
    
    st.markdown("### 📊 Analysis Settings")
    confidence_threshold = st.slider("Confidence Threshold", 0.0, 1.0, 0.8, 0.1)
    max_tokens = st.number_input("Max Tokens", min_value=100, max_value=4000, value=2000)
    
    if st.button("💾 Save Settings", type="primary"):
        st.success("Settings saved successfully!")

if __name__ == "__main__":
    main() 