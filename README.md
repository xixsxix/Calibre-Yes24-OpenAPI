# Calibre YES24 Plugin Suite

이 저장소는 YES24를 Calibre에서 사용하는 두 플러그인을 함께 배포합니다.

- **YES24 Metadata Source 0.5.5** — YES24 메타데이터/표지 검색, `identifier:yes24` 저장, 공식 관련분류 2단계 태그 보강, 공유 캐시 기반 `⭐스테디셀러` 태그
- **YES24 Library Status 0.3.7** — YES24 공개 랭킹 상태/이력 기록 및 Metadata Source 자동 연동, 스테디셀러 storefront 공유 캐시 생성, 전용 툴바 아이콘

두 플러그인은 독립적으로 설치할 수 있지만 함께 사용할 때 가장 잘 연결됩니다. Metadata Source가 저장한 `identifier:yes24`를 Library Status가 상태 갱신에 사용하고, Library Status가 만든 storefront 캐시를 Metadata Source가 `⭐스테디셀러` 판정에 사용합니다.

## 설치 파일

GitHub Releases에서 `Yes24.zip`과 `Yes24LibraryStatus.zip`을 설치합니다. Calibre에서 `환경설정 → 플러그인 → 파일에서 플러그인 불러오기`를 사용합니다.

## YES24 Metadata Source 0.5.5

YES24 공식 Open API를 우선 사용해 제목, 저자, ISBN, YES24 itemId, 출판사, 발행일, 책소개, 카테고리 태그, 언어, 시리즈, 표지를 가져옵니다. 상품 페이지의 `관련분류 > 카테고리 분류`에서 광역 루트 아래 2단계까지 공식 분류 태그를 보강하며, ISBN 뒤 부가번호가 붙은 identifier에서도 유효 ISBN을 검색용으로 추출합니다.

Library Status가 만든 로컬 공유 캐시에 선택 도서의 YES24 `itemId`가 포함되어 있으면 기존 태그에 `⭐스테디셀러`를 추가합니다. 캐시가 없거나 손상되어도 일반 검색은 그대로 동작합니다.

## YES24 Library Status 0.3.7

선택 도서 또는 Metadata Source 저장 직후 도서의 YES24 현재 랭킹 상태와 월별 이력을 사용자 정의 컬럼에 기록합니다. Calibre 시작 후 공개 YES24 Open API 랭킹 snapshot을 백그라운드에서 prefetch하고, YES24 국내도서 스테디셀러 storefront를 순회해 `<Calibre config>/yes24_library_status/steady_seller.json` 공유 캐시를 만듭니다.

0.3.7은 검증된 0.3.6 동작을 유지하면서 설치 ZIP에 `images/icon.png`를 포함하고 실제 Interface Action에서 전용 툴바 아이콘을 로드합니다.

## API Key

YES24 Metadata Source 설정에서 YES24 Open API Key를 입력합니다. Library Status는 별도의 키 입력란을 만들지 않고 같은 설정을 읽습니다.

## 네트워크 및 데이터

Metadata Source는 메타데이터/표지 조회를 위해 YES24 Open API와 필요한 경우 YES24 상품/시리즈 페이지에 접속합니다. Library Status는 API Key가 설정되어 있으면 YES24 Open API 공개 랭킹 목록을 prefetch하며, YES24 국내도서 스테디셀러 공개 storefront도 조회합니다. startup 요청에는 사용자의 EPUB/PDF 파일이나 라이브러리 전체 메타데이터를 전송하지 않습니다.

## 문서

- `docs/metadata-source.md` — Metadata Source 상세
- `docs/library-status.md` — Library Status 상세
- `docs/integration.md` — 두 플러그인의 연동
- `docs/network-and-data.md` — 네트워크와 로컬 데이터
- `docs/releases.md` — 릴리스 기록

## 라이선스

저장소의 `LICENSE`를 따릅니다.
