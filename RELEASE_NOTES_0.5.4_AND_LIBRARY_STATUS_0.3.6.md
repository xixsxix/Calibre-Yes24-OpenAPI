# YES24 Metadata Source 0.5.4 / Library Status 0.3.6

## ⭐스테디셀러 연동

YES24 Library Status 0.3.6이 Calibre 시작 후 YES24 국내도서 스테디셀러 storefront를 백그라운드에서 순회해 공유 캐시를 생성합니다. Metadata Source 0.5.4는 검색 중 별도 HTML 요청을 하지 않고 이 로컬 캐시만 조회합니다.

선택된 YES24 상품의 `itemId`가 캐시에 있으면 기존 태그에 `⭐스테디셀러`를 추가합니다. 캐시가 없거나 읽을 수 없는 경우 일반 메타데이터 검색은 그대로 성공하며 별 태그만 생략됩니다.

공유 캐시 경로:

```text
<Calibre config>/yes24_library_status/steady_seller.json
```

Library Status는 새 캐시를 임시 파일에 완성한 뒤 원자적으로 교체합니다. 시작 시 갱신이 실패하면 이전 정상 캐시는 그대로 유지됩니다.

## 실환경 검증

2026-09-14 Calibre 9.14 / Windows 11 / 3,776권 라이브러리에서 검증했습니다.

- Library Status 0.3.6과 Metadata Source 0.5.4 정상 로드
- 기존 Status startup snapshot prefetch 정상 동작
- storefront steady-seller cache: **26 pages / 1,028 unique product IDs / PASS**
- 스테디셀러 도서의 기존 별 태그를 삭제한 뒤 재검색하면 `⭐스테디셀러` 재생성: **PASS**
- 여러 도서를 연속 재검색해 캐시와 일치하는 도서에만 선택적으로 별 태그 추가: **PASS**
- 기존 YES24 카테고리 태그와 별 태그 공존: **PASS**

현재 storefront 캐시는 목록 페이지를 순회하면서 발견되는 YES24 상품 링크 집합을 사용합니다. 따라서 YES24 페이지의 부가 상품 링크가 일부 포함될 수 있으며 캐시 개수는 정확히 1,000으로 고정하지 않습니다.

## 네트워크 동작

Library Status 0.3.6은 기존 YES24 Open API startup prefetch에 더해 YES24 국내도서 스테디셀러 공개 storefront 페이지를 백그라운드에서 읽습니다. 이 storefront 요청에는 사용자의 EPUB/PDF 파일, 책 제목, ISBN, `identifier:yes24`, 라이브러리 메타데이터를 전송하지 않습니다.

Metadata Source 0.5.4는 `⭐스테디셀러` 판정을 위해 네트워크 요청을 추가하지 않습니다. Library Status가 만든 로컬 공유 캐시만 읽습니다.
