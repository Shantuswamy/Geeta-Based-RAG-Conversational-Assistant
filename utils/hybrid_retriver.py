"""
This module is been deprecated , as we are now using the 
custom built hybrid retriever provided by Langchain ChromaDB 
"""


from langchain_chroma import Chroma
from langchain_community.retrievers import BM25Retriever
from langchain_classic.retrievers import EnsembleRetriever
from langchain_core.documents import Document
import time

# 1. BM25 / lexical retriver 
#    - keyword-based
#    - fast
#    - needs fair amount of data to work well

# 2. Vector retriver/dense retriver(vector DB)
#    - semantic similarity
#    - needs embedding model
#    - needs vector database

# 3. hybrid retriver 
#    - combines the results of a dense retriever and a sparse retriever
#    - uses ensemble weighting to combine the results
#    - uses reciprocal rank fusion to combine the results

_BM25_CACHE={}
def load_bm25_retriver(data:list[Document],k:int=20):
    
    try:
        if "BM25" not in _BM25_CACHE:
            print("at bm25 retriver function (loading fresh)")
            _BM25_CACHE["BM25"]=BM25Retriever.from_documents(data)
            _BM25_CACHE["BM25"].k=k
        return _BM25_CACHE["BM25"]
    except Exception as e:
        print(f"Error loading BM25 model: {e}")
        return None

# create the BM25 sparse indexes only once and cache it once at every startup

def cache_sparse_indexes(data:list[Document],k:int=20):
    """
    This function is used to cache the sparse indexes of the data.
    Args:
        data: The data to be used for the BM25 retriever
    """
    try:
        if "sparse_indexes" not in _BM25_CACHE:
            print("Loading (BM25) sparse indexes Freshly...")
            _BM25_CACHE["sparse_indexes"]=BM25Retriever.from_documents(data)
            _BM25_CACHE["sparse_indexes"].k=k
        return _BM25_CACHE["sparse_indexes"]
    except Exception as e:
        print(f"Error loading (BM25) sparse indexes: {e}")
        return None



def Hybride_Retriver(vectorDBfunc: Chroma,data:list[Document],weights_to_lexical:float=0.4,weights_to_dense:float=0.6):
    """
    This function is used to create a hybrid retriever that combines the results of a dense retriever (vector database) and a sparse retriever (BM25).
    Args:
        vectorDBfunc: The vector database function
        data: The data to be used for the BM25 retriever
    Returns:
        A hybrid retriever that combines the results of a dense retriever and a sparse retriever
    """
    print("at hybride retriver function")
    
    # 1. sparse retriver (BM25)
    bm25_retriver=cache_sparse_indexes(data) 

    # 2. dense retriver (vector DB)
    chroma_retriever = vectorDBfunc.as_retriever(
        search_kwargs={"k": 20} #number of documents to be retrieved from chrom
    )

    hybrid_retriever = EnsembleRetriever(
        retrievers=[
            chroma_retriever,
            bm25_retriver
        ],
        weights=[
            weights_to_dense,
            weights_to_lexical
        ]
    )
    

    return hybrid_retriever


    # create native hybride retriever using langchian chromadb that returns documents
