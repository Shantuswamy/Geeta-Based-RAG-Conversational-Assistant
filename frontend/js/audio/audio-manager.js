/**
 * AudioManager
 * Web Audio Context lifecycle, shared nodes, and real-time amplitude/spectrum analysis.
 */
export class AudioManager {
  constructor() {
    this.audioCtx = null;
    this.analyser = null;
    this.masterGain = null;
    this.dataArray = null;
    this.fftSize = 256;
    this.smoothedVolume = 0;
    this.isInitialized = false;
  }

  async init() {
    if (this.isInitialized && this.audioCtx && this.audioCtx.state === 'running') {
      return;
    }

    const AudioContextClass = window.AudioContext || window.webkitAudioContext;
    if (!this.audioCtx) {
      this.audioCtx = new AudioContextClass({ latencyHint: 'interactive' });
    }

    if (this.audioCtx.state === 'suspended') {
      await this.audioCtx.resume();
    }

    if (!this.analyser) {
      this.analyser = this.audioCtx.createAnalyser();
      this.analyser.fftSize = this.fftSize;
      this.analyser.smoothingTimeConstant = 0.35;
      this.dataArray = new Uint8Array(this.analyser.frequencyBinCount);
    }

    if (!this.masterGain) {
      this.masterGain = this.audioCtx.createGain();
      this.masterGain.gain.value = 1.0;
      this.analyser.connect(this.masterGain);
      this.masterGain.connect(this.audioCtx.destination);
    }

    this.isInitialized = true;
    console.log('[AudioManager] AudioContext initialized, state:', this.audioCtx.state);
  }

  getVolume() {
    if (!this.analyser || !this.dataArray) return 0;
    this.analyser.getByteTimeDomainData(this.dataArray);

    let sum = 0;
    for (let i = 0; i < this.dataArray.length; i++) {
      const normalized = (this.dataArray[i] - 128) / 128.0;
      sum += normalized * normalized;
    }
    const rms = Math.sqrt(sum / this.dataArray.length);

    // Apply asymmetric attack/decay smoothing: fast attack (0.75), smooth release (0.3)
    const attack = 0.75;
    const decay = 0.25;
    if (rms > this.smoothedVolume) {
      this.smoothedVolume = this.smoothedVolume * (1 - attack) + rms * attack;
    } else {
      this.smoothedVolume = this.smoothedVolume * (1 - decay) + rms * decay;
    }

    return this.smoothedVolume;
  }

  getFrequencyData() {
    if (!this.analyser || !this.dataArray) return new Uint8Array(0);
    this.analyser.getByteFrequencyData(this.dataArray);
    return this.dataArray;
  }
}
