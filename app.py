from flask import Flask, request, jsonify
from flask_cors import CORS
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_ollama import OllamaLLM
from langchain_classic.chains import RetrievalQA
from langchain_classic.prompts import PromptTemplate
import os

app = Flask(__name__)
CORS(app)

# --- 1. SETUP AI LOGIC ---
print("Initializing AI... please wait.")

loader = PyPDFLoader("about me.pdf")
docs = loader.load_and_split()

embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

vectorstore = FAISS.from_documents(docs, embeddings)

llm = OllamaLLM(model="llama3.2:1b")

# Custom prompt
prompt_template = """You are an AI assistant on Kennie Angelo R. Estrellon's portfolio website.
You help VISITORS learn about Kennie. You are Kennie yourself.
Use the following information from Kennie's PDF to answer questions about him.
Answer as if you are Kennie, and be friendly and engaging. If you don't know the answer, say you don't know.

Context: {context}

Question: {question}

Answer:"""

PROMPT = PromptTemplate(
    template=prompt_template,
    input_variables=["context", "question"]
)

qa_chain = RetrievalQA.from_chain_type(
    llm=llm,
    retriever=vectorstore.as_retriever(),
    chain_type_kwargs={"prompt": PROMPT}
)

print("AI is ready!")

# --- 2. THE API ROUTE ---
@app.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.json
        user_message = data.get("message")
        response = qa_chain.invoke({"query": user_message})
        return jsonify({"reply": response["result"]})
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"reply": "I'm having trouble connecting to my brain. Is Ollama running?"}), 500

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=True)