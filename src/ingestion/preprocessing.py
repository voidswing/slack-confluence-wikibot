# built-in
import re

# beautifulsoup4
from bs4 import BeautifulSoup


def html_to_text(html_content: str):
    soup = BeautifulSoup(html_content, "html.parser")
    text = soup.get_text(separator=" ")
    text = re.sub(r"\s+", " ", text).strip()
    return text


def chunk_text(text: str, chunk_size: int = 2048, overlap: int = 50):
    words = text.split()
    chunks = []

    start_idx = 0
    while start_idx < len(words):
        end_idx = start_idx + chunk_size
        chunk = words[start_idx:end_idx]
        chunks.append(" ".join(chunk))
        start_idx += chunk_size - overlap

    return chunks
