// 1. Grab the elements from the HTML
const trigger = document.getElementById('chatTrigger');
const popup = document.getElementById('chatPopup');
const closeBtn = document.getElementById('closeChatBtn');
const userInput = document.getElementById('userInput');
const sendBtn = document.getElementById('sendBtn');
const chatMessages = document.getElementById('chatMessages');

// 2. Function to toggle the window
trigger.addEventListener('click', () => {
    popup.classList.toggle('show');
});

// 3. Function to close the window
// Note: Ensure your HTML button has id="closeChatBtn"
if (closeBtn) {
    closeBtn.addEventListener('click', () => {
        popup.classList.remove('show');
    });
}

async function sendMessage() {
    const text = userInput.value.trim();
    if (text === "") return;

    // 1. Add User Message to UI
    appendMessage(text, 'user');
    userInput.value = '';

    // 2. Create a "Loading" bubble for the bot
    const loadingDiv = appendMessage("Typing...", 'bot');

    try {
        // 3. Call your Python Backend
        const response = await fetch("http://127.0.0.1:5000/chat", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ message: text })
        });

        const data = await response.json();

        // 4. Update the loading bubble with the real AI reply
        loadingDiv.textContent = data.reply;
    } catch (error) {
        loadingDiv.textContent = "Oops! My backend is offline. Make sure app.py is running.";
        console.error("Error:", error);
    }

    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Helper to create message bubbles
function appendMessage(text, side) {
    const msgDiv = document.createElement('div');
    msgDiv.className = `message ${side}`;
    msgDiv.textContent = text;
    chatMessages.appendChild(msgDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
    return msgDiv;
}

sendBtn.addEventListener('click', sendMessage);
userInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') sendMessage();
});