// static/js/app.js
import { elements } from './modules/dom.js';
import { state } from './modules/state.js';
import { PCMPlayer, setupAudioRecorder, processAudioPacket } from './modules/audio.js';
import * as UI from './modules/ui.js';
import * as Network from './modules/network.js';
import { setUiState, getUiState } from './modules/states.js';
import {
    onWindowResize,
    startAnimation,
    loadVRMModel,
    init3DScene,
    applyMoodReaction,
    maintainMoodReaction,
    blendToNeutral,
    getSupportedExpressions,
    getEmotionExpressionMapping,
    setManualExpression,
    clearManualExpression,
    getEmotionRuntimeSnapshot,
    getExpressionValue,
} from './modules/scene.js';

document.addEventListener('DOMContentLoaded', () => {
    init();
});

let moodHoldUntil = 0;

async function init() {
    window.addEventListener('vrm-expressions-updated', () => {
        refreshExpressionPreview();
    });
    window.__koaEmotionDev = {
        getSupportedExpressions: () => getSupportedExpressions(),
        getMapping: () => getEmotionExpressionMapping(),
        getRuntime: () => getEmotionRuntimeSnapshot(),
        getExpressionValue: (name) => getExpressionValue(name),
        previewEmotion: (emotion, intensity = 0.8, confidence = 0.95, valence = 'neutral') => {
            const packet = {
                type: 'emotion',
                emotion,
                intensity,
                confidence,
                valence,
                valence_score: 0,
            };
            const reaction = applyMoodReaction(packet);
            setUiState('speaking');
            maintainMoodReaction();
            updateMoodDebug(packet, reaction);
            moodHoldUntil = Date.now() + reaction.holdMs;
            return reaction;
        },
        simulateLipSync: (volume = 120, durationMs = 600) => {
            const previousAnalyser = state.lipSyncAnalyser;
            const previousData = state.lipSyncDataArray;
            const fakeAnalyser = {
                getByteFrequencyData: (arr) => {
                    for (let i = 0; i < arr.length; i += 1) {
                        arr[i] = Math.max(0, Math.min(255, Number(volume) || 0));
                    }
                },
            };
            state.lipSyncDataArray = new Uint8Array(64);
            state.lipSyncAnalyser = fakeAnalyser;
            setTimeout(() => {
                state.lipSyncAnalyser = previousAnalyser;
                state.lipSyncDataArray = previousData;
            }, Math.max(50, Number(durationMs) || 600));
        },
        clearEmotion: () => {
            blendToNeutral();
            setUiState('idle');
        },
    };

    if (elements.expressionPreviewToggle) {
        elements.expressionPreviewToggle.addEventListener('change', () => {
            setExpressionPreviewVisible(Boolean(elements.expressionPreviewToggle.checked));
        });
        setExpressionPreviewVisible(Boolean(elements.expressionPreviewToggle.checked));
    }

    if (elements.expressionPreviewClear) {
        elements.expressionPreviewClear.addEventListener('click', () => {
            clearManualExpression();
            blendToNeutral();
            refreshExpressionPreview();
        });
    }
    if (!state.sessionId) {
        state.sessionId = `session-${Date.now()}`;
    }

    await loadInitData();

    setupAudioRecorder(sendAudioToServer);
    setupEventListeners();

    window.addEventListener('resize', onWindowResize);
    init3DScene();
    setTimeout(onWindowResize, 100); // let layout settle before sizing the canvas
    startAnimation();

    // Greeting (not persisted to model history)
    UI.addMessageToChat('ai', "Hey — I'm online. Tap the mic to talk, or type below.", false);
    setUiState('idle');

    if (elements.loadingOverlay) {
        setTimeout(() => elements.loadingOverlay.classList.add('hidden'), 1000);
    }
    scheduleExpressionPreviewRefresh();
}

async function loadInitData() {
    try {
        const sysData = await Network.fetchSystemPrompts();
        if (elements.systemPromptSelect && sysData.system_prompts) {
            elements.systemPromptSelect.innerHTML = sysData.system_prompts
                .map(name => `<option value="${name}">${name}</option>`).join('');
        }

        const modelData = await Network.fetchModels();
        if (elements.modelSelect && modelData.models) {
            elements.modelSelect.innerHTML = modelData.models
                .map(name => `<option value="${name}">${name}</option>`).join('');
            const models = modelData.models;
            if (models.length > 0) {
                // Default avatar (falls back to the first available model)
                const defaultModel = '788686174174413810.vrm';
                const def = models.includes(defaultModel) ? defaultModel : models[0];
                elements.modelSelect.value = def;
                loadVRMModel(def);
                scheduleExpressionPreviewRefresh();
            }
        }
    } catch (e) {
        console.error('Init Error', e);
    }
}

/* ===================== Event wiring ===================== */

function setupEventListeners() {
    // Settings drawer
    elements.settingsBtn.addEventListener('click', openSettings);
    elements.closeSettingsBtn.addEventListener('click', closeSettings);
    elements.settingsScrim.addEventListener('click', closeSettings);
    elements.modelSelect.addEventListener('change', (e) => {
        loadVRMModel(e.target.value);
        scheduleExpressionPreviewRefresh();
    });
    // Text input toggle
    elements.textToggleBtn.addEventListener('click', toggleTextInput);

    // Send
    elements.sendBtn.addEventListener('click', handleChat);
    elements.promptInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter' && !state.isLoading) handleChat();
    });

    // Voice
    elements.recordButton.addEventListener('click', toggleRecording);

    // Interrupt / barge-in
    elements.stopBtn.addEventListener('click', stopSpeaking);

    // Chat panel collapse / reopen
    elements.chatCollapseBtn.addEventListener('click', () => setChatCollapsed(true));
    elements.chatReopenBtn.addEventListener('click', () => setChatCollapsed(false));

    // Clear history
    elements.clearChatBtn.addEventListener('click', async () => {
        if (!confirm('Clear chat history?')) return;
        await Network.postClearHistory(state.sessionId || 'default');
        UI.clearChat();
        closeSettings();
    });

    // Esc closes settings
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') closeSettings();
    });

    if (elements.moodDebugToggle) {
        elements.moodDebugToggle.addEventListener('change', () => {
            setMoodDebugVisible(Boolean(elements.moodDebugToggle.checked));
        });
        setMoodDebugVisible(Boolean(elements.moodDebugToggle.checked));
    }
}

function openSettings() {
    elements.settingsPanel.classList.add('active');
    elements.settingsScrim.classList.add('active');
    elements.settingsPanel.setAttribute('aria-hidden', 'false');
}

function closeSettings() {
    elements.settingsPanel.classList.remove('active');
    elements.settingsScrim.classList.remove('active');
    elements.settingsPanel.setAttribute('aria-hidden', 'true');
}

function toggleTextInput() {
    const isHidden = elements.textInputBar.hasAttribute('hidden');
    if (isHidden) {
        elements.textInputBar.removeAttribute('hidden');
        elements.textToggleBtn.classList.add('active');
        elements.promptInput.focus();
    } else {
        elements.textInputBar.setAttribute('hidden', '');
        elements.textToggleBtn.classList.remove('active');
    }
}

function setChatCollapsed(collapsed) {
    elements.chatPanel.classList.toggle('collapsed', collapsed);
    document.body.classList.toggle('chat-collapsed', collapsed);
}

/* ===================== Chat flows ===================== */

async function handleChat() {
    const prompt = elements.promptInput.value.trim();
    if (!prompt || state.isLoading) return;

    elements.promptInput.value = '';
    UI.addMessageToChat('user', prompt);
    UI.setLoading(true);

    try {
        await handleVoiceStream(prompt);
    } catch (error) {
        console.error('Chat Error', error);
    } finally {
        UI.setLoading(false);
    }
}

async function handleVoiceStream(prompt) {
    const payload = {
        prompt,
        history: state.chatHistory,
        system_prompt_name: elements.systemPromptSelect.value,
        use_memory: elements.memoryToggle.checked,
        session_id: state.sessionId || 'default',
    };

    setUiState('thinking');
    const aiBubble = UI.addStreamingMessage();

    if (state.audioContext.state === 'suspended') await state.audioContext.resume();
    state.audioPlayer = new PCMPlayer(state.audioContext);

    state.abortController = new AbortController();
    let fullReply = '';
    let started = false;

    try {
        const response = await Network.postVoiceStream(payload, state.abortController.signal);
        const reader = response.body.getReader();
        const decoder = new TextDecoder('utf-8');
        let buffer = '';

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split('\n');
            buffer = lines.pop();

            for (const line of lines) {
                if (!line.trim()) continue;
                const packet = JSON.parse(line);

                if (packet.type === 'emotion') {
                    const reaction = applyMoodReaction(packet);
                    updateMoodDebug(packet, reaction);

                    moodHoldUntil = Date.now() + reaction.holdMs;
                } else if (packet.type === 'text') {
                    if (!started) {
                        started = true;
                        setUiState('speaking');
                        maintainMoodReaction();
                        UI.beginStreaming(aiBubble);
                    }
                    UI.appendToBubble(aiBubble, packet.content);
                    fullReply += packet.content;
                } else if (packet.type === 'audio') {
                    const float32Data = processAudioPacket(packet);
                    state.audioPlayer.playChunk(float32Data);
                }
            }
        }

        UI.endStreaming(aiBubble);
        if (fullReply) state.chatHistory.push({ role: 'assistant', content: fullReply });
    } catch (error) {
        if (error.name === 'AbortError') {
            UI.endStreaming(aiBubble, fullReply || '(stopped)');
        } else {
            console.error('Stream Error', error);
            UI.endStreaming(aiBubble, (fullReply + ' …connection lost.').trim());
        }
    } finally {
        state.abortController = null;
        setUiState('idle');
        const remainingHold = Math.max(0, moodHoldUntil - Date.now());
        setTimeout(() => blendToNeutral(), Math.min(remainingHold + 250, 2300));
    }
}

function stopSpeaking() {
    if (state.abortController) {
        state.abortController.abort();
        state.abortController = null;
    }
    if (state.audioPlayer) state.audioPlayer.stop();
    setUiState('idle');
}

function setMoodDebugVisible(visible) {
    if (!elements.moodDebug) return;
    elements.moodDebug.hidden = !visible;
}

function setExpressionPreviewVisible(visible) {
    if (!elements.expressionPreviewPanel) return;
    elements.expressionPreviewPanel.hidden = !visible;
    if (visible) refreshExpressionPreview();
}

function scheduleExpressionPreviewRefresh() {
    setTimeout(refreshExpressionPreview, 300);
    setTimeout(refreshExpressionPreview, 900);
}

function refreshExpressionPreview() {
    if (!elements.expressionPreviewList || !elements.expressionPreviewLog) return;

    const supported = getSupportedExpressions();
    const mapping = getEmotionExpressionMapping();

    elements.expressionPreviewList.innerHTML = '';
    if (!supported.length) {
        elements.expressionPreviewLog.textContent = 'Expressions unavailable. Ensure a VRM with expression clips is loaded.';
        return;
    }

    const mappingText = ['happy', 'sad', 'angry', 'worried', 'surprised', 'neutral']
        .map((emo) => `${emo}:${mapping[emo] || 'neutral'}`)
        .join(' | ');
    elements.expressionPreviewLog.textContent = `supported: ${supported.length} | ${mappingText}`;

    supported.forEach((name) => {
        const chip = document.createElement('button');
        chip.type = 'button';
        chip.className = 'expression-chip';
        chip.textContent = name;
        chip.addEventListener('click', () => {
            [...elements.expressionPreviewList.querySelectorAll('.expression-chip.active')].forEach((node) => node.classList.remove('active'));
            chip.classList.add('active');
            setManualExpression(name, 0.95);
        });
        elements.expressionPreviewList.appendChild(chip);
    });

    console.groupCollapsed('Expression preview report');
    console.info('Supported expressions:', supported);
    console.table(mapping);
    console.groupEnd();
}

function updateMoodDebug(packet, reaction) {
    if (!elements.moodDebug || elements.moodDebug.hidden) return;

    const emotion = (packet?.emotion || 'neutral').toLowerCase();
    const valence = (packet?.valence || 'neutral').toLowerCase();
    const valenceScore = Number(packet?.valence_score ?? 0);
    const confidence = Number(packet?.confidence ?? 0);

    if (elements.moodDebugEmotion) {
        elements.moodDebugEmotion.textContent = `emotion: ${emotion}`;
    }
    if (elements.moodDebugValence) {
        elements.moodDebugValence.textContent = `valence: ${valence} (${Number.isFinite(valenceScore) ? valenceScore.toFixed(2) : '0.00'})`;
    }
    if (elements.moodDebugConfidence) {
        const base = `confidence: ${Number.isFinite(confidence) ? confidence.toFixed(2) : '0.00'}`;
        elements.moodDebugConfidence.textContent = reaction?.expressionName ? `${base} -> ${reaction.expressionName}` : `${base} -> neutral`;
    }
}

/* ===================== Voice capture ===================== */

function toggleRecording() {
    if (state.isRecording) {
        if (state.mediaRecorder) state.mediaRecorder.stop();
        state.isRecording = false;
        // onstop → sendAudioToServer() will move us to "thinking"
    } else {
        if (getUiState() === 'speaking') stopSpeaking(); // barge-in
        if (!state.mediaRecorder || state.mediaRecorder.state === 'inactive') {
            setupAudioRecorder(sendAudioToServer);
        }
        setTimeout(() => {
            if (state.mediaRecorder && state.mediaRecorder.state === 'inactive') {
                state.audioChunks = [];
                state.mediaRecorder.start();
                state.isRecording = true;
                setUiState('listening');
            }
        }, 200);
    }
}

async function sendAudioToServer() {
    setUiState('thinking');
    const recordedBlob = new Blob(state.audioChunks, { type: 'audio/webm' });
    const audioBlob = await convertBlobToWav(recordedBlob);
    const formData = new FormData();
    formData.append('audio_file', audioBlob, 'recording.wav');

    try {
        const data = await Network.postTranscribe(formData);
        if (data?.error) {
            UI.addMessageToChat('ai', `Microphone transcription is unavailable: ${data.error}`, false);
            setUiState('idle');
            return;
        }
        if (data.transcription && data.transcription.trim()) {
            UI.addMessageToChat('user', data.transcription);
            await handleVoiceStream(data.transcription);
        } else {
            UI.addMessageToChat('ai', 'I could not detect speech from the microphone input. Please try again.', false);
            setUiState('idle'); // nothing recognized
        }
    } catch (e) {
        console.error('Transcription Error', e);
        UI.addMessageToChat('ai', 'Microphone transcription request failed. Please verify Whisper setup and try again.', false);
        setUiState('idle');
    }
}

async function convertBlobToWav(inputBlob) {
    try {
        const arr = await inputBlob.arrayBuffer();
        const decoded = await state.audioContext.decodeAudioData(arr.slice(0));
        const wav = audioBufferToWav(decoded);
        return new Blob([wav], { type: 'audio/wav' });
    } catch (err) {
        console.warn('WAV conversion failed, using recorded blob as-is:', err);
        return inputBlob;
    }
}

function audioBufferToWav(audioBuffer) {
    const numChannels = audioBuffer.numberOfChannels;
    const sampleRate = audioBuffer.sampleRate;
    const format = 1; // PCM
    const bitDepth = 16;
    const channelData = [];
    for (let c = 0; c < numChannels; c++) {
        channelData.push(audioBuffer.getChannelData(c));
    }

    const blockAlign = numChannels * bitDepth / 8;
    const byteRate = sampleRate * blockAlign;
    const dataLength = audioBuffer.length * blockAlign;
    const buffer = new ArrayBuffer(44 + dataLength);
    const view = new DataView(buffer);

    let offset = 0;
    const writeString = (str) => {
        for (let i = 0; i < str.length; i++) {
            view.setUint8(offset + i, str.charCodeAt(i));
        }
        offset += str.length;
    };

    writeString('RIFF');
    view.setUint32(offset, 36 + dataLength, true); offset += 4;
    writeString('WAVE');
    writeString('fmt ');
    view.setUint32(offset, 16, true); offset += 4;
    view.setUint16(offset, format, true); offset += 2;
    view.setUint16(offset, numChannels, true); offset += 2;
    view.setUint32(offset, sampleRate, true); offset += 4;
    view.setUint32(offset, byteRate, true); offset += 4;
    view.setUint16(offset, blockAlign, true); offset += 2;
    view.setUint16(offset, bitDepth, true); offset += 2;
    writeString('data');
    view.setUint32(offset, dataLength, true); offset += 4;

    let pos = offset;
    for (let i = 0; i < audioBuffer.length; i++) {
        for (let c = 0; c < numChannels; c++) {
            const sample = Math.max(-1, Math.min(1, channelData[c][i]));
            view.setInt16(pos, sample < 0 ? sample * 0x8000 : sample * 0x7fff, true);
            pos += 2;
        }
    }
    return buffer;
}
