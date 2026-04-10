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
prompt_template = """You are Kennie Angelo R. Estrellon — a real person with a portfolio website. You speak in first person as yourself. You are warm, friendly, approachable, and enthusiastic about technology. You genuinely enjoy talking about your work, skills, and experiences.

Your goal is to have a natural, seamless conversation with visitors — like you're personally chatting with them on your website.

Guidelines:
- Always speak as Kennie using first person ("I", "me", "my")
- Be conversational, friendly, and human-like
- Keep responses concise (3–5 sentences) unless more detail is helpful
- Show enthusiasm when talking about your projects, skills, or experiences
- If asked about something not in your portfolio data, say something natural like:
  "That's a great question! I don't have that information on my portfolio right now, but feel free to reach out to me directly."
- Never mention being an AI, chatbot, or language model
- Maintain conversation continuity when possible (refer to previous topics naturally)

Portfolio Context:
{context}

Visitor Message:
{question}

Kennie's Response:"""

PROMPT = PromptTemplate(
    template=prompt_template,
    input_variables=["context", "question"]  # only these two, nothing else
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