let currentMode = null;
let sessionId = null;
let ws = null;
const clientId = Date.now().toString(); // Simple client ID generation

const landingPage = document.getElementById('landing-page');
const chatPage = document.getElementById('chat-page');
const chatTitle = document.getElementById('chat-title');
const chatArea = document.getElementById('chat-area');
const messageInput = document.getElementById('message-input');
const statusIndicator = document.getElementById('status-indicator');

function selectMode(mode) {
    currentMode = mode;
    landingPage.classList.remove('active');
    chatPage.classList.add('active');
    
    if (mode === 'ai') {
        chatTitle.innerText = 'AI Companion';
        sessionId = 'ai_session_' + clientId; // Unique session for AI chat
        statusIndicator.style.backgroundColor = '#3b82f6'; // Blue for AI
        loadHistory(sessionId);
    } else {
        chatTitle.innerText = 'Human Connect';
        sessionId = 'global_human_chat'; // Shared session for demo
        statusIndicator.style.backgroundColor = '#22c55e'; // Green for Online
        connectWebSocket();
        loadHistory(sessionId);
    }
}

function goBack() {
    chatPage.classList.remove('active');
    landingPage.classList.add('active');
    
    if (ws) {
        ws.close();
        ws = null;
    }
    currentMode = null;
    chatArea.innerHTML = ''; // Clear chat area
}

async function loadHistory(sid) {
    try {
        const response = await fetch(`/api/history/${sid}`);
        const messages = await response.json();
        chatArea.innerHTML = '';
        messages.forEach(msg => {
            addMessageToUI(msg.content, msg.sender === 'user' || msg.sender === `User ${clientId}` ? 'user' : 'other');
        });
        scrollToBottom();
    } catch (error) {
        console.error('Error loading history:', error);
    }
}

function connectWebSocket() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    ws = new WebSocket(`${protocol}//${window.location.host}/ws/${clientId}`);
    
    ws.onmessage = function(event) {
        // The server sends "User ID: message"
        const text = event.data;
        const parts = text.split(': ');
        if (parts.length > 1) {
            const sender = parts[0];
            const content = parts.slice(1).join(': ');
            // Don't show own messages again if we handled them optimistically (optional, but here we rely on broadcast for others)
            // Actually, for this simple implementation, let's just show everything that comes from WS
            // But we need to distinguish own messages.
            // The server broadcasts to everyone EXCEPT sender.
            // So if we receive it, it's from someone else.
            addMessageToUI(content, 'other');
            scrollToBottom();
        } else {
            // System message
            addMessageToUI(text, 'other');
            scrollToBottom();
        }
    };

    ws.onclose = function() {
        statusIndicator.style.backgroundColor = '#ef4444'; // Red for offline
    };
}

async function sendMessage() {
    const text = messageInput.value.trim();
    if (!text) return;

    // Add to UI immediately
    addMessageToUI(text, 'user');
    messageInput.value = '';
    scrollToBottom();

    if (currentMode === 'ai') {
        try {
            const response = await fetch('/api/chat/ai', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: text, session_id: sessionId })
            });
            const data = await response.json();
            addMessageToUI(data.response, 'other');
            scrollToBottom();
        } catch (error) {
            console.error('Error sending to AI:', error);
            addMessageToUI('Error communicating with AI.', 'other');
        }
    } else if (currentMode === 'human') {
        if (ws && ws.readyState === WebSocket.OPEN) {
            ws.send(text);
        } else {
            addMessageToUI('Connection lost. Reconnecting...', 'other');
            connectWebSocket();
        }
    }
}

function addMessageToUI(text, type) {
    const msgDiv = document.createElement('div');
    msgDiv.classList.add('message', type);
    msgDiv.innerText = text;
    chatArea.appendChild(msgDiv);
}

function scrollToBottom() {
    chatArea.scrollTop = chatArea.scrollHeight;
}

// Allow Enter key to send
messageInput.addEventListener('keypress', function(e) {
    if (e.key === 'Enter') {
        sendMessage();
    }
});
