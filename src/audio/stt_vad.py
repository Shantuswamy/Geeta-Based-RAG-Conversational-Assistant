"""
This module is responsible for speech to text conversion.
Uses faster Whisper STT for local offline speech to text conversion.
"""
# pyrefly: ignore [missing-import]
from src.config import settings
from faster_whisper import WhisperModel
import os
import numpy as np
import re



# --- A. Regex Pattern to catch typical Whisper Hindi Hallucinations ---
# Detects repetitive nonsense characters/matras (like ू, ु, ुं) common in empty audio streaming artifacts
HINDI_HALLUCINATION_PATTERN = re.compile(r'[\u0900-\u097F]*([ूुुंूदूरूसूलूकुमु])\1{2,}[\u0900-\u097F]*')


_WHISPER_CACHE={}

async def load_whisper_model(model_name:str=settings.WHISPER_MODEL_NAME, path:str=settings.WHISPER_MODEL_DIR):
    try:
        if model_name not in _WHISPER_CACHE:
            print(f"Loading Whisper model locally from {path}...")
            # If the local directory containing model.bin exists, pass path directly
            model_path = str(path) if os.path.exists(path) else model_name
            model = WhisperModel(
                model_size_or_path=model_path,
                device=settings.DEVICE,
                compute_type= "float16",
                local_files_only=True
            )
            _WHISPER_CACHE[model_name] = model
        return _WHISPER_CACHE[model_name]
    except Exception as e:
        print(f"Error loading Whisper model: {e}")
        return None



# function for STT conversion for chunks of audio
# the audio_buffer list contains mono float32 data in 16kHz

# functio to receive the audio PCM bytes from the client and convert them to numpy array and process them and transcribe
speech_buffer=[]
custom_vad_parameters = {
    "threshold": 0.5,
    "min_speech_duration_ms": 250,
    "max_speech_duration_s": 15,
    "min_silence_duration_ms": 1000
}
def catch_bytes_and_transcribe(model, pcm_byte_chunk: bytes,**kwargs):
    try:
        audio_array = np.frombuffer(pcm_byte_chunk, dtype=np.float32)   # ADD THIS LINE
        # Extract values passed from handle_mic_chunk, or fall back to sensible defaults
        initial_prompt = kwargs.get("initial_prompt", "नमस्ते, आप कैसे हैं? मुझे कर्म योग के बारे में बताओ।")
        temperature = kwargs.get("temperature", [0.0, 0.2, 0.4])

        segments, info = model.transcribe(
            audio_array,
            language="hi",
            condition_on_previous_text=False,  # Keep false to prevent audio backlog pollution
            vad_filter=True,
            vad_parameters=custom_vad_parameters,
            beam_size=5,
            length_penalty=1.0,
            repetition_penalty=1.2,            # Raised slightly to block repeating matras/vowels
            no_repeat_ngram_size=3,
            initial_prompt=initial_prompt,     # Hard-anchors clean Devanagari vocabulary paths
            temperature=temperature,            # Dynamic backoff breaks hallucination loops
        )


        transcript = ""
        for segment in segments:
            if segment.text.strip() and segment.no_speech_prob < 0.3 and segment.avg_logprob > -0.8:
                transcript += " " + segment.text.strip()
        print(f"User : {transcript}")
        return transcript.strip()

    except Exception as e:
        print(f"Error in STT: {e}")
        return "" 