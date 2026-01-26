/*
    File: main.js
    Purpose: Global JavaScript utilities for GenCon SG application
    Author: to be assigned
    Date: December 2025
    Description: This file contains:
                 - Accessibility functions (font size, contrast, themes)
                 - Notification system management
                 - Streak and badge handling
                 - Modal utilities
                 - Form validation helpers
                 - Common UI interactions
                 - AJAX/Fetch utilities
*/

// ==================== ACCESSIBILITY FUNCTIONS ====================

/**
 * Set font size for senior users
 * @param {string} size - 'normal', 'large', or 'xlarge'
 * Stores preference in localStorage and applies to body element
 */
function setFontSize(size) {
    // Validate size parameter
    const validSizes = ['normal', 'large', 'xlarge'];
    if (!validSizes.includes(size)) {
        console.error('Invalid font size:', size);
        return;
    }

    // Apply font size to body element
    document.body.setAttribute('data-font-size', size);

    // Store preference in localStorage for persistence
    localStorage.setItem('fontSize', size);

    // Visual feedback
    showToast(`Font size changed to ${size}`, 'success');
}

/**
 * Toggle high contrast mode for senior users
 * Improves visibility with black background and white text
 */
function toggleHighContrast() {
    const body = document.body;
    const currentMode = body.getAttribute('data-high-contrast') === 'true';

    // Toggle the attribute
    body.setAttribute('data-high-contrast', !currentMode);

    // Store preference
    localStorage.setItem('highContrast', !currentMode);

    // Update checkbox state
    const checkbox = document.getElementById('highContrastToggle');
    if (checkbox) {
        checkbox.checked = !currentMode;
    }

    showToast(`High contrast mode ${!currentMode ? 'enabled' : 'disabled'}`, 'info');
}

/**
 * Set theme for youth users
 * @param {string} theme - 'light', 'dark', 'blue', or 'purple'
 * Applies theme to body and stores preference
 */
function setTheme(theme) {
    const validThemes = ['light', 'dark', 'blue', 'purple'];
    if (!validThemes.includes(theme)) {
        console.error('Invalid theme:', theme);
        return;
    }

    // Apply theme
    document.body.setAttribute('data-theme', theme);

    // Store preference
    localStorage.setItem('theme', theme);

    // Update active state in theme selector
    document.querySelectorAll('.theme-option').forEach(option => {
        option.classList.remove('active');
    });
    const selectedOption = document.querySelector(`.theme-option.${theme}`);
    if (selectedOption) {
        selectedOption.classList.add('active');
    }

    showToast(`Theme changed to ${theme}`, 'success');
}

/**
 * Load saved accessibility preferences on page load
 * Restores font size, contrast mode, and theme from localStorage
 */
function loadAccessibilityPreferences() {
    // Load font size preference (seniors)
    const savedFontSize = localStorage.getItem('fontSize');
    if (savedFontSize) {
        document.body.setAttribute('data-font-size', savedFontSize);
    }

    // Load high contrast preference (seniors)
    const savedHighContrast = localStorage.getItem('highContrast') === 'true';
    if (savedHighContrast) {
        document.body.setAttribute('data-high-contrast', 'true');
        const checkbox = document.getElementById('highContrastToggle');
        if (checkbox) checkbox.checked = true;
    }

    // Load theme preference (youth)
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme) {
        document.body.setAttribute('data-theme', savedTheme);
    }
}

// ==================== NOTIFICATION SYSTEM ====================

/**
 * Load event notifications for seniors and youth
 * Fetches upcoming events (within 7 days) and displays in notification dropdown
 */
async function loadNotifications() {
    try {
        // Fetch notifications from backend
        const response = await fetch('/api/notifications');
        const data = await response.json();

        // Update badge count
        const badge = document.getElementById('notificationBadge');
        if (badge) {
            badge.textContent = data.count;
            badge.style.display = data.count > 0 ? 'inline' : 'none';
        }

        // Update notification list
        const listElement = document.getElementById('notificationList');
        if (listElement && data.notifications) {
            if (data.notifications.length === 0) {
                listElement.innerHTML = '<p class="text-muted text-center py-3 mb-0">No new notifications</p>';
            } else {
                listElement.innerHTML = data.notifications.map(notif => `
                    <li>
                        <a class="dropdown-item notification-item" href="${notif.link || '#'}" data-notif-id="${notif.id}">
                            <div class="d-flex justify-content-between align-items-start">
                                <div>
                                    <strong>${notif.title}</strong>
                                    <p class="mb-0 small text-muted">${notif.message}</p>
                                    <small class="text-muted">${notif.timeAgo}</small>
                                </div>
                                <button class="btn btn-sm btn-link" onclick="event.preventDefault(); event.stopPropagation(); dismissNotification(${notif.id})">
                                    <i class="fas fa-times"></i>
                                </button>
                            </div>
                        </a>
                    </li>
                `).join('');
            }
        }
    } catch (error) {
        console.error('Error loading notifications:', error);
    }
}

/**
 * Dismiss a notification
 * @param {number} notificationId - ID of notification to dismiss
 */
async function dismissNotification(notificationId) {
    try {
        await fetch(`/api/notifications/${notificationId}/dismiss`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });

        // Reload notifications
        await loadNotifications();

        showToast('Notification dismissed', 'success');
    } catch (error) {
        console.error('Error dismissing notification:', error);
        showToast('Failed to dismiss notification', 'danger');
    }
}

// ==================== STREAK MANAGEMENT ====================

/**
 * Load and display user's current streak
 * Updates the streak counter in navigation bar
 */
async function loadStreak() {
    try {
        const response = await fetch('/api/streak');
        const data = await response.json();

        const streakElement = document.getElementById('streakCount');
        if (streakElement) {
            streakElement.textContent = data.currentStreak || 0;
        }

        // Check if user just earned a badge
        if (data.newBadge) {
            showBadgeModal(data.newBadge);
        }

        // Check if it's a daily reward
        if (data.dailyReward) {
            showDailyRewardModal(data.currentStreak);
        }
    } catch (error) {
        console.error('Error loading streak:', error);
    }
}

/**
 * Show badge earned modal
 * @param {object} badge - Badge object with name, description, icon
 */
function showBadgeModal(badge) {
    const modal = document.createElement('div');
    modal.className = 'modal-backdrop';
    modal.innerHTML = `
        <div class="modal fade-in">
            <div class="modal-header">
                <h3 class="modal-title">🎉 New Badge Earned!</h3>
                <button class="modal-close" onclick="this.closest('.modal-backdrop').remove()">×</button>
            </div>
            <div class="modal-body text-center">
                <div style="font-size: 5rem; margin: 1rem 0;">${badge.icon}</div>
                <h4>${badge.name}</h4>
                <p class="text-muted">${badge.description}</p>
                <button class="btn btn-primary mt-3" onclick="this.closest('.modal-backdrop').remove()">
                    Awesome!
                </button>
            </div>
        </div>
    `;
    document.body.appendChild(modal);
}

/**
 * Show daily reward modal for streak continuation
 * @param {number} streakDays - Number of consecutive days
 */
function showDailyRewardModal(streakDays) {
    const modal = document.createElement('div');
    modal.className = 'modal-backdrop';
    modal.innerHTML = `
        <div class="modal fade-in">
            <div class="modal-header">
                <h3 class="modal-title">🔥 Daily Streak!</h3>
                <button class="modal-close" onclick="this.closest('.modal-backdrop').remove()">×</button>
            </div>
            <div class="modal-body text-center">
                <div style="font-size: 5rem; margin: 1rem 0;">🔥</div>
                <h4>${streakDays} Day Streak!</h4>
                <p class="text-muted">Keep coming back every day to maintain your streak!</p>
                <p><strong>+${streakDays * 10} Points Earned</strong></p>
                <button class="btn btn-primary mt-3" onclick="this.closest('.modal-backdrop').remove()">
                    Continue
                </button>
            </div>
        </div>
    `;
    document.body.appendChild(modal);
}

// ==================== TOAST NOTIFICATIONS ====================

/**
 * Show toast notification
 * @param {string} message - Message to display
 * @param {string} type - 'success', 'danger', 'warning', 'info'
 * @param {string|null} actionLink - URL to redirect to on click (optional)
 * @param {string} actionText - Text for the action button (optional)
 */
function showToast(message, type = 'info', actionLink = null, actionText = 'View') {
    // Create toast element
    const toast = document.createElement('div');
    toast.className = `alert alert-${type} toast-notification fade-in`;
    toast.style.cssText = `
        position: fixed;
        top: 80px;
        right: 20px;
        z-index: 9999;
        min-width: 300px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        cursor: ${actionLink ? 'pointer' : 'default'};
    `;

    // Add icon based on type
    let icon = '';
    switch(type) {
        case 'success': icon = '<i class="fas fa-check-circle me-2"></i>'; break;
        case 'danger': icon = '<i class="fas fa-exclamation-circle me-2"></i>'; break;
        case 'warning': icon = '<i class="fas fa-exclamation-triangle me-2"></i>'; break;
        default: icon = '<i class="fas fa-info-circle me-2"></i>';
    }

    let actionButton = '';
    if (actionLink) {
        actionButton = `<a href="${actionLink}" class="btn btn-sm btn-light ms-3" style="text-decoration:none; color:inherit; font-weight:bold;">${actionText}</a>`;
        // Make the whole toast clickable if it's a link, except the close button
        toast.onclick = function(e) {
            if (e.target.tagName !== 'BUTTON' && e.target.tagName !== 'A') {
                window.location.href = actionLink;
            }
        };
    }

    toast.innerHTML = `
        <div class="d-flex justify-content-between align-items-center">
            <div>${icon}${message}</div>
            ${actionButton}
            <button type="button" class="btn-close ms-2" onclick="this.closest('.alert').remove(); event.stopPropagation();"></button>
        </div>
    `;

    document.body.appendChild(toast);

    // Auto-remove after 5 seconds (slightly longer for interactive toasts)
    const duration = actionLink ? 6000 : 4000;
    setTimeout(() => {
        if (document.body.contains(toast)) {
            toast.style.opacity = '0';
            setTimeout(() => { 
                if (document.body.contains(toast)) toast.remove(); 
            }, 300);
        }
    }, duration);
}

// ==================== FORM VALIDATION ====================

/**
 * Validate email format
 * @param {string} email - Email address to validate
 * @returns {boolean} - True if valid email format
 */
function validateEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
}

/**
 * Validate password strength
 * @param {string} password - Password to validate
 * @returns {object} - {valid: boolean, message: string, strength: string}
 */
function validatePassword(password) {
    const minLength = 8;
    const hasUpperCase = /[A-Z]/.test(password);
    const hasLowerCase = /[a-z]/.test(password);
    const hasNumber = /\d/.test(password);
    const hasSpecialChar = /[!@#$%^&*(),.?":{}|<>]/.test(password);

    if (password.length < minLength) {
        return { valid: false, message: 'Password must be at least 8 characters', strength: 'weak' };
    }

    let strength = 'weak';
    let strengthCount = 0;

    if (hasUpperCase) strengthCount++;
    if (hasLowerCase) strengthCount++;
    if (hasNumber) strengthCount++;
    if (hasSpecialChar) strengthCount++;

    if (strengthCount === 4) strength = 'strong';
    else if (strengthCount >= 2) strength = 'medium';

    return {
        valid: strengthCount >= 2,
        message: strengthCount >= 2 ? 'Password is acceptable' : 'Password should include uppercase, lowercase, numbers',
        strength: strength
    };
}

/**
 * Update password strength indicator
 * @param {string} password - Password to check
 * @param {string} indicatorId - ID of the indicator element
 */
function updatePasswordStrength(password, indicatorId) {
    const result = validatePassword(password);
    const indicator = document.getElementById(indicatorId);

    if (!indicator) return;

    // Update indicator color and text
    indicator.className = `password-strength ${result.strength}`;
    indicator.textContent = result.strength.charAt(0).toUpperCase() + result.strength.slice(1);

    // Update colors
    if (result.strength === 'strong') {
        indicator.style.color = '#28A745';
    } else if (result.strength === 'medium') {
        indicator.style.color = '#FFC107';
    } else {
        indicator.style.color = '#DC3545';
    }
}

/**
 * Validate age based on user role
 * @param {number} age - Age to validate
 * @param {string} role - 'senior' or 'youth'
 * @returns {object} - {valid: boolean, message: string}
 */
function validateAge(age, role) {
    if (role === 'senior' && age < 60) {
        return { valid: false, message: 'Seniors must be 60 years or older' };
    }
    if (role === 'youth' && age < 13) {
        return { valid: false, message: 'Youth volunteers must be 13 years or older' };
    }
    if (role === 'youth' && age >= 60) {
        return { valid: false, message: 'Please select the Senior role if you are 60 or older' };
    }
    return { valid: true, message: 'Age is valid' };
}

// ==================== MODAL UTILITIES ====================

/**
 * Show confirmation modal
 * @param {string} title - Modal title
 * @param {string} message - Confirmation message
 * @param {function} onConfirm - Callback function when confirmed
 */
function showConfirmModal(title, message, onConfirm) {
    const modal = document.createElement('div');
    modal.className = 'modal-backdrop';
    modal.innerHTML = `
        <div class="modal">
            <div class="modal-header">
                <h3 class="modal-title">${title}</h3>
            </div>
            <div class="modal-body">
                <p>${message}</p>
            </div>
            <div class="modal-footer">
                <button class="btn btn-secondary" onclick="this.closest('.modal-backdrop').remove()">
                    Cancel
                </button>
                <button class="btn btn-danger" id="confirmBtn">
                    Confirm
                </button>
            </div>
        </div>
    `;

    document.body.appendChild(modal);

    // Add event listener to confirm button
    document.getElementById('confirmBtn').addEventListener('click', () => {
        onConfirm();
        modal.remove();
    });
}

// ==================== AJAX UTILITIES ====================

/**
 * Generic AJAX POST request
 * @param {string} url - API endpoint
 * @param {object} data - Data to send
 * @returns {Promise} - Promise with response data
 */
async function postData(url, data) {
    try {
        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        return await response.json();
    } catch (error) {
        console.error('POST request failed:', error);
        throw error;
    }
}

/**
 * Generic AJAX GET request
 * @param {string} url - API endpoint
 * @returns {Promise} - Promise with response data
 */
async function getData(url) {
    try {
        const response = await fetch(url);

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        return await response.json();
    } catch (error) {
        console.error('GET request failed:', error);
        throw error;
    }
}

// ==================== IMAGE UPLOAD PREVIEW ====================

/**
 * Preview uploaded image before submission
 * @param {HTMLInputElement} input - File input element
 * @param {string} previewElementId - ID of element to show preview
 */
function previewImage(input, previewElementId) {
    const file = input.files[0];
    const preview = document.getElementById(previewElementId);

    if (!file || !preview) return;

    // Validate file type
    const validTypes = ['image/jpeg', 'image/png', 'image/gif'];
    if (!validTypes.includes(file.type)) {
        showToast('Please upload a valid image (JPG, PNG, or GIF)', 'danger');
        input.value = '';
        return;
    }

    // Validate file size (max 5MB)
    const maxSize = 5 * 1024 * 1024; // 5MB in bytes
    if (file.size > maxSize) {
        showToast('Image size must be less than 5MB', 'danger');
        input.value = '';
        return;
    }

    // Create preview
    const reader = new FileReader();
    reader.onload = function(e) {
        preview.src = e.target.result;
        preview.style.display = 'block';
    };
    reader.readAsDataURL(file);
}

// ==================== TIME FORMATTING ====================

/**
 * Format date to relative time (e.g., "2 hours ago")
 * @param {Date|string} date - Date to format
 * @returns {string} - Formatted relative time
 */
function formatTimeAgo(date) {
    const now = new Date();
    const past = new Date(date);
    const diffInSeconds = Math.floor((now - past) / 1000);

    if (diffInSeconds < 60) return 'Just now';
    if (diffInSeconds < 3600) return `${Math.floor(diffInSeconds / 60)} minutes ago`;
    if (diffInSeconds < 86400) return `${Math.floor(diffInSeconds / 3600)} hours ago`;
    if (diffInSeconds < 604800) return `${Math.floor(diffInSeconds / 86400)} days ago`;

    return past.toLocaleDateString();
}

/**
 * Format countdown for upcoming events
 * @param {Date|string} eventDate - Event date
 * @returns {string} - Countdown text (e.g., "in 3 days")
 */
function formatCountdown(eventDate) {
    const now = new Date();
    const event = new Date(eventDate);
    const diffInDays = Math.floor((event - now) / (1000 * 60 * 60 * 24));

    if (diffInDays === 0) return 'Today';
    if (diffInDays === 1) return 'Tomorrow';
    if (diffInDays < 7) return `in ${diffInDays} days`;

    return event.toLocaleDateString();
}

// ==================== INITIALIZATION ====================

/**
 * Initialize all features when DOM is fully loaded
 */
document.addEventListener('DOMContentLoaded', function() {
    // Load accessibility preferences
    loadAccessibilityPreferences();

    // Fix navbar profile picture display
    fixNavbarProfile();

    // Load notifications (if user is logged in)
    const notificationBadge = document.getElementById('notificationBadge');
    if (notificationBadge) {
        loadNotifications();
        
        // Clear badge on dropdown open
        const dropdownToggle = document.getElementById('notificationDropdown');
        if (dropdownToggle) {
            dropdownToggle.addEventListener('show.bs.dropdown', function () {
                // Visual clear
                notificationBadge.textContent = '0';
                notificationBadge.style.display = 'none';
                
                // Server-side mark as read
                fetch('/api/notifications/mark-read', { method: 'POST' })
                    .catch(err => console.error('Error marking notifications as read:', err));
            });
        }
    }

    // Load streak data (if user is logged in)
    const streakCount = document.getElementById('streakCount');
    if (streakCount) {
        loadStreak();
    }

    // Add active class to current nav link
    const currentPath = window.location.pathname;
    document.querySelectorAll('.nav-link').forEach(link => {
        if (link.getAttribute('href') === currentPath) {
            link.classList.add('active');
        }
    });

    // Initialize tooltips (if Bootstrap tooltips are used)
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    if (typeof bootstrap !== 'undefined' && bootstrap.Tooltip) {
        tooltipTriggerList.map(function (tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    }

    console.log('GenCon SG initialized successfully');
});

/**
 * Initialize Socket.IO notification listener
 * @param {object} socket - Socket.IO instance
 */
window.initNotificationSocket = function(socket) {
    if (!socket) return;

    socket.on('new_notification', function(data) {
        console.log('New notification received:', data);

        // Update badge count
        const badge = document.getElementById('notificationBadge');
        if (badge) {
            let count = parseInt(badge.textContent) || 0;
            count++;
            badge.textContent = count;
            badge.style.display = 'inline';
            badge.classList.add('pulse'); // Add animation
            setTimeout(() => badge.classList.remove('pulse'), 2000);
        }

        // Add to list
        const listElement = document.getElementById('notificationList');
        if (listElement) {
            // Remove "No new notifications" message if it exists
            const noNotifMsg = listElement.querySelector('.text-muted.text-center');
            if (noNotifMsg && listElement.children.length === 1) {
                noNotifMsg.remove();
            }

            // Create new item
            const li = document.createElement('li');
            li.innerHTML = `
                <a class="dropdown-item notification-item slide-up" href="${data.link || '#'}" data-notif-id="${data.id}">
                    <div class="d-flex justify-content-between align-items-start">
                        <div>
                            <strong>${data.title}</strong>
                            <p class="mb-0 small text-muted">${data.message}</p>
                            <small class="text-muted">${data.timeAgo}</small>
                        </div>
                        <button class="btn btn-sm btn-link" onclick="event.preventDefault(); event.stopPropagation(); dismissNotification(${data.id})">
                            <i class="fas fa-times"></i>
                        </button>
                    </div>
                </a>
            `;
            
            // Prepend to list
            listElement.insertBefore(li, listElement.firstChild);
        }

        // Show toast
        showToast(data.title + ': ' + data.message, 'info', data.link);
    });
};

/**
 * Fix navbar profile picture display and styling
 * Ensures circle shape, proper object fit, and spacing from name
 * Also handles broken image links due to path issues
 */
function fixNavbarProfile() {
    // Target profile pictures in navbar/header
    // We look for images that are likely user avatars (small, rounded)
    const navImages = document.querySelectorAll('.navbar img, nav img, header img');
    
    navImages.forEach(img => {
        // Apply styling if it looks like a profile pic (or just apply to all small nav images)
        if (img.classList.contains('rounded-circle') || (img.width > 0 && img.width < 60)) {
            img.style.width = '40px';
            img.style.height = '40px';
            img.style.objectFit = 'cover';
            img.style.borderRadius = '50%';
            img.style.marginRight = '10px'; // Padding so it doesn't overlap with name
            
            // Handle broken image paths
            img.onerror = function() {
                const src = this.src;
                if (src.includes('images/images/')) {
                    this.src = src.replace('images/images/', 'images/');
                } else if (!src.includes('images/') && src.includes('/static/')) {
                    this.src = src.replace('/static/', '/static/images/');
                } else {
                    this.src = '/static/images/default-avatar.png';
                }
            };
            
            // Check immediately
            if (img.complete && img.naturalWidth === 0) {
                img.onerror();
            }
        }
    });
}

// ==================== EXPORT FUNCTIONS FOR GLOBAL USE ====================
// Make functions available globally
window.setFontSize = setFontSize;
window.toggleHighContrast = toggleHighContrast;
window.setTheme = setTheme;
window.dismissNotification = dismissNotification;
window.showToast = showToast;
window.showConfirmModal = showConfirmModal;
window.validateEmail = validateEmail;
window.validatePassword = validatePassword;
window.validateAge = validateAge;
window.updatePasswordStrength = updatePasswordStrength;
window.previewImage = previewImage;
window.formatTimeAgo = formatTimeAgo;
window.formatCountdown = formatCountdown;
window.postData = postData;
window.getData = getData;
