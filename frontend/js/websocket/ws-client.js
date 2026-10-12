/**
 * WebSocketClient
 * High-performance WebSocket client for streaming voice frames to/from FastAPI backend.
 */
export class WebSocketClient {
  constructor(url, callbacks = {}) {
    this.url = url;
    this.callbacks = {
      onConnect: callbacks.onConnect || (() => {}),
      onDisconnect: callbacks.onDisconnect || (() => {}),
      onAudioFrame: callbacks.onAudioFrame || (() => {}),
      onMessage: callbacks.onMessage || (() => {}),
      onError: callbacks.onError || (() => {})
    };
    this.ws = null;
    this.isConnected = false;
    this.reconnectTimer = null;
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 10;
  }

  setUrl(url) {
    this.url = url;
    if (this.isConnected) {
      this.disconnect();
      this.connect();
    }
  }

  connect() {
    if (this.ws && (this.ws.readyState === WebSocket.OPEN || this.ws.readyState === WebSocket.CONNECTING)) {
      return;
    }

    console.log(`[WebSocket] Connecting to ${this.url}...`);
    try {
      this.ws = new WebSocket(this.url);
      this.ws.binaryType = 'arraybuffer';

      this.ws.onopen = () => {
        console.log('[WebSocket] Connected successfully.');
        this.isConnected = true;
        this.reconnectAttempts = 0;
        this.callbacks.onConnect();
      };

      this.ws.onmessage = (event) => {
        if (event.data instanceof ArrayBuffer) {
          // Binary audio chunk (Float32 PCM 24kHz)
          this.callbacks.onAudioFrame(event.data);
        } else if (typeof event.data === 'string') {
          try {
            const parsed = JSON.parse(event.data);
            this.callbacks.onMessage(parsed);
          } catch (_) {
            this.callbacks.onMessage({ text: event.data });
          }
        }
      };

      this.ws.onclose = (event) => {
        console.warn('[WebSocket] Closed:', event.code, event.reason);
        this.isConnected = false;
        this.callbacks.onDisconnect(event);
        this.scheduleReconnect();
      };

      this.ws.onerror = (err) => {
        console.error('[WebSocket] Error:', err);
        this.callbacks.onError(err);
      };
    } catch (err) {
      console.error('[WebSocket] Connection attempt failed:', err);
      this.scheduleReconnect();
    }
  }

  scheduleReconnect() {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.warn('[WebSocket] Max reconnect attempts reached.');
      return;
    }
    const delay = Math.min(1000 * Math.pow(1.5, this.reconnectAttempts), 10000);
    this.reconnectAttempts++;
    console.log(`[WebSocket] Reconnecting in ${(delay / 1000).toFixed(1)}s (attempt ${this.reconnectAttempts})...`);
    clearTimeout(this.reconnectTimer);
    this.reconnectTimer = setTimeout(() => this.connect(), delay);
  }

  send(data) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(data);
      return true;
    }
    return false;
  }

  disconnect() {
    clearTimeout(this.reconnectTimer);
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
    this.isConnected = false;
  }
}
