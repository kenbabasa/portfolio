from flask import Flask, request, jsonify, render_template
from flask_cors import CORS

from langchain_community.document_loaders import PyPDFLoader
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings

from langchain_ollama import OllamaLLM
from langchain_core.prompts import PromptTemplate

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

import os
import uuid
import json
from datetime import datetime, timedelta

app = Flask(__name__, template_folder='templates', static_folder='static')
CORS(app)

# -------------------------------
# CONFIG  ← update these
# -------------------------------
OWNER_EMAIL  = 'kennieangelo.estrellon_cyn@isu.edu.ph'
GMAIL_PASS   = 'acngwawkbbeplcja'          # your 16-char app password
BASE_URL     = 'http://127.0.0.1:5000'     # change to your public URL when deployed

# In-memory store for pending meetings (use a DB in production)
pending_meetings = {}

# -------------------------------
# 1. INIT
# -------------------------------
print("Initializing AI...")

pdf_path = "me.pdf"

if not os.path.exists(pdf_path):
    raise FileNotFoundError("me.pdf not found")

loader = PyPDFLoader(pdf_path)
docs = loader.load_and_split()

embeddings = HuggingFaceEmbeddings(model_name="BAAI/bge-small-en-v1.5")

if os.path.exists("faiss_index"):
    vectorstore = FAISS.load_local(
        "faiss_index", embeddings, allow_dangerous_deserialization=True
    )
else:
    vectorstore = FAISS.from_documents(docs, embeddings)
    vectorstore.save_local("faiss_index")

retriever = vectorstore.as_retriever(
    search_type="mmr", search_kwargs={"k": 4, "fetch_k": 10}
)

llm = OllamaLLM(model="llama3.2:1b-instruct-q4_K_M")
print("AI Ready!")

# -------------------------------
# 2. RAG / ROUTING
# -------------------------------
def get_rag_context(query):
    docs = retriever.invoke(query)
    return "\n\n".join([d.page_content for d in docs]) if docs else ""

def route_query(query: str) -> str:
    q = query.lower()
    if any(k in q for k in ["project","portfolio","experience","skill","certificate","certification","resume","education"]):
        return "rag"
    if any(k in q for k in ["how","what is","can you build","explain","flask","python","react","app","api","code"]):
        return "llm"
    return "hybrid"

def ask_llm(prompt): return llm.invoke(prompt)

def rag_answer(user_message, context):
    return ask_llm(f"""You are Kennie Angelo R. Estrellon.
Answer in first person. Be natural, friendly, and concise (2–3 sentences max).
Context:\n{context}\nQuestion:\n{user_message}\nAnswer:""")

def llm_answer(user_message):
    return ask_llm(f"""You are Kennie's personal portfolio assistant.
Answer naturally in first person. Be helpful and concise.\nQuestion:\n{user_message}""")

def hybrid_answer(user_message, context):
    return ask_llm(f"""You are Kennie's AI assistant.
Use context if helpful, but rely on your own knowledge when needed.
Context:\n{context}\nQuestion:\n{user_message}""")

# -------------------------------
# 3. EMAIL HELPERS
# -------------------------------
def send_email(to_addr, subject, html_body, text_body=""):
    msg = MIMEMultipart("alternative")
    msg["From"]    = OWNER_EMAIL
    msg["To"]      = to_addr
    msg["Subject"] = subject
    if text_body:
        msg.attach(MIMEText(text_body, "plain"))
    msg.attach(MIMEText(html_body, "html"))
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as s:
        s.login(OWNER_EMAIL, GMAIL_PASS)
        s.sendmail(OWNER_EMAIL, to_addr, msg.as_string())


def make_google_meet_link(date_str, time_str, duration, title, attendees):
    """
    Generates a Google Meet link via a pre-filled Google Calendar event URL.
    Real Meet links are created server-side only via Google Calendar API.
    This opens a calendar event with Meet conference pre-selected — clicking
    'Save' creates the Meet. For a true auto-generated link you'd need OAuth.
    """
    def pad(n): return str(n).zfill(2)
    dt = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
    dt_end = dt + timedelta(minutes=int(duration))
    fmt = lambda d: d.strftime("%Y%m%dT%H%M%S")
    enc = lambda s: s.replace(" ", "+").replace(",", "%2C").replace(":", "%3A")
    attendee_str = "&add=" + "&add=".join(enc(a) for a in attendees)
    return (
        f"https://calendar.google.com/calendar/render?action=TEMPLATE"
        f"&text={enc(title)}"
        f"&dates={fmt(dt)}/{fmt(dt_end)}"
        f"&details={enc('Meeting scheduled via portfolio.')}"
        f"&location={enc('Google Meet')}"
        f"&conferenceSolution=hangoutsMeet"
        f"{attendee_str}"
    )


def make_ics(title, date_str, time_str, duration, organizer_email, guest_name, guest_email, meet_url=""):
    dt = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
    dt_end = dt + timedelta(minutes=int(duration))
    fmt = lambda d: d.strftime("%Y%m%dT%H%M%S")
    uid = str(uuid.uuid4())
    desc = f"Meeting scheduled via portfolio.\\nGoogle Meet: {meet_url}" if meet_url else "Meeting scheduled via portfolio."
    return "\r\n".join([
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//Kennie Portfolio//EN",
        "METHOD:REQUEST",
        "BEGIN:VEVENT",
        f"UID:{uid}",
        f"DTSTART:{fmt(dt)}",
        f"DTEND:{fmt(dt_end)}",
        f"SUMMARY:{title}",
        f"DESCRIPTION:{desc}",
        f"LOCATION:Google Meet",
        f"ORGANIZER;CN=Kennie Angelo Estrellon:MAILTO:{organizer_email}",
        f"ATTENDEE;CN=Kennie;RSVP=TRUE:MAILTO:{organizer_email}",
        f"ATTENDEE;CN={guest_name};RSVP=TRUE:MAILTO:{guest_email}",
        "END:VEVENT",
        "END:VCALENDAR"
    ])


def send_owner_notification(token, meeting):
    confirm_url = f"{BASE_URL}/meeting/confirm/{token}"
    decline_url = f"{BASE_URL}/meeting/decline/{token}"

    h = int(meeting['time'].split(':')[0])
    mn = meeting['time'].split(':')[1]
    readable_time = f"{h%12 or 12}:{mn} {'PM' if h>=12 else 'AM'}"
    readable_date = datetime.strptime(meeting['date'], "%Y-%m-%d").strftime("%A, %B %d, %Y")

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="UTF-8">
      <style>
        body {{ font-family: 'Segoe UI', Arial, sans-serif; background: #f5f5f5; margin: 0; padding: 20px; }}
        .card {{ background: #fff; max-width: 520px; margin: 0 auto; border: 1px solid #e8e8e8; padding: 36px; }}
        h2 {{ margin: 0 0 6px 0; font-size: 20px; color: #1a1a1a; }}
        .meta {{ font-size: 14px; color: #555; margin-bottom: 24px; }}
        .detail {{ display: flex; gap: 10px; margin-bottom: 10px; font-size: 14px; color: #333; }}
        .label {{ font-weight: 600; min-width: 70px; }}
        .divider {{ border: none; border-top: 1px solid #e8e8e8; margin: 24px 0; }}
        .btn-row {{ display: flex; gap: 12px; margin-top: 8px; }}
        .btn {{ display: inline-block; padding: 13px 28px; font-size: 14px; font-weight: 700;
                text-decoration: none; text-align: center; letter-spacing: 0.3px; }}
        .btn-confirm {{ background: #1a1a1a; color: #fff; }}
        .btn-decline {{ background: #fff; color: #1a1a1a; border: 1.5px solid #1a1a1a; }}
        .footer {{ font-size: 12px; color: #aaa; margin-top: 24px; text-align: center; }}
      </style>
    </head>
    <body>
      <div class="card">
        <h2>📅 New Meeting Request</h2>
        <p class="meta">Someone wants to schedule a meeting with you.</p>
        <div class="detail"><span class="label">Guest</span><span>{meeting['name']}</span></div>
        <div class="detail"><span class="label">Email</span><span>{meeting['email']}</span></div>
        <div class="detail"><span class="label">Topic</span><span>{meeting['topic']}</span></div>
        <div class="detail"><span class="label">Date</span><span>{readable_date}</span></div>
        <div class="detail"><span class="label">Time</span><span>{readable_time}</span></div>
        <div class="detail"><span class="label">Duration</span><span>{meeting['duration']} min</span></div>
        <hr class="divider">
        <p style="font-size:14px; color:#333; margin-bottom:16px;">
          Click <strong>Confirm</strong> to accept and send both parties a calendar invite with a Google Meet link,
          or <strong>Decline</strong> to notify the guest politely.
        </p>
        <div class="btn-row">
          <a href="{confirm_url}" class="btn btn-confirm">✓ Confirm Meeting</a>
          <a href="{decline_url}" class="btn btn-decline">✗ Decline</a>
        </div>
        <p class="footer">This link expires once used. Kennie's Portfolio Bot</p>
      </div>
    </body>
    </html>
    """
    send_email(OWNER_EMAIL, f"📅 Meeting Request: {meeting['topic']} — {readable_date}", html)


def send_guest_pending(meeting):
    h = int(meeting['time'].split(':')[0])
    mn = meeting['time'].split(':')[1]
    readable_time = f"{h%12 or 12}:{mn} {'PM' if h>=12 else 'AM'}"
    readable_date = datetime.strptime(meeting['date'], "%Y-%m-%d").strftime("%A, %B %d, %Y")

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="UTF-8">
      <style>
        body {{ font-family: 'Segoe UI', Arial, sans-serif; background: #f5f5f5; margin: 0; padding: 20px; }}
        .card {{ background: #fff; max-width: 520px; margin: 0 auto; border: 1px solid #e8e8e8; padding: 36px; }}
        h2 {{ margin: 0 0 8px 0; font-size: 20px; color: #1a1a1a; }}
        .badge {{ display: inline-block; padding: 4px 12px; background: #fff8e1;
                  border: 1px solid #ffe082; color: #b8860b; font-size: 12px;
                  font-weight: 700; margin-bottom: 20px; letter-spacing: 0.5px; }}
        .detail {{ display: flex; gap: 10px; margin-bottom: 10px; font-size: 14px; color: #333; }}
        .label {{ font-weight: 600; min-width: 70px; }}
        .footer {{ font-size: 12px; color: #aaa; margin-top: 24px; text-align: center; }}
      </style>
    </head>
    <body>
      <div class="card">
        <h2>Your meeting request was received! 🎉</h2>
        <div class="badge">PENDING CONFIRMATION</div>
        <p style="font-size:14px; color:#555; margin-bottom:20px;">
          Hi {meeting['name']}, thank you for reaching out! Your meeting request has been sent to Kennie.
          You'll receive a confirmation email once it's approved.
        </p>
        <div class="detail"><span class="label">Topic</span><span>{meeting['topic']}</span></div>
        <div class="detail"><span class="label">Date</span><span>{readable_date}</span></div>
        <div class="detail"><span class="label">Time</span><span>{readable_time}</span></div>
        <div class="detail"><span class="label">Duration</span><span>{meeting['duration']} min</span></div>
        <p class="footer">Kennie Angelo Estrellon · Portfolio</p>
      </div>
    </body>
    </html>
    """
    send_email(meeting['email'], f"⏳ Meeting request received — awaiting confirmation", html)


def send_confirmed_emails(meeting, meet_url, ics_data):
    h = int(meeting['time'].split(':')[0])
    mn = meeting['time'].split(':')[1]
    readable_time = f"{h%12 or 12}:{mn} {'PM' if h>=12 else 'AM'}"
    readable_date = datetime.strptime(meeting['date'], "%Y-%m-%d").strftime("%A, %B %d, %Y")

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="UTF-8">
      <style>
        body {{ font-family: 'Segoe UI', Arial, sans-serif; background: #f5f5f5; margin: 0; padding: 20px; }}
        .card {{ background: #fff; max-width: 520px; margin: 0 auto; border: 1px solid #e8e8e8; padding: 36px; }}
        h2 {{ margin: 0 0 8px 0; font-size: 20px; color: #1a1a1a; }}
        .badge {{ display: inline-block; padding: 4px 12px; background: #e8f5e9;
                  border: 1px solid #a5d6a7; color: #2e7d32; font-size: 12px;
                  font-weight: 700; margin-bottom: 20px; letter-spacing: 0.5px; }}
        .detail {{ display: flex; gap: 10px; margin-bottom: 10px; font-size: 14px; color: #333; }}
        .label {{ font-weight: 600; min-width: 70px; }}
        .meet-box {{ background: #f0f7ff; border: 1px solid #bbdefb; padding: 14px 18px;
                     margin: 20px 0; border-radius: 2px; }}
        .meet-box a {{ color: #1565c0; font-size: 14px; word-break: break-all; }}
        .btn {{ display: inline-block; padding: 13px 28px; font-size: 14px; font-weight: 700;
                background: #1a1a1a; color: #fff; text-decoration: none; margin-top: 8px; }}
        .footer {{ font-size: 12px; color: #aaa; margin-top: 24px; text-align: center; }}
      </style>
    </head>
    <body>
      <div class="card">
        <h2>Meeting Confirmed! ✅</h2>
        <div class="badge">CONFIRMED</div>
        <p style="font-size:14px; color:#555; margin-bottom:20px;">
          Hi {meeting['name']}, your meeting with Kennie Angelo Estrellon has been confirmed. See details below.
        </p>
        <div class="detail"><span class="label">Topic</span><span>{meeting['topic']}</span></div>
        <div class="detail"><span class="label">Date</span><span>{readable_date}</span></div>
        <div class="detail"><span class="label">Time</span><span>{readable_time}</span></div>
        <div class="detail"><span class="label">Duration</span><span>{meeting['duration']} min</span></div>
        <div class="meet-box">
          <strong style="font-size:13px; display:block; margin-bottom:6px;">📹 Google Meet Link</strong>
          <a href="{meet_url}">{meet_url}</a>
        </div>
        <p style="font-size:13px; color:#777; margin-bottom:8px;">
          A calendar invite (.ics) is attached — open it to add this event to your calendar automatically.
        </p>
        <p class="footer">Kennie Angelo Estrellon · Portfolio</p>
      </div>
    </body>
    </html>
    """

    # Build multipart email with ICS attachment for GUEST
    def build_msg(to_addr, subject):
        msg = MIMEMultipart("mixed")
        msg["From"]    = OWNER_EMAIL
        msg["To"]      = to_addr
        msg["Subject"] = subject
        msg.attach(MIMEText(html, "html"))
        ics_part = MIMEText(ics_data, "calendar; method=REQUEST")
        ics_part.add_header("Content-Disposition", "attachment", filename="meeting-kennie.ics")
        msg.attach(ics_part)
        return msg

    subj = f"✅ Meeting Confirmed: {meeting['topic']} — {readable_date} at {readable_time}"

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as s:
        s.login(OWNER_EMAIL, GMAIL_PASS)
        # send to guest
        guest_msg = build_msg(meeting['email'], subj)
        s.sendmail(OWNER_EMAIL, meeting['email'], guest_msg.as_string())
        # send to owner
        owner_msg = build_msg(OWNER_EMAIL, subj)
        s.sendmail(OWNER_EMAIL, OWNER_EMAIL, owner_msg.as_string())


def send_declined_email(meeting):
    h = int(meeting['time'].split(':')[0])
    mn = meeting['time'].split(':')[1]
    readable_time = f"{h%12 or 12}:{mn} {'PM' if h>=12 else 'AM'}"
    readable_date = datetime.strptime(meeting['date'], "%Y-%m-%d").strftime("%A, %B %d, %Y")

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="UTF-8">
      <style>
        body {{ font-family: 'Segoe UI', Arial, sans-serif; background: #f5f5f5; margin: 0; padding: 20px; }}
        .card {{ background: #fff; max-width: 520px; margin: 0 auto; border: 1px solid #e8e8e8; padding: 36px; }}
        h2 {{ margin: 0 0 8px 0; font-size: 20px; color: #1a1a1a; }}
        .badge {{ display: inline-block; padding: 4px 12px; background: #fce4ec;
                  border: 1px solid #f48fb1; color: #880e4f; font-size: 12px;
                  font-weight: 700; margin-bottom: 20px; letter-spacing: 0.5px; }}
        .detail {{ display: flex; gap: 10px; margin-bottom: 10px; font-size: 14px; color: #333; }}
        .label {{ font-weight: 600; min-width: 70px; }}
        .footer {{ font-size: 12px; color: #aaa; margin-top: 24px; text-align: center; }}
      </style>
    </head>
    <body>
      <div class="card">
        <h2>Meeting Request — Unable to Attend</h2>
        <div class="badge">DECLINED</div>
        <p style="font-size:14px; color:#555; margin-bottom:20px;">
          Hi {meeting['name']}, thank you for your interest in meeting with Kennie!
          Unfortunately, Kennie is not available at the requested time:
        </p>
        <div class="detail"><span class="label">Date</span><span>{readable_date}</span></div>
        <div class="detail"><span class="label">Time</span><span>{readable_time}</span></div>
        <p style="font-size:14px; color:#555; margin-top:20px; line-height:1.7;">
          Please visit the portfolio again and choose a different date and time that works for you.
          Kennie looks forward to connecting with you soon! 😊
        </p>
        <p style="margin-top:20px;">
          <a href="{BASE_URL}" style="font-size:14px; color:#1a1a1a; font-weight:700;">
            → Schedule another time
          </a>
        </p>
        <p class="footer">Kennie Angelo Estrellon · Portfolio</p>
      </div>
    </body>
    </html>
    """
    send_email(meeting['email'], f"Meeting Request Update — {meeting['topic']}", html)

# -------------------------------
# 4. ROUTES
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
        if first_message:
            first_message = False
            return jsonify({"reply": "Hey there! 👋 I'm Kennie. Ask me anything about my projects or skills 🚀"})
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
        return jsonify({"reply": "Something went wrong connecting to the AI."}), 500


@app.route('/schedule', methods=['POST'])
def schedule():
    try:
        data     = request.get_json()
        name     = data.get('name', '').strip()
        email    = data.get('email', '').strip()
        date     = data.get('date', '')
        time     = data.get('time', '')
        duration = data.get('duration', '15')
        topic    = data.get('topic', 'Meeting with Kennie') or 'Meeting with Kennie'

        if not all([name, email, date, time]):
            return jsonify({'status': 'error', 'message': 'Missing required fields'}), 400

        token = str(uuid.uuid4())
        pending_meetings[token] = {
            'name': name, 'email': email, 'date': date,
            'time': time, 'duration': duration, 'topic': topic,
            'status': 'pending'
        }

        # Notify owner with confirm/decline buttons
        send_owner_notification(token, pending_meetings[token])

        # Notify guest that request is pending
        send_guest_pending(pending_meetings[token])

        print(f"✅ Meeting request stored [{token}] for {name}")
        return jsonify({'status': 'ok'})

    except Exception as e:
        print("❌ Schedule error:", e)
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/meeting/confirm/<token>')
def confirm_meeting(token):
    meeting = pending_meetings.get(token)

    if not meeting:
        return _response_page("❌ Invalid or Expired Link",
            "This confirmation link is no longer valid.", "#fce4ec", "#880e4f")

    if meeting.get('status') != 'pending':
        return _response_page("ℹ️ Already Processed",
            f"This meeting has already been {meeting.get('status')}.", "#e3f2fd", "#1565c0")

    meeting['status'] = 'confirmed'

    # Build Google Meet link (opens calendar with Meet pre-selected)
    meet_url = make_google_meet_link(
        meeting['date'], meeting['time'], meeting['duration'],
        meeting['topic'], [OWNER_EMAIL, meeting['email']]
    )

    # Build ICS
    ics_data = make_ics(
        meeting['topic'], meeting['date'], meeting['time'],
        meeting['duration'], OWNER_EMAIL,
        meeting['name'], meeting['email'], meet_url
    )

    try:
        send_confirmed_emails(meeting, meet_url, ics_data)
        print(f"✅ Meeting confirmed [{token}]")
    except Exception as e:
        print("❌ Confirm email error:", e)

    return _response_page(
        "✅ Meeting Confirmed!",
        f"A confirmation email with the Google Meet link and calendar invite has been sent to <strong>{meeting['name']}</strong> ({meeting['email']}) and to you.",
        "#e8f5e9", "#2e7d32"
    )


@app.route('/meeting/decline/<token>')
def decline_meeting(token):
    meeting = pending_meetings.get(token)

    if not meeting:
        return _response_page("❌ Invalid or Expired Link",
            "This link is no longer valid.", "#fce4ec", "#880e4f")

    if meeting.get('status') != 'pending':
        return _response_page("ℹ️ Already Processed",
            f"This meeting has already been {meeting.get('status')}.", "#e3f2fd", "#1565c0")

    meeting['status'] = 'declined'

    try:
        send_declined_email(meeting)
        print(f"❌ Meeting declined [{token}]")
    except Exception as e:
        print("❌ Decline email error:", e)

    return _response_page(
        "Meeting Declined",
        f"A polite decline email has been sent to <strong>{meeting['name']}</strong> ({meeting['email']}), letting them know to choose a different time.",
        "#fff8e1", "#b8860b"
    )


def _response_page(title, message, bg, color):
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="UTF-8">
      <meta name="viewport" content="width=device-width,initial-scale=1">
      <title>{title}</title>
      <style>
        * {{ margin:0; padding:0; box-sizing:border-box; }}
        body {{ font-family:'Segoe UI',Arial,sans-serif; background:#f5f5f5;
                display:flex; align-items:center; justify-content:center;
                min-height:100vh; padding:20px; }}
        .card {{ background:#fff; max-width:460px; width:100%;
                 border:1px solid #e8e8e8; padding:40px 36px; }}
        .badge {{ display:inline-block; padding:5px 14px; background:{bg};
                  color:{color}; font-size:12px; font-weight:700;
                  margin-bottom:18px; letter-spacing:0.5px; }}
        h1 {{ font-size:22px; color:#1a1a1a; margin-bottom:14px; }}
        p {{ font-size:14px; color:#555; line-height:1.7; margin-bottom:20px; }}
        a {{ color:#1a1a1a; font-size:14px; font-weight:700; text-decoration:none;
             padding:12px 24px; border:1.5px solid #1a1a1a; display:inline-block; }}
        a:hover {{ background:#1a1a1a; color:#fff; }}
      </style>
    </head>
    <body>
      <div class="card">
        <div class="badge">{title.split()[0]}</div>
        <h1>{title}</h1>
        <p>{message}</p>
        <a href="/">← Back to Portfolio</a>
      </div>
    </body>
    </html>
    """

# -------------------------------
# 5. RUN  ← always last
# -------------------------------
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)