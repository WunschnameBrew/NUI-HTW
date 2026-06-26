// static/js/modules/states.js
// Drives the Natural-UI interaction state machine:
//   idle → listening → thinking → speaking → idle
// A single source of truth that updates ambient feedback (state badge,
// listening rings, mic button) via the body[data-ui-state] attribute.

import { elements } from './dom.js';

const LABELS = {
    idle:      'Online',
    listening: 'Listening',
    thinking:  'Thinking',
    speaking:  'Speaking',
};

let current = 'idle';

export function setUiState(next) {
    if (!LABELS[next] || next === current) {
        // Still allow re-applying labels/classes if forced through a real change
        if (!LABELS[next]) return;
    }
    current = next;

    document.body.dataset.uiState = next;

    if (elements.stateBadge) elements.stateBadge.dataset.state = next;
    if (elements.stateLabel) elements.stateLabel.textContent = LABELS[next];

    // Mic button reflects "listening"
    if (elements.recordButton) {
        elements.recordButton.classList.toggle('recording', next === 'listening');
    }
}

export function getUiState() {
    return current;
}
