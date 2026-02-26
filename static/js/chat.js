/**
 * File: chat.js
 * Purpose: Handles real-time messaging functionality
 * Author: to be assigned
 * Date: January 2026
 * Description:
 *   - Receives new messages instantly via Socket.IO push
 *   - Loads initial message history via HTTP fetch on page open
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
    const editEndpointBase = `/${role}/api/messages`;

    // Socket.IO connection — server already joins user_{id} room on connect
    const socket = io();

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
     * Fetch messages from the server and update the UI.
     * Used for: initial history load, edit re-renders, language re-renders.
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

                if (messages.length > lastMessageCount || forceRender) {
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
     * Append a socket-pushed message bubble to the chat.
     * Uses msg.sender_id vs window._myId to determine side.
     */
    function appendSocketMessage(msg) {
        if (!chatMessages) return;

        // Remove empty-state placeholder if present
        const emptyState = chatMessages.querySelector('.empty-chat-state');
        if (emptyState) emptyState.remove();

        const isMe = msg.sender_id === window._myId;
        const sideClass = isMe ? 'me' : 'other';

        const flaggedAlert = msg.is_flagged ? `
            <div class="flagged-warning">
                <i class="fas fa-exclamation-triangle me-1"></i>
                <small>Unkind language detected</small>
            </div>
        ` : '';

        const replyQuoteHtml = msg.reply_preview ? `
            <div class="reply-quote">
                <span class="reply-quote-author">${escapeHtml(msg.reply_preview.author)}</span>
                <span class="reply-quote-content">${escapeHtml(msg.reply_preview.content)}</span>
            </div>
        ` : '';

        const reportBtn = !isMe ? `
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

        const editBtn = isMe
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

        const wrapper = document.createElement('div');
        wrapper.className = `message-wrapper ${sideClass}`;
        wrapper.setAttribute('data-msg-id', msg.id);
        wrapper.innerHTML = `
            ${actionsHtml}
            <div class="message-bubble">
                ${flaggedAlert}
                ${replyQuoteHtml}
                <div class="content-text">${msg.content}</div>
                <div class="d-flex justify-content-end align-items-center mt-1">
                    ${ttsBtn}
                    <div class="time-stamp mb-0">${msg.created_at}</div>
                    ${reportBtn}
                </div>
            </div>
        `;
        chatMessages.appendChild(wrapper);
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
     * Safely escape HTML to prevent XSS in user-supplied strings
     */
    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    // ── Socket listener for new buddy messages ────────────────────────────
    socket.on('new_buddy_message', function(msg) {
        appendSocketMessage(msg);
        lastMessageCount++;
        scrollToBottom();
    });

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
            // Emit via Socket.IO — server saves and echoes back via new_buddy_message
            socket.emit('buddy_message', {
                content: content,
                recipient_id: window._buddyId,
                reply_to_id: replyingTo ? replyingTo.id : null
            });

            // Clear input and cancel reply immediately
            messageInput.value = '';
            messageInput.style.height = 'auto';
            if (typeof autoExpand === 'function') autoExpand(messageInput);
            window.cancelReply();
        });
    }

    // Expose fetchMessages so the language switcher can trigger a refresh
    window.chatFetchMessages = function() {
        lastMessageCount = 0; // Force re-render
        return fetchMessages();
    };

    // Initial fetch to load history
    fetchMessages();

});
