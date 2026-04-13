/**
 * Voice mode — bidirectional audio chat with the agent.
 *
 * State machine:  idle → listening → thinking → speaking → idle
 *
 * Uses AudioCapture (mic → PCM) and AudioPlayback (PCM → speakers)
 * with a dedicated WebSocket to /ws/voice.
 *
 * Rendering uses incremental DOM updates — the layout is built once,
 * then only the changed elements are patched on each event.
 */

const Voice = {
    state: 'idle',          // idle | listening | thinking | speaking
    ws: null,               // WebSocket
    connected: false,       // WebSocket is open
    capture: null,          // AudioCapture instance
    playback: null,         // AudioPlayback instance
    transcript: [],         // [{role: 'user'|'agent', text, partial}]
    thinkingSteps: [],      // [{tool, label}]
    sessionId: null,        // voice session (agent_voice)
    sharedSessionId: null,  // shared session (agent_chat) — set by app.js
    onStatusChange: null,   // callback from app.js
    onTextEvent: null,      // callback for text panel events
    onVoiceQuestion: null,  // callback when voice asks a data question
    _rendered: false,       // true after initial render

    // --- Lifecycle ---

    /** Initialize voice mode (does not start recording). */
    init(onStatusChange) {
        this.onStatusChange = onStatusChange;
        this.capture = new AudioCapture();
        this.playback = new AudioPlayback();

        // Mic audio → WebSocket
        this.capture.ondata = (buf) => {
            if (this.ws && this.ws.readyState === WebSocket.OPEN
                && this.state === 'listening') {
                this.ws.send(buf);
            }
        };

        // Level metering for visualisation
        this.capture.onlevel = (level) => {
            this._updateOrb(level);
        };
    },

    /** Connect the voice WebSocket. Returns a promise that resolves when open. */
    connect(sharedSessionId) {
        if (sharedSessionId) {
            this.sharedSessionId = sharedSessionId;
        }

        const protocol = location.protocol === 'https:' ? 'wss:' : 'ws:';
        const url = `${protocol}//${location.host}/ws/voice`;

        console.log('[Voice] Connecting to', url);
        this.ws = new WebSocket(url);
        this.ws.binaryType = 'arraybuffer';
        this._setStatus('connecting');

        return new Promise((resolve) => {
            this.ws.onopen = () => {
                console.log('[Voice] WebSocket open');
                this.connected = true;
                this._setStatus('connected');
                this._updateControls();

                // Send init message with shared session ID
                if (this.sharedSessionId) {
                    this.ws.send(JSON.stringify({
                        type: 'init',
                        session_id: this.sharedSessionId,
                    }));
                    console.log('[Voice] Sent init with shared session:', this.sharedSessionId);
                }

                resolve();
            };

            this.ws.onmessage = (e) => {
                if (e.data instanceof ArrayBuffer) {
                    this._onAudio(e.data);
                } else {
                    try {
                        const event = JSON.parse(e.data);
                        console.log('[Voice] Event:', event.type, event);
                        this._onEvent(event);
                    } catch (err) {
                        console.error('Voice event parse error:', err);
                    }
                }
            };

            this.ws.onclose = (e) => {
                console.log('[Voice] WebSocket closed:', e.code, e.reason);
                this.connected = false;
                this._setStatus('disconnected');
                this.capture.stop();
                this._micActive = false;
                this._updateControls();
                resolve();
            };

            this.ws.onerror = (err) => {
                console.error('[Voice] WebSocket error:', err);
                this._setStatus('error');
            };
        });
    },

    /** Disconnect and clean up. */
    disconnect() {
        this._micActive = false;
        this.capture.stop();
        this.playback.stop();
        if (this.ws) {
            this.ws.close();
            this.ws = null;
        }
        this.connected = false;
        this.state = 'idle';
    },

    // --- Mic control ---

    _micActive: false,   // true while mic is on (persists across turns)

    /**
     * Toggle mic on/off. When on, the mic stays active across multiple
     * turns — the model uses VAD to detect speech boundaries. The user
     * speaks naturally without clicking between turns.
     */
    async toggleMic() {
        if (this._micActive) {
            // Turn mic off
            this._micActive = false;
            this.capture.stop();
            this.state = 'idle';
            this.thinkingSteps = [];
        } else {
            // Reconnect if WebSocket dropped
            if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
                await this.connect(this.sharedSessionId);
            }
            try {
                await this.capture.start();
            } catch (err) {
                console.error('Mic access denied:', err);
                return;
            }
            this._micActive = true;
            this.state = 'listening';
            this.thinkingSteps = [];
        }
        this._updateControls();
    },

    // --- Event handling ---

    _onAudio(buffer) {
        if (this.state !== 'speaking') {
            this.state = 'speaking';
            this._updateControls();
        }
        this.playback.feed(buffer);
    },

    _onEvent(event) {
        switch (event.type) {
            case 'status':
                if (event.session_id) this.sessionId = event.session_id;
                break;

            case 'transcript_in':
                this._addTranscript('user', event.text, event.partial);
                break;

            case 'transcript_out':
                this._addTranscript('agent', event.text, event.partial);
                break;

            case 'thinking':
                if (this.state !== 'thinking') {
                    this.state = 'thinking';
                    this._updateControls();
                }
                this.thinkingSteps.push({ tool: event.tool, label: event.label });
                this._appendThinkingStep(event.label);
                break;

            case 'voice_question':
                // Voice asked a data question — forward to text panel
                if (this.onVoiceQuestion) {
                    this.onVoiceQuestion(event.question);
                }
                break;

            case 'text_event':
                // Detailed event from agent_chat — forward to text panel
                if (this.onTextEvent) {
                    this.onTextEvent(event.event);
                }
                // Mirror progress in voice activity status
                this._updateActivityFromEvent(event.event);
                break;

            case 'turn_complete':
                this.thinkingSteps = [];
                this._updateActivity('');
                if (this.state === 'speaking') {
                    // Audio may still be queued — wait for it to finish
                    // before re-enabling the mic to prevent echo interrupts
                    this._waitForPlaybackEnd();
                } else {
                    this.state = this._micActive ? 'listening' : 'idle';
                }
                this._updateControls();
                break;

            case 'interrupted':
                this.playback.stop();
                this.state = this._micActive ? 'listening' : 'idle';
                this._updateControls();
                break;

            case 'error':
                this._addTranscript('agent', `Error: ${event.content}`, false);
                this.state = this._micActive ? 'listening' : 'idle';
                this._updateControls();
                break;
        }
    },

    _addTranscript(role, text, partial) {
        const last = this.transcript[this.transcript.length - 1];
        if (last && last.role === role && (last.partial || partial)) {
            last.text = text;
            last.partial = partial;
            this._updateLastTranscriptLine(role, text, partial);
        } else {
            this.transcript.push({ role, text, partial: partial || false });
            this._appendTranscriptLine(role, text, partial);
        }
    },

    // --- Commands ---

    /** Poll until audio playback finishes, then re-enable mic. */
    _waitForPlaybackEnd() {
        const check = () => {
            if (!this.playback.isPlaying()) {
                this.state = this._micActive ? 'listening' : 'idle';
                this._updateControls();
            } else {
                setTimeout(check, 100);
            }
        };
        setTimeout(check, 100);
    },

    _sendCommand(type, data) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify({ type, ...data }));
        }
    },

    _setStatus(status) {
        if (this.onStatusChange) this.onStatusChange(status);
    },

    // --- Incremental DOM updates ---

    _updateControls() {
        const stateLabels = {
            idle: 'Ready',
            listening: 'Listening...',
            thinking: 'Thinking...',
            speaking: 'Speaking...',
        };

        const orb = document.getElementById('voice-orb');
        if (orb) {
            orb.className = `voice-orb ${this.state}`;
            orb.style.transform = '';
            orb.style.boxShadow = '';
        }

        const btn = document.getElementById('voice-mic-btn');
        if (btn) {
            btn.className = `voice-mic-btn ${this._micActive ? 'active' : ''}`;
            btn.disabled = !this.connected;
            const icon = btn.querySelector('.material-symbols-outlined');
            if (icon) icon.textContent = this._micActive ? 'mic' : 'mic_none';
        }

        const label = document.getElementById('voice-state-label');
        if (label) label.textContent = stateLabels[this.state] || '';

        // Clear thinking chips when not thinking
        if (this.state !== 'thinking') {
            const tc = document.getElementById('voice-thinking');
            if (tc) tc.innerHTML = '';
        }
    },

    _updateOrb(level) {
        const orb = document.getElementById('voice-orb');
        if (!orb) return;
        const scale = 1 + level * 0.5;
        const glow = Math.round(level * 30);
        orb.style.transform = `scale(${scale})`;
        orb.style.boxShadow = `0 0 ${glow}px rgba(133, 173, 255, ${0.3 + level * 0.5})`;
    },

    _appendThinkingStep(label) {
        const tc = document.getElementById('voice-thinking');
        if (!tc) return;
        const chip = document.createElement('div');
        chip.className = 'voice-thinking-step';
        chip.innerHTML = `<span class="material-symbols-outlined">settings</span> ${_escapeHtml(label)}`;
        tc.appendChild(chip);
    },

    _updateActivity(text) {
        const el = document.getElementById('voice-activity');
        if (el) el.textContent = text || '';
    },

    _updateActivityFromEvent(event) {
        if (!event) return;
        switch (event.type) {
            case 'transfer':
                this._updateActivity(`Routing to ${event.to || 'agent'}...`);
                break;
            case 'thinking':
                this._updateActivity(event.label || 'Processing...');
                break;
            case 'sql':
                this._updateActivity('SQL query generated');
                break;
            case 'data':
                this._updateActivity('Processing results...');
                break;
            case 'text':
                this._updateActivity('Composing response...');
                break;
            case 'status':
                if (event.content === 'done') this._updateActivity('');
                break;
        }
    },

    _appendTranscriptLine(role, text, partial) {
        const panel = document.getElementById('voice-transcript');
        if (!panel) return;

        // Remove placeholder if present
        const empty = panel.querySelector('.voice-empty');
        if (empty) empty.remove();

        const cls = role === 'user' ? 'voice-line-user' : 'voice-line-agent';
        const labelText = role === 'user' ? 'You' : 'Agent';
        const div = document.createElement('div');
        div.className = `voice-line ${cls}${partial ? ' partial' : ''}`;
        div.innerHTML = `<span class="voice-line-label">${labelText}</span><span class="voice-line-text">${_escapeHtml(text)}</span>`;
        panel.appendChild(div);
        panel.scrollTop = panel.scrollHeight;
    },

    _updateLastTranscriptLine(role, text, partial) {
        const panel = document.getElementById('voice-transcript');
        if (!panel) return;

        const lines = panel.querySelectorAll('.voice-line');
        const last = lines[lines.length - 1];
        if (!last) return;

        const span = last.querySelector('.voice-line-text');
        if (span) span.textContent = text;

        if (partial) {
            last.classList.add('partial');
        } else {
            last.classList.remove('partial');
        }
        panel.scrollTop = panel.scrollHeight;
    },

    // --- Render (initial layout — called once) ---

    render() {
        const container = document.getElementById('voice-content');
        if (!container) return;

        // Only build the DOM skeleton once
        if (!this._rendered) {
            container.innerHTML = `
                <div class="voice-center">
                    <div class="voice-orb-wrap">
                        <div id="voice-orb" class="voice-orb idle"></div>
                    </div>
                    <button id="voice-mic-btn" class="voice-mic-btn" disabled>
                        <span class="material-symbols-outlined">mic_none</span>
                    </button>
                    <div id="voice-state-label" class="voice-state-label">Ready</div>
                </div>
                <div id="voice-activity" class="voice-activity"></div>
                <div id="voice-thinking" class="voice-thinking"></div>
                <div id="voice-transcript" class="voice-transcript">
                    <div class="voice-empty">Tap the microphone and ask a question</div>
                </div>
            `;

            // Wire mic button (once — persists across updates)
            const micBtn = document.getElementById('voice-mic-btn');
            if (micBtn) {
                micBtn.addEventListener('click', () => this.toggleMic());
            }
            this._rendered = true;
        }

        // Sync current state
        this._updateControls();

        // Re-populate transcript if switching back from text mode
        const panel = document.getElementById('voice-transcript');
        if (panel && this.transcript.length > 0 && panel.querySelectorAll('.voice-line').length === 0) {
            panel.innerHTML = '';
            for (const t of this.transcript) {
                this._appendTranscriptLine(t.role, t.text, t.partial);
            }
        }
    },
};
