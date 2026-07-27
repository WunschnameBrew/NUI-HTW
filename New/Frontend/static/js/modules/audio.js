// static/js/modules/audio.js
import { state } from './state.js';
import { elements } from './dom.js';

export class PCMPlayer {
    constructor(context) {
        this.context = context;
        this.nextStartTime = 0;
        this.isPlaying = true;
        this.activeSources = [];
        
        // Robust Analyzer setup for Lip Sync
        this.analyser = this.context.createAnalyser();
        this.analyser.fftSize = 2048; 
        this.analyser.smoothingTimeConstant = 0.5;
        this.bufferLength = this.analyser.frequencyBinCount;
        this.dataArray = new Uint8Array(this.bufferLength);
        
        // Share with State so scene.js can see it
        state.lipSyncAnalyser = this.analyser;
        state.lipSyncDataArray = this.dataArray;
    }

    playChunk(float32Array) {
        if (!this.isPlaying) return; 

        // Mobile "Wake Up" - If context is suspended, resume it!
        if (this.context.state === 'suspended') {
            this.context.resume();
        }

        // Piper "Amy" is 22050Hz. If static occurs, try 16000 or 24000.
        const piperSampleRate = 22050; 
        
        const buffer = this.context.createBuffer(1, float32Array.length, piperSampleRate);
        buffer.copyToChannel(float32Array, 0);
        
        const source = this.context.createBufferSource();
        source.buffer = buffer;
        
        // Connect Source -> Analyser -> Speakers
        source.connect(this.analyser);
        this.analyser.connect(this.context.destination);

        const now = this.context.currentTime;
        const schedulingDelay = 0.05; 
        
        if (this.nextStartTime < now) this.nextStartTime = now + schedulingDelay;
        
        source.start(this.nextStartTime);
        this.nextStartTime += buffer.duration;
        this.activeSources.push(source);

        source.onended = () => {
            const idx = this.activeSources.indexOf(source);
            if (idx !== -1) {
                this.activeSources.splice(idx, 1);
            }
        };
    }

    hasAudioPlaying() {
        return this.isPlaying && (this.activeSources.length > 0 || this.nextStartTime > this.context.currentTime + 0.05);
    }

    stop() {
        this.isPlaying = false;
        for (const source of this.activeSources) {
            try {
                source.stop(0);
                source.disconnect();
            } catch (_e) {}
        }
        this.activeSources = [];
        this.nextStartTime = 0;
        if (this.context && typeof this.context.suspend === 'function') {
            try {
                this.context.suspend().then(() => {
                    if (this.context.state === 'suspended') {
                        this.context.resume();
                    }
                });
            } catch (_e) {}
        }
    }
}

export function setupAudioRecorder(onStopCallback) {
    if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
        navigator.mediaDevices.getUserMedia({ audio: true })
            .then(stream => {
                state.mediaRecorder = new MediaRecorder(stream);
                state.mediaRecorder.ondataavailable = e => state.audioChunks.push(e.data);
                state.mediaRecorder.onstop = onStopCallback;
            })
            .catch(err => {
                console.error("Mic Error:", err);
                if(elements.recordButton) {
                    elements.recordButton.disabled = true;
                    elements.recordButton.title = "Mic not available";
                }
            });
    }
}

// --- THIS WAS MISSING PREVIOUSLY ---
export function processAudioPacket(packet) {
    // 1. Decode Base64 string to binary string
    const binaryString = atob(packet.data);
    
    // 2. Convert binary string to byte array (Uint8)
    const bytes = new Uint8Array(binaryString.length);
    for (let i = 0; i < binaryString.length; i++) {
        bytes[i] = binaryString.charCodeAt(i);
    }
    
    // 3. Convert bytes to 16-bit PCM (Int16)
    const int16Data = new Int16Array(bytes.buffer);
    
    // 4. Convert Int16 to Float32 (Range -1.0 to 1.0) for Web Audio API
    const float32Data = new Float32Array(int16Data.length);
    for (let i = 0; i < int16Data.length; i++) {
        float32Data[i] = int16Data[i] / 32768.0;
    }
    
    return float32Data;
}