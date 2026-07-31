# Backend/services/llm.py
import asyncio
import logging
from Backend.config.settings import DEFAULT_MODEL, LLM_CONTEXT_SIZE

logger = logging.getLogger("LLM")

try:
    from llama_cpp import Llama
except ImportError:
    Llama = None

class LLMService:
    def __init__(self):
        self.is_active = True
        self.llm = None
        
    def load_model(self):
        if self.llm is None and Llama is not None:
            if not DEFAULT_MODEL:
                logger.error("No GGUF model found in Llama_Models directory.")
                return
            logger.info(f"Loading LLM model from {DEFAULT_MODEL}...")
            # We load the model synchronously on first request
            self.llm = Llama(
                model_path=DEFAULT_MODEL,
                n_ctx=LLM_CONTEXT_SIZE,
                n_gpu_layers=-1, # Will use GPU if compiled with it, else CPU
                verbose=False
            )
            logger.info("LLM model loaded.")

    async def stream_chat(self, messages, temperature=0.7, **kwargs):
        if Llama is None:
            yield "[LLM Error: llama-cpp-python not installed]"
            return
            
        try:
            # First, load the model in a thread if it isn't already loaded to avoid blocking
            if self.llm is None:
                await asyncio.to_thread(self.load_model)
                
            if self.llm is None:
                yield "[Error: Model failed to load]"
                return
            
            # Since create_chat_completion with stream=True returns a generator synchronously,
            # we need to be careful not to block. 
            def _generate():
                return self.llm.create_chat_completion(
                    messages=messages,
                    temperature=temperature,
                    stream=True,
                    stop=kwargs.get("stop", [])
                )
            
            # Start generation
            stream = await asyncio.to_thread(_generate)
            
            # Since iteration might block, we ideally should run `next(stream)` in to_thread, 
            # but for simple integration, we'll iterate and yield. In llama-cpp-python, the generator
            # does the compute in `__next__`. 
            # To be truly non-blocking, we need a small wrapper:
            
            while True:
                def _get_next():
                    try:
                        return next(stream)
                    except StopIteration:
                        return None
                
                chunk = await asyncio.to_thread(_get_next)
                if chunk is None:
                    break
                    
                if isinstance(chunk, str):
                    yield chunk
                else:
                    if "choices" in chunk and len(chunk["choices"]) > 0:
                        delta = chunk["choices"][0].get("delta", {})
                        if "content" in delta and delta["content"]:
                            yield delta["content"]
                            
        except Exception as e:
            logger.error(f"LLM Error: {e}")
            yield f"[LLM Error: {e}]"

llm_service = LLMService()
