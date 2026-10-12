"""
This module is used to generate the audio from the text queue.Uses Kokoro TTS model

"""
import os
# pyrefly: ignore [missing-import]
from src.config import settings 
import time
from kokoro import KPipeline
import soundfile as sf
import numpy as np

# create a function to load the model from models\kokoro-82m directory and also it must use GPU
_MODEL_CACHE={}
async def load_kokoro_model(model_name:str=settings.KOKORO_MODEL_NAME , path:str=settings.KOKORO_MODEL_DIR):
    try:
        if model_name not in _MODEL_CACHE:
            print("Loading Kokoro model...")
            # Auto-detect language code: 'a' for American English, 'b' for British English, 'h' for Hindi
            
            _MODEL_CACHE[model_name] = KPipeline(
                lang_code="h",  
                repo_id=model_name,
                device=settings.DEVICE
            )

        model=_MODEL_CACHE[model_name]           
        return model
    except Exception as e:
        print(f"Error loading Kokoro model: {e}")
        return None



def _sync_tts(model, text: str): #voice: str
    
    chunks = []
    try:
        for _, _, audio in model(text, voice="hm_omega", speed=1.0):
            if audio is not None:
                chunks.append(np.asarray(audio, dtype=np.float32))
    except Exception as e:
        print(f"Error in _sync_tts: {e}")   
    return chunks