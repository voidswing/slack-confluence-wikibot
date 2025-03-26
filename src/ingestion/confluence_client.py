# built-in
import os

# atlassian
from atlassian import Confluence

# python-dotenv
from dotenv import load_dotenv

load_dotenv()


def create_confluence_client():
    confluence = Confluence(
        url=os.getenv("CONFLUENCE_URL"),
        username=os.getenv("CONFLUENCE_USERNAME"),
        password=os.getenv("CONFLUENCE_API_TOKEN"),
        cloud=True,
    )
    return confluence
