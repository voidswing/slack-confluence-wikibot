# built-in
import os

# python-dotenv
from dotenv import load_dotenv

# openai
from openai import AsyncOpenAI

# ingestion
from ingestion.chroma_client import get_chroma_collection


load_dotenv()

CONFLUENCE_URL = os.getenv("CONFLUENCE_URL")
SPACE_KEY = os.getenv("SPACE_KEY")


def retrieve_relevant_chunks(query_text, top_k=3):
    collection = get_chroma_collection()
    results = collection.query(query_texts=[query_text], n_results=top_k)
    documents = results["documents"][0]
    metadatas = results["metadatas"][0]
    return documents, metadatas

async def query_confluence(prompt: str, temperature: float = 0.2):
    documents, metadatas = retrieve_relevant_chunks(prompt)

    # Slack Markdown 스타일 적용
    context_with_links = ""
    seen_pages = set()

    for doc, meta in zip(documents, metadatas):
        page_id = meta.get("page_id", "")
        page_title = meta.get("title", "Untitled")
        page_url = f"{CONFLUENCE_URL}/spaces/{SPACE_KEY}/pages/{page_id}"

        if page_id not in seen_pages:
            context_with_links += f"*<{page_url}|{page_title}>*\n```{doc}```\n\n"
            seen_pages.add(page_id)
        else:
            context_with_links += f"```{doc}```\n\n"

    client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    completion = await client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
            "role": "system",
            "content": (
                "당신은 컨플루언스 위키 문서만을 기반으로 Slack 메시지 형식으로 답변하는 컨플루언스 위키봇입니다. "
                "반드시 제공된 Context만을 사용하여 Slack Markdown을 활용해 깔끔하게 정리된 답변을 생성하세요.\n\n"
                "- 볼드체는 슬랙 Markdown 형식에 맞게 별표 1개로 감싸서 표현합니다. 예: *볼드체*\n"
                "- 문서 제목과 링크를 출처로 명확히 표기하세요. 예시: 출처: *<url|문서 제목>*\n"
                "- 참고할 수 있는 문서는 최대한 참고하여 상세한 답변을 생성하세요. \n"
                "- 중요한 코드 또는 강조할 문장은 슬랙 코드블록 스타일(```내용```) 또는 인라인 코드(`내용`)로 표현하세요.\n"
                "- 답변 마지막에 출처를 명시하세요.\n"
                "- Slack Markdown 포맷을 유지하세요."
            ),
        },
            {
                "role": "user",
                "content": f"Context:\n{context_with_links}\n\nQuestion: {prompt}",
            },
        ],
        temperature=temperature,
    )

    return completion.choices[0].message.content.strip()


