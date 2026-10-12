/**
 * MicRecorder
 * Captures user microphone audio and streams raw Float32 PCM at 16kHz mono to WebSocket.
 */
export class MicRecorder {
  constructor(audioManager, onAudioChunk) {
    this.audioManager = audioManager;
    this.onAudioChunk = onAudioChunk; // Callback receiving Float32Array / ArrayBuffer
    this.mediaStream = null;
    this.sourceNode = null;
    this.processorNode = null;
    this.isRecording = false;
    this.targetSampleRate = 16000;
  }

  async start() {
    if (this.isRecording) return;
    await this.audioManager.init();

    try {
      this.mediaStream = await navigator.mediaDevices.getUserMedia({
        audio: {
          channelCount: 1,
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true
        }
      });

      const audioCtx = this.audioManager.audioCtx;
      this.sourceNode = audioCtx.createMediaStreamSource(this.mediaStream);

      // Buffer size: 2048 samples (~46ms per window at 44.1k/48k)
      const bufferSize = 2048;
      this.processorNode = audioCtx.createScriptProcessor(bufferSize, 1, 1);

      this.processorNode.onaudioprocess = (e) => {
        if (!this.isRecording) return;
        const inputData = e.inputBuffer.getChannelData(0);
        const inputSampleRate = audioCtx.sampleRate;

        // Downsample/resample to 16,000 Hz Float32 PCM
        const resampledData = this.resampleTo16k(inputData, inputSampleRate, this.targetSampleRate);
        if (resampledData && resampledData.length > 0 && this.onAudioChunk) {
          this.onAudioChunk(resampledData.buffer);
        }
      };

      this.sourceNode.connect(this.processorNode);
      this.processorNode.connect(audioCtx.destination);
      this.isRecording = true;
      console.log('[MicRecorder] Started streaming 16kHz Float32 PCM from mic.');
    } catch (err) {
      console.error('[MicRecorder] Failed to start microphone:', err);
      throw err;
    }
  }

  stop() {
    if (!this.isRecording) return;
    this.isRecording = false;

    if (this.processorNode) {
      this.processorNode.disconnect();
      this.processorNode.onaudioprocess = null;
      this.processorNode = null;
    }

    if (this.sourceNode) {
      this.sourceNode.disconnect();
      this.sourceNode = null;
    }

    if (this.mediaStream) {
      this.mediaStream.getTracks().forEach((track) => track.stop());
      this.mediaStream = null;
    }

    console.log('[MicRecorder] Microphone stopped.');
  }

  /**
   * High quality linear interpolation resampler
   */
  resampleTo16k(audioBuffer, sourceSampleRate, targetSampleRate) {
    if (sourceSampleRate === targetSampleRate) {
      return new Float32Array(audioBuffer);
    }

    const ratio = sourceSampleRate / targetSampleRate;
    const newLength = Math.round(audioBuffer.length / ratio);
    const result = new Float32Array(newLength);

    for (let i = 0; i < newLength; i++) {
      const srcPos = i * ratio;
      const leftIdx = Math.floor(srcPos);
      const rightIdx = Math.min(leftIdx + 1, audioBuffer.length - 1);
      const fraction = srcPos - leftIdx;
      result[i] = audioBuffer[leftIdx] * (1 - fraction) + audioBuffer[rightIdx] * fraction;
    }

    return result;
  }
}
