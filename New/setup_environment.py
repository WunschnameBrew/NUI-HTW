import os
import sys
import subprocess
import platform

def run_cmd(cmd):
    print(f"Running: {cmd}")
    subprocess.check_call(cmd, shell=True)

def main():
    print("🚀 Setting up Koa-AI Environment...")
    
    # 1. Install standard dependencies
    print("\n📦 Installing standard dependencies (faster-whisper, piper-tts, etc)...")
    run_cmd(f"{sys.executable} -m pip install fastapi uvicorn python-multipart faster-whisper piper-tts httpx openai pytest pydantic pydantic-settings")
    
    # 2. Install llama-cpp-python
    print("\n🦙 Installing llama-cpp-python...")
    print("Checking OS and Hardware...")
    os_name = platform.system()
    
    # We provide a basic prompt for hardware acceleration
    print("\nWhich hardware acceleration do you want to use for llama-cpp-python?")
    print("1) CPU (Default, works everywhere)")
    print("2) NVIDIA GPU (CUDA 12.1+)")
    print("3) AMD/Intel GPU (Vulkan)")
    print("4) Apple Metal - Mac Only")
    
    choice = input("Enter your choice (1-4) [1]: ").strip()
    
    install_cmd = f"{sys.executable} -m pip install llama-cpp-python"
    
    if choice == "2":
        install_cmd = f"{sys.executable} -m pip install llama-cpp-python --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cu121"
    elif choice == "3":
        # Vulkan wheels are available for Windows/Linux, or you can build it.
        # abetlen provides vulkan wheels in the /vulkan folder.
        install_cmd = f"{sys.executable} -m pip install llama-cpp-python --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/vulkan"
    elif choice == "4":
        if os_name == "Darwin":
            install_cmd = f"CMAKE_ARGS=\"-DGGML_METAL=on\" {sys.executable} -m pip install llama-cpp-python"
        else:
            print("⚠️ Metal is only supported on macOS. Defaulting to CPU.")
            
    run_cmd(install_cmd)
    
    # 3. Create models directories and download LLM
    print("\n📥 Checking Llama models...")
    os.makedirs("Llama_Models", exist_ok=True)
    os.makedirs("Piper", exist_ok=True)
    
    model_path = os.path.join("Llama_Models", "Dolphin3.0-Llama3.2-3B.Q4_K_S.gguf")
    # Check if file exists and has a reasonable size (> 1GB)
    if not os.path.exists(model_path) or os.path.getsize(model_path) < 1000000000:
        print(f"Downloading Dolphin3.0-Llama3.2-3B model to {model_path} (This may take a while)...")
        try:
            # We use huggingface_hub instead of urllib to handle redirects, resumes, and CDN links reliably.
            from huggingface_hub import hf_hub_download
            hf_hub_download(
                repo_id="QuantFactory/Dolphin3.0-Llama3.2-3B-GGUF",
                filename="Dolphin3.0-Llama3.2-3B.Q4_K_S.gguf",
                local_dir="Llama_Models"
            )
            print("✅ Model downloaded successfully!")
        except ImportError:
            print("❌ huggingface_hub not installed. Running pip install huggingface_hub...")
            run_cmd(f"{sys.executable} -m pip install huggingface_hub")
            from huggingface_hub import hf_hub_download
            hf_hub_download(
                repo_id="QuantFactory/Dolphin3.0-Llama3.2-3B-GGUF",
                filename="Dolphin3.0-Llama3.2-3B.Q4_K_S.gguf",
                local_dir="Llama_Models"
            )
            print("✅ Model downloaded successfully!")
        except Exception as e:
            print(f"❌ Failed to download model: {e}")
            print("Please download it manually from: https://huggingface.co/QuantFactory/Dolphin3.0-Llama3.2-3B-GGUF/resolve/main/Dolphin3.0-Llama3.2-3B.Q4_K_S.gguf")
    # 4. Check and download Piper Voice
    print("\n🗣️ Checking Piper voice models...")
    piper_onnx = os.path.join("Piper", "en_US-amy-medium.onnx")
    piper_json = os.path.join("Piper", "en_US-amy-medium.onnx.json")
    if not os.path.exists(piper_onnx) or not os.path.exists(piper_json):
        print("Downloading Piper voice model (en_US-amy-medium)...")
        try:
            from huggingface_hub import hf_hub_download
            import shutil
            hf_hub_download(repo_id="rhasspy/piper-voices", filename="en/en_US/amy/medium/en_US-amy-medium.onnx", local_dir="Piper_tmp")
            hf_hub_download(repo_id="rhasspy/piper-voices", filename="en/en_US/amy/medium/en_US-amy-medium.onnx.json", local_dir="Piper_tmp")
            shutil.move(os.path.join("Piper_tmp", "en", "en_US", "amy", "medium", "en_US-amy-medium.onnx"), piper_onnx)
            shutil.move(os.path.join("Piper_tmp", "en", "en_US", "amy", "medium", "en_US-amy-medium.onnx.json"), piper_json)
            shutil.rmtree("Piper_tmp", ignore_errors=True)
            print("✅ Piper voice downloaded successfully!")
        except Exception as e:
            print(f"⚠️ Could not download Piper voice model automatically: {e}")
    else:
        print("✅ Piper voice model already exists!")

    print("\n✅ Setup complete!")

if __name__ == "__main__":
    main()
