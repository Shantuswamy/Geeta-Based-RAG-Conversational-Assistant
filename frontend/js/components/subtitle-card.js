/**
 * SubtitleCard
 * Handles progressive caption updates, chapter references, and live audio waveform equalizer bars.
 */
export class SubtitleCard {
  constructor(audioManager) {
    this.audioManager = audioManager;
    this.textEl = document.getElementById('subtitle-text');
    this.speakerTag = document.getElementById('speaker-tag');
    this.waveformEl = document.getElementById('waveform-container');
    this.verseChip = document.getElementById('verse-chip-text');

    this.bars = [];
    this.barCount = 7;
    this.visualizerFrameId = null;
    this.fullTextBuffer = '';
  }

  init() {
    this.initWaveform();
    this.startVisualizer();
  }

  initWaveform() {
    if (!this.waveformEl) return;
    this.waveformEl.innerHTML = '';
    this.bars = [];

    for (let i = 0; i < this.barCount; i++) {
      const bar = document.createElement('div');
      bar.className = 'waveform-bar';
      this.waveformEl.appendChild(bar);
      this.bars.push(bar);
    }
  }

  startVisualizer() {
    const update = () => {
      const freqData = this.audioManager.getFrequencyData();
      if (freqData && freqData.length > 0 && this.bars.length > 0) {
        const step = Math.floor(freqData.length / this.barCount);
        for (let i = 0; i < this.barCount; i++) {
          const val = freqData[i * step] || 0;
          const normalized = val / 255.0;
          const height = Math.max(3, Math.round(normalized * 18));
          this.bars[i].style.height = `${height}px`;
          this.bars[i].style.opacity = Math.max(0.25, normalized * 0.9 + 0.1).toFixed(2);
        }
      } else {
        for (let i = 0; i < this.bars.length; i++) {
          this.bars[i].style.height = '3px';
          this.bars[i].style.opacity = '0.25';
        }
      }
      this.visualizerFrameId = requestAnimationFrame(update);
    };
    this.visualizerFrameId = requestAnimationFrame(update);
  }

  setText(text, isUser = false) {
    if (!this.textEl) return;
    this.fullTextBuffer = text;

    if (isUser) {
      if (this.speakerTag) this.speakerTag.textContent = 'You (Seeker)';
      this.textEl.style.fontStyle = 'normal';
      this.textEl.textContent = `"${text}"`;
    } else {
      if (this.speakerTag) this.speakerTag.textContent = 'Shri Krishna';
      this.textEl.style.fontStyle = 'italic';
      this.textEl.textContent = text.startsWith('"') ? text : `"${text}"`;
    }
  }

  appendStreamingText(chunk) {
    if (!this.textEl) return;
    this.fullTextBuffer += chunk;
    this.textEl.textContent = `"${this.fullTextBuffer}"`;
  }

  clear() {
    this.fullTextBuffer = '';
    if (this.textEl) this.textEl.textContent = '...';
  }

  setVerse(verse) {
    if (this.verseChip) {
      this.verseChip.textContent = verse;
    }
  }
}
