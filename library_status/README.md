# YES24 Library Status

YES24 공개 랭킹 목록을 Calibre 사용자 정의 컬럼에 기록하는 Interface Action 플러그인입니다.

현재 릴리스 후보는 **0.3.6**입니다.

## Metadata Source 연동

YES24 Metadata Source가 저장한 `identifier:yes24`를 우선 사용하고 ISBN13을 보조 식별자로 사용합니다. Metadata Source 저장 직후 identifiers 변경 이벤트를 감지해 해당 도서의 YES24 상태를 자동 갱신할 수 있습니다.

0.3.6부터 Calibre 시작 후 YES24 국내도서 스테디셀러 storefront를 백그라운드에서 순회해 공유 캐시를 생성합니다.

```text
<Calibre config>/yes24_library_status/steady_seller.json
```

Metadata Source 0.5.4는 이 캐시에서 선택된 YES24 `itemId`를 로컬 대조하고 포함된 도서에 `⭐스테디셀러` 태그를 추가합니다. Metadata Source 검색 자체는 storefront HTML을 추가 요청하지 않습니다.

새 캐시는 임시 파일에 완성한 뒤 원자적으로 교체합니다. 갱신 실패 시 이전 정상 캐시를 보존하며, 캐시가 없어도 Metadata Source의 일반 메타데이터 검색은 계속 정상 동작합니다.

## 현재 상태와 이력

현재 snapshot은 YES24 Open API의 실시간/종합/특가/스테디/일간/월간 베스트 목록을 사용합니다. 월별 과거 이력은 로컬 SQLite 캐시에 동기화합니다.

수동 `YES24 상태 갱신`은 live query를 유지하고, Metadata Source 저장 직후 자동 갱신은 startup snapshot cache를 우선 사용합니다.

## 네트워크 동작

API Key가 설정되어 있으면 Calibre 시작 후 Library Status가 백그라운드에서 YES24 Open API 공개 랭킹 목록을 prefetch합니다. 0.3.6은 여기에 YES24 국내도서 스테디셀러 공개 storefront 페이지 조회가 추가됩니다.

startup 요청에는 사용자의 EPUB/PDF 파일, 책 제목, ISBN, `identifier:yes24`, 라이브러리 전체 메타데이터를 전송하지 않습니다. 공개 목록과 로컬 도서 식별자의 비교는 로컬에서 수행합니다.

## 실환경 검증

2026-09-14 Calibre 9.14 / Windows 11 / 3,776권 라이브러리에서 다음을 확인했습니다.

- Library Status 0.3.6 정상 로드
- 기존 startup ranking snapshot prefetch 정상
- storefront steady-seller cache 26페이지 / 1,028 unique product IDs 수집
- Metadata Source 0.5.4의 `⭐스테디셀러` 태그와 정상 연동

자세한 내용은 `RELEASE_NOTES_0.3.6.md`와 저장소 루트의 `RELEASE_NOTES_0.5.4_AND_LIBRARY_STATUS_0.3.6.md`를 참고하세요.

## 빌드

```powershell
cd library_status
python .\test_status_core.py
python .\test_history_core.py
python .\test_public_contract.py
python .\test_steady_cache.py
python .\build_plugin.py
```

생성 파일:

```text
Yes24LibraryStatus.zip
```
