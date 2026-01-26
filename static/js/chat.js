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
            
            // Report button for received messages
            const reportBtn = !msg.is_me ? `
                <button class="btn btn-link btn-sm text-muted p-0 ms-2 report-btn" onclick="openReportModal(${msg.id})" title="Report Message">
                    <i class="fas fa-flag"></i>
                </button>
            ` : '';

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
                        <div class="d-flex justify-content-between align-items-start">
                            <p class="mb-1">${msg.content}</p>
                            ${reportBtn}
                        </div>
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
