

# pyrefly: ignore [missing-import]
from src.config import settings
from langchain_ollama import ChatOllama
from langchain_groq import ChatGroq
# pyrefly: ignore [missing-import]
from src.llm.prompt_templates import CLASSIFIER_PROMPT , RAG_ANSWER_PROMPT , CASUAL_PROMPT
from langchain_core.output_parsers import StrOutputParser
import time
from dotenv import load_dotenv
import os

load_dotenv()


classfier=ChatGroq(
        model="openai/gpt-oss-20b",
        api_key=os.getenv("GROQ_API_KEY")
        )

parser=StrOutputParser()


# function to load the llm model and cache it 

_LLM_CACHE={}

async def load_local_llm():
    global _LLM_CACHE
    model_name=settings.OLLAMA_MODEL_NAME
    if model_name in _LLM_CACHE:
        return _LLM_CACHE[model_name]

    _LLM_CACHE[model_name]=ChatOllama(
    model="qwen2.5:1.5b",
    streaming=True,
    temperature=0.2,
    repetition_penalty=1.3,  
    no_repeat_ngram_size= 3,
)
    return _LLM_CACHE[model_name]


#create function to classify the user query
async def query_classifier(user_query:str):
    t0 = time.perf_counter()
    print("at query classifier function")
    classigy_chain = CLASSIFIER_PROMPT | classfier | parser
    result=await classigy_chain.ainvoke({"user_query":user_query})
    t1 = time.perf_counter()
    print(f"[TIMING] Query Classifier: {t1-t0:.2f}s")
    print(result)

    return result


# llm streaming function 

async def brain_stream(user_query: str, context: str, query_class: str):
    brain=await load_local_llm()
    t1 = time.perf_counter()
    first_token_received = False

    if query_class == "NEEDS_RETRIEVAL":
        if not first_token_received:
            t_first = time.perf_counter()
            print(f"⏱️ [TIMING] Time-to-First-Token (TTFT): {t_first - t1:.2f}s")
            first_token_received = True
        chain = RAG_ANSWER_PROMPT | brain | parser
        input_data = {"retrieved_context": context, "user_query": user_query}
    else:
        if not first_token_received:
            t_first = time.perf_counter()
            print(f"⏱️ [TIMING] Time-to-First-Token (TTFT): {t_first - t1:.2f}s")
            first_token_received = True
        chain = CASUAL_PROMPT | brain | parser
        input_data = {"user_query": user_query}

    
    

    async for chunk in chain.astream(input_data):
        yield chunk
    t_end = time.perf_counter()
    print(f"🛑 [TIMING] Full Text Generation Completed in: {t_end - t1:.2f}s total.")

        

    
