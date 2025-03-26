# built-in
import chromadb

# src
from ingestion import embedding


def init_chromadb(collection_name: str = "confluence_collection", persist_path: str = "./chromadb"):
    client = chromadb.PersistentClient(path=persist_path)
    openai_ef = embedding.get_embedding_function()
    collection = client.get_or_create_collection(
        name=collection_name,
        embedding_function=openai_ef,
    )
    return collection


def store_chunks_in_chroma(
    collection: chromadb.Collection,
    page_id: str,
    page_title: str,
    chunks: list[str],
):
    try:
        ids = [f"{page_id}-{i}" for i in range(len(chunks))]
        metadatas = [{"page_id": page_id, "title": page_title}] * len(chunks)
        collection.add(documents=chunks, metadatas=metadatas, ids=ids)

        print(f"Stored {len(chunks)} chunks for page {page_id} ({page_title})")
    except Exception as e:
        print(f"Error storing chunks for page {page_id}: {e}")
