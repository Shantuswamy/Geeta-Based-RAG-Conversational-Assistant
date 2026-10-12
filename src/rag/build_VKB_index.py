"""
This module is used to create and manage the vector database for the Gita.
This module uses Langchain ChromaDB for vector storage.
This module uses Langchain HuggingfaceEmbeddings for embedding.
This module is only responsible to create the persistent vector store ,
to decide if to create  one if existing or not is in main.py
This module will also return the retrived chunks for the query.
"""



# pyrefly: ignore [missing-import]
from data.data_preparation import gita_structured_chunker
# pyrefly: ignore [missing-import]
from utils.instantiate_embed_model import InstantiateEmbedModel
# from langchain_community.retrievers import BM25Retriever
# pyrefly: ignore [missing-import]
# from chromadb import Search, K, Knn, Rrf
from langchain_chroma import Chroma
from dotenv import load_dotenv
import json
import chromadb
load_dotenv()





async def get_or_create_vkb(path: str = "data/index/chroma", collection_name: str = "gita"):
    embedding_func = InstantiateEmbedModel()
    client = chromadb.PersistentClient(path=path)

    existing_names = [c.name for c in client.list_collections()]
    chunk_count = (
        client.get_collection(collection_name).count()
        if collection_name in existing_names else 0
    )

    # Documents are needed either way — for BM25 on first build,
    # and for BM25 on every subsequent load too (it's never persisted).
    with open("data/raw.json","r",encoding="utf-8") as f:
        data = json.load(f)
    documents = gita_structured_chunker(data)

    if chunk_count > 0:
        print(f"Loading existing '{collection_name}' — {chunk_count} chunks already indexed")
        vector_db = Chroma(client=client, collection_name=collection_name, embedding_function=embedding_func)
    else:
        print("No existing index found — building for the first time")
        vector_db = Chroma.from_documents(
            documents=documents, collection_name=collection_name,
            embedding=embedding_func, client=client,
        )
        print(f"Indexed {len(documents)} chunks into '{collection_name}'")

    return vector_db, documents   # <- now returns both


# def Hybride_retriver(vectorDBfunc: Chroma, data: list[Document], weights_to_dense: float = 0.6, weights_to_lexical: float = 0.4):
#     bm25_retriever = BM25Retriever.from_documents(data)
#     bm25_retriever.k = 20

#     chroma_retriever = vectorDBfunc.as_retriever(search_kwargs={"k": 20})

#     return EnsembleRetriever(
#         retrievers=[chroma_retriever, bm25_retriever],
#         weights=[weights_to_dense, weights_to_lexical],
#     )

# function that will  use the above function and return the retrived chunks


# def native_hybrid_retriever(vector_db: Chroma, user_query: str, k: int = 5):
#     """
#     Runs Chroma's NATIVE hybrid search: one dense KNN pass (query text
#     auto-embedded via Qwen) + one sparse KNN pass (BM25 over the query
#     text), fused with Reciprocal Rank Fusion — entirely inside Chroma's
#     engine, not hand-merged in Python.
#     """
#     print("at native hybrid retriever function")
#     hybrid_rank = Rrf(
#         ranks=[
#             Knn(query=user_query, key="#embedding", limit=k * 4),        # dense leg
#             Knn(query=user_query, key="sparse_embedding", limit=k * 4),   # sparse/BM25 leg
#         ],
#         weights=[0.7, 0.3],   # tune once you're evaluating retrieval quality
#         k=60,
#     )

#     search = (
#         Search()
#         .rank(hybrid_rank)
#         .limit(k)
#         .select(K.DOCUMENT, K.SCORE, K.METADATA)
#     )

#     return vector_db.hybrid_search(search)   # LangChain's hybrid entry point — not .search()


