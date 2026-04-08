from flask import Flask, request, jsonify
from flask_cors import CORS
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_ollama import OllamaLLM
from langchain.chains import RetrievalQA
import os

app = Flask(__name__)
CORS(app)  # This allows your HTML file to talk to this Python server

# --- 1. SETUP AI LOGIC ---
print("Initializing AI... please wait.")
# Make sure "about me.pdf" is in the same folder!
loader = PyPDFLoader("about me.pdf")
docs = loader.load_and_split()

# Create the librarian (Embeddings)
embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

# Create the library (Vector Store)
vectorstore = FAISS.from_documents(docs, embeddings)

# Connect to the Brain (Ollama)
llm = OllamaLLM(model="llama3.2:1b")

# Combine them into a QA Chain
qa_chain = RetrievalQA.from_chain_type(llm=llm, retriever=vectorstore.as_retriever())
print("AI is ready!")

# --- 2. THE API ROUTE ---
@app.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.json
        user_message = data.get("message")
        
        # Get response from your PDF-trained AI
        response = qa_chain.invoke({"query": user_message})
        
        return jsonify({"reply": response["result"]})
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"reply": "I'm having trouble connecting to my brain. Is Ollama running?"}), 500

if __name__ == '__main__':
    # Run on port 5000 to match your JS fetch URL
    app.run(host='127.0.0.1', port=5000, debug=True)