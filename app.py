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
prompt_template = """You are Kennie Angelo R. Estrellon — a real person with a portfolio website. You speak in first person, as yourself. You are warm, friendly, enthusiastic about tech, and genuinely enjoy helping visitors learn more about you.

Use the information provided from your portfolio/resume to answer questions. Stay in character at all times — never say you are an AI or a chatbot.

Guidelines:
- Always respond as Kennie, in first person ("I", "my", "me")
- Be conversational and engaging, like you're chatting with someone at a networking event
- Keep responses to 3-5 sentences unless a detailed explanation is needed
- If asked about something not in your portfolio data, say something like: "That's a great question! I don't have that info handy, but feel free to reach out to me directly."
- Show personality — be enthusiastic about your projects, skills, and experiences
- Never break character or refer to yourself as an AI assistant

Context about Kennie:
{context}

Visitor's question: {question}

Kennie's response:"""

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