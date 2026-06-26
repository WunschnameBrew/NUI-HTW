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

// Helpers
let blinkTimer = 0;
let saccadeTimer = 0;
let eyeTarget = new THREE.Vector3();
let currentEyeLook = new THREE.Vector3();

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
        updateVibe([0,0,0]); 
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

// Play a random animation from a named category defined in index.md
// (e.g. 'neutral' = Idle, 'taunt' = a gesture). Falls back to 'neutral'.
export function playAnimation(category = 'neutral') {
    const list = animationDB[category] || animationDB['neutral'];
    if (!list || !list.length) return;
    const item = list[Math.floor(Math.random() * list.length)];
    if (item) playVRMA(item.file);
}

function animate() {
    if (!isAnimating) return;
    requestAnimationFrame(animate);
    const delta = clock.getDelta();
    if (currentMixer) currentMixer.update(delta);
    if (currentVrm) {
        currentVrm.update(delta);
        updateProceduralEyes(delta);
        
        // Lip Sync
        if (state.lipSyncAnalyser && state.lipSyncDataArray && currentVrm.expressionManager) {
             state.lipSyncAnalyser.getByteFrequencyData(state.lipSyncDataArray);
             const vol = state.lipSyncDataArray.reduce((a,b)=>a+b,0) / state.lipSyncDataArray.length; 
             currentVrm.expressionManager.setValue('aa', Math.min(1.0, vol / 60));
        }
    }
    if(controls) controls.update();
    renderer.render(scene, camera);
}

function updateProceduralEyes(delta) {
    if (!currentVrm || !currentVrm.expressionManager) return;
    blinkTimer -= delta;
    if (blinkTimer < 0) {
        blinkTimer = Math.random() * 5 + 1;
        currentVrm.expressionManager.setValue('blink', 1);
        setTimeout(() => { if(currentVrm) currentVrm.expressionManager.setValue('blink', 0); }, 150);
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