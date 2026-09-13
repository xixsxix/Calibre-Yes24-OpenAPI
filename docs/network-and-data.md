# 네트워크와 데이터 처리

이 문서는 YES24 Metadata Source와 YES24 Library Status가 어떤 네트워크 요청을 하고, 어떤 데이터를 로컬에 저장하며, 어떤 데이터를 외부로 전송하지 않는지 설명합니다.

## YES24 Metadata Source

Metadata Source는 사용자가 메타데이터 검색을 실행할 때 YES24 공식 Open API와 필요한 YES24 상품 페이지에 접근합니다.

검색 입력에 따라 제목, 저자, ISBN 등이 YES24 조회에 사용될 수 있습니다. 선택된 상품의 서지정보와 표지를 Calibre에 저장하며 YES24 API key는 Calibre 설정에만 보관합니다.

## YES24 Library Status

Library Status 0.3.5부터 YES24 Metadata Source의 API Key가 설정되어 있으면 Calibre GUI 초기화 완료 후 약 5초 뒤 YES24 공개 랭킹 목록을 백그라운드에서 미리 가져옵니다.

이 startup prefetch는 베스트셀러·스테디셀러 등 공개 Category API 목록을 준비하기 위한 요청입니다. prefetch 요청 자체에는 사용자의 EPUB 파일, Calibre 라이브러리 전체 메타데이터, 개별 책 제목, ISBN 또는 `identifier:yes24`를 전달하지 않습니다.

받아온 공개 랭킹 목록과 사용자의 책 식별자 비교는 로컬에서 수행합니다.

## 메모리 current snapshot

Library Status는 현재 랭킹 snapshot을 Calibre 프로세스 메모리에만 보관합니다.

```text
GUI 초기화 완료
→ 약 5초 후 current snapshot prefetch
→ 메모리 캐시 저장
→ fresh TTL 10분
→ 주기적 background refresh
→ Calibre 종료 시 메모리 snapshot 폐기
```

fresh TTL은 10분이며 자동 갱신에서는 최대 30분 이내의 stale snapshot을 즉시 사용할 수 있습니다. stale snapshot을 사용한 경우 새 snapshot을 백그라운드에서 갱신합니다. 캐시가 전혀 없으면 live snapshot 조회로 fallback합니다.

## 월별 history.sqlite3

과거 월별 베스트셀러 이력은 다음 위치의 SQLite 캐시에 최소 정보만 저장합니다.

```text
<Calibre config>/yes24_library_status/history.sqlite3
```

저장 항목은 기간, 카테고리, 순위, YES24 itemId, ISBN13입니다. YES24 원본 JSON 응답 전체를 영구 저장하지 않습니다.

완료된 `카테고리 + 월` 데이터는 성공적으로 받은 뒤 재사용하여 같은 과거 월을 반복 다운로드하지 않습니다.

## 로그

자동 연동 진단 로그는 다음 위치에 기록됩니다.

```text
<Calibre config>/yes24_library_status/auto_debug.log
```

API key와 YES24 원본 응답 전체는 로그에 기록하지 않습니다. 로그에는 자동 이벤트, 대상 book id, 식별자 안정성, 캐시 hit/miss, worker 처리시간, 컬럼 기록 결과 같은 진단 정보가 포함될 수 있습니다.

## API Key

두 플러그인은 같은 YES24 Open API Key를 사용합니다. Library Status는 별도 API Key 입력란을 두지 않고 Metadata Source의 설정을 읽습니다.

```text
metadata_sources/Yes24.json
```

API key를 공개 저장소, 스크린샷, 로그 첨부, 버그 리포트에 포함하지 마세요.

## 요약

Metadata Source는 사용자가 요청한 책을 찾기 위해 책 관련 검색 조건을 YES24에 보낼 수 있습니다. 반면 Library Status의 startup prefetch는 사용자의 라이브러리를 조회 조건으로 보내지 않고 공개 랭킹 목록을 먼저 내려받은 뒤 로컬에서 식별자를 대조합니다.
