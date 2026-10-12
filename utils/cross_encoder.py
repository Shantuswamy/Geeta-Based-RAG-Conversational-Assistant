from transformers.models.decision_transformer import modeling_decision_transformer
from transformers.models.decision_transformer import modeling_decision_transformer
from sentence_transformers import CrossEncoder
from langchain_core.documents import Document
# pyrefly: ignore [missing-import]
from src.config import settings
import torch
import asyncio
import time



# model = CrossEncoder("Qwen/Qwen3-Reranker-0.6B", trust_remote_code=True)
# it will b initiated in the main page. and passed as a function to the rag functions
_ENCODER_MODEL_CACHE = {}
async def cross_encoder(user_query:str, hybrid_retrived_chunks:list[Document], k_final=5, batch_size=2,model=settings.RERANKER_MODEL_NAME):

    """
    This function is used to rerank the documents retrieved from the hybrid retriever.
    Args:
        user_query: query
        hybrid_retrived_chunks: list of documents from hybrid retriever
        k_final: number of documents to return
        batch_size: batch size for the model
    Returns:
        reranked documents
    """
    
    
    if model not in _ENCODER_MODEL_CACHE:
        print("at cross encoder function (loading fresh)")
        print(f"Loading Reranker Model from local cache: {model}...")
        _ENCODER_MODEL_CACHE[model] = CrossEncoder(
            model,
            max_length=512,
            device=settings.DEVICE,
            model_kwargs={"cache_dir":str(settings.RERANKER_MODEL_DIR)}  # explicit — no ambiguity
        )
    cross_enc_model = _ENCODER_MODEL_CACHE[model]


    pairs = [
        [user_query, doc.page_content]
        for doc in hybrid_retrived_chunks
    ]
    
    if torch.cuda.is_available():
        print("Device Name:", torch.cuda.get_device_name(0))
        print(" cross encoder Model is on:", next(cross_enc_model.parameters()).device)

    else:
        print("CUDA is not available.")

    
    scores=await asyncio.to_thread(cross_enc_model.predict,
        pairs,
        batch_size=batch_size,
        show_progress_bar=False
    )
    print("scores of retrived documents :\n",scores)

    reranked = sorted(
        zip(hybrid_retrived_chunks, scores),
        key=lambda x: x[1],
        reverse=True
    )
   
    return reranked[:k_final]