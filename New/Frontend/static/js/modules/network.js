// static/js/modules/network.js

export async function fetchSystemPrompts() {
    const response = await fetch('/get_system_prompts');
    return await response.json();
}

export async function fetchModels() {
    const response = await fetch('/get_models');
    return await response.json();
}

export async function postVoiceStream(payload, signal) {
    const response = await fetch('/chat_voice_stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
        signal,
    });
    if (!response.ok) throw new Error('Stream failed');
    return response;
}

export async function postTranscribe(formData) {
    const response = await fetch('/transcribe', { method: 'POST', body: formData });
    return await response.json();
}

export async function postClearHistory(sessionId = 'default') {
    const response = await fetch('/clear_history', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: sessionId }),
    });
    return await response.json();
}
