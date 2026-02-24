/**
 * Text-to-Speech Module
 * Uses the Web Speech API (speechSynthesis) to read text aloud.
 *
 * Usage:
 *   speakText(text)                     — speak with default English voice
 *   speakText(text, 'zh')               — speak with Chinese voice
 *   stopSpeaking()                      — stop current speech
 *   toggleSpeak(buttonEl, text, lang)   — toggle speak/stop on a button
 */

var TTS_LANG_MAP = {
    'en': 'en-US',
    'zh': 'zh-CN',
    'ms': 'ms-MY',
    'ta': 'ta-IN'
};

var _ttsCurrentBtn = null;

function speakText(text, lang) {
    if (!window.speechSynthesis) return false;
    window.speechSynthesis.cancel();
    if (!text || !text.trim()) return false;
    var utterance = new SpeechSynthesisUtterance(text.trim());
    utterance.lang = TTS_LANG_MAP[lang] || lang || 'en-US';
    utterance.rate = 0.9;
    window.speechSynthesis.speak(utterance);
    return true;
}

function stopSpeaking() {
    if (window.speechSynthesis) window.speechSynthesis.cancel();
    if (_ttsCurrentBtn) {
        _ttsCurrentBtn.classList.remove('tts-playing');
        var icon = _ttsCurrentBtn.querySelector('i');
        if (icon) icon.className = 'fas fa-volume-up';
        _ttsCurrentBtn = null;
    }
}

function toggleSpeak(btn, text, lang) {
    if (!window.speechSynthesis) {
        if (typeof showToast === 'function') showToast('Text-to-speech not supported in this browser.', 'warning');
        return;
    }
    // If this button is already playing, stop
    if (_ttsCurrentBtn === btn && window.speechSynthesis.speaking) {
        stopSpeaking();
        return;
    }
    // Stop any other speech first
    stopSpeaking();
    if (!text || !text.trim()) return;

    var utterance = new SpeechSynthesisUtterance(text.trim());
    utterance.lang = TTS_LANG_MAP[lang] || lang || 'en-US';
    utterance.rate = 0.9;

    _ttsCurrentBtn = btn;
    btn.classList.add('tts-playing');
    var icon = btn.querySelector('i');
    if (icon) icon.className = 'fas fa-stop';

    utterance.onend = function () {
        btn.classList.remove('tts-playing');
        if (icon) icon.className = 'fas fa-volume-up';
        _ttsCurrentBtn = null;
    };
    utterance.onerror = function () {
        btn.classList.remove('tts-playing');
        if (icon) icon.className = 'fas fa-volume-up';
        _ttsCurrentBtn = null;
    };

    window.speechSynthesis.speak(utterance);
}
