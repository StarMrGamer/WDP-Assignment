/**
 * Voice-to-Text Input Module
 * Uses the Web Speech API to transcribe speech into a target textarea.
 *
 * Usage:
 *   initVoiceInput(btnEl, textareaEl);                        // defaults to en-US
 *   initVoiceInput(btnEl, textareaEl, langSelectEl);          // language from <select>
 */

// Map app language codes → BCP-47 locale tags for the Web Speech API
var VOICE_LANG_MAP = {
    'en': 'en-US',
    'zh': 'zh-CN',
    'ms': 'ms-MY',
    'ta': 'ta-IN'
};

function initVoiceInput(buttonEl, targetTextarea, langSelectEl) {
    if (!buttonEl || !targetTextarea) return;

    var SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

    if (!SpeechRecognition) {
        buttonEl.title = 'Voice input not supported in this browser';
        buttonEl.disabled = true;
        buttonEl.classList.add('disabled');
        if (langSelectEl) { langSelectEl.disabled = true; }
        return;
    }

    var recognition = new SpeechRecognition();
    recognition.continuous = true;
    recognition.interimResults = true;

    // Helper: resolve current language code → BCP-47 locale
    function getCurrentLang() {
        var code = (langSelectEl && langSelectEl.value)
            || localStorage.getItem('voiceLang')
            || 'en';
        return VOICE_LANG_MAP[code] || 'en-US';
    }

    recognition.lang = getCurrentLang();

    // Restore persisted language in the select element
    if (langSelectEl) {
        var saved = localStorage.getItem('voiceLang') || 'en';
        langSelectEl.value = saved;

        langSelectEl.addEventListener('change', function () {
            localStorage.setItem('voiceLang', langSelectEl.value);
            recognition.lang = getCurrentLang();
        });
    }

    var isRecording = false;
    var processedUpTo = 0;

    buttonEl.addEventListener('click', function () {
        if (isRecording) {
            recognition.stop();
        } else {
            processedUpTo = 0;
            recognition.lang = getCurrentLang(); // refresh lang on every start
            try {
                recognition.start();
            } catch (e) {
                // Already started
            }
        }
    });

    recognition.onstart = function () {
        isRecording = true;
        buttonEl.classList.add('recording');
        buttonEl.title = 'Click to stop recording';
        var icon = buttonEl.querySelector('i');
        if (icon) icon.className = 'fas fa-stop';
    };

    recognition.onend = function () {
        isRecording = false;
        buttonEl.classList.remove('recording');
        buttonEl.title = 'Voice input';
        var icon = buttonEl.querySelector('i');
        if (icon) icon.className = 'fas fa-microphone';
    };

    recognition.onresult = function (event) {
        var newFinal = '';

        for (var i = processedUpTo; i < event.results.length; i++) {
            if (event.results[i].isFinal) {
                newFinal += event.results[i][0].transcript;
                processedUpTo = i + 1;
            }
        }

        if (newFinal) {
            var current = targetTextarea.value;
            var separator = current && !current.endsWith(' ') && !current.endsWith('\n') ? ' ' : '';
            targetTextarea.value = current + separator + newFinal;
            targetTextarea.dispatchEvent(new Event('input', { bubbles: true }));
        }
    };

    recognition.onerror = function (event) {
        isRecording = false;
        buttonEl.classList.remove('recording');
        var icon = buttonEl.querySelector('i');
        if (icon) icon.className = 'fas fa-microphone';

        if (event.error === 'not-allowed') {
            if (typeof showToast === 'function') {
                showToast('Microphone access denied. Please allow microphone permissions.', 'danger');
            } else {
                alert('Microphone access denied. Please allow microphone permissions.');
            }
        } else if (event.error !== 'aborted') {
            if (typeof showToast === 'function') {
                showToast('Voice recognition error: ' + event.error, 'warning');
            }
        }
    };
}
