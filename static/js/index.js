// ── CHAT ──────────────────────────────────────────────────────
const trigger      = document.getElementById('chatTrigger');
const popup        = document.getElementById('chatPopup');
const closeChatBtn = document.getElementById('closeChatBtn');
const userInput    = document.getElementById('userInput');
const sendBtn      = document.getElementById('sendBtn');
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

    userInput.disabled = true;
    sendBtn.disabled   = true;

    const loadingDiv = appendMessage("typing", 'bot');

    try {
        const response = await fetch("/chat", {  // ✅ relative URL — works on any IP
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ message: text })
        });

        const contentType = response.headers.get('content-type') || '';

        if (contentType.includes('text/plain')) {
            // ✅ Streaming: render tokens live as they arrive
            const reader  = response.body.getReader();
            const decoder = new TextDecoder();
            let fullText  = '';

            const botBubble = swapToBotBubble(loadingDiv);

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;
                fullText += decoder.decode(value, { stream: true });
                botBubble.textContent = fullText;
                chatMessages.scrollTop = chatMessages.scrollHeight;
            }

        } else {
            // ✅ JSON fallback: greeting message still returns JSON
            const data = await response.json();
            const botBubble = swapToBotBubble(loadingDiv);
            botBubble.textContent = data.reply;
        }

    } catch (error) {
        const botBubble = swapToBotBubble(loadingDiv);
        botBubble.textContent = "Oops! My backend is offline. Make sure app.py is running.";
        console.error("Error:", error);
    }

    userInput.disabled = false;
    sendBtn.disabled   = false;
    userInput.focus();
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Replaces typing indicator with a real bot bubble, returns the .msg-text element
function swapToBotBubble(typingDiv) {
    const msgDiv = typingDiv.closest('.message') || typingDiv.parentElement?.parentElement;
    msgDiv.innerHTML = `
        <img src="/static/images/ken.jpg" alt="Kennie" class="msg-avatar">
        <div class="bot-content">
            <div class="msg-text"></div>
        </div>`;
    return msgDiv.querySelector('.msg-text');
}

function appendMessage(text, side) {
    const msgDiv      = document.createElement('div');
    msgDiv.className  = `message ${side}`;

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
    return msgDiv.querySelector('.typing-indicator') || msgDiv.querySelector('.msg-text') || msgDiv;
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
const icon     = document.getElementById('theme-icon');

const savedTheme = localStorage.getItem('theme');
if (savedTheme === 'dark') {
    document.documentElement.setAttribute('data-theme', 'dark');
    checkbox.checked  = true;
    icon.textContent  = '🌙';
} else {
    document.documentElement.removeAttribute('data-theme');
    checkbox.checked  = false;
    icon.textContent  = '☀️';
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
    var modal     = document.getElementById('scheduleModal');
    var openBtn   = document.getElementById('scheduleBtn');
    var closeBtn  = document.getElementById('closeScheduleModal');
    var step1     = document.getElementById('schedStep1');
    var step1b    = document.getElementById('schedStep1b');
    var step2     = document.getElementById('schedStep2');
    var step3     = document.getElementById('schedStep3');

    var curYear, curMonth;
    var selectedDate = null, selectedTime = null;

    var MONTHS = ['January','February','March','April','May','June',
                  'July','August','September','October','November','December'];
    var SLOTS  = ['09:00','09:30','10:00','10:30','11:00','11:30',
                  '13:00','13:30','14:00','14:30','15:00','15:30','16:00','16:30','17:00'];

    var availabilityCache = {};
    var blockedMonthCache = {};

    async function fetchAvailability(date) {
        if (availabilityCache[date]) return availabilityCache[date];
        try {
            const res  = await fetch(`/api/availability?date=${date}`);  // ✅ relative URL
            const data = await res.json();
            availabilityCache[date] = data;
            return data;
        } catch (_) {
            return { day_blocked: false, range_blocks: [], booked_slots: [] };
        }
    }

    async function fetchBlockedMonth(year, month) {
        var key = year + '-' + String(month + 1).padStart(2, '0');
        if (blockedMonthCache[key]) return blockedMonthCache[key];
        try {
            const res  = await fetch(`/api/blocked-month?year=${year}&month=${month + 1}`);  // ✅ relative URL
            const data = await res.json();
            blockedMonthCache[key] = data.blocks || [];
            return blockedMonthCache[key];
        } catch (_) {
            return [];
        }
    }

    function toMin(timeStr) {
        var p = timeStr.split(':');
        return parseInt(p[0]) * 60 + parseInt(p[1]);
    }

    var tz      = Intl.DateTimeFormat().resolvedOptions().timeZone;
    var tzTime  = new Date().toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', timeZoneName: 'short' });
    var tzLabel = tz + ' (' + tzTime + ')';
    document.getElementById('calTzLabel').textContent  = tzLabel;
    document.getElementById('calTzLabel2').textContent = tzLabel;

    function showOnly(el) {
        [step1, step1b, step2, step3].forEach(function (s) { s.style.display = 'none'; });
        el.style.display = 'block';
    }

    function openModal() {
        var now  = new Date();
        curYear  = now.getFullYear();
        curMonth = now.getMonth();
        selectedDate = null;
        selectedTime = null;
        blockedMonthCache = {};
        availabilityCache = {};
        renderCalendar();
        showOnly(step1);
        modal.style.display          = 'flex';
        document.body.style.overflow = 'hidden';
    }

    function closeModal() {
        modal.style.display          = 'none';
        document.body.style.overflow = 'auto';
    }

    openBtn.addEventListener('click', openModal);
    closeBtn.addEventListener('click', closeModal);
    modal.addEventListener('click', function (e) { if (e.target === modal) closeModal(); });

    async function renderCalendar() {
        document.getElementById('calMonthLabel').textContent = MONTHS[curMonth] + ' ' + curYear;
        var tbody = document.getElementById('calBody');
        tbody.innerHTML = '';

        var today = new Date(); today.setHours(0, 0, 0, 0);
        var first = new Date(curYear, curMonth, 1).getDay();
        var days  = new Date(curYear, curMonth + 1, 0).getDate();
        var cells = [];
        for (var i = 0; i < first; i++) cells.push(null);
        for (var d = 1; d <= days; d++) cells.push(d);
        while (cells.length % 7 !== 0) cells.push(null);

        var monthBlocks     = await fetchBlockedMonth(curYear, curMonth);
        var wholeDayBlocked = new Set(
            monthBlocks
                .filter(function (b) { return b.time_from == null; })
                .map(function (b) { return b.date; })
        );

        for (var r = 0; r < cells.length / 7; r++) {
            var tr = document.createElement('tr');
            for (var c = 0; c < 7; c++) {
                var td  = document.createElement('td');
                var day = cells[r * 7 + c];
                if (day) {
                    var btn         = document.createElement('button');
                    btn.className   = 'cal-day';
                    btn.textContent = day;

                    var pad      = function (n) { return String(n).padStart(2, '0'); };
                    var dateStr  = curYear + '-' + pad(curMonth + 1) + '-' + pad(day);
                    var thisDate = new Date(curYear, curMonth, day);
                    thisDate.setHours(0, 0, 0, 0);

                    var isPast    = thisDate < today;
                    var isBlocked = wholeDayBlocked.has(dateStr);

                    if (isPast || isBlocked) {
                        btn.disabled = true;
                        if (isBlocked) {
                            btn.title                = 'Not available';
                            btn.style.textDecoration = 'line-through';
                            btn.style.opacity        = '0.35';
                        }
                    } else {
                        btn.classList.add('available');
                        if (thisDate.getTime() === today.getTime()) btn.classList.add('today');
                        if (selectedDate &&
                            selectedDate.getFullYear() === curYear &&
                            selectedDate.getMonth()    === curMonth &&
                            selectedDate.getDate()     === day) btn.classList.add('selected');

                        (function (y, m, dy, ds) {
                            btn.addEventListener('click', function () {
                                selectedDate = new Date(y, m, dy);
                                selectedTime = null;
                                delete availabilityCache[ds];
                                renderCalendar();
                                renderTimeSlots();
                                showOnly(step1b);
                            });
                        })(curYear, curMonth, day, dateStr);
                    }
                    td.appendChild(btn);
                }
                tr.appendChild(td);
            }
            tbody.appendChild(tr);
        }
    }

    document.getElementById('calPrev').addEventListener('click', function () {
        curMonth--;
        if (curMonth < 0) { curMonth = 11; curYear--; }
        blockedMonthCache = {};
        renderCalendar();
    });
    document.getElementById('calNext').addEventListener('click', function () {
        curMonth++;
        if (curMonth > 11) { curMonth = 0; curYear++; }
        blockedMonthCache = {};
        renderCalendar();
    });

    async function renderTimeSlots() {
        var pad  = function (n) { return String(n).padStart(2, '0'); };
        var y    = selectedDate.getFullYear();
        var mo   = pad(selectedDate.getMonth() + 1);
        var dy   = pad(selectedDate.getDate());
        var ds   = y + '-' + mo + '-' + dy;

        var label = selectedDate.toLocaleDateString('en-PH', { weekday: 'long', month: 'long', day: 'numeric' });
        document.getElementById('backToCalLabel').textContent = label;

        var container = document.getElementById('timeSlots');
        container.innerHTML = '<p style="font-size:13px;opacity:0.5;padding:8px 0;">Loading slots…</p>';

        var avail = await fetchAvailability(ds);
        container.innerHTML = '';

        var dur = parseInt(document.getElementById('schedDur').value, 10);

        SLOTS.forEach(function (slot) {
            var btn       = document.createElement('button');
            btn.className = 'time-slot-btn';
            var parts     = slot.split(':');
            var h         = parseInt(parts[0]);
            var mn        = parts[1];
            btn.textContent = (h % 12 || 12) + ':' + mn + ' ' + (h >= 12 ? 'PM' : 'AM');

            var slotStart     = toMin(slot);
            var slotEnd       = slotStart + dur;
            var isUnavailable = false;

            avail.booked_slots.forEach(function (bs) {
                var bStart = toMin(bs);
                var bEnd   = bStart + dur;
                if (slotStart < bEnd && slotEnd > bStart) isUnavailable = true;
            });

            avail.range_blocks.forEach(function (rb) {
                var bStart = toMin(rb.from);
                var bEnd   = toMin(rb.to);
                if (slotStart < bEnd && slotEnd > bStart) isUnavailable = true;
            });

            if (isUnavailable) {
                btn.disabled             = true;
                btn.style.opacity        = '0.35';
                btn.style.textDecoration = 'line-through';
                btn.title                = 'Already booked';
            } else {
                if (selectedTime === slot) btn.classList.add('selected');
                btn.addEventListener('click', function () {
                    selectedTime = slot;
                    renderTimeSlots();
                    showOnly(step2);
                });
            }
            container.appendChild(btn);
        });
    }

    document.getElementById('backToCalendar').addEventListener('click', function () { showOnly(step1); });
    document.getElementById('backToTime').addEventListener('click', function () { showOnly(step1b); });

    var schedDur = document.getElementById('schedDur');
    document.getElementById('sched-dur-label').textContent = schedDur.options[schedDur.selectedIndex].text;
    schedDur.addEventListener('change', function () {
        document.getElementById('sched-dur-label').textContent = this.options[this.selectedIndex].text;
        if (selectedDate) renderTimeSlots();
    });

    document.getElementById('schedConfirmBtn').addEventListener('click', function () {
        var name  = document.getElementById('schedName').value.trim();
        var email = document.getElementById('schedEmail').value.trim();
        if (!name)  { alert('Please enter your name.');  return; }
        if (!email) { alert('Please enter your email.'); return; }

        var topic = document.getElementById('schedTopic').value.trim() || 'Meeting with Kennie';
        var dur   = document.getElementById('schedDur').value;

        function pad(n) { return String(n).padStart(2, '0'); }
        var y       = selectedDate.getFullYear();
        var mo      = pad(selectedDate.getMonth() + 1);
        var dy      = pad(selectedDate.getDate());
        var dateStr = y + '-' + mo + '-' + dy;

        var h            = parseInt(selectedTime.split(':')[0]);
        var mn           = selectedTime.split(':')[1];
        var readableDate = selectedDate.toLocaleDateString('en-PH', {
            weekday: 'long', year: 'numeric', month: 'long', day: 'numeric'
        });
        document.getElementById('schedSummary').innerHTML =
            '<strong>' + topic + '</strong><br>' +
            readableDate + ' at ' + (h % 12 || 12) + ':' + mn + ' ' + (h >= 12 ? 'PM' : 'AM') +
            ' (' + dur + ' min)<br>Guest: ' + name;

        fetch('/schedule', {  // ✅ relative URL
            method:  'POST',
            headers: { 'Content-Type': 'application/json' },
            body:    JSON.stringify({
                name: name, email: email, date: dateStr,
                time: selectedTime, duration: dur, topic: topic
            })
        }).then(async function (res) {
            if (res.status === 409) {
                var data = await res.json();
                alert('⚠️ ' + (data.message || 'Time slot no longer available. Please pick another.'));
                delete availabilityCache[dateStr];
                renderTimeSlots();
                showOnly(step1b);
            }
        }).catch(function () {
            // Backend offline — guest already sees step3
        });

        showOnly(step3);
    });

})();