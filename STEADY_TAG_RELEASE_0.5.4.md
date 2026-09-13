# YES24 Metadata Source 0.5.4

## ⭐스테디셀러 연동

YES24 Library Status 0.3.6이 Calibre 시작 후 YES24 국내도서 스테디셀러 storefront를 백그라운드에서 순회해 공유 캐시를 생성합니다. Metadata Source 0.5.4는 검색 중 별도 HTML 요청을 하지 않고 이 로컬 캐시만 조회합니다.

선택된 YES24 상품의 `itemId`가 캐시에 있으면 기존 태그에 `⭐스테디셀러`를 추가합니다. 캐시가 없거나 읽을 수 없는 경우 일반 메타데이터 검색은 그대로 성공하며 별 태그만 생략됩니다.

## 실환경 검증

2026-09-14 Calibre 9.14 / Windows 11 / 3,776권 라이브러리에서 검증했습니다.

- Library Status 0.3.6과 Metadata Source 0.5.4 정상 로드
- startup storefront cache: 26 pages / 1,028 unique product IDs
- 기존 Status snapshot prefetch 정상 동작
- 스테디셀러 도서의 기존 태그를 삭제한 뒤 재검색하면 `⭐스테디셀러` 재생성 확인
- 여러 도서를 연속 재검색해 캐시와 일치하는 도서에만 선택적으로 별 태그가 추가되는 것 확인
- 기존 YES24 카테고리 태그와 별 태그가 함께 유지되는 것 확인

현재 storefront 캐시는 목록 페이지를 순회하면서 발견되는 YES24 상품 링크 집합을 사용합니다. 따라서 YES24 페이지의 부가 상품 링크가 일부 포함될 수 있으며 캐시 개수는 정확히 1,000으로 고정하지 않습니다.
