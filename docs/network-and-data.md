# 네트워크와 데이터 처리

이 문서는 YES24 Metadata Source와 YES24 Library Status가 어떤 네트워크 요청을 하고, 어떤 데이터를 로컬에 저장하는지 설명합니다.

## YES24 Metadata Source

Metadata Source는 사용자가 메타데이터 검색을 실행할 때 YES24 공식 Open API에 접근합니다. 검색 입력에 따라 제목, 저자, ISBN 등이 YES24 조회에 사용될 수 있습니다.

0.5.5에서는 Open API가 제공하는 넓은 분류를 보강하기 위해 반환 후보의 YES24 상품 페이지를 추가로 조회할 수 있습니다. 상품 페이지에서는 `관련분류`의 `카테고리 분류`만 읽으며 수상/미디어 추천 분류와 마케팅 태그는 카테고리 태그로 사용하지 않습니다. 상품 페이지 요청이나 파싱이 실패해도 Open API 검색 결과는 그대로 반환합니다.

표지와 시리즈/책소개 보강이 필요한 경우에도 기존과 같이 YES24 상품·시리즈 페이지에 접근할 수 있습니다. 선택된 상품의 서지정보와 표지를 Calibre에 저장하며 YES24 API key는 Calibre 설정에만 보관합니다.

## YES24 Library Status

Library Status는 YES24 Metadata Source의 API Key가 설정되어 있으면 Calibre GUI 초기화 후 YES24 공개 랭킹 목록을 백그라운드에서 미리 가져옵니다. 0.3.6부터는 YES24 국내도서 스테디셀러 storefront도 순회하여 공유 캐시를 만듭니다.

startup 요청 자체에는 사용자의 EPUB/PDF 파일, Calibre 라이브러리 전체 메타데이터, 개별 책 제목, ISBN 또는 `identifier:yes24`를 전달하지 않습니다. 공개 목록과 사용자의 책 식별자 비교는 로컬에서 수행합니다.

## 로컬 캐시

현재 랭킹 snapshot은 Calibre 프로세스 메모리에 보관됩니다. 과거 월별 베스트셀러 이력은 `<Calibre config>/yes24_library_status/history.sqlite3`, storefront steady-seller itemId 집합은 `<Calibre config>/yes24_library_status/steady_seller.json`에 저장됩니다.

자동 연동 진단 로그는 `<Calibre config>/yes24_library_status/auto_debug.log`에 기록될 수 있습니다. API key와 YES24 원본 응답 전체는 로그에 기록하지 않습니다.

## API Key

두 플러그인은 같은 YES24 Open API Key를 사용합니다. Library Status는 별도 API Key 입력란을 두지 않고 Metadata Source의 `metadata_sources/Yes24.json` 설정을 읽습니다.

API key를 공개 저장소, 스크린샷, 로그 첨부, 버그 리포트에 포함하지 마세요.
