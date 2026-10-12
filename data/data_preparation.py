import json
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter


# with open(file="data/raw/gita_full_enriched_dataset.json") as f:
#   data=json.load(f)

# create a function that will chunk the data into documents
# and also create metadata for each document
def gita_structured_chunker(data, chunk_size: int = None, chunk_overlap: int = None):
    all_processed_documents = []
    current_id = 0
    

    for item in data:
        prabhu_data = item.get("prabhu") or {}

        # Create doc_verse
        doc_verse = Document(
            page_content=f"""
            chapter:{item.get("chapter")}
            verse:{item.get("verse")}
            sloka_sanskrith:{item.get("slok")}
            transliteration:{item.get("transliteration")}
            english_transliteration:{prabhu_data.get("et", "")}
            intent:{item.get("intent")}
            primary_emotion:{item.get("emotion", {}).get("primary", "")}
            problems:{" ".join(item.get("problems", []))}
            life_domians:{" ".join(item.get("life_domains", []))}
            """,
            metadata={
                "parent_id": f"BG_{item.get("chapter")}_{item.get("verse")}",
                "child_id": f"BG_{item.get("chapter")}_{item.get("verse")}_verse",
                "chunk_id": f"{current_id}",
                "type": "verse",
                "chapter": f"{item.get("chapter")}",
                "verse": f"{item.get("verse")}",
                "Author": f"{prabhu_data.get("author", "")}",
                "primary_emotion": f"{item.get("emotion", {}).get("primary", "")}",
                "secondary_emotion": f"{item.get("emotion", {}).get("secondary", "")}",
                "confidence": f"{item.get("emotion", {}).get("confidence", "")}",
                "tags": " ".join(item.get("emotion", {}).get("tags", [])),
                "intent": f"{item.get("intent")}",
                "keywords": " ".join(item.get("keywords", [])),
                "problems": " ".join(item.get("problems", [])),
                "life_domians": " ".join(item.get("life_domains", []))
            }
        )
        all_processed_documents.append(doc_verse)
        current_id += 1

        # Create doc_coment
        doc_coment = Document(
            page_content=f"""
            chapter:{item.get("chapter")}
            verse:{item.get("verse")},
            primary_emotion:{item.get("emotion", {}).get("primary", "")}
            problems:{" ".join(item.get("problems", []))}
            life_domians:{" ".join(item.get("life_domains", []))}
            commentary:{prabhu_data.get("ec", "")}

            """,
            metadata={
                "parent_id": f"BG_{item.get("chapter")}_{item.get("verse")}",
                "child_id": f"BG_{item.get("chapter")}_{item.get("verse")}_commentary",
                "chunk_id": f"{current_id}",
                "type": "commentary",
                "chapter": f"{item.get("chapter")}",
                "verse": f"{item.get("verse")}",
                "Author": f"{prabhu_data.get("author", "")}",
                "primary_emotion": f"{item.get("emotion", {}).get("primary", "")}",
                "secondary_emotion": f"{item.get("emotion", {}).get("secondary", "")}",
                "confidence": f"{item.get("emotion", {}).get("confidence", "")}",
                "tags": " ".join(item.get("emotion", {}).get("tags", [])),
                "intent": f"{item.get("intent")}",
                "keywords": " ".join(item.get("keywords", [])),
                "problems": " ".join(item.get("problems", [])),
                "life_domians": " ".join(item.get("life_domains", []))
            }
        )
        # doc_identity_for_subchunks=f'''chapter:{item.get("chapter")}
        #     verse:{item.get("verse")},
        #     primary_emotion:{item.get("emotion", {}).get("primary", "")}'''

        # # Determine if commentary needs sub-chunking
        # # Use a default chunk_size if not provided, e.g., 800 words
        # threshold = chunk_size 
        # if len(doc_coment.page_content.split()) >= threshold:
        #     text_splitter = RecursiveCharacterTextSplitter(
        #         chunk_size=chunk_size,
        #         chunk_overlap=chunk_overlap,
        #         length_function=len
        #     )
        #     # Use split_text on page_content and create new Document objects for sub-chunks
        #     sub_chunks_content = text_splitter.split_text(doc_coment.page_content)
        #     for i, content in enumerate(sub_chunks_content):
        #         sub_chunk_metadata = doc_coment.metadata.copy()
        #         sub_chunk_metadata["chunk_id"] = f"{doc_coment.metadata['chunk_id']}_sub_{i}"
        #         sub_chunk_metadata["type"] = "commentary_subchunk"
        #         sub_chunk_page_content=doc_identity_for_subchunks+content
        #         all_processed_documents.append(Document(page_content=sub_chunk_page_content, metadata=sub_chunk_metadata))
        # else:
            # If not long enough, add the original commentary document
        all_processed_documents.append(doc_coment)

        current_id += 1 # Increment ID after processing the commentary (either original or sub-chunks)

    return all_processed_documents