/**
 * File: chat.js
 * Purpose: Handles real-time messaging functionality
 * Author: to be assigned
 * Date: January 2026
 * Description:
 *   - Polls the server for new messages every 3 seconds
 *   - Updates the chat UI dynamically without page reload
 *   - Auto-scrolls to the newest message
 *   - Supports reply and edit of messages
 */

document.addEventListener('DOMContentLoaded', function() {
    const chatMessages = document.getElementById('chatMessages');
    const messageForm = document.getElementById('messageForm');
    const messageInput = document.getElementById('messageInput');

    // Determine the API endpoint based on the current URL
    // If we are in /senior/messages, use /senior/api/messages
    // If we are in /youth/messages, use /youth/api/messages
    const role = window.location.pathname.split('/')[1]; // 'senior' or 'youth'
    const apiEndpoint = `/${role}/api/messages`;
    const postEndpoint = `/${role}/messages`;
    const editEndpointBase = `/${role}/api/messages`;

    let lastMessageCount = 0;
    let lastLang = localStorage.getItem('translationLanguage') || 'none';
    let forceRender = false;

    // ── Reply / Edit state ────────────────────────────────────────────────
    let replyingTo = null;   // { id, author, preview }
    let editingMsgId = null;

    window.startReply = function(msgId) {
        window.cancelEdit();
        const wrapper = document.querySelector(`.message-wrapper[data-msg-id="${msgId}"]`);
        if (!wrapper) return;
        const contentEl = wrapper.querySelector('.content-text');
        // In 1-on-1 chat there are no sender-name elements; determine author from bubble side
        const isMe = wrapper.classList.contains('me');
        const author = isMe
            ? (window._myName || 'You')
            : (window._buddyName || 'Buddy');
        const preview = contentEl ? contentEl.textContent.trim().substring(0, 80) : '';
        replyingTo = { id: msgId, author, preview };
        document.getElementById('reply-bar-author').textContent = author;
        document.getElementById('reply-bar-preview').textContent = preview;
        document.getElementById('reply-bar').classList.add('active');
        if (messageInput) messageInput.focus();
    };

    window.cancelReply = function() {
        replyingTo = null;
        const bar = document.getElementById('reply-bar');
        if (bar) bar.classList.remove('active');
        const inp = document.getElementById('replyToId');
        if (inp) inp.value = '';
    };

    window.startEdit = function(msgId) {
        window.cancelReply();
        const wrapper = document.querySelector(`.message-wrapper[data-msg-id="${msgId}"]`);
        if (!wrapper) return;
        const contentEl = wrapper.querySelector('.content-text');
        const raw = contentEl ? contentEl.textContent.trim() : '';
        editingMsgId = msgId;
        if (messageInput) {
            messageInput.value = raw;
            messageInput.removeAttribute('required');
            if (typeof autoExpand === 'function') autoExpand(messageInput);
            messageInput.focus();
        }
        document.getElementById('edit-bar').classList.add('active');
    };

    window.cancelEdit = function() {
        editingMsgId = null;
        const bar = document.getElementById('edit-bar');
        if (bar) bar.classList.remove('active');
        if (messageInput) {
            messageInput.value = '';
            messageInput.setAttribute('required', '');
        }
    };

    /**
     * Fetch messages from the server and update the UI
     */
    function fetchMessages() {
        const lang = localStorage.getItem('translationLanguage') || 'none';
        const url = apiEndpoint + '?lang=' + encodeURIComponent(lang);

        // Detect language change
        if (lang !== lastLang) {
            forceRender = true;
            lastLang = lang;
        }

        return fetch(url)
            .then(response => response.json())
            .then(data => {
                const messages = data.messages;

                if (messages.length !== lastMessageCount || forceRender) {
                    renderMessages(messages);
                    lastMessageCount = messages.length;
                    scrollToBottom();
                    forceRender = false;
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

            // Reply quote
            const replyQuoteHtml = msg.reply_preview ? `
                <div class="reply-quote">
                    <span class="reply-quote-author">${escapeHtml(msg.reply_preview.author)}</span>
                    <span class="reply-quote-content">${escapeHtml(msg.reply_preview.content)}</span>
                </div>
            ` : '';

            // Translation box (if applicable)
            const translationBox = msg.translated_content ? `
                <div class="translation-text">
                    <i class="fas fa-language"></i> ${msg.translated_content}
                </div>
            ` : '';

            // (edited) label
            const editedLabel = msg.edited_at ? `<span class="edited-label">(edited)</span>` : '';

            // Report button (only for received messages)
            const reportBtn = !msg.is_me ? `
                <button class="btn btn-link btn-sm text-muted p-0 ms-2 report-btn" onclick="openReportModal(${msg.id})" title="Report Message">
                    <i class="far fa-flag" style="font-size: 0.8rem;"></i>
                </button>
            ` : '';

            const ttsBtn = `
                <button class="btn btn-link btn-sm text-muted p-0 me-2 tts-btn"
                        onclick="toggleSpeak(this, this.closest('.message-bubble').querySelector('.translation-text')?.innerText || this.closest('.message-bubble').querySelector('.content-text').innerText, localStorage.getItem('translationLanguage') || 'en')"
                        title="Read aloud">
                    <i class="fas fa-volume-up" style="font-size: 0.8rem;"></i>
                </button>
            `;

            // Action buttons (reply for all, edit only for own)
            const editBtn = msg.is_me
                ? `<button class="msg-action-btn" title="Edit" onclick="window.startEdit(${msg.id})"><i class="fas fa-pencil-alt"></i></button>`
                : '';
            const actionsHtml = `
                <div class="message-actions">
                    <button class="msg-action-btn" title="Reply" onclick="window.startReply(${msg.id})">
                        <i class="fas fa-reply"></i>
                    </button>
                    ${editBtn}
                </div>
            `;

            return `
                <div class="message-wrapper ${sideClass}" data-msg-id="${msg.id}">
                    ${actionsHtml}
                    <div class="message-bubble">
                        ${flaggedAlert}
                        ${replyQuoteHtml}
                        <div class="content-text">${msg.content}</div>
                        ${translationBox}
                        <div class="d-flex justify-content-end align-items-center mt-1">
                            ${ttsBtn}
                            <div class="time-stamp mb-0">${msg.created_at}</div>
                            ${editedLabel}
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

    /**
     * Safely escape HTML to prevent XSS in optimistic messages
     */
    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    /**
     * Append a sent message to the chat immediately (optimistic UI)
     */
    function appendMyMessage(content, replyPreview) {
        if (!chatMessages) return;

        // Remove empty-state placeholder if present
        const emptyState = chatMessages.querySelector('.empty-chat-state');
        if (emptyState) emptyState.remove();

        const now = new Date();
        const timeStr = now.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });

        const replyHtml = replyPreview ? `
            <div class="reply-quote">
                <span class="reply-quote-author">${escapeHtml(replyPreview.author)}</span>
                <span class="reply-quote-content">${escapeHtml(replyPreview.preview)}</span>
            </div>
        ` : '';

        const wrapper = document.createElement('div');
        wrapper.className = 'message-wrapper me';
        wrapper.innerHTML = `
            <div class="message-bubble">
                ${replyHtml}
                <div class="content-text">${escapeHtml(content)}</div>
                <div class="d-flex justify-content-end align-items-center mt-1">
                    <button class="btn btn-link btn-sm text-muted p-0 me-2 tts-btn"
                            onclick="toggleSpeak(this, this.closest('.message-bubble').querySelector('.content-text').innerText, localStorage.getItem('translationLanguage') || 'en')"
                            title="Read aloud">
                        <i class="fas fa-volume-up" style="font-size: 0.8rem;"></i>
                    </button>
                    <div class="time-stamp mb-0">${timeStr}</div>
                </div>
            </div>
        `;
        chatMessages.appendChild(wrapper);
        scrollToBottom();

        // Keep lastMessageCount in sync so the next poll doesn't re-render
        lastMessageCount++;
    }

    // Handle Form Submission
    if (messageForm) {
        const sendBtn = messageForm.querySelector('[type="submit"]');

        messageForm.addEventListener('submit', function(e) {
            e.preventDefault();

            const content = messageInput.value.trim();
            if (!content) return;

            // ── Edit mode ────────────────────────────────────────────────
            if (editingMsgId) {
                if (sendBtn) sendBtn.disabled = true;

                fetch(`${editEndpointBase}/${editingMsgId}/edit`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-Requested-With': 'XMLHttpRequest'
                    },
                    body: JSON.stringify({ content })
                })
                .then(r => r.json())
                .then(() => {
                    messageInput.value = '';
                    messageInput.style.height = 'auto';
                    window.cancelEdit();
                    forceRender = true;
                    lastMessageCount = 0;
                    fetchMessages();
                })
                .catch(err => {
                    console.error('Error editing message:', err);
                    if (typeof showToast === 'function') showToast('Failed to edit message. Please try again.', 'danger');
                })
                .finally(() => {
                    if (sendBtn) sendBtn.disabled = false;
                });
                return;
            }

            // ── Send mode ────────────────────────────────────────────────
            // Prevent double-submit
            if (sendBtn) sendBtn.disabled = true;

            // Set reply_to_id hidden input before capturing FormData
            const replyInput = document.getElementById('replyToId');
            if (replyInput) replyInput.value = replyingTo ? replyingTo.id : '';

            // Capture form data BEFORE clearing input (includes CSRF token)
            const formData = new FormData(messageForm);

            // Snapshot reply context for optimistic bubble, then clear
            const currentReply = replyingTo ? { ...replyingTo } : null;

            // Clear input immediately for a responsive feel
            messageInput.value = '';
            messageInput.style.height = 'auto';
            if (typeof autoExpand === 'function') autoExpand(messageInput);

            // Show message instantly without waiting for server
            appendMyMessage(content, currentReply);
            window.cancelReply();

            // Send to server in background
            fetch(postEndpoint, {
                method: 'POST',
                body: formData,
                headers: { 'X-Requested-With': 'XMLHttpRequest' }
            })
            .then(response => {
                if (response.ok) return response.json();
                throw new Error('Failed to send message');
            })
            .then(data => {
                if (!data.success) {
                    console.error('Server rejected message');
                }
                // If flagged, force a re-render so the flagged warning appears
                if (data.flagged) {
                    if (typeof showToast === 'function') {
                        showToast('Your message was flagged for potentially unkind language.', 'warning');
                    }
                    forceRender = true;
                    lastMessageCount--;
                    fetchMessages();
                }
            })
            .catch(error => {
                console.error('Error sending message:', error);
                // Roll back the optimistic counter so the next poll re-renders
                // and removes the ghost bubble
                lastMessageCount--;
                if (typeof showToast === 'function') {
                    showToast('Failed to send message. Please try again.', 'danger');
                }
            })
            .finally(() => {
                if (sendBtn) sendBtn.disabled = false;
            });
        });
    }

    // Expose fetchMessages so the language switcher can trigger a refresh
    window.chatFetchMessages = function() {
        lastMessageCount = 0; // Force re-render
        return fetchMessages();
    };

    // Initial fetch
    fetchMessages();

    // Poll every 3 seconds for new messages
    setInterval(fetchMessages, 3000);

});
