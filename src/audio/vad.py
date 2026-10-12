"""
This module is responsible for loading the VAD model.
This module is for detection of voice activity in the audio stream.
uses Silero VAD 
"""

# pyrefly: ignore [missing-import]
from src.config import settings
import torch 
import asyncio
import numpy as np
from silero_vad import load_silero_vad



# function to load the VAD model

# _VAD_CACHE={}

# async def load_vad_model():
#     try:
#         if "VAD" not in _VAD_CACHE:
#             print("Loading VAD...")
#             _VAD_CACHE["VAD"]=load_silero_vad()
#         return _VAD_CACHE["VAD"]
#     except Exception as e:
#         print(f"Error loading VAD model: {e}")
#         return None


# async def is_speech(pcm_chunk: np.ndarray, threshold: float = 0.5) -> bool:
#     model = await load_vad_model()
#     tensor_chunk = torch.from_numpy(pcm_chunk).float()
#     prob = model(tensor_chunk, 16000).item()
#     return prob > threshold