import streamlit as st
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.vectorstores import FAISS
from langchain.chains import RetrievalQA 
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
# --- SWAPPED THIS ---
from langchain_ollama import OllamaLLM 

st.title("Chat with Kennie (Local AI)")

@st.cache_resource 
def initialize_qa():
    # 1. Load PDF
    loader = PyPDFLoader("about me.pdf") 
    documents = loader.load()
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    docs = text_splitter.split_documents(documents)

    # 2. Local Embeddings (Stays the same)
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    vectorstore = FAISS.from_documents(docs, embeddings)

    # 3. Initialize Local Ollama (NO API KEY NEEDED)
    # We use llama3.2:1b because it's fast on your MateBook D15
    llm = OllamaLLM(model="llama3.2:1b") 

    # 4. Create the QA Chain
    qa = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=vectorstore.as_retriever()
    )
    return qa

# Initialize the chain
try:
    qa_chain = initialize_qa()
except Exception as e:
    st.error(f"Make sure Ollama is running! Error: {e}")
    st.stop()

# --- Chat Interface (Stays mostly the same) ---
if 'messages' not in st.session_state:
    st.session_state['messages'] = []

for message in st.session_state['messages']:
    st.chat_message(message['role']).markdown(message['content'])

prompt = st.chat_input("Ask me about my portfolio:")

if prompt:
    st.chat_message('user').markdown(prompt)
    st.session_state['messages'].append({"role": "user", "content": prompt})

    with st.spinner("Processing locally..."):
        # invoke is the modern way to call the chain
        response = qa_chain.invoke({"query": prompt}) 
        answer = response["result"]

    st.chat_message('assistant').markdown(answer)
    st.session_state['messages'].append({"role": "assistant", "content": answer})