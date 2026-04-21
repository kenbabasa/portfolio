// ── CHAT ──────────────────────────────────────────────────────
const trigger = document.getElementById('chatTrigger');
const popup = document.getElementById('chatPopup');
const closeChatBtn = document.getElementById('closeChatBtn');
const userInput = document.getElementById('userInput');
const sendBtn = document.getElementById('sendBtn');
const chatMessages = document.getElementById('chatMessages');

trigger.addEventListener('click', () => {
    popup.classList.toggle('show');
});

if (closeChatBtn) {
    closeChatBtn.addEventListener('click', () => {
        popup.classList.remove('show');
    });
}

async function sendMessage() {
    const text = userInput.value.trim();
    if (text === "") return;

    appendMessage(text, 'user');
    userInput.value = '';

    const loadingDiv = appendMessage("typing", 'bot');

    try {
        const response = await fetch("http://127.0.0.1:5000/chat", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ message: text })
        });
        const data = await response.json();
        loadingDiv.textContent = data.reply;
    } catch (error) {
        loadingDiv.textContent = "Oops! My backend is offline. Make sure app.py is running.";
        console.error("Error:", error);
    }

    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function appendMessage(text, side) {
    const msgDiv = document.createElement('div');
    msgDiv.className = `message ${side}`;

    if (side === 'bot') {
        if (text === 'typing') {
            msgDiv.innerHTML = `
                <img src="/static/images/ken.jpg" alt="Kennie" class="msg-avatar">
                <div class="bot-content">
                    <div class="typing-indicator">
                        <span></span><span></span><span></span>
                    </div>
                </div>`;
        } else {
            msgDiv.innerHTML = `
                <img src="/static/images/ken.jpg" alt="Kennie" class="msg-avatar">
                <div class="bot-content">
                    <span class="bot-name">Kennie</span>
                    <div class="msg-text">${text}</div>
                </div>`;
        }
    } else {
        msgDiv.innerHTML = `<div class="msg-text">${text}</div>`;
    }

    chatMessages.appendChild(msgDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
    return msgDiv.querySelector('.msg-text, .typing-indicator') || msgDiv;
}

sendBtn.addEventListener('click', sendMessage);
userInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') sendMessage();
});

const projectChatBtn = document.getElementById('projectChatBtn');
if (projectChatBtn) {
    projectChatBtn.addEventListener('click', () => {
        popup.classList.toggle('show');
        if (popup.classList.contains('show')) userInput.focus();
    });
}

// ── THEME ─────────────────────────────────────────────────────
const checkbox = document.getElementById('theme-checkbox');
const icon = document.getElementById('theme-icon');

const savedTheme = localStorage.getItem('theme');
if (savedTheme === 'dark') {
    document.documentElement.setAttribute('data-theme', 'dark');
    checkbox.checked = true;
    icon.textContent = '🌙';
} else {
    document.documentElement.removeAttribute('data-theme');
    checkbox.checked = false;
    icon.textContent = '☀️';
}

checkbox.addEventListener('change', () => {
    if (checkbox.checked) {
        document.documentElement.setAttribute('data-theme', 'dark');
        localStorage.setItem('theme', 'dark');
        icon.textContent = '🌙';
    } else {
        document.documentElement.removeAttribute('data-theme');
        localStorage.setItem('theme', 'light');
        icon.textContent = '☀️';
    }
});

// ── SCHEDULE MODAL ────────────────────────────────────────────
(function () {
    var modal = document.getElementById('scheduleModal');
    var schedBtn = document.getElementById('scheduleBtn');
    var closeSchedBtn = document.getElementById('closeScheduleModal');
    var nextBtn = document.getElementById('schedNextBtn');
    var backBtn = document.getElementById('schedBackBtn');
    var step1 = document.getElementById('schedStep1');
    var step2 = document.getElementById('schedStep2');

    // Set min date to today
    var today = new Date().toISOString().split('T')[0];
    document.getElementById('schedDate').min = today;
    document.getElementById('schedDate').value = today;

    function openModal() {
        modal.style.display = 'flex';
        document.body.style.overflow = 'hidden';
        step1.style.display = 'block';
        step2.style.display = 'none';
    }

    function closeModal() {
        modal.style.display = 'none';
        document.body.style.overflow = 'auto';
    }

    schedBtn.addEventListener('click', openModal);
    closeSchedBtn.addEventListener('click', closeModal);
    modal.addEventListener('click', function (e) {
        if (e.target === modal) closeModal();
    });

    backBtn.addEventListener('click', function () {
        step2.style.display = 'none';
        step1.style.display = 'block';
    });

    nextBtn.addEventListener('click', function () {
        var date = document.getElementById('schedDate').value;
        var time = document.getElementById('schedTime').value;
        if (!date || !time) { alert('Please fill in the date and time.'); return; }

        var name = document.getElementById('schedName').value.trim();
        var email = document.getElementById('schedEmail').value.trim();
        var dur = document.getElementById('schedDur').value;
        var topic = document.getElementById('schedTopic').value.trim() || 'Meeting with Kennie';

        function pad(n) { return String(n).padStart(2, '0'); }

        function toGDT(d, t) {
            return d.replace(/-/g, '') + 'T' + t.replace(':', '') + '00';
        }

        function addMins(d, t, m) {
            var dt = new Date(d + 'T' + t + ':00');
            dt.setMinutes(dt.getMinutes() + parseInt(m));
            return dt.getFullYear() + '' + pad(dt.getMonth() + 1) + '' + pad(dt.getDate()) +
                'T' + pad(dt.getHours()) + '' + pad(dt.getMinutes()) + '00';
        }

        function addMinsISO(d, t, m) {
            var dt = new Date(d + 'T' + t + ':00');
            dt.setMinutes(dt.getMinutes() + parseInt(m));
            return dt.toISOString().slice(0, 16);
        }

        var dtStart = toGDT(date, time);
        var dtEnd = addMins(date, time, dur);
        var dtEndISO = addMinsISO(date, time, dur);
        var enc = encodeURIComponent;
        var desc = "Scheduled via Kennie's portfolio." +
            (name ? ' Guest: ' + name : '') +
            (email ? ' Email: ' + email : '');

        // Google Calendar
        document.getElementById('gcalLink').href =
            'https://calendar.google.com/calendar/render?action=TEMPLATE' +
            '&text=' + enc(topic) +
            '&dates=' + dtStart + '/' + dtEnd +
            '&details=' + enc(desc) +
            '&location=' + enc('To be confirmed');

        // Outlook
        document.getElementById('outlookLink').href =
            'https://outlook.live.com/calendar/0/deeplink/compose' +
            '?subject=' + enc(topic) +
            '&startdt=' + date + 'T' + time + ':00' +
            '&enddt=' + dtEndISO +
            '&body=' + enc(desc) +
            '&path=%2Fcalendar%2Faction%2Fcompose';

        // Apple / iCal (.ics download)
        var ics = [
            'BEGIN:VCALENDAR',
            'VERSION:2.0',
            'PRODID:-//Kennie Portfolio//EN',
            'BEGIN:VEVENT',
            'DTSTART:' + dtStart,
            'DTEND:' + dtEnd,
            'SUMMARY:' + topic,
            'DESCRIPTION:' + desc,
            'LOCATION:To be confirmed',
            'END:VEVENT',
            'END:VCALENDAR'
        ].join('\r\n');
        var blob = new Blob([ics], { type: 'text/calendar' });
        document.getElementById('icsLink').href = URL.createObjectURL(blob);

        // Summary text
        var d = new Date(date + 'T' + time + ':00');
        var dateStr = d.toLocaleDateString('en-PH', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' });
        var timeStr = d.toLocaleTimeString('en-PH', { hour: '2-digit', minute: '2-digit' });
        document.getElementById('schedSummary').innerHTML =
            '<strong>' + topic + '</strong><br>' +
            dateStr + ' at ' + timeStr + ' (' + dur + ' min)' +
            (name ? '<br>Guest: ' + name : '');

        step1.style.display = 'none';
        step2.style.display = 'block';
    });
})();