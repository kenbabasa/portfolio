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
if(closeBtn) {
    closeBtn.addEventListener('click', () => {
        popup.classList.remove('show');
    });
}

// 4. Basic Send Logic (So it's not just a static window)
function sendMessage() {
    const text = userInput.value.trim();
    if (text !== "") {
        // Add User Message
        const userDiv = document.createElement('div');
        userDiv.className = 'message user';
        userDiv.textContent = text;
        chatMessages.appendChild(userDiv);
        
        userInput.value = ''; // Clear input
        
        // Simple Bot Auto-Reply
        setTimeout(() => {
            const botDiv = document.createElement('div');
            botDiv.className = 'message bot';
            botDiv.textContent = "Thanks for messaging! I'll get back to you soon.";
            chatMessages.appendChild(botDiv);
            chatMessages.scrollTop = chatMessages.scrollHeight;
        }, 1000);
    }
}

sendBtn.addEventListener('click', sendMessage);
userInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') sendMessage();
});