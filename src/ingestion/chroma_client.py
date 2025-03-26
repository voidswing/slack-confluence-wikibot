# built-in
import os

# chromadb
import chromadb
from chromadb.utils import embedding_functions

# python-dotenv
from dotenv import load_dotenv

load_dotenv()


def get_chroma_collection(collection_name="confluence_collection"):
    client = chromadb.PersistentClient(path="./chromadb")
    openai_ef = embedding_functions.OpenAIEmbeddingFunction(
        api_key=os.getenv("OPENAI_API_KEY"),
        model_name=os.getenv("OPENAI_EMBEDDING_MODEL"),
    )

    collection = client.get_or_create_collection(
        name=collection_name,
        embedding_function=openai_ef,
    )

    return collection
