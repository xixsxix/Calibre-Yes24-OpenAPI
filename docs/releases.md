# 릴리스 문서

이 저장소에는 두 개의 플러그인이 함께 있으므로 버전 번호만 쓰지 않고 항상 플러그인 이름과 버전을 함께 표기합니다.

## 현재 안정 기준

| 플러그인 | 버전 | 상태 | 설치 파일 |
| --- | ---: | --- | --- |
| YES24 Metadata Source | 0.5.5 | 공개 안정 릴리스 | `Yes24.zip` |
| YES24 Library Status | 0.3.6 | 공개 안정 릴리스 | `Yes24LibraryStatus.zip` |

## 2026-09-16 릴리스

### YES24 Metadata Source 0.5.5

- YES24 상품 페이지 `관련분류 > 카테고리 분류`에서 광역 루트 아래 2단계까지 공식 카테고리 태그를 보강합니다.
- 여러 관련분류 경로를 합치고 정확한 중복만 제거합니다.
- `수상내역 및 미디어 추천 분류`와 `이 상품의 태그`는 카테고리 태그에서 제외합니다.
- HTML comment 등 storefront 마크업 변형을 안전하게 처리합니다.
- ISBN 뒤에 5자리 부가번호가 붙은 EPUB identifier에서도 체크디지트가 유효한 ISBN을 추출해 검색합니다.
- YES24 Open API에서 ISBN이 누락되면 기존 제목/저자 fallback을 사용합니다.
- 공개 태그: `v0.5.5`
- 설치 자산: `Yes24.zip`

상세 릴리스 메모: [Metadata Source 0.5.5](./releases/metadata-source-0.5.5.md)

## 2026-09-14 릴리스

### YES24 Metadata Source 0.5.4

- Library Status 0.3.6이 만든 로컬 storefront steady-seller cache를 읽어 선택된 YES24 `itemId`가 포함되면 `⭐스테디셀러` 태그를 추가합니다.
- 캐시가 없거나 손상되어도 일반 메타데이터 검색은 그대로 동작합니다.
- 공개 태그: `v0.5.4`

### YES24 Library Status 0.3.6

- Calibre 시작 후 YES24 국내도서 스테디셀러 storefront를 백그라운드에서 순회합니다.
- 고유 product `itemId` 집합을 `<Calibre config>/yes24_library_status/steady_seller.json`에 저장합니다.
- 공개 태그: `library-status-v0.3.6`

상세 릴리스 메모: [0.5.4 / 0.3.6](../RELEASE_NOTES_0.5.4_AND_LIBRARY_STATUS_0.3.6.md)

## 이전 안정 릴리스

- [Metadata Source 0.5.3](../RELEASE_NOTES_0.5.3.md)
- [Metadata Source 0.5.0](../RELEASE_NOTES_0.5.0.md)
- [Library Status 0.3.5](./releases/library-status-0.3.5.md)

## GitHub Release 자산

```text
Yes24.zip               # Metadata Source
Yes24LibraryStatus.zip  # Library Status
```

GitHub가 자동 생성하는 `Source code (zip)`은 Calibre 플러그인 설치 파일이 아닙니다.
