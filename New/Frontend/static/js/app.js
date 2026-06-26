// static/js/app.js
import { elements } from './modules/dom.js';
import { state } from './modules/state.js';
import { PCMPlayer, setupAudioRecorder, processAudioPacket } from './modules/audio.js';
import * as UI from './modules/ui.js';
import * as Network from './modules/network.js';
import { setUiState, getUiState } from './modules/states.js';
import { onWindowResize, startAnimation, loadVRMModel, init3DScene, playAnimation } from './modules/scene.js';

document.addEventListener('DOMContentLoaded', () => {
    init();
});

async function init() {
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

    // Avatar model switch
    elements.modelSelect.addEventListener('change', (e) => loadVRMModel(e.target.value));

    // Clear history
    elements.clearChatBtn.addEventListener('click', async () => {
        if (!confirm('Clear chat history?')) return;
        await Network.postClearHistory();
        UI.clearChat();
        closeSettings();
    });

    // Esc closes settings
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') closeSettings();
    });
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

                if (packet.type === 'text') {
                    if (!started) {
                        started = true;
                        setUiState('speaking');
                        playAnimation('taunt'); // gesture while talking
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
        playAnimation('neutral'); // return to resting idle
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
    const audioBlob = new Blob(state.audioChunks, { type: 'audio/webm' });
    const formData = new FormData();
    formData.append('audio_file', audioBlob, 'recording.webm');

    try {
        const data = await Network.postTranscribe(formData);
        if (data.transcription && data.transcription.trim()) {
            UI.addMessageToChat('user', data.transcription);
            await handleVoiceStream(data.transcription);
        } else {
            setUiState('idle'); // nothing recognized
        }
    } catch (e) {
        console.error('Transcription Error', e);
        setUiState('idle');
    }
}
