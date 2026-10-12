/**
 * GitaRAG Voice Assistant App Controller
 * Orchestrates Audio, WebSocket, Lip-Sync, Subtitles, and UI States.
 */
import { AudioManager } from './audio/audio-manager.js';
import { MicRecorder } from './audio/mic-recorder.js';
import { PCMPlayer } from './audio/player.js';
import { WebSocketClient } from './websocket/ws-client.js';
import { VisemeController } from './visual/viseme-controller.js';
import { ParticlesField } from './visual/particles.js';
import { SettingsModal } from './components/settings-modal.js';
import { SubtitleCard } from './components/subtitle-card.js';

class App {
  constructor() {
    this.state = 'idle'; // 'idle' | 'listening' | 'speaking'
    this.audioManager = new AudioManager();
    this.subtitleCard = new SubtitleCard(this.audioManager);
    this.visemeController = new VisemeController(this.audioManager);
    this.particlesField = new ParticlesField('particles', 30);

    this.player = new PCMPlayer(this.audioManager, {
      sampleRate: 24000,
      onPlayStart: () => this.handleKrishnaSpeechStart(),
      onPlayEnd: () => this.handleKrishnaSpeechEnd()
    });

    this.micRecorder = new MicRecorder(this.audioManager, (chunkBuffer) => {
      // Send raw 16kHz Float32 PCM to backend
      if (this.wsClient && this.wsClient.isConnected) {
        this.wsClient.send(chunkBuffer);
      }
    });

    this.settingsModal = new SettingsModal((newSettings) => {
      if (this.wsClient && this.wsClient.url !== newSettings.wsUrl) {
        this.wsClient.setUrl(newSettings.wsUrl);
      }
    });

    this.wsClient = null;
    this.micBtn = document.getElementById('mic-trigger');
    this.fullscreenBtn = document.getElementById('fullscreen-btn');
    this.connectionStatusText = document.getElementById('connection-status-text');
    this.statusDot = document.getElementById('status-live-dot');
  }

  init() {
    this.particlesField.init();
    this.subtitleCard.init();
    this.visemeController.init();
    this.settingsModal.init();

    this.initWebSocket();
    this.bindUIEvents();
    this.setState('idle');

    console.log('[App] GitaRAG Frontend initialized successfully.');
  }

  initWebSocket() {
    const wsUrl = this.settingsModal.settings.wsUrl;
    this.wsClient = new WebSocketClient(wsUrl, {
      onConnect: () => {
        if (this.connectionStatusText) this.connectionStatusText.textContent = 'Sanctum Connected';
        if (this.statusDot) {
          this.statusDot.style.backgroundColor = 'var(--color-emerald)';
          this.statusDot.style.boxShadow = '0 0 8px var(--color-emerald)';
        }
      },
      onDisconnect: () => {
        if (this.connectionStatusText) this.connectionStatusText.textContent = 'Reconnecting...';
        if (this.statusDot) {
          this.statusDot.style.backgroundColor = '#eab308';
          this.statusDot.style.boxShadow = '0 0 8px #eab308';
        }
      },
      onAudioFrame: (arrayBuffer) => {
        // Feed Float32 24kHz PCM chunk to player
        this.player.feed(arrayBuffer);
      },
      onMessage: (msg) => {
        if (msg.text) {
          this.subtitleCard.setText(msg.text, false);
        }
        if (msg.verse) {
          this.subtitleCard.setVerse(msg.verse);
        }
      },
      onError: (err) => {
        console.warn('[App] WebSocket error:', err);
      }
    });

    this.wsClient.connect();
  }

  bindUIEvents() {
    // Microphone Button Tap
    if (this.micBtn) {
      this.micBtn.addEventListener('click', () => this.toggleMicrophone());
    }

    // Avatar Tap to trigger dialogue
    const avatar = document.getElementById('krishna-avatar');
    if (avatar) {
      avatar.addEventListener('click', () => {
        if (this.state === 'idle') {
          this.toggleMicrophone();
        }
      });
    }

    // Fullscreen Toggle
    if (this.fullscreenBtn) {
      this.fullscreenBtn.addEventListener('click', () => {
        if (!document.fullscreenElement) {
          document.documentElement.requestFullscreen().catch(() => {});
        } else {
          document.exitFullscreen().catch(() => {});
        }
      });
    }

    // Preset chips
    window.triggerPreset = (question) => {
      this.subtitleCard.setText(question, true);
      this.audioManager.init();
      if (!this.micRecorder.isRecording) {
        this.startListening();
      }
    };
  }

  async toggleMicrophone() {
    await this.audioManager.init();
    if (this.state === 'listening') {
      this.stopListening();
    } else {
      await this.startListening();
    }
  }

  async startListening() {
    try {
      // Barge-in: if Krishna was speaking, stop output audio immediately
      if (this.state === 'speaking') {
        this.player.stopAndClear();
      }

      await this.micRecorder.start();
      this.setState('listening');
    } catch (err) {
      alert('Microphone access required for voice interaction. Please check browser permissions.');
    }
  }

  stopListening() {
    this.micRecorder.stop();
    this.setState('idle');
  }

  handleKrishnaSpeechStart() {
    this.setState('speaking');
    this.visemeController.setSpeaking(true);
  }

  handleKrishnaSpeechEnd() {
    this.visemeController.setSpeaking(false);
    if (this.micRecorder.isRecording) {
      this.setState('listening');
    } else {
      this.setState('idle');
    }
  }

  setState(newState) {
    this.state = newState;
    document.body.setAttribute('data-state', newState);

    const micPingRing = document.getElementById('mic-ping-ring');
    if (micPingRing) {
      micPingRing.classList.toggle('active', newState === 'listening');
    }
  }
}

window.addEventListener('DOMContentLoaded', () => {
  window.app = new App();
  window.app.init();
});
