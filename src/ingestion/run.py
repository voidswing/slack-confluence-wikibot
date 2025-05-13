# built-in
import os
import argparse
from datetime import datetime, timezone, timedelta
from dateutil import parser as date_parser
from typing import List, Dict, Any, Optional, Set

# python-dotenv
from dotenv import load_dotenv

# ingestion
from ingestion import confluence_client
from ingestion import preprocessing
from ingestion import storage

# utils
from utils import times

load_dotenv()

SPACE_KEY = os.getenv("SPACE_KEY")
MAX_PAGES_PER_REQUEST = 100  # Confluence API의 기본 제한



def get_all_pages_in_space(confluence, space_key: str) -> List[Dict[str, Any]]:
    """
    Confluence 공간의 모든 페이지를 페이지네이션하여 가져옵니다.
    
    Args:
        confluence: Confluence 클라이언트 인스턴스
        space_key: 페이지를 가져올 공간의 키
    
    Returns:
        모든 페이지 목록
    """
    all_pages = []
    start = 0
    limit = MAX_PAGES_PER_REQUEST

    while True:
        pages = confluence.get_all_pages_from_space(
            space_key, 
            start=start, 
            limit=limit, 
            expand='version'
        )
        
        if not pages:
            break
        
        all_pages.extend(pages)
        
        # 페이지 수가 제한보다 적으면 더 이상 페이지가 없는 것
        if len(pages) < limit:
            break
        
        start += limit

    return all_pages


def ingest_all_pages(
    confluence, 
    collection, 
    space_key: Optional[str] = None, 
    page_ids: Optional[List[str]] = None, 
    exclude_ids: Optional[Set[str]] = None, 
    limit: int = 5000, 
    after_date: Optional[datetime] = None
):
    """
    페이지를 인제스트하고 필요한 경우 벡터 DB를 업데이트합니다.
    """
    exclude_ids = set(exclude_ids or [])
    
    # 페이지 목록 결정
    if page_ids:
        pages = [confluence.get_page_by_id(pid, expand='version,body.view') for pid in page_ids]
    else:
        space_key = space_key or SPACE_KEY
        pages = get_all_pages_in_space(confluence, space_key)
    
    total_pages = len(pages)
    processed_pages = skipped_pages = error_pages = 0

    print(f"📋 START: 총 {total_pages}개 페이지 처리를 시작합니다.")

    # after_date를 timezone-aware로 변환
    if after_date:
        after_date = times.ensure_timezone_aware(after_date)

    for page in pages:
        if processed_pages >= limit:
            print(f"⏹️ LIMIT: 지정된 페이지 한계({limit})에 도달하여 중단합니다.")
            break

        page_id = page["id"]

        if page_id in exclude_ids:
            print(f"🚫 SKIP: 페이지 ID {page_id} (제목: {page['title']})는 제외 목록에 있어 건너뛰었습니다.")
            skipped_pages += 1
            continue

        try:
            # API 호출 시 body.view를 명시적으로 확장
            page_detail = confluence.get_page_by_id(page_id, expand="version,body.view")
            
            # 페이지 디테일 로깅 (디버깅용)
            print(f"📝 페이지 상세: {page_detail.keys()}")

            # 마지막 업데이트 시간 추출
            last_updated = times.ensure_timezone_aware(date_parser.isoparse(page_detail["version"]["when"]))

            if after_date and last_updated < after_date:
                print(f"📅 SKIP: 페이지 ID {page_id} (제목: {page['title']})는 지정한 날짜({after_date.date()}) 이전에 업데이트되었습니다.")
                skipped_pages += 1
                continue

            page_title = page["title"]
            print(f"✅ PROCESS: {page_title} (ID: {page_id})")

            # body 키 안전하게 접근
            html_content = page_detail.get("body", {}).get("view", {}).get("value", "")
            
            if not html_content:
                print(f"⚠️ SKIP: 페이지 ID {page_id} (제목: {page_title})의 본문이 비어있습니다.")
                skipped_pages += 1
                continue

            text_content = preprocessing.html_to_text(html_content)

            if not text_content:
                print(f"⚠️ SKIP: 페이지 ID {page_id} (제목: {page_title})의 텍스트 변환 결과가 비어있습니다.")
                skipped_pages += 1
                continue

            # 기존 청크 삭제
            existing_ids = collection.get(where={"page_id": page_id}).get("ids", [])
            if existing_ids:
                collection.delete(ids=existing_ids)

            # 새 청크 추가
            chunks = preprocessing.chunk_text(text_content)
            new_ids = [f"{page_id}-{i}" for i in range(len(chunks))]
            metadatas = [{"page_id": page_id, "title": page_title}] * len(chunks)
            collection.add(ids=new_ids, documents=chunks, metadatas=metadatas)

            processed_pages += 1

        except KeyError as e:
            print(f"❌ KEY ERROR: 페이지 ID {page_id} (제목: {page['title']}) 처리 중 키 오류 발생: {e}")
            print(f"페이지 상세 정보: {page}")
            error_pages += 1
        except Exception as e:
            print(f"❌ ERROR: 페이지 ID {page_id} (제목: {page['title']}) 처리 중 오류 발생: {e}")
            print(f"페이지 상세 정보: {page}")
            error_pages += 1

    print("\n📊 SUMMARY:")
    print(f"🔹 총 페이지 수: {total_pages}")
    print(f"✅ 성공적으로 처리된 페이지: {processed_pages}")
    print(f"⏩ 건너뛴 페이지: {skipped_pages}")
    print(f"❌ 오류 발생 페이지: {error_pages}")


def main():
    parser = argparse.ArgumentParser(description="Confluence 데이터를 벡터DB에 저장하는 스크립트")

    parser.add_argument("--all", action="store_true", help="모든 페이지를 처리")
    parser.add_argument("--ids", nargs="+", help="처리할 특정 페이지 ID 목록")
    parser.add_argument("--exclude", nargs="+", help="제외할 페이지 ID 목록 (모든 페이지 처리 시 사용)")
    parser.add_argument("--limit", type=int, default=5000, help="처리할 페이지 최대 개수")
    parser.add_argument("--after-date", type=str, help="YYYY-MM-DD 형식으로, 지정 날짜 이후로 생성 또는 수정된 페이지만 처리")
    parser.add_argument("--space", type=str, default=SPACE_KEY, help="처리할 Confluence 공간 키")
    parser.add_argument("--recent", action="store_true", help="최근 하루 이내에 생성 또는 수정된 페이지만 처리")

    args = parser.parse_args()

    if not args.all and not args.ids:
        parser.error("⚠️ 최소한 하나의 옵션(--all 또는 --ids)이 필요합니다.")

    # Check for conflicting options
    if args.recent and args.after_date:
        print("⚠️ WARNING: --recent와 --after-date 옵션이 동시에 설정되었습니다. --recent 옵션을 무시합니다.")
        args.recent = False

    confluence = confluence_client.create_confluence_client()
    collection = storage.init_chromadb()

    exclude_ids = set(args.exclude or [])

    after_date = None
    if args.after_date:
        after_date = datetime.strptime(args.after_date, "%Y-%m-%d")
    elif args.recent:
        # 현재 시간에서 1일 전 날짜 계산
        after_date = datetime.now(timezone.utc) - timedelta(days=1)

    if args.all:
        ingest_all_pages(
            confluence, 
            collection, 
            space_key=args.space, 
            exclude_ids=exclude_ids, 
            limit=args.limit, 
            after_date=after_date
        )

    if args.ids:
        ingest_all_pages(
            confluence, 
            collection, 
            page_ids=args.ids, 
            after_date=after_date
        )

    print("\n🎉 작업 완료")


if __name__ == "__main__":
    main()