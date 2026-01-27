/**
 * File: chat.js
 * Purpose: Handles real-time messaging functionality
 * Author: to be assigned
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
                <div class="empty-chat-state text-center py-5">
                    <div class="icon-circle mb-3"><i class="fas fa-comments"></i></div>
                    <p class="text-muted">No messages yet. Start a conversation!</p>
                </div>
            `;
            return;
        }

        // Build HTML string for all messages
        const messagesHtml = messages.map(msg => {
            const sideClass = msg.is_me ? 'me' : 'other';
            
            // Flagged content warning
            const flaggedAlert = msg.is_flagged ? `
                <div class="flagged-warning">
                    <i class="fas fa-exclamation-triangle me-1"></i>
                    <small>Unkind language detected</small>
                </div>
            ` : '';

            // Translation box (if applicable)
            const translationBox = msg.translated_content ? `
                <div class="translation-text">
                    <i class="fas fa-language"></i> ${msg.translated_content}
                </div>
            ` : '';

            // Report button (only for received messages)
            const reportBtn = !msg.is_me ? `
                <button class="btn btn-link btn-sm text-muted p-0 ms-2 report-btn" onclick="openReportModal(${msg.id})" title="Report Message">
                    <i class="far fa-flag" style="font-size: 0.8rem;"></i>
                </button>
            ` : '';

            return `
                <div class="message-wrapper ${sideClass}">
                    <div class="message-bubble">
                        ${flaggedAlert}
                        <div class="content-text">${msg.content}</div>
                        ${translationBox}
                        <div class="d-flex justify-content-end align-items-center mt-1">
                            <div class="time-stamp mb-0">${msg.created_at}</div>
                            ${reportBtn}
                        </div>
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

