/**
 * Voice-to-Text Input Module
 * Uses the Web Speech API to transcribe speech into a target textarea.
 *
 * Usage:
 *   initVoiceInput(document.getElementById('voiceBtn'), document.getElementById('myTextarea'));
 */

function initVoiceInput(buttonEl, targetTextarea) {
    if (!buttonEl || !targetTextarea) return;

    var SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

    if (!SpeechRecognition) {
        buttonEl.title = 'Voice input not supported in this browser';
        buttonEl.disabled = true;
        buttonEl.classList.add('disabled');
        return;
    }

    var recognition = new SpeechRecognition();
    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.lang = document.documentElement.lang || 'en-US';

    var isRecording = false;
    var finalTranscript = '';

    buttonEl.addEventListener('click', function () {
        if (isRecording) {
            recognition.stop();
        } else {
            finalTranscript = '';
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
        var interim = '';
        finalTranscript = '';

        for (var i = 0; i < event.results.length; i++) {
            var transcript = event.results[i][0].transcript;
            if (event.results[i].isFinal) {
                finalTranscript += transcript;
            } else {
                interim += transcript;
            }
        }

        if (finalTranscript) {
            // Append final transcript to textarea
            var current = targetTextarea.value;
            var separator = current && !current.endsWith(' ') && !current.endsWith('\n') ? ' ' : '';
            targetTextarea.value = current + separator + finalTranscript;

            // Trigger input event so char counters and auto-expand update
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
