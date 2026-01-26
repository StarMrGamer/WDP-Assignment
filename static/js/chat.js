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

            return `
                <div class="message-wrapper ${sideClass}">
                    <div class="message-bubble">
                        ${flaggedAlert}
                        <div class="content-text">${msg.content}</div>
                        ${translationBox}
                        <div class="time-stamp">${msg.created_at}</div>
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

// ==================== REPORTING LOGIC ====================
// Defined globally to ensure onclick handlers work
window.openReportModal = function(messageId) {
    document.getElementById('reportMessageId').value = messageId;
    const modalEl = document.getElementById('reportModal');
    if (modalEl) {
        const modal = bootstrap.Modal.getOrCreateInstance(modalEl);
        modal.show();
    }
};

window.submitReport = async function() {
    const messageId = document.getElementById('reportMessageId').value;
    const reason = document.getElementById('reportReason').value;
    const description = document.getElementById('reportDescription').value;

    if (!reason) {
        alert('Please select a reason for reporting');
        return;
    }

    try {
        // Determine role from URL to use correct blueprint
        const role = window.location.pathname.split('/')[1]; 
        const response = await fetch(`/${role}/api/messages/${messageId}/report`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ reason, description })
        });

        if (response.ok) {
            alert('Report submitted successfully. Admins will review it.');
            const modalEl = document.getElementById('reportModal');
            const modal = bootstrap.Modal.getInstance(modalEl);
            if (modal) modal.hide();
            
            document.getElementById('reportForm').reset();
        } else {
            const data = await response.json();
            alert(data.message || 'Failed to submit report');
        }
    } catch (error) {
        console.error('Error submitting report:', error);
        alert('An error occurred while submitting the report');
    }
};
