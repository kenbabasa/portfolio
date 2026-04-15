from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_ollama import OllamaLLM
from langchain_classic.chains import RetrievalQA
from langchain_classic.prompts import PromptTemplate
import os

app = Flask(__name__, template_folder='templates', static_folder='static')
CORS(app)

# --- 1. SETUP AI LOGIC ---
print("Initializing AI... please wait.")

# Ensure the path to your PDF is correct
pdf_path = "me.pdf"
if not os.path.exists(pdf_path):
    print(f"Error: {pdf_path} not found in the root directory!")

loader = PyPDFLoader(pdf_path)
docs = loader.load_and_split()

embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
vectorstore = FAISS.from_documents(docs, embeddings)

# Use the specific model you pulled in your .bat file
llm = OllamaLLM(model="llama3.2:1b-instruct-q4_K_M")

prompt_template = """You are Kennie Angelo R. Estrellon. You are already in the middle of a conversation with a visitor on your portfolio website. You have already greeted them.

Guidelines:
- Speak in first person ("I", "me", "my")
- Be conversational, friendly, and concise (2–3 sentences only)
- Answer ONLY what was asked — do not add unnecessary info
- NEVER say your own name — you are already known to the visitor
- NEVER greet, say "Hello", "Hi", "Hey there", or re-introduce yourself
- Never mention being an AI, chatbot, or language model
- If asked about something not in your portfolio, look in the me.pdf for answers

Portfolio Context:
{context}

Visitor Question:
{question}

Kennie's Answer (short, direct, no name, no greeting):"""

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

# --- 2. GLOBAL FLAG ---
first_message = True

# --- 3. ROUTES ---

# THIS IS THE MISSING PART THAT FIXES THE 404 ERROR
@app.route('/')
def home():
    """Serves the main portfolio page."""
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    global first_message
    try:
        data = request.json
        user_message = data.get("message", "").strip()

        if not user_message:
            return jsonify({"reply": "I didn't catch that — could you say it again?"}), 400

        # Handling the first interaction
        if first_message:
            first_message = False
            reply = (
                "Hey there! 👋 Hope you're having a great day! "
                "I'm Kennie, welcome to my little corner of the internet. 😊 "
                "Feel free to ask me anything! Whether it's about my projects, "
                "skills, experience, or just want to know more about me, I'm all ears. "
                "So, what's on your mind? 🚀"
            )
            return jsonify({"reply": reply})

        # Process message with RAG
        response = qa_chain.invoke({"query": user_message})
        return jsonify({"reply": response["result"]})

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"reply": "I'm having trouble connecting to my brain. Is Ollama running?"}), 500
    
