/**
 * VisemeController
 * Real-time 2D viseme lip-sync engine and life-like idle motions (breathing, swaying, blinking).
 */
export class VisemeController {
  constructor(audioManager, options = {}) {
    this.audioManager = audioManager;
    this.mouthClosed = document.getElementById('mouth-closed');
    this.mouthHalf = document.getElementById('mouth-half');
    this.mouthOpen = document.getElementById('mouth-open');
    this.characterWrapper = document.getElementById('krishna-character-wrapper');
    this.speechGlow = document.getElementById('speech-glow-ring');

    this.currentMouthState = 'closed'; // 'closed' | 'half' | 'open'
    this.isSpeaking = false;
    this.animationFrameId = null;

    // Amplitude thresholds
    this.thresholdHalf = options.thresholdHalf || 0.045;
    this.thresholdOpen = options.thresholdOpen || 0.16;

    // Smoothed energy
    this.currentEnergy = 0;
  }

  init() {
    this.setMouthState('closed');
    this.startLoop();
  }

  startLoop() {
    const render = () => {
      this.updateLipSync();
      this.animationFrameId = requestAnimationFrame(render);
    };
    this.animationFrameId = requestAnimationFrame(render);
  }

  stopLoop() {
    if (this.animationFrameId) {
      cancelAnimationFrame(this.animationFrameId);
      this.animationFrameId = null;
    }
  }

  setSpeaking(speaking) {
    this.isSpeaking = speaking;
    if (this.speechGlow) {
      if (speaking) {
        this.speechGlow.classList.remove('opacity-0');
        this.speechGlow.classList.add('opacity-80');
      } else {
        this.speechGlow.classList.remove('opacity-80');
        this.speechGlow.classList.add('opacity-0');
      }
    }
    if (!speaking) {
      this.setMouthState('closed');
    }
  }

  updateLipSync() {
    if (!this.isSpeaking) {
      if (this.currentMouthState !== 'closed') {
        this.setMouthState('closed');
      }
      return;
    }

    const rawVol = this.audioManager.getVolume();
    // Smooth lerping: fast attack, smooth decay
    const attack = 0.8;
    const decay = 0.25;
    if (rawVol > this.currentEnergy) {
      this.currentEnergy = this.currentEnergy * (1 - attack) + rawVol * attack;
    } else {
      this.currentEnergy = this.currentEnergy * (1 - decay) + rawVol * decay;
    }

    if (this.currentEnergy >= this.thresholdOpen) {
      this.setMouthState('open');
    } else if (this.currentEnergy >= this.thresholdHalf) {
      this.setMouthState('half');
    } else {
      this.setMouthState('closed');
    }
  }

  setMouthState(state) {
    if (this.currentMouthState === state) return;
    this.currentMouthState = state;

    if (this.mouthClosed) {
      this.mouthClosed.classList.toggle('active', state === 'closed');
    }
    if (this.mouthHalf) {
      this.mouthHalf.classList.toggle('active', state === 'half');
    }
    if (this.mouthOpen) {
      this.mouthOpen.classList.toggle('active', state === 'open');
    }
  }
}
