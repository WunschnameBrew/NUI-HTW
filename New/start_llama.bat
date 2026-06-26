@echo off
echo 🧠 Starting llama-server...
cd llamacpp
llama-server.exe --model ../Llama_Models/model.gguf --ctx-size 8192 --n-gpu-layers -1 --port 8001
pause
