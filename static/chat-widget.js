/**
 * Mantra Chat Widget - JavaScript
 * Handles chat interactions with the FastAPI backend
 */

(function() {
    'use strict';

    // Configuration
    const API_BASE_URL = window.location.origin;
    const CHAT_ENDPOINT = `${API_BASE_URL}/chat`;

    // DOM Elements
    const chatButton = document.getElementById('mantra-chat-button');
    const chatWindow = document.getElementById('mantra-chat-window');
    const closeButton = document.getElementById('close-chat');
    const chatMessages = document.getElementById('chat-messages');
    const chatInput = document.getElementById('chat-input');
    const sendButton = document.getElementById('send-button');

    // State
    let isOpen = false;
    let isProcessing = false;

    // Event Listeners
    chatButton.addEventListener('click', toggleChat);
    closeButton.addEventListener('click', toggleChat);
    sendButton.addEventListener('click', sendMessage);
    chatInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });

    /**
     * Toggle chat window open/closed
     */
    function toggleChat() {
        isOpen = !isOpen;
        chatWindow.classList.toggle('open', isOpen);

        if (isOpen) {
            chatInput.focus();
        }
    }

    /**
     * Send message to the backend
     */
    async function sendMessage() {
        const message = chatInput.value.trim();

        if (!message || isProcessing) {
            return;
        }

        // Clear input
        chatInput.value = '';

        // Add user message to chat
        addMessage(message, 'user');

        // Show typing indicator
        const typingIndicator = showTypingIndicator();

        // Disable input while processing
        isProcessing = true;
        sendButton.disabled = true;
        chatInput.disabled = true;

        try {
            // Call API
            const response = await fetch(CHAT_ENDPOINT, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ message })
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();

            // Remove typing indicator
            typingIndicator.remove();

            // Add bot response
            addMessage(data.message, 'bot', data.sources);

        } catch (error) {
            console.error('Error sending message:', error);

            // Remove typing indicator
            typingIndicator.remove();

            // Show error message
            addMessage(
                'Sorry, I encountered an error. Please try again or check if the server is running.',
                'bot'
            );
        } finally {
            // Re-enable input
            isProcessing = false;
            sendButton.disabled = false;
            chatInput.disabled = false;
            chatInput.focus();
        }
    }

    /**
     * Convert basic markdown to HTML
     */
    function parseMarkdown(text) {
        // Convert **bold** to <strong>bold</strong>
        let html = text.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');

        // Convert *italic* to <em>italic</em>
        html = html.replace(/\*(.+?)\*/g, '<em>$1</em>');

        // Preserve line breaks
        html = html.replace(/\n/g, '<br>');

        return html;
    }

    /**
     * Add a message to the chat
     */
    function addMessage(text, sender, sources = null) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `chat-message ${sender}`;

        const bubbleDiv = document.createElement('div');
        bubbleDiv.className = 'message-bubble';

        // Parse markdown for bot messages, plain text for user messages
        if (sender === 'bot') {
            bubbleDiv.innerHTML = parseMarkdown(text);
        } else {
            bubbleDiv.textContent = text;
        }

        messageDiv.appendChild(bubbleDiv);

        // Add sources if provided
        if (sources && sources.length > 0) {
            const sourcesDiv = document.createElement('div');
            sourcesDiv.className = 'message-sources';

            const sourcesTitle = document.createElement('div');
            sourcesTitle.textContent = '📚 Sources:';
            sourcesTitle.style.fontWeight = '600';
            sourcesTitle.style.marginBottom = '8px';
            sourcesDiv.appendChild(sourcesTitle);

            sources.forEach((source, index) => {
                const sourceItem = document.createElement('div');
                sourceItem.style.marginBottom = '4px';

                const sourceLink = document.createElement('a');
                sourceLink.href = source.url;
                sourceLink.target = '_blank';
                sourceLink.rel = 'noopener noreferrer';
                sourceLink.textContent = `${index + 1}. ${source.case_name} (${new Date(source.date).getFullYear()})`;

                sourceItem.appendChild(sourceLink);
                sourcesDiv.appendChild(sourceItem);
            });

            messageDiv.appendChild(sourcesDiv);
        }

        chatMessages.appendChild(messageDiv);
        scrollToBottom();
    }

    /**
     * Show typing indicator
     */
    function showTypingIndicator() {
        const messageDiv = document.createElement('div');
        messageDiv.className = 'chat-message bot';

        const bubbleDiv = document.createElement('div');
        bubbleDiv.className = 'message-bubble typing-indicator';

        for (let i = 0; i < 3; i++) {
            const dot = document.createElement('span');
            bubbleDiv.appendChild(dot);
        }

        messageDiv.appendChild(bubbleDiv);
        chatMessages.appendChild(messageDiv);
        scrollToBottom();

        return messageDiv;
    }

    /**
     * Scroll chat to bottom
     */
    function scrollToBottom() {
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    /**
     * Initialize widget
     */
    function init() {
        console.log('Mantra Chat Widget initialized');

        // Check if backend is healthy
        fetch(`${API_BASE_URL}/health`)
            .then(response => response.json())
            .then(data => {
                console.log('Backend health:', data);
                if (!data.index_loaded) {
                    console.warn('FAISS index not loaded');
                }
            })
            .catch(error => {
                console.error('Backend health check failed:', error);
            });
    }

    // Initialize on load
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

})();
