// static/js/modules/state.js

// static/js/modules/state.js

export const state = {
    chatHistory: [],
    isLoading: false,
    isRecording: false,
    currentChatMode: 'text', 
    currentImageBase64: null,
    is3DInitialized: false,
	
	// NEW: Session & Privacy
    sessionId: null,          // The DB Key. Null if Memory is OFF.
    lastActiveBackend: 'llm', // 'llm' or 'image'. Used for VRAM UX.
	
	// NEW: Track memory state before Thinking Mode
    preThinkingMemoryState: null,
    
    // Controllers
    abortController: null,
    audioPlayer: null,
    mediaRecorder: null,
    audioChunks: [],
    audioContext: new (window.AudioContext || window.webkitAudioContext)(),
    
    // NEW: Shared Audio Analyzer
    lipSyncAnalyser: null, 
    lipSyncDataArray: null,
    lastAudioTime: 0
};

export function resetState() {
    state.chatHistory = [];
    state.isLoading = false;
    state.isRecording = false;
    state.currentImageBase64 = null;
}