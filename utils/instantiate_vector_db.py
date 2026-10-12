"""this module has been deprecated since the build_VKB_index.py 
module now has the functionality to create and manage the vector database"""

from langchain_chroma import Chroma



def InstantiateChromaVectorDB(collection_name,embedding_func,documents,persistent_client):
  """
  Function to instantiate the Chroma vector database
  """

  chroma_vecDB=Chroma.from_documents(
      documents=documents,
      collection_name=collection_name,
      embedding=embedding_func,
      client=persistent_client
      )
  
  return chroma_vecDB