
# pyrefly: ignore [missing-import]
from src.rag.pipeline import catch_query_and_text_queues
from fastapi import FastAPI , WebSocket ,WebSocketDisconnect
import asyncio
import numpy as np
# pyrefly: ignore [missing-import]
from src.audio.stt_vad import load_whisper_model , catch_bytes_and_transcribe , HINDI_HALLUCINATION_PATTERN
# pyrefly: ignore [missing-import]
from src.rag.pipeline import generate_audio_from_text_queue
# pyrefly: ignore [missing-import]
from utils.instantiate_embed_model import InstantiateEmbedModel
# pyrefly: ignore [missing-import]
from utils.cross_encoder import cross_encoder
# pyrefly: ignore [missing-import]
from src.rag.pipeline import get_cached_retriever
# pyrefly: ignore [missing-import]
from src.audio.tts import load_kokoro_model
# pyrefly: ignore [missing-import]
from src.llm.gemini_client import load_local_llm
import time




app = FastAPI(debug=True)

# --- ADDED: tunables for the buffering logic ---
ENERGY_THRESHOLD = 0.01
MIN_SPEECH_CHUNKS = 15
SILENCE_CHUNKS_TO_FINALIZE = 12


custom_vad_parameters = {
    "threshold": 0.5,
    "min_speech_duration_ms": 250,
    "max_speech_duration_s": 15,
    "min_silence_duration_ms": 1000
}

@app.get("/health")
def health_check():
    return {"status": "ok"}



# =======================================================================
# Per-connection state — NEVER share this across users
# =======================================================================
class ConversationState:
    """One instance per connected user — never shared."""
    def __init__(self):
        self.audio_out_queue: asyncio.Queue = asyncio.Queue()
        self.speech_buffer: list[np.ndarray] = []
        self.consecutive_silent_chunks: int = 0
        self.bot_speaking: bool = False
        self.current_response_task: asyncio.Task | None = None
        self.user_speaking: bool = False



# this function will check if the audio chunk has sufficient energy to be processed
def rms_energy(chunk: np.ndarray) -> float:
    return float(np.sqrt(np.mean(chunk ** 2)))

# Add a cheap energy check BETWEEN whisper calls — don't process
# every 40 chunks blindly; wait until a real pause happens.
def is_silent(chunk: np.ndarray, threshold: float = 0.01) -> bool:
    return np.sqrt(np.mean(chunk ** 2)) < threshold

 # -----------------------------------------------------------------
# Called on every incoming mic chunk
# -----------------------------------------------------------------
async def handle_mic_chunk(state: ConversationState, model, chunk: np.ndarray):
    energy = rms_energy(chunk)
    is_silent = energy < ENERGY_THRESHOLD
 
    state.speech_buffer.append(chunk)
    state.consecutive_silent_chunks = state.consecutive_silent_chunks + 1 if is_silent else 0
 
    ready = (
        len(state.speech_buffer) >= MIN_SPEECH_CHUNKS
        and state.consecutive_silent_chunks >= SILENCE_CHUNKS_TO_FINALIZE
    )
    if not ready:
        return " not ready yet"
 
    full_window = np.concatenate(state.speech_buffer, axis=0)
    state.speech_buffer = []
    state.consecutive_silent_chunks = 0
 
    if rms_energy(full_window) < ENERGY_THRESHOLD:
        print("[VAD] Discarded — buffer was filled with silence or energy is less ")
        return
 
    try:
        if not state.user_speaking:
            # Injecting explicit transcription configurations inside your synchronization thread wrapper
            user_query = await asyncio.to_thread(
                catch_bytes_and_transcribe, 
                model, 
                full_window.tobytes(),
                language="hi",
                initial_prompt="नमस्ते, आप कैसे हैं? मुझे कर्म योग के बारे में बताओ।", # Context anchor for clean token paths
                beam_size=5,
                temperature=[0.0, 0.2, 0.4]  # Dynamic fallback prevents loop repetition
            )
            state.user_speaking = False
        else:
            print("[BARGE-IN] User is already speaking")
    except Exception as e:
        print(f"[STT] Error: {e}")
        return
 
    # Clean string extraction checks
    if not user_query:
        print("[STT] Discarded low-confidence result: Empty Query")
        return

    cleaned_query = user_query.strip()

    # --- B. Apply Hallucination Filtering ---
    # Catch repetitive phonetic gibberish text generated during execution stutters
    if HINDI_HALLUCINATION_PATTERN.search(cleaned_query) or len(set(cleaned_query)) < 4:
        print(f"[STT] Caught and blocked Whisper Hallucination: '{cleaned_query}'")
        return
 
    if len(cleaned_query.split()) < 2:
        print(f"[STT] Discarded low-confidence result: '{cleaned_query}'")
        return
 
    print(f"[STT] User said: {cleaned_query}")
 
    if state.bot_speaking and energy < ENERGY_THRESHOLD:
        print("[BARGE-IN] Cancelling in-progress response")
        if state.current_response_task and not state.current_response_task.done():
            state.current_response_task.cancel()
        while not state.audio_out_queue.empty():
            state.audio_out_queue.get_nowait()
        state.bot_speaking = False
 
    # Use clean output context string safely
    asyncio.create_task(process_utterance(state, cleaned_query))
 

 
 
async def process_utterance(state: ConversationState, user_query: str):
    t0 = time.perf_counter()
    state.bot_speaking = True
    state.current_response_task = asyncio.current_task()

    txt_queue = asyncio.Queue()   # NEW — sits between LLM and Kokoro

    try:
        print("[PIPELINE] Processing query...")

        # Run BOTH concurrently: LLM streams sentences into txt_queue while
        # Kokoro is simultaneously pulling from txt_queue and generating
        # audio for earlier sentences — this is what makes the response
        # start playing before the full reply is even done generating.
        await asyncio.gather(
            catch_query_and_text_queues(user_query, txt_queue),

            generate_audio_from_text_queue(txt_queue, state.audio_out_queue),
        )

        print(f"[DONE] Turn completed in {time.perf_counter() - t0:.2f}s")

    except asyncio.CancelledError:
        print("[BARGE-IN] Response generation cancelled mid-flight")
    except Exception as e:
        print(f"[ERROR] process_utterance failed: {e}")
    finally:
        print("\n End of response processing\n")
        state.bot_speaking = False



# -----------------------------------------------------------------
# TASK 1 — everything FROM the user
# -----------------------------------------------------------------
async def receiver_loop(websocket: WebSocket, state: ConversationState, model):
    while True:
        data = await websocket.receive()
 
        if data["type"] == "websocket.disconnect":
            print("[WS] Client disconnected")
            break
 
        if "bytes" in data and data["bytes"] is not None:
            chunk = np.frombuffer(data["bytes"], dtype=np.float32)
            await handle_mic_chunk(state, model, chunk)


# -----------------------------------------------------------------
# TASK 2 — everything TO the user, fully decoupled
# -----------------------------------------------------------------
async def sender_loop(websocket: WebSocket, state: ConversationState):
    while True:
        chunk = await state.audio_out_queue.get()
        if chunk is None:      # ADDED — end-of-turn marker from generate_audio_from_text_queue
            continue
        await websocket.send_bytes(chunk.astype(np.float32).tobytes())



@app.on_event("startup")
async def warm_up_models():
    await get_cached_retriever()
    await load_whisper_model()
    await load_kokoro_model()
    await load_local_llm()   # if this has its own similar issue
    print("[STARTUP] All models warm — first query will be fast")



# API end point for voice to text and text to voice
 
@app.websocket("/ws/voice-chat")
async def receive_send_voice_chat(websocket: WebSocket):
    await websocket.accept()
    print("[WS] Connection accepted")
 
    state = ConversationState()
    model = await load_whisper_model()
 
    receiver_task = asyncio.create_task(receiver_loop(websocket, state, model))
    sender_task = asyncio.create_task(sender_loop(websocket, state))
 
    try:
        done, pending = await asyncio.wait(
            [receiver_task, sender_task],
            return_when=asyncio.FIRST_COMPLETED,
        )
        for task in pending:
            task.cancel()
    except WebSocketDisconnect:
        print("[WS] Disconnected mid-session")
    except Exception as e:
        print(f"[WS] Unexpected error: {e}")
    finally:
        if state.current_response_task and not state.current_response_task.done():
            state.current_response_task.cancel()
        receiver_task.cancel()
        sender_task.cancel()
        print("[WS] Cleaned up")


# run the app
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="[IP_ADDRESS]", port=8000)