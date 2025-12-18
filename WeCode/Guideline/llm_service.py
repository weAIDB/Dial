import os
import time
try:
    import openai
except ImportError:
    print("Warning: openai package not installed.")

class LLMService:
    def __init__(self, api_key="", base_url=None, model_name="DeepSeek-V3-250324", timeout=60):
        self.model_name = model_name
        self.timeout = timeout
        
        # DeepSeek Auto-Configuration
        if "deepseek" in model_name.lower():
            if not base_url:
                base_url = ""
            
            # Priority: Constructor Arg > Env Var > Hardcoded Fallback
            # Note: The user hardcoded a key in the constructor arg default, so we respect that.
            # But we still check env var if the user passed None explicitly (though default prevents that)
            if not api_key:
                api_key = ""
            
            if not api_key:
                 # Fallback key (Updated to the one user provided, but please verify it!)
                api_key = ""

        # Qwen (DashScope) Auto-Configuration
        elif "qwen" in model_name.lower():
            if not base_url:
                base_url = ""
            # Use DASHSCOPE_API_KEY if api_key is missing or if it's the default deepseek key
            if not api_key or api_key == "":
                api_key = os.getenv("DASHSCOPE_API_KEY")
        
        # ParaTera (Kimi/MiniMax) Auto-Configuration
        elif "kimi" in model_name.lower() or "minimax" in model_name.lower():
            if not base_url:
                base_url = ""
            if not api_key or api_key == "":
                api_key = os.getenv("PARATERA_API_KEY")

        if not api_key:
            api_key = os.getenv("OPENAI_API_KEY")

        self.client = openai.OpenAI(api_key=api_key, base_url=base_url)

    def generate_response(self, prompt: str, max_retries=3) -> str:
        """
        Generate response with retry logic for API errors.
        """
        for attempt in range(max_retries):
            try:
                response = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=[
                        {"role": "system", "content": "You are a helpful AI assistant."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.0,
                    timeout=self.timeout
                )
                return response.choices[0].message.content
            
            except Exception as e:
                error_str = str(e)
                print(f"LLM Call Error (Attempt {attempt+1}/{max_retries}): {error_str}")
                
                # If it's an authentication error (401), retrying immediately usually won't help unless it's a temporary glitch.
                # But if it's "Please wait for 1 minute", we should wait.
                if "401" in error_str or "429" in error_str:
                    wait_time = 5 * (attempt + 1) # Backoff: 5s, 10s, 15s
                    if "wait for 1 minute" in error_str:
                        wait_time = 65 # Force wait > 1 min if instructed
                    
                    print(f"Sleeping for {wait_time}s before retry...")
                    time.sleep(wait_time)
                else:
                    # For other errors (timeout, network), short wait
                    time.sleep(2)
        
        return f"Error: Failed after {max_retries} retries. Last error: {error_str}"

class VLLMService:
    """
    Local VLLM Service wrapper to match the interface.
    """
    def __init__(self, model_path, gpu_devices="0"):
        try:
            from vllm import LLM, SamplingParams
            os.environ["CUDA_VISIBLE_DEVICES"] = gpu_devices
            self.llm = LLM(model=model_path, trust_remote_code=True)
            self.sampling_params = SamplingParams(temperature=0.0, max_tokens=2048)
        except ImportError:
            print("Error: vllm not installed.")
            self.llm = None

    def generate_response(self, prompt: str) -> str:
        if not self.llm:
            return "Error: VLLM not initialized"
        
        outputs = self.llm.generate([prompt], self.sampling_params)
        return outputs[0].outputs[0].text
