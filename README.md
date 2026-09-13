# Calibre YES24 Plugin Suite

이 저장소는 YES24를 Calibre에서 사용하는 두 플러그인을 함께 배포합니다.

- **YES24 Metadata Source 0.5.4** — YES24 메타데이터/표지 검색, `identifier:yes24` 저장, 공유 캐시 기반 `⭐스테디셀러` 태그 추가
- **YES24 Library Status 0.3.6** — YES24 공개 랭킹 상태/이력 기록 및 Metadata Source 자동 연동, 스테디셀러 storefront 공유 캐시 생성

두 플러그인은 독립적으로 설치할 수 있지만 함께 사용할 때 가장 잘 연결됩니다. Metadata Source가 저장한 `identifier:yes24`를 Library Status가 상태 갱신에 사용하고, Library Status 0.3.6이 만든 storefront 캐시를 Metadata Source 0.5.4가 `⭐스테디셀러` 태그 판정에 사용합니다.

## 설치 파일

GitHub Releases에서 각각 설치합니다.

```text
Yes24.zip
Yes24LibraryStatus.zip
```

Calibre에서 `환경설정 → 플러그인 → 파일에서 플러그인 불러오기`로 설치할 수 있습니다.

## YES24 Metadata Source 0.5.4

YES24 공식 Open API를 우선 사용해 제목, 저자, ISBN, YES24 itemId, 출판사, 발행일, 책소개, 카테고리 태그, 언어, 시리즈, 표지를 가져옵니다. 여러 후보가 있는 경우 자체 서지 랭킹 순서를 유지한 채 최대 10개까지 보여 주어 사용자가 판본을 선택할 수 있습니다.

0.5.4부터 Library Status가 만든 로컬 공유 캐시에서 선택 도서의 YES24 `itemId`를 대조합니다. 포함되어 있으면 기존 카테고리 태그에 `⭐스테디셀러`를 추가합니다. 캐시가 없거나 손상되어도 일반 메타데이터 검색은 그대로 동작하며 별 태그만 생략됩니다.

Metadata Source는 이 별 태그를 판정하기 위해 YES24 storefront HTML을 추가 요청하지 않습니다.

## YES24 Library Status 0.3.6

선택 도서 또는 Metadata Source 저장 직후 도서의 YES24 현재 랭킹 상태와 월별 이력을 사용자 정의 컬럼에 기록합니다. Calibre 시작 후 공개 YES24 Open API 랭킹 snapshot을 백그라운드에서 prefetch해 자동 갱신 속도를 높입니다.

0.3.6부터 Calibre 시작 후 YES24 국내도서 스테디셀러 storefront를 백그라운드에서 순회해 다음 공유 캐시를 만듭니다.

```text
<Calibre config>/yes24_library_status/steady_seller.json
```

새 캐시는 원자적으로 교체되어 갱신 실패 시 이전 정상 캐시를 보존합니다. 현재 정책은 지정 storefront를 순회하며 발견되는 고유 YES24 상품 링크 집합을 캐시하므로 개수가 정확히 1,000으로 고정되지는 않습니다.

## API Key

YES24 Metadata Source 설정에서 YES24 Open API Key를 입력합니다. Library Status는 별도의 키 입력란을 만들지 않고 같은 설정을 읽습니다.

## 네트워크 및 데이터

Metadata Source는 메타데이터/표지 조회를 위해 YES24 Open API와 필요한 경우 YES24 상품/시리즈 페이지에 접속합니다.

Library Status는 API Key가 설정되어 있으면 Calibre 시작 후 YES24 Open API 공개 랭킹 목록을 자동 prefetch합니다. 0.3.6부터는 여기에 YES24 국내도서 스테디셀러 공개 storefront 페이지 조회가 추가됩니다.

Library Status의 startup 요청에는 사용자의 EPUB/PDF 파일, 책 제목, ISBN, `identifier:yes24`, 라이브러리 전체 메타데이터를 전송하지 않습니다. 공개 목록과 로컬 식별자의 비교는 로컬에서 수행합니다.

## 0.5.4 / 0.3.6 실환경 검증

2026-09-14 Calibre 9.14 / Windows 11 / 3,776권 라이브러리에서 두 플러그인의 연동을 검증했습니다.

- 두 플러그인 0.5.4 / 0.3.6 정상 로드
- 기존 startup ranking snapshot prefetch 정상
- storefront cache 26페이지 / 1,028 unique product IDs 수집
- 스테디셀러 도서의 별 태그 삭제 후 재검색 시 `⭐스테디셀러` 재생성
- 여러 도서를 연속 재검색할 때 캐시 일치 도서에만 별 태그 추가
- 기존 YES24 카테고리 태그와 별 태그 공존

자세한 릴리스 메모는 `RELEASE_NOTES_0.5.4_AND_LIBRARY_STATUS_0.3.6.md`를 참고하세요.

## 문서

- `docs/README.md` — 문서 안내
- `docs/metadata-source.md` — Metadata Source 상세
- `docs/library-status.md` — Library Status 상세
- `docs/integration.md` — 두 플러그인의 연동
- `docs/network-and-data.md` — 네트워크와 로컬 데이터
- `docs/releases.md` — 릴리스 기록

## 라이선스

저장소의 `LICENSE`를 따릅니다.
