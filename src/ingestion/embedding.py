# built-in
import os

# chromadb
from chromadb.utils import embedding_functions

# python-dotenv
from dotenv import load_dotenv

load_dotenv()


def get_embedding_function():
    openai_ef = embedding_functions.OpenAIEmbeddingFunction(
        api_key=os.getenv("OPENAI_API_KEY"),
        model_name=os.getenv("OPENAI_EMBEDDING_MODEL"),
    )
    return openai_ef
