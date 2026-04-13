/**
 * Audio capture and playback utilities for voice mode.
 *
 * AudioCapture  — records mic input as Int16 PCM at 16 kHz
 * AudioPlayback — plays back Int16 PCM chunks from the agent
 *
 * Both use the Web Audio API. Capture uses ScriptProcessorNode
 * (widely supported) with downsampling from native rate to 16 kHz.
 */

const TARGET_SAMPLE_RATE = 16000;
const PLAYBACK_SAMPLE_RATE = 24000;


// ---------------------------------------------------------------------------
// AudioCapture — mic → Int16 PCM at 16 kHz
// ---------------------------------------------------------------------------

class AudioCapture {
    constructor() {
        this.ondata = null;     // callback(ArrayBuffer) — Int16 PCM chunk
        this.onlevel = null;    // callback(Number 0-1) — audio level
        this._ctx = null;
        this._stream = null;
        this._processor = null;
        this._analyser = null;
        this._levelBuf = null;
        this._levelTimer = null;
    }

    async start() {
        // Clean up any previous session
        this.stop();

        // Get mic stream at native sample rate
        this._stream = await navigator.mediaDevices.getUserMedia({
            audio: {
                channelCount: 1,
                echoCancellation: true,
                noiseSuppression: true,
                autoGainControl: true,
            },
        });

        // Use browser's native sample rate (typically 48 kHz)
        this._ctx = new AudioContext();
        if (this._ctx.state === 'suspended') {
            await this._ctx.resume();
        }
        const nativeRate = this._ctx.sampleRate;
        console.log('[Audio] Capture sample rate:', nativeRate);

        const source = this._ctx.createMediaStreamSource(this._stream);

        // ScriptProcessorNode for reliable cross-browser support
        const bufferSize = 4096;
        this._processor = this._ctx.createScriptProcessor(bufferSize, 1, 1);

        this._processor.onaudioprocess = (e) => {
            const float32 = e.inputBuffer.getChannelData(0);

            // Downsample to 16 kHz
            const downsampled = _downsample(float32, nativeRate, TARGET_SAMPLE_RATE);

            // Convert Float32 → Int16
            const int16 = new Int16Array(downsampled.length);
            for (let i = 0; i < downsampled.length; i++) {
                const s = Math.max(-1, Math.min(1, downsampled[i]));
                int16[i] = s < 0 ? s * 0x8000 : s * 0x7FFF;
            }

            if (this.ondata) this.ondata(int16.buffer);
        };

        source.connect(this._processor);
        this._processor.connect(this._ctx.destination);

        // Analyser for level metering
        this._analyser = this._ctx.createAnalyser();
        this._analyser.fftSize = 256;
        source.connect(this._analyser);
        this._levelBuf = new Uint8Array(this._analyser.frequencyBinCount);
        this._levelTimer = setInterval(() => this._emitLevel(), 50);
    }

    stop() {
        if (this._levelTimer) {
            clearInterval(this._levelTimer);
            this._levelTimer = null;
        }
        if (this._processor) {
            this._processor.disconnect();
            this._processor = null;
        }
        if (this._stream) {
            this._stream.getTracks().forEach(t => t.stop());
            this._stream = null;
        }
        if (this._ctx) {
            this._ctx.close();
            this._ctx = null;
        }
    }

    _emitLevel() {
        if (!this._analyser || !this.onlevel) return;
        this._analyser.getByteFrequencyData(this._levelBuf);
        let sum = 0;
        for (let i = 0; i < this._levelBuf.length; i++) sum += this._levelBuf[i];
        const avg = sum / this._levelBuf.length / 255;
        this.onlevel(avg);
    }
}


/** Downsample Float32 audio from srcRate to dstRate using linear interpolation. */
function _downsample(buffer, srcRate, dstRate) {
    if (srcRate === dstRate) return buffer;
    const ratio = srcRate / dstRate;
    const newLength = Math.round(buffer.length / ratio);
    const result = new Float32Array(newLength);
    for (let i = 0; i < newLength; i++) {
        const srcIdx = i * ratio;
        const lo = Math.floor(srcIdx);
        const hi = Math.min(lo + 1, buffer.length - 1);
        const frac = srcIdx - lo;
        result[i] = buffer[lo] * (1 - frac) + buffer[hi] * frac;
    }
    return result;
}


// ---------------------------------------------------------------------------
// AudioPlayback — Int16 PCM from agent → speakers
// ---------------------------------------------------------------------------

class AudioPlayback {
    constructor() {
        this._ctx = null;
        this._nextTime = 0;
    }

    _ensureContext() {
        if (!this._ctx) {
            this._ctx = new AudioContext({ sampleRate: PLAYBACK_SAMPLE_RATE });
            this._nextTime = 0;
        }
        if (this._ctx.state === 'suspended') {
            this._ctx.resume();
        }
    }

    /**
     * Feed a chunk of Int16 PCM audio (ArrayBuffer) for playback.
     * Chunks are scheduled back-to-back for gapless audio.
     */
    feed(pcmBuffer) {
        this._ensureContext();

        const int16 = new Int16Array(pcmBuffer);
        const numSamples = int16.length;
        if (numSamples === 0) return;

        // Convert Int16 → Float32
        const float32 = new Float32Array(numSamples);
        for (let i = 0; i < numSamples; i++) {
            float32[i] = int16[i] / 0x8000;
        }

        const buffer = this._ctx.createBuffer(1, numSamples, PLAYBACK_SAMPLE_RATE);
        buffer.getChannelData(0).set(float32);

        const source = this._ctx.createBufferSource();
        source.buffer = buffer;
        source.connect(this._ctx.destination);

        // Schedule gapless playback
        const now = this._ctx.currentTime;
        const startTime = Math.max(now, this._nextTime);
        source.start(startTime);
        this._nextTime = startTime + buffer.duration;
    }

    /** True if audio is still scheduled for playback. */
    isPlaying() {
        return this._ctx != null && this._ctx.currentTime < this._nextTime;
    }

    /** Stop all pending audio and reset the schedule. */
    stop() {
        if (this._ctx) {
            this._ctx.close();
            this._ctx = null;
            this._nextTime = 0;
        }
    }
}
