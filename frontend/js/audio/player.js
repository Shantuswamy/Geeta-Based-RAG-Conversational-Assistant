/**
 * PCMPlayer
 * Gapless, click-free 24kHz Float32 PCM streaming audio playback engine using Web Audio API.
 */
export class PCMPlayer {
  constructor(audioManager, options = {}) {
    this.audioManager = audioManager;
    this.sampleRate = options.sampleRate || 24000;
    this.nextStartTime = 0;
    this.isPlaying = false;
    this.activeSources = [];
    this.onPlayStart = options.onPlayStart || null;
    this.onPlayEnd = options.onPlayEnd || null;
    this.endCheckTimer = null;
  }

  async feed(chunkBuffer) {
    await this.audioManager.init();
    const audioCtx = this.audioManager.audioCtx;

    // chunkBuffer is an ArrayBuffer of Float32 PCM data
    const float32Data = new Float32Array(chunkBuffer);
    if (float32Data.length === 0) return;

    // Create single-channel AudioBuffer at 24kHz
    const audioBuffer = audioCtx.createBuffer(1, float32Data.length, this.sampleRate);
    audioBuffer.copyToChannel(float32Data, 0);

    const source = audioCtx.createBufferSource();
    source.buffer = audioBuffer;

    // Connect source to shared AnalyserNode for mouth visemes & visualizer, then to master gain
    source.connect(this.audioManager.analyser);

    const currentTime = audioCtx.currentTime;
    // Schedule gapless timeline: if nextStartTime is behind currentTime, catch up with a tiny buffer
    if (this.nextStartTime < currentTime) {
      this.nextStartTime = currentTime + 0.025; // 25ms jitter buffer
    }

    const startTime = this.nextStartTime;
    source.start(startTime);
    this.nextStartTime += audioBuffer.duration;

    this.activeSources.push(source);

    if (!this.isPlaying) {
      this.isPlaying = true;
      if (this.onPlayStart) this.onPlayStart();
    }

    source.onended = () => {
      const idx = this.activeSources.indexOf(source);
      if (idx !== -1) this.activeSources.splice(idx, 1);
      this.checkPlaybackEnded();
    };

    this.resetEndCheck();
  }

  checkPlaybackEnded() {
    const audioCtx = this.audioManager.audioCtx;
    if (this.activeSources.length === 0 && (!audioCtx || audioCtx.currentTime >= this.nextStartTime - 0.05)) {
      if (this.isPlaying) {
        this.isPlaying = false;
        this.nextStartTime = 0;
        if (this.onPlayEnd) this.onPlayEnd();
      }
    }
  }

  resetEndCheck() {
    if (this.endCheckTimer) clearTimeout(this.endCheckTimer);
    const audioCtx = this.audioManager.audioCtx;
    if (!audioCtx) return;

    const remainingTimeMs = Math.max(50, (this.nextStartTime - audioCtx.currentTime) * 1000 + 100);
    this.endCheckTimer = setTimeout(() => {
      this.checkPlaybackEnded();
    }, remainingTimeMs);
  }

  stopAndClear() {
    if (this.endCheckTimer) clearTimeout(this.endCheckTimer);
    this.activeSources.forEach((source) => {
      try {
        source.stop();
        source.disconnect();
      } catch (_) {}
    });
    this.activeSources = [];
    this.nextStartTime = 0;
    if (this.isPlaying) {
      this.isPlaying = false;
      if (this.onPlayEnd) this.onPlayEnd();
    }
    console.log('[PCMPlayer] Playback queue cleared.');
  }
}
