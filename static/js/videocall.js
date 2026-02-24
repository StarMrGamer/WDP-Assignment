/**
 * File: videocall.js
 * Purpose: WebRTC video/audio call and screen sharing between buddies
 * Reference: mirotalkbro (github.com/miroslavpejic85/mirotalkbro)
 * Date: February 2026
 *
 * Approach: Like mirotalkbro, when switching to screen share we tear down
 * the peer connection and rebuild it with the new stream. This is more
 * reliable than replaceTrack across browsers.
 */

(function () {
    'use strict';

    var localStream = null;
    var screenStream = null;
    var peerConnection = null;
    var isScreenSharing = false;
    var remoteIsScreenSharing = false;
    var isCalling = false;
    var isInCall = false;
    var callDirection = null;

    var ICE_SERVERS = [
        { urls: 'stun:stun.l.google.com:19302' },
        { urls: 'stun:stun1.l.google.com:19302' }
    ];

    var els = {};
    function cacheElements() {
        els.overlay = document.getElementById('videocallOverlay');
        els.localVideo = document.getElementById('localVideo');
        els.remoteVideo = document.getElementById('remoteVideo');
        els.btnCall = document.getElementById('btnStartCall');
        els.btnScreenShare = document.getElementById('btnScreenShare');
        els.btnEndCall = document.getElementById('btnEndCall');
        els.btnToggleMic = document.getElementById('btnToggleMic');
        els.btnToggleScreen = document.getElementById('btnToggleScreen');
        els.callStatus = document.getElementById('callStatus');
        els.incomingCallModal = document.getElementById('incomingCallModal');
        els.incomingCallerName = document.getElementById('incomingCallerName');
        els.btnAcceptCall = document.getElementById('btnAcceptCall');
        els.btnRejectCall = document.getElementById('btnRejectCall');
    }

    function getSocket() {
        if (typeof io !== 'undefined') {
            if (window._videocallSocket) return window._videocallSocket;
            window._videocallSocket = io({ transports: ['websocket', 'polling'] });
            return window._videocallSocket;
        }
        return null;
    }

    // ======================== MEDIA ========================

    async function getLocalStream(videoEnabled) {
        try {
            return await navigator.mediaDevices.getUserMedia({
                audio: true,
                video: videoEnabled ? { width: { ideal: 1920 }, height: { ideal: 1080 }, frameRate: { ideal: 30 } } : false
            });
        } catch (err) {
            console.error('getUserMedia error:', err);
            if (videoEnabled) {
                return navigator.mediaDevices.getUserMedia({ audio: true, video: false });
            }
            throw err;
        }
    }

    function stopStream(stream) {
        if (stream) {
            stream.getTracks().forEach(function (t) { t.stop(); });
        }
    }

    /**
     * Returns the stream that should currently be sent to the peer.
     * If screen sharing, combines screen video + camera audio.
     * Otherwise just the camera stream.
     */
    function getActiveStream() {
        if (isScreenSharing && screenStream) {
            var tracks = [];
            // Screen video
            var svt = screenStream.getVideoTracks()[0];
            if (svt) tracks.push(svt);
            // Camera audio (keep mic from localStream)
            if (localStream) {
                var at = localStream.getAudioTracks()[0];
                if (at) tracks.push(at);
            }
            return new MediaStream(tracks);
        }
        return localStream;
    }

    // ======================== PEER CONNECTION ========================

    /**
     * Build a fresh RTCPeerConnection, add the active stream tracks,
     * and wire up ICE + ontrack.  Returns the pc.
     */
    function buildPeerConnection() {
        var socket = getSocket();
        var pc = new RTCPeerConnection({ iceServers: ICE_SERVERS });

        // Add tracks from the active stream
        var stream = getActiveStream();
        if (stream) {
            stream.getTracks().forEach(function (track) {
                pc.addTrack(track, stream);
            });
        }

        pc.onicecandidate = function (event) {
            if (event.candidate) {
                socket.emit('webrtc_candidate', {
                    candidate: event.candidate,
                    target_id: window._videocallBuddyId
                });
            }
        };

        pc.ontrack = function (event) {
            if (event.streams && event.streams[0]) {
                els.remoteVideo.srcObject = event.streams[0];
                els.remoteVideo.autoplay = true;
                els.remoteVideo.playsInline = true;
                els.remoteVideo.play().catch(function () {});
                setCallStatus('Connected');
            }
        };

        pc.onconnectionstatechange = function () {
            var state = pc.connectionState;
            if (state === 'connected') {
                if (remoteIsScreenSharing) {
                    setCallStatus('Viewing screen share');
                } else {
                    setCallStatus('Connected');
                }
            } else if (state === 'disconnected' || state === 'failed' || state === 'closed') {
                if (isInCall) endCall(false);
            }
        };

        // Set high bitrate for video senders
        setHighBitrate(pc);

        return pc;
    }

    /**
     * Increase max video bitrate so screen shares stay crisp.
     */
    function setHighBitrate(pc) {
        try {
            pc.getSenders().forEach(function (sender) {
                if (sender.track && sender.track.kind === 'video') {
                    var params = sender.getParameters();
                    if (!params.encodings || params.encodings.length === 0) {
                        params.encodings = [{}];
                    }
                    params.encodings[0].maxBitrate = 4000000; // 4 Mbps
                    sender.setParameters(params).catch(function () {});
                }
            });
        } catch (e) {
            // Not all browsers support this
        }
    }

    /**
     * Tear down the old pc (if any) and create + negotiate a brand-new one.
     * The caller side creates the offer; the callee waits for it.
     * `iAmOfferer` – true means this side sends the offer.
     */
    async function rebuildConnection(iAmOfferer) {
        // Close old connection but keep streams alive
        if (peerConnection) {
            peerConnection.onicecandidate = null;
            peerConnection.ontrack = null;
            peerConnection.onconnectionstatechange = null;
            peerConnection.close();
            peerConnection = null;
        }

        peerConnection = buildPeerConnection();

        if (iAmOfferer) {
            try {
                var offer = await peerConnection.createOffer();
                await peerConnection.setLocalDescription(offer);
                var socket = getSocket();
                socket.emit('webrtc_offer', {
                    offer: peerConnection.localDescription,
                    target_id: window._videocallBuddyId
                });
            } catch (err) {
                console.error('rebuildConnection offer error:', err);
            }
        }
    }

    // ======================== CALL FLOW ========================

    async function startCall(videoEnabled) {
        if (isCalling || isInCall) return;
        isCalling = true;
        callDirection = 'outgoing';

        try {
            localStream = await getLocalStream(videoEnabled);
            showOverlay();
            setCallStatus('Calling...');

            var socket = getSocket();
            socket.emit('call_user', {
                target_id: window._videocallBuddyId,
                caller_name: window._videocallUserName,
                video: videoEnabled
            });
        } catch (err) {
            console.error('startCall error:', err);
            isCalling = false;
            callDirection = null;
            alert('Could not access camera/microphone. Please check permissions.');
        }
    }

    async function acceptCall(data) {
        callDirection = 'incoming';
        isInCall = true;
        isCalling = false;
        hideIncomingModal();

        try {
            localStream = await getLocalStream(data.video !== false);
            showOverlay();
            setCallStatus('Connecting...');

            // Build pc — callee side waits for the offer
            peerConnection = buildPeerConnection();

            var socket = getSocket();
            socket.emit('call_accepted', {
                target_id: data.caller_id
            });
        } catch (err) {
            console.error('acceptCall error:', err);
            endCall(true);
        }
    }

    function rejectCall(data) {
        hideIncomingModal();
        var socket = getSocket();
        socket.emit('call_rejected', { target_id: data.caller_id });
    }

    function endCall(notify) {
        if (notify !== false) {
            var socket = getSocket();
            socket.emit('end_call', { target_id: window._videocallBuddyId });
        }

        if (peerConnection) {
            peerConnection.close();
            peerConnection = null;
        }

        stopStream(localStream);
        stopStream(screenStream);
        localStream = null;
        screenStream = null;
        isScreenSharing = false;
        remoteIsScreenSharing = false;
        isCalling = false;
        isInCall = false;
        callDirection = null;

        if (els.remoteVideo) els.remoteVideo.srcObject = null;
        if (els.localVideo) els.localVideo.srcObject = null;

        if (els.overlay) {
            els.overlay.classList.remove('remote-screenshare');
            els.overlay.classList.remove('local-screenshare');
        }
        hideOverlay();
        hideIncomingModal();
        resetControlButtons();
    }

    // ======================== SCREEN SHARING ========================
    // Like mirotalkbro: tear down connection, rebuild with new stream.

    async function toggleScreenShare() {
        if (!peerConnection || !isInCall) return;

        if (isScreenSharing) {
            // ---- STOP screen share ----
            stopStream(screenStream);
            screenStream = null;
            isScreenSharing = false;

            els.btnToggleScreen.classList.remove('active');
            if (els.overlay) els.overlay.classList.remove('local-screenshare');
            setCallStatus('Connected');

            // Tell buddy screen share stopped, then rebuild with camera
            var socket = getSocket();
            socket.emit('screen_share_toggle', {
                target_id: window._videocallBuddyId,
                sharing: false
            });

            await rebuildConnection(true);
        } else {
            // ---- START screen share ----
            try {
                screenStream = await navigator.mediaDevices.getDisplayMedia({
                    video: {
                        width: { ideal: 1920 },
                        height: { ideal: 1080 },
                        frameRate: { ideal: 30 }
                    },
                    audio: true
                });
                isScreenSharing = true;

                els.btnToggleScreen.classList.add('active');
                if (els.overlay) els.overlay.classList.add('local-screenshare');
                setCallStatus('You are sharing your screen');

                // Tell buddy screen share started, then rebuild with screen stream
                var socket2 = getSocket();
                socket2.emit('screen_share_toggle', {
                    target_id: window._videocallBuddyId,
                    sharing: true
                });

                await rebuildConnection(true);

                // If user clicks "Stop sharing" in browser chrome
                screenStream.getVideoTracks()[0].onended = function () {
                    if (isScreenSharing) toggleScreenShare();
                };
            } catch (err) {
                console.error('Screen share error:', err);
                isScreenSharing = false;
            }
        }
    }

    // ======================== MIC / CAM ========================

    function toggleMic() {
        if (!localStream) return;
        var audioTrack = localStream.getAudioTracks()[0];
        if (audioTrack) {
            audioTrack.enabled = !audioTrack.enabled;
            els.btnToggleMic.classList.toggle('muted', !audioTrack.enabled);
            var icon = els.btnToggleMic.querySelector('i');
            if (icon) {
                icon.className = audioTrack.enabled ? 'fas fa-microphone' : 'fas fa-microphone-slash';
            }
        }
    }

    // ======================== UI HELPERS ========================

    function showOverlay() {
        if (els.overlay) els.overlay.classList.add('active');
    }

    function hideOverlay() {
        if (els.overlay) els.overlay.classList.remove('active');
    }

    function showIncomingModal(data) {
        if (els.incomingCallerName) {
            els.incomingCallerName.textContent = data.caller_name || 'Your buddy';
        }
        if (els.incomingCallModal) els.incomingCallModal.classList.add('active');
        window._incomingCallData = data;
    }

    function hideIncomingModal() {
        if (els.incomingCallModal) els.incomingCallModal.classList.remove('active');
        window._incomingCallData = null;
    }

    function setCallStatus(text) {
        if (els.callStatus) els.callStatus.textContent = text;
    }

    function resetControlButtons() {
        if (els.btnToggleMic) {
            els.btnToggleMic.classList.remove('muted');
            var micIcon = els.btnToggleMic.querySelector('i');
            if (micIcon) micIcon.className = 'fas fa-microphone';
        }
        if (els.btnToggleScreen) {
            els.btnToggleScreen.classList.remove('active');
        }
    }

    // ======================== SOCKET EVENTS ========================

    function registerSocketEvents() {
        var socket = getSocket();
        if (!socket) return;

        // --- Incoming call ---
        socket.on('incoming_call', function (data) {
            if (isInCall || isCalling) {
                socket.emit('call_rejected', { target_id: data.caller_id });
                return;
            }
            showIncomingModal(data);
        });

        // --- Call accepted — caller builds pc and sends offer ---
        socket.on('call_accepted', async function () {
            if (!isCalling) return;
            isInCall = true;
            isCalling = false;
            setCallStatus('Connecting...');

            peerConnection = buildPeerConnection();

            try {
                var offer = await peerConnection.createOffer();
                await peerConnection.setLocalDescription(offer);
                socket.emit('webrtc_offer', {
                    offer: peerConnection.localDescription,
                    target_id: window._videocallBuddyId
                });
            } catch (err) {
                console.error('createOffer error:', err);
                endCall(true);
            }
        });

        socket.on('call_rejected', function () {
            setCallStatus('Call declined');
            setTimeout(function () { endCall(false); }, 1500);
        });

        // --- WebRTC offer (initial + renegotiation) ---
        socket.on('webrtc_offer', async function (data) {
            if (!peerConnection) return;
            try {
                await peerConnection.setRemoteDescription(new RTCSessionDescription(data.offer));
                var answer = await peerConnection.createAnswer();
                await peerConnection.setLocalDescription(answer);
                socket.emit('webrtc_answer', {
                    answer: peerConnection.localDescription,
                    target_id: data.caller_id
                });
            } catch (err) {
                console.error('handleOffer error:', err);
            }
        });

        // --- WebRTC answer ---
        socket.on('webrtc_answer', async function (data) {
            if (!peerConnection) return;
            try {
                await peerConnection.setRemoteDescription(new RTCSessionDescription(data.answer));
            } catch (err) {
                console.error('handleAnswer error:', err);
            }
        });

        // --- ICE candidates ---
        socket.on('webrtc_candidate', async function (data) {
            if (!peerConnection) return;
            try {
                await peerConnection.addIceCandidate(new RTCIceCandidate(data.candidate));
            } catch (err) {
                console.error('addIceCandidate error:', err);
            }
        });

        // --- Remote ended call ---
        socket.on('call_ended', function () {
            endCall(false);
        });

        // --- Remote toggled screen share ---
        socket.on('screen_share_toggled', function (data) {
            remoteIsScreenSharing = data.sharing;
            if (els.overlay) {
                els.overlay.classList.toggle('remote-screenshare', remoteIsScreenSharing);
            }
            if (remoteIsScreenSharing) {
                // Force play when the new stream arrives via ontrack
                if (els.remoteVideo && els.remoteVideo.srcObject) {
                    els.remoteVideo.play().catch(function () {});
                }
                setCallStatus('Viewing screen share');
            } else {
                setCallStatus('Connected');
            }

            // Rebuild our side too so we can receive the new stream
            rebuildConnection(false);
        });
    }

    // ======================== INIT ========================

    function init() {
        cacheElements();
        registerSocketEvents();

        if (els.btnCall) {
            els.btnCall.addEventListener('click', function () { startCall(false); });
        }
        if (els.btnEndCall) {
            els.btnEndCall.addEventListener('click', function () { endCall(true); });
        }
        if (els.btnToggleMic) {
            els.btnToggleMic.addEventListener('click', toggleMic);
        }
        if (els.btnToggleScreen) {
            els.btnToggleScreen.addEventListener('click', toggleScreenShare);
        }
        if (els.btnAcceptCall) {
            els.btnAcceptCall.addEventListener('click', function () {
                if (window._incomingCallData) acceptCall(window._incomingCallData);
            });
        }
        if (els.btnRejectCall) {
            els.btnRejectCall.addEventListener('click', function () {
                if (window._incomingCallData) rejectCall(window._incomingCallData);
            });
        }
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
