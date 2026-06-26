// static/js/modules/dom.js

export const elements = {
    // Shell / stage
    app:            document.getElementById('app'),
    sceneContainer: document.getElementById('scene-container'),
    loadingOverlay: document.getElementById('loading-overlay'),

    // Top bar
    topBar:         document.getElementById('top-bar'),
    stateBadge:     document.getElementById('state-badge'),
    stateLabel:     document.querySelector('#state-badge .state-label'),
    settingsBtn:    document.getElementById('settings-btn'),

    // Chat panel
    chatPanel:       document.getElementById('chat-panel'),
    chatWindow:      document.getElementById('chat-window'),
    chatCollapseBtn: document.getElementById('chat-collapse-btn'),
    chatReopenBtn:   document.getElementById('chat-reopen'),

    // Dock
    textInputBar:  document.getElementById('text-input-bar'),
    promptInput:   document.getElementById('prompt-input'),
    sendBtn:       document.getElementById('send-btn'),
    controlCluster:document.getElementById('control-cluster'),
    recordButton:  document.getElementById('record-btn'),
    textToggleBtn: document.getElementById('text-toggle-btn'),
    stopBtn:       document.getElementById('stop-btn'),

    // Settings drawer
    settingsPanel:     document.getElementById('settings-panel'),
    settingsScrim:     document.getElementById('settings-scrim'),
    closeSettingsBtn:  document.getElementById('close-settings'),
    memoryToggle:      document.getElementById('memory-toggle'),
    systemPromptSelect:document.getElementById('system-prompt-select'),
    modelSelect:       document.getElementById('model-select'),
    clearChatBtn:      document.getElementById('clear-chat-btn'),
};
