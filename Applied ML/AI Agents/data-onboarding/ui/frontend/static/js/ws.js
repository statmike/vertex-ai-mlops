/**
 * WebSocket client — connects to the backend and dispatches events.
 *
 * Usage:
 *   const ws = new ChatSocket(onEvent, onStatusChange);
 *   ws.setSessionId(id);   // set shared session before first send
 *   ws.connect();
 *   ws.send("What tables are available?");
 */

class ChatSocket {
    constructor(onEvent, onStatusChange) {
        this.onEvent = onEvent;
        this.onStatusChange = onStatusChange;
        this.ws = null;
        this.sessionId = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
    }

    /** Set the shared session ID (call before first send). */
    setSessionId(id) {
        this.sessionId = id;
    }

    connect() {
        const protocol = location.protocol === 'https:' ? 'wss:' : 'ws:';
        const url = `${protocol}//${location.host}/ws/chat`;

        this.ws = new WebSocket(url);
        this.onStatusChange('connecting');

        this.ws.onopen = () => {
            this.reconnectAttempts = 0;
            this.onStatusChange('connected');
        };

        this.ws.onmessage = (e) => {
            try {
                const event = JSON.parse(e.data);

                // Track session ID from status events
                if (event.session_id && !this.sessionId) {
                    this.sessionId = event.session_id;
                }

                this.onEvent(event);
            } catch (err) {
                console.error('Failed to parse event:', err);
            }
        };

        this.ws.onclose = () => {
            this.onStatusChange('disconnected');
            this._tryReconnect();
        };

        this.ws.onerror = (err) => {
            console.error('WebSocket error:', err);
            this.onStatusChange('error');
        };
    }

    send(message) {
        if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
            console.warn('WebSocket not connected');
            return;
        }

        this.ws.send(JSON.stringify({
            message: message,
            session_id: this.sessionId,
        }));
    }

    disconnect() {
        this.maxReconnectAttempts = 0;
        if (this.ws) {
            this.ws.close();
        }
    }

    _tryReconnect() {
        if (this.reconnectAttempts >= this.maxReconnectAttempts) return;

        this.reconnectAttempts++;
        const delay = Math.min(1000 * Math.pow(2, this.reconnectAttempts), 10000);

        setTimeout(() => {
            this.onStatusChange('reconnecting');
            this.connect();
        }, delay);
    }
}
