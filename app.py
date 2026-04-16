from flask import Flask, request, jsonify, render_template
from flask_cors import CORS

from langchain_community.document_loaders import PyPDFLoader
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings

from langchain_ollama import OllamaLLM
from langchain_core.prompts import PromptTemplate

import os

app = Flask(__name__, template_folder='templates', static_folder='static')
CORS(app)

# -------------------------------
# 1. INIT
# -------------------------------
print("Initializing AI...")

pdf_path = "me.pdf"

if not os.path.exists(pdf_path):
    raise FileNotFoundError("me.pdf not found")

loader = PyPDFLoader(pdf_path)
docs = loader.load_and_split()

# Embeddings
embeddings = HuggingFaceEmbeddings(
    model_name="BAAI/bge-small-en-v1.5"
)

# -------------------------------
# 2. FAISS
# -------------------------------
if os.path.exists("faiss_index"):
    vectorstore = FAISS.load_local(
        "faiss_index",
        embeddings,
        allow_dangerous_deserialization=True
    )
else:
    vectorstore = FAISS.from_documents(docs, embeddings)
    vectorstore.save_local("faiss_index")

retriever = vectorstore.as_retriever(
    search_type="mmr",
    search_kwargs={"k": 4, "fetch_k": 10}
)

# -------------------------------
# 3. LLM (Hugging Face via Ollama wrapper)
# -------------------------------
llm = OllamaLLM(
    model="llama3.2:1b-instruct-q4_K_M"
)

print("AI Ready!")

# -------------------------------
# 4. SIMPLE RAG RETRIEVAL
# -------------------------------
def get_rag_context(query):
    docs = retriever.invoke(query)

    if not docs:
        return ""

    return "\n\n".join([d.page_content for d in docs])

# -------------------------------
# 5. SMART ROUTER
# -------------------------------
def route_query(query: str) -> str:
    q = query.lower()

    rag_keywords = [
        "project", "portfolio", "experience",
        "skill", "certificate", "certification", "resume", "education"
    ]

    general_keywords = [
        "how", "what is", "can you build", "explain",
        "flask", "python", "react", "app", "api", "code"
    ]

    if any(k in q for k in rag_keywords):
        return "rag"

    if any(k in q for k in general_keywords):
        return "llm"

    return "hybrid"

# -------------------------------
# 6. PROMPT FUNCTIONS
# -------------------------------
def ask_llm(prompt: str):
    return llm.invoke(prompt)

def rag_answer(user_message, context):
    prompt = f"""
You are Kennie Angelo R. Estrellon.

Answer in first person. Be natural, friendly, and concise (2–3 sentences max).

Use the context ONLY if it is relevant.

Context:
{context}

Question:
{user_message}

Answer:
"""
    return ask_llm(prompt)

def llm_answer(user_message):
    prompt = f"""
You are Kennie's personal portfolio assistant.

Answer naturally in first person.
Be helpful and concise.

Question:
{user_message}
"""
    return ask_llm(prompt)

def hybrid_answer(user_message, context):
    prompt = f"""
You are Kennie's AI assistant.

Use context if helpful, but rely on your own knowledge when needed.

Context:
{context}

Question:
{user_message}
"""
    return ask_llm(prompt)

# -------------------------------
# 7. ROUTES
# -------------------------------
first_message = True

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/techstack')
def techstack():
    return render_template('techstack.html')

@app.route('/certifications')
def certifications():
    return render_template('certifications.html')

@app.route('/chat', methods=['POST'])
def chat():
    global first_message

    try:
        data = request.get_json()
        user_message = (data.get("message") or data.get("query") or "").strip()

        if not user_message:
            return jsonify({"reply": "Please type something."}), 400

        # First greeting
        if first_message:
            first_message = False
            return jsonify({
                "reply": "Hey there! 👋 I'm Kennie. Ask me anything about my projects or skills 🚀"
            })

        mode = route_query(user_message)
        context = get_rag_context(user_message)

        if mode == "rag":
            reply = rag_answer(user_message, context)

        elif mode == "llm":
            reply = llm_answer(user_message)

        else:
            reply = hybrid_answer(user_message, context)

        return jsonify({"reply": reply})

    except Exception as e:
        print("ERROR:", e)
        return jsonify({
            "reply": "Something went wrong connecting to the AI."
        }), 500

# -------------------------------
# 8. RUN
# -------------------------------
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)