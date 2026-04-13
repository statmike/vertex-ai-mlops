/**
 * Main application — initializes WebSocket, wires up input, manages views.
 *
 * Supports dual-panel mode where text and voice can both be active at once,
 * sharing the same agent_chat session. Voice-originated data events stream
 * into the text panel in real-time. When toggling a panel on, past events
 * are backfilled from the server.
 *
 * Toggle states:
 *   Text only   — [Text *] [Voice  ]   (default)
 *   Both active — [Text *] [Voice *]
 *   Voice only  — [Text  ] [Voice *]
 *
 * At least one panel must be active at all times.
 */

document.addEventListener('DOMContentLoaded', () => {
    const input = document.getElementById('chat-input');
    const sendBtn = document.getElementById('send-btn');
    const statusDot = document.getElementById('status-dot');
    const statusText = document.getElementById('status-text');
    const textToggle = document.getElementById('text-toggle');
    const voiceToggle = document.getElementById('voice-toggle');
    const appContainer = document.getElementById('app-container');

    // Session management elements
    const sessionLabel = document.getElementById('session-label');
    const newSessionBtn = document.getElementById('new-session-btn');
    const sessionHistoryBtn = document.getElementById('session-history-btn');
    const sessionDropdown = document.getElementById('session-dropdown');

    let textActive = true;
    let voiceActive = false;
    let sharedSessionId = null;
    let switching = false;
    let _sessionPromise = null;

    // Session history (scoped to this UI instance)
    let sessionHistory = []; // [{id, createdAt}]

    // --- Shared session lifecycle ---

    async function ensureSession() {
        if (sharedSessionId) return sharedSessionId;
        // Deduplicate concurrent calls — return the same promise
        if (_sessionPromise) return _sessionPromise;
        _sessionPromise = (async () => {
            try {
                const resp = await fetch('/api/sessions/', { method: 'POST' });
                const data = await resp.json();
                sharedSessionId = data.id || data.session_id || '';
                console.log('[App] Created shared session:', sharedSessionId);
                // Pass to text WebSocket
                socket.setSessionId(sharedSessionId);
                // Track in session history
                _trackSession(sharedSessionId);
                _updateSessionLabel();
                return sharedSessionId;
            } catch (err) {
                console.error('[App] Failed to create session:', err);
                _sessionPromise = null; // Allow retry on failure
                return null;
            }
        })();
        return _sessionPromise;
    }

    async function createNewSession() {
        // Disconnect voice if active
        if (voiceActive) {
            Voice.disconnect();
        }
        // Reset state
        sharedSessionId = null;
        _sessionPromise = null;
        Chat.entries = [];
        Chat.current = null;
        Chat.render();
        // Create fresh session
        await ensureSession();
        // Reconnect voice if it was active
        if (voiceActive && sharedSessionId) {
            await Voice.connect(sharedSessionId);
            Voice.render();
        }
    }

    async function switchToSession(sessionId) {
        // Disconnect voice if active
        if (voiceActive) {
            Voice.disconnect();
        }
        // Switch session
        sharedSessionId = sessionId;
        _sessionPromise = Promise.resolve(sessionId);
        socket.setSessionId(sessionId);
        Chat.entries = [];
        Chat.current = null;
        // Backfill from server
        await backfillTextPanel();
        Chat.render();
        _updateSessionLabel();
        // Close dropdown
        sessionDropdown.classList.remove('open');
        // Reconnect voice if active
        if (voiceActive && sharedSessionId) {
            await Voice.connect(sharedSessionId);
            Voice.render();
        }
    }

    function _trackSession(id) {
        if (!sessionHistory.find(s => s.id === id)) {
            sessionHistory.unshift({ id, createdAt: new Date().toLocaleTimeString() });
            // Keep max 10
            if (sessionHistory.length > 10) sessionHistory.pop();
        }
    }

    function _updateSessionLabel() {
        if (sharedSessionId) {
            // Show last 8 chars of session ID
            const short = sharedSessionId.length > 8
                ? '...' + sharedSessionId.slice(-8)
                : sharedSessionId;
            sessionLabel.textContent = short;
            sessionLabel.title = sharedSessionId;
        } else {
            sessionLabel.textContent = 'No session';
            sessionLabel.title = '';
        }
    }

    function _renderSessionDropdown() {
        if (sessionHistory.length === 0) {
            sessionDropdown.innerHTML = '<div class="session-dropdown-empty">No previous sessions</div>';
            return;
        }
        sessionDropdown.innerHTML = sessionHistory.map(s => {
            const short = s.id.length > 12 ? s.id.slice(0, 6) + '...' + s.id.slice(-6) : s.id;
            const isActive = s.id === sharedSessionId;
            return `<button class="session-dropdown-item${isActive ? ' active' : ''}"
                            data-session-id="${s.id}"
                            title="${s.id}">
                        <span class="material-symbols-outlined" style="font-size: 0.75rem;">
                            ${isActive ? 'radio_button_checked' : 'radio_button_unchecked'}
                        </span>
                        <span>${short}</span>
                        <span style="margin-left: auto; opacity: 0.5; font-family: Manrope, sans-serif;">${s.createdAt}</span>
                    </button>`;
        }).join('');

        // Wire click handlers
        sessionDropdown.querySelectorAll('.session-dropdown-item').forEach(btn => {
            btn.addEventListener('click', () => {
                const id = btn.dataset.sessionId;
                if (id !== sharedSessionId) {
                    switchToSession(id);
                }
            });
        });
    }

    // Session button handlers
    newSessionBtn.addEventListener('click', () => createNewSession());
    sessionHistoryBtn.addEventListener('click', () => {
        _renderSessionDropdown();
        sessionDropdown.classList.toggle('open');
    });

    // Close dropdown on outside click
    document.addEventListener('click', (e) => {
        if (!e.target.closest('.session-dropdown-wrap')) {
            sessionDropdown.classList.remove('open');
        }
    });

    // --- Status handler (shared by both modes) ---

    function updateStatus(status) {
        statusDot.className = 'status-dot';
        switch (status) {
            case 'connected':
                statusDot.classList.add('connected');
                statusText.textContent = 'Connected';
                break;
            case 'connecting':
            case 'reconnecting':
                statusText.textContent = 'Connecting...';
                break;
            case 'disconnected':
                statusDot.classList.add('disconnected');
                statusText.textContent = 'Disconnected';
                break;
            case 'error':
                statusDot.classList.add('disconnected');
                statusText.textContent = 'Error';
                break;
        }
    }

    // --- Text mode (WebSocket + Chat) ---

    const socket = new ChatSocket(
        (event) => Chat.handleEvent(event),
        updateStatus,
    );

    async function sendMessage() {
        const message = input.value.trim();
        if (!message) return;
        // Ensure shared session exists before sending
        await ensureSession();
        Chat.ask(message, 'text');
        socket.send(message);
        input.value = '';
        input.focus();
    }

    sendBtn.addEventListener('click', () => sendMessage());

    input.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });

    // --- Voice mode ---

    Voice.init(updateStatus);

    // Wire voice → text panel callbacks
    Voice.onVoiceQuestion = (question) => {
        // Voice asked a data question — create entry in text panel
        Chat.ask(question, 'voice');
        // Set state to thinking since events will stream in
        if (Chat.current) Chat.current.state = 'thinking';
        Chat.render();
    };

    Voice.onTextEvent = (event) => {
        // Detailed agent_chat event from voice bridge → render in text panel
        Chat.handleEvent(event);
    };

    // --- Layout management ---

    function updateLayout() {
        const chatContent = document.getElementById('chat-content');
        const voiceContent = document.getElementById('voice-content');
        const textInputBar = document.getElementById('text-input-bar');

        // Update toggle button states
        textToggle.classList.toggle('active', textActive);
        voiceToggle.classList.toggle('active', voiceActive);

        // Dual-panel mode
        const isDual = textActive && voiceActive;
        appContainer.classList.toggle('dual-panel', isDual);

        // Text panel
        chatContent.style.display = textActive ? 'flex' : 'none';
        textInputBar.style.display = textActive ? 'flex' : 'none';

        // Voice panel
        voiceContent.style.display = voiceActive ? 'flex' : 'none';
    }

    // --- Toggle handlers ---

    async function toggleText() {
        if (switching) return;

        // Can't deactivate the last active panel
        if (textActive && !voiceActive) return;

        switching = true;
        try {
            if (textActive) {
                // Deactivate text
                textActive = false;
                updateLayout();
            } else {
                // Activate text
                textActive = true;
                updateLayout();

                // Backfill text panel with server history if local state is empty
                if (sharedSessionId && Chat.entries.length === 0) {
                    await backfillTextPanel();
                }

                // Re-render to fix charts that were rendered while hidden (0 width)
                Chat.render();
            }
        } finally {
            switching = false;
        }
    }

    async function toggleVoice() {
        if (switching) return;

        // Can't deactivate the last active panel
        if (voiceActive && !textActive) return;

        switching = true;
        try {
            if (voiceActive) {
                // Deactivate voice
                voiceActive = false;
                Voice.disconnect();
                updateLayout();
            } else {
                // Activate voice
                voiceActive = true;
                updateLayout();

                // Ensure we have a shared session
                await ensureSession();

                // Connect voice WebSocket with shared session
                if (!Voice.ws || Voice.ws.readyState !== WebSocket.OPEN) {
                    await Voice.connect(sharedSessionId);
                }
                Voice.render();
            }
        } finally {
            switching = false;
        }
    }

    textToggle.addEventListener('click', toggleText);
    voiceToggle.addEventListener('click', toggleVoice);

    // --- Backfill ---

    async function backfillTextPanel() {
        if (!sharedSessionId) return;
        try {
            const resp = await fetch(`/api/sessions/${sharedSessionId}/history`);
            const data = await resp.json();
            if (data.events && data.events.length > 0) {
                console.log('[App] Backfilling text panel:', data.events.length, 'events');
                Chat.backfill(data.events);
            }
        } catch (err) {
            console.error('[App] Backfill failed:', err);
        }
    }

    // --- Suggested query chips ---

    function wireSuggestedQueries() {
        document.querySelectorAll('.suggested-query').forEach(btn => {
            btn.addEventListener('click', () => {
                input.value = btn.textContent;
                sendMessage();
            });
        });
    }

    // --- Initialize ---

    socket.connect();
    Chat.render();
    wireSuggestedQueries();
    updateLayout();

    // Create session eagerly so it's ready for either mode
    ensureSession();
});
