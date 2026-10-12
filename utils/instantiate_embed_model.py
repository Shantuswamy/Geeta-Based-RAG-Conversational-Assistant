from langchain_huggingface import HuggingFaceEmbeddings

# pyrefly: ignore [missing-import]
from src.config import settings
import os
import torch
os.environ["HF_HUB_OFFLINE"] = "1"   # forces an error instead of a silent download if cache is missed

# function to instantiate embed model
_embed_cache = {}

def InstantiateEmbedModel(model=settings.EMBEDDING_MODEL_NAME,batch_size=settings.BATCH_SIZE):

  #open source qwen model to be implemented
  print("at embed model instantiation function")

  global _embed_cache
  if model not in _embed_cache:
    print(f"[DEBUG] embed model object id: {id(_embed_cache)}")
    print("at embed model instantiation function (loading fresh)")
    _embed_cache[model]=HuggingFaceEmbeddings(
        model_name=model,
        cache_folder= str(settings.EMBEDDING_MODEL_DIR),        
        model_kwargs={'device':'cpu','local_files_only':True},
        encode_kwargs={'batch_size': batch_size}
          ) 
    print("Model target configuration:", _embed_cache[model].model_kwargs.get('device', 'cpu'))

  return _embed_cache[model]