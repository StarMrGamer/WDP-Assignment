/**
 * File: chat.js
 * Purpose: Handles real-time messaging functionality
 * Author: Rai (Team Lead)
 * Date: January 2026
 * Description: 
 *   - Polls the server for new messages every 3 seconds
 *   - Updates the chat UI dynamically without page reload
 *   - Auto-scrolls to the newest message
 */

document.addEventListener('DOMContentLoaded', function() {
    const chatMessages = document.getElementById('chatMessages');
    
    // Determine the API endpoint based on the current URL
    // If we are in /senior/messages, use /senior/api/messages
    // If we are in /youth/messages, use /youth/api/messages
    const role = window.location.pathname.split('/')[1]; // 'senior' or 'youth'
    const apiEndpoint = `/${role}/api/messages`;
    
    let lastMessageCount = 0;

    /**
     * Fetch messages from the server and update the UI
     */
    function fetchMessages() {
        fetch(apiEndpoint)
            .then(response => response.json())
            .then(data => {
                const messages = data.messages;
                
                // Only update if we have new messages or if it's the first load
                // This is a simple optimization. Ideally, we'd check IDs.
                if (messages.length !== lastMessageCount) {
                    renderMessages(messages);
                    lastMessageCount = messages.length;
                    scrollToBottom();
                }
            })
            .catch(error => console.error('Error fetching messages:', error));
    }

    /**
     * Render the list of messages into the chat container
     * @param {Array} messages - List of message objects from API
     */
    function renderMessages(messages) {
        if (!chatMessages) return;
        
        if (messages.length === 0) {
            chatMessages.innerHTML = `
                <div class="text-center py-5 text-muted">
                    <i class="fas fa-comments fa-3x mb-3"></i>
                    <p>No messages yet. Start a conversation!</p>
                </div>
            `;
            return;
        }

        // Build HTML string for all messages
        const messagesHtml = messages.map(msg => {
            const messageClass = msg.is_me ? 'message-sent' : 'message-received';
            const checkIcon = msg.is_me ? '<i class="fas fa-check-double text-primary"></i>' : '';
            
            // Flagged content warning
            const flaggedAlert = msg.is_flagged ? `
                <div class="alert alert-warning alert-sm mb-2">
                    <i class="fas fa-exclamation-triangle me-2"></i>
                    <small>This message contains potentially unkind language</small>
                </div>
            ` : '';

            // Translation box (if applicable)
            const translationBox = msg.translated_content ? `
                <div class="translation-box mt-2">
                    <small class="text-muted">
                        <i class="fas fa-language me-1"></i>
                        Translation:
                    </small>
                    <p class="mb-0">${msg.translated_content}</p>
                </div>
            ` : '';

            return `
                <div class="message ${messageClass}">
                    <div class="message-content">
                        ${flaggedAlert}
                        <p class="mb-1">${msg.content}</p>
                        ${translationBox}
                        <small class="message-time">
                            ${msg.created_at}
                            ${checkIcon}
                        </small>
                    </div>
                </div>
            `;
        }).join('');

        chatMessages.innerHTML = messagesHtml;
    }

    /**
     * Scroll the chat container to the bottom to show latest messages
     */
    function scrollToBottom() {
        if (chatMessages) {
            chatMessages.scrollTop = chatMessages.scrollHeight;
        }
    }

    // Initial fetch
    fetchMessages();

    // Poll every 3 seconds for new messages
    setInterval(fetchMessages, 3000);
});
