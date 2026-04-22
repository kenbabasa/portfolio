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

// schedule modal logic
(function () {
    var modal = document.getElementById('scheduleModal');
    var openBtn = document.getElementById('scheduleBtn');
    var closeBtn = document.getElementById('closeScheduleModal');
    var step1 = document.getElementById('schedStep1');
    var step1b = document.getElementById('schedStep1b');
    var step2 = document.getElementById('schedStep2');
    var step3 = document.getElementById('schedStep3');

    var curYear, curMonth;
    var selectedDate = null, selectedTime = null;

    var MONTHS = ['January', 'February', 'March', 'April', 'May', 'June',
        'July', 'August', 'September', 'October', 'November', 'December'];
    var SLOTS = ['09:00', '09:30', '10:00', '10:30', '11:00', '11:30',
        '13:00', '13:30', '14:00', '14:30', '15:00', '15:30', '16:00', '16:30', '17:00'];

    // Time zone
    var tz = Intl.DateTimeFormat().resolvedOptions().timeZone;
    var tzTime = new Date().toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', timeZoneName: 'short' });
    var tzLabel = tz + ' (' + tzTime + ')';
    document.getElementById('calTzLabel').textContent = tzLabel;
    document.getElementById('calTzLabel2').textContent = tzLabel;

    function showOnly(el) {
        [step1, step1b, step2, step3].forEach(function (s) { s.style.display = 'none'; });
        el.style.display = 'block';
    }

    function openModal() {
        var now = new Date();
        curYear = now.getFullYear();
        curMonth = now.getMonth();
        selectedDate = null; selectedTime = null;
        renderCalendar();
        showOnly(step1);
        modal.style.display = 'flex';
        document.body.style.overflow = 'hidden';
    }

    function closeModal() {
        modal.style.display = 'none';
        document.body.style.overflow = 'auto';
    }

    openBtn.addEventListener('click', openModal);
    closeBtn.addEventListener('click', closeModal);
    modal.addEventListener('click', function (e) { if (e.target === modal) closeModal(); });

    // Render calendar grid
    function renderCalendar() {
        document.getElementById('calMonthLabel').textContent = MONTHS[curMonth] + ' ' + curYear;
        var tbody = document.getElementById('calBody');
        tbody.innerHTML = '';
        var today = new Date(); today.setHours(0, 0, 0, 0);
        var first = new Date(curYear, curMonth, 1).getDay();
        var days = new Date(curYear, curMonth + 1, 0).getDate();
        var cells = [];
        for (var i = 0; i < first; i++) cells.push(null);
        for (var d = 1; d <= days; d++) cells.push(d);
        while (cells.length % 7 !== 0) cells.push(null);

        for (var r = 0; r < cells.length / 7; r++) {
            var tr = document.createElement('tr');
            for (var c = 0; c < 7; c++) {
                var td = document.createElement('td');
                var day = cells[r * 7 + c];
                if (day) {
                    var btn = document.createElement('button');
                    btn.className = 'cal-day';
                    btn.textContent = day;
                    var thisDate = new Date(curYear, curMonth, day);
                    thisDate.setHours(0, 0, 0, 0);
                    if (thisDate < today) {
                        btn.disabled = true;
                    } else {
                        btn.classList.add('available');
                        if (thisDate.getTime() === today.getTime()) btn.classList.add('today');
                        if (selectedDate &&
                            selectedDate.getFullYear() === curYear &&
                            selectedDate.getMonth() === curMonth &&
                            selectedDate.getDate() === day) btn.classList.add('selected');
                        (function (y, m, dy) {
                            btn.addEventListener('click', function () {
                                selectedDate = new Date(y, m, dy);
                                selectedTime = null;
                                renderCalendar();
                                renderTimeSlots();
                                showOnly(step1b);
                            });
                        })(curYear, curMonth, day);
                    }
                    td.appendChild(btn);
                }
                tr.appendChild(td);
            }
            tbody.appendChild(tr);
        }
    }

    document.getElementById('calPrev').addEventListener('click', function () {
        curMonth--; if (curMonth < 0) { curMonth = 11; curYear--; } renderCalendar();
    });
    document.getElementById('calNext').addEventListener('click', function () {
        curMonth++; if (curMonth > 11) { curMonth = 0; curYear++; } renderCalendar();
    });

    // Render time slots
    function renderTimeSlots() {
        var label = selectedDate.toLocaleDateString('en-PH', { weekday: 'long', month: 'long', day: 'numeric' });
        document.getElementById('backToCalLabel').textContent = label;
        var container = document.getElementById('timeSlots');
        container.innerHTML = '';
        SLOTS.forEach(function (slot) {
            var btn = document.createElement('button');
            btn.className = 'time-slot-btn';
            var parts = slot.split(':'), h = parseInt(parts[0]), mn = parts[1];
            btn.textContent = (h % 12 || 12) + ':' + mn + ' ' + (h >= 12 ? 'PM' : 'AM');
            if (selectedTime === slot) btn.classList.add('selected');
            btn.addEventListener('click', function () {
                selectedTime = slot;
                renderTimeSlots();
                showOnly(step2);
            });
            container.appendChild(btn);
        });
    }

    document.getElementById('backToCalendar').addEventListener('click', function () { showOnly(step1); });
    document.getElementById('backToTime').addEventListener('click', function () { showOnly(step1b); });

    // Duration label sync — set default label on load
    var schedDur = document.getElementById('schedDur');
    document.getElementById('sched-dur-label').textContent = schedDur.options[schedDur.selectedIndex].text;
    schedDur.addEventListener('change', function () {
        document.getElementById('sched-dur-label').textContent = this.options[this.selectedIndex].text;
    });

    // Confirm
    document.getElementById('schedConfirmBtn').addEventListener('click', function () {
        var name = document.getElementById('schedName').value.trim();
        var email = document.getElementById('schedEmail').value.trim();
        if (!name) { alert('Please enter your name.'); return; }
        if (!email) { alert('Please enter your email.'); return; }

        var topic = document.getElementById('schedTopic').value.trim() || 'Meeting with Kennie';
        var dur = document.getElementById('schedDur').value;

        function pad(n) { return String(n).padStart(2, '0'); }
        var y = selectedDate.getFullYear();
        var mo = pad(selectedDate.getMonth() + 1);
        var dy = pad(selectedDate.getDate());
        var dateStr = y + '-' + mo + '-' + dy;
        var dtStart = dateStr.replace(/-/g, '') + 'T' + selectedTime.replace(':', '') + '00';

        function addMins(ds, ts, m) {
            var dt = new Date(ds + 'T' + ts + ':00');
            dt.setMinutes(dt.getMinutes() + parseInt(m));
            return dt.getFullYear() + '' + pad(dt.getMonth() + 1) + '' + pad(dt.getDate()) +
                'T' + pad(dt.getHours()) + '' + pad(dt.getMinutes()) + '00';
        }
        function addMinsISO(ds, ts, m) {
            var dt = new Date(ds + 'T' + ts + ':00');
            dt.setMinutes(dt.getMinutes() + parseInt(m));
            return dt.toISOString().slice(0, 16);
        }

        var dtEnd = addMins(dateStr, selectedTime, dur);
        var dtEndISO = addMinsISO(dateStr, selectedTime, dur);
        var enc = encodeURIComponent;
        var desc = "Scheduled via Kennie's portfolio. Guest: " + name + (email ? ' (' + email + ')' : '');

        // Google Calendar — &add= sends YOU an invite so it appears on your phone
        document.getElementById('gcalLink').href =
            'https://calendar.google.com/calendar/render?action=TEMPLATE' +
            '&text=' + enc(topic) +
            '&dates=' + dtStart + '/' + dtEnd +
            '&details=' + enc(desc) +
            '&location=' + enc('Google Meet / To be confirmed') +
            '&add=' + enc('kennieangelo.estrellon_cyn@isu.edu.ph');

        // Outlook Calendar
        document.getElementById('outlookLink').href =
            'https://outlook.live.com/calendar/0/deeplink/compose?subject=' + enc(topic) +
            '&startdt=' + dateStr + 'T' + selectedTime + ':00' +
            '&enddt=' + dtEndISO +
            '&body=' + enc(desc) +
            '&path=%2Fcalendar%2Faction%2Fcompose';

        // Apple / iCal download
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
            'ORGANIZER;CN=Kennie Angelo Estrellon:MAILTO:kennieangelo.estrellon_cyn@isu.edu.ph',
            'ATTENDEE;CN=' + name + ':MAILTO:' + email,
            'END:VEVENT',
            'END:VCALENDAR'
        ].join('\r\n');
        document.getElementById('icsLink').href =
            URL.createObjectURL(new Blob([ics], { type: 'text/calendar' }));

        // Summary display
        var h = parseInt(selectedTime.split(':')[0]);
        var mn = selectedTime.split(':')[1];
        var readableDate = selectedDate.toLocaleDateString('en-PH', {
            weekday: 'long', year: 'numeric', month: 'long', day: 'numeric'
        });
        document.getElementById('schedSummary').innerHTML =
            '<strong>' + topic + '</strong><br>' +
            readableDate + ' at ' + (h % 12 || 12) + ':' + mn + ' ' + (h >= 12 ? 'PM' : 'AM') +
            ' (' + dur + ' min)<br>Guest: ' + name;

        // Notify backend (optional, fails silently if offline)
        fetch('http://127.0.0.1:5000/schedule', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name: name, email: email, date: dateStr, time: selectedTime, duration: dur, topic: topic })
        }).catch(function () { });

        showOnly(step3);
    });
})();
