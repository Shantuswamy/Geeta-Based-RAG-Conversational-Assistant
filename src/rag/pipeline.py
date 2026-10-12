"""
This module is used to create and manage the pipeline for the Gita.
This module uses Langchain ChromaDB for vector storage.
This module uses Langchain HuggingfaceEmbeddings for embedding.
This module is only responsible to create the persistent vector store ,
to decide if to create  one if existing or not is in main.py
This module is also used to build the whole pipeline logic 
that includes embedding , vector store and reranking.

"""

# pyrefly: ignore [missing-import]
from src.llm.gemini_client import query_classifier , brain_stream
# pyrefly: ignore [missing-import]
from utils.hybrid_retriver import Hybride_Retriver
# pyrefly: ignore [missing-import]
from utils.cross_encoder import cross_encoder
# pyrefly: ignore [missing-import]
from src.config import settings
# pyrefly: ignore [missing-import]
from src.audio.tts import load_kokoro_model
# pyrefly: ignore [missing-import]
from src.rag.build_VKB_index import get_or_create_vkb
# pyrefly: ignore [missing-import]
from src.audio.tts import _sync_tts

import time
import asyncio
import numpy as np

# import sounddevice as sd

_retriever_cache = None

async def get_cached_retriever():
    global _retriever_cache
    if _retriever_cache is None:
        print("[STARTUP] Loading embed model (once)...")
        vector_db, documents = await get_or_create_vkb()
        _retriever_cache = Hybride_Retriver(vector_db, documents)
    return _retriever_cache


# build to catch the query from user and decide wether to use the retrieval or not
async def catch_query_and_text_queues(user_query:str,txt_queue:asyncio.Queue , audio_queue:asyncio.Queue=None):
    
    t0=time.perf_counter()
    if await query_classifier(user_query)=="NO_RETRIEVAL":
        buffer=""
        async for token in brain_stream(user_query,context="NA",query_class="NO_RETRIEVAL"):
            print(token , end="",flush=True)
            buffer = buffer + token

            if any(token.strip().endswith(p) for p in (".", "?", "।")):
                sentence = buffer.strip()
                if sentence:
                    print(f"\nLLM -> TEXT QUEUE:\n{sentence}")
                    await txt_queue.put(sentence)
                buffer=""
            
        # after the loop is done, there might be some text left in the buffer
        # add that to the queue
        if buffer.strip():
            await txt_queue.put(buffer.strip())
            print(f"\nLLM -> TEXT QUEUE:\n{buffer.strip()}")

        await txt_queue.put(None)
        t1 = time.perf_counter()
        print(f"[TIMING] NO RETRIEVAL Query to Text Queue: {t1-t0:.2f}s")
        print("\nLLM -> TEXT QUEUE: (END OF STREAM)")
    
    else:
        # We need to require the actuall RAG functionality here
        # which includes instantiating the hybrid retriever, 
        
        # initialize the embedding model and the vectore store here 
        # retrive from offline vectore store  if it not exists create one 
        # get the documents from hybrid retriever
        # rerank the documents
        # build the prompt
        # call the gemini LLM
        # stream the response to the tts queue

    
        t0=time.perf_counter()
        # # 1. Initialize the Vector DB if not exists else use the existing one
        # vectore_db,documents=await get_or_create_vkb()
        # t1=time.perf_counter()
        # print(f"[TIMING] Vector DB Initialization: {t1-t0:.2f}s")

        # # 2. Use the native hybrid retriever to retrieve the documents
        # retriever = Hybride_Retriver(vectore_db,documents)
        retriever_cache_obj =await get_cached_retriever()
        t1=time.perf_counter()
        print(f"[TIMING] obj of Hybrid Retriver Initialization: {t1-t0:.2f}s")

        # 3.use the cross encoder to rerank the documents
        retrieved_documents= await retriever_cache_obj.ainvoke(user_query)
        t2=time.perf_counter()
        print(f"[TIMING] Hybrid Retriever Retrieval: {t2-t1:.2f}s")

        reranked_documents = await cross_encoder(user_query, retrieved_documents)
        t3=time.perf_counter()
        print(f"[TIMING] Cross Encoder: {t3-t2:.2f}s")

        print("reranking has been done successfully")

        RELEVANCE_THRESHOLD = 0.3  # tune based on your cross-encoder's score distribution
        top_score = reranked_documents[0][1] if reranked_documents else 0 
        if top_score < RELEVANCE_THRESHOLD:
            context = "NA"
            
            print(f"[RAG] Low relevance detected (top score: {top_score:.3f} < {RELEVANCE_THRESHOLD}), generating response without context")
        else:
            context = "\n\n".join([doc[0].page_content for doc in reranked_documents])
            print(f"[RAG] High relevance detected (top score: {top_score:.3f} >= {RELEVANCE_THRESHOLD})")
        # 4. create a context from retrived documents

        t4=time.perf_counter()
        print(f"[TIMING] Context Creation: {t4-t3:.2f}s")
        print("context has been created successfully")

        # 5. call the brain_stream function and stream the response
        buffer=""

        t6=time.perf_counter()
        async for token in brain_stream(user_query,context=context,query_class="NEEDS_RETRIEVAL"):
            print(token , end="",flush=True)
            buffer = buffer + token

            if any(token.strip().endswith(p) for p in (".","?","।")):
                sentence=buffer.strip()
                if sentence:
                    # appending the last token in the buffer
                    print(f"\nLLM -> TEXT QUEUE:\n{sentence}")
                                 
                    await txt_queue.put(sentence)
                buffer=""
        t7=time.perf_counter()
        print(f"[TIMING] LLM response Stream: {t7-t6:.2f}s")

        # after the loop is done, there might be some text left in the buffer
        # add that to the queue
        if buffer.strip():
            await txt_queue.put(buffer.strip())
            print(f"\nLLM -> TEXT QUEUE:\n{buffer.strip()}")

        await txt_queue.put(None)
        t8 = time.perf_counter()
        print(f"[TIMING]  Total time of NEEDS RETRIEVAL Query to Text Queue: {t8-t0:.2f}s")
        print("\nLLM -> TEXT QUEUE: (END OF STREAM)")    


    return txt_queue


# function to generate the audio from the text queue
async def generate_audio_from_text_queue(txt_queue: asyncio.Queue, audio_queue: asyncio.Queue):
    
    at0=time.perf_counter()
    kokoro_model = await load_kokoro_model()
    at1=time.perf_counter()
    print(f"[TIMING] Kokoro Model Loading: {at1-at0:.2f}s")
    while True:
        text = await txt_queue.get()
        if text is None:
            await audio_queue.put(None)
            txt_queue.task_done()
            break
        
        if kokoro_model is not None and text.strip():
            try:
                # Run Kokoro in worker thread to prevent event loop lag
                audio_chunks = await asyncio.to_thread(_sync_tts, kokoro_model, text)
                for audio in audio_chunks:
                    await audio_queue.put(audio)

        
            except Exception as e:
                print(f"Error in TTS generation: {e}")
        txt_queue.task_done()
    at2=time.perf_counter()
    print(f"[TIMING]  Total time of TTS Generation: {at2-at1:.2f}s")
    return audio_queue
        # generate audio from text queue and put it in the audio queue 
        # CALL THE KOKORO TTS MODEL TO COVERT TXT CHUNKS TO AUDIO CHUNKS 



        

        
        

