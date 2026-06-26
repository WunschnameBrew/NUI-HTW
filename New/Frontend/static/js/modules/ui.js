// static/js/modules/ui.js
import { elements } from './dom.js';
import { state } from './state.js';

const SPARKLES_SVG = `<svg class="spark" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M9.94 14.06A2 2 0 0 0 8.5 12.6l-5.2-1.35a.5.5 0 0 1 0-.97L8.5 8.94A2 2 0 0 0 9.94 7.5l1.35-5.2a.5.5 0 0 1 .97 0l1.35 5.2A2 2 0 0 0 15.06 8.94l5.2 1.34a.5.5 0 0 1 0 .97l-5.2 1.35a2 2 0 0 0-1.45 1.46l-1.35 5.2a.5.5 0 0 1-.97 0z"/></svg>`;

function scrollToBottom() {
    if (elements.chatWindow) elements.chatWindow.scrollTop = elements.chatWindow.scrollHeight;
}

function clearEmptyState() {
    const empty = elements.chatWindow?.querySelector('.chat-empty');
    if (empty) empty.remove();
}

export function setLoading(isLoading) {
    state.isLoading = isLoading;
    if (elements.promptInput) elements.promptInput.disabled = isLoading;
    if (elements.sendBtn) elements.sendBtn.disabled = isLoading;
}

export function renderEmptyState() {
    if (!elements.chatWindow) return;
    elements.chatWindow.innerHTML =
        `<div class="chat-empty">${SPARKLES_SVG}<div>Tap the mic to talk, or type below — Koa is listening.</div></div>`;
}

function buildRole(role) {
    const el = document.createElement('div');
    el.className = 'role';
    if (role === 'user') {
        el.textContent = 'You';
    } else {
        el.innerHTML = `<span class="avatar-mark" aria-hidden="true"></span> Koa`;
    }
    return el;
}

// Adds a complete message. Returns the .bubble element.
export function addMessageToChat(role, text, saveToHistory = true) {
    clearEmptyState();

    const wrap = document.createElement('div');
    wrap.className = `message ${role === 'user' ? 'user-message' : 'ai-message'}`;

    const bubble = document.createElement('div');
    bubble.className = 'bubble';
    bubble.textContent = text;

    wrap.appendChild(buildRole(role));
    wrap.appendChild(bubble);
    elements.chatWindow.appendChild(wrap);
    scrollToBottom();

    if (text && saveToHistory) {
        state.chatHistory.push({ role: role === 'user' ? 'user' : 'assistant', content: text });
    }
    return bubble;
}

// Adds an AI message that starts as a typing indicator. Returns the .bubble
// element. Call beginStreaming(bubble) once the first token arrives.
export function addStreamingMessage() {
    clearEmptyState();

    const wrap = document.createElement('div');
    wrap.className = 'message ai-message';

    const bubble = document.createElement('div');
    bubble.className = 'bubble';
    bubble.innerHTML = `<span class="typing" aria-label="Koa is thinking"><span></span><span></span><span></span></span>`;

    wrap.appendChild(buildRole('ai'));
    wrap.appendChild(bubble);
    elements.chatWindow.appendChild(wrap);
    scrollToBottom();
    return bubble;
}

// Switches a streaming bubble from "thinking" dots to live text.
export function beginStreaming(bubble) {
    if (!bubble) return;
    bubble.innerHTML = '';
    bubble.textContent = '';
    bubble.classList.add('streaming');
}

export function appendToBubble(bubble, chunk) {
    if (!bubble) return;
    bubble.textContent += chunk;
    scrollToBottom();
}

export function endStreaming(bubble, fallbackText) {
    if (!bubble) return;
    bubble.classList.remove('streaming');
    if (!bubble.textContent.trim() && fallbackText) {
        bubble.textContent = fallbackText;
    }
}

export function clearChat() {
    if (!elements.chatWindow) return;
    elements.chatWindow.innerHTML = '';
    state.chatHistory = [];
    renderEmptyState();
}
