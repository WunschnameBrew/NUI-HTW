// static/js/modules/scene.js
/*
 * ==========================================================================
 * ANIMATION SYSTEM CREDITS
 * VRMA structure and conversion logic adapted from: 
 * https://github.com/tk256ailab/fbx2vrma-converter
 * ==========================================================================
 */

import { elements } from './dom.js'; 
import { state } from './state.js';

const ANIMATION_PATH = '/static/assets/animations/converted_gltf/';
const INDEX_PATH = '/static/assets/animations/index.md';
let animationDB = {}; 

let scene, camera, renderer, controls;
let currentVrm = null;
let currentMixer = null; 
let clock = new THREE.Clock(); 
let isAnimating = false;
let activeBodyCategory = 'neutral';
let availableExpressions = new Set();
let resolvedEmotionMap = {
    happy: null,
    sad: null,
    angry: null,
    worried: null,
    surprised: null,
    neutral: null,
};

const SAFE_CONFIDENCE = 0.45;
const EMOTION_ALIASES = {
    happy: ['happy', 'joy', 'smile', 'relaxed'],
    sad: ['sad', 'sorrow'],
    angry: ['angry', 'mad'],
    worried: ['worried', 'sad', 'surprised'],
    surprised: ['surprised', 'shock'],
    neutral: ['neutral', 'relaxed'],
};
const NON_EMOTION_EXPRESSIONS = new Set([
    'aa', 'ih', 'ou', 'ee', 'oh',
    'blink', 'blinkleft', 'blinkright',
    'lookup', 'lookdown', 'lookleft', 'lookright',
]);

const emotionBlendState = {
    activeName: null,
    targetWeight: 0,
    currentWeight: 0,
    releaseAt: 0,
    manualLock: false,
};

// Helpers
let blinkTimer = 0;
let saccadeTimer = 0;
let eyeTarget = new THREE.Vector3();
let currentEyeLook = new THREE.Vector3();

function getExpressionController() {
    return currentVrm?.expressionManager || currentVrm?.blendShapeProxy || null;
}

export function init3DScene() {
    const container = elements.sceneContainer;
    if (!container) return;

    scene = new THREE.Scene();
    
    camera = new THREE.PerspectiveCamera(30.0, container.clientWidth / container.clientHeight, 0.1, 50.0);
    camera.position.set(0.0, 1.4, 2.5); 

    renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true });
    renderer.setPixelRatio(window.devicePixelRatio);
    const width = container.clientWidth || window.innerWidth;
    const height = container.clientHeight || (window.innerHeight / 2);
    renderer.setSize(width, height);
    renderer.outputEncoding = THREE.sRGBEncoding; 
    renderer.toneMapping = THREE.ACESFilmicToneMapping; 
    renderer.domElement.style.position = 'absolute';
    renderer.domElement.style.top = '0';
    renderer.domElement.style.left = '0';
    renderer.domElement.style.width = '100%';
    renderer.domElement.style.height = '100%';
    container.appendChild(renderer.domElement);

    const dirLight = new THREE.DirectionalLight(0xffffff, 0.8);
    dirLight.position.set(-1, 2, 2);
    scene.add(dirLight);
    scene.add(new THREE.AmbientLight(0xffffff, 0.6));

    controls = new THREE.OrbitControls(camera, renderer.domElement);
    controls.target.set(0.0, 1.2, 0.0); 
    controls.enablePan = true;
    controls.update();

    loadAnimationIndex(); 
    
    state.is3DInitialized = true;
    startAnimation();
}

async function loadAnimationIndex() {
    try {
        const text = await fetch(`${INDEX_PATH}?t=${Date.now()}`).then(r => r.text());
        let cat = 'neutral';
        animationDB['neutral'] = [];
        
        text.split('\n').forEach(line => {
            line = line.trim();
            if (!line) return;
            if (line.startsWith('#')) {
                cat = line.replace(/[#:]/g, '').trim().toLowerCase();
                if (!animationDB[cat]) animationDB[cat] = [];
            } 
            else if (line.startsWith('-')) {
                const parts = line.replace(/^-/, '').trim().split(' ');
                const ints = parseFloat(parts.pop());
                if (animationDB[cat]) animationDB[cat].push({ file: parts.join(' '), intensity: ints });
            }
        });
    } catch(e) { console.error("Index Load Error:", e); }
}

export function loadVRMModel(filename) {
    if (!scene) {
        init3DScene();
    }
    if (currentVrm) {
        scene.remove(currentVrm.scene);
        THREE_VRM.VRMUtils.deepDispose(currentVrm.scene);
        currentVrm = null;
    }
    const loader = new THREE.GLTFLoader();
    loader.register((parser) => new THREE_VRM.VRMLoaderPlugin(parser));

    loader.load(`/static/assets/${filename}`, (gltf) => {
        const vrm = gltf.userData.vrm;
        THREE_VRM.VRMUtils.removeUnnecessaryJoints(gltf.scene);
        vrm.scene.rotation.y = Math.PI;
        scene.add(vrm.scene);
        currentVrm = vrm;
        currentMixer = new THREE.AnimationMixer(currentVrm.scene);
        syncAvailableExpressions();
        updateVibe([0,0,0]); 
        if (!getExpressionController()) {
            console.warn('VRM expression controller unavailable on this model. Emotion reactions will remain neutral.');
        }
    });
}

function syncAvailableExpressions() {
    availableExpressions = new Set();
    const manager = getExpressionController();
    if (!manager) return;

    const registerName = (name) => {
        const normalized = String(name || '').toLowerCase().trim();
        if (normalized) availableExpressions.add(normalized);
    };

    const expressionMap = manager.expressionMap || manager._expressionMap || null;
    if (expressionMap instanceof Map) {
        expressionMap.forEach((value, key) => {
            registerName(key);
            registerName(value?.expressionName);
            registerName(value?.presetName);
        });
    } else if (expressionMap && typeof expressionMap === 'object') {
        Object.entries(expressionMap).forEach(([key, value]) => {
            registerName(key);
            registerName(value?.expressionName);
            registerName(value?.presetName);
        });
    }

    const expressions = manager.expressions || manager._expressions || [];
    if (Array.isArray(expressions)) {
        expressions.forEach((expr) => {
            registerName(expr?.expressionName);
            registerName(expr?.presetName);
            registerName(expr?.name);
        });
    }

    ['neutral', 'happy', 'angry', 'sad', 'relaxed', 'surprised', 'aa', 'ih', 'ou', 'ee', 'oh', 'blink']
        .forEach((candidate) => {
            if (typeof manager.getValue === 'function') {
                try {
                    const value = manager.getValue(candidate);
                    if (value !== undefined && value !== null) registerName(candidate);
                } catch (_e) {
                    // Probe only.
                }
            }
        });

    const legacyPresetMap = manager.blendShapePresetMap || manager._blendShapePresetMap || null;
    if (legacyPresetMap instanceof Map) {
        legacyPresetMap.forEach((_value, key) => registerName(key));
    } else if (legacyPresetMap && typeof legacyPresetMap === 'object') {
        Object.keys(legacyPresetMap).forEach((key) => registerName(key));
    }

    resolvedEmotionMap = {
        happy: resolveExpressionName('happy'),
        sad: resolveExpressionName('sad'),
        angry: resolveExpressionName('angry'),
        worried: resolveExpressionName('worried'),
        surprised: resolveExpressionName('surprised'),
        neutral: resolveExpressionName('neutral'),
    };

    if (availableExpressions.size) {
        console.groupCollapsed('VRM expression capability report');
        console.info('Available expressions:', [...availableExpressions].join(', '));
        console.table(resolvedEmotionMap);
        console.groupEnd();
    }

    window.__koaVrmDebug = {
        hasExpressionManager: Boolean(currentVrm?.expressionManager),
        hasBlendShapeProxy: Boolean(currentVrm?.blendShapeProxy),
        supportedExpressions: [...availableExpressions],
        mapping: { ...resolvedEmotionMap },
    };

    window.dispatchEvent(new CustomEvent('vrm-expressions-updated', {
        detail: {
            supportedExpressions: [...availableExpressions],
            mapping: { ...resolvedEmotionMap },
        },
    }));
}

function hasAnimationCategory(category) {
    const list = animationDB[category];
    return Array.isArray(list) && list.length > 0;
}

function clamp01(value) {
    if (!Number.isFinite(value)) return 0;
    return Math.max(0, Math.min(1, value));
}

function resolveExpressionName(emotion) {
    const aliases = EMOTION_ALIASES[String(emotion || 'neutral').toLowerCase()] || [];
    const candidates = [];
    aliases.forEach((alias) => {
        const normalized = alias.toLowerCase();
        candidates.push(normalized);
        candidates.push(`vrmexpression_${normalized}`);
    });

    for (const candidate of candidates) {
        if (!availableExpressions.has(candidate)) continue;
        if (canDriveExpression(candidate)) return candidate;
    }
    return null;
}

function canDriveExpression(name) {
    const manager = getExpressionController();
    if (!manager || typeof manager.getValue !== 'function' || typeof manager.setValue !== 'function') {
        return true;
    }

    try {
        const base = Number(manager.getValue(name) || 0);
        const probe = Math.max(base, 0.55);
        manager.setValue(name, probe);
        const observed = Number(manager.getValue(name) || 0);
        manager.setValue(name, base);
        return observed > 0.05;
    } catch (_e) {
        return false;
    }
}

function isEmotionExpression(name) {
    return !NON_EMOTION_EXPRESSIONS.has(String(name || '').toLowerCase());
}

function clearEmotionExpressions() {
    const manager = getExpressionController();
    if (!manager || typeof manager.setValue !== 'function') return;
    availableExpressions.forEach((name) => {
        if (isEmotionExpression(name)) {
            manager.setValue(name, 0);
        }
    });
}

function setExpression(name, amount) {
    const manager = getExpressionController();
    if (!manager || typeof manager.setValue !== 'function' || !name) return false;
    if (!availableExpressions.has(name.toLowerCase())) return false;
    manager.setValue(name, clamp01(amount));
    return true;
}

function applyEmotionBlend(delta) {
    if (!getExpressionController()) return;

    if (!emotionBlendState.manualLock && Date.now() > emotionBlendState.releaseAt) {
        emotionBlendState.targetWeight = 0;
    }

    const speed = emotionBlendState.targetWeight > emotionBlendState.currentWeight ? 8.0 : 3.5;
    const t = 1 - Math.exp(-speed * Math.max(0.0001, delta));
    emotionBlendState.currentWeight += (emotionBlendState.targetWeight - emotionBlendState.currentWeight) * t;

    clearEmotionExpressions();
    if (emotionBlendState.activeName) {
        setExpression(emotionBlendState.activeName, emotionBlendState.currentWeight);
        if (emotionBlendState.currentWeight < 0.01 && emotionBlendState.targetWeight === 0 && !emotionBlendState.manualLock) {
            emotionBlendState.activeName = null;
            emotionBlendState.currentWeight = 0;
        }
    }
}

function setMoodExpression(emotion, intensity, confidence) {
    const name = resolvedEmotionMap[String(emotion || 'neutral').toLowerCase()] || null;
    const safeIntensity = clamp01(intensity);
    const safeConfidence = clamp01(confidence);
    const weight = name ? Math.max(0.2, Math.min(1.0, 0.2 + safeIntensity * 0.65 + safeConfidence * 0.2)) : 0;
    const holdMs = Math.round(900 + safeIntensity * 1700 + safeConfidence * 700);

    emotionBlendState.manualLock = false;
    emotionBlendState.activeName = name;
    emotionBlendState.targetWeight = weight;
    emotionBlendState.releaseAt = Date.now() + holdMs;

    return { expressionName: name, expressionWeight: weight, holdMs };
}

function updateLipSync(delta) {
    const manager = getExpressionController();
    if (!manager || typeof manager.getValue !== 'function' || typeof manager.setValue !== 'function') return;

    let aaTarget = 0;
    let ohTarget = 0;
    let ouTarget = 0;
    if (state.lipSyncAnalyser && state.lipSyncDataArray) {
        state.lipSyncAnalyser.getByteFrequencyData(state.lipSyncDataArray);
        const vol = state.lipSyncDataArray.reduce((a, b) => a + b, 0) / state.lipSyncDataArray.length;
        const normalized = clamp01(vol / 70);
        aaTarget = Math.min(1.0, normalized * 1.1);
        ohTarget = Math.min(0.65, Math.max(0, normalized - 0.28) * 0.7);
        ouTarget = Math.min(0.5, Math.max(0, normalized - 0.45) * 0.85);
    }

    const smooth = 1 - Math.exp(-12.0 * Math.max(0.0001, delta));
    const visemeTargets = { aa: aaTarget, oh: ohTarget, ou: ouTarget };
    Object.keys(visemeTargets).forEach((name) => {
        if (!availableExpressions.has(name)) return;
        const current = manager.getValue(name) || 0;
        const next = current + (visemeTargets[name] - current) * smooth;
        manager.setValue(name, clamp01(next));
    });
}

function playVRMA(filename) {
    if (!currentVrm || !currentMixer) return;
    const loader = new THREE.GLTFLoader();
    loader.register((parser) => new THREE_VRM_ANIMATION.VRMAnimationLoaderPlugin(parser));

    loader.load(ANIMATION_PATH + filename, (gltf) => {
        const vrmAnimations = gltf.userData.vrmAnimations;
        if (vrmAnimations && vrmAnimations.length > 0) {
            const clip = THREE_VRM_ANIMATION.createVRMAnimationClip(vrmAnimations[0], currentVrm);
            currentMixer.stopAllAction();
            const action = currentMixer.clipAction(clip);
            action.fadeIn(0.5);
            action.play();
        }
    });
}

export function updateVibe(vibe) {
    const [x, y, z] = vibe || [0,0,0];
    let cat = 'neutral';
    if (z > 4.0) cat = 'angry';
    else if (z < -2.0) cat = 'sad';
    else if (z > 3.0) cat = 'happy';

    const list = animationDB[cat] || animationDB['neutral'];
    if (!list || !list.length) return;
    
    const item = list[Math.floor(Math.random() * list.length)];
    if(item) playVRMA(item.file);
}

// Play a random animation from a named category defined in index.md.
// Emotion flow keeps body at neutral and only uses facial expressions.
export function playAnimation(category = 'neutral') {
    const list = animationDB[category] || animationDB['neutral'];
    if (!list || !list.length) return;
    const item = list[Math.floor(Math.random() * list.length)];
    if (item) {
        activeBodyCategory = category;
        playVRMA(item.file);
    }
}

export function applyMoodReaction(packet) {
    const confidence = clamp01(Number(packet?.confidence ?? 0));
    const safe = confidence >= SAFE_CONFIDENCE;

    const mood = {
        emotion: safe ? String(packet?.emotion || 'neutral').toLowerCase() : 'neutral',
        valence: safe ? String(packet?.valence || 'neutral').toLowerCase() : 'neutral',
        intensity: safe ? clamp01(Number(packet?.intensity ?? 0)) : 0,
        confidence,
    };

    if (activeBodyCategory !== 'neutral' && hasAnimationCategory('neutral')) {
        playAnimation('neutral');
    }

    const reaction = setMoodExpression(mood.emotion, mood.intensity, confidence);
    const expressionApplied = Boolean(reaction.expressionName);

    return {
        usedEmotion: mood.emotion,
        usedValence: mood.valence,
        usedIntensity: mood.intensity,
        usedConfidence: confidence,
        safe,
        expressionApplied,
        bodyCategory: 'neutral',
        expressionName: reaction.expressionName,
        expressionWeight: reaction.expressionWeight,
        holdMs: reaction.holdMs,
    };
}

export function maintainMoodReaction() {
    if (!emotionBlendState.manualLock) {
        emotionBlendState.releaseAt = Math.max(emotionBlendState.releaseAt, Date.now() + 250);
    }
    return {
        bodyCategory: activeBodyCategory,
        activeExpression: emotionBlendState.activeName,
    };
}

export function blendToNeutral() {
    emotionBlendState.manualLock = false;
    emotionBlendState.targetWeight = 0;
    emotionBlendState.releaseAt = Date.now();
    playAnimation('neutral');
}

export function getSupportedExpressions() {
    return [...availableExpressions];
}

export function getEmotionExpressionMapping() {
    return { ...resolvedEmotionMap };
}

export function setManualExpression(name, amount = 0.8) {
    const normalized = String(name || '').toLowerCase();
    if (!availableExpressions.has(normalized)) return false;
    emotionBlendState.manualLock = true;
    emotionBlendState.activeName = normalized;
    emotionBlendState.targetWeight = clamp01(amount);
    emotionBlendState.releaseAt = Number.MAX_SAFE_INTEGER;
    return true;
}

export function clearManualExpression() {
    emotionBlendState.manualLock = false;
    emotionBlendState.targetWeight = 0;
    emotionBlendState.releaseAt = Date.now();
}

export function getEmotionRuntimeSnapshot() {
    return {
        activeName: emotionBlendState.activeName,
        targetWeight: emotionBlendState.targetWeight,
        currentWeight: emotionBlendState.currentWeight,
        manualLock: emotionBlendState.manualLock,
        releaseAt: emotionBlendState.releaseAt,
    };
}

export function getExpressionValue(name) {
    const manager = getExpressionController();
    if (!manager || typeof manager.getValue !== 'function') return null;
    try {
        const value = manager.getValue(String(name || '').toLowerCase());
        return Number.isFinite(value) ? value : 0;
    } catch (_e) {
        return null;
    }
}

function animate() {
    if (!isAnimating) return;
    requestAnimationFrame(animate);
    const delta = clock.getDelta();
    if (currentMixer) currentMixer.update(delta);
    if (currentVrm) {
        currentVrm.update(delta);
        applyEmotionBlend(delta);
        updateProceduralEyes(delta);
        updateLipSync(delta);
    }
    if(controls) controls.update();
    renderer.render(scene, camera);
}

function updateProceduralEyes(delta) {
    const manager = getExpressionController();
    if (!currentVrm || !manager || typeof manager.setValue !== 'function') return;
    blinkTimer -= delta;
    if (blinkTimer < 0) {
        blinkTimer = Math.random() * 5 + 1;
        manager.setValue('blink', 1);
        setTimeout(() => { if(currentVrm) manager.setValue('blink', 0); }, 150);
    }
    saccadeTimer -= delta;
    if (saccadeTimer <= 0) {
        saccadeTimer = Math.random() * 2 + 0.5;
        if (Math.random() < 0.6) eyeTarget.copy(camera.position); 
        else eyeTarget.set(camera.position.x + (Math.random() - 0.5), camera.position.y + (Math.random() - 0.5), 2);
    }
    currentEyeLook.lerp(eyeTarget, delta * 3.0); 
    try {
        if(currentVrm.lookAt) {
            // VRM 1.0 lookAt expects a target Object3D or direct bone manipulation
            // If .lookAt() function doesn't exist, this will prevent crashes
            if (typeof currentVrm.lookAt.lookAt === 'function') {
                currentVrm.lookAt.lookAt(currentEyeLook);
            }
        }
    } catch(e) {
        console.warn("VRM LookAt error suppressed", e);
    }
}

export function startAnimation() { if (!isAnimating) { isAnimating = true; clock.start(); animate(); } }
export function stopAnimation() { isAnimating = false; }
export function onWindowResize() {
    if (!camera || !renderer) return;
    const container = elements.sceneContainer;
    if (!container || container.clientWidth === 0 || container.clientHeight === 0) return;
    camera.aspect = container.clientWidth / container.clientHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(container.clientWidth, container.clientHeight);
}